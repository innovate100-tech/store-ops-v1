"""
분석총평 페이지
세부 분석(매출·비용·실제정산·원가·재고·재료·메뉴·QSC) 고도화 자료를 복합·고도화 분석하여
최종 분석자료 + 해석 + 우선순위 액션 제공
"""
from __future__ import annotations

import logging
from calendar import monthrange
from datetime import datetime
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from src.analytics import calculate_ingredient_usage, calculate_menu_cost
from src.auth import get_current_store_id
from src.bootstrap import bootstrap
from src.storage_supabase import (
    calculate_break_even_sales,
    get_fixed_costs,
    get_variable_cost_ratio,
    load_actual_settlement_items,
    load_csv,
    load_expense_structure,
    load_monthly_sales_total,
)
from src.ui_helpers import render_page_header
from src.utils.time_utils import current_month_kst, current_year_kst, today_kst

logger = logging.getLogger(__name__)

bootstrap(page_title="분석총평")

# 도메인별 page_key
DOMAIN_PAGES = {
    "매출": "매출 관리",
    "비용": "비용 분석",
    "실제정산": "실제정산 분석",
    "원가": "원가 파악",
    "재고": "재고 분석",
    "재료": "재료 사용량 집계",
    "메뉴": "판매 관리",
    "QSC": "체크결과",
}


def _safe_float(v: Any, default: float = 0.0) -> float:
    if v is None:
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _safe_monthly_sales(store_id: str, year: int, month: int) -> float:
    try:
        return float(load_monthly_sales_total(store_id, year, month) or 0)
    except Exception:
        return 0.0


def _safe_target_sales(store_id: str, year: int, month: int) -> float:
    try:
        df = load_csv("targets.csv", default_columns=["연도", "월", "목표매출"], store_id=store_id)
        if df.empty:
            return 0.0
        r = df[(df["연도"] == year) & (df["월"] == month)]
        if r.empty:
            return 0.0
        return _safe_float(r.iloc[0].get("목표매출"), 0.0)
    except Exception:
        return 0.0


def _safe_actual_costs(store_id: str, year: int, month: int) -> float:
    try:
        items = load_actual_settlement_items(store_id, year, month) or []
        return sum(_safe_float(it.get("amount")) for it in items)
    except Exception:
        return 0.0


@st.cache_data(ttl=300)
def _load_latest_qsc_session(store_id: str) -> Optional[Dict]:
    try:
        from src.auth import get_supabase_client
        supabase = get_supabase_client()
        if not supabase:
            return None
        r = (
            supabase.table("health_check_sessions")
            .select("id, completed_at")
            .eq("store_id", store_id)
            .not_.is_("completed_at", "null")
            .order("completed_at", desc=True)
            .limit(1)
            .execute()
        )
        if r.data and len(r.data) > 0:
            return r.data[0]
    except Exception as e:
        logger.warning("_load_latest_qsc_session: %s", e)
    return None


def _summary_sales(store_id: str, year: int, month: int) -> Dict[str, Any]:
    ms = _safe_monthly_sales(store_id, year, month)
    ts = _safe_target_sales(store_id, year, month)
    be = calculate_break_even_sales(store_id, year, month) or 0.0
    fixed = get_fixed_costs(store_id, year, month) or 0.0
    var = get_variable_cost_ratio(store_id, year, month) or 0.0
    days = monthrange(year, month)[1]
    be_daily = (be / days) if be and days > 0 else 0.0
    target_daily = (ts / days) if ts and days > 0 else 0.0

    today = today_kst()
    is_cur = today.year == year and today.month == month
    cur_day = max(1, today.day if is_cur else days)
    daily_avg = ms / cur_day if cur_day > 0 else 0.0
    avg_daily_profit = 0.0
    if fixed is not None and var is not None and be_daily and be_daily > 0:
        daily_fixed = fixed / days if days > 0 else 0.0
        avg_daily_profit = daily_avg * (1 - var) - daily_fixed if daily_avg else 0.0

    be_pct = (ms / be * 100) if be and be > 0 else None
    tg_pct = (ms / ts * 100) if ts and ts > 0 else None

    return {
        "당월매출": ms,
        "손익분기": be,
        "손익분기대비": be_pct,
        "목표매출": ts,
        "목표대비": tg_pct,
        "일평균매출": daily_avg,
        "평균일별영업이익": avg_daily_profit,
        "지표": [
            ("당월 누적 매출", f"{int(ms):,}원" if ms else "—"),
            ("손익분기 대비", f"{be_pct:.0f}%" if be_pct is not None else "—"),
            ("목표 대비", f"{tg_pct:.0f}%" if tg_pct is not None else "—"),
            ("평균 일별 영업이익", f"{int(avg_daily_profit):,}원" if avg_daily_profit else "—"),
        ],
        "해석": _sales_insight(ms, ts, be, be_pct, tg_pct),
    }


