"""
매장 운영 시스템 v1 - 메인 앱 (Supabase 기반)
"""
import streamlit as st
from datetime import datetime
import pandas as pd

# 페이지 설정은 최상단에 위치 (다른 st.* 호출 전에)
st.set_page_config(
    page_title="황승진 외식경영 의사결정도구",
    page_icon="🍽️",
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
    update_menu_category,
    update_menu_cooking_method,
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
from src.auth import get_supabase_client, get_current_store_id
from src.analytics import (
    calculate_correlation,
    merge_sales_visitors,
    calculate_menu_cost,
    calculate_ingredient_usage,
    calculate_order_recommendation,
    abc_analysis,
    target_gap_analysis,
    optimize_order_by_supplier,
    calculate_inventory_turnover
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
    
    /* ========== 메인 헤더 (반응형) - 블랙 테마 ========== */
    .main-header {
        background: linear-gradient(135deg, #000000 0%, #1a1a2e 30%, #16213e 60%, #0f3460 100%);
        background-size: 200% 200%;
        animation: gradientShift 8s ease infinite;
        padding: 2.5rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), 0 0 40px rgba(100, 150, 255, 0.2);
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, rgba(100, 150, 255, 0.1) 30%, transparent 70%);
        animation: rotate 20s linear infinite;
    }
    
    .main-header::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: 
            radial-gradient(circle at 20% 50%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(100, 150, 255, 0.15) 0%, transparent 50%),
            radial-gradient(circle at 40% 20%, rgba(255, 255, 255, 0.08) 0%, transparent 50%);
        animation: sparkle 4s ease-in-out infinite alternate;
        pointer-events: none;
    }
    
    .main-header h1 {
        position: relative;
        z-index: 1;
        font-weight: 700;
        letter-spacing: -0.5px;
        color: white;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        white-space: nowrap;
        font-size: 2.25rem;
    }
    
    .main-header h1 .text-gradient {
        color: white;
        display: inline-block;
        background: none !important;
        -webkit-background-clip: initial !important;
        -webkit-text-fill-color: white !important;
        background-clip: initial !important;
        text-shadow: none;
    }
    
    .main-header h1 .emoji {
        display: inline-block;
        -webkit-text-fill-color: initial;
        background: none !important;
        text-shadow: none;
        filter: none;
    }
    
    /* 전광판 스타일 (독립 박스) */
    .led-board {
        position: relative;
        background: #000000;
        border: 3px solid #333333;
        border-radius: 8px;
        padding: 1rem 1.5rem;
        margin-bottom: 2rem;
        overflow: hidden;
        box-shadow: 
            inset 0 0 20px rgba(0, 255, 0, 0.3),
            0 0 30px rgba(0, 255, 0, 0.2);
    }
    
    .led-board::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: repeating-linear-gradient(
            0deg,
            rgba(0, 255, 0, 0.05) 0px,
            rgba(0, 255, 0, 0.05) 2px,
            transparent 2px,
            transparent 4px
        );
        pointer-events: none;
        z-index: 1;
    }
    
    .led-text {
        position: relative;
        height: 1.5rem;
        overflow: hidden;
        z-index: 2;
    }
    
    .led-text {
        position: relative;
        height: 1.5rem;
        overflow: hidden;
        z-index: 2;
    }
    
    .led-text::before {
        content: '마감 1분 입력  •  모든 데이터 분석  •  두희 현식 화이팅  •  마감 1분 입력  •  모든 데이터 분석  •  두희 현식 화이팅  •  마감 1분 입력  •  모든 데이터 분석  •  두희 현식 화이팅  •  마감 1분 입력  •  모든 데이터 분석  •  두희 현식 화이팅  •  ';
        position: absolute;
        white-space: nowrap;
        color: #33ff33;
        font-weight: 700;
        font-size: 1.2rem;
        letter-spacing: 2px;
        text-shadow: none;
        animation: ledBlink 1.5s ease-in-out infinite, ledScroll 8s linear infinite;
        line-height: 1.5rem;
        background: none !important;
        -webkit-background-clip: initial !important;
        -webkit-text-fill-color: #33ff33 !important;
        background-clip: initial !important;
    }
    
    @keyframes ledBlink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.85; }
    }
    
    @keyframes ledScroll {
        0% {
            transform: translateX(0);
        }
        100% {
            transform: translateX(-25%);
        }
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    @keyframes rotate {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    @keyframes sparkle {
        0% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    @media (max-width: 768px) {
        .main-header {
            padding: 1.5rem 1rem;
            margin-bottom: 1rem;
            border-radius: 8px;
        }
        
        .main-header h1 {
            font-size: 1.35rem !important;
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
    
    /* ========== 현재 매장 타일 박스 (메인 헤더와 동일한 블랙 테마, 톤 다운) ========== */
    .store-tile {
        background: linear-gradient(135deg, #0a0a0a 0%, #151520 30%, #121220 60%, #0d1a2e 100%);
        background-size: 200% 200%;
        animation: gradientShift 10s ease infinite;
        padding: 1.2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3), 0 0 20px rgba(100, 150, 255, 0.1);
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    .store-tile::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, rgba(100, 150, 255, 0.05) 30%, transparent 70%);
        animation: rotate 25s linear infinite;
    }
    
    .store-tile::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: 
            radial-gradient(circle at 20% 50%, rgba(255, 255, 255, 0.05) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(100, 150, 255, 0.08) 0%, transparent 50%),
            radial-gradient(circle at 40% 20%, rgba(255, 255, 255, 0.04) 0%, transparent 50%);
        animation: sparkle 5s ease-in-out infinite alternate;
        pointer-events: none;
    }
    
    .store-tile-label {
        position: relative;
        z-index: 1;
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.7);
        margin-bottom: 0.4rem;
        font-weight: 500;
        letter-spacing: 0.3px;
    }
    
    .store-tile-name {
        position: relative;
        z-index: 1;
        font-size: 1.15rem;
        font-weight: 600;
        color: #ffffff;
        letter-spacing: 0.3px;
    }
    
    @media (max-width: 768px) {
        .store-tile {
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
        
        .store-tile-label {
            font-size: 0.75rem;
        }
        
        .store-tile-name {
            font-size: 1rem;
        }
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
    <h1>
        <span class="emoji">😎</span>
        <span class="text-gradient">외식경영 의사결정 시스템 (운영 OS)</span>
    </h1>
</div>
<div class="led-board">
    <div class="led-text"></div>
</div>
""", unsafe_allow_html=True)

# 사이드바 상단: 매장명 및 로그아웃
with st.sidebar:
    store_name = get_current_store_name()
    
    st.markdown(f"""
    <div class="store-tile">
        <div class="store-tile-label">🏪 현재 매장</div>
        <div class="store-tile-name">{store_name}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 사이드바 네비게이션 - 카테고리별로 구분
    # 메뉴 항목들을 카테고리별로 정의
    menu_categories = {
        "⚡ 핵심 기능 (매일)": [
            ("점장 마감", "📋"),
            ("발주 관리", "🛒"),
            ("통합 대시보드", "📊"),
        ],
        "💰 매출 & 비용 (주 2-3회)": [
            ("매출 관리", "📊"),
            ("판매 관리", "📦"),
            ("재료 사용량 집계", "📈"),
            ("원가 파악", "💰"),
        ],
        "📈 재무 분석 (월 1-2회)": [
            ("목표 비용구조", "💳"),
            ("목표 매출구조", "📈"),
            ("실제정산", "🧾"),
        ],
        "📝 정보입력(변경시)": [
            ("매출 등록", "💰"),
            ("판매량 등록", "📦"),
            ("메뉴 등록", "🍽️"),
            ("재료 등록", "🥬"),
            ("레시피 등록", "📝"),
        ],
        "📄 리포트 (주간/월간)": [
            ("주간 리포트", "📄"),
        ],
        "👥 파트너 (필요시)": [
            ("직원 연락망", "👤"),
            ("협력사 연락망", "🤝"),
            ("게시판", "📌"),
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
    
    # 사이드바 하단: 테마 설정 (모든 메뉴 카테고리 아래에 배치)
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎨 테마 설정")
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
    
    # 사이드바 하단: 유틸리티 기능들 (테마 설정 아래에 배치)
    st.sidebar.markdown("---")
    st.sidebar.markdown("**🔧 유틸리티**")
    
    if st.sidebar.button("🚪 로그아웃", use_container_width=True, type="secondary", key="sidebar_logout_btn"):
        logout()
        st.rerun()
    
    if st.sidebar.button("💾 데이터 백업 생성", use_container_width=True, key="sidebar_backup_btn"):
        try:
            success, message = create_backup()
            if success:
                st.success(f"백업이 생성되었습니다!\n{message}")
            else:
                st.error(f"백업 생성 실패: {message}")
        except Exception as e:
            st.error(f"백업 중 오류: {e}")
    
    st.sidebar.markdown("**🔍 데이터 진단**")
    
    if st.sidebar.button("🔍 데이터 연결 상태 확인", use_container_width=True, key="sidebar_data_check_btn"):
        try:
            from src.auth import get_supabase_client, get_current_store_id
            
            # Supabase 클라이언트 확인
            supabase = get_supabase_client()
            if not supabase:
                st.error("❌ Supabase 클라이언트를 생성할 수 없습니다. 로그아웃 후 다시 로그인해주세요.")
            else:
                st.success("✅ Supabase 클라이언트 연결 성공")
            
            # store_id 확인
            store_id = get_current_store_id()
            if not store_id:
                st.error("❌ store_id를 찾을 수 없습니다. 로그아웃 후 다시 로그인해주세요.")
            else:
                st.success(f"✅ store_id: {store_id}")
            
            # 실제 데이터 확인
            if supabase and store_id:
                try:
                    # 메뉴 데이터 확인
                    menu_result = supabase.table("menu_master").select("id,name,price").eq("store_id", store_id).execute()
                    menu_count = len(menu_result.data) if menu_result.data else 0
                    st.info(f"📊 메뉴 데이터: {menu_count}개")
                    if menu_count > 0:
                        st.json(menu_result.data[:3])  # 처음 3개만 표시
                    
                    # 재료 데이터 확인
                    ing_result = supabase.table("ingredients").select("id,name,unit,unit_cost").eq("store_id", store_id).execute()
                    ing_count = len(ing_result.data) if ing_result.data else 0
                    st.info(f"📊 재료 데이터: {ing_count}개")
                    if ing_count > 0:
                        st.json(ing_result.data[:3])  # 처음 3개만 표시
                    
                    if menu_count == 0 and ing_count == 0:
                        st.warning("⚠️ 데이터가 없습니다. Supabase 테이블에서 직접 확인해주세요.")
                    else:
                        st.success("✅ 데이터가 존재합니다. 캐시를 클리어하고 새로고침해주세요.")
                        
                except Exception as e:
                    st.error(f"데이터 조회 중 오류: {e}")
                    st.exception(e)
        except Exception as e:
            st.error(f"진단 중 오류: {e}")
            st.exception(e)
    
    if st.sidebar.button("🔄 모든 캐시 클리어", use_container_width=True, key="sidebar_cache_clear_btn"):
        try:
            load_csv.clear()
            st.success("✅ 캐시가 클리어되었습니다. 페이지를 새로고침해주세요.")
            st.rerun()
        except Exception as e:
            st.error(f"캐시 클리어 중 오류: {e}")

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

# 매출 등록 페이지
elif page == "매출 등록":
    render_page_header("매출 등록", "💰")
    
    # 카테고리 선택 (매출 / 네이버 스마트플레이스 방문자)
    category = st.radio(
        "카테고리",
        ["💰 매출", "👥 네이버 스마트플레이스 방문자"],
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
    
    # ========== 네이버 스마트플레이스 방문자 입력 섹션 ==========
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
                        st.error("네이버 스마트플레이스 방문자수는 0보다 큰 값이어야 합니다.")
                    else:
                        try:
                            save_visitor(date, visitors)
                            st.success(f"네이버 스마트플레이스 방문자수가 저장되었습니다! ({date}, {visitors}명)")
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
                    columns=['날짜', '네이버 스마트플레이스 방문자수']
                )
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
                
                st.markdown(f"**총 {len(visitor_data)}일, 총 네이버 스마트플레이스 방문자수: {sum(v for _, v in visitor_data):,}명**")
                
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
                            st.success(f"✅ {success_count}일의 네이버 스마트플레이스 방문자수가 저장되었습니다!")
                            st.balloons()
                            st.rerun()

# 매출 관리 페이지 (분석 전용)
elif page == "매출 관리":
    render_page_header("매출 관리", "📊")
    
    from datetime import datetime, timedelta
    from calendar import monthrange
    
    # 데이터 로드
    sales_df = load_csv('sales.csv', default_columns=['날짜', '매장', '총매출'])
    visitors_df = load_csv('naver_visitors.csv', default_columns=['날짜', '방문자수'])
    targets_df = load_csv('targets.csv', default_columns=[
        '연도', '월', '목표매출', '목표원가율', '목표인건비율',
        '목표임대료율', '목표기타비용율', '목표순이익률'
    ])
    
    # 매출과 방문자 데이터 통합
    merged_df = merge_sales_visitors(sales_df, visitors_df)
    
    # 날짜 컬럼을 datetime으로 변환
    if not merged_df.empty and '날짜' in merged_df.columns:
        merged_df['날짜'] = pd.to_datetime(merged_df['날짜'])
    if not sales_df.empty and '날짜' in sales_df.columns:
        sales_df['날짜'] = pd.to_datetime(sales_df['날짜'])
    if not visitors_df.empty and '날짜' in visitors_df.columns:
        visitors_df['날짜'] = pd.to_datetime(visitors_df['날짜'])
    
    current_year = datetime.now().year
    current_month = datetime.now().month
    today = datetime.now().date()
    
    # 목표 매출 확인 (전역 사용)
    target_sales = 0
    target_row = targets_df[
        (targets_df['연도'] == current_year) & 
        (targets_df['월'] == current_month)
    ]
    if not target_row.empty:
        target_sales = float(target_row.iloc[0].get('목표매출', 0))
    
    # 이번달 데이터 필터링 및 기본 변수 계산 (전역 사용)
    month_data = merged_df[
        (merged_df['날짜'].dt.year == current_year) & 
        (merged_df['날짜'].dt.month == current_month)
    ].copy() if not merged_df.empty else pd.DataFrame()
    
    month_total_sales = month_data['총매출'].sum() if not month_data.empty and '총매출' in month_data.columns else 0
    month_total_visitors = month_data['방문자수'].sum() if not month_data.empty and '방문자수' in month_data.columns else 0
    
    if not merged_df.empty:
        # ========== 1. 핵심 요약 지표 (KPI 카드) ==========
        st.markdown("""
        <div style="margin: 2rem 0 1rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                📊 이번달 요약
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        if not month_data.empty:
            month_avg_daily_sales = month_total_sales / len(month_data) if len(month_data) > 0 else 0
            month_avg_daily_visitors = month_total_visitors / len(month_data) if len(month_data) > 0 else 0
            avg_customer_value = month_total_sales / month_total_visitors if month_total_visitors > 0 else 0
            
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("이번달 누적 매출", f"{month_total_sales:,.0f}원")
            with col2:
                st.metric("평균 일일 매출", f"{month_avg_daily_sales:,.0f}원")
            with col3:
                st.metric("이번달 총 방문자", f"{int(month_total_visitors):,}명")
            with col4:
                st.metric("평균 객단가", f"{avg_customer_value:,.0f}원")
            with col5:
                # 목표 달성률 계산
                target_achievement = (month_total_sales / target_sales * 100) if target_sales > 0 else None
                if target_achievement is not None:
                    st.metric("목표 달성률", f"{target_achievement:.1f}%", 
                            f"{target_achievement - 100:.1f}%p" if target_achievement != 100 else "0%p")
                else:
                    st.metric("목표 달성률", "-", help="목표 매출이 설정되지 않았습니다")
        
        render_section_divider()
        
        # ========== 2. 기간별 비교 분석 ==========
        st.markdown("""
        <div style="margin: 2rem 0 1rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                📈 기간별 비교 분석
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # 전월 데이터
        if current_month == 1:
            prev_month = 12
            prev_year = current_year - 1
        else:
            prev_month = current_month - 1
            prev_year = current_year
        
        prev_month_data = merged_df[
            (merged_df['날짜'].dt.year == prev_year) & 
            (merged_df['날짜'].dt.month == prev_month)
        ].copy()
        
        # 작년 동월 데이터
        last_year_month_data = merged_df[
            (merged_df['날짜'].dt.year == current_year - 1) & 
            (merged_df['날짜'].dt.month == current_month)
        ].copy()
        
        # 주간 비교 (이번 주 vs 지난 주)
        week_start = today - timedelta(days=today.weekday())
        last_week_start = week_start - timedelta(days=7)
        last_week_end = week_start - timedelta(days=1)
        
        this_week_data = merged_df[
            (merged_df['날짜'].dt.date >= week_start) & 
            (merged_df['날짜'].dt.date <= today)
        ].copy()
        
        last_week_data = merged_df[
            (merged_df['날짜'].dt.date >= last_week_start) & 
            (merged_df['날짜'].dt.date <= last_week_end)
        ].copy()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**전월 대비**")
            if not prev_month_data.empty and not month_data.empty:
                prev_sales = prev_month_data['총매출'].sum() if '총매출' in prev_month_data.columns else 0
                prev_visitors = prev_month_data['방문자수'].sum() if '방문자수' in prev_month_data.columns else 0
                
                sales_change = month_total_sales - prev_sales
                sales_change_pct = (sales_change / prev_sales * 100) if prev_sales > 0 else 0
                visitors_change = month_total_visitors - prev_visitors
                visitors_change_pct = (visitors_change / prev_visitors * 100) if prev_visitors > 0 else 0
                
                st.metric("매출", f"{month_total_sales:,.0f}원", f"{sales_change:+,.0f}원 ({sales_change_pct:+.1f}%)")
                st.metric("방문자", f"{int(month_total_visitors):,}명", f"{visitors_change:+,.0f}명 ({visitors_change_pct:+.1f}%)")
            else:
                st.info("전월 데이터 없음")
        
        with col2:
            st.write("**작년 동월 대비**")
            if not last_year_month_data.empty and not month_data.empty:
                last_year_sales = last_year_month_data['총매출'].sum() if '총매출' in last_year_month_data.columns else 0
                last_year_visitors = last_year_month_data['방문자수'].sum() if '방문자수' in last_year_month_data.columns else 0
                
                sales_change = month_total_sales - last_year_sales
                sales_change_pct = (sales_change / last_year_sales * 100) if last_year_sales > 0 else 0
                visitors_change = month_total_visitors - last_year_visitors
                visitors_change_pct = (visitors_change / last_year_visitors * 100) if last_year_visitors > 0 else 0
                
                st.metric("매출", f"{month_total_sales:,.0f}원", f"{sales_change:+,.0f}원 ({sales_change_pct:+.1f}%)")
                st.metric("방문자", f"{int(month_total_visitors):,}명", f"{visitors_change:+,.0f}명 ({visitors_change_pct:+.1f}%)")
            else:
                st.info("작년 동월 데이터 없음")
        
        with col3:
            st.write("**주간 비교 (이번 주 vs 지난 주)**")
            if not this_week_data.empty and not last_week_data.empty:
                this_week_sales = this_week_data['총매출'].sum() if '총매출' in this_week_data.columns else 0
                last_week_sales = last_week_data['총매출'].sum() if '총매출' in last_week_data.columns else 0
                this_week_visitors = this_week_data['방문자수'].sum() if '방문자수' in this_week_data.columns else 0
                last_week_visitors = last_week_data['방문자수'].sum() if '방문자수' in last_week_data.columns else 0
                
                sales_change = this_week_sales - last_week_sales
                sales_change_pct = (sales_change / last_week_sales * 100) if last_week_sales > 0 else 0
                visitors_change = this_week_visitors - last_week_visitors
                visitors_change_pct = (visitors_change / last_week_visitors * 100) if last_week_visitors > 0 else 0
                
                st.metric("매출", f"{this_week_sales:,.0f}원", f"{sales_change:+,.0f}원 ({sales_change_pct:+.1f}%)")
                st.metric("방문자", f"{int(this_week_visitors):,}명", f"{visitors_change:+,.0f}명 ({visitors_change_pct:+.1f}%)")
            else:
                st.info("주간 데이터 부족")
        
        render_section_divider()
        
        # ========== 3. 요일별 분석 ==========
        st.markdown("""
        <div style="margin: 2rem 0 1rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                📅 요일별 패턴 분석
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        if not month_data.empty:
            month_data['요일'] = month_data['날짜'].dt.day_name()
            day_names_kr = {
                'Monday': '월요일', 'Tuesday': '화요일', 'Wednesday': '수요일',
                'Thursday': '목요일', 'Friday': '금요일', 'Saturday': '토요일', 'Sunday': '일요일'
            }
            month_data['요일한글'] = month_data['요일'].map(day_names_kr)
            
            day_analysis = month_data.groupby('요일한글').agg({
                '총매출': ['mean', 'sum', 'count'],
                '방문자수': ['mean', 'sum']
            }).reset_index()
            day_analysis.columns = ['요일', '평균매출', '총매출', '일수', '평균방문자', '총방문자']
            day_analysis['객단가'] = day_analysis['평균매출'] / day_analysis['평균방문자']
            day_analysis = day_analysis.sort_values('평균매출', ascending=False)
            
            # 요일 순서 정렬
            day_order = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
            day_analysis['요일순서'] = day_analysis['요일'].map({day: i for i, day in enumerate(day_order)})
            day_analysis = day_analysis.sort_values('요일순서')
            
            display_day = day_analysis.copy()
            display_day['평균매출'] = display_day['평균매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
            display_day['총매출'] = display_day['총매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
            display_day['평균방문자'] = display_day['평균방문자'].apply(lambda x: f"{int(x):,.1f}명" if pd.notna(x) else "-")
            display_day['객단가'] = display_day['객단가'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
            
            st.dataframe(
                display_day[['요일', '일수', '평균매출', '총매출', '평균방문자', '객단가']],
                use_container_width=True,
                hide_index=True
            )
            
            # 가장 좋은/나쁜 요일
            best_day = day_analysis.loc[day_analysis['평균매출'].idxmax()]
            worst_day = day_analysis.loc[day_analysis['평균매출'].idxmin()]
            
            col1, col2 = st.columns(2)
            with col1:
                st.success(f"✅ **최고 요일**: {best_day['요일']} (평균 {int(best_day['평균매출']):,}원)")
            with col2:
                st.warning(f"⚠️ **최저 요일**: {worst_day['요일']} (평균 {int(worst_day['평균매출']):,}원)")
        
        render_section_divider()
        
        # 목표 관련 변수 초기화 (전역 사용)
        days_in_month = monthrange(current_year, current_month)[1]
        current_day = today.day if today.year == current_year and today.month == current_month else days_in_month
        remaining_days = days_in_month - current_day
        
        # 예상 매출 및 달성률 계산 (목표가 있는 경우)
        daily_actual = month_total_sales / current_day if current_day > 0 else 0
        forecast_sales = month_total_sales + (daily_actual * remaining_days) if current_day > 0 else 0
        forecast_achievement = (forecast_sales / target_sales * 100) if not target_row.empty and target_sales > 0 else None
        
        # ========== 4. 목표 대비 실적 ==========
        if not target_row.empty:
            st.markdown("""
            <div style="margin: 2rem 0 1rem 0;">
                <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                    🎯 목표 달성 현황
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            daily_target = target_sales / days_in_month if days_in_month > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("목표 매출", f"{target_sales:,.0f}원")
            with col2:
                st.metric("현재 누적 매출", f"{month_total_sales:,.0f}원", 
                        f"{month_total_sales - target_sales:+,.0f}원")
            with col3:
                st.metric("일평균 목표", f"{daily_target:,.0f}원")
            with col4:
                st.metric("일평균 실적", f"{daily_actual:,.0f}원", 
                        f"{daily_actual - daily_target:+,.0f}원")
            
            # 예상 매출 및 달성 가능성
            col1, col2 = st.columns(2)
            with col1:
                st.metric("예상 월 매출", f"{forecast_sales:,.0f}원")
            with col2:
                achievement_status = "✅ 달성 가능" if forecast_achievement >= 100 else "⚠️ 달성 위험"
                st.metric("예상 달성률", f"{forecast_achievement:.1f}%", achievement_status)
            
            # 남은 일수 기준 필요 일평균
            if remaining_days > 0:
                required_daily = (target_sales - month_total_sales) / remaining_days
                if required_daily > 0:
                    st.info(f"📌 목표 달성을 위해 남은 {remaining_days}일 동안 일평균 **{required_daily:,.0f}원**이 필요합니다.")
            
            render_section_divider()
        
        # ========== 5. 트렌드 분석 ==========
        st.markdown("""
        <div style="margin: 2rem 0 1rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                📊 매출 트렌드
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # 최근 7일 vs 최근 30일
        recent_7_days = merged_df[merged_df['날짜'].dt.date >= (today - timedelta(days=7))].copy()
        recent_30_days = merged_df[merged_df['날짜'].dt.date >= (today - timedelta(days=30))].copy()
        
        if not recent_7_days.empty and not recent_30_days.empty:
            avg_7d = recent_7_days['총매출'].mean() if '총매출' in recent_7_days.columns else 0
            avg_30d = recent_30_days['총매출'].mean() if '총매출' in recent_30_days.columns else 0
            trend_change = avg_7d - avg_30d
            trend_pct = (trend_change / avg_30d * 100) if avg_30d > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("최근 7일 평균", f"{avg_7d:,.0f}원")
            with col2:
                st.metric("최근 30일 평균", f"{avg_30d:,.0f}원")
            with col3:
                trend_status = "📈 상승" if trend_change > 0 else "📉 하락" if trend_change < 0 else "➡️ 유지"
                st.metric("트렌드", f"{trend_pct:+.1f}%", trend_status)
        
        render_section_divider()
        
        # ========== 6. 경고/알림 ==========
        st.markdown("""
        <div style="margin: 2rem 0 1rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                ⚠️ 알림 및 경고
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        alerts = []
        
        # 목표 대비 저조한 날짜
        if not target_row.empty and not month_data.empty:
            daily_target = target_sales / days_in_month if days_in_month > 0 else 0
            low_days = month_data[month_data['총매출'] < daily_target * 0.8] if '총매출' in month_data.columns else pd.DataFrame()
            if not low_days.empty:
                low_days_count = len(low_days)
                alerts.append(f"🔴 목표 대비 저조한 날짜: {low_days_count}일 (목표의 80% 미만)")
        
        # 전일 대비 급락
        if len(month_data) >= 2:
            recent_days = month_data.sort_values('날짜').tail(2)
            if len(recent_days) == 2:
                prev_sales = recent_days.iloc[0]['총매출'] if '총매출' in recent_days.columns else 0
                curr_sales = recent_days.iloc[1]['총매출'] if '총매출' in recent_days.columns else 0
                if prev_sales > 0:
                    drop_pct = ((curr_sales - prev_sales) / prev_sales * 100)
                    if drop_pct < -20:
                        alerts.append(f"🔴 전일 대비 급락: {drop_pct:.1f}% 감소")
        
        # 연속 저조일
        if not month_data.empty and '총매출' in month_data.columns:
            month_data_sorted = month_data.sort_values('날짜')
            daily_target = target_sales / days_in_month if not target_row.empty and days_in_month > 0 else month_data_sorted['총매출'].mean() * 0.8
            low_days_series = month_data_sorted['총매출'] < daily_target
            consecutive_low = 0
            max_consecutive = 0
            for is_low in low_days_series:
                if is_low:
                    consecutive_low += 1
                    max_consecutive = max(max_consecutive, consecutive_low)
                else:
                    consecutive_low = 0
            if max_consecutive >= 3:
                alerts.append(f"🟡 연속 저조일: {max_consecutive}일 연속 목표 미달")
        
        # 월말 목표 달성 위험
        if not target_row.empty and forecast_achievement is not None:
            if forecast_achievement < 90 and remaining_days <= 7:
                alerts.append(f"🔴 월말 목표 달성 위험: 현재 달성률 {target_achievement:.1f}%, 예상 달성률 {forecast_achievement:.1f}%")
        
        if alerts:
            for alert in alerts:
                if "🔴" in alert:
                    st.error(alert)
                elif "🟡" in alert:
                    st.warning(alert)
                else:
                    st.info(alert)
        else:
            st.success("✅ 특별한 알림이 없습니다. 매출이 정상적으로 진행되고 있습니다.")
        
        render_section_divider()
        
        # ========== 7. 월별 요약 테이블 ==========
        st.markdown("""
        <div style="margin: 2rem 0 1rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                📋 월별 요약 (최근 6개월)
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # 최근 6개월 데이터
        six_months_ago = today - timedelta(days=180)
        recent_6m_data = merged_df[merged_df['날짜'].dt.date >= six_months_ago].copy()
        
        if not recent_6m_data.empty:
            recent_6m_data['연도'] = recent_6m_data['날짜'].dt.year
            recent_6m_data['월'] = recent_6m_data['날짜'].dt.month
            
            monthly_summary = recent_6m_data.groupby(['연도', '월']).agg({
                '총매출': ['sum', 'mean', 'count'],
                '방문자수': ['sum', 'mean']
            }).reset_index()
            monthly_summary.columns = ['연도', '월', '월총매출', '일평균매출', '영업일수', '월총방문자', '일평균방문자']
            monthly_summary['월별객단가'] = monthly_summary['월총매출'] / monthly_summary['월총방문자']
            monthly_summary = monthly_summary.sort_values(['연도', '월'], ascending=[False, False])
            
            # 성장률 계산
            monthly_summary['전월대비'] = monthly_summary['월총매출'].pct_change() * 100
            
            display_monthly = monthly_summary.head(6).copy()
            display_monthly['월'] = display_monthly['월'].apply(lambda x: f"{int(x)}월")
            display_monthly['월총매출'] = display_monthly['월총매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
            display_monthly['일평균매출'] = display_monthly['일평균매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
            display_monthly['월총방문자'] = display_monthly['월총방문자'].apply(lambda x: f"{int(x):,}명" if pd.notna(x) else "-")
            display_monthly['월별객단가'] = display_monthly['월별객단가'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
            display_monthly['전월대비'] = display_monthly['전월대비'].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "-")
            
            st.dataframe(
                display_monthly[['연도', '월', '영업일수', '월총매출', '일평균매출', '월총방문자', '월별객단가', '전월대비']],
                use_container_width=True,
                hide_index=True
            )
        
        render_section_divider()
        
        # ========== 8. 예측/예상 ==========
        st.markdown("""
        <div style="margin: 2rem 0 1rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                🔮 예상 매출 및 목표 달성 가능성
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        if not month_data.empty:
            # 현재 추세 기반 예상 (위에서 이미 계산된 forecast_sales 사용)
            if current_day > 0:
                
                # 필요 일평균 (목표가 있는 경우만)
                if not target_row.empty and target_sales > 0:
                    required_daily = (target_sales - month_total_sales) / remaining_days if remaining_days > 0 and target_sales > month_total_sales else 0
                else:
                    required_daily = 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("이번달 예상 총 매출", f"{forecast_sales:,.0f}원")
                with col2:
                    if forecast_achievement is not None:
                        st.metric("예상 목표 달성률", f"{forecast_achievement:.1f}%")
                    else:
                        st.info("목표 매출 미설정")
                with col3:
                    if required_daily > 0:
                        st.warning(f"필요 일평균: {required_daily:,.0f}원")
                    elif not target_row.empty:
                        st.success("목표 달성 가능")
                    else:
                        st.info("목표 미설정")
        
        render_section_divider()
        
        # ========== 저장된 매출 내역 ==========
        # 저장된 매출 내역 (매출 + 네이버 스마트플레이스 방문자 통합)
        st.markdown("""
        <div style="margin: 2rem 0 1rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                📋 저장된 매출 내역
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        if not merged_df.empty:
            # 통합 데이터 표시 (입력값만 표시)
            display_df = merged_df.copy()
            
            # 표시할 컬럼만 선택 (기술적 컬럼 제외)
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
            if '방문자수' in display_df.columns:
                display_columns.append('방문자수')
            
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
                if '방문자수' in display_df.columns:
                    display_df['방문자수'] = display_df['방문자수'].apply(lambda x: f"{int(x):,}명" if pd.notna(x) else "-")
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # ========== 이달 일일 매출과 방문자 사이의 연관성 ==========
        st.markdown("""
        <div style="margin: 2rem 0 1rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                📈 이달 일일 매출과 방문자 사이의 연관성
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # 이번달 데이터 사용 (위에서 이미 필터링됨)
        chart_df = month_data.copy() if not month_data.empty else pd.DataFrame()
        
        if not chart_df.empty and '총매출' in chart_df.columns and '방문자수' in chart_df.columns:
            # 연관성 지표 계산
            month_sales_df = chart_df[['날짜', '총매출']].copy()
            month_visitors_df = chart_df[['날짜', '방문자수']].copy()
            correlation = calculate_correlation(month_sales_df, month_visitors_df)
            
            # 연관성 지표 표시
            if correlation is not None:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "상관계수",
                        f"{correlation:.3f}",
                        help="피어슨 상관계수: -1 ~ 1 사이 값. 1에 가까울수록 양의 상관관계가 강함"
                    )
                with col2:
                    if correlation > 0.7:
                        st.success("✅ 강한 양의 상관관계\n방문자가 많을수록 매출이 높습니다.")
                    elif correlation > 0.3:
                        st.info("ℹ️ 중간 정도의 양의 상관관계")
                    elif correlation > -0.3:
                        st.warning("⚠️ 상관관계가 거의 없음")
                    else:
                        st.error("❌ 음의 상관관계")
                with col3:
                    # 평균 일일 매출
                    avg_sales = chart_df['총매출'].mean()
                    st.metric("평균 일일 매출", f"{avg_sales:,.0f}원")
            
            render_section_divider()
            
            # 표로 표시
            display_chart_df = chart_df.copy()
            display_chart_df['날짜'] = display_chart_df['날짜'].dt.strftime('%Y-%m-%d')
            display_chart_df['일일 매출'] = display_chart_df['총매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
            display_chart_df['일일 방문자수'] = display_chart_df['방문자수'].apply(lambda x: f"{int(x):,}명" if pd.notna(x) else "-")
            
            # 표시할 컬럼만 선택
            table_df = display_chart_df[['날짜', '일일 매출', '일일 방문자수']].copy()
            
            st.dataframe(table_df, use_container_width=True, hide_index=True)
        elif not chart_df.empty:
            st.info("이번달 매출 또는 방문자 데이터가 없습니다.")
        else:
            st.info("이번달 데이터가 없습니다.")
    else:
        st.info("저장된 매출 데이터가 없습니다.")

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
        
        # 입력할 메뉴 개수 가져오기
        menu_count = st.session_state.get("batch_menu_count", 5)
        
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
            
            # 버튼 클릭 시 현재 입력값을 직접 읽어오기
            col1, col2 = st.columns([1, 4])
            with col1:
                save_button_clicked = st.button("💾 일괄 저장", type="primary", use_container_width=True)
            
            if save_button_clicked:
                # 버튼 클릭 시 현재 입력된 모든 값 읽기
                current_menu_data = []
                for i in range(menu_count):
                    menu_name_key = f"batch_menu_name_{i}"
                    price_key = f"batch_menu_price_{i}"
                    
                    menu_name = st.session_state.get(menu_name_key, "")
                    price = st.session_state.get(price_key, 0)
                    
                    if menu_name and menu_name.strip() and price > 0:
                        current_menu_data.append((menu_name.strip(), price))
                
                if not current_menu_data:
                    st.error("⚠️ 저장할 메뉴가 없습니다. 메뉴명과 판매가를 모두 입력해주세요.")
                else:
                    errors = []
                    success_count = 0
                    
                    for menu_name, price in current_menu_data:
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
                        # 입력 필드 초기화
                        for i in range(menu_count):
                            if f"batch_menu_name_{i}" in st.session_state:
                                del st.session_state[f"batch_menu_name_{i}"]
                            if f"batch_menu_price_{i}" in st.session_state:
                                st.session_state[f"batch_menu_price_{i}"] = 0
                        st.rerun()
    
    render_section_divider()
    
    # 저장된 메뉴 표시 및 수정/삭제
    # 제목을 화이트 모드에서도 흰색으로 표시
    st.markdown("""
    <div style="margin: 2rem 0 1rem 0;">
        <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
            📋 등록된 메뉴 리스트
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
    
    if not menu_df.empty:
        # 카테고리 컬럼이 없으면 추가 (기본값: '기타메뉴')
        if 'category' not in menu_df.columns:
            menu_df['category'] = '기타메뉴'
        elif '카테고리' in menu_df.columns:
            menu_df['category'] = menu_df['카테고리']
        # 카테고리가 None이거나 빈 값인 경우 기본값 설정
        menu_df['category'] = menu_df['category'].fillna('기타메뉴')
        menu_df['category'] = menu_df['category'].replace('', '기타메뉴')
        
        # 카테고리 색상 매핑
        category_colors = {
            '대표메뉴': '#1e3a8a',      # 진한 파란색
            '주력메뉴': '#166534',      # 진한 초록색
            '유인메뉴': '#ea580c',      # 진한 주황색
            '보조메뉴': '#6b7280',      # 회색
            '기타메뉴': '#3b82f6'       # 연한 파란색
        }
        
        # 순서 정보를 session_state에 저장 (초기화)
        menu_order_key = "menu_display_order"
        if menu_order_key not in st.session_state:
            # 초기 순서 설정 (메뉴명 기준)
            menu_names = menu_df['메뉴명'].tolist()
            st.session_state[menu_order_key] = {name: idx + 1 for idx, name in enumerate(menu_names)}
        
        # 순서에 따라 정렬
        menu_df['순서'] = menu_df['메뉴명'].map(st.session_state[menu_order_key])
        menu_df = menu_df.sort_values('순서').reset_index(drop=True)
        
        # 메뉴 번호 매기기
        menu_df['번호'] = range(1, len(menu_df) + 1)
        
        # 메뉴 리스트 표시 (체크박스, 번호, 메뉴명, 판매가, 카테고리, 순서 변경 버튼, 삭제 버튼)
        st.markdown("**📋 메뉴 목록**")
        
        # 선택된 메뉴 인덱스 수집
        selected_indices = []
        
        # 헤더 행
        header_col1, header_col2, header_col3, header_col4, header_col5, header_col6, header_col7, header_col8 = st.columns([0.3, 0.5, 2.5, 1.5, 1.5, 1, 1, 1])
        with header_col1:
            st.write("**선택**")
        with header_col2:
            st.write("**번호**")
        with header_col3:
            st.write("**메뉴명**")
        with header_col4:
            st.write("**판매가**")
        with header_col5:
            st.write("**카테고리**")
        with header_col6:
            st.write("**위로**")
        with header_col7:
            st.write("**아래로**")
        with header_col8:
            st.write("**삭제**")
        
        st.markdown("---")
        
        # 카테고리별 배경색 CSS 스타일 정의 (더 진하고 넓게)
        st.markdown("""
        <style>
        .menu-row-wrapper {
            padding: 1rem 0.75rem;
            margin: 0.5rem 0;
            border-radius: 8px;
            border-left: 6px solid;
            min-height: 60px;
            display: flex;
            align-items: center;
        }
        .menu-row-대표메뉴 {
            background-color: #1e3a8a80;
            border-left-color: #1e40af;
        }
        .menu-row-주력메뉴 {
            background-color: #16653480;
            border-left-color: #15803d;
        }
        .menu-row-유인메뉴 {
            background-color: #ea580c80;
            border-left-color: #f97316;
        }
        .menu-row-보조메뉴 {
            background-color: #6b728080;
            border-left-color: #9ca3af;
        }
        .menu-row-기타메뉴 {
            background-color: #3b82f680;
            border-left-color: #60a5fa;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 각 메뉴 행
        for idx, row in menu_df.iterrows():
            # 카테고리별 배경색 설정
            category = row.get('category', '기타메뉴')
            category_class = category if category in category_colors else '기타메뉴'
            
            # 행 시작 - 배경색 적용
            st.markdown(f'<div class="menu-row-wrapper menu-row-{category_class}">', unsafe_allow_html=True)
            
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([0.3, 0.5, 2.5, 1.5, 1.5, 1, 1, 1])
            
            with col1:
                checkbox_key = f"menu_checkbox_{idx}"
                if st.checkbox("", key=checkbox_key, label_visibility="collapsed"):
                    selected_indices.append(idx)
            
            with col2:
                st.write(f"**{row['번호']}**")
            
            with col3:
                st.write(f"**{row['메뉴명']}**")
            
            with col4:
                st.write(f"{int(row['판매가']):,}원")
            
            with col5:
                # 카테고리 선택
                category_options = ['대표메뉴', '주력메뉴', '유인메뉴', '보조메뉴', '기타메뉴']
                current_category = category if category in category_options else '기타메뉴'
                category_key = f"category_select_{idx}"
                new_category = st.selectbox(
                    "",
                    category_options,
                    index=category_options.index(current_category) if current_category in category_options else 4,
                    key=category_key,
                    label_visibility="collapsed"
                )
                
                # 카테고리가 변경되었으면 업데이트
                if new_category != current_category:
                    try:
                        success, message = update_menu_category(row['메뉴명'], new_category)
                        if success:
                            try:
                                load_csv.clear()
                            except:
                                pass
                            st.rerun()
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"카테고리 업데이트 중 오류: {e}")
            
            with col6:
                # 위로 이동 버튼
                if idx > 0:
                    if st.button("⬆️", key=f"move_up_{idx}", help="위로 이동", use_container_width=True):
                        # 순서 변경: 현재 항목과 위 항목의 순서 교환
                        current_menu = row['메뉴명']
                        prev_menu = menu_df.iloc[idx - 1]['메뉴명']
                        current_order = st.session_state[menu_order_key][current_menu]
                        prev_order = st.session_state[menu_order_key][prev_menu]
                        st.session_state[menu_order_key][current_menu] = prev_order
                        st.session_state[menu_order_key][prev_menu] = current_order
                        try:
                            load_csv.clear()
                        except:
                            pass
                        st.rerun()
            
            with col7:
                # 아래로 이동 버튼
                if idx < len(menu_df) - 1:
                    if st.button("⬇️", key=f"move_down_{idx}", help="아래로 이동", use_container_width=True):
                        # 순서 변경: 현재 항목과 아래 항목의 순서 교환
                        current_menu = row['메뉴명']
                        next_menu = menu_df.iloc[idx + 1]['메뉴명']
                        current_order = st.session_state[menu_order_key][current_menu]
                        next_order = st.session_state[menu_order_key][next_menu]
                        st.session_state[menu_order_key][current_menu] = next_order
                        st.session_state[menu_order_key][next_menu] = current_order
                        try:
                            load_csv.clear()
                        except:
                            pass
                        st.rerun()
            
            with col8:
                # 개별 삭제 버튼
                if st.button("🗑️", key=f"delete_single_{idx}", help="삭제", use_container_width=True, type="secondary"):
                    menu_name = row['메뉴명']
                    try:
                        success, message, refs = delete_menu(menu_name)
                        if success:
                            st.success(f"✅ '{menu_name}' 메뉴가 삭제되었습니다!")
                            # session_state에서도 제거
                            if menu_name in st.session_state[menu_order_key]:
                                del st.session_state[menu_order_key][menu_name]
                            # 순서 재정렬
                            remaining_menus = list(st.session_state[menu_order_key].keys())
                            st.session_state[menu_order_key] = {name: idx + 1 for idx, name in enumerate(remaining_menus)}
                            # 캐시 클리어
                            try:
                                load_csv.clear()
                            except:
                                pass
                            st.rerun()
                        else:
                            st.error(message)
                            if refs:
                                st.info(f"**참조 정보:** {', '.join([f'{k}: {v}개' for k, v in refs.items()])}")
                    except Exception as e:
                        st.error(f"삭제 중 오류: {e}")
            
            # 행 종료
            st.markdown('</div>', unsafe_allow_html=True)
            
            if idx < len(menu_df) - 1:
                st.markdown("---")
        
        # 선택된 메뉴 일괄 삭제 버튼
        if selected_indices:
            st.markdown("---")
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button(f"🗑️ 선택한 {len(selected_indices)}개 삭제", type="primary", key="delete_selected_menus", use_container_width=True):
                    errors = []
                    success_count = 0
                    
                    for idx in selected_indices:
                        menu_name = menu_df.iloc[idx]['메뉴명']
                        try:
                            success, message, refs = delete_menu(menu_name)
                            if success:
                                success_count += 1
                                # session_state에서도 제거
                                if menu_name in st.session_state[menu_order_key]:
                                    del st.session_state[menu_order_key][menu_name]
                            else:
                                errors.append(f"{menu_name}: {message}")
                        except Exception as e:
                            errors.append(f"{menu_name}: {e}")
                    
                    if errors:
                        for error in errors:
                            st.error(error)
                    
                    if success_count > 0:
                        st.success(f"✅ {success_count}개 메뉴가 삭제되었습니다!")
                        # 순서 재정렬
                        remaining_menus = list(st.session_state[menu_order_key].keys())
                        st.session_state[menu_order_key] = {name: idx + 1 for idx, name in enumerate(remaining_menus)}
                        # 캐시 클리어
                        try:
                            load_csv.clear()
                        except:
                            pass
                        st.rerun()
        
        render_section_divider()
        
        # 수정 기능
        render_section_divider()
        st.markdown("**📝 메뉴 수정**")
        menu_list = menu_df['메뉴명'].tolist()
        selected_menu = st.selectbox(
            "수정할 메뉴 선택",
            ["선택하세요"] + menu_list,
            key="menu_edit_select"
        )
        
        if selected_menu != "선택하세요":
            menu_info = menu_df[menu_df['메뉴명'] == selected_menu].iloc[0]
            
            new_menu_name = st.text_input("메뉴명", value=menu_info['메뉴명'], key="menu_edit_name")
            new_price = st.number_input("판매가 (원)", min_value=0, value=int(menu_info['판매가']), step=1000, key="menu_edit_price")
            if st.button("✅ 수정", key="menu_edit_btn"):
                try:
                    success, message = update_menu(menu_info['메뉴명'], new_menu_name, new_price)
                    if success:
                        st.success(message)
                        try:
                            load_csv.clear()
                        except:
                            pass
                        st.rerun()
                    else:
                        st.error(message)
                except Exception as e:
                    st.error(f"수정 중 오류: {e}")
    else:
        st.info("등록된 메뉴가 없습니다.")

# 재료 등록 페이지
elif page == "재료 등록":
    render_page_header("재료 등록", "🥬")
    
    # 재료 입력 폼
    ingredient_result = render_ingredient_input()
    if len(ingredient_result) == 5:
        ingredient_name, unit, unit_price, order_unit, conversion_rate = ingredient_result
    else:
        # 기존 호환성 유지
        ingredient_name, unit, unit_price = ingredient_result[:3]
        order_unit = None
        conversion_rate = 1.0
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("💾 저장", type="primary", use_container_width=True):
            if not ingredient_name or ingredient_name.strip() == "":
                st.error("재료명을 입력해주세요.")
            elif unit_price <= 0:
                st.error("단가는 0보다 큰 값이어야 합니다.")
            else:
                try:
                    # 단위 자동 변환: kg → g, L → ml
                    final_unit = unit
                    final_unit_price = unit_price
                    
                    if unit == "kg":
                        # kg을 g로 변환: 1kg = 1000g, 단가는 1000으로 나눔
                        final_unit = "g"
                        final_unit_price = unit_price / 1000.0
                        st.info(f"💡 단위가 자동 변환되었습니다: {unit} → {final_unit} (단가: {unit_price:,.2f}원/{unit} → {final_unit_price:,.4f}원/{final_unit})")
                    elif unit == "L":
                        # L을 ml로 변환: 1L = 1000ml, 단가는 1000으로 나눔
                        final_unit = "ml"
                        final_unit_price = unit_price / 1000.0
                        st.info(f"💡 단위가 자동 변환되었습니다: {unit} → {final_unit} (단가: {unit_price:,.2f}원/{unit} → {final_unit_price:,.4f}원/{final_unit})")
                    
                    # 발주 단위도 변환 필요 시 조정
                    final_order_unit = order_unit if order_unit else final_unit
                    final_conversion_rate = conversion_rate
                    
                    # 발주 단위가 기본 단위와 다르면 변환 비율 적용
                    if final_order_unit != final_unit and final_conversion_rate == 1.0:
                        # 변환 비율이 설정되지 않았으면 기본값 1 유지
                        pass
                    
                    success, message = save_ingredient(ingredient_name, final_unit, final_unit_price, final_order_unit, final_conversion_rate)
                    if success:
                        unit_display = f"{final_unit_price:,.4f}원/{final_unit}"
                        if final_order_unit != final_unit:
                            unit_display += f" (발주: {final_order_unit}, 변환비율: {final_conversion_rate})"
                        st.success(f"재료가 저장되었습니다! ({ingredient_name}, {unit_display})")
                        # 재료 마스터 캐시 초기화 후 리스트 즉시 갱신
                        try:
                            load_csv.clear()
                        except Exception:
                            pass
                        st.rerun()
                    else:
                        st.error(message)
                except Exception as e:
                    st.error(f"저장 중 오류가 발생했습니다: {e}")
    
    render_section_divider()
    
    # 저장된 재료 표시 및 수정/삭제
    # 제목을 화이트 모드에서도 흰색으로 표시
    st.markdown("""
    <div style="margin: 2rem 0 1rem 0;">
        <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
            📋 등록된 재료 리스트
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가', '발주단위', '변환비율'])
    
    if not ingredient_df.empty:
        # 발주 단위 정보 처리
        if '발주단위' not in ingredient_df.columns:
            ingredient_df['발주단위'] = ingredient_df['단위']
        if '변환비율' not in ingredient_df.columns:
            ingredient_df['변환비율'] = 1.0
        
        ingredient_df['발주단위'] = ingredient_df['발주단위'].fillna(ingredient_df['단위'])
        ingredient_df['변환비율'] = ingredient_df['변환비율'].fillna(1.0)
        
        # 표시용 DataFrame 생성
        display_df = ingredient_df[['재료명', '단위', '발주단위', '단가', '변환비율']].copy()
        
        # 원본 발주단위 저장 (발주단위단가 계산용)
        display_df['원본발주단위'] = display_df['발주단위']
        
        # 발주단위 컬럼 포맷팅 (발주단위 + 변환 정보)
        def format_order_unit(row):
            order_unit = row['발주단위']
            base_unit = row['단위']
            conversion_rate = row['변환비율']
            
            if pd.isna(order_unit) or order_unit == base_unit or conversion_rate == 1.0:
                # 발주단위가 기본단위와 같거나 변환비율이 1이면 단위만 표시
                return order_unit if not pd.isna(order_unit) else base_unit
            else:
                # 1 발주단위 = 변환비율 기본단위 형식으로 표시
                return f"{order_unit} (1{order_unit} = {conversion_rate:,.0f}{base_unit})"
        
        display_df['발주단위'] = display_df.apply(format_order_unit, axis=1)
        
        # 1단위단가 (기본 단위 기준) - 소수점 1자리까지
        display_df['1단위단가'] = display_df.apply(
            lambda row: f"{row['단가']:,.1f}원/{row['단위']}",
            axis=1
        )
        
        # 발주단위단가 계산 (기본 단가 × 변환비율)
        display_df['발주단위단가'] = display_df.apply(
            lambda row: f"{(row['단가'] * row['변환비율']):,.1f}원/{row['원본발주단위']}",
            axis=1
        )
        
        # 표시할 컬럼 선택: 재료명, 단위, 발주단위, 1단위단가, 발주단위단가
        display_cols = ['재료명', '단위', '발주단위', '1단위단가', '발주단위단가']
        display_df = display_df[display_cols]
        
        # 표에 수정/삭제 버튼 추가
        st.write("**📋 등록된 재료 리스트** (표에서 바로 수정/삭제 가능)")
        
        # 표 헤더
        header_col_name, header_col_unit, header_col_order_unit, header_col_price1, header_col_price2, header_col_actions = st.columns([2, 1, 2, 1.5, 1.5, 1.5])
        with header_col_name:
            st.markdown("**재료명**")
        with header_col_unit:
            st.markdown("**단위**")
        with header_col_order_unit:
            st.markdown("**발주단위**")
        with header_col_price1:
            st.markdown("**1단위단가**")
        with header_col_price2:
            st.markdown("**발주단위단가**")
        with header_col_actions:
            st.markdown("**작업**")
        
        st.markdown("<hr style='margin: 0.5rem 0; border-color: rgba(255,255,255,0.2);'>", unsafe_allow_html=True)
        
        # 각 재료별로 수정/삭제 버튼이 있는 표 생성
        for idx, row in display_df.iterrows():
            ingredient_name = row['재료명']
            ingredient_info = ingredient_df[ingredient_df['재료명'] == ingredient_name].iloc[0]
            
            # 행 표시
            col_name, col_unit, col_order_unit, col_price1, col_price2, col_actions = st.columns([2, 1, 2, 1.5, 1.5, 1.5])
            
            with col_name:
                st.write(f"**{row['재료명']}**")
            with col_unit:
                st.write(row['단위'])
            with col_order_unit:
                st.write(row['발주단위'])
            with col_price1:
                st.write(row['1단위단가'])
            with col_price2:
                st.write(row['발주단위단가'])
            with col_actions:
                # 수정/삭제 버튼
                edit_col, delete_col = st.columns(2)
                with edit_col:
                    if st.button("✏️", key=f"edit_{ingredient_name}", help="수정"):
                        st.session_state[f'editing_{ingredient_name}'] = True
                        st.rerun()
                with delete_col:
                    if st.button("🗑️", key=f"delete_{ingredient_name}", help="삭제"):
                        st.session_state[f'deleting_{ingredient_name}'] = True
                        st.rerun()
            
            # 수정 모드
            if st.session_state.get(f'editing_{ingredient_name}', False):
                with st.expander(f"✏️ {ingredient_name} 수정", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_ingredient_name = st.text_input("재료명", value=ingredient_info['재료명'], key=f"edit_name_{ingredient_name}")
                        new_unit = st.selectbox(
                            "기본 단위",
                            options=["g", "ml", "ea", "개", "kg", "L"],
                            index=["g", "ml", "ea", "개", "kg", "L"].index(ingredient_info['단위']) if ingredient_info['단위'] in ["g", "ml", "ea", "개", "kg", "L"] else 0,
                            key=f"edit_unit_{ingredient_name}"
                        )
                        new_unit_price = st.number_input("단가 (원/기본단위)", min_value=0.0, value=float(ingredient_info['단가']), step=100.0, key=f"edit_price_{ingredient_name}")
                    
                    with col2:
                        new_order_unit = st.selectbox(
                            "발주 단위",
                            options=["", "g", "ml", "ea", "개", "kg", "L", "박스", "봉지"],
                            index=["", "g", "ml", "ea", "개", "kg", "L", "박스", "봉지"].index(ingredient_info.get('발주단위', '')) if ingredient_info.get('발주단위', '') in ["", "g", "ml", "ea", "개", "kg", "L", "박스", "봉지"] else 0,
                            key=f"edit_order_unit_{ingredient_name}"
                        )
                        new_conversion_rate = st.number_input(
                            "변환 비율 (1 발주단위 = ? 기본단위)",
                            min_value=0.0,
                            value=float(ingredient_info.get('변환비율', 1.0)),
                            step=0.1,
                            format="%.2f",
                            key=f"edit_conversion_{ingredient_name}"
                        )
                    
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.button("💾 저장", key=f"save_edit_{ingredient_name}", type="primary"):
                            try:
                                # 단위 자동 변환: kg → g, L → ml
                                final_unit = new_unit
                                final_unit_price = new_unit_price
                                
                                if new_unit == "kg":
                                    final_unit = "g"
                                    final_unit_price = new_unit_price / 1000.0
                                elif new_unit == "L":
                                    final_unit = "ml"
                                    final_unit_price = new_unit_price / 1000.0
                                
                                final_order_unit = new_order_unit if new_order_unit else final_unit
                                
                                # update_ingredient 함수는 기존 함수이므로 발주단위와 변환비율을 지원하도록 수정 필요
                                # 일단 기본 정보만 업데이트
                                success, message = update_ingredient(ingredient_info['재료명'], new_ingredient_name, final_unit, final_unit_price)
                                if success:
                                    # 발주단위와 변환비율은 별도로 업데이트 필요
                                    from src.storage_supabase import get_supabase_client, get_current_store_id
                                    supabase = get_supabase_client()
                                    store_id = get_current_store_id()
                                    if supabase and store_id:
                                        # 재료 ID 찾기
                                        ing_result = supabase.table("ingredients").select("id").eq("store_id", store_id).eq("name", new_ingredient_name).execute()
                                        if ing_result.data:
                                            supabase.table("ingredients").update({
                                                "order_unit": final_order_unit,
                                                "conversion_rate": float(new_conversion_rate)
                                            }).eq("id", ing_result.data[0]['id']).execute()
                                    
                                    st.session_state[f'editing_{ingredient_name}'] = False
                                    st.cache_data.clear()
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                            except Exception as e:
                                st.error(f"수정 중 오류: {e}")
                    
                    with col_cancel:
                        if st.button("❌ 취소", key=f"cancel_edit_{ingredient_name}"):
                            st.session_state[f'editing_{ingredient_name}'] = False
                            st.rerun()
            
            # 삭제 확인 모드
            if st.session_state.get(f'deleting_{ingredient_name}', False):
                with st.expander(f"🗑️ {ingredient_name} 삭제 확인", expanded=True):
                    st.warning(f"⚠️ '{ingredient_name}' 재료를 삭제하시겠습니까?")
                    col_del, col_cancel_del = st.columns(2)
                    with col_del:
                        if st.button("✅ 삭제 확인", key=f"confirm_delete_{ingredient_name}", type="primary"):
                            try:
                                success, message, refs = delete_ingredient(ingredient_name)
                                if success:
                                    st.session_state[f'deleting_{ingredient_name}'] = False
                                    st.cache_data.clear()
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                                    if refs:
                                        st.info(f"**참조 정보:** {', '.join([f'{k}: {v}개' for k, v in refs.items()])}")
                            except Exception as e:
                                st.error(f"삭제 중 오류: {e}")
                    
                    with col_cancel_del:
                        if st.button("❌ 취소", key=f"cancel_delete_{ingredient_name}"):
                            st.session_state[f'deleting_{ingredient_name}'] = False
                            st.rerun()
            
            # 구분선
            st.markdown("<hr style='margin: 0.5rem 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
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
    
    render_section_divider()
    
    # 일괄 입력 전용 폼
    st.subheader("📝 레시피 일괄 등록")
    st.info("💡 한 메뉴에 여러 재료를 한 번에 등록할 수 있습니다. (최대 30개 재료)")
    
    if not menu_list:
        st.warning("먼저 메뉴를 등록해주세요.")
    elif not ingredient_list:
        st.warning("먼저 재료를 등록해주세요.")
    else:
        # 메뉴 선택
        selected_menu = st.selectbox(
            "메뉴 선택",
            options=menu_list,
            key="batch_recipe_menu"
        )
        
        # 등록할 재료 개수 선택 (최대 30개)
        ingredient_count = st.number_input(
            "등록할 재료 개수",
            min_value=1,
            max_value=30,
            value=10,
            step=1,
            key="batch_recipe_count"
        )
        
        st.markdown("---")
        st.write(f"**📋 총 {ingredient_count}개 재료 입력**")
        
        # 재료 정보를 딕셔너리로 변환 (검색 및 단위/단가 조회용)
        ingredient_info_dict = {}
        if not ingredient_df.empty:
            for _, row in ingredient_df.iterrows():
                ingredient_info_dict[row['재료명']] = {
                    '단위': row.get('단위', ''),
                    '단가': float(row.get('단가', 0))
                }
        
        # 각 재료별 입력 필드 (재료명, 기준단위, 사용량, 사용단가)
        recipe_data = []
        
        # 컴팩트 스타일 CSS 추가 (세로 구분선 포함, 엑셀처럼 오밀조밀하게)
        st.markdown("""
        <style>
        .compact-recipe-row {
            margin: 0.05rem 0 !important;
            padding: 0.1rem 0 !important;
        }
        /* 입력 필드 높이 최소화 */
        .compact-recipe-row [data-testid="stTextInput"] {
            margin-bottom: 0.1rem !important;
        }
        .compact-recipe-row [data-testid="stTextInput"] > div > div {
            padding-top: 0.1rem !important;
            padding-bottom: 0.1rem !important;
            min-height: 28px !important;
            height: 28px !important;
        }
        .compact-recipe-row [data-testid="stTextInput"] input {
            padding: 0.2rem 0.5rem !important;
            font-size: 0.85rem !important;
            line-height: 1.2 !important;
        }
        .compact-recipe-row [data-testid="stSelectbox"] {
            margin-bottom: 0.1rem !important;
        }
        .compact-recipe-row [data-testid="stSelectbox"] > div > div {
            padding-top: 0.1rem !important;
            padding-bottom: 0.1rem !important;
            min-height: 28px !important;
            height: 28px !important;
        }
        .compact-recipe-row [data-testid="stSelectbox"] select {
            padding: 0.2rem 0.5rem !important;
            font-size: 0.85rem !important;
            line-height: 1.2 !important;
        }
        .compact-recipe-row [data-testid="stNumberInput"] {
            margin-bottom: 0.1rem !important;
        }
        .compact-recipe-row [data-testid="stNumberInput"] > div > div {
            padding-top: 0.1rem !important;
            padding-bottom: 0.1rem !important;
            min-height: 28px !important;
            height: 28px !important;
        }
        .compact-recipe-row [data-testid="stNumberInput"] input {
            padding: 0.2rem 0.5rem !important;
            font-size: 0.85rem !important;
            line-height: 1.2 !important;
        }
        /* 텍스트 표시 영역도 컴팩트하게 */
        .compact-recipe-row div[style*="margin-top: 0.5rem"] {
            margin-top: 0.2rem !important;
            margin-bottom: 0.1rem !important;
            font-size: 0.85rem !important;
            line-height: 1.3 !important;
        }
        /* 세로 구분선: 컬럼 사이에 얇은 선 표시 */
        .compact-recipe-row > div[data-testid="column"] {
            border-right: 1px solid rgba(148, 163, 184, 0.35);
            padding-right: 0.3rem;
            padding-left: 0.3rem;
        }
        .compact-recipe-row > div[data-testid="column"]:last-child {
            border-right: none;
        }
        /* 컬럼 간격 최소화 */
        .compact-recipe-row [data-testid="column"] {
            padding-left: 0.2rem !important;
            padding-right: 0.2rem !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 헤더 행
        header_col1, header_col2, header_col3, header_col4 = st.columns([3, 1.5, 2, 2])
        with header_col1:
            st.markdown("**재료명** (검색 가능)")
        with header_col2:
            st.markdown("**기준단위**")
        with header_col3:
            st.markdown("**사용량**")
        with header_col4:
            st.markdown("**사용단가**")
        
        st.markdown("<hr style='margin: 0.1rem 0; border-color: rgba(255,255,255,0.1); border-width: 0.5px;'>", unsafe_allow_html=True)
        
        for i in range(ingredient_count):
            # 컴팩트 행 컨테이너
            with st.container():
                st.markdown('<div class="compact-recipe-row">', unsafe_allow_html=True)
                col1, col2, col3, col4 = st.columns([3, 1.5, 2, 2])
                
                with col1:
                    # 재료 검색 기능
                    search_key = f"recipe_search_{i}"
                    search_term = st.text_input(
                        "",
                        key=search_key,
                        placeholder="🔍 재료명 검색...",
                        label_visibility="collapsed"
                    )
                    
                    # 검색어로 필터링된 재료 목록 (단위 정보 포함)
                    if search_term and search_term.strip():
                        filtered_ingredients = [ing for ing in ingredient_list if search_term.lower() in ing.lower()]
                        if not filtered_ingredients:
                            filtered_ingredients = ingredient_list
                    else:
                        filtered_ingredients = ingredient_list
                    
                    # 재료 선택 옵션에 단위 정보 표시
                    ingredient_options = []
                    if '발주단위' in ingredient_df.columns:
                        for ing in filtered_ingredients:
                            ing_row = ingredient_df[ingredient_df['재료명'] == ing]
                            if not ing_row.empty:
                                unit = ing_row.iloc[0].get('단위', '')
                                order_unit = ing_row.iloc[0].get('발주단위', unit)
                                if order_unit != unit:
                                    ingredient_options.append(f"{ing} ({unit} / 발주: {order_unit})")
                                else:
                                    ingredient_options.append(f"{ing} ({unit})")
                            else:
                                ingredient_options.append(ing)
                    else:
                        ingredient_options = filtered_ingredients
                    
                    # 재료 선택 (필터링된 목록에서)
                    ingredient_key = f"batch_recipe_ingredient_{i}"
                    selected_ingredient_option = st.selectbox(
                        "",
                        options=ingredient_options,
                        key=ingredient_key,
                        index=None,
                        label_visibility="collapsed"
                    )
                    
                    # 선택된 옵션에서 재료명 추출
                    selected_ingredient = selected_ingredient_option.split(" (")[0] if selected_ingredient_option and " (" in selected_ingredient_option else selected_ingredient_option
                
                with col2:
                    # 기준단위 (자동 표시, 발주 단위도 함께 표시)
                    if selected_ingredient and selected_ingredient in ingredient_info_dict:
                        unit = ingredient_info_dict[selected_ingredient]['단위']
                        # 발주 단위 정보 가져오기
                        if '발주단위' in ingredient_df.columns:
                            ing_row = ingredient_df[ingredient_df['재료명'] == selected_ingredient]
                            if not ing_row.empty:
                                order_unit = ing_row.iloc[0].get('발주단위', unit)
                                if order_unit != unit:
                                    unit_display = f"{unit} / 발주: {order_unit}"
                                else:
                                    unit_display = unit
                            else:
                                unit_display = unit
                        else:
                            unit_display = unit
                        st.markdown(f"<div style='margin-top: 0.2rem; margin-bottom: 0.1rem; font-size: 0.85rem;'><strong>{unit_display}</strong></div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='margin-top: 0.2rem; margin-bottom: 0.1rem; font-size: 0.85rem;'>-</div>", unsafe_allow_html=True)
                
                with col3:
                    # 사용량 입력
                    quantity_key = f"batch_recipe_quantity_{i}"
                    quantity = st.number_input(
                        "",
                        min_value=0.0,
                        value=0.0,
                        step=0.1,
                        format="%.2f",
                        key=quantity_key,
                        label_visibility="collapsed"
                    )
                
                with col4:
                    # 사용단가 (자동 계산: 사용량 × 1단위 단가)
                    if selected_ingredient and selected_ingredient in ingredient_info_dict and quantity > 0:
                        unit_price = ingredient_info_dict[selected_ingredient]['단가']
                        total_price = quantity * unit_price
                        st.markdown(f"<div style='margin-top: 0.2rem; margin-bottom: 0.1rem; font-size: 0.85rem;'><strong>{total_price:,.1f}원</strong></div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='margin-top: 0.2rem; margin-bottom: 0.1rem; font-size: 0.85rem;'>-</div>", unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # 유효한 데이터만 수집
                if selected_ingredient and quantity > 0:
                    unit = ingredient_info_dict.get(selected_ingredient, {}).get('단위', '')
                    unit_price = ingredient_info_dict.get(selected_ingredient, {}).get('단가', 0)
                    total_price = quantity * unit_price
                    recipe_data.append({
                        'ingredient': selected_ingredient,
                        'quantity': quantity,
                        'unit': unit,
                        'total_price': total_price
                    })
                
                # 마지막 행이 아니면 얇은 구분선
                if i < ingredient_count - 1:
                    st.markdown("<hr style='margin: 0.05rem 0; border-color: rgba(255,255,255,0.05); border-width: 0.5px;'>", unsafe_allow_html=True)
        
        # 조리방법 입력 필드
        render_section_divider()
        st.markdown("**👨‍🍳 조리방법**")
        cooking_method = st.text_area(
            "조리방법을 입력하세요 (줄글로 음식 만드는 방법을 적어주세요)",
            height=150,
            placeholder="예: 1. 재료를 준비합니다.\n2. 팬에 기름을 두르고 재료를 볶습니다.\n3. 물을 넣고 끓입니다.\n4. 간을 맞춰 완성합니다.",
            key="cooking_method_input"
        )
        
        render_section_divider()
        
        # 입력 요약 표시
        if recipe_data:
            st.write("**📊 입력 요약**")
            summary_data = []
            for item in recipe_data:
                summary_data.append({
                    '재료명': item['ingredient'],
                    '기준단위': item['unit'],
                    '사용량': f"{item['quantity']:.2f}",
                    '사용단가': f"{item['total_price']:,.1f}원"
                })
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            st.markdown(f"**총 {len(recipe_data)}개 재료**")
        
        # 일괄 저장 버튼 (항상 표시)
        render_section_divider()
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("💾 일괄 저장", type="primary", use_container_width=True):
                if not recipe_data:
                    st.error("⚠️ 저장할 재료가 없습니다. 재료명과 사용량을 입력해주세요.")
                else:
                    errors = []
                    success_count = 0
                    
                    # 재료 저장
                    for item in recipe_data:
                        try:
                            save_recipe(selected_menu, item['ingredient'], item['quantity'])
                            success_count += 1
                        except Exception as e:
                            errors.append(f"{item['ingredient']}: {e}")
                    
                    # 조리방법 저장 (입력된 경우)
                    if cooking_method and cooking_method.strip():
                        try:
                            success, message = update_menu_cooking_method(selected_menu, cooking_method)
                            if not success:
                                errors.append(f"조리방법 저장 실패: {message}")
                        except Exception as e:
                            errors.append(f"조리방법 저장 중 오류: {e}")
                    
                    if errors:
                        for error in errors:
                            st.error(error)
                    
                    if success_count > 0:
                        success_msg = f"✅ {success_count}개 레시피가 저장되었습니다!"
                        if cooking_method and cooking_method.strip():
                            success_msg += " (조리방법도 함께 저장되었습니다.)"
                        st.success(success_msg)
                        st.balloons()
                        # 레시피 데이터 캐시 초기화 후 리스트 즉시 갱신
                        try:
                            load_csv.clear()
                        except Exception:
                            pass
                        st.rerun()
    
    render_section_divider()
    
    # 레시피 검색 및 수정 (등록된 레시피 헤더 제거, 메뉴별 편집 UI만 제공)
    recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
    
    if not recipe_df.empty:
        # 레시피가 있는 메뉴 목록 추출
        menus_with_recipes = recipe_df['메뉴명'].unique().tolist()
        
        if menus_with_recipes:
            # 메뉴 필터 (레시피가 있는 메뉴만 표시)
            render_section_header("레시피 검색 및 수정", "🔍")
            filter_menu = st.selectbox(
                "메뉴 선택",
                options=menus_with_recipes,
                key="recipe_filter_menu",
                index=0 if menus_with_recipes else None
            )
            
            # 선택한 메뉴의 레시피만 필터링
            display_recipe_df = recipe_df[recipe_df['메뉴명'] == filter_menu].copy()
            
            if not display_recipe_df.empty:
                # 재료 정보와 조인하여 단위 및 단가 표시
                display_recipe_df = pd.merge(
                    display_recipe_df,
                    ingredient_df[['재료명', '단위', '단가']],
                    on='재료명',
                    how='left'
                )
                
                # 원가 계산 (이 메뉴의 원가)
                menu_cost_df = calculate_menu_cost(menu_df, recipe_df, ingredient_df)
                menu_cost_info = menu_cost_df[menu_cost_df['메뉴명'] == filter_menu]
                
                # 메뉴 정보 가져오기 (판매가, 조리방법)
                menu_info = menu_df[menu_df['메뉴명'] == filter_menu]
                menu_price = int(menu_info.iloc[0]['판매가']) if not menu_info.empty else 0
                
                # 조리방법 가져오기 (menu_master에서)
                cooking_method_text = ""
                try:
                    from src.auth import get_supabase_client, get_current_store_id
                    supabase = get_supabase_client()
                    store_id = get_current_store_id()
                    if supabase and store_id:
                        menu_result = supabase.table("menu_master").select("cooking_method").eq("store_id", store_id).eq("name", filter_menu).execute()
                        if menu_result.data and menu_result.data[0].get('cooking_method'):
                            cooking_method_text = menu_result.data[0]['cooking_method']
                except Exception:
                    pass
                
                # 원가 정보
                cost = int(menu_cost_info.iloc[0]['원가']) if not menu_cost_info.empty else 0
                cost_rate = float(menu_cost_info.iloc[0]['원가율']) if not menu_cost_info.empty else 0
                
                # 요리책 스타일 카드 레이아웃
                st.markdown(f"""
                <div style="border-radius: 16px; padding: 2rem; margin: 1rem 0 2rem 0;
                            background: linear-gradient(135deg, #1f2937 0%, #111827 60%, #020617 100%);
                            box-shadow: 0 12px 30px rgba(0,0,0,0.4); border: 2px solid rgba(148,163,184,0.3);">
                    <div style="text-align: center; margin-bottom: 2rem;">
                        <h2 style="margin: 0 0 0.5rem 0; color: #ffffff; font-weight: 800; font-size: 2rem; letter-spacing: 1px;">
                            🍽️ {filter_menu}
                        </h2>
                        <div style="display: flex; justify-content: center; gap: 2rem; margin-top: 1.5rem; flex-wrap: wrap;">
                            <div style="background: rgba(59, 130, 246, 0.2); padding: 0.8rem 1.5rem; border-radius: 8px; border: 1px solid rgba(59, 130, 246, 0.5);">
                                <div style="color: #93c5fd; font-size: 0.85rem; margin-bottom: 0.3rem;">판매가</div>
                                <div style="color: #ffffff; font-size: 1.3rem; font-weight: 700;">{menu_price:,}원</div>
                            </div>
                            <div style="background: rgba(239, 68, 68, 0.2); padding: 0.8rem 1.5rem; border-radius: 8px; border: 1px solid rgba(239, 68, 68, 0.5);">
                                <div style="color: #fca5a5; font-size: 0.85rem; margin-bottom: 0.3rem;">원가</div>
                                <div style="color: #ffffff; font-size: 1.3rem; font-weight: 700;">{cost:,}원</div>
                            </div>
                            <div style="background: rgba(234, 179, 8, 0.2); padding: 0.8rem 1.5rem; border-radius: 8px; border: 1px solid rgba(234, 179, 8, 0.5);">
                                <div style="color: #fde047; font-size: 0.85rem; margin-bottom: 0.3rem;">원가율</div>
                                <div style="color: #ffffff; font-size: 1.3rem; font-weight: 700;">{cost_rate:.1f}%</div>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 구성 재료 및 사용량 (엑셀처럼 깔끔하게)
                st.markdown("**📋 구성 재료 및 사용량**")
                
                # 엑셀 스타일 테이블 데이터 준비
                table_data = []
                for idx, row in display_recipe_df.iterrows():
                    ing_name = row['재료명']
                    unit = row['단위'] if pd.notna(row['단위']) else ""
                    current_qty = float(row['사용량'])
                    unit_price = float(row['단가']) if pd.notna(row['단가']) else 0
                    ingredient_cost = current_qty * unit_price
                    
                    table_data.append({
                        '재료명': ing_name,
                        '기준단위': unit,
                        '사용량': f"{current_qty:.2f}",
                        '1단위 단가': f"{unit_price:,.1f}원",
                        '재료비': f"{ingredient_cost:,.1f}원"
                    })
                
                # 엑셀 스타일 테이블 표시
                ingredients_table_df = pd.DataFrame(table_data)
                st.dataframe(ingredients_table_df, use_container_width=True, hide_index=True)
                
                # 조리방법 표시 (구성 재료 다음에 배치)
                render_section_divider()
                st.markdown("**👨‍🍳 조리방법**")
                if cooking_method_text:
                    st.markdown(f"""
                    <div style="background: rgba(30, 41, 59, 0.5); padding: 1.5rem; border-radius: 12px; 
                                border-left: 4px solid #667eea; margin: 1rem 0;">
                        <div style="color: #e5e7eb; font-size: 1rem; line-height: 1.8; white-space: pre-wrap;">
                            {cooking_method_text.replace(chr(10), '<br>')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("조리방법이 등록되지 않았습니다. 레시피 일괄 등록에서 조리방법을 입력해주세요.")
                
                render_section_divider()
                
                # 각 재료별 사용량 수정/삭제 UI
                st.markdown("**✏️ 재료 사용량 수정 및 삭제**")
                
                # 컴팩트 스타일 CSS 추가 (세로 구분선 포함)
                st.markdown("""
                <style>
                .compact-edit-row {
                    margin: 0.2rem 0 !important;
                    padding: 0.3rem 0 !important;
                }
                .compact-edit-row [data-testid="stNumberInput"] > div > div {
                    padding-top: 0.3rem !important;
                    padding-bottom: 0.3rem !important;
                }
                .compact-edit-row [data-testid="stButton"] {
                    margin-top: 0.2rem !important;
                }
                .compact-edit-row [data-testid="stButton"] > button {
                    padding: 0.3rem 0.5rem !important;
                    font-size: 0.85rem !important;
                    height: auto !important;
                }
                /* 세로 구분선: 컬럼 사이에 얇은 선 표시 */
                .compact-edit-row > div[data-testid="column"] {
                    border-right: 1px solid rgba(148, 163, 184, 0.35);
                    padding-right: 0.4rem;
                }
                .compact-edit-row > div[data-testid="column"]:last-child {
                    border-right: none;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # 테이블 헤더
                header_col1, header_col2, header_col3, header_col4, header_col5 = st.columns([2.5, 1, 2, 1.2, 1.2])
                with header_col1:
                    st.markdown("**재료명**")
                with header_col2:
                    st.markdown("**단위**")
                with header_col3:
                    st.markdown("**사용량**")
                with header_col4:
                    st.markdown("**수정**")
                with header_col5:
                    st.markdown("**삭제**")
                
                st.markdown("<hr style='margin: 0.3rem 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
                
                # 각 재료별 사용량 수정/삭제 UI (표 형태)
                for idx, row in display_recipe_df.iterrows():
                    ing_name = row['재료명']
                    unit = row['단위'] if pd.notna(row['단위']) else ""
                    current_qty = float(row['사용량'])
                    
                    # 컴팩트 행 컨테이너
                    with st.container():
                        st.markdown('<div class="compact-edit-row">', unsafe_allow_html=True)
                        col1, col2, col3, col4, col5 = st.columns([2.5, 1, 2, 1.2, 1.2])
                        
                        with col1:
                            st.markdown(f"<div style='margin-top: 0.5rem;'><strong>{ing_name}</strong></div>", unsafe_allow_html=True)
                        with col2:
                            st.markdown(f"<div style='margin-top: 0.5rem;'>{unit}</div>", unsafe_allow_html=True)
                        with col3:
                            new_qty = st.number_input(
                                "",
                                min_value=0.0,
                                value=current_qty,
                                step=0.1,
                                format="%.2f",
                                key=f"edit_recipe_qty_{filter_menu}_{ing_name}",
                                label_visibility="collapsed"
                            )
                        with col4:
                            if st.button("💾 수정", key=f"save_recipe_{filter_menu}_{ing_name}", use_container_width=True):
                                if new_qty <= 0:
                                    st.error("사용량은 0보다 큰 값이어야 합니다.")
                                else:
                                    try:
                                        save_recipe(filter_menu, ing_name, new_qty)
                                        st.success(
                                            f"'{filter_menu}' - '{ing_name}' 사용량이 {new_qty:.2f}{unit} 으로 수정되었습니다."
                                        )
                                        try:
                                            load_csv.clear()
                                        except Exception:
                                            pass
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"사용량 수정 중 오류: {e}")
                        with col5:
                            if st.button("🗑️ 삭제", key=f"delete_recipe_{filter_menu}_{ing_name}", use_container_width=True):
                                try:
                                    success, msg = delete_recipe(filter_menu, ing_name)
                                    if success:
                                        st.success(f"'{filter_menu}' - '{ing_name}' 레시피가 삭제되었습니다.")
                                        try:
                                            load_csv.clear()
                                        except Exception:
                                            pass
                                        st.rerun()
                                    else:
                                        st.error(msg)
                                except Exception as e:
                                    st.error(f"레시피 삭제 중 오류: {e}")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # 마지막 행이 아니면 얇은 구분선
                        if idx < len(display_recipe_df) - 1:
                            st.markdown("<hr style='margin: 0.2rem 0; border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
        else:
            st.info("등록된 레시피가 없습니다.")
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

# 실제 정산 페이지
elif page == "실제정산":
    render_page_header("실제 정산 (월별 실적)", "🧾")
    
    # 매출 데이터 로드 (일별 총매출)
    sales_df = load_csv('sales.csv', default_columns=['날짜', '매장', '총매출'])
    
    if sales_df.empty:
        st.info("저장된 매출 데이터가 없습니다. 먼저 매출 관리 페이지에서 일매출을 입력해주세요.")
    else:
        # 날짜 컬럼을 datetime으로 변환
        sales_df['날짜'] = pd.to_datetime(sales_df['날짜'])
        sales_df['연도'] = sales_df['날짜'].dt.year
        sales_df['월'] = sales_df['날짜'].dt.month
        
        # 사용 가능한 연/월 목록
        available_years = sorted(sales_df['연도'].unique().tolist(), reverse=True)
        
        from datetime import datetime
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        col1, col2 = st.columns(2)
        with col1:
            selected_year = st.selectbox(
                "정산 연도 선택",
                options=available_years,
                index=0 if current_year in available_years else 0,
                key="settlement_year",
            )
        
        # 선택한 연도의 사용 가능한 월만 표시
        available_months = sorted(
            sales_df[sales_df['연도'] == selected_year]['월'].unique().tolist()
        )
        if current_month in available_months:
            default_month_index = available_months.index(current_month)
        else:
            default_month_index = len(available_months) - 1
        
        with col2:
            selected_month = st.selectbox(
                "정산 월 선택",
                options=available_months,
                index=default_month_index,
                key="settlement_month",
            )
        
        # 선택한 연/월의 매출 합계 계산
        month_sales_df = sales_df[
            (sales_df['연도'] == selected_year) & (sales_df['월'] == selected_month)
        ].copy()
        
        if month_sales_df.empty:
            st.info(f"{selected_year}년 {selected_month}월에 해당하는 매출 데이터가 없습니다.")
        else:
            month_total_sales = float(month_sales_df['총매출'].sum())
            
            render_section_divider()
            
            # 상단 요약 카드
            st.markdown(
                f"""
                <div class="info-box">
                    <strong>📅 정산 대상 기간</strong><br>
                    <span style="font-size: 0.9rem; opacity: 0.9;">
                        {selected_year}년 {selected_month}월의 실제 매출과 비용을 기준으로 정산합니다.
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("해당 월 총 매출", f"{month_total_sales:,.0f}원")
            # 비용/이익은 아래 입력값 기준으로 다시 표시
            
            # 기존 실제 정산 데이터 로드
            actual_df = load_csv(
                "actual_settlement.csv",
                default_columns=["연도", "월", "실제매출", "실제비용", "실제이익", "실제이익률"],
            )
            
            existing_row = None
            if not actual_df.empty:
                existing_row = actual_df[
                    (actual_df["연도"] == selected_year)
                    & (actual_df["월"] == selected_month)
                ]
                if not existing_row.empty:
                    existing_row = existing_row.iloc[0]
            
            render_section_divider()
            st.markdown("**💸 해당 월 실제 비용 입력 (5대 비용 항목별)**")
            
            # 5대 비용 항목 정의
            expense_categories = {
                '임차료': {'icon': '🏢', 'description': '임차료', 'type': 'fixed', 'fixed_items': ['임차료']},
                '인건비': {'icon': '👥', 'description': '인건비 관련 모든 비용', 'type': 'fixed', 'fixed_items': ['직원 실지급 인건비', '사회보험(직원+회사분 통합)', '원천징수(국세+지방세)', '퇴직급여 충당금', '보너스']},
                '재료비': {'icon': '🥬', 'description': '재료비 관련 모든 비용', 'type': 'variable'},
                '공과금': {'icon': '💡', 'description': '공과금 관련 모든 비용', 'type': 'mixed', 'fixed_items': ['전기', '가스', '수도']},
                '부가세&카드수수료': {'icon': '💳', 'description': '부가세 및 카드수수료 (매출 대비 비율)', 'type': 'rate', 'fixed_items': ['부가세', '카드수수료']}
            }
            
            # 세션 상태에 비용 항목별 세부 데이터 저장 및 고정 항목 초기화
            if f'actual_expense_items_{selected_year}_{selected_month}' not in st.session_state:
                expense_items = {cat: [] for cat in expense_categories.keys()}
                
                # 고정 항목 초기화
                # 임차료: 임차료 1개 항목
                if '임차료' in expense_items:
                    expense_items['임차료'] = [{'item_name': '임차료', 'amount': 0}]
                
                # 인건비: 5개 고정 항목
                if '인건비' in expense_items:
                    expense_items['인건비'] = [
                        {'item_name': '직원 실지급 인건비', 'amount': 0},
                        {'item_name': '사회보험(직원+회사분 통합)', 'amount': 0},
                        {'item_name': '원천징수(국세+지방세)', 'amount': 0},
                        {'item_name': '퇴직급여 충당금', 'amount': 0},
                        {'item_name': '보너스', 'amount': 0}
                    ]
                
                # 공과금: 전기, 가스, 수도 3개 고정 항목
                if '공과금' in expense_items:
                    expense_items['공과금'] = [
                        {'item_name': '전기', 'amount': 0},
                        {'item_name': '가스', 'amount': 0},
                        {'item_name': '수도', 'amount': 0}
                    ]
                
                # 부가세&카드수수료: 부가세, 카드수수료 2개 항목 (비율로 저장)
                if '부가세&카드수수료' in expense_items:
                    expense_items['부가세&카드수수료'] = [
                        {'item_name': '부가세', 'amount': 0.0},  # 비율(%)
                        {'item_name': '카드수수료', 'amount': 0.0}  # 비율(%)
                    ]
                
                st.session_state[f'actual_expense_items_{selected_year}_{selected_month}'] = expense_items
            else:
                expense_items = st.session_state[f'actual_expense_items_{selected_year}_{selected_month}']
                
                # 고정 항목이 없으면 초기화
                if '임차료' in expense_items and not expense_items['임차료']:
                    expense_items['임차료'] = [{'item_name': '임차료', 'amount': 0}]
                
                if '인건비' in expense_items:
                    fixed_items = ['직원 실지급 인건비', '사회보험(직원+회사분 통합)', '원천징수(국세+지방세)', '퇴직급여 충당금', '보너스']
                    existing_names = [item.get('item_name') for item in expense_items['인건비']]
                    for fixed_name in fixed_items:
                        if fixed_name not in existing_names:
                            expense_items['인건비'].append({'item_name': fixed_name, 'amount': 0})
                    # 순서 정렬
                    expense_items['인건비'] = sorted(
                        expense_items['인건비'],
                        key=lambda x: fixed_items.index(x['item_name']) if x['item_name'] in fixed_items else 999
                    )
                
                if '공과금' in expense_items:
                    fixed_items = ['전기', '가스', '수도']
                    existing_names = [item.get('item_name') for item in expense_items['공과금']]
                    # 고정 항목이 없으면 추가 (기존 가변 항목은 유지)
                    for fixed_name in fixed_items:
                        if fixed_name not in existing_names:
                            expense_items['공과금'].insert(0, {'item_name': fixed_name, 'amount': 0})
                    # 고정 항목을 상단에 정렬 (가변 항목은 하단)
                    fixed_items_list = [item for item in expense_items['공과금'] if item.get('item_name') in fixed_items]
                    variable_items_list = [item for item in expense_items['공과금'] if item.get('item_name') not in fixed_items]
                    # 고정 항목 순서 정렬
                    fixed_items_list = sorted(
                        fixed_items_list,
                        key=lambda x: fixed_items.index(x['item_name']) if x['item_name'] in fixed_items else 999
                    )
                    expense_items['공과금'] = fixed_items_list + variable_items_list
                
                if '부가세&카드수수료' in expense_items:
                    fixed_items = ['부가세', '카드수수료']
                    existing_names = [item.get('item_name') for item in expense_items['부가세&카드수수료']]
                    for fixed_name in fixed_items:
                        if fixed_name not in existing_names:
                            expense_items['부가세&카드수수료'].append({'item_name': fixed_name, 'amount': 0.0})
                    # 순서 정렬
                    expense_items['부가세&카드수수료'] = sorted(
                        expense_items['부가세&카드수수료'],
                        key=lambda x: fixed_items.index(x['item_name']) if x['item_name'] in fixed_items else 999
                    )
            
            # 한글 원화 변환 함수
            def format_korean_currency(amount):
                """숫자를 한글 원화로 변환"""
                if amount == 0:
                    return "0원"
                eok = amount // 100000000
                remainder = amount % 100000000
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
            category_totals = {}
            for category, info in expense_categories.items():
                # 카테고리 헤더
                col1, col2 = st.columns([3, 1])
                with col1:
                    header_color = "#ffffff"
                    st.markdown(f"""
                    <div style="margin: 1.5rem 0 0.5rem 0;">
                        <h3 style="color: {header_color}; font-weight: 600; margin: 0;">
                            {info['icon']} {category}
                        </h3>
                    </div>
                    """, unsafe_allow_html=True)
                    st.caption(f"{info['description']}")
                
                # 카테고리별 총액 계산
                if info['type'] == 'rate':
                    # 부가세&카드수수료: 비율 합계를 금액으로 변환
                    total_rate = sum(item.get('amount', 0) for item in expense_items[category])
                    category_total = (month_total_sales * total_rate / 100) if month_total_sales > 0 else 0
                else:
                    # 절대 금액
                    category_total = sum(item.get('amount', 0) for item in expense_items[category])
                
                category_totals[category] = category_total
                
                with col2:
                    if category_total > 0:
                        if info['type'] == 'rate':
                            total_rate = sum(item.get('amount', 0) for item in expense_items[category])
                            st.markdown(f"""
                            <div style="text-align: right; margin-top: 0.5rem; padding-top: 0.5rem;">
                                <strong style="color: #667eea; font-size: 1.1rem;">
                                    총 비율: {total_rate:.2f}%
                                </strong>
                                <div style="font-size: 0.85rem; color: #666;">
                                    ({category_total:,.0f}원)
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
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
                
                # 고정 항목인지 확인
                is_fixed = 'fixed_items' in info and (info['type'] == 'fixed' or info['type'] == 'rate')
                is_mixed = 'fixed_items' in info and info['type'] == 'mixed'
                
                # 항목 표시 및 수정
                if expense_items[category]:
                    # mixed 타입인 경우 고정 항목과 가변 항목 분리
                    if is_mixed:
                        fixed_items_names = info.get('fixed_items', [])
                        fixed_items_list = [item for item in expense_items[category] if item.get('item_name') in fixed_items_names]
                        variable_items_list = [item for item in expense_items[category] if item.get('item_name') not in fixed_items_names]
                        
                        # 고정 항목 먼저 표시
                        if fixed_items_list:
                            for idx, item in enumerate(fixed_items_list):
                                col_a, col_b, col_c = st.columns([3, 2, 1])
                                with col_a:
                                    st.write(f"**{item.get('item_name', '')}**")
                                with col_b:
                                    edit_amount_key = f"edit_amount_{category}_fixed_{item.get('item_name')}_{selected_year}_{selected_month}"
                                    edited_amount = st.number_input(
                                        "금액 (원)",
                                        min_value=0,
                                        value=int(item.get('amount', 0)),
                                        step=10000,
                                        format="%d",
                                        key=edit_amount_key,
                                    )
                                    if edited_amount != item.get('amount'):
                                        item['amount'] = edited_amount
                                        st.session_state[f'actual_expense_items_{selected_year}_{selected_month}'] = expense_items
                                with col_c:
                                    st.write("")  # 삭제 버튼 없음
                            
                            if variable_items_list:
                                st.markdown("---")
                                with st.expander(f"📋 추가 항목 ({len(variable_items_list)}개)", expanded=True):
                                    for idx, item in enumerate(variable_items_list):
                                        col_a, col_b, col_c = st.columns([3, 2, 1])
                                        with col_a:
                                            edit_key = f"edit_name_{category}_var_{idx}_{selected_year}_{selected_month}"
                                            if edit_key not in st.session_state:
                                                st.session_state[edit_key] = item.get('item_name', '')
                                            edited_name = st.text_input(
                                                "항목명",
                                                value=st.session_state[edit_key],
                                                key=edit_key,
                                            )
                                            if edited_name != item.get('item_name'):
                                                item['item_name'] = edited_name
                                                st.session_state[f'actual_expense_items_{selected_year}_{selected_month}'] = expense_items
                                        with col_b:
                                            edit_amount_key = f"edit_amount_{category}_var_{idx}_{selected_year}_{selected_month}"
                                            edited_amount = st.number_input(
                                                "금액 (원)",
                                                min_value=0,
                                                value=int(item.get('amount', 0)),
                                                step=10000,
                                                format="%d",
                                                key=edit_amount_key,
                                            )
                                            if edited_amount != item.get('amount'):
                                                item['amount'] = edited_amount
                                                st.session_state[f'actual_expense_items_{selected_year}_{selected_month}'] = expense_items
                                        with col_c:
                                            if st.button("🗑️", key=f"del_{category}_var_{idx}_{selected_year}_{selected_month}", help="삭제"):
                                                expense_items[category].remove(item)
                                                st.session_state[f'actual_expense_items_{selected_year}_{selected_month}'] = expense_items
                                                st.rerun()
                    else:
                        # 고정 항목 또는 가변 항목만 있는 경우
                        # 가변 항목(재료비 등)은 expander로 표시
                        if not is_fixed and expense_items[category]:
                            with st.expander(f"📋 입력된 항목 ({len(expense_items[category])}개)", expanded=True):
                                for idx, item in enumerate(expense_items[category]):
                                    col_a, col_b, col_c = st.columns([3, 2, 1])
                                    with col_a:
                                        # 수정 가능한 항목명
                                        edit_key = f"edit_name_{category}_{idx}_{selected_year}_{selected_month}"
                                        if edit_key not in st.session_state:
                                            st.session_state[edit_key] = item.get('item_name', '')
                                        edited_name = st.text_input(
                                            "항목명",
                                            value=st.session_state[edit_key],
                                            key=edit_key,
                                        )
                                        if edited_name != item.get('item_name'):
                                            item['item_name'] = edited_name
                                            st.session_state[f'actual_expense_items_{selected_year}_{selected_month}'] = expense_items
                                    
                                    with col_b:
                                        # 절대 금액 입력
                                        edit_amount_key = f"edit_amount_{category}_{idx}_{selected_year}_{selected_month}"
                                        edited_amount = st.number_input(
                                            "금액 (원)",
                                            min_value=0,
                                            value=int(item.get('amount', 0)),
                                            step=10000,
                                            format="%d",
                                            key=edit_amount_key,
                                        )
                                        
                                        # 변경된 값 저장
                                        if edited_amount != item.get('amount'):
                                            item['amount'] = edited_amount
                                            st.session_state[f'actual_expense_items_{selected_year}_{selected_month}'] = expense_items
                                    
                                    with col_c:
                                        if st.button("🗑️", key=f"del_{category}_{idx}_{selected_year}_{selected_month}", help="삭제"):
                                            expense_items[category].pop(idx)
                                            st.session_state[f'actual_expense_items_{selected_year}_{selected_month}'] = expense_items
                                            st.rerun()
                        elif is_fixed:
                            # 고정 항목은 expander 없이 직접 표시
                            for idx, item in enumerate(expense_items[category]):
                                col_a, col_b, col_c = st.columns([3, 2, 1])
                                with col_a:
                                    # 고정 항목: 항목명 표시만
                                    st.write(f"**{item.get('item_name', '')}**")
                                
                                with col_b:
                                    if info['type'] == 'rate':
                                        # 비율 입력
                                        edit_amount_key = f"edit_amount_{category}_{idx}_{selected_year}_{selected_month}"
                                        edited_rate = st.number_input(
                                            "매출 대비 비율 (%)",
                                            min_value=0.0,
                                            max_value=100.0,
                                            value=float(item.get('amount', 0)),
                                            step=0.1,
                                            format="%.2f",
                                            key=edit_amount_key,
                                        )
                                        
                                        # 변경된 값 저장
                                        if edited_rate != item.get('amount'):
                                            item['amount'] = edited_rate
                                            st.session_state[f'actual_expense_items_{selected_year}_{selected_month}'] = expense_items
                                        
                                        # 계산된 금액 표시
                                        calculated_amount = (month_total_sales * edited_rate / 100) if month_total_sales > 0 else 0
                                        st.caption(f"→ {calculated_amount:,.0f}원")
                                    else:
                                        # 절대 금액 입력
                                        edit_amount_key = f"edit_amount_{category}_{idx}_{selected_year}_{selected_month}"
                                        edited_amount = st.number_input(
                                            "금액 (원)",
                                            min_value=0,
                                            value=int(item.get('amount', 0)),
                                            step=10000,
                                            format="%d",
                                            key=edit_amount_key,
                                        )
                                        
                                        # 변경된 값 저장
                                        if edited_amount != item.get('amount'):
                                            item['amount'] = edited_amount
                                            st.session_state[f'actual_expense_items_{selected_year}_{selected_month}'] = expense_items
                                
                                with col_c:
                                    st.write("")  # 삭제 버튼 없음
                
                # 고정 항목이 아니거나 mixed 타입인 경우 새 항목 추가
                if not is_fixed or is_mixed:
                    with st.container():
                        st.markdown("---")
                        col1, col2, col3 = st.columns([3, 2, 1])
                        with col1:
                            new_item_name = st.text_input(
                                "항목명",
                                key=f"new_item_name_{category}_{selected_year}_{selected_month}",
                                placeholder="예: 월세, 관리비 등"
                            )
                        with col2:
                            new_item_amount = st.number_input(
                                "금액 (원)",
                                min_value=0,
                                value=0,
                                step=10000,
                                format="%d",
                                key=f"new_item_amount_{category}_{selected_year}_{selected_month}"
                            )
                        with col3:
                            st.write("")
                            st.write("")
                            if st.button("➕ 추가", key=f"add_{category}_{selected_year}_{selected_month}", use_container_width=True):
                                if new_item_name.strip():
                                    # mixed 타입인 경우 고정 항목 이름과 중복 체크
                                    if is_mixed:
                                        fixed_items_names = info.get('fixed_items', [])
                                        if new_item_name.strip() in fixed_items_names:
                                            st.error(f"'{new_item_name.strip()}'는 고정 항목입니다.")
                                        else:
                                            expense_items[category].append({
                                                'item_name': new_item_name.strip(),
                                                'amount': new_item_amount
                                            })
                                            st.session_state[f'actual_expense_items_{selected_year}_{selected_month}'] = expense_items
                                            st.rerun()
                                    else:
                                        expense_items[category].append({
                                            'item_name': new_item_name.strip(),
                                            'amount': new_item_amount
                                        })
                                        st.session_state[f'actual_expense_items_{selected_year}_{selected_month}'] = expense_items
                                        st.rerun()
                                else:
                                    st.error("항목명을 입력해주세요.")
            
            # 전체 비용 합계 계산
            total_actual_cost = sum(category_totals.values())
            
            # 이익 및 이익률 계산
            actual_sales = month_total_sales
            actual_profit = actual_sales - total_actual_cost
            profit_margin = (actual_profit / actual_sales * 100) if actual_sales > 0 else 0.0
            
            render_section_divider()
            
            # 요약 정보
            st.markdown("**📊 비용 합계 요약**")
            summary_col1, summary_col2, summary_col3 = st.columns(3)
            with summary_col1:
                st.metric("실제 총 비용", f"{total_actual_cost:,.0f}원")
            with summary_col2:
                st.metric("실제 이익", f"{actual_profit:,.0f}원")
            with summary_col3:
                st.metric("실제 이익률", f"{profit_margin:,.1f}%")
            
            # 카테고리별 비용 요약 테이블
            cost_summary_data = []
            for category, total in category_totals.items():
                cost_summary_data.append({
                    '비용 항목': category,
                    '금액': f"{total:,.0f}원",
                    '비율': f"{(total / total_actual_cost * 100):.1f}%" if total_actual_cost > 0 else "0.0%"
                })
            cost_summary_df = pd.DataFrame(cost_summary_data)
            st.dataframe(cost_summary_df, use_container_width=True, hide_index=True)
            
            render_section_divider()
            
            # 저장 버튼
            save_col, _ = st.columns([1, 4])
            with save_col:
                if st.button("💾 실제 정산 저장", type="primary", use_container_width=True):
                    try:
                        from src.storage_supabase import save_actual_settlement
                        
                        success = save_actual_settlement(
                            selected_year,
                            selected_month,
                            actual_sales,
                            total_actual_cost,
                            actual_profit,
                            profit_margin,
                        )
                        if success:
                            st.success(
                                f"{selected_year}년 {selected_month}월 실제 정산 데이터가 저장되었습니다."
                            )
                            try:
                                load_csv.clear()
                            except Exception:
                                pass
                            st.rerun()
                    except Exception as e:
                        st.error(f"실제 정산 데이터 저장 중 오류가 발생했습니다: {e}")
            
            # 하단에 기존 정산 이력 표시
            render_section_divider()
            st.markdown("**📜 실제 정산 이력 (월별)**")
            history_df = load_csv(
                "actual_settlement.csv",
                default_columns=["연도", "월", "실제매출", "실제비용", "실제이익", "실제이익률"],
            )
            if not history_df.empty:
                history_df = history_df.sort_values(["연도", "월"], ascending=[False, False])
                display_history = history_df.copy()
                display_history["실제매출"] = display_history["실제매출"].apply(
                    lambda x: f"{float(x):,.0f}원"
                )
                display_history["실제비용"] = display_history["실제비용"].apply(
                    lambda x: f"{float(x):,.0f}원"
                )
                display_history["실제이익"] = display_history["실제이익"].apply(
                    lambda x: f"{float(x):,.0f}원"
                )
                display_history["실제이익률"] = display_history["실제이익률"].apply(
                    lambda x: f"{float(x):,.1f}%"
                )
                st.dataframe(display_history, use_container_width=True, hide_index=True)
            else:
                st.info("저장된 실제 정산 데이터가 없습니다.")

# 판매 관리 페이지 (분석 전용)
elif page == "판매 관리":
    render_page_header("판매 관리", "📦")
    
    from datetime import datetime, timedelta
    
    # 메뉴 목록 로드
    menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
    daily_sales_df = load_csv('daily_sales_items.csv', default_columns=['날짜', '메뉴명', '판매수량'])
    recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
    ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가'])
    
    if daily_sales_df.empty or menu_df.empty:
        st.info("판매 분석을 위해서는 메뉴와 일일 판매 데이터가 필요합니다.")
    else:
        # 날짜를 datetime으로 변환
        daily_sales_df['날짜'] = pd.to_datetime(daily_sales_df['날짜'])
        
        # 사용 가능한 날짜 범위
        min_date = daily_sales_df['날짜'].min().date()
        max_date = daily_sales_df['날짜'].max().date()
        
        # 기간 선택 필터 (전역 사용)
        st.markdown("""
        <div style="margin: 2rem 0 1rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                📅 분석 기간 선택
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            analysis_start_date = st.date_input(
                "시작일",
                value=min_date,
                min_value=min_date,
                max_value=max_date,
                key="sales_mgmt_start_date"
            )
        with col2:
            analysis_end_date = st.date_input(
                "종료일",
                value=max_date,
                min_value=min_date,
                max_value=max_date,
                key="sales_mgmt_end_date"
            )
        
        # 기간 유효성 검사
        if analysis_start_date > analysis_end_date:
            st.error("⚠️ 시작일은 종료일보다 이전이어야 합니다.")
        else:
            # 기간 필터링
            filtered_sales_df = daily_sales_df[
                (daily_sales_df['날짜'].dt.date >= analysis_start_date) & 
                (daily_sales_df['날짜'].dt.date <= analysis_end_date)
            ].copy()
            
            if filtered_sales_df.empty:
                st.info(f"선택한 기간({analysis_start_date.strftime('%Y년 %m월 %d일')} ~ {analysis_end_date.strftime('%Y년 %m월 %d일')})에 해당하는 판매 데이터가 없습니다.")
            else:
                # 메뉴별 총 판매수량 집계
                sales_summary = (
                    filtered_sales_df.groupby('메뉴명')['판매수량']
                    .sum()
                    .reset_index()
                )
                sales_summary.columns = ['메뉴명', '판매수량']
                
                # 메뉴 마스터와 조인하여 판매가 가져오기
                summary_df = pd.merge(
                    sales_summary,
                    menu_df[['메뉴명', '판매가']],
                    on='메뉴명',
                    how='left',
                )
                
                # 매출 금액 계산
                summary_df['매출'] = summary_df['판매수량'] * summary_df['판매가']
                
                # 원가 정보 계산
                if not recipe_df.empty and not ingredient_df.empty:
                    cost_df = calculate_menu_cost(menu_df, recipe_df, ingredient_df)
                    summary_df = pd.merge(
                        summary_df,
                        cost_df[['메뉴명', '원가']],
                        on='메뉴명',
                        how='left',
                    )
                    summary_df['원가'] = summary_df['원가'].fillna(0)
                    summary_df['총판매원가'] = summary_df['판매수량'] * summary_df['원가']
                    summary_df['이익'] = summary_df['매출'] - summary_df['총판매원가']
                    summary_df['이익률'] = (summary_df['이익'] / summary_df['매출'] * 100).round(2)
                    summary_df['원가율'] = (summary_df['원가'] / summary_df['판매가'] * 100).round(2)
                else:
                    summary_df['원가'] = 0
                    summary_df['총판매원가'] = 0
                    summary_df['이익'] = summary_df['매출']
                    summary_df['이익률'] = 0
                    summary_df['원가율'] = 0
                
                # 총합계 계산
                total_revenue = summary_df['매출'].sum()
                total_cost = summary_df['총판매원가'].sum()
                total_profit = summary_df['이익'].sum()
                total_quantity = summary_df['판매수량'].sum()
                days_count = (analysis_end_date - analysis_start_date).days + 1
                
                # ========== 1. 핵심 요약 지표 (KPI 카드) ==========
                st.markdown("""
                <div style="margin: 2rem 0 1rem 0;">
                    <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                        📊 기간 내 요약
                    </h3>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("총 판매량", f"{int(total_quantity):,}개")
                with col2:
                    st.metric("총 매출", f"{total_revenue:,.0f}원")
                with col3:
                    st.metric("총 원가", f"{total_cost:,.0f}원")
                with col4:
                    st.metric("총 이익", f"{total_profit:,.0f}원")
                with col5:
                    avg_daily_quantity = total_quantity / days_count if days_count > 0 else 0
                    st.metric("일평균 판매량", f"{avg_daily_quantity:,.1f}개")
                
                render_section_divider()
                
                # ========== 2. ABC 분석 ==========
                st.markdown("""
                <div style="margin: 2rem 0 1rem 0;">
                    <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                        📊 판매 ABC 분석
                    </h3>
                </div>
                """, unsafe_allow_html=True)
                
                if total_revenue <= 0:
                    st.info("매출 데이터가 충분하지 않아 ABC 분석을 할 수 없습니다.")
                else:
                    # ABC 분석 테이블
                    summary_df = summary_df.sort_values('매출', ascending=False)
                    summary_df['비율(%)'] = (summary_df['매출'] / total_revenue * 100).round(2)
                    summary_df['누계 비율(%)'] = summary_df['비율(%)'].cumsum().round(2)
                    
                    # ABC 등급 부여
                    def assign_abc_grade(cumulative_ratio):
                        if cumulative_ratio <= 70:
                            return 'A'
                        elif cumulative_ratio <= 90:
                            return 'B'
                        else:
                            return 'C'
                    
                    summary_df['ABC 등급'] = summary_df['누계 비율(%)'].apply(assign_abc_grade)
                    
                    # 표시용 데이터프레임 구성
                    display_df = summary_df.copy()
                    display_df['판매가'] = display_df['판매가'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                    display_df['매출'] = display_df['매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                    display_df['원가'] = display_df['원가'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                    display_df['총판매원가'] = display_df['총판매원가'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                    
                    # 이익 컬럼이 있는지 확인 후 포맷팅
                    if '이익' in display_df.columns:
                        display_df['이익'] = display_df['이익'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                    if '이익률' in display_df.columns:
                        display_df['이익률'] = display_df['이익률'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
                    if '원가율' in display_df.columns:
                        display_df['원가율'] = display_df['원가율'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
                    
                    # 표시할 컬럼 선택 (존재하는 컬럼만)
                    available_columns = []
                    column_order = ['메뉴명', '판매가', '판매수량', '매출', '비율(%)', '누계 비율(%)', 'ABC 등급', 
                                   '원가', '총판매원가', '이익', '이익률', '원가율']
                    for col in column_order:
                        if col in display_df.columns:
                            available_columns.append(col)
                    
                    display_df = display_df[available_columns]
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                    
                    render_section_divider()
                    
                    # ========== 3. 인기 메뉴 TOP 10 ==========
                    st.markdown("""
                    <div style="margin: 2rem 0 1rem 0;">
                        <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                            🏆 인기 메뉴 TOP 10
                        </h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    top10_df = summary_df.head(10).copy()
                    top10_df.insert(0, '순위', range(1, len(top10_df) + 1))
                    
                    display_top10 = top10_df.copy()
                    display_top10['판매수량'] = display_top10['판매수량'].apply(lambda x: f"{int(x):,}개")
                    display_top10['매출'] = display_top10['매출'].apply(lambda x: f"{int(x):,}원")
                    
                    st.dataframe(
                        display_top10[['순위', '메뉴명', '판매수량', '매출', '비율(%)', 'ABC 등급']],
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    render_section_divider()
                    
                    # ========== 4. 수익성 분석 ==========
                    st.markdown("""
                    <div style="margin: 2rem 0 1rem 0;">
                        <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                            💰 수익성 분석
                        </h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 이익률 기준 정렬
                    profitability_df = summary_df.sort_values('이익률', ascending=False).copy()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**✅ 최고 수익성 메뉴 (이익률 기준)**")
                        top_profit_df = profitability_df.head(5).copy()
                        top_profit_df['이익률'] = top_profit_df['이익률'].apply(lambda x: f"{x:.1f}%")
                        top_profit_df['이익'] = top_profit_df['이익'].apply(lambda x: f"{int(x):,}원")
                        st.dataframe(
                            top_profit_df[['메뉴명', '이익', '이익률', '원가율']],
                            use_container_width=True,
                            hide_index=True
                        )
                    
                    with col2:
                        st.write("**⚠️ 저수익성 메뉴 (이익률 기준)**")
                        low_profit_df = profitability_df.tail(5).copy()
                        low_profit_df = low_profit_df[low_profit_df['이익률'] < 30].copy()  # 이익률 30% 미만만 표시
                        if not low_profit_df.empty:
                            low_profit_df['이익률'] = low_profit_df['이익률'].apply(lambda x: f"{x:.1f}%")
                            low_profit_df['이익'] = low_profit_df['이익'].apply(lambda x: f"{int(x):,}원")
                            st.dataframe(
                                low_profit_df[['메뉴명', '이익', '이익률', '원가율']],
                                use_container_width=True,
                                hide_index=True
                            )
                        else:
                            st.info("저수익성 메뉴가 없습니다.")
                    
                    render_section_divider()
                    
                    # ========== 5. 판매 트렌드 분석 ==========
                    st.markdown("""
                    <div style="margin: 2rem 0 1rem 0;">
                        <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                            📈 판매 트렌드 분석
                        </h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 일별 판매량 집계
                    daily_summary = filtered_sales_df.groupby('날짜')['판매수량'].sum().reset_index()
                    daily_summary = daily_summary.sort_values('날짜')
                    
                    # 최근 7일 vs 최근 30일 비교
                    today_date = datetime.now().date()
                    recent_7_days = filtered_sales_df[
                        filtered_sales_df['날짜'].dt.date >= (today_date - timedelta(days=7))
                    ]
                    recent_30_days = filtered_sales_df[
                        filtered_sales_df['날짜'].dt.date >= (today_date - timedelta(days=30))
                    ]
                    
                    if not recent_7_days.empty and not recent_30_days.empty:
                        avg_7d = recent_7_days['판매수량'].sum() / 7
                        avg_30d = recent_30_days['판매수량'].sum() / 30
                        trend_change = avg_7d - avg_30d
                        trend_pct = (trend_change / avg_30d * 100) if avg_30d > 0 else 0
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("최근 7일 평균 판매량", f"{avg_7d:,.1f}개")
                        with col2:
                            st.metric("최근 30일 평균 판매량", f"{avg_30d:,.1f}개")
                        with col3:
                            trend_status = "📈 상승" if trend_change > 0 else "📉 하락" if trend_change < 0 else "➡️ 유지"
                            st.metric("트렌드", f"{trend_pct:+.1f}%", trend_status)
                    
                    # 일별 판매량 표
                    if not daily_summary.empty:
                        st.write("**📅 일별 판매량 추이**")
                        display_daily = daily_summary.copy()
                        display_daily['날짜'] = display_daily['날짜'].dt.strftime('%Y-%m-%d')
                        display_daily['판매수량'] = display_daily['판매수량'].apply(lambda x: f"{int(x):,}개")
                        st.dataframe(display_daily, use_container_width=True, hide_index=True)
                    
                    render_section_divider()
                    
                    # ========== 6. 요일별 인기 메뉴 ==========
                    st.markdown("""
                    <div style="margin: 2rem 0 1rem 0;">
                        <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                            📅 요일별 인기 메뉴
                        </h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    filtered_sales_df['요일'] = filtered_sales_df['날짜'].dt.day_name()
                    day_names_kr = {
                        'Monday': '월요일', 'Tuesday': '화요일', 'Wednesday': '수요일',
                        'Thursday': '목요일', 'Friday': '금요일', 'Saturday': '토요일', 'Sunday': '일요일'
                    }
                    filtered_sales_df['요일한글'] = filtered_sales_df['요일'].map(day_names_kr)
                    
                    day_menu_summary = filtered_sales_df.groupby(['요일한글', '메뉴명'])['판매수량'].sum().reset_index()
                    day_menu_summary = day_menu_summary.sort_values(['요일한글', '판매수량'], ascending=[True, False])
                    
                    # 요일별 TOP 3 메뉴
                    day_order = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
                    for day in day_order:
                        day_data = day_menu_summary[day_menu_summary['요일한글'] == day].head(3)
                        if not day_data.empty:
                            st.write(f"**{day} TOP 3**")
                            display_day = day_data.copy()
                            display_day['판매수량'] = display_day['판매수량'].apply(lambda x: f"{int(x):,}개")
                            st.dataframe(display_day[['메뉴명', '판매수량']], use_container_width=True, hide_index=True)
                    
                    render_section_divider()
                    
                    # ========== 7. 메뉴별 성장률 분석 ==========
                    st.markdown("""
                    <div style="margin: 2rem 0 1rem 0;">
                        <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                            📊 메뉴별 성장률 분석
                        </h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 기간을 반으로 나눠서 비교
                    mid_date = analysis_start_date + (analysis_end_date - analysis_start_date) / 2
                    first_half = filtered_sales_df[filtered_sales_df['날짜'].dt.date <= mid_date]
                    second_half = filtered_sales_df[filtered_sales_df['날짜'].dt.date > mid_date]
                    
                    if not first_half.empty and not second_half.empty:
                        first_half_summary = first_half.groupby('메뉴명')['판매수량'].sum().reset_index()
                        first_half_summary.columns = ['메뉴명', '전반기 판매량']
                        second_half_summary = second_half.groupby('메뉴명')['판매수량'].sum().reset_index()
                        second_half_summary.columns = ['메뉴명', '후반기 판매량']
                        
                        growth_df = pd.merge(first_half_summary, second_half_summary, on='메뉴명', how='outer')
                        growth_df = growth_df.fillna(0)
                        growth_df['성장률(%)'] = ((growth_df['후반기 판매량'] - growth_df['전반기 판매량']) / 
                                                 growth_df['전반기 판매량'] * 100).round(1)
                        growth_df = growth_df.replace([float('inf'), float('-inf')], 0)
                        growth_df = growth_df.sort_values('성장률(%)', ascending=False)
                        
                        st.write("**📈 성장률 TOP 10 메뉴**")
                        top_growth_df = growth_df.head(10).copy()
                        top_growth_df['전반기 판매량'] = top_growth_df['전반기 판매량'].apply(lambda x: f"{int(x):,}개")
                        top_growth_df['후반기 판매량'] = top_growth_df['후반기 판매량'].apply(lambda x: f"{int(x):,}개")
                        top_growth_df['성장률(%)'] = top_growth_df['성장률(%)'].apply(lambda x: f"{x:+.1f}%")
                        st.dataframe(
                            top_growth_df[['메뉴명', '전반기 판매량', '후반기 판매량', '성장률(%)']],
                            use_container_width=True,
                            hide_index=True
                        )

# 판매량 등록 페이지
elif page == "판매량 등록":
    render_page_header("판매량 등록", "📦")
    
    # 메뉴 목록 로드
    menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
    menu_list = menu_df['메뉴명'].tolist() if not menu_df.empty else []
    
    # ========== 일일 판매 입력 (점장 마감 스타일 - 지정 날짜에 전 메뉴 수량 입력) ==========
    from datetime import datetime
    st.subheader("📦 일일 판매 입력 (전 메뉴 일괄 입력)")
    
    if not menu_list:
        st.warning("먼저 메뉴를 등록해주세요.")
    else:
        col_date, _ = st.columns([1, 3])
        with col_date:
            sales_date = st.date_input(
                "판매 날짜 선택",
                value=datetime.now().date(),
                key="daily_sales_full_date",
            )
        
        st.markdown("---")
        st.write("**선택한 날짜의 각 메뉴별 판매 수량을 한 번에 입력하세요. (0은 미판매)**")
        
        sales_items = []
        # 메뉴를 3열 그리드로 표시 (점장 마감 페이지와 동일한 스타일)
        num_rows = (len(menu_list) + 2) // 3
        for row in range(num_rows):
            cols = st.columns(3)
            for col_idx in range(3):
                menu_idx = row * 3 + col_idx
                if menu_idx < len(menu_list):
                    menu_name = menu_list[menu_idx]
                    with cols[col_idx]:
                        qty = st.number_input(
                            menu_name,
                            min_value=0,
                            value=0,
                            step=1,
                            key=f"daily_sales_full_{menu_name}",
                        )
                        if qty > 0:
                            sales_items.append((menu_name, qty))
        
        render_section_divider()
        
        save_col, _ = st.columns([1, 3])
        with save_col:
            if st.button("💾 일괄 저장", type="primary", use_container_width=True, key="daily_sales_full_save"):
                if not sales_items:
                    st.error("저장할 판매 내역이 없습니다. 한 개 이상의 메뉴에 판매 수량을 입력해주세요.")
                else:
                    success_count = 0
                    errors = []
                    for menu_name, quantity in sales_items:
                        try:
                            save_daily_sales_item(sales_date, menu_name, quantity)
                            success_count += 1
                        except Exception as e:
                            errors.append(f"{menu_name}: {e}")
                    
                    if errors:
                        for msg in errors:
                            st.error(msg)
                    
                    if success_count > 0:
                        st.success(f"✅ {sales_date} 기준 {success_count}개 메뉴의 판매 내역이 저장되었습니다.")
                        st.balloons()
                        st.rerun()

# 재료 사용량 집계 페이지
elif page == "재료 사용량 집계":
    render_page_header("재료 사용량 집계", "📈")

    # 데이터 로드
    daily_sales_df = load_csv('daily_sales_items.csv', default_columns=['날짜', '메뉴명', '판매수량'])
    recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
    ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가'])

    if not daily_sales_df.empty and not recipe_df.empty:
        usage_df = calculate_ingredient_usage(daily_sales_df, recipe_df)

        if not usage_df.empty:
            # 날짜를 datetime으로 변환
            usage_df['날짜'] = pd.to_datetime(usage_df['날짜'])
            
            # 사용 가능한 날짜 범위
            min_date = usage_df['날짜'].min().date()
            max_date = usage_df['날짜'].max().date()
            
            # 기간 선택 필터
            st.markdown("**📅 기간 선택**")
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "시작일",
                    value=min_date,
                    min_value=min_date,
                    max_value=max_date,
                    key="usage_start_date"
                )
            with col2:
                end_date = st.date_input(
                    "종료일",
                    value=max_date,
                    min_value=min_date,
                    max_value=max_date,
                    key="usage_end_date"
                )
            
            # 기간 유효성 검사
            if start_date > end_date:
                st.error("⚠️ 시작일은 종료일보다 이전이어야 합니다.")
            else:
                # 기간 필터링
                display_usage_df = usage_df[
                    (usage_df['날짜'].dt.date >= start_date) & 
                    (usage_df['날짜'].dt.date <= end_date)
                ].copy()
                
                if not display_usage_df.empty:
                    # 재료 단가와 조인하여 총 사용 단가 계산
                    if not ingredient_df.empty:
                        display_usage_df = pd.merge(
                            display_usage_df,
                            ingredient_df[['재료명', '단가']],
                            on='재료명',
                            how='left'
                        )
                        display_usage_df['단가'] = display_usage_df['단가'].fillna(0)
                    else:
                        display_usage_df['단가'] = 0.0

                    display_usage_df['총사용단가'] = display_usage_df['총사용량'] * display_usage_df['단가']
                    
                    # 기간 표시
                    st.markdown(f"**📊 조회 기간: {start_date.strftime('%Y년 %m월 %d일')} ~ {end_date.strftime('%Y년 %m월 %d일')}**")
                    
                    render_section_divider()
                    
                    # 재료별 총 사용량/총 사용 단가 집계 (기간 전체 합계)
                    ingredient_summary = (
                        display_usage_df
                        .groupby('재료명')[['총사용량', '총사용단가']]
                        .sum()
                        .reset_index()
                    )

                    # 사용 단가 기준으로 정렬
                    ingredient_summary = ingredient_summary.sort_values('총사용단가', ascending=False)
                    
                    # 총 사용단가 합계 계산
                    total_cost = ingredient_summary['총사용단가'].sum()
                    
                    # 비율 및 누적 비율 계산
                    ingredient_summary['비율(%)'] = (ingredient_summary['총사용단가'] / total_cost * 100).round(2)
                    ingredient_summary['누적 비율(%)'] = ingredient_summary['비율(%)'].cumsum().round(2)
                    
                    # ABC 등급 부여
                    def assign_abc_grade(cumulative_ratio):
                        if cumulative_ratio <= 70:
                            return 'A'
                        elif cumulative_ratio <= 90:
                            return 'B'
                        else:
                            return 'C'
                    
                    ingredient_summary['ABC 등급'] = ingredient_summary['누적 비율(%)'].apply(assign_abc_grade)
                    
                    # TOP 10 재료
                    st.markdown("**💰 사용 단가 TOP 10 재료**")
                    top10_df = ingredient_summary.head(10).copy()
                    top10_df.insert(0, '순위', range(1, len(top10_df) + 1))
                    top10_df['총 사용량'] = top10_df['총사용량']
                    top10_df['총 사용단가'] = top10_df['총사용단가']
                    top10_df = top10_df[['순위', '재료명', '총 사용량', '총 사용단가', '비율(%)', '누적 비율(%)', 'ABC 등급']]
                    st.dataframe(top10_df, use_container_width=True, hide_index=True)
                    # TOP 10 총합계
                    top10_total = top10_df['총 사용단가'].sum()
                    st.markdown(f"**💰 TOP 10 총 사용단가 합계: {top10_total:,.0f}원**")
                    
                    render_section_divider()
                    
                    # 전체 재료 사용 단가 순위표 (1위부터 끝까지, ABC 분석 포함)
                    st.markdown("**📊 전체 재료 사용 단가 순위 (ABC 분석)**")
                    full_ranking_df = ingredient_summary.copy()
                    full_ranking_df.insert(0, '순위', range(1, len(full_ranking_df) + 1))
                    full_ranking_df['총 사용량'] = full_ranking_df['총사용량']
                    full_ranking_df['총 사용단가'] = full_ranking_df['총사용단가']
                    full_ranking_df = full_ranking_df[['순위', '재료명', '총 사용량', '총 사용단가', '비율(%)', '누적 비율(%)', 'ABC 등급']]
                    st.dataframe(full_ranking_df, use_container_width=True, hide_index=True)
                    # 전체 총합계
                    full_total = full_ranking_df['총 사용단가'].sum()
                    st.markdown(f"**📊 전체 총 사용단가 합계: {full_total:,.0f}원**")
                    
                    # ABC 등급별 통계
                    abc_stats = full_ranking_df.groupby('ABC 등급').agg({
                        '재료명': 'count',
                        '총 사용단가': 'sum',
                        '비율(%)': 'sum'
                    }).reset_index()
                    abc_stats.columns = ['ABC 등급', '재료 수', '총 사용단가', '비율 합계(%)']
                    
                    render_section_divider()
                    st.markdown("**📈 ABC 등급별 통계**")
                    st.dataframe(abc_stats, use_container_width=True, hide_index=True)
                    
                    # 통계 정보
                    st.markdown(
                        f"**총 {len(full_ranking_df)}개 재료**"
                        f" | **총 사용량: {full_ranking_df['총 사용량'].sum():,.2f}**"
                        f" | **총 사용 단가: {full_ranking_df['총 사용단가'].sum():,.0f}원**"
                    )
                else:
                    st.warning(f"선택한 기간({start_date.strftime('%Y년 %m월 %d일')} ~ {end_date.strftime('%Y년 %m월 %d일')})에 해당하는 데이터가 없습니다.")
        else:
            st.info("재료 사용량을 계산할 데이터가 없습니다.")
    else:
        st.info("판매 내역과 레시피 데이터가 필요합니다.")

# 발주 관리 페이지
elif page == "발주 관리":
    render_page_header("발주 관리", "🛒")
    
    # 재료 목록 로드 (발주단위/변환비율 포함)
    ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가', '발주단위', '변환비율'])
    ingredient_list = ingredient_df['재료명'].tolist() if not ingredient_df.empty else []
    
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
        render_section_header("안전재고 등록", "🛡️")
        
        inventory_df = load_csv('inventory.csv', default_columns=['재료명', '현재고', '안전재고'])
        
        if ingredient_df.empty:
            st.info("먼저 재료를 등록해주세요.")
        else:
            st.caption("전체 재료를 한 번에 펼쳐서 발주단위 기준 안전재고를 등록·수정할 수 있습니다.")
            
            # 재료 목록과 기존 안전재고를 조인 (발주단위/변환비율 포함)
            safety_df = pd.merge(
                ingredient_df[['재료명', '단위', '단가', '발주단위', '변환비율']],
                inventory_df[['재료명', '안전재고']] if not inventory_df.empty else pd.DataFrame(columns=['재료명', '안전재고']),
                on='재료명',
                how='left'
            )
            
            # 기본값 처리
            safety_df['발주단위'] = safety_df['발주단위'].fillna(safety_df['단위'])
            safety_df['변환비율'] = safety_df['변환비율'].fillna(1.0)
            safety_df['단가'] = safety_df['단가'].fillna(0.0)
            safety_df['안전재고'] = safety_df['안전재고'].fillna(0.0)
            
            # 사용단가 / 발주단가 계산
            safety_df['발주단위단가_숫자'] = safety_df['단가'] * safety_df['변환비율']
            
            # 헤더 행 (테이블 느낌으로)
            h1, h2, h3, h4, h5, h6, h7 = st.columns([3, 1.2, 1.2, 1.8, 1.8, 2, 1])
            h1.markdown("**재료명**")
            h2.markdown("**사용단위**")
            h3.markdown("**발주단위**")
            h4.markdown("**사용단가**")
            h5.markdown("**발주단가**")
            h6.markdown("**안전재고 (발주단위)**")
            h7.markdown("**저장**")
            
            for idx, row in safety_df.iterrows():
                # 기존 안전재고를 발주단위 기준으로 변환
                current_safety_order = float(row['안전재고'] or 0.0) / float(row['변환비율'] or 1.0)
                
                col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 1.2, 1.2, 1.8, 1.8, 2, 1])
                with col1:
                    st.write(f"**{row['재료명']}**")
                with col2:
                    st.write(row['단위'])
                with col3:
                    st.write(row['발주단위'])
                with col4:
                    st.write(f"{row['단가']:,.1f}원/{row['단위']}")
                with col5:
                    st.write(f"{row['발주단위단가_숫자']:,.1f}원/{row['발주단위']}")
                with col6:
                    new_safety_order = st.number_input(
                        f"발주단위: {row['발주단위']}",
                        min_value=0.0,
                        value=current_safety_order,
                        step=1.0,
                        format="%.2f",
                        key=f"safety_stock_order_{row['재료명']}",
                    )
                with col7:
                    if st.button("저장", key=f"safety_save_{row['재료명']}", use_container_width=True):
                        try:
                            # 기존 현재고는 그대로 두고, 안전재고만 수정 (기본단위 기준으로 저장)
                            if not inventory_df.empty and row['재료명'] in inventory_df['재료명'].values:
                                cur_row = inventory_df[inventory_df['재료명'] == row['재료명']].iloc[0]
                                current_stock_base = float(cur_row.get('현재고', 0) or 0)
                            else:
                                current_stock_base = 0.0
                            
                            new_safety_base = float(new_safety_order) * float(row['변환비율'] or 1.0)
                            
                            save_inventory(row['재료명'], current_stock_base, new_safety_base)
                            st.cache_data.clear()
                            st.success(
                                f"'{row['재료명']}'의 안전재고가 "
                                f"{new_safety_order:,.2f} {row['발주단위']} "
                                f"(기본단위 기준 {new_safety_base:,.2f} {row['단위']})로 저장되었습니다."
                            )
                            st.rerun()
                        except Exception as e:
                            st.error(f"안전재고 저장 중 오류가 발생했습니다: {e}")
    
    # ========== 탭 2: 현재 재고 현황 ==========
    with tab2:
        render_section_header("현재 재고 현황", "📦")
        
        inventory_df = load_csv('inventory.csv', default_columns=['재료명', '현재고', '안전재고'])
        
        if not ingredient_df.empty:
            # 전체 재료 기준으로 조인해서 재고가 없는 재료도 모두 표시 (현재고/안전재고는 0으로 처리)
            display_inventory_df = pd.merge(
                ingredient_df[['재료명', '단위', '단가', '발주단위', '변환비율']],
                inventory_df[['재료명', '현재고', '안전재고']] if not inventory_df.empty else pd.DataFrame(columns=['재료명', '현재고', '안전재고']),
                on='재료명',
                how='left'
            )
            display_inventory_df['현재고'] = display_inventory_df['현재고'].fillna(0.0)
            display_inventory_df['안전재고'] = display_inventory_df['안전재고'].fillna(0.0)
            
            # 발주 단위/변환비율 기본값 처리
            display_inventory_df['발주단위'] = display_inventory_df['발주단위'].fillna(display_inventory_df['단위'])
            display_inventory_df['변환비율'] = display_inventory_df['변환비율'].fillna(1.0)
            display_inventory_df['단가'] = display_inventory_df['단가'].fillna(0)
            
            # 재료사용단가 포맷팅
            display_inventory_df['재료사용단가'] = display_inventory_df.apply(
                lambda row: f"{row['단가']:,.1f}원/{row['단위']}",
                axis=1
            )
            
            # 발주단위단가 계산 (기본 단가 × 변환비율)
            display_inventory_df['발주단위단가'] = display_inventory_df.apply(
                lambda row: f"{(row['단가'] * row['변환비율']):,.1f}원/{row['발주단위']}",
                axis=1
            )
            
            # 현재고와 안전재고를 발주 단위로 변환하여 표시
            display_inventory_df['현재고_발주단위'] = display_inventory_df['현재고'] / display_inventory_df['변환비율']
            display_inventory_df['안전재고_발주단위'] = display_inventory_df['안전재고'] / display_inventory_df['변환비율']
            
            # 현재고/안전재고/차이 표시
            display_inventory_df['현재고표시'] = display_inventory_df.apply(
                lambda row: f"{row['현재고_발주단위']:,.2f} {row['발주단위']}",
                axis=1
            )
            display_inventory_df['안전재고표시'] = display_inventory_df.apply(
                lambda row: f"{row['안전재고_발주단위']:,.2f} {row['발주단위']}",
                axis=1
            )
            display_inventory_df['차이'] = display_inventory_df['현재고_발주단위'] - display_inventory_df['안전재고_발주단위']
            display_inventory_df['차이(+/-)'] = display_inventory_df.apply(
                lambda row: f"{row['차이']:+,.2f} {row['발주단위']}",
                axis=1
            )
            
            # 표 표시
            view_cols = [
                '재료명', '단위', '재료사용단가',
                '발주단위', '발주단위단가',
                '현재고표시', '안전재고표시', '차이(+/-)'
            ]
            rename_map = {
                '단위': '재료사용단위',
                '현재고표시': '현재고',
                '안전재고표시': '기준 안전재고',
            }
            st.dataframe(
                display_inventory_df[view_cols].rename(columns=rename_map),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("먼저 재료를 등록해주세요.")
        
        render_section_divider()
        render_section_header("현재고 / 안전재고 수정", "✏️")
        
        if not ingredient_df.empty:
            # 전체 재료 기준으로 현재고/안전재고를 한 번에 수정 (발주단위 기준 입력)
            edit_df = pd.merge(
                ingredient_df[['재료명', '단위', '단가', '발주단위', '변환비율']],
                inventory_df[['재료명', '현재고', '안전재고']] if not inventory_df.empty else pd.DataFrame(columns=['재료명', '현재고', '안전재고']),
                on='재료명',
                how='left'
            )
            edit_df['발주단위'] = edit_df['발주단위'].fillna(edit_df['단위'])
            edit_df['변환비율'] = edit_df['변환비율'].fillna(1.0)
            edit_df['단가'] = edit_df['단가'].fillna(0.0)
            edit_df['현재고'] = edit_df['현재고'].fillna(0.0)
            edit_df['안전재고'] = edit_df['안전재고'].fillna(0.0)
            
            # 발주단가 계산
            edit_df['발주단위단가_숫자'] = edit_df['단가'] * edit_df['변환비율']
            
            # 현재고/안전재고를 발주단위 기준으로 변환
            edit_df['현재고_발주단위'] = edit_df['현재고'] / edit_df['변환비율']
            edit_df['안전재고_발주단위'] = edit_df['안전재고'] / edit_df['변환비율']
            
            # 헤더 (안전재고 등록과 동일 구조 + 현재고 입력 추가)
            h1, h2, h3, h4, h5, h6, h7, h8 = st.columns([3, 1.2, 1.2, 1.8, 1.8, 2, 2, 1])
            h1.markdown("**재료명**")
            h2.markdown("**사용단위**")
            h3.markdown("**발주단위**")
            h4.markdown("**사용단가**")
            h5.markdown("**발주단가**")
            h6.markdown("**현재고 (발주단위)**")
            h7.markdown("**안전재고 (발주단위)**")
            h8.markdown("**저장**")
            
            for idx, row in edit_df.iterrows():
                col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([3, 1.2, 1.2, 1.8, 1.8, 2, 2, 1])
                with col1:
                    st.write(f"**{row['재료명']}**")
                with col2:
                    st.write(row['단위'])
                with col3:
                    st.write(row['발주단위'])
                with col4:
                    st.write(f"{row['단가']:,.1f}원/{row['단위']}")
                with col5:
                    st.write(f"{row['발주단위단가_숫자']:,.1f}원/{row['발주단위']}")
                with col6:
                    new_current_order = st.number_input(
                        f"발주단위: {row['발주단위']}",
                        min_value=0.0,
                        value=float(row['현재고_발주단위']),
                        step=1.0,
                        format="%.2f",
                        key=f"edit_current_order_{row['재료명']}"
                    )
                with col7:
                    new_safety_order = st.number_input(
                        f"발주단위: {row['발주단위']}",
                        min_value=0.0,
                        value=float(row['안전재고_발주단위']),
                        step=1.0,
                        format="%.2f",
                        key=f"edit_safety_order_{row['재료명']}"
                    )
                with col8:
                    if st.button("저장", key=f"edit_inventory_save_{row['재료명']}", use_container_width=True):
                        try:
                            # 발주단위를 기본단위로 변환해서 저장
                            new_current_base = float(new_current_order) * float(row['변환비율'] or 1.0)
                            new_safety_base = float(new_safety_order) * float(row['변환비율'] or 1.0)
                            
                            save_inventory(row['재료명'], new_current_base, new_safety_base)
                            st.cache_data.clear()
                            st.success(
                                f"'{row['재료명']}'의 현재고/안전재고가 "
                                f"{new_current_order:,.2f} / {new_safety_order:,.2f} {row['발주단위']} "
                                f"(기본단위 기준 {new_current_base:,.2f} / {new_safety_base:,.2f} {row['단위']})로 수정되었습니다."
                            )
                            st.rerun()
                        except Exception as e:
                            st.error(f"재고 수정 중 오류가 발생했습니다: {e}")
    
    # ========== 탭 3: 발주 추천 ==========
    with tab3:
        render_section_header("발주 추천", "🛒")
        
        inventory_df = load_csv('inventory.csv', default_columns=['재료명', '현재고', '안전재고'])
        
        # ========== Phase 4: 고급 알림 및 경고 ==========
        from datetime import datetime, timedelta
        
        # 품절 위험 알림 계산 (예상 소진일 포함)
        urgent_orders = []
        low_stock_items = []
        pending_orders_count = 0
        expected_deliveries = []
        overdue_orders = []  # 발주 미완료 재료
        low_turnover_items = []  # 재고 회전율 낮은 재료
        excess_inventory_cost = 0  # 과다재고 비용
        
        # 재료 사용량 데이터 로드 (예상 소진일 계산용)
        daily_sales_df = load_csv('daily_sales_items.csv', default_columns=['날짜', '메뉴명', '판매수량'])
        recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
        usage_df = pd.DataFrame()
        
        if not daily_sales_df.empty and not recipe_df.empty:
            usage_df = calculate_ingredient_usage(daily_sales_df, recipe_df)
        
        if not inventory_df.empty:
            # 현재고 < 안전재고인 재료 찾기 (예상 소진일 계산 포함)
            for idx, row in inventory_df.iterrows():
                ingredient_name = row['재료명']
                current_stock = row.get('현재고', 0)
                safety_stock = row.get('안전재고', 0)
                
                if current_stock < safety_stock:
                    # 예상 소진일 계산
                    expected_depletion_days = None
                    if not usage_df.empty:
                        ingredient_usage = usage_df[usage_df['재료명'] == ingredient_name]
                        if not ingredient_usage.empty:
                            # 최근 7일 평균 일일 사용량
                            recent_usage = ingredient_usage.tail(7)
                            if not recent_usage.empty:
                                avg_daily_usage = recent_usage['총사용량'].mean()
                                if avg_daily_usage > 0:
                                    expected_depletion_days = int(current_stock / avg_daily_usage)
                    
                    low_stock_items.append({
                        '재료명': ingredient_name,
                        '현재고': current_stock,
                        '안전재고': safety_stock,
                        '부족량': safety_stock - current_stock,
                        '예상소진일': expected_depletion_days
                    })
                
                # 재고 회전율 계산 (과다재고 경고용)
                if not usage_df.empty and current_stock > 0:
                    from src.analytics import calculate_inventory_turnover
                    turnover_info = calculate_inventory_turnover(
                        ingredient_name,
                        usage_df,
                        inventory_df,
                        days_period=30
                    )
                    
                    # 회전율이 낮은 재료 (연간 회전율 < 12회 = 월 1회 미만)
                    if turnover_info['turnover_rate'] > 0 and turnover_info['turnover_rate'] < 12:
                        days_on_hand = turnover_info['days_on_hand']
                        # 재고 보유일수가 30일 이상인 경우 과다재고로 판단
                        if days_on_hand >= 30:
                            # 과다재고 비용 계산 (재고 가치의 일부)
                            ingredient_row = ingredient_df[ingredient_df['재료명'] == ingredient_name]
                            if not ingredient_row.empty:
                                unit_price = ingredient_row.iloc[0].get('단가', 0)
                                excess_stock = current_stock - (safety_stock * 2)  # 안전재고의 2배를 기준으로
                                if excess_stock > 0:
                                    excess_cost = excess_stock * unit_price
                                    excess_inventory_cost += excess_cost
                                    
                                    low_turnover_items.append({
                                        '재료명': ingredient_name,
                                        '현재고': current_stock,
                                        '재고보유일수': int(days_on_hand),
                                        '회전율': turnover_info['turnover_rate'],
                                        '과다재고량': excess_stock,
                                        '과다재고비용': excess_cost
                                    })
        
        # 발주 예정/완료 상태인 발주 개수
        orders_df = load_csv('orders.csv', default_columns=['id', '재료명', '공급업체명', '발주일', '수량', '단가', '총금액', '상태', '입고예정일', '입고일', '비고'])
        if not orders_df.empty:
            pending_orders = orders_df[orders_df['상태'].isin(['예정', '완료'])]
            pending_orders_count = len(pending_orders)
            
            # 입고 예정일이 오늘 또는 내일인 발주
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)
            if '입고예정일' in orders_df.columns:
                orders_df['입고예정일'] = pd.to_datetime(orders_df['입고예정일'], errors='coerce')
                expected_deliveries = orders_df[
                    (orders_df['상태'].isin(['예정', '완료'])) & 
                    (pd.to_datetime(orders_df['입고예정일']).dt.date <= tomorrow)
                ]
            
            # 발주 미완료 재료 리마인더 (발주 예정인데 3일 이상 지난 경우)
            if '발주일' in orders_df.columns:
                orders_df['발주일'] = pd.to_datetime(orders_df['발주일'], errors='coerce')
                three_days_ago = today - timedelta(days=3)
                overdue_orders = orders_df[
                    (orders_df['상태'] == '예정') & 
                    (pd.to_datetime(orders_df['발주일']).dt.date < three_days_ago)
                ]
        
        # 알림 타일 표시 (Phase 4: 고급 알림)
        expected_count = len(expected_deliveries) if isinstance(expected_deliveries, pd.DataFrame) and not expected_deliveries.empty else 0
        overdue_count = len(overdue_orders) if isinstance(overdue_orders, pd.DataFrame) and not overdue_orders.empty else (len(overdue_orders) if isinstance(overdue_orders, list) else 0)
        
        # 알림 섹션 상단의 요약 타일(4개 박스)는 UI 단순화를 위해 제거
        
        # 품절 위험 상세 정보 (예상 소진일 + 단위 표시 포함)
        if low_stock_items:
            with st.expander(f"🚨 품절 위험 재료 상세 ({len(low_stock_items)}개)", expanded=True):
                urgent_df = pd.DataFrame(low_stock_items)

                # 재료 단위/발주단위 정보 조인
                if not ingredient_df.empty:
                    urgent_df = pd.merge(
                        urgent_df,
                        ingredient_df[['재료명', '단위', '발주단위', '변환비율']] if '발주단위' in ingredient_df.columns and '변환비율' in ingredient_df.columns
                        else ingredient_df[['재료명', '단위']],
                        on='재료명',
                        how='left'
                    )
                if '발주단위' not in urgent_df.columns:
                    urgent_df['발주단위'] = urgent_df.get('단위', '')

                # 수량을 발주단위 기준으로 변환
                if '변환비율' in urgent_df.columns:
                    urgent_df['변환비율'] = urgent_df['변환비율'].fillna(1.0)
                    urgent_df['현재고_발주단위'] = urgent_df['현재고'] / urgent_df['변환비율']
                    urgent_df['안전재고_발주단위'] = urgent_df['안전재고'] / urgent_df['변환비율']
                    urgent_df['부족량_발주단위'] = urgent_df['부족량'] / urgent_df['변환비율']
                else:
                    urgent_df['현재고_발주단위'] = urgent_df['현재고']
                    urgent_df['안전재고_발주단위'] = urgent_df['안전재고']
                    urgent_df['부족량_발주단위'] = urgent_df['부족량']

                # 표시용 컬럼 포맷팅 (숫자 + 단위)
                urgent_df['현재고'] = urgent_df.apply(
                    lambda row: f"{row['현재고_발주단위']:,.2f} {row['발주단위']}",
                    axis=1
                )
                urgent_df['안전재고'] = urgent_df.apply(
                    lambda row: f"{row['안전재고_발주단위']:,.2f} {row['발주단위']}",
                    axis=1
                )
                urgent_df['부족량'] = urgent_df.apply(
                    lambda row: f"{row['부족량_발주단위']:,.2f} {row['발주단위']}",
                    axis=1
                )

                # 예상 소진일 표시
                if '예상소진일' in urgent_df.columns:
                    def format_depletion_days(days):
                        if pd.isna(days) or days is None:
                            return "계산 불가"
                        elif days <= 0:
                            return "⚠️ 즉시 소진"
                        elif days <= 3:
                            return f"🔴 {int(days)}일 후 (긴급)"
                        elif days <= 7:
                            return f"🟡 {int(days)}일 후"
                        else:
                            return f"🟢 {int(days)}일 후"
                    
                    urgent_df['예상소진일'] = urgent_df['예상소진일'].apply(format_depletion_days)

                # 표시할 컬럼만 선택
                display_cols = ['재료명', '단위', '발주단위', '현재고', '안전재고', '부족량']
                if '예상소진일' in urgent_df.columns:
                    display_cols.append('예상소진일')
                st.dataframe(urgent_df[display_cols], use_container_width=True, hide_index=True)
            
            # 발주 미완료 재료 리마인더
            if overdue_count > 0 and isinstance(overdue_orders, pd.DataFrame) and not overdue_orders.empty:
                with st.expander(f"⏰ 발주 미완료 재료 리마인더 ({overdue_count}건)", expanded=True):
                    display_overdue = overdue_orders[['재료명', '공급업체명', '발주일', '수량', '상태']].copy()
                    if '발주일' in display_overdue.columns:
                        display_overdue['발주일'] = pd.to_datetime(display_overdue['발주일']).dt.strftime('%Y-%m-%d')
                    if '수량' in display_overdue.columns:
                        display_overdue['수량'] = display_overdue['수량'].apply(lambda x: f"{x:,.2f}")
                    
                    # 지연일수 계산
                    if '발주일' in overdue_orders.columns:
                        display_overdue['지연일수'] = (today - pd.to_datetime(overdue_orders['발주일']).dt.date).apply(lambda x: f"{x.days}일")
                    
                    st.dataframe(display_overdue, use_container_width=True, hide_index=True)
                    st.warning("⚠️ 발주 예정 상태인데 3일 이상 지난 발주입니다. 발주 상태를 확인해주세요.")
            
            # 과다재고 경고
            if low_turnover_items:
                with st.expander(f"📊 과다재고 경고 ({len(low_turnover_items)}개 재료)", expanded=False):
                    excess_df = pd.DataFrame(low_turnover_items)
                    excess_df['현재고'] = excess_df['현재고'].apply(lambda x: f"{x:,.2f}")
                    excess_df['재고보유일수'] = excess_df['재고보유일수'].apply(lambda x: f"{int(x)}일")
                    excess_df['회전율'] = excess_df['회전율'].apply(lambda x: f"{x:.1f}회/년")
                    excess_df['과다재고량'] = excess_df['과다재고량'].apply(lambda x: f"{x:,.2f}")
                    excess_df['과다재고비용'] = excess_df['과다재고비용'].apply(lambda x: f"{int(x):,}원")
                    
                    st.dataframe(excess_df, use_container_width=True, hide_index=True)
                    
                    if excess_inventory_cost > 0:
                        st.warning(f"💰 총 과다재고 비용: {int(excess_inventory_cost):,}원 (재고 회전율이 낮아 자금이 묶여있습니다)")
            
            render_section_divider()
        
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
                        
                        # 공급업체 정보 로드
                        from src.storage_supabase import save_order
                        suppliers_df = load_csv('suppliers.csv', default_columns=['공급업체명', '전화번호', '이메일', '배송일', '최소주문금액', '배송비'])
                        ingredient_suppliers_df = load_csv('ingredient_suppliers.csv', default_columns=['재료명', '공급업체명', '단가', '기본공급업체'])
                        
                        # 표시용 DataFrame 생성
                        display_order_df = order_df.copy()
                        
                        # 발주 단위 정보 추가 (재료 마스터에서)
                        if '발주단위' in ingredient_df.columns and '변환비율' in ingredient_df.columns:
                            order_unit_map = dict(zip(ingredient_df['재료명'], ingredient_df['발주단위']))
                            conversion_rate_map = dict(zip(ingredient_df['재료명'], ingredient_df['변환비율']))
                            
                            # 발주 단위 및 변환비율 매핑
                            display_order_df['발주단위'] = display_order_df['재료명'].map(order_unit_map).fillna(display_order_df['단위'])
                            display_order_df['변환비율'] = display_order_df['재료명'].map(conversion_rate_map).fillna(1.0)
                        else:
                            display_order_df['발주단위'] = display_order_df['단위']
                            display_order_df['변환비율'] = 1.0

                        # 발주 필요량을 발주 단위로 변환 (기본 단위 -> 발주 단위)
                        display_order_df['발주필요량_발주단위'] = display_order_df['발주필요량'] / display_order_df['변환비율']
                        # 화면에 보이는 값과 계산 값이 일치하도록 소수 둘째 자리까지 반올림
                        display_order_df['발주필요량_발주단위'] = display_order_df['발주필요량_발주단위'].round(2)
                        
                        # 공급업체 정보 추가
                        supplier_price_map = {}
                        if not ingredient_suppliers_df.empty:
                            # 기본 공급업체 매핑
                            default_suppliers = ingredient_suppliers_df[ingredient_suppliers_df.get('기본공급업체', pd.Series([False]*len(ingredient_suppliers_df))) == True]
                            supplier_map = dict(zip(default_suppliers['재료명'], default_suppliers['공급업체명']))
                            supplier_price_map = dict(zip(default_suppliers['재료명'], default_suppliers['단가']))
                            display_order_df['공급업체'] = display_order_df['재료명'].map(supplier_map).fillna("미지정")
                        else:
                            display_order_df['공급업체'] = "미지정"

                        # 사용단가 분리: 재료등록 기준 vs 공급업체 매핑 기준
                        # order_df['단가']는 재료등록 기준 기본단위단가(원/사용단위)
                        display_order_df['사용단가_재료등록'] = display_order_df['단가'].fillna(0.0)
                        display_order_df['사용단가_공급업체'] = display_order_df['재료명'].map(supplier_price_map)
                        # 실제 발주에 사용할 단가: 공급업체 단가가 있으면 우선, 없으면 재료등록 단가
                        display_order_df['사용단가_실제'] = display_order_df['사용단가_공급업체'].combine_first(display_order_df['사용단가_재료등록'])
                        
                        # 발주단위 기준 단가 계산 (사용자에게 보이는 "발주단가")
                        # 실제 사용단가(원/기본단위) × 변환비율 = 발주단위단가(원/발주단위)
                        display_order_df['발주단위단가_숫자'] = display_order_df['사용단가_실제'] * display_order_df['변환비율']

                        # 예상금액도 발주단위 기준으로 다시 계산 (발주필요량_발주단위 × 발주단위단가)
                        display_order_df['예상금액_숫자'] = display_order_df['발주필요량_발주단위'] * display_order_df['발주단위단가_숫자']

                        # 수량 관련 컬럼에 단위 붙여서 표시
                        display_order_df['현재고_표시'] = display_order_df.apply(
                            lambda row: f"{row['현재고']:,.2f} {row['단위']}",
                            axis=1
                        )
                        display_order_df['안전재고_표시'] = display_order_df.apply(
                            lambda row: f"{row['안전재고']:,.2f} {row['단위']}",
                            axis=1
                        )
                        display_order_df['최근평균사용량_표시'] = display_order_df.apply(
                            lambda row: f"{row['최근평균사용량']:,.2f} {row['단위']}",
                            axis=1
                        )
                        display_order_df['예상소요량_표시'] = display_order_df.apply(
                            lambda row: f"{row['예상소요량']:,.2f} {row['단위']}",
                            axis=1
                        )
                        display_order_df['발주필요량_표시'] = display_order_df.apply(
                            lambda row: f"{row['발주필요량_발주단위']:,.2f} {row['발주단위']}",
                            axis=1
                        )
                        display_order_df['발주단위단가_표시'] = display_order_df.apply(
                            lambda row: f"{row['발주단위단가_숫자']:,.1f}원/{row['발주단위']}",
                            axis=1
                        )
                        # 예상금액 숫자가 NaN일 수 있으므로 방어적으로 처리
                        def format_expected_amount(x):
                            try:
                                if x is None or pd.isna(x):
                                    return "-"
                                return f"{int(round(float(x))):,}원"
                            except Exception:
                                return "-"
                        display_order_df['예상금액'] = display_order_df['예상금액_숫자'].apply(format_expected_amount)
                        
                        # 발주 단위 표시 (기본 단위와 발주 단위 모두 표시)
                        display_order_df['단위표시'] = display_order_df.apply(
                            lambda row: f"{row['단위']} / 발주: {row['발주단위']}" if row['발주단위'] != row['단위'] else row['단위'],
                            axis=1
                        )
                        
                        st.dataframe(
                            display_order_df[[
                                '재료명',
                                '단위표시',
                                '공급업체',
                                '현재고_표시',
                                '안전재고_표시',
                                '최근평균사용량_표시',
                                '예상소요량_표시',
                                '발주필요량_표시',
                                '발주단위단가_표시',
                                '예상금액'
                            ]].rename(columns={
                                '단위표시': '단위',
                                '현재고_표시': '현재고',
                                '안전재고_표시': '안전재고',
                                '최근평균사용량_표시': '최근평균사용량',
                                '예상소요량_표시': '예상소요량',
                                '발주필요량_표시': '발주필요량',
                                '발주단위단가_표시': '발주단가'
                            }),
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # 총 예상 금액 (발주단위 기준 금액 합계 사용)
                        total_amount = display_order_df['예상금액_숫자'].sum()
                        st.metric("총 예상 발주 금액", f"{int(total_amount):,}원")
                        
                        # (사용자 요청으로 Phase 3 스마트 발주 최적화/비용 비교 UI는 비활성화됨)
                        
                        # 최적화 계산 (발주단위 기준 수량/단가/금액 사용)
                        # 👉 사용자 요청으로 스마트 발주 최적화 기능은 비활성화.
                        #    나중에 다시 사용할 때를 대비해 최소한의 더미 값만 남겨둔다.
                        optimization_result = {
                            'optimized_orders': [],
                            'total_savings': 0,
                            'recommendations': [],
                            'total_delivery_fee': 0,
                            'optimized_delivery_fee': 0,
                        }
                        
                        optimized_orders = []
                        total_savings = 0
                        recommendations = []
                        
                        # 최적화 결과 표시
                        if optimized_orders:
                            # 배송비 절감 정보
                            if total_savings > 0:
                                st.success(f"💰 배송비 절감 가능: {int(total_savings):,}원 (공급업체별 통합 발주 시)")
                            
                            # 공급업체별 그룹화된 발주
                            st.write("**📦 공급업체별 통합 발주 (최적화)**")
                            
                            for supplier_name, supplier_data in optimized_orders.items():
                                with st.expander(f"🏢 {supplier_name} ({len(supplier_data['items'])}개 재료)", expanded=True):
                                    # 발주 항목 표시
                                    items_df = pd.DataFrame(supplier_data['items'])
                                    
                                    # 재료 단위 정보 추가
                                    if '발주단위' in ingredient_df.columns and '변환비율' in ingredient_df.columns:
                                        order_unit_map = dict(zip(ingredient_df['재료명'], ingredient_df['발주단위']))
                                        conversion_rate_map = dict(zip(ingredient_df['재료명'], ingredient_df['변환비율']))
                                        
                                        items_df['단위'] = items_df['재료명'].map(dict(zip(ingredient_df['재료명'], ingredient_df['단위']))).fillna('')
                                        items_df['발주단위'] = items_df['재료명'].map(order_unit_map).fillna(items_df['단위'])
                                        items_df['변환비율'] = items_df['재료명'].map(conversion_rate_map).fillna(1.0)
                                        
                                        # 단위 표시 컬럼 생성
                                        def format_unit_display(row):
                                            if pd.isna(row.get('발주단위')) or row.get('발주단위') == row.get('단위', ''):
                                                return row.get('단위', '')
                                            else:
                                                return f"{row.get('단위', '')} / 발주: {row.get('발주단위', '')}"
                                        
                                        items_df['단위표시'] = items_df.apply(format_unit_display, axis=1)
                                    else:
                                        items_df['단위표시'] = ''
                                    
                                    items_df['수량'] = items_df['수량'].apply(lambda x: f"{x:,.2f}")
                                    items_df['단가'] = items_df['단가'].apply(lambda x: f"{int(x):,}원")
                                    items_df['금액'] = items_df['금액'].apply(lambda x: f"{int(x):,}원")
                                    
                                    st.dataframe(items_df[['재료명', '단위표시', '수량', '단가', '금액']].rename(columns={'단위표시': '단위'}), use_container_width=True, hide_index=True)
                                    
                                    # 요약 정보
                                    col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
                                    with col_sum1:
                                        st.metric("총 발주금액", f"{int(supplier_data['total_amount']):,}원")
                                    with col_sum2:
                                        st.metric("배송비", f"{int(supplier_data['delivery_fee']):,}원")
                                    with col_sum3:
                                        savings = supplier_data['savings']
                                        if savings > 0:
                                            st.metric("절감액", f"{int(savings):,}원", delta=f"{int(savings):,}원")
                                        else:
                                            st.metric("절감액", "0원")
                                    with col_sum4:
                                        total_with_delivery = supplier_data['total_amount'] + supplier_data['delivery_fee']
                                        st.metric("총 비용", f"{int(total_with_delivery):,}원")
                                    
                                    # 최소 주문량 확인
                                    if supplier_data['min_order_amount'] > 0:
                                        if not supplier_data['meets_min_order']:
                                            shortage = supplier_data['min_order_amount'] - supplier_data['total_amount']
                                            st.warning(f"⚠️ 최소 주문금액 미달: {int(supplier_data['min_order_amount']):,}원 (부족: {int(shortage):,}원)")
                                        else:
                                            st.success(f"✅ 최소 주문금액 충족: {int(supplier_data['min_order_amount']):,}원")
                            
                            # 최적화 제안
                            if recommendations:
                                st.write("**💡 최적화 제안**")
                                for rec in recommendations:
                                    if rec['type'] == 'min_order':
                                        st.info(f"📌 {rec['message']}")
                            
                            # 통합 발주 vs 개별 발주 비교
                            render_section_divider()
                            st.write("**📊 비용 비교**")
                            
                            individual_total = total_amount + optimization_result['total_delivery_fee']
                            optimized_total = total_amount + optimization_result['optimized_delivery_fee']
                            
                            comp_col1, comp_col2, comp_col3 = st.columns(3)
                            with comp_col1:
                                st.markdown(f"""
                                <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px; text-align: center;">
                                    <div style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 0.5rem;">개별 발주</div>
                                    <div style="color: #ffffff; font-size: 1.3rem; font-weight: 700;">{int(individual_total):,}원</div>
                                </div>
                                """, unsafe_allow_html=True)
                            with comp_col2:
                                st.markdown(f"""
                                <div style="background: rgba(16,185,129,0.2); padding: 1rem; border-radius: 8px; text-align: center; border: 2px solid #10b981;">
                                    <div style="color: #10b981; font-size: 0.9rem; margin-bottom: 0.5rem;">통합 발주 (최적화)</div>
                                    <div style="color: #10b981; font-size: 1.3rem; font-weight: 700;">{int(optimized_total):,}원</div>
                                </div>
                                """, unsafe_allow_html=True)
                            with comp_col3:
                                savings_pct = (total_savings / individual_total * 100) if individual_total > 0 else 0
                                st.markdown(f"""
                                <div style="background: rgba(239,68,68,0.2); padding: 1rem; border-radius: 8px; text-align: center; border: 2px solid #ef4444;">
                                    <div style="color: #ef4444; font-size: 0.9rem; margin-bottom: 0.5rem;">절감액</div>
                                    <div style="color: #ef4444; font-size: 1.3rem; font-weight: 700;">{int(total_savings):,}원</div>
                                    <div style="color: #ef4444; font-size: 0.85rem; margin-top: 0.3rem;">({savings_pct:.1f}%)</div>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # 발주 생성 버튼
                        render_section_divider()
                        render_section_header("발주 생성", "📝")
                        
                        # 발주일 선택
                        from datetime import datetime, timedelta
                        col_date1, col_date2 = st.columns([1, 1])
                        with col_date1:
                            order_date = st.date_input("발주일", value=datetime.now().date(), key="order_date")
                        
                        # 발주 생성할 재료 선택 (새로운 단순 구조: 멀티셀렉트 기반)
                        st.write("**발주할 재료 선택**")
                        
                        # 멀티셀렉트용 옵션 라벨 구성
                        option_labels = []
                        label_to_name = {}
                        for _, row in display_order_df.iterrows():
                            ingredient_name = row.get('재료명')
                            if not ingredient_name:
                                continue
                            supplier_name = row.get('공급업체', '미지정')
                            qty = float(row.get('발주필요량_발주단위', row.get('발주필요량', 0)) or 0)
                            unit = row.get('발주단위', row.get('단위', ''))
                            amount = float(row.get('예상금액_숫자', row.get('예상금액', 0)) or 0)
                            
                            label = f"{ingredient_name} | {supplier_name} | {qty:,.2f}{unit} | {int(amount):,}원"
                            option_labels.append(label)
                            label_to_name[label] = ingredient_name
                        
                        if option_labels:
                            selected_labels = st.multiselect(
                                "발주할 재료를 선택하세요.",
                                options=option_labels,
                                default=option_labels,
                                key="order_select_items"
                            )
                            selected_items = [label_to_name[label] for label in selected_labels]
                        else:
                            selected_items = []
                            st.info("발주할 수 있는 재료가 없습니다.")
                        
                        # 선택된 재료 카드 표시
                        for ingredient_name in selected_items:
                            row_display_df = display_order_df[display_order_df['재료명'] == ingredient_name]
                            if row_display_df.empty:
                                continue
                            row_display = row_display_df.iloc[0]
                            
                            supplier_name = row_display.get('공급업체', '미지정')
                            qty = float(row_display.get('발주필요량_발주단위', row_display.get('발주필요량', 0)) or 0)
                            unit = row_display.get('발주단위', row_display.get('단위', ''))
                            amount = float(row_display.get('예상금액_숫자', row_display.get('예상금액', 0)) or 0)
                            
                            supplier_color = "#ef4444" if supplier_name == "미지정" else "#10b981"
                            st.markdown(f"""
                            <div style="background: rgba(255,255,255,0.05); padding: 0.75rem; border-radius: 6px; margin-bottom: 0.5rem; border-left: 3px solid {supplier_color};">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <strong style="color: #ffffff; font-size: 1rem;">{ingredient_name}</strong>
                                        <span style="color: #94a3b8; font-size: 0.85rem; margin-left: 0.5rem;">({unit})</span>
                                    </div>
                                    <div style="text-align: right;">
                                        <div style="color: #ffffff; font-size: 0.9rem;">수량: {qty:,.2f} {unit}</div>
                                        <div style="color: #94a3b8; font-size: 0.85rem;">금액: {int(amount):,}원</div>
                                    </div>
                                </div>
                                <div style="margin-top: 0.3rem; font-size: 0.8rem; color: #94a3b8;">
                                    공급업체: <span style="color: {supplier_color};">{supplier_name}</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # 선택 요약
                        if selected_items:
                            selected_mask = display_order_df['재료명'].isin(selected_items)
                            total_selected_amount = float(display_order_df.loc[selected_mask, '예상금액_숫자'].sum() or 0)
                            st.info(f"📊 선택된 재료: {len(selected_items)}개 | 총 예상 금액: {int(total_selected_amount):,}원")
                        
                        if st.button("📝 발주 생성", type="primary", key="create_order"):
                            if selected_items:
                                # 공급업체 미지정 재료 확인
                                missing_suppliers = []
                                for ingredient_name in selected_items:
                                    row_display_df = display_order_df[display_order_df['재료명'] == ingredient_name]
                                    if row_display_df.empty:
                                        # 매칭 데이터 없으면 해당 항목은 스킵 (추후 CSV/캐시 문제 방지)
                                        continue
                                    supplier_name = row_display_df['공급업체'].iloc[0] if '공급업체' in row_display_df.columns else "미지정"
                                    if supplier_name == "미지정":
                                        missing_suppliers.append(ingredient_name)
                                
                                if missing_suppliers:
                                    st.error(f"⚠️ 다음 재료의 공급업체가 지정되지 않았습니다: {', '.join(missing_suppliers)}\n공급업체 탭에서 먼저 설정해주세요.")
                                else:
                                    try:
                                        from src.storage_supabase import save_order
                                        created_count = 0
                                        failed_items = []
                                        
                                        for ingredient_name in selected_items:
                                            # 화면에 보이는 발주 기준 데이터를 우선 사용
                                            row_display_df = display_order_df[display_order_df['재료명'] == ingredient_name]
                                            if row_display_df.empty:
                                                # 매칭 데이터 없으면 해당 재료는 건너뛰고, 실패 목록에 추가
                                                failed_items.append(f"{ingredient_name} (발주 기준 데이터 없음)")
                                                continue
                                            row_display = row_display_df.iloc[0]
                                            supplier_name = row_display['공급업체']
                                            
                                            # 발주필요량(발주단위)을 소수 둘째 자리까지 사용
                                            order_qty_order_unit = float(row_display['발주필요량_발주단위'])
                                            conversion = float(row_display.get('변환비율', 1.0) or 1.0)
                                            
                                            # DB에는 기본단위 기준 수량과 단가를 저장
                                            quantity = order_qty_order_unit * conversion  # 기본단위 수량
                                            
                                            # 기본단위 단가 (실제 발주에 사용하는 단가: 공급업체 단가 우선, 없으면 재료등록 단가)
                                            supplier_price = float(row_display['사용단가_실제'])
                                            
                                            # 예상금액은 화면에서 계산한 값 사용
                                            total_amount_item = float(row_display['예상금액_숫자'])
                                            
                                            # 입고 예정일 계산 (배송일 정보 활용)
                                            expected_delivery_date = None
                                            if not suppliers_df.empty:
                                                supplier_info = suppliers_df[suppliers_df['공급업체명'] == supplier_name]
                                                if not supplier_info.empty and supplier_info.iloc[0].get('배송일'):
                                                    delivery_days = supplier_info.iloc[0]['배송일']
                                                    try:
                                                        days = int(delivery_days)
                                                        expected_delivery_date = order_date + timedelta(days=days)
                                                    except:
                                                        pass
                                            
                                            try:
                                                save_order(
                                                    order_date=order_date,
                                                    ingredient_name=ingredient_name,
                                                    supplier_name=supplier_name,
                                                    quantity=quantity,
                                                    unit_price=supplier_price,
                                                    total_amount=total_amount_item,
                                                    status="예정",
                                                    expected_delivery_date=expected_delivery_date
                                                )
                                                created_count += 1
                                            except Exception as e:
                                                failed_items.append(f"{ingredient_name} ({str(e)})")
                                        
                                        if created_count > 0:
                                            success_msg = f"✅ {created_count}개 재료의 발주가 생성되었습니다!"
                                            if failed_items:
                                                success_msg += f"\n⚠️ 실패: {len(failed_items)}개"
                                            st.success(success_msg)
                                            if failed_items:
                                                with st.expander("실패한 항목 상세", expanded=False):
                                                    for item in failed_items:
                                                        st.error(item)
                                            # 새로 생성된 발주가 알림/발주 이력/입고 예정에 즉시 반영되도록 캐시 초기화
                                            st.cache_data.clear()
                                            st.rerun()
                                        else:
                                            st.error("발주 생성에 실패했습니다. 모든 항목을 확인해주세요.")
                                    except Exception as e:
                                        st.error(f"발주 생성 중 오류가 발생했습니다: {e}")
                            else:
                                st.warning("발주할 재료를 선택해주세요.")
                        
                        # CSV 다운로드
                        render_section_divider()
                        render_section_header("발주 리스트 다운로드", "📥")
                        
                        # CSV도 화면에 보이는 발주 기준 단위/단가/금액을 기준으로 생성
                        export_df = display_order_df[[
                            '재료명',
                            '단위표시',
                            '공급업체',
                            '현재고_표시',
                            '안전재고_표시',
                            '최근평균사용량_표시',
                            '예상소요량_표시',
                            '발주필요량_표시',
                            '발주단위단가_표시',
                            '예상금액'
                        ]].rename(columns={
                            '단위표시': '단위',
                            '현재고_표시': '현재고',
                            '안전재고_표시': '안전재고',
                            '최근평균사용량_표시': '최근평균사용량',
                            '예상소요량_표시': '예상소요량',
                            '발주필요량_표시': '발주필요량',
                            '발주단위단가_표시': '발주단가'
                        })

                        csv_data = export_df.to_csv(index=False, encoding='utf-8-sig')
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
    
    # ========== 탭 4: 발주 관리 (진행 현황) ==========
    with tab4:
        render_section_header("진행 현황", "📋")
        
        from datetime import datetime
        
        # 발주 이력 로드
        orders_df = load_csv('orders.csv', default_columns=['id', '재료명', '공급업체명', '발주일', '수량', '단가', '총금액'])
        
        if not orders_df.empty:
            # 재료 정보와 조인하여 단위/발주단위/변환비율 확보
            orders_display = pd.merge(
                orders_df,
                ingredient_df[['재료명', '단위', '발주단위', '변환비율']] if not ingredient_df.empty else pd.DataFrame(columns=['재료명', '단위', '발주단위', '변환비율']),
                on='재료명',
                how='left'
            )
            orders_display['발주단위'] = orders_display['발주단위'].fillna(orders_display['단위'])
            orders_display['변환비율'] = orders_display['변환비율'].fillna(1.0)
            
            # 발주일 정리
            if '발주일' in orders_display.columns:
                orders_display['발주일'] = pd.to_datetime(orders_display['발주일'], errors='coerce')
            else:
                orders_display['발주일'] = pd.NaT
            
            # 생성 시각(배치 기준 시간) - created_at 컬럼이 있으면 사용
            if 'created_at' in orders_display.columns:
                orders_display['생성시각'] = pd.to_datetime(orders_display['created_at'], errors='coerce')
            else:
                orders_display['생성시각'] = pd.NaT
            
            # 발주 수량/단가를 발주단위 기준으로 변환
            orders_display['수량_발주단위'] = orders_display['수량'] / orders_display['변환비율']
            orders_display['발주단위단가'] = orders_display['단가'] * orders_display['변환비율']

            # 발주 생성 배치 기준 그룹 키 (초 단위까지)
            # 1) 생성시각이 있으면 초 단위로 내림(floor), 2) 없으면 발주일(날짜) 사용
            orders_display['그룹키'] = orders_display['생성시각'].dt.floor('S')
            fallback_mask = orders_display['그룹키'].isna()
            orders_display.loc[fallback_mask, '그룹키'] = orders_display.loc[fallback_mask, '발주일']
            
            # 최신 발주부터 표시
            orders_display = orders_display.sort_values('그룹키', ascending=False)
            grouped = orders_display.groupby('그룹키')
            
            for group_key, group in grouped:
                # 헤더용 일시 문자열 구성
                header_dt = pd.to_datetime(group_key, errors='coerce')
                if pd.isna(header_dt):
                    date_time_str = "발주일시 미지정"
                else:
                    date_time_str = header_dt.strftime("%Y-%m-%d %H:%M:%S")
                
                total_amount = group['총금액'].fillna(0).sum()
                
                st.markdown(f"""
                <div style="background: rgba(15,23,42,0.9); border-radius: 10px; padding: 1rem; margin-bottom: 1rem; border: 1px solid rgba(148,163,184,0.3);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <div style="font-size: 1rem; font-weight: 600; color: #e5e7eb;">📅 발주일시: {date_time_str}</div>
                        <div style="font-size: 0.95rem; color: #93c5fd;">총 발주 금액: {int(total_amount):,}원</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                display_cols = ['재료명', '공급업체명', '단위', '발주단위', '수량_발주단위', '발주단위단가', '총금액']
                disp = group[display_cols].copy()
                disp.rename(columns={
                    '단위': '사용단위',
                    '수량_발주단위': '수량(발주단위)',
                    '발주단위단가': '발주단가(발주단위)',
                }, inplace=True)
                
                disp['수량(발주단위)'] = disp['수량(발주단위)'].apply(lambda x: f"{x:,.2f}")
                disp['발주단가(발주단위)'] = disp['발주단가(발주단위)'].apply(lambda x: f"{int(x):,}원")
                disp['총금액'] = disp['총금액'].apply(lambda x: f"{int(x):,}원")
                
                st.dataframe(disp, use_container_width=True, hide_index=True)
        else:
            st.info("아직 생성된 발주 이력이 없습니다. 발주 추천 탭에서 발주를 생성해 주세요.")
    
    # ========== 탭 5: 공급업체 ==========
    with tab5:
        render_section_header("공급업체 관리", "🏢")
        
        from src.storage_supabase import save_supplier, delete_supplier, save_ingredient_supplier, delete_ingredient_supplier
        
        # 공급업체 등록
        with st.expander("➕ 공급업체 등록", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                supplier_name = st.text_input("공급업체명 *", key="new_supplier_name")
                phone = st.text_input("전화번호", key="new_supplier_phone")
                email = st.text_input("이메일", key="new_supplier_email")
            with col2:
                delivery_days = st.text_input("배송일 (일수)", key="new_supplier_delivery_days", help="예: 2 (2일 소요)")
                min_order_amount = st.number_input("최소 주문금액 (원)", min_value=0, value=0, key="new_supplier_min_order")
                delivery_fee = st.number_input("배송비 (원)", min_value=0, value=0, key="new_supplier_delivery_fee")
            
            notes = st.text_area("비고", key="new_supplier_notes")
            
            if st.button("💾 공급업체 등록", type="primary", key="save_supplier"):
                if supplier_name:
                    try:
                        save_supplier(supplier_name, phone, email, delivery_days, min_order_amount, delivery_fee, notes)
                        # Supabase 캐시 초기화 후 즉시 목록 반영
                        try:
                            st.cache_data.clear()
                        except Exception:
                            pass
                        st.success(f"✅ 공급업체 '{supplier_name}'가 등록되었습니다!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"등록 중 오류가 발생했습니다: {e}")
                else:
                    st.warning("공급업체명을 입력해주세요.")
        
        render_section_divider()
        
        # 공급업체 목록
        suppliers_df = load_csv('suppliers.csv', default_columns=['공급업체명', '전화번호', '이메일', '배송일', '최소주문금액', '배송비', '비고'])
        
        if not suppliers_df.empty:
            st.write("**📋 등록된 공급업체**")

            # 재료-공급업체 매핑을 이용해 업체별 취급 품목 목록 생성
            ingredient_suppliers_all = load_csv('ingredient_suppliers.csv', default_columns=['재료명', '공급업체명'])
            supplier_items_map = {}
            if not ingredient_suppliers_all.empty:
                for sup_name in suppliers_df['공급업체명'].tolist():
                    items = ingredient_suppliers_all[ingredient_suppliers_all['공급업체명'] == sup_name]['재료명'].dropna().unique().tolist()
                    if items:
                        supplier_items_map[sup_name] = ", ".join(items)
                    else:
                        supplier_items_map[sup_name] = ""
            else:
                supplier_items_map = {sup_name: "" for sup_name in suppliers_df['공급업체명'].tolist()}

            # 표시용 DataFrame 구성 (영문 컬럼 제거, 한글 컬럼 + 취급품목만)
            display_suppliers = suppliers_df.copy()
            # 중복 영문 컬럼 제거
            for col in ['name', 'phone', 'email', 'delivery_days', 'min_order_amount', 'delivery_fee', 'notes']:
                if col in display_suppliers.columns:
                    display_suppliers.drop(columns=[col], inplace=True)

            display_suppliers['취급품목'] = display_suppliers['공급업체명'].map(supplier_items_map).fillna("")

            display_cols = ['공급업체명', '전화번호', '이메일', '배송일', '최소주문금액', '배송비', '비고', '취급품목']
            display_cols = [c for c in display_cols if c in display_suppliers.columns]

            st.dataframe(display_suppliers[display_cols], use_container_width=True, hide_index=True)
            
            # 공급업체 삭제
            supplier_to_delete = st.selectbox("삭제할 공급업체", options=suppliers_df['공급업체명'].tolist(), key="delete_supplier_select")
            if st.button("🗑️ 공급업체 삭제", key="delete_supplier"):
                try:
                    # 삭제 전에 매핑된 품목 수 확인 (경고용)
                    mapped_count = 0
                    if not ingredient_suppliers_all.empty:
                        mapped_count = int(
                            (ingredient_suppliers_all['공급업체명'] == supplier_to_delete).sum()
                        )

                    delete_supplier(supplier_to_delete)

                    # 캐시 초기화 후 즉시 반영
                    try:
                        st.cache_data.clear()
                    except Exception:
                        pass

                    warn_suffix = f" (연결된 매핑 {mapped_count}건도 함께 삭제되었습니다.)" if mapped_count > 0 else ""
                    st.success(f"✅ 공급업체 '{supplier_to_delete}'가 삭제되었습니다!{warn_suffix}")
                    st.rerun()
                except Exception as e:
                    st.error(f"삭제 중 오류가 발생했습니다: {e}")
        else:
            st.info("등록된 공급업체가 없습니다.")
        
        render_section_divider()
        
        # 재료-공급업체 매핑
        render_section_header("재료-공급업체 매핑", "🔗")
        
        if not suppliers_df.empty and not ingredient_df.empty:
            with st.expander("➕ 재료-공급업체 매핑 추가", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    # 재료 선택 옵션에 단위 정보 표시
                    ingredient_options = []
                    if '발주단위' in ingredient_df.columns:
                        for ing in ingredient_list:
                            ing_row = ingredient_df[ingredient_df['재료명'] == ing]
                            if not ing_row.empty:
                                unit = ing_row.iloc[0].get('단위', '')
                                order_unit = ing_row.iloc[0].get('발주단위', unit)
                                if order_unit != unit:
                                    ingredient_options.append(f"{ing} ({unit} / 발주: {order_unit})")
                                else:
                                    ingredient_options.append(f"{ing} ({unit})")
                            else:
                                ingredient_options.append(ing)
                    else:
                        ingredient_options = ingredient_list
                    
                    mapping_ingredient_option = st.selectbox("재료 선택", options=ingredient_options, key="mapping_ingredient")
                    # 선택된 옵션에서 재료명 추출
                    mapping_ingredient = mapping_ingredient_option.split(" (")[0] if " (" in mapping_ingredient_option else mapping_ingredient_option
                    mapping_supplier = st.selectbox("공급업체 선택", options=suppliers_df['공급업체명'].tolist(), key="mapping_supplier")
                with col2:
                    # 발주 단위 기준 단가 입력 (원/발주단위)
                    mapping_price = st.number_input(
                        "발주 단위 기준 단가 (원/발주단위)",
                        min_value=0.0,
                        value=0.0,
                        key="mapping_price",
                        help="예: 1박스 가격, 1개 가격 등 발주 단위 기준 금액을 입력하세요."
                    )
                    is_default = st.checkbox("기본 공급업체로 설정", value=True, key="mapping_is_default")
                
                if st.button("💾 매핑 저장", type="primary", key="save_mapping"):
                    try:
                        save_ingredient_supplier(mapping_ingredient, mapping_supplier, mapping_price, is_default)
                        # 캐시 초기화 후 목록 즉시 반영
                        try:
                            st.cache_data.clear()
                        except Exception:
                            pass
                        st.success(f"✅ 매핑이 저장되었습니다! ({mapping_ingredient} → {mapping_supplier})")
                        st.rerun()
                    except Exception as e:
                        st.error(f"저장 중 오류가 발생했습니다: {e}")
            
            # 매핑 목록
            ingredient_suppliers_df = load_csv('ingredient_suppliers.csv', default_columns=['재료명', '공급업체명', '단가', '기본공급업체'])
            
            if not ingredient_suppliers_df.empty:
                st.write("**📋 재료-공급업체 매핑 목록**")
                display_mapping = ingredient_suppliers_df.copy()
                
                # 재료 단위/발주단위/변환비율/사용단가(재료등록 기준) 정보 추가
                unit_map = dict(zip(ingredient_df['재료명'], ingredient_df.get('단위', pd.Series(index=ingredient_df.index, dtype=str))))
                order_unit_map = dict(zip(ingredient_df['재료명'], ingredient_df.get('발주단위', ingredient_df.get('단위', pd.Series(index=ingredient_df.index, dtype=str)))))
                conv_map = dict(zip(ingredient_df['재료명'], ingredient_df.get('변환비율', pd.Series(index=ingredient_df.index, dtype=float)).fillna(1.0)))
                base_unit_cost_map = dict(zip(ingredient_df['재료명'], ingredient_df.get('단가', pd.Series(index=ingredient_df.index, dtype=float)).fillna(0.0)))

                # 사용단위(기본단위) / 발주단위 / 변환비율
                display_mapping['사용단위'] = display_mapping['재료명'].map(unit_map).fillna('')
                display_mapping['발주단위'] = display_mapping['재료명'].map(order_unit_map).fillna(display_mapping['사용단위'])

                # ingredient_suppliers 단가: 공급업체 매핑 기준 기본단위 단가(원/사용단위)
                base_price_series = display_mapping.get('단가', pd.Series(index=display_mapping.index, dtype=float)).fillna(0)
                conv_series = display_mapping['재료명'].map(conv_map).fillna(1.0)

                # 사용단가/발주단가 계산 (공급업체 매핑 기준)
                display_mapping['사용단가'] = (
                    base_price_series.astype(float).round(1)
                )
                display_mapping['발주단가'] = (
                    (base_price_series * conv_series).astype(float).round(1)
                )

                # 재료등록 기준 발주단가 계산 (비교용)
                ingredient_base_price_series = display_mapping['재료명'].map(base_unit_cost_map).fillna(0.0)
                ingredient_order_price_series = (ingredient_base_price_series * conv_series).astype(float)

                # 포맷팅: "x.x원/단위"
                display_mapping['사용단가'] = display_mapping.apply(
                    lambda row: f"{row['사용단가']:,.1f}원/{row['사용단위']}" if row['사용단위'] else f"{row['사용단가']:,.1f}원",
                    axis=1
                )
                display_mapping['발주단가'] = display_mapping.apply(
                    lambda row: f"{row['발주단가']:,.1f}원/{row['발주단위']}" if row['발주단위'] else f"{row['발주단가']:,.1f}원",
                    axis=1
                )

                # 재료등록 발주단가와 공급업체 발주단가 차이 경고 컬럼
                def compute_warning(row):
                    try:
                        name = row['재료명']
                        # 재료등록 기준 발주단가 숫자
                        base_unit_cost = float(base_unit_cost_map.get(name, 0.0) or 0.0)
                        conv = float(conv_map.get(name, 1.0) or 1.0)
                        ingredient_order_price = base_unit_cost * conv
                        supplier_order_price = float(base_price_series.loc[row.name]) * conv
                        # 1원 이상 차이나면 경고
                        if abs(ingredient_order_price - supplier_order_price) >= 1:
                            return "⚠️ 재료등록 발주단가와 공급업체 발주단가가 다릅니다"
                        return ""
                    except Exception:
                        return ""

                display_mapping['경고'] = display_mapping.apply(compute_warning, axis=1)

                # 기본공급업체 체크 표시
                if '기본공급업체' in display_mapping.columns:
                    display_mapping['기본공급업체'] = display_mapping['기본공급업체'].apply(lambda x: "✅" if x else "")

                # 최종 표시 컬럼: 재료명, 사용단위, 발주단위, 공급업체명, 사용단가, 발주단가, 기본공급업체, 경고
                mapping_display_cols = ['재료명', '사용단위', '발주단위', '공급업체명', '사용단가', '발주단가', '기본공급업체', '경고']
                mapping_display_cols = [col for col in mapping_display_cols if col in display_mapping.columns]
                display_mapping = display_mapping[mapping_display_cols]

                st.dataframe(display_mapping, use_container_width=True, hide_index=True)
                
                # 매핑 삭제
                if len(ingredient_suppliers_df) > 0:
                    mapping_options = [f"{row['재료명']} → {row['공급업체명']}" for idx, row in ingredient_suppliers_df.iterrows()]
                    mapping_to_delete_idx = st.selectbox("삭제할 매핑", options=range(len(mapping_options)), format_func=lambda x: mapping_options[x], key="delete_mapping_select")
                    
                    if st.button("🗑️ 매핑 삭제", key="delete_mapping"):
                        try:
                            mapping_to_delete = ingredient_suppliers_df.iloc[mapping_to_delete_idx]
                            delete_ingredient_supplier(mapping_to_delete['재료명'], mapping_to_delete['공급업체명'])
                            # 캐시 초기화 후 목록 즉시 반영
                            try:
                                st.cache_data.clear()
                            except Exception:
                                pass
                            st.success(f"✅ 매핑이 삭제되었습니다!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"삭제 중 오류가 발생했습니다: {e}")
            else:
                st.info("등록된 재료-공급업체 매핑이 없습니다.")
        else:
            st.info("공급업체와 재료를 먼저 등록해주세요.")
    
    # ========== 탭 6: 발주 분석 대시보드 (Phase 5) ==========
    with tab6:
        render_section_header("발주 분석 대시보드", "📊")
        
        from datetime import datetime, timedelta
        from src.analytics import calculate_inventory_turnover, calculate_ingredient_usage
        
        # 필요한 데이터 로드
        orders_df = load_csv('orders.csv', default_columns=['id', '재료명', '공급업체명', '발주일', '수량', '단가', '총금액', '상태', '입고예정일', '입고일', '비고'])
        inventory_df = load_csv('inventory.csv', default_columns=['재료명', '현재고', '안전재고'])
        daily_sales_df = load_csv('daily_sales_items.csv', default_columns=['날짜', '메뉴명', '판매수량'])
        recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
        suppliers_df = load_csv('suppliers.csv', default_columns=['공급업체명', '전화번호', '이메일', '배송일', '최소주문금액', '배송비', '비고'])
        
        # 재료 사용량 계산
        usage_df = pd.DataFrame()
        if not daily_sales_df.empty and not recipe_df.empty:
            usage_df = calculate_ingredient_usage(daily_sales_df, recipe_df)
        
        # ========== 5.1 재고 회전율 분석 ==========
        st.markdown("### 📈 재고 회전율 분석")
        
        if not inventory_df.empty and not usage_df.empty:
            turnover_data = []
            total_days_on_hand = 0
            valid_count = 0
            
            for idx, row in inventory_df.iterrows():
                ingredient_name = row['재료명']
                current_stock = row.get('현재고', 0)
                
                if current_stock > 0:
                    turnover_info = calculate_inventory_turnover(
                        ingredient_name,
                        usage_df,
                        inventory_df,
                        days_period=30
                    )
                    
                    if turnover_info['turnover_rate'] > 0:
                        turnover_data.append({
                            '재료명': ingredient_name,
                            '재고회전율': turnover_info['turnover_rate'],
                            '재고보유일수': turnover_info['days_on_hand'],
                            '현재고': current_stock
                        })
                        total_days_on_hand += turnover_info['days_on_hand']
                        valid_count += 1
            
            if turnover_data:
                turnover_df = pd.DataFrame(turnover_data)
                
                # 평균 재고 보유일수
                avg_days_on_hand = total_days_on_hand / valid_count if valid_count > 0 else 0
                
                # KPI 카드
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("평균 재고 보유일수", f"{avg_days_on_hand:.1f}일")
                with col2:
                    avg_turnover = turnover_df['재고회전율'].mean()
                    st.metric("평균 재고 회전율", f"{avg_turnover:.1f}회/년")
                with col3:
                    st.metric("분석 대상 재료", f"{len(turnover_df)}개")
                
                # 회전율 낮은 재료 TOP 10
                st.markdown("#### 회전율 낮은 재료 TOP 10")
                low_turnover_df = turnover_df.nsmallest(10, '재고회전율').copy()
                low_turnover_df = low_turnover_df.sort_values('재고회전율', ascending=True)
                low_turnover_df['재고회전율'] = low_turnover_df['재고회전율'].apply(lambda x: f"{x:.2f}회/년")
                low_turnover_df['재고보유일수'] = low_turnover_df['재고보유일수'].apply(lambda x: f"{int(x)}일")
                low_turnover_df['현재고'] = low_turnover_df['현재고'].apply(lambda x: f"{x:,.2f}")
                st.dataframe(low_turnover_df[['재료명', '재고회전율', '재고보유일수', '현재고']], use_container_width=True, hide_index=True)
                
                # 재료별 재고 회전율 전체 목록
                with st.expander("전체 재료별 재고 회전율", expanded=False):
                    full_turnover_df = turnover_df.sort_values('재고회전율', ascending=True).copy()
                    full_turnover_df['재고회전율'] = full_turnover_df['재고회전율'].apply(lambda x: f"{x:.2f}회/년")
                    full_turnover_df['재고보유일수'] = full_turnover_df['재고보유일수'].apply(lambda x: f"{int(x)}일")
                    full_turnover_df['현재고'] = full_turnover_df['현재고'].apply(lambda x: f"{x:,.2f}")
                    st.dataframe(full_turnover_df, use_container_width=True, hide_index=True)
            else:
                st.info("재고 회전율을 계산할 수 있는 데이터가 없습니다.")
        else:
            st.info("재고 정보와 사용량 데이터가 필요합니다.")
        
        render_section_divider()
        
        # ========== 5.2 발주 패턴 분석 ==========
        st.markdown("### 📊 발주 패턴 분석")
        
        if not orders_df.empty:
            # 발주일 컬럼이 있는지 확인
            if '발주일' in orders_df.columns:
                orders_df['발주일'] = pd.to_datetime(orders_df['발주일'], errors='coerce')
                orders_df = orders_df.dropna(subset=['발주일'])
                
                # 월별 발주 횟수/금액
                orders_df['년월'] = orders_df['발주일'].dt.to_period('M').astype(str)
                
                monthly_stats = orders_df.groupby('년월').agg({
                    'id': 'count',
                    '총금액': 'sum'
                }).reset_index()
                monthly_stats.columns = ['년월', '발주횟수', '발주금액']
                monthly_stats = monthly_stats.sort_values('년월', ascending=False)
                
                st.markdown("#### 월별 발주 통계")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**발주 횟수**")
                    display_monthly_count = monthly_stats[['년월', '발주횟수']].copy()
                    display_monthly_count.columns = ['년월', '발주 횟수']
                    st.dataframe(display_monthly_count, use_container_width=True, hide_index=True)
                
                with col2:
                    st.markdown("**발주 금액**")
                    display_monthly_amount = monthly_stats[['년월', '발주금액']].copy()
                    display_monthly_amount['발주금액'] = display_monthly_amount['발주금액'].apply(lambda x: f"{int(x):,}원")
                    display_monthly_amount.columns = ['년월', '발주 금액']
                    st.dataframe(display_monthly_amount, use_container_width=True, hide_index=True)
                
                # 공급업체별 발주 비중
                if '공급업체명' in orders_df.columns and '총금액' in orders_df.columns:
                    st.markdown("#### 공급업체별 발주 비중")
                    supplier_stats = orders_df.groupby('공급업체명').agg({
                        'id': 'count',
                        '총금액': 'sum'
                    }).reset_index()
                    supplier_stats.columns = ['공급업체명', '발주횟수', '발주금액']
                    supplier_stats = supplier_stats.sort_values('발주금액', ascending=False)
                    
                    total_amount = supplier_stats['발주금액'].sum()
                    supplier_stats['비중'] = (supplier_stats['발주금액'] / total_amount * 100).apply(lambda x: f"{x:.1f}%")
                    supplier_stats['발주금액'] = supplier_stats['발주금액'].apply(lambda x: f"{int(x):,}원")
                    
                    st.dataframe(supplier_stats, use_container_width=True, hide_index=True)
                
                # 재료별 발주 빈도
                if '재료명' in orders_df.columns:
                    st.markdown("#### 재료별 발주 빈도")
                    ingredient_freq = orders_df.groupby('재료명').agg({
                        'id': 'count',
                        '수량': 'sum',
                        '총금액': 'sum'
                    }).reset_index()
                    ingredient_freq.columns = ['재료명', '발주횟수', '총수량', '총금액']
                    ingredient_freq = ingredient_freq.sort_values('발주횟수', ascending=False)
                    
                    ingredient_freq['총수량'] = ingredient_freq['총수량'].apply(lambda x: f"{x:,.2f}")
                    ingredient_freq['총금액'] = ingredient_freq['총금액'].apply(lambda x: f"{int(x):,}원")
                    
                    st.dataframe(ingredient_freq.head(20), use_container_width=True, hide_index=True)
                
                # 발주 비용 추이 그래프 (간단한 표로 표시)
                st.markdown("#### 발주 비용 추이")
                if len(monthly_stats) > 0:
                    trend_df = monthly_stats[['년월', '발주금액']].copy()
                    trend_df['발주금액'] = trend_df['발주금액'].apply(lambda x: int(x))
                    trend_df = trend_df.sort_values('년월', ascending=True)
                    st.dataframe(trend_df, use_container_width=True, hide_index=True)
            else:
                st.info("발주일 정보가 없어 분석할 수 없습니다.")
        else:
            st.info("발주 이력이 없습니다.")
        
        render_section_divider()
        
        # ========== 5.3 비용 최적화 인사이트 ==========
        st.markdown("### 💡 비용 최적화 인사이트")
        
        if not orders_df.empty and not suppliers_df.empty:
            # 배송비 절감 기회
            st.markdown("#### 배송비 절감 기회")
            
            # 최근 30일 발주 데이터
            thirty_days_ago = datetime.now().date() - timedelta(days=30)
            if '발주일' in orders_df.columns:
                recent_orders = orders_df[pd.to_datetime(orders_df['발주일']).dt.date >= thirty_days_ago]
                
                if not recent_orders.empty and '공급업체명' in recent_orders.columns:
                    # 공급업체별 발주 횟수
                    supplier_order_count = recent_orders.groupby('공급업체명')['id'].count().reset_index()
                    supplier_order_count.columns = ['공급업체명', '발주횟수']
                    
                    # 공급업체별 배송비 정보 조인
                    if '배송비' in suppliers_df.columns:
                        supplier_order_count = supplier_order_count.merge(
                            suppliers_df[['공급업체명', '배송비']],
                            on='공급업체명',
                            how='left'
                        )
                        supplier_order_count['배송비'] = supplier_order_count['배송비'].fillna(0)
                        
                        # 배송비 절감 계산 (2회 이상 발주 시 통합 가능)
                        supplier_order_count['현재배송비'] = supplier_order_count['발주횟수'] * supplier_order_count['배송비']
                        supplier_order_count['최적화배송비'] = supplier_order_count['배송비']  # 통합 시 1회만
                        supplier_order_count['절감가능액'] = supplier_order_count['현재배송비'] - supplier_order_count['최적화배송비']
                        supplier_order_count = supplier_order_count[supplier_order_count['발주횟수'] >= 2]
                        supplier_order_count = supplier_order_count.sort_values('절감가능액', ascending=False)
                        
                        if not supplier_order_count.empty:
                            total_savings = supplier_order_count['절감가능액'].sum()
                            
                            st.success(f"💰 최근 30일 기준 배송비 절감 가능액: {int(total_savings):,}원")
                            
                            display_savings = supplier_order_count[['공급업체명', '발주횟수', '현재배송비', '최적화배송비', '절감가능액']].copy()
                            display_savings['현재배송비'] = display_savings['현재배송비'].apply(lambda x: f"{int(x):,}원")
                            display_savings['최적화배송비'] = display_savings['최적화배송비'].apply(lambda x: f"{int(x):,}원")
                            display_savings['절감가능액'] = display_savings['절감가능액'].apply(lambda x: f"{int(x):,}원")
                            display_savings.columns = ['공급업체명', '발주횟수', '현재 배송비', '최적화 배송비', '절감 가능액']
                            st.dataframe(display_savings, use_container_width=True, hide_index=True)
                        else:
                            st.info("최근 30일 동안 2회 이상 발주한 공급업체가 없습니다.")
                    else:
                        st.info("공급업체 배송비 정보가 없습니다.")
                else:
                    st.info("최근 30일 발주 이력이 없습니다.")
            else:
                st.info("발주일 정보가 없습니다.")
            
            # 가격 변동 영향 분석
            st.markdown("#### 가격 변동 영향 분석")
            
            if '재료명' in orders_df.columns and '단가' in orders_df.columns and '발주일' in orders_df.columns:
                # 재료별 최근 가격 추이
                price_trend = orders_df.groupby(['재료명', '발주일'])['단가'].mean().reset_index()
                price_trend['발주일'] = pd.to_datetime(price_trend['발주일'])
                price_trend = price_trend.sort_values(['재료명', '발주일'])
                
                # 가격 변동이 큰 재료 찾기
                price_changes = []
                for ingredient in price_trend['재료명'].unique():
                    ingredient_prices = price_trend[price_trend['재료명'] == ingredient]
                    if len(ingredient_prices) >= 2:
                        first_price = ingredient_prices.iloc[0]['단가']
                        last_price = ingredient_prices.iloc[-1]['단가']
                        if first_price > 0:
                            change_pct = ((last_price - first_price) / first_price) * 100
                            price_changes.append({
                                '재료명': ingredient,
                                '초기단가': first_price,
                                '최근단가': last_price,
                                '변동률': change_pct
                            })
                
                if price_changes:
                    price_change_df = pd.DataFrame(price_changes)
                    price_change_df = price_change_df.sort_values('변동률', key=abs, ascending=False)
                    
                    st.info("가격 변동이 큰 재료 TOP 10")
                    display_price_change = price_change_df.head(10).copy()
                    display_price_change['초기단가'] = display_price_change['초기단가'].apply(lambda x: f"{int(x):,}원")
                    display_price_change['최근단가'] = display_price_change['최근단가'].apply(lambda x: f"{int(x):,}원")
                    display_price_change['변동률'] = display_price_change['변동률'].apply(lambda x: f"{x:+.1f}%")
                    st.dataframe(display_price_change, use_container_width=True, hide_index=True)
                else:
                    st.info("가격 변동 데이터가 부족합니다.")
            else:
                st.info("가격 변동 분석을 위한 데이터가 없습니다.")
            
            # 발주 최적화 제안
            st.markdown("#### 발주 최적화 제안")
            
            if not inventory_df.empty and not usage_df.empty:
                suggestions = []
                
                # 1. 과다재고 재료
                for idx, row in inventory_df.iterrows():
                    ingredient_name = row['재료명']
                    current_stock = row.get('현재고', 0)
                    safety_stock = row.get('안전재고', 0)
                    
                    if current_stock > safety_stock * 3:  # 안전재고의 3배 이상
                        suggestions.append({
                            '유형': '과다재고',
                            '재료명': ingredient_name,
                            '제안': f"현재고({current_stock:,.2f})가 안전재고({safety_stock:,.2f})의 3배 이상입니다. 발주 빈도를 줄이거나 수량을 조정하세요."
                        })
                
                # 2. 회전율이 높은 재료 (발주 빈도 증가 고려)
                if turnover_data:
                    high_turnover = [t for t in turnover_data if t['재고회전율'] > 24]  # 연간 24회 이상
                    for item in high_turnover[:5]:  # 상위 5개만
                        suggestions.append({
                            '유형': '발주빈도증가',
                            '재료명': item['재료명'],
                            '제안': f"재고 회전율이 높습니다({item['재고회전율']:.1f}회/년). 발주 빈도를 늘려 재고 부족을 방지하세요."
                        })
                
                if suggestions:
                    suggestion_df = pd.DataFrame(suggestions)
                    st.dataframe(suggestion_df, use_container_width=True, hide_index=True)
                else:
                    st.success("현재 발주 최적화 제안사항이 없습니다.")
            else:
                st.info("발주 최적화 제안을 위한 데이터가 부족합니다.")
        else:
            st.info("발주 이력과 공급업체 정보가 필요합니다.")

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
    render_page_header("통합 대시보드", "📊")
    
    from datetime import datetime
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    # ========== 손익분기 매출 vs 목표 매출 비교 ==========
    expense_df = load_expense_structure(current_year, current_month)
    
    # 고정비 계산 (임차료, 인건비, 공과금)
    fixed_costs = 0
    if not expense_df.empty:
        fixed_categories = ['임차료', '인건비', '공과금']
        fixed_costs = expense_df[expense_df['category'].isin(fixed_categories)]['amount'].sum()
    
    # 변동비율 계산 (재료비, 부가세&카드수수료)
    variable_cost_rate = 0.0
    if not expense_df.empty:
        variable_categories = ['재료비', '부가세&카드수수료']
        variable_df = expense_df[expense_df['category'].isin(variable_categories)]
        if not variable_df.empty:
            variable_cost_rate = variable_df['amount'].sum()
    
    # 손익분기점 계산
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
        target_row = targets_df[(targets_df['연도'] == current_year) & (targets_df['월'] == current_month)]
        if not target_row.empty:
            target_sales = float(target_row.iloc[0].get('목표매출', 0))
    
    # 평일/주말 비율 (기본값: 70/30)
    weekday_ratio = 70.0
    weekend_ratio = 30.0
    
    if breakeven_sales is not None and breakeven_sales > 0:
        # 일일 손익분기 매출 계산
        weekday_daily_breakeven = (breakeven_sales * weekday_ratio / 100) / 22
        weekend_daily_breakeven = (breakeven_sales * weekend_ratio / 100) / 8
        
        # 일일 목표 매출 계산
        weekday_daily_target = 0
        weekend_daily_target = 0
        if target_sales > 0:
            weekday_daily_target = (target_sales * weekday_ratio / 100) / 22
            weekend_daily_target = (target_sales * weekend_ratio / 100) / 8
        
        # 일일 고정비 계산
        weekday_monthly_fixed = fixed_costs * (22 / 30)
        weekend_monthly_fixed = fixed_costs * (8 / 30)
        weekday_daily_fixed = weekday_monthly_fixed / 22
        weekend_daily_fixed = weekend_monthly_fixed / 8
        
        # 변동비율 소수점 변환
        variable_rate_decimal = variable_cost_rate / 100
        
        # 일일 영업이익 계산
        weekday_daily_breakeven_profit = 0
        weekend_daily_breakeven_profit = 0
        
        weekday_daily_target_profit = 0
        weekend_daily_target_profit = 0
        if target_sales > 0:
            weekday_daily_target_profit = (weekday_daily_target * (1 - variable_rate_decimal)) - weekday_daily_fixed
            weekend_daily_target_profit = (weekend_daily_target * (1 - variable_rate_decimal)) - weekend_daily_fixed
        
        # 추정 영업이익 계산
        breakeven_profit = 0
        target_profit = 0
        if target_sales > 0:
            target_profit = (target_sales * (1 - variable_rate_decimal)) - fixed_costs
        
        # 손익분기 매출 vs 목표 매출 비교 섹션
        st.markdown("""
        <div style="margin: 1rem 0 0.5rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.2rem;">
                📊 손익분기 매출 vs 목표 매출 비교
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        if breakeven_sales:
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.1); padding: 0.75rem; border-radius: 8px; margin-bottom: 0.75rem;">
                <span style="color: #ffffff; font-size: 0.85rem;">
                    계산 공식: 고정비 ÷ (1 - 변동비율) = {int(fixed_costs):,}원 ÷ (1 - {variable_cost_rate:.1f}%)
                </span>
            </div>
            """, unsafe_allow_html=True)
        
        # 월간 매출 비교
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.25rem;">
                <div style="font-size: 1.1rem; margin-bottom: 0.4rem; opacity: 0.9;">📊 손익분기 월매출</div>
                <div style="font-size: 1.5rem; font-weight: 700;">{int(breakeven_sales):,}원</div>
                <div style="font-size: 1.1rem; margin-top: 0.75rem; opacity: 0.9; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.6rem;">
                    💰 추정 영업이익
                </div>
                <div style="font-size: 1.1rem; font-weight: 600; margin-top: 0.2rem;">0원</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            if target_sales > 0:
                profit_color = "#ffd700" if target_profit > 0 else "#ff6b6b"
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); padding: 1rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.25rem;">
                    <div style="font-size: 1.1rem; margin-bottom: 0.4rem; opacity: 0.9;">🎯 목표 월매출</div>
                    <div style="font-size: 1.5rem; font-weight: 700;">{int(target_sales):,}원</div>
                    <div style="font-size: 1.1rem; margin-top: 0.75rem; opacity: 0.9; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.6rem;">
                        💰 추정 영업이익
                    </div>
                    <div style="font-size: 1.1rem; font-weight: 600; margin-top: 0.2rem; color: {profit_color};">{int(target_profit):,}원</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px; text-align: center; margin-top: 0.25rem; border: 2px dashed rgba(255,255,255,0.3);">
                    <div style="font-size: 0.85rem; margin-bottom: 0.4rem; color: #ffffff;">🎯 목표 월매출</div>
                    <div style="font-size: 0.8rem; color: rgba(255,255,255,0.7);">목표 비용구조 페이지에서 목표 매출을 설정하세요</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)
        
        # 일일 매출 비교 섹션
        st.markdown("""
        <div style="margin: 1rem 0 0.5rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.2rem;">
                📅 일일 매출 비교
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            weekday_profit_color = "#ffd700" if weekday_daily_target_profit > 0 else "#ff6b6b" if weekday_daily_target_profit < 0 else "white"
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); padding: 1rem; border-radius: 8px; color: white; margin-top: 0.25rem; text-align: right;">
                <div style="font-size: 1.1rem; margin-bottom: 0.3rem; opacity: 0.9; text-align: center;">📅 평일 일일 매출</div>
                <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 0.1rem;">일일손익분기매출: {int(weekday_daily_breakeven):,}원</div>
                {f'<div style="font-size: 1.1rem; font-weight: 700;">일일목표매출: {int(weekday_daily_target):,}원</div>' if target_sales > 0 else '<div style="font-size: 0.75rem; opacity: 0.7; margin-top: 0.2rem;">목표 매출 입력 필요</div>'}
                <div style="font-size: 1rem; margin-top: 0.7rem; opacity: 0.9; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.5rem; text-align: center;">
                    💰 일일 영업이익
                </div>
                <div style="font-size: 0.85rem; font-weight: 600; margin-top: 0.2rem; margin-bottom: 0.2rem;">손익분기시 영업이익: 0원</div>
                {f'<div style="font-size: 0.85rem; font-weight: 600; color: {weekday_profit_color};">목표시 영업이익: {int(weekday_daily_target_profit):,}원</div>' if target_sales > 0 else '<div style="font-size: 0.75rem; opacity: 0.7;">목표 매출 입력 필요</div>'}
                <div style="font-size: 0.7rem; margin-top: 0.4rem; opacity: 0.8; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.4rem;">
                    (월매출 × {weekday_ratio:.1f}% ÷ 22일)
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            weekend_profit_color = "#ffd700" if weekend_daily_target_profit > 0 else "#ff6b6b" if weekend_daily_target_profit < 0 else "white"
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%); padding: 1rem; border-radius: 8px; color: white; margin-top: 0.25rem; text-align: right;">
                <div style="font-size: 1.1rem; margin-bottom: 0.3rem; opacity: 0.9; text-align: center;">🎉 주말 일일 매출</div>
                <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 0.1rem;">일일손익분기매출: {int(weekend_daily_breakeven):,}원</div>
                {f'<div style="font-size: 1.1rem; font-weight: 700;">일일목표매출: {int(weekend_daily_target):,}원</div>' if target_sales > 0 else '<div style="font-size: 0.75rem; opacity: 0.7; margin-top: 0.2rem;">목표 매출 입력 필요</div>'}
                <div style="font-size: 1rem; margin-top: 0.7rem; opacity: 0.9; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.5rem; text-align: center;">
                    💰 일일 영업이익
                </div>
                <div style="font-size: 0.85rem; font-weight: 600; margin-top: 0.2rem; margin-bottom: 0.2rem;">손익분기시 영업이익: 0원</div>
                {f'<div style="font-size: 0.85rem; font-weight: 600; color: {weekend_profit_color};">목표시 영업이익: {int(weekend_daily_target_profit):,}원</div>' if target_sales > 0 else '<div style="font-size: 0.75rem; opacity: 0.7;">목표 매출 입력 필요</div>'}
                <div style="font-size: 0.7rem; margin-top: 0.4rem; opacity: 0.8; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.4rem;">
                    (월매출 × {weekend_ratio:.1f}% ÷ 8일)
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)
        
        # ========== 매출 수준별 비용·영업이익 시뮬레이션 ==========
        if target_sales > 0:
            # 5대 비용 세부 계산을 위한 카테고리별 데이터
            fixed_by_category = {
                '임차료': 0,
                '인건비': 0,
                '공과금': 0,
            }
            variable_rate_by_category = {
                '재료비': 0.0,
                '부가세&카드수수료': 0.0,
            }
            
            if not expense_df.empty:
                fixed_categories = ['임차료', '인건비', '공과금']
                for cat in fixed_categories:
                    fixed_by_category[cat] = expense_df[expense_df['category'] == cat]['amount'].sum()
                
                variable_categories = ['재료비', '부가세&카드수수료']
                variable_df = expense_df[expense_df['category'].isin(variable_categories)]
                if not variable_df.empty:
                    for cat in variable_categories:
                        variable_rate_by_category[cat] = variable_df[variable_df['category'] == cat]['amount'].sum()
            
            # 목표매출을 기준으로 다양한 시나리오 생성
            scenarios = [
                ("목표매출 - 1,000만원", max(target_sales - 10_000_000, 0)),
                ("목표매출 - 500만원", max(target_sales - 5_000_000, 0)),
                ("목표매출 (기준)", target_sales),
                ("목표매출 + 500만원", target_sales + 5_000_000),
                ("목표매출 + 1,000만원", target_sales + 10_000_000),
                ("목표매출 + 1,500만원", target_sales + 15_000_000),
            ]
            
            st.markdown("""
            <div style="margin: 1rem 0 0.5rem 0;">
                <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.2rem;">
                    📊 매출 수준별 비용·영업이익 시뮬레이션
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div style="background: rgba(255,255,255,0.1); padding: 0.75rem; border-radius: 8px; margin-bottom: 0.75rem;">
                <span style="color: #ffffff; font-size: 0.85rem;">
                    비용구조의 고정비와 변동비율, 목표 매출을 기준으로 다양한 매출 수준에서의 비용과 영업이익을 비교합니다.
                </span>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            cols = [col1, col2, col3]
            
            for idx, (label, sales) in enumerate(scenarios):
                if sales <= 0:
                    continue
                
                # 5대 비용 세부 계산
                rent_cost = fixed_by_category.get('임차료', 0)
                labor_cost = fixed_by_category.get('인건비', 0)
                utility_cost = fixed_by_category.get('공과금', 0)
                material_rate = variable_rate_by_category.get('재료비', 0.0) / 100
                fee_rate = variable_rate_by_category.get('부가세&카드수수료', 0.0) / 100
                material_cost = sales * material_rate
                fee_cost = sales * fee_rate
                
                total_cost = rent_cost + labor_cost + utility_cost + material_cost + fee_cost
                profit = sales - total_cost
                
                tile_col = cols[idx % 3]
                with tile_col:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 1rem; border-radius: 10px; margin-top: 0.5rem; color: #e5e7eb; box-shadow: 0 2px 6px rgba(0,0,0,0.35);">
                        <div style="font-size: 0.85rem; margin-bottom: 0.3rem; opacity: 0.9;">{label}</div>
                        <!-- 매출 영역: 선명한 흰색 -->
                        <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 0.25rem; color: #ffffff !important;">
                            매출: {int(sales):,}원
                        </div>
                        <!-- 비용 영역 제목: 더 진한 빨간색 -->
                        <div style="font-size: 0.85rem; margin-top: 0.4rem; border-top: 1px solid rgba(148,163,184,0.5); padding-top: 0.4rem; color: #ff4d4f !important;">
                            비용 합계 및 세부내역
                        </div>
                        <!-- 총 비용: 더 진한 빨간색 -->
                        <div style="font-size: 1rem; font-weight: 600; margin-bottom: 0.15rem; color: #ff4d4f !important;">
                            총 비용: {int(total_cost):,}원
                        </div>
                        <div style="font-size: 0.75rem; margin-top: 0.25rem; line-height: 1.3; color: #ff4d4f !important;">
                            임차료(고정비): {int(rent_cost):,}원<br>
                            인건비(고정비): {int(labor_cost):,}원<br>
                            공과금(고정비): {int(utility_cost):,}원<br>
                            재료비(변동비): {int(material_cost):,}원<br>
                            부가세·카드수수료(변동비): {int(fee_cost):,}원
                        </div>
                        <!-- 추정 영업이익 제목: 선명한 노란색 -->
                        <div style="font-size: 0.85rem; margin-top: 0.4rem; border-top: 1px solid rgba(148,163,184,0.5); padding-top: 0.4rem; color: #ffd700 !important;">
                            추정 영업이익
                        </div>
                        <!-- 추정 영업이익 값: 선명한 노란색 -->
                        <div style="font-size: 1rem; font-weight: 600; color: #ffd700 !important;">
                            {int(profit):,}원
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)
        
        # ========== 매출 관리 항목들 ==========
        from datetime import timedelta
        from calendar import monthrange
        
        # 매출 데이터 로드
        sales_df_dashboard = load_csv('sales.csv', default_columns=['날짜', '매장', '총매출'])
        visitors_df_dashboard = load_csv('naver_visitors.csv', default_columns=['날짜', '방문자수'])
        targets_df_dashboard = load_csv('targets.csv', default_columns=[
            '연도', '월', '목표매출', '목표원가율', '목표인건비율',
            '목표임대료율', '목표기타비용율', '목표순이익률'
        ])
        
        # 매출과 방문자 데이터 통합
        merged_df_dashboard = merge_sales_visitors(sales_df_dashboard, visitors_df_dashboard)
        
        # 날짜 컬럼을 datetime으로 변환
        if not merged_df_dashboard.empty and '날짜' in merged_df_dashboard.columns:
            merged_df_dashboard['날짜'] = pd.to_datetime(merged_df_dashboard['날짜'])
        
        # 이번달 데이터 필터링
        month_data_dashboard = merged_df_dashboard[
            (merged_df_dashboard['날짜'].dt.year == current_year) & 
            (merged_df_dashboard['날짜'].dt.month == current_month)
        ].copy() if not merged_df_dashboard.empty else pd.DataFrame()
        
        month_total_sales_dashboard = month_data_dashboard['총매출'].sum() if not month_data_dashboard.empty and '총매출' in month_data_dashboard.columns else 0
        month_total_visitors_dashboard = month_data_dashboard['방문자수'].sum() if not month_data_dashboard.empty and '방문자수' in month_data_dashboard.columns else 0
        
        # 목표 매출 확인
        target_sales_dashboard = 0
        target_row_dashboard = targets_df_dashboard[
            (targets_df_dashboard['연도'] == current_year) & 
            (targets_df_dashboard['월'] == current_month)
        ]
        if not target_row_dashboard.empty:
            target_sales_dashboard = float(target_row_dashboard.iloc[0].get('목표매출', 0))
        
        if not merged_df_dashboard.empty:
            # 1. 이번달 요약
            st.markdown("""
            <div style="margin: 1rem 0 0.5rem 0;">
                <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.2rem;">
                    📊 이번달 요약
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            if not month_data_dashboard.empty:
                month_avg_daily_sales = month_total_sales_dashboard / len(month_data_dashboard) if len(month_data_dashboard) > 0 else 0
                month_avg_daily_visitors = month_total_visitors_dashboard / len(month_data_dashboard) if len(month_data_dashboard) > 0 else 0
                avg_customer_value = month_total_sales_dashboard / month_total_visitors_dashboard if month_total_visitors_dashboard > 0 else 0
                
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("이번달 누적 매출", f"{month_total_sales_dashboard:,.0f}원")
                with col2:
                    st.metric("평균 일일 매출", f"{month_avg_daily_sales:,.0f}원")
                with col3:
                    st.metric("이번달 총 방문자", f"{int(month_total_visitors_dashboard):,}명")
                with col4:
                    st.metric("평균 객단가", f"{avg_customer_value:,.0f}원")
                with col5:
                    # 목표 달성률 계산
                    target_achievement = (month_total_sales_dashboard / target_sales_dashboard * 100) if target_sales_dashboard > 0 else None
                    if target_achievement is not None:
                        st.metric("목표 달성률", f"{target_achievement:.1f}%", 
                                f"{target_achievement - 100:.1f}%p" if target_achievement != 100 else "0%p")
                    else:
                        st.metric("목표 달성률", "-", help="목표 매출이 설정되지 않았습니다")
            
            st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)
            
            # 2. 저장된 매출 내역
            st.markdown("""
            <div style="margin: 1rem 0 0.5rem 0;">
                <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.2rem;">
                    📋 저장된 매출 내역
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            if not merged_df_dashboard.empty:
                # 통합 데이터 표시
                display_df_dashboard = merged_df_dashboard.copy()
                
                # 표시할 컬럼만 선택
                display_columns = []
                if '날짜' in display_df_dashboard.columns:
                    display_columns.append('날짜')
                if '매장' in display_df_dashboard.columns:
                    display_columns.append('매장')
                if '카드매출' in display_df_dashboard.columns:
                    display_columns.append('카드매출')
                if '현금매출' in display_df_dashboard.columns:
                    display_columns.append('현금매출')
                if '총매출' in display_df_dashboard.columns:
                    display_columns.append('총매출')
                if '방문자수' in display_df_dashboard.columns:
                    display_columns.append('방문자수')
                
                # 필요한 컬럼만 선택
                if display_columns:
                    display_df_dashboard = display_df_dashboard[display_columns]
                    
                    # 날짜를 문자열로 변환
                    if '날짜' in display_df_dashboard.columns:
                        display_df_dashboard['날짜'] = pd.to_datetime(display_df_dashboard['날짜']).dt.strftime('%Y-%m-%d')
                    
                    # 숫자 포맷팅
                    if '총매출' in display_df_dashboard.columns:
                        display_df_dashboard['총매출'] = display_df_dashboard['총매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                    if '카드매출' in display_df_dashboard.columns:
                        display_df_dashboard['카드매출'] = display_df_dashboard['카드매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                    if '현금매출' in display_df_dashboard.columns:
                        display_df_dashboard['현금매출'] = display_df_dashboard['현금매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                    if '방문자수' in display_df_dashboard.columns:
                        display_df_dashboard['방문자수'] = display_df_dashboard['방문자수'].apply(lambda x: f"{int(x):,}명" if pd.notna(x) else "-")
                
                st.dataframe(display_df_dashboard, use_container_width=True, hide_index=True)
            
            st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)
            
            # 3. 월별 요약 (최근 6개월)
            st.markdown("""
            <div style="margin: 1rem 0 0.5rem 0;">
                <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.2rem;">
                    📋 월별 요약 (최근 6개월)
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            # 최근 6개월 데이터
            today_dashboard = datetime.now().date()
            six_months_ago = today_dashboard - timedelta(days=180)
            recent_6m_data = merged_df_dashboard[merged_df_dashboard['날짜'].dt.date >= six_months_ago].copy()
            
            if not recent_6m_data.empty:
                recent_6m_data['연도'] = recent_6m_data['날짜'].dt.year
                recent_6m_data['월'] = recent_6m_data['날짜'].dt.month
                
                monthly_summary = recent_6m_data.groupby(['연도', '월']).agg({
                    '총매출': ['sum', 'mean', 'count'],
                    '방문자수': ['sum', 'mean']
                }).reset_index()
                monthly_summary.columns = ['연도', '월', '월총매출', '일평균매출', '영업일수', '월총방문자', '일평균방문자']
                monthly_summary['월별객단가'] = monthly_summary['월총매출'] / monthly_summary['월총방문자']
                monthly_summary = monthly_summary.sort_values(['연도', '월'], ascending=[False, False])
                
                # 성장률 계산
                monthly_summary['전월대비'] = monthly_summary['월총매출'].pct_change() * 100
                
                display_monthly = monthly_summary.head(6).copy()
                display_monthly['월'] = display_monthly['월'].apply(lambda x: f"{int(x)}월")
                display_monthly['월총매출'] = display_monthly['월총매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                display_monthly['일평균매출'] = display_monthly['일평균매출'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                display_monthly['월총방문자'] = display_monthly['월총방문자'].apply(lambda x: f"{int(x):,}명" if pd.notna(x) else "-")
                display_monthly['월별객단가'] = display_monthly['월별객단가'].apply(lambda x: f"{int(x):,}원" if pd.notna(x) else "-")
                display_monthly['전월대비'] = display_monthly['전월대비'].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "-")
                
                st.dataframe(
                    display_monthly[['연도', '월', '영업일수', '월총매출', '일평균매출', '월총방문자', '월별객단가', '전월대비']],
                    use_container_width=True,
                    hide_index=True
                )
        
        st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)
        
        # ========== 판매 ABC 분석 ==========
        
        # 판매 데이터 로드
        menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
        daily_sales_df = load_csv('daily_sales_items.csv', default_columns=['날짜', '메뉴명', '판매수량'])
        recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
        ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가'])
        
        if not daily_sales_df.empty and not menu_df.empty:
            # 날짜 변환
            daily_sales_df['날짜'] = pd.to_datetime(daily_sales_df['날짜'])
            
            # 이번 달 데이터 필터링
            start_of_month = datetime(current_year, current_month, 1).date()
            days_in_month = (datetime(current_year, current_month + 1, 1) - timedelta(days=1)).day if current_month < 12 else 31
            end_of_month = datetime(current_year, current_month, days_in_month).date()
            
            filtered_sales_df = daily_sales_df[
                (daily_sales_df['날짜'].dt.date >= start_of_month) & 
                (daily_sales_df['날짜'].dt.date <= end_of_month)
            ].copy()
            
            if not filtered_sales_df.empty:
                # 메뉴별 총 판매수량 집계
                sales_summary = (
                    filtered_sales_df.groupby('메뉴명')['판매수량']
                    .sum()
                    .reset_index()
                )
                sales_summary.columns = ['메뉴명', '판매수량']
                
                # 메뉴 마스터와 조인하여 판매가 가져오기
                summary_df = pd.merge(
                    sales_summary,
                    menu_df[['메뉴명', '판매가']],
                    on='메뉴명',
                    how='left',
                )
                
                # 매출 금액 계산
                summary_df['매출'] = summary_df['판매수량'] * summary_df['판매가']
                
                # 원가 정보 계산
                if not recipe_df.empty and not ingredient_df.empty:
                    cost_df = calculate_menu_cost(menu_df, recipe_df, ingredient_df)
                    summary_df = pd.merge(
                        summary_df,
                        cost_df[['메뉴명', '원가']],
                        on='메뉴명',
                        how='left',
                    )
                    summary_df['원가'] = summary_df['원가'].fillna(0)
                    summary_df['총판매원가'] = summary_df['판매수량'] * summary_df['원가']
                    summary_df['이익'] = summary_df['매출'] - summary_df['총판매원가']
                    summary_df['이익률'] = (summary_df['이익'] / summary_df['매출'] * 100).round(2)
                    summary_df['원가율'] = (summary_df['원가'] / summary_df['판매가'] * 100).round(2)
                else:
                    summary_df['원가'] = 0
                    summary_df['총판매원가'] = 0
                    summary_df['이익'] = summary_df['매출']
                    summary_df['이익률'] = 0
                    summary_df['원가율'] = 0
                
                # 총 매출 계산
                total_revenue = summary_df['매출'].sum()
                
                if total_revenue > 0:
                    st.markdown("""
                    <div style="margin: 1rem 0 0.5rem 0;">
                        <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.2rem;">
                            📊 판매 ABC 분석
                        </h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # ABC 분석
                    summary_df = summary_df.sort_values('매출', ascending=False)
                    summary_df['비율(%)'] = (summary_df['매출'] / total_revenue * 100).round(2)
                    summary_df['누계 비율(%)'] = summary_df['비율(%)'].cumsum().round(2)
                    
                    # ABC 등급 부여
                    def assign_abc_grade(cumulative_ratio):
                        if cumulative_ratio <= 70:
                            return 'A'
                        elif cumulative_ratio <= 90:
                            return 'B'
                        else:
                            return 'C'
                    
                    summary_df['ABC 등급'] = summary_df['누계 비율(%)'].apply(assign_abc_grade)
                    
                    # ABC 등급별 통계
                    abc_stats = summary_df.groupby('ABC 등급').agg({
                        '메뉴명': 'count',
                        '매출': 'sum',
                        '판매수량': 'sum'
                    }).reset_index()
                    abc_stats.columns = ['ABC 등급', '메뉴 수', '총 매출', '총 판매수량']
                    abc_stats['매출 비율(%)'] = (abc_stats['총 매출'] / total_revenue * 100).round(2)
                    
                    # ABC 등급별 통계 카드
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        a_count = abc_stats[abc_stats['ABC 등급'] == 'A']['메뉴 수'].values[0] if not abc_stats[abc_stats['ABC 등급'] == 'A'].empty else 0
                        a_revenue = abc_stats[abc_stats['ABC 등급'] == 'A']['총 매출'].values[0] if not abc_stats[abc_stats['ABC 등급'] == 'A'].empty else 0
                        a_ratio = abc_stats[abc_stats['ABC 등급'] == 'A']['매출 비율(%)'].values[0] if not abc_stats[abc_stats['ABC 등급'] == 'A'].empty else 0
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 1rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.25rem;">
                            <div style="font-size: 1rem; margin-bottom: 0.4rem; opacity: 0.9;">🟢 A등급</div>
                            <div style="font-size: 1.3rem; font-weight: 700; margin-bottom: 0.25rem;">{int(a_count)}개 메뉴</div>
                            <div style="font-size: 1rem; margin-bottom: 0.25rem;">{int(a_revenue):,}원</div>
                            <div style="font-size: 0.85rem; opacity: 0.8;">매출 비중: {a_ratio:.1f}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        b_count = abc_stats[abc_stats['ABC 등급'] == 'B']['메뉴 수'].values[0] if not abc_stats[abc_stats['ABC 등급'] == 'B'].empty else 0
                        b_revenue = abc_stats[abc_stats['ABC 등급'] == 'B']['총 매출'].values[0] if not abc_stats[abc_stats['ABC 등급'] == 'B'].empty else 0
                        b_ratio = abc_stats[abc_stats['ABC 등급'] == 'B']['매출 비율(%)'].values[0] if not abc_stats[abc_stats['ABC 등급'] == 'B'].empty else 0
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 1rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.25rem;">
                            <div style="font-size: 1rem; margin-bottom: 0.4rem; opacity: 0.9;">🟡 B등급</div>
                            <div style="font-size: 1.3rem; font-weight: 700; margin-bottom: 0.25rem;">{int(b_count)}개 메뉴</div>
                            <div style="font-size: 1rem; margin-bottom: 0.25rem;">{int(b_revenue):,}원</div>
                            <div style="font-size: 0.85rem; opacity: 0.8;">매출 비중: {b_ratio:.1f}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col3:
                        c_count = abc_stats[abc_stats['ABC 등급'] == 'C']['메뉴 수'].values[0] if not abc_stats[abc_stats['ABC 등급'] == 'C'].empty else 0
                        c_revenue = abc_stats[abc_stats['ABC 등급'] == 'C']['총 매출'].values[0] if not abc_stats[abc_stats['ABC 등급'] == 'C'].empty else 0
                        c_ratio = abc_stats[abc_stats['ABC 등급'] == 'C']['매출 비율(%)'].values[0] if not abc_stats[abc_stats['ABC 등급'] == 'C'].empty else 0
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); padding: 1rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.25rem;">
                            <div style="font-size: 1rem; margin-bottom: 0.4rem; opacity: 0.9;">🔴 C등급</div>
                            <div style="font-size: 1.3rem; font-weight: 700; margin-bottom: 0.25rem;">{int(c_count)}개 메뉴</div>
                            <div style="font-size: 1rem; margin-bottom: 0.25rem;">{int(c_revenue):,}원</div>
                            <div style="font-size: 0.85rem; opacity: 0.8;">매출 비중: {c_ratio:.1f}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # TOP 10 메뉴 표시
                    st.markdown("""
                    <div style="margin: 1rem 0 0.5rem 0;">
                        <h4 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.1rem;">
                            🏆 ABC 분석 TOP 10 메뉴
                        </h4>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    top10_df = summary_df.head(10).copy()
                    top10_df.insert(0, '순위', range(1, len(top10_df) + 1))
                    
                    # 표시용 포맷팅
                    display_top10 = top10_df.copy()
                    display_top10['판매수량'] = display_top10['판매수량'].apply(lambda x: f"{int(x):,}개")
                    display_top10['매출'] = display_top10['매출'].apply(lambda x: f"{int(x):,}원")
                    display_top10['비율(%)'] = display_top10['비율(%)'].apply(lambda x: f"{x:.2f}%")
                    display_top10['누계 비율(%)'] = display_top10['누계 비율(%)'].apply(lambda x: f"{x:.2f}%")
                    
                    st.dataframe(
                        display_top10[['순위', '메뉴명', '판매수량', '매출', '비율(%)', '누계 비율(%)', 'ABC 등급']],
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)
                    
                    # ========== 재료 사용량 TOP 10 ==========
                    # 재료 사용량 계산
                    usage_df = calculate_ingredient_usage(filtered_sales_df, recipe_df)
                    
                    if not usage_df.empty and not ingredient_df.empty:
                        # 재료 단가와 조인하여 총 사용 단가 계산
                        usage_df = pd.merge(
                            usage_df,
                            ingredient_df[['재료명', '단가']],
                            on='재료명',
                            how='left'
                        )
                        usage_df['단가'] = usage_df['단가'].fillna(0)
                        usage_df['총사용단가'] = usage_df['총사용량'] * usage_df['단가']
                        
                        # 재료별 총 사용량/총 사용 단가 집계
                        ingredient_summary = (
                            usage_df
                            .groupby('재료명')[['총사용량', '총사용단가']]
                            .sum()
                            .reset_index()
                        )
                        
                        # 사용 단가 기준으로 정렬
                        ingredient_summary = ingredient_summary.sort_values('총사용단가', ascending=False)
                        
                        # 총 사용단가 합계 계산
                        total_cost = ingredient_summary['총사용단가'].sum()
                        
                        if total_cost > 0:
                            # 비율 및 누적 비율 계산
                            ingredient_summary['비율(%)'] = (ingredient_summary['총사용단가'] / total_cost * 100).round(2)
                            ingredient_summary['누적 비율(%)'] = ingredient_summary['비율(%)'].cumsum().round(2)
                            
                            # ABC 등급 부여
                            def assign_abc_grade_ingredient(cumulative_ratio):
                                if cumulative_ratio <= 70:
                                    return 'A'
                                elif cumulative_ratio <= 90:
                                    return 'B'
                                else:
                                    return 'C'
                            
                            ingredient_summary['ABC 등급'] = ingredient_summary['누적 비율(%)'].apply(assign_abc_grade_ingredient)
                            
                            st.markdown("""
                            <div style="margin: 1rem 0 0.5rem 0;">
                                <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.2rem;">
                                    📦 재료 사용 단가 TOP 10
                                </h3>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # TOP 10 재료
                            top10_ingredients = ingredient_summary.head(10).copy()
                            top10_ingredients.insert(0, '순위', range(1, len(top10_ingredients) + 1))
                            
                            # 표시용 포맷팅
                            display_top10_ingredients = top10_ingredients.copy()
                            display_top10_ingredients['총 사용량'] = display_top10_ingredients['총사용량'].apply(lambda x: f"{x:,.2f}")
                            display_top10_ingredients['총 사용단가'] = display_top10_ingredients['총사용단가'].apply(lambda x: f"{int(x):,}원")
                            display_top10_ingredients['비율(%)'] = display_top10_ingredients['비율(%)'].apply(lambda x: f"{x:.2f}%")
                            display_top10_ingredients['누적 비율(%)'] = display_top10_ingredients['누적 비율(%)'].apply(lambda x: f"{x:.2f}%")
                            
                            st.dataframe(
                                display_top10_ingredients[['순위', '재료명', '총 사용량', '총 사용단가', '비율(%)', '누적 비율(%)', 'ABC 등급']],
                                use_container_width=True,
                                hide_index=True
                            )
                            
                            # TOP 10 총합계
                            top10_total = top10_ingredients['총사용단가'].sum()
                            st.markdown(f"""
                            <div style="background: rgba(255,255,255,0.1); padding: 0.75rem; border-radius: 8px; margin-top: 0.75rem;">
                                <span style="color: #ffffff; font-size: 0.9rem; font-weight: 600;">
                                    💰 TOP 10 총 사용단가 합계: {int(top10_total):,}원
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)
                    
                    # ========== 레시피 검색 및 수정 ==========
                    recipe_df_dashboard = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
                    
                    if not recipe_df_dashboard.empty:
                        # 레시피가 있는 메뉴 목록 추출
                        menus_with_recipes = recipe_df_dashboard['메뉴명'].unique().tolist()
                        
                        if menus_with_recipes:
                            st.markdown("""
                            <div style="margin: 1rem 0 0.5rem 0;">
                                <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.2rem;">
                                    🔍 레시피 검색 및 수정
                                </h3>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # 메뉴 선택
                            filter_menu = st.selectbox(
                                "메뉴 선택",
                                options=menus_with_recipes,
                                key="dashboard_recipe_filter_menu",
                                index=0 if menus_with_recipes else None
                            )
                            
                            # 선택한 메뉴의 레시피만 필터링
                            display_recipe_df = recipe_df_dashboard[recipe_df_dashboard['메뉴명'] == filter_menu].copy()
                            
                            if not display_recipe_df.empty:
                                # 재료 정보와 조인하여 단위 및 단가 표시
                                display_recipe_df = pd.merge(
                                    display_recipe_df,
                                    ingredient_df[['재료명', '단위', '단가']],
                                    on='재료명',
                                    how='left'
                                )
                                
                                # 원가 계산
                                menu_cost_df = calculate_menu_cost(menu_df, recipe_df_dashboard, ingredient_df)
                                menu_cost_info = menu_cost_df[menu_cost_df['메뉴명'] == filter_menu]
                                
                                # 메뉴 정보 가져오기
                                menu_info = menu_df[menu_df['메뉴명'] == filter_menu]
                                menu_price = int(menu_info.iloc[0]['판매가']) if not menu_info.empty else 0
                                
                                # 조리방법 가져오기 (menu_master에서)
                                cooking_method_text = ""
                                try:
                                    from src.auth import get_supabase_client, get_current_store_id
                                    supabase = get_supabase_client()
                                    store_id = get_current_store_id()
                                    if supabase and store_id:
                                        menu_result = supabase.table("menu_master").select("cooking_method").eq("store_id", store_id).eq("name", filter_menu).execute()
                                        if menu_result.data and menu_result.data[0].get('cooking_method'):
                                            cooking_method_text = menu_result.data[0]['cooking_method']
                                except Exception:
                                    pass
                                
                                # 원가 정보
                                cost = int(menu_cost_info.iloc[0]['원가']) if not menu_cost_info.empty else 0
                                cost_rate = float(menu_cost_info.iloc[0]['원가율']) if not menu_cost_info.empty else 0
                                
                                # 메뉴 정보 카드
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.markdown(f"""
                                    <div style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); padding: 1rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.25rem;">
                                        <div style="font-size: 0.85rem; margin-bottom: 0.4rem; opacity: 0.9;">판매가</div>
                                        <div style="font-size: 1.3rem; font-weight: 700;">{menu_price:,}원</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                with col2:
                                    st.markdown(f"""
                                    <div style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); padding: 1rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.25rem;">
                                        <div style="font-size: 0.85rem; margin-bottom: 0.4rem; opacity: 0.9;">원가</div>
                                        <div style="font-size: 1.3rem; font-weight: 700;">{cost:,}원</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                with col3:
                                    st.markdown(f"""
                                    <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 1rem; border-radius: 8px; text-align: center; color: white; margin-top: 0.25rem;">
                                        <div style="font-size: 0.85rem; margin-bottom: 0.4rem; opacity: 0.9;">원가율</div>
                                        <div style="font-size: 1.3rem; font-weight: 700;">{cost_rate:.1f}%</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                # 구성 재료 및 사용량 테이블
                                st.markdown("""
                                <div style="margin: 1rem 0 0.5rem 0;">
                                    <h4 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.1rem;">
                                        📋 구성 재료 및 사용량
                                    </h4>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # 테이블 데이터 준비
                                table_data = []
                                for idx, row in display_recipe_df.iterrows():
                                    ing_name = row['재료명']
                                    unit = row['단위'] if pd.notna(row['단위']) else ""
                                    current_qty = float(row['사용량'])
                                    unit_price = float(row['단가']) if pd.notna(row['단가']) else 0
                                    ingredient_cost = current_qty * unit_price
                                    
                                    table_data.append({
                                        '재료명': ing_name,
                                        '기준단위': unit,
                                        '사용량': f"{current_qty:.2f}",
                                        '1단위 단가': f"{unit_price:,.1f}원",
                                        '재료비': f"{ingredient_cost:,.1f}원"
                                    })
                                
                                # 테이블 표시
                                ingredients_table_df = pd.DataFrame(table_data)
                                st.dataframe(ingredients_table_df, use_container_width=True, hide_index=True)
                                
                                # 조리방법 표시
                                st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)
                                st.markdown("""
                                <div style="margin: 1rem 0 0.5rem 0;">
                                    <h4 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.1rem;">
                                        👨‍🍳 조리방법
                                    </h4>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                if cooking_method_text:
                                    st.markdown(f"""
                                    <div style="background: rgba(30, 41, 59, 0.5); padding: 1rem; border-radius: 12px; 
                                                border-left: 4px solid #667eea; margin: 0.75rem 0;">
                                        <div style="color: #e5e7eb; font-size: 0.9rem; line-height: 1.6; white-space: pre-wrap;">
                                            {cooking_method_text.replace(chr(10), '<br>')}
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.info("조리방법이 등록되지 않았습니다.")
                    
    else:
        st.info("손익분기 매출을 계산하려면 목표 비용구조 페이지에서 고정비와 변동비율을 입력해주세요.")

# 목표 비용구조 페이지 (비용구조와 동일)
elif page == "목표 비용구조" or page == "비용구조":
    # 비용구조 페이지 전용 헤더 (화이트 모드에서도 항상 흰색 텍스트로 표시)
    header_color = "#ffffff"
    page_title = "목표 비용구조 관리" if page == "목표 비용구조" else "비용구조 관리"
    st.markdown(f"""
    <div style="margin: 0 0 1.0rem 0;">
        <h2 style="color: {header_color}; font-weight: 700; margin: 0;">
            💳 {page_title}
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
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
        # 평일/주말 비율 입력 - 공통 info-box 스타일 사용
        st.markdown("""
        <div class="info-box">
            <strong>📅 평일/주말 매출 비율 설정</strong>
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
        
        # 목표 월매출 입력 - 공통 info-box 스타일 사용
        st.markdown("""
        <div class="info-box">
            <strong>🎯 목표 월매출 설정</strong>
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
            
            # 손익분기 매출과 목표 매출 비교 - 공통 info-box 스타일 사용 + 계산 공식 안내
            st.markdown(f"""
            <div class="info-box">
                <strong>📊 손익분기 매출 vs 목표 매출 비교</strong><br>
                <span style="font-size: 0.85rem; opacity: 0.95;">
                    계산 공식: 고정비 ÷ (1 - 변동비율) = {int(fixed_costs):,}원 ÷ (1 - {variable_cost_rate:.1f}%)
                </span>
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
                    <div style="font-size: 1.35rem; margin-bottom: 0.5rem; opacity: 0.9;">📊 손익분기 월매출</div>
                    <div style="font-size: 1.8rem; font-weight: 700;">{int(breakeven_sales):,}원</div>
                    <div style="font-size: 1.35rem; margin-top: 1rem; opacity: 0.9; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.8rem;">
                        💰 추정 영업이익
                    </div>
                    <div style="font-size: 1.3rem; font-weight: 600; margin-top: 0.3rem;">0원</div>
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
                    <div style="font-size: 1.35rem; margin-bottom: 0.5rem; opacity: 0.9;">🎯 목표 월매출</div>
                        <div style="font-size: 1.8rem; font-weight: 700;">{int(target_sales_input):,}원</div>
                    <div style="font-size: 1.35rem; margin-top: 1rem; opacity: 0.9; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.8rem;">
                        💰 추정 영업이익
                    </div>
                        <div style="font-size: 1.3rem; font-weight: 600; margin-top: 0.3rem; color: {profit_color};">{int(target_profit):,}원</div>
                        <!-- 차이(원, %) 표시는 제거하여 박스를 더 단순하게 유지 -->
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 8px; text-align: center; margin-top: 0.5rem; border: 2px dashed #dee2e6;">
                        <div style="font-size: 0.9rem; margin-bottom: 0.5rem; color: #6c757d;">🎯 목표 월매출</div>
                        <div style="font-size: 0.85rem; color: #6c757d;">위에서 목표 매출을 입력하세요</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # 일일 매출 비교 - 공통 info-box 스타일 사용
            st.markdown("""
            <div class="info-box">
                <strong>📅 일일 매출 비교</strong>
            </div>
            """, unsafe_allow_html=True)
            
            # 평일 일일 매출
            col1, col2 = st.columns(2)
            with col1:
                weekday_profit_color = "#ffd700" if weekday_daily_target_profit > 0 else "#ff6b6b" if weekday_daily_target_profit < 0 else "white"
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); padding: 1.5rem; border-radius: 8px; color: white; margin-top: 0.5rem; text-align: right;">
                    <div style="font-size: 1.3rem; margin-bottom: 0.4rem; opacity: 0.9; text-align: center;">📅 평일 일일 매출</div>
                    <div style="font-size: 1.3rem; font-weight: 700; margin-bottom: 0.1rem;">일일손익분기매출: {int(weekday_daily_breakeven):,}원</div>
                    {f'<div style="font-size: 1.3rem; font-weight: 700;">일일목표매출: {int(weekday_daily_target):,}원</div>' if target_sales_input > 0 else '<div style="font-size: 0.8rem; opacity: 0.7; margin-top: 0.2rem;">목표 매출 입력 필요</div>'}
                    <div style="font-size: 1.275rem; margin-top: 0.9rem; opacity: 0.9; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.7rem; text-align: center;">
                        💰 일일 영업이익
                    </div>
                    <div style="font-size: 0.95rem; font-weight: 600; margin-top: 0.25rem; margin-bottom: 0.25rem;">손익분기시 영업이익: 0원</div>
                    {f'<div style="font-size: 0.95rem; font-weight: 600; color: {weekday_profit_color};">목표시 영업이익: {int(weekday_daily_target_profit):,}원</div>' if target_sales_input > 0 else '<div style="font-size: 0.8rem; opacity: 0.7;">목표 매출 입력 필요</div>'}
                    <div style="font-size: 0.75rem; margin-top: 0.5rem; opacity: 0.8; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.5rem;">
                        (월매출 × {weekday_ratio:.1f}% ÷ 22일)
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                weekend_profit_color = "#ffd700" if weekend_daily_target_profit > 0 else "#ff6b6b" if weekend_daily_target_profit < 0 else "white"
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%); padding: 1.5rem; border-radius: 8px; color: white; margin-top: 0.5rem; text-align: right;">
                    <div style="font-size: 1.3rem; margin-bottom: 0.4rem; opacity: 0.9; text-align: center;">🎉 주말 일일 매출</div>
                    <div style="font-size: 1.3rem; font-weight: 700; margin-bottom: 0.1rem;">일일손익분기매출: {int(weekend_daily_breakeven):,}원</div>
                    {f'<div style="font-size: 1.3rem; font-weight: 700;">일일목표매출: {int(weekend_daily_target):,}원</div>' if target_sales_input > 0 else '<div style="font-size: 0.8rem; opacity: 0.7; margin-top: 0.2rem;">목표 매출 입력 필요</div>'}
                    <div style="font-size: 1.275rem; margin-top: 1rem; opacity: 0.9; border-top: 1px solid rgba(255,255,255,0.3); padding-top: 0.7rem; text-align: center;">
                        💰 일일 영업이익
                    </div>
                    <div style="font-size: 0.95rem; font-weight: 600; margin-top: 0.25rem; margin-bottom: 0.25rem;">손익분기시 영업이익: 0원</div>
                    {f'<div style="font-size: 0.95rem; font-weight: 600; color: {weekend_profit_color};">목표시 영업이익: {int(weekend_daily_target_profit):,}원</div>' if target_sales_input > 0 else '<div style="font-size: 0.8rem; opacity: 0.7;">목표 매출 입력 필요</div>'}
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
            # 화이트 테마일 때도 비용구조 카테고리 텍스트는 흰색으로 보이도록 색상 분기
            header_color = "#ffffff" if st.session_state.get("theme", "light") == "light" else "#ffffff"
            st.markdown(f"""
            <div style="margin: 1.5rem 0 0.5rem 0;">
                <h3 style="color: {header_color}; font-weight: 600; margin: 0;">
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
            # 기존 항목은 기본적으로 펼쳐 두고, 필요시 사용자가 접을 수 있게 처리
            with st.expander(f"📋 기존 입력된 항목 ({len(existing_items[category])}개)", expanded=True):
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
                                        # 캐시된 비용구조 데이터를 무효화하여 즉시 반영되도록 처리
                                        try:
                                            load_expense_structure.clear()
                                        except Exception:
                                            pass
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
                        # 마지막 두 컬럼(✏️, 🗑️ 버튼) 간격이 화면이 넓어져도 너무 벌어지지 않도록
                        # 버튼 컬럼 자체의 비율을 줄여 간격을 일정하게 보이게 조정
                        col1, col2, col3, col4, col5 = st.columns([6, 4, 1.2, 0.6, 0.6])
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
                                    try:
                                        load_expense_structure.clear()
                                    except Exception:
                                        pass
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
                                    try:
                                        load_expense_structure.clear()
                                    except Exception:
                                        pass
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
                                    try:
                                        load_expense_structure.clear()
                                    except Exception:
                                        pass
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
                
                # 변동비율 기준 (위험: 50% 이상, 주의: 40-50%, 정상: 40% 미만)
                if variable_cost_rate >= 50:
                    alerts.append("🔴 변동비율이 50% 이상입니다. 원가 관리가 시급합니다.")
                elif variable_cost_rate >= 40:
                    alerts.append("🟡 변동비율이 40% 이상입니다. 주의가 필요합니다.")
                else:
                    alerts.append("✅ 변동비율이 정상 범위입니다.")
                
                # 고정비 기준 (위험: 목표 매출의 30% 이상, 주의: 20-30%, 정상: 20% 미만)
                fixed_cost_ratio = (fixed_costs / target_sales_input * 100) if target_sales_input > 0 else 0
                if fixed_cost_ratio >= 30:
                    alerts.append("🔴 고정비가 목표 매출의 30% 이상입니다. 고정비 절감이 필요합니다.")
                elif fixed_cost_ratio >= 20:
                    alerts.append("🟡 고정비가 목표 매출의 20% 이상입니다. 주의가 필요합니다.")
                else:
                    alerts.append("✅ 고정비가 정상 범위입니다.")
                
                # 총 비용률 기준 (위험: 90% 이상, 주의: 80-90%, 정상: 80% 미만)
                if expense_ratio >= 90:
                    alerts.append("🔴 총 비용률이 90% 이상입니다. 수익성이 매우 낮습니다.")
                elif expense_ratio >= 80:
                    alerts.append("🟡 총 비용률이 80% 이상입니다. 비용 절감이 필요합니다.")
                else:
                    alerts.append("✅ 총 비용률이 정상 범위입니다.")
                
                # 알림 표시
                for alert in alerts:
                    if "🔴" in alert:
                        st.error(alert)
                    elif "🟡" in alert:
                        st.warning(alert)
                    else:
                        st.success(alert)
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

# 목표 매출구조 페이지 (매출구조와 동일)
elif page == "목표 매출구조" or page == "매출구조":
    page_title = "목표 매출구조 분석" if page == "목표 매출구조" else "매출구조 분석"
    render_page_header(page_title, "📈")
    
    from datetime import datetime
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    # 비용구조 페이지에서 사용한 연/월을 우선 사용하고, 없으면 현재 연/월 사용
    selected_year = int(st.session_state.get("expense_year", current_year))
    selected_month = int(st.session_state.get("expense_month", current_month))
    
    # 비용구조에서 고정비/변동비율과 목표매출 불러오기
    expense_df = load_expense_structure(selected_year, selected_month)
    
    fixed_costs = 0
    variable_cost_rate = 0.0  # % 단위

    # 5대 비용(임차료, 인건비, 재료비, 공과금, 부가세&카드수수료)을 위한 세부 항목
    fixed_by_category = {
        '임차료': 0,
        '인건비': 0,
        '공과금': 0,
    }
    variable_rate_by_category = {
        '재료비': 0.0,
        '부가세&카드수수료': 0.0,
    }
    
    if not expense_df.empty:
        fixed_categories = ['임차료', '인건비', '공과금']
        fixed_costs = expense_df[expense_df['category'].isin(fixed_categories)]['amount'].sum()
        for cat in fixed_categories:
            fixed_by_category[cat] = expense_df[expense_df['category'] == cat]['amount'].sum()
        
        variable_categories = ['재료비', '부가세&카드수수료']
        variable_df = expense_df[expense_df['category'].isin(variable_categories)]
        if not variable_df.empty:
            variable_cost_rate = variable_df['amount'].sum()
            for cat in variable_categories:
                variable_rate_by_category[cat] = variable_df[variable_df['category'] == cat]['amount'].sum()
    
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
    
    # 기본 검증
    variable_rate_decimal = variable_cost_rate / 100 if variable_cost_rate > 0 else 0
    
    if fixed_costs <= 0 or variable_rate_decimal <= 0 or variable_rate_decimal >= 1:
        st.info("비용구조 페이지에서 고정비와 변동비율을 먼저 올바르게 입력해주세요.")
    elif target_sales <= 0:
        st.info("비용구조 페이지에서 목표 매출을 먼저 설정해주세요.")
    else:
        # 목표매출을 기준으로 다양한 시나리오 생성
        scenarios = [
            ("목표매출 - 1,000만원", max(target_sales - 10_000_000, 0)),
            ("목표매출 - 500만원", max(target_sales - 5_000_000, 0)),
            ("목표매출 (기준)", target_sales),
            ("목표매출 + 500만원", target_sales + 5_000_000),
            ("목표매출 + 1,000만원", target_sales + 10_000_000),
            ("목표매출 + 1,500만원", target_sales + 15_000_000),
        ]
        
        st.markdown("""
        <div class="info-box">
            <strong>📊 매출 수준별 비용·영업이익 시뮬레이션</strong><br>
            <span style="font-size: 0.9rem; opacity: 0.9;">
                비용구조의 고정비와 변동비율, 목표 매출을 기준으로 다양한 매출 수준에서의 비용과 영업이익을 비교합니다.
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        cols = [col1, col2, col3]
        
        for idx, (label, sales) in enumerate(scenarios):
            if sales <= 0:
                continue
            
            # 5대 비용 세부 계산
            rent_cost = fixed_by_category.get('임차료', 0)
            labor_cost = fixed_by_category.get('인건비', 0)
            utility_cost = fixed_by_category.get('공과금', 0)
            material_rate = variable_rate_by_category.get('재료비', 0.0) / 100
            fee_rate = variable_rate_by_category.get('부가세&카드수수료', 0.0) / 100
            material_cost = sales * material_rate
            fee_cost = sales * fee_rate

            total_cost = rent_cost + labor_cost + utility_cost + material_cost + fee_cost
            profit = sales - total_cost
            
            tile_col = cols[idx % 3]
            with tile_col:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 1.2rem; border-radius: 10px; margin-top: 0.8rem; color: #e5e7eb; box-shadow: 0 2px 6px rgba(0,0,0,0.35);">
                    <div style="font-size: 0.9rem; margin-bottom: 0.4rem; opacity: 0.9;">{label}</div>
                    <!-- 매출 영역: 선명한 흰색 -->
                    <div style="font-size: 1.3rem; font-weight: 700; margin-bottom: 0.3rem; color: #ffffff !important;">
                        매출: {int(sales):,}원
                    </div>
                    <!-- 비용 영역 제목: 더 진한 빨간색 -->
                    <div style="font-size: 0.9rem; margin-top: 0.5rem; border-top: 1px solid rgba(148,163,184,0.5); padding-top: 0.5rem; color: #ff4d4f !important;">
                        비용 합계 및 세부내역
                    </div>
                    <!-- 총 비용: 더 진한 빨간색 -->
                    <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.2rem; color: #ff4d4f !important;">
                        총 비용: {int(total_cost):,}원
                    </div>
                    <div style="font-size: 0.85rem; margin-top: 0.3rem; line-height: 1.4; color: #ff4d4f !important;">
                        임차료(고정비): {int(rent_cost):,}원<br>
                        인건비(고정비): {int(labor_cost):,}원<br>
                        공과금(고정비): {int(utility_cost):,}원<br>
                        재료비(변동비): {int(material_cost):,}원<br>
                        부가세·카드수수료(변동비): {int(fee_cost):,}원
                    </div>
                    <!-- 추정 영업이익 제목: 선명한 노란색 -->
                    <div style="font-size: 0.9rem; margin-top: 0.5rem; border-top: 1px solid rgba(148,163,184,0.5); padding-top: 0.5rem; color: #ffd700 !important;">
                        추정 영업이익
                    </div>
                    <!-- 추정 영업이익 값: 선명한 노란색 -->
                    <div style="font-size: 1.1rem; font-weight: 600; color: #ffd700 !important;">
                        {int(profit):,}원
                    </div>
                </div>
                """, unsafe_allow_html=True)

# 직원 연락망 페이지
elif page == "직원 연락망":
    render_page_header("직원 연락망", "👤")
    
    # 직원 데이터 (임시 - 추후 DB 연결)
    if 'employees' not in st.session_state:
        st.session_state.employees = []
    
    # 직원 추가
    with st.expander("➕ 직원 추가", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            emp_name = st.text_input("이름", key="emp_name")
        with col2:
            emp_role = st.text_input("역할", key="emp_role", placeholder="예: 주방장, 서버 등")
        with col3:
            emp_phone = st.text_input("연락처", key="emp_phone", placeholder="010-0000-0000")
        
        col4, col5 = st.columns(2)
        with col4:
            emp_worktime = st.text_input("근무시간", key="emp_worktime", placeholder="예: 평일 09:00-18:00")
        with col5:
            st.write("")
            st.write("")
            if st.button("추가", key="emp_add", type="primary"):
                if emp_name and emp_phone:
                    new_emp = {
                        'id': len(st.session_state.employees) + 1,
                        'name': emp_name,
                        'role': emp_role,
                        'phone': emp_phone,
                        'worktime': emp_worktime,
                    }
                    st.session_state.employees.append(new_emp)
                    st.success(f"{emp_name} 직원이 추가되었습니다!")
                    st.rerun()
                else:
                    st.error("이름과 연락처는 필수입니다.")
    
    # 직원 목록
    if st.session_state.employees:
        st.markdown("**👥 직원 목록**")
        for idx, emp in enumerate(st.session_state.employees):
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            with col1:
                st.write(f"**{emp['name']}**")
                if emp['role']:
                    st.caption(f"역할: {emp['role']}")
            with col2:
                st.write(f"📞 {emp['phone']}")
            with col3:
                if emp['worktime']:
                    st.caption(f"⏰ {emp['worktime']}")
            with col4:
                if st.button("🗑️", key=f"del_emp_{idx}", help="삭제"):
                    st.session_state.employees.pop(idx)
                    st.rerun()
            st.markdown("---")
    else:
        st.info("등록된 직원이 없습니다. 직원을 추가해주세요.")

# 협력사 연락망 페이지
elif page == "협력사 연락망":
    render_page_header("협력사 연락망", "🤝")
    
    # 협력사 데이터 (임시 - 추후 DB 연결)
    if 'partners' not in st.session_state:
        st.session_state.partners = []
    
    # 협력사 추가
    with st.expander("➕ 협력사 추가", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            partner_name = st.text_input("업체명", key="partner_name")
            partner_contact = st.text_input("담당자", key="partner_contact")
        with col2:
            partner_phone = st.text_input("연락처", key="partner_phone", placeholder="010-0000-0000")
            partner_type = st.selectbox("유형", ["재료 공급", "배달", "기타"], key="partner_type")
        
        partner_memo = st.text_area("메모", key="partner_memo", placeholder="거래 내역, 특이사항 등")
        
        if st.button("추가", key="partner_add", type="primary"):
            if partner_name and partner_phone:
                new_partner = {
                    'id': len(st.session_state.partners) + 1,
                    'name': partner_name,
                    'contact': partner_contact,
                    'phone': partner_phone,
                    'type': partner_type,
                    'memo': partner_memo,
                }
                st.session_state.partners.append(new_partner)
                st.success(f"{partner_name} 협력사가 추가되었습니다!")
                st.rerun()
            else:
                st.error("업체명과 연락처는 필수입니다.")
    
    # 협력사 목록
    if st.session_state.partners:
        st.markdown("**🤝 협력사 목록**")
        for idx, partner in enumerate(st.session_state.partners):
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            with col1:
                st.write(f"**{partner['name']}**")
                if partner['contact']:
                    st.caption(f"담당자: {partner['contact']}")
            with col2:
                st.write(f"📞 {partner['phone']}")
                st.caption(f"유형: {partner['type']}")
            with col3:
                if partner['memo']:
                    st.caption(f"📝 {partner['memo']}")
            with col4:
                if st.button("🗑️", key=f"del_partner_{idx}", help="삭제"):
                    st.session_state.partners.pop(idx)
                    st.rerun()
            st.markdown("---")
    else:
        st.info("등록된 협력사가 없습니다. 협력사를 추가해주세요.")

# 게시판 페이지
elif page == "게시판":
    render_page_header("게시판", "📌")
    
    # 게시판 데이터 (임시 - 추후 DB 연결)
    if 'board_posts' not in st.session_state:
        st.session_state.board_posts = []
    
    # 게시글 작성
    with st.expander("✏️ 새 게시글 작성", expanded=False):
        post_title = st.text_input("제목", key="board_title")
        post_content = st.text_area("내용", key="board_content", height=200)
        if st.button("작성", key="board_submit", type="primary"):
            if post_title and post_content:
                from datetime import datetime
                new_post = {
                    'id': len(st.session_state.board_posts) + 1,
                    'title': post_title,
                    'content': post_content,
                    'author': get_current_store_name(),
                    'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                }
                st.session_state.board_posts.insert(0, new_post)
                st.success("게시글이 작성되었습니다!")
                st.rerun()
            else:
                st.error("제목과 내용을 모두 입력해주세요.")
    
    # 게시글 목록
    if st.session_state.board_posts:
        st.markdown("**📌 게시글 목록**")
        for post in st.session_state.board_posts:
            with st.container():
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.05); padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-left: 3px solid #667eea;">
                    <div style="font-weight: 600; font-size: 1.2rem; margin-bottom: 0.5rem; color: #ffffff;">{post['title']}</div>
                    <div style="color: rgba(255,255,255,0.8); font-size: 0.95rem; margin-bottom: 0.8rem; line-height: 1.6; white-space: pre-wrap;">{post['content']}</div>
                    <div style="color: rgba(255,255,255,0.5); font-size: 0.85rem;">👤 {post['author']} • 📅 {post['date']}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("게시글이 없습니다. 첫 게시글을 작성해보세요!")
