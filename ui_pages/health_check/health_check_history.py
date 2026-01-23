"""
검진 히스토리 페이지
검진 회차별 비교 및 트렌드 표시
"""
import streamlit as st
import logging

logger = logging.getLogger(__name__)

def render_health_check_history():
    """검진 히스토리 페이지 렌더링"""
    st.title("검진 히스토리")
    
    st.info("""
    **PHASE 1에서 연결 예정**
    
    이 페이지는 검진 회차별 히스토리를 표시합니다.
    
    포함 예정 요소:
    - 검진 회차 리스트
    - 날짜별 점수 변화
    - 축별 트렌드(Q~F)
    - "개선됨 / 악화됨 / 정체" 표시
    """)