def _sales_insight(ms: float, ts: float, be: float, be_pct: Optional[float], tg_pct: Optional[float]) -> str:
    parts = []
    if be and be > 0 and be_pct is not None:
        if be_pct >= 100:
            parts.append("매출이 손익분기 이상입니다.")
        else:
            parts.append(f"손익분기 미달(대비 {be_pct:.0f}%)입니다. 매출 증대 또는 비용 조정이 필요합니다.")
    if ts and ts > 0 and tg_pct is not None:
        if tg_pct >= 100:
            parts.append("목표 달성 중입니다.")
        else:
            parts.append(f"목표 대비 {tg_pct:.0f}%로 미달입니다.")
    return " ".join(parts) if parts else "매출·목표 데이터를 입력하면 해석이 제공됩니다."


def _summary_costs(store_id: str, year: int, month: int) -> Dict[str, Any]:
    try:
        exp = load_expense_structure(year, month, store_id=store_id)
    except Exception:
        exp = pd.DataFrame()
    fixed = get_fixed_costs(store_id, year, month) or 0.0
    var = get_variable_cost_ratio(store_id, year, month) or 0.0
    ms = _safe_monthly_sales(store_id, year, month)
    actual = _safe_actual_costs(store_id, year, month)

    by_cat = {}
    if isinstance(exp, pd.DataFrame) and not exp.empty and "category" in exp.columns:
        for _, row in exp.iterrows():
            c = row.get("category")
            if not c:
                continue
            amt = _safe_float(row.get("amount"))
            by_cat[c] = {"amount": amt}

    total_target = fixed + (ms * var) if ms and var is not None else fixed
    diff = actual - total_target if total_target else 0.0

    return {
        "고정비": fixed,
        "변동비율": var,
        "5대비용": by_cat,
        "목표총비용": total_target,
        "실제총비용": actual,
        "순이익차이": (ms - actual) - (ms - total_target) if ms else None,
        "지표": [
            ("고정비", f"{int(fixed):,}원" if fixed else "—"),
            ("변동비율", f"{var*100:.1f}%" if var is not None else "—"),
            ("실제 총비용", f"{int(actual):,}원" if actual else "—"),
        ],
        "해석": f"고정비 {int(fixed):,}원, 변동비율 {var*100:.1f}%. 실제 비용 {int(actual):,}원." if fixed is not None and var is not None else "비용 구조를 입력하면 해석이 제공됩니다.",
    }


def _summary_settlement(store_id: str, year: int, month: int) -> Dict[str, Any]:
    ms = _safe_monthly_sales(store_id, year, month)
    ts = _safe_target_sales(store_id, year, month)
    actual = _safe_actual_costs(store_id, year, month)
    fixed = get_fixed_costs(store_id, year, month) or 0.0
    var = get_variable_cost_ratio(store_id, year, month) or 0.0
    target_cost = fixed + (ts * var) if ts and var is not None else fixed
    target_profit = ts - target_cost if ts else 0.0
    actual_profit = ms - actual if ms else 0.0
    diff = actual_profit - target_profit if target_profit else actual_profit

    return {
        "목표매출": ts,
        "실제매출": ms,
        "목표순이익": target_profit,
        "실제순이익": actual_profit,
        "순이익차이": diff,
        "지표": [
            ("실제 매출", f"{int(ms):,}원" if ms else "—"),
            ("실제 순이익", f"{int(actual_profit):,}원" if actual_profit is not None else "—"),
            ("목표 대비 순이익", f"{int(diff):+,}원" if diff is not None else "—"),
        ],
        "해석": f"실제 순이익 {int(actual_profit):,}원. 목표 대비 {int(diff):+,}원." if actual_profit is not None and diff is not None else "실제정산 데이터를 입력하면 해석이 제공됩니다.",
    }


