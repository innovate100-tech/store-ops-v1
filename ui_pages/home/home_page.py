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
from src.auth import get_current_store_id, get_onboarding_mode
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


def get_today_one_action(store_id: str, level: int, is_coach_mode: bool = False) -> dict:
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
            if is_coach_mode:
                problems = get_problems_top3(store_id)
                has_sales = any("매출" in p.get("text", "") and ("감소" in p.get("text", "") or "떨어" in p.get("text", "")) for p in problems)
                if has_sales:
                    return {"title": "판매 흐름 점검", "reason": "최근 매출이 흔들리고 있어, 오늘은 판매 흐름을 3분만 점검해보세요.", "button_label": "📦 판매 관리 보러가기", "target_page": "매출 관리"}
                return {"title": "판매 흐름 점검", "reason": "판매 데이터가 쌓였습니다. 메뉴별 흐름을 보고 오늘 밀 메뉴를 정하세요.", "button_label": "📦 판매 관리 보러가기", "target_page": "매출 관리"}
            return {"title": "판매 흐름 3분 점검", "reason": "판매 데이터가 쌓였습니다. 메뉴별 흐름을 보고 오늘 밀 메뉴를 정하세요.", "button_label": "📦 판매 관리 보러가기", "target_page": "매출 관리"}
        if level == 3:
            if not check_actual_settlement_exists(store_id, cy, cm):
                return {"title": "이번 달 성적표 만들기", "reason": "정산이 있어야 이익/구조판이 자동으로 작동합니다.", "button_label": "🧾 실제정산 하러가기", "target_page": "실제정산"}
            if is_coach_mode:
                return {"title": "숫자 구조 복습", "reason": "매출이 오르면 얼마가 남는지 알고 있으면 의사결정이 빨라집니다. 오늘은 10초만 복습해보세요.", "button_label": "💳 목표 비용구조 보기", "target_page": "목표 비용구조"}
            return {"title": "숫자 구조 10초 복습", "reason": "매출이 오르면 얼마가 남는지 알고 있으면 의사결정이 빨라집니다.", "button_label": "💳 목표 비용구조 보기", "target_page": "목표 비용구조"}
        return fallback
    except Exception:
        return fallback


def get_today_one_action_with_day_context(store_id: str, level: int, is_coach_mode: bool = False, day_level: str | None = None) -> dict:
    """오늘 하나만 추천 (DAY 톤)."""
    action = get_today_one_action(store_id, level, is_coach_mode)
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


