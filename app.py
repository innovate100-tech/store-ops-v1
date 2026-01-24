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

    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/icon?family=Material+Icons');
    
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
    }
    
    /* Streamlit 네이티브 사이드바 토글 버튼 완전히 숨김 및 비활성화 (최우선) */
    button[aria-label*="sidebar"],
    button[aria-label*="메뉴"],
    button[aria-label*="Menu"],
    button[aria-label*="Close"],
    button[aria-label*="열기"],
    button[aria-label*="Open"],
    [data-testid="stHeader"] button:first-child,
    header button:first-child,
    button[kind="header"]:first-child,
    header[data-testid="stHeader"] button:first-child {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
        width: 0 !important;
        height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
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

    /* 강조 버튼 애니메이션 (Glow) */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
        border: none !important;
        animation: pulse-glow 3s infinite !important;
    }

    /* 글래스모피즘 효과 카드 */
    .glass-card {
        background: rgba(30, 41, 59, 0.7) !important;
        backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
    }
    
    /* Streamlit 기본 사이드바 완전히 숨기기 (커스텀 사이드바 사용) */
    [data-testid="stSidebar"],
    section[data-testid="stSidebar"],
    div[data-testid="stSidebar"],
    .css-1d391kg,
    .css-1lcbmhc {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
    }
    
    /* Streamlit 네이티브 토글 버튼 완전히 숨김 */
    button[aria-label*="sidebar"],
    button[aria-label*="메뉴"],
    button[aria-label*="Menu"],
    button[aria-label*="Close"],
    button[aria-label*="열기"],
    button[aria-label*="Open"],
    [data-testid="stHeader"] button:first-child,
    [data-testid="stHeader"] button:first-of-type,
    [data-testid="stHeader"] button,
    header button:first-child,
    header button:first-of-type,
    header[data-testid="stHeader"] button,
    header[data-testid="stHeader"] button:first-child,
    button[kind="header"]:first-child {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
        width: 0 !important;
        height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        position: absolute !important;
        left: -9999px !important;
        z-index: -1 !important;
    }
    
    /* 헤더 자체에서도 버튼 숨김 */
    [data-testid="stHeader"] button:hover,
    header button:hover {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* 메인 콘텐츠 영역은 커스텀 사이드바 JavaScript에서 조정 */
    [data-testid="stSidebar"],
    section[data-testid="stSidebar"],
    div[data-testid="stSidebar"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        transform: translateX(0) !important;
        position: relative !important;
    }
    
    /* 사이드바가 완전히 사라지지 않도록 보장 */
    [data-testid="stSidebar"][aria-expanded="false"],
    [data-testid="stSidebar"][aria-expanded="true"] {
        display: block !important;
        visibility: visible !important;
        transform: translateX(0) !important;
    }
    
    /* Streamlit이 자동으로 메인 콘텐츠를 조정하도록 함 - 추가 margin 제거 */
    /* Streamlit이 사이드바가 열려있을 때 자동으로 메인 콘텐츠 영역을 조정하므로 
       추가 margin을 주지 않음 */
    
    /* 사이드바 오버레이 제거 */
    .css-1d391kg[aria-expanded="false"]::before,
    [data-testid="stSidebar"][aria-expanded="false"]::before {
        display: none !important;
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

# 사이드바 상태 동기화 JavaScript (최종 강화 버전 - Streamlit 내부 함수 완전 차단)
sidebar_collapsed_js = "true" if st.session_state.get("sidebar_collapsed", False) else "false"
st.markdown(f"""
<script>
(function() {{
    'use strict';
    
    // Streamlit의 내부 함수 완전 차단 (최우선 실행)
    (function() {{
        // window.streamlit 객체가 있으면 완전 차단
        if (window.streamlit) {{
            // toggleSidebar 함수 완전 차단
            if (window.streamlit.toggleSidebar) {{
                window.streamlit.toggleSidebar = function() {{
                    console.log('[Custom] Streamlit toggleSidebar blocked');
                    return false;
                }};
            }}
            
            // setSidebarVisibility 함수도 차단
            if (window.streamlit.setSidebarVisibility) {{
                window.streamlit.setSidebarVisibility = function(visible) {{
                    console.log('[Custom] Streamlit setSidebarVisibility blocked');
                    return true; // 항상 visible로 유지
                }};
            }}
        }}
        
        // Streamlit의 내부 이벤트 리스너 차단
        const originalAddEventListener = EventTarget.prototype.addEventListener;
        EventTarget.prototype.addEventListener = function(type, listener, options) {{
            // 사이드바 토글 관련 이벤트 차단
            if (type === 'click' && listener && (
                listener.toString().includes('sidebar') ||
                listener.toString().includes('toggle') ||
                (listener.name && listener.name.includes('sidebar'))
            )) {{
                console.log('[Custom] Blocked sidebar click event listener');
                return;
            }}
            return originalAddEventListener.call(this, type, listener, options);
        }};
    }})();
    
    // 햄버거 버튼 완전히 제거 함수 (전역) - DOM에서 완전 삭제
    function removeHamburgerButtons() {{
        const headerButtons = document.querySelectorAll(
            '[data-testid="stHeader"] button, ' +
            'header button, ' +
            'button[aria-label*="sidebar"], ' +
            'button[aria-label*="메뉴"], ' +
            'button[aria-label*="Menu"]'
        );
        
        headerButtons.forEach(function(btn) {{
            const label = btn.getAttribute('aria-label') || '';
            const text = btn.textContent || '';
            const icon = btn.querySelector('[data-testid*="Icon"]') || btn.querySelector('svg');
            
            // 햄버거 버튼 판별 (여러 조건)
            const isHamburger = 
                label.includes('sidebar') || 
                label.includes('메뉴') || 
                label.includes('Menu') || 
                label.includes('Close') || 
                label.includes('열기') || 
                label.includes('Open') ||
                text.includes('☰') ||
                text.includes('≡') ||
                (icon && (icon.textContent?.includes('menu') || icon.getAttribute('data-icon')?.includes('menu')));
            
            if (isHamburger) {{
                // DOM에서 완전히 제거 (가장 확실한 방법)
                try {{
                    if (btn.parentNode) {{
                        btn.parentNode.removeChild(btn);
                    }}
                }} catch(e) {{
                    // 제거 실패 시 완전히 숨김
                    btn.style.setProperty('display', 'none', 'important');
                    btn.style.setProperty('visibility', 'hidden', 'important');
                    btn.style.setProperty('opacity', '0', 'important');
                    btn.style.setProperty('pointer-events', 'none', 'important');
                    btn.style.setProperty('width', '0', 'important');
                    btn.style.setProperty('height', '0', 'important');
                    btn.style.setProperty('padding', '0', 'important');
                    btn.style.setProperty('margin', '0', 'important');
                    btn.style.setProperty('position', 'absolute', 'important');
                    btn.style.setProperty('left', '-9999px', 'important');
                    btn.style.setProperty('z-index', '-1', 'important');
                    btn.setAttribute('disabled', 'true');
                    btn.setAttribute('aria-hidden', 'true');
                    btn.setAttribute('tabindex', '-1', 'important');
                    
                    // 클릭 이벤트 완전 차단
                    const blockClick = function(e) {{
                        e.preventDefault();
                        e.stopPropagation();
                        e.stopImmediatePropagation();
                        return false;
                    }};
                    btn.removeEventListener('click', blockClick, true);
                    btn.addEventListener('click', blockClick, true);
                    btn.removeEventListener('mousedown', blockClick, true);
                    btn.addEventListener('mousedown', blockClick, true);
                }}
            }}
        }});
    }}
    
    function syncSidebarState() {{
        // 사이드바가 항상 표시되도록 강제
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        if (!sidebar) return;
        
        // 사이드바가 사라지지 않도록 강제
        sidebar.setAttribute('aria-expanded', 'true');
        sidebar.style.setProperty('display', 'block', 'important');
        sidebar.style.setProperty('visibility', 'visible', 'important');
        sidebar.style.setProperty('opacity', '1', 'important');
        sidebar.style.setProperty('transform', 'translateX(0)', 'important');
        sidebar.style.setProperty('position', 'relative', 'important');
        
        const isCollapsed = sidebar.getAttribute('data-sidebar-collapsed') === 'true' || {sidebar_collapsed_js};
        const targetWidth = isCollapsed ? '4rem' : '15rem';
        const targetWidthPx = isCollapsed ? '64px' : '240px';
        
        // 클래스 및 속성 설정
        if (isCollapsed) {{
            sidebar.classList.add('sidebar-collapsed');
            sidebar.setAttribute('data-sidebar-collapsed', 'true');
        }} else {{
            sidebar.classList.remove('sidebar-collapsed');
            sidebar.setAttribute('data-sidebar-collapsed', 'false');
        }}
        
        // 사이드바 자체에 인라인 스타일로 강제 적용 (cssText 사용 - 더 강력)
        // 기존 스타일을 완전히 덮어쓰지 않고 필요한 속성만 추가
        sidebar.style.setProperty('display', 'block', 'important');
        sidebar.style.setProperty('visibility', 'visible', 'important');
        sidebar.style.setProperty('opacity', '1', 'important');
        sidebar.style.setProperty('transform', 'translateX(0)', 'important');
        sidebar.style.setProperty('position', 'relative', 'important');
        sidebar.style.setProperty('width', targetWidth, 'important');
        sidebar.style.setProperty('min-width', targetWidth, 'important');
        sidebar.style.setProperty('max-width', targetWidth, 'important');
        sidebar.style.setProperty('flex-basis', targetWidth, 'important');
        sidebar.style.setProperty('flex-shrink', '0', 'important');
        sidebar.style.setProperty('flex-grow', '0', 'important');
        sidebar.style.setProperty('flex', '0 0 ' + targetWidth, 'important');
        
        // 사이드바의 모든 부모 요소도 조정
        let parent = sidebar.parentElement;
        let depth = 0;
        while (parent && parent !== document.body && depth < 10) {{
            if (parent.style) {{
                // 부모가 flex 컨테이너인 경우
                const parentComputed = window.getComputedStyle(parent);
                if (parentComputed.display === 'flex' || parentComputed.display === 'inline-flex') {{
                    // 사이드바 자식 요소의 flex 속성 강제
                    const sidebarChild = parent.querySelector('[data-testid="stSidebar"]');
                    if (sidebarChild) {{
                        sidebarChild.style.setProperty('flex', '0 0 ' + targetWidth, 'important');
                        sidebarChild.style.setProperty('width', targetWidth, 'important');
                    }}
                }}
            }}
            parent = parent.parentElement;
            depth++;
        }}
        
        // 모든 가능한 사이드바 관련 요소에도 적용
        const sidebarSelectors = [
            '[data-testid="stSidebar"]',
            'section[data-testid="stSidebar"]',
            'div[data-testid="stSidebar"]',
            '.css-1d391kg',
            '.css-1lcbmhc',
            '[class*="stSidebar"]'
        ];
        
        sidebarSelectors.forEach(function(selector) {{
            try {{
                const elements = document.querySelectorAll(selector);
                elements.forEach(function(el) {{
                    el.style.setProperty('width', targetWidth, 'important');
                    el.style.setProperty('min-width', targetWidth, 'important');
                    el.style.setProperty('max-width', targetWidth, 'important');
                    el.style.setProperty('flex-basis', targetWidth, 'important');
                    el.style.setProperty('flex-shrink', '0', 'important');
                    el.style.setProperty('flex-grow', '0', 'important');
                    el.style.setProperty('display', 'block', 'important');
                    el.style.setProperty('visibility', 'visible', 'important');
                }});
            }} catch(e) {{
                // 선택자 실패 무시
            }}
        }});
        
        // Streamlit의 레이아웃 컨테이너 찾아서 강제 조정
        const appContainer = document.querySelector('[data-testid="stAppViewContainer"]');
        if (appContainer) {{
            const computed = window.getComputedStyle(appContainer);
            
            // flexbox 레이아웃인 경우 - 더 강력하게
            if (computed.display === 'flex' || computed.display === 'inline-flex') {{
                // 사이드바의 flex 속성 강제 설정
                sidebar.style.setProperty('flex', '0 0 ' + targetWidth, 'important');
                sidebar.style.setProperty('flex-basis', targetWidth, 'important');
                sidebar.style.setProperty('flex-shrink', '0', 'important');
                sidebar.style.setProperty('flex-grow', '0', 'important');
                sidebar.style.setProperty('width', targetWidth, 'important');
                sidebar.style.setProperty('min-width', targetWidth, 'important');
                sidebar.style.setProperty('max-width', targetWidth, 'important');
                
                // 부모 컨테이너의 자식 요소들도 조정
                const children = Array.from(appContainer.children);
                children.forEach(function(child) {{
                    if (child === sidebar || child.querySelector('[data-testid="stSidebar"]') || 
                        child.getAttribute('data-testid') === 'stSidebar') {{
                        child.style.setProperty('flex', '0 0 ' + targetWidth, 'important');
                        child.style.setProperty('flex-basis', targetWidth, 'important');
                        child.style.setProperty('flex-shrink', '0', 'important');
                        child.style.setProperty('flex-grow', '0', 'important');
                        child.style.setProperty('width', targetWidth, 'important');
                        child.style.setProperty('min-width', targetWidth, 'important');
                        child.style.setProperty('max-width', targetWidth, 'important');
                    }} else {{
                        // 메인 콘텐츠 영역
                        child.style.setProperty('flex', '1 1 auto', 'important');
                        child.style.setProperty('margin-left', '0', 'important');
                    }}
                }});
                
                // appContainer 자체도 조정
                appContainer.style.setProperty('display', 'flex', 'important');
            }}
            
            // grid 레이아웃인 경우
            if (computed.display === 'grid') {{
                appContainer.style.setProperty('grid-template-columns', 
                    targetWidth + ' 1fr', 'important');
            }}
        }}
        
        // CSS 변수로도 설정 (더 강력한 방법)
        document.documentElement.style.setProperty('--sidebar-width', targetWidth, 'important');
        document.documentElement.style.setProperty('--sidebar-width-px', targetWidthPx, 'important');
        
        // 모든 스타일시트에도 강제 적용
        const styleSheets = document.styleSheets;
        for (let i = 0; i < styleSheets.length; i++) {{
            try {{
                const sheet = styleSheets[i];
                if (sheet.cssRules) {{
                    for (let j = 0; j < sheet.cssRules.length; j++) {{
                        const rule = sheet.cssRules[j];
                        if (rule.selectorText && rule.selectorText.includes('stSidebar')) {{
                            try {{
                                rule.style.setProperty('width', targetWidth, 'important');
                                rule.style.setProperty('min-width', targetWidth, 'important');
                                rule.style.setProperty('max-width', targetWidth, 'important');
                            }} catch(e) {{
                                // 읽기 전용 스타일시트는 무시
                            }}
                        }}
                    }}
                }}
            }} catch(e) {{
                // 크로스 오리진 스타일시트는 무시
            }}
        }}
        
        // 메인 콘텐츠 영역도 조정
        const mainSelectors = [
            '[data-testid="stAppViewContainer"] > div:not([data-testid="stSidebar"])',
            '.main',
            '.block-container',
            '[class*="block-container"]'
        ];
        
        mainSelectors.forEach(function(selector) {{
            try {{
                const elements = document.querySelectorAll(selector);
                elements.forEach(function(el) {{
                    // 사이드바가 아닌 경우만 조정
                    if (!el.closest('[data-testid="stSidebar"]')) {{
                        el.style.setProperty('margin-left', targetWidthPx, 'important');
                    }}
                }});
            }} catch(e) {{
                // 선택자 실패 무시
            }}
        }});
        
        // 햄버거 버튼 제거
        removeHamburgerButtons();
        
        // 사이드바가 사라지지 않도록 최종 보장
        if (sidebar) {{
            const computed = window.getComputedStyle(sidebar);
            if (computed.display === 'none' || computed.visibility === 'hidden') {{
                sidebar.style.setProperty('display', 'block', 'important');
                sidebar.style.setProperty('visibility', 'visible', 'important');
                sidebar.style.setProperty('opacity', '1', 'important');
            }}
        }}
    }}
    
    // 즉시 실행 (여러 번 실행)
    syncSidebarState();
    removeHamburgerButtons();
    
    // DOM 로드 후 실행 (여러 번 실행)
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', function() {{
            removeHamburgerButtons();
            syncSidebarState();
            setTimeout(function() {{ removeHamburgerButtons(); syncSidebarState(); }}, 10);
            setTimeout(function() {{ removeHamburgerButtons(); syncSidebarState(); }}, 50);
            setTimeout(function() {{ removeHamburgerButtons(); syncSidebarState(); }}, 100);
            setTimeout(function() {{ removeHamburgerButtons(); syncSidebarState(); }}, 200);
            setTimeout(function() {{ removeHamburgerButtons(); syncSidebarState(); }}, 500);
        }});
    }} else {{
        setTimeout(function() {{ removeHamburgerButtons(); syncSidebarState(); }}, 10);
        setTimeout(function() {{ removeHamburgerButtons(); syncSidebarState(); }}, 50);
        setTimeout(function() {{ removeHamburgerButtons(); syncSidebarState(); }}, 100);
        setTimeout(function() {{ removeHamburgerButtons(); syncSidebarState(); }}, 200);
        setTimeout(function() {{ removeHamburgerButtons(); syncSidebarState(); }}, 500);
    }}
    
    // 주기적 확인 (매우 자주 체크 - 10ms마다)
    setInterval(function() {{
        removeHamburgerButtons();
        syncSidebarState();
    }}, 10);
    
    // requestAnimationFrame으로도 지속적으로 강제 적용 (매우 자주)
    function forceSidebarWidth() {{
        removeHamburgerButtons();
        
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        if (!sidebar) {{
            requestAnimationFrame(forceSidebarWidth);
            return;
        }}
        
        const isCollapsed = sidebar.getAttribute('data-sidebar-collapsed') === 'true' || {sidebar_collapsed_js};
        const targetWidth = isCollapsed ? '4rem' : '15rem';
        const targetWidthPx = isCollapsed ? '64px' : '240px';
        
        // 사이드바 폭 강제 적용 (모든 방법 시도)
        sidebar.style.setProperty('width', targetWidth, 'important');
        sidebar.style.setProperty('min-width', targetWidth, 'important');
        sidebar.style.setProperty('max-width', targetWidth, 'important');
        sidebar.style.setProperty('flex-basis', targetWidth, 'important');
        sidebar.style.setProperty('flex', '0 0 ' + targetWidth, 'important');
        sidebar.style.setProperty('flex-shrink', '0', 'important');
        sidebar.style.setProperty('flex-grow', '0', 'important');
        
        // 사이드바의 모든 부모 요소들도 조정
        let parent = sidebar.parentElement;
        let depth = 0;
        while (parent && parent !== document.body && depth < 15) {{
            const computed = window.getComputedStyle(parent);
            if (computed.display === 'flex' || computed.display === 'inline-flex') {{
                // flex 컨테이너인 경우 자식 요소 조정
                Array.from(parent.children).forEach(function(child) {{
                    if (child === sidebar || child.querySelector('[data-testid="stSidebar"]') || 
                        child.getAttribute('data-testid') === 'stSidebar') {{
                        child.style.setProperty('flex', '0 0 ' + targetWidth, 'important');
                        child.style.setProperty('width', targetWidth, 'important');
                        child.style.setProperty('min-width', targetWidth, 'important');
                        child.style.setProperty('max-width', targetWidth, 'important');
                        child.style.setProperty('flex-basis', targetWidth, 'important');
                    }}
                }});
            }}
            if (computed.display === 'grid') {{
                parent.style.setProperty('grid-template-columns', targetWidth + ' 1fr', 'important');
            }}
            parent = parent.parentElement;
            depth++;
        }}
        
        // 메인 콘텐츠 영역도 조정
        const mainContent = document.querySelector('[data-testid="stAppViewContainer"] > div:not([data-testid="stSidebar"])');
        if (mainContent) {{
            mainContent.style.setProperty('margin-left', targetWidthPx, 'important');
        }}
        
        requestAnimationFrame(forceSidebarWidth);
    }}
    requestAnimationFrame(forceSidebarWidth);
    
    // 사이드바가 사라지는 것을 방지하는 감시자 (강화 버전)
    const sidebarWatcher = new MutationObserver(function(mutations) {{
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        if (sidebar) {{
            const computed = window.getComputedStyle(sidebar);
            const display = computed.display;
            const visibility = computed.visibility;
            const opacity = computed.opacity;
            
            // 사이드바가 사라지려고 하면 즉시 복구
            if (display === 'none' || visibility === 'hidden' || opacity === '0') {{
                sidebar.style.setProperty('display', 'block', 'important');
                sidebar.style.setProperty('visibility', 'visible', 'important');
                sidebar.style.setProperty('opacity', '1', 'important');
                sidebar.setAttribute('aria-expanded', 'true');
            }}
        }}
        
        // 햄버거 버튼 제거 함수 호출
        removeHamburgerButtons();
        syncSidebarState();
    }});
    
    if (document.body) {{
        sidebarWatcher.observe(document.body, {{
            attributes: true,
            childList: true,
            subtree: true,
            attributeFilter: ['style', 'aria-expanded', 'class', 'aria-hidden']
        }});
    }}
    
    // 사이드바가 사라지는 것을 방지하는 추가 보호
    document.addEventListener('click', function(e) {{
        const target = e.target;
        const isHeaderButton = target && (
            target.closest('[data-testid="stHeader"]') || 
            target.getAttribute('aria-label')?.includes('sidebar') ||
            target.closest('button[aria-label*="sidebar"]')
        );
        
        if (isHeaderButton) {{
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            
            // 사이드바 복구
            const sidebar = document.querySelector('[data-testid="stSidebar"]');
            if (sidebar) {{
                sidebar.style.setProperty('display', 'block', 'important');
                sidebar.style.setProperty('visibility', 'visible', 'important');
                sidebar.setAttribute('aria-expanded', 'true');
            }}
            
            // 햄버거 버튼 제거
            removeHamburgerButtons();
            return false;
        }}
    }}, true);
    
    // 마우스 오버 시에도 햄버거 버튼 제거 (더 자주 체크)
    document.addEventListener('mouseover', function(e) {{
        const target = e.target;
        if (target && (target.closest('[data-testid="stHeader"]') || target.closest('header'))) {{
            removeHamburgerButtons();
        }}
    }}, true);
    
    // 마우스 이동 시에도 체크
    document.addEventListener('mousemove', function(e) {{
        const target = e.target;
        if (target && (target.closest('[data-testid="stHeader"]') || target.closest('header'))) {{
            removeHamburgerButtons();
        }}
    }}, true);
    
    // 헤더 영역에 마우스가 들어가면 즉시 제거
    const header = document.querySelector('[data-testid="stHeader"]') || document.querySelector('header');
    if (header) {{
        header.addEventListener('mouseenter', function() {{
            removeHamburgerButtons();
        }}, true);
    }}
    
    // DOM 변경 감지
    const observer = new MutationObserver(function() {{
        syncSidebarState();
    }});
    
    const sidebar = document.querySelector('[data-testid="stSidebar"]');
    if (sidebar) {{
        observer.observe(sidebar, {{
            attributes: true,
            childList: true,
            subtree: false,
            attributeFilter: ['data-sidebar-collapsed', 'class', 'style']
        }});
    }}
    
    // window load 이벤트
    window.addEventListener('load', function() {{
        removeHamburgerButtons();
        syncSidebarState();
        setTimeout(function() {{ removeHamburgerButtons(); syncSidebarState(); }}, 100);
        setTimeout(function() {{ removeHamburgerButtons(); syncSidebarState(); }}, 300);
        setTimeout(function() {{ removeHamburgerButtons(); syncSidebarState(); }}, 500);
        setTimeout(function() {{ removeHamburgerButtons(); syncSidebarState(); }}, 1000);
    }}, {{ passive: true }});
    
    // Streamlit의 사이드바 관련 모든 이벤트 차단 (더 강력하게)
    document.addEventListener('click', function(e) {{
        const target = e.target;
        if (target && (
            target.closest('[data-testid="stHeader"]') ||
            target.getAttribute('aria-label')?.includes('sidebar') ||
            target.closest('button[aria-label*="sidebar"]') ||
            target.closest('button[aria-label*="메뉴"]') ||
            target.closest('button[aria-label*="Menu"]')
        )) {{
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            removeHamburgerButtons();
            
            // 사이드바 복구
            const sidebar = document.querySelector('[data-testid="stSidebar"]');
            if (sidebar) {{
                sidebar.style.setProperty('display', 'block', 'important');
                sidebar.style.setProperty('visibility', 'visible', 'important');
                sidebar.setAttribute('aria-expanded', 'true');
            }}
            
            return false;
        }}
    }}, true);
    
    // mousedown 이벤트도 차단
    document.addEventListener('mousedown', function(e) {{
        const target = e.target;
        if (target && (
            target.closest('[data-testid="stHeader"]') ||
            target.getAttribute('aria-label')?.includes('sidebar') ||
            target.closest('button[aria-label*="sidebar"]')
        )) {{
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            removeHamburgerButtons();
            return false;
        }}
    }}, true);
}})();
</script>
""", unsafe_allow_html=True)

if st.session_state.get("theme", "light") == "dark":
    st.markdown("<style>.main { background-color: #020617 !important; color: #e5e7eb !important; }</style>", unsafe_allow_html=True)

# Sidebar Navigation
# 사이드바 상태 관리
if "sidebar_collapsed" not in st.session_state:
    st.session_state.sidebar_collapsed = False

# 메뉴 구조 정의
menu = {
    "🏠 홈": [("홈", "홈")],
    "🧠 설계": {
        "main": [("가게 전략 센터", "가게 전략 센터")],
        "sub": [
            ("메뉴 포트폴리오 설계", "메뉴 등록"),
            ("메뉴 수익 설계", "메뉴 수익 구조 설계실"),
            ("재료 구조 설계", "재료 등록"),
            ("수익 구조 설계", "수익 구조 설계실"),
            ("레시피 설계", "레시피 등록")
        ]
    },
    "📊 분석": {
        "main": [("분석 허브", "분석 허브")],
        "sub": [
            ("매출 분석", "매출 관리"),
            ("판매·메뉴 분석", "판매 관리"),
            ("원가 분석", "비용 분석"),
            ("체크 결과 요약", "검진 결과 요약"),
            ("체크 히스토리", "검진 히스토리"),
            ("매출 하락 원인 찾기", "매출 하락 원인 찾기")
        ]
    },
    "✍ 입력": {
        "main": [("데이터 입력 센터", "입력 허브")],
        "sub": [
            ("오늘 마감 입력", "일일 입력(통합)"),
            ("매출/방문자 입력", "매출 등록"),
            ("판매량 입력", "판매량 등록"),
            ("월간 정산 입력", "실제정산"),
            ("비용 목표 입력", "목표 비용구조"),
            ("매출 목표 입력", "목표 매출구조"),
            ("QSC 입력", "건강검진 실시")
        ]
    },
    "🛠 운영": [
        ("직원 연락망", "직원 연락망"),
        ("협력사 연락망", "협력사 연락망"),
        ("게시판", "게시판")
    ]
}

def render_expanded_sidebar(menu):
    """펼친 상태 사이드바 렌더링"""
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
        st.markdown(f"**{cat}**")
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
    
    # 로그아웃, 캐시 클리어
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 로그아웃"): 
        logout()
        st.rerun()
    if st.button("🔄 캐시 클리어"): 
        load_csv.clear()
        st.rerun()

def render_collapsed_sidebar(menu):
    """접힌 상태 사이드바 렌더링 (아이콘만 표시)"""
    category_icons = {
        "🏠 홈": "🏠",
        "🧠 설계": "🧠",
        "📊 분석": "📊",
        "✍ 입력": "✍",
        "🛠 운영": "🛠"
    }
    
    for cat, data in menu.items():
        icon = category_icons.get(cat, "📋")
        if st.button(icon, key=f"collapsed_{cat}", use_container_width=True, help=cat):
            st.session_state.sidebar_collapsed = False
            if isinstance(data, list):
                st.session_state.current_page = data[0][1]
            else:
                st.session_state.current_page = data["main"][0][1]
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪", key="collapsed_logout", use_container_width=True, help="로그아웃"):
        logout()
        st.rerun()
    if st.button("🔄", key="collapsed_clear", use_container_width=True, help="캐시 클리어"):
        load_csv.clear()
        st.rerun()

def render_custom_sidebar(menu):
    """커스텀 사이드바 렌더링 함수 (Streamlit 기본 사이드바 대신)"""
    # 사이드바 상태 초기화
    if "sidebar_collapsed" not in st.session_state:
        st.session_state.sidebar_collapsed = False
    
    # current_page 초기화
    if "current_page" not in st.session_state:
        st.session_state.current_page = "홈"
    
    collapsed = st.session_state.sidebar_collapsed
    sidebar_width = "4rem" if collapsed else "15rem"
    current_page = st.session_state.current_page
    
    # 커스텀 사이드바 CSS (전역에 한 번만 추가)
    if "custom_sidebar_css_injected" not in st.session_state:
        st.session_state.custom_sidebar_css_injected = True
        st.markdown("""
        <style>
        /* Streamlit 기본 사이드바 완전히 숨기기 */
        [data-testid="stSidebar"],
        section[data-testid="stSidebar"],
        div[data-testid="stSidebar"] {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            min-width: 0 !important;
            max-width: 0 !important;
        }
        
        /* 커스텀 사이드바 컨테이너 */
        #custom-sidebar-container {
            position: fixed !important;
            left: 0 !important;
            top: 0 !important;
            height: 100vh !important;
            width: 15rem !important;
            max-width: 15rem !important;
            min-width: 15rem !important;
            background: var(--surface-bg, #1E293B) !important;
            border-right: 1px solid rgba(232, 238, 247, 0.12) !important;
            z-index: 999 !important;
            transition: width 0.3s ease !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
            padding: 1rem 0.5rem !important;
            box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1) !important;
        }
        
        #custom-sidebar-container.collapsed {
            width: 4rem !important;
            max-width: 4rem !important;
            min-width: 4rem !important;
        }
        
        #custom-sidebar-container.expanded {
            width: 15rem !important;
            max-width: 15rem !important;
            min-width: 15rem !important;
        }
        
        /* 커스텀 사이드바 내부 버튼 스타일 */
        #custom-sidebar-container .stButton > button {
            width: 100% !important;
            margin-bottom: 0.25rem !important;
            text-align: left !important;
            justify-content: flex-start !important;
        }
        
        #custom-sidebar-container.collapsed .stButton > button {
            justify-content: center !important;
            padding: 0.75rem 0.5rem !important;
        }
        
        /* 카테고리 제목 */
        .custom-sidebar-category {
            margin-top: 1rem;
            margin-bottom: 0.5rem;
            font-weight: 600;
            font-size: 0.75rem;
            color: var(--text-muted, #94A3B8);
            text-transform: uppercase;
            padding: 0 0.5rem;
        }
        
        #custom-sidebar-container.collapsed .custom-sidebar-category {
            display: none;
        }
        
        /* 메인 콘텐츠 영역 margin-left 조정 - JavaScript에서 동적으로 설정 */
        .main .block-container,
        [data-testid="stAppViewContainer"] > div:not([data-testid="stSidebar"]),
        [data-testid="stAppViewContainer"] {
            transition: margin-left 0.3s ease !important;
        }
        
        /* Streamlit 기본 레이아웃 강제 조정 */
        [data-testid="stAppViewContainer"] {
            display: flex !important;
            flex-direction: row !important;
        }
        
        /* 메인 콘텐츠가 사이드바 옆에 오도록 */
        .main {
            margin-left: 15rem !important;
            transition: margin-left 0.3s ease !important;
            width: calc(100% - 15rem) !important;
        }
        
        /* 접힌 상태일 때 */
        body:has(#custom-sidebar-container.collapsed) .main,
        html:has(#custom-sidebar-container.collapsed) .main {
            margin-left: 4rem !important;
            width: calc(100% - 4rem) !important;
        }
        </style>
        """, unsafe_allow_html=True)
    
    # 사이드바 컨테이너 시작
    sidebar_class = "collapsed" if collapsed else "expanded"
    st.markdown(f'<div id="custom-sidebar-container" class="{sidebar_class}">', unsafe_allow_html=True)
    
    # 토글 버튼 (Streamlit 버튼 사용)
    toggle_label = "▶" if collapsed else "◀ 접기"
    if st.button(toggle_label, key="custom_sidebar_toggle", use_container_width=True):
        st.session_state.sidebar_collapsed = not st.session_state.sidebar_collapsed
        st.rerun()
    
    # 사이드바 메뉴 렌더링
    for cat, data in menu.items():
        # 카테고리 제목
        if not collapsed:
            st.markdown(f'<div class="custom-sidebar-category">{cat}</div>', unsafe_allow_html=True)
        
        # 메뉴 항목
        if isinstance(data, list):
            # 단순 리스트
            for label, key in data:
                icon = "🏠" if "홈" in label else "🛠"
                is_active = "primary" if current_page == key else "secondary"
                if collapsed:
                    if st.button(icon, key=f"nav_{key}", help=label, type=is_active):
                        st.session_state.current_page = key
                        st.rerun()
                else:
                    if st.button(f"{icon} {label}", key=f"nav_{key}", use_container_width=True, type=is_active):
                        st.session_state.current_page = key
                        st.rerun()
        else:
            # 딕셔너리 (main/sub)
            # Main 항목
            for label, key in data["main"]:
                icon = "🧠" if "설계" in cat else "📊" if "분석" in cat else "✍"
                is_active = "primary" if current_page == key else "secondary"
                if collapsed:
                    if st.button(icon, key=f"nav_{key}", help=label, type=is_active):
                        st.session_state.current_page = key
                        st.rerun()
                else:
                    if st.button(f"{icon} {label}", key=f"nav_{key}", use_container_width=True, type=is_active):
                        st.session_state.current_page = key
                        st.rerun()
            
            # Sub 항목 (접힌 상태에서는 숨김)
            if not collapsed:
                for label, key in data["sub"]:
                    is_active = "primary" if current_page == key else "secondary"
                    if st.button(label, key=f"nav_{key}", use_container_width=True, type=is_active):
                        st.session_state.current_page = key
                        st.rerun()
    
    # 매장 선택
    if not collapsed:
        user_stores = get_user_stores()
        if len(user_stores) > 1:
            st.markdown('<div class="custom-sidebar-category">매장 선택</div>', unsafe_allow_html=True)
            store_options = {f"{s['name']} ({s['role']})": s['id'] for s in user_stores}
            curr_name = get_current_store_name()
            selected_display = f"{curr_name} ({next((s['role'] for s in user_stores if s['name'] == curr_name), '')})"
            selected = st.selectbox("", options=list(store_options.keys()), 
                                  index=list(store_options.keys()).index(selected_display) if selected_display in store_options else 0,
                                  key="custom_store_select", label_visibility="collapsed")
            if selected != selected_display:
                switch_store(store_options[selected])
                st.rerun()
    
    # 로그아웃, 캐시 클리어
    st.markdown('<div style="margin-top: auto; padding-top: 1rem; border-top: 1px solid rgba(232, 238, 247, 0.12);">', unsafe_allow_html=True)
    if not collapsed:
        st.markdown('<div class="custom-sidebar-category">시스템</div>', unsafe_allow_html=True)
    
    if st.button("🚪 로그아웃", key="custom_logout", use_container_width=True):
        logout()
        st.rerun()
    if st.button("🔄 캐시 클리어", key="custom_cache_clear", use_container_width=True):
        load_csv.clear()
        st.rerun()
    
    # 사이드바 컨테이너 종료
    st.markdown('</div>', unsafe_allow_html=True)
    
    # JavaScript로 사이드바 폭 및 메인 콘텐츠 margin-left 동기화 (강화 버전)
    st.markdown(f"""
    <script>
    (function() {{
        const targetWidth = '{sidebar_width}';
        const targetWidthPx = {('64' if collapsed else '240')};
        
        // 사이드바 폭 강제 설정
        function setSidebarWidth() {{
            const sidebar = document.getElementById('custom-sidebar-container');
            if (sidebar) {{
                sidebar.style.setProperty('width', targetWidth, 'important');
                sidebar.style.setProperty('max-width', targetWidth, 'important');
                sidebar.style.setProperty('min-width', targetWidth, 'important');
            }}
        }}
        
        // 메인 콘텐츠 영역 margin-left 조정 (모든 가능한 요소)
        function adjustMainContent() {{
            // .main 요소 직접 조정
            const mainElements = document.querySelectorAll('.main');
            mainElements.forEach(function(el) {{
                el.style.setProperty('margin-left', targetWidth, 'important');
                el.style.setProperty('width', 'calc(100% - ' + targetWidth + ')', 'important');
                el.style.setProperty('max-width', 'calc(100% - ' + targetWidth + ')', 'important');
            }});
            
            // .block-container 조정
            const blockContainers = document.querySelectorAll('.main .block-container');
            blockContainers.forEach(function(el) {{
                el.style.setProperty('margin-left', '0', 'important');
                el.style.setProperty('max-width', '100%', 'important');
            }});
            
            // stAppViewContainer 조정
            const appContainer = document.querySelector('[data-testid="stAppViewContainer"]');
            if (appContainer) {{
                appContainer.style.setProperty('margin-left', targetWidth, 'important');
                appContainer.style.setProperty('width', 'calc(100% - ' + targetWidth + ')', 'important');
                appContainer.style.setProperty('max-width', 'calc(100% - ' + targetWidth + ')', 'important');
            }}
            
            // stAppViewContainer의 직접 자식 요소들 조정
            const appContainerChildren = document.querySelectorAll('[data-testid="stAppViewContainer"] > div');
            appContainerChildren.forEach(function(el) {{
                if (!el.querySelector('#custom-sidebar-container')) {{
                    el.style.setProperty('margin-left', '0', 'important');
                    el.style.setProperty('width', '100%', 'important');
                }}
            }});
        }}
        
        // 모든 조정 함수 실행
        function applyAllAdjustments() {{
            setSidebarWidth();
            adjustMainContent();
        }}
        
        // 즉시 실행 (여러 번)
        applyAllAdjustments();
        setTimeout(applyAllAdjustments, 10);
        setTimeout(applyAllAdjustments, 50);
        setTimeout(applyAllAdjustments, 100);
        setTimeout(applyAllAdjustments, 300);
        
        // DOM 변경 감지
        const observer = new MutationObserver(applyAllAdjustments);
        if (document.body) {{
            observer.observe(document.body, {{ 
                childList: true, 
                subtree: true,
                attributes: true,
                attributeFilter: ['style', 'class']
            }});
        }}
        
        // 주기적 확인 (매우 자주 - 안전장치)
        setInterval(applyAllAdjustments, 50);
        
        // window load 이벤트
        window.addEventListener('load', function() {{
            setTimeout(applyAllAdjustments, 100);
            setTimeout(applyAllAdjustments, 500);
        }});
    }})();
    </script>
    """, unsafe_allow_html=True)

# 커스텀 사이드바 렌더링 (Streamlit 기본 사이드바 대신)
render_custom_sidebar(menu)

# Page Routing
# current_page는 render_custom_sidebar에서 초기화됨
if "current_page" not in st.session_state:
    st.session_state.current_page = "홈"
page = st.session_state.current_page

if st.session_state.get("_show_supabase_diagnosis", False):
    _diagnose_supabase_connection()

if page == "홈":
    from ui_pages.home import render_home
    render_home()
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
