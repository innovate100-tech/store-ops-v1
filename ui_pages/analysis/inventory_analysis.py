"""
재고 분석 페이지
안전재고와 현재고 차이를 한눈에 파악하고 발주 필요량을 계산
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
import logging
from datetime import datetime, timedelta
from src.ui_helpers import render_page_header, ui_flash_success, ui_flash_error, render_section_header
from src.storage_supabase import load_csv
from src.auth import get_current_store_id, get_supabase_client
from src.analytics import calculate_ingredient_usage, calculate_order_recommendation

logger = logging.getLogger(__name__)

# 공통 설정 적용
bootstrap(page_title="재고 분석")

# 재료 분류 옵션
INGREDIENT_CATEGORIES = ["채소", "육류", "해산물", "조미료", "기타"]

# 우선순위 색상
PRIORITY_COLORS = {
    "긴급": "#EF4444",
    "높음": "#F97316",
    "보통": "#F59E0B",
    "낮음": "#22C55E"
}

STATUS_COLORS = {
    "긴급": "#EF4444",
    "주의": "#F59E0B",
    "정상": "#22C55E"
}


def _get_ingredient_categories(store_id, ingredient_df):
    """재료 분류 조회 (DB에서)"""
    categories = {}
    if ingredient_df.empty:
        return categories
    
    supabase = get_supabase_client()
    if supabase:
        try:
            result = supabase.table("ingredients")\
                .select("name,category")\
                .eq("store_id", store_id)\
                .execute()
            
            if result.data:
                for row in result.data:
                    ingredient_name = row.get('name')
                    category_value = row.get('category')
                    if ingredient_name and category_value and category_value.strip():
                        categories[ingredient_name] = category_value.strip()
        except Exception as e:
            logger.warning(f"재료 분류 조회 실패: {e}")
    
    return categories


def _calculate_priority(current, safety):
    """우선순위 계산"""
    if current is None or safety is None or safety == 0:
        return "낮음"
    
    ratio = current / safety if safety > 0 else 1.0
    
    if ratio < 0.5:
        return "긴급"
    elif ratio < 0.8:
        return "높음"
    elif ratio < 1.0:
        return "보통"
    else:
        return "낮음"


def _calculate_status(current, safety):
    """상태 계산"""
    if current is None or safety is None:
        return "정상", "#22C55E"
    if current < safety * 0.5:
        return "긴급", "#EF4444"
    elif current < safety:
        return "주의", "#F59E0B"
    else:
        return "정상", "#22C55E"


def render_inventory_analysis():
    """재고 분석 페이지 렌더링"""
    render_page_header("📊 재고 분석", "📊")
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    # 데이터 로드
    ingredient_df = load_csv('ingredient_master.csv', store_id=store_id, 
                            default_columns=['재료명', '단위', '단가', '발주단위', '변환비율'])
    inventory_df = load_csv('inventory.csv', store_id=store_id, 
                           default_columns=['재료명', '현재고', '안전재고'])
    recipe_df = load_csv('recipes.csv', store_id=store_id, default_columns=['메뉴명', '재료명', '사용량'])
    daily_sales_df = load_csv('daily_sales_items.csv', store_id=store_id, 
                              default_columns=['날짜', '메뉴명', '판매수량'])
    
    if ingredient_df.empty:
        st.warning("먼저 재료를 등록해주세요.")
        if st.button("🧺 사용 재료 입력으로 이동", key="go_to_ingredient_input"):
            st.session_state["current_page"] = "재료 입력"
            st.rerun()
        return
    
    if inventory_df.empty:
        st.warning("먼저 재고 정보를 등록해주세요.")
        if st.button("📦 재고 입력으로 이동", key="go_to_inventory_input"):
            st.session_state["current_page"] = "재고 입력"
            st.rerun()
        return
    
    # 재료 분류 로드
    categories = _get_ingredient_categories(store_id, ingredient_df)
    
    # 사용량 계산
    usage_df = pd.DataFrame()
    if not daily_sales_df.empty and not recipe_df.empty:
        try:
            usage_df = calculate_ingredient_usage(daily_sales_df, recipe_df)
        except Exception as e:
            logger.warning(f"사용량 계산 실패: {e}")
    
    # 발주 추천 계산
    order_recommendation = pd.DataFrame()
    if not ingredient_df.empty and not inventory_df.empty:
        try:
            order_recommendation = calculate_order_recommendation(
                ingredient_df, inventory_df, usage_df, days_for_avg=7, forecast_days=3
            )
        except Exception as e:
            logger.warning(f"발주 추천 계산 실패: {e}")
    
    # ============================================
    # ZONE A: 대시보드 & 핵심 지표
    # ============================================
    _render_zone_a_dashboard(ingredient_df, inventory_df, order_recommendation)
    
    st.markdown("---")
    
    # ============================================
    # 필터 & 검색
    # ============================================
    filtered_order_df = _render_filters(order_recommendation, categories, ingredient_df, inventory_df)
    
    st.markdown("---")
    
    # ============================================
    # ZONE B: 발주 필요량 분석 (핵심)
    # ============================================
    _render_zone_b_order_analysis(filtered_order_df, ingredient_df, categories)
    
    st.markdown("---")
    
    # ============================================
    # ZONE C: 재고 현황 분석
    # ============================================
    _render_zone_c_inventory_analysis(ingredient_df, inventory_df, usage_df, categories)
    
    st.markdown("---")
    
    # ============================================
    # ZONE D: 발주 내보내기 & 액션
    # ============================================
    _render_zone_d_export_actions(filtered_order_df, store_id)


def _render_zone_a_dashboard(ingredient_df, inventory_df, order_recommendation):
    """ZONE A: 대시보드 & 핵심 지표"""
    render_section_header("📊 재고 현황 대시보드", "📊")
    
    # 재고 상태 계산
    order_needed_count = len(order_recommendation) if not order_recommendation.empty else 0
    
    urgent_count = 0
    warning_count = 0
    normal_count = 0
    
    if not inventory_df.empty:
        for _, row in inventory_df.iterrows():
            current = float(row.get('현재고', 0)) if row.get('현재고') else 0
            safety = float(row.get('안전재고', 0)) if row.get('안전재고') else 0
            
            if safety > 0:
                if current < safety * 0.5:
                    urgent_count += 1
                elif current < safety:
                    warning_count += 1
                else:
                    normal_count += 1
    
    # 예상 발주 비용 계산
    total_expected_cost = 0
    if not order_recommendation.empty and '예상금액' in order_recommendation.columns:
        total_expected_cost = order_recommendation['예상금액'].sum()
    
    # 핵심 지표 카드
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("발주 필요", f"{order_needed_count}개", 
                 delta=f"-{order_needed_count}" if order_needed_count > 0 else None)
    with col2:
        st.metric("긴급 발주", f"{urgent_count}개", 
                 delta=f"-{urgent_count}" if urgent_count > 0 else None)
    with col3:
        st.metric("주의 재고", f"{warning_count}개")
    with col4:
        st.metric("정상 재고", f"{normal_count}개")
    
    # 예상 발주 비용
    st.markdown("### 예상 발주 비용")
    st.metric("총 예상 발주 비용", f"{int(total_expected_cost):,}원" if total_expected_cost > 0 else "0원")
    
    # 스마트 알림
    alerts = []
    if urgent_count > 0:
        alerts.append(f"⚠️ 긴급 발주 필요 재고가 {urgent_count}개 있습니다.")
    if order_needed_count > 0:
        alerts.append(f"ℹ️ 발주 필요 재고가 {order_needed_count}개 있습니다.")
    
    if alerts:
        for alert in alerts:
            st.warning(alert)


def _render_filters(order_recommendation, categories, ingredient_df, inventory_df):
    """필터 & 검색"""
    if order_recommendation.empty:
        return pd.DataFrame()
    
    col1, col2, col3, col4 = st.columns([2, 2, 2, 4])
    
    with col1:
        category_filter = st.multiselect("재료 분류", options=["전체"] + INGREDIENT_CATEGORIES + ["미지정"], 
                                         default=["전체"], key="inventory_analysis_filter_category")
    with col2:
        priority_filter = st.selectbox("우선순위", options=["전체", "긴급", "높음", "보통", "낮음"], 
                                      key="inventory_analysis_filter_priority")
    with col3:
        status_filter = st.selectbox("상태", options=["전체", "긴급", "주의", "정상"], 
                                     key="inventory_analysis_filter_status")
    with col4:
        search_term = st.text_input("🔍 재료명 검색", key="inventory_analysis_search", placeholder="재료명으로 검색...")
    
    # 필터링 적용
    filtered_df = order_recommendation.copy()
    
    # 재료 분류 필터
    if "전체" not in category_filter:
        def category_match(name):
            cat = categories.get(name, "미지정")
            if "미지정" in category_filter:
                return cat == "미지정" or cat not in INGREDIENT_CATEGORIES
            return cat in category_filter
        filtered_df = filtered_df[filtered_df['재료명'].apply(category_match)]
    
    # 우선순위 필터
    if priority_filter != "전체":
        # 재고 정보와 조인하여 우선순위 계산
        merged_df = pd.merge(
            filtered_df[['재료명']],
            inventory_df[['재료명', '현재고', '안전재고']],
            on='재료명',
            how='left'
        )
        merged_df['우선순위'] = merged_df.apply(
            lambda row: _calculate_priority(
                float(row.get('현재고', 0)) if row.get('현재고') else 0,
                float(row.get('안전재고', 0)) if row.get('안전재고') else 0
            ),
            axis=1
        )
        filtered_df = filtered_df[filtered_df['재료명'].isin(
            merged_df[merged_df['우선순위'] == priority_filter]['재료명']
        )]
    
    # 상태 필터
    if status_filter != "전체":
        merged_df = pd.merge(
            filtered_df[['재료명']],
            inventory_df[['재료명', '현재고', '안전재고']],
            on='재료명',
            how='left'
        )
        merged_df['상태'] = merged_df.apply(
            lambda row: _calculate_status(
                float(row.get('현재고', 0)) if row.get('현재고') else 0,
                float(row.get('안전재고', 0)) if row.get('안전재고') else 0
            )[0],
            axis=1
        )
        filtered_df = filtered_df[filtered_df['재료명'].isin(
            merged_df[merged_df['상태'] == status_filter]['재료명']
        )]
    
    # 검색 필터
    if search_term and search_term.strip():
        filtered_df = filtered_df[filtered_df['재료명'].str.contains(search_term, case=False, na=False)]
    
    return filtered_df


def _render_zone_b_order_analysis(order_df, ingredient_df, categories):
    """ZONE B: 발주 필요량 분석 (핵심)"""
    render_section_header("🛒 발주 필요량 분석", "🛒")
    
    if order_df.empty:
        st.info("발주 필요 재고가 없습니다. 모든 재고가 정상입니다.")
        return
    
    # 재고 정보와 조인하여 우선순위 및 상태 계산
    inventory_df = load_csv('inventory.csv', store_id=get_current_store_id(), 
                           default_columns=['재료명', '현재고', '안전재고'])
    
    # 발주 단위 변환을 위한 재료 정보 매핑
    ingredient_info_map = {}
    for _, row in ingredient_df.iterrows():
        ingredient_name = row['재료명']
        unit = row.get('단위', '')
        order_unit = row.get('발주단위', unit)
        conversion_rate = float(row.get('변환비율', 1.0)) if row.get('변환비율') else 1.0
        ingredient_info_map[ingredient_name] = {
            'unit': unit,
            'order_unit': order_unit,
            'conversion_rate': conversion_rate
        }
    
    # 분석 결과 데이터프레임 준비
    analysis_data = []
    
    for _, row in order_df.iterrows():
        ingredient_name = row['재료명']
        current_base = float(row.get('현재고', 0))
        safety_base = float(row.get('안전재고', 0))
        order_amount_base = float(row.get('발주필요량', 0))  # 기본 단위
        expected_usage_base = float(row.get('예상소요량', 0)) if '예상소요량' in row else 0  # 기본 단위
        expected_cost = float(row.get('예상금액', 0))
        
        # 발주 단위로 변환
        info = ingredient_info_map.get(ingredient_name, {'order_unit': '', 'conversion_rate': 1.0})
        conversion_rate = info['conversion_rate']
        order_unit = info['order_unit']
        
        current_order = current_base / conversion_rate if conversion_rate > 0 else current_base
        safety_order = safety_base / conversion_rate if conversion_rate > 0 else safety_base
        shortage_order = max(0, safety_order - current_order)
        expected_usage_order = expected_usage_base / conversion_rate if conversion_rate > 0 else expected_usage_base
        order_amount_order = order_amount_base / conversion_rate if conversion_rate > 0 else order_amount_base
        
        # 우선순위 및 상태 계산
        priority = _calculate_priority(current_base, safety_base)
        status_text, _ = _calculate_status(current_base, safety_base)
        
        category = categories.get(ingredient_name, "미지정")
        
        analysis_data.append({
            '재료명': ingredient_name,
            '재료분류': category if category in INGREDIENT_CATEGORIES else "미지정",
            '단위': order_unit,
            '현재고': current_order,
            '안전재고': safety_order,
            '부족량': shortage_order,
            '예상소요량': expected_usage_order,
            '발주필요량': order_amount_order,
            '예상금액': expected_cost,
            '우선순위': priority,
            '상태': status_text
        })
    
    analysis_df = pd.DataFrame(analysis_data)
    
    # 정렬 (우선순위 우선, 발주 필요량 내림차순)
    priority_order = {"긴급": 0, "높음": 1, "보통": 2, "낮음": 3}
    analysis_df['우선순위_순서'] = analysis_df['우선순위'].map(priority_order)
    analysis_df = analysis_df.sort_values(['우선순위_순서', '발주필요량'], ascending=[True, False])
    analysis_df = analysis_df.drop('우선순위_순서', axis=1)
    
    # 테이블 표시
    st.dataframe(
        analysis_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            '재료명': st.column_config.TextColumn('재료명', width="medium"),
            '재료분류': st.column_config.TextColumn('재료분류', width="small"),
            '단위': st.column_config.TextColumn('단위', width="small"),
            '현재고': st.column_config.NumberColumn('현재고', format="%.2f", width="small"),
            '안전재고': st.column_config.NumberColumn('안전재고', format="%.2f", width="small"),
            '부족량': st.column_config.NumberColumn('부족량', format="%.2f", width="small"),
            '예상소요량': st.column_config.NumberColumn('예상소요량', format="%.2f", width="small"),
            '발주필요량': st.column_config.NumberColumn('발주필요량', format="%.2f", width="small"),
            '예상금액': st.column_config.NumberColumn('예상금액', format="%,.0f", width="medium"),
            '우선순위': st.column_config.TextColumn('우선순위', width="small"),
            '상태': st.column_config.TextColumn('상태', width="small"),
        }
    )


def _render_zone_c_inventory_analysis(ingredient_df, inventory_df, usage_df, categories):
    """ZONE C: 재고 현황 분석"""
    render_section_header("📊 재고 현황 분석", "📊")
    
    if inventory_df.empty:
        st.info("재고 정보가 없습니다.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 재고 상태 분포")
        
        # 재고 상태 계산
        status_counts = {"정상": 0, "주의": 0, "긴급": 0}
        for _, row in inventory_df.iterrows():
            current = float(row.get('현재고', 0)) if row.get('현재고') else 0
            safety = float(row.get('안전재고', 0)) if row.get('안전재고') else 0
            status, _ = _calculate_status(current, safety)
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # 파이 차트
        if sum(status_counts.values()) > 0:
            chart_data = pd.DataFrame({
                '상태': list(status_counts.keys()),
                '개수': list(status_counts.values())
            })
            st.bar_chart(chart_data.set_index('상태'))
    
    with col2:
        st.markdown("### 재고 회전율 TOP 10")
        
        if not usage_df.empty and not inventory_df.empty:
            # 최근 7일 평균 사용량 계산
            usage_df['날짜'] = pd.to_datetime(usage_df['날짜'])
            max_date = usage_df['날짜'].max()
            recent_cutoff = max_date - timedelta(days=7)
            recent_usage = usage_df[usage_df['날짜'] >= recent_cutoff]
            
            if not recent_usage.empty:
                daily_avg = recent_usage.groupby('재료명')['총사용량'].sum() / 7
                daily_avg = daily_avg.reset_index()
                daily_avg.columns = ['재료명', '평균사용량']
                
                # 재고 정보와 조인
                merged = pd.merge(
                    daily_avg,
                    inventory_df[['재료명', '현재고']],
                    on='재료명',
                    how='inner'
                )
                
                # 회전율 계산 (사용량 / 현재고)
                merged['회전율'] = merged.apply(
                    lambda row: row['평균사용량'] / row['현재고'] if row['현재고'] > 0 else 0,
                    axis=1
                )
                
                # TOP 10
                top10 = merged.nlargest(10, '회전율')[['재료명', '회전율']]
                st.dataframe(top10, use_container_width=True, hide_index=True)
    
    # 과다재고 경고
    st.markdown("### 과다재고 경고")
    excess_inventory = []
    for _, row in inventory_df.iterrows():
        current = float(row.get('현재고', 0)) if row.get('현재고') else 0
        safety = float(row.get('안전재고', 0)) if row.get('안전재고') else 0
        if safety > 0 and current > safety * 2:
            excess_inventory.append({
                '재료명': row['재료명'],
                '현재고': current,
                '안전재고': safety,
                '비율': current / safety if safety > 0 else 0
            })
    
    if excess_inventory:
        excess_df = pd.DataFrame(excess_inventory)
        st.dataframe(excess_df, use_container_width=True, hide_index=True)
    else:
        st.info("과다재고 재료가 없습니다.")


def _render_zone_d_export_actions(order_df, store_id):
    """ZONE D: 발주 내보내기 & 액션"""
    render_section_header("💾 발주 내보내기 & 액션", "💾")
    
    if order_df.empty:
        st.info("내보낼 발주 정보가 없습니다.")
    else:
        # CSV 내보내기
        csv = order_df[['재료명', '발주필요량', '예상금액']].to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 CSV 내보내기",
            data=csv,
            file_name=f"발주필요량_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="inventory_analysis_export_csv"
        )
    
    # 연계 페이지
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📦 재고 입력으로 이동", key="go_to_inventory_input", use_container_width=True):
            st.session_state["current_page"] = "재고 입력"
            st.rerun()
    with col2:
        if st.button("🧺 사용 재료 입력으로 이동", key="go_to_ingredient_input", use_container_width=True):
            st.session_state["current_page"] = "재료 입력"
            st.rerun()
