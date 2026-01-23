"""
입력 허브 페이지
입력 관련 모든 페이지로의 네비게이션 허브
"""
from src.bootstrap import bootstrap
import streamlit as st
from src.ui_helpers import render_page_header

# 공통 설정 적용
bootstrap(page_title="Input Hub")


def render_input_hub():
    """입력 허브 페이지 렌더링"""
    render_page_header("✍ 입력 허브", "✍")
    
    # 안내 문구
    st.info("💡 **입력은 기준(원본)을 만드는 곳입니다.** 업그레이드/변형은 🧠 설계에서 합니다.")
    
    st.markdown("---")
    
    # A) 매일 입력
    st.markdown("### 📅 매일 입력")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📝 오늘 입력(통합)", use_container_width=True, type="primary", key="input_hub_daily_input"):
            st.session_state["current_page"] = "일일 입력(통합)"
            st.rerun()
    
    with col2:
        if st.button("📋 점장 마감", use_container_width=True, type="primary", key="input_hub_manager_close"):
            st.session_state["current_page"] = "점장 마감"
            st.rerun()
    
    st.markdown("---")
    
    # B) 월 1회 입력
    st.markdown("### 📆 월 1회 입력")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📅 월간 정산(실제 입력)", use_container_width=True, type="secondary", key="input_hub_settlement"):
            st.session_state["current_page"] = "실제정산"
            st.rerun()
        st.caption("페이지 키: 실제정산 (기존 유지)")
    
    with col2:
        if st.button("🎯 목표 매출 구조(기준 입력)", use_container_width=True, type="secondary", key="input_hub_target_sales"):
            st.session_state["current_page"] = "목표 매출구조"
            st.rerun()
    
    with col3:
        if st.button("🧾 목표 비용 구조(기준 입력)", use_container_width=True, type="secondary", key="input_hub_target_cost"):
            st.session_state["current_page"] = "목표 비용구조"
            st.rerun()
    
    st.markdown("---")
    
    # C) 보정/과거 입력(필요할 때만)
    st.markdown("### 🔧 보정/과거 입력 (필요할 때만)")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧮 매출 등록(보정)", use_container_width=True, type="secondary", key="input_hub_sales_entry"):
            st.session_state["current_page"] = "매출 등록"
            st.rerun()
    
    with col2:
        if st.button("📦 판매량 등록(보정)", use_container_width=True, type="secondary", key="input_hub_sales_volume"):
            st.session_state["current_page"] = "판매량 등록"
            st.rerun()
