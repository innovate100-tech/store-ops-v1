"""
홈 화면 프리미엄 스타일 CSS 주입 모듈
HOME 페이지에서만 적용되는 스코프 CSS
"""
import streamlit as st


def inject_home_premium_css():
    """
    홈 화면 프리미엄 CSS 주입 (홈 페이지 진입 시마다 재주입)
    모든 섹션 프리미엄 디자인 적용 - 업그레이드 버전
    
    Note: 다른 페이지로 갔다가 돌아올 때 CSS가 풀리는 문제를 해결하기 위해
    홈 페이지에 진입할 때마다 CSS를 재주입합니다.
    """
    # 현재 페이지가 홈인지 확인
    current_page = st.session_state.get("current_page", "홈")
    
    # 홈 페이지가 아니면 주입하지 않음
    if current_page != "홈":
        return
    
    # 이전에 주입된 CSS 태그 제거를 위한 고유 ID 사용
    # (중복 주입 방지는 브라우저가 자동으로 처리)
    
    css = """
    <style id="ps-home-premium-style">
    /* ============================================
       홈 화면 프리미엄 스타일 (전체 섹션) - 업그레이드
       ============================================ */
    
    /* fadeInUp 애니메이션 */
    @keyframes ps-home-fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* glow pulse 애니메이션 */
    @keyframes ps-home-glow-pulse {
        0%, 100% {
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35), 0 0 30px rgba(59, 130, 246, 0.18);
        }
        50% {
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 0 0 40px rgba(59, 130, 246, 0.28);
        }
    }
    
    /* prefers-reduced-motion 지원 */
    @media (prefers-reduced-motion: reduce) {
        .ps-brand-hero,
        .ps-status-card,
        .ps-step-card,
        .ps-quote-card {
            animation: none !important;
        }
    }
    
    /* ============================================
       SECTION 0: CAUSE OS 브랜드 히어로 영역
       ============================================ */
    
    .ps-brand-hero {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.9) 50%, rgba(15, 23, 42, 0.95) 100%);
        border-radius: 24px;
        padding: 5rem 3rem;
        margin: 0 0 3rem 0;
        text-align: center;
        position: relative;
        overflow: hidden;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5), 0 0 80px rgba(59, 130, 246, 0.15);
        animation: ps-home-fadeInUp 1s ease-out forwards;
        opacity: 0;
        border: 1px solid rgba(59, 130, 246, 0.2);
    }
    
    .ps-brand-hero::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(circle at 50% 0%, rgba(59, 130, 246, 0.1) 0%, transparent 70%);
        pointer-events: none;
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
    
    @supports (backdrop-filter: blur(16px)) {
        .ps-brand-hero {
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
        }
    }
    
    .ps-brand-hero-content {
        position: relative;
        z-index: 1;
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
        text-shadow: 0 0 40px rgba(59, 130, 246, 0.3);
        animation: gradient-shift 6s ease infinite;
        color: #60A5FA; /* fallback */
    }
    
    @supports not (-webkit-background-clip: text) {
        .ps-brand-name {
            -webkit-text-fill-color: #60A5FA;
            color: #60A5FA;
        }
    }
    
    .ps-brand-tagline {
        font-size: 1.8rem;
        font-weight: 700;
        color: #F8FAFC;
        line-height: 1.6;
        margin-bottom: 1rem;
        letter-spacing: -0.02em;
    }
    
    .ps-brand-subtitle {
        font-size: 1.2rem;
        font-weight: 500;
        color: #94A3B8;
        margin-bottom: 3rem;
        letter-spacing: 0.01em;
    }
    
    /* 브랜드 히어로 CTA 버튼 스타일 */
    .ps-brand-hero .stButton > button {
        font-size: 1.2rem !important;
        font-weight: 800 !important;
        padding: 1.25rem 2.5rem !important;
        border-radius: 16px !important;
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
        border: none !important;
        box-shadow: 0 8px 24px rgba(59, 130, 246, 0.5), 0 0 40px rgba(59, 130, 246, 0.3) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        min-height: 64px !important;
    }
    
    .ps-brand-hero .stButton > button:hover {
        transform: translateY(-4px) scale(1.02) !important;
        box-shadow: 0 12px 32px rgba(59, 130, 246, 0.6), 0 0 50px rgba(59, 130, 246, 0.4) !important;
    }
    
    /* ============================================
       SECTION 1: Hero Card (프리미엄) - 업그레이드 (사용 안 함, 레거시)
       ============================================ */
    
    .ps-hero-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.85) 0%, rgba(15, 23, 42, 0.75) 100%);
        border: 1px solid rgba(59, 130, 246, 0.4);
        border-radius: 20px;
        padding: 32px;
        margin: 0 0 2rem 0;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4), 0 0 50px rgba(59, 130, 246, 0.2);
        animation: ps-home-fadeInUp 0.9s ease-out forwards, ps-home-glow-pulse 4s ease-in-out infinite;
        opacity: 0;
        position: relative;
        overflow: hidden;
    }
    
    .ps-hero-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.5), transparent);
        opacity: 0.6;
    }
    
    @supports (backdrop-filter: blur(12px)) {
        .ps-hero-card {
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
        }
    }
    
    .ps-neon {
        height: 6px;
        border-radius: 999px;
        margin-bottom: 20px;
        position: relative;
    }
    
    .ps-neon-blue {
        background: linear-gradient(90deg, #3B82F6 0%, #60A5FA 30%, #93C5FD 50%, #60A5FA 70%, #3B82F6 100%);
        background-size: 200% 100%;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.6), 0 0 40px rgba(59, 130, 246, 0.3);
        animation: shimmer 3s ease-in-out infinite;
    }
    
    @keyframes shimmer {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    .ps-hero-body {
        position: relative;
        z-index: 1;
    }
    
    .ps-hero-title {
        font-size: 2.5rem;
        font-weight: 900;
        background: linear-gradient(135deg, #60A5FA 0%, #3B82F6 50%, #2563EB 100%);
        background-size: 200% 200%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 16px;
        line-height: 1.2;
        letter-spacing: -0.02em;
        animation: gradient-shift 5s ease infinite;
        color: #60A5FA; /* fallback */
    }
    
    @keyframes gradient-shift {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    @supports not (-webkit-background-clip: text) {
        .ps-hero-title {
            -webkit-text-fill-color: #60A5FA;
            color: #60A5FA;
        }
    }
    
    .ps-hero-sub {
        color: #CBD5E1;
        font-size: 1.35rem;
        margin-bottom: 12px;
        font-weight: 600;
        letter-spacing: -0.01em;
    }
    
    .ps-hero-desc {
        color: #E2E8F0;
        font-size: 1.1rem;
        line-height: 1.7;
        font-weight: 400;
    }
    
    /* ============================================
       SECTION 2: Status Dashboard (프리미엄) - 업그레이드
       ============================================ */
    
    .ps-status-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.75) 0%, rgba(15, 23, 42, 0.65) 100%);
        border: 1px solid rgba(245, 158, 11, 0.4);
        border-radius: 20px;
        padding: 32px;
        margin: 0 0 2rem 0;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35), 0 0 60px rgba(245, 158, 11, 0.15);
        animation: ps-home-fadeInUp 0.9s ease-out forwards;
        animation-delay: 0.15s;
        opacity: 0;
        position: relative;
        overflow: hidden;
    }
    
    .ps-status-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(245, 158, 11, 0.6), transparent);
        opacity: 0.6;
    }
    
    @supports (backdrop-filter: blur(10px)) {
        .ps-status-card {
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }
    }
    
    .ps-neon-amber {
        background: linear-gradient(90deg, #F59E0B 0%, #EF4444 30%, #F97316 50%, #EF4444 70%, #F59E0B 100%);
        background-size: 200% 100%;
        box-shadow: 0 0 20px rgba(245, 158, 11, 0.6), 0 0 40px rgba(245, 158, 11, 0.3);
        animation: shimmer 3s ease-in-out infinite;
    }
    
    .ps-status-content {
        position: relative;
        z-index: 1;
    }
    
    .ps-status-title {
        font-size: 1.75rem;
        font-weight: 800;
        color: #F8FAFC;
        line-height: 1.3;
        margin-bottom: 2rem;
        letter-spacing: -0.02em;
    }
    
    .ps-metric-card {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(59, 130, 246, 0.08) 100%);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 14px;
        padding: 1.25rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15), 0 0 20px rgba(59, 130, 246, 0.1);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .ps-metric-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.5), transparent);
    }
    
    .ps-metric-card:hover {
        transform: translateY(-4px) scale(1.02);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2), 0 0 30px rgba(59, 130, 246, 0.2);
        border-color: rgba(59, 130, 246, 0.5);
    }
    
    .ps-metric-label {
        font-size: 0.9rem;
        color: #94a3b8;
        margin-bottom: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .ps-metric-value {
        font-size: 1.4rem;
        font-weight: 800;
        color: #F8FAFC;
        letter-spacing: -0.02em;
    }
    
    .ps-reco-section {
        margin-top: 2.5rem;
    }
    
    .ps-reco-title {
        font-size: 1.4rem;
        font-weight: 800;
        color: #F59E0B;
        margin-bottom: 0.5rem;
        letter-spacing: -0.01em;
    }
    
    .ps-reco-subtitle {
        font-size: 0.95rem;
        color: #94a3b8;
        font-style: italic;
        margin-bottom: 1.5rem;
        line-height: 1.5;
    }
    
    .ps-reco-message-card {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(245, 158, 11, 0.08) 100%);
        border-left: 5px solid #F59E0B;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15), 0 0 30px rgba(245, 158, 11, 0.1);
    }
    
    .ps-reco-message-card p {
        font-weight: 700;
        margin-bottom: 0.5rem;
        font-size: 1.15rem;
        white-space: pre-line;
        color: #F8FAFC;
        line-height: 1.6;
    }
    
    .ps-reco-summary-card {
        margin-top: 1.5rem;
        padding: 1rem;
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(59, 130, 246, 0.04) 100%);
        border-radius: 10px;
        border: 1px solid rgba(59, 130, 246, 0.2);
    }
    
    .ps-reco-summary-card p {
        margin: 0;
        font-size: 0.95rem;
        color: #94a3b8;
        font-weight: 500;
    }
    
    /* ============================================
       SECTION 3: STEP Cards (프리미엄) - 업그레이드
       ============================================ */
    
    .ps-step-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.5) 100%);
        border-radius: 20px;
        border: 1px solid rgba(59, 130, 246, 0.35);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25), 0 0 40px rgba(59, 130, 246, 0.12);
        padding: 32px;
        margin: 0 0 2rem 0;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        animation: ps-home-fadeInUp 0.9s ease-out forwards;
        opacity: 0;
        position: relative;
        overflow: hidden;
    }
    
    .ps-step-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.5), transparent);
        opacity: 0.6;
    }
    
    @supports (backdrop-filter: blur(10px)) {
        .ps-step-card {
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }
    }
    
    .ps-step-card:hover {
        transform: translateY(-6px) scale(1.01);
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35), 0 0 50px rgba(59, 130, 246, 0.25);
    }
    
    .ps-step-card.ps-step-1 {
        border-color: rgba(59, 130, 246, 0.4);
        animation-delay: 0.25s;
    }
    
    .ps-step-card.ps-step-1 .ps-neon-blue {
        background: linear-gradient(90deg, #3B82F6 0%, #60A5FA 30%, #93C5FD 50%, #60A5FA 70%, #3B82F6 100%);
        background-size: 200% 100%;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.6), 0 0 40px rgba(59, 130, 246, 0.3);
        animation: shimmer 3s ease-in-out infinite;
    }
    
    .ps-step-card.ps-step-2 {
        border-color: rgba(16, 185, 129, 0.4);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25), 0 0 40px rgba(16, 185, 129, 0.12);
        animation-delay: 0.35s;
    }
    
    .ps-step-card.ps-step-2::before {
        background: linear-gradient(90deg, transparent, rgba(16, 185, 129, 0.5), transparent);
    }
    
    .ps-step-card.ps-step-2:hover {
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35), 0 0 50px rgba(16, 185, 129, 0.25);
    }
    
    .ps-step-card.ps-step-2 .ps-neon-green {
        background: linear-gradient(90deg, #10B981 0%, #34D399 30%, #6EE7B7 50%, #34D399 70%, #10B981 100%);
        background-size: 200% 100%;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.6), 0 0 40px rgba(16, 185, 129, 0.3);
        animation: shimmer 3s ease-in-out infinite;
    }
    
    .ps-step-card.ps-step-3 {
        border-color: rgba(168, 85, 247, 0.4);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25), 0 0 40px rgba(168, 85, 247, 0.12);
        animation-delay: 0.45s;
    }
    
    .ps-step-card.ps-step-3::before {
        background: linear-gradient(90deg, transparent, rgba(168, 85, 247, 0.5), transparent);
    }
    
    .ps-step-card.ps-step-3:hover {
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35), 0 0 50px rgba(168, 85, 247, 0.25);
    }
    
    .ps-step-card.ps-step-3 .ps-neon-purple {
        background: linear-gradient(90deg, #A855F7 0%, #C084FC 30%, #E9D5FF 50%, #C084FC 70%, #A855F7 100%);
        background-size: 200% 100%;
        box-shadow: 0 0 20px rgba(168, 85, 247, 0.6), 0 0 40px rgba(168, 85, 247, 0.3);
        animation: shimmer 3s ease-in-out infinite;
    }
    
    .ps-step-title {
        font-size: 1.75rem;
        font-weight: 800;
        color: #F8FAFC;
        margin-bottom: 1.5rem;
        letter-spacing: -0.02em;
        line-height: 1.3;
    }
    
    .ps-step-highlight-box {
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border-left: 5px solid;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    .ps-step-highlight-box.ps-color-blue {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(59, 130, 246, 0.08) 100%);
        border-left-color: #3B82F6;
    }
    
    .ps-step-highlight-box.ps-color-green {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(16, 185, 129, 0.08) 100%);
        border-left-color: #10B981;
    }
    
    .ps-step-highlight-box.ps-color-purple {
        background: linear-gradient(135deg, rgba(168, 85, 247, 0.15) 0%, rgba(168, 85, 247, 0.08) 100%);
        border-left-color: #A855F7;
    }
    
    .ps-step-highlight-box p {
        font-weight: 700;
        margin-bottom: 0.5rem;
        font-size: 1.15rem;
        color: #F8FAFC;
        line-height: 1.6;
    }
    
    .ps-step-description {
        color: #CBD5E1;
        line-height: 1.7;
        margin: 1.5rem 0;
        font-size: 1.05rem;
    }
    
    .ps-step-actions {
        margin-top: 2rem;
    }
    
    /* ============================================
       SECTION 4: Quote Card (프리미엄) - 업그레이드
       ============================================ */
    
    .ps-quote-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.5) 0%, rgba(15, 23, 42, 0.4) 100%);
        border-radius: 20px;
        border-left: 5px solid rgba(59, 130, 246, 0.6);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25), 0 0 40px rgba(59, 130, 246, 0.12);
        padding: 40px;
        margin: 3rem 0 0 0;
        text-align: center;
        animation: ps-home-fadeInUp 0.9s ease-out forwards;
        animation-delay: 0.55s;
        opacity: 0;
        position: relative;
        overflow: hidden;
    }
    
    .ps-quote-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.5), transparent);
        opacity: 0.6;
    }
    
    @supports (backdrop-filter: blur(10px)) {
        .ps-quote-card {
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }
    }
    
    .ps-quote-text {
        font-size: 1.4rem;
        font-weight: 700;
        font-style: italic;
        color: #CBD5E1;
        line-height: 2;
        margin: 0;
        letter-spacing: -0.01em;
    }
    
    /* ============================================
       버튼 스타일 개선
       ============================================ */
    
    .ps-step-actions .stButton > button,
    .ps-status-content .stButton > button {
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        padding: 0.875rem 1.5rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
    }
    
    .ps-step-actions .stButton > button:hover,
    .ps-status-content .stButton > button:hover {
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3) !important;
    }
    
    .ps-step-actions .stButton > button[kind="primary"],
    .ps-status-content .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
        border: none !important;
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4), 0 0 30px rgba(59, 130, 246, 0.2) !important;
    }
    
    .ps-step-actions .stButton > button[kind="primary"]:hover,
    .ps-status-content .stButton > button[kind="primary"]:hover {
        box-shadow: 0 8px 24px rgba(59, 130, 246, 0.5), 0 0 40px rgba(59, 130, 246, 0.3) !important;
    }
    
    /* ============================================
       반응형 디자인
       ============================================ */
    
    @media (max-width: 768px) {
        .ps-brand-hero {
            padding: 3rem 1.5rem;
            border-radius: 20px;
            margin-bottom: 2rem;
        }
        
        .ps-brand-name {
            font-size: 3.5rem;
        }
        
        .ps-brand-tagline {
            font-size: 1.4rem;
        }
        
        .ps-brand-subtitle {
            font-size: 1rem;
            margin-bottom: 2rem;
        }
        
        .ps-brand-hero .stButton > button {
            font-size: 1rem !important;
            padding: 1rem 1.5rem !important;
            min-height: 56px !important;
        }
        
        .ps-status-card,
        .ps-step-card {
            padding: 1.5rem 1.25rem;
            border-radius: 16px;
        }
        
        .ps-status-title {
            font-size: 1.5rem;
        }
        
        .ps-step-title {
            font-size: 1.4rem;
        }
        
        .ps-metric-card {
            padding: 1rem;
        }
    }
    </style>
    """
    
    # 기존 스타일 태그 제거 후 재주입 (중복 방지)
    remove_script = """
    <script>
    (function() {
        // 기존 홈 프리미엄 CSS 제거
        var existingStyle = document.getElementById('ps-home-premium-style');
        if (existingStyle) {
            existingStyle.remove();
        }
    })();
    </script>
    """
    st.markdown(remove_script, unsafe_allow_html=True)
    
    # CSS 주입
    st.markdown(css, unsafe_allow_html=True)
    
    # 주입 완료 플래그 설정 (디버깅용)
    st.session_state["_ps_home_premium_css_injected"] = True
