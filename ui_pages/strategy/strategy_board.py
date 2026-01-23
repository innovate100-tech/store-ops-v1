"""
전략 보드 페이지
- 가게 상태 분류 결과 + 전략 카드 TOP3 + 이번 주 실행 로드맵 표시
"""
from __future__ import annotations

import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo

from src.bootstrap import bootstrap
from src.ui_helpers import render_page_header
from src.auth import get_current_store_id
from ui_pages.strategy.store_state import classify_store_state
from ui_pages.strategy.strategy_cards import build_strategy_cards
from ui_pages.strategy.roadmap import build_weekly_roadmap

# 공통 설정 적용
bootstrap(page_title="전략 보드")


def render_strategy_board():
    """전략 보드 페이지 렌더링"""
    render_page_header("전략 보드 (이번 달)", "📌")
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    # 현재 연월
    kst = ZoneInfo("Asia/Seoul")
    now = datetime.now(kst)
    current_year = now.year
    current_month = now.month
    
    try:
        # 1. 가게 상태 분류
        state_result = classify_store_state(store_id, current_year, current_month)
        store_state = state_result.get("state", {})
        scores = state_result.get("scores", {})
        evidence = state_result.get("evidence", [])
        
        # 2. 전략 카드 생성
        cards_result = build_strategy_cards(
            store_id,
            current_year,
            current_month,
            state_payload=state_result
        )
        cards = cards_result.get("cards", [])
        
        # 3. 로드맵 생성
        roadmap = build_weekly_roadmap(cards_result)
        
        # 상단 배지: 상태 + 점수
        _render_state_badge(store_state, scores)
        
        # 섹션 1: 근거 (evidence)
        _render_evidence_section(evidence)
        
        # 섹션 2: 전략 카드 TOP3
        _render_strategy_cards_section(cards)
        
        # 섹션 3: 이번 주 실행 TOP3
        _render_roadmap_section(roadmap)
        
        # DEV 전용: debug 정보
        if st.session_state.get("_dev_mode", False):
            with st.expander("🔧 DEV: Debug 정보"):
                st.json({
                    "state": state_result,
                    "cards": cards_result,
                    "roadmap": roadmap
                })
    
    except Exception as e:
        st.error(f"전략 보드를 불러오는 중 오류가 발생했습니다: {str(e)}")
        st.info("가게 설계 센터에서 시작하세요.")
        if st.button("가게 설계 센터로 이동", key="fallback_to_design_center"):
            st.session_state["current_page"] = "가게 설계 센터"
            st.rerun()


def _render_state_badge(store_state: dict, scores: dict):
    """상단 배지: 상태 + 점수"""
    state_code = store_state.get("code", "unknown")
    state_label = store_state.get("label", "상태 미확인")
    overall_score = scores.get("overall", 0)
    
    # 상태별 색상
    color_map = {
        "survival": "🔴",
        "recovery": "🟡",
        "restructure": "🟠",
        "growth": "🟢",
        "unknown": "⚪"
    }
    emoji = color_map.get(state_code, "⚪")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"### {emoji} {state_label}")
    with col2:
        st.metric("종합 점수", f"{overall_score:.0f}점")
    
    st.divider()


def _render_evidence_section(evidence: list):
    """섹션 1: 근거 (evidence) 3개 카드"""
    st.markdown("### 📊 근거")
    
    if not evidence:
        st.info("데이터가 부족합니다. 먼저 마감/보정을 입력해주세요.")
        return
    
    # 최대 3개만 표시
    display_evidence = evidence[:3]
    
    cols = st.columns(len(display_evidence))
    for idx, ev in enumerate(display_evidence):
        with cols[idx]:
            title = ev.get("title", "근거")
            value = ev.get("value", "")
            delta = ev.get("delta")
            note = ev.get("note", "")
            
            st.markdown(f"**{title}**")
            if value:
                st.markdown(f"`{value}`")
            if delta:
                st.markdown(f"변화: `{delta}`")
            if note:
                st.caption(note)
    
    st.divider()


def _render_strategy_cards_section(cards: list):
    """섹션 2: 전략 카드 TOP3"""
    st.markdown("### 🎯 전략 카드 TOP3")
    
    if not cards:
        st.info("전략 카드를 생성할 수 없습니다.")
        return
    
    for card in cards:
        rank = card.get("rank", 0)
        title = card.get("title", "")
        goal = card.get("goal", "")
        why = card.get("why", "")
        evidence_list = card.get("evidence", [])
        cta = card.get("cta", {})
        
        with st.container():
            st.markdown(f"#### {rank}. {title}")
            st.markdown(f"**목표**: {goal}")
            st.markdown(f"**이유**: {why}")
            
            if evidence_list:
                st.markdown("**근거**:")
                for ev in evidence_list:
                    st.markdown(f"- {ev}")
            
            # CTA 버튼
            cta_label = cta.get("label", "실행하기")
            cta_page = cta.get("page", "")
            if cta_page:
                if st.button(cta_label, key=f"strategy_card_{rank}_cta", use_container_width=True):
                    st.session_state["current_page"] = cta_page
                    # params 전달 (tab 등)
                    params = cta.get("params", {})
                    if params:
                        for key, value in params.items():
                            st.session_state[f"_strategy_param_{key}"] = value
                    st.rerun()
            
            st.divider()


def _render_roadmap_section(roadmap: list):
    """섹션 3: 이번 주 실행 TOP3"""
    st.markdown("### 📋 이번 주 실행 TOP3")
    
    if not roadmap:
        st.info("실행 로드맵을 생성할 수 없습니다.")
        return
    
    for item in roadmap:
        rank = item.get("rank", 0)
        task = item.get("task", "")
        estimate = item.get("estimate", "30m")
        cta = item.get("cta", {})
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{rank}. {task}**")
        with col2:
            st.markdown(f"⏱️ `{estimate}`")
        
        # CTA 버튼
        cta_label = cta.get("label", "실행하기")
        cta_page = cta.get("page", "")
        if cta_page:
            if st.button(cta_label, key=f"roadmap_{rank}_cta", use_container_width=True):
                st.session_state["current_page"] = cta_page
                params = cta.get("params", {})
                if params:
                    for key, value in params.items():
                        st.session_state[f"_strategy_param_{key}"] = value
                st.rerun()
        
        st.divider()