def _summary_cost_overview(store_id: str) -> Dict[str, Any]:
    menu_df = load_csv("menu_master.csv", default_columns=["메뉴명", "판매가"], store_id=store_id)
    recipe_df = load_csv("recipes.csv", default_columns=["메뉴명", "재료명", "사용량"], store_id=store_id)
    ing_df = load_csv("ingredient_master.csv", default_columns=["재료명", "단위", "단가"], store_id=store_id)
    cost_df = pd.DataFrame()
    if not menu_df.empty and not recipe_df.empty and not ing_df.empty:
        try:
            cost_df = calculate_menu_cost(menu_df, recipe_df, ing_df)
        except Exception:
            pass

    risk_count = 0
    avg_rate = 0.0
    if not cost_df.empty and "원가율" in cost_df.columns:
        risk_count = int((cost_df["원가율"] >= 35).sum())
        avg_rate = float(cost_df["원가율"].mean())

    return {
        "원가율위험메뉴수": risk_count,
        "평균원가율": avg_rate,
        "지표": [
            ("원가율 35% 이상 메뉴", f"{risk_count}개"),
            ("평균 원가율", f"{avg_rate:.1f}%"),
        ],
        "해석": f"고원가율 메뉴 {risk_count}개, 평균 원가율 {avg_rate:.1f}%." if risk_count is not None else "메뉴·레시피·재료를 입력하면 원가 분석이 제공됩니다.",
    }


def _summary_inventory(store_id: str) -> Dict[str, Any]:
    inv_df = load_csv("inventory.csv", default_columns=["재료명", "현재고", "안전재고"], store_id=store_id)
    danger = 0
    if not inv_df.empty and "현재고" in inv_df.columns and "안전재고" in inv_df.columns:
        for _, row in inv_df.iterrows():
            cur, safe = row.get("현재고"), row.get("안전재고")
            if safe and (cur is None or _safe_float(cur) < _safe_float(safe)):
                danger += 1

    return {
        "품절위험수": danger,
        "지표": [
            ("품절 위험 재고", f"{danger}개"),
            ("재고 상태", "품절 위험 있음" if danger > 0 else "안정"),
        ],
        "해석": f"품절 위험 {danger}개. 발주·안전재고 조정을 검토하세요." if danger > 0 else "재고 안정.",
    }


def _summary_usage(store_id: str) -> Dict[str, Any]:
    sales_df = load_csv("daily_sales_items.csv", default_columns=["날짜", "메뉴명", "판매수량"], store_id=store_id)
    recipe_df = load_csv("recipes.csv", default_columns=["메뉴명", "재료명", "사용량"], store_id=store_id)
    usage_df = pd.DataFrame()
    if not sales_df.empty and not recipe_df.empty:
        try:
            usage_df = calculate_ingredient_usage(sales_df, recipe_df)
        except Exception:
            pass

    top_n = 0
    if not usage_df.empty and "재료명" in usage_df.columns and "총사용량" in usage_df.columns:
        top_n = min(5, len(usage_df))

    return {
        "사용재료수": len(usage_df) if not usage_df.empty else 0,
        "top사용재료수": top_n,
        "지표": [
            ("사용 재료 수", f"{len(usage_df)}개" if not usage_df.empty else "0개"),
            ("TOP 사용 재료", f"{top_n}개" if top_n else "—"),
        ],
        "해석": f"사용 재료 {len(usage_df)}개. 재료 사용량 트렌드를 확인하세요." if not usage_df.empty else "판매·레시피 데이터를 입력하면 재료 사용량 분석이 제공됩니다.",
    }


def _summary_menu(store_id: str) -> Dict[str, Any]:
    menu_df = load_csv("menu_master.csv", default_columns=["메뉴명", "판매가"], store_id=store_id)
    sales_df = load_csv("daily_sales_items.csv", default_columns=["날짜", "메뉴명", "판매수량"], store_id=store_id)
    n_menu = len(menu_df) if not menu_df.empty else 0
    has_sales = not sales_df.empty and "메뉴명" in sales_df.columns

    return {
        "메뉴수": n_menu,
        "판매데이터유무": has_sales,
        "지표": [
            ("등록 메뉴 수", f"{n_menu}개"),
            ("판매 데이터", "있음" if has_sales else "없음"),
        ],
        "해석": f"메뉴 {n_menu}개. 판매·메뉴 분석에서 트렌드와 수익성을 확인하세요." if n_menu else "메뉴를 등록하면 판매·메뉴 분석이 제공됩니다.",
    }


