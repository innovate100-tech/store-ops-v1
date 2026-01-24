"""
설계실 공통 네비게이션 컴포넌트
"""
import streamlit as st


def render_back_to_design_center_button():
    """가게 전략 센터로 돌아가기 버튼"""
    if st.button("← 가게 전략 센터로 돌아가기", key="back_to_design_center", use_container_width=False):
        st.session_state.current_page = "가게 전략 센터"
        st.rerun()
