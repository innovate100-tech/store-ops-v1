"""
홈 메인 렌더링 및 진입점
- render_home, _render_home_body
- get_coach_summary, get_month_status_summary
- get_today_one_action, get_today_one_action_with_day_context
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import streamlit as st

from src.ui_helpers import render_page_header, render_section_divider
from src.auth import get_current_store_id
from ui_pages.home.home_data import (
    load_home_kpis,
    get_monthly_close_stats,
    get_menu_count,
    get_close_count,
    check_actual_settlement_exists,
    detect_data_level,
    detect_owner_day_level,
)
from ui_pages.home.home_rules import (
    get_problems_top1,
    get_good_points_top1,
    get_problems_top3,
    get_good_points_top3,
)
from ui_pages.home.home_alerts import get_anomaly_signals_light, get_anomaly_signals
from ui_pages.home.home_lazy import get_monthly_memos, render_lazy_insights, get_store_financial_structure
from ui_pages.home.home_verdict import get_coach_verdict
from ui_pages.coach.coach_adapters import get_home_coach_verdict
from ui_pages.coach.coach_renderer import render_verdict_card
from ui_pages.routines.routine_state import get_routine_status
from ui_pages.home.home_v3_zones import (
    _render_zone0_today_instruction,
    _render_zone1_strategy_summary,
    _render_zone2_quick_actions,
    _render_zone3_status_board,
    _render_zone4_weekly_priorities,
    _render_zone5_design_snapshot,
)

logger = logging.getLogger(__name__)


def get_coach_summary(store_id: str, day_level: str | None = None) -> str:
    """코치 요약 문장 (DAY 단계 톤)."""
    try:
        problems = get_problems_top3(store_id)
        good_points = get_good_points_top3(store_id)
        signals = get_anomaly_signals(store_id)
        if day_level == "DAY1":
            return "아직은 데이터를 쌓는 중입니다. 3일만 지나면 가게 흐름이 보이기 시작합니다."
        problem_count = len([p for p in problems if "데이터를 불러올 수 없습니다" not in p.get("text", "") and "아직 분석할 데이터가 충분하지 않습니다" not in p.get("text", "")])
        signal_count = len(signals)
        if day_level == "DAY3":
            has_good_sales = any("매출" in g.get("text", "") and ("증가" in g.get("text", "") or "최고" in g.get("text", "")) for g in good_points)
            has_good_close = any("마감" in g.get("text", "") for g in good_points)
            if has_good_sales and has_good_close:
                return "이번 달은 구조가 안정적이고, 운영 리듬도 잘 유지되고 있습니다."
            elif has_good_sales:
                return "이번 달은 매출 흐름이 양호하고, 운영이 안정적으로 진행되고 있습니다."
            elif problem_count == 0:
                return "이번 달은 전반적으로 안정적인 상태를 유지하고 있습니다."
            return "이번 달 가게 상태를 점검 중입니다."
        has_sales_decline = any("매출" in p.get("text", "") and ("감소" in p.get("text", "") or "떨어" in p.get("text", "")) for p in problems)
        has_close_gap = any("마감" in p.get("text", "") and ("공백" in p.get("text", "") or "누락" in p.get("text", "") or "없는 날" in p.get("text", "")) for p in problems)
        has_good_sales = any("매출" in g.get("text", "") and ("증가" in g.get("text", "") or "최고" in g.get("text", "")) for g in good_points)
        has_good_close = any("마감" in g.get("text", "") for g in good_points)
        if has_sales_decline and signal_count > 0:
            return "최근 매출이 떨어지고 있어, 원인 점검이 필요한 상태입니다."
        if has_sales_decline:
            return "이번 달은 매출 흐름이 불안정하여 관리가 필요합니다."
        if has_close_gap:
            return "마감 데이터가 끊겨 있어, 가게 상태 파악이 어려운 상황입니다."
        if problem_count > 0 and signal_count > 0:
            return "이번 달은 변동성이 증가하고 있어, 원인 추적이 필요한 상태입니다."
        if has_good_sales and has_good_close:
            return "이번 달은 구조가 안정적이고, 운영 리듬도 잘 유지되고 있습니다."
        if has_good_sales:
            return "이번 달은 매출 흐름이 양호하고, 운영이 안정적으로 진행되고 있습니다."
        if problem_count == 0 and signal_count == 0:
            return "이번 달은 전반적으로 안정적인 상태를 유지하고 있습니다."
        return "이번 달 가게 상태를 점검 중입니다."
    except Exception:
        return "이번 달 가게 상태를 확인 중입니다."


def get_month_status_summary(store_id: str, year: int, month: int, day_level: str | None = None) -> str:
    """이번 달 가게 상태 한 줄 (DAY prefix)."""
    try:
        problems = get_problems_top3(store_id)
        signals = get_anomaly_signals(store_id)
        has_settlement = check_actual_settlement_exists(store_id, year, month)
        problem_count = len([p for p in problems if "데이터를 불러올 수 없습니다" not in p.get("text", "") and "아직 분석할 데이터가 충분하지 않습니다" not in p.get("text", "")])
        signal_count = len(signals)
        from src.storage_supabase import load_monthly_sales_total
        monthly_sales = 0
        try:
            monthly_sales = load_monthly_sales_total(store_id, year, month)
        except Exception:
            pass
        if problem_count == 0 and signal_count == 0 and has_settlement:
            status_text = "'구조 안정 + 운영 리듬 양호' 상태입니다." if monthly_sales > 0 else "'데이터 수집 중' 상태입니다."
        elif problem_count > 0 or signal_count > 0:
            status_text = "'변동성 증가, 원인 추적 필요' 상태입니다." if has_settlement else "'관리 필요, 데이터 보완 필요' 상태입니다."
        elif has_settlement:
            status_text = "'매출은 유지, 이익은 관리 필요' 상태입니다."
        else:
            status_text = "'데이터 수집 중' 상태입니다."
        if day_level == "DAY1":
            return f"이번 달은 아직 구조를 만드는 중입니다. ({status_text})"
        if day_level == "DAY3":
            return f"이번 달 가게 상태가 정리되기 시작했습니다. ({status_text})"
        if day_level == "DAY7":
            return f"이번 달 가게 상태 요약입니다. ({status_text})"
        return f"이번 달은 {status_text}"
    except Exception:
        return "이번 달 상태를 확인 중입니다."


def get_today_one_action(store_id: str, level: int) -> dict:
    """오늘 하나만 추천 (룰 기반)."""
    fallback = {"title": "오늘 마감부터 시작", "reason": "데이터가 없어서 분석이 불가능합니다. 오늘 마감 1회만 하면 홈이 채워집니다.", "button_label": "📋 점장 마감 하러가기", "target_page": "점장 마감"}
    try:
        kst = ZoneInfo("Asia/Seoul")
        now = datetime.now(kst)
        cy, cm = now.year, now.month
        close_count = get_close_count(store_id)
        if close_count < 3:
            return {"title": "점장마감 3회 달성하기", "reason": f"현재 {close_count}회 완료. 3번만 하면 홈이 자동으로 흐름을 읽기 시작합니다.", "button_label": "📋 점장 마감 하러가기", "target_page": "점장 마감"}
        if level == 0:
            return fallback
        if level == 1:
            return {"title": "이번 주는 마감 루틴 만들기", "reason": "매출은 들어오고 있습니다. 마감이 쌓이면 판매/원가/발주까지 자동으로 연결됩니다.", "button_label": "📋 점장 마감 하러가기", "target_page": "점장 마감"}
        if level == 2:
            memos = get_monthly_memos(store_id, cy, cm, limit=1)
            if not memos:
                return {"title": "마감에 특이사항 1줄 남기기", "reason": "숫자 변화의 원인을 기억하면 다음 달 전략이 쉬워집니다.", "button_label": "📋 점장 마감 하러가기", "target_page": "점장 마감"}
            problems = get_problems_top3(store_id)
            has_sales = any("매출" in p.get("text", "") and ("감소" in p.get("text", "") or "떨어" in p.get("text", "")) for p in problems)
            if has_sales:
                return {"title": "판매 흐름 점검", "reason": "최근 매출이 흔들리고 있어, 오늘은 판매 흐름을 3분만 점검해보세요.", "button_label": "📦 판매 관리 보러가기", "target_page": "매출 관리"}
            return {"title": "판매 흐름 점검", "reason": "판매 데이터가 쌓였습니다. 메뉴별 흐름을 보고 오늘 밀 메뉴를 정하세요.", "button_label": "📦 판매 관리 보러가기", "target_page": "매출 관리"}
        if level == 3:
            if not check_actual_settlement_exists(store_id, cy, cm):
                return {"title": "이번 달 성적표 만들기", "reason": "정산이 있어야 이익/구조판이 자동으로 작동합니다.", "button_label": "🧾 실제정산 하러가기", "target_page": "실제정산"}
            return {"title": "숫자 구조 복습", "reason": "매출이 오르면 얼마가 남는지 알고 있으면 의사결정이 빨라집니다. 오늘은 10초만 복습해보세요.", "button_label": "💳 목표 비용구조 보기", "target_page": "목표 비용구조"}
        return fallback
    except Exception:
        return fallback


def get_today_one_action_with_day_context(store_id: str, level: int, day_level: str | None = None) -> dict:
    """오늘 하나만 추천 (DAY 톤)."""
    action = get_today_one_action(store_id, level)
    if day_level == "DAY1":
        action["title"] = "오늘도 마감 습관 만들기"
        action["reason"] = "기록을 쌓는 습관이 생기면, 3일 후부터 가게 흐름이 보이기 시작합니다."
        action["button_label"] = "📋 점장 마감 하러가기"
        action["target_page"] = "점장 마감"
    elif day_level == "DAY3":
        if "마감" in action.get("title", "") or "마감" in action.get("button_label", ""):
            action["reason"] = "마감을 꾸준히 하면 패턴이 보이기 시작합니다. 오늘도 기록을 쌓아보세요."
        elif "판매" in action.get("title", "") or "판매" in action.get("button_label", ""):
            action["reason"] = "이제 판매 흐름을 보면 패턴이 보이기 시작합니다. 메뉴별 흐름을 확인해보세요."
        elif "메모" in action.get("title", ""):
            action["reason"] = "특이사항을 기록하면 나중에 패턴을 찾을 때 도움이 됩니다."
    elif day_level == "DAY7":
        if "성적표" in action.get("title", "") or "실제정산" in action.get("button_label", ""):
            action["reason"] = "이번 달 성적표를 만들면 가게 구조가 완성되고, 무엇을 고칠지 결정할 수 있습니다."
        elif "숫자 구조" in action.get("title", "") or "비용구조" in action.get("button_label", ""):
            action["reason"] = "가게 구조를 이해하면 매출이 오를 때 얼마가 남는지 바로 알 수 있습니다."
        elif "판매" in action.get("title", "") or "문제" in action.get("reason", ""):
            action["reason"] = "문제를 발견했다면 지금 고치면 다음 달이 달라집니다."
    return action


def _render_home_body(store_id: str) -> None:
    """통합 홈 렌더링."""
    load_start = time.time()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다. 로그인 상태를 확인해주세요.")
        return
    kst = ZoneInfo("Asia/Seoul")
    now = datetime.now(kst)
    year, month = now.year, now.month
    
    # 새로고침 버튼 (캐시 무효화 강화)
    render_page_header("사장 계기판", "🏠")
    col_refresh, _ = st.columns([1, 5])
    with col_refresh:
        if st.button("🔄 새로고침", key="home_btn_refresh", use_container_width=True):
            try:
                # 모든 캐시 강제 클리어
                st.cache_data.clear()
                st.cache_resource.clear()
                # 세션 상태도 일부 클리어
                keys_to_remove = [
                    "_home_problems_expanded", "_home_good_points_expanded", 
                    "_home_anomaly_expanded", "_home_problems_top3", 
                    "_home_good_points_top3"
                ]
                for key in keys_to_remove:
                    if key in st.session_state:
                        del st.session_state[key]
                # 강제 리로드를 위한 타임스탬프 추가
                st.session_state["_home_last_refresh"] = time.time()
                logger.info("홈 캐시 무효화 완료 (강화)")
                st.rerun()
            except Exception as e:
                logger.error(f"캐시 무효화 실패: {e}")
    
    data_level = detect_data_level(store_id)
    st.session_state["home_data_level"] = data_level
    day_level = detect_owner_day_level(store_id)
    kpis = load_home_kpis(store_id, year, month)
    monthly_sales = kpis["monthly_sales"]
    yesterday_sales = kpis["yesterday_sales"]
    close_stats = kpis["close_stats"]
    revenue_per_visit = kpis["revenue_per_visit"]
    monthly_profit = kpis["monthly_profit"]
    target_sales = kpis["target_sales"]
    target_ratio = kpis["target_ratio"]
    unofficial_days = kpis.get("unofficial_days", 0)  # 미마감 날짜 개수
    closed_days, total_days, close_rate, streak_days = close_stats
    
    load_time = time.time() - load_start
    logger.info(f"[홈 로드 시간] {load_time:.3f}초 (store_id={store_id})")

    # ===== HOME v3 구조 (운영 지시 홈) =====
    
    # ZONE 0: 오늘의 운영 지시 (최상단, 가장 중요)
    _render_zone0_today_instruction(store_id, year, month)
    
    # ZONE 1: 이번 달 가게 전략 요약
    _render_zone1_strategy_summary(store_id, year, month)
    
    # ZONE 2: 문제 인식 & 빠른 진입
    _render_zone2_quick_actions(store_id)
    
    # ZONE 3: 오늘 상태판 (숫자, 크기 축소)
    _render_zone3_status_board(store_id, year, month, kpis, unofficial_days)
    
    # ZONE 4: 이번 주 우선순위 TOP3
    _render_zone4_weekly_priorities(store_id, year, month)
    
    # ZONE 5: 가게 구조 스냅샷 (보조)
    _render_zone5_design_snapshot(store_id, year, month)

    # ===== HOME v3: 오늘 하나만 추천은 ZONE 0에 통합됨 =====

    # ===== Lazy 영역 (expander, 모던 스타일) =====
    with st.expander("📈 미니 차트", expanded=False):
        st.markdown("""<div style="padding: 1.5rem; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 10px; text-align: center; border: 2px dashed #dee2e6; box-shadow: 0 2px 4px rgba(0,0,0,0.05);"><p style="color: #6c757d; margin: 0; font-size: 0.9rem;">차트를 표시하려면 마감 데이터가 필요합니다.</p></div>""", unsafe_allow_html=True)
        if st.button("📋 점장 마감으로 이동", use_container_width=True, key="home_btn_chart_close"):
            st.session_state["current_page"] = "점장 마감"
            st.rerun()

    # 이번 달 가게 상태 한 줄
    try:
        s = get_month_status_summary(store_id, year, month, day_level)
        st.markdown(f"""
            <div style="padding: 1rem 1.2rem; background: linear-gradient(135deg, #e7f3ff 0%, #d1ecf1 100%); border-radius: 10px; border-left: 4px solid #17a2b8; margin-top: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <div style="font-size: 0.85rem; color: #0c5460; font-weight: 600; margin-bottom: 0.3rem;">📌 이번 달 가게 상태 한 줄</div>
                <div style="font-size: 0.95rem; color: #495057; line-height: 1.5;">{s}</div>
            </div>
            """, unsafe_allow_html=True)
    except Exception:
        pass
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    render_lazy_insights(store_id, year, month)


def _kpi_card_modern(label: str, value: str, subtitle: str | None = None, gradient: str | None = None) -> None:
    """
    모던한 KPI 카드 스타일 (세련된 디자인)
    - 높이: 110px 고정
    - 패딩: 1.2rem
    - 폰트: label 0.8rem, value 1.4rem, subtitle 0.75rem
    - 그라데이션 배경 또는 흰색 배경
    - 그림자 효과
    - 부드러운 호버 효과
    """
    sub_html = f'<div style="font-size: 0.75rem; color: rgba(255,255,255,0.85); margin-top: 0.3rem; font-weight: 400;">{subtitle}</div>' if subtitle else ""
    
    if gradient:
        # 그라데이션 카드 (색상 있는 지표)
        st.markdown(f"""
        <div style="
            padding: 1.2rem;
            background: {gradient};
            border-radius: 12px;
            text-align: center;
            height: 110px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1), 0 2px 4px rgba(0,0,0,0.06);
            transition: transform 0.2s, box-shadow 0.2s;
            color: white;
        ">
            <div style="font-size: 0.8rem; color: rgba(255,255,255,0.9); margin-bottom: 0.4rem; font-weight: 500; letter-spacing: 0.3px;">{label}</div>
            <div style="font-size: 1.4rem; font-weight: 700; color: white; line-height: 1.2; letter-spacing: -0.5px;">{value}</div>
            {sub_html}
        </div>
        """, unsafe_allow_html=True)
    else:
        # 흰색 카드 (기본 지표)
        st.markdown(f"""
        <div style="
            padding: 1.2rem;
            background: #ffffff;
            border: 1px solid #e9ecef;
            border-radius: 12px;
            text-align: center;
            height: 110px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.03);
            transition: transform 0.2s, box-shadow 0.2s;
        ">
            <div style="font-size: 0.8rem; color: #6c757d; margin-bottom: 0.4rem; font-weight: 500; letter-spacing: 0.3px;">{label}</div>
            <div style="font-size: 1.4rem; font-weight: 700; color: #212529; line-height: 1.2; letter-spacing: -0.5px;">{value}</div>
            {sub_html}
        </div>
        """, unsafe_allow_html=True)


def _kpi_card_compact(label: str, value: str, subtitle: str | None = None, value_color: str | None = None) -> None:
    """
    압축된 KPI 카드 스타일 (한눈형 계기판용) - 레거시 호환용
    """
    _kpi_card_modern(label, value, subtitle, None)


def _kpi_card_unified(label: str, value: str, subtitle: str | None = None) -> None:
    """
    통일된 KPI 카드 스타일 (중립 톤, 일관된 레이아웃) - 레거시 호환용
    """
    _kpi_card_compact(label, value, subtitle)


def _kpi_card(label: str, value: str, gradient: str | None) -> None:
    """레거시 함수 (하위 호환용)"""
    _kpi_card_compact(label, value, None)


def _render_status_strip(store_id: str, monthly_sales: int, target_sales: int, target_ratio: float | None, close_rate: float, closed_days: int, total_days: int) -> None:
    """
    상태 해석 스트립 (KPI 바로 아래, 1줄 요약, 모던 스타일)
    """
    try:
        from src.storage_supabase import get_fixed_costs, calculate_break_even_sales
        from src.auth import get_supabase_client
        kst = ZoneInfo("Asia/Seoul")
        now = datetime.now(kst)
        year, month = now.year, now.month
        
        status_parts = []
        
        # 목표 대비 상태
        if target_ratio is not None and target_sales > 0:
            if target_ratio >= 100:
                status_parts.append(f"목표 대비 {target_ratio}% 달성")
            else:
                remaining = target_sales - monthly_sales
                if remaining > 0:
                    status_parts.append(f"목표 대비 {target_ratio}%, 약 {remaining:,}원 남음")
        
        # 손익분기점 정보
        try:
            break_even = calculate_break_even_sales(store_id, year, month)
            if break_even > 0 and monthly_sales > 0:
                if monthly_sales < break_even:
                    gap = break_even - monthly_sales
                    status_parts.append(f"손익분기점까지 약 {gap:,}원 남음")
                else:
                    status_parts.append("손익분기점 달성")
        except Exception:
            pass
        
        # 마감률 상태
        if closed_days > 0:
            if close_rate >= 0.9:
                status_parts.append("마감률 양호")
            elif close_rate < 0.7:
                missing = total_days - closed_days
                status_parts.append(f"마감 누락 {missing}일")
        
        # 최근 7일 평균 매출 비교 (SSOT: best_available 사용)
        try:
            from src.storage_supabase import load_best_available_daily_sales
            from datetime import timedelta
            today = now.date()
            seven_ago = today - timedelta(days=7)
            start_m = f"{year}-{month:02d}-01"
            end_m = f"{year + 1}-01-01" if month == 12 else f"{year}-{month + 1:02d}-01"
            
            # best_available 기반으로 조회
            best_df = load_best_available_daily_sales(store_id=store_id, start_date=seven_ago.isoformat(), end_date=today.isoformat())
            month_best_df = load_best_available_daily_sales(store_id=store_id, start_date=start_m, end_date=end_m)
            
            if not best_df.empty and not month_best_df.empty:
                recent_avg = best_df['total_sales'].mean() if 'total_sales' in best_df.columns else 0
                month_avg = month_best_df['total_sales'].mean() if 'total_sales' in month_best_df.columns else 0
                if month_avg > 0:
                    ratio = recent_avg / month_avg
                    if ratio < 0.9:
                        status_parts.append("최근 7일 평균이 이번 달 평균보다 낮음")
        except Exception:
            pass
        
        if status_parts:
            status_text = " • ".join(status_parts)
            st.markdown(f"""
            <div style="padding: 0.8rem 1.2rem; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 10px; border-left: 4px solid #17a2b8; margin-top: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <div style="font-size: 0.9rem; color: #495057; line-height: 1.5; font-weight: 500;">{status_text}</div>
            </div>
            """, unsafe_allow_html=True)
    except Exception:
        pass


def _render_coach_missions(store_id: str, year: int, month: int, kpis: dict) -> None:
    menu_count = get_menu_count(store_id)
    close_count = get_close_count(store_id)
    has_settlement = check_actual_settlement_exists(store_id, year, month)
    m1, m2, m3 = menu_count >= 3, close_count >= 3, has_settlement
    done = sum([m1, m2, m3])
    pct = int((done / 3.0) * 100)
    st.markdown("### 🚀 시작 미션 3개")
    st.progress(pct / 100.0)
    st.caption(f"온보딩 진행률 {pct}%")
    if m1:
        st.info("✅ 메뉴 기반이 생겨서 판매/원가 분석이 정확해졌습니다.")
    if m2:
        st.info("✅ 점장마감 데이터가 쌓여서 홈이 자동으로 흐름을 읽기 시작합니다.")
    if m3:
        st.info("✅ 이번 달 성적표가 완성되어 손익 구조가 잠겼습니다.")
    missions = [
        ("메뉴 3개 등록하기", f"({menu_count}/3)", m1, "메뉴 등록", "m1", "메뉴 등록"),
        ("점장마감 3회 하기", f"({close_count}/3)", m2, "점장 마감", "m2", "점장 마감"),
        ("이번 달 성적표 1회 만들기", "", m3, "실제정산", "m3", "실제정산"),
    ]
    for name, sub, ok, page, key, btn_label in missions:
        status = "✅" if ok else (f"⬜ {sub}" if sub else "⬜")
        st.markdown(f"**{name}** {status}")
        if not ok and st.button(btn_label, key=f"mission_{key}", use_container_width=True):
            st.session_state["current_page"] = page
            st.rerun()
    if not m2:
        st.info("점장마감을 3회 하면 홈이 자동으로 흐름을 읽기 시작합니다.")
        if st.button("점장 마감 하러 가기", type="primary", use_container_width=True, key="mission_next"):
            st.session_state["current_page"] = "점장 마감"
            st.rerun()
    elif not m1:
        st.info("메뉴가 있어야 판매/원가/분석이 의미가 생깁니다.")
        if st.button("메뉴 등록 하러 가기", type="primary", use_container_width=True, key="mission_next"):
            st.session_state["current_page"] = "메뉴 등록"
            st.rerun()
    elif not m3:
        st.info("이번 달 성적표가 완성되면 손익 구조가 잠깁니다.")
        if st.button("실제정산 하러 가기", type="primary", use_container_width=True, key="mission_next"):
            st.session_state["current_page"] = "실제정산"
            st.rerun()
    else:
        st.success("🎉 기본 세팅이 끝났습니다. 이제 홈이 매일 가게를 읽어드립니다.")


def _render_problems_good_points(store_id: str) -> None:
    """문제/잘한 점 TOP1 표시 + 자세히 보기 버튼 (TOP3 lazy load)."""
    st.markdown("### 🔴 문제 / 🟢 잘한 점")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🔴 문제")
        try:
            problems = get_problems_top1(store_id)
            if not problems:
                st.info("아직 분석할 데이터가 충분하지 않습니다.")
                if st.button("📋 점장 마감 시작하기", key="home_btn_pf", use_container_width=True):
                    st.session_state["current_page"] = "점장 마감"
                    st.rerun()
            else:
                p = problems[0]
                t = p.get("text", "")
                g = ""
                if "매출" in t and ("감소" in t or "떨어" in t):
                    g = "<div style='color:#856404;font-size:0.8rem; margin-top:0.4rem;'>이 문제는 보통 요일/메뉴/객단가 흐름에서 원인이 보입니다.</div>"
                elif "마감" in t and ("공백" in t or "누락" in t or "없는 날" in t):
                    g = "<div style='color:#856404;font-size:0.8rem; margin-top:0.4rem;'>데이터가 끊기면 가게 상태도 같이 안 보입니다.</div>"
                elif "메뉴" in t and "50%" in t:
                    g = "<div style='color:#856404;font-size:0.8rem; margin-top:0.4rem;'>메뉴 쏠림은 판매 관리에서 메뉴별 흐름을 확인하면 보입니다.</div>"
                st.markdown(f"""<div style="padding: 1rem; background: #fff5f5; border: 1px solid #fecaca; border-left: 4px solid #dc3545; border-radius: 8px; margin-bottom: 0.5rem;"><div style="font-weight: 600; color: #721c24; font-size: 0.95rem;">{t}</div>{g}</div>""", unsafe_allow_html=True)
                if st.button("보러가기", key="home_btn_p_1", use_container_width=True):
                    st.session_state["current_page"] = p.get("target_page", "점장 마감")
                    st.rerun()
                if st.button("📋 자세히 보기 (TOP3)", key="home_btn_p_detail", use_container_width=True):
                    st.session_state["_home_problems_expanded"] = True
                    st.rerun()
            if st.session_state.get("_home_problems_expanded", False):
                with st.expander("🔴 문제 TOP3 전체", expanded=True):
                    if "_home_problems_top3" not in st.session_state:
                        st.session_state["_home_problems_top3"] = get_problems_top3(store_id)
                    problems_full = st.session_state["_home_problems_top3"]
                    for i, p in enumerate(problems_full, 1):
                        t = p.get("text", "")
                        st.markdown(f"""<div style="padding: 0.8rem; background: #fff5f5; border: 1px solid #fecaca; border-left: 4px solid #dc3545; border-radius: 8px; margin-bottom: 0.5rem;"><div style="font-weight: 600; color: #721c24; font-size: 0.9rem;">{i}. {t}</div></div>""", unsafe_allow_html=True)
                        if st.button("보러가기", key=f"home_btn_p_full_{i}", use_container_width=True):
                            st.session_state["current_page"] = p.get("target_page", "점장 마감")
                            st.rerun()
        except Exception:
            st.error("문제 분석 중 오류가 발생했습니다.")
    with col2:
        st.markdown("#### 🟢 잘한 점")
        try:
            good = get_good_points_top1(store_id)
            if not good:
                st.info("데이터가 쌓이면 자동 분석됩니다.")
                if st.button("📋 점장 마감 시작하기", key="home_btn_gf", use_container_width=True):
                    st.session_state["current_page"] = "점장 마감"
                    st.rerun()
            else:
                g = good[0]
                st.markdown(f"""<div style="padding: 1rem; background: #f0fdf4; border: 1px solid #bbf7d0; border-left: 4px solid #28a745; border-radius: 8px; margin-bottom: 0.5rem;"><div style="font-weight: 600; color: #155724; font-size: 0.95rem;">{g.get('text','')}</div></div>""", unsafe_allow_html=True)
                if st.button("보러가기", key="home_btn_g_1", use_container_width=True):
                    st.session_state["current_page"] = g.get("target_page", "점장 마감")
                    st.rerun()
                if st.button("📋 자세히 보기 (TOP3)", key="home_btn_g_detail", use_container_width=True):
                    st.session_state["_home_good_points_expanded"] = True
                    st.rerun()
            if st.session_state.get("_home_good_points_expanded", False):
                with st.expander("🟢 잘한 점 TOP3 전체", expanded=True):
                    if "_home_good_points_top3" not in st.session_state:
                        st.session_state["_home_good_points_top3"] = get_good_points_top3(store_id)
                    good_full = st.session_state["_home_good_points_top3"]
                    for i, g in enumerate(good_full, 1):
                        st.markdown(f"""<div style="padding: 0.8rem; background: #f0fdf4; border: 1px solid #bbf7d0; border-left: 4px solid #28a745; border-radius: 8px; margin-bottom: 0.5rem;"><div style="font-weight: 600; color: #155724; font-size: 0.9rem;">{i}. {g.get('text','')}</div></div>""", unsafe_allow_html=True)
                        if st.button("보러가기", key=f"home_btn_g_full_{i}", use_container_width=True):
                            st.session_state["current_page"] = g.get("target_page", "점장 마감")
                            st.rerun()
        except Exception:
            st.error("잘한 점 분석 중 오류가 발생했습니다.")


def _render_compressed_alerts(store_id: str) -> None:
    """
    압축된 알림 영역 (이상징후/문제/잘한점, 기본 1개만, 3줄 규격)
    - 결론 한 줄 (굵게 + 숫자)
    - 왜 중요한지 한 줄
    - 다음 행동 버튼 1개
    """
    try:
        # 우선순위: 이상징후 > 문제 > 잘한점
        signals = get_anomaly_signals_light(store_id)
        problems = get_problems_top1(store_id)
        good_points = get_good_points_top1(store_id)
        
        # 이상징후 우선 표시
        if signals and len(signals) > 0:
            s = signals[0]
            text = s.get("text", "")
            icon = s.get("icon", "⚠️")
            target_page = s.get("target_page", "점장 마감")
            
            # 숫자 추출 (3줄 규격용)
            import re
            numbers = re.findall(r'\d+', text)
            number_text = f" {numbers[0]}" if numbers else ""
            
            # 중요성 문구
            importance = ""
            if "매출" in text and ("감소" in text or "누락" in text):
                importance = "누락되면 월 성과 분석이 왜곡됩니다."
            elif "마감" in text and ("누락" in text or "없습니다" in text):
                importance = "데이터가 끊기면 가게 상태도 같이 안 보입니다."
            elif "판매량" in text or "판매" in text:
                importance = "판매 흐름 변화는 메뉴별 데이터를 보면 확인됩니다."
            else:
                importance = "조기 발견하면 대응이 빠릅니다."
            
            # 버튼 라벨
            if "마감" in target_page:
                button_label = "점장마감 하러가기"
            elif "매출" in target_page or "판매" in target_page:
                button_label = "매출 관리 보러가기"
            else:
                button_label = "보러가기"
            
            _render_alert_card_3line(
                icon=icon,
                conclusion=f"{text}{number_text}",
                importance=importance,
                button_label=button_label,
                target_page=target_page,
                card_type="warning"
            )
            return
        
        # 문제 표시
        if problems and len(problems) > 0:
            p = problems[0]
            text = p.get("text", "")
            target_page = p.get("target_page", "점장 마감")
            
            # 숫자 추출
            import re
            numbers = re.findall(r'\d+', text)
            number_text = f" {numbers[0]}" if numbers else ""
            
            # 중요성 문구
            importance = ""
            if "매출" in text and ("감소" in text or "떨어" in text):
                importance = "요일/메뉴/유입 흐름에서 원인이 보입니다."
            elif "마감" in text and ("공백" in text or "누락" in text or "없는 날" in text):
                importance = "데이터가 끊기면 가게 상태도 같이 안 보입니다."
            elif "메뉴" in text and "50%" in text:
                importance = "메뉴 쏠림은 판매 관리에서 메뉴별 흐름을 확인하면 보입니다."
            else:
                importance = "지금 고치면 다음 달이 달라집니다."
            
            # 버튼 라벨
            if "마감" in target_page:
                button_label = "점장마감 하러가기"
            elif "매출" in target_page:
                button_label = "매출 관리 보러가기"
            elif "판매" in target_page:
                button_label = "판매 관리 보러가기"
            else:
                button_label = "보러가기"
            
            _render_alert_card_3line(
                icon="🔴",
                conclusion=f"{text}{number_text}",
                importance=importance,
                button_label=button_label,
                target_page=target_page,
                card_type="problem"
            )
            return
        
        # 잘한 점 표시
        if good_points and len(good_points) > 0:
            g = good_points[0]
            text = g.get("text", "")
            target_page = g.get("target_page", "점장 마감")
            
            # 숫자 추출
            import re
            numbers = re.findall(r'\d+', text)
            number_text = f" {numbers[0]}" if numbers else ""
            
            # 중요성 문구
            importance = "이런 패턴을 유지하면 안정적인 운영이 가능합니다."
            
            # 버튼 라벨
            if "마감" in target_page:
                button_label = "점장마감 보러가기"
            elif "매출" in target_page:
                button_label = "매출 관리 보러가기"
            elif "판매" in target_page:
                button_label = "판매 관리 보러가기"
            else:
                button_label = "보러가기"
            
            _render_alert_card_3line(
                icon="🟢",
                conclusion=f"{text}{number_text}",
                importance=importance,
                button_label=button_label,
                target_page=target_page,
                card_type="good"
            )
            return
        
        # 아무것도 없으면 빈 상태
        st.info("현재 특별한 알림이 없습니다. 정상 범위로 보입니다.")
        
    except Exception:
        st.error("알림 분석 중 오류가 발생했습니다.")


def _render_alert_card_3line(icon: str, conclusion: str, importance: str, button_label: str, target_page: str, card_type: str) -> None:
    """
    3줄 규격 알림 카드 (모던 스타일)
    - 결론 한 줄 (굵게 + 숫자)
    - 왜 중요한지 한 줄
    - 다음 행동 버튼 1개
    """
    if card_type == "warning":
        bg_gradient = "linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%)"
        border_color = "#ffc107"
        text_color = "#92400e"
        icon_bg = "#fef3c7"
    elif card_type == "problem":
        bg_gradient = "linear-gradient(135deg, #fff5f5 0%, #fee2e2 100%)"
        border_color = "#dc3545"
        text_color = "#721c24"
        icon_bg = "#fee2e2"
    else:  # good
        bg_gradient = "linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)"
        border_color = "#28a745"
        text_color = "#155724"
        icon_bg = "#dcfce7"
    
    st.markdown(f"""
    <div style="padding: 1rem 1.2rem; background: {bg_gradient}; border: 1px solid {border_color}; border-left: 4px solid {border_color}; border-radius: 12px; margin-bottom: 0.8rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
        <div style="display: flex; align-items: flex-start; margin-bottom: 0.5rem;">
            <div style="font-size: 1.3rem; margin-right: 0.8rem; padding: 0.3rem; background: {icon_bg}; border-radius: 8px; display: flex; align-items: center; justify-content: center; min-width: 2.5rem; height: 2.5rem;">{icon}</div>
            <div style="flex: 1;">
                <div style="font-weight: 700; color: {text_color}; font-size: 1rem; line-height: 1.4; margin-bottom: 0.4rem; letter-spacing: -0.2px;">{conclusion}</div>
                <div style="color: {text_color}; font-size: 0.875rem; opacity: 0.9; line-height: 1.4; font-weight: 400;">{importance}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn1:
        if st.button(button_label, key=f"home_btn_alert_{card_type}", use_container_width=True):
            st.session_state["current_page"] = target_page
            st.rerun()
    with col_btn2:
        if st.button("📋 전체", key=f"home_btn_alert_expand_{card_type}", use_container_width=True):
            st.session_state[f"_home_{card_type}_expanded"] = True
            st.rerun()


