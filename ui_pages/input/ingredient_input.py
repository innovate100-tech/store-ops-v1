"""
재료 입력 페이지 (입력 전용)
설계 기능 없이 재료 등록만 수행
"""
from src.bootstrap import bootstrap
import streamlit as st
from src.ui_helpers import render_page_header, ui_flash_success, ui_flash_error
from src.ui import render_ingredient_input
from src.storage_supabase import load_csv, save_ingredient
from src.auth import get_current_store_id

# 공통 설정 적용
bootstrap(page_title="Ingredient Input")


def render_ingredient_input_page():
    """재료 입력 페이지 렌더링 (입력 전용)"""
    render_page_header("🧺 재료 입력", "🧺")
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    st.info("💡 재료를 등록하면 레시피와 원가 계산이 가능합니다.")
    st.markdown("---")
    
    st.markdown("### 📝 재료 등록")
    ingredient_name, unit, unit_price, order_unit, conversion_rate = render_ingredient_input(key_prefix="ingredient_input")
    
    if st.button("💾 저장", type="primary", key="ingredient_input_save"):
        if not ingredient_name or not ingredient_name.strip():
            ui_flash_error("재료명을 입력해주세요.")
        elif unit_price <= 0:
            ui_flash_error("단가를 입력해주세요.")
        else:
            try:
                save_ingredient(
                    ingredient_name.strip(),
                    unit,
                    float(unit_price),
                    order_unit,
                    float(conversion_rate) if conversion_rate else 1.0
                )
                ui_flash_success(f"재료 '{ingredient_name.strip()}'이(가) 저장되었습니다.")
                st.rerun()
            except Exception as e:
                ui_flash_error(f"저장 실패: {str(e)}")
    
    st.markdown("---")
    
    # 등록된 재료 목록
    st.markdown("### 📋 등록된 재료 목록")
    ingredient_df = load_csv('ingredient_master.csv', store_id=store_id, default_columns=['재료명', '단위', '단가'])
    
    if ingredient_df.empty:
        st.info("등록된 재료가 없습니다.")
    else:
        display_df = ingredient_df[['재료명', '단위', '단가']].copy()
        display_df['단가'] = display_df['단가'].apply(lambda x: f"{float(x):,.0f}원")
        display_df.columns = ['재료명', '단위', '단가']
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        st.caption(f"총 {len(ingredient_df)}개 재료")
