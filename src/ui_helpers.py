"""
UI 헬퍼 함수 모듈 (디자인 개선)
"""
import streamlit as st


def render_page_header(title, icon="📋"):
    """페이지 헤더 렌더링 (개선된 디자인)

    화이트/다크 테마 상관없이 제목 텍스트는 항상 흰색으로 표시.
    배경은 각 페이지의 레이아웃/CSS에서 제어하도록 분리한다.
    """
    st.markdown(f"""
    <div style="margin-bottom: 2rem;">
        <h2 style="color: #ffffff; border-bottom: 3px solid #667eea; padding-bottom: 0.5rem; margin-bottom: 1rem;">
            {icon} {title}
        </h2>
    </div>
    """, unsafe_allow_html=True)


def render_section_header(title, icon="📋"):
    """섹션 헤더 렌더링 (개선된 디자인)"""
    st.markdown(f"""
    <div style="margin: 2rem 0 1rem 0;">
        <h3 style="color: #2c3e50; font-weight: 600; margin: 0;">
            {icon} {title}
        </h3>
    </div>
    """, unsafe_allow_html=True)


def render_section_divider():
    """섹션 구분선 렌더링"""
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
