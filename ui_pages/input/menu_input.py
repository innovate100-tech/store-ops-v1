"""
메뉴 입력 페이지 (입력 전용)
설계 기능 없이 메뉴 등록만 수행
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
import logging
from src.ui_helpers import render_page_header, ui_flash_success, ui_flash_error
from src.ui import render_menu_input, render_menu_batch_input
from src.storage_supabase import load_csv, save_menu
from src.auth import get_current_store_id

logger = logging.getLogger(__name__)

# 공통 설정 적용
bootstrap(page_title="Menu Input")


def render_menu_input_page():
    """메뉴 입력 페이지 렌더링 (입력 전용)"""
    render_page_header("📘 메뉴 입력", "📘")
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    st.info("💡 메뉴를 등록하면 레시피와 원가 계산이 가능합니다.")
    st.markdown("---")
    
    # 탭: 단일 입력 / 일괄 입력
    tab1, tab2 = st.tabs(["📝 단일 입력", "📋 일괄 입력"])
    
    with tab1:
        st.markdown("### 📝 메뉴 단일 등록")
        menu_name, price = render_menu_input(key_prefix="menu_input_single")
        
        if st.button("💾 저장", type="primary", key="menu_input_single_save"):
            if not menu_name or not menu_name.strip():
                ui_flash_error("메뉴명을 입력해주세요.")
            elif price <= 0:
                ui_flash_error("판매가를 입력해주세요.")
            else:
                try:
                    save_menu(menu_name.strip(), int(price))
                    ui_flash_success(f"메뉴 '{menu_name.strip()}'이(가) 저장되었습니다.")
                    # 입력 필드 초기화를 위해 rerun
                    st.rerun()
                except Exception as e:
                    ui_flash_error(f"저장 실패: {str(e)}")
    
    with tab2:
        st.markdown("### 📋 메뉴 일괄 등록")
        menu_data = render_menu_batch_input(key_prefix="menu_input_batch")
        
        if st.button("💾 일괄 저장", type="primary", key="menu_input_batch_save"):
            if not menu_data:
                ui_flash_error("저장할 메뉴가 없습니다. 메뉴명과 판매가를 입력해주세요.")
            else:
                try:
                    saved_count = 0
                    for menu_name, price in menu_data:
                        save_menu(menu_name, int(price))
                        saved_count += 1
                    ui_flash_success(f"{saved_count}개 메뉴가 저장되었습니다.")
                    st.rerun()
                except Exception as e:
                    ui_flash_error(f"저장 실패: {str(e)}")
    
    st.markdown("---")
    
    # 등록된 메뉴 목록 (상태 표시 포함)
    st.markdown("### 📋 등록된 메뉴 목록")
    menu_df = load_csv('menu_master.csv', store_id=store_id, default_columns=['메뉴명', '판매가'])
    
    if menu_df.empty:
        st.info("등록된 메뉴가 없습니다.")
    else:
        # 검색 기능
        search_term = st.text_input("🔍 메뉴 검색", key="menu_search", placeholder="메뉴명으로 검색...")
        
        # 검색어로 필터링
        if search_term and search_term.strip():
            menu_df = menu_df[menu_df['메뉴명'].str.contains(search_term, case=False, na=False)]
        
        if menu_df.empty:
            st.info("검색 결과가 없습니다.")
            return
        # 레시피 상태 확인
        from src.auth import get_supabase_client
        supabase = get_supabase_client()
        menu_has_recipe = {}
        
        if supabase:
            try:
                # 메뉴 ID 매핑
                menu_result = supabase.table("menu_master")\
                    .select("id,name")\
                    .eq("store_id", store_id)\
                    .execute()
                menu_id_map = {m['name']: m['id'] for m in menu_result.data if menu_result.data}
                
                if menu_id_map:
                    menu_ids = list(menu_id_map.values())
                    recipe_result = supabase.table("recipes")\
                        .select("menu_id")\
                        .eq("store_id", store_id)\
                        .in_("menu_id", menu_ids)\
                        .execute()
                    
                    recipe_menu_ids = set()
                    if recipe_result.data:
                        recipe_menu_ids = {r['menu_id'] for r in recipe_result.data}
                    
                    id_to_name = {v: k for k, v in menu_id_map.items()}
                    for menu_id in recipe_menu_ids:
                        menu_name = id_to_name.get(menu_id)
                        if menu_name:
                            menu_has_recipe[menu_name] = True
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.warning(f"레시피 상태 확인 실패: {e}")
        
        # 상태 표시가 포함된 데이터프레임 생성
        display_data = []
        for _, row in menu_df.iterrows():
            menu_name = row['메뉴명']
            has_recipe = menu_has_recipe.get(menu_name, False)
            status = "✓ 레시피" if has_recipe else "⚠ 레시피 없음"
            display_data.append({
                '메뉴명': menu_name,
                '판매가': f"{int(row['판매가']):,}원",
                '상태': status
            })
        
        display_df = pd.DataFrame(display_data)
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # 통계 표시
        total_menus = len(menu_df)
        menus_with_recipe = sum(1 for name in menu_df['메뉴명'] if menu_has_recipe.get(name, False))
        menus_without_recipe = total_menus - menus_with_recipe
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("전체 메뉴", f"{total_menus}개")
        with col2:
            st.metric("레시피 있음", f"{menus_with_recipe}개", delta=f"{menus_with_recipe/total_menus*100:.0f}%" if total_menus > 0 else None)
        with col3:
            st.metric("레시피 없음", f"{menus_without_recipe}개", delta=f"-{menus_without_recipe/total_menus*100:.0f}%" if total_menus > 0 else None)
        
        if menus_without_recipe > 0:
            st.info(f"💡 레시피가 없는 메뉴가 {menus_without_recipe}개 있습니다. 레시피를 등록하면 원가 계산이 가능합니다.")
            if st.button("🧑‍🍳 레시피 입력하러 가기", key="go_to_recipe_input_from_menu"):
                st.session_state["current_page"] = "레시피 입력"
                st.rerun()
