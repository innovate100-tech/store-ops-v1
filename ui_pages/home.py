"""
홈 화면 (HOME v0)
완전 리셋된 단순 버전
"""
from src.bootstrap import bootstrap
import streamlit as st
from src.auth import get_current_store_id, get_current_store_name, check_login, show_login_page

# 공통 설정 적용
bootstrap(page_title="Home")

# 로그인 체크
if not check_login():
    show_login_page()
    st.stop()


def render_home():
    """
    HOME v0 - 단순 뼈대 버전
    """
    # 타이틀
    st.title("HOME (v0)")
    
    # 설명
    st.caption("홈 화면 재구성 중입니다.")
    
    st.markdown("---")
    
    # 버튼 2개
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("데이터 입력센터로", type="primary", use_container_width=True):
            st.session_state.current_page = "입력 허브"
            st.rerun()
    
    with col2:
        if st.button("데이터 분석센터로", type="primary", use_container_width=True):
            st.session_state.current_page = "분석 허브"
            st.rerun()
    
    st.markdown("---")
    
    # 현재 로그인 상태 (선택)
    try:
        store_id = get_current_store_id()
        store_name = get_current_store_name()
        
        if store_id and store_name:
            st.info(f"**현재 매장:** {store_name} (ID: {store_id})")
    except Exception:
        pass
