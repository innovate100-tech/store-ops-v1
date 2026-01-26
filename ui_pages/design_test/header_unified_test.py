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
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.9) 50%, rgba(15, 23, 42, 0.95) 100%);
        border-radius: 24px;
        padding: 5rem 3rem;
        margin: 0 0 3rem 0;
        text-align: center;
        position: relative;
        overflow: hidden;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5), 0 0 80px rgba(59, 130, 246, 0.15);
        border: 1px solid rgba(59, 130, 246, 0.2);
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
        margin-bottom: 3rem;
    }
    
    /* STEP 가이드 (간결형) */
    .ps-step-guide-compact {
        margin-top: 2rem;
    }
    
    .ps-step-guide-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .ps-step-buttons-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.5rem;
    }
    
    .ps-step-button {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.85) 0%, rgba(15, 23, 42, 0.75) 100%);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 16px;
        padding: 2rem 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
        cursor: pointer;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    .ps-step-button:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(59, 130, 246, 0.4);
        border-color: rgba(59, 130, 246, 0.6);
    }
    
    .ps-step-button.step-1 {
        border-color: rgba(59, 130, 246, 0.4);
    }
    
    .ps-step-button.step-2 {
        border-color: rgba(16, 185, 129, 0.4);
    }
    
    .ps-step-button.step-3 {
        border-color: rgba(168, 85, 247, 0.4);
    }
    
    .ps-step-icon {
        font-size: 2.5rem;
        margin-bottom: 0.75rem;
    }
    
    .ps-step-name {
        font-size: 1.1rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-bottom: 0.5rem;
    }
    
    .ps-step-desc {
        font-size: 0.85rem;
        color: #94A3B8;
        line-height: 1.5;
    }
    
    /* 반응형 */
    @media (max-width: 768px) {
        .ps-step-buttons-grid {
            grid-template-columns: 1fr;
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
                우리는 매출을 보지 않습니다.<br>
                원인을 봅니다.
            </div>
            <div class="ps-brand-subtitle">사장을 위한 숫자 운영체제</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 메인 CTA 버튼
    if st.button("오늘 숫자 입력하기", type="primary", use_container_width=True, key="test_brand_hero_cta"):
        st.info("테스트: 일일 입력(통합) 페이지로 이동")
    
    st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)
    
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
