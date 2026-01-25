"""
공통 헤더 컴포넌트 (제목 박스 + 전광판)
모든 페이지 상단에 표시되는 공통 헤더
"""
import streamlit as st
from src.ui.css_manager import inject_theme

try:
    from src.debug.nav_trace import push_render_step
except ImportError:
    def push_render_step(*args, **kwargs):
        pass


# 헤더 CSS 문자열 (상수로 관리, 핵심 속성에 !important 적용)
COMMON_HEADER_CSS = """
/* ========== 메인 헤더 (반응형) - 테마 토큰 기반 ========== */
.ps-header-card {
    background: linear-gradient(135deg, var(--ps-surface) 0%, var(--ps-surface-2) 30%, var(--ps-surface-2) 60%, var(--ps-surface) 100%) !important;
    background-size: 200% 200% !important;
    animation: ps-gradientShift 8s ease infinite !important;
    padding: 2.5rem !important;
    border-radius: 16px !important;
    color: var(--ps-text) !important;
    margin-bottom: 2rem !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 40px var(--ps-accent-weak) !important;
    position: relative !important;
    overflow: hidden !important;
    border: 1px solid var(--ps-border) !important;
}

.ps-header-card::before {
    content: '' !important;
    position: absolute !important;
    top: -50% !important;
    left: -50% !important;
    width: 200% !important;
    height: 200% !important;
    background: radial-gradient(circle, var(--ps-accent-weak) 0%, var(--ps-accent-weak) 30%, transparent 70%) !important;
    animation: ps-rotate 20s linear infinite !important;
}

.ps-header-card::after {
    content: '' !important;
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    bottom: 0 !important;
    background: 
        radial-gradient(circle at 20% 50%, var(--ps-accent-weak) 0%, transparent 50%),
        radial-gradient(circle at 80% 80%, var(--ps-accent-weak) 0%, transparent 50%),
        radial-gradient(circle at 40% 20%, var(--ps-accent-weak) 0%, transparent 50%) !important;
    animation: ps-sparkle 4s ease-in-out infinite alternate !important;
    pointer-events: none !important;
}

.ps-header-card h1 {
    position: relative !important;
    z-index: 1 !important;
    font-weight: 700 !important;
    letter-spacing: -0.5px !important;
    color: var(--ps-text) !important;
    display: flex !important;
    align-items: center !important;
    gap: 0.5rem !important;
    white-space: nowrap !important;
    font-size: 2.25rem !important;
    margin: 0 !important;
    padding: 0 !important;
}

.ps-header-card h1 .ps-title-text {
    color: var(--ps-text) !important;
    display: inline-block !important;
    background: none !important;
    -webkit-background-clip: initial !important;
    -webkit-text-fill-color: var(--ps-text) !important;
    background-clip: initial !important;
    text-shadow: none !important;
}

.ps-header-card h1 .ps-title-emoji {
    display: inline-block !important;
    -webkit-text-fill-color: initial !important;
    background: none !important;
    text-shadow: none !important;
    filter: none !important;
}

/* 저작권 표시 (오른쪽 하단) */
.ps-header-card .ps-copyright {
    position: absolute !important;
    bottom: 0.75rem !important;
    right: 1.5rem !important;
    font-size: calc(0.7rem * 1.15) !important;
    color: var(--ps-muted) !important;
    z-index: 2 !important;
    font-weight: 300 !important;
    letter-spacing: 0.5px !important;
}

/* 전광판 스타일 (독립 박스) */
.ps-marquee {
    position: relative !important;
    background: var(--ps-surface-2) !important;
    border: 1px solid var(--ps-accent-weak) !important;
    border-radius: 8px !important;
    padding: 0 !important;
    height: 44px !important;
    margin-bottom: 2rem !important;
    overflow: hidden !important;
    box-shadow: 
        0 0 8px var(--ps-accent-weak),
        inset 0 0 8px var(--ps-accent-weak) !important;
    display: flex !important;
    align-items: center !important;
}

.ps-marquee::before {
    content: '' !important;
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    bottom: 0 !important;
    background: repeating-linear-gradient(
        0deg,
        var(--ps-accent-weak) 0px,
        var(--ps-accent-weak) 2px,
        transparent 2px,
        transparent 4px
    ) !important;
    pointer-events: none !important;
    z-index: 1 !important;
}

.ps-marquee__container {
    position: relative !important;
    height: 100% !important;
    overflow: hidden !important;
    z-index: 10 !important;
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
}

.ps-marquee__inner {
    display: flex !important;
    align-items: center !important;
    width: max-content !important;
    will-change: transform !important;
    animation: ps-marquee-move 45.5s linear infinite !important;
    height: 100% !important;
}

.ps-marquee__track {
    flex: 0 0 auto !important;
    white-space: nowrap !important;
    color: var(--ps-accent) !important;
    font-weight: 700 !important;
    font-size: 1.2rem !important;
    letter-spacing: 0.3px !important;
    text-shadow: 0 0 2px var(--ps-accent-weak) !important;
    animation: ps-ledBlink 1.5s ease-in-out infinite !important;
    line-height: 1.1 !important;
    padding: 0 14px !important;
    display: flex !important;
    align-items: center !important;
    height: 100% !important;
    background: none !important;
    -webkit-background-clip: initial !important;
    -webkit-text-fill-color: var(--ps-accent) !important;
    background-clip: initial !important;
    opacity: 1 !important;
    filter: none !important;
}

@keyframes ps-ledBlink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.85; }
}

@keyframes ps-marquee-move {
    0% {
        transform: translateX(0);
    }
    100% {
        transform: translateX(-50%);
    }
}

@keyframes ps-gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

@keyframes ps-rotate {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

@keyframes ps-sparkle {
    0% { opacity: 0.5; }
    100% { opacity: 1; }
}

@media (max-width: 768px) {
    .ps-header-card {
        padding: 1.5rem 1rem !important;
        margin-bottom: 1rem !important;
        border-radius: 8px !important;
    }
    
    .ps-header-card h1 {
        font-size: 1.35rem !important;
    }
}
"""