def _render_anomaly_signals(store_id: str) -> None:
    """이상 징후 경량 버전 (1-2개) + 자세히 보기 버튼 (전체 3개 lazy load). - 레거시 호환용"""
    _render_compressed_alerts(store_id)


def render_home() -> None:
    """홈 진입점."""
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.error("로그인이 필요합니다.")
        return
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다. 로그인 상태를 확인해주세요.")
        return
    _render_home_body(store_id)


# ===== HOME v2 ZONE 렌더링 함수 =====

def _render_zone1_status_board(store_id: str, year: int, month: int, kpis: dict, unofficial_days: int) -> None:
    """ZONE 1: 오늘 상태판 (10초 판단)"""
    monthly_sales = kpis["monthly_sales"]
    yesterday_sales = kpis["yesterday_sales"]
    close_stats = kpis["close_stats"]
    revenue_per_visit = kpis["revenue_per_visit"]
    target_sales = kpis["target_sales"]
    target_ratio = kpis["target_ratio"]
    closed_days, total_days, close_rate, streak_days = close_stats
    
    # A) KPI 4개 카드 (best_available 기준)
    st.markdown("### 🟡 오늘 상태판")
    
    # 미마감 배지 표시
    if unofficial_days > 0:
        st.warning(f"⚠️ **미마감 데이터 포함 ({unofficial_days}일)**: 이번달 누적 매출에 마감되지 않은 날짜의 매출이 포함되어 있습니다.")
    
    # 전략 보드 진입 버튼
    col_strategy, _ = st.columns([1, 3])
    with col_strategy:
        if st.button("📌 이번 달 전략 보기", key="home_to_strategy_board", use_container_width=True):
            st.session_state["current_page"] = "전략 보드"
            st.rerun()
    
    # KPI 4개: 어제 매출, 이번 달 누적 매출, 이번 달 평균 일매출, 네이버방문자 또는 객단가
    k1, k2, k3, k4 = st.columns(4, gap="medium")
    with k1:
        _kpi_card_modern("어제 매출", f"{yesterday_sales:,}원" if yesterday_sales > 0 else "-", None, gradient="linear-gradient(135deg, #f093fb 0%, #f5576c 100%)")
    with k2:
        _kpi_card_modern("이번 달 누적 매출", f"{monthly_sales:,}원" if monthly_sales > 0 else "-", None, gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)")
    with k3:
        avg_daily = (monthly_sales / total_days) if total_days > 0 else 0
        avg_text = f"{int(avg_daily):,}원" if avg_daily > 0 else "-"
        _kpi_card_modern("이번 달 평균 일매출", avg_text, None, gradient="linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)")
    with k4:
        # 네이버방문자 또는 객단가 중 택1 (객단가 우선)
        if revenue_per_visit and revenue_per_visit > 0:
            v = f"{revenue_per_visit:,}원"
            _kpi_card_modern("객단가", v, "네이버방문자 기준", gradient="linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)")
        else:
            # 네이버방문자 누적 조회
            try:
                from src.auth import get_supabase_client
                supabase = get_supabase_client()
                if supabase:
                    kst = ZoneInfo("Asia/Seoul")
                    now = datetime.now(kst)
                    start = f"{year}-{month:02d}-01"
                    end = f"{year + 1}-01-01" if month == 12 else f"{year}-{month + 1:02d}-01"
                    visitors_result = supabase.table("naver_visitors").select("visitors").eq("store_id", store_id).gte("date", start).lt("date", end).execute()
                    total_visitors = sum(int(r.get("visitors", 0) or 0) for r in (visitors_result.data or []))
                    v_text = f"{total_visitors:,}명" if total_visitors > 0 else "-"
                    _kpi_card_modern("네이버방문자", v_text, "이번 달 누적", gradient="linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)")
                else:
                    _kpi_card_modern("네이버방문자", "-", None, gradient="linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)")
            except Exception:
                _kpi_card_modern("네이버방문자", "-", None, gradient="linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)")
    
    # B) 상태 스트립 1줄
    missing_days = total_days - closed_days
    status_parts = []
    if closed_days > 0:
        pct = int(close_rate * 100)
        status_parts.append(f"마감률 {pct}%")
    if streak_days > 0:
        status_parts.append(f"연속 마감 {streak_days}일")
    if missing_days > 0:
        status_parts.append(f"미마감 {missing_days}일")
    
    if status_parts:
        status_text = " • ".join(status_parts)
        st.markdown(f"""
        <div style="padding: 0.8rem 1.2rem; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 10px; border-left: 4px solid #17a2b8; margin-top: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            <div style="font-size: 0.9rem; color: #495057; line-height: 1.5; font-weight: 500;">{status_text}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # C) 오늘 입력 바로가기 버튼
    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
    st.markdown("#### 오늘 입력 바로가기")
    col1, col2, col3 = st.columns(3, gap="medium")
    with col1:
        if st.button("📋 점장마감", type="primary", use_container_width=True, key="zone1_btn_close"):
            st.session_state["current_page"] = "점장 마감"
            st.rerun()
    with col2:
        if st.button("💰 매출·네이버방문자 보정", type="primary", use_container_width=True, key="zone1_btn_sales"):
            st.session_state["current_page"] = "매출 등록"
            st.rerun()
    with col3:
        if st.button("📦 판매량 보정", type="secondary", use_container_width=True, key="zone1_btn_volume"):
            st.session_state["current_page"] = "판매량 등록"
            st.rerun()
    
    # 매출 하락 원인 찾기 버튼 (상시 노출)
    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
    if st.button("📉 매출 하락 원인 찾기", type="primary", use_container_width=True, key="zone1_btn_sales_drop"):
        st.session_state["current_page"] = "매출 하락 원인 찾기"
        st.rerun()
    
    # 루틴 배지 추가 (ZONE 1 아래)
    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
    _render_routine_badges(store_id)
    
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)


def _render_zone2_coach_verdict(store_id: str, year: int, month: int, monthly_sales: int) -> None:
    """ZONE 2: 이번 달 코치 판결 (Verdict)"""
    st.markdown("### 🟢 이번 달 코치 판결")
    
    try:
        # CoachVerdict 표준 형식으로 변환
        verdict = get_home_coach_verdict(store_id, year, month)
        render_verdict_card(verdict, compact=False)
    except Exception as e:
        logger.error(f"코치 판결 렌더링 오류: {e}")
        st.info("코치 판결을 생성하는 중입니다. 데이터가 더 필요할 수 있습니다.")
    
    # monitoring 미션 자동 평가 (PHASE 10-7C)
    try:
        from src.storage_supabase import load_active_mission, set_mission_status, update_mission_evaluation, save_mission_result
        from src.strategy.strategy_monitor import evaluate_mission_effect
        from datetime import date
        
        # monitoring 상태 미션 찾기
        monitoring_mission = load_active_mission(store_id, date.today())
        if monitoring_mission and monitoring_mission.get("status") == "monitoring":
            # 평가 시도
            evaluation = evaluate_mission_effect(monitoring_mission, store_id)
            if evaluation and evaluation.get("result_type") != "data_insufficient":
                # 결과 저장
                result_type = evaluation.get("result_type")
                coach_comment = evaluation.get("coach_comment", "")
                baseline = evaluation.get("baseline", {})
                after = evaluation.get("after", {})
                delta = evaluation.get("delta", {})
                
                if update_mission_evaluation(monitoring_mission["id"], result_type, coach_comment):
                    save_mission_result(monitoring_mission["id"], baseline, after, delta)
    except Exception as e:
        logger.error(f"미션 평가 오류: {e}")
        # 에러 발생해도 계속 진행
    
    # 오늘의 전략 카드 추가
    try:
        from ui_pages.analysis.strategy_engine import pick_primary_strategy
        from ui_pages.common.today_strategy_card import render_today_strategy_card
        from datetime import date
        
        strategy = pick_primary_strategy(store_id, ref_date=date.today(), window_days=14)
        if strategy:
            render_today_strategy_card(strategy, location="home")
    except Exception as e:
        logger.error(f"오늘의 전략 카드 렌더링 오류: {e}")
        # 에러 발생해도 계속 진행
    
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)


def _render_zone3_action_radar(store_id: str) -> None:
    """ZONE 3: 문제 TOP3 (Action Radar)"""
    st.markdown("### 🔵 문제 TOP3 (Action Radar)")
    
    try:
        problems = get_problems_top3(store_id)
        if not problems:
            st.info("현재 특별한 문제가 없습니다. 정상 범위로 보입니다.")
            return
        
        for idx, problem in enumerate(problems[:3], 1):
            text = problem.get("text", "")
            target_page = problem.get("target_page", "점장 마감")
            
            st.markdown(f"""
            <div style="padding: 1rem 1.2rem; background: linear-gradient(135deg, #fff5f5 0%, #fee2e2 100%); border: 1px solid #fecaca; border-left: 4px solid #dc3545; border-radius: 10px; margin-bottom: 0.8rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <div style="font-weight: 600; color: #721c24; font-size: 0.95rem; margin-bottom: 0.3rem;">{idx}. {text}</div>
            </div>
            """, unsafe_allow_html=True)
            
            col_btn, _ = st.columns([2, 4])
            with col_btn:
                if st.button(f"보러가기", key=f"zone3_btn_{idx}", use_container_width=True):
                    st.session_state["current_page"] = target_page
                    st.rerun()
    except Exception as e:
        logger.error(f"문제 TOP3 렌더링 오류: {e}")
        st.info("문제 분석 중입니다.")
    
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)


def _render_zone4_design_snapshot(store_id: str, year: int, month: int) -> None:
    """ZONE 4: 가게 구조 스냅샷 (Design Snapshot)"""
    st.markdown("### 🟣 가게 구조 스냅샷")
    
    col1, col2, col3 = st.columns(3, gap="medium")
    
    with col1:
        # 메뉴 구조 점수
        try:
            menu_count = get_menu_count(store_id)
            if menu_count >= 10:
                score = "A"
            elif menu_count >= 5:
                score = "B"
            elif menu_count >= 3:
                score = "C"
            else:
                score = "—"
            
            if score != "—":
                st.markdown(f"""
                <div style="padding: 1.5rem; background: linear-gradient(135deg, #e7f3ff 0%, #d1ecf1 100%); border-radius: 12px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <div style="font-size: 0.9rem; color: #0c5460; margin-bottom: 0.5rem; font-weight: 600;">메뉴 구조</div>
                    <div style="font-size: 2.5rem; font-weight: 700; color: #17a2b8;">{score}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("메뉴 설계실", key="zone4_btn_menu", use_container_width=True):
                    st.session_state["current_page"] = "메뉴 등록"
                    st.rerun()
            else:
                st.markdown(f"""
                <div style="padding: 1.5rem; background: #f8f9fa; border-radius: 12px; text-align: center; border: 2px dashed #dee2e6;">
                    <div style="font-size: 0.9rem; color: #6c757d; margin-bottom: 0.5rem; font-weight: 600;">메뉴 구조</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #6c757d;">—</div>
                    <div style="font-size: 0.8rem; color: #6c757d; margin-top: 0.5rem;">진단 준비중</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("메뉴 설계실", key="zone4_btn_menu", use_container_width=True):
                    st.session_state["current_page"] = "메뉴 등록"
                    st.rerun()
        except Exception:
            st.markdown(f"""
            <div style="padding: 1.5rem; background: #f8f9fa; border-radius: 12px; text-align: center; border: 2px dashed #dee2e6;">
                <div style="font-size: 0.9rem; color: #6c757d; margin-bottom: 0.5rem; font-weight: 600;">메뉴 구조</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #6c757d;">—</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        # 수익 구조 점수
        try:
            from src.storage_supabase import get_fixed_costs, get_variable_cost_ratio, calculate_break_even_sales, load_monthly_sales_total
            break_even = calculate_break_even_sales(store_id, year, month)
            monthly_sales = load_monthly_sales_total(store_id, year, month) or 0
            
            if break_even > 0 and monthly_sales > 0:
                if monthly_sales >= break_even * 1.2:
                    score = "A"
                elif monthly_sales >= break_even:
                    score = "B"
                else:
                    score = "C"
            else:
                score = "—"
            
            if score != "—":
                st.markdown(f"""
                <div style="padding: 1.5rem; background: linear-gradient(135deg, #e7f3ff 0%, #d1ecf1 100%); border-radius: 12px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <div style="font-size: 0.9rem; color: #0c5460; margin-bottom: 0.5rem; font-weight: 600;">수익 구조</div>
                    <div style="font-size: 2.5rem; font-weight: 700; color: #17a2b8;">{score}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("수익 구조 설계실", key="zone4_btn_revenue", use_container_width=True):
                    st.session_state["current_page"] = "목표 비용구조"
                    st.rerun()
            else:
                st.markdown(f"""
                <div style="padding: 1.5rem; background: #f8f9fa; border-radius: 12px; text-align: center; border: 2px dashed #dee2e6;">
                    <div style="font-size: 0.9rem; color: #6c757d; margin-bottom: 0.5rem; font-weight: 600;">수익 구조</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #6c757d;">—</div>
                    <div style="font-size: 0.8rem; color: #6c757d; margin-top: 0.5rem;">진단 준비중</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("수익 구조 설계실", key="zone4_btn_revenue", use_container_width=True):
                    st.session_state["current_page"] = "목표 비용구조"
                    st.rerun()
        except Exception:
            st.markdown(f"""
            <div style="padding: 1.5rem; background: #f8f9fa; border-radius: 12px; text-align: center; border: 2px dashed #dee2e6;">
                <div style="font-size: 0.9rem; color: #6c757d; margin-bottom: 0.5rem; font-weight: 600;">수익 구조</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #6c757d;">—</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        # 재료 구조 점수
        try:
            from src.storage_supabase import load_csv
            ingredient_df = load_csv('ingredient_master.csv', store_id=store_id, default_columns=['재료명'])
            ingredient_count = len(ingredient_df) if not ingredient_df.empty else 0
            
            if ingredient_count >= 20:
                score = "A"
            elif ingredient_count >= 10:
                score = "B"
            elif ingredient_count >= 5:
                score = "C"
            else:
                score = "—"
            
            if score != "—":
                st.markdown(f"""
                <div style="padding: 1.5rem; background: linear-gradient(135deg, #e7f3ff 0%, #d1ecf1 100%); border-radius: 12px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <div style="font-size: 0.9rem; color: #0c5460; margin-bottom: 0.5rem; font-weight: 600;">재료 구조</div>
                    <div style="font-size: 2.5rem; font-weight: 700; color: #17a2b8;">{score}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("재료 구조 설계실", key="zone4_btn_ingredient", use_container_width=True):
                    st.session_state["current_page"] = "재료 등록"
                    st.rerun()
            else:
                st.markdown(f"""
                <div style="padding: 1.5rem; background: #f8f9fa; border-radius: 12px; text-align: center; border: 2px dashed #dee2e6;">
                    <div style="font-size: 0.9rem; color: #6c757d; margin-bottom: 0.5rem; font-weight: 600;">재료 구조</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #6c757d;">—</div>
                    <div style="font-size: 0.8rem; color: #6c757d; margin-top: 0.5rem;">진단 준비중</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("재료 구조 설계실", key="zone4_btn_ingredient", use_container_width=True):
                    st.session_state["current_page"] = "재료 등록"
                    st.rerun()
        except Exception:
            st.markdown(f"""
            <div style="padding: 1.5rem; background: #f8f9fa; border-radius: 12px; text-align: center; border: 2px dashed #dee2e6;">
                <div style="font-size: 0.9rem; color: #6c757d; margin-bottom: 0.5rem; font-weight: 600;">재료 구조</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #6c757d;">—</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)


def _render_routine_badges(store_id: str) -> None:
    """루틴 배지 렌더링"""
    try:
        routine_status = get_routine_status(store_id)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_emoji = "✅" if routine_status["daily_close_done"] else "⚠️"
            if st.button(
                f"{status_emoji} 오늘 마감",
                key="routine_daily_close",
                use_container_width=True,
                disabled=routine_status["daily_close_done"]
            ):
                st.session_state.current_page = "점장 마감"
                st.rerun()
        
        with col2:
            status_emoji = "✅" if routine_status["weekly_design_check_done"] else "⚠️"
            if st.button(
                f"{status_emoji} 이번 주 구조 점검",
                key="routine_weekly_design",
                use_container_width=True,
                disabled=routine_status["weekly_design_check_done"]
            ):
                st.session_state.current_page = "가게 설계 센터"
                st.rerun()
        
        with col3:
            status_emoji = "✅" if routine_status["monthly_structure_review_done"] else "⚠️"
            if st.button(
                f"{status_emoji} 이번 달 구조 판결",
                key="routine_monthly_review",
                use_container_width=True,
                disabled=routine_status["monthly_structure_review_done"]
            ):
                st.session_state.current_page = "실제정산"
                st.rerun()
    except Exception:
        pass


def _render_zone5_school_strip() -> None:
    """ZONE 5: 사장 학교 1줄 (School Strip)"""
    st.markdown("### 🔴 사장 학교")
    
    # 랜덤 또는 룰 기반 개념 카드
    concepts = [
        "손익분기점은 목표가 아니라 생존선입니다.",
        "고정비는 매출이 없어도 나가는 돈입니다. 변동비는 매출에 비례합니다.",
        "메뉴 원가율이 50%를 넘으면 그 메뉴는 수익에 거의 기여하지 않습니다.",
        "재료 집중도가 높으면 가격 변동에 취약합니다.",
        "마감 데이터가 쌓이면 가게 패턴이 보이기 시작합니다.",
    ]
    
    import random
    concept = random.choice(concepts)
    
    st.markdown(f"""
    <div style="padding: 1.2rem 1.5rem; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 12px; border-left: 4px solid #6c757d; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
        <div style="font-size: 0.9rem; color: #495057; line-height: 1.6; font-weight: 500; font-style: italic;">💡 {concept}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 더보기 버튼 (향후 확장 포인트)
    # st.button("더보기", key="zone5_btn_more", use_container_width=True)
    
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
