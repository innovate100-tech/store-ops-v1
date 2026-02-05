"""
레시피 등록 페이지 (FormKit v2 + 블록 리듬)
CONSOLE형: 입력 컴포넌트만 FormKit v2로 통일
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
from src.ui_helpers import safe_get_value, ui_flash_success, ui_flash_error
from src.ui.layouts.input_layouts import render_console_layout
from src.ui.components.form_kit import inject_form_kit_css, ps_section
from src.ui.components.form_kit_v2 import (
    inject_form_kit_v2_css,
    ps_input_block,
    ps_primary_quantity_input,
    ps_secondary_select,
    ps_note_input,
    ps_inline_feedback,
)
from src.storage_supabase import load_csv, save_recipe, update_menu_cooking_method, delete_recipe
from src.analytics import calculate_menu_cost

# 공통 설정 적용
bootstrap(page_title="Recipe Management")


def render_recipe_management():
    """레시피 입력 (FormKit v2 + 블록 리듬, ActionBar만 저장)"""
    inject_form_kit_css()
    inject_form_kit_v2_css("recipe_management")
    
    # 메뉴 및 재료 목록 로드
    menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
    ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가'])
    
    menu_list = menu_df['메뉴명'].tolist() if not menu_df.empty else []
    ingredient_list = ingredient_df['재료명'].tolist() if not ingredient_df.empty else []
    
    def render_dashboard_content():
        """Top Dashboard: 메뉴/재료 현황"""
        st.metric("등록 메뉴", f"{len(menu_list)}개")
        st.metric("등록 재료", f"{len(ingredient_list)}개")
    
    def render_work_area_content():
        """Work Area: 레시피 입력 (FormKit v2, ActionBar만 저장)"""
        if not menu_list:
            st.warning("먼저 메뉴를 등록해주세요.")
            return
        if not ingredient_list:
            st.warning("먼저 재료를 등록해주세요.")
            return
        
        def _body_recipe():
            st.info("💡 한 메뉴에 여러 재료를 한 번에 등록할 수 있습니다. (최대 30개 재료)")
            
            ps_secondary_select("메뉴 선택", key="recipe_management_batch_recipe_menu", options=menu_list, index=0)
            ingredient_count = st.number_input("등록할 재료 개수", min_value=1, max_value=30, value=10, step=1, key="recipe_management_batch_recipe_count")
            
            st.markdown("---")
            st.write(f"**📋 총 {ingredient_count}개 재료 입력**")
            # 재료가 많을 때 드롭다운 목록을 좁히기 위한 공통 검색
            global_search = st.text_input(
                "🔍 재료 검색 (아래 모든 행의 드롭다운에 공통 적용)",
                key="recipe_management_ingredient_search",
                placeholder="재료명 일부를 입력하면 선택 목록이 필터됩니다..."
            )
            if global_search and global_search.strip():
                base_ingredient_list = [ing for ing in ingredient_list if global_search.strip().lower() in ing.lower()]
                if not base_ingredient_list:
                    base_ingredient_list = ingredient_list
            else:
                base_ingredient_list = ingredient_list
            
            # 재료 정보를 딕셔너리로 변환 (검색 및 단위/단가 조회용)
            ingredient_info_dict = {}
            if not ingredient_df.empty:
                for _, row in ingredient_df.iterrows():
                    ingredient_info_dict[row['재료명']] = {
                        '단위': row.get('단위', ''),
                        '단가': float(row.get('단가', 0))
                    }
            
            # 각 재료별 입력 필드 (재료명, 기준단위, 사용량, 사용단가)
            recipe_data = []
            
            # 컴팩트 스타일 CSS 추가 (세로 구분선 포함, 엑셀처럼 오밀조밀하게)
            st.markdown("""
        <style>
        .compact-recipe-row {
            margin: 0.05rem 0 !important;
            padding: 0.1rem 0 !important;
        }
        /* 입력 필드 높이 최소화 */
        .compact-recipe-row [data-testid="stTextInput"] {
            margin-bottom: 0.1rem !important;
        }
        .compact-recipe-row [data-testid="stTextInput"] > div > div {
            padding-top: 0.1rem !important;
            padding-bottom: 0.1rem !important;
            min-height: 28px !important;
            height: 28px !important;
        }
        .compact-recipe-row [data-testid="stTextInput"] input {
            padding: 0.2rem 0.5rem !important;
            font-size: 0.85rem !important;
            line-height: 1.2 !important;
        }
        .compact-recipe-row [data-testid="stSelectbox"] {
            margin-bottom: 0.1rem !important;
        }
        .compact-recipe-row [data-testid="stSelectbox"] > div > div {
            padding-top: 0.1rem !important;
            padding-bottom: 0.1rem !important;
            min-height: 28px !important;
            height: 28px !important;
        }
        .compact-recipe-row [data-testid="stSelectbox"] select {
            padding: 0.2rem 0.5rem !important;
            font-size: 0.85rem !important;
            line-height: 1.2 !important;
        }
        .compact-recipe-row [data-testid="stNumberInput"] {
            margin-bottom: 0.1rem !important;
        }
        .compact-recipe-row [data-testid="stNumberInput"] > div > div {
            padding-top: 0.1rem !important;
            padding-bottom: 0.1rem !important;
            min-height: 28px !important;
            height: 28px !important;
        }
        .compact-recipe-row [data-testid="stNumberInput"] input {
            padding: 0.2rem 0.5rem !important;
            font-size: 0.85rem !important;
            line-height: 1.2 !important;
        }
        /* 텍스트 표시 영역도 컴팩트하게 */
        .compact-recipe-row div[style*="margin-top: 0.5rem"] {
            margin-top: 0.2rem !important;
            margin-bottom: 0.1rem !important;
            font-size: 0.85rem !important;
            line-height: 1.3 !important;
        }
        /* 세로 구분선: 컬럼 사이에 얇은 선 표시 */
        .compact-recipe-row > div[data-testid="column"] {
            border-right: 1px solid rgba(148, 163, 184, 0.35);
            padding-right: 0.3rem;
            padding-left: 0.3rem;
        }
        .compact-recipe-row > div[data-testid="column"]:last-child {
            border-right: none;
        }
        /* 컬럼 간격 최소화 */
        .compact-recipe-row [data-testid="column"] {
            padding-left: 0.2rem !important;
            padding-right: 0.2rem !important;
        }
        </style>
            """, unsafe_allow_html=True)
            
            # 헤더 행
            header_col1, header_col2, header_col3, header_col4 = st.columns([3, 1.5, 2, 2])
            with header_col1:
                st.markdown("**재료명** (검색 가능)")
            with header_col2:
                st.markdown("**기준단위**")
            with header_col3:
                st.markdown("**사용량**")
            with header_col4:
                st.markdown("**사용단가**")
            
            st.markdown("<hr style='margin: 0.1rem 0; border-color: rgba(255,255,255,0.1); border-width: 0.5px;'>", unsafe_allow_html=True)
            
            for i in range(ingredient_count):
                # 컴팩트 행 컨테이너
                with st.container():
                    st.markdown('<div class="compact-recipe-row">', unsafe_allow_html=True)
                    col1, col2, col3, col4 = st.columns([3, 1.5, 2, 2])
                    
                    with col1:
                        # 재료 선택 옵션 (상단 검색으로 필터된 목록 사용)
                        ingredient_options = []
                        if '발주단위' in ingredient_df.columns:
                            for ing in base_ingredient_list:
                                ing_row = ingredient_df[ingredient_df['재료명'] == ing]
                                if not ing_row.empty:
                                    # Phase 1: 안전한 DataFrame 접근
                                    unit = safe_get_value(ing_row, '단위', '')
                                    order_unit = safe_get_value(ing_row, '발주단위', unit)
                                    if order_unit != unit:
                                        ingredient_options.append(f"{ing} ({unit} / 발주: {order_unit})")
                                    else:
                                        ingredient_options.append(f"{ing} ({unit})")
                                else:
                                    ingredient_options.append(ing)
                        else:
                            ingredient_options = base_ingredient_list
                        
                        # 재료 선택 (상단 검색 필터 적용된 목록)
                        ingredient_key = f"batch_recipe_ingredient_{i}"
                        selected_ingredient_option = st.selectbox(
                            "",
                            options=ingredient_options,
                            key=ingredient_key,
                            index=None,
                            label_visibility="collapsed"
                        )
                        
                        # 선택된 옵션에서 재료명 추출
                        selected_ingredient = selected_ingredient_option.split(" (")[0] if selected_ingredient_option and " (" in selected_ingredient_option else selected_ingredient_option
                    
                    with col2:
                        # 기준단위 (자동 표시, 발주 단위도 함께 표시)
                        if selected_ingredient and selected_ingredient in ingredient_info_dict:
                            unit = ingredient_info_dict[selected_ingredient]['단위']
                            # 발주 단위 정보 가져오기
                            if '발주단위' in ingredient_df.columns:
                                ing_row = ingredient_df[ingredient_df['재료명'] == selected_ingredient]
                                if not ing_row.empty:
                                    # Phase 1: 안전한 DataFrame 접근
                                    order_unit = safe_get_value(ing_row, '발주단위', unit)
                                    if order_unit != unit:
                                        unit_display = f"{unit} / 발주: {order_unit}"
                                    else:
                                        unit_display = unit
                                else:
                                    unit_display = unit
                            else:
                                unit_display = unit
                            st.markdown(f"<div style='margin-top: 0.2rem; margin-bottom: 0.1rem; font-size: 0.85rem;'><strong>{unit_display}</strong></div>", unsafe_allow_html=True)
                        else:
                            st.markdown("<div style='margin-top: 0.2rem; margin-bottom: 0.1rem; font-size: 0.85rem;'>-</div>", unsafe_allow_html=True)
                    
                    with col3:
                        # 사용량 입력 (compact quantity)
                        quantity_key = f"batch_recipe_quantity_{i}"
                        unit_for_input = ingredient_info_dict.get(selected_ingredient, {}).get('단위', '') if selected_ingredient else 'g'
                        quantity = ps_primary_quantity_input(
                            "",
                            key=quantity_key,
                            value=0.0,
                            min_value=0.0,
                            step=0.1,
                            unit=unit_for_input or "g"
                        )
                    
                    with col4:
                        # 사용단가 (자동 계산: 사용량 × 1단위 단가) → ps_inline_feedback
                        if selected_ingredient and selected_ingredient in ingredient_info_dict and quantity > 0:
                            unit_price = ingredient_info_dict[selected_ingredient]['단가']
                            total_price = quantity * unit_price
                            ps_inline_feedback("재료비", f"{total_price:,.1f}원", "ok")
                        else:
                            ps_inline_feedback("재료비", "-", "ok")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # 유효한 데이터만 수집
                    if selected_ingredient and quantity > 0:
                        unit = ingredient_info_dict.get(selected_ingredient, {}).get('단위', '')
                        unit_price = ingredient_info_dict.get(selected_ingredient, {}).get('단가', 0)
                        total_price = quantity * unit_price
                        recipe_data.append({
                            'ingredient': selected_ingredient,
                            'quantity': quantity,
                            'unit': unit,
                            'total_price': total_price
                        })
                    
                    # 마지막 행이 아니면 얇은 구분선
                    if i < ingredient_count - 1:
                        st.markdown("<hr style='margin: 0.05rem 0; border-color: rgba(255,255,255,0.05); border-width: 0.5px;'>", unsafe_allow_html=True)
            
            # 조리방법 입력 (ps_note_input)
            st.markdown("**👨‍🍳 조리방법**")
            ps_note_input(
                "조리방법 (줄글로 입력)",
                key="recipe_management_cooking_method_input",
                value="",
                height=150,
                placeholder="예: 1. 재료를 준비합니다.\n2. 팬에 기름을 두르고 재료를 볶습니다.\n3. 물을 넣고 끓입니다.\n4. 간을 맞춰 완성합니다."
            )
            
            # 입력 요약 표시 (분석/통계 최소화)
            if recipe_data:
                st.write("**📊 입력 요약**")
                summary_data = []
                for item in recipe_data:
                    summary_data.append({
                        '재료명': item['ingredient'],
                        '기준단위': item['unit'],
                        '사용량': f"{item['quantity']:.2f}",
                        '사용단가': f"{item['total_price']:,.1f}원"
                    })
                summary_df = pd.DataFrame(summary_data)
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
                st.markdown(f"**총 {len(recipe_data)}개 재료**")
        
        def handle_save_batch():
            selected_menu = st.session_state.get("recipe_management_batch_recipe_menu") or (menu_list[0] if menu_list else None)
            count = int(st.session_state.get("recipe_management_batch_recipe_count", 10))
            cooking_method = (st.session_state.get("recipe_management_cooking_method_input") or "").strip()
            ingredient_info_dict = {}
            if not ingredient_df.empty:
                for _, row in ingredient_df.iterrows():
                    ingredient_info_dict[row["재료명"]] = {"단위": row.get("단위", ""), "단가": float(row.get("단가", 0))}
            recipe_data = []
            for i in range(count):
                opt = st.session_state.get(f"batch_recipe_ingredient_{i}")
                selected_ingredient = (opt.split(" (")[0] if opt and " (" in opt else opt) or None
                q = st.session_state.get(f"batch_recipe_quantity_{i}", 0.0) or 0.0
                if selected_ingredient and q > 0:
                    unit = ingredient_info_dict.get(selected_ingredient, {}).get("단위", "")
                    recipe_data.append({"ingredient": selected_ingredient, "quantity": q, "unit": unit})
            if not recipe_data:
                ui_flash_error("저장할 재료가 없습니다. 재료명과 사용량을 입력해주세요.")
                return
            errors = []
            success_count = 0
            for item in recipe_data:
                try:
                    save_recipe(selected_menu, item["ingredient"], item["quantity"])
                    success_count += 1
                except Exception as e:
                    errors.append(f"{item['ingredient']}: {e}")
            if cooking_method:
                try:
                    ok, msg = update_menu_cooking_method(selected_menu, cooking_method)
                    if not ok:
                        errors.append(f"조리방법: {msg}")
                except Exception as e:
                    errors.append(f"조리방법: {e}")
            if errors:
                ui_flash_error("; ".join(errors))
            if success_count > 0:
                try:
                    st.cache_data.clear()
                except Exception:
                    pass
                ui_flash_success(f"{success_count}개 레시피 저장되었습니다." + (" (조리방법 포함)" if cooking_method else ""))
                st.rerun()
        
        st.session_state["_recipe_batch_save"] = handle_save_batch
        ps_input_block(
            title="레시피 일괄 등록",
            description="메뉴 선택 후 재료·사용량 입력. 저장은 하단 ActionBar에서.",
            level="primary",
            body_fn=_body_recipe
        )
    
    def render_list_content():
        """List: 레시피 검색 및 수정"""
        # 레시피 검색 및 수정 (등록된 레시피 헤더 제거, 메뉴별 편집 UI만 제공)
        recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
        
        if not recipe_df.empty:
            # 레시피가 있는 메뉴 목록 추출
            menus_with_recipes = recipe_df['메뉴명'].unique().tolist()
            
            if menus_with_recipes:
                # 메뉴 필터 (레시피가 있는 메뉴만 표시)
                ps_section("레시피 검색 및 수정", icon="🔍")
                filter_menu = st.selectbox(
                    "메뉴 선택",
                    options=menus_with_recipes,
                    key="recipe_management_recipe_filter_menu",
                    index=0 if menus_with_recipes else None
                )
                
                # 선택한 메뉴의 레시피만 필터링
                display_recipe_df = recipe_df[recipe_df['메뉴명'] == filter_menu].copy()
                
                if not display_recipe_df.empty:
                    # 재료 정보와 조인하여 단위 및 단가 표시
                    display_recipe_df = pd.merge(
                        display_recipe_df,
                        ingredient_df[['재료명', '단위', '단가']],
                        on='재료명',
                        how='left'
                    )
                    
                    # 원가 계산 (이 메뉴의 원가)
                    menu_cost_df = calculate_menu_cost(menu_df, recipe_df, ingredient_df)
                    menu_cost_info = menu_cost_df[menu_cost_df['메뉴명'] == filter_menu]
                    
                    # 메뉴 정보 가져오기 (판매가, 조리방법)
                    menu_info = menu_df[menu_df['메뉴명'] == filter_menu]
                    # Phase 1: 안전한 DataFrame 접근
                    menu_price = int(safe_get_value(menu_info, '판매가', 0)) if not menu_info.empty else 0
                    
                    # 조리방법 가져오기 (menu_master에서)
                    cooking_method_text = ""
                    try:
                        from src.auth import get_supabase_client, get_current_store_id
                        supabase = get_supabase_client()
                        store_id = get_current_store_id()
                        if supabase and store_id:
                            menu_result = supabase.table("menu_master").select("cooking_method").eq("store_id", store_id).eq("name", filter_menu).execute()
                            if menu_result.data and menu_result.data[0].get('cooking_method'):
                                cooking_method_text = menu_result.data[0]['cooking_method']
                    except Exception as e:
                        import logging
                        logging.getLogger(__name__).warning(f"조리방법 조회 실패: {e}")
                    
                    # 원가 정보
                    # Phase 1: 안전한 DataFrame 접근
                    cost = int(safe_get_value(menu_cost_info, '원가', 0)) if not menu_cost_info.empty else 0
                    cost_rate = float(safe_get_value(menu_cost_info, '원가율', 0)) if not menu_cost_info.empty else 0
                    
                    # 요리책 스타일 카드 레이아웃
                    st.markdown(f"""
                    <div style="border-radius: 16px; padding: 2rem; margin: 1rem 0 2rem 0;
                                background: linear-gradient(135deg, #1f2937 0%, #111827 60%, #020617 100%);
                                box-shadow: 0 12px 30px rgba(0,0,0,0.4); border: 2px solid rgba(148,163,184,0.3);">
                        <div style="text-align: center; margin-bottom: 2rem;">
                            <h2 style="margin: 0 0 0.5rem 0; color: #ffffff; font-weight: 800; font-size: 2rem; letter-spacing: 1px;">
                                🍽️ {filter_menu}
                            </h2>
                            <div style="display: flex; justify-content: center; gap: 2rem; margin-top: 1.5rem; flex-wrap: wrap;">
                                <div style="background: rgba(59, 130, 246, 0.2); padding: 0.8rem 1.5rem; border-radius: 8px; border: 1px solid rgba(59, 130, 246, 0.5);">
                                    <div style="color: #93c5fd; font-size: 0.85rem; margin-bottom: 0.3rem;">판매가</div>
                                    <div style="color: #ffffff; font-size: 1.3rem; font-weight: 700;">{menu_price:,}원</div>
                                </div>
                                <div style="background: rgba(239, 68, 68, 0.2); padding: 0.8rem 1.5rem; border-radius: 8px; border: 1px solid rgba(239, 68, 68, 0.5);">
                                    <div style="color: #fca5a5; font-size: 0.85rem; margin-bottom: 0.3rem;">원가</div>
                                    <div style="color: #ffffff; font-size: 1.3rem; font-weight: 700;">{cost:,}원</div>
                                </div>
                                <div style="background: rgba(234, 179, 8, 0.2); padding: 0.8rem 1.5rem; border-radius: 8px; border: 1px solid rgba(234, 179, 8, 0.5);">
                                    <div style="color: #fde047; font-size: 0.85rem; margin-bottom: 0.3rem;">원가율</div>
                                    <div style="color: #ffffff; font-size: 1.3rem; font-weight: 700;">{cost_rate:.1f}%</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 구성 재료 및 사용량 (엑셀처럼 깔끔하게)
                    st.markdown("**📋 구성 재료 및 사용량**")
                    
                    # 엑셀 스타일 테이블 데이터 준비
                    table_data = []
                    for idx, row in display_recipe_df.iterrows():
                        ing_name = row['재료명']
                        unit = row['단위'] if pd.notna(row['단위']) else ""
                        current_qty = float(row['사용량'])
                        unit_price = float(row['단가']) if pd.notna(row['단가']) else 0
                        ingredient_cost = current_qty * unit_price
                        
                        table_data.append({
                            '재료명': ing_name,
                            '기준단위': unit,
                            '사용량': f"{current_qty:.2f}",
                            '1단위 단가': f"{unit_price:,.1f}원",
                            '재료비': f"{ingredient_cost:,.1f}원"
                        })
                    
                    # 엑셀 스타일 테이블 표시
                    ingredients_table_df = pd.DataFrame(table_data)
                    st.dataframe(ingredients_table_df, use_container_width=True, hide_index=True)
                    
                    # 조리방법 표시 (구성 재료 다음에 배치)
                    st.markdown("**👨‍🍳 조리방법**")
                    if cooking_method_text:
                        st.markdown(f"""
                        <div style="background: rgba(30, 41, 59, 0.5); padding: 1.5rem; border-radius: 12px; 
                                    border-left: 4px solid #667eea; margin: 1rem 0;">
                            <div style="color: #e5e7eb; font-size: 1rem; line-height: 1.8; white-space: pre-wrap;">
                                {cooking_method_text.replace(chr(10), '<br>')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.info("조리방법이 등록되지 않았습니다. 레시피 일괄 등록에서 조리방법을 입력해주세요.")
                    
                    # 각 재료별 사용량 수정/삭제 UI
                    st.markdown("**✏️ 재료 사용량 수정 및 삭제**")
                    
                    # 컴팩트 스타일 CSS 추가 (세로 구분선 포함)
                    st.markdown("""
                    <style>
                    .compact-edit-row {
                        margin: 0.2rem 0 !important;
                        padding: 0.3rem 0 !important;
                    }
                    .compact-edit-row [data-testid="stNumberInput"] > div > div {
                        padding-top: 0.3rem !important;
                        padding-bottom: 0.3rem !important;
                    }
                    .compact-edit-row [data-testid="stButton"] {
                        margin-top: 0.2rem !important;
                    }
                    .compact-edit-row [data-testid="stButton"] > button {
                        padding: 0.3rem 0.5rem !important;
                        font-size: 0.85rem !important;
                        height: auto !important;
                    }
                    /* 세로 구분선: 컬럼 사이에 얇은 선 표시 */
                    .compact-edit-row > div[data-testid="column"] {
                        border-right: 1px solid rgba(148, 163, 184, 0.35);
                        padding-right: 0.4rem;
                    }
                    .compact-edit-row > div[data-testid="column"]:last-child {
                        border-right: none;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # 테이블 헤더
                    header_col1, header_col2, header_col3, header_col4, header_col5 = st.columns([2.5, 1, 2, 1.2, 1.2])
                    with header_col1:
                        st.markdown("**재료명**")
                    with header_col2:
                        st.markdown("**단위**")
                    with header_col3:
                        st.markdown("**사용량**")
                    with header_col4:
                        st.markdown("**수정**")
                    with header_col5:
                        st.markdown("**삭제**")
                    
                    st.markdown("<hr style='margin: 0.3rem 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
                    
                    # 각 재료별 사용량 수정/삭제 UI (표 형태)
                    for idx, row in display_recipe_df.iterrows():
                        ing_name = row['재료명']
                        unit = row['단위'] if pd.notna(row['단위']) else ""
                        current_qty = float(row['사용량'])
                        
                        # 컴팩트 행 컨테이너
                        with st.container():
                            st.markdown('<div class="compact-edit-row">', unsafe_allow_html=True)
                            col1, col2, col3, col4, col5 = st.columns([2.5, 1, 2, 1.2, 1.2])
                            
                            with col1:
                                st.markdown(f"<div style='margin-top: 0.5rem;'><strong>{ing_name}</strong></div>", unsafe_allow_html=True)
                            with col2:
                                st.markdown(f"<div style='margin-top: 0.5rem;'>{unit}</div>", unsafe_allow_html=True)
                            with col3:
                                new_qty = st.number_input(
                                    "",
                                    min_value=0.0,
                                    value=current_qty,
                                    step=0.1,
                                    format="%.2f",
                                    key=f"edit_recipe_qty_{filter_menu}_{ing_name}",
                                    label_visibility="collapsed"
                                )
                            with col4:
                                if st.button("💾 수정", key=f"save_recipe_{filter_menu}_{ing_name}", use_container_width=True):
                                    if new_qty <= 0:
                                        st.error("사용량은 0보다 큰 값이어야 합니다.")
                                    else:
                                        try:
                                            save_recipe(filter_menu, ing_name, new_qty)
                                            # 캐시만 클리어하고 rerun 없이 성공 메시지만 표시
                                            try:
                                                st.cache_data.clear()
                                            except Exception as e:
                                                import logging
                                                logging.getLogger(__name__).warning(f"캐시 클리어 실패 (레시피 수정): {e}")
                                            st.success(
                                                f"✅ '{filter_menu}' - '{ing_name}' 사용량이 {new_qty:.2f}{unit} 으로 수정되었습니다."
                                            )
                                        except Exception as e:
                                            st.error(f"사용량 수정 중 오류: {e}")
                            with col5:
                                if st.button("🗑️ 삭제", key=f"delete_recipe_{filter_menu}_{ing_name}", use_container_width=True):
                                    try:
                                        success, msg = delete_recipe(filter_menu, ing_name)
                                        if success:
                                            # 캐시만 클리어하고 rerun 없이 성공 메시지만 표시
                                            try:
                                                st.cache_data.clear()
                                            except Exception as e:
                                                import logging
                                                logging.getLogger(__name__).warning(f"캐시 클리어 실패 (레시피 삭제): {e}")
                                            st.success(f"✅ '{filter_menu}' - '{ing_name}' 레시피가 삭제되었습니다.")
                                        else:
                                            st.error(msg)
                                    except Exception as e:
                                        st.error(f"레시피 삭제 중 오류: {e}")
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            # 마지막 행이 아니면 얇은 구분선
                            if idx < len(display_recipe_df) - 1:
                                st.markdown("<hr style='margin: 0.2rem 0; border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
            else:
                st.info("등록된 레시피가 없습니다.")
        else:
            st.info("등록된 레시피가 없습니다.")
        
        # 레시피 현황 표시
        st.markdown("### 📋 레시피 현황")
        
        total_menus = len(menu_list)
        
        # 레시피가 있는 메뉴 개수 계산
        if not recipe_df.empty:
            menus_with_recipes_count = len(recipe_df['메뉴명'].unique())
            menus_with_recipes_set = set(recipe_df['메뉴명'].unique())
        else:
            menus_with_recipes_count = 0
            menus_with_recipes_set = set()
        
        menus_without_recipes_count = total_menus - menus_with_recipes_count
        recipe_rate = (menus_with_recipes_count / total_menus * 100) if total_menus > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("전체 메뉴", f"{total_menus}개")
        with col2:
            st.metric("레시피 등록", f"{menus_with_recipes_count}개", delta=f"{recipe_rate:.0f}%")
        with col3:
            st.metric("레시피 없음", f"{menus_without_recipes_count}개", delta=f"-{menus_without_recipes_count/total_menus*100:.0f}%" if total_menus > 0 else None)
        
        if menus_without_recipes_count > 0:
            st.info(f"💡 레시피가 없는 메뉴가 {menus_without_recipes_count}개 있습니다. 레시피를 등록하면 원가 계산이 가능합니다.")
            if st.button("📝 레시피 없는 메뉴 보기", key="show_menus_without_recipe"):
                # 레시피가 없는 메뉴 목록 표시
                menus_without_recipes_list = [m for m in menu_list if m not in menus_with_recipes_set]
                
                if menus_without_recipes_list:
                    st.markdown("**레시피가 없는 메뉴:**")
                    for menu_name in menus_without_recipes_list:
                        st.write(f"- {menu_name}")
                else:
                    st.success("모든 메뉴에 레시피가 등록되어 있습니다!")
    
    # ActionBar: 일괄 저장 (Work Area에서 _recipe_batch_save 설정)
    action_primary = None
    if "_recipe_batch_save" in st.session_state:
        action_primary = {
            "label": "💾 일괄 저장",
            "action": st.session_state["_recipe_batch_save"]
        }
        del st.session_state["_recipe_batch_save"]
    
    render_console_layout(
        title="레시피 입력",
        icon="🧑‍🍳",
        dashboard_content=render_dashboard_content,
        work_area_content=render_work_area_content,
        filter_content=None,
        list_content=render_list_content,
        cta_label=action_primary["label"] if action_primary else None,
        cta_action=action_primary["action"] if action_primary else None
    )


# Streamlit 멀티페이지에서 직접 실행될 때
# 주석 처리: app.py에서만 렌더되도록 함 (중복 호출 방지)
# render_recipe_management()
