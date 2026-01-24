"""
재고 입력 페이지 (대량 입력 중심)
전체 재료를 한 번에 빠르게 등록할 수 있는 UI
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
import logging
from datetime import datetime, timedelta
from src.ui_helpers import ui_flash_success, ui_flash_error, render_section_header
from src.ui.layouts.input_layouts import render_console_layout
from src.storage_supabase import load_csv, save_inventory, soft_invalidate, clear_session_cache
from src.auth import get_current_store_id, get_supabase_client
from src.analytics import calculate_ingredient_usage, calculate_order_recommendation

logger = logging.getLogger(__name__)

# 공통 설정 적용
bootstrap(page_title="재고 입력")

# 재료 분류 옵션
INGREDIENT_CATEGORIES = ["채소", "육류", "해산물", "조미료", "기타"]
ITEMS_PER_PAGE = 50  # 페이지네이션: 한 페이지에 50개씩


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


def _calculate_status(current, safety):
    """재고 상태 계산"""
    if current is None or safety is None:
        return "미등록", "#9CA3AF"
    if current < safety:
        return "부족", "#EF4444"
    elif current <= safety * 1.2:
        return "주의", "#F59E0B"
    else:
        return "정상", "#22C55E"


def render_inventory_input_page():
    """재고 입력 페이지 렌더링 (대량 입력 중심, CONSOLE형 레이아웃 적용)"""
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    # 데이터 로드
    ingredient_df = load_csv('ingredient_master.csv', store_id=store_id, 
                            default_columns=['재료명', '단위', '단가', '발주단위', '변환비율'])
    inventory_df = load_csv('inventory.csv', store_id=store_id, 
                           default_columns=['재료명', '현재고', '안전재고'])
    
    if ingredient_df.empty:
        st.warning("먼저 재료를 등록해주세요.")
        if st.button("🧺 사용 재료 입력으로 이동", key="go_to_ingredient_input"):
            st.session_state["current_page"] = "재료 입력"
            st.rerun()
        return
    
    # 재료 분류 로드
    categories = _get_ingredient_categories(store_id, ingredient_df)
    
    # 재고 정보 매핑
    inventory_map = {}
    if not inventory_df.empty:
        for _, row in inventory_df.iterrows():
            ingredient_name = row.get('재료명', '')
            current_stock = float(row.get('현재고', 0)) if row.get('현재고') else 0
            safety_stock = float(row.get('안전재고', 0)) if row.get('안전재고') else 0
            if ingredient_name:
                inventory_map[ingredient_name] = {
                    'current': current_stock,
                    'safety': safety_stock
                }
    
    # 발주 필요 여부 확인 (간단 버전)
    needs_order = {}
    if not ingredient_df.empty and not inventory_df.empty:
        try:
            recipe_df = load_csv('recipes.csv', store_id=store_id, default_columns=['메뉴명', '재료명', '사용량'])
            daily_sales_df = load_csv('daily_sales_items.csv', store_id=store_id, 
                                      default_columns=['날짜', '메뉴명', '판매수량'])
            usage_df = pd.DataFrame()
            if not daily_sales_df.empty and not recipe_df.empty:
                usage_df = calculate_ingredient_usage(daily_sales_df, recipe_df)
            
            order_recommendation = calculate_order_recommendation(
                ingredient_df, inventory_df, usage_df, days_for_avg=7, forecast_days=3
            )
            if not order_recommendation.empty:
                needs_order = {row['재료명']: True for _, row in order_recommendation.iterrows()}
        except Exception as e:
            logger.warning(f"발주 추천 계산 실패: {e}")
    
    def render_dashboard_content():
        """Top Dashboard: ZONE A"""
        _render_zone_a_dashboard(ingredient_df, inventory_map, needs_order)
    
    def render_work_area_content():
        """Work Area: Filter + ZONE B"""
        # 필터 & 검색
        filtered_ingredient_df = _render_filters(ingredient_df, inventory_map, categories)
        st.markdown("---")
        # ZONE B: 대량 입력 테이블
        _render_zone_b_bulk_input_table(store_id, filtered_ingredient_df, ingredient_df, inventory_map, categories)
        # ZONE C도 여기서 처리 (filtered_ingredient_df 접근을 위해)
        st.markdown("---")
        _render_zone_c_save_validation(store_id, filtered_ingredient_df, ingredient_df, inventory_map)
    
    def render_list_content():
        """List/Editor: 사용 안 함 (Work Area에 포함)"""
        pass
    
    # CONSOLE형 레이아웃 적용
    render_console_layout(
        title="재고 입력",
        icon="📦",
        dashboard_content=render_dashboard_content,
        work_area_content=render_work_area_content,
        filter_content=None,  # Filter는 Work Area 내부에서 처리
        list_content=render_list_content,
        cta_label=None,
        cta_action=None
    )


def _render_zone_a_dashboard(ingredient_df, inventory_map, needs_order):
    """ZONE A: 대시보드 & 빠른 액션"""
    render_section_header("📊 재고 현황 대시보드", "📊")
    
    total_ingredients = len(ingredient_df)
    registered_inventory = len(inventory_map)
    shortage_count = sum(1 for inv_data in inventory_map.values() 
                         if inv_data['current'] < inv_data['safety'])
    unregistered_count = total_ingredients - registered_inventory
    
    # 핵심 지표 카드
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("전체 재료 수", f"{total_ingredients}개")
    with col2:
        st.metric("재고 등록 수", f"{registered_inventory}개", 
                 delta=f"{unregistered_count}개 미등록" if unregistered_count > 0 else None)
    with col3:
        st.metric("발주 필요", f"{shortage_count}개", 
                 delta=f"-{shortage_count}" if shortage_count > 0 else None)
    with col4:
        normal_count = sum(1 for inv_data in inventory_map.values() 
                          if inv_data['current'] > inv_data['safety'] * 1.2)
        st.metric("정상 재고", f"{normal_count}개")
    
    # 진행률 표시
    registration_rate = (registered_inventory / total_ingredients * 100) if total_ingredients > 0 else 0
    st.progress(registration_rate / 100, text=f"재고 등록률: {registration_rate:.0f}%")
    
    # 빠른 액션 버튼
    col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 2])
    with col_btn1:
        if st.button("📋 기존 재고 불러오기", key="inventory_load_existing", use_container_width=True):
            st.session_state['inventory_load_existing'] = True
            st.rerun()
    with col_btn2:
        if st.button("🔄 초기화", key="inventory_reset", use_container_width=True):
            if 'inventory_input_data' in st.session_state:
                del st.session_state['inventory_input_data']
            st.rerun()
    with col_btn3:
        if st.button("💾 전체 저장", type="primary", key="inventory_save_all", use_container_width=True):
            st.session_state['inventory_save_trigger'] = True
            st.rerun()


def _render_filters(ingredient_df, inventory_map, categories):
    """필터 & 검색"""
    if ingredient_df.empty:
        return pd.DataFrame()
    
    col1, col2, col3 = st.columns([2, 2, 4])
    
    with col1:
        category_filter = st.multiselect("재료 분류", options=["전체"] + INGREDIENT_CATEGORIES + ["미지정"], 
                                         default=["전체"], key="inventory_filter_category")
    with col2:
        registration_filter = st.selectbox("재고 등록 상태", options=["전체", "등록됨", "미등록"], 
                                          key="inventory_filter_registration")
    with col3:
        search_term = st.text_input("🔍 재료명 검색", key="inventory_search", placeholder="재료명으로 검색...")
    
    # 필터링 적용
    filtered_df = ingredient_df.copy()
    
    # 재료 분류 필터
    if "전체" not in category_filter:
        def category_match(name):
            cat = categories.get(name, "미지정")
            if "미지정" in category_filter:
                return cat == "미지정" or cat not in INGREDIENT_CATEGORIES
            return cat in category_filter
        filtered_df = filtered_df[filtered_df['재료명'].apply(category_match)]
    
    # 재고 등록 상태 필터
    if registration_filter == "등록됨":
        filtered_df = filtered_df[filtered_df['재료명'].isin(inventory_map.keys())]
    elif registration_filter == "미등록":
        filtered_df = filtered_df[~filtered_df['재료명'].isin(inventory_map.keys())]
    
    # 검색 필터
    if search_term and search_term.strip():
        filtered_df = filtered_df[filtered_df['재료명'].str.contains(search_term, case=False, na=False)]
    
    return filtered_df


def _render_zone_b_bulk_input_table(store_id, filtered_ingredient_df, full_ingredient_df, inventory_map, categories):
    """ZONE B: 대량 입력 테이블"""
    render_section_header("📝 재고 대량 입력", "📝")
    
    if filtered_ingredient_df.empty:
        st.info("필터 조건에 맞는 재료가 없습니다.")
        return
    
    # 페이지네이션
    total_items = len(filtered_ingredient_df)
    total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    current_page = st.session_state.get('inventory_page', 1)
    
    if current_page > total_pages:
        current_page = 1
        st.session_state['inventory_page'] = 1
    
    # 페이지네이션 컨트롤
    if total_pages > 1:
        col_prev, col_page, col_next = st.columns([1, 10, 1])
        with col_prev:
            if st.button("◀ 이전", key="inventory_page_prev", disabled=(current_page == 1)):
                st.session_state['inventory_page'] = current_page - 1
                st.rerun()
        with col_page:
            st.write(f"**페이지 {current_page} / {total_pages}** (총 {total_items}개 재료)")
        with col_next:
            if st.button("다음 ▶", key="inventory_page_next", disabled=(current_page == total_pages)):
                st.session_state['inventory_page'] = current_page + 1
                st.rerun()
    
    # 현재 페이지 데이터
    start_idx = (current_page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    page_df = filtered_ingredient_df.iloc[start_idx:end_idx].copy()
    
    # 입력 데이터프레임 준비
    input_data_list = []
    
    for _, row in page_df.iterrows():
        ingredient_name = row['재료명']
        unit = row.get('단위', '')
        order_unit = row.get('발주단위', unit)
        conversion_rate = float(row.get('변환비율', 1.0)) if row.get('변환비율') else 1.0
        category = categories.get(ingredient_name, "미지정")
        
        # 기존 재고 정보
        existing_inv = inventory_map.get(ingredient_name, {'current': 0, 'safety': 0})
        existing_current_base = existing_inv['current']
        existing_safety_base = existing_inv['safety']
        
        # 발주 단위로 변환
        existing_current_order = existing_current_base / conversion_rate if conversion_rate > 0 else existing_current_base
        existing_safety_order = existing_safety_base / conversion_rate if conversion_rate > 0 else existing_safety_base
        
        # 세션 상태에서 입력 데이터 가져오기
        session_key = f"inventory_input_{ingredient_name}"
        if session_key in st.session_state:
            input_data = st.session_state[session_key]
            current_input = input_data.get('current', existing_current_order)
            safety_input = input_data.get('safety', existing_safety_order)
        else:
            current_input = existing_current_order
            safety_input = existing_safety_order
        
        # 상태 계산 (세션 상태에서 가져오거나 새로 계산)
        status_key = f"inventory_status_{ingredient_name}"
        if status_key in st.session_state:
            status_text = st.session_state[status_key]
            _, status_color = _calculate_status(current_input * conversion_rate, safety_input * conversion_rate)
        else:
            current_base = current_input * conversion_rate
            safety_base = safety_input * conversion_rate
            status_text, status_color = _calculate_status(current_base, safety_base)
        
        # 단위 표시
        if order_unit != unit:
            unit_display = f"{unit} / 발주: {order_unit}"
        else:
            unit_display = unit
        
        input_data_list.append({
            '재료명': ingredient_name,
            '재료분류': category if category in INGREDIENT_CATEGORIES else "미지정",
            '단위': unit_display,
            '현재고': current_input,
            '안전재고': safety_input,
            '상태': status_text,
            '기존_현재고': existing_current_order,
            '기존_안전재고': existing_safety_order,
            '_conversion_rate': conversion_rate,
            '_unit': unit,
            '_order_unit': order_unit
        })
    
    input_df = pd.DataFrame(input_data_list)
    
    # 커스텀 테이블로 렌더링 (더블클릭 없이 바로 입력 가능)
    # 테이블 헤더
    header_cols = st.columns([3, 1.5, 2, 2, 2, 1.5, 2, 2])
    with header_cols[0]:
        st.markdown("**재료명**")
    with header_cols[1]:
        st.markdown("**재료분류**")
    with header_cols[2]:
        st.markdown("**단위**")
    with header_cols[3]:
        st.markdown("**현재고**")
    with header_cols[4]:
        st.markdown("**안전재고**")
    with header_cols[5]:
        st.markdown("**상태**")
    with header_cols[6]:
        st.markdown("**기존 현재고**")
    with header_cols[7]:
        st.markdown("**기존 안전재고**")
    
    st.markdown("---")
    
    # 각 행 렌더링
    for idx, (_, row) in enumerate(page_df.iterrows()):
        ingredient_name = row['재료명']
        unit = row.get('단위', '')
        order_unit = row.get('발주단위', unit)
        conversion_rate = float(row.get('변환비율', 1.0)) if row.get('변환비율') else 1.0
        category = categories.get(ingredient_name, "미지정")
        
        # 기존 재고 정보
        existing_inv = inventory_map.get(ingredient_name, {'current': 0, 'safety': 0})
        existing_current_base = existing_inv['current']
        existing_safety_base = existing_inv['safety']
        
        # 발주 단위로 변환
        existing_current_order = existing_current_base / conversion_rate if conversion_rate > 0 else existing_current_base
        existing_safety_order = existing_safety_base / conversion_rate if conversion_rate > 0 else existing_safety_base
        
        # 세션 상태에서 입력 데이터 가져오기
        session_key = f"inventory_input_{ingredient_name}"
        if session_key in st.session_state:
            input_data = st.session_state[session_key]
            current_input = input_data.get('current', existing_current_order)
            safety_input = input_data.get('safety', existing_safety_order)
        else:
            current_input = existing_current_order
            safety_input = existing_safety_order
        
        # 상태 계산
        status_key = f"inventory_status_{ingredient_name}"
        current_base = current_input * conversion_rate
        safety_base = safety_input * conversion_rate
        status_text, status_color = _calculate_status(current_base, safety_base)
        
        # 단위 표시
        if order_unit != unit:
            unit_display = f"{unit}<br><small>(발주: {order_unit})</small>"
        else:
            unit_display = unit
        
        # 재료 분류 뱃지 색상
        category_colors = {
            "채소": "#22C55E",
            "육류": "#EF4444",
            "해산물": "#3B82F6",
            "조미료": "#EAB308",
            "기타": "#9CA3AF",
            "미지정": "#6B7280"
        }
        category_color = category_colors.get(category, "#6B7280")
        display_category = category if category in INGREDIENT_CATEGORIES else "미지정"
        
        # 행 렌더링
        row_cols = st.columns([3, 1.5, 2, 2, 2, 1.5, 2, 2])
        
        with row_cols[0]:
            st.markdown(f"**{ingredient_name}**")
        with row_cols[1]:
            st.markdown(f'<span style="background: {category_color}; padding: 0.2rem 0.5rem; border-radius: 4px; color: white; font-size: 0.8rem;">{display_category}</span>', 
                       unsafe_allow_html=True)
        with row_cols[2]:
            st.markdown(unit_display, unsafe_allow_html=True)
        with row_cols[3]:
            # 현재고 입력 (클릭 한 번으로 바로 입력 가능)
            new_current = st.number_input(
                "",
                min_value=0.0,
                value=float(current_input),
                step=0.1,
                format="%.2f",
                key=f"inventory_current_{ingredient_name}_{current_page}",
                label_visibility="collapsed"
            )
        with row_cols[4]:
            # 안전재고 입력 (클릭 한 번으로 바로 입력 가능)
            new_safety = st.number_input(
                "",
                min_value=0.0,
                value=float(safety_input),
                step=0.1,
                format="%.2f",
                key=f"inventory_safety_{ingredient_name}_{current_page}",
                label_visibility="collapsed"
            )
        with row_cols[5]:
            st.markdown(f'<span style="color: {status_color}; font-weight: 600;">{status_text}</span>', 
                       unsafe_allow_html=True)
        with row_cols[6]:
            st.markdown(f"{existing_current_order:.2f}")
        with row_cols[7]:
            st.markdown(f"{existing_safety_order:.2f}")
        
        # 변경 감지 및 세션 상태 저장
        if abs(new_current - current_input) > 0.01 or abs(new_safety - safety_input) > 0.01:
            # 세션 상태에 저장
            st.session_state[session_key] = {
                'current': float(new_current),
                'safety': float(new_safety)
            }
            
            # 상태 재계산
            new_current_base = new_current * conversion_rate
            new_safety_base = new_safety * conversion_rate
            new_status_text, _ = _calculate_status(new_current_base, new_safety_base)
            st.session_state[status_key] = new_status_text
            
            # 변경 표시를 위해 세션 상태 업데이트
            if 'inventory_changed_items' not in st.session_state:
                st.session_state['inventory_changed_items'] = set()
            st.session_state['inventory_changed_items'].add(ingredient_name)
        
        st.markdown("---")




def _render_zone_c_save_validation(store_id, filtered_ingredient_df, full_ingredient_df, inventory_map):
    """ZONE C: 저장 & 검증"""
    render_section_header("💾 저장 & 검증", "💾")
    
    # 변경된 항목 수집
    changed_items = {}
    if 'inventory_changed_items' in st.session_state:
        for ingredient_name in st.session_state['inventory_changed_items']:
            session_key = f"inventory_input_{ingredient_name}"
            if session_key in st.session_state:
                changed_items[ingredient_name] = st.session_state[session_key]
    
    # 변경된 항목 표시
    if changed_items:
        st.info(f"**변경된 항목: {len(changed_items)}개**")
        
        # 변경된 항목 목록
        with st.expander("변경된 항목 목록 보기"):
            for ingredient_name in list(changed_items.keys())[:10]:  # 최대 10개만 표시
                st.write(f"- {ingredient_name}")
            if len(changed_items) > 10:
                st.write(f"... 외 {len(changed_items) - 10}개")
    else:
        st.info("변경된 항목이 없습니다.")
    
    # 저장 버튼
    col_save, col_cancel = st.columns([1, 1])
    with col_save:
        if st.button("💾 변경된 항목 저장", type="primary", key="inventory_save_changed", use_container_width=True):
            if not changed_items:
                ui_flash_error("저장할 변경 사항이 없습니다.")
            else:
                _save_changed_items(store_id, changed_items, full_ingredient_df)
    
    with col_cancel:
        if st.button("🔄 초기화", key="inventory_reset_changes", use_container_width=True):
            if 'inventory_changed_items' in st.session_state:
                for ingredient_name in st.session_state['inventory_changed_items']:
                    session_key = f"inventory_input_{ingredient_name}"
                    if session_key in st.session_state:
                        del st.session_state[session_key]
                del st.session_state['inventory_changed_items']
            st.rerun()
    
    # 전체 저장 버튼 (ZONE A에서 트리거된 경우)
    if st.session_state.get('inventory_save_trigger', False):
        st.session_state['inventory_save_trigger'] = False
        _save_all_items(store_id, filtered_ingredient_df, full_ingredient_df, inventory_map)
    
    # 기존 재고 불러오기 (ZONE A에서 트리거된 경우)
    if st.session_state.get('inventory_load_existing', False):
        st.session_state['inventory_load_existing'] = False
        _load_existing_inventory(filtered_ingredient_df, inventory_map, full_ingredient_df)


def _save_changed_items(store_id, changed_items, full_ingredient_df):
    """변경된 항목만 저장"""
    if not changed_items:
        return
    
    try:
        saved_count = 0
        failed_items = []
        
        # 재료 정보 매핑 생성
        ingredient_info_map = {}
        for _, row in full_ingredient_df.iterrows():
            ingredient_name = row['재료명']
            conversion_rate = float(row.get('변환비율', 1.0)) if row.get('변환비율') else 1.0
            ingredient_info_map[ingredient_name] = {
                'conversion_rate': conversion_rate
            }
        
        for ingredient_name, input_data in changed_items.items():
            try:
                # 발주 단위 → 기본 단위 변환
                conversion_rate = ingredient_info_map.get(ingredient_name, {}).get('conversion_rate', 1.0)
                current_stock = input_data['current'] * conversion_rate
                safety_stock = input_data['safety'] * conversion_rate
                
                # 저장
                success = save_inventory(ingredient_name, current_stock, safety_stock)
                if success:
                    saved_count += 1
                    # 세션 상태에서 제거
                    session_key = f"inventory_input_{ingredient_name}"
                    if session_key in st.session_state:
                        del st.session_state[session_key]
                else:
                    failed_items.append(f"{ingredient_name}: 저장 실패")
            except Exception as e:
                logger.error(f"재고 저장 중 예외 발생 ({ingredient_name}): {e}")
                failed_items.append(f"{ingredient_name}: {str(e)}")
        
        # 변경된 항목 목록 초기화
        if 'inventory_changed_items' in st.session_state:
            del st.session_state['inventory_changed_items']
        
        if saved_count > 0:
            if failed_items:
                ui_flash_success(f"{saved_count}개 재고가 저장되었습니다. ({len(failed_items)}개 실패)")
                for failed in failed_items:
                    st.warning(failed)
            else:
                ui_flash_success(f"{saved_count}개 재고가 모두 저장되었습니다.")
            st.rerun()
        else:
            ui_flash_error(f"저장에 실패했습니다. {len(failed_items)}개 재고 모두 저장 실패.")
            for failed in failed_items:
                st.error(failed)
    except Exception as e:
        logger.error(f"일괄 저장 중 예외 발생: {e}")
        ui_flash_error(f"저장 실패: {str(e)}")


def _save_all_items(store_id, filtered_ingredient_df, full_ingredient_df, inventory_map):
    """전체 항목 저장 (현재 페이지의 모든 항목)"""
    try:
        # 현재 페이지의 모든 항목 수집
        current_page = st.session_state.get('inventory_page', 1)
        start_idx = (current_page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        page_df = filtered_ingredient_df.iloc[start_idx:end_idx]
        
        saved_count = 0
        failed_items = []
        
        # 재료 정보 매핑 생성
        ingredient_info_map = {}
        for _, row in full_ingredient_df.iterrows():
            ingredient_name = row['재료명']
            conversion_rate = float(row.get('변환비율', 1.0)) if row.get('변환비율') else 1.0
            ingredient_info_map[ingredient_name] = {
                'conversion_rate': conversion_rate
            }
        
        for _, row in page_df.iterrows():
            ingredient_name = row['재료명']
            
            # 세션 상태에서 입력 데이터 가져오기
            session_key = f"inventory_input_{ingredient_name}"
            if session_key in st.session_state:
                input_data = st.session_state[session_key]
                current_input = input_data['current']
                safety_input = input_data['safety']
            else:
                # 기존 재고 정보 사용
                existing_inv = inventory_map.get(ingredient_name, {'current': 0, 'safety': 0})
                conversion_rate = ingredient_info_map.get(ingredient_name, {}).get('conversion_rate', 1.0)
                current_input = existing_inv['current'] / conversion_rate if conversion_rate > 0 else existing_inv['current']
                safety_input = existing_inv['safety'] / conversion_rate if conversion_rate > 0 else existing_inv['safety']
            
            try:
                # 발주 단위 → 기본 단위 변환
                conversion_rate = ingredient_info_map.get(ingredient_name, {}).get('conversion_rate', 1.0)
                current_stock = current_input * conversion_rate
                safety_stock = safety_input * conversion_rate
                
                # 저장
                success = save_inventory(ingredient_name, current_stock, safety_stock)
                if success:
                    saved_count += 1
                    # 세션 상태에서 제거
                    if session_key in st.session_state:
                        del st.session_state[session_key]
                else:
                    failed_items.append(f"{ingredient_name}: 저장 실패")
            except Exception as e:
                logger.error(f"재고 저장 중 예외 발생 ({ingredient_name}): {e}")
                failed_items.append(f"{ingredient_name}: {str(e)}")
        
        # 변경된 항목 목록 초기화
        if 'inventory_changed_items' in st.session_state:
            del st.session_state['inventory_changed_items']
        
        if saved_count > 0:
            if failed_items:
                ui_flash_success(f"{saved_count}개 재고가 저장되었습니다. ({len(failed_items)}개 실패)")
                for failed in failed_items:
                    st.warning(failed)
            else:
                ui_flash_success(f"{saved_count}개 재고가 모두 저장되었습니다.")
            st.rerun()
        else:
            ui_flash_error(f"저장에 실패했습니다. {len(failed_items)}개 재고 모두 저장 실패.")
            for failed in failed_items:
                st.error(failed)
    except Exception as e:
        logger.error(f"전체 저장 중 예외 발생: {e}")
        ui_flash_error(f"저장 실패: {str(e)}")


def _load_existing_inventory(filtered_ingredient_df, inventory_map, full_ingredient_df):
    """기존 재고 정보 불러오기"""
    try:
        current_page = st.session_state.get('inventory_page', 1)
        start_idx = (current_page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        page_df = filtered_ingredient_df.iloc[start_idx:end_idx]
        
        loaded_count = 0
        
        for _, row in page_df.iterrows():
            ingredient_name = row['재료명']
            
            # 기존 재고 정보 가져오기
            existing_inv = inventory_map.get(ingredient_name, {'current': 0, 'safety': 0})
            if existing_inv['current'] > 0 or existing_inv['safety'] > 0:
                # 발주 단위로 변환
                conversion_rate = float(row.get('변환비율', 1.0)) if row.get('변환비율') else 1.0
                current_order = existing_inv['current'] / conversion_rate if conversion_rate > 0 else existing_inv['current']
                safety_order = existing_inv['safety'] / conversion_rate if conversion_rate > 0 else existing_inv['safety']
                
                # 세션 상태에 저장
                session_key = f"inventory_input_{ingredient_name}"
                st.session_state[session_key] = {
                    'current': float(current_order),
                    'safety': float(safety_order)
                }
                loaded_count += 1
        
        if loaded_count > 0:
            ui_flash_success(f"{loaded_count}개 재고 정보를 불러왔습니다.")
            st.rerun()
        else:
            ui_flash_error("불러올 재고 정보가 없습니다.")
    except Exception as e:
        logger.error(f"기존 재고 불러오기 중 예외 발생: {e}")
        ui_flash_error(f"불러오기 실패: {str(e)}")
