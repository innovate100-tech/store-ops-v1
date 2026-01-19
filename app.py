"""
매장 운영 시스템 v1 - 메인 앱 (Supabase 기반)
"""
import streamlit as st
from datetime import datetime
import pandas as pd

# 페이지 설정은 최상단에 위치 (다른 st.* 호출 전에)
st.set_page_config(
    page_title="매장 운영 시스템 v1",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded",  # 사이드바 항상 열림
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# 테마 상태 초기화 (기본: 화이트 모드)
if "theme" not in st.session_state:
    st.session_state.theme = "light"

# 로그인 체크
from src.auth import check_login, show_login_page, get_current_store_name, logout, apply_dev_mode_session

# DEV MODE 체크 (로컬 개발용)
apply_dev_mode_session()

# 로그인이 안 되어 있으면 로그인 화면 표시
if not check_login():
    show_login_page()
    st.stop()

# Supabase 기반 storage 사용
from src.storage_supabase import (
    load_csv,
    save_sales,
    save_visitor,
    save_menu,
    update_menu,
    delete_menu,
    save_ingredient,
    update_ingredient,
    delete_ingredient,
    save_recipe,
    delete_recipe,
    save_daily_sales_item,
    save_inventory,
    save_targets,
    save_abc_history,
    delete_sales,
    delete_visitor,
    create_backup,
    save_daily_close,
    save_expense_item,
    update_expense_item,
    delete_expense_item,
    load_expense_structure,
    load_expense_structure_range,
    copy_expense_structure_from_previous_month
)
from src.analytics import (
    calculate_correlation,
    merge_sales_visitors,
    calculate_menu_cost,
    calculate_ingredient_usage,
    calculate_order_recommendation,
    abc_analysis,
    target_gap_analysis
)
from src.ui import (
    render_sales_input,
    render_sales_batch_input,
    render_visitor_input,
    render_visitor_batch_input,
    render_menu_input,
    render_menu_batch_input,
    render_sales_chart,
    render_correlation_info,
    render_ingredient_input,
    render_recipe_input,
    render_cost_analysis,
    render_daily_sales_input,
    render_inventory_input,
    render_report_input,
    render_target_input,
    render_target_dashboard,
    render_abc_analysis,
    render_manager_closing_input
)
from src.reporting import generate_weekly_report
from src.ui_helpers import render_page_header, render_section_header, render_section_divider

# 커스텀 CSS 적용 (반응형 최적화 포함)
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Noto Sans KR', sans-serif !important;
    }
    
    /* Streamlit Material 아이콘(특히 keyboard_double_arrow_* 아이콘)을
       텍스트가 아닌 '보라색 동그란 아이콘 버튼'처럼 보이게 만들기 */
    [data-testid="stIconMaterial"] {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border-radius: 999px;
        background-color: #667eea;
        /* 원래 영어 텍스트는 완전히 숨기기 (모바일에서도 강제로 적용) */
        font-size: 0 !important;
        line-height: 0 !important;
        color: transparent !important;
    }
    
    [data-testid="stIconMaterial"]::before {
        /* 사이드바 접기/펼치기 아이콘을 웃는 스마일 이모티콘으로 표시 */
        content: '😊';
        font-size: 18px;
        line-height: 1;
        color: #ffffff;
        display: inline-block;
    }
    
    /* ========== 반응형 기본 설정 ========== */
    :root {
        --mobile-breakpoint: 768px;
        --tablet-breakpoint: 1024px;
    }
    
    /* ========== 메인 헤더 (반응형) ========== */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    @media (max-width: 768px) {
        .main-header {
            padding: 1.5rem 1rem;
            margin-bottom: 1rem;
            border-radius: 8px;
        }
        
        .main-header h1 {
            font-size: 1.5rem !important;
        }
        
        .main-header p {
            font-size: 0.9rem !important;
        }
    }
    
    .main-header h1 {
        color: white !important;
        border: none !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* ========== 정보 박스 (반응형) ========== */
    .info-box {
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
        border-left: 4px solid #667eea;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    @media (max-width: 768px) {
        .info-box {
            padding: 0.75rem 1rem;
            margin: 0.75rem 0;
            font-size: 0.9rem;
        }
    }
    
    /* ========== 메트릭 카드 (반응형) ========== */
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        border: 1px solid #e0e0e0;
    }
    
    @media (max-width: 768px) {
        .metric-card {
            padding: 1rem;
            border-radius: 8px;
        }
        
        .metric-card > div:first-child {
            font-size: 0.85rem !important;
        }
        
        .metric-card > div:last-child {
            font-size: 1.3rem !important;
        }
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    @media (max-width: 768px) {
        .metric-card:hover {
            transform: none; /* 모바일에서는 호버 효과 제거 */
        }
    }
    
    /* ========== 섹션 구분선 ========== */
    .section-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #667eea, transparent);
        margin: 2rem 0;
        border: none;
    }
    
    @media (max-width: 768px) {
        .section-divider {
            margin: 1rem 0;
        }
    }
    
    /* ========== 입력 폼 컨테이너 (반응형) ========== */
    .form-container {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border: 1px solid #e0e0e0;
    }
    
    @media (max-width: 768px) {
        .form-container {
            padding: 1rem;
            border-radius: 8px;
            margin: 0.75rem 0;
        }
    }
    
    /* ========== 데이터프레임 스타일 (반응형) ========== */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }
    
    @media (max-width: 768px) {
        .stDataFrame {
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }
        
        /* 테이블 가로 스크롤 최적화 */
        .stDataFrame table {
            min-width: 100%;
            font-size: 0.85rem;
        }
        
        .stDataFrame th,
        .stDataFrame td {
            padding: 0.5rem 0.75rem !important;
            white-space: nowrap;
        }
    }
    
    /* ========== 버튼 그룹 (반응형) ========== */
    .button-group {
        display: flex;
        gap: 0.5rem;
        margin: 1rem 0;
    }
    
    @media (max-width: 768px) {
        .button-group {
            flex-direction: column;
            gap: 0.75rem;
        }
        
        .button-group button {
            width: 100% !important;
        }
    }
    
    /* ========== Streamlit 버튼 최적화 (모바일) ========== */
    @media (max-width: 768px) {
        /* 기본 버튼: 기존보다 한 단계 더 작게 */
        button[data-testid="baseButton-secondary"],
        button[data-testid="baseButton-primary"] {
            min-height: 34px !important;
            padding: 0.35rem 0.6rem !important;
            font-size: 0.85rem !important;
        }
        
        /* 사이드바 버튼: 최대한 컴팩트하게 */
        [data-testid="stSidebar"] button {
            min-height: 30px !important;
            padding: 0.25rem 0.5rem !important;
            font-size: 0.8rem !important;
            margin-bottom: 0.25rem !important;
        }
        
        /* 모바일에서 비용구조 페이지의 기존 항목 수정/삭제/저장 버튼들은 숨겨서 스크롤을 줄임 */
        .expense-existing-items ~ div button {
            display: none !important;
        }
    }
    
    /* ========== 카드 스타일 섹션 (반응형) ========== */
    .card-section {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    @media (max-width: 768px) {
        .card-section {
            padding: 1rem;
            border-radius: 8px;
            margin: 0.75rem 0;
        }
    }
    
    /* ========== 사이드바 최적화 (모바일) ========== */
    @media (max-width: 768px) {
        /* 폭을 화면의 50%로 고정 (비율 연동) */
        [data-testid="stSidebar"] {
            width: 50vw !important;
            max-width: 50vw !important;
            min-width: auto !important;
        }
        
        [data-testid="stSidebar"] .stButton > button {
            width: 100% !important;
            /* 버튼 간 간격을 약 5px 수준으로 (기존의 1/3) */
            margin-bottom: 5px !important;
        }
        
        /* 사이드바 카테고리 헤더: 아주 타이트하게 */
        [data-testid="stSidebar"] .category-header {
            font-size: 0.65rem !important;
            padding: 0.25rem 0.4rem !important;
            margin-bottom: 0.05rem !important;
        }
    }
    
    /* ========== 컬럼 레이아웃 기본값 유지 ==========
       비용구조 타일은 Streamlit 기본 레이아웃(한 줄 1개, 넓게)으로 두고
       필요할 때 개별 섹션에서만 별도 스타일을 적용합니다. */
    
    /* ========== 입력 필드 최적화 (모바일) ========== */
    @media (max-width: 768px) {
        /* 텍스트 입력 필드 */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stDateInput > div > div > input,
        .stSelectbox > div > div > select {
            font-size: 16px !important; /* iOS 줌 방지 */
            padding: 0.75rem !important;
            min-height: 44px !important;
        }
        
        /* 라디오 버튼 */
        .stRadio > label {
            font-size: 0.95rem !important;
            padding: 0.5rem 0 !important;
        }
        
        /* 체크박스 */
        .stCheckbox > label {
            font-size: 0.95rem !important;
            padding: 0.5rem 0 !important;
        }
    }
    
    /* ========== 테이블/데이터프레임 가로 스크롤 ========== */
    @media (max-width: 768px) {
        /* 데이터프레임 래퍼 */
        .element-container:has(.stDataFrame) {
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }
        
        /* 스크롤 인디케이터 */
        .element-container:has(.stDataFrame)::after {
            content: '← 스와이프하여 더 보기 →';
            display: block;
            text-align: center;
            font-size: 0.75rem;
            color: #666;
            padding: 0.5rem;
            opacity: 0.7;
        }
    }
    
    /* ========== 사이드바 카테고리별 메뉴 구분 스타일 ========== */
    [data-testid="stSidebar"] .stRadio {
        margin-top: 0 !important;
        margin-bottom: 0.5rem !important;
    }
    
    @media (max-width: 768px) {
        [data-testid="stSidebar"] .stRadio {
            margin-bottom: 0.75rem !important;
        }
    }
    
    /* 라디오 버튼 항목 그룹핑을 위한 스타일 */
    [data-testid="stSidebar"] .stRadio > label {
        position: relative;
    }
    
    /* 카테고리 구분선 효과 */
    .category-separator {
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        margin: 0.5rem 0;
    }
    
    /* ========== 메인 컨텐츠 영역 최적화 ========== */
    @media (max-width: 768px) {
        /* 메인 영역 패딩 조정 */
        .main .block-container {
            padding: 1rem 0.5rem !important;
        }
        
        /* 섹션 헤더 */
        h1, h2, h3 {
            font-size: 1.5rem !important;
            margin-top: 1rem !important;
            margin-bottom: 0.75rem !important;
        }
        
        h2 {
            font-size: 1.25rem !important;
        }
        
        h3 {
            font-size: 1.1rem !important;
        }
        
        /* 일반 텍스트 */
        p, div, span {
            font-size: 0.95rem !important;
            line-height: 1.6 !important;
        }
    }
    
    /* ========== 차트 최적화 (모바일) ========== */
    @media (max-width: 768px) {
        .stPlotlyChart,
        .stPyplot {
            width: 100% !important;
            height: auto !important;
        }
    }
    
    /* ========== 메트릭 표시 최적화 ========== */
    @media (max-width: 768px) {
        [data-testid="stMetricValue"] {
            font-size: 1.5rem !important;
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 0.85rem !important;
        }
    }
    
    /* ========== 다운로드 버튼 최적화 ========== */
    @media (max-width: 768px) {
        .stDownloadButton > button {
            width: 100% !important;
            min-height: 44px !important;
            font-size: 1rem !important;
        }
    }
    
    /* ========== 폼 제출 버튼 최적화 ========== */
    @media (max-width: 768px) {
        .stForm > div:last-child button {
            width: 100% !important;
            min-height: 44px !important;
            font-size: 1rem !important;
            margin-top: 1rem !important;
        }
    }
    
    /* ========== 스크롤바 스타일링 (모바일) ========== */
    @media (max-width: 768px) {
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
    }
    
    /* 모든 title 툴팁 완전히 차단 - 가장 강력한 방법 */
    * {
        /* 브라우저 기본 툴팁 완전히 비활성화 */
    }
    
    /* keyboard 관련 모든 요소의 툴팁 차단 */
    [title*="keyboard" i],
    [title*="arrow" i],
    [title*="double" i],
    [aria-label*="keyboard" i],
    [aria-label*="arrow" i],
    [aria-label*="double" i] {
        /* title 속성 자체를 무효화 */
        pointer-events: auto !important;
    }
    
    /* 사이드바 헤더 영역: 토글 버튼을 오른쪽에 배치 */
    [data-testid="stSidebarHeader"] {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        padding: 0.25rem 0.5rem;
    }
    
    /* 브라우저 기본 툴팁 스타일 완전히 제거 */
    *[title]:hover,
    *[title]:focus,
    *[title]:active {
        /* 툴팁 표시 안 함 */
    }
    
</style>
<script>
    // 완전히 새로운 접근: 브라우저의 툴팁 시스템 자체를 차단
    (function() {
        'use strict';
        
        // keyboard 관련 키워드 목록 (대소문자 무시)
        const keyboardKeywords = ['keyboard', 'arrow', 'double', 'left', 'right'];
        
        // 키워드 포함 여부 확인 (대소문자 무시)
        function containsKeyboardKeyword(str) {
            if (!str || typeof str !== 'string') return false;
            const lowerStr = str.toLowerCase();
            return keyboardKeywords.some(keyword => lowerStr.includes(keyword));
        }
        
        // 1. Element.prototype.setAttribute 완전히 오버라이드
        const originalSetAttribute = Element.prototype.setAttribute;
        Element.prototype.setAttribute = function(name, value) {
            if (name === 'title' && typeof value === 'string' && containsKeyboardKeyword(value)) {
                // keyboard 관련 title은 아예 설정하지 않음
                return;
            }
            if (name === 'aria-label' && typeof value === 'string' && containsKeyboardKeyword(value)) {
                // keyboard 관련 aria-label도 차단
                return;
            }
            return originalSetAttribute.call(this, name, value);
        };
        
        // 2. Element.prototype.setAttributeNS도 오버라이드
        const originalSetAttributeNS = Element.prototype.setAttributeNS;
        Element.prototype.setAttributeNS = function(namespace, name, value) {
            if (name === 'title' && typeof value === 'string' && containsKeyboardKeyword(value)) {
                return;
            }
            if (name === 'aria-label' && typeof value === 'string' && containsKeyboardKeyword(value)) {
                return;
            }
            return originalSetAttributeNS.call(this, namespace, name, value);
        };
        
        // 3. getAttribute 오버라이드 - 빈 문자열 반환
        const originalGetAttribute = Element.prototype.getAttribute;
        Element.prototype.getAttribute = function(name) {
            if (name === 'title') {
                const value = originalGetAttribute.call(this, name);
                if (value && containsKeyboardKeyword(value)) {
                    return ''; // 빈 문자열 반환하여 툴팁 표시 안 함
                }
            }
            if (name === 'aria-label') {
                const value = originalGetAttribute.call(this, name);
                if (value && containsKeyboardKeyword(value)) {
                    return '';
                }
            }
            return originalGetAttribute.call(this, name);
        };
        
        // 4. title 속성 자체를 Object.defineProperty로 완전히 차단
        function blockTitleProperty(element) {
            try {
                // 이미 차단된 요소는 건너뛰기
                if (element._titleBlocked) return;
                
                const titleValue = element.getAttribute('title');
                if (titleValue && containsKeyboardKeyword(titleValue)) {
                    element.removeAttribute('title');
                    // title 속성을 완전히 차단
                    try {
                        Object.defineProperty(element, 'title', {
                            get: function() { return ''; },
                            set: function(value) {
                                if (value && containsKeyboardKeyword(value)) {
                                    return; // 설정 차단
                                }
                                element.setAttribute('title', value);
                            },
                            configurable: true
                        });
                        element._titleBlocked = true;
                    } catch(e) {
                        // 이미 정의된 경우 무시
                    }
                }
            } catch(e) {
                // 오류 무시
            }
        }
        
        // 5. 모든 요소에서 keyboard 관련 속성 제거
        function removeKeyboardAttributes() {
            document.querySelectorAll('*').forEach(el => {
                try {
                    // title 제거
                    const title = el.getAttribute('title');
                    if (title && containsKeyboardKeyword(title)) {
                        el.removeAttribute('title');
                        blockTitleProperty(el);
                    }
                    
                    // aria-label 제거
                    const ariaLabel = el.getAttribute('aria-label');
                    if (ariaLabel && containsKeyboardKeyword(ariaLabel)) {
                        el.removeAttribute('aria-label');
                    }
                    
                    // data 속성도 체크 (일부 경우)
                    Array.from(el.attributes).forEach(attr => {
                        if (attr.name.startsWith('data-') && containsKeyboardKeyword(attr.value)) {
                            // data 속성은 유지하되 title만 제거
                        }
                    });
                } catch(e) {
                    // 무시
                }
            });
        }
        
        // 6. MutationObserver - 모든 변경사항 실시간 감지
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes') {
                    const target = mutation.target;
                    const attrName = mutation.attributeName;
                    
                    if (attrName === 'title' || attrName === 'aria-label') {
                        const value = target.getAttribute(attrName);
                        if (value && containsKeyboardKeyword(value)) {
                            target.removeAttribute(attrName);
                            if (attrName === 'title') {
                                blockTitleProperty(target);
                            }
                        }
                    }
                }
                
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1) { // Element node
                            // 새로 추가된 노드 즉시 처리
                            ['title', 'aria-label'].forEach(attr => {
                                const value = node.getAttribute && node.getAttribute(attr);
                                if (value && containsKeyboardKeyword(value)) {
                                    node.removeAttribute(attr);
                                    if (attr === 'title') {
                                        blockTitleProperty(node);
                                    }
                                }
                            });
                            
                            // 자식 요소도 재귀적으로 처리
                            if (node.querySelectorAll) {
                                node.querySelectorAll('*').forEach(child => {
                                    ['title', 'aria-label'].forEach(attr => {
                                        const value = child.getAttribute(attr);
                                        if (value && containsKeyboardKeyword(value)) {
                                            child.removeAttribute(attr);
                                            if (attr === 'title') {
                                                blockTitleProperty(child);
                                            }
                                        }
                                    });
                                });
                            }
                        }
                    });
                }
            });
            
            // 주기적으로 전체 스캔
            removeKeyboardAttributes();
        });
        
        // 7. 모든 마우스/포커스 이벤트에서 실시간 차단
        const eventTypes = ['mouseover', 'mouseenter', 'mousemove', 'focus', 'focusin', 'touchstart'];
        eventTypes.forEach(eventType => {
            document.addEventListener(eventType, function(e) {
                if (e.target) {
                    const target = e.target;
                    ['title', 'aria-label'].forEach(attr => {
                        const value = target.getAttribute && target.getAttribute(attr);
                        if (value && containsKeyboardKeyword(value)) {
                            target.removeAttribute(attr);
                            if (attr === 'title') {
                                blockTitleProperty(target);
                            }
                        }
                    });
                }
            }, true); // capture phase에서 실행
        });
        
        // 8. 초기화 함수
        function init() {
            removeKeyboardAttributes();
            
            // MutationObserver 시작
            observer.observe(document.documentElement, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ['title', 'aria-label']
            });
        }
        
        // 9. 즉시 실행 및 다양한 시점에서 재실행
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
        } else {
            init();
        }
        
        window.addEventListener('load', init);
        
        // 최적화: 주기적 체크를 1초로 변경 (10ms -> 1000ms)
        // MutationObserver가 실시간으로 처리하므로 주기적 체크는 보조적 역할만
        setInterval(removeKeyboardAttributes, 1000);
        
        // 사이드바 특별 감시 (1초 주기로 변경, 50ms -> 1000ms)
        function watchSidebar() {
            // 1) 사이드바 내부 요소들의 툴팁 제거
            const sidebar = document.querySelector('[data-testid="stSidebar"]');
            if (sidebar) {
                sidebar.querySelectorAll('*').forEach(el => {
                    ['title', 'aria-label'].forEach(attr => {
                        const value = el.getAttribute(attr);
                        if (value && containsKeyboardKeyword(value)) {
                            el.removeAttribute(attr);
                            if (attr === 'title') {
                                blockTitleProperty(el);
                            }
                        }
                    });
                });
            }
            
            // 2) 페이지 내 모든 요소를 검사해서 keyboard_double_* 텍스트를 가진 토글 컨트롤 찾기
            const elements = document.querySelectorAll('*');
            elements.forEach(el => {
                const text = (el.textContent || '').trim().toLowerCase();
                if (!text) return;
                
                // keyboard_double_* 같은 텍스트가 포함된 요소만 대상으로 함
                const hasKeyboardDouble =
                    (text.includes('keyboard') && text.includes('double')) ||
                    text.includes('keyboard_double');
                
                if (!hasKeyboardDouble) return;
                
                // 실제 클릭 가능한 요소 (button이나 role=button인 상위 요소)를 찾음
                const clickable = el.closest('button, [role=\"button\"]') || el;
                
                // 툴팁/접근성 텍스트 제거
                clickable.removeAttribute('title');
                clickable.removeAttribute('aria-label');
                if (clickable.getAttribute('title')) {
                    blockTitleProperty(clickable);
                }
                
                // 인라인 스타일로 강제 적용 (열림/닫힘 상태 모두 공통)
                clickable.style.width = '32px';
                clickable.style.height = '32px';
                clickable.style.borderRadius = '999px';
                clickable.style.backgroundColor = '#667eea';
                clickable.style.border = 'none';
                clickable.style.boxShadow = '0 0 0 2px rgba(255, 255, 255, 0.5)';
                clickable.style.display = 'inline-flex';
                clickable.style.alignItems = 'center';
                clickable.style.justifyContent = 'center';
                clickable.style.padding = '0';
                clickable.style.color = '#ffffff';
                clickable.style.cursor = 'pointer';
                
                // 기존 텍스트는 전부 숨김
                el.textContent = '';
                
                // 가운데 정렬된 화살표 아이콘 추가 (이미 있으면 건너뜀)
                if (!clickable.querySelector('.custom-sidebar-arrow')) {
                    const arrow = document.createElement('span');
                    arrow.className = 'custom-sidebar-arrow';
                    arrow.textContent = '⇔';
                    arrow.style.fontSize = '18px';
                    arrow.style.lineHeight = '1';
                    arrow.style.color = '#ffffff';
                    arrow.style.display = 'inline-block';
                    clickable.appendChild(arrow);
                }
            });
        }
        setInterval(watchSidebar, 1000);
        
        // 최적화: requestAnimationFrame 제거
        // MutationObserver와 주기적 체크로 충분히 처리 가능
        // requestAnimationFrame은 매 프레임마다 실행되어 성능 저하 유발
        
    })();
    
    // ========== 반응형 레이아웃 자동 조정 ==========
    (function() {
        'use strict';
        
        // 화면 크기 감지 및 조정
        function adjustLayout() {
            const width = window.innerWidth;
            const isMobile = width <= 768;
            const isTablet = width > 768 && width <= 1024;
            
            // 모바일에서 사이드바 자동 접기
            if (isMobile) {
                const sidebar = document.querySelector('[data-testid="stSidebar"]');
                if (sidebar) {
                    // 사이드바가 열려있으면 접기
                    const sidebarButton = document.querySelector('[data-testid="stSidebar"] button[aria-label*="close"], [data-testid="stSidebar"] button[aria-label*="열기"]');
                    if (sidebarButton && sidebar.offsetWidth > 0) {
                        // 사이드바가 열려있는 상태
                        // 필요시 자동으로 접을 수 있지만, 사용자 경험을 위해 수동 제어 유지
                    }
                }
            }
            
            // 컬럼 레이아웃 자동 조정
            const columns = document.querySelectorAll('.stColumn');
            if (isMobile && columns.length > 1) {
                columns.forEach(col => {
                    col.style.width = '100%';
                    col.style.marginBottom = '1rem';
                });
            }
        }
        
        // 초기 실행
        adjustLayout();
        
        // 리사이즈 이벤트 리스너 (디바운싱)
        let resizeTimer;
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(adjustLayout, 250);
        });
        
        // 화면 방향 변경 감지 (모바일)
        window.addEventListener('orientationchange', function() {
            setTimeout(adjustLayout, 500);
        });
        
        // 터치 이벤트 최적화
        if ('ontouchstart' in window) {
            // 터치 디바이스 감지
            document.body.classList.add('touch-device');
            
            // 더블 탭 줌 방지 (선택적)
            let lastTouchEnd = 0;
            document.addEventListener('touchend', function(event) {
                const now = Date.now();
                if (now - lastTouchEnd <= 300) {
                    event.preventDefault();
                }
                lastTouchEnd = now;
            }, false);
        }
    })();
