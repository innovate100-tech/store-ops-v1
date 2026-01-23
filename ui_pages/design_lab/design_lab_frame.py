"""
설계실 공통 프레임 (4층 구조)
- ZONE A: Coach Board (결론)
- ZONE B: Structure Map (시각화)
- ZONE C: Owner School (이론 카드)
- ZONE D: Design Tools (기존 기능 영역)
"""
from __future__ import annotations

import streamlit as st
from typing import List, Dict, Callable, Optional


def render_coach_board(
    cards: List[Dict[str, str]],
    verdict_text: str,
    action_title: str = None,
    action_reason: str = None,
    action_target_page: str = None,
    action_button_label: str = None
) -> None:
    """
    ZONE A: Coach Board (결론)
    
    Args:
        cards: [{"title": str, "value": str, "subtitle": str | None}]
        verdict_text: 한 줄 판결문
        action_title: 추천 액션 제목 (선택)
        action_reason: 추천 액션 이유 (선택)
        action_target_page: 추천 액션 대상 페이지 (선택)
        action_button_label: 추천 액션 버튼 라벨 (선택)
    """
    st.markdown("### 🟢 코치 요약")
    
    # 핵심 카드 3~4개
    if cards:
        card_cols = st.columns(min(len(cards), 4), gap="medium")
        for idx, card in enumerate(cards[:4]):
            with card_cols[idx]:
                title = card.get("title", "")
                value = card.get("value", "-")
                subtitle = card.get("subtitle")
                
                st.markdown(f"""
                <div style="padding: 1rem; background: linear-gradient(135deg, #e7f3ff 0%, #d1ecf1 100%); border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <div style="font-size: 0.85rem; color: #0c5460; margin-bottom: 0.3rem; font-weight: 600;">{title}</div>
                    <div style="font-size: 1.3rem; font-weight: 700; color: #17a2b8; margin-bottom: 0.2rem;">{value}</div>
                    {f'<div style="font-size: 0.75rem; color: #6c757d;">{subtitle}</div>' if subtitle else ''}
                </div>
                """, unsafe_allow_html=True)
    
    # 한 줄 판결문
    if verdict_text:
        st.markdown(f"""
        <div style="padding: 1rem 1.2rem; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 10px; border-left: 4px solid #17a2b8; margin-top: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            <div style="font-size: 0.95rem; color: #495057; line-height: 1.5; font-weight: 500;">{verdict_text}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 추천 액션
    if action_title and action_target_page:
        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="padding: 1rem 1.2rem; background: linear-gradient(135deg, #fff5f5 0%, #fee2e2 100%); border-radius: 10px; border-left: 4px solid #dc3545; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            <div style="font-weight: 600; color: #721c24; font-size: 0.95rem; margin-bottom: 0.3rem;">🎯 이번 달 추천 액션</div>
            <div style="font-size: 0.9rem; color: #495057; line-height: 1.5; margin-bottom: 0.5rem;">{action_title}</div>
            {f'<div style="font-size: 0.85rem; color: #6c757d; line-height: 1.4;">{action_reason}</div>' if action_reason else ''}
        </div>
        """, unsafe_allow_html=True)
        
        button_label = action_button_label or "바로가기"
        if st.button(button_label, type="primary", use_container_width=True, key=f"coach_action_{action_target_page}"):
            st.session_state["current_page"] = action_target_page
            st.rerun()
    
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)


def render_structure_map_container(
    content_func: Callable = None,
    empty_message: str = "데이터가 부족하여 구조 맵을 표시할 수 없습니다.",
    empty_action_label: str = None,
    empty_action_page: str = None
) -> None:
    """
    ZONE B: Structure Map (시각화)
    
    Args:
        content_func: 차트/맵을 렌더링하는 함수 (선택)
        empty_message: 데이터 없을 때 메시지
        empty_action_label: 데이터 없을 때 액션 버튼 라벨 (선택)
        empty_action_page: 데이터 없을 때 액션 대상 페이지 (선택)
    """
    st.markdown("### 🔵 구조 맵")
    
    if content_func:
        try:
            content_func()
        except Exception:
            st.info(empty_message)
            if empty_action_label and empty_action_page:
                if st.button(empty_action_label, key=f"structure_map_action_{empty_action_page}"):
                    st.session_state["current_page"] = empty_action_page
                    st.rerun()
    else:
        st.info(empty_message)
        if empty_action_label and empty_action_page:
            if st.button(empty_action_label, key=f"structure_map_action_{empty_action_page}"):
                st.session_state["current_page"] = empty_action_page
                st.rerun()
    
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)


def render_school_cards(cards: List[Dict[str, str]] = None) -> None:
    """
    ZONE C: Owner School (이론 카드)
    
    Args:
        cards: [{"title": str, "point1": str, "point2": str}] (선택, 없으면 기본 카드 사용)
    """
    st.markdown("### 🟣 사장 학교")
    
    # 기본 카드 (설계실별로 다를 수 있음)
    default_cards = [
        {
            "title": "구조 설계의 핵심",
            "point1": "고정비는 매출이 없어도 나가는 돈입니다",
            "point2": "변동비는 매출에 비례합니다"
        },
        {
            "title": "수익 구조 이해",
            "point1": "손익분기점은 목표가 아니라 생존선입니다",
            "point2": "매출이 오르면 얼마가 남는지 알고 있어야 합니다"
        },
        {
            "title": "메뉴 수익 관리",
            "point1": "원가율이 50%를 넘으면 수익 기여가 거의 없습니다",
            "point2": "저마진 메뉴는 가격 조정 또는 메뉴 교체를 고려하세요"
        },
    ]
    
    cards_to_show = cards if cards else default_cards
    
    if cards_to_show:
        school_cols = st.columns(min(len(cards_to_show), 3), gap="medium")
        for idx, card in enumerate(cards_to_show[:3]):
            with school_cols[idx]:
                title = card.get("title", "")
                point1 = card.get("point1", "")
                point2 = card.get("point2", "")
                
                st.markdown(f"""
                <div style="padding: 1.2rem; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 10px; border-left: 4px solid #6c757d; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <div style="font-weight: 700; color: #495057; font-size: 0.95rem; margin-bottom: 0.8rem;">{title}</div>
                    <div style="font-size: 0.85rem; color: #6c757d; line-height: 1.6; margin-bottom: 0.5rem;">• {point1}</div>
                    <div style="font-size: 0.85rem; color: #6c757d; line-height: 1.6;">• {point2}</div>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)


def render_design_tools_container(content_func: Callable) -> None:
    """
    ZONE D: Design Tools (기존 기능 영역)
    
    Args:
        content_func: 기존 페이지의 핵심 입력/테이블/수정 UI를 렌더링하는 함수
    """
    st.markdown("### 🔴 설계 도구")
    
    if content_func:
        content_func()
    
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
