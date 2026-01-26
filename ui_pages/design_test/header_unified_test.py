"""
홈화면 리뉴얼 테스트 페이지
최대 간결형 테스트
"""
import streamlit as st


def render_header_unified_test():
    """홈화면 리뉴얼 구조 테스트 - 최대 간결형"""
    
    st.title("🎨 홈화면 리뉴얼 테스트")
    st.caption("최대 간결형 - 브랜드 히어로 + STEP 가이드")
    
    # 리뉴얼 CSS
    css = """
    <style>
    /* 브랜드 히어로 */
    .ps-brand-hero {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.9) 50%, rgba(15, 23, 42, 0.95) 100%) !important;
        border-radius: 24px !important;
        padding: 5rem 3rem 2rem 3rem !important;
        margin: 0 0 0 0 !important;
        text-align: center !important;
        position: relative !important;
        overflow: hidden !important;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5), 0 0 80px rgba(59, 130, 246, 0.15) !important;
        border: 1px solid rgba(59, 130, 246, 0.2) !important;
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
    }
    
    .ps-brand-tagline {
        font-size: 1.8rem;
        font-weight: 700;
        color: #F8FAFC;
        line-height: 1.6;
        margin-bottom: 1rem;
    }
    
    .ps-brand-subtitle {
        font-size: 1.2rem;
        font-weight: 500;
        color: #94A3B8;
        margin-bottom: 0;
        padding-bottom: 0;
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
    
    /* STEP별 버튼 색상 연계 */
    button[data-testid="baseButton-secondary"]:has-text("입력하기"),
    button:has-text("입력하기") {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
        border-color: rgba(59, 130, 246, 0.5) !important;
    }
    
    button[data-testid="baseButton-secondary"]:has-text("분석하기"),
    button:has-text("분석하기") {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        border-color: rgba(16, 185, 129, 0.5) !important;
    }
    
    button[data-testid="baseButton-secondary"]:has-text("설계하기"),
    button:has-text("설계하기") {
        background: linear-gradient(135deg, #A855F7 0%, #9333EA 100%) !important;
        border-color: rgba(168, 85, 247, 0.5) !important;
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
        if st.button("▶ 입력하기", type="primary", use_container_width=True, key="test_step1_btn"):
            st.info("테스트: 입력 허브로 이동")
    
    with step_col2:
        st.markdown("""
        <div class="ps-step-button step-2">
            <div class="ps-step-icon">📊</div>
            <div class="ps-step-name">STEP 2: 분석</div>
            <div class="ps-step-desc">숫자가 말하는 문제</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("▶ 분석하기", type="primary", use_container_width=True, key="test_step2_btn"):
            st.info("테스트: 분석 허브로 이동")
    
    with step_col3:
        st.markdown("""
        <div class="ps-step-button step-3">
            <div class="ps-step-icon">🎯</div>
            <div class="ps-step-name">STEP 3: 설계</div>
            <div class="ps-step-desc">행동으로 바꾸기</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("▶ 설계하기", type="primary", use_container_width=True, key="test_step3_btn"):
            st.info("테스트: 전략 센터로 이동")
    
    st.markdown("""
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ============================================
    # 히어로 박스 화려한 디자인 예시안
    # ============================================
    st.markdown("---")
    st.markdown("### 🎨 히어로 박스 화려한 디자인 예시안")
    
    # 예시안 CSS
    hero_variants_css = """
    <style>
    /* 예시안 1: 강화된 글로우 + 애니메이션 */
    .ps-hero-variant-1 {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.98) 0%, rgba(30, 41, 59, 0.95) 50%, rgba(15, 23, 42, 0.98) 100%) !important;
        border-radius: 24px !important;
        padding: 5rem 3rem 2rem 3rem !important;
        margin: 2rem 0 !important;
        text-align: center !important;
        position: relative !important;
        overflow: hidden !important;
        box-shadow: 0 30px 80px rgba(0, 0, 0, 0.6), 
                    0 0 120px rgba(59, 130, 246, 0.25),
                    inset 0 0 60px rgba(59, 130, 246, 0.1) !important;
        border: 2px solid rgba(59, 130, 246, 0.4) !important;
    }
    
    .ps-hero-variant-1::before {
        content: "";
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, transparent 70%);
        animation: rotate 20s linear infinite;
    }
    
    @keyframes rotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    .ps-hero-variant-1::after {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(59, 130, 246, 0.8), 
            rgba(96, 165, 250, 1), 
            rgba(59, 130, 246, 0.8), 
            transparent);
        box-shadow: 0 0 30px rgba(59, 130, 246, 0.8);
        animation: shimmer 3s ease-in-out infinite;
    }
    
    @keyframes shimmer {
        0%, 100% { opacity: 0.8; }
        50% { opacity: 1; }
    }
    
    /* 예시안 2: 입체감 + 다중 레이어 */
    .ps-hero-variant-2 {
        background: 
            linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.9) 50%, rgba(15, 23, 42, 0.95) 100%),
            radial-gradient(circle at 20% 50%, rgba(59, 130, 246, 0.2) 0%, transparent 50%),
            radial-gradient(circle at 80% 50%, rgba(96, 165, 250, 0.15) 0%, transparent 50%) !important;
        border-radius: 24px !important;
        padding: 5rem 3rem 2rem 3rem !important;
        margin: 2rem 0 !important;
        text-align: center !important;
        position: relative !important;
        overflow: hidden !important;
        box-shadow: 
            0 25px 70px rgba(0, 0, 0, 0.5),
            0 0 100px rgba(59, 130, 246, 0.2),
            0 0 200px rgba(59, 130, 246, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        transform: perspective(1000px) rotateX(0deg);
        transition: transform 0.3s ease;
    }
    
    .ps-hero-variant-2:hover {
        transform: perspective(1000px) rotateX(2deg) translateY(-5px);
    }
    
    .ps-hero-variant-2::after {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, 
            transparent 0%,
            rgba(59, 130, 246, 0.6) 20%,
            rgba(96, 165, 250, 1) 50%,
            rgba(59, 130, 246, 0.6) 80%,
            transparent 100%);
        box-shadow: 0 0 40px rgba(59, 130, 246, 0.6);
        animation: pulse-glow 2s ease-in-out infinite;
    }
    
    @keyframes pulse-glow {
        0%, 100% { 
            box-shadow: 0 0 40px rgba(59, 130, 246, 0.6);
            opacity: 0.8;
        }
        50% { 
            box-shadow: 0 0 60px rgba(59, 130, 246, 0.9);
            opacity: 1;
        }
    }
    
    /* 예시안 3: 네온 효과 + 강화된 그라데이션 */
    .ps-hero-variant-3 {
        background: linear-gradient(135deg, 
            rgba(15, 23, 42, 0.98) 0%, 
            rgba(30, 41, 59, 0.95) 25%,
            rgba(59, 130, 246, 0.1) 50%,
            rgba(30, 41, 59, 0.95) 75%,
            rgba(15, 23, 42, 0.98) 100%) !important;
        border-radius: 24px !important;
        padding: 5rem 3rem 2rem 3rem !important;
        margin: 2rem 0 !important;
        text-align: center !important;
        position: relative !important;
        overflow: hidden !important;
        box-shadow: 
            0 20px 60px rgba(0, 0, 0, 0.5),
            0 0 80px rgba(59, 130, 246, 0.2),
            0 0 120px rgba(59, 130, 246, 0.1),
            inset 0 0 80px rgba(59, 130, 246, 0.05) !important;
        border: 2px solid rgba(59, 130, 246, 0.5) !important;
    }
    
    .ps-hero-variant-3::before {
        content: "";
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        background: linear-gradient(45deg, 
            rgba(59, 130, 246, 0.8),
            rgba(96, 165, 250, 0.8),
            rgba(59, 130, 246, 0.8),
            rgba(96, 165, 250, 0.8));
        border-radius: 24px;
        z-index: -1;
        animation: border-rotate 3s linear infinite;
        filter: blur(8px);
    }
    
    @keyframes border-rotate {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .ps-hero-variant-3::after {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, 
            transparent,
            rgba(59, 130, 246, 1),
            rgba(96, 165, 250, 1),
            rgba(59, 130, 246, 1),
            transparent);
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.8);
    }
    
    /* 예시안 4: 홀로그램 효과 */
    .ps-hero-variant-4 {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.9) 50%, rgba(15, 23, 42, 0.95) 100%) !important;
        border-radius: 24px !important;
        padding: 5rem 3rem 2rem 3rem !important;
        margin: 2rem 0 !important;
        text-align: center !important;
        position: relative !important;
        overflow: hidden !important;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5), 0 0 80px rgba(59, 130, 246, 0.15) !important;
        border: 1px solid rgba(59, 130, 246, 0.2) !important;
    }
    
    .ps-hero-variant-4::before {
        content: "";
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, 
            transparent,
            rgba(255, 255, 255, 0.1),
            transparent);
        animation: shine 3s infinite;
    }
    
    @keyframes shine {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    
    .ps-hero-variant-4::after {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, 
            transparent, 
            rgba(59, 130, 246, 0.6), 
            rgba(96, 165, 250, 0.8), 
            rgba(59, 130, 246, 0.6), 
            transparent);
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
    }
    
    /* 공통 스타일 (예시안용) */
    .ps-hero-variant-name {
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
        z-index: 1;
        animation: gradient-shift 3s ease infinite;
    }
    
    @keyframes gradient-shift {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    .ps-hero-variant-tagline {
        font-size: 1.8rem;
        font-weight: 700;
        color: #F8FAFC;
        line-height: 1.6;
        margin-bottom: 1rem;
        position: relative;
        z-index: 1;
    }
    
    .ps-hero-variant-subtitle {
        font-size: 1.2rem;
        font-weight: 500;
        color: #94A3B8;
        margin-bottom: 0;
        padding-bottom: 0;
        position: relative;
        z-index: 1;
    }
    </style>
    """
    st.markdown(hero_variants_css, unsafe_allow_html=True)
    
    # 예시안 1: 강화된 글로우 + 애니메이션
    st.markdown("#### 예시안 1: 강화된 글로우 + 애니메이션")
    st.caption("회전하는 배경 그라데이션 + 펄스 효과 네온 바")
    st.markdown("""
    <div class="ps-hero-variant-1">
        <div class="ps-brand-hero-content">
            <div class="ps-hero-variant-name">CAUSE OS</div>
            <div class="ps-hero-variant-tagline">
                매출이 아니라 원인을 봅니다.<br>
                그래서 결과가 달라집니다.
            </div>
            <div class="ps-hero-variant-subtitle">경영의사결정 OS</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 예시안 2: 입체감 + 다중 레이어
    st.markdown("#### 예시안 2: 입체감 + 다중 레이어")
    st.caption("3D 효과 + 다중 배경 레이어 + 펄스 글로우")
    st.markdown("""
    <div class="ps-hero-variant-2">
        <div class="ps-brand-hero-content">
            <div class="ps-hero-variant-name">CAUSE OS</div>
            <div class="ps-hero-variant-tagline">
                매출이 아니라 원인을 봅니다.<br>
                그래서 결과가 달라집니다.
            </div>
            <div class="ps-hero-variant-subtitle">경영의사결정 OS</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 예시안 3: 네온 효과 + 강화된 그라데이션
    st.markdown("#### 예시안 3: 네온 효과 + 강화된 그라데이션")
    st.caption("회전하는 네온 테두리 + 강화된 내부 그라데이션")
    st.markdown("""
    <div class="ps-hero-variant-3">
        <div class="ps-brand-hero-content">
            <div class="ps-hero-variant-name">CAUSE OS</div>
            <div class="ps-hero-variant-tagline">
                매출이 아니라 원인을 봅니다.<br>
                그래서 결과가 달라집니다.
            </div>
            <div class="ps-hero-variant-subtitle">경영의사결정 OS</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 예시안 4: 홀로그램 효과
    st.markdown("#### 예시안 4: 홀로그램 효과")
    st.caption("빛이 지나가는 효과 + 그라데이션 텍스트 애니메이션")
    st.markdown("""
    <div class="ps-hero-variant-4">
        <div class="ps-brand-hero-content">
            <div class="ps-hero-variant-name">CAUSE OS</div>
            <div class="ps-hero-variant-tagline">
                매출이 아니라 원인을 봅니다.<br>
                그래서 결과가 달라집니다.
            </div>
            <div class="ps-hero-variant-subtitle">경영의사결정 OS</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