</script>
""".replace('{{THEME}}', st.session_state.get('theme', 'light')), unsafe_allow_html=True)

# 테마별 다크 모드 스타일 추가 (Python에서 theme 값으로 직접 제어)
if st.session_state.get("theme", "light") == "dark":
    st.markdown("""
    <style>
        /* 다크 모드 전용 스타일 */
        body,
        /* Streamlit 메인 컨테이너 */
        [data-testid="stAppViewContainer"] > .main {
            background-color: #020617 !important;
            color: #e5e7eb !important;
        }
        
        .main-header {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.6) !important;
        }
        
        .info-box {
            background: linear-gradient(135deg, #1e293b80 0%, #0f172a80 100%) !important;
            border-left-color: #38bdf8 !important;
            color: #e5e7eb !important;
        }
        
        .metric-card {
            background: #1e293b !important;
            border-color: #334155 !important;
            box-shadow: 0 2px 10px rgba(0,0,0,0.7) !important;
            color: #e5e7eb !important;
        }
        
        .card-section {
            background: #1e293b !important;
            border-left-color: #38bdf8 !important;
            color: #e5e7eb !important;
        }
        
        .form-container {
            background: #1e293b !important;
            border-color: #334155 !important;
            box-shadow: 0 2px 10px rgba(0,0,0,0.7) !important;
            color: #e5e7eb !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: #0f172a !important;
        }
        
        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] div {
            color: #e5e7eb !important;
        }
        
        h1,
        h2,
        h3,
        h4,
        h5,
        h6,
        p,
        span,
        div {
            color: #e5e7eb !important;
        }
        
        .stDataFrame {
            background-color: #1e293b !important;
        }
        
        .stDataFrame table {
            background-color: #1e293b !important;
            color: #e5e7eb !important;
        }
        
        .stDataFrame th {
            background-color: #0f172a !important;
            color: #e5e7eb !important;
        }
        
        .stDataFrame td {
            border-color: #334155 !important;
            color: #e5e7eb !important;
        }
        
        button[data-testid="baseButton-primary"] {
            background-color: #2563eb !important;
            color: #ffffff !important;
            border-color: #1d4ed8 !important;
        }
        
        button[data-testid="baseButton-primary"]:hover {
            background-color: #1d4ed8 !important;
        }
        
        button[data-testid="baseButton-secondary"] {
            background-color: #1e293b !important;
            color: #e5e7eb !important;
            border-color: #334155 !important;
        }
        
        button[data-testid="baseButton-secondary"]:hover {
            background-color: #334155 !important;
        }
        
        input,
        select,
        textarea {
            background-color: #1e293b !important;
            color: #e5e7eb !important;
            border-color: #334155 !important;
        }
        
        .stSelectbox > div > div > select,
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input {
            background-color: #1e293b !important;
            color: #e5e7eb !important;
        }
    </style>
    """, unsafe_allow_html=True)

# 타이틀 (개선된 디자인)
st.markdown("""
<div class="main-header">
    <h1>🏪 매장 운영 시스템 v1</h1>
    <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1.1rem;">효율적인 매장 운영을 위한 통합 관리 시스템</p>
