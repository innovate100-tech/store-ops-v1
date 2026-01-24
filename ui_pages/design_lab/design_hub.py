"""
가게 전략 센터 (통합 허브)
- 상태 확인 -> 문제 진단 -> 전략 수립 -> 설계실 이동 흐름 통합
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

from src.ui_helpers import render_page_header
from src.utils.time_utils import current_year_kst, current_month_kst
from src.storage_supabase import (
    load_csv,
    get_fixed_costs,
    get_variable_cost_ratio,
)
from src.analytics import calculate_menu_cost
from src.auth import get_current_store_id
from src.design.baseline_loader import load_baseline_structure, get_baseline_structure

# 전략 보드 및 설계 센터 데이터 로더 임포트
from ui_pages.strategy.store_state import classify_store_state
from ui_pages.strategy.strategy_cards import build_strategy_cards
from ui_pages.strategy.roadmap import build_weekly_roadmap
from ui_pages.design_lab.design_center_data import get_design_center_summary, get_primary_concern
from ui_pages.routines.routine_state import get_routine_status, mark_weekly_check_done

bootstrap(page_title="가게 전략 센터")


def _check_menu_completion(store_id: str) -> dict:
    """메뉴 포트폴리오 설계 완성도"""
    menu_df = load_csv("menu_master.csv", default_columns=["메뉴명", "판매가"], store_id=store_id)
    count = len(menu_df) if not menu_df.empty else 0
    completion = 100.0 if count > 0 else 0.0
    return {
        "completion": completion,
        "status": "완료" if completion == 100 else "미시작",
        "indicator": f"메뉴 {count}개 등록",
        "page_key": "메뉴 등록",
    }


def _check_ingredient_completion(store_id: str) -> dict:
    """재료 구조 설계 완성도"""
    ing_df = load_csv("ingredient_master.csv", default_columns=["재료명", "단위", "단가"], store_id=store_id)
    count = len(ing_df) if not ing_df.empty else 0
    completion = 100.0 if count > 0 else 0.0
    return {
        "completion": completion,
        "status": "완료" if completion == 100 else "미시작",
        "indicator": f"재료 {count}개 등록",
        "page_key": "재료 등록",
    }


def _check_menu_profit_completion(store_id: str) -> dict:
    """메뉴 수익 설계 완성도"""
    menu_df = load_csv("menu_master.csv", default_columns=["메뉴명", "판매가"], store_id=store_id)
    recipe_df = load_csv("recipes.csv", default_columns=["메뉴명", "재료명", "사용량"], store_id=store_id)
    ing_df = load_csv("ingredient_master.csv", default_columns=["재료명", "단위", "단가"], store_id=store_id)
    
    can_calculate = False
    if not menu_df.empty and not recipe_df.empty and not ing_df.empty:
        try:
            cost_df = calculate_menu_cost(menu_df, recipe_df, ing_df)
            can_calculate = not cost_df.empty
        except Exception:
            pass
    
    completion = 100.0 if can_calculate else 0.0
    return {
        "completion": completion,
        "status": "완료" if completion == 100 else "미시작",
        "indicator": "원가율 계산 가능" if can_calculate else "원가율 계산 불가",
        "page_key": "메뉴 수익 구조 설계실",
    }


def _check_profit_structure_completion(store_id: str, year: int, month: int) -> dict:
    """수익 구조 설계 완성도"""
    fixed = get_fixed_costs(store_id, year, month) or 0.0
    var_ratio = get_variable_cost_ratio(store_id, year, month) or 0.0
    has_structure = (fixed is not None and fixed > 0) or (var_ratio is not None and var_ratio > 0)
    completion = 100.0 if has_structure else 0.0
    if has_structure:
        var_pct = (var_ratio * 100) if var_ratio is not None else 0.0
        indicator = f"고정비 {int(fixed):,}원, 변동비율 {var_pct:.1f}%"
    else:
        indicator = "수익 구조 미설정"
    return {
        "completion": completion,
        "status": "완료" if completion == 100 else "미시작",
        "indicator": indicator,
        "page_key": "수익 구조 설계실",
    }


def _calculate_overall_completion(completions: list) -> float:
    """전체 완성도 계산"""
    if not completions:
        return 0.0
    total = sum(c.get("completion", 0.0) for c in completions)
    return total / len(completions)


def _hub_card(title: str, completion: float, status: str, indicator: str, page_key: str, icon: str = "📊"):
    """세부 설계실 진입 카드 렌더링"""
    if completion == 100:
        border_color = "#10b981"  # 녹색
        status_emoji = "🟢"
    elif completion > 0:
        border_color = "#f59e0b"  # 노란색
        status_emoji = "🟡"
    else:
        border_color = "#ef4444"  # 빨간색
        status_emoji = "🔴"
    
    st.markdown(f"""
    <div style="padding: 1.2rem; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); 
                border-radius: 12px; border-left: 4px solid {border_color}; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.3); margin-bottom: 1rem;">
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.8rem;">
            <span style="font-size: 1.5rem;">{icon}</span>
            <h3 style="margin: 0; font-size: 1rem; font-weight: 600; color: #e5e7eb;">{title}</h3>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <div style="font-size: 1.1rem; font-weight: 700; color: #ffffff;">
                {status_emoji} {completion:.0f}%
            </div>
            <div style="font-size: 0.85rem; color: #94a3b8;">
                {status}
            </div>
        </div>
        <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 0.8rem;">
            {indicator}
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("설계실 입장", key=f"design_hub_go_{page_key}", use_container_width=True, type="primary"):
        st.session_state["current_page"] = page_key
        st.rerun()


