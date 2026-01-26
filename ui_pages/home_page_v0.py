"""
홈 화면 (HOME v2)
CAUSE OS 브랜드 첫 화면 + 오늘 행동 시작점
"""
from src.bootstrap import bootstrap
import streamlit as st
import logging
from src.auth import get_current_store_id, get_current_store_name, check_login, show_login_page

logger = logging.getLogger(__name__)

# 공통 설정 적용
bootstrap(page_title="Home")

# 로그인 체크
if not check_login():
    show_login_page()
    st.stop()


def render_brand_hero():
    """
    CAUSE OS 브랜드 히어로 영역
    홈 화면 최상단에 표시되는 브랜드 정체성 영역
    """
    pass


def render_home():
    """
    HOME v2 - CAUSE OS 브랜드 첫 화면 + 오늘 행동 시작점
    """
    # 리뉴얼 CSS
    css = """
    <style>
    /* 브랜드 히어로 - 홀로그램 효과 */
    .ps-brand-hero {
        background: 
            linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.9) 50%, rgba(15, 23, 42, 0.95) 100%),
            linear-gradient(45deg, rgba(59, 130, 246, 0.05) 0%, transparent 50%, rgba(96, 165, 250, 0.05) 100%) !important;
        border-radius: 24px !important;
        padding: 5rem 3rem 2rem 3rem !important;
        margin: 0 0 0 0 !important;
        text-align: center !important;
        position: relative !important;
        overflow: hidden !important;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5), 0 0 80px rgba(59, 130, 246, 0.15) !important;
        border: 1px solid rgba(59, 130, 246, 0.2) !important;
    }
    
    /* 홀로그램 shine 효과 - 강화 */
    .ps-brand-hero::before {
        content: "";
        position: absolute;
        top: 0;
        left: -150%;
        width: 50%;
        height: 100%;
        background: linear-gradient(90deg, 
            transparent 0%,
            rgba(255, 255, 255, 0.2) 20%,
            rgba(255, 255, 255, 0.4) 50%,
            rgba(255, 255, 255, 0.2) 80%,
            transparent 100%);
        animation: shine 4s ease-in-out infinite;
        z-index: 1;
        transform: skewX(-20deg);
        filter: blur(1px);
    }
    
    @keyframes shine {
        0% { left: -150%; opacity: 0; }
        10% { opacity: 1; }
        50% { left: 150%; opacity: 1; }
        51% { opacity: 0; }
        100% { left: 150%; opacity: 0; }
    }
    
    /* Streamlit 마크다운 컨테이너 오버라이드 */
    [data-testid="stMarkdownContainer"] .ps-brand-hero,
    .stMarkdown .ps-brand-hero {
        margin: 0 0 0 0 !important;
        padding-bottom: 2rem !important;
    }
    
    .ps-brand-hero::after {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.6), rgba(96, 165, 250, 0.8), rgba(59, 130, 246, 0.6), transparent);
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
        z-index: 2;
    }
    
    /* 홀로그램 추가 레이어 효과 */
    .ps-brand-hero-content {
        position: relative;
        z-index: 3;
    }
    
    .ps-brand-hero-content::before {
        content: "";
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, transparent 70%);
        animation: hologram-rotate 8s linear infinite;
        z-index: -1;
        pointer-events: none;
    }
    
    @keyframes hologram-rotate {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .ps-brand-name {
        font-size: 5rem;
        font-weight: 900;
        background: linear-gradient(135deg, #60A5FA 0%, #3B82F6 30%, #2563EB 50%, #3B82F6 70%, #60A5FA 100%);
        background-size: 200% 200%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.05em;
        line-height: 1.1;
        margin-bottom: 1.5rem;
        color: #60A5FA;
        position: relative;
        z-index: 3;
        animation: gradient-shift 3s ease infinite;
    }
    
    @keyframes gradient-shift {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    .ps-brand-tagline {
        font-size: 1.8rem;
        font-weight: 700;
        color: #F8FAFC;
        line-height: 1.6;
        margin-bottom: 1rem;
        position: relative;
        z-index: 3;
    }
    
    .ps-brand-subtitle {
        font-size: 1.2rem;
        font-weight: 500;
        color: #94A3B8;
        margin-bottom: 0;
        padding-bottom: 0;
        position: relative;
        z-index: 3;
    }
    
    /* STEP 가이드 (간결형) */
    .ps-step-guide-compact {
        margin-top: 0 !important;
    }
    
    /* Streamlit 마크다운 컨테이너 오버라이드 */
    [data-testid="stMarkdownContainer"] .ps-step-guide-compact,
    .stMarkdown .ps-step-guide-compact {
        margin-top: 0 !important;
    }
    
    .ps-step-guide-title {
        font-size: 1.75rem;
        font-weight: 800;
        color: #F8FAFC;
        margin-bottom: 2rem;
        text-align: center;
        position: relative;
        padding-bottom: 1rem;
    }
    
    .ps-step-guide-title::after {
        content: "";
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 60px;
        height: 3px;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(59, 130, 246, 0.8), 
            transparent);
        border-radius: 2px;
    }
    
    .ps-step-buttons-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.5rem;
    }
    
    .ps-step-button {
        position: relative;
        overflow: hidden;
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.85) 0%, rgba(15, 23, 42, 0.75) 100%);
        border-radius: 16px;
        padding: 2rem 1.5rem;
        text-align: center;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        margin-bottom: 1.5rem;
    }
    
    /* 상단 네온 바 */
    .ps-step-button::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        border-radius: 16px 16px 0 0;
        opacity: 0.8;
    }
    
    /* 리플 효과 */
    .ps-step-button::after {
        content: "";
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.1);
        transform: translate(-50%, -50%);
        transition: width 0.6s ease, height 0.6s ease;
    }
    
    .ps-step-button:hover::after {
        width: 300px;
        height: 300px;
    }
    
    .ps-step-button:hover {
        transform: translateY(-6px) scale(1.02);
    }
    
    /* STEP 1: 입력 (파란색) */
    .ps-step-button.step-1 {
        background: linear-gradient(135deg, 
            rgba(59, 130, 246, 0.15) 0%, 
            rgba(30, 41, 59, 0.85) 50%, 
            rgba(15, 23, 42, 0.75) 100%);
        border: 2px solid rgba(59, 130, 246, 0.5);
    }
    
    .ps-step-button.step-1::before {
        background: linear-gradient(90deg, #3B82F6 0%, #60A5FA 50%, #3B82F6 100%);
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
    }
    
    .ps-step-button.step-1:hover {
        box-shadow: 0 16px 48px rgba(0, 0, 0, 0.4), 
                    0 0 40px rgba(59, 130, 246, 0.3);
        border-color: rgba(59, 130, 246, 0.7);
    }
    
    /* STEP 2: 분석 (녹색) */
    .ps-step-button.step-2 {
        background: linear-gradient(135deg, 
            rgba(16, 185, 129, 0.15) 0%, 
            rgba(30, 41, 59, 0.85) 50%, 
            rgba(15, 23, 42, 0.75) 100%);
        border: 2px solid rgba(16, 185, 129, 0.5);
    }
    
    .ps-step-button.step-2::before {
        background: linear-gradient(90deg, #10B981 0%, #34D399 50%, #10B981 100%);
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
    }
    
    .ps-step-button.step-2:hover {
        box-shadow: 0 16px 48px rgba(0, 0, 0, 0.4), 
                    0 0 40px rgba(16, 185, 129, 0.3);
        border-color: rgba(16, 185, 129, 0.7);
    }
    
    /* STEP 3: 설계 (보라색) */
    .ps-step-button.step-3 {
        background: linear-gradient(135deg, 
            rgba(168, 85, 247, 0.15) 0%, 
            rgba(30, 41, 59, 0.85) 50%, 
            rgba(15, 23, 42, 0.75) 100%);
        border: 2px solid rgba(168, 85, 247, 0.5);
    }
    
    .ps-step-button.step-3::before {
        background: linear-gradient(90deg, #A855F7 0%, #C084FC 50%, #A855F7 100%);
        box-shadow: 0 0 10px rgba(168, 85, 247, 0.5);
    }
    
    .ps-step-button.step-3:hover {
        box-shadow: 0 16px 48px rgba(0, 0, 0, 0.4), 
                    0 0 40px rgba(168, 85, 247, 0.3);
        border-color: rgba(168, 85, 247, 0.7);
    }
    
    .ps-step-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.3));
        transition: transform 0.3s ease;
        position: relative;
        z-index: 1;
    }
    
    .ps-step-button:hover .ps-step-icon {
        transform: scale(1.1) rotate(5deg);
    }
    
    .ps-step-name {
        font-size: 1.2rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin-bottom: 0.75rem;
        background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        position: relative;
        z-index: 1;
    }
    
    .ps-step-desc {
        font-size: 0.9rem;
        color: #CBD5E1;
        line-height: 1.6;
        font-weight: 400;
        position: relative;
        z-index: 1;
    }
    
    /* Streamlit 마크다운 블록 사이 간격 제거 */
    [data-testid="stMarkdownContainer"]:has(.ps-brand-hero) + [data-testid="stMarkdownContainer"]:has(.ps-step-guide-compact),
    [data-testid="stMarkdownContainer"]:has(.ps-brand-hero) ~ [data-testid="stMarkdownContainer"]:has(.ps-step-guide-compact) {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* 브랜드 히어로 다음 마크다운 컨테이너 간격 제거 */
    [data-testid="stMarkdownContainer"]:has(.ps-brand-hero) {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }
    
    /* 미니멀 라인 아트 버튼 스타일 */
    .ps-minimal-btn {
        min-width: 150px;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 600;
        border: 2px solid;
        background: transparent;
        cursor: pointer;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
        text-align: center;
        font-family: inherit;
        width: 100%;
    }
    
    .ps-minimal-btn-1 {
        border-color: #3B82F6;
        color: #3B82F6;
    }
    
    .ps-minimal-btn-1::before,
    .ps-minimal-btn-1::after {
        content: "";
        position: absolute;
        width: 0;
        height: 0;
        border: 2px solid #3B82F6;
        transition: all 0.3s ease;
    }
    
    .ps-minimal-btn-1::before {
        top: 0;
        left: 0;
        border-right: none;
        border-bottom: none;
    }
    
    .ps-minimal-btn-1::after {
        bottom: 0;
        right: 0;
        border-left: none;
        border-top: none;
    }
    
    .ps-minimal-btn-1:hover {
        background: rgba(59, 130, 246, 0.1);
        color: #60A5FA;
    }
    
    .ps-minimal-btn-1:hover::before,
    .ps-minimal-btn-1:hover::after {
        width: 100%;
        height: 100%;
    }
    
    .ps-minimal-btn-2 {
        border-color: #10B981;
        color: #10B981;
    }
    
    .ps-minimal-btn-2::before,
    .ps-minimal-btn-2::after {
        content: "";
        position: absolute;
        width: 0;
        height: 0;
        border: 2px solid #10B981;
        transition: all 0.3s ease;
    }
    
    .ps-minimal-btn-2::before {
        top: 0;
        left: 0;
        border-right: none;
        border-bottom: none;
    }
    
    .ps-minimal-btn-2::after {
        bottom: 0;
        right: 0;
        border-left: none;
        border-top: none;
    }
    
    .ps-minimal-btn-2:hover {
        background: rgba(16, 185, 129, 0.1);
        color: #34D399;
    }
    
    .ps-minimal-btn-2:hover::before,
    .ps-minimal-btn-2:hover::after {
        width: 100%;
        height: 100%;
    }
    
    .ps-minimal-btn-3 {
        border-color: #A855F7;
        color: #A855F7;
    }
    
    .ps-minimal-btn-3::before,
    .ps-minimal-btn-3::after {
        content: "";
        position: absolute;
        width: 0;
        height: 0;
        border: 2px solid #A855F7;
        transition: all 0.3s ease;
    }
    
    .ps-minimal-btn-3::before {
        top: 0;
        left: 0;
        border-right: none;
        border-bottom: none;
    }
    
    .ps-minimal-btn-3::after {
        bottom: 0;
        right: 0;
        border-left: none;
        border-top: none;
    }
    
    .ps-minimal-btn-3:hover {
        background: rgba(168, 85, 247, 0.1);
        color: #C084FC;
    }
    
    .ps-minimal-btn-3:hover::before,
    .ps-minimal-btn-3:hover::after {
        width: 100%;
        height: 100%;
    }
    
    .ps-minimal-btn span {
        position: relative;
        z-index: 1;
    }
    
    /* 반응형 */
    @media (max-width: 768px) {
        .ps-step-buttons-grid {
            grid-template-columns: 1fr;
            gap: 1rem;
        }
        
        .ps-step-button {
            padding: 1.5rem 1rem;
        }
        
        .ps-brand-name {
            font-size: 3.5rem;
        }
        
        .ps-brand-tagline {
            font-size: 1.4rem;
        }
    }
    
    @media (max-width: 480px) {
        .ps-brand-hero {
            padding: 3rem 1.5rem 1.5rem 1.5rem !important;
        }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    
    # HTML 버튼 클릭 시 직접 페이지 이동 처리 (Streamlit 버튼 완전 제거)
    js = """
    <script>
    (function() {
        // 페이지 이동 함수 - Streamlit 세션 상태 직접 업데이트
        function navigateToPage(pageName) {
            // Streamlit의 내부 메시지 시스템 사용
            if (window.parent && window.parent !== window) {
                // Streamlit iframe 내부에서 실행되는 경우
                try {
                    // 세션 상태 업데이트를 위한 메시지 전송
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: {current_page: pageName}
                    }, '*');
                    
                    // rerun 트리거
                    setTimeout(() => {
                        window.parent.postMessage({
                            type: 'streamlit:rerun'
                        }, '*');
                    }, 100);
                } catch (e) {
                    console.error('Navigation error:', e);
                    // Fallback: URL 파라미터 사용
                    const url = new URL(window.location.href);
                    url.searchParams.set('navigate_to', pageName);
                    window.location.href = url.toString();
                }
            } else {
                // 직접 실행되는 경우 (일반적으로 발생하지 않음)
                const url = new URL(window.location.href);
                url.searchParams.set('navigate_to', pageName);
                window.location.href = url.toString();
            }
        }
        
        // HTML 버튼 클릭 이벤트 설정
        function setupButtonTriggers() {
            // 입력하기 버튼
            const btn1 = document.querySelector('.ps-minimal-btn-1[data-action="step1"]');
            if (btn1 && !btn1.dataset.listenerAdded) {
                btn1.dataset.listenerAdded = 'true';
                btn1.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    const pageName = btn1.getAttribute('data-page');
                    if (pageName) {
                        navigateToPage(pageName);
                    }
                });
            }
            
            // 분석하기 버튼
            const btn2 = document.querySelector('.ps-minimal-btn-2[data-action="step2"]');
            if (btn2 && !btn2.dataset.listenerAdded) {
                btn2.dataset.listenerAdded = 'true';
                btn2.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    const pageName = btn2.getAttribute('data-page');
                    if (pageName) {
                        navigateToPage(pageName);
                    }
                });
            }
            
            // 설계하기 버튼
            const btn3 = document.querySelector('.ps-minimal-btn-3[data-action="step3"]');
            if (btn3 && !btn3.dataset.listenerAdded) {
                btn3.dataset.listenerAdded = 'true';
                btn3.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    const pageName = btn3.getAttribute('data-page');
                    if (pageName) {
                        navigateToPage(pageName);
                    }
                });
            }
        }
        
        // 즉시 실행
        setupButtonTriggers();
        
        // DOM 로드 후 실행
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                setupButtonTriggers();
            });
        } else {
            setupButtonTriggers();
        }
        
        // Streamlit rerun 대응 - 여러 번 시도
        [50, 100, 200, 300, 500, 1000, 2000].forEach(delay => {
            setTimeout(function() {
                setupButtonTriggers();
            }, delay);
        });
        
        // MutationObserver로 DOM 변경 감지
        const observer = new MutationObserver(function() {
            setupButtonTriggers();
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true
        });
    })();
    </script>
    """
    st.markdown(js, unsafe_allow_html=True)
    
    # URL 파라미터로 페이지 이동 처리 (fallback)
    query_params = st.query_params
    if 'navigate_to' in query_params:
        st.session_state.current_page = query_params['navigate_to']
        # 파라미터 제거
        st.query_params.clear()
        st.rerun()
    
    # ============================================
    # SECTION 1: 브랜드 히어로
    # ============================================
    st.markdown("""
    <div class="ps-brand-hero">
        <div class="ps-brand-hero-content">
            <div class="ps-brand-name">CAUSE OS</div>
            <div class="ps-brand-tagline">
                매출이 아니라 원인을 봅니다.<br>
                그래서 결과가 달라집니다.
            </div>
            <div class="ps-brand-subtitle">경영의사결정 OS</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ============================================
    # SECTION 2: STEP 가이드 (간결형)
    # ============================================
    st.markdown("""
    <div class="ps-step-guide-compact">
        <div class="ps-step-guide-title">3단계 운영 흐름</div>
        <div class="ps-step-buttons-grid">
    """, unsafe_allow_html=True)
    
    # STEP 버튼 그룹 (3개 컬럼)
    step_col1, step_col2, step_col3 = st.columns(3)
    
    with step_col1:
        st.markdown("""
        <div class="ps-step-button step-1">
            <div class="ps-step-icon">📝</div>
            <div class="ps-step-name">STEP 1: 입력</div>
            <div class="ps-step-desc">데이터 자산 만들기</div>
        </div>
        """, unsafe_allow_html=True)
        # HTML 버튼만 사용 (Streamlit 버튼 완전 제거)
        st.markdown("""
        <button class="ps-minimal-btn ps-minimal-btn-1" data-action="step1" data-page="입력 허브">
            <span>▶ 입력하기</span>
        </button>
        """, unsafe_allow_html=True)
    
    with step_col2:
        st.markdown("""
        <div class="ps-step-button step-2">
            <div class="ps-step-icon">📊</div>
            <div class="ps-step-name">STEP 2: 분석</div>
            <div class="ps-step-desc">숫자가 말하는 문제</div>
        </div>
        """, unsafe_allow_html=True)
        # HTML 버튼만 사용 (Streamlit 버튼 완전 제거)
        st.markdown("""
        <button class="ps-minimal-btn ps-minimal-btn-2" data-action="step2" data-page="분석 허브">
            <span>▶ 분석하기</span>
        </button>
        """, unsafe_allow_html=True)
    
    with step_col3:
        st.markdown("""
        <div class="ps-step-button step-3">
            <div class="ps-step-icon">🎯</div>
            <div class="ps-step-name">STEP 3: 설계</div>
            <div class="ps-step-desc">행동으로 바꾸기</div>
        </div>
        """, unsafe_allow_html=True)
        # HTML 버튼만 사용 (Streamlit 버튼 완전 제거)
        st.markdown("""
        <button class="ps-minimal-btn ps-minimal-btn-3" data-action="step3" data-page="가게 전략 센터">
            <span>▶ 설계하기</span>
        </button>
        """, unsafe_allow_html=True)
    
    st.markdown("""
        </div>
    </div>
    """, unsafe_allow_html=True)
    