def _render_home_body(store_id: str, coaching_enabled: bool) -> None:
    """통합 홈 렌더링. coaching_enabled=True면 coach_only 블록 표시."""
    load_start = time.time()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다. 로그인 상태를 확인해주세요.")
        return
    kst = ZoneInfo("Asia/Seoul")
    now = datetime.now(kst)
    year, month = now.year, now.month
    
    # 새로고침 버튼 (캐시 무효화)
    render_page_header("사장 계기판", "🏠")
    col_refresh, _ = st.columns([1, 5])
    with col_refresh:
        if st.button("🔄 새로고침", key="home_btn_refresh", use_container_width=True):
            try:
                st.cache_data.clear()
                st.cache_resource.clear()
                logger.info("홈 캐시 무효화 완료")
                st.rerun()
            except Exception as e:
                logger.error(f"캐시 무효화 실패: {e}")
    
    data_level = detect_data_level(store_id)
    st.session_state["home_data_level"] = data_level
    day_level = detect_owner_day_level(store_id)
    kpis = load_home_kpis(store_id, year, month)
    monthly_sales = kpis["monthly_sales"]
    today_sales = kpis["today_sales"]
    close_stats = kpis["close_stats"]
    avg_customer_spend = kpis["avg_customer_spend"]
    monthly_profit = kpis["monthly_profit"]
    closed_days, total_days, close_rate, streak_days = close_stats
    
    load_time = time.time() - load_start
    logger.info(f"[홈 로드 시간] {load_time:.3f}초 (store_id={store_id}, coaching_enabled={coaching_enabled})")

    # ===== 첫 화면 구성 (스크롤 0~1회) =====
    
    # 1. 빠른 이동
    render_section_divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📋 점장마감", type="primary", use_container_width=True, key="home_btn_quick_close"):
            st.session_state["current_page"] = "점장 마감"
            st.rerun()
    with col2:
        if st.button("📊 매출관리", type="primary", use_container_width=True, key="home_btn_quick_sales"):
            st.session_state["current_page"] = "매출 관리"
            st.rerun()
    with col3:
        if st.button("🧾 실제정산", type="primary", use_container_width=True, key="home_btn_quick_settlement"):
            st.session_state["current_page"] = "실제정산"
            st.rerun()
    render_section_divider()

    # 2. 상태 요약 (5 KPI 카드) - 중립 톤, 일관된 스타일
    st.markdown("### 📊 상태 요약")
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        _kpi_card_unified("이번 달 매출", f"{monthly_sales:,}원" if monthly_sales > 0 else "-", None)
    with k2:
        pct = int(close_rate * 100) if closed_days > 0 else 0
        close_text = f"{pct}%" if closed_days > 0 else "-"
        if closed_days > 0:
            close_sub = f"{closed_days}/{total_days}일"
            if streak_days > 0:
                close_sub = f"{close_sub} 🔥{streak_days}일"
        else:
            close_sub = None
        _kpi_card_unified("마감률", close_text, close_sub)
    with k3:
        _kpi_card_unified("오늘 매출", f"{today_sales:,}원" if today_sales > 0 else "-", None)
    with k4:
        v = f"{avg_customer_spend:,}원" if (avg_customer_spend or 0) > 0 else "-"
        _kpi_card_unified("객단가", v, None)
    with k5:
        profit_text = f"{monthly_profit:,}원" if monthly_profit is not None else "-"
        _kpi_card_unified("이번 달 이익", profit_text, None)
    render_section_divider()

    # 3. 이상 징후 (최대 2개)
    try:
        _render_anomaly_signals(store_id, coaching_enabled)
    except Exception:
        pass
    render_section_divider()

    # 4. 문제 TOP1 / 잘한 점 TOP1
    try:
        _render_problems_good_points(store_id, coaching_enabled)
    except Exception:
        pass
    render_section_divider()

    # ===== Coach Only 섹션 (첫 화면 이후) =====
    if coaching_enabled and day_level:
        try:
            if day_level == "DAY1":
                st.info("**지금은 '기록 습관'을 만드는 단계입니다.**\n\n이 앱은 아직 분석보다 '쌓는 중'입니다. 3일만 지나면 가게 흐름이 보이기 시작합니다.")
            elif day_level == "DAY3":
                st.success("**이제 가게가 숫자로 보이기 시작했습니다.**\n\n지금부터 홈은 '기록 앱'이 아니라 '코치 화면'으로 바뀌기 시작합니다.")
            elif day_level == "DAY7":
                st.success("**이제 이 앱은 사장님의 '매장 코치' 모드입니다.**\n\n오늘부터는 기록보다, '무엇을 고칠지'가 먼저 보입니다.")
        except Exception:
            pass
    if coaching_enabled and "coach_mode_welcomed" not in st.session_state:
        st.success("🎉 코치 모드가 활성화되었습니다.\n이제 홈이 매일 가게 상태를 읽고, 중요한 것부터 알려드립니다.")
        st.session_state["coach_mode_welcomed"] = True
    render_section_divider()

    if coaching_enabled:
        try:
            _render_coach_missions(store_id, year, month, kpis)
        except Exception:
            pass
        render_section_divider()

    if coaching_enabled:
        try:
            action = get_today_one_action_with_day_context(store_id, data_level, True, day_level)
            st.markdown("### 🎯 오늘 코치의 한 가지 제안")
            st.markdown(f"""<div style="padding: 1.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; color: white;"><h4 style="color: white;">{action['title']}</h4><p style="color: rgba(255,255,255,0.9);">{action['reason']}</p></div>""", unsafe_allow_html=True)
            if st.button(action["button_label"], type="primary", use_container_width=True, key="home_btn_today_one"):
                st.session_state["current_page"] = action["target_page"]
                st.rerun()
        except Exception:
            try:
                st.markdown("""<div style="padding: 1.5rem; background: #fff3cd; border-radius: 12px; border-left: 4px solid #ffc107;"><h4 style="color: #856404;">오늘 마감부터 시작</h4><p style="color: #856404;">데이터가 없어서 분석이 불가능합니다. 오늘 마감 1회만 하면 홈이 채워집니다.</p></div>""", unsafe_allow_html=True)
                if st.button("📋 점장 마감 하러가기", type="primary", use_container_width=True, key="home_btn_fallback"):
                    st.session_state["current_page"] = "점장 마감"
                    st.rerun()
            except Exception:
                pass
    render_section_divider()

    # ===== Lazy 영역 (expander) =====
    st.markdown("### 📈 미니 차트")
    st.markdown("""<div style="padding: 2rem; background: #f8f9fa; border-radius: 8px; text-align: center; border: 2px dashed #dee2e6;"><p style="color: #6c757d;">차트를 표시하려면 마감 데이터가 필요합니다.</p></div>""", unsafe_allow_html=True)
    if st.button("📋 점장 마감으로 이동", use_container_width=True, key="home_btn_chart_close"):
        st.session_state["current_page"] = "점장 마감"
        st.rerun()
    render_section_divider()

    if coaching_enabled:
        try:
            s = get_month_status_summary(store_id, year, month, day_level)
            st.markdown(f"**📌 이번 달 가게 상태 한 줄**\n\n{s}")
        except Exception:
            pass
    render_section_divider()

    render_lazy_insights(store_id, year, month)


