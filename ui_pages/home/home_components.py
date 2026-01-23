"""
홈 UI 카드/컴포넌트
"""
from __future__ import annotations

import streamlit as st


def kpi_card(label: str, value: str | int, gradient: str | None = None, empty_char: str = "-") -> None:
    """단일 KPI 카드 (숫자 또는 empty_char)."""
    if gradient:
        st.markdown(f"""
        <div style="padding: 1.2rem; background: linear-gradient(135deg, {gradient}); border-radius: 8px; text-align: center; color: white;">
            <div style="font-size: 0.85rem; opacity: 0.9; margin-bottom: 0.3rem;">{label}</div>
            <div style="font-size: 1.3rem; font-weight: 700;">{value if isinstance(value, str) else f'{value:,}'}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="padding: 1.2rem; background: #f8f9fa; border-radius: 8px; text-align: center;">
            <div style="font-size: 0.85rem; color: #6c757d; margin-bottom: 0.3rem;">{label}</div>
            <div style="font-size: 1.3rem; font-weight: 700; color: #6c757d;">{value}</div>
        </div>
        """, unsafe_allow_html=True)


def status_board_two_col(col1_val: str, col1_label: str, col2_val: str, col2_label: str, col2_sub: str | None = None) -> None:
    """상태판 2열 (이번 달 매출 | 마감률)."""
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div style="padding: 1.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; color: white; text-align: center;">
            <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">{col1_label}</div>
            <div style="font-size: 2rem; font-weight: 700;">{col1_val}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        sub = f"<div style='font-size: 0.85rem; opacity: 0.9;'>{col2_sub}</div>" if col2_sub else ""
        st.markdown(f"""
        <div style="padding: 1.5rem; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 12px; color: white; text-align: center;">
            <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">{col2_label}</div>
            <div style="font-size: 2rem; font-weight: 700; margin-bottom: 0.5rem;">{col2_val}</div>
            {sub}
        </div>
        """, unsafe_allow_html=True)
