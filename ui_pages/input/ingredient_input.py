"""
사용 재료 입력 페이지 (FormKit v2 + 블록 리듬)
CONSOLE형: 입력 컴포넌트만 FormKit v2로 통일
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
import logging
from datetime import datetime, timedelta
from src.ui_helpers import ui_flash_success, ui_flash_error
from src.ui.layouts.input_layouts import render_console_layout
from src.ui.components.form_kit import inject_form_kit_css, ps_section
from src.ui.components.form_kit_v2 import (
    inject_form_kit_v2_css,
    ps_input_block,
    ps_primary_money_input,
    ps_primary_ratio_input,
    ps_secondary_select,
    ps_note_input,
)
from src.storage_supabase import load_csv, save_ingredient, update_ingredient, delete_ingredient
from src.auth import get_current_store_id, get_supabase_client
from src.analytics import calculate_ingredient_usage
# 분석/전략 관련 import 제거 (P3: 입력 전용 페이지로 역할 분리)
# TODO: 분석센터로 이동 예정
# from src.analytics import calculate_order_recommendation

logger = logging.getLogger(__name__)

# 공통 설정 적용
bootstrap(page_title="사용 재료 입력")

# 재료 분류 옵션
INGREDIENT_CATEGORIES = ["채소", "육류", "해산물", "조미료", "기타"]
INGREDIENT_STATUSES = ["사용중", "사용중지"]
UNIT_OPTIONS = ["g", "ml", "ea", "개", "kg", "L", "박스", "봉지"]


def render_ingredient_input_page():
    """사용 재료 입력 (FormKit v2 + 블록 리듬, ActionBar만 저장)"""
    inject_form_kit_css()
    inject_form_kit_v2_css("ingredient_input")
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    # 데이터 로드
    ingredient_df = load_csv('ingredient_master.csv', store_id=store_id, 
                            default_columns=['재료명', '단위', '단가', '발주단위', '변환비율'])
    
    # 재료 분류 로드 (DB에서) - 매번 새로 조회 (캐시 사용 안 함)
    # 세션 상태에 저장하지 않고 매번 DB에서 직접 조회하여 최신 데이터 보장
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
    
    # 발주 필요 여부 확인 (입력 상태 확인용 - 추천 로직 제거)
    # TODO: 발주 추천 로직은 분석센터로 이동 예정
    needs_order = {}
    # 발주 필요 여부는 재고 정보에서 직접 확인 (안전재고 대비 현재고)
    if not ingredient_df.empty and not inventory_df.empty:
        try:
            for _, row in inventory_df.iterrows():
                ingredient_name = row.get('재료명')
                current_stock = float(row.get('현재고', 0) or 0)
                safety_stock = float(row.get('안전재고', 0) or 0)
                if ingredient_name and current_stock < safety_stock:
                    needs_order[ingredient_name] = True
        except Exception as e:
            logger.warning(f"발주 필요 여부 확인 실패: {e}")
    
    def render_dashboard_content():
        """Top Dashboard: ZONE A"""
        _render_zone_a_dashboard(ingredient_df, categories, ingredient_in_recipe, needs_order)
    
    def render_work_area_content():
        """Work Area: ZONE B"""
        _render_zone_b_input(store_id)
    
    def render_list_content():
        """List/Editor: ZONE C (Filter) + ZONE D (List)"""
        # ZONE C: 필터 & 검색
        filtered_ingredient_df = _render_zone_c_filters(ingredient_df, categories, ingredient_in_recipe, needs_order)
        st.markdown("---")
        # ZONE D: 재료 목록 & 관리
        _render_zone_d_ingredient_list(filtered_ingredient_df, categories, ingredient_in_recipe, 
                                        recent_usage, needs_order, store_id)
    
    # ActionBar 설정
    action_primary = None
    if "_ingredient_single_save" in st.session_state:
        action_primary = {
            "label": "💾 단일 저장",
            "key": "ingredient_single_save",
            "action": st.session_state["_ingredient_single_save"]
        }
        del st.session_state["_ingredient_single_save"]
    elif "_ingredient_batch_save" in st.session_state:
        action_primary = {
            "label": "💾 일괄 저장",
            "key": "ingredient_batch_save",
            "action": st.session_state["_ingredient_batch_save"]
        }
        del st.session_state["_ingredient_batch_save"]
    
    # CONSOLE형 레이아웃 적용
    render_console_layout(
        title="재료 입력",
        icon="🧺",
        dashboard_content=render_dashboard_content,
        work_area_content=render_work_area_content,
        filter_content=None,
        list_content=render_list_content,
        cta_label=action_primary["label"] if action_primary else None,
        cta_action=action_primary["action"] if action_primary else None
    )
    
    # ZONE E는 레이아웃 외부에 배치 (기존 구조 유지)
    st.markdown("---")
    _render_zone_e_management(ingredient_df, categories, ingredient_in_recipe, recent_usage, store_id)


def _get_ingredient_categories(store_id, ingredient_df):
    """재료 분류 조회 (DB에서) - 매번 새로 조회하여 최신 데이터 보장"""
    categories = {}
    if ingredient_df.empty:
        return categories
    
    # DB에서 category 필드 확인 (캐시 없이 직접 조회)
    supabase = get_supabase_client()
    if supabase:
        try:
            # 모든 재료의 분류를 한 번에 조회
            result = supabase.table("ingredients")\
                .select("name,category")\
                .eq("store_id", store_id)\
                .execute()
            
            if result.data:
                for row in result.data:
                    ingredient_name = row.get('name')
                    category_value = row.get('category')
                    # category가 None이 아니고 빈 문자열이 아니면 저장
                    if ingredient_name:
                        if category_value and category_value.strip():
                            categories[ingredient_name] = category_value.strip()
                        # category가 None이거나 빈 문자열이면 딕셔너리에 추가하지 않음 (미지정으로 표시됨)
            
            logger.debug(f"재료 분류 조회 완료: {len(categories)}개 재료에 분류가 있음")
        except Exception as e:
            logger.error(f"재료 분류 조회 실패: {e}")
            logger.exception(e)  # 상세 에러 로그
    
    return categories


def _set_ingredient_category(store_id, ingredient_name, category):
    """재료 분류 저장 (DB)"""
    supabase = get_supabase_client()
    if not supabase:
        logger.error("Supabase 클라이언트를 가져올 수 없습니다.")
        return False
    
    try:
        # 재료 ID 찾기
        result = supabase.table("ingredients")\
            .select("id,category")\
            .eq("store_id", store_id)\
            .eq("name", ingredient_name)\
            .execute()
        
        if not result.data or len(result.data) == 0:
            logger.error(f"재료를 찾을 수 없습니다: {ingredient_name} (store_id: {store_id})")
            return False
        
        ingredient_id = result.data[0]['id']
        # 빈 문자열이면 NULL로 설정 (분류 제거)
        update_value = category if category and category.strip() else None
        
        # 업데이트 실행 (에러 처리 강화)
        try:
            update_result = supabase.table("ingredients")\
                .update({"category": update_value})\
                .eq("id", ingredient_id)\
                .execute()
        except Exception as update_error:
            # 컬럼이 없을 수 있음
            error_msg = str(update_error)
            if "column" in error_msg.lower() and "does not exist" in error_msg.lower():
                logger.error(f"category 컬럼이 존재하지 않습니다. SQL 스키마를 실행해주세요: sql/schema_ingredient_category.sql")
                logger.error(f"에러 상세: {error_msg}")
                return False
            else:
                raise  # 다른 에러는 그대로 전파
        
        # 업데이트 확인 및 검증
        if update_result.data:
            updated_category = update_result.data[0].get('category')
            logger.info(f"재료 분류 저장 성공: {ingredient_name} -> {update_value} (id: {ingredient_id}, DB 저장값: {updated_category})")
        else:
            logger.warning(f"재료 분류 업데이트 결과가 없습니다: {ingredient_name}")
            # 결과가 없어도 업데이트는 성공했을 수 있으므로 확인
            verify_result = supabase.table("ingredients")\
                .select("category")\
                .eq("id", ingredient_id)\
                .execute()
            if verify_result.data:
                actual_category = verify_result.data[0].get('category')
                logger.info(f"재료 분류 저장 확인: {ingredient_name} -> DB에 저장된 값: {actual_category}")
        
        # 저장 후 즉시 DB에서 다시 조회하여 확인
        verify_result = supabase.table("ingredients")\
            .select("name,category")\
            .eq("store_id", store_id)\
            .eq("name", ingredient_name)\
            .execute()
        
        if verify_result.data:
            actual_category = verify_result.data[0].get('category')
            logger.info(f"재료 분류 저장 최종 확인: {ingredient_name} -> DB에 저장된 값: {actual_category if actual_category else 'NULL'}")
            if actual_category != update_value:
                logger.warning(f"재료 분류 저장 불일치: 저장하려던 값={update_value}, 실제 DB 값={actual_category}")
        
        # 캐시 무효화 (재료 데이터 갱신 필요)
        try:
            from src.storage_supabase import soft_invalidate, clear_session_cache
            # 소프트 무효화
            soft_invalidate(
                reason=f"재료 분류 수정: {ingredient_name}",
                targets=["ingredients"],
                session_keys=['ss_ingredient_master_df']
            )
            # 세션 캐시 직접 클리어 (즉시 반영)
            clear_session_cache('ss_ingredient_master_df')
            # load_csv 캐시도 무효화 (상단에서 이미 import했으므로 그대로 사용)
            try:
                load_csv.clear()
            except Exception as e:
                logger.warning(f"load_csv 캐시 클리어 실패: {e}")
        except Exception as e:
            logger.warning(f"캐시 무효화 실패: {e}")
        
        return True
    except Exception as e:
        logger.error(f"재료 분류 저장 실패: {ingredient_name}, 오류: {e}")
        logger.exception(e)  # 상세 에러 로그
        return False


def _set_ingredient_status_and_notes(store_id, ingredient_name, status=None, notes=None):
    """재료 상태 및 메모 저장 (DB)"""
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
            update_data = {}
            
            if status is not None:
                update_data["status"] = status
            if notes is not None:
                update_data["notes"] = notes.strip() if notes and notes.strip() else None
            
            if update_data:
                supabase.table("ingredients")\
                    .update(update_data)\
                    .eq("id", ingredient_id)\
                    .execute()
                return True
    except Exception as e:
        logger.warning(f"재료 상태/메모 저장 실패: {e}")
        # DB에 컬럼이 없을 수 있으므로 경고만 하고 계속 진행
    
    return False


def _render_zone_a_dashboard(ingredient_df, categories, ingredient_in_recipe, needs_order):
    """ZONE A: 대시보드 & 현황 요약 (입력 상태 확인용)"""
    ps_section("재료 현황", icon="📊")
    
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
    
    # 입력 상태 확인 알림 (입력 오류/주의로만 표현)
    alerts = []
    if ingredients_in_recipe_count < total_ingredients:
        alerts.append(f"ℹ️ 레시피 미사용 재료: {total_ingredients - ingredients_in_recipe_count}개")
    if ingredients_with_category < total_ingredients:
        alerts.append(f"ℹ️ 재료 분류 미지정: {total_ingredients - ingredients_with_category}개")
    if needs_order_count > 0:
        alerts.append(f"⚠️ 발주 필요 재료: {needs_order_count}개")
    
    if alerts:
        for alert in alerts:
            st.caption(alert)


def _render_zone_b_input(store_id):
    """Work Area: 재료 입력 (단일/일괄 블록 분리)"""
    tab1, tab2 = st.tabs(["📝 단일 입력", "📋 일괄 입력"])
    
    with tab1:
        _render_single_input(store_id)
    
    with tab2:
        _render_batch_input(store_id)


def _render_single_input(store_id):
    """단일 재료 입력 (FormKit v2, ActionBar만 저장)"""
    def _body_single():
        col1, col2, col3 = st.columns(3)
        with col1:
            st.text_input("재료명 *", key="ingredient_input_single_name", placeholder="재료명을 입력하세요")
        with col2:
            ps_secondary_select("단위 *", key="ingredient_input_single_unit", options=UNIT_OPTIONS, index=0)
        with col3:
            ps_primary_money_input("단가 (원/단위) *", key="ingredient_input_single_price", value=0.0, min_value=0.0, step=100.0, unit="원")
        
        st.markdown("**📦 발주 단위 설정 (선택사항)**")
        col4, col5 = st.columns(2)
        with col4:
            ps_secondary_select("발주 단위", key="ingredient_input_single_order_unit", options=[""] + UNIT_OPTIONS, index=0, help_text="발주 시 사용할 단위 (비워두면 기본 단위와 동일)")
        with col5:
            ps_primary_ratio_input("변환 비율 (1 발주단위 = ? 기본단위)", key="ingredient_input_single_conversion_rate", value=1.0, min_value=0.1, step=0.1, compact=True, help_text="예: 버터 1개 = 500g이면 500 입력")
        
        col6, col7 = st.columns(2)
        with col6:
            ps_secondary_select("재료 분류", key="ingredient_input_single_category", options=[""] + INGREDIENT_CATEGORIES, index=0)
        with col7:
            ps_secondary_select("상태", key="ingredient_input_single_status", options=INGREDIENT_STATUSES, index=0)
        
        ps_note_input("메모 (선택)", key="ingredient_input_single_notes", value="", height=100)
    
    ps_input_block(title="재료 단일 등록", description="재료명, 단가, 단위, 발주단위/변환비율 입력", level="primary", body_fn=_body_single)
    
    def handle_save_single():
        ingredient_name = st.session_state.get("ingredient_input_single_name", "").strip()
        unit = st.session_state.get("ingredient_input_single_unit", UNIT_OPTIONS[0])
        unit_price = st.session_state.get("ingredient_input_single_price", 0.0) or 0.0
        order_unit = st.session_state.get("ingredient_input_single_order_unit", "")
        conversion_rate = st.session_state.get("ingredient_input_single_conversion_rate", 1.0) or 1.0
        category = st.session_state.get("ingredient_input_single_category", "")
        status = st.session_state.get("ingredient_input_single_status", INGREDIENT_STATUSES[0])
        notes = st.session_state.get("ingredient_input_single_notes", "")
        
        if not ingredient_name:
            ui_flash_error("재료명을 입력해주세요.")
            return
        if unit_price <= 0:
            ui_flash_error("단가를 입력해주세요.")
            return
        if conversion_rate <= 0:
            ui_flash_error("변환 비율은 0보다 큰 값이어야 합니다.")
            return
        
        try:
            success, msg = save_ingredient(ingredient_name, unit, float(unit_price), order_unit.strip() if order_unit else None, float(conversion_rate))
            if not success:
                ui_flash_error(msg)
                return
            if category and category.strip():
                _set_ingredient_category(store_id, ingredient_name, category.strip())
            status_value = status if status else "사용중"
            notes_value = notes.strip() if notes else None
            _set_ingredient_status_and_notes(store_id, ingredient_name, status_value, notes_value)
            ui_flash_success(f"재료 '{ingredient_name}'이(가) 저장되었습니다.")
            st.rerun()
        except Exception as e:
            logger.error(f"재료 저장 중 예외 발생: {e}")
            ui_flash_error(f"저장 실패: {str(e)}")
    
    st.session_state["_ingredient_single_save"] = handle_save_single


def _render_batch_input(store_id):
    """일괄 재료 입력 (FormKit v2, ActionBar만 저장)"""
    def _body_batch():
        ingredient_count = st.number_input("등록할 재료 개수", min_value=1, max_value=20, value=5, step=1, key="ingredient_input_batch_count")
        
        col_batch1, col_batch2 = st.columns(2)
        with col_batch1:
            batch_category = ps_secondary_select("일괄 재료 분류", key="ingredient_input_batch_category", options=[""] + INGREDIENT_CATEGORIES, index=0)
        with col_batch2:
            batch_status = ps_secondary_select("일괄 상태", key="ingredient_input_batch_status", options=[""] + INGREDIENT_STATUSES, index=0)
        
        st.markdown("---")
        st.write(f"**📋 총 {ingredient_count}개 재료 입력**")
        
        for i in range(ingredient_count):
            with st.expander(f"재료 {i+1}", expanded=(i < 3)):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.text_input(f"재료명 {i+1}", key=f"ingredient_input_batch_name_{i}")
                with col2:
                    ps_secondary_select(f"단위 {i+1}", key=f"ingredient_input_batch_unit_{i}", options=UNIT_OPTIONS, index=0)
                with col3:
                    ps_primary_money_input(f"단가 (원) {i+1}", key=f"ingredient_input_batch_price_{i}", value=0.0, min_value=0.0, step=100.0, unit="원", compact=True)
                
                col4, col5 = st.columns(2)
                with col4:
                    ps_secondary_select(f"발주단위 {i+1}", key=f"ingredient_input_batch_order_unit_{i}", options=[""] + UNIT_OPTIONS, index=0)
                with col5:
                    ps_primary_ratio_input(f"변환비율 {i+1}", key=f"ingredient_input_batch_conversion_{i}", value=1.0, min_value=0.1, step=0.1, compact=True)
                
                col6, col7 = st.columns(2)
                with col6:
                    cat_idx = INGREDIENT_CATEGORIES.index(batch_category) + 1 if batch_category and batch_category in INGREDIENT_CATEGORIES else 0
                    ps_secondary_select(f"재료 분류 {i+1}", key=f"ingredient_input_batch_category_{i}", options=[""] + INGREDIENT_CATEGORIES, index=cat_idx)
                with col7:
                    status_idx = INGREDIENT_STATUSES.index(batch_status) if batch_status and batch_status in INGREDIENT_STATUSES else 0
                    ps_secondary_select(f"상태 {i+1}", key=f"ingredient_input_batch_status_{i}", options=INGREDIENT_STATUSES, index=status_idx)
    
    ps_input_block(title="재료 일괄 등록", description="여러 재료를 한 번에 등록", level="secondary", body_fn=_body_batch)
    
    def handle_save_batch():
        ingredient_count = st.session_state.get("ingredient_input_batch_count", 5)
        ingredient_data = []
        for i in range(ingredient_count):
            name = st.session_state.get(f"ingredient_input_batch_name_{i}", "").strip()
            unit = st.session_state.get(f"ingredient_input_batch_unit_{i}", UNIT_OPTIONS[0])
            price = st.session_state.get(f"ingredient_input_batch_price_{i}", 0.0) or 0.0
            order_unit = st.session_state.get(f"ingredient_input_batch_order_unit_{i}", "")
            conversion = st.session_state.get(f"ingredient_input_batch_conversion_{i}", 1.0) or 1.0
            category = st.session_state.get(f"ingredient_input_batch_category_{i}", "")
            status = st.session_state.get(f"ingredient_input_batch_status_{i}", INGREDIENT_STATUSES[0])
            
            if name and price > 0:
                ingredient_data.append({
                    'name': name,
                    'unit': unit,
                    'price': float(price),
                    'order_unit': order_unit.strip() if order_unit else None,
                    'conversion_rate': float(conversion) if conversion > 0 else 1.0,
                    'category': category.strip() if category else None,
                    'status': status
                })
        
        if not ingredient_data:
            ui_flash_error("저장할 재료가 없습니다. 재료명과 단가를 입력해주세요.")
            return
        
        try:
            saved_count = 0
            failed_items = []
            for ing in ingredient_data:
                try:
                    success, msg = save_ingredient(ing['name'], ing['unit'], ing['price'], ing['order_unit'], ing['conversion_rate'])
                    if success:
                        if ing.get('category') and ing['category'].strip():
                            _set_ingredient_category(store_id, ing['name'], ing['category'].strip())
                        status_value = ing.get('status', '사용중')
                        _set_ingredient_status_and_notes(store_id, ing['name'], status_value, None)
                        saved_count += 1
                    else:
                        failed_items.append(f"{ing['name']}: {msg}")
                except Exception as e:
                    logger.error(f"재료 저장 중 예외 발생 ({ing['name']}): {e}")
                    failed_items.append(f"{ing['name']}: {str(e)}")
            
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
    
    st.session_state["_ingredient_batch_save"] = handle_save_batch


def _render_zone_c_filters(ingredient_df, categories, ingredient_in_recipe, needs_order):
    """ZONE C: 필터 & 검색"""
    # Filter Bar는 1줄 규칙 (섹션 헤더 제거, 바로 필터 표시)
    
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
    ps_section("재료 목록", icon="📋")
    
    if ingredient_df.empty:
        st.info("등록된 재료가 없습니다.")
        return
    
    # 목록 표시
    st.markdown("### 재료 목록")
    
    # 컬럼 헤더 표시
    header_col1, header_col2, header_col3, header_col4, header_col5, header_col6, header_col7, header_col8 = st.columns([3, 2, 2, 2, 2, 2, 2, 3])
    with header_col1:
        st.markdown("**재료명**")
    with header_col2:
        st.markdown("**재료 분류**")
    with header_col3:
        st.markdown("**단위**")
    with header_col4:
        st.markdown("**단가**")
    with header_col5:
        st.markdown("**발주단위/변환비율**")
    with header_col6:
        st.markdown("**레시피 사용**")
    with header_col7:
        st.markdown("**사용량/발주**")
    with header_col8:
        st.markdown("**관리**")
    
    st.markdown("---")
    
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
                    edit_key = f"ingredient_input_btn_edit_{ingredient_name}"
                    if st.button("✏️", key=edit_key, help="수정"):
                        st.session_state[f"ingredient_input_edit_{ingredient_name}"] = True
                        st.rerun()
                with action_col2:
                    delete_key = f"ingredient_input_btn_delete_{ingredient_name}"
                    if st.button("🗑️", key=delete_key, help="삭제"):
                        st.session_state[f"ingredient_input_delete_{ingredient_name}"] = True
                        st.rerun()
                with action_col3:
                    if in_recipe:
                        recipe_key = f"ingredient_input_btn_recipe_{ingredient_name}"
                        if st.button("📋", key=recipe_key, help="레시피 보기"):
                            st.session_state[f"ingredient_input_view_recipe_{ingredient_name}"] = True
                            st.rerun()
                    else:
                        st.markdown("—")
                with action_col4:
                    if needs_order_flag:
                        order_key = f"ingredient_input_btn_order_{ingredient_name}"
                        if st.button("🛒", key=order_key, help="발주 관리", type="primary"):
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
                    # 재료 분류 선택 (빈 문자열 = 분류 제거)
                    category_options = [""] + INGREDIENT_CATEGORIES
                    category_index = 0
                    if category and category in INGREDIENT_CATEGORIES:
                        category_index = INGREDIENT_CATEGORIES.index(category) + 1
                    new_category = st.selectbox("재료 분류", options=category_options,
                                               index=category_index,
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
                                        
                                        # 재료 분류 저장 (빈 문자열도 처리 - 분류 제거)
                                        if new_category is not None:
                                            # 빈 문자열이면 분류 제거, 아니면 저장
                                            category_to_save = new_category.strip() if new_category.strip() else None
                                            # 재료명이 변경되었을 수 있으므로 new_name 사용
                                            category_success = _set_ingredient_category(store_id, new_name.strip(), category_to_save)
                                            if not category_success:
                                                logger.error(f"재료 분류 저장 실패: {new_name.strip()}, category: {category_to_save}")
                                                ui_flash_error(f"재료 분류 저장에 실패했습니다: {new_name.strip()}")
                                            else:
                                                logger.info(f"재료 분류 저장 성공: {new_name.strip()} -> {category_to_save}")
                                                # 저장 후 즉시 DB에서 확인
                                                verify_result = supabase.table("ingredients")\
                                                    .select("name,category")\
                                                    .eq("store_id", store_id)\
                                                    .eq("name", new_name.strip())\
                                                    .execute()
                                                if verify_result.data:
                                                    actual_category = verify_result.data[0].get('category')
                                                    logger.info(f"재료 분류 저장 확인: {new_name.strip()} -> DB에 저장된 값: {actual_category}")
                                        
                                        # 재료 상태 저장 (수정 시에는 상태 변경 없음 - 필요시 추가)
                                        # 현재는 수정 모달에 상태 필드가 없으므로 생략
                                        
                                        # 캐시 무효화 (데이터 갱신) - _set_ingredient_category에서 이미 처리하지만 추가로 확실히
                                        try:
                                            from src.storage_supabase import soft_invalidate, clear_session_cache
                                            soft_invalidate(
                                                reason=f"재료 수정: {ingredient_name} -> {new_name.strip()}",
                                                targets=["ingredients"],
                                                session_keys=['ss_ingredient_master_df']
                                            )
                                            # 세션 캐시 직접 클리어
                                            clear_session_cache('ss_ingredient_master_df')
                                            # load_csv 캐시도 무효화 (상단에서 이미 import했으므로 그대로 사용)
                                            try:
                                                load_csv.clear()
                                            except Exception as e:
                                                logger.warning(f"load_csv 캐시 클리어 실패: {e}")
                                        except Exception as e:
                                            logger.warning(f"캐시 무효화 실패: {e}")
                                        
                                        # 수정 완료 후 세션 상태 초기화 및 강제 새로고침
                                        st.session_state[f"ingredient_input_edit_{ingredient_name}"] = False
                                        
                                        # 모든 관련 세션 캐시 클리어
                                        try:
                                            from src.storage_supabase import clear_session_cache
                                            clear_session_cache('ss_ingredient_master_df')
                                        except Exception as e:
                                            logger.warning(f"세션 캐시 클리어 실패: {e}")
                                        
                                        ui_flash_success(f"재료 '{new_name.strip()}'이(가) 수정되었습니다.")
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
    """ZONE E: 입력 작업 안내 (Bottom CTA)"""
    # 분석/전략 요소 제거: 재료 분류 현황, 통계, TOP 5, 설계실 이동 버튼 제거
    # TODO: 분석센터로 이동 예정
    
    if ingredient_df.empty:
        st.info("등록된 재료가 없습니다. 위에서 재료를 등록해주세요.")
        return
    
    # 발주 단위 미설정 재료 보기 (입력 작업 안내)
    ingredients_without_order_unit = []
    for _, row in ingredient_df.iterrows():
        ingredient_name = row['재료명']
        order_unit = row.get('발주단위', '')
        unit = row.get('단위', '')
        if not order_unit or order_unit == unit:
            ingredients_without_order_unit.append(ingredient_name)
    
    if ingredients_without_order_unit:
        ps_section("다음 입력 작업", icon="📌")
        st.caption(f"발주 단위 미설정 재료: {len(ingredients_without_order_unit)}개")
        if st.button("📦 발주 단위 미설정 재료 보기", key="show_ingredients_without_order_unit", use_container_width=True):
            # 필터에 발주 단위 미설정 조건 추가 (필터 로직은 향후 구현)
            st.info("발주 단위를 설정하려면 재료 목록에서 수정하세요.")