</div>
""", unsafe_allow_html=True)

# 사이드바 상단: 매장명 및 로그아웃
with st.sidebar:
    store_name = get_current_store_name()
    
    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
        <div style="font-size: 0.9rem; color: rgba(255,255,255,0.7); margin-bottom: 0.3rem;">🏪 현재 매장</div>
        <div style="font-size: 1.1rem; font-weight: 600; color: white;">{store_name}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 테마 전환 버튼
    st.markdown("### 🎨 테마 설정")
    col1, col2 = st.columns(2)
    current_theme = st.session_state.get("theme", "light")
    
    with col1:
        if st.button("☀️ 화이트", use_container_width=True, 
                    type="primary" if current_theme == "light" else "secondary",
                    key="theme_light"):
            st.session_state.theme = "light"
            st.rerun()
    
    with col2:
        if st.button("🌙 다크", use_container_width=True,
                    type="primary" if current_theme == "dark" else "secondary",
                    key="theme_dark"):
            st.session_state.theme = "dark"
            st.rerun()
    
    st.markdown("---")
    
    if st.button("🚪 로그아웃", use_container_width=True, type="secondary"):
        logout()
        st.rerun()
    
    st.markdown("---")
    
    # 백업 기능
    if st.button("💾 데이터 백업 생성", use_container_width=True):
        try:
            success, message = create_backup()
            if success:
                st.success(f"백업이 생성되었습니다!\n{message}")
            else:
                st.error(f"백업 생성 실패: {message}")
        except Exception as e:
            st.error(f"백업 중 오류: {e}")

# 사이드바 네비게이션 - 카테고리별로 구분
# 메뉴 항목들을 카테고리별로 정의
menu_categories = {
    "매출": [
        ("점장 마감", "📋"),
        ("매출 관리", "📊"),
        ("판매 관리", "📦"),
        ("발주 관리", "🛒"),
    ],
    "비용": [
        ("재료 사용량 집계", "📈"),
        ("메뉴 등록", "🍽️"),
        ("재료 등록", "🥬"),
        ("레시피 등록", "📝"),
        ("원가 파악", "💰"),
    ],
    "재무": [
        ("비용구조", "💳"),
    ],
    "기타": [
        ("주간 리포트", "📄"),
        ("통합 대시보드", "📊"),
    ]
}

# 선택된 페이지 확인
if 'current_page' not in st.session_state:
    st.session_state.current_page = "점장 마감"

# 모든 메뉴 항목 추출 (순서 유지)
all_menu_items = []
all_menu_options = []

for category_name, items in menu_categories.items():
    for menu_name, icon in items:
        all_menu_items.append((menu_name, icon))
        all_menu_options.append(f"{icon} {menu_name}")

# 카테고리별로 헤더와 메뉴를 함께 표시
# 각 카테고리의 메뉴를 버튼으로 표시하여 카테고리별 구분이 명확하게 보이도록 함
selected_menu_text = st.session_state.current_page

for category_name, items in menu_categories.items():
    # 카테고리 헤더
    st.sidebar.markdown(f"""
    <div style="margin-top: 1.5rem; margin-bottom: 0.5rem;">
        <div style="font-size: 0.85rem; color: rgba(255,255,255,0.6); text-transform: uppercase; letter-spacing: 1px; font-weight: 600; padding-left: 0.5rem;">
            {category_name}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 카테고리 내 각 메뉴를 버튼으로 표시
    for menu_name, icon in items:
        # 현재 선택된 메뉴인지 확인
        is_selected = (selected_menu_text == menu_name)
        button_type = "primary" if is_selected else "secondary"
        
        if st.sidebar.button(
            f"{icon} {menu_name}",
            key=f"menu_btn_{menu_name}",
            use_container_width=True,
            type=button_type
        ):
            st.session_state.current_page = menu_name
            st.rerun()

page = st.session_state.current_page

# 점장 마감 페이지
if page == "점장 마감":
    render_page_header("점장 마감", "📋")
    
    st.markdown("""
    <div class="info-box">
        <strong>⏱️ 목표:</strong> 하루 1번, 1분 안에 입력하고 끝내는 간단한 마감 입력 화면입니다.
    </div>
    """, unsafe_allow_html=True)
    
    # 전체 메뉴 로드
    menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
    menu_list = menu_df['메뉴명'].tolist() if not menu_df.empty else []
    
    # 점장 마감 입력 폼
    date, store, card_sales, cash_sales, total_sales, visitors, sales_items, issues, memo = render_manager_closing_input(menu_list)
    
    st.markdown("---")
    
    # 마감 완료 버튼
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✅ 마감 완료", type="primary", use_container_width=True, key="manager_close_btn"):
            errors = []
            
            if not store or store.strip() == "":
                errors.append("매장명을 입력해주세요.")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                try:
                    # daily_close에 저장
                    result = save_daily_close(
                        date, store, card_sales, cash_sales, total_sales,
                        visitors, sales_items, issues, memo
                    )
                    
                    # 저장 결과에 따라 메시지 표시
                    if result:
                        st.success("✅ 마감이 완료되었습니다! 데이터가 저장되었습니다.")
                    else:
                        # DEV MODE 등에서 저장되지 않은 경우
                        st.warning("⚠️ DEV MODE: 마감 정보는 표시되지만 실제 데이터는 저장되지 않았습니다.")
                        st.info("💡 실제 저장을 원하시면 Supabase를 설정하고 DEV MODE를 비활성화하세요.")
                    
                    # 저장 성공 여부와 관계없이 풍선 애니메이션 및 마감 완료 메시지 표시
                    st.balloons()  # 항상 풍선 애니메이션 표시
                    st.info("💡 **마감 수정 방법**: 같은 날짜로 다시 마감을 입력하시면 기존 데이터가 자동으로 업데이트됩니다.")
                    
                    # 오늘 요약 카드 표시
                    st.markdown("---")
                    st.markdown("### 📊 오늘 요약")
                    
                    # 객단가 계산
                    avg_price = (total_sales / visitors) if visitors > 0 else 0
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div style="font-size: 0.9rem; color: #7f8c8d; margin-bottom: 0.5rem;">총매출</div>
                            <div style="font-size: 1.8rem; font-weight: 700; color: #28a745;">{total_sales:,}원</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div style="font-size: 0.9rem; color: #7f8c8d; margin-bottom: 0.5rem;">방문자수</div>
                            <div style="font-size: 1.8rem; font-weight: 700; color: #17a2b8;">{visitors}명</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div style="font-size: 0.9rem; color: #7f8c8d; margin-bottom: 0.5rem;">객단가</div>
                            <div style="font-size: 1.8rem; font-weight: 700; color: #ffc107;">{avg_price:,.0f}원</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col4:
                        menu_count = len([q for _, q in sales_items if q > 0])
                        st.markdown(f"""
                        <div class="metric-card">
                            <div style="font-size: 0.9rem; color: #7f8c8d; margin-bottom: 0.5rem;">판매 메뉴 수</div>
                            <div style="font-size: 1.8rem; font-weight: 700; color: #667eea;">{menu_count}개</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # 판매량 TOP 3
                    if sales_items:
                        st.markdown("---")
                        st.markdown("### 🔝 판매량 TOP 3")
                        
                        sorted_items = sorted([(m, q) for m, q in sales_items if q > 0], key=lambda x: x[1], reverse=True)
                        top3_items = sorted_items[:3]
                        
                        if top3_items:
                            top3_cols = st.columns(len(top3_items))
                            for idx, (menu_name, quantity) in enumerate(top3_items):
                                with top3_cols[idx]:
                                    st.markdown(f"""
                                    <div class="metric-card">
                                        <div style="font-size: 0.9rem; color: #7f8c8d; margin-bottom: 0.5rem;">{menu_name}</div>
                                        <div style="font-size: 1.5rem; font-weight: 700; color: #667eea;">{quantity}개</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"저장 중 오류가 발생했습니다: {e}")

