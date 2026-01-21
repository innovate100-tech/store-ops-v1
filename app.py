"""
매장 운영 시스템 v1 - 메인 앱 (Supabase 기반)
"""
import streamlit as st
from datetime import datetime
import pandas as pd
import numpy as np

# 공통 설정 적용
from src.bootstrap import bootstrap
bootstrap(page_title="App")

# 로그인 체크
from src.auth import check_login, show_login_page, get_current_store_name, logout

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
from src.ui_helpers import (
    render_page_header, 
    render_section_header, 
    render_section_divider,
    safe_get_first_row,
    safe_get_value,
    safe_get_row_by_condition,
    handle_data_error,
    format_error_message
)

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
    
    /* 저작권 표시 (오른쪽 하단) */
    .main-header .copyright {
        position: absolute;
        bottom: 0.75rem;
        right: 1.5rem;
        font-size: 0.7rem;
        color: rgba(255, 255, 255, 0.4);
        opacity: 0.6;
        z-index: 2;
        font-weight: 300;
        letter-spacing: 0.5px;
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
    from pages.manager_close import render_manager_close
    render_manager_close()

# 매출 등록 페이지
elif page == "매출 등록":
    from pages.sales_entry import render_sales_entry
    render_sales_entry()

# 매출 관리 페이지 (분석 전용)
elif page == "매출 관리":
    from pages.sales_management import render_sales_management
    render_sales_management()

# 메뉴 등록 페이지
elif page == "메뉴 등록":
    from pages.menu_management import render_menu_management
    render_menu_management()

# 재료 등록 페이지
elif page == "재료 등록":
    from pages.ingredient_management import render_ingredient_management
    render_ingredient_management()

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
                                # Phase 1: 안전한 DataFrame 접근
                                unit = safe_get_value(ing_row, '단위', '')
                                order_unit = safe_get_value(ing_row, '발주단위', unit)
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
                                # Phase 1: 안전한 DataFrame 접근
                                order_unit = safe_get_value(ing_row, '발주단위', unit)
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
                        # 캐시만 클리어하고 rerun 없이 성공 메시지만 표시
                        try:
                            st.cache_data.clear()
                        except Exception as e:
                            import logging
                            logging.getLogger(__name__).warning(f"캐시 클리어 실패 (레시피 저장): {e}")
                        st.success(success_msg)
                        st.balloons()
    
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
                # Phase 1: 안전한 DataFrame 접근
                menu_price = int(safe_get_value(menu_info, '판매가', 0)) if not menu_info.empty else 0
                
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
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"조리방법 조회 실패: {e}")
                
                # 원가 정보
                # Phase 1: 안전한 DataFrame 접근
                cost = int(safe_get_value(menu_cost_info, '원가', 0)) if not menu_cost_info.empty else 0
                cost_rate = float(safe_get_value(menu_cost_info, '원가율', 0)) if not menu_cost_info.empty else 0
                
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
                                        # 캐시만 클리어하고 rerun 없이 성공 메시지만 표시
                                        try:
                                            st.cache_data.clear()
                                        except Exception as e:
                                            import logging
                                            logging.getLogger(__name__).warning(f"캐시 클리어 실패 (레시피 수정): {e}")
                                        st.success(
                                            f"✅ '{filter_menu}' - '{ing_name}' 사용량이 {new_qty:.2f}{unit} 으로 수정되었습니다."
                                        )
                                    except Exception as e:
                                        st.error(f"사용량 수정 중 오류: {e}")
                        with col5:
                            if st.button("🗑️ 삭제", key=f"delete_recipe_{filter_menu}_{ing_name}", use_container_width=True):
                                try:
                                    success, msg = delete_recipe(filter_menu, ing_name)
                                    if success:
                                        # 캐시만 클리어하고 rerun 없이 성공 메시지만 표시
                                        try:
                                            st.cache_data.clear()
                                        except Exception as e:
                                            import logging
                                            logging.getLogger(__name__).warning(f"캐시 클리어 실패 (레시피 삭제): {e}")
                                        st.success(f"✅ '{filter_menu}' - '{ing_name}' 레시피가 삭제되었습니다.")
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
    from pages.cost_overview import render_cost_overview
    render_cost_overview()

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
                # Phase 1: 안전한 DataFrame 접근
                if not existing_row.empty:
                    existing_row = safe_get_first_row(existing_row)
                    if existing_row is None:
                        existing_row = pd.Series()
            
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
                            except Exception as e:
                                import logging
                                logging.getLogger(__name__).warning(f"캐시 클리어 실패 (실제 정산 저장): {e}")
                            st.rerun()
                    except Exception as e:
                        # Phase 3: 에러 메시지 표준화
                        error_msg = handle_data_error("실제 정산 데이터 저장", e)
                        st.error(error_msg)
            
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