def _summary_qsc(store_id: str) -> Dict[str, Any]:
    sess = _load_latest_qsc_session(store_id)
    if not sess:
        return {
            "Top리스크": None,
            "지표": [("QSC 체크", "완료된 체크 없음")],
            "해석": "매장 체크리스트를 실시하면 QSC 결과가 반영됩니다.",
        }

    try:
        from src.health_check.storage import get_health_diagnosis

        diag = get_health_diagnosis(sess["id"])
    except Exception:
        diag = None

    risk_axes = (diag or {}).get("risk_axes") or []
    top = risk_axes[0] if risk_axes else None
    axis = top.get("axis", "") if top else ""
    reason = top.get("reason", "") if top else ""

    return {
        "Top리스크": {"axis": axis, "reason": reason},
        "지표": [
            ("최근 체크", "완료됨"),
            ("Top 리스크", f"{axis}: {reason[:30]}…" if axis and reason else "없음"),
        ],
        "해석": f"QSC Top 리스크: {axis}축 – {reason}" if axis and reason else "QSC 체크 결과를 확인하세요.",
    }


def _composite_insights(
    sales: Dict,
    costs: Dict,
    settlement: Dict,
    cost_ov: Dict,
    inv: Dict,
    usage: Dict,
    menu: Dict,
    qsc: Dict,
) -> List[Dict[str, str]]:
    out = []
    ms = sales.get("당월매출") or 0
    be = sales.get("손익분기") or 0
    be_pct = sales.get("손익분기대비")
    tg_pct = sales.get("목표대비")
    actual_profit = settlement.get("실제순이익")
    target_profit = settlement.get("목표순이익")
    diff_profit = settlement.get("순이익차이")
    risk_count = cost_ov.get("원가율위험메뉴수", 0)
    danger = inv.get("품절위험수", 0)
    top_risk = qsc.get("Top리스크")

    if be and be > 0 and be_pct is not None:
        if be_pct < 100:
            out.append({
                "주제": "매출–비용 구조",
                "해석": "고정비 대비 매출이 부족해 손익분기 미달입니다. 매출 회복 또는 고정비 조정이 우선입니다.",
                "링크": "비용 분석",
            })
        elif tg_pct is not None and tg_pct < 100:
            out.append({
                "주제": "매출–목표",
                "해석": "손익분기는 넘겼으나 목표 미달입니다. 목표 달성을 위해 매출 증대 방안을 검토하세요.",
                "링크": "매출 관리",
            })

    if actual_profit is not None and target_profit is not None and diff_profit is not None and diff_profit < 0:
        out.append({
            "주제": "매출–실제정산",
            "해석": f"실제 순이익이 목표 대비 {int(diff_profit):,}원 적습니다. 비용 초과(인건비·재료비 등)를 확인하세요.",
            "링크": "실제정산 분석",
        })

    if risk_count > 0 and danger > 0:
        out.append({
            "주제": "원가–재고–재료",
            "해석": "고원가율 메뉴와 품절 위험 재고가 동시에 있습니다. 원가·재고·재료 사용량을 함께 점검하세요.",
            "링크": "원가 파악",
        })
    elif risk_count > 0:
        out.append({
            "주제": "원가",
            "해석": f"원가율 35% 이상 메뉴가 {risk_count}개입니다. 원가 최적화와 메뉴 구조 검토를 권장합니다.",
            "링크": "원가 파악",
        })
    elif danger > 0:
        out.append({
            "주제": "재고",
            "해석": f"품절 위험 재고 {danger}개. 안전재고·발주 시점을 조정하세요.",
            "링크": "재고 분석",
        })

    if top_risk and top_risk.get("axis") == "M":
        out.append({
            "주제": "QSC–매출·메뉴",
            "해석": "마케팅(M) 축이 리스크로 잡혀 있습니다. 유입·메뉴 기획과 함께 점검하세요.",
            "링크": "체크결과",
        })

    return out[:5]