# 매출 관리 페이지 (매출 + 방문자 통합)
elif page == "매출 관리":
    render_page_header("매출 관리", "📊")
    
    # 카테고리 선택 (매출 / 방문자)
    category = st.radio(
        "카테고리",
        ["💰 매출", "👥 방문자"],
        horizontal=True,
        key="sales_category"
    )
    
    render_section_divider()
    
    # ========== 매출 입력 섹션 ==========
    if category == "💰 매출":
        # 입력 모드 선택 (단일 / 일괄)
        input_mode = st.radio(
            "입력 모드",
            ["단일 입력", "일괄 입력 (여러 날짜)"],
            horizontal=True,
            key="sales_input_mode"
        )
        
        render_section_divider()
        
        if input_mode == "단일 입력":
            # 단일 입력 폼
            date, store, card_sales, cash_sales, total_sales = render_sales_input()
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("💾 저장", type="primary", use_container_width=True):
                    if not store or store.strip() == "":
                        st.error("매장명을 입력해주세요.")
                    elif total_sales <= 0:
                        st.error("매출은 0보다 큰 값이어야 합니다.")
                    else:
                        try:
                            save_sales(date, store, card_sales, cash_sales, total_sales)
                            st.success(f"매출이 저장되었습니다! ({date}, {store}, 총매출: {total_sales:,}원)")
                            st.rerun()
                        except Exception as e:
                            st.error(f"저장 중 오류가 발생했습니다: {e}")
        
        else:
            # 일괄 입력 폼
            sales_data = render_sales_batch_input()
            
            if sales_data:
                render_section_divider()
                
                # 입력 요약 표시
                st.write("**📊 입력 요약**")
                summary_df = pd.DataFrame(
                    [(d.strftime('%Y-%m-%d'), s, f"{card:,}원", f"{cash:,}원", f"{total:,}원") 
                     for d, s, card, cash, total in sales_data],
                    columns=['날짜', '매장', '카드매출', '현금매출', '총매출']
                )
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
                
                total_card = sum(card for _, _, card, _, _ in sales_data)
                total_cash = sum(cash for _, _, _, cash, _ in sales_data)
                total_all = sum(total for _, _, _, _, total in sales_data)
                
                st.markdown(f"**총 {len(sales_data)}일, 카드매출: {total_card:,}원, 현금매출: {total_cash:,}원, 총 매출: {total_all:,}원**")
                
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("💾 일괄 저장", type="primary", use_container_width=True):
                        errors = []
                        success_count = 0
                        
                        for date, store, card_sales, cash_sales, total_sales in sales_data:
                            if not store or store.strip() == "":
                                errors.append(f"{date}: 매장명이 없습니다.")
                            else:
                                try:
                                    save_sales(date, store, card_sales, cash_sales, total_sales)
                                    success_count += 1
                                except Exception as e:
                                    errors.append(f"{date}: {e}")
                        
                        if errors:
                            for error in errors:
                                st.error(error)
                        
                        if success_count > 0:
                            st.success(f"✅ {success_count}일의 매출이 저장되었습니다!")
                            st.balloons()
                            st.rerun()
    
    # ========== 방문자 입력 섹션 ==========
    else:
        # 입력 모드 선택 (단일 / 일괄)
        input_mode = st.radio(
            "입력 모드",
            ["단일 입력", "일괄 입력 (여러 날짜)"],
            horizontal=True,
            key="visitor_input_mode"
        )
        
        render_section_divider()
        
        if input_mode == "단일 입력":
            # 단일 입력 폼
            date, visitors = render_visitor_input()
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("💾 저장", type="primary", use_container_width=True):
                    if visitors <= 0:
                        st.error("방문자수는 0보다 큰 값이어야 합니다.")
                    else:
                        try:
                            save_visitor(date, visitors)
                            st.success(f"방문자수가 저장되었습니다! ({date}, {visitors}명)")
                            st.rerun()
                        except Exception as e:
                            st.error(f"저장 중 오류가 발생했습니다: {e}")
        
        else:
            # 일괄 입력 폼
            visitor_data = render_visitor_batch_input()
            
            if visitor_data:
                render_section_divider()
                
                # 입력 요약 표시
                st.write("**📊 입력 요약**")
                summary_df = pd.DataFrame(
                    [(d.strftime('%Y-%m-%d'), f"{v}명") for d, v in visitor_data],
                    columns=['날짜', '방문자수']
                )
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
                
                st.markdown(f"**총 {len(visitor_data)}일, 총 방문자수: {sum(v for _, v in visitor_data):,}명**")
                
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("💾 일괄 저장", type="primary", use_container_width=True):
                        errors = []
                        success_count = 0
                        
                        for date, visitors in visitor_data:
                            try:
                                save_visitor(date, visitors)
                                success_count += 1
                            except Exception as e:
                                errors.append(f"{date}: {e}")
                        
                        if errors:
                            for error in errors:
                                st.error(error)
                        
                        if success_count > 0:
                            st.success(f"✅ {success_count}일의 방문자수가 저장되었습니다!")
                            st.balloons()
                            st.rerun()
    
    render_section_divider()
    
    # ========== 저장된 데이터 표시 ==========
    if category == "💰 매출":
        # 저장된 매출 표시 및 삭제
        render_section_header("저장된 매출 내역", "📋")
        sales_df = load_csv('sales.csv', default_columns=['날짜', '매장', '총매출'])
        
        if not sales_df.empty:
            # 삭제 기능
            st.write("**🗑️ 매출 데이터 삭제**")
            col1, col2, col3 = st.columns(3)
            with col1:
                delete_date = st.date_input("삭제할 날짜", key="sales_delete_date")
            with col2:
                delete_store_list = sales_df['매장'].unique().tolist()
                delete_store = st.selectbox(
                    "매장 선택 (전체 삭제 시 '전체' 선택)",
                    ["전체"] + delete_store_list,
                    key="sales_delete_store"
                )
            with col3:
                st.write("")
                st.write("")
                if st.button("🗑️ 삭제", key="sales_delete_btn", type="primary"):
                    try:
                        if delete_store == "전체":
                            success, message = delete_sales(delete_date, None)
                        else:
                            success, message = delete_sales(delete_date, delete_store)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"삭제 중 오류: {e}")
            
            render_section_divider()
            
            # 실제 입력값만 표시 (기술적 컬럼 제거)
            display_df = sales_df.copy()
            
            # 표시할 컬럼만 선택
            display_columns = []
            if '날짜' in display_df.columns:
                display_columns.append('날짜')
            if '매장' in display_df.columns:
                display_columns.append('매장')
            if '카드매출' in display_df.columns:
                display_columns.append('카드매출')
            if '현금매출' in display_df.columns:
                display_columns.append('현금매출')
            if '총매출' in display_df.columns:
                display_columns.append('총매출')
            
            # 필요한 컬럼만 선택
            if display_columns:
                display_df = display_df[display_columns]
                
                # 날짜를 문자열로 변환
                if '날짜' in display_df.columns:
                    display_df['날짜'] = pd.to_datetime(display_df['날짜']).dt.strftime('%Y-%m-%d')
                # 숫자 포맷팅
                if '총매출' in display_df.columns:
                    display_df['총매출'] = display_df['총매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                if '카드매출' in display_df.columns:
                    display_df['카드매출'] = display_df['카드매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                if '현금매출' in display_df.columns:
                    display_df['현금매출'] = display_df['현금매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # 차트 표시
            render_section_header("날짜별 매출 추이", "📈")
            render_sales_chart(sales_df)
        else:
            st.info("저장된 매출 데이터가 없습니다.")
    
    else:
        # 저장된 방문자 표시 및 삭제
        render_section_header("저장된 방문자 내역", "📋")
        visitors_df = load_csv('naver_visitors.csv', default_columns=['날짜', '방문자수'])
        
        if not visitors_df.empty:
            # 삭제 기능
            st.write("**🗑️ 방문자 데이터 삭제**")
            col1, col2 = st.columns([2, 1])
            with col1:
                delete_date = st.date_input("삭제할 날짜", key="visitor_delete_date")
            with col2:
                st.write("")
                st.write("")
                if st.button("🗑️ 삭제", key="visitor_delete_btn", type="primary"):
                    try:
                        success, message = delete_visitor(delete_date)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"삭제 중 오류: {e}")
            
            render_section_divider()
            
            # 실제 입력값만 표시 (기술적 컬럼 제거)
            display_df = visitors_df.copy()
            
            # 표시할 컬럼만 선택
            display_columns = []
            if '날짜' in display_df.columns:
                display_columns.append('날짜')
            if '방문자수' in display_df.columns:
                display_columns.append('방문자수')
            
            # 필요한 컬럼만 선택
            if display_columns:
                display_df = display_df[display_columns]
                
                # 날짜를 문자열로 변환
                if '날짜' in display_df.columns:
                    display_df['날짜'] = pd.to_datetime(display_df['날짜']).dt.strftime('%Y-%m-%d')
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("저장된 방문자 데이터가 없습니다.")

# 메뉴 등록 페이지
elif page == "메뉴 등록":
    render_page_header("메뉴 등록", "🍽️")
    
    # 입력 모드 선택 (단일 / 일괄)
    input_mode = st.radio(
        "입력 모드",
        ["단일 입력", "일괄 입력 (여러 메뉴)"],
        horizontal=True,
        key="menu_input_mode"
    )
    
    render_section_divider()
    
    if input_mode == "단일 입력":
        # 단일 입력 폼
        menu_name, price = render_menu_input()
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("💾 저장", type="primary", use_container_width=True):
                if not menu_name or menu_name.strip() == "":
                    st.error("메뉴명을 입력해주세요.")
                elif price <= 0:
                    st.error("판매가는 0보다 큰 값이어야 합니다.")
                else:
                    try:
                        success, message = save_menu(menu_name, price)
                        if success:
                            st.success(f"메뉴가 저장되었습니다! ({menu_name}, {price:,}원)")
                            st.rerun()
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"저장 중 오류가 발생했습니다: {e}")
    
    else:
        # 일괄 입력 폼
        menu_data = render_menu_batch_input()
        
        if menu_data:
            render_section_divider()
            
            # 입력 요약 표시
            st.write("**📊 입력 요약**")
            summary_df = pd.DataFrame(
                [(name, f"{price:,}원") for name, price in menu_data],
                columns=['메뉴명', '판매가']
            )
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            
            st.markdown(f"**총 {len(menu_data)}개 메뉴**")
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("💾 일괄 저장", type="primary", use_container_width=True):
                    errors = []
                    success_count = 0
                    
                    for menu_name, price in menu_data:
                        try:
                            success, message = save_menu(menu_name, price)
                            if success:
                                success_count += 1
                            else:
                                errors.append(f"{menu_name}: {message}")
                        except Exception as e:
                            errors.append(f"{menu_name}: {e}")
                    
                    if errors:
                        for error in errors:
                            st.error(error)
                    
                    if success_count > 0:
                        st.success(f"✅ {success_count}개 메뉴가 저장되었습니다!")
                        st.balloons()
                        st.rerun()
    
    render_section_divider()
    
    # 저장된 메뉴 표시 및 수정/삭제
    render_section_header("등록된 메뉴 리스트", "📋")
    menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
    
    if not menu_df.empty:
        display_df = menu_df.copy()
        if '판매가' in display_df.columns:
            display_df['판매가'] = display_df['판매가'].apply(lambda x: f"{int(x):,}원")
        
        # 수정/삭제 기능
        st.write("**📝 메뉴 수정/삭제**")
        menu_list = menu_df['메뉴명'].tolist()
        selected_menu = st.selectbox(
            "수정/삭제할 메뉴 선택",
            ["선택하세요"] + menu_list,
            key="menu_edit_select"
        )
        
        if selected_menu != "선택하세요":
            menu_info = menu_df[menu_df['메뉴명'] == selected_menu].iloc[0]
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**수정**")
                new_menu_name = st.text_input("메뉴명", value=menu_info['메뉴명'], key="menu_edit_name")
                new_price = st.number_input("판매가 (원)", min_value=0, value=int(menu_info['판매가']), step=1000, key="menu_edit_price")
                if st.button("✅ 수정", key="menu_edit_btn"):
                    try:
                        success, message = update_menu(menu_info['메뉴명'], new_menu_name, new_price)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"수정 중 오류: {e}")
            
            with col2:
                st.write("**삭제**")
                st.warning(f"⚠️ '{selected_menu}' 메뉴를 삭제하시겠습니까?")
                if st.button("🗑️ 삭제", key="menu_delete_btn", type="primary"):
                    try:
                        success, message, refs = delete_menu(selected_menu)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                            if refs:
                                st.info(f"**참조 정보:** {', '.join([f'{k}: {v}개' for k, v in refs.items()])}")
                    except Exception as e:
                        st.error(f"삭제 중 오류: {e}")
        
        render_section_divider()
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("등록된 메뉴가 없습니다.")

