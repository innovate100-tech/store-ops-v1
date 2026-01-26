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
    # 푸터 내용 렌더링 - 명확한 클래스명과 인라인 스타일로 이중 보장
    st.markdown("""
    <div class="causeos-footer" style="width: 100% !important; margin-top: 18px !important; padding: 10px 0 6px 0 !important; text-align: center !important; opacity: 0.72 !important; font-size: 12px !important; line-height: 1.35 !important; letter-spacing: 0.2px !important; border-top: 1px solid rgba(255, 255, 255, 0.08) !important; display: block !important;">
        <div class="causeos-footer__line1" style="text-align: center !important; display: block !important; font-weight: 600 !important; color: rgba(148, 163, 184, 0.85) !important;">CAUSE OS — 성공에는 이유가 있습니다</div>
        <div class="causeos-footer__line2" style="text-align: center !important; display: block !important; margin-top: 2px !important; opacity: 0.9 !important; font-size: 11px !important; color: rgba(148, 163, 184, 0.45) !important;">© 2026 INNOVATION100. All rights reserved.</div>
    </div>
    """, unsafe_allow_html=True)
