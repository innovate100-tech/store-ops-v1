"""
홈 화면 프리미엄 스타일 CSS 주입 모듈
HOME 페이지에서만 적용되는 스코프 CSS
"""
import streamlit as st


def inject_home_premium_css():
    """
    홈 화면 프리미엄 CSS 주입 (1회만 실행)
    Hero 카드에만 먼저 적용
    """
    # 1회 주입 가드
    if st.session_state.get("_ps_home_premium_css_injected", False):
        return
    
    css = """
    <style>
    /* ============================================
       홈 화면 프리미엄 스타일 (Hero 카드만)
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
    
    /* ============================================
       SECTION 1: Hero Card (프리미엄) - 강제 테스트
       ============================================ */
    
    /* 강제 테스트: 빨간 테두리 (CSS 매칭 확인용) */
    .ps-hero-card {
        outline: 3px solid red !important;
    }
    
    .ps-hero-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(59, 130, 246, 0.35);
        border-radius: 16px;
        padding: 24px;
        margin: 10px 0 18px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35), 0 0 30px rgba(59, 130, 246, 0.18);
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
       반응형 디자인
       ============================================ */
    
    @media (max-width: 768px) {
        .ps-hero-card {
            padding: 1.5rem 1rem;
            border-radius: 12px;
        }
        
        .ps-hero-title {
            font-size: 1.8rem;
        }
    }
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)
    st.session_state["_ps_home_premium_css_injected"] = True
