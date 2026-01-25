"""
홈 화면 프리미엄 스타일 CSS 주입 모듈
HOME 페이지에서만 적용되는 스코프 CSS
"""
import streamlit as st


def inject_home_premium_css():
    """
    홈 화면 프리미엄 CSS 주입 (1회만 실행)
    각 섹션을 완결된 HTML 카드 블록으로 렌더링하여 CSS 적용
    """
    # 1회 주입 가드
    if st.session_state.get("_ps_home_premium_css_injected", False):
        return
    
    css = """
    <style>
    /* ============================================
       홈 화면 프리미엄 스타일 (직접 클래스 셀렉터)
       ============================================ */
    
    /* CSS 주입 확인용 프로브 */
    .ps-home-css-probe {
        background: #FF1493 !important;
        border: 5px solid #FF00FF !important;
        padding: 1rem !important;
        font-size: 1.5rem !important;
        font-weight: 900 !important;
        color: #FFFFFF !important;
        text-align: center !important;
        margin: 1rem 0 !important;
        border-radius: 8px !important;
    }
    
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
        .ps-home-hero-card,
        .ps-home-status-card,
        .ps-step-card,
        .ps-home-quote-card {
            animation: none !important;
        }
    }
    
    /* ============================================
       SECTION 1: Hero Section
       ============================================ */
    
.ps-home-hero-card {
        background: linear-gradient(135deg, 
            rgba(30, 41, 59, 0.7) 0%, 
            rgba(30, 41, 59, 0.8) 100%);
        border-radius: 16px;
        border: 1px solid rgba(59, 130, 246, 0.3);
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.3),
            0 0 40px rgba(59, 130, 246, 0.15);
        padding: 2.5rem;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
        animation: ps-home-fadeInUp 0.8s ease-out forwards;
        opacity: 0;
    }
    
    @supports (backdrop-filter: blur(10px)) {
.ps-home-hero-card {
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }
    }
    
.ps-neon-bar {
        height: 6px;
        border-radius: 3px;
        margin-bottom: 2rem;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
    }
    
.ps-neon-bar.ps-neon-blue {
        background: linear-gradient(90deg, 
            #3B82F6 0%, 
            #60A5FA 50%, 
            #3B82F6 100%);
    }
    
    .ps-hero-title {
        font-size: 2.5rem;
        font-weight: 800;
        line-height: 1.3;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #60A5FA 0%, #3B82F6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: 0 0 30px rgba(96, 165, 250, 0.5);
        color: #60A5FA; /* fallback */
    }
    
    @supports not (-webkit-background-clip: text) {
        .ps-hero-title {
            -webkit-text-fill-color: #60A5FA;
            color: #60A5FA;
        }
    }
    
.ps-hero-subtitle {
        font-size: 1.3rem;
        font-weight: 500;
        color: #94a3b8;
        line-height: 1.5;
        margin-bottom: 1.5rem;
    }
    
.ps-hero-description {
        font-size: 1rem;
        color: #cbd5e1;
        line-height: 1.6;
    }
    
    /* ============================================
       SECTION 2: Status Dashboard
       ============================================ */
    
.ps-home-status-card {
        background: linear-gradient(135deg, 
            rgba(30, 41, 59, 0.6) 0%, 
            rgba(30, 41, 59, 0.8) 100%);
        border-radius: 16px;
        border: 1px solid rgba(245, 158, 11, 0.3);
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.3),
            0 0 40px rgba(245, 158, 11, 0.1);
        padding: 2rem;
        margin-bottom: 2rem;
        animation: ps-home-fadeInUp 0.8s ease-out forwards;
        animation-delay: 0.1s;
        opacity: 0;
    }
    
    @supports (backdrop-filter: blur(8px)) {
.ps-home-status-card {
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
        }
    }
    
.ps-neon-bar.ps-neon-amber {
        background: linear-gradient(90deg, 
            #F59E0B 0%, 
            #EF4444 50%, 
            #F59E0B 100%);
        box-shadow: 0 0 20px rgba(245, 158, 11, 0.5);
    }
    
.ps-status-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #F8FAFC;
        line-height: 1.3;
        margin-bottom: 1.5rem;
    }
    
    /* 상태 지표 미니 카드 (3개 그리드) */
.ps-status-metrics {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin: 1.5rem 0;
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
    
    /* 추천 섹션 */
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
    
    /* 액션 버튼 컨테이너 */
.ps-reco-action-container {
        margin: 1.5rem 0;
    }
    
    /* 요약 카드 */
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
       SECTION 3: STEP Cards
       ============================================ */
    
.ps-step-card {
        background: linear-gradient(135deg, 
            rgba(30, 41, 59, 0.5) 0%, 
            rgba(30, 41, 59, 0.7) 100%);
        border-radius: 16px;
        border: 1px solid rgba(59, 130, 246, 0.3);
        box-shadow: 
            0 4px 16px rgba(0, 0, 0, 0.2),
            0 0 20px rgba(59, 130, 246, 0.1);
        padding: 2rem;
        margin-bottom: 1.5rem;
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
        box-shadow: 
            0 8px 24px rgba(0, 0, 0, 0.3),
            0 0 30px rgba(59, 130, 246, 0.2);
    }
    
.ps-step-card.ps-step-1 {
        border-color: rgba(59, 130, 246, 0.3);
        animation-delay: 0.2s;
    }
    
.ps-step-card.ps-step-2 {
        border-color: rgba(16, 185, 129, 0.3);
        box-shadow: 
            0 4px 16px rgba(0, 0, 0, 0.2),
            0 0 20px rgba(16, 185, 129, 0.1);
        animation-delay: 0.3s;
    }
    
.ps-step-card.ps-step-2:hover {
        box-shadow: 
            0 8px 24px rgba(0, 0, 0, 0.3),
            0 0 30px rgba(16, 185, 129, 0.2);
    }
    
.ps-step-card.ps-step-3 {
        border-color: rgba(168, 85, 247, 0.3);
        box-shadow: 
            0 4px 16px rgba(0, 0, 0, 0.2),
            0 0 20px rgba(168, 85, 247, 0.1);
        animation-delay: 0.4s;
    }
    
.ps-step-card.ps-step-3:hover {
        box-shadow: 
            0 8px 24px rgba(0, 0, 0, 0.3),
            0 0 30px rgba(168, 85, 247, 0.2);
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
       SECTION 4: Quote Section
       ============================================ */
    
.ps-home-quote-card {
        background: rgba(30, 41, 59, 0.4);
        border-radius: 16px;
        border-left: 4px solid rgba(59, 130, 246, 0.5);
        box-shadow: 
            0 4px 16px rgba(0, 0, 0, 0.2),
            0 0 20px rgba(59, 130, 246, 0.1);
        padding: 2rem;
        margin-top: 3rem;
        text-align: center;
        animation: ps-home-fadeInUp 0.8s ease-out forwards;
        animation-delay: 0.5s;
        opacity: 0;
    }
    
    @supports (backdrop-filter: blur(8px)) {
.ps-home-quote-card {
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
.ps-home-hero-card,
.ps-home-status-card,
.ps-step-card {
            padding: 1.5rem 1rem;
            border-radius: 12px;
        }
        
.ps-hero-title {
            font-size: 1.8rem;
        }
        
.ps-status-metrics {
            grid-template-columns: 1fr;
            gap: 0.75rem;
        }
        
.ps-step-title {
            font-size: 1.2rem;
        }
    }
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)
    st.session_state["_ps_home_premium_css_injected"] = True