def _kpi_card_unified(label: str, value: str, subtitle: str | None = None) -> None:
    """
    통일된 KPI 카드 스타일 (중립 톤, 일관된 레이아웃)
    - 높이: 120px 고정
    - 패딩: 1.2rem
    - 폰트: label 0.85rem, value 1.4rem, subtitle 0.75rem
    - 배경: #f8f9fa (중립 회색)
    - 테두리: 1px solid #e9ecef
    """
    sub_html = f'<div style="font-size: 0.75rem; color: #6c757d; margin-top: 0.3rem;">{subtitle}</div>' if subtitle else ""
    st.markdown(f"""
    <div style="
        padding: 1.2rem;
        background: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        text-align: center;
        height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    ">
        <div style="font-size: 0.85rem; color: #6c757d; margin-bottom: 0.5rem; font-weight: 500;">{label}</div>
        <div style="font-size: 1.4rem; font-weight: 700; color: #212529; line-height: 1.2;">{value}</div>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def _kpi_card(label: str, value: str, gradient: str | None) -> None:
    """레거시 함수 (하위 호환용)"""
    _kpi_card_unified(label, value, None)


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


def _render_problems_good_points(store_id: str, coaching_enabled: bool) -> None:
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
                if coaching_enabled:
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


def _render_anomaly_signals(store_id: str, coaching_enabled: bool) -> None:
    """이상 징후 경량 버전 (1-2개) + 자세히 보기 버튼 (전체 3개 lazy load)."""
    st.markdown("### ⚠️ 이상 징후")
    try:
        signals = get_anomaly_signals_light(store_id)
        if not signals:
            st.info("현재 감지된 이상 징후가 없습니다. 정상 범위로 보입니다.")
        else:
            for i, s in enumerate(signals, 1):
                t = s.get("text", "")
                g = ""
                if coaching_enabled:
                    if "매출" in t and ("감소" in t or "떨어" in t):
                        g = "<div style='color:#856404;font-size:0.8rem; margin-top:0.4rem;'>이 문제는 보통 요일/메뉴/객단가 흐름에서 원인이 보입니다.</div>"
                    elif "마감" in t and ("누락" in t or "없습니다" in t):
                        g = "<div style='color:#856404;font-size:0.8rem; margin-top:0.4rem;'>데이터가 끊기면 가게 상태도 같이 안 보입니다.</div>"
                    elif "판매량" in t or "판매" in t:
                        g = "<div style='color:#856404;font-size:0.8rem; margin-top:0.4rem;'>판매 흐름 변화는 판매 관리에서 메뉴별 데이터를 보면 확인됩니다.</div>"
                st.markdown(f"""<div style="padding: 1rem; background: #fffbeb; border: 1px solid #fef3c7; border-left: 4px solid #ffc107; border-radius: 8px; margin-bottom: 0.5rem;"><span style="font-size:1.1rem;">{s.get('icon','')}</span> <strong style="color:#92400e;">{t}</strong>{g}</div>""", unsafe_allow_html=True)
                if st.button("보러가기", key=f"home_btn_a_{i}", use_container_width=True):
                    st.session_state["current_page"] = s.get("target_page", "점장 마감")
                    st.rerun()
            if st.button("📋 자세히 보기 (전체)", key="home_btn_a_detail", use_container_width=True):
                st.session_state["_home_anomaly_expanded"] = True
                st.rerun()
        if st.session_state.get("_home_anomaly_expanded", False):
            with st.expander("⚠️ 이상 징후 전체 (최대 3개)", expanded=True):
                if "_home_anomaly_full" not in st.session_state:
                    st.session_state["_home_anomaly_full"] = get_anomaly_signals(store_id)
                signals_full = st.session_state["_home_anomaly_full"]
                if not signals_full:
                    st.info("추가 이상 징후가 없습니다.")
                else:
                    for i, s in enumerate(signals_full, 1):
                        t = s.get("text", "")
                        st.markdown(f"""<div style="padding: 0.8rem; background: #fffbeb; border: 1px solid #fef3c7; border-left: 4px solid #ffc107; border-radius: 8px; margin-bottom: 0.5rem;"><span style="font-size:1.1rem;">{s.get('icon','')}</span> <strong style="color:#92400e;">{t}</strong></div>""", unsafe_allow_html=True)
                        if st.button("보러가기", key=f"home_btn_a_full_{i}", use_container_width=True):
                            st.session_state["current_page"] = s.get("target_page", "점장 마감")
                            st.rerun()
    except Exception:
        st.error("이상 징후 분석 중 오류가 발생했습니다.")


def render_home() -> None:
    """홈 진입점."""
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.error("로그인이 필요합니다.")
        return
    if st.session_state.get("_mode_changed", False):
        try:
            st.cache_data.clear()
            st.cache_resource.clear()
        except Exception:
            pass
        st.session_state["_mode_changed"] = False
    mode = get_onboarding_mode(user_id)
    logger.info("render_home: user_id=%s, mode=%s", user_id, mode)
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다. 로그인 상태를 확인해주세요.")
        return
    coaching_enabled = mode != "fast"
    _render_home_body(store_id, coaching_enabled)
