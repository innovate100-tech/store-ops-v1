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
    action_title = "가게 설계 센터부터 시작"
    action_cta = {"label": "가게 설계 센터", "page": "가게 설계 센터", "params": {}}
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
            action_title = today_action.get("task", "가게 설계 센터부터 시작")
            action_cta = today_action.get("cta", {"label": "지금 실행하기", "page": "가게 설계 센터", "params": {}})
        # 2순위: 전략 카드 1순위
        elif cards_result.get("cards") and len(cards_result["cards"]) > 0:
            first_card = cards_result["cards"][0]
            today_action = {
                "task": first_card.get("title", "가게 설계 센터부터 시작"),
                "why": first_card.get("why", ""),
                "cta": first_card.get("cta", {"label": "지금 실행하기", "page": "가게 설계 센터", "params": {}})
            }
            action_title = today_action["task"]
            action_cta = today_action["cta"]
        
        # 근거 1줄 생성
        if today_action and "why" in today_action and today_action["why"]:
            evidence_line = today_action["why"]
        elif cards_result.get("store_state", {}).get("primary_reason"):
            evidence_line = cards_result["store_state"]["primary_reason"]
        else:
            # 기본 근거
            try:
                from src.storage_supabase import load_monthly_sales_total, calculate_break_even_sales
                monthly_sales = load_monthly_sales_total(store_id, year, month) or 0
                break_even = calculate_break_even_sales(store_id, year, month) or 0
                if break_even > 0:
                    ratio = (monthly_sales / break_even) * 100 if monthly_sales > 0 else 0
                    evidence_line = f"손익분기점 대비 {ratio:.0f}%"
                else:
                    evidence_line = "데이터 수집 중"
            except Exception:
                evidence_line = "데이터 수집 중"
        
        # action_title이 비어있으면 기본값 사용
        if not action_title or action_title.strip() == "":
            action_title = "가게 설계 센터부터 시작"
        
    except Exception as e:
        # 에러 발생 시 Fallback (에러 메시지도 표시)
        logger.error(f"ZONE 0 데이터 로드 오류: {e}", exc_info=True)
        
        # DEV 모드에서만 에러 상세 표시
        if st.session_state.get("_dev_mode", False):
            st.error(f"ZONE 0 데이터 로드 오류: {str(e)}")
    
    # 메인 카드 표시 (항상 표시되도록 try 블록 밖으로 이동)
    # action_title과 evidence_line이 확실히 설정되었는지 확인
    if not action_title or action_title.strip() == "":
        action_title = "가게 설계 센터부터 시작"
    if not evidence_line or evidence_line.strip() == "":
        evidence_line = "데이터 수집 중"
    
    # 메인 카드 표시 (더 확실하게 표시되도록)
    # 먼저 간단한 텍스트로 표시 확인
    st.markdown(f"**오늘은 '{action_title}'부터 하세요.**")
    st.markdown(f"*{evidence_line}*")
    st.markdown("---")
    
    # 그 다음 스타일 카드 표시
    st.markdown(f"""
    <div style="padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 16px; color: white; box-shadow: 0 4px 12px rgba(102,126,234,0.4); margin-bottom: 1rem;">
        <h3 style="color: white; margin-bottom: 1rem; font-size: 1.3rem; font-weight: 700;">오늘은 '{action_title}'부터 하세요.</h3>
        <p style="color: rgba(255,255,255,0.95); margin: 0; font-size: 1rem; line-height: 1.6;">{evidence_line}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 메인 버튼 (항상 표시되도록)
    cta_label = action_cta.get("label", "지금 실행하기")
    cta_page = action_cta.get("page", "가게 설계 센터")
    
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
        if st.button("📊 이번 달 전략 보기", key="zone0_to_strategy_board", use_container_width=True):
            st.session_state["current_page"] = "전략 보드"
            st.rerun()
    
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)


def _render_zone1_strategy_summary(store_id: str, year: int, month: int) -> None:
    """ZONE 1: 이번 달 가게 전략 요약"""
    st.markdown("### 🧭 이번 달 가게 전략")
    
    try:
        # 전략 데이터 로드
        state_result = classify_store_state(store_id, year, month)
        cards_result = build_strategy_cards(store_id, year, month, state_payload=state_result)
        
        store_state = state_result.get("state", {})
        cards = cards_result.get("cards", [])
        
        # 카드 3개 표시
        col1, col2, col3 = st.columns(3, gap="medium")
        
        with col1:
            # 가게 상태
            state_code = store_state.get("code", "unknown")
            state_label = store_state.get("label", "상태 미확인")
            color_map = {
                "survival": "🔴",
                "recovery": "🟡",
                "restructure": "🟠",
                "growth": "🟢",
                "unknown": "⚪"
            }
            emoji = color_map.get(state_code, "⚪")
            st.markdown(f"""
            <div style="padding: 1.5rem; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 12px; border-left: 4px solid #17a2b8; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <div style="font-size: 0.9rem; color: #6c757d; margin-bottom: 0.5rem; font-weight: 600;">가게 상태</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #495057;">{emoji} {state_label}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # 메인 전략
            main_strategy = "전략 수립 중" if not cards else cards[0].get("title", "전략 수립 중")
            st.markdown(f"""
            <div style="padding: 1.5rem; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 12px; border-left: 4px solid #17a2b8; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <div style="font-size: 0.9rem; color: #6c757d; margin-bottom: 0.5rem; font-weight: 600;">메인 전략</div>
                <div style="font-size: 1rem; font-weight: 600; color: #495057; line-height: 1.4;">{main_strategy}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            # 가장 위험한 구조
            design_state = get_design_state(store_id, year, month)
            risk_areas = []
            if design_state.get("menu_portfolio", {}).get("status") == "risk":
                risk_areas.append("메뉴")
            if design_state.get("menu_profit", {}).get("status") == "risk":
                risk_areas.append("메뉴수익")
            if design_state.get("ingredient_structure", {}).get("status") == "risk":
                risk_areas.append("재료")
            if design_state.get("revenue_structure", {}).get("status") == "risk":
                risk_areas.append("수익")
            
            risk_text = risk_areas[0] if risk_areas else "없음"
            st.markdown(f"""
            <div style="padding: 1.5rem; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 12px; border-left: 4px solid #17a2b8; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <div style="font-size: 0.9rem; color: #6c757d; margin-bottom: 0.5rem; font-weight: 600;">가장 위험한 구조</div>
                <div style="font-size: 1rem; font-weight: 600; color: #495057;">{risk_text}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # 버튼
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("전략 보드 전체 보기", use_container_width=True, key="zone1_to_strategy_board"):
                st.session_state["current_page"] = "전략 보드"
                st.rerun()
        with col_btn2:
            if st.button("가게 설계 센터", use_container_width=True, key="zone1_to_design_center"):
                st.session_state["current_page"] = "가게 설계 센터"
                st.rerun()
    
    except Exception as e:
        st.info("전략 요약을 불러오는 중입니다.")
    
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)


def _render_zone2_quick_actions(store_id: str) -> None:
    """ZONE 2: 문제 인식 & 빠른 진입"""
    st.markdown("### 🚨 문제 인식 & 빠른 진입")
    
    col1, col2, col3 = st.columns(3, gap="medium")
    
    with col1:
        st.markdown("""
        <div style="padding: 1.5rem; background: linear-gradient(135deg, #fff5f5 0%, #fee2e2 100%); border-radius: 12px; border-left: 4px solid #dc3545; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">🔍</div>
            <div style="font-weight: 600; color: #721c24; margin-bottom: 0.5rem; font-size: 1rem;">매출 하락 원인 찾기</div>
            <div style="font-size: 0.85rem; color: #856404; line-height: 1.4;">3분 안에 원인을 좁히고, 고칠 곳으로 바로 이동합니다.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("원클릭 진입", type="primary", use_container_width=True, key="zone2_sales_drop"):
            st.session_state["current_page"] = "매출 하락 원인 찾기"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div style="padding: 1.5rem; background: linear-gradient(135deg, #e7f3ff 0%, #d1ecf1 100%); border-radius: 12px; border-left: 4px solid #17a2b8; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">🏗</div>
            <div style="font-weight: 600; color: #0c5460; margin-bottom: 0.5rem; font-size: 1rem;">가게 구조 진단하기</div>
            <div style="font-size: 0.85rem; color: #0c5460; line-height: 1.4;">4개 설계실 통합 진단 및 전략 실행.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("가게 설계 센터", type="primary", use_container_width=True, key="zone2_design_center"):
            st.session_state["current_page"] = "가게 설계 센터"
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
        
        if st.button("가게 설계 센터로", use_container_width=True, key="zone5_to_design_center"):
            st.session_state["current_page"] = "가게 설계 센터"
            st.rerun()
    
    except Exception:
        st.info("구조 스냅샷을 불러오는 중입니다.")
    
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
