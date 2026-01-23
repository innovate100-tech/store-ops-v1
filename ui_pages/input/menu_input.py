"""
메뉴 입력 페이지 (입력 전용)
설계 기능 없이 메뉴 등록만 수행
"""
from src.bootstrap import bootstrap
import streamlit as st
from src.ui_helpers import render_page_header, ui_flash_success, ui_flash_error
from src.ui import render_menu_input, render_menu_batch_input
from src.storage_supabase import load_csv, save_menu
from src.auth import get_current_store_id

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
    
    # 등록된 메뉴 목록
    st.markdown("### 📋 등록된 메뉴 목록")
    menu_df = load_csv('menu_master.csv', store_id=store_id, default_columns=['메뉴명', '판매가'])
    
    if menu_df.empty:
        st.info("등록된 메뉴가 없습니다.")
    else:
        display_df = menu_df[['메뉴명', '판매가']].copy()
        display_df['판매가'] = display_df['판매가'].apply(lambda x: f"{int(x):,}원")
        display_df.columns = ['메뉴명', '판매가']
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        st.caption(f"총 {len(menu_df)}개 메뉴")
