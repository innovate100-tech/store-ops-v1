"""
검진 결과 요약 페이지
가장 최근 완료 검진 기준으로 결과를 요약 표시
"""
import streamlit as st
import logging

logger = logging.getLogger(__name__)

def render_health_check_result():
    """검진 결과 요약 페이지 렌더링"""
    st.title("검진 결과 요약")
    
    st.info("""
    **PHASE 1에서 연결 예정**
    
    이 페이지는 가장 최근 완료된 건강검진의 결과를 요약하여 표시합니다.
    
    포함 예정 요소:
    - 9축 점수(Q,S,C,P1,P2,P3,M,H,F)
    - 위험/주의/양호 분류
    - Top3 리스크 자동 요약
    - HOME/전략으로 연결되는 CTA 버튼
    """)