def _prioritized_actions(
    sales: Dict,
    costs: Dict,
    settlement: Dict,
    cost_ov: Dict,
    inv: Dict,
    menu: Dict,
    qsc: Dict,
) -> List[Dict[str, str]]:
    actions = []
    be_pct = sales.get("손익분기대비")
    tg_pct = sales.get("목표대비")
    diff = settlement.get("순이익차이")
    risk_count = cost_ov.get("원가율위험메뉴수", 0)
    danger = inv.get("품절위험수", 0)

    if be_pct is not None and be_pct < 100:
        actions.append({"설명": "손익분기 미달 – 매출 증대·비용 조정", "page": "매출 관리", "우선순위": 1})
    if tg_pct is not None and tg_pct < 100 and (be_pct is None or be_pct >= 100):
        actions.append({"설명": "목표 미달 – 매출 증대 방안 검토", "page": "매출 관리", "우선순위": 2})
    if diff is not None and diff < 0:
        actions.append({"설명": "실제정산 순이익 부족 – 비용·실제정산 확인", "page": "실제정산 분석", "우선순위": 3})
    if risk_count > 0:
        actions.append({"설명": "고원가율 메뉴 – 원가·메뉴 최적화", "page": "원가 파악", "우선순위": 4})
    if danger > 0:
        actions.append({"설명": "품절 위험 재고 – 발주·안전재고 검토", "page": "재고 분석", "우선순위": 5})
    if not actions:
        actions.append({"설명": "비용 구조 점검 – 목표 vs 실제", "page": "비용 분석", "우선순위": 6})
        actions.append({"설명": "메뉴·판매 트렌드 확인", "page": "판매 관리", "우선순위": 7})
    actions.sort(key=lambda x: x["우선순위"])
    return actions[:10]


def _go(page_key: str, key: str):
    if st.button("자세히 보기", key=key, use_container_width=True):
        st.session_state["current_page"] = page_key
        st.rerun()


