"""
홈 페이지
메인 헤더 표시
"""
from src.bootstrap import bootstrap
import streamlit as st

# 공통 설정 적용
bootstrap(page_title="Home")

# 커스텀 CSS 적용 (헤더 스타일만 - app.py와 동일)
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Noto Sans KR', sans-serif !important;
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
</style>
""", unsafe_allow_html=True)

# 테마별 다크 모드 스타일 추가 (app.py와 동일)
if st.session_state.get("theme", "light") == "dark":
    st.markdown("""
    <style>
        .main-header {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.6) !important;
        }
    </style>
    """, unsafe_allow_html=True)

# 타이틀 (개선된 디자인) - app.py 원본과 동일
st.markdown("""
<div class="main-header">
    <h1>
        <span class="emoji">😎</span>
        <span class="text-gradient">외식경영 의사결정 시스템 (운영 OS)</span>
    </h1>
    <div class="copyright">© 2026 황승진. All rights reserved.</div>
</div>
<div class="led-board">
    <div class="led-text"></div>
</div>
""", unsafe_allow_html=True)