# 재료 등록 페이지
elif page == "재료 등록":
    render_page_header("재료 등록", "🥬")
    
    # 재료 입력 폼
    ingredient_name, unit, unit_price = render_ingredient_input()
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("💾 저장", type="primary", use_container_width=True):
            if not ingredient_name or ingredient_name.strip() == "":
                st.error("재료명을 입력해주세요.")
            elif unit_price <= 0:
                st.error("단가는 0보다 큰 값이어야 합니다.")
            else:
                try:
                    success, message = save_ingredient(ingredient_name, unit, unit_price)
                    if success:
                        st.success(f"재료가 저장되었습니다! ({ingredient_name}, {unit_price:,.2f}원/{unit})")
                        st.rerun()
                    else:
                        st.error(message)
                except Exception as e:
                    st.error(f"저장 중 오류가 발생했습니다: {e}")
    
    render_section_divider()
    
    # 저장된 재료 표시 및 수정/삭제
    render_section_header("등록된 재료 리스트", "📋")
    ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가'])
    
    if not ingredient_df.empty:
        display_df = ingredient_df.copy()
        # 단가 표시 포맷팅
        display_df['단가'] = display_df.apply(
            lambda x: f"{x['단가']:,.2f}원/{x['단위']}",
            axis=1
        )
        
        # 수정/삭제 기능
        st.write("**📝 재료 수정/삭제**")
        ingredient_list = ingredient_df['재료명'].tolist()
        selected_ingredient = st.selectbox(
            "수정/삭제할 재료 선택",
            ["선택하세요"] + ingredient_list,
            key="ingredient_edit_select"
        )
        
        if selected_ingredient != "선택하세요":
            ingredient_info = ingredient_df[ingredient_df['재료명'] == selected_ingredient].iloc[0]
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**수정**")
                new_ingredient_name = st.text_input("재료명", value=ingredient_info['재료명'], key="ingredient_edit_name")
                new_unit = st.text_input("단위", value=ingredient_info['단위'], key="ingredient_edit_unit")
                new_unit_price = st.number_input("단가 (원)", min_value=0.0, value=float(ingredient_info['단가']), step=100.0, key="ingredient_edit_price")
                if st.button("✅ 수정", key="ingredient_edit_btn"):
                    try:
                        success, message = update_ingredient(ingredient_info['재료명'], new_ingredient_name, new_unit, new_unit_price)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"수정 중 오류: {e}")
            
            with col2:
                st.write("**삭제**")
                st.warning(f"⚠️ '{selected_ingredient}' 재료를 삭제하시겠습니까?")
                if st.button("🗑️ 삭제", key="ingredient_delete_btn", type="primary"):
                    try:
                        success, message, refs = delete_ingredient(selected_ingredient)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                            if refs:
                                st.info(f"**참조 정보:** {', '.join([f'{k}: {v}개' for k, v in refs.items()])}")
                    except Exception as e:
                        st.error(f"삭제 중 오류: {e}")
        
        render_section_divider()
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("등록된 재료가 없습니다.")

# 레시피 등록 페이지
elif page == "레시피 등록":
    render_page_header("레시피 등록", "📝")
    
    # 메뉴 및 재료 목록 로드
    menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
    ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가'])
    
    menu_list = menu_df['메뉴명'].tolist() if not menu_df.empty else []
    ingredient_list = ingredient_df['재료명'].tolist() if not ingredient_df.empty else []
    
    # 레시피 입력 폼
    recipe_result = render_recipe_input(menu_list, ingredient_list)
    
    if recipe_result[0] is not None:
        menu_name, ingredient_name, quantity = recipe_result
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("💾 저장", type="primary", use_container_width=True):
                if quantity <= 0:
                    st.error("사용량은 0보다 큰 값이어야 합니다.")
                else:
                    try:
                        save_recipe(menu_name, ingredient_name, quantity)
                        st.success(f"레시피가 저장되었습니다! ({menu_name} - {ingredient_name}: {quantity})")
                        st.rerun()
                    except Exception as e:
                        st.error(f"저장 중 오류가 발생했습니다: {e}")
    
    render_section_divider()
    
    # 저장된 레시피 표시
    render_section_header("등록된 레시피", "📋")
    recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
    
    if not recipe_df.empty:
        # 메뉴 필터
        render_section_header("레시피 검색", "🔍")
        filter_menu = st.selectbox(
            "메뉴 필터",
            options=["전체"] + menu_list,
            key="recipe_filter_menu"
        )
        
        display_recipe_df = recipe_df.copy()
        if filter_menu != "전체":
            display_recipe_df = display_recipe_df[display_recipe_df['메뉴명'] == filter_menu]
        
        if not display_recipe_df.empty:
            # 재료 정보와 조인하여 단위 표시
            display_recipe_df = pd.merge(
                display_recipe_df,
                ingredient_df[['재료명', '단위']],
                on='재료명',
                how='left'
            )
            display_recipe_df['사용량'] = display_recipe_df.apply(
                lambda x: f"{x['사용량']:.2f}{x['단위']}" if pd.notna(x['단위']) else f"{x['사용량']:.2f}",
                axis=1
            )
            display_recipe_df = display_recipe_df[['메뉴명', '재료명', '사용량']]
            
            st.dataframe(display_recipe_df, use_container_width=True, hide_index=True)
        else:
            st.info(f"'{filter_menu}' 메뉴에 대한 레시피가 없습니다.")
    else:
        st.info("등록된 레시피가 없습니다.")

# 원가 파악 페이지
elif page == "원가 파악":
    render_page_header("원가 파악", "💰")
    
    # 데이터 로드
    menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
    recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
    ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가'])
    
    # 원가 계산
    if not menu_df.empty and not recipe_df.empty and not ingredient_df.empty:
        cost_df = calculate_menu_cost(menu_df, recipe_df, ingredient_df)
        render_cost_analysis(cost_df, warning_threshold=35.0)
    else:
        st.info("원가를 계산하려면 메뉴, 레시피, 재료 데이터가 모두 필요합니다.")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("메뉴 수", len(menu_df))
        with col2:
            st.metric("레시피 수", len(recipe_df))
        with col3:
            st.metric("재료 수", len(ingredient_df))

# 판매 관리 페이지
elif page == "판매 관리":
    render_page_header("판매 관리", "📦")
    
    # 메뉴 목록 로드
    menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
    menu_list = menu_df['메뉴명'].tolist() if not menu_df.empty else []
    
    # 일일 판매 입력 폼
    sales_result = render_daily_sales_input(menu_list)
    
    if sales_result[0] is not None:
        date, menu_name, quantity = sales_result
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("💾 저장", type="primary", use_container_width=True):
                if quantity <= 0:
                    st.error("판매수량은 0보다 큰 값이어야 합니다.")
                else:
                    try:
                        save_daily_sales_item(date, menu_name, quantity)
                        st.success(f"판매 내역이 저장되었습니다! ({date}, {menu_name}: {quantity}개)")
                        st.rerun()
                    except Exception as e:
                        st.error(f"저장 중 오류가 발생했습니다: {e}")
    
    render_section_divider()
    
    # 저장된 판매 내역 표시
    render_section_header("일일 판매 내역", "📋")
    daily_sales_df = load_csv('daily_sales_items.csv', default_columns=['날짜', '메뉴명', '판매수량'])
    
    if not daily_sales_df.empty:
        # 날짜 필터
        date_list = sorted(daily_sales_df['날짜'].unique(), reverse=True)
        selected_date = st.selectbox("날짜 필터", options=["전체"] + [str(d.date()) if hasattr(d, 'date') else str(d) for d in date_list], key="sales_date_filter")
        
        display_df = daily_sales_df.copy()
        if selected_date != "전체":
            display_df = display_df[display_df['날짜'].astype(str).str.startswith(selected_date)]
        
        if not display_df.empty:
            # 날짜를 문자열로 변환
            display_df['날짜'] = pd.to_datetime(display_df['날짜']).dt.strftime('%Y-%m-%d')
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # 집계 정보
            render_section_divider()
            render_section_header("판매 집계", "📊")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**날짜별 판매량**")
                date_summary = display_df.groupby('날짜')['판매수량'].sum().reset_index()
                date_summary.columns = ['날짜', '총 판매수량']
                st.dataframe(date_summary, use_container_width=True, hide_index=True)
            
            with col2:
                st.write("**메뉴별 판매량**")
                menu_summary = display_df.groupby('메뉴명')['판매수량'].sum().reset_index()
                menu_summary.columns = ['메뉴명', '총 판매수량']
                menu_summary = menu_summary.sort_values('총 판매수량', ascending=False)
                st.dataframe(menu_summary, use_container_width=True, hide_index=True)
        else:
            st.info(f"'{selected_date}' 날짜의 판매 내역이 없습니다.")
    else:
        st.info("저장된 판매 내역이 없습니다.")

# 재료 사용량 집계 페이지
elif page == "재료 사용량 집계":
    render_page_header("재료 사용량 집계", "📈")

    # 데이터 로드
    daily_sales_df = load_csv('daily_sales_items.csv', default_columns=['날짜', '메뉴명', '판매수량'])
    recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])

    render_section_divider()
    render_section_header("재료 사용량 집계", "📈")

    if not daily_sales_df.empty and not recipe_df.empty:
        usage_df = calculate_ingredient_usage(daily_sales_df, recipe_df)

        if not usage_df.empty:
            # 날짜 필터
            usage_date_list = sorted(usage_df['날짜'].unique(), reverse=True)
            selected_usage_date = st.selectbox(
                "날짜 필터 (재료 사용량)",
                options=["전체"] + [str(d.date()) if hasattr(d, 'date') else str(d) for d in usage_date_list],
                key="usage_date_filter"
            )

            display_usage_df = usage_df.copy()
            if selected_usage_date != "전체":
                display_usage_df = display_usage_df[display_usage_df['날짜'].astype(str).str.startswith(selected_usage_date)]

            if not display_usage_df.empty:
                display_usage_df['날짜'] = pd.to_datetime(display_usage_df['날짜']).dt.strftime('%Y-%m-%d')

                # 재료별 총 사용량 표시
                st.write("**재료별 사용량**")
                st.dataframe(display_usage_df, use_container_width=True, hide_index=True)

                # 오늘 사용한 재료 TOP (선택된 날짜가 오늘이거나 전체일 때)
                if selected_usage_date == "전체" or selected_usage_date == str(pd.Timestamp.now().date()):
                    ingredient_summary = display_usage_df.groupby('재료명')['총사용량'].sum().reset_index()
                    ingredient_summary = ingredient_summary.sort_values('총사용량', ascending=False).head(10)
                    ingredient_summary.columns = ['재료명', '총 사용량']

                    st.write("**🔝 사용량 TOP 10 재료**")
                    st.dataframe(ingredient_summary, use_container_width=True, hide_index=True)
        else:
            st.info("재료 사용량을 계산할 데이터가 없습니다.")
    else:
        st.info("판매 내역과 레시피 데이터가 필요합니다.")

# 발주 관리 페이지
elif page == "발주 관리":
    render_page_header("발주 관리", "🛒")
    
    # 재료 목록 로드
    ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가'])
    ingredient_list = ingredient_df['재료명'].tolist() if not ingredient_df.empty else []
    
    # 재고 입력 폼
    inventory_result = render_inventory_input(ingredient_list)
    
    if inventory_result[0] is not None:
        ingredient_name, current_stock, safety_stock = inventory_result
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("💾 저장", type="primary", use_container_width=True):
                try:
                    save_inventory(ingredient_name, current_stock, safety_stock)
                    st.success(f"재고 정보가 저장되었습니다! ({ingredient_name}: 현재고 {current_stock}, 안전재고 {safety_stock})")
                    st.rerun()
                except Exception as e:
                    st.error(f"저장 중 오류가 발생했습니다: {e}")
    
    render_section_divider()
    
    # 저장된 재고 정보 표시
    render_section_header("재고 현황", "📦")
    inventory_df = load_csv('inventory.csv', default_columns=['재료명', '현재고', '안전재고'])
    
    if not inventory_df.empty:
        # 재료 정보와 조인하여 단위 표시
        display_inventory_df = pd.merge(
            inventory_df,
            ingredient_df[['재료명', '단위']],
            on='재료명',
            how='left'
        )
        
        st.dataframe(display_inventory_df, use_container_width=True, hide_index=True)
    else:
        st.info("등록된 재고 정보가 없습니다.")
    
    # 발주 추천
    render_section_divider()
    render_section_header("발주 추천", "🛒")
    
    if not inventory_df.empty:
        # 재료 사용량 계산을 위한 데이터 로드
        daily_sales_df = load_csv('daily_sales_items.csv', default_columns=['날짜', '메뉴명', '판매수량'])
        recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
        
        # 발주 추천 파라미터 설정
        col1, col2 = st.columns(2)
        with col1:
            days_for_avg = st.number_input("평균 사용량 계산 기간 (일)", min_value=1, value=7, step=1, key="days_for_avg")
        with col2:
            forecast_days = st.number_input("예측일수", min_value=1, value=3, step=1, key="forecast_days")
        
        if not daily_sales_df.empty and not recipe_df.empty:
            # 재료 사용량 계산
            usage_df = calculate_ingredient_usage(daily_sales_df, recipe_df)
            
            if not usage_df.empty:
                # 발주 추천 계산
                order_df = calculate_order_recommendation(
                    ingredient_df,
                    inventory_df,
                    usage_df,
                    days_for_avg=int(days_for_avg),
                    forecast_days=int(forecast_days)
                )
                
                if not order_df.empty:
                    st.write("**📋 발주 추천 리스트**")
                    
                    # 표시용 DataFrame 생성
                    display_order_df = order_df.copy()
                    display_order_df['현재고'] = display_order_df['현재고'].apply(lambda x: f"{x:,.2f}")
                    display_order_df['안전재고'] = display_order_df['안전재고'].apply(lambda x: f"{x:,.2f}")
                    display_order_df['최근평균사용량'] = display_order_df['최근평균사용량'].apply(lambda x: f"{x:,.2f}")
                    display_order_df['예상소요량'] = display_order_df['예상소요량'].apply(lambda x: f"{x:,.2f}")
                    display_order_df['발주필요량'] = display_order_df['발주필요량'].apply(lambda x: f"{x:,.2f}")
                    display_order_df['예상금액'] = display_order_df['예상금액'].apply(lambda x: f"{int(x):,}원")
                    
                    st.dataframe(display_order_df, use_container_width=True, hide_index=True)
                    
                    # 총 예상 금액
                    total_amount = order_df['예상금액'].sum()
                    st.metric("총 예상 발주 금액", f"{int(total_amount):,}원")
                    
                    # 엑셀 다운로드
                    render_section_divider()
                    render_section_header("발주 리스트 다운로드", "📥")
                    
                    # CSV 형식으로 변환
                    csv_data = order_df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 발주 리스트 다운로드 (CSV)",
                        data=csv_data,
                        file_name=f"발주리스트_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.success("✅ 현재 발주가 필요한 재료가 없습니다.")
            else:
                st.info("재료 사용량 데이터가 없습니다. 판매 내역을 입력해주세요.")
        else:
            st.info("발주 추천을 계산하려면 판매 내역과 레시피 데이터가 필요합니다.")
    else:
        st.info("발주 추천을 계산하려면 재고 정보를 먼저 등록해주세요.")

