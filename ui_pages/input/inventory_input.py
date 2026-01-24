"""
재고 입력 페이지 (입력 전용)
재기획안에 따른 5-Zone 구조
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
import logging
from datetime import datetime, timedelta
from src.ui_helpers import render_page_header, ui_flash_success, ui_flash_error, render_section_header
from src.storage_supabase import load_csv, save_inventory, soft_invalidate, clear_session_cache
from src.auth import get_current_store_id, get_supabase_client
from src.analytics import calculate_ingredient_usage, calculate_order_recommendation

logger = logging.getLogger(__name__)

# 공통 설정 적용
bootstrap(page_title="재고 입력")

# 재료 분류 옵션 (재료 입력 페이지와 동일)
INGREDIENT_CATEGORIES = ["채소", "육류", "해산물", "조미료", "기타"]


def _update_inventory(store_id, ingredient_name, current_stock, safety_stock):
    """재고 정보 수정 (DB 직접 업데이트)"""
    supabase = get_supabase_client()
    if not supabase:
        return False
    
    try:
        # 재료 ID 찾기
        ing_result = supabase.table("ingredients")\
            .select("id")\
            .eq("store_id", store_id)\
            .eq("name", ingredient_name)\
            .execute()
        
        if not ing_result.data:
            logger.error(f"재료를 찾을 수 없습니다: {ingredient_name}")
            return False
        
        ingredient_id = ing_result.data[0]['id']
        
        # 재고 정보 업데이트
        supabase.table("inventory")\
            .update({
                "on_hand": float(current_stock),
                "safety_stock": float(safety_stock)
            })\
            .eq("store_id", store_id)\
            .eq("ingredient_id", ingredient_id)\
            .execute()
        
        # 캐시 무효화
        try:
            soft_invalidate(
                reason=f"재고 수정: {ingredient_name}",
                targets=["inventory"],
                session_keys=['ss_inventory_df']
            )
            clear_session_cache('ss_inventory_df')
            load_csv.clear()
        except Exception as e:
            logger.warning(f"캐시 무효화 실패: {e}")
        
        return True
    except Exception as e:
        logger.error(f"재고 수정 실패: {e}")
        return False


def _delete_inventory(store_id, ingredient_name):
    """재고 정보 삭제 (DB 직접 삭제)"""
    supabase = get_supabase_client()
    if not supabase:
        return False
    
    try:
        # 재료 ID 찾기
        ing_result = supabase.table("ingredients")\
            .select("id")\
            .eq("store_id", store_id)\
            .eq("name", ingredient_name)\
            .execute()
        
        if not ing_result.data:
            logger.error(f"재료를 찾을 수 없습니다: {ingredient_name}")
            return False
        
        ingredient_id = ing_result.data[0]['id']
        
        # 발주 이력 확인
        order_check = supabase.table("orders")\
            .select("id")\
            .eq("store_id", store_id)\
            .eq("ingredient_id", ingredient_id)\
            .execute()
        
        if order_check.data:
            return False, f"발주 이력이 있어 삭제할 수 없습니다. (발주 이력: {len(order_check.data)}건)"
        
        # 재고 정보 삭제
        supabase.table("inventory")\
            .delete()\
            .eq("store_id", store_id)\
            .eq("ingredient_id", ingredient_id)\
            .execute()
        
        # 캐시 무효화
        try:
            soft_invalidate(
                reason=f"재고 삭제: {ingredient_name}",
                targets=["inventory"],
                session_keys=['ss_inventory_df']
            )
            clear_session_cache('ss_inventory_df')
            load_csv.clear()
        except Exception as e:
            logger.warning(f"캐시 무효화 실패: {e}")
        
        return True, "삭제 성공"
    except Exception as e:
        logger.error(f"재고 삭제 실패: {e}")
        return False, f"삭제 실패: {str(e)}"


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


def render_inventory_input_page():
    """재고 입력 페이지 렌더링 (5-Zone 구조)"""
    render_page_header("📦 재고 입력", "📦")
    
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
                usage_df['날짜'] = pd.to_datetime(usage_df['날짜'])
                max_date = usage_df['날짜'].max()
                recent_cutoff = max_date - timedelta(days=7)
                recent_usage_df = usage_df[usage_df['날짜'] >= recent_cutoff]
                
                if not recent_usage_df.empty:
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
    _render_zone_a_dashboard(ingredient_df, inventory_map, needs_order)
    
    st.markdown("---")
    
    # ============================================
    # ZONE B: 재고 입력 (단일/일괄)
    # ============================================
    _render_zone_b_input(store_id, ingredient_df, inventory_map)
    
    st.markdown("---")
    
    # ============================================
    # ZONE C: 필터 & 검색
    # ============================================
    filtered_inventory_df = _render_zone_c_filters(ingredient_df, inventory_map, categories, ingredient_in_recipe, needs_order)
    
    st.markdown("---")
    
    # ============================================
    # ZONE D: 재고 목록 & 관리
    # ============================================
    _render_zone_d_inventory_list(filtered_inventory_df, ingredient_df, inventory_map, categories, 
                                   ingredient_in_recipe, recent_usage, needs_order, store_id)
    
    st.markdown("---")
    
    # ============================================
    # ZONE E: 통계 & 연계 관리
    # ============================================
    _render_zone_e_management(ingredient_df, inventory_map, recent_usage, needs_order, store_id)


def _render_zone_a_dashboard(ingredient_df, inventory_map, needs_order):
    """ZONE A: 대시보드 & 현황 요약"""
    render_section_header("📊 재고 현황 대시보드", "📊")
    
    total_ingredients = len(ingredient_df)
    registered_inventory = len(inventory_map)
    
    if total_ingredients == 0:
        st.info("등록된 재료가 없습니다. 먼저 재료를 등록해주세요.")
        return
    
    # 재고 상태 계산
    normal_count = 0
    warning_count = 0
    shortage_count = 0
    
    for ing_name, inv_data in inventory_map.items():
        current = inv_data['current']
        safety = inv_data['safety']
        
        if current < safety:
            shortage_count += 1
        elif current <= safety * 1.2:
            warning_count += 1
        else:
            normal_count += 1
    
    # 핵심 지표 카드
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("전체 재고 등록", f"{registered_inventory}개", delta=f"{total_ingredients}개 재료 중")
    with col2:
        st.metric("정상 재고", f"{normal_count}개")
    with col3:
        st.metric("발주 필요", f"{shortage_count}개", delta=f"-{shortage_count}" if shortage_count > 0 else None)
    with col4:
        st.metric("주의 재고", f"{warning_count}개")
    
    # 진행률 바
    st.markdown("### 진행률")
    registration_rate = (registered_inventory / total_ingredients * 100) if total_ingredients > 0 else 0
    normal_rate = (normal_count / registered_inventory * 100) if registered_inventory > 0 else 0
    
    st.progress(registration_rate / 100, text=f"재고 등록률: {registration_rate:.0f}%")
    st.progress(normal_rate / 100, text=f"재고 정상률: {normal_rate:.0f}%")
    
    # 스마트 알림
    alerts = []
    if registered_inventory < total_ingredients:
        alerts.append(f"ℹ️ 재고 정보가 없는 재료가 {total_ingredients - registered_inventory}개 있습니다.")
    if shortage_count > 0:
        alerts.append(f"⚠️ 발주 필요 재고가 {shortage_count}개 있습니다.")
    if warning_count > 0:
        alerts.append(f"ℹ️ 주의 재고가 {warning_count}개 있습니다.")
    
    if alerts:
        for alert in alerts:
            st.info(alert)


def _render_zone_b_input(store_id, ingredient_df, inventory_map):
    """ZONE B: 재고 입력 (단일/일괄)"""
    render_section_header("📝 재고 입력", "📝")
    
    tab1, tab2 = st.tabs(["📝 단일 입력", "📋 일괄 입력"])
    
    with tab1:
        _render_single_input(store_id, ingredient_df, inventory_map)
    
    with tab2:
        _render_batch_input(store_id, ingredient_df, inventory_map)


def _render_single_input(store_id, ingredient_df, inventory_map):
    """단일 재고 입력"""
    st.markdown("### 📝 재고 단일 등록")
    
    # 재료명과 단위 매핑 생성
    ingredient_unit_map = {}
    ingredient_order_unit_map = {}
    ingredient_conversion_rate_map = {}
    
    for _, row in ingredient_df.iterrows():
        ingredient_name = row.get('재료명', '')
        unit = row.get('단위', '')
        order_unit = row.get('발주단위', unit)
        conversion_rate = float(row.get('변환비율', 1.0)) if row.get('변환비율') else 1.0
        
        if ingredient_name:
            ingredient_unit_map[ingredient_name] = unit
            ingredient_order_unit_map[ingredient_name] = order_unit
            ingredient_conversion_rate_map[ingredient_name] = conversion_rate
    
    # 재료 선택 옵션
    ingredient_list = ingredient_df['재료명'].tolist()
    ingredient_options = []
    for ing in ingredient_list:
        unit = ingredient_unit_map.get(ing, '')
        order_unit = ingredient_order_unit_map.get(ing, unit)
        if unit:
            if order_unit != unit:
                ingredient_options.append(f"{ing} ({unit} / 발주: {order_unit})")
            else:
                ingredient_options.append(f"{ing} ({unit})")
        else:
            ingredient_options.append(ing)
    
    selected_option = st.selectbox(
        "재료 선택 *",
        options=ingredient_options,
        key="inventory_input_single_ingredient"
    )
    
    # 선택된 옵션에서 재료명 추출
    ingredient_name = selected_option.split(" (")[0] if " (" in selected_option else selected_option
    selected_unit = ingredient_unit_map.get(ingredient_name, '')
    selected_order_unit = ingredient_order_unit_map.get(ingredient_name, selected_unit)
    selected_conversion_rate = ingredient_conversion_rate_map.get(ingredient_name, 1.0)
    
    # 기존 재고 정보 가져오기
    existing_inventory = inventory_map.get(ingredient_name, {'current': 0, 'safety': 0})
    existing_current = existing_inventory['current']
    existing_safety = existing_inventory['safety']
    
    # 단위 정보 표시
    st.info(f"**단위 정보**: 기본 단위: {selected_unit}, 발주 단위: {selected_order_unit}, 변환비율: 1 {selected_order_unit} = {selected_conversion_rate} {selected_unit}")
    
    # 현재고/안전재고 입력
    col1, col2 = st.columns(2)
    
    with col1:
        current_stock_label = f"현재고 ({selected_order_unit}) *"
        if existing_current > 0:
            current_in_order_unit = existing_current / selected_conversion_rate if selected_conversion_rate > 0 else existing_current
            current_stock_input = st.number_input(
                current_stock_label,
                min_value=0.0,
                value=float(current_in_order_unit),
                step=1.0,
                format="%.2f",
                key="inventory_input_single_current",
                help=f"기본 단위({selected_unit})로 저장됩니다"
            )
        else:
            current_stock_input = st.number_input(
                current_stock_label,
                min_value=0.0,
                value=0.0,
                step=1.0,
                format="%.2f",
                key="inventory_input_single_current",
                help=f"기본 단위({selected_unit})로 저장됩니다"
            )
        current_stock = current_stock_input * selected_conversion_rate
    
    with col2:
        safety_stock_label = f"안전재고 ({selected_order_unit}) *"
        if existing_safety > 0:
            safety_in_order_unit = existing_safety / selected_conversion_rate if selected_conversion_rate > 0 else existing_safety
            safety_stock_input = st.number_input(
                safety_stock_label,
                min_value=0.0,
                value=float(safety_in_order_unit),
                step=1.0,
                format="%.2f",
                key="inventory_input_single_safety",
                help=f"기본 단위({selected_unit})로 저장됩니다"
            )
        else:
            safety_stock_input = st.number_input(
                safety_stock_label,
                min_value=0.0,
                value=0.0,
                step=1.0,
                format="%.2f",
                key="inventory_input_single_safety",
                help=f"기본 단위({selected_unit})로 저장됩니다"
            )
        safety_stock = safety_stock_input * selected_conversion_rate
    
    # 저장 버튼
    col_save, col_reset = st.columns([1, 1])
    with col_save:
        if st.button("💾 저장", type="primary", key="inventory_input_single_save", use_container_width=True):
            if current_stock_input < 0 or safety_stock_input < 0:
                ui_flash_error("현재고와 안전재고는 0 이상이어야 합니다.")
            else:
                try:
                    success = save_inventory(ingredient_name, current_stock, safety_stock)
                    if success:
                        ui_flash_success(f"재고 정보가 저장되었습니다: {ingredient_name}")
                        st.rerun()
                    else:
                        ui_flash_error("재고 정보 저장에 실패했습니다.")
                except Exception as e:
                    logger.error(f"재고 저장 중 예외 발생: {e}")
                    ui_flash_error(f"저장 실패: {str(e)}")
    
    with col_reset:
        if st.button("🔄 초기화", key="inventory_input_single_reset", use_container_width=True):
            st.rerun()


def _render_batch_input(store_id, ingredient_df, inventory_map):
    """일괄 재고 입력"""
    st.markdown("### 📋 재고 일괄 등록")
    
    ingredient_count = st.number_input("등록할 재고 개수", min_value=1, max_value=20, value=5, step=1, 
                                      key="inventory_input_batch_count")
    
    # 재료명과 단위 매핑 생성
    ingredient_unit_map = {}
    ingredient_order_unit_map = {}
    ingredient_conversion_rate_map = {}
    
    for _, row in ingredient_df.iterrows():
        ingredient_name = row.get('재료명', '')
        unit = row.get('단위', '')
        order_unit = row.get('발주단위', unit)
        conversion_rate = float(row.get('변환비율', 1.0)) if row.get('변환비율') else 1.0
        
        if ingredient_name:
            ingredient_unit_map[ingredient_name] = unit
            ingredient_order_unit_map[ingredient_name] = order_unit
            ingredient_conversion_rate_map[ingredient_name] = conversion_rate
    
    # 재료 선택 옵션
    ingredient_list = ingredient_df['재료명'].tolist()
    ingredient_options = []
    for ing in ingredient_list:
        unit = ingredient_unit_map.get(ing, '')
        order_unit = ingredient_order_unit_map.get(ing, unit)
        if unit:
            if order_unit != unit:
                ingredient_options.append(f"{ing} ({unit} / 발주: {order_unit})")
            else:
                ingredient_options.append(f"{ing} ({unit})")
        else:
            ingredient_options.append(ing)
    
    st.markdown("---")
    st.write(f"**📋 총 {ingredient_count}개 재고 입력**")
    
    inventory_data = []
    for i in range(ingredient_count):
        with st.expander(f"재고 {i+1}", expanded=(i < 3)):
            selected_option = st.selectbox(
                f"재료 선택 {i+1}",
                options=ingredient_options,
                key=f"inventory_input_batch_ingredient_{i}"
            )
            
            ingredient_name = selected_option.split(" (")[0] if " (" in selected_option else selected_option
            selected_order_unit = ingredient_order_unit_map.get(ingredient_name, ingredient_unit_map.get(ingredient_name, ''))
            selected_conversion_rate = ingredient_conversion_rate_map.get(ingredient_name, 1.0)
            
            # 기존 재고 정보
            existing_inv = inventory_map.get(ingredient_name, {'current': 0, 'safety': 0})
            existing_current = existing_inv['current']
            existing_safety = existing_inv['safety']
            
            col1, col2 = st.columns(2)
            with col1:
                if existing_current > 0:
                    current_in_order_unit = existing_current / selected_conversion_rate if selected_conversion_rate > 0 else existing_current
                    current_stock_input = st.number_input(
                        f"현재고 ({selected_order_unit}) {i+1}",
                        min_value=0.0,
                        value=float(current_in_order_unit),
                        step=1.0,
                        format="%.2f",
                        key=f"inventory_input_batch_current_{i}"
                    )
                else:
                    current_stock_input = st.number_input(
                        f"현재고 ({selected_order_unit}) {i+1}",
                        min_value=0.0,
                        value=0.0,
                        step=1.0,
                        format="%.2f",
                        key=f"inventory_input_batch_current_{i}"
                    )
                current_stock = current_stock_input * selected_conversion_rate
            
            with col2:
                if existing_safety > 0:
                    safety_in_order_unit = existing_safety / selected_conversion_rate if selected_conversion_rate > 0 else existing_safety
                    safety_stock_input = st.number_input(
                        f"안전재고 ({selected_order_unit}) {i+1}",
                        min_value=0.0,
                        value=float(safety_in_order_unit),
                        step=1.0,
                        format="%.2f",
                        key=f"inventory_input_batch_safety_{i}"
                    )
                else:
                    safety_stock_input = st.number_input(
                        f"안전재고 ({selected_order_unit}) {i+1}",
                        min_value=0.0,
                        value=0.0,
                        step=1.0,
                        format="%.2f",
                        key=f"inventory_input_batch_safety_{i}"
                    )
                safety_stock = safety_stock_input * selected_conversion_rate
            
            if ingredient_name and current_stock_input >= 0 and safety_stock_input >= 0:
                inventory_data.append({
                    'name': ingredient_name,
                    'current': current_stock,
                    'safety': safety_stock
                })
    
    if st.button("💾 일괄 저장", type="primary", key="inventory_input_batch_save", use_container_width=True):
        if not inventory_data:
            ui_flash_error("저장할 재고 정보가 없습니다.")
        else:
            try:
                saved_count = 0
                failed_items = []
                
                for inv in inventory_data:
                    try:
                        success = save_inventory(inv['name'], inv['current'], inv['safety'])
                        if success:
                            saved_count += 1
                        else:
                            failed_items.append(f"{inv['name']}: 저장 실패")
                    except Exception as e:
                        logger.error(f"재고 저장 중 예외 발생 ({inv['name']}): {e}")
                        failed_items.append(f"{inv['name']}: {str(e)}")
                
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


def _render_zone_c_filters(ingredient_df, inventory_map, categories, ingredient_in_recipe, needs_order):
    """ZONE C: 필터 & 검색"""
    render_section_header("🔍 필터 & 검색", "🔍")
    
    if ingredient_df.empty:
        return pd.DataFrame()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        category_filter = st.multiselect("재료 분류", options=["전체"] + INGREDIENT_CATEGORIES + ["미지정"], 
                                         default=["전체"], key="inventory_input_filter_category")
    with col2:
        status_filter = st.selectbox("재고 상태", options=["전체", "정상", "주의", "부족"], 
                                     key="inventory_input_filter_status")
    with col3:
        registration_filter = st.selectbox("재고 등록 상태", options=["전체", "등록됨", "미등록"], 
                                          key="inventory_input_filter_registration")
    with col4:
        recipe_filter = st.selectbox("레시피 사용 상태", options=["전체", "레시피에서 사용", "레시피에서 미사용"], 
                                     key="inventory_input_filter_recipe")
    
    # 검색
    search_term = st.text_input("🔍 재료명 검색", key="inventory_input_search", placeholder="재료명으로 검색...")
    
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
    
    # 재고 상태 필터
    if status_filter != "전체":
        def status_match(name):
            if name not in inventory_map:
                return False
            current = inventory_map[name]['current']
            safety = inventory_map[name]['safety']
            
            if status_filter == "부족":
                return current < safety
            elif status_filter == "주의":
                return safety <= current <= safety * 1.2
            elif status_filter == "정상":
                return current > safety * 1.2
            return True
        filtered_df = filtered_df[filtered_df['재료명'].apply(status_match)]
    
    # 재고 등록 상태 필터
    if registration_filter == "등록됨":
        filtered_df = filtered_df[filtered_df['재료명'].isin(inventory_map.keys())]
    elif registration_filter == "미등록":
        filtered_df = filtered_df[~filtered_df['재료명'].isin(inventory_map.keys())]
    
    # 레시피 사용 상태 필터
    if recipe_filter == "레시피에서 사용":
        filtered_df = filtered_df[filtered_df['재료명'].isin(ingredient_in_recipe.keys())]
    elif recipe_filter == "레시피에서 미사용":
        filtered_df = filtered_df[~filtered_df['재료명'].isin(ingredient_in_recipe.keys())]
    
    # 검색 필터
    if search_term and search_term.strip():
        filtered_df = filtered_df[filtered_df['재료명'].str.contains(search_term, case=False, na=False)]
    
    return filtered_df


def _render_zone_d_inventory_list(ingredient_df, full_ingredient_df, inventory_map, categories, 
                                  ingredient_in_recipe, recent_usage, needs_order, store_id):
    """ZONE D: 재고 목록 & 관리"""
    render_section_header("📋 재고 목록 & 관리", "📋")
    
    if ingredient_df.empty:
        st.info("등록된 재료가 없습니다.")
        return
    
    # 재고 정보가 있는 재료만 표시 (또는 모든 재료 표시)
    st.markdown("### 재고 목록")
    
    # 컬럼 헤더 표시
    header_col1, header_col2, header_col3, header_col4, header_col5, header_col6, header_col7, header_col8 = st.columns([3, 2, 2, 2, 2, 2, 2, 3])
    with header_col1:
        st.markdown("**재료명**")
    with header_col2:
        st.markdown("**재료 분류**")
    with header_col3:
        st.markdown("**단위**")
    with header_col4:
        st.markdown("**현재고**")
    with header_col5:
        st.markdown("**안전재고**")
    with header_col6:
        st.markdown("**상태**")
    with header_col7:
        st.markdown("**발주 필요**")
    with header_col8:
        st.markdown("**관리**")
    
    st.markdown("---")
    
    # 재료명과 단위 매핑 생성
    ingredient_unit_map = {}
    ingredient_order_unit_map = {}
    ingredient_conversion_rate_map = {}
    
    for _, row in full_ingredient_df.iterrows():
        ingredient_name = row.get('재료명', '')
        unit = row.get('단위', '')
        order_unit = row.get('발주단위', unit)
        conversion_rate = float(row.get('변환비율', 1.0)) if row.get('변환비율') else 1.0
        
        if ingredient_name:
            ingredient_unit_map[ingredient_name] = unit
            ingredient_order_unit_map[ingredient_name] = order_unit
            ingredient_conversion_rate_map[ingredient_name] = conversion_rate
    
    for idx, row in ingredient_df.iterrows():
        ingredient_name = row['재료명']
        unit = ingredient_unit_map.get(ingredient_name, '—')
        order_unit = ingredient_order_unit_map.get(ingredient_name, unit)
        conversion_rate = ingredient_conversion_rate_map.get(ingredient_name, 1.0)
        category = categories.get(ingredient_name, "미지정")
        
        # 재고 정보
        inv_data = inventory_map.get(ingredient_name, {'current': 0, 'safety': 0})
        current = inv_data['current']
        safety = inv_data['safety']
        
        # 발주 단위로 변환하여 표시
        current_display = current / conversion_rate if conversion_rate > 0 else current
        safety_display = safety / conversion_rate if conversion_rate > 0 else safety
        
        # 상태 판단
        if ingredient_name not in inventory_map:
            status = "미등록"
            status_color = "#9CA3AF"
        elif current < safety:
            status = "⚠️ 부족"
            status_color = "#EF4444"
        elif current <= safety * 1.2:
            status = "⚠️ 주의"
            status_color = "#F59E0B"
        else:
            status = "✓ 정상"
            status_color = "#22C55E"
        
        # 발주 필요 여부
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
                if order_unit != unit:
                    st.markdown(f"{unit}<br><small>(발주: {order_unit})</small>", unsafe_allow_html=True)
                else:
                    st.markdown(f"{unit}")
            with col4:
                if ingredient_name in inventory_map:
                    st.markdown(f"{current_display:.1f} {order_unit}")
                else:
                    st.markdown("—")
            with col5:
                if ingredient_name in inventory_map:
                    st.markdown(f"{safety_display:.1f} {order_unit}")
                else:
                    st.markdown("—")
            with col6:
                st.markdown(f'<span style="color: {status_color}; font-weight: 600;">{status}</span>', 
                           unsafe_allow_html=True)
            with col7:
                if needs_order_flag:
                    st.markdown("⚠️", help="발주 필요")
                else:
                    st.markdown("✓", help="발주 불필요")
            with col8:
                # 액션 버튼
                action_col1, action_col2, action_col3 = st.columns(3)
                with action_col1:
                    edit_key = f"inventory_input_btn_edit_{ingredient_name}"
                    if st.button("✏️", key=edit_key, help="수정"):
                        st.session_state[f"inventory_input_edit_{ingredient_name}"] = True
                        st.rerun()
                with action_col2:
                    delete_key = f"inventory_input_btn_delete_{ingredient_name}"
                    if st.button("🗑️", key=delete_key, help="삭제"):
                        st.session_state[f"inventory_input_delete_{ingredient_name}"] = True
                        st.rerun()
                with action_col3:
                    if needs_order_flag:
                        order_key = f"inventory_input_btn_order_{ingredient_name}"
                        if st.button("🛒", key=order_key, help="발주 관리", type="primary"):
                            st.session_state["current_page"] = "발주 관리"
                            st.session_state["selected_ingredient"] = ingredient_name
                            st.rerun()
                    else:
                        st.markdown("—")
            
            # 수정 모달
            if st.session_state.get(f"inventory_input_edit_{ingredient_name}", False):
                with st.expander(f"✏️ {ingredient_name} 재고 수정", expanded=True):
                    existing_inv = inventory_map.get(ingredient_name, {'current': 0, 'safety': 0})
                    existing_current = existing_inv['current']
                    existing_safety = existing_inv['safety']
                    
                    # 발주 단위로 변환하여 표시
                    current_in_order_unit = existing_current / conversion_rate if conversion_rate > 0 else existing_current
                    safety_in_order_unit = existing_safety / conversion_rate if conversion_rate > 0 else existing_safety
                    
                    new_current_input = st.number_input(
                        f"현재고 ({order_unit})",
                        min_value=0.0,
                        value=float(current_in_order_unit),
                        step=1.0,
                        format="%.2f",
                        key=f"inventory_input_edit_current_{ingredient_name}"
                    )
                    new_safety_input = st.number_input(
                        f"안전재고 ({order_unit})",
                        min_value=0.0,
                        value=float(safety_in_order_unit),
                        step=1.0,
                        format="%.2f",
                        key=f"inventory_input_edit_safety_{ingredient_name}"
                    )
                    
                    # 발주 단위를 기본 단위로 변환
                    new_current = new_current_input * conversion_rate
                    new_safety = new_safety_input * conversion_rate
                    
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.button("💾 저장", key=f"inventory_input_save_edit_{ingredient_name}"):
                            try:
                                success = _update_inventory(store_id, ingredient_name, new_current, new_safety)
                                if success:
                                    ui_flash_success(f"재고 정보가 수정되었습니다: {ingredient_name}")
                                    st.session_state[f"inventory_input_edit_{ingredient_name}"] = False
                                    st.rerun()
                                else:
                                    ui_flash_error("재고 정보 수정에 실패했습니다.")
                            except Exception as e:
                                logger.error(f"재고 수정 중 예외 발생: {e}")
                                ui_flash_error(f"수정 실패: {str(e)}")
                    with col_cancel:
                        if st.button("취소", key=f"inventory_input_cancel_edit_{ingredient_name}"):
                            st.session_state[f"inventory_input_edit_{ingredient_name}"] = False
                            st.rerun()
            
            # 삭제 확인
            if st.session_state.get(f"inventory_input_delete_{ingredient_name}", False):
                st.warning(f"'{ingredient_name}' 재고 정보를 삭제하시겠습니까?")
                
                # 발주 이력 확인
                try:
                    supabase = get_supabase_client()
                    if supabase:
                        ing_result = supabase.table("ingredients")\
                            .select("id")\
                            .eq("store_id", store_id)\
                            .eq("name", ingredient_name)\
                            .execute()
                        
                        if ing_result.data:
                            ingredient_id = ing_result.data[0]['id']
                            order_check = supabase.table("orders")\
                                .select("id")\
                                .eq("store_id", store_id)\
                                .eq("ingredient_id", ingredient_id)\
                                .execute()
                            
                            if order_check.data:
                                st.error(f"⚠️ 이 재고는 발주 이력이 있어 삭제할 수 없습니다. (발주 이력: {len(order_check.data)}건)")
                except Exception as e:
                    logger.warning(f"발주 이력 확인 실패: {e}")
                
                col_del, col_cancel = st.columns(2)
                with col_del:
                    if st.button("🗑️ 삭제", key=f"inventory_input_confirm_delete_{ingredient_name}", type="primary"):
                        try:
                            success, msg = _delete_inventory(store_id, ingredient_name)
                            if success:
                                ui_flash_success(f"재고 정보가 삭제되었습니다: {ingredient_name}")
                                st.session_state[f"inventory_input_delete_{ingredient_name}"] = False
                                st.rerun()
                            else:
                                ui_flash_error(msg)
                        except Exception as e:
                            logger.error(f"재고 삭제 중 예외 발생: {e}")
                            ui_flash_error(f"삭제 실패: {str(e)}")
                with col_cancel:
                    if st.button("취소", key=f"inventory_input_cancel_delete_{ingredient_name}"):
                        st.session_state[f"inventory_input_delete_{ingredient_name}"] = False
                        st.rerun()
            
            st.markdown("---")


def _render_zone_e_management(ingredient_df, inventory_map, recent_usage, needs_order, store_id):
    """ZONE E: 통계 & 연계 관리"""
    render_section_header("📊 재고 통계 & 연계 관리", "📊")
    
    if ingredient_df.empty:
        st.info("등록된 재료가 없습니다.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 재고 통계")
        
        # 재고 등록률
        total = len(ingredient_df)
        registered = len(inventory_map)
        registration_rate = (registered / total * 100) if total > 0 else 0
        st.metric("재고 등록률", f"{registration_rate:.0f}%", delta=f"{registered}/{total}")
        
        # 재고 정상률
        normal_count = sum(1 for inv_data in inventory_map.values() 
                          if inv_data['current'] > inv_data['safety'] * 1.2)
        normal_rate = (normal_count / registered * 100) if registered > 0 else 0
        st.metric("재고 정상률", f"{normal_rate:.0f}%", delta=f"{normal_count}/{registered}")
        
        # 발주 필요 TOP 5
        if needs_order:
            st.markdown("**발주 필요 재료 TOP 5**")
            needs_order_list = [name for name in needs_order.keys() if name in ingredient_df['재료명'].values]
            for i, name in enumerate(needs_order_list[:5], 1):
                st.write(f"{i}. {name}")
        
        if st.button("🛒 발주 관리로 이동", key="inventory_input_go_to_order", use_container_width=True):
            st.session_state["current_page"] = "발주 관리"
            st.rerun()
    
    with col2:
        st.markdown("### 연계 페이지")
        
        # 최근 사용량 TOP 5
        if recent_usage:
            st.markdown("**최근 사용량 TOP 5**")
            sorted_usage = sorted(recent_usage.items(), key=lambda x: x[1], reverse=True)[:5]
            for name, usage_val in sorted_usage:
                st.write(f"- {name}: {usage_val:.1f}")
        
        if st.button("🧺 사용 재료 입력으로 이동", key="inventory_input_go_to_ingredient", use_container_width=True):
            st.session_state["current_page"] = "재료 입력"
            st.rerun()
        
        if st.button("📊 재료 사용량 집계로 이동", key="inventory_input_go_to_usage", use_container_width=True):
            st.session_state["current_page"] = "재료 사용량 집계"
            st.rerun()