def render_analysis_summary():
    """분석총평 페이지 렌더링"""
    render_page_header("분석총평", "📋")

    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return

    year = current_year_kst()
    month = current_month_kst()
    period_label = f"{year}년 {month}월"

    st.caption(f"기준: **{period_label}** · 세부 분석 결과를 복합해 최종 자료와 해석을 제공합니다.")

    # 데이터 로드
    sales = _summary_sales(store_id, year, month)
    costs = _summary_costs(store_id, year, month)
    settlement = _summary_settlement(store_id, year, month)
    cost_ov = _summary_cost_overview(store_id)
    inv = _summary_inventory(store_id)
    usage = _summary_usage(store_id)
    menu = _summary_menu(store_id)
    qsc = _summary_qsc(store_id)

    # ZONE A: 총평 헤더 + 한눈에 요약
    st.markdown("---")
    st.markdown("### 한눈에 요약")

    c1, c2, c3 = st.columns(3)
    with c1:
        _summary_card("매출·손익", f"{int(sales['당월매출']):,}원" if sales["당월매출"] else "—", sales.get("해석", "")[:80], "매출 관리")
    with c2:
        ac = costs.get("실제총비용") or 0
        sub = "목표 대비 초과" if (ac and costs.get("목표총비용") and ac > (costs.get("목표총비용") or 0)) else (costs.get("해석", "")[:50] or "—")
        _summary_card("비용·실제정산", f"{int(ac):,}원" if ac else "—", sub, "비용 분석")
    with c3:
        v = f"원가위험 {cost_ov['원가율위험메뉴수']}개 / 품절 {inv['품절위험수']}개"
        _summary_card("원가·재고·재료", v, usage.get("해석", "")[:60], "원가 파악")

    d1, d2 = st.columns(2)
    with d1:
        m = f"메뉴 {menu['메뉴수']}개"
        _summary_card("메뉴", m, menu.get("해석", "")[:60], "판매 관리")
    with d2:
        r = qsc.get("Top리스크") or {}
        rv = f"{r.get('axis', '—')}: {r.get('reason', '')[:20]}" if r else "—"
        _summary_card("QSC", rv[:40] if rv else "—", qsc.get("해석", "")[:60], "체크결과")

    insight_lines = []
    if sales.get("해석"):
        insight_lines.append(sales["해석"])
    if costs.get("해석"):
        insight_lines.append(costs["해석"])
    if inv.get("품절위험수", 0) > 0 or cost_ov.get("원가율위험메뉴수", 0) > 0:
        insight_lines.append("원가·재고에서 압박이 있습니다.")
    st.info("**통합 해석:** " + " ".join(insight_lines[:3]) if insight_lines else "데이터를 입력하면 통합 해석이 제공됩니다.")

    # ZONE B: 도메인별 핵심 지표 + 해석
    st.markdown("---")
    st.markdown("### 도메인별 핵심 지표")

    domains = [
        ("매출", sales, "매출 관리"),
        ("비용", costs, "비용 분석"),
        ("실제정산", settlement, "실제정산 분석"),
        ("원가", cost_ov, "원가 파악"),
        ("재고", inv, "재고 분석"),
        ("재료", usage, "재료 사용량 집계"),
        ("메뉴", menu, "판매 관리"),
        ("QSC", qsc, "체크결과"),
    ]
    for i, (label, data, page_key) in enumerate(domains):
        with st.expander(f"**{label}**", expanded=(i < 2)):
            for k, v in data.get("지표", []):
                st.caption(f"{k}: **{v}**")
            st.caption(data.get("해석", ""))
            _go(page_key, f"zoneb_go_{page_key}")

    # ZONE C: 복합 인사이트
    st.markdown("---")
    st.markdown("### 복합 인사이트 (도메인 간)")

    composite = _composite_insights(sales, costs, settlement, cost_ov, inv, usage, menu, qsc)
    if composite:
        for j, item in enumerate(composite):
            st.markdown(f"**{item['주제']}**")
            st.caption(item["해석"])
            pk = DOMAIN_PAGES.get(item.get("링크", ""), item.get("링크", ""))
            if pk and st.button("이동", key=f"zonec_go_{j}_{pk}", use_container_width=True):
                st.session_state["current_page"] = pk
                st.rerun()
            st.divider()
    else:
        st.info("매출·비용·실제정산·원가·재고 등을 입력하면 도메인 간 복합 인사이트가 제공됩니다.")

    # ZONE D: 우선순위 액션
    st.markdown("---")
    st.markdown("### 우선순위 액션")

    actions = _prioritized_actions(sales, costs, settlement, cost_ov, inv, menu, qsc)
    for k, act in enumerate(actions):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption(act["설명"])
        with col2:
            if st.button("이동", key=f"zoned_go_{k}_{act['page']}", use_container_width=True):
                st.session_state["current_page"] = act["page"]
                st.rerun()

    # ZONE E: 내보내기 (간단 TXT)
    st.markdown("---")
    st.markdown("### 요약 내보내기")

    export_lines = [f"# 분석총평 ({period_label})", ""]
    export_lines.append("## 한눈에 요약")
    export_lines.append(f"- 매출: {int(sales['당월매출']):,}원, 손익분기대비 {sales.get('손익분기대비') or '—'}%")
    export_lines.append(f"- 비용: 실제 {int(costs.get('실제총비용', 0)):,}원")
    export_lines.append(f"- 원가 위험 {cost_ov['원가율위험메뉴수']}개, 품절 위험 {inv['품절위험수']}개")
    export_lines.append("")
    export_lines.append("## 통합 해석")
    export_lines.append(" ".join(insight_lines[:3]) or "—")
    export_lines.append("")
    export_lines.append("## 우선순위 액션")
    for a in actions:
        export_lines.append(f"- {a['설명']} → {a['page']}")

    export_txt = "\n".join(export_lines)
    st.download_button("총평 요약 다운로드 (TXT)", export_txt, file_name=f"분석총평_{year}{month:02d}.txt", mime="text/plain", use_container_width=True)


def _summary_card(title: str, value: str, sub: str, page_key: str):
    st.markdown(f"""
    <div style="padding: 1rem; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); 
                border-radius: 10px; border: 1px solid rgba(148,163,184,0.3); margin-bottom: 0.8rem;">
        <div style="font-size: 0.9rem; font-weight: 600; color: #94a3b8;">{title}</div>
        <div style="font-size: 1.1rem; font-weight: 700; color: #fff;">{value or '—'}</div>
        <div style="font-size: 0.8rem; color: #64748b;">{sub[:60] if sub else ''}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("자세히", key=f"card_go_{page_key}", use_container_width=True):
        st.session_state["current_page"] = page_key
        st.rerun()