# 주간 리포트 페이지
elif page == "주간 리포트":
    render_page_header("주간 리포트 생성", "📄")
    
    # 리포트 입력 폼
    start_date, end_date = render_report_input()
    
    # 날짜 유효성 검사
    if start_date > end_date:
        st.error("시작일이 종료일보다 늦을 수 없습니다.")
    else:
        st.markdown("---")
        
        # 리포트 생성 버튼
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("📄 리포트 생성", type="primary", use_container_width=True):
                try:
                    # 필요한 데이터 로드
                    sales_df = load_csv('sales.csv', default_columns=['날짜', '매장', '총매출'])
                    visitors_df = load_csv('naver_visitors.csv', default_columns=['날짜', '방문자수'])
                    daily_sales_df = load_csv('daily_sales_items.csv', default_columns=['날짜', '메뉴명', '판매수량'])
                    recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
                    ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가'])
                    inventory_df = load_csv('inventory.csv', default_columns=['재료명', '현재고', '안전재고'])
                    
                    # 재료 사용량 계산
                    from src.analytics import calculate_ingredient_usage
                    usage_df = calculate_ingredient_usage(daily_sales_df, recipe_df)
                    
                    # 리포트 생성
                    with st.spinner("리포트 생성 중..."):
                        pdf_path = generate_weekly_report(
                            sales_df,
                            visitors_df,
                            daily_sales_df,
                            recipe_df,
                            ingredient_df,
                            inventory_df,
                            usage_df,
                            start_date,
                            end_date
                        )
                    
                    st.success(f"리포트가 생성되었습니다! 📄")
                    
                    # PDF 다운로드 버튼
                    with open(pdf_path, 'rb') as f:
                        pdf_data = f.read()
                    
                    st.download_button(
                        label="📥 PDF 다운로드",
                        data=pdf_data,
                        file_name=f"주간리포트_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf",
                        mime="application/pdf"
                    )
                    
                    # 리포트 미리보기 정보
                    render_section_divider()
                    render_section_header("리포트 포함 내용", "📋")
                    st.info("""
                    - 총매출 및 일평균 매출
                    - 방문자수 총합 및 일평균
                    - 매출 vs 방문자 추세 차트
                    - 메뉴별 판매 TOP 10
                    - 재료 사용량 TOP 10
                    - 발주 추천 TOP 10
                    """)
                    
                except Exception as e:
                    st.error(f"리포트 생성 중 오류가 발생했습니다: {e}")
                    st.exception(e)
        
        # 기존 리포트 목록 표시
        render_section_divider()
        render_section_header("생성된 리포트 목록", "📁")
        
        from pathlib import Path
        reports_dir = Path(__file__).parent / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        pdf_files = list(reports_dir.glob("*.pdf"))
        if pdf_files:
            pdf_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for pdf_file in pdf_files[:10]:  # 최근 10개만 표시
                with open(pdf_file, 'rb') as f:
                    pdf_data = f.read()
                
                file_size = len(pdf_data) / 1024  # KB
                file_date = datetime.fromtimestamp(pdf_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"📄 {pdf_file.name}")
                with col2:
                    st.write(f"{file_size:.1f} KB ({file_date})")
                with col3:
                    st.download_button(
                        label="다운로드",
                        data=pdf_data,
                        file_name=pdf_file.name,
                        mime="application/pdf",
                        key=f"download_{pdf_file.name}"
                    )
        else:
            st.info("생성된 리포트가 없습니다.")

# 통합 대시보드 페이지
elif page == "통합 대시보드":
    st.header("📊 통합 대시보드")
    
    # 데이터 로드
    sales_df = load_csv('sales.csv', default_columns=['날짜', '매장', '총매출'])
    visitors_df = load_csv('naver_visitors.csv', default_columns=['날짜', '방문자수'])
    
    # 조인된 데이터 표시
    render_section_header("매출 & 방문자 통합 데이터", "📋")
    merged_df = merge_sales_visitors(sales_df, visitors_df)
    
    if not merged_df.empty:
        display_df = merged_df.copy()
        if '날짜' in display_df.columns:
            display_df['날짜'] = pd.to_datetime(display_df['날짜']).dt.strftime('%Y-%m-%d')
        if '총매출' in display_df.columns:
            display_df['총매출'] = display_df['총매출'].apply(
                lambda x: f"{int(x):,}원" if pd.notna(x) else "-"
            )
        if '방문자수' in display_df.columns:
            display_df['방문자수'] = display_df['방문자수'].apply(
                lambda x: f"{int(x):,}명" if pd.notna(x) else "-"
            )
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # 상관계수 계산 및 표시
        render_section_divider()
        render_section_header("매출-방문자 상관관계 분석", "📈")
        correlation = calculate_correlation(sales_df, visitors_df)
        render_correlation_info(correlation)
    else:
        st.info("통합할 데이터가 없습니다. 매출과 방문자 데이터를 먼저 입력해주세요.")

