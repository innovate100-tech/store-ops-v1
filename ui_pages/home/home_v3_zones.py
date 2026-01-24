"""
HOME v3 ZONE 렌더링 함수들
- ZONE 0: 오늘의 운영 지시
- ZONE 1: 이번 달 가게 전략 요약
- ZONE 2: 문제 인식 & 빠른 진입
- ZONE 3: 오늘 상태판 (숫자)
- ZONE 4: 이번 주 우선순위 TOP3
- ZONE 5: 가게 구조 스냅샷
"""
from __future__ import annotations

import logging
import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Optional

from ui_pages.strategy.store_state import classify_store_state
from ui_pages.strategy.strategy_cards import build_strategy_cards
from ui_pages.strategy.roadmap import build_weekly_roadmap
from ui_pages.home.home_data import load_home_kpis, get_menu_count, get_close_count
from ui_pages.home.home_rules import get_problems_top3
from ui_pages.design_lab.design_state_loader import get_design_state

logger = logging.getLogger(__name__)


def _render_zone0_today_instruction(store_id: str, year: int, month: int) -> None:
    """ZONE 0: 오늘의 운영 지시 (최상단, 가장 중요)"""
    # 기본값 초기화 (에러 발생 시에도 표시되도록)
    action_title = "가게 전략 센터부터 시작"
    action_cta = {"label": "가게 전략 센터", "page": "가게 전략 센터", "params": {}}
    evidence_line = "데이터 수집 중"
    today_action = None
    
    # 디버깅: 함수 호출 확인
    logger.info(f"ZONE 0 렌더링 시작: store_id={store_id}, year={year}, month={month}")
    
    # 제목은 home_page.py에서 이미 표시되므로 여기서는 제목 표시 제거
    
    try:
        # 전략 보드 데이터 로드 (v4 엔진 사용: 건강검진 통합)
        state_result = classify_store_state(store_id, year, month)
        cards_result = build_strategy_cards(store_id, year, month, state_payload=state_result, use_v4=True)
        roadmap = build_weekly_roadmap(cards_result)
        
        # 오늘의 1순위 행동 결정
        # 1순위: 로드맵 1순위
        if roadmap and len(roadmap) > 0:
            today_action = roadmap[0]
            action_title = today_action.get("task", "가게 전략 센터부터 시작")
            action_cta = today_action.get("cta", {"label": "지금 실행하기", "page": "가게 전략 센터", "params": {}})
        # 2순위: 전략 카드 1순위
        elif cards_result.get("cards") and len(cards_result["cards"]) > 0:
            first_card = cards_result["cards"][0]
            impact = first_card.get("impact", {})
            action_plan = first_card.get("action_plan", {})
            
            today_action = {
                "task": first_card.get("title", "가게 전략 센터부터 시작"),
                "why": first_card.get("why", ""),
                "cta": first_card.get("cta", {"label": "지금 실행하기", "page": "가게 전략 센터", "params": {}}),
                "impact": impact,
                "action_plan": action_plan
            }
            action_title = today_action["task"]
            action_cta = today_action["cta"]
        
        # 근거 1줄 생성 (숫자 근거 + 검진 근거 결합)
        evidence_parts = []
        
        # 숫자 근거
        if today_action and "why" in today_action and today_action["why"]:
            evidence_parts.append(today_action["why"])
        elif cards_result.get("store_state", {}).get("primary_reason"):
            evidence_parts.append(cards_result["store_state"]["primary_reason"])
        else:
            # 기본 근거
            try:
                from src.storage_supabase import load_monthly_sales_total, calculate_break_even_sales
                monthly_sales = load_monthly_sales_total(store_id, year, month) or 0
                break_even = calculate_break_even_sales(store_id, year, month) or 0
                if break_even > 0:
                    ratio = (monthly_sales / break_even) * 100 if monthly_sales > 0 else 0
                    evidence_parts.append(f"손익분기점 대비 {ratio:.0f}%")
                else:
                    evidence_parts.append("데이터 수집 중")
            except Exception:
                evidence_parts.append("데이터 수집 중")
        
        # 검진 근거 추가 (보조 근거로 1줄만)
        try:
            from ui_pages.home.home_data import load_latest_health_diag
            from src.health_check.health_integration import get_health_evidence_line
            health_diag = load_latest_health_diag(store_id)
            if health_diag:
                health_evidence = get_health_evidence_line(health_diag)
                if health_evidence and len(evidence_parts) > 0:
                    # 숫자 근거가 있으면 검진 근거를 짧게 추가
                    evidence_parts.append(f"+ {health_evidence}")
        except Exception as e:
            logger.debug(f"검진 근거 추가 실패: {e}")
        
        # 최종 근거 문장 생성
        evidence_line = " | ".join(evidence_parts) if evidence_parts else "데이터 수집 중"
        
        # action_title이 비어있으면 기본값 사용
        if not action_title or action_title.strip() == "":
            action_title = "가게 전략 센터부터 시작"
        
    except Exception as e:
        # 에러 발생 시 Fallback (에러 메시지도 표시)
        logger.error(f"ZONE 0 데이터 로드 오류: {e}", exc_info=True)
        
        # DEV 모드에서만 에러 상세 표시
        if st.session_state.get("_dev_mode", False):
            st.error(f"ZONE 0 데이터 로드 오류: {str(e)}")
    
    # 메인 카드 표시 (항상 표시되도록 try 블록 밖으로 이동)
    # action_title과 evidence_line이 확실히 설정되었는지 확인
    if not action_title or action_title.strip() == "":
        action_title = "가게 전략 센터부터 시작"
    if not evidence_line or evidence_line.strip() == "":
        evidence_line = "데이터 수집 중"
    
    # 메인 카드 표시 (v4 포맷: impact 포함)
    impact_info = ""
    if today_action and "impact" in today_action:
        impact = today_action.get("impact", {})
        won = impact.get("won")
        # won이 None이거나 0 이하일 때는 메시지를 표시하지 않음 (과도한 노출 방지)
        if won is not None and won > 0:
            kind = impact.get("kind", "profit_up")
            kind_label = "예상 이익" if kind == "profit_up" else "리스크 회피" if kind == "risk_avoid" else "간접효과"
            confidence = impact.get("confidence", 0.5)
            impact_info = f"""
            <div style="margin-top: 1rem; padding: 1rem; background: rgba(255,255,255,0.15); border-radius: 8px;">
                <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.3rem;">💰 {kind_label}</div>
                <div style="font-size: 1.5rem; font-weight: 700;">+{won:,}원/월</div>
                <div style="font-size: 0.8rem; opacity: 0.8; margin-top: 0.3rem;">신뢰도 {confidence*100:.0f}%</div>
            </div>
            """
        # won이 None이면 메시지 표시하지 않음 (데이터 부족 시 과도한 노출 방지)
    
    st.markdown(f"""
    <div style="padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 16px; color: white; box-shadow: 0 4px 12px rgba(102,126,234,0.4); margin-bottom: 1rem;">
        <h3 style="color: white; margin-bottom: 1rem; font-size: 1.3rem; font-weight: 700;">오늘은 '{action_title}'부터 하세요.</h3>
        <p style="color: rgba(255,255,255,0.95); margin: 0; font-size: 1rem; line-height: 1.6;">{evidence_line}</p>
        {impact_info}
    </div>
    """, unsafe_allow_html=True)
    
    # 메인 버튼 (항상 표시되도록)
    cta_label = action_cta.get("label", "지금 실행하기")
    cta_page = action_cta.get("page", "가게 전략 센터")
    
    col_main, col_sub = st.columns([2, 1])
    with col_main:
        if st.button(cta_label, type="primary", use_container_width=True, key="zone0_main_action"):
            st.session_state["current_page"] = cta_page
            params = action_cta.get("params", {})
            if params:
                for key, value in params.items():
                    st.session_state[f"_strategy_param_{key}"] = value
            st.rerun()
    with col_sub:
        if st.button("📊 전략 센터 전체 보기", key="zone0_to_strategy_board", use_container_width=True):
            st.session_state["current_page"] = "가게 전략 센터"
            st.rerun()
    
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)


