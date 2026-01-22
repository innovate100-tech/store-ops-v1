"""
발주 관리 페이지
"""
from src.bootstrap import bootstrap
import streamlit as st
from src.ui_helpers import render_page_header, render_section_header
from src.storage_supabase import load_csv
from src.order_ui import (
    render_safety_stock_tab,
    render_inventory_status_tab,
    render_order_history_tab,
    render_supplier_management_tab,
    render_order_analysis_tab
)

# 공통 설정 적용
bootstrap(page_title="Order Management")


def render_order_management():
    """발주 관리 페이지 렌더링"""
    render_page_header("발주 관리", "🛒")
    
    # 재료 / 재고 공통 로드 (발주단위/변환비율 포함)
    ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가', '발주단위', '변환비율'])
    ingredient_list = ingredient_df['재료명'].tolist() if not ingredient_df.empty else []
    inventory_df = load_csv('inventory.csv', default_columns=['재료명', '현재고', '안전재고'])
    
    # 탭 구조
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🛡️ 안전재고 등록",
        "📦 현재 재고 현황",
        "🛒 발주 추천",
        "📋 진행 현황",
        "🏢 공급업체",
        "📊 발주 분석",
    ])
    
    # ========== 탭 1: 안전재고 등록 ==========
    with tab1:
        render_safety_stock_tab(ingredient_df, load_csv)
    
    # ========== 탭 2: 현재 재고 현황 ==========
    with tab2:
        render_inventory_status_tab(ingredient_df, load_csv)
    
    # ========== 탭 3: 발주 추천 ==========
    # 재기획 예정 - 현재 비워둠
    with tab3:
        render_section_header("발주 추천", "🛒")
        st.info("📝 발주 추천 기능은 재기획 중입니다. 곧 새로운 기능으로 업데이트될 예정입니다.")
    
    # ========== 탭 4: 발주 관리 (진행 현황) ==========
    with tab4:
        render_section_header("발주 관리 (진행 현황)", "📋")
        st.info("📝 진행 현황 기능은 재기획 중입니다. 곧 새로운 기능으로 업데이트될 예정입니다.")
    
    # ========== 탭 5: 공급업체 ==========
    with tab5:
        render_section_header("공급업체", "🏢")
        st.info("📝 공급업체 기능은 재기획 중입니다. 곧 새로운 기능으로 업데이트될 예정입니다.")
    
    # ========== 탭 6: 발주 분석 대시보드 ==========
    with tab6:
        render_section_header("발주 분석 대시보드", "📊")
        st.info("📝 발주 분석 기능은 재기획 중입니다. 곧 새로운 기능으로 업데이트될 예정입니다.")


# Streamlit 멀티페이지에서 직접 실행될 때
# 주석 처리: app.py에서만 렌더되도록 함 (중복 호출 방지)
# render_order_management()