DARK_THEME_CSS = """
/* 다크 모드 전용 CSS는 이제 전역 토큰으로 자동 처리됨 */
/* 필요 시 추가 오버라이드만 여기에 작성 */
"""


def render_common_header(marquee_text: str | None = None):
    """
    공통 헤더 렌더링 (제목 박스 + 전광판)
    
    Args:
        marquee_text: 전광판 텍스트 (None이면 전광판 미표시)
    
    Note:
        - DB/스토리지 호출 금지
        - 무거운 계산 금지
        - UI-only 구현
        - 제목은 고정 문자열 사용
        - CSS 주입은 1회만 실행 (가드 적용)
    """
    try:
        # THEME 계층: Common Header CSS (1회만 실행)
        if st.session_state.get("_ps_common_header_css_injected", False):
            pass  # CSS는 이미 주입됨, HTML만 렌더링
        else:
            inject_theme(f"<style>{COMMON_HEADER_CSS}</style>", "common_header")
            st.session_state["_ps_common_header_css_injected"] = True
        
        # 제목 박스 렌더 (고정 제목 사용) - HTML 블록으로 강제 렌더
        st.markdown("""
        <div class="ps-header-card">
            <h1>
                <span class="ps-title-emoji">😎</span>
                <span class="ps-title-text">외식경영 의사결정 시스템 (운영 OS)</span>
            </h1>
            <div class="ps-copyright">© 2026 황승진. All rights reserved.</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 전광판 렌더 (marquee_text가 있을 때만) - HTML 블록으로 강제 렌더
        if marquee_text:
            # 전광판 텍스트를 구분자와 충분한 공백으로 반복하여 무한 스크롤 효과
            # 끊김 없는 무한 루프를 위해 충분히 긴 텍스트 생성
            sep = "   •   "
            track_text = (marquee_text + sep) * 12  # 12번 반복하여 충분한 길이 확보
            # 트랙 2개를 렌더하여 seamless loop 구현
            st.markdown(f"""
            <div class="ps-marquee">
                <div class="ps-marquee__container">
                    <div class="ps-marquee__inner">
                        <div class="ps-marquee__track">{track_text}</div>
                        <div class="ps-marquee__track">{track_text}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    except Exception:
        # 헤더 렌더 실패해도 페이지는 계속 동작
        pass