def _render_zone1_strategy_summary(store_id: str, year: int, month: int) -> None:
    """ZONE 1: 이번 달 가게 전략 요약 (v4 포맷: 전략 카드 TOP3 + Evidence)"""
    st.markdown("### 🧭 이번 달 가게 전략")
    
    try:
        # 전략 데이터 로드 (v4 엔진 사용)
        state_result = classify_store_state(store_id, year, month)
        cards_result = build_strategy_cards(store_id, year, month, state_payload=state_result, use_v4=True)
        
        store_state = state_result.get("state", {})
        cards = cards_result.get("cards", [])
        
        # DEV 모드: 디버그 정보 표시
        if st.session_state.get("_dev_mode", False):
            with st.expander("🔍 ZONE 1 디버그 정보", expanded=False):
                st.write(f"**store_state**: {store_state}")
                st.write(f"**cards 개수**: {len(cards) if cards else 0}")
                st.write(f"**cards_result keys**: {list(cards_result.keys()) if cards_result else 'None'}")
                if cards:
                    st.write(f"**첫 번째 카드**: {cards[0] if len(cards) > 0 else 'None'}")
        
        # Evidence 섹션 추가 (PHASE 1-C)
        try:
            from ui_pages.strategy.evidence_builder import build_evidence_bundle
            from ui_pages.design_lab.design_insights import get_design_insights
            
            design_insights = get_design_insights(store_id, year, month)
            evidence_bundle = build_evidence_bundle(
                store_id=store_id,
                year=year,
                month=month,
                metrics_bundle=None,
                design_insights=design_insights,
                health_diag=None
            )
            
            if evidence_bundle:
                st.markdown("#### 📊 근거")
                cols = st.columns(min(len(evidence_bundle), 3))
                for idx, ev in enumerate(evidence_bundle[:3]):
                    with cols[idx]:
                        ev_type = ev.get("type", "unknown")
                        title = ev.get("title", "근거")
                        summary = ev.get("summary", "")
                        
                        type_emoji = {
                            "numbers": "📊",
                            "design": "🔥",
                            "health": "🩺"
                        }
                        emoji = type_emoji.get(ev_type, "📌")
                        
                        st.markdown(f"""
                        <div style="
                            padding: 1rem;
                            border: 1px solid rgba(255,255,255,0.2);
                            border-radius: 0.5rem;
                            background: rgba(255,255,255,0.05);
                            margin-bottom: 0.5rem;
                        ">
                            <div style="font-size: 1rem; margin-bottom: 0.3rem;">
                                {emoji} <strong>{title}</strong>
                            </div>
                            <div style="color: rgba(255,255,255,0.8); font-size: 0.85rem;">
                                {summary}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.divider()
        except Exception as e:
            logger.warning(f"Evidence 섹션 렌더링 실패: {e}")
            if st.session_state.get("_dev_mode", False):
                st.error(f"Evidence 오류: {e}")
        
        # 전략 카드 TOP3 표시 (v4 포맷)
        if cards and len(cards) > 0:
            from ui_pages.common.strategy_card_v4 import render_strategy_card_v4
            
            # TOP3만 표시
            for card in cards[:3]:
                render_strategy_card_v4(card)
        else:
            # Fallback UI: 전략 카드가 없을 때
            st.info("""
            **전략을 계산 중입니다.**
            
            데이터가 부족하거나 전략 생성 중 오류가 발생했습니다.
            - 마감 데이터를 입력하세요
            - 가게 전략 센터에서 기본 설정을 완료하세요
            - 건강검진을 실시하세요
            """)
            
            col_fallback1, col_fallback2, col_fallback3 = st.columns(3)
            with col_fallback1:
                if st.button("📋 점장 마감", use_container_width=True, key="zone1_fallback_close"):
                    st.session_state["current_page"] = "점장 마감"
                    st.rerun()
            with col_fallback2:
                if st.button("🔥 가게 전략 센터", use_container_width=True, key="zone1_fallback_design"):
                    st.session_state["current_page"] = "가게 전략 센터"
                    st.rerun()
            with col_fallback3:
                if st.button("🩺 건강검진 실시", use_container_width=True, key="zone1_fallback_health"):
                    st.session_state["current_page"] = "건강검진 실시"
                    st.rerun()
        
        # 버튼
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("전략 센터 전체 보기", use_container_width=True, key="zone1_to_strategy_board"):
                st.session_state["current_page"] = "가게 전략 센터"
                st.rerun()
        with col_btn2:
            if st.button("가게 전략 센터", use_container_width=True, key="zone1_to_design_center"):
                st.session_state["current_page"] = "가게 전략 센터"
                st.rerun()
        
    
    except Exception as e:
        # 에러 발생 시 상세 정보 표시
        logger.error(f"ZONE 1 전략 요약 렌더링 오류: {e}", exc_info=True)
        
        # DEV 모드에서만 상세 에러 표시
        if st.session_state.get("_dev_mode", False):
            st.error(f"전략 요약 로드 오류: {str(e)}")
            import traceback
            with st.expander("상세 에러 정보"):
                st.code(traceback.format_exc())
        else:
            st.info("전략 요약을 불러오는 중입니다.")
        
        # Fallback UI
        st.info("""
        **전략을 계산할 수 없습니다.**
        
        다음을 확인해주세요:
        - 마감 데이터 입력
        - 가게 전략 센터 기본 설정
        - 건강검진 실시
        """)
        
        col_fallback1, col_fallback2 = st.columns(2)
        with col_fallback1:
            if st.button("가게 전략 센터로 이동", use_container_width=True, key="zone1_error_fallback_design"):
                st.session_state["current_page"] = "가게 전략 센터"
                st.rerun()
        with col_fallback2:
            if st.button("전략 센터로 이동", use_container_width=True, key="zone1_error_fallback_strategy"):
                st.session_state["current_page"] = "가게 전략 센터"
                st.rerun()
    
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)


def _render_zone2_quick_actions(store_id: str) -> None:
    """ZONE 2: 문제 인식 & 빠른 진입"""
    st.markdown("### 🚨 문제 인식 & 빠른 진입")
    
    col1, col2, col3 = st.columns(3, gap="medium")
    
    with col1:
        st.markdown("""
        <div style="padding: 1.5rem; background: linear-gradient(135deg, #fff5f5 0%, #fee2e2 100%); border-radius: 12px; border-left: 4px solid #dc3545; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">📋</div>
            <div style="font-weight: 600; color: #721c24; margin-bottom: 0.5rem; font-size: 1rem;">분석총평</div>
            <div style="font-size: 0.85rem; color: #856404; line-height: 1.4;">세부 분석을 복합해 최종 자료와 해석을 한눈에 확인합니다.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("분석총평 보기", type="primary", use_container_width=True, key="zone2_analysis_summary"):
            st.session_state["current_page"] = "분석총평"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div style="padding: 1.5rem; background: linear-gradient(135deg, #e7f3ff 0%, #d1ecf1 100%); border-radius: 12px; border-left: 4px solid #17a2b8; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">🏗</div>
            <div style="font-weight: 600; color: #0c5460; margin-bottom: 0.5rem; font-size: 1rem;">가게 구조 진단하기</div>
            <div style="font-size: 0.85rem; color: #0c5460; line-height: 1.4;">4개 설계실 통합 진단 및 전략 실행.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("가게 전략 센터", type="primary", use_container_width=True, key="zone2_design_center"):
            st.session_state["current_page"] = "가게 전략 센터"
            st.rerun()
    
    with col3:
        st.markdown("""
        <div style="padding: 1.5rem; background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border-radius: 12px; border-left: 4px solid #0ea5e9; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">🛠</div>
            <div style="font-weight: 600; color: #0c4a6e; margin-bottom: 0.5rem; font-size: 1rem;">오늘 입력/보정</div>
            <div style="font-size: 0.85rem; color: #0c4a6e; line-height: 1.4;">마감 / 매출·네이버방문자 보정 / 판매량 보정</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("입력하기", type="primary", use_container_width=True, key="zone2_input"):
            st.session_state["current_page"] = "점장 마감"
            st.rerun()
    
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)


def _render_zone3_status_board(store_id: str, year: int, month: int, kpis: dict, unofficial_days: int) -> None:
    """ZONE 3: 오늘 상태판 (숫자, 크기 축소) - 기존 ZONE 1 재사용"""
    # 기존 _render_zone1_status_board를 호출하되, 제목과 스타일만 변경
    from ui_pages.home.home_page import _render_zone1_status_board
    
    # 제목 변경
    st.markdown("### 📊 오늘 상태판 (근거 정보)")
    
    # 기존 함수 호출 (내부적으로는 큰 스타일이지만, 여기서는 작게 보이도록)
    # 실제로는 기존 함수를 수정하지 않고 여기서 직접 렌더링
    monthly_sales = kpis["monthly_sales"]
    yesterday_sales = kpis["yesterday_sales"]
    close_stats = kpis["close_stats"]
    revenue_per_visit = kpis["revenue_per_visit"]
    closed_days, total_days, close_rate, streak_days = close_stats
    
    # 미마감 배지 (작게)
    if unofficial_days > 0:
        st.caption(f"⚠️ 미마감 데이터 포함 ({unofficial_days}일)")
    
    # KPI 4개 (컴팩트 - st.metric 사용)
    k1, k2, k3, k4 = st.columns(4, gap="small")
    with k1:
        st.metric("어제 매출", f"{yesterday_sales:,}원" if yesterday_sales > 0 else "-")
    with k2:
        st.metric("이번 달 누적", f"{monthly_sales:,}원" if monthly_sales > 0 else "-")
    with k3:
        avg_daily = (monthly_sales / total_days) if total_days > 0 else 0
        avg_text = f"{int(avg_daily):,}원" if avg_daily > 0 else "-"
        st.metric("평균 일매출", avg_text)
    with k4:
        if revenue_per_visit and revenue_per_visit > 0:
            st.metric("객단가", f"{revenue_per_visit:,}원")
        else:
            st.metric("객단가", "-")
    
    # 상태 스트립 (1줄, 작게)
    missing_days = total_days - closed_days
    status_parts = []
    if closed_days > 0:
        pct = int(close_rate * 100)
        status_parts.append(f"마감률 {pct}%")
    if streak_days > 0:
        status_parts.append(f"연속 {streak_days}일")
    if missing_days > 0:
        status_parts.append(f"미마감 {missing_days}일")
    
    if status_parts:
        status_text = " • ".join(status_parts)
        st.caption(status_text)
    
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)


def _render_zone4_weekly_priorities(store_id: str, year: int, month: int) -> None:
    """ZONE 4: 이번 주 우선순위 TOP3"""
    st.markdown("### 📋 이번 주 우선순위 TOP3")
    
    try:
        # 로드맵 로드
        state_result = classify_store_state(store_id, year, month)
        cards_result = build_strategy_cards(store_id, year, month, state_payload=state_result)
        roadmap = build_weekly_roadmap(cards_result)
        
        if not roadmap:
            st.info("이번 주 우선순위를 생성할 수 없습니다.")
            return
        
        for item in roadmap[:3]:
            rank = item.get("rank", 0)
            task = item.get("task", "")
            estimate = item.get("estimate", "30m")
            cta = item.get("cta", {})
            
            col_task, col_time, col_btn = st.columns([3, 1, 2])
            with col_task:
                st.markdown(f"**{rank}. {task}**")
            with col_time:
                st.markdown(f"⏱️ `{estimate}`")
            with col_btn:
                cta_label = cta.get("label", "바로 실행")
                cta_page = cta.get("page", "")
                if cta_page:
                    if st.button(cta_label, key=f"zone4_roadmap_{rank}", use_container_width=True):
                        st.session_state["current_page"] = cta_page
                        params = cta.get("params", {})
                        if params:
                            for key, value in params.items():
                                st.session_state[f"_strategy_param_{key}"] = value
                        st.rerun()
            
            st.divider()
    
    except Exception as e:
        st.info("이번 주 우선순위를 불러오는 중입니다.")
    
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)


def _render_zone5_design_snapshot(store_id: str, year: int, month: int) -> None:
    """ZONE 5: 가게 구조 스냅샷 (보조)"""
    st.markdown("### 🏗 가게 구조 스냅샷")
    
    try:
        design_state = get_design_state(store_id, year, month)
        
        col1, col2, col3, col4 = st.columns(4, gap="small")
        
        # 메뉴 포트폴리오
        menu_portfolio = design_state.get("menu_portfolio", {})
        menu_score = menu_portfolio.get("score", 0)
        menu_status = menu_portfolio.get("status", "unknown")
        with col1:
            status_emoji = "✅" if menu_status == "safe" else "⚠️" if menu_status == "warn" else "🔴"
            st.metric("메뉴 구조", f"{menu_score}점", delta=None)
            st.caption(status_emoji)
        
        # 메뉴 수익
        menu_profit = design_state.get("menu_profit", {})
        profit_score = menu_profit.get("score", 0)
        profit_status = menu_profit.get("status", "unknown")
        with col2:
            status_emoji = "✅" if profit_status == "safe" else "⚠️" if profit_status == "warn" else "🔴"
            st.metric("메뉴 수익", f"{profit_score}점", delta=None)
            st.caption(status_emoji)
        
        # 재료 구조
        ingredient = design_state.get("ingredient_structure", {})
        ing_score = ingredient.get("score", 0)
        ing_status = ingredient.get("status", "unknown")
        with col3:
            status_emoji = "✅" if ing_status == "safe" else "⚠️" if ing_status == "warn" else "🔴"
            st.metric("재료 구조", f"{ing_score}점", delta=None)
            st.caption(status_emoji)
        
        # 수익 구조
        revenue = design_state.get("revenue_structure", {})
        rev_score = revenue.get("score", 0)
        rev_status = revenue.get("status", "unknown")
        with col4:
            status_emoji = "✅" if rev_status == "safe" else "⚠️" if rev_status == "warn" else "🔴"
            st.metric("수익 구조", f"{rev_score}점", delta=None)
            st.caption(status_emoji)
        
        if st.button("가게 전략 센터로", use_container_width=True, key="zone5_to_design_center"):
            st.session_state["current_page"] = "가게 전략 센터"
            st.rerun()
    
    except Exception:
        st.info("구조 스냅샷을 불러오는 중입니다.")
    
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
