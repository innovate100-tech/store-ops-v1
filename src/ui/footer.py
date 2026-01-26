"""
CAUSE OS 전용 제품 푸터 컴포넌트
모든 페이지 하단에 표시되는 브랜드 시그니처
"""
import streamlit as st


def render_cause_os_footer():
    """
    CAUSE OS 푸터 렌더링
    
    Note:
        - OS 명판 / 브랜드 시그니처 역할
        - 얇고 작은 폰트, 연한 톤
        - 페이지 맨 아래 마침표 역할
        - 중앙 정렬
        - Self-contained: CSS를 함수 내부에 포함하여 페이지 이동 시에도 안정적으로 적용됨
    """
    # 푸터 CSS와 HTML을 함께 출력 (self-contained)
    st.markdown("""
    <style>
    .causeos-footer {
        width: 100% !important;
        margin-top: 18px !important;
        padding: 10px 0 6px 0 !important;
        text-align: center !important;
        opacity: 0.72 !important;
        font-size: 12px !important;
        line-height: 1.35 !important;
        letter-spacing: 0.2px !important;
        border-top: 1px solid rgba(255, 255, 255, 0.08) !important;
        display: block !important;
        color: rgba(148, 163, 184, 0.65) !important;
    }
    
    .causeos-footer__line1 {
        text-align: center !important;
        display: block !important;
        font-weight: 600 !important;
        color: rgba(148, 163, 184, 0.85) !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    .causeos-footer__line2 {
        text-align: center !important;
        display: block !important;
        margin-top: 2px !important;
        opacity: 0.9 !important;
        font-size: 11px !important;
        color: rgba(148, 163, 184, 0.45) !important;
        font-weight: 300 !important;
    }
    
    /* Streamlit 마크다운 컨테이너 오버라이드 */
    [data-testid="stMarkdownContainer"] .causeos-footer,
    [data-testid="stMarkdownContainer"] .causeos-footer *,
    .stMarkdown .causeos-footer,
    .stMarkdown .causeos-footer * {
        text-align: center !important;
    }
    
    /* 전역 transition이 푸터에 영향을 주지 않도록 */
    .causeos-footer,
    .causeos-footer * {
        transition: none !important;
    }
    
    /* 다크 모드 대응 */
    @media (prefers-color-scheme: dark) {
        .causeos-footer {
            border-top-color: rgba(148, 163, 184, 0.15) !important;
        }
    }
    </style>
    
    <div class="causeos-footer">
        <div class="causeos-footer__line1">CAUSE OS — 성공에는 이유가 있습니다</div>
        <div class="causeos-footer__line2">© 2026 INNOVATION100. All rights reserved.</div>
    </div>
    """, unsafe_allow_html=True)