def _render_store_state_badge(store_state: dict, scores: dict):
    """ZONE A: 상단 상태 배지"""
    state_code = store_state.get("code", "unknown")
    state_label = store_state.get("label", "상태 미확인")
    overall_score = scores.get("overall", 0)
    
    color_map = {
        "survival": "🔴",
        "recovery": "🟡",
        "restructure": "🟠",
        "growth": "🟢",
        "unknown": "⚪"
    }
    emoji = color_map.get(state_code, "⚪")
    
    st.markdown(f"""
    <div style="padding: 1.5rem; background: #1e293b; border-radius: 12px; border: 1px solid #334155; margin-bottom: 1.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 0.9rem; color: #94a3b8; margin-bottom: 0.3rem;">가게 현재 상태</div>
                <div style="font-size: 1.8rem; font-weight: 800; color: #ffffff;">{emoji} {state_label}</div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 0.9rem; color: #94a3b8; margin-bottom: 0.3rem;">종합 건강 점수</div>
                <div style="font-size: 2rem; font-weight: 800; color: #3b82f6;">{overall_score:.0f}<span style="font-size: 1.2rem;">점</span></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_diagnostic_cards(summary: dict):
    """ZONE A: 4대 설계 영역 진단 카드"""
    cols = st.columns(4)
    
    # 1) 메뉴 포트폴리오
    mp = summary["menu_portfolio"]
    status_emoji = "✅" if mp["status"] == "균형" else "⚠️" if mp["status"] == "주의" else "🔴"
    with cols[0]:
        st.metric("메뉴 포트폴리오", f"{mp['balance_score']}점", f"{status_emoji} {mp['status']}", delta_color="off")
    
    # 2) 메뉴 수익 구조
    mpr = summary["menu_profit"]
    status_emoji = "✅" if mpr["status"] == "안정" else "⚠️" if mpr["status"] == "주의" else "🔴"
    with cols[1]:
        st.metric("메뉴 수익 구조", f"{mpr['high_cost_rate_count']}개", f"{status_emoji} 고원가율", delta_color="inverse")
    
    # 3) 재료 구조
    ing = summary["ingredient_structure"]
    status_emoji = "✅" if ing["status"] == "안정" else "⚠️" if ing["status"] == "주의" else "🔴"
    with cols[2]:
        st.metric("재료 집중도", f"{ing['top3_concentration']:.1f}%", f"{status_emoji} TOP3", delta_color="inverse")
    
    # 4) 수익 구조
    rev = summary["revenue_structure"]
    status_emoji = "✅" if rev["status"] == "안정" else "⚠️" if rev["status"] == "주의" else "🔴"
    breakeven_ratio = (rev["estimated_sales"] / rev["breakeven"] * 100) if rev["breakeven"] > 0 else 0
    with cols[3]:
        st.metric("손익분기 달성", f"{breakeven_ratio:.0f}%", f"{status_emoji} 생존선", delta_color="off")


def _get_card_code_from_title(title: str) -> str:
    """제목에서 카드 코드 추출 (완료 체크용)"""
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
    """이번 주 완료된 전략 로드 (session_state)"""
    key = f"_completed_actions_{store_id}_{week_start.isoformat()}"
    return st.session_state.get(key, [])


def _save_completed_action(store_id: str, card_code: str):
    """전략 완료 저장"""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    key = f"_completed_actions_{store_id}_{week_start.isoformat()}"
    completed = st.session_state.get(key, [])
    if card_code not in completed:
        completed.append(card_code)
        st.session_state[key] = completed


def render_strategy_cards_section(cards: list, store_id: str):
    """전략 카드 TOP3 렌더링"""
    if not cards:
        st.info("전략 카드를 생성할 수 없습니다.")
        return
    
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    completed_actions = _load_completed_actions(store_id, week_start)
    
    from ui_pages.common.strategy_card_v4 import render_strategy_card_v4
    for card in cards:
        card_code = _get_card_code_from_title(card.get("title", ""))
        is_completed = card_code in completed_actions if card_code else False
        
        render_strategy_card_v4(card)
        
        if card_code:
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if is_completed:
                    st.success("✅ 완료됨")
                else:
                    if st.button("✅ 완료", key=f"complete_{card_code}"):
                        _save_completed_action(store_id, card_code)
                        st.rerun()
        st.divider()


def render_roadmap_section(roadmap: list):
    """이번 주 실행 로드맵 렌더링"""
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
        
        cta_label = cta.get("label", "실행하기")
        cta_page = cta.get("page", "")
        if cta_page:
            if st.button(cta_label, key=f"roadmap_{rank}_cta", use_container_width=True):
                st.session_state["current_page"] = cta_page
                params = cta.get("params", {})
                if params:
                    for k, v in params.items():
                        st.session_state[f"_strategy_param_{k}"] = v
                st.rerun()
        st.divider()


def render_design_hub():
    """가게 전략 센터 페이지 렌더링 (통합)"""
    render_page_header("가게 전략 센터", "🏗️")

    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return

    year = current_year_kst()
    month = current_month_kst()

    try:
        # 데이터 로드
        state_result = classify_store_state(store_id, year, month)
        store_state = state_result.get("state", {})
        scores = state_result.get("scores", {})
        
        cards_result = build_strategy_cards(store_id, year, month, state_payload=state_result, use_v4=True)
        strategy_cards = cards_result.get("cards", [])
        roadmap = build_weekly_roadmap(cards_result)
        
        summary = get_design_center_summary(store_id)
        concern_name, verdict_text, target_page = get_primary_concern(summary)

        # 상단 액션: 이번 주 구조 점검 완료
        routine_status = get_routine_status(store_id)
        if not routine_status["weekly_design_check_done"]:
            if st.button("✅ 이번 주 구조 점검 완료 처리", key="mark_weekly_check_done_hub", use_container_width=True):
                mark_weekly_check_done(store_id)
                st.success("이번 주 구조 점검 완료 처리되었습니다!")
                st.rerun()
        else:
            st.info("✅ 이번 주 점검 완료 (다음 주에 다시 점검하세요)")

        # ZONE A: 가게 상태 및 종합 진단
        st.markdown("### 🩺 가게 상태 및 종합 진단")
        _render_store_state_badge(store_state, scores)
        _render_diagnostic_cards(summary)
        
        st.info(f"💡 **전문가 판결**: {verdict_text}")
        st.markdown("---")

        # ZONE B: 이번 달 핵심 전략 및 로드맵
        st.markdown("### 📌 이번 달 핵심 전략 및 로드맵")
        col1, col2 = st.columns([1.5, 1])
        
        with col1:
            st.markdown("**핵심 전략 TOP 3**")
            render_strategy_cards_section(strategy_cards, store_id)
            
        with col2:
            st.markdown("**이번 주 실행 로드맵**")
            render_roadmap_section(roadmap)
            
        st.markdown("---")

        # ZONE C: 설계 기준안 (Baseline)
        st.markdown("### 📐 설계 기준안 (우리 매장 기본 설계도)")
        baseline = get_baseline_structure(store_id, year, month)
        if baseline is None:
            if st.button("🔄 현재 가게 구조 불러오기", key="design_hub_load_baseline", use_container_width=True, type="primary"):
                try:
                    baseline = load_baseline_structure(store_id, year, month)
                    st.success("기준 구조를 불러왔습니다. 이 구조를 바탕으로 시뮬레이션을 시작하세요.")
                    st.rerun()
                except Exception as e:
                    st.error(f"기준 구조 불러오기 실패: {e}")
            st.caption("실제 데이터를 분석하여 시뮬레이션의 기준이 되는 '현재 설계도'를 만듭니다.")
        else:
            sales_b = baseline.get("sales", {})
            cost_b = baseline.get("cost", {})
            profit_b = baseline.get("profit", {})
            b1, b2, b3 = st.columns(3)
            with b1:
                st.metric("기준 월매출", f"{int(sales_b.get('monthly_sales', 0) or sales_b.get('forecast_sales', 0)):,.0f}원")
            with b2:
                st.metric("기준 고정비", f"{int(cost_b.get('fixed_costs', 0)):,.0f}원")
            with b3:
                st.metric("기준 손익분기점", f"{int(profit_b.get('break_even_sales', 0)):,.0f}원")
            
            if st.button("🔄 기준 구조 갱신하기", key="design_hub_reload_baseline", use_container_width=True):
                load_baseline_structure(store_id, year, month)
                st.rerun()
        
        st.markdown("---")

        # ZONE D: 세부 설계실 이동 & 완성도
        st.markdown("### 🧠 세부 설계실 진입")
        st.caption("진단 결과를 바탕으로 문제가 되는 영역의 구조를 직접 설계하세요.")
        
        # 설계실 정보 구성
        completions = [
            {"name": "메뉴 포트폴리오 설계", "icon": "🍽️", **_check_menu_completion(store_id)},
            {"name": "메뉴 수익 설계", "icon": "💰", **_check_menu_profit_completion(store_id)},
            {"name": "재료 구조 설계", "icon": "🧺", **_check_ingredient_completion(store_id)},
            {"name": "수익 구조 설계실", "icon": "📊", **_check_profit_structure_completion(store_id, year, month)},
        ]
        
        cols = st.columns(2)
        for idx, comp in enumerate(completions):
            col = cols[idx % 2]
            with col:
                _hub_card(
                    comp["name"],
                    comp["completion"],
                    comp["status"],
                    comp["indicator"],
                    comp["page_key"],
                    comp["icon"],
                )

    except Exception as e:
        st.error(f"전략 센터를 불러오는 중 오류가 발생했습니다: {str(e)}")
        st.exception(e)

