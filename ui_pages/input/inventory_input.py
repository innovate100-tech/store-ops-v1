"""
재고 입력 페이지 (입력 전용)
재고 현황과 안전재고를 입력하는 페이지
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
import logging
from src.ui_helpers import render_page_header, ui_flash_success, ui_flash_error, render_section_header
from src.storage_supabase import load_csv, save_inventory
from src.auth import get_current_store_id, get_supabase_client

logger = logging.getLogger(__name__)

# 공통 설정 적용
bootstrap(page_title="재고 입력")


def render_inventory_input_page():
    """재고 입력 페이지 렌더링"""
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
    
    if ingredient_df.empty:
        st.warning("먼저 재료를 등록해주세요.")
        if st.button("🧺 사용 재료 입력으로 이동", key="go_to_ingredient_input"):
            st.session_state["current_page"] = "재료 입력"
            st.rerun()
        return
    
    # 재고 정보 매핑 (재료명 -> 현재고, 안전재고)
    inventory_map = {}
    if not inventory_df.empty:
        for _, row in inventory_df.iterrows():
            ingredient_name = row.get('재료명', '')
            current_stock = row.get('현재고', 0)
            safety_stock = row.get('안전재고', 0)
            if ingredient_name:
                inventory_map[ingredient_name] = {
                    'current': float(current_stock) if current_stock else 0,
                    'safety': float(safety_stock) if safety_stock else 0
                }
    
    # ============================================
    # 재고 입력 섹션
    # ============================================
    render_section_header("📦 재고 입력", "📦")
    
    st.markdown("**재료별 현재고와 안전재고를 입력하세요**")
    
    # 재료 선택
    ingredient_list = ingredient_df['재료명'].tolist()
    
    # 재료명과 단위 매핑 생성 (기본 단위, 발주 단위, 변환 비율)
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
    
    # 재료 선택 옵션에 단위 표시
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
        key="inventory_input_ingredient"
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
    
    # 발주 단위로 표시 (입력은 발주 단위로 받고, 저장 시 기본 단위로 변환)
    col1, col2 = st.columns(2)
    
    with col1:
        # 현재고 입력 (발주 단위)
        current_stock_label = f"현재고 ({selected_order_unit})"
        if existing_current > 0:
            # 기본 단위를 발주 단위로 변환하여 표시
            current_in_order_unit = existing_current / selected_conversion_rate if selected_conversion_rate > 0 else existing_current
            current_stock_input = st.number_input(
                current_stock_label,
                min_value=0.0,
                value=float(current_in_order_unit),
                step=1.0,
                format="%.2f",
                key="inventory_input_current",
                help=f"기본 단위({selected_unit})로 저장됩니다"
            )
        else:
            current_stock_input = st.number_input(
                current_stock_label,
                min_value=0.0,
                value=0.0,
                step=1.0,
                format="%.2f",
                key="inventory_input_current",
                help=f"기본 단위({selected_unit})로 저장됩니다"
            )
        # 발주 단위를 기본 단위로 변환
        current_stock = current_stock_input * selected_conversion_rate
    
    with col2:
        # 안전재고 입력 (발주 단위)
        safety_stock_label = f"안전재고 ({selected_order_unit})"
        if existing_safety > 0:
            # 기본 단위를 발주 단위로 변환하여 표시
            safety_in_order_unit = existing_safety / selected_conversion_rate if selected_conversion_rate > 0 else existing_safety
            safety_stock_input = st.number_input(
                safety_stock_label,
                min_value=0.0,
                value=float(safety_in_order_unit),
                step=1.0,
                format="%.2f",
                key="inventory_input_safety",
                help=f"기본 단위({selected_unit})로 저장됩니다"
            )
        else:
            safety_stock_input = st.number_input(
                safety_stock_label,
                min_value=0.0,
                value=0.0,
                step=1.0,
                format="%.2f",
                key="inventory_input_safety",
                help=f"기본 단위({selected_unit})로 저장됩니다"
            )
        # 발주 단위를 기본 단위로 변환
        safety_stock = safety_stock_input * selected_conversion_rate
    
    # 저장 버튼
    col_save, col_reset = st.columns([1, 1])
    with col_save:
        if st.button("💾 저장", type="primary", key="inventory_input_save", use_container_width=True):
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
        if st.button("🔄 초기화", key="inventory_input_reset", use_container_width=True):
            st.rerun()
    
    st.markdown("---")
    
    # ============================================
    # 재고 현황 요약
    # ============================================
    render_section_header("📊 재고 현황 요약", "📊")
    
    if inventory_df.empty:
        st.info("등록된 재고 정보가 없습니다.")
    else:
        # 재고 현황 표시
        st.markdown("### 재고 목록")
        
        # 헤더
        header_col1, header_col2, header_col3, header_col4, header_col5 = st.columns([3, 2, 2, 2, 2])
        with header_col1:
            st.markdown("**재료명**")
        with header_col2:
            st.markdown("**단위**")
        with header_col3:
            st.markdown("**현재고**")
        with header_col4:
            st.markdown("**안전재고**")
        with header_col5:
            st.markdown("**상태**")
        
        st.markdown("---")
        
        for _, row in inventory_df.iterrows():
            ing_name = row.get('재료명', '')
            current = float(row.get('현재고', 0))
            safety = float(row.get('안전재고', 0))
            
            # 재료 정보 가져오기
            ing_row = ingredient_df[ingredient_df['재료명'] == ing_name]
            if not ing_row.empty:
                unit = ing_row.iloc[0].get('단위', '')
                order_unit = ing_row.iloc[0].get('발주단위', unit)
                conversion_rate = float(ing_row.iloc[0].get('변환비율', 1.0)) if ing_row.iloc[0].get('변환비율') else 1.0
                
                # 발주 단위로 변환하여 표시
                current_display = current / conversion_rate if conversion_rate > 0 else current
                safety_display = safety / conversion_rate if conversion_rate > 0 else safety
                
                # 상태 판단
                if current < safety:
                    status = "⚠️ 부족"
                    status_color = "#EF4444"
                elif current <= safety * 1.2:
                    status = "⚠️ 주의"
                    status_color = "#F59E0B"
                else:
                    status = "✓ 정상"
                    status_color = "#22C55E"
                
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])
                with col1:
                    st.markdown(f"**{ing_name}**")
                with col2:
                    if order_unit != unit:
                        st.markdown(f"{unit}<br><small>(발주: {order_unit})</small>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"{unit}")
                with col3:
                    st.markdown(f"{current_display:.1f} {order_unit}")
                with col4:
                    st.markdown(f"{safety_display:.1f} {order_unit}")
                with col5:
                    st.markdown(f'<span style="color: {status_color}; font-weight: 600;">{status}</span>', 
                               unsafe_allow_html=True)
                
                st.markdown("---")
        
        # 발주 관리로 이동
        if st.button("🛒 발주 관리로 이동", key="inventory_input_go_to_order", use_container_width=True):
            st.session_state["current_page"] = "발주 관리"
            st.rerun()