# 비용구조 페이지
elif page == "비용구조":
    render_page_header("비용구조 관리", "💳")
    
    from datetime import datetime
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    # 기간 선택 및 전월 데이터 복사
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        selected_year = st.number_input(
            "연도",
            min_value=2020,
            max_value=2100,
            value=current_year,
            key="expense_year"
        )
    with col2:
        selected_month = st.number_input(
            "월",
            min_value=1,
            max_value=12,
            value=current_month,
            key="expense_month"
        )
    with col3:
        st.write("")
        st.write("")
        if st.button("📋 전월 데이터 복사", key="copy_prev_month", use_container_width=True):
            try:
                success, message = copy_expense_structure_from_previous_month(selected_year, selected_month)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.warning(message)
            except Exception as e:
                st.error(f"복사 중 오류: {e}")
    
    render_section_divider()
    
    # ========== 손익분기점 계산 및 상단 표시 ==========
    expense_df = load_expense_structure(selected_year, selected_month)
    
    # 고정비 계산 (임차료, 인건비, 공과금)
    fixed_costs = 0
    if not expense_df.empty:
        fixed_categories = ['임차료', '인건비', '공과금']
        fixed_costs = expense_df[expense_df['category'].isin(fixed_categories)]['amount'].sum()
    
    # 변동비율 계산 (재료비, 부가세&카드수수료)
    # 변동비 카테고리의 모든 항목 비율 합계
    variable_cost_rate = 0.0  # % 단위
    if not expense_df.empty:
        variable_categories = ['재료비', '부가세&카드수수료']
        variable_df = expense_df[expense_df['category'].isin(variable_categories)]
        if not variable_df.empty:
            # 각 항목의 비율 합계 (amount 필드에 비율 저장됨)
            variable_cost_rate = variable_df['amount'].sum()
    
    # 손익분기점 계산: 고정비 / (1 - 변동비율)
    # 조건: 고정비 > 0 AND 변동비율 > 0 AND 변동비율 < 100
    breakeven_sales = None
    if fixed_costs > 0 and variable_cost_rate > 0 and variable_cost_rate < 100:
        variable_rate_decimal = variable_cost_rate / 100
        if variable_rate_decimal < 1 and (1 - variable_rate_decimal) > 0:
            breakeven_sales = fixed_costs / (1 - variable_rate_decimal)
    
    # 목표 매출 로드
    targets_df = load_csv('targets.csv', default_columns=[
        '연도', '월', '목표매출', '목표원가율', '목표인건비율',
        '목표임대료율', '목표기타비용율', '목표순이익률'
    ])
    
    target_sales = 0
    if not targets_df.empty:
        target_row = targets_df[(targets_df['연도'] == selected_year) & (targets_df['월'] == selected_month)]
        if not target_row.empty:
            target_sales = float(target_row.iloc[0].get('목표매출', 0))
    
    # 손익분기점 상단 공지 표시
    if breakeven_sales is not None and breakeven_sales > 0:
        # 평일/주말 비율 입력
        st.markdown("""
        <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid #667eea;">
            <div style="font-size: 1rem; font-weight: 600; margin-bottom: 0.5rem; color: #2c3e50;">📅 평일/주말 매출 비율 설정</div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 2, 2])
        with col1:
            weekday_ratio = st.number_input(
                "평일 매출 비율 (%)",
                min_value=0.0,
                max_value=100.0,
                value=70.0,
                step=1.0,
                format="%.1f",
                key="weekday_ratio",
                help="평일(22일) 매출이 차지하는 비율"
            )
        with col2:
            weekend_ratio = st.number_input(
                "주말 매출 비율 (%)",
                min_value=0.0,
                max_value=100.0,
                value=30.0,
                step=1.0,
                format="%.1f",
                key="weekend_ratio",
                help="주말(8일) 매출이 차지하는 비율"
            )
        with col3:
            st.write("")
            st.write("")
            total_ratio = weekday_ratio + weekend_ratio
            if abs(total_ratio - 100.0) > 0.1:
                st.warning(f"⚠️ 합계: {total_ratio:.1f}% (100%가 되어야 합니다)")
            else:
                st.success(f"✓ 합계: {total_ratio:.1f}%")
        
        # 목표 월매출 입력
        st.markdown("""
        <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; margin-top: 1rem; border-left: 4px solid #28a745;">
            <div style="font-size: 1rem; font-weight: 600; margin-bottom: 0.5rem; color: #2c3e50;">🎯 목표 월매출 설정</div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            target_sales_input = st.number_input(
                "목표 월매출 (원)",
                min_value=0,
                value=int(target_sales) if target_sales > 0 else 0,
                step=100000,
                key="target_sales_input",
                help="이번 달 목표 매출을 입력하세요"
            )
        with col2:
            st.write("")
            st.write("")
            if st.button("💾 목표 저장", key="save_target_sales", use_container_width=True):
                try:
                    # 목표 매출만 저장 (나머지는 0으로 설정)
                    save_targets(
                        selected_year, selected_month, 
                        target_sales_input, 0, 0, 0, 0, 0
                    )
                    st.success("목표 매출이 저장되었습니다!")
                    st.rerun()
                except Exception as e:
                    st.error(f"저장 중 오류: {e}")
        
        # 손익분기 매출과 목표 매출 비교 표시
        if abs(total_ratio - 100.0) <= 0.1:
            # 일일 손익분기 매출 계산
            weekday_daily_breakeven = (breakeven_sales * weekday_ratio / 100) / 22
            weekend_daily_breakeven = (breakeven_sales * weekend_ratio / 100) / 8
            
            # 일일 목표 매출 계산 (목표 매출이 있을 때만)
            weekday_daily_target = 0
            weekend_daily_target = 0
            if target_sales_input > 0:
                weekday_daily_target = (target_sales_input * weekday_ratio / 100) / 22
                weekend_daily_target = (target_sales_input * weekend_ratio / 100) / 8
            
            # 일일 고정비 계산 개선 (평일/주말 비율 반영)
            # 평일 고정비 = 고정비 × (평일 일수 / 총 일수) / 평일 일수
            weekday_monthly_fixed = fixed_costs * (22 / 30)
            weekend_monthly_fixed = fixed_costs * (8 / 30)
            weekday_daily_fixed = weekday_monthly_fixed / 22
            weekend_daily_fixed = weekend_monthly_fixed / 8
            
            # 일일 영업이익 계산
            # 일일 영업이익 = 일일 매출 × (1 - 변동비율) - 일일 고정비
            weekday_daily_breakeven_profit = 0  # 손익분기점이므로 0원
            weekend_daily_breakeven_profit = 0  # 손익분기점이므로 0원
            
            weekday_daily_target_profit = 0
            weekend_daily_target_profit = 0
            if target_sales_input > 0:
                weekday_daily_target_profit = (weekday_daily_target * (1 - variable_rate_decimal)) - weekday_daily_fixed
                weekend_daily_target_profit = (weekend_daily_target * (1 - variable_rate_decimal)) - weekend_daily_fixed
            
            # 손익분기 매출과 목표 매출 비교
            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 8px; margin-top: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem; color: #2c3e50; border-bottom: 2px solid #667eea; padding-bottom: 0.5rem;">
                    📊 손익분기 매출 vs 목표 매출 비교
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 추정 영업이익 계산
            # 영업이익 = 매출 × (1 - 변동비율) - 고정비
            variable_rate_decimal = variable_cost_rate / 100
            
            # 손익분기 매출의 추정 영업이익 (0원)
            breakeven_profit = 0
            
            # 목표 매출의 추정 영업이익
            target_profit = 0
            if target_sales_input > 0:
                target_profit = (target_sales_input * (1 - variable_rate_decimal)) - fixed_costs
            
            # 월간 매출 비교
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.5rem;">
                    <div style="font-size: 0.9rem; margin-bottom: 0.5rem; opacity: 0.9;">📊 손익분기 월매출</div>
                    <div style="font-size: 1.8rem; font-weight: 700;">{int(breakeven_sales):,}원</div>
                    <div style="font-size: 0.9rem; margin-top: 1rem; opacity: 0.9; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.8rem;">
                        💰 추정 영업이익
                    </div>
                    <div style="font-size: 1.3rem; font-weight: 600; margin-top: 0.3rem;">0원</div>
                    <div style="font-size: 0.75rem; margin-top: 0.5rem; opacity: 0.8; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.5rem;">
                        <strong>계산 공식:</strong><br>
                        고정비 ÷ (1 - 변동비율)<br>
                        = {int(fixed_costs):,}원 ÷ (1 - {variable_cost_rate:.1f}%)
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if target_sales_input > 0:
                    gap = target_sales_input - breakeven_sales
                    gap_percent = (gap / breakeven_sales * 100) if breakeven_sales > 0 else 0
                    gap_color = "#28a745" if gap > 0 else "#dc3545"
                    profit_color = "#ffd700" if target_profit > 0 else "#ff6b6b"
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); padding: 1.5rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.5rem;">
                        <div style="font-size: 0.9rem; margin-bottom: 0.5rem; opacity: 0.9;">🎯 목표 월매출</div>
                        <div style="font-size: 1.8rem; font-weight: 700;">{int(target_sales_input):,}원</div>
                        <div style="font-size: 0.9rem; margin-top: 1rem; opacity: 0.9; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.8rem;">
                            💰 추정 영업이익
                        </div>
                        <div style="font-size: 1.3rem; font-weight: 600; margin-top: 0.3rem; color: {profit_color};">{int(target_profit):,}원</div>
                        <div style="font-size: 0.75rem; margin-top: 0.5rem; opacity: 0.8; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.5rem;">
                            <strong>차이:</strong> <span style="color: {gap_color};">{gap:+,}원 ({gap_percent:+.1f}%)</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 8px; text-align: center; margin-top: 0.5rem; border: 2px dashed #dee2e6;">
                        <div style="font-size: 0.9rem; margin-bottom: 0.5rem; color: #6c757d;">🎯 목표 월매출</div>
                        <div style="font-size: 0.85rem; color: #6c757d;">위에서 목표 매출을 입력하세요</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # 일일 매출 비교
            st.markdown("""
            <div style="background: white; padding: 1.5rem; border-radius: 8px; margin-top: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem; color: #2c3e50; border-bottom: 2px solid #667eea; padding-bottom: 0.5rem;">
                    📅 일일 매출 비교
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 평일 일일 매출
            col1, col2 = st.columns(2)
            with col1:
                weekday_profit_color = "#ffd700" if weekday_daily_target_profit > 0 else "#ff6b6b" if weekday_daily_target_profit < 0 else "white"
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); padding: 1.5rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.5rem;">
                    <div style="font-size: 0.9rem; margin-bottom: 0.5rem; opacity: 0.9;">📅 평일 일일 매출</div>
                    <div style="font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">손익분기: {int(weekday_daily_breakeven):,}원</div>
                    {f'<div style="font-size: 1.5rem; font-weight: 700; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.5rem; margin-top: 0.5rem;">목표: {int(weekday_daily_target):,}원</div>' if target_sales_input > 0 else '<div style="font-size: 0.85rem; opacity: 0.7; margin-top: 0.5rem;">목표 매출 입력 필요</div>'}
                    <div style="font-size: 0.9rem; margin-top: 1rem; opacity: 0.9; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.8rem;">
                        💰 일일 영업이익
                    </div>
                    <div style="font-size: 1.1rem; font-weight: 600; margin-top: 0.3rem; margin-bottom: 0.3rem;">손익분기: 0원</div>
                    {f'<div style="font-size: 1.1rem; font-weight: 600; color: {weekday_profit_color};">목표: {int(weekday_daily_target_profit):,}원</div>' if target_sales_input > 0 else '<div style="font-size: 0.85rem; opacity: 0.7;">목표 매출 입력 필요</div>'}
                    <div style="font-size: 0.75rem; margin-top: 0.5rem; opacity: 0.8; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.5rem;">
                        (월매출 × {weekday_ratio:.1f}% ÷ 22일)
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                weekend_profit_color = "#ffd700" if weekend_daily_target_profit > 0 else "#ff6b6b" if weekend_daily_target_profit < 0 else "white"
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%); padding: 1.5rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.5rem;">
                    <div style="font-size: 0.9rem; margin-bottom: 0.5rem; opacity: 0.9;">🎉 주말 일일 매출</div>
                    <div style="font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">손익분기: {int(weekend_daily_breakeven):,}원</div>
                    {f'<div style="font-size: 1.5rem; font-weight: 700; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.5rem; margin-top: 0.5rem;">목표: {int(weekend_daily_target):,}원</div>' if target_sales_input > 0 else '<div style="font-size: 0.85rem; opacity: 0.7; margin-top: 0.5rem;">목표 매출 입력 필요</div>'}
                    <div style="font-size: 0.9rem; margin-top: 1rem; opacity: 0.9; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.8rem;">
                        💰 일일 영업이익
                    </div>
                    <div style="font-size: 1.1rem; font-weight: 600; margin-top: 0.3rem; margin-bottom: 0.3rem;">손익분기: 0원</div>
                    {f'<div style="font-size: 1.1rem; font-weight: 600; color: {weekend_profit_color};">목표: {int(weekend_daily_target_profit):,}원</div>' if target_sales_input > 0 else '<div style="font-size: 0.85rem; opacity: 0.7;">목표 매출 입력 필요</div>'}
                    <div style="font-size: 0.75rem; margin-top: 0.5rem; opacity: 0.8; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.5rem;">
                        (월매출 × {weekend_ratio:.1f}% ÷ 8일)
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("평일과 주말 비율의 합이 100%가 되어야 일일 매출을 계산할 수 있습니다.")
    else:
        st.markdown(f"""
        <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 12px; margin-bottom: 2rem; text-align: center; border-left: 4px solid #667eea;">
            <div style="font-size: 1.2rem; margin-bottom: 0.5rem; font-weight: 600;">📊 손익분기 매출 계산</div>
            <div style="font-size: 0.9rem; color: #666;">고정비와 변동비율을 모두 입력해야 손익분기 매출이 계산됩니다.</div>
            <div style="font-size: 0.85rem; color: #888; margin-top: 0.3rem;">고정비: 임차료, 인건비, 공과금 / 변동비: 재료비, 부가세&카드수수료</div>
        </div>
        """, unsafe_allow_html=True)
    
    render_section_divider()
    
    # ========== 비용 구조 입력 ==========
    # 5개 카테고리별 입력
    expense_categories = {
        '임차료': {'type': 'fixed', 'icon': '🏢', 'description': '고정비 (금액 직접 입력)'},
        '인건비': {'type': 'fixed', 'icon': '👥', 'description': '고정비 (금액 직접 입력)'},
        '재료비': {'type': 'variable', 'icon': '🥬', 'description': '변동비 (매출 대비 비율)'},
        '공과금': {'type': 'fixed', 'icon': '💡', 'description': '고정비 (금액 직접 입력)'},
        '부가세&카드수수료': {'type': 'variable', 'icon': '💳', 'description': '변동비 (매출 대비 비율)'}
    }
    
    # 기존 데이터 로드
    existing_items = {}
    if not expense_df.empty:
        for _, row in expense_df.iterrows():
            cat = row['category']
            if cat not in existing_items:
                existing_items[cat] = []
            existing_items[cat].append({
                'id': row.get('id'),
                'item_name': row.get('item_name'),
                'amount': row.get('amount'),
                'notes': row.get('notes')
            })
    
    # 한글 원화 변환 함수
    def format_korean_currency(amount):
        """숫자를 한글 원화로 변환 (예: 10000 -> 1만원, 15000000 -> 1천5백만원)"""
        if amount == 0:
            return "0원"
        
        # 억 단위
        eok = amount // 100000000
        remainder = amount % 100000000
        
        # 만 단위
        man = remainder // 10000
        remainder = remainder % 10000
        
        parts = []
        if eok > 0:
            parts.append(f"{eok}억")
        if man > 0:
            parts.append(f"{man}만")
        if remainder > 0:
            parts.append(f"{remainder:,}".replace(",", ""))
        
        if not parts:
            return "0원"
        
        return "".join(parts) + "원"
    
    # 각 카테고리별 입력 섹션
    for category, info in expense_categories.items():
        # 카테고리별 총액 계산
        category_total = 0
        category_items = existing_items.get(category, [])
        if category_items:
            if info['type'] == 'fixed':
                category_total = sum(item['amount'] for item in category_items)
            else:
                # 변동비는 비율 합계
                category_total = sum(item['amount'] for item in category_items)
        
        # 섹션 헤더와 총액 표시
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"""
            <div style="margin: 1.5rem 0 0.5rem 0;">
                <h3 style="color: #2c3e50; font-weight: 600; margin: 0;">
                    {info['icon']} {category}
                </h3>
            </div>
            """, unsafe_allow_html=True)
            st.caption(f"{info['description']}")
        with col2:
            if category_items:
                if info['type'] == 'fixed':
                    st.markdown(f"""
                    <div style="text-align: right; margin-top: 0.5rem; padding-top: 0.5rem;">
                        <strong style="color: #667eea; font-size: 1.1rem;">
                            총액: {format_korean_currency(int(category_total))}
                        </strong>
                        <div style="font-size: 0.85rem; color: #666;">
                            ({category_total:,.0f}원)
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="text-align: right; margin-top: 0.5rem;">
                        <strong style="color: #667eea; font-size: 1.1rem;">
                            총 비율: {category_total:.2f}%
                        </strong>
                    </div>
                    """, unsafe_allow_html=True)
        
        # 기존 항목 표시 - Expander 제거하고 직접 표시 (중첩 문제 해결)
        if category in existing_items and existing_items[category]:
            # 기존 항목은 기본적으로 접어두고 필요할 때만 펼치도록 처리 (모바일 스크롤 최소화)
            with st.expander(f"📋 기존 입력된 항목 ({len(existing_items[category])}개)", expanded=False):
                for item in existing_items[category]:
                    # 수정 모드 체크
                    edit_key = f"edit_{category}_{item['id']}"
                    is_editing = st.session_state.get(edit_key, False)
                    
                    if is_editing:
                        # 수정 모드
                        with st.container():
                            st.markdown("---")
                            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                            with col1:
                                edit_name = st.text_input(
                                    "항목명",
                                    value=item['item_name'],
                                    key=f"edit_name_{category}_{item['id']}"
                                )
                            with col2:
                                if info['type'] == 'fixed':
                                    edit_amount = st.number_input(
                                        "금액 (원)",
                                        min_value=0,
                                        value=int(item['amount']),
                                        step=10000,
                                        key=f"edit_amount_{category}_{item['id']}"
                                    )
                                else:
                                    edit_amount = st.number_input(
                                        "매출 대비 비율 (%)",
                                        min_value=0.0,
                                        max_value=100.0,
                                        value=float(item['amount']),
                                        step=0.1,
                                        format="%.2f",
                                        key=f"edit_rate_{category}_{item['id']}"
                                    )
                            with col3:
                                st.write("")
                                st.write("")
                                if st.button("💾 저장", key=f"save_edit_{category}_{item['id']}"):
                                    try:
                                        # 변동비율 검증 (변동비인 경우)
                                        if info['type'] == 'variable':
                                            existing_variable_total = sum(
                                                other_item['amount'] 
                                                for other_item in category_items 
                                                if other_item['id'] != item['id']
                                            )
                                            total_variable_rate = existing_variable_total + edit_amount
                                            
                                            # 모든 변동비 카테고리 합계 검증
                                            all_variable_categories = ['재료비', '부가세&카드수수료']
                                            all_variable_total = 0
                                            for var_cat in all_variable_categories:
                                                var_items = existing_items.get(var_cat, [])
                                                if var_cat == category:
                                                    all_variable_total += total_variable_rate
                                                else:
                                                    all_variable_total += sum(
                                                        other_item['amount'] 
                                                        for other_item in var_items
                                                    )
                                            
                                            if all_variable_total > 100:
                                                st.error(f"⚠️ 변동비율 합계가 100%를 초과할 수 없습니다. (합계: {all_variable_total:.2f}%)")
                                                st.stop()
                                        
                                        update_expense_item(item['id'], edit_name.strip(), edit_amount, item.get('notes'))
                                        st.session_state[edit_key] = False
                                        st.success("수정되었습니다!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"수정 중 오류: {e}")
                            with col4:
                                st.write("")
                                st.write("")
                            if st.button("❌ 취소", key=f"cancel_edit_{category}_{item['id']}"):
                                st.session_state[edit_key] = False
                                st.rerun()
                else:
                    # 일반 표시 모드
                    col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])
                    with col1:
                        st.write(f"**{item['item_name']}**")
                    with col2:
                        if info['type'] == 'fixed':
                            st.write(f"{format_korean_currency(int(item['amount']))} ({int(item['amount']):,}원)")
                        else:
                            st.write(f"{item['amount']:.2f}%")
                    with col3:
                        if item.get('notes'):
                            st.write(f"📝 {item['notes']}")
                    with col4:
                        if st.button("✏️", key=f"edit_btn_{category}_{item['id']}", help="수정"):
                            st.session_state[edit_key] = True
                            st.rerun()
                    with col5:
                        if st.button("🗑️", key=f"del_{category}_{item['id']}", help="삭제"):
                            try:
                                delete_expense_item(item['id'])
                                st.success("삭제되었습니다!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"삭제 중 오류: {e}")
        
        # 새 항목 입력
        if info['type'] == 'fixed':
            # 고정비: 금액 직접 입력
            # 입력 필드 초기화를 위한 카운터 사용
            reset_key = f"reset_count_{category}"
            if reset_key not in st.session_state:
                st.session_state[reset_key] = 0
            
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    # value 파라미터로 초기값 설정
                    default_name = "" if st.session_state[reset_key] == 0 else ""
                    new_item_name = st.text_input(
                        "항목명",
                        value=default_name,
                        key=f"new_item_name_{category}_{st.session_state[reset_key]}",
                        placeholder="예: 본점 임차료, 메인 요리사 급여 등"
                    )
                with col2:
                    default_amount = 0 if st.session_state[reset_key] == 0 else 0
                    new_amount = st.number_input(
                        "금액 (원)",
                        min_value=0,
                        value=default_amount,
                        step=10000,
                        key=f"new_amount_{category}_{st.session_state[reset_key]}"
                    )
                    # 한글 원화 표시
                    if new_amount > 0:
                        st.caption(f"💬 {format_korean_currency(int(new_amount))}")
                with col3:
                    st.write("")
                    st.write("")
                    if st.button("➕ 추가", key=f"add_{category}"):
                        if new_item_name and new_item_name.strip() and new_amount > 0:
                            # 항목명 중복 체크
                            existing_names = [item['item_name'] for item in category_items]
                            if new_item_name.strip() in existing_names:
                                st.warning("⚠️ 동일한 항목명이 이미 존재합니다.")
                            else:
                                try:
                                    save_expense_item(selected_year, selected_month, category, new_item_name.strip(), new_amount)
                                    # 입력 필드 초기화를 위해 카운터 증가
                                    st.session_state[reset_key] += 1
                                    st.success(f"{category} 항목이 추가되었습니다!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"저장 중 오류: {e}")
                        else:
                            st.error("항목명과 금액을 모두 입력해주세요.")
        else:
            # 변동비: 매출 대비 비율 입력
            # 입력 필드 초기화를 위한 카운터 사용
            reset_key = f"reset_count_{category}"
            if reset_key not in st.session_state:
                st.session_state[reset_key] = 0
            
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    # value 파라미터로 초기값 설정
                    default_name = "" if st.session_state[reset_key] == 0 else ""
                    new_item_name = st.text_input(
                        "항목명",
                        value=default_name,
                        key=f"new_item_name_{category}_{st.session_state[reset_key]}",
                        placeholder="예: 식자재 구매비, 카드사 수수료 등"
                    )
                with col2:
                    default_rate = 0.0 if st.session_state[reset_key] == 0 else 0.0
                    new_rate = st.number_input(
                        "매출 대비 비율 (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=default_rate,
                        step=0.1,
                        format="%.2f",
                        key=f"new_rate_{category}_{st.session_state[reset_key]}"
                    )
                    # 비율을 금액으로 저장 (나중에 계산 시 사용)
                    # 실제로는 비율(%)로 저장하되, amount 필드에 비율 값을 저장
                    # 하지만 DB 스키마상 amount는 NUMERIC이므로 비율도 저장 가능
                with col3:
                    st.write("")
                    st.write("")
                    if st.button("➕ 추가", key=f"add_{category}"):
                        if new_item_name and new_item_name.strip() and new_rate > 0:
                            # 변동비율 합계 검증
                            existing_variable_total = sum(item['amount'] for item in category_items)
                            total_variable_rate = existing_variable_total + new_rate
                            
                            # 모든 변동비 카테고리 합계 검증
                            all_variable_categories = ['재료비', '부가세&카드수수료']
                            all_variable_total = 0
                            for var_cat in all_variable_categories:
                                var_items = existing_items.get(var_cat, [])
                                if var_cat == category:
                                    all_variable_total += total_variable_rate
                                else:
                                    all_variable_total += sum(item['amount'] for item in var_items)
                            
                            if all_variable_total > 100:
                                st.error(f"⚠️ 변동비율 합계가 100%를 초과할 수 없습니다. (현재 합계: {all_variable_total:.2f}%)")
                            elif new_item_name.strip() in [item['item_name'] for item in category_items]:
                                st.warning("⚠️ 동일한 항목명이 이미 존재합니다.")
                            else:
                                try:
                                    # 변동비는 비율(%)을 amount에 저장
                                    save_expense_item(selected_year, selected_month, category, new_item_name.strip(), new_rate)
                                    # 입력 필드 초기화를 위해 카운터 증가
                                    st.session_state[reset_key] += 1
                                    st.success(f"{category} 항목이 추가되었습니다!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"저장 중 오류: {e}")
                        else:
                            st.error("항목명과 비율을 모두 입력해주세요.")
        
        render_section_divider()
    
    # ========== 목표매출 달성시 비용구조 분석 ==========
    if breakeven_sales is not None and breakeven_sales > 0 and target_sales_input > 0:
        render_section_header("목표매출 달성시 비용구조 분석", "💰")
        
        if not expense_df.empty:
            # 목표매출 달성시 각 비용 카테고리별 월매출 대비 비율 계산
            analysis_data = []
            
            for category in expense_categories.keys():
                cat_df = expense_df[expense_df['category'] == category]
                if not cat_df.empty:
                    if expense_categories[category]['type'] == 'fixed':
                        # 고정비: 금액을 월매출 대비 비율로 계산
                        category_amount = cat_df['amount'].sum()
                        category_ratio = (category_amount / target_sales_input * 100) if target_sales_input > 0 else 0
                        analysis_data.append({
                            '비용 카테고리': category,
                            '비용 금액': f"{int(category_amount):,}원",
                            '월매출 대비 비율': f"{category_ratio:.2f}%"
                        })
                    else:
                        # 변동비: 이미 비율로 저장되어 있음
                        category_rate = cat_df['amount'].sum()
                        category_amount = target_sales_input * (category_rate / 100)
                        analysis_data.append({
                            '비용 카테고리': category,
                            '비용 금액': f"{int(category_amount):,}원",
                            '월매출 대비 비율': f"{category_rate:.2f}%"
                        })
            
            # 분석 데이터프레임 생성
            if analysis_data:
                analysis_df = pd.DataFrame(analysis_data)
                st.dataframe(analysis_df, use_container_width=True, hide_index=True)
                
                # 총 비용 및 이익률 계산
                total_expenses = fixed_costs + (target_sales_input * variable_cost_rate / 100)
                expense_ratio = (total_expenses / target_sales_input * 100) if target_sales_input > 0 else 0
                profit_margin = 100 - expense_ratio
                
                st.markdown("---")
                
                # 요약 지표
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("목표 월매출", f"{int(target_sales_input):,}원")
                with col2:
                    st.metric("총 비용", f"{int(total_expenses):,}원")
                with col3:
                    st.metric("총 비용률", f"{expense_ratio:.2f}%")
                with col4:
                    st.metric("이익률", f"{profit_margin:.2f}%")
                
                # 알림 시스템
                st.markdown("#### ⚠️ 알림")
                alerts = []
                
                if variable_cost_rate > 50:
                    alerts.append("🔴 변동비율이 50%를 초과했습니다. 원가 관리가 필요합니다.")
                elif variable_cost_rate > 40:
                    alerts.append("🟡 변동비율이 40%를 초과했습니다. 주의가 필요합니다.")
                
                if fixed_costs > target_sales_input * 0.3:
                    alerts.append("🔴 고정비가 목표 매출의 30%를 초과했습니다.")
                
                if expense_ratio > 90:
                    alerts.append("🔴 총 비용률이 90%를 초과했습니다. 수익성이 매우 낮습니다.")
                elif expense_ratio > 80:
                    alerts.append("🟡 총 비용률이 80%를 초과했습니다. 비용 절감이 필요합니다.")
                
                if alerts:
                    for alert in alerts:
                        st.warning(alert)
                else:
                    st.success("✅ 모든 비용 지표가 정상 범위입니다.")
            else:
                st.info("비용 데이터가 없습니다.")
        else:
            st.info("목표 매출을 입력하고 비용 데이터를 입력해주세요.")
    
    # ========== 월간 집계 표시 ==========
    render_section_header("월간 비용 집계", "📊")
    
    if not expense_df.empty:
        # 카테고리별 집계
        summary_data = []
        total_amount = 0
        
        for category in expense_categories.keys():
            cat_df = expense_df[expense_df['category'] == category]
            if not cat_df.empty:
                if expense_categories[category]['type'] == 'fixed':
                    # 고정비: 합계
                    cat_total = cat_df['amount'].sum()
                    summary_data.append({
                        '카테고리': category,
                        '유형': '고정비',
                        '항목수': len(cat_df),
                        '합계': f"{int(cat_total):,}원"
                    })
                    total_amount += cat_total
                else:
                    # 변동비: 비율 표시 (평균 또는 합계)
                    # 실제로는 각 항목이 비율이므로, 가장 큰 비율 또는 합계를 표시
                    cat_max_rate = cat_df['amount'].max()
                    summary_data.append({
                        '카테고리': category,
                        '유형': '변동비',
                        '항목수': len(cat_df),
                        '합계': f"{cat_max_rate:.2f}% (최대 비율)"
                    })
        
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-top: 1rem;">
                <strong>총 고정비: {int(total_amount):,}원</strong>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info(f"{selected_year}년 {selected_month}월의 비용 데이터가 없습니다. 위에서 비용 항목을 입력해주세요.")

# 비용구조 페이지 끝
