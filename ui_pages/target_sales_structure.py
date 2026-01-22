"""
목표 매출구조 페이지
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
import time
from src.ui_helpers import render_page_header, safe_get_value
from src.utils.time_utils import current_year_kst, current_month_kst
from src.storage_supabase import load_csv, load_expense_structure

# 공통 설정 적용
bootstrap(page_title="Target Sales Structure")


def render_target_sales_structure():
    """목표 매출구조 페이지 렌더링"""
    # 성능 측정 시작
    t0 = time.perf_counter()
    
    page_title = "목표 매출구조 분석"
    render_page_header(page_title, "📈")
    
    current_year = current_year_kst()
    current_month = current_month_kst()
    
    # 비용구조 페이지에서 사용한 연/월을 우선 사용하고, 없으면 현재 연/월 사용
    selected_year = int(st.session_state.get("expense_year", current_year))
    selected_month = int(st.session_state.get("expense_month", current_month))
    
    # 모든 원본 데이터를 render 함수 상단에서 한 번만 로드 (캐시 활용)
    expense_df = load_expense_structure(selected_year, selected_month)
    
    fixed_costs = 0
    variable_cost_rate = 0.0  # % 단위

    # 5대 비용(임차료, 인건비, 재료비, 공과금, 부가세&카드수수료)을 위한 세부 항목
    fixed_by_category = {
        '임차료': 0,
        '인건비': 0,
        '공과금': 0,
    }
    variable_rate_by_category = {
        '재료비': 0.0,
        '부가세&카드수수료': 0.0,
    }
    
    if not expense_df.empty:
        fixed_categories = ['임차료', '인건비', '공과금']
        fixed_costs = expense_df[expense_df['category'].isin(fixed_categories)]['amount'].sum()
        for cat in fixed_categories:
            fixed_by_category[cat] = expense_df[expense_df['category'] == cat]['amount'].sum()
        
        variable_categories = ['재료비', '부가세&카드수수료']
        variable_df = expense_df[expense_df['category'].isin(variable_categories)]
        if not variable_df.empty:
            variable_cost_rate = variable_df['amount'].sum()
            for cat in variable_categories:
                variable_rate_by_category[cat] = variable_df[variable_df['category'] == cat]['amount'].sum()
    
    # 목표 매출 로드
    targets_df = load_csv('targets.csv', default_columns=[
        '연도', '월', '목표매출', '목표원가율', '목표인건비율',
        '목표임대료율', '목표기타비용율', '목표순이익률'
    ])
    
    # 일일 판매 데이터 로드 (매출구조 분석용)
    daily_sales_items_df = load_csv('daily_sales_items.csv', default_columns=['날짜', '메뉴명', '판매수량'])
    
    # 원본 데이터 로드 완료 시점
    t1 = time.perf_counter()
    
    # 개발모드 디버그 정보 표시
    try:
        from src.auth import is_dev_mode, get_current_store_id
        if is_dev_mode():
            with st.expander("🔍 DEBUG: sales structure", expanded=False):
                current_store_id = get_current_store_id()
                st.write(f"**CURRENT STORE ID:** {current_store_id}")
                st.write(f"**선택된 기간:** {selected_year}년 {selected_month}월")
                
                st.write("**targets 로드 직후:**")
                st.write(f"  - row_count: {len(targets_df)}")
                if not targets_df.empty:
                    st.dataframe(targets_df.head(5), use_container_width=True)
                else:
                    st.caption("  (데이터 없음)")
                
                # targets 필터 적용 후
                if not targets_df.empty:
                    filtered_targets = targets_df[(targets_df['연도'] == selected_year) & (targets_df['월'] == selected_month)]
                    st.write("**targets 필터 적용 후 (연도, 월):**")
                    st.write(f"  - row_count: {len(filtered_targets)}")
                    if not filtered_targets.empty:
                        st.dataframe(filtered_targets.head(5), use_container_width=True)
                    else:
                        st.caption("  (필터 후 데이터 없음)")
                
                st.write("**daily_sales_items 로드 직후:**")
                st.write(f"  - row_count: {len(daily_sales_items_df)}")
                if not daily_sales_items_df.empty:
                    st.dataframe(daily_sales_items_df.head(5), use_container_width=True)
                    # 날짜 컬럼 확인 및 필터링
                    if '날짜' in daily_sales_items_df.columns:
                        daily_sales_items_df['날짜'] = pd.to_datetime(daily_sales_items_df['날짜'], errors='coerce')
                        filtered_daily = daily_sales_items_df[
                            (daily_sales_items_df['날짜'].dt.year == selected_year) & 
                            (daily_sales_items_df['날짜'].dt.month == selected_month)
                        ]
                        st.write("**daily_sales_items 필터 적용 후 (연도, 월):**")
                        st.write(f"  - row_count: {len(filtered_daily)}")
                        if not filtered_daily.empty:
                            st.dataframe(filtered_daily.head(5), use_container_width=True)
                        else:
                            st.caption("  (필터 후 데이터 없음)")
                else:
                    st.caption("  (데이터 없음)")
    except Exception:
        pass  # 디버그 실패해도 페이지는 계속 동작
    
    target_sales = 0
    if not targets_df.empty:
        target_row = targets_df[(targets_df['연도'] == selected_year) & (targets_df['월'] == selected_month)]
        # Phase 1: 안전한 DataFrame 접근
        target_sales = float(safe_get_value(target_row, '목표매출', 0)) if not target_row.empty else 0.0
    
    # 기본 검증
    variable_rate_decimal = variable_cost_rate / 100 if variable_cost_rate > 0 else 0
    
    # 목표매출을 기준으로 다양한 시나리오 생성 (데이터 가공)
    scenarios = []
    if not (fixed_costs <= 0 or variable_rate_decimal <= 0 or variable_rate_decimal >= 1) and target_sales > 0:
        scenarios = [
            ("목표매출 - 1,000만원", max(target_sales - 10_000_000, 0)),
            ("목표매출 - 500만원", max(target_sales - 5_000_000, 0)),
            ("목표매출 (기준)", target_sales),
            ("목표매출 + 500만원", target_sales + 5_000_000),
            ("목표매출 + 1,000만원", target_sales + 10_000_000),
            ("목표매출 + 1,500만원", target_sales + 15_000_000),
        ]
    
    # 데이터 가공 완료 시점
    t2 = time.perf_counter()
    
    # UI 출력 시작
    if fixed_costs <= 0 or variable_rate_decimal <= 0 or variable_rate_decimal >= 1:
        st.info("비용구조 페이지에서 고정비와 변동비율을 먼저 올바르게 입력해주세요.")
    elif target_sales <= 0:
        st.info("비용구조 페이지에서 목표 매출을 먼저 설정해주세요.")
    else:
        st.markdown("""
        <div class="info-box">
            <strong>📊 매출 수준별 비용·영업이익 시뮬레이션</strong><br>
            <span style="font-size: 0.9rem; opacity: 0.9;">
                비용구조의 고정비와 변동비율, 목표 매출을 기준으로 다양한 매출 수준에서의 비용과 영업이익을 비교합니다.
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        cols = [col1, col2, col3]
        
        for idx, (label, sales) in enumerate(scenarios):
            if sales <= 0:
                continue
            
            # 5대 비용 세부 계산
            rent_cost = fixed_by_category.get('임차료', 0)
            labor_cost = fixed_by_category.get('인건비', 0)
            utility_cost = fixed_by_category.get('공과금', 0)
            material_rate = variable_rate_by_category.get('재료비', 0.0) / 100
            fee_rate = variable_rate_by_category.get('부가세&카드수수료', 0.0) / 100
            material_cost = sales * material_rate
            fee_cost = sales * fee_rate

            total_cost = rent_cost + labor_cost + utility_cost + material_cost + fee_cost
            profit = sales - total_cost
            
            tile_col = cols[idx % 3]
            with tile_col:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 1.2rem; border-radius: 10px; margin-top: 0.8rem; color: #e5e7eb; box-shadow: 0 2px 6px rgba(0,0,0,0.35);">
                    <div style="font-size: 0.9rem; margin-bottom: 0.4rem; opacity: 0.9;">{label}</div>
                    <!-- 매출 영역: 선명한 흰색 -->
                    <div style="font-size: 1.3rem; font-weight: 700; margin-bottom: 0.3rem; color: #ffffff !important;">
                        매출: {int(sales):,}원
                    </div>
                    <!-- 비용 영역 제목: 더 진한 빨간색 -->
                    <div style="font-size: 0.9rem; margin-top: 0.5rem; border-top: 1px solid rgba(148,163,184,0.5); padding-top: 0.5rem; color: #ff4d4f !important;">
                        비용 합계 및 세부내역
                    </div>
                    <!-- 총 비용: 더 진한 빨간색 -->
                    <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.2rem; color: #ff4d4f !important;">
                        총 비용: {int(total_cost):,}원
                    </div>
                    <div style="font-size: 0.85rem; margin-top: 0.3rem; line-height: 1.4; color: #ff4d4f !important;">
                        임차료(고정비): {int(rent_cost):,}원<br>
                        인건비(고정비): {int(labor_cost):,}원<br>
                        공과금(고정비): {int(utility_cost):,}원<br>
                        재료비(변동비): {int(material_cost):,}원<br>
                        부가세·카드수수료(변동비): {int(fee_cost):,}원
                    </div>
                    <!-- 추정 영업이익 제목: 선명한 노란색 -->
                    <div style="font-size: 0.9rem; margin-top: 0.5rem; border-top: 1px solid rgba(148,163,184,0.5); padding-top: 0.5rem; color: #ffd700 !important;">
                        추정 영업이익
                    </div>
                    <!-- 추정 영업이익 값: 선명한 노란색 -->
                    <div style="font-size: 1.1rem; font-weight: 600; color: #ffd700 !important;">
                        {int(profit):,}원
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # UI 출력 완료 시점
    t3 = time.perf_counter()
    
    # 개발모드 성능 측정 표시
    try:
        from src.auth import is_dev_mode
        if is_dev_mode():
            total_sec = round(t3 - t0, 3)
            load_sec = round(t1 - t0, 3)
            transform_sec = round(t2 - t1, 3)
            ui_sec = round(t3 - t2, 3)
            
            with st.expander("🔍 DEBUG: performance", expanded=False):
                st.write("**렌더 성능 측정:**")
                st.write(f"  - **총 시간:** {total_sec}초")
                st.write(f"  - **데이터 로드:** {load_sec}초")
                st.write(f"  - **데이터 가공:** {transform_sec}초")
                st.write(f"  - **UI 출력:** {ui_sec}초")
                
                # 병목 지점 표시
                if load_sec > 5:
                    st.warning(f"⚠️ 데이터 로드가 느립니다 ({load_sec}초)")
                if transform_sec > 2:
                    st.warning(f"⚠️ 데이터 가공이 느립니다 ({transform_sec}초)")
                if ui_sec > 2:
                    st.warning(f"⚠️ UI 출력이 느립니다 ({ui_sec}초)")
    except Exception:
        pass  # 성능 측정 실패해도 페이지는 계속 동작


# Streamlit 멀티페이지에서 직접 실행될 때
# 주석 처리: app.py에서만 렌더되도록 함 (중복 호출 방지)
# render_target_sales_structure()
