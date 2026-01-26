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
        - CSS는 theme_manager.py의 전역 CSS에 포함되어 모든 페이지에서 자동 적용됨
    """
    # 푸터 내용 렌더링
    st.markdown("""
    <div class="ps-cause-footer-wrapper">
        <div class="ps-cause-footer">
            <div class="ps-cause-footer-brand-line">
                <span class="ps-cause-footer-brand">CAUSE OS</span>
                <span class="ps-cause-footer-separator">—</span>
                <span class="ps-cause-footer-tagline">성공에는 이유가 있습니다</span>
            </div>
            <div class="ps-cause-footer-copyright">© 2026 INNOVATION100. All rights reserved.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
