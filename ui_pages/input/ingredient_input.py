"""
재료 입력 페이지 (입력 전용)
설계 기능 없이 재료 등록만 수행
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
import logging
from src.ui_helpers import render_page_header, ui_flash_success, ui_flash_error
from src.ui import render_ingredient_input
from src.storage_supabase import load_csv, save_ingredient
from src.auth import get_current_store_id

logger = logging.getLogger(__name__)

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
    
    # 등록된 재료 목록 (상태 표시 포함)
    st.markdown("### 📋 등록된 재료 목록")
    ingredient_df = load_csv('ingredient_master.csv', store_id=store_id, default_columns=['재료명', '단위', '단가'])
    
    if ingredient_df.empty:
        st.info("등록된 재료가 없습니다.")
    else:
        # 레시피에서 사용 여부 확인
        from src.auth import get_supabase_client
        supabase = get_supabase_client()
        ingredient_in_recipe = {}
        
        if supabase:
            try:
                # 재료 ID 매핑
                ingredient_result = supabase.table("ingredient_master")\
                    .select("id,name")\
                    .eq("store_id", store_id)\
                    .execute()
                ingredient_id_map = {i['name']: i['id'] for i in ingredient_result.data if ingredient_result.data}
                
                if ingredient_id_map:
                    ingredient_ids = list(ingredient_id_map.values())
                    recipe_result = supabase.table("recipes")\
                        .select("ingredient_id")\
                        .eq("store_id", store_id)\
                        .in_("ingredient_id", ingredient_ids)\
                        .execute()
                    
                    recipe_ingredient_ids = set()
                    if recipe_result.data:
                        recipe_ingredient_ids = {r['ingredient_id'] for r in recipe_result.data}
                    
                    id_to_name = {v: k for k, v in ingredient_id_map.items()}
                    for ingredient_id in recipe_ingredient_ids:
                        ingredient_name = id_to_name.get(ingredient_id)
                        if ingredient_name:
                            ingredient_in_recipe[ingredient_name] = True
            except Exception as e:
                logger.warning(f"레시피 사용 여부 확인 실패: {e}")
        
        # 상태 표시가 포함된 데이터프레임 생성
        display_data = []
        for _, row in ingredient_df.iterrows():
            ingredient_name = row['재료명']
            in_recipe = ingredient_in_recipe.get(ingredient_name, False)
            status = "✓ 레시피 사용" if in_recipe else "— 미사용"
            display_data.append({
                '재료명': ingredient_name,
                '단위': row.get('단위', '—'),
                '단가': f"{float(row['단가']):,.0f}원",
                '상태': status
            })
        
        display_df = pd.DataFrame(display_data)
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # 통계 표시
        total_ingredients = len(ingredient_df)
        ingredients_in_recipe = sum(1 for name in ingredient_df['재료명'] if ingredient_in_recipe.get(name, False))
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("전체 재료", f"{total_ingredients}개")
        with col2:
            st.metric("레시피에서 사용", f"{ingredients_in_recipe}개", delta=f"{ingredients_in_recipe/total_ingredients*100:.0f}%" if total_ingredients > 0 else None)
        
        st.caption("💡 재료를 등록하면 레시피 입력이 쉬워집니다.")