# 판매 관리 페이지
elif page == "판매 관리":
    from pages.sales_analysis import render_sales_analysis
    render_sales_analysis()

# 판매량 등록 페이지
elif page == "판매량 등록":
    from pages.sales_volume_entry import render_sales_volume_entry
    render_sales_volume_entry()

# 재료 사용량 집계 페이지
elif page == "재료 사용량 집계":
    from pages.ingredient_usage_summary import render_ingredient_usage_summary
    render_ingredient_usage_summary()

# 발주 관리 페이지
elif page == "발주 관리":
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
    
    # 발주 관리 UI 모듈 import
    from src.order_ui import (
        render_safety_stock_tab,
        render_inventory_status_tab,
        render_order_history_tab,
        render_supplier_management_tab,
        render_order_analysis_tab
    )
    
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

# 주간 리포트 페이지
elif page == "주간 리포트":
    from pages.weekly_report import render_weekly_report
    render_weekly_report()

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
        # Phase 1: 안전한 DataFrame 접근
        target_sales = float(safe_get_value(target_row, '목표매출', 0)) if not target_row.empty else 0.0
    
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
            target_sales_dashboard = float(safe_get_value(target_row_dashboard, '목표매출', 0))
        
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
        st.markdown("""
        <div style="margin: 1rem 0 0.5rem 0;">
            <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.2rem;">
                📊 판매 ABC 분석
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # ABC 분석 자동 실행
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
                                # Phase 1: 안전한 DataFrame 접근
                                menu_price = int(safe_get_value(menu_info, '판매가', 0)) if not menu_info.empty else 0
                                
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
                                except Exception as e:
                                    import logging
                                    logging.getLogger(__name__).warning(f"조리방법 조회 실패 (대시보드): {e}")
                                
                                # 원가 정보
                                cost = int(safe_get_value(menu_cost_info, '원가', 0)) if not menu_cost_info.empty else 0
                                cost_rate = float(safe_get_value(menu_cost_info, '원가율', 0)) if not menu_cost_info.empty else 0
                                
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
        # Phase 1: 안전한 DataFrame 접근
        target_sales = float(safe_get_value(target_row, '목표매출', 0)) if not target_row.empty else 0.0
    
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
                                        except Exception as e:
                                            import logging
                                            logging.getLogger(__name__).warning(f"캐시 클리어 실패 (비용구조 수정): {e}")
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
                                    except Exception as e:
                                        import logging
                                        logging.getLogger(__name__).warning(f"캐시 클리어 실패 (비용구조 삭제): {e}")
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
                                    except Exception as e:
                                        import logging
                                        logging.getLogger(__name__).warning(f"캐시 클리어 실패 (비용구조 고정비 저장): {e}")
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
                                    except Exception as e:
                                        import logging
                                        logging.getLogger(__name__).warning(f"캐시 클리어 실패 (비용구조 변동비 저장): {e}")
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
        # Phase 1: 안전한 DataFrame 접근
        target_sales = float(safe_get_value(target_row, '목표매출', 0)) if not target_row.empty else 0.0
    
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
    from pages.staff_contacts import render_staff_contacts
    render_staff_contacts()

# 협력사 연락망 페이지
elif page == "협력사 연락망":
    from pages.vendor_contacts import render_vendor_contacts
    render_vendor_contacts()

# 게시판 페이지
elif page == "게시판":
    from pages.board import render_board
    render_board()
