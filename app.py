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
    
    /* 헤더의 모든 버튼 표시 */
    header[data-testid="stHeader"] button,
    [data-testid="stHeader"] button,
    button[kind="header"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    
    /* 사이드바 토글 버튼 강제 표시 - 모든 가능한 선택자 */
    [data-testid="stHeader"] button,
    header button,
    button[kind="header"],
    button[aria-label*="sidebar"],
    button[aria-label*="메뉴"],
    button[aria-label*="Menu"],
    button[aria-label*="Close"],
    button[aria-label*="열기"],
    button[aria-label*="Open"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        z-index: 1000 !important;
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
    
    /* 사이드바 항상 표시 보장 및 접기 방지 - 모든 가능한 선택자 사용 */
    section[data-testid="stSidebar"],
    [data-testid="stSidebar"],
    div[data-testid="stSidebar"],
    .css-1d391kg,
    .css-1lcbmhc,
    [class*="stSidebar"] {
        display: block !important;
        visibility: visible !important;
        width: 21rem !important;
        min-width: 21rem !important;
        max-width: 21rem !important;
        transform: translateX(0) !important;
        position: relative !important;
        opacity: 1 !important;
        z-index: 999 !important;
    }
    
    /* 사이드바가 접힌 상태로 보이지 않도록 - 모든 상태에서 강제 표시 */
    [data-testid="stSidebar"][aria-expanded="false"],
    [data-testid="stSidebar"][aria-expanded="true"],
    section[data-testid="stSidebar"][aria-expanded="false"],
    section[data-testid="stSidebar"][aria-expanded="true"] {
        display: block !important;
        visibility: visible !important;
        transform: translateX(0) !important;
        width: 21rem !important;
        min-width: 21rem !important;
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

# 사이드바 강제 열기 JavaScript - 더 강력한 버전 (에러 핸들링 강화)
st.markdown("""
<script>
(function() {
    'use strict';
    
    try {
        let observer = null;
        let intervalId = null;
        
        function forceSidebarOpen() {
            try {
                // 모든 가능한 사이드바 선택자로 찾기
                const selectors = [
                    '[data-testid="stSidebar"]',
                    'section[data-testid="stSidebar"]',
                    'div[data-testid="stSidebar"]',
                    '.css-1d391kg',
                    '.css-1lcbmhc'
                ];
                
                let sidebar = null;
                for (const selector of selectors) {
                    try {
                        sidebar = document.querySelector(selector);
                        if (sidebar) break;
                    } catch(e) {
                        // 선택자 실패는 무시
                    }
                }
                
                if (sidebar) {
                    // 사이드바를 항상 열린 상태로 강제 설정
                    sidebar.setAttribute('aria-expanded', 'true');
                    sidebar.style.cssText = `
                        display: block !important;
                        visibility: visible !important;
                        transform: translateX(0) !important;
                        width: 21rem !important;
                        min-width: 21rem !important;
                        max-width: 21rem !important;
                        position: relative !important;
                        opacity: 1 !important;
                        z-index: 999 !important;
                    `;
                    
                    // 부모 요소도 확인
                    try {
                        let parent = sidebar.parentElement;
                        while (parent && parent !== document.body) {
                            if (parent.style) {
                                parent.style.overflow = 'visible';
                            }
                            parent = parent.parentElement;
                        }
                    } catch(e) {
                        // 부모 요소 처리 실패 무시
                    }
                }
                
                // 햄버거 메뉴 버튼 찾기 및 표시 - 모든 가능한 방법
                try {
                    const headerButtons = document.querySelectorAll('button[kind="header"], [data-testid="stHeader"] button, header button');
                    headerButtons.forEach(btn => {
                        try {
                            const label = btn.getAttribute('aria-label') || '';
                            if (label.includes('sidebar') || label.includes('메뉴') || label.includes('Menu') || 
                                label.includes('Close') || label.includes('열기') || label.includes('Open')) {
                                btn.style.cssText = 'display: block !important; visibility: visible !important; opacity: 1 !important;';
                            }
                        } catch(e) {
                            // 개별 버튼 처리 실패 무시
                        }
                    });
                } catch(e) {
                    // 버튼 찾기 실패 무시
                }
                
                // Streamlit의 사이드바 토글 버튼 클릭 이벤트 오버라이드 (한 번만)
                try {
                    const toggleButtons = document.querySelectorAll('[data-testid="stHeader"] button, button[kind="header"]');
                    toggleButtons.forEach(btn => {
                        // 이미 리스너가 추가되었는지 확인
                        if (!btn.hasAttribute('data-sidebar-listener')) {
                            btn.setAttribute('data-sidebar-listener', 'true');
                            btn.addEventListener('click', function(e) {
                                try {
                                    setTimeout(function() {
                                        try { forceSidebarOpen(); } catch(e) {}
                                    }, 100);
                                } catch(e) {
                                    // 클릭 핸들러 에러 무시
                                }
                            }, { passive: true });
                        }
                    });
                } catch(e) {
                    // 토글 버튼 처리 실패 무시
                }
            } catch(e) {
                console.warn('사이드바 강제 열기 실패:', e);
            }
        }
        
        // 즉시 실행
        forceSidebarOpen();
        
        // 페이지 로드 시 실행
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                try { forceSidebarOpen(); } catch(e) {}
            });
        } else {
            forceSidebarOpen();
        }
        
        // window.load 이벤트
        window.addEventListener('load', function() {
            try { forceSidebarOpen(); } catch(e) {}
        }, { passive: true });
        
        // 주기적으로 확인하여 사이드바가 접히면 다시 열기
        try {
            intervalId = setInterval(function() {
                try { forceSidebarOpen(); } catch(e) {}
            }, 200);
        } catch(e) {
            console.warn('setInterval 설정 실패:', e);
        }
        
        // DOM 변경 감지하여 사이드바 상태 유지
        try {
            observer = new MutationObserver(function(mutations) {
                try {
                    let shouldForce = false;
                    mutations.forEach(function(mutation) {
                        if (mutation.type === 'attributes' && 
                            (mutation.attributeName === 'aria-expanded' || 
                             mutation.attributeName === 'style' || 
                             mutation.attributeName === 'class')) {
                            shouldForce = true;
                        }
                        if (mutation.type === 'childList') {
                            shouldForce = true;
                        }
                    });
                    if (shouldForce) {
                        setTimeout(function() {
                            try { forceSidebarOpen(); } catch(e) {}
                        }, 50);
                    }
                } catch(e) {
                    // MutationObserver 콜백 에러 무시
                }
            });
            
            if (document.body) {
                observer.observe(document.body, {
                    childList: true,
                    subtree: true,
                    attributes: true,
                    attributeFilter: ['style', 'aria-expanded', 'class', 'data-testid']
                });
            }
        } catch(e) {
            console.warn('MutationObserver 설정 실패:', e);
        }
        
        // 페이지 언로드 시 정리
        window.addEventListener('beforeunload', function() {
            try {
                if (observer) {
                    observer.disconnect();
                }
                if (intervalId) {
                    clearInterval(intervalId);
                }
            } catch(e) {
                // 정리 실패 무시
            }
        }, { passive: true });
        
    } catch(e) {
        console.warn('사이드바 스크립트 초기화 실패:', e);
    }
})();
</script>
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
    
    if "current_page" not in st.session_state: st.session_state.current_page = "홈"
    
    for cat, data in menu.items():
        st.markdown(f"**{cat}**")
        if isinstance(data, list):
            for label, key in data:
                if st.button(label, key=f"btn_{key}", use_container_width=True, type="primary" if st.session_state.current_page == key else "secondary"):
                    st.session_state.current_page = key
                    st.rerun()
        else:
            # Main items
            for label, key in data["main"]:
                if st.button(label, key=f"btn_{key}", use_container_width=True, type="primary" if st.session_state.current_page == key else "secondary"):
                    st.session_state.current_page = key
                    st.rerun()
            # Sub items in expander
            with st.expander("상세 선택", expanded=False):
                for label, key in data["sub"]:
                    if st.button(label, key=f"btn_sub_{key}", use_container_width=True, type="primary" if st.session_state.current_page == key else "secondary"):
                        st.session_state.current_page = key
                        st.rerun()

    if st.button("🚪 로그아웃"): logout(); st.rerun()
    if st.button("🔄 캐시 클리어"): load_csv.clear(); st.rerun()

# Page Routing
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
