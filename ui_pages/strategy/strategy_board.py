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
from ui_pages.strategy.evidence_builder import build_evidence_bundle
from ui_pages.design_lab.design_insights import get_design_insights
from src.auth import get_current_store_id

# 공통 설정 적용
bootstrap(page_title="전략 보드")


def render_strategy_board():
    """전략 보드 페이지 렌더링"""
    render_page_header("전략 보드 (이번 달)", "📌")
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    # store_id를 전역으로 사용하기 위해 함수 내부에서 접근 가능하도록
    # (하지만 함수 파라미터로 전달하는 것이 더 깔끔하므로 수정)
    
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
        
        # 2. 전략 카드 생성 (v4 엔진 사용: 건강검진 통합)
        cards_result = build_strategy_cards(
            store_id,
            current_year,
            current_month,
            state_payload=state_result,
            use_v4=True
        )
        cards = cards_result.get("cards", [])
        
        # 3. 로드맵 생성
        roadmap = build_weekly_roadmap(cards_result)
        
        # 4. Evidence Bundle 생성 (숫자+설계+검진)
        design_insights = get_design_insights(store_id, current_year, current_month)
        evidence_bundle = build_evidence_bundle(
            store_id=store_id,
            year=current_year,
            month=current_month,
            metrics_bundle=None,  # state_result에서 추출 가능
            design_insights=design_insights,
            health_diag=None  # 내부에서 로드
        )
        
        # 상단 배지: 상태 + 점수
        _render_state_badge(store_state, scores)
        
        # 섹션 1: 근거 (evidence) - 표준화된 3종
        _render_evidence_section(evidence_bundle)
        
        # 섹션 2: 전략 카드 TOP3
        _render_strategy_cards_section(cards, store_id)
        
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


def _render_evidence_section(evidence_bundle: list):
    """섹션 1: 근거 (evidence) 3개 카드 - 표준화된 구조"""
    st.markdown("### 📊 근거")
    
    if not evidence_bundle:
        st.info("데이터가 부족합니다. 먼저 마감/보정을 입력해주세요.")
        return
    
    # 3개 고정 (숫자/설계/검진)
    cols = st.columns(3)
    
    for idx, ev in enumerate(evidence_bundle[:3]):
        with cols[idx]:
            ev_type = ev.get("type", "unknown")
            title = ev.get("title", "근거")
            summary = ev.get("summary", "")
            detail = ev.get("detail", "")
            cta = ev.get("cta", {})
            
            # 타입별 이모지
            type_emoji = {
                "numbers": "📊",
                "design": "🔥",
                "health": "🩺"
            }
            emoji = type_emoji.get(ev_type, "📌")
            
            # 카드 스타일
            st.markdown(f"""
            <div style="
                padding: 1rem;
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 0.5rem;
                background: rgba(255,255,255,0.05);
                margin-bottom: 0.5rem;
            ">
                <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">
                    {emoji} <strong>{title}</strong>
                </div>
                <div style="color: rgba(255,255,255,0.8); margin-bottom: 0.5rem;">
                    {summary}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Detail (expander)
            if detail:
                with st.expander("자세히 보기"):
                    st.markdown(detail)
            
            # CTA 버튼
            if cta and cta.get("route"):
                cta_label = cta.get("label", "이동하기")
                if st.button(cta_label, key=f"evidence_{idx}_cta", use_container_width=True):
                    st.session_state["current_page"] = cta["route"]
                    st.rerun()
    
    st.divider()


def _get_card_code_from_title(title: str) -> str:
    """
    카드 제목에서 카드 코드 추출
    
    Args:
        title: 카드 제목
    
    Returns:
        카드 코드 (없으면 빈 문자열)
    """
    # 제목 기반 매핑
    title_to_code = {
        "생존선": "FINANCE_SURVIVAL_LINE",
        "마진": "MENU_MARGIN_RECOVERY",
        "원가": "INGREDIENT_RISK_DIVERSIFY",
        "포트폴리오": "MENU_PORTFOLIO_REBALANCE",
        "매출 하락": "SALES_DROP_INVESTIGATION",
        "운영": "OPERATION_QSC_RECOVERY",
        "QSC": "OPERATION_QSC_RECOVERY",
    }
    
    for key, code in title_to_code.items():
        if key in title:
            return code
    
    return ""


def _load_completed_actions(store_id: str, week_start: date) -> list:
    """
    이번 주 완료된 전략 카드 로드 (간단한 구현: session_state 사용)
    
    Args:
        store_id: 매장 ID
        week_start: 주 시작일 (월요일)
    
    Returns:
        완료된 카드 코드 리스트
    """
    # session_state에서 완료된 카드 코드 리스트 가져오기
    key = f"_completed_actions_{store_id}_{week_start.isoformat()}"
    completed_actions = st.session_state.get(key, [])
    
    # 리스트가 아니면 빈 리스트 반환
    if not isinstance(completed_actions, list):
        return []
    
    return completed_actions


def _save_completed_action(store_id: str, card_code: str):
    """
    전략 카드 완료 저장 (간단한 구현: session_state 사용)
    
    Args:
        store_id: 매장 ID
        card_code: 카드 코드
    """
    from datetime import date, timedelta
    
    # 이번 주 시작일 계산
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    
    # session_state에 저장
    key = f"_completed_actions_{store_id}_{week_start.isoformat()}"
    completed_actions = st.session_state.get(key, [])
    
    if not isinstance(completed_actions, list):
        completed_actions = []
    
    # 중복 제거 후 추가
    if card_code and card_code not in completed_actions:
        completed_actions.append(card_code)
        st.session_state[key] = completed_actions


def _render_strategy_cards_section(cards: list, store_id: str):
    """섹션 2: 전략 카드 TOP3 (v4 포맷)"""
    st.markdown("### 🎯 전략 카드 TOP3")
    
    if not cards:
        st.info("전략 카드를 생성할 수 없습니다.")
        return
    
    # 완료 체크 로드 (이번 주)
    from datetime import date, timedelta
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    completed_actions = _load_completed_actions(store_id, week_start)
    
    # 완료 뱃지 표시
    if completed_actions:
        completed_count = len(completed_actions)
        st.caption(f"이번 주 완료: {completed_count}/3")
    
    # v4 공통 컴포넌트 사용
    from ui_pages.common.strategy_card_v4 import render_strategy_card_v4
    
    for card in cards:
        card_code = _get_card_code_from_title(card.get("title", ""))
        is_completed = card_code in completed_actions if card_code else False
        
        render_strategy_card_v4(card)
        
        # 완료 체크 버튼 (카드 하단)
        if card_code:
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if is_completed:
                    st.success("✅ 완료됨")
                else:
                    if st.button("✅ 완료", key=f"complete_{card_code}", use_container_width=True):
                        _save_completed_action(store_id, card_code)
                        # Phase 0 STEP 3: session_state 변경만으로 UI가 자동 업데이트되므로 rerun 불필요
        
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
