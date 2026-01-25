"""
홈 화면 프리미엄 스타일 CSS 주입 모듈
HOME 페이지에서만 적용되는 스코프 CSS
"""
import streamlit as st


def inject_home_premium_css():
    """
    홈 화면 프리미엄 CSS 주입 (1회만 실행)
    모든 섹션 프리미엄 디자인 적용
    """
    # 1회 주입 가드
    if st.session_state.get("_ps_home_premium_css_injected", False):
        return
    
    css = """
    <style>
    /* ============================================
       홈 화면 프리미엄 스타일 (전체 섹션)
       ============================================ */
    
    /* fadeInUp 애니메이션 */
    @keyframes ps-home-fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* prefers-reduced-motion 지원 */
    @media (prefers-reduced-motion: reduce) {
        .ps-hero-card,
        .ps-status-card,
        .ps-step-card,
        .ps-quote-card {
            animation: none !important;
        }
    }
    
    /* ============================================
       SECTION 1: Hero Card (프리미엄)
       ============================================ */
    
    .ps-hero-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(59, 130, 246, 0.35);
        border-radius: 16px;
        padding: 24px;
        margin: 10px 0 18px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35), 0 0 30px rgba(59, 130, 246, 0.18);
        animation: ps-home-fadeInUp 0.8s ease-out forwards;
        opacity: 0;
    }
    
    @supports (backdrop-filter: blur(10px)) {
        .ps-hero-card {
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }
    }
    
    .ps-neon {
        height: 6px;
        border-radius: 999px;
        margin-bottom: 16px;
    }
    
    .ps-neon-blue {
        background: linear-gradient(90deg, #3B82F6 0%, #60A5FA 50%, #3B82F6 100%);
        box-shadow: 0 0 18px rgba(59, 130, 246, 0.55);
    }
    
    .ps-hero-body {
        position: relative;
        z-index: 1;
    }
    
    .ps-hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #60A5FA 0%, #3B82F6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
        color: #60A5FA; /* fallback */
    }
    
    @supports not (-webkit-background-clip: text) {
        .ps-hero-title {
            -webkit-text-fill-color: #60A5FA;
            color: #60A5FA;
        }
    }
    
    .ps-hero-sub {
        color: #94a3b8;
        font-size: 1.2rem;
        margin-bottom: 10px;
        font-weight: 600;
    }
    
    .ps-hero-desc {
        color: #cbd5e1;
        font-size: 1rem;
        line-height: 1.6;
    }
    
    /* ============================================
       SECTION 2: Status Dashboard (프리미엄)
       ============================================ */
    
    .ps-status-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(245, 158, 11, 0.3);
        border-radius: 16px;
        padding: 24px;
        margin: 18px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 40px rgba(245, 158, 11, 0.1);
        animation: ps-home-fadeInUp 0.8s ease-out forwards;
        animation-delay: 0.1s;
        opacity: 0;
    }
    
    @supports (backdrop-filter: blur(8px)) {
        .ps-status-card {
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
        }
    }
    
    .ps-neon-amber {
        background: linear-gradient(90deg, #F59E0B 0%, #EF4444 50%, #F59E0B 100%);
        box-shadow: 0 0 18px rgba(245, 158, 11, 0.55);
    }
    
    .ps-status-content {
        position: relative;
        z-index: 1;
    }
    
    .ps-status-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #F8FAFC;
        line-height: 1.3;
        margin-bottom: 1.5rem;
    }
    
    .ps-metric-card {
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .ps-metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    .ps-metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
        margin-bottom: 0.5rem;
        font-weight: 500;
    }
    
    .ps-metric-value {
        font-size: 1.1rem;
        font-weight: 700;
        color: #F8FAFC;
    }
    
    .ps-reco-section {
        margin-top: 2rem;
    }
    
    .ps-reco-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #F59E0B;
        margin-bottom: 0.25rem;
    }
    
    .ps-reco-subtitle {
        font-size: 0.85rem;
        color: #94a3b8;
        font-style: italic;
        margin-bottom: 1rem;
    }
    
    .ps-reco-message-card {
        background: rgba(245, 158, 11, 0.1);
        border-left: 4px solid #F59E0B;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .ps-reco-message-card p {
        font-weight: 600;
        margin-bottom: 0.5rem;
        font-size: 1.05rem;
        white-space: pre-line;
        color: #F8FAFC;
    }
    
    .ps-reco-summary-card {
        margin-top: 1rem;
        padding: 0.75rem;
        background: rgba(59, 130, 246, 0.05);
        border-radius: 8px;
    }
    
    .ps-reco-summary-card p {
        margin: 0;
        font-size: 0.9rem;
        color: #94a3b8;
    }
    
    /* ============================================
       SECTION 3: STEP Cards (프리미엄)
       ============================================ */
    
    .ps-step-card {
        background: rgba(30, 41, 59, 0.5);
        border-radius: 16px;
        border: 1px solid rgba(59, 130, 246, 0.3);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2), 0 0 20px rgba(59, 130, 246, 0.1);
        padding: 24px;
        margin: 18px 0;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        animation: ps-home-fadeInUp 0.8s ease-out forwards;
        opacity: 0;
    }
    
    @supports (backdrop-filter: blur(8px)) {
        .ps-step-card {
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
        }
    }
    
    .ps-step-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3), 0 0 30px rgba(59, 130, 246, 0.2);
    }
    
    .ps-step-card.ps-step-1 {
        border-color: rgba(59, 130, 246, 0.3);
        animation-delay: 0.2s;
    }
    
    .ps-step-card.ps-step-2 {
        border-color: rgba(16, 185, 129, 0.3);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2), 0 0 20px rgba(16, 185, 129, 0.1);
        animation-delay: 0.3s;
    }
    
    .ps-step-card.ps-step-2:hover {
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3), 0 0 30px rgba(16, 185, 129, 0.2);
    }
    
    .ps-step-card.ps-step-3 {
        border-color: rgba(168, 85, 247, 0.3);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2), 0 0 20px rgba(168, 85, 247, 0.1);
        animation-delay: 0.4s;
    }
    
    .ps-step-card.ps-step-3:hover {
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3), 0 0 30px rgba(168, 85, 247, 0.2);
    }
    
    .ps-step-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-bottom: 1rem;
    }
    
    .ps-step-highlight-box {
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid;
    }
    
    .ps-step-highlight-box.ps-color-blue {
        background: rgba(59, 130, 246, 0.1);
        border-left-color: #3B82F6;
    }
    
    .ps-step-highlight-box.ps-color-green {
        background: rgba(16, 185, 129, 0.1);
        border-left-color: #10B981;
    }
    
    .ps-step-highlight-box.ps-color-purple {
        background: rgba(168, 85, 247, 0.1);
        border-left-color: #A855F7;
    }
    
    .ps-step-highlight-box p {
        font-weight: 600;
        margin-bottom: 0.5rem;
        font-size: 1.05rem;
        color: #F8FAFC;
        line-height: 1.5;
    }
    
    .ps-step-description {
        color: #cbd5e1;
        line-height: 1.6;
        margin: 1rem 0;
    }
    
    .ps-step-actions {
        margin-top: 1.5rem;
    }
    
    /* ============================================
       SECTION 4: Quote Card (프리미엄)
       ============================================ */
    
    .ps-quote-card {
        background: rgba(30, 41, 59, 0.4);
        border-radius: 16px;
        border-left: 4px solid rgba(59, 130, 246, 0.5);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2), 0 0 20px rgba(59, 130, 246, 0.1);
        padding: 24px;
        margin: 3rem 0 0 0;
        text-align: center;
        animation: ps-home-fadeInUp 0.8s ease-out forwards;
        animation-delay: 0.5s;
        opacity: 0;
    }
    
    @supports (backdrop-filter: blur(8px)) {
        .ps-quote-card {
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
        }
    }
    
    .ps-quote-text {
        font-size: 1.2rem;
        font-weight: 600;
        font-style: italic;
        color: #94a3b8;
        line-height: 1.8;
        margin: 0;
    }
    
    /* ============================================
       반응형 디자인
       ============================================ */
    
    @media (max-width: 768px) {
        .ps-hero-card,
        .ps-status-card,
        .ps-step-card,
        .ps-quote-card {
            padding: 1.5rem 1rem;
            border-radius: 12px;
        }
        
        .ps-hero-title {
            font-size: 1.8rem;
        }
        
        .ps-status-title {
            font-size: 1.5rem;
        }
        
        .ps-step-title {
            font-size: 1.2rem;
        }
    }
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)
    st.session_state["_ps_home_premium_css_injected"] = True
