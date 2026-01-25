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

from src.bootstrap import bootstrap
bootstrap(page_title="Store Ops")

from src.ui.theme_manager import inject_global_ui
inject_global_ui()

from src.auth import check_login, show_login_page, get_current_store_name, logout, get_current_store_id, get_user_stores, switch_store, needs_onboarding
from src.ui.css_manager import inject_dom, inject_rescue

try:
    from src.debug.nav_trace import push_render_step
except ImportError:
    def push_render_step(*args, **kwargs):
        pass

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
# @import 규칙은 반드시 별도의 스타일 블록에서 최상단에 위치해야 함
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/icon?family=Material+Icons');
</style>
""", unsafe_allow_html=True)

# ============================================
# 사이드바 프리미엄 CSS 주입 함수
# ============================================
def inject_sidebar_premium_css():
    """사이드바 울트라 시크 CSS 주입 (rerun마다 실행, 사이드바 DOM 재생성 대응)"""
    # 주의: 1회 가드 없음 - 사이드바 DOM이 재생성될 때마다 CSS 재적용 필요
    # 안전장치: 모든 셀렉터는 [data-testid="stSidebar"]로 제한되어 있어 전역 영향 없음
    
    css_content = """
    <style>
    /* =========================
       ULTRA SLEEK SIDEBAR v3
       scope: sidebar only (rerun마다 재주입)
       안전장치: 모든 셀렉터는 [data-testid="stSidebar"]로 제한
       ========================= */
    
    @keyframes ultra-neon-pulse {
        0%, 100% {
            box-shadow: 0 6px 18px rgba(59, 130, 246, 0.25),
                        0 0 0 0 rgba(59, 130, 246, 0.25),
                        0 0 24px rgba(59, 130, 246, 0.10);
        }
        50% {
            box-shadow: 0 10px 30px rgba(59, 130, 246, 0.35),
                        0 0 0 4px rgba(59, 130, 246, 0.12),
                        0 0 36px rgba(59, 130, 246, 0.18);
        }
    }
    
    @keyframes ultra-gradient-shift {
        0%, 100% {
            background-position: 0% 50%;
        }
        50% {
            background-position: 100% 50%;
        }
    }
    
    @media (prefers-reduced-motion: reduce) {
        [data-testid="stSidebar"] * {
            animation: none !important;
            transition: none !important;
        }
    }
    
    /* ---------- CATEGORY TITLE ---------- */
    [data-testid="stSidebar"] .ultra-category {
        margin: 22px 0 10px;
        padding: 0 10px;
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        position: relative;
        background: linear-gradient(135deg, #94A3B8 0%, #60A5FA 35%, #3B82F6 50%, #60A5FA 65%, #94A3B8 100%);
        background-size: 260% 260%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: 0 0 10px rgba(96, 165, 250, 0.18);
        animation: ultra-gradient-shift 4.5s ease infinite;
        /* Fallback */
        color: #94A3B8;
    }
    
    @supports not (-webkit-background-clip: text) {
        [data-testid="stSidebar"] .ultra-category {
            -webkit-text-fill-color: #94A3B8;
            color: #94A3B8;
        }
    }
    
    /* 카테고리 액센트 dot */
    [data-testid="stSidebar"] .ultra-category::before {
        content: "•";
        position: absolute;
        left: -2px;
        top: 0;
        color: rgba(96, 165, 250, 0.85);
        text-shadow: 0 0 10px rgba(96, 165, 250, 0.35);
    }
    
    [data-testid="stSidebar"] .ultra-category::after {
        content: "";
        position: absolute;
        left: 10px;
        bottom: -10px;
        width: 48px;
        height: 2px;
        border-radius: 2px;
        background: linear-gradient(90deg, rgba(59, 130, 246, 0.85), rgba(96, 165, 250, 0.55), transparent);
        box-shadow: 0 0 12px rgba(59, 130, 246, 0.25);
    }
    
    /* ---------- BUTTON BASE (3-step fallback) ---------- */
    [data-testid="stSidebar"] .stButton > button,
    [data-testid="stSidebar"] button[kind],
    [data-testid="stSidebar"] button {
        border-radius: 14px !important;
        min-height: 56px !important;
        padding: 14px 16px !important;
        font-size: 0.90rem !important;
        font-weight: 550 !important;
        line-height: 1.42 !important;
        white-space: normal !important;
        word-break: break-word !important;
        display: flex !important;
        align-items: center !important;
        text-align: left !important;
        color: #E2E8F0 !important;
        border: 1px solid rgba(255, 255, 255, 0.14) !important;
        background:
            linear-gradient(180deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.03) 55%, rgba(255, 255, 255, 0.012) 100%),
            radial-gradient(circle at 15% 0%, rgba(59, 130, 246, 0.08) 0%, transparent 55%) !important;
        box-shadow:
            0 2px 5px rgba(0, 0, 0, 0.18),
            0 10px 22px rgba(0, 0, 0, 0.16),
            inset 0 1px 0 rgba(255, 255, 255, 0.10) !important;
        position: relative !important;
        overflow: hidden !important;
        transition: background 0.32s ease, border-color 0.32s ease, box-shadow 0.32s ease, transform 0.18s ease !important;
        margin-bottom: 0.5rem;
    }
    
    /* 버튼 왼쪽 액센트 바 */
    [data-testid="stSidebar"] .stButton > button::before,
    [data-testid="stSidebar"] button[kind]::before,
    [data-testid="stSidebar"] button::before {
        content: "";
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 2px;
        background: rgba(59, 130, 246, 0.35);
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.20);
        opacity: 1;
        z-index: 1;
    }
    
    /* hover sweep overlay via ::after */
    [data-testid="stSidebar"] .stButton > button::after,
    [data-testid="stSidebar"] button[kind]::after,
    [data-testid="stSidebar"] button::after {
        content: "";
        position: absolute;
        top: 0;
        left: -120%;
        width: 120%;
        height: 100%;
        background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.10) 35%, rgba(96, 165, 250, 0.18) 50%, rgba(255, 255, 255, 0.10) 65%, transparent 100%);
        opacity: 0;
        transition: left 0.62s ease, opacity 0.25s ease;
        pointer-events: none;
        z-index: 2;
    }
    
    /* HOVER */
    [data-testid="stSidebar"] .stButton > button:hover,
    [data-testid="stSidebar"] button[kind]:hover,
    [data-testid="stSidebar"] button:hover {
        background:
            linear-gradient(180deg, rgba(255, 255, 255, 0.12) 0%, rgba(255, 255, 255, 0.06) 55%, rgba(255, 255, 255, 0.025) 100%),
            radial-gradient(circle at 15% 0%, rgba(59, 130, 246, 0.12) 0%, transparent 55%) !important;
        border-color: rgba(255, 255, 255, 0.28) !important;
        box-shadow:
            0 6px 14px rgba(0, 0, 0, 0.24),
            0 18px 34px rgba(0, 0, 0, 0.22),
            0 0 0 1px rgba(255, 255, 255, 0.08),
            inset 0 1px 0 rgba(255, 255, 255, 0.14) !important;
        transform: scale(1.01) !important;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover::before,
    [data-testid="stSidebar"] button[kind]:hover::before,
    [data-testid="stSidebar"] button:hover::before {
        background: rgba(59, 130, 246, 0.62);
        box-shadow: 0 0 14px rgba(59, 130, 246, 0.28);
    }
    
    [data-testid="stSidebar"] .stButton > button:hover::after,
    [data-testid="stSidebar"] button[kind]:hover::after,
    [data-testid="stSidebar"] button:hover::after {
        left: 120%;
        opacity: 1;
    }
    
    /* ACTIVE CLICK FEEDBACK (ripple may fail, so ensure highlight) */
    [data-testid="stSidebar"] .stButton > button:active,
    [data-testid="stSidebar"] button[kind]:active,
    [data-testid="stSidebar"] button:active {
        background:
            linear-gradient(180deg, rgba(255, 255, 255, 0.18) 0%, rgba(255, 255, 255, 0.10) 55%, rgba(255, 255, 255, 0.05) 100%),
            radial-gradient(circle at 15% 0%, rgba(59, 130, 246, 0.16) 0%, transparent 55%) !important;
    }
    
    /* PRIMARY (selected) */
    [data-testid="stSidebar"] .stButton > button[kind="primary"],
    [data-testid="stSidebar"] button[kind="primary"] {
        color: #fff !important;
        border-color: rgba(96, 165, 250, 0.72) !important;
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 30%, #1D4ED8 60%, #1E40AF 100%) !important;
        background-size: 220% 220% !important;
        box-shadow:
            0 10px 26px rgba(59, 130, 246, 0.32),
            0 18px 44px rgba(59, 130, 246, 0.22),
            0 0 0 1px rgba(96, 165, 250, 0.35),
            0 0 46px rgba(59, 130, 246, 0.16),
            inset 0 1px 0 rgba(255, 255, 255, 0.22) !important;
        animation: ultra-neon-pulse 3.6s ease-in-out infinite, ultra-gradient-shift 4.2s ease infinite !important;
    }
    
    [data-testid="stSidebar"] .stButton > button[kind="primary"]::before,
    [data-testid="stSidebar"] button[kind="primary"]::before {
        width: 3px;
        background: rgba(255, 255, 255, 0.55);
        box-shadow: 0 0 18px rgba(255, 255, 255, 0.18);
    }
    
    /* EXPANDER / SELECTBOX : keep minimal, consistent */
    [data-testid="stSidebar"] .stExpander header,
    [data-testid="stSidebar"] .stExpander summary {
        border-radius: 14px !important;
        border: 1px solid rgba(255, 255, 255, 0.14) !important;
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02)) !important;
        color: #E2E8F0 !important;
        transition: all 0.32s ease !important;
    }
    
    [data-testid="stSidebar"] .stExpander header:hover,
    [data-testid="stSidebar"] .stExpander summary:hover {
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.04)) !important;
        border-color: rgba(255, 255, 255, 0.22) !important;
    }
    
    /* Expander 내부 버튼도 동일한 높이 통일 */
    [data-testid="stSidebar"] .stExpander .stButton > button,
    [data-testid="stSidebar"] .stExpander button {
        min-height: 56px !important;
        display: flex !important;
        align-items: center !important;
        line-height: 1.42 !important;
        white-space: normal !important;
        word-break: break-word !important;
    }
    
    [data-testid="stSidebar"] .stSelectbox div[role="combobox"],
    [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"],
    [data-testid="stSidebar"] .stSelectbox select {
        border-radius: 14px !important;
        border: 1px solid rgba(255, 255, 255, 0.14) !important;
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.02)) !important;
        color: #E2E8F0 !important;
        transition: all 0.32s ease !important;
    }
    
    [data-testid="stSidebar"] .stSelectbox div[role="combobox"]:hover,
    [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"]:hover,
    [data-testid="stSidebar"] .stSelectbox select:hover {
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05)) !important;
        border-color: rgba(255, 255, 255, 0.22) !important;
    }
    
    [data-testid="stSidebar"] .stSelectbox label {
        color: #E2E8F0 !important;
        font-weight: 500 !important;
    }
    
    /* SYSTEM SECTION */
    [data-testid="stSidebar"] .ultra-system {
        margin-top: 26px;
        padding-top: 18px;
        border-top: 1px solid rgba(255, 255, 255, 0.12);
        position: relative;
    }
    
    [data-testid="stSidebar"] .ultra-system::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.35), rgba(96, 165, 250, 0.55), rgba(59, 130, 246, 0.35), transparent);
        box-shadow: 0 0 12px rgba(59, 130, 246, 0.22);
    }
    
    /* 시스템 버튼도 동일한 높이 통일 */
    [data-testid="stSidebar"] .ultra-system .stButton > button,
    [data-testid="stSidebar"] .ultra-system button {
        min-height: 56px !important;
        display: flex !important;
        align-items: center !important;
        line-height: 1.42 !important;
        white-space: normal !important;
        word-break: break-word !important;
    }
    </style>
    """
    # DOM 계층: 사이드바 CSS (rerun마다 실행)
    inject_dom(css_content, "sidebar")

# 나머지 CSS는 별도 스타일 블록으로
st.markdown("""
<style>
    /* 디자인 고도화: 컬러 시스템 및 애니메이션 */
    :root {
        --base-bg: #0F172A;
        --surface-bg: #1E293B;
        --accent-blue: #3B82F6;
        --accent-glow: rgba(59, 130, 246, 0.5);
        --success-emerald: #10B981;
        --warning-amber: #F59E0B;
        --text-main: #F8FAFC;
        --text-muted: #94A3B8;
    }

    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }

    @keyframes pulse-glow {
        0% { box-shadow: 0 0 5px rgba(59, 130, 246, 0.2); }
        50% { box-shadow: 0 0 20px rgba(59, 130, 246, 0.5); }
        100% { box-shadow: 0 0 5px rgba(59, 130, 246, 0.2); }
    }

    @keyframes wave {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }

    .animate-in {
        animation: fadeInUp 0.6s ease-out forwards;
        opacity: 0;
    }

    .delay-1 { animation-delay: 0.1s; }
    .delay-2 { animation-delay: 0.2s; }
    .delay-3 { animation-delay: 0.3s; }
    .delay-4 { animation-delay: 0.4s; }
    
    /* Material Icons 폰트 preload로 빠른 로드 보장 */
    @font-face {
        font-family: 'Material Icons';
        font-style: normal;
        font-weight: 400;
        src: url(https://fonts.gstatic.com/s/materialicons/v142/flUhRq6tzZclQEJ-Vdg-IuiaDsNc.woff2) format('woff2');
        font-display: swap;
    }
    
    /* 본질적 해결: Material Icons를 최우선으로, 텍스트 요소에만 Noto Sans KR 적용 */
    
    /* ============================================
       본질적 해결: Material Icons 문제 해결
       ============================================ */
    
    /* 1. Material Icons 폰트 강제 적용 (모든 가능한 선택자) */
    [data-testid="stIconMaterial"],
    span[data-testid="stIconMaterial"],
    [data-testid*="Icon"],
    [data-testid*="icon"],
    [class*="material-icons"],
    [class*="MaterialIcons"],
    [class*="material"],
    [class*="Material"],
    .material-icons,
    .MaterialIcons {
        font-family: 'Material Icons' !important;
        font-weight: normal !important;
        font-style: normal !important;
        font-size: 24px !important;
        line-height: 1 !important;
        letter-spacing: normal !important;
        text-transform: none !important;
        display: inline-block !important;
        white-space: nowrap !important;
        word-wrap: normal !important;
        direction: ltr !important;
        -webkit-font-feature-settings: 'liga' !important;
        -webkit-font-smoothing: antialiased !important;
        /* 핵심: overflow를 visible로 하여 텍스트가 잘리지 않도록 */
        overflow: visible !important;
        width: auto !important;
        min-width: 24px !important;
        max-width: none !important;
        text-overflow: unset !important;
        flex-shrink: 0 !important;
        vertical-align: middle !important;
    }
    
    /* ============================================
       Expander 화살표를 제목 앞으로 이동
       ============================================ */
    
    /* 2. Expander 버튼을 Flexbox로 설정하여 순서 제어 가능하게 */
    [data-testid="stExpander"] > div > div,
    [data-testid="stExpander"] button,
    [data-testid="stExpander"] > div > div > button {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        position: relative !important;
        overflow: visible !important;
        /* 오른쪽 padding 제거 (더 이상 필요 없음) */
        padding-right: 1rem !important;
    }
    
    /* 3. Expander 내부 아이콘을 제목 앞으로 이동 (order 사용) */
    [data-testid="stExpander"] [data-testid="stIconMaterial"],
    [data-testid="stExpander"] button [data-testid="stIconMaterial"],
    [data-testid="stExpander"] > div > div [data-testid="stIconMaterial"],
    [data-testid="stExpander"] > div > div > button [data-testid="stIconMaterial"] {
        /* absolute positioning 제거 */
        position: static !important;
        /* order로 앞으로 이동 */
        order: -1 !important;
        /* 아이콘과 텍스트 사이 간격 */
        margin-right: 0.5rem !important;
        margin-left: 0 !important;
        width: auto !important;
        min-width: 24px !important;
        /* vertical-align 대신 flexbox align-items 사용 */
        vertical-align: middle !important;
        z-index: auto !important;
        pointer-events: auto !important;
        overflow: visible !important;
    }
    
    /* ============================================
       본질적 해결: Expander 내부 버튼 스타일 문제 해결
       ============================================ */
    
    /* 4. Expander 내부 버튼 테두리 명시적 정의 */
    [data-testid="stExpander"] .stButton > button,
    [data-testid="stExpander"] button.stButton,
    [data-testid="stExpander"] [data-testid="baseButton-secondary"],
    [data-testid="stExpander"] [data-testid="baseButton-primary"],
    [data-testid="stExpander"] button[kind="secondary"],
    [data-testid="stExpander"] button[kind="primary"] {
        border: 1px solid rgba(232, 238, 247, 0.12) !important;
        border-width: 1px !important;
        border-style: solid !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        min-height: 2.5rem !important;
    }
    
    /* 5. Expander 내부 버튼 hover 상태 */
    [data-testid="stExpander"] .stButton > button:hover,
    [data-testid="stExpander"] button:hover {
        border-color: rgba(232, 238, 247, 0.3) !important;
        border-width: 1px !important;
    }
    
    /* 6. Expander 내부 모든 버튼 요소에 테두리 보장 */
    [data-testid="stExpander"] button:not([data-testid="stIconMaterial"]) {
        border: 1px solid rgba(232, 238, 247, 0.12) !important;
    }
    
    /* 2단계: 텍스트 요소에만 Noto Sans KR 적용 (Material Icons보다 낮은 우선순위) */
    body { font-family: 'Noto Sans KR', sans-serif !important; }
    p, h1, h2, h3, h4, h5, h6, label, input, textarea, select, a, li, td, th,
    .stMarkdown, .stText, .stCaption {
        font-family: 'Noto Sans KR', sans-serif !important;
    }
    
    /* div와 span은 조건부 적용 (아이콘이 아닌 경우만) */
    div:not([class*="material"]):not([class*="Material"]):not([data-testid*="Icon"]):not([data-testid*="icon"]),
    span:not([class*="material"]):not([class*="Material"]):not([data-testid*="Icon"]):not([data-testid*="icon"]) {
        font-family: 'Noto Sans KR', sans-serif !important;
    }
    
    /* button도 조건부 적용 */
    button:not([class*="material"]):not([data-testid*="Icon"]):not([data-testid*="icon"]) {
        font-family: 'Noto Sans KR', sans-serif !important;
    }
    
    /* 상단 여백 강제 축소 */
    .main .block-container {
        padding-top: 0rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* 헤더 완전히 표시 (햄버거 메뉴를 위해) */
    header[data-testid="stHeader"] {
        display: flex !important;
        visibility: visible !important;
        height: auto !important;
        min-height: 3.5rem !important;
        padding: 0.5rem 1rem !important;
        background: transparent !important;
        border-bottom: none !important;
        position: relative !important;
        z-index: 2147483647 !important; /* 최상위 z-index 보장 */
        pointer-events: auto !important; /* 클릭 가능 보장 */
    }
    
    /* 햄버거 버튼 클릭 가능성 보장 */
    header[data-testid="stHeader"] button,
    header[data-testid="stHeader"] [role="button"],
    header[data-testid="stHeader"] > div > button,
    header[data-testid="stHeader"] > div > div > button {
        position: relative !important;
        z-index: 2147483647 !important; /* 최상위 z-index 보장 */
        pointer-events: auto !important; /* 클릭 가능 보장 */
    }
    
    /* 제목 위 불필요한 간격 제거 */
    #root > div:nth-child(1) > div > div > div > div > section > div {
        padding-top: 0rem !important;
    }

    /* 버튼 마이크로 인터랙션 */
    button[kind="primary"], button[kind="secondary"] {
        transition: all 0.2s ease-in-out !important;
        border-radius: 8px !important;
    }
    button:hover {
        transform: scale(1.02) !important;
        filter: brightness(1.1) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
    }

    /* 강조 버튼 애니메이션 (Glow) - 입력허브 시작 필요 버튼 제외 */
    .stButton > button[kind="primary"]:not([data-start-needed-applied]) {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
        border: none !important;
        animation: pulse-glow 3s infinite !important;
    }
    
    /* 입력허브 시작 필요 버튼은 페이지별 CSS 우선 */
    [data-ps-scope="input_hub"] .stButton > button[kind="primary"][data-start-needed-applied],
    [data-ps-scope="input_hub"] button[kind="primary"]:has-text("🚀") {
        animation: inherit !important;
    }

    /* 글래스모피즘 효과 카드 */
    .glass-card {
        background: rgba(30, 41, 59, 0.7) !important;
        backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
    }
</style>
""", unsafe_allow_html=True)

# Material Icons 폰트 강제 적용 JavaScript - 정확한 타겟팅
st.markdown("""
<script>
(function() {
    'use strict';
    
    // Material Icons 폰트 강제 로드
    const linkId = 'material-icons-font-link';
    if (!document.getElementById(linkId)) {
        const link = document.createElement('link');
        link.id = linkId;
        link.href = 'https://fonts.googleapis.com/icon?family=Material+Icons';
        link.rel = 'stylesheet';
        document.head.insertBefore(link, document.head.firstChild);
    }
    
    // 본질적 해결: Material Icons 폰트 강제 적용 및 Expander 화살표 위치 변경
    function fixMaterialIcons() {
        // 1. 모든 stIconMaterial 요소에 Material Icons 폰트 강제 적용
        document.querySelectorAll('[data-testid="stIconMaterial"]').forEach(el => {
            // Material Icons 폰트 적용
            el.style.setProperty('font-family', "'Material Icons'", 'important');
            el.style.setProperty('font-weight', 'normal', 'important');
            el.style.setProperty('font-style', 'normal', 'important');
            el.style.setProperty('font-size', '24px', 'important');
            el.style.setProperty('line-height', '1', 'important');
            el.style.setProperty('letter-spacing', 'normal', 'important');
            el.style.setProperty('text-transform', 'none', 'important');
            el.style.setProperty('display', 'inline-block', 'important');
            el.style.setProperty('white-space', 'nowrap', 'important');
            el.style.setProperty('-webkit-font-feature-settings', "'liga'", 'important');
            el.style.setProperty('-webkit-font-smoothing', 'antialiased', 'important');
            
            // overflow를 visible로 하여 텍스트가 잘리지 않도록
            el.style.setProperty('overflow', 'visible', 'important');
            el.style.setProperty('width', 'auto', 'important');
            el.style.setProperty('min-width', '24px', 'important');
            el.style.setProperty('max-width', 'none', 'important');
            el.style.setProperty('flex-shrink', '0', 'important');
            el.style.setProperty('vertical-align', 'middle', 'important');
        });
        
        // 2. Expander 화살표를 제목 앞으로 이동 (하이브리드 접근)
        document.querySelectorAll('[data-testid="stExpander"]').forEach(expander => {
            // 여러 가능한 버튼 선택자 시도
            let button = expander.querySelector('button');
            if (!button) button = expander.querySelector('div[role="button"]');
            if (!button) button = expander.querySelector('> div > div');
            if (!button) {
                // 더 넓은 범위로 찾기
                const divs = expander.querySelectorAll('div');
                for (let div of divs) {
                    if (div.querySelector('[data-testid="stIconMaterial"]')) {
                        button = div;
                        break;
                    }
                }
            }
            if (!button) return;
            
            const icon = button.querySelector('[data-testid="stIconMaterial"]');
            if (!icon) return;
            
            // 이미 처리된 expander인지 확인 (중복 처리 방지)
            if (expander.hasAttribute('data-icon-reordered')) return;
            expander.setAttribute('data-icon-reordered', 'true');
            
            // 방법 1: Flexbox Order 사용 (CSS 우선)
            const buttonStyle = window.getComputedStyle(button);
            if (buttonStyle.display !== 'flex' && buttonStyle.display !== 'inline-flex') {
                button.style.setProperty('display', 'flex', 'important');
                button.style.setProperty('flex-direction', 'row', 'important');
                button.style.setProperty('align-items', 'center', 'important');
            }
            
            // 아이콘 order 설정
            icon.style.setProperty('order', '-1', 'important');
            icon.style.setProperty('margin-right', '0.5rem', 'important');
            icon.style.setProperty('margin-left', '0', 'important');
            icon.style.setProperty('position', 'static', 'important');
            
            // 방법 2: DOM 순서 변경 (백업, CSS order가 작동하지 않는 경우)
            setTimeout(() => {
                const children = Array.from(button.childNodes);
                const iconIndex = children.indexOf(icon);
                
                // 텍스트 노드나 다른 요소 찾기
                let firstTextOrElement = null;
                for (let child of children) {
                    if (child === icon) continue;
                    if (child.nodeType === Node.TEXT_NODE && child.textContent.trim()) {
                        firstTextOrElement = child;
                        break;
                    } else if (child.nodeType === Node.ELEMENT_NODE && child !== icon) {
                        // 제목을 담고 있는 요소 찾기
                        if (!child.querySelector('[data-testid="stIconMaterial"]')) {
                            firstTextOrElement = child;
                            break;
                        }
                    }
                }
                
                // 아이콘이 첫 번째 요소가 아니고, 다른 요소가 있는 경우
                if (iconIndex > 0 && firstTextOrElement) {
                    const firstIndex = children.indexOf(firstTextOrElement);
                    if (firstIndex < iconIndex) {
                        // DOM 순서 변경: 아이콘을 첫 번째 요소 앞으로
                        button.insertBefore(icon, firstTextOrElement);
                    }
                } else if (iconIndex > 0 && children.length > 1) {
                    // 텍스트 노드를 찾지 못한 경우, 첫 번째 요소 앞으로 이동
                    const firstChild = children.find(child => child !== icon);
                    if (firstChild) {
                        button.insertBefore(icon, firstChild);
                    }
                }
            }, 10);
        });
        
        // 3. Expander 내부 버튼 테두리 명시적 적용
        document.querySelectorAll('[data-testid="stExpander"] .stButton > button, [data-testid="stExpander"] button[kind="secondary"], [data-testid="stExpander"] button[kind="primary"]').forEach(el => {
            // 테두리 스타일 강제 적용
            const computedStyle = window.getComputedStyle(el);
            const currentBorder = computedStyle.borderWidth;
            
            if (!currentBorder || currentBorder === '0px') {
                el.style.setProperty('border', '1px solid rgba(232, 238, 247, 0.12)', 'important');
                el.style.setProperty('border-width', '1px', 'important');
                el.style.setProperty('border-style', 'solid', 'important');
                el.style.setProperty('border-radius', '8px', 'important');
            }
        });
        
        // 4. 다른 아이콘 요소들도 확인
        document.querySelectorAll('[data-testid*="Icon"], [data-testid*="icon"]').forEach(el => {
            if (el.getAttribute('data-testid') !== 'stIconMaterial') {
                const text = el.textContent.trim();
                if (text.includes('_') || text === 'key' || text.includes('arrow') || text.includes('menu')) {
                    el.style.setProperty('font-family', "'Material Icons'", 'important');
                    el.style.setProperty('font-weight', 'normal', 'important');
                    el.style.setProperty('font-style', 'normal', 'important');
                    el.style.setProperty('font-size', '24px', 'important');
                    el.style.setProperty('line-height', '1', 'important');
                }
            }
        });
    }
    
    // 즉시 실행
    fixMaterialIcons();
    
    // DOMContentLoaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            fixMaterialIcons();
            // DOM이 완전히 로드된 후 다시 한 번 확인
            setTimeout(fixMaterialIcons, 100);
        });
    } else {
        setTimeout(fixMaterialIcons, 100);
    }
    
    // load 이벤트
    window.addEventListener('load', function() {
        setTimeout(fixMaterialIcons, 50);
        setTimeout(fixMaterialIcons, 200);
        setTimeout(fixMaterialIcons, 500);
    });
    
    // MutationObserver - 새로 추가된 expander 감지
    const observer = new MutationObserver(function(mutations) {
        let hasNewExpander = false;
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        if (node.getAttribute && node.getAttribute('data-testid') === 'stExpander') {
                            hasNewExpander = true;
                        } else if (node.querySelector && node.querySelector('[data-testid="stExpander"]')) {
                            hasNewExpander = true;
                        }
                    }
                });
            }
        });
        if (hasNewExpander) {
            setTimeout(fixMaterialIcons, 10);
        }
    });
    
    if (document.body) {
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            characterData: false,
            attributes: false
        });
    }
    
    // 주기적 확인 (덜 자주, 성능 고려)
    setInterval(fixMaterialIcons, 1000);
})();
</script>
""", unsafe_allow_html=True)

# THEME 계층: 다크 모드 오버라이드 (조건부)
if st.session_state.get("theme", "light") == "dark":
    inject_theme("<style>.main { background-color: #020617 !important; color: #e5e7eb !important; }</style>", "dark_mode_override")

# Sidebar Navigation
# 메뉴 구조 정의
menu = {
    "🏠 홈": [("홈", "홈")],
    "✍ 입력": {
        "main": [("데이터 입력센터", "입력 허브")],
        "sub": [
            ("오늘 마감", "일일 입력(통합)"),
            ("매출·방문자", "매출 등록"),
            ("판매량", "판매량 등록"),
            ("월간 정산", "실제정산"),
            ("목표(비용)", "목표 비용구조"),
            ("목표(매출)", "목표 매출구조"),
            ("QSC 체크", "건강검진 실시")
        ]
    },
    "📊 분석": {
        "main": [("데이터 분석센터", "분석 허브")],
        "sub": [
            ("매출", "매출 관리"),
            ("판매·메뉴", "판매 관리"),
            ("원가", "비용 분석"),
            ("QSC 요약", "검진 결과 요약"),
            ("QSC 히스토리", "검진 히스토리"),
            ("하락 원인", "매출 하락 원인 찾기")
        ]
    },
    "🎯 전략": {
        "main": [("데이터 전략센터", "가게 전략 센터")],
        "sub": [
            ("메뉴 구성", "메뉴 등록"),
            ("메뉴 수익", "메뉴 수익 구조 설계실"),
            ("재료 구조", "재료 등록"),
            ("수익 구조", "수익 구조 설계실"),
            ("레시피", "레시피 등록")
        ]
    },
    "🛠 운영": [
        ("직원 연락망", "직원 연락망"),
        ("협력사 연락망", "협력사 연락망"),
        ("게시판", "게시판")
    ],
    "🧪 테스트": [
        ("화면테스트", "화면테스트")
    ]
}

def render_expanded_sidebar(menu):
    """펼친 상태 사이드바 렌더링 (구조만 담당, CSS는 전역 주입)"""
    # 매장 선택
    user_stores = get_user_stores()
    curr_name = get_current_store_name()
    if len(user_stores) > 1:
        store_options = {f"{s['name']} ({s['role']})": s['id'] for s in user_stores}
        selected = st.selectbox("🏪 매장 선택", options=list(store_options.keys()))
        if store_options[selected] != get_current_store_id():
            if switch_store(store_options[selected]): st.rerun()
    else:
        st.markdown(f"🏪 **{curr_name}**")
    
    # 메뉴 렌더링
    if "current_page" not in st.session_state:
        st.session_state.current_page = "홈"
    
    for cat, data in menu.items():
        # 카테고리 제목 (ultra-category 클래스)
        st.markdown(
            f'<div class="ultra-category">{cat}</div>',
            unsafe_allow_html=True
        )
        if isinstance(data, list):
            for label, key in data:
                if st.button(label, key=f"btn_{key}", use_container_width=True, 
                           type="primary" if st.session_state.current_page == key else "secondary"):
                    st.session_state.current_page = key
                    st.rerun()
        else:
            # Main items
            for label, key in data["main"]:
                if st.button(label, key=f"btn_{key}", use_container_width=True,
                           type="primary" if st.session_state.current_page == key else "secondary"):
                    st.session_state.current_page = key
                    st.rerun()
            # Sub items in expander
            with st.expander("상세 선택", expanded=False):
                for label, key in data["sub"]:
                    if st.button(label, key=f"btn_sub_{key}", use_container_width=True,
                               type="primary" if st.session_state.current_page == key else "secondary"):
                        st.session_state.current_page = key
                        st.rerun()
    
    # FX 토글 섹션
    st.markdown("---")
    st.markdown("**FX 설정**")
    st.sidebar.checkbox("FX: blur(backdrop-filter) ON", key="_ps_fx_blur_on", value=False, help="카드에 backdrop-filter blur 효과 적용 (기본 OFF)")
    
    # 시스템 버튼 (ultra-system wrapper)
    st.markdown('<div class="ultra-system">', unsafe_allow_html=True)
    if st.button("🚪 로그아웃"): 
        logout()
        st.rerun()
    if st.button("🔄 캐시 클리어"): 
        load_csv.clear()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# 사이드바 프리미엄 CSS 주입 (매 rerun마다 실행)
# 로그인 체크 후, 페이지 라우팅 전에 무조건 실행
inject_sidebar_premium_css()

# current_page 초기화
if "current_page" not in st.session_state:
    st.session_state.current_page = "홈"

# 기본 Streamlit 사이드바 렌더링 (기능 추가 없음)
with st.sidebar:
    render_expanded_sidebar(menu)

# Page Routing
page = st.session_state.get("current_page", "홈")

if st.session_state.get("_show_supabase_diagnosis", False):
    _diagnose_supabase_connection()

if page == "홈":
    st.sidebar.error("ROUTING -> HOME ✅ app.py 홈 분기 실행됨")
    # ui_pages/home.py에서 직접 import (__init__.py 우회)
    # import sys
    # import importlib.util
    # spec = importlib.util.spec_from_file_location("home_module", "ui_pages/home.py")
    # home_module = importlib.util.module_from_spec(spec)
    # spec.loader.exec_module(home_module)
    # home_module.render_home()
    
    # 더 간단한 방법: importlib로 직접 로드
    import importlib.util
    import os
    home_file_path = os.path.join(os.path.dirname(__file__), "ui_pages", "home.py")
    spec = importlib.util.spec_from_file_location("home_direct", home_file_path)
    home_direct = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(home_direct)
    st.sidebar.code(f"home_direct __file__: {home_direct.__file__}")
    home_direct.render_home()
elif page == "오늘의 전략 실행":
    from ui_pages.strategy.mission_detail import render_mission_detail
    render_mission_detail()
elif page == "입력 허브":
    from ui_pages.input.input_hub import render_input_hub_v3
    render_input_hub_v3()
elif page == "분석 허브":
    from ui_pages.analysis.analysis_hub import render_analysis_hub
    render_analysis_hub()
elif page == "일일 입력(통합)":
    from ui_pages.daily_input_hub import render_daily_input_hub
    render_daily_input_hub()
elif page == "매출 등록":
    from ui_pages.sales_entry import render_sales_entry
    render_sales_entry()
elif page == "분석총평":
    from ui_pages.analysis.analysis_summary import render_analysis_summary
    render_analysis_summary()
elif page == "매출 관리":
    from ui_pages.analysis.sales_analysis import render_sales_analysis
    render_sales_analysis()
elif page == "메뉴 입력":
    from ui_pages.input.menu_input import render_menu_input_page
    render_menu_input_page()
elif page == "재료 입력":
    from ui_pages.input.ingredient_input import render_ingredient_input_page
    render_ingredient_input_page()
elif page == "재고 입력":
    from ui_pages.input.inventory_input import render_inventory_input_page
    render_inventory_input_page()
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
    from ui_pages.analysis.sales_analysis import render_sales_analysis
    render_sales_analysis()
elif page == "판매량 등록":
    from ui_pages.sales_volume_entry import render_sales_volume_entry
    render_sales_volume_entry()
elif page == "건강검진 실시":
    from ui_pages.health_check.health_check_page import render_health_check_page
    render_health_check_page()
elif page == "검진 결과 요약":
    from ui_pages.health_check.health_check_result import render_health_check_result
    render_health_check_result()
elif page == "검진 히스토리":
    from ui_pages.health_check.health_check_history import render_health_check_history
    render_health_check_history()
elif page == "매출 하락 원인 찾기":
    from ui_pages.diagnostics.sales_drop_oneclick import render_sales_drop_oneclick
    render_sales_drop_oneclick()
elif page == "메뉴 수익 구조 설계실":
    from ui_pages.menu_profit_design_lab import render_menu_profit_design_lab
    render_menu_profit_design_lab()
elif page == "수익 구조 설계실":
    from ui_pages.revenue_structure_design_lab import render_revenue_structure_design_lab
    render_revenue_structure_design_lab()
elif page == "레시피 등록":
    from ui_pages.recipe_management import render_recipe_management
    render_recipe_management()
elif page == "목표 비용구조":
    from ui_pages.target_cost_structure import render_target_cost_structure
    render_target_cost_structure()
elif page == "목표 매출구조":
    from ui_pages.target_sales_structure import render_target_sales_structure
    render_target_sales_structure()
elif page == "직원 연락망":
    from ui_pages.staff_contacts import render_staff_contacts
    render_staff_contacts()
elif page == "협력사 연락망":
    from ui_pages.vendor_contacts import render_vendor_contacts
    render_vendor_contacts()
elif page == "주간 리포트":
    from ui_pages.weekly_report import render_weekly_report
    render_weekly_report()
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
elif page == "화면테스트":
    from ui_pages.design_test.header_unified_test import render_header_unified_test
    render_header_unified_test()

# ============================================
# 최종 안전핀 CSS (모든 CSS 주입 후 마지막에 주입)
# ============================================
if not st.session_state.get("_ps_final_safety_pin_injected", False):
    push_render_step("CSS_INJECT: app.py:1045 FINAL_SAFETY_PIN", extra={"where": "final"})
    final_safety_pin_css = """
    <style>
    /* keyframes 정의 (RESCUE 계층에서도 보장) */
    /* 컨텐츠 강제 복구 */
    [data-testid="stMain"], [data-testid="stMainBlockContainer"]{
      display: block !important;
      visibility: visible !important;
      opacity: 1 !important;
      /* transform: none 제거 - 애니메이션을 위해 제외 */
      filter: none !important;
      backdrop-filter: none !important;
      -webkit-backdrop-filter: none !important;
    }
    

    /* 헤더와 햄버거 버튼 최우선 보장 */
    header[data-testid="stHeader"] {
      position: relative !important;
      z-index: 2147483647 !important; /* 최상위 z-index 보장 */
      pointer-events: auto !important; /* 클릭 가능 보장 */
    }
    
    /* 햄버거 버튼 클릭 가능성 보장 */
    header[data-testid="stHeader"] button,
    header[data-testid="stHeader"] [role="button"],
    header[data-testid="stHeader"] > div > button,
    header[data-testid="stHeader"] > div > div > button,
    header[data-testid="stHeader"] > div > div > div > button {
      position: relative !important;
      z-index: 2147483647 !important; /* 최상위 z-index 보장 */
      pointer-events: auto !important; /* 클릭 가능 보장 */
    }
    
    /* 컨텐츠 레이어 올리기 */
    [data-testid="stAppViewContainer"]{ position: relative !important; z-index: 1 !important; }
    [data-testid="stSidebar"], [data-testid="stMain"], [data-testid="stMainBlockContainer"]{
      position: relative !important;
      z-index: 2147483000 !important;
    }

    /* 배경/오버레이 레이어는 클릭 방해 금지 + 뒤로 */
    .ps-ultra-bg, .ps-mesh, .ps-overlay, .ultra-bg, .mesh-bg, .animated-bg,
    .overlay, .backdrop, .background, .bg-layer {
      pointer-events: none !important;
      z-index: 0 !important;
    }
    
    /* 헤더 위를 덮는 모든 fixed/absolute 요소 차단 */
    div[style*="position: fixed"][style*="top: 0"],
    div[style*="position: fixed"][style*="top:0"],
    div[style*="position: absolute"][style*="top: 0"],
    div[style*="position: absolute"][style*="top:0"] {
      /* 헤더 영역(상단 60px)을 덮는 경우 pointer-events 차단 */
      pointer-events: none !important;
      z-index: -1 !important;
    }
    
    /* 파란 투명 화면 문제 해결: ps-hub-bg::before와 ::after 완전 제거 */
    [data-ps-scope="input_hub"].ps-hub-bg::before,
    [data-ps-scope="input_hub"].ps-hub-bg::after {
      content: none !important;
      display: none !important;
      visibility: hidden !important;
      opacity: 0 !important;
      pointer-events: none !important;
      z-index: -1 !important;
    }
    </style>
    """
    inject_rescue(final_safety_pin_css, "final_safety_pin")
    
    # 햄버거 버튼 클릭 가능성 보장 JavaScript
    hamburger_fix_js = """
    <script>
    (function() {
        'use strict';
        
        function ensureHamburgerClickable() {
            try {
                // 헤더 찾기
                const header = document.querySelector('header[data-testid="stHeader"]');
                if (!header) return;
                
                // 헤더 z-index 최상위 보장
                header.style.setProperty('z-index', '2147483647', 'important');
                header.style.setProperty('position', 'relative', 'important');
                header.style.setProperty('pointer-events', 'auto', 'important');
                
                // 헤더 내부 모든 버튼 찾기
                const buttons = header.querySelectorAll('button, [role="button"]');
                buttons.forEach(btn => {
                    btn.style.setProperty('z-index', '2147483647', 'important');
                    btn.style.setProperty('position', 'relative', 'important');
                    btn.style.setProperty('pointer-events', 'auto', 'important');
                });
                
                // 헤더 위를 덮는 모든 요소 찾기
                const allElements = document.querySelectorAll('*');
                allElements.forEach(el => {
                    if (el === header || header.contains(el)) return;
                    
                    const style = window.getComputedStyle(el);
                    const rect = el.getBoundingClientRect();
                    const headerRect = header.getBoundingClientRect();
                    
                    // 헤더 영역과 겹치는지 확인
                    const overlaps = !(
                        rect.bottom < headerRect.top ||
                        rect.top > headerRect.bottom ||
                        rect.right < headerRect.left ||
                        rect.left > headerRect.right
                    );
                    
                    if (overlaps && (style.position === 'fixed' || style.position === 'absolute')) {
                        // 헤더보다 z-index가 높으면 낮춤
                        const zIndex = parseInt(style.zIndex) || 0;
                        if (zIndex >= 2147483000) {
                            el.style.setProperty('pointer-events', 'none', 'important');
                            el.style.setProperty('z-index', '-1', 'important');
                        }
                    }
                });
            } catch (e) {
                // 에러 무시
            }
        }
        
        // 즉시 실행
        ensureHamburgerClickable();
        
        // DOMContentLoaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', ensureHamburgerClickable);
        }
        
        // load 이벤트
        window.addEventListener('load', ensureHamburgerClickable);
        
        // 사이드바 토글 시마다 실행
        const observer = new MutationObserver(function() {
            setTimeout(ensureHamburgerClickable, 100);
        });
        
        if (document.body) {
            observer.observe(document.body, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ['style', 'class']
            });
        }
        
        // 주기적 확인 (덜 자주)
        setInterval(ensureHamburgerClickable, 2000);
    })();
    </script>
    """
    st.markdown(hamburger_fix_js, unsafe_allow_html=True)
    
    st.session_state["_ps_final_safety_pin_injected"] = True
