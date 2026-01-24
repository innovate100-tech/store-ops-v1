"""
사용 재료 입력 페이지 (입력 전용)
재기획안에 따른 5-Zone 구조
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
import logging
from datetime import datetime, timedelta
from src.ui_helpers import render_page_header, ui_flash_success, ui_flash_error, render_section_header
from src.storage_supabase import load_csv, save_ingredient, update_ingredient, delete_ingredient
from src.auth import get_current_store_id, get_supabase_client
from src.analytics import calculate_ingredient_usage, calculate_order_recommendation

logger = logging.getLogger(__name__)

# 공통 설정 적용
bootstrap(page_title="사용 재료 입력")

# 재료 분류 옵션
INGREDIENT_CATEGORIES = ["채소", "육류", "해산물", "조미료", "기타"]
INGREDIENT_STATUSES = ["사용중", "사용중지"]
UNIT_OPTIONS = ["g", "ml", "ea", "개", "kg", "L", "박스", "봉지"]


def render_ingredient_input_page():
    """사용 재료 입력 페이지 렌더링 (5-Zone 구조)"""
    render_page_header("🧺 사용 재료 입력", "🧺")
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    # 데이터 로드
    ingredient_df = load_csv('ingredient_master.csv', store_id=store_id, 
                            default_columns=['재료명', '단위', '단가', '발주단위', '변환비율'])
    
    # 재료 분류 로드 (DB에서)
    categories = _get_ingredient_categories(store_id, ingredient_df)
    
    # 레시피 및 사용량 정보 로드
    recipe_df = load_csv('recipes.csv', store_id=store_id, default_columns=['메뉴명', '재료명', '사용량'])
    daily_sales_df = load_csv('daily_sales_items.csv', store_id=store_id, 
                              default_columns=['날짜', '메뉴명', '판매수량'])
    inventory_df = load_csv('inventory.csv', store_id=store_id, 
                           default_columns=['재료명', '현재고', '안전재고'])
    
    # 레시피 사용 여부 확인
    ingredient_in_recipe = {}
    if not recipe_df.empty:
        ingredient_in_recipe = {ing: True for ing in recipe_df['재료명'].unique()}
    
    # 사용량 계산 (최근 7일)
    usage_df = pd.DataFrame()
    recent_usage = {}
    if not daily_sales_df.empty and not recipe_df.empty:
        try:
            usage_df = calculate_ingredient_usage(daily_sales_df, recipe_df)
            if not usage_df.empty:
                # 최근 7일 데이터만
                usage_df['날짜'] = pd.to_datetime(usage_df['날짜'])
                max_date = usage_df['날짜'].max()
                recent_cutoff = max_date - timedelta(days=7)
                recent_usage_df = usage_df[usage_df['날짜'] >= recent_cutoff]
                
                if not recent_usage_df.empty:
                    # 재료별 최근 7일 평균 사용량
                    daily_avg = recent_usage_df.groupby('재료명')['총사용량'].sum() / 7
                    recent_usage = daily_avg.to_dict()
        except Exception as e:
            logger.warning(f"사용량 계산 실패: {e}")
    
    # 발주 필요 여부 확인
    needs_order = {}
    if not ingredient_df.empty and not inventory_df.empty:
        try:
            order_recommendation = calculate_order_recommendation(
                ingredient_df, inventory_df, usage_df, days_for_avg=7, forecast_days=3
            )
            if not order_recommendation.empty:
                needs_order = {row['재료명']: True for _, row in order_recommendation.iterrows()}
        except Exception as e:
            logger.warning(f"발주 추천 계산 실패: {e}")
    
    # ============================================
    # ZONE A: 대시보드 & 현황 요약
    # ============================================
    _render_zone_a_dashboard(ingredient_df, categories, ingredient_in_recipe, needs_order)
    
    st.markdown("---")
    
    # ============================================
    # ZONE B: 재료 입력 (단일/일괄)
    # ============================================
    _render_zone_b_input(store_id)
    
    st.markdown("---")
    
    # ============================================
    # ZONE C: 필터 & 검색
    # ============================================
    filtered_ingredient_df = _render_zone_c_filters(ingredient_df, categories, ingredient_in_recipe, needs_order)
    
    st.markdown("---")
    
    # ============================================
    # ZONE D: 재료 목록 & 관리
    # ============================================
    _render_zone_d_ingredient_list(filtered_ingredient_df, categories, ingredient_in_recipe, 
                                    recent_usage, needs_order, store_id)
    
    st.markdown("---")
    
    # ============================================
    # ZONE E: 재료 분류 & 통계 관리
    # ============================================
    _render_zone_e_management(ingredient_df, categories, ingredient_in_recipe, recent_usage, store_id)


def _get_ingredient_categories(store_id, ingredient_df):
    """재료 분류 조회 (DB에서)"""
    categories = {}
    if ingredient_df.empty:
        return categories
    
    # DB에서 category 필드 확인
    supabase = get_supabase_client()
    if supabase:
        try:
            result = supabase.table("ingredients")\
                .select("name,category")\
                .eq("store_id", store_id)\
                .execute()
            
            if result.data:
                for row in result.data:
                    if row.get('category'):
                        categories[row['name']] = row['category']
        except Exception as e:
            logger.warning(f"재료 분류 조회 실패: {e}")
    
    return categories


def _set_ingredient_category(store_id, ingredient_name, category):
    """재료 분류 저장 (DB)"""
    supabase = get_supabase_client()
    if not supabase:
        return False
    
    try:
        # 재료 ID 찾기
        result = supabase.table("ingredients")\
            .select("id")\
            .eq("store_id", store_id)\
            .eq("name", ingredient_name)\
            .execute()
        
        if result.data:
            ingredient_id = result.data[0]['id']
            supabase.table("ingredients")\
                .update({"category": category})\
                .eq("id", ingredient_id)\
                .execute()
            return True
    except Exception as e:
        logger.warning(f"재료 분류 저장 실패: {e}")
    
    return False


def _render_zone_a_dashboard(ingredient_df, categories, ingredient_in_recipe, needs_order):
    """ZONE A: 대시보드 & 현황 요약"""
    render_section_header("📊 재료 현황 대시보드", "📊")
    
    if ingredient_df.empty:
        st.info("등록된 재료가 없습니다. 아래에서 재료를 등록해주세요.")
        return
    
    total_ingredients = len(ingredient_df)
    ingredients_in_recipe_count = sum(1 for name in ingredient_df['재료명'] if ingredient_in_recipe.get(name, False))
    ingredients_with_category = sum(1 for name in ingredient_df['재료명'] if categories.get(name) and categories.get(name) != "미지정")
    ingredients_on_sale = total_ingredients  # 기본값 (status 필드 추가 전)
    needs_order_count = sum(1 for name in ingredient_df['재료명'] if needs_order.get(name, False))
    
    # 핵심 지표 카드
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("전체 재료", f"{total_ingredients}개")
    with col2:
        st.metric("사용중 재료", f"{ingredients_on_sale}개")
    with col3:
        recipe_usage_rate = (ingredients_in_recipe_count / total_ingredients * 100) if total_ingredients > 0 else 0
        st.metric("레시피 사용률", f"{ingredients_in_recipe_count}개", delta=f"{recipe_usage_rate:.0f}%")
    with col4:
        st.metric("발주 필요", f"{needs_order_count}개", delta=f"-{needs_order_count}" if needs_order_count > 0 else None)
    
    # 진행률 바
    st.markdown("### 진행률")
    category_rate = (ingredients_with_category / total_ingredients * 100) if total_ingredients > 0 else 0
    
    st.progress(recipe_usage_rate / 100, text=f"레시피 사용률: {recipe_usage_rate:.0f}%")
    st.progress(category_rate / 100, text=f"재료 분류 지정률: {category_rate:.0f}%")
    
    # 스마트 알림
    alerts = []
    if ingredients_in_recipe_count < total_ingredients:
        alerts.append(f"ℹ️ 레시피에서 사용하지 않는 재료가 {total_ingredients - ingredients_in_recipe_count}개 있습니다.")
    if ingredients_with_category < total_ingredients:
        alerts.append(f"ℹ️ 재료 분류가 미지정인 재료가 {total_ingredients - ingredients_with_category}개 있습니다.")
    if needs_order_count > 0:
        alerts.append(f"⚠️ 발주 필요 재료가 {needs_order_count}개 있습니다.")
    
    if alerts:
        for alert in alerts:
            st.info(alert)


def _render_zone_b_input(store_id):
    """ZONE B: 재료 입력 (단일/일괄)"""
    render_section_header("📝 재료 입력", "📝")
    
    tab1, tab2 = st.tabs(["📝 단일 입력", "📋 일괄 입력"])
    
    with tab1:
        _render_single_input(store_id)
    
    with tab2:
        _render_batch_input(store_id)


def _render_single_input(store_id):
    """단일 재료 입력"""
    st.markdown("### 📝 재료 단일 등록")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        ingredient_name = st.text_input("재료명 *", key="ingredient_input_single_name", placeholder="재료명을 입력하세요")
    with col2:
        unit = st.selectbox("단위 *", options=UNIT_OPTIONS, key="ingredient_input_single_unit")
    with col3:
        unit_price = st.number_input("단가 (원/단위) *", min_value=0.0, value=0.0, step=100.0, 
                                     format="%.2f", key="ingredient_input_single_price")
    
    st.markdown("**📦 발주 단위 설정 (선택사항)**")
    col4, col5 = st.columns(2)
    with col4:
        order_unit = st.selectbox("발주 단위", options=[""] + UNIT_OPTIONS, key="ingredient_input_single_order_unit",
                                  help="발주 시 사용할 단위 (비워두면 기본 단위와 동일)")
    with col5:
        conversion_rate = st.number_input("변환 비율 (1 발주단위 = ? 기본단위)", min_value=0.1, value=1.0, 
                                         step=0.1, format="%.2f", key="ingredient_input_single_conversion_rate",
                                         help="예: 버터 1개 = 500g이면 500 입력")
    
    col6, col7 = st.columns(2)
    with col6:
        category = st.selectbox("재료 분류", options=[""] + INGREDIENT_CATEGORIES, key="ingredient_input_single_category")
    with col7:
        status = st.selectbox("상태", options=INGREDIENT_STATUSES, index=0, key="ingredient_input_single_status")
    
    notes = st.text_area("메모 (선택)", key="ingredient_input_single_notes", height=100)
    
    col_save, col_reset = st.columns([1, 1])
    with col_save:
        if st.button("💾 저장", type="primary", key="ingredient_input_single_save", use_container_width=True):
            # 입력값 검증
            ingredient_name_clean = ingredient_name.strip() if ingredient_name else ""
            if not ingredient_name_clean:
                ui_flash_error("재료명을 입력해주세요.")
            elif unit_price <= 0:
                ui_flash_error("단가를 입력해주세요.")
            elif conversion_rate <= 0:
                ui_flash_error("변환 비율은 0보다 큰 값이어야 합니다.")
            else:
                try:
                    # 변환비율 검증
                    conversion_rate_float = float(conversion_rate) if conversion_rate else 1.0
                    if conversion_rate_float <= 0:
                        ui_flash_error("변환 비율은 0보다 큰 값이어야 합니다.")
                        return
                    
                    # 재료 저장
                    success, msg = save_ingredient(
                        ingredient_name_clean,
                        unit,
                        float(unit_price),
                        order_unit.strip() if order_unit and order_unit.strip() else None,
                        conversion_rate_float
                    )
                    if not success:
                        ui_flash_error(msg)
                    else:
                        # 재료 분류 저장
                        if category and category.strip():
                            category_success = _set_ingredient_category(store_id, ingredient_name_clean, category.strip())
                            if not category_success:
                                logger.warning(f"재료 분류 저장 실패: {ingredient_name_clean}")
                        
                        ui_flash_success(f"재료 '{ingredient_name_clean}'이(가) 저장되었습니다.")
                        st.rerun()
                except ValueError as e:
                    ui_flash_error(f"입력값 형식 오류: {str(e)}")
                except Exception as e:
                    logger.error(f"재료 저장 중 예외 발생: {e}")
                    ui_flash_error(f"저장 실패: {str(e)}")
    
    with col_reset:
        if st.button("🔄 초기화", key="ingredient_input_single_reset", use_container_width=True):
            st.rerun()


def _render_batch_input(store_id):
    """일괄 재료 입력"""
    st.markdown("### 📋 재료 일괄 등록")
    
    ingredient_count = st.number_input("등록할 재료 개수", min_value=1, max_value=20, value=5, step=1, key="ingredient_input_batch_count")
    
    # 일괄 선택 옵션
    col_batch1, col_batch2 = st.columns(2)
    with col_batch1:
        batch_category = st.selectbox("일괄 재료 분류", options=[""] + INGREDIENT_CATEGORIES, key="ingredient_input_batch_category")
    with col_batch2:
        batch_status = st.selectbox("일괄 상태", options=[""] + INGREDIENT_STATUSES, key="ingredient_input_batch_status")
    
    st.markdown("---")
    st.write(f"**📋 총 {ingredient_count}개 재료 입력**")
    
    ingredient_data = []
    for i in range(ingredient_count):
        with st.expander(f"재료 {i+1}", expanded=(i < 3)):
            col1, col2, col3 = st.columns(3)
            with col1:
                ingredient_name = st.text_input(f"재료명 {i+1}", key=f"ingredient_input_batch_name_{i}")
            with col2:
                unit = st.selectbox(f"단위 {i+1}", options=UNIT_OPTIONS, key=f"ingredient_input_batch_unit_{i}")
            with col3:
                unit_price = st.number_input(f"단가 (원) {i+1}", min_value=0.0, value=0.0, step=100.0, 
                                            format="%.2f", key=f"ingredient_input_batch_price_{i}")
            
            col4, col5 = st.columns(2)
            with col4:
                order_unit = st.selectbox(f"발주단위 {i+1}", options=[""] + UNIT_OPTIONS, key=f"ingredient_input_batch_order_unit_{i}")
            with col5:
                conversion_rate = st.number_input(f"변환비율 {i+1}", min_value=0.1, value=1.0, step=0.1, 
                                                format="%.2f", key=f"ingredient_input_batch_conversion_{i}")
            
            col6, col7 = st.columns(2)
            with col6:
                category = st.selectbox(f"재료 분류 {i+1}", options=[""] + INGREDIENT_CATEGORIES,
                                      index=INGREDIENT_CATEGORIES.index(batch_category) + 1 if batch_category in INGREDIENT_CATEGORIES else 0,
                                      key=f"ingredient_input_batch_category_{i}")
            with col7:
                status = st.selectbox(f"상태 {i+1}", options=INGREDIENT_STATUSES,
                                      index=INGREDIENT_STATUSES.index(batch_status) if batch_status in INGREDIENT_STATUSES else 0,
                                      key=f"ingredient_input_batch_status_{i}")
            
            # 입력값 검증 및 데이터 수집
            ingredient_name_clean = ingredient_name.strip() if ingredient_name else ""
            if ingredient_name_clean and unit_price > 0:
                try:
                    ingredient_data.append({
                        'name': ingredient_name_clean,
                        'unit': unit,
                        'price': float(unit_price),
                        'order_unit': order_unit.strip() if order_unit and order_unit.strip() else None,
                        'conversion_rate': float(conversion_rate) if conversion_rate and conversion_rate > 0 else 1.0,
                        'category': category.strip() if category and category.strip() else None,
                        'status': status
                    })
                except (ValueError, TypeError) as e:
                    logger.warning(f"재료 데이터 변환 실패 ({ingredient_name_clean}): {e}")
    
    if st.button("💾 일괄 저장", type="primary", key="ingredient_input_batch_save", use_container_width=True):
        if not ingredient_data:
            ui_flash_error("저장할 재료가 없습니다. 재료명과 단가를 입력해주세요.")
        else:
            try:
                saved_count = 0
                failed_items = []
                
                for ing in ingredient_data:
                    try:
                        success, msg = save_ingredient(
                            ing['name'], 
                            ing['unit'], 
                            ing['price'], 
                            ing['order_unit'], 
                            ing['conversion_rate']
                        )
                        if success:
                            # 재료 분류 저장
                            if ing.get('category') and ing['category'].strip():
                                category_success = _set_ingredient_category(store_id, ing['name'], ing['category'].strip())
                                if not category_success:
                                    logger.warning(f"재료 분류 저장 실패: {ing['name']}")
                            saved_count += 1
                        else:
                            failed_items.append(f"{ing['name']}: {msg}")
                    except Exception as e:
                        logger.error(f"재료 저장 중 예외 발생 ({ing['name']}): {e}")
                        failed_items.append(f"{ing['name']}: {str(e)}")
                
                # 결과 메시지 표시
                if saved_count > 0:
                    if failed_items:
                        ui_flash_success(f"{saved_count}개 재료가 저장되었습니다. ({len(failed_items)}개 실패)")
                        for failed in failed_items:
                            st.warning(failed)
                    else:
                        ui_flash_success(f"{saved_count}개 재료가 모두 저장되었습니다.")
                    st.rerun()
                else:
                    ui_flash_error(f"저장에 실패했습니다. {len(failed_items)}개 재료 모두 저장 실패.")
                    for failed in failed_items:
                        st.error(failed)
            except Exception as e:
                logger.error(f"일괄 저장 중 예외 발생: {e}")
                ui_flash_error(f"저장 실패: {str(e)}")


def _render_zone_c_filters(ingredient_df, categories, ingredient_in_recipe, needs_order):
    """ZONE C: 필터 & 검색"""
    render_section_header("🔍 필터 & 검색", "🔍")
    
    if ingredient_df.empty:
        return ingredient_df
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        category_filter = st.multiselect("재료 분류", options=["전체"] + INGREDIENT_CATEGORIES + ["미지정"], 
                                         default=["전체"], key="ingredient_input_filter_category")
    with col2:
        status_filter = st.selectbox("상태", options=["전체"] + INGREDIENT_STATUSES, key="ingredient_input_filter_status")
    with col3:
        recipe_filter = st.selectbox("레시피 사용 상태", options=["전체", "레시피에서 사용", "레시피에서 미사용"], key="ingredient_input_filter_recipe")
    with col4:
        order_filter = st.selectbox("발주 상태", options=["전체", "발주 필요", "발주 불필요"], key="ingredient_input_filter_order")
    
    # 검색
    search_term = st.text_input("🔍 재료명 검색", key="ingredient_input_search", placeholder="재료명으로 검색...")
    
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
    
    # 레시피 사용 상태 필터
    if recipe_filter == "레시피에서 사용":
        filtered_df = filtered_df[filtered_df['재료명'].isin(ingredient_in_recipe.keys())]
    elif recipe_filter == "레시피에서 미사용":
        filtered_df = filtered_df[~filtered_df['재료명'].isin(ingredient_in_recipe.keys())]
    
    # 발주 상태 필터
    if order_filter == "발주 필요":
        filtered_df = filtered_df[filtered_df['재료명'].isin(needs_order.keys())]
    elif order_filter == "발주 불필요":
        filtered_df = filtered_df[~filtered_df['재료명'].isin(needs_order.keys())]
    
    # 검색 필터
    if search_term and search_term.strip():
        filtered_df = filtered_df[filtered_df['재료명'].str.contains(search_term, case=False, na=False)]
    
    return filtered_df


def _render_zone_d_ingredient_list(ingredient_df, categories, ingredient_in_recipe, recent_usage, needs_order, store_id):
    """ZONE D: 재료 목록 & 관리"""
    render_section_header("📋 재료 목록 & 관리", "📋")
    
    if ingredient_df.empty:
        st.info("등록된 재료가 없습니다.")
        return
    
    # 목록 표시
    st.markdown("### 재료 목록")
    
    for idx, row in ingredient_df.iterrows():
        ingredient_name = row['재료명']
        unit = row.get('단위', '—')
        unit_price = float(row.get('단가', 0))
        order_unit = row.get('발주단위', unit)
        conversion_rate = row.get('변환비율', 1.0)
        category = categories.get(ingredient_name, "미지정")
        in_recipe = ingredient_in_recipe.get(ingredient_name, False)
        usage = recent_usage.get(ingredient_name, 0)
        needs_order_flag = needs_order.get(ingredient_name, False)
        
        # 카드 형태로 표시
        with st.container():
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([3, 2, 2, 2, 2, 2, 2, 3])
            
            with col1:
                st.markdown(f"**{ingredient_name}**")
            with col2:
                # 재료 분류 뱃지
                category_colors = {
                    "채소": "#22C55E",
                    "육류": "#EF4444",
                    "해산물": "#3B82F6",
                    "조미료": "#EAB308",
                    "기타": "#9CA3AF",
                    "미지정": "#6B7280"
                }
                color = category_colors.get(category, "#6B7280")
                display_category = category if category in INGREDIENT_CATEGORIES else "미지정"
                st.markdown(f'<span style="background: {color}; padding: 0.2rem 0.5rem; border-radius: 4px; color: white; font-size: 0.8rem;">{display_category}</span>', 
                           unsafe_allow_html=True)
            with col3:
                st.markdown(f"{unit}")
            with col4:
                st.markdown(f"{unit_price:,.0f}원")
            with col5:
                if order_unit != unit:
                    st.markdown(f"{order_unit}<br><small>({conversion_rate:.1f}배)</small>", unsafe_allow_html=True)
                else:
                    st.markdown("—")
            with col6:
                if in_recipe:
                    st.markdown("✅")
                else:
                    st.markdown("—")
            with col7:
                col7_1, col7_2 = st.columns(2)
                with col7_1:
                    if usage > 0:
                        st.markdown(f"{usage:.1f}")
                    else:
                        st.markdown("—")
                with col7_2:
                    if needs_order_flag:
                        st.markdown("⚠️", help="발주 필요")
                    else:
                        st.markdown("✓", help="발주 불필요")
            with col8:
                # 액션 버튼
                action_col1, action_col2, action_col3, action_col4 = st.columns(4)
                with action_col1:
                    if st.button("✏️", key=f"ingredient_input_edit_{ingredient_name}", help="수정"):
                        st.session_state[f"ingredient_input_edit_{ingredient_name}"] = True
                with action_col2:
                    if st.button("🗑️", key=f"ingredient_input_delete_{ingredient_name}", help="삭제"):
                        st.session_state[f"ingredient_input_delete_{ingredient_name}"] = True
                with action_col3:
                    if in_recipe:
                        if st.button("📋", key=f"ingredient_input_recipe_{ingredient_name}", help="레시피 보기"):
                            st.session_state[f"ingredient_input_view_recipe_{ingredient_name}"] = True
                    else:
                        st.markdown("—")
                with action_col4:
                    if needs_order_flag:
                        if st.button("🛒", key=f"ingredient_input_order_{ingredient_name}", help="발주 관리", type="primary"):
                            st.session_state["current_page"] = "발주 관리"
                            st.session_state["selected_ingredient"] = ingredient_name
                            st.rerun()
                    else:
                        st.markdown("—")
            
            # 수정 모달
            if st.session_state.get(f"ingredient_input_edit_{ingredient_name}", False):
                with st.expander(f"✏️ {ingredient_name} 수정", expanded=True):
                    new_name = st.text_input("재료명", value=ingredient_name, key=f"ingredient_input_edit_name_{ingredient_name}")
                    new_unit = st.selectbox("단위", options=UNIT_OPTIONS, 
                                           index=UNIT_OPTIONS.index(unit) if unit in UNIT_OPTIONS else 0,
                                           key=f"ingredient_input_edit_unit_{ingredient_name}")
                    new_price = st.number_input("단가 (원)", min_value=0.0, value=unit_price, step=100.0, 
                                               format="%.2f", key=f"ingredient_input_edit_price_{ingredient_name}")
                    new_order_unit = st.selectbox("발주단위", options=[""] + UNIT_OPTIONS,
                                                index=UNIT_OPTIONS.index(order_unit) + 1 if order_unit in UNIT_OPTIONS else 0,
                                                key=f"ingredient_input_edit_order_unit_{ingredient_name}")
                    new_conversion = st.number_input("변환비율", min_value=0.1, value=float(conversion_rate) if conversion_rate and conversion_rate > 0 else 1.0, 
                                                    step=0.1, format="%.2f", key=f"ingredient_input_edit_conversion_{ingredient_name}")
                    new_category = st.selectbox("재료 분류", options=[""] + INGREDIENT_CATEGORIES,
                                               index=INGREDIENT_CATEGORIES.index(category) + 1 if category in INGREDIENT_CATEGORIES else 0,
                                               key=f"ingredient_input_edit_category_{ingredient_name}")
                    
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.button("💾 저장", key=f"ingredient_input_save_edit_{ingredient_name}"):
                            if not new_name or not new_name.strip():
                                ui_flash_error("재료명을 입력해주세요.")
                            elif new_price <= 0:
                                ui_flash_error("단가를 입력해주세요.")
                            elif new_conversion <= 0:
                                ui_flash_error("변환 비율은 0보다 큰 값이어야 합니다.")
                            else:
                                try:
                                    # 재료 기본 정보 수정
                                    success, msg = update_ingredient(ingredient_name, new_name.strip(), new_unit, new_price)
                                    if success:
                                        # 발주단위와 변환비율 수정 (DB 직접 업데이트)
                                        supabase = get_supabase_client()
                                        if supabase:
                                            try:
                                                # update_ingredient 성공 후 new_name으로 재료 찾기
                                                result = supabase.table("ingredients")\
                                                    .select("id")\
                                                    .eq("store_id", store_id)\
                                                    .eq("name", new_name.strip())\
                                                    .execute()
                                                
                                                if result.data and len(result.data) > 0:
                                                    ingredient_id = result.data[0]['id']
                                                    update_data = {}
                                                    
                                                    # 발주단위 처리 (빈 문자열이면 None, 아니면 값 설정)
                                                    if new_order_unit and new_order_unit.strip():
                                                        update_data["order_unit"] = new_order_unit.strip()
                                                    elif new_order_unit == "":
                                                        # 빈 문자열이면 기본 단위로 설정
                                                        update_data["order_unit"] = new_unit
                                                    
                                                    # 변환비율 처리
                                                    try:
                                                        new_conversion_float = float(new_conversion)
                                                        current_conversion_float = float(conversion_rate) if conversion_rate else 1.0
                                                        if abs(new_conversion_float - current_conversion_float) > 0.001:  # 부동소수점 비교
                                                            update_data["conversion_rate"] = new_conversion_float
                                                    except (ValueError, TypeError) as e:
                                                        logger.warning(f"변환비율 변환 실패: {new_conversion}, 오류: {e}")
                                                    
                                                    # 업데이트 데이터가 있으면 실행
                                                    if update_data:
                                                        supabase.table("ingredients")\
                                                            .update(update_data)\
                                                            .eq("id", ingredient_id)\
                                                            .execute()
                                                        logger.info(f"발주 정보 수정 완료: {new_name}")
                                            except Exception as e:
                                                logger.error(f"발주 정보 수정 실패: {e}")
                                                ui_flash_error(f"발주 정보 수정 중 오류가 발생했습니다: {str(e)}")
                                        
                                        # 재료 분류 저장
                                        if new_category and new_category.strip():
                                            category_success = _set_ingredient_category(store_id, new_name.strip(), new_category.strip())
                                            if not category_success:
                                                logger.warning(f"재료 분류 저장 실패: {new_name}")
                                        
                                        ui_flash_success(f"재료 '{new_name.strip()}'이(가) 수정되었습니다.")
                                        st.session_state[f"ingredient_input_edit_{ingredient_name}"] = False
                                        st.rerun()
                                    else:
                                        ui_flash_error(msg)
                                except Exception as e:
                                    logger.error(f"재료 수정 중 예외 발생: {e}")
                                    ui_flash_error(f"수정 실패: {str(e)}")
                    with col_cancel:
                        if st.button("취소", key=f"ingredient_input_cancel_edit_{ingredient_name}"):
                            st.session_state[f"ingredient_input_edit_{ingredient_name}"] = False
                            st.rerun()
            
            # 삭제 확인
            if st.session_state.get(f"ingredient_input_delete_{ingredient_name}", False):
                st.warning(f"'{ingredient_name}' 재료를 삭제하시겠습니까?")
                
                # 레시피 사용 여부 사전 확인 (더 정확한 메시지 표시)
                try:
                    success, msg, refs = delete_ingredient(ingredient_name, check_references=True)
                    if not success and refs:
                        # 참조가 있는 경우 상세 정보 표시
                        ref_info = []
                        if refs.get('레시피'):
                            ref_info.append(f"레시피 {refs['레시피']}개")
                        if refs.get('재고정보'):
                            ref_info.append("재고정보")
                        if ref_info:
                            st.error(f"⚠️ 이 재료는 다음에서 사용 중입니다: {', '.join(ref_info)}")
                except Exception as e:
                    logger.warning(f"삭제 전 참조 확인 실패: {e}")
                
                col_del, col_cancel = st.columns(2)
                with col_del:
                    if st.button("🗑️ 삭제", key=f"ingredient_input_confirm_delete_{ingredient_name}", type="primary"):
                        try:
                            success, msg, refs = delete_ingredient(ingredient_name, check_references=True)
                            if success:
                                ui_flash_success(f"재료 '{ingredient_name}'이(가) 삭제되었습니다.")
                                st.session_state[f"ingredient_input_delete_{ingredient_name}"] = False
                                st.rerun()
                            else:
                                ui_flash_error(msg)
                                if refs:
                                    ref_info = []
                                    if refs.get('레시피'):
                                        ref_info.append(f"레시피 {refs['레시피']}개")
                                    if refs.get('재고정보'):
                                        ref_info.append("재고정보")
                                    if ref_info:
                                        st.error(f"사용 중인 항목: {', '.join(ref_info)}")
                        except Exception as e:
                            logger.error(f"재료 삭제 중 예외 발생: {e}")
                            ui_flash_error(f"삭제 실패: {str(e)}")
                with col_cancel:
                    if st.button("취소", key=f"ingredient_input_cancel_delete_{ingredient_name}"):
                        st.session_state[f"ingredient_input_delete_{ingredient_name}"] = False
                        st.rerun()
            
            # 레시피 보기
            if st.session_state.get(f"ingredient_input_view_recipe_{ingredient_name}", False):
                with st.expander(f"📋 {ingredient_name} 레시피 보기", expanded=True):
                    recipe_df = load_csv('recipes.csv', store_id=store_id, default_columns=['메뉴명', '재료명', '사용량'])
                    if not recipe_df.empty:
                        menu_list = recipe_df[recipe_df['재료명'] == ingredient_name]['메뉴명'].unique().tolist()
                        if menu_list:
                            st.write(f"**{ingredient_name}**을(를) 사용하는 메뉴:")
                            for menu in menu_list:
                                usage_qty = recipe_df[(recipe_df['재료명'] == ingredient_name) & 
                                                     (recipe_df['메뉴명'] == menu)]['사용량'].iloc[0]
                                st.write(f"- {menu} ({usage_qty}{unit})")
                        else:
                            st.info("이 재료를 사용하는 메뉴가 없습니다.")
                    if st.button("닫기", key=f"ingredient_input_close_recipe_{ingredient_name}"):
                        st.session_state[f"ingredient_input_view_recipe_{ingredient_name}"] = False
                        st.rerun()
            
            st.markdown("---")


def _render_zone_e_management(ingredient_df, categories, ingredient_in_recipe, recent_usage, store_id):
    """ZONE E: 재료 분류 & 통계 관리"""
    render_section_header("📊 재료 분류 & 통계 관리", "📊")
    
    if ingredient_df.empty:
        st.info("등록된 재료가 없습니다.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 재료 분류 현황")
        category_counts = {}
        for category in INGREDIENT_CATEGORIES:
            count = sum(1 for name in ingredient_df['재료명'] if categories.get(name) == category)
            category_counts[category] = count
        
        for category, count in category_counts.items():
            st.metric(category, f"{count}개")
        
        if st.button("💡 재료 구조 설계실로 이동", key="ingredient_input_go_to_design"):
            st.session_state["current_page"] = "재료 등록"
            st.rerun()
    
    with col2:
        st.markdown("### 재료 사용 통계")
        
        # 레시피 사용률
        total = len(ingredient_df)
        in_recipe = sum(1 for name in ingredient_df['재료명'] if ingredient_in_recipe.get(name, False))
        usage_rate = (in_recipe / total * 100) if total > 0 else 0
        st.metric("레시피 사용률", f"{usage_rate:.0f}%", delta=f"{in_recipe}/{total}")
        
        # 최근 사용량 TOP 5
        if recent_usage:
            st.markdown("**최근 사용량 TOP 5**")
            sorted_usage = sorted(recent_usage.items(), key=lambda x: x[1], reverse=True)[:5]
            for name, usage_val in sorted_usage:
                st.write(f"- {name}: {usage_val:.1f}")
        
        if st.button("🛒 발주 관리로 이동", key="ingredient_input_go_to_order"):
            st.session_state["current_page"] = "발주 관리"
            st.rerun()
