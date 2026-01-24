"""
판매 메뉴 입력 페이지 (입력 전용)
재기획안에 따른 5-Zone 구조
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
import logging
from src.ui_helpers import render_page_header, ui_flash_success, ui_flash_error, render_section_header
from src.storage_supabase import load_csv, save_menu, update_menu, update_menu_category, delete_menu
from src.auth import get_current_store_id, get_supabase_client
from src.analytics import calculate_menu_cost
from ui_pages.design_lab.menu_portfolio_helpers import (
    get_menu_portfolio_tags,
    set_menu_portfolio_tag,
    get_menu_portfolio_categories,
    set_menu_portfolio_category,
)

logger = logging.getLogger(__name__)

# 공통 설정 적용
bootstrap(page_title="판매 메뉴 입력")

# 메뉴분류 옵션
MENU_CATEGORIES = ["대표메뉴", "주력메뉴", "유인메뉴", "보조메뉴", "기타메뉴"]
MENU_STATUSES = ["판매중", "판매중지"]
ROLE_TAGS = ["미끼", "볼륨", "마진"]


def render_menu_input_page():
    """판매 메뉴 입력 페이지 렌더링 (5-Zone 구조)"""
    render_page_header("메뉴 입력", "📘")
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    # 데이터 로드
    menu_df = load_csv('menu_master.csv', store_id=store_id, default_columns=['메뉴명', '판매가'])
    categories = get_menu_portfolio_categories(store_id)
    roles = get_menu_portfolio_tags(store_id)
    
    # 레시피 및 원가 정보 로드
    recipe_df = load_csv('recipes.csv', store_id=store_id, default_columns=['메뉴명', '재료명', '사용량'])
    ingredient_df = load_csv('ingredient_master.csv', store_id=store_id, default_columns=['재료명', '단위', '단가'])
    
    # 원가 계산 (레시피 있는 메뉴만)
    menu_cost_df = pd.DataFrame()
    if not menu_df.empty and not recipe_df.empty and not ingredient_df.empty:
        try:
            menu_cost_df = calculate_menu_cost(menu_df, recipe_df, ingredient_df)
        except Exception as e:
            logger.warning(f"원가 계산 실패: {e}")
    
    # 레시피 상태 확인
    menu_has_recipe = {}
    if not recipe_df.empty:
        menu_has_recipe = {menu: True for menu in recipe_df['메뉴명'].unique()}
    
    # ============================================
    # ZONE A: 대시보드 & 현황 요약
    # ============================================
    _render_zone_a_dashboard(menu_df, categories, roles, menu_has_recipe)
    
    st.markdown("---")
    
    # ============================================
    # ZONE B: 메뉴 입력 (단일/일괄)
    # ============================================
    _render_zone_b_input(store_id)
    
    st.markdown("---")
    
    # ============================================
    # ZONE C: 필터 & 검색
    # ============================================
    filtered_menu_df = _render_zone_c_filters(menu_df, categories, roles, menu_has_recipe)
    
    st.markdown("---")
    
    # ============================================
    # ZONE D: 메뉴 목록 & 관리
    # ============================================
    _render_zone_d_menu_list(filtered_menu_df, categories, roles, menu_has_recipe, menu_cost_df, store_id)
    
    st.markdown("---")
    
    # ============================================
    # ZONE E: 메뉴분류 & 해시태그 관리
    # ============================================
    _render_zone_e_management(menu_df, categories, roles, store_id)


def _render_zone_a_dashboard(menu_df, categories, roles, menu_has_recipe):
    """ZONE A: 대시보드 & 현황 요약"""
    render_section_header("📊 메뉴 현황 대시보드", "📊")
    
    if menu_df.empty:
        st.info("등록된 메뉴가 없습니다. 아래에서 메뉴를 등록해주세요.")
        return
    
    total_menus = len(menu_df)
    menus_with_recipe = sum(1 for name in menu_df['메뉴명'] if menu_has_recipe.get(name, False))
    menus_with_category = sum(1 for name in menu_df['메뉴명'] if categories.get(name) and categories.get(name) != "미지정")
    menus_with_role = sum(1 for name in menu_df['메뉴명'] if roles.get(name) and roles.get(name) != "미분류")
    menus_on_sale = total_menus  # 기본값 (status 필드 추가 전)
    
    # 핵심 지표 카드
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("전체 메뉴", f"{total_menus}개")
    with col2:
        st.metric("판매중 메뉴", f"{menus_on_sale}개")
    with col3:
        recipe_completion = (menus_with_recipe / total_menus * 100) if total_menus > 0 else 0
        st.metric("레시피 완성도", f"{menus_with_recipe}개", delta=f"{recipe_completion:.0f}%")
    
    # 진행률 바
    st.markdown("### 진행률")
    category_rate = (menus_with_category / total_menus * 100) if total_menus > 0 else 0
    role_rate = (menus_with_role / total_menus * 100) if total_menus > 0 else 0
    
    st.progress(recipe_completion / 100, text=f"레시피 완성도: {recipe_completion:.0f}%")
    st.progress(category_rate / 100, text=f"메뉴분류 지정률: {category_rate:.0f}%")
    st.progress(role_rate / 100, text=f"해시태그 분류 지정률: {role_rate:.0f}%")
    
    # 스마트 알림
    alerts = []
    if menus_with_recipe < total_menus:
        alerts.append(f"⚠️ 레시피가 없는 메뉴가 {total_menus - menus_with_recipe}개 있습니다.")
    if menus_with_category < total_menus:
        alerts.append(f"ℹ️ 메뉴분류가 미지정인 메뉴가 {total_menus - menus_with_category}개 있습니다.")
    if menus_with_role < total_menus:
        alerts.append(f"ℹ️ 해시태그 분류가 미지정인 메뉴가 {total_menus - menus_with_role}개 있습니다.")
    
    if alerts:
        for alert in alerts:
            st.info(alert)


def _render_zone_b_input(store_id):
    """ZONE B: 메뉴 입력 (단일/일괄)"""
    render_section_header("📝 메뉴 입력", "📝")
    
    tab1, tab2 = st.tabs(["📝 단일 입력", "📋 일괄 입력"])
    
    with tab1:
        _render_single_input(store_id)
    
    with tab2:
        _render_batch_input(store_id)


def _render_single_input(store_id):
    """단일 메뉴 입력"""
    st.markdown("### 📝 메뉴 단일 등록")
    
    col1, col2 = st.columns(2)
    with col1:
        menu_name = st.text_input("메뉴명 *", key="single_menu_name", placeholder="메뉴명을 입력하세요")
    with col2:
        price = st.number_input("판매가 (원) *", min_value=0, value=0, step=1000, key="single_menu_price")
    
    col3, col4, col5 = st.columns(3)
    with col3:
        category = st.selectbox("메뉴분류", options=[""] + MENU_CATEGORIES, key="single_menu_category")
    with col4:
        status = st.selectbox("상태", options=MENU_STATUSES, index=0, key="single_menu_status")
    with col5:
        role_tags = st.multiselect("해시태그 분류", options=ROLE_TAGS, key="single_menu_roles")
    
    notes = st.text_area("메모 (선택)", key="single_menu_notes", height=100)
    
    col_save, col_reset = st.columns([1, 1])
    with col_save:
        if st.button("💾 저장", type="primary", key="single_save", use_container_width=True):
            if not menu_name or not menu_name.strip():
                ui_flash_error("메뉴명을 입력해주세요.")
            elif price <= 0:
                ui_flash_error("판매가를 입력해주세요.")
            else:
                try:
                    # 메뉴 저장
                    success, msg = save_menu(menu_name.strip(), int(price))
                    if not success:
                        ui_flash_error(msg)
                    else:
                        # 메뉴분류 저장
                        if category:
                            set_menu_portfolio_category(store_id, menu_name.strip(), category)
                        
                        # 해시태그 분류 저장 (첫 번째 것만, 향후 멀티 지원)
                        if role_tags:
                            set_menu_portfolio_tag(store_id, menu_name.strip(), role_tags[0])
                        
                        ui_flash_success(f"메뉴 '{menu_name.strip()}'이(가) 저장되었습니다.")
                        st.rerun()
                except Exception as e:
                    ui_flash_error(f"저장 실패: {str(e)}")
    
    with col_reset:
        if st.button("🔄 초기화", key="single_reset", use_container_width=True):
            st.rerun()


def _render_batch_input(store_id):
    """일괄 메뉴 입력"""
    st.markdown("### 📋 메뉴 일괄 등록")
    
    menu_count = st.number_input("등록할 메뉴 개수", min_value=1, max_value=20, value=5, step=1, key="batch_menu_count")
    
    # 일괄 선택 옵션
    col_batch1, col_batch2, col_batch3 = st.columns(3)
    with col_batch1:
        batch_category = st.selectbox("일괄 메뉴분류", options=[""] + MENU_CATEGORIES, key="batch_category")
    with col_batch2:
        batch_status = st.selectbox("일괄 상태", options=[""] + MENU_STATUSES, key="batch_status")
    with col_batch3:
        batch_roles = st.multiselect("일괄 해시태그 분류", options=ROLE_TAGS, key="batch_roles")
    
    st.markdown("---")
    st.write(f"**📋 총 {menu_count}개 메뉴 입력**")
    
    menu_data = []
    for i in range(menu_count):
        with st.expander(f"메뉴 {i+1}", expanded=(i < 3)):
            col1, col2 = st.columns([3, 2])
            with col1:
                menu_name = st.text_input(f"메뉴명 {i+1}", key=f"batch_menu_name_{i}")
            with col2:
                price = st.number_input(f"판매가 (원) {i+1}", min_value=0, value=0, step=1000, key=f"batch_menu_price_{i}")
            
            col3, col4 = st.columns(2)
            with col3:
                category = st.selectbox(f"메뉴분류 {i+1}", options=[""] + MENU_CATEGORIES, 
                                       index=MENU_CATEGORIES.index(batch_category) + 1 if batch_category in MENU_CATEGORIES else 0,
                                       key=f"batch_category_{i}")
            with col4:
                status = st.selectbox(f"상태 {i+1}", options=MENU_STATUSES,
                                     index=MENU_STATUSES.index(batch_status) if batch_status in MENU_STATUSES else 0,
                                     key=f"batch_status_{i}")
            
            roles = st.multiselect(f"해시태그 분류 {i+1}", options=ROLE_TAGS, default=batch_roles, key=f"batch_roles_{i}")
            
            if menu_name and menu_name.strip() and price > 0:
                menu_data.append({
                    'name': menu_name.strip(),
                    'price': int(price),
                    'category': category if category else None,
                    'status': status,
                    'roles': roles
                })
    
    if st.button("💾 일괄 저장", type="primary", key="batch_save", use_container_width=True):
        if not menu_data:
            ui_flash_error("저장할 메뉴가 없습니다. 메뉴명과 판매가를 입력해주세요.")
        else:
            try:
                saved_count = 0
                for menu in menu_data:
                    success, msg = save_menu(menu['name'], menu['price'])
                    if success:
                        if menu['category']:
                            set_menu_portfolio_category(store_id, menu['name'], menu['category'])
                        if menu['roles']:
                            set_menu_portfolio_tag(store_id, menu['name'], menu['roles'][0])
                        saved_count += 1
                ui_flash_success(f"{saved_count}개 메뉴가 저장되었습니다.")
                st.rerun()
            except Exception as e:
                ui_flash_error(f"저장 실패: {str(e)}")


def _render_zone_c_filters(menu_df, categories, roles, menu_has_recipe):
    """ZONE C: 필터 & 검색"""
    render_section_header("🔍 필터 & 검색", "🔍")
    
    if menu_df.empty:
        return menu_df
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        category_filter = st.multiselect("메뉴분류", options=["전체"] + MENU_CATEGORIES + ["미지정"], 
                                         default=["전체"], key="filter_category")
    with col2:
        role_filter = st.multiselect("해시태그 분류", options=["전체"] + ROLE_TAGS + ["미분류"],
                                     default=["전체"], key="filter_role")
    with col3:
        status_filter = st.selectbox("상태", options=["전체"] + MENU_STATUSES, key="filter_status")
    with col4:
        recipe_filter = st.selectbox("레시피 상태", options=["전체", "레시피 있음", "레시피 없음"], key="filter_recipe")
    
    # 검색
    search_term = st.text_input("🔍 메뉴명 검색", key="menu_search", placeholder="메뉴명으로 검색...")
    
    # 필터링 적용
    filtered_df = menu_df.copy()
    
    # 메뉴분류 필터
    if "전체" not in category_filter:
        def category_match(name):
            cat = categories.get(name, "미지정")
            if "미지정" in category_filter:
                return cat == "미지정" or cat not in MENU_CATEGORIES
            return cat in category_filter
        filtered_df = filtered_df[filtered_df['메뉴명'].apply(category_match)]
    
    # 해시태그 분류 필터
    if "전체" not in role_filter:
        def role_match(name):
            role = roles.get(name, "미분류")
            if "미분류" in role_filter:
                return role == "미분류" or role not in ROLE_TAGS
            return role in role_filter
        filtered_df = filtered_df[filtered_df['메뉴명'].apply(role_match)]
    
    # 레시피 상태 필터
    if recipe_filter == "레시피 있음":
        filtered_df = filtered_df[filtered_df['메뉴명'].isin(menu_has_recipe.keys())]
    elif recipe_filter == "레시피 없음":
        filtered_df = filtered_df[~filtered_df['메뉴명'].isin(menu_has_recipe.keys())]
    
    # 검색 필터
    if search_term and search_term.strip():
        filtered_df = filtered_df[filtered_df['메뉴명'].str.contains(search_term, case=False, na=False)]
    
    return filtered_df


def _render_zone_d_menu_list(menu_df, categories, roles, menu_has_recipe, menu_cost_df, store_id):
    """ZONE D: 메뉴 목록 & 관리"""
    render_section_header("📋 메뉴 목록 & 관리", "📋")
    
    if menu_df.empty:
        st.info("등록된 메뉴가 없습니다.")
        return
    
    # 선택된 메뉴 (일괄 작업용)
    if 'selected_menus' not in st.session_state:
        st.session_state.selected_menus = set()
    
    # 목록 표시
    st.markdown("### 메뉴 목록")
    
    for idx, row in menu_df.iterrows():
        menu_name = row['메뉴명']
        price = int(row['판매가'])
        category = categories.get(menu_name, "미지정")
        role = roles.get(menu_name, "미분류")
        has_recipe = menu_has_recipe.get(menu_name, False)
        
        # 원가 정보
        cost = 0
        cost_rate = 0
        if not menu_cost_df.empty:
            cost_row = menu_cost_df[menu_cost_df['메뉴명'] == menu_name]
            if not cost_row.empty:
                cost = int(cost_row.iloc[0]['원가']) if '원가' in cost_row.columns else 0
                cost_rate = float(cost_row.iloc[0]['원가율']) if '원가율' in cost_row.columns else 0
        
        # 카드 형태로 표시
        with st.container():
            col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 2, 2, 2, 2, 2, 3])
            
            with col1:
                st.markdown(f"**{menu_name}**")
            with col2:
                # 메뉴분류 뱃지
                category_colors = {
                    "대표메뉴": "#FFD700",
                    "주력메뉴": "#3B82F6",
                    "유인메뉴": "#EAB308",
                    "보조메뉴": "#9CA3AF",
                    "기타메뉴": "#86EFAC",
                    "미지정": "#6B7280"
                }
                color = category_colors.get(category, "#6B7280")
                display_category = category if category in MENU_CATEGORIES else "미지정"
                st.markdown(f'<span style="background: {color}; padding: 0.2rem 0.5rem; border-radius: 4px; color: white; font-size: 0.8rem;">{display_category}</span>', 
                           unsafe_allow_html=True)
            with col3:
                # 해시태그 분류 뱃지
                role_colors = {"미끼": "#FB923C", "볼륨": "#22C55E", "마진": "#A855F7", "미분류": "#6B7280"}
                role_color = role_colors.get(role, "#6B7280")
                display_role = role if role in ROLE_TAGS else "미분류"
                st.markdown(f'<span style="background: {role_color}; padding: 0.2rem 0.5rem; border-radius: 4px; color: white; font-size: 0.8rem;">{display_role}</span>', 
                           unsafe_allow_html=True)
            with col4:
                st.markdown(f"{price:,}원")
            with col5:
                if has_recipe and cost > 0:
                    st.markdown(f"{cost:,}원")
                else:
                    st.markdown("-")
            with col6:
                if has_recipe and cost_rate > 0:
                    color = "#EF4444" if cost_rate >= 40 else "#22C55E"
                    st.markdown(f'<span style="color: {color};">{cost_rate:.1f}%</span>', unsafe_allow_html=True)
                else:
                    st.markdown("-")
            with col7:
                # 액션 버튼
                action_col1, action_col2, action_col3 = st.columns(3)
                with action_col1:
                    if st.button("✏️", key=f"edit_{menu_name}", help="수정"):
                        st.session_state[f"edit_menu_{menu_name}"] = True
                with action_col2:
                    if st.button("🗑️", key=f"delete_{menu_name}", help="삭제"):
                        st.session_state[f"delete_menu_{menu_name}"] = True
                with action_col3:
                    if not has_recipe:
                        if st.button("🧑‍🍳", key=f"recipe_{menu_name}", help="레시피 입력", type="primary"):
                            st.session_state["current_page"] = "레시피 입력"
                            st.session_state["selected_menu"] = menu_name
                            st.rerun()
                    else:
                        st.markdown("✅")
            
            # 수정 모달
            if st.session_state.get(f"edit_menu_{menu_name}", False):
                with st.expander(f"✏️ {menu_name} 수정", expanded=True):
                    new_name = st.text_input("메뉴명", value=menu_name, key=f"edit_name_{menu_name}")
                    new_price = st.number_input("판매가 (원)", min_value=0, value=price, step=1000, key=f"edit_price_{menu_name}")
                    new_category = st.selectbox("메뉴분류", options=[""] + MENU_CATEGORIES,
                                               index=MENU_CATEGORIES.index(category) + 1 if category in MENU_CATEGORIES else 0,
                                               key=f"edit_category_{menu_name}")
                    new_role = st.selectbox("해시태그 분류", options=[""] + ROLE_TAGS,
                                           index=ROLE_TAGS.index(role) + 1 if role in ROLE_TAGS else 0,
                                           key=f"edit_role_{menu_name}")
                    
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.button("💾 저장", key=f"save_edit_{menu_name}"):
                            try:
                                success, msg = update_menu(menu_name, new_name, new_price, new_category if new_category else None)
                                if success:
                                    if new_category:
                                        set_menu_portfolio_category(store_id, new_name, new_category)
                                    if new_role:
                                        set_menu_portfolio_tag(store_id, new_name, new_role)
                                    ui_flash_success(f"메뉴 '{new_name}'이(가) 수정되었습니다.")
                                    st.session_state[f"edit_menu_{menu_name}"] = False
                                    st.rerun()
                                else:
                                    ui_flash_error(msg)
                            except Exception as e:
                                ui_flash_error(f"수정 실패: {str(e)}")
                    with col_cancel:
                        if st.button("취소", key=f"cancel_edit_{menu_name}"):
                            st.session_state[f"edit_menu_{menu_name}"] = False
                            st.rerun()
            
            # 삭제 확인
            if st.session_state.get(f"delete_menu_{menu_name}", False):
                st.warning(f"'{menu_name}' 메뉴를 삭제하시겠습니까?")
                col_del, col_cancel = st.columns(2)
                with col_del:
                    if st.button("🗑️ 삭제", key=f"confirm_delete_{menu_name}", type="primary"):
                        try:
                            success, msg = delete_menu(menu_name)
                            if success:
                                ui_flash_success(f"메뉴 '{menu_name}'이(가) 삭제되었습니다.")
                                st.session_state[f"delete_menu_{menu_name}"] = False
                                st.rerun()
                            else:
                                ui_flash_error(msg)
                        except Exception as e:
                            ui_flash_error(f"삭제 실패: {str(e)}")
                with col_cancel:
                    if st.button("취소", key=f"cancel_delete_{menu_name}"):
                        st.session_state[f"delete_menu_{menu_name}"] = False
                        st.rerun()
            
            st.markdown("---")


def _render_zone_e_management(menu_df, categories, roles, store_id):
    """ZONE E: 메뉴분류 & 해시태그 관리"""
    render_section_header("📊 메뉴분류 & 해시태그 관리", "📊")
    
    if menu_df.empty:
        st.info("등록된 메뉴가 없습니다.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 메뉴분류 현황")
        category_counts = {}
        for category in MENU_CATEGORIES:
            count = sum(1 for name in menu_df['메뉴명'] if categories.get(name) == category)
            category_counts[category] = count
        
        for category, count in category_counts.items():
            st.metric(category, f"{count}개")
        
        if st.button("💡 메뉴 포트폴리오 설계실로 이동", key="go_to_portfolio"):
            st.session_state["current_page"] = "메뉴 등록"
            st.rerun()
    
    with col2:
        st.markdown("### 해시태그 분류 현황")
        role_counts = {}
        for role in ROLE_TAGS:
            count = sum(1 for name in menu_df['메뉴명'] if roles.get(name) == role)
            role_counts[role] = count
        
        for role, count in role_counts.items():
            st.metric(role, f"{count}개")
        
        st.info("💡 해시태그 분류는 메뉴 포트폴리오 설계실에서도 관리할 수 있습니다.")
