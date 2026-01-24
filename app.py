"""
Store Ops Main App - Clean Version v2
"""
import streamlit as st
from datetime import datetime
import pandas as pd
import numpy as np
import sys
import os

# Essential UI and Logic Imports
from ui_pages.home import render_home
from ui_pages.strategy.mission_detail import render_mission_detail
from ui_pages.input.input_hub import render_input_hub
from ui_pages.analysis.analysis_hub import render_analysis_hub
from ui_pages.daily_input_hub import render_daily_input_hub
from ui_pages.manager_close import render_manager_close
from ui_pages.sales_entry import render_sales_entry
from ui_pages.analysis.analysis_summary import render_analysis_summary
from ui_pages.analysis.sales_analysis import render_sales_analysis
from ui_pages.input.menu_input import render_menu_input_page
from ui_pages.input.ingredient_input import render_ingredient_input_page
from ui_pages.input.inventory_input import render_inventory_input_page

from src.ui.theme_manager import inject_global_ui
inject_global_ui()

from src.bootstrap import bootstrap
bootstrap(page_title="Store Ops")

from src.auth import check_login, show_login_page, get_current_store_name, logout, get_current_store_id, get_user_stores, switch_store, needs_onboarding

if not check_login():
    show_login_page()
    st.stop()

user_id = st.session_state.get('user_id')
import logging
logger = logging.getLogger(__name__)

# Onboarding and Store Setup
_onboarding_check_key = "_onboarding_checked"
_onboarding_complete_key = "_onboarding_complete"

if user_id:
    if st.session_state.get(_onboarding_complete_key, False):
        logger.debug("Onboarding complete (cached)")
    else:
        if not st.session_state.get(_onboarding_check_key, False):
            try:
                from src.auth import get_onboarding_mode, set_onboarding_mode
                mode = get_onboarding_mode(user_id)
                needs = needs_onboarding(user_id)
                st.session_state[_onboarding_check_key] = True
                if needs:
                    set_onboarding_mode(user_id, 'coach')
                    st.session_state[_onboarding_complete_key] = True
                else:
                    st.session_state[_onboarding_complete_key] = True
            except Exception as e:
                logger.error(f"Onboarding check error: {e}")
                st.session_state[_onboarding_check_key] = True

store_id = get_current_store_id()
if not store_id:
    from ui_pages.store_setup import render_store_setup_page
    render_store_setup_page()
    st.stop()

# Utility Functions
def _diagnose_supabase_connection():
    st.markdown("### 🔍 Supabase 연결 진단")
    if st.button("❌ 닫기"):
        st.session_state["_show_supabase_diagnosis"] = False
    try:
        from src.auth import get_supabase_client
        client = get_supabase_client()
        st.write(f"Store ID: `{get_current_store_id()}`")
        result = client.table("stores").select("*").limit(1).execute()
        st.success(f"Success: {len(result.data)} rows")
    except Exception as e:
        st.error(f"Error: {e}")

# Data Storage and Analytics Imports
from src.storage_supabase import load_csv, create_backup
from src.ui_helpers import render_page_header, render_section_divider

# Theme and CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap');
    * { font-family: 'Noto Sans KR', sans-serif !important; }
    [data-testid="stIconMaterial"] {
        display: inline-flex; align-items: center; justify-content: center;
        width: 28px; height: 28px; border-radius: 999px; background-color: #667eea;
        font-size: 0 !important; color: transparent !important;
    }
    [data-testid="stIconMaterial"]::before { content: '😊'; font-size: 18px; color: #ffffff; }
</style>
""", unsafe_allow_html=True)

if st.session_state.get("theme", "light") == "dark":
    st.markdown("<style>.main { background-color: #020617 !important; color: #e5e7eb !important; }</style>", unsafe_allow_html=True)

# Sidebar Navigation
with st.sidebar:
    user_stores = get_user_stores()
    curr_name = get_current_store_name()
    if len(user_stores) > 1:
        store_options = {f"{s['name']} ({s['role']})": s['id'] for s in user_stores}
        selected = st.selectbox("🏪 매장 선택", options=list(store_options.keys()))
        if store_options[selected] != get_current_store_id():
            if switch_store(store_options[selected]): st.rerun()
    else:
        st.markdown(f"🏪 **{curr_name}**")
    
    menu = {
        "🏠 홈": [("홈", "홈")],
        "✍ 입력": [("입력 허브", "입력 허브")],
        "📊 분석": [("분석 허브", "분석 허브")],
        "🧠 설계": [("가게 전략 센터", "가게 전략 센터")],
        "🛠 운영": [("직원 연락망", "직원 연락망"), ("게시판", "게시판")]
    }
    
    if "current_page" not in st.session_state: st.session_state.current_page = "홈"
    
    for cat, items in menu.items():
        st.markdown(f"**{cat}**")
        for label, key in items:
            if st.button(label, key=f"btn_{key}", use_container_width=True, type="primary" if st.session_state.current_page == key else "secondary"):
                st.session_state.current_page = key
                st.rerun()

    if st.button("🚪 로그아웃"): logout(); st.rerun()
    if st.button("🔄 캐시 클리어"): load_csv.clear(); st.rerun()

# Page Routing
page = st.session_state.current_page

if st.session_state.get("_show_supabase_diagnosis", False):
    _diagnose_supabase_connection()

if page == "홈": render_home()
elif page == "오늘의 전략 실행": render_mission_detail()
elif page == "입력 허브": render_input_hub()
elif page == "분석 허브": render_analysis_hub()
elif page == "일일 입력(통합)": render_daily_input_hub()
elif page == "점장 마감": render_manager_close()
elif page == "매출 등록": render_sales_entry()
elif page == "분석총평": render_analysis_summary()
elif page == "매출 관리": render_sales_analysis()
elif page == "메뉴 입력": render_menu_input_page()
elif page == "재료 입력": render_ingredient_input_page()
elif page == "재고 입력": render_inventory_input_page()
elif page == "원가 파악":
    from ui_pages.cost_overview import render_cost_overview
    render_cost_overview()
elif page == "가게 전략 센터":
    from ui_pages.design_lab.design_hub import render_design_hub
    render_design_hub()
elif page == "메뉴 등록":
    from ui_pages.menu_management import render_menu_management
    render_menu_management()
elif page == "재료 등록":
    from ui_pages.ingredient_management import render_ingredient_management
    render_ingredient_management()
elif page == "실제정산":
    from ui_pages.settlement_actual import render_settlement_actual
    render_settlement_actual()
elif page == "판매 관리":
    render_sales_analysis()
elif page == "재료 사용량 집계":
    from ui_pages.ingredient_usage_summary import render_ingredient_usage_summary
    render_ingredient_usage_summary()
elif page == "재고 분석":
    from ui_pages.analysis.inventory_analysis import render_inventory_analysis
    render_inventory_analysis()
elif page == "비용 분석":
    from ui_pages.analysis.cost_analysis import render_cost_analysis
    render_cost_analysis()
elif page == "실제정산 분석":
    from ui_pages.analysis.settlement_analysis import render_settlement_analysis
    render_settlement_analysis()
elif page == "게시판":
    from ui_pages.board import render_board
    render_board()
