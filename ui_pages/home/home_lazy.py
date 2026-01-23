"""
홈 Lazy 영역 (expander 클릭 시 로드)
- get_store_financial_structure, get_monthly_memos
- render_lazy_insights
"""
from __future__ import annotations

import streamlit as st
from datetime import datetime, date
from zoneinfo import ZoneInfo

from src.auth import get_supabase_client
from src.storage_supabase import (
    get_fixed_costs,
    get_variable_cost_ratio,
    calculate_break_even_sales,
    get_month_settlement_status,
)


def get_store_financial_structure(store_id: str, target_year: int, target_month: int) -> dict:
    """
    우리 가게 숫자 구조 (고정비/변동비/손익분기점).
    source: "actual" | "target" | "none"
    """
    default = {"source": "none", "fixed_cost": 0, "variable_ratio": 0.0, "break_even_sales": 0, "example_table": None}
    try:
        supabase = get_supabase_client()
        if not supabase:
            return default
        fixed_cost = get_fixed_costs(store_id, target_year, target_month)
        variable_ratio = get_variable_cost_ratio(store_id, target_year, target_month)
        break_even_sales = calculate_break_even_sales(store_id, target_year, target_month)
        month_status = get_month_settlement_status(store_id, target_year, target_month)
        source = "actual" if month_status == "final" else ("target" if (fixed_cost > 0 or variable_ratio > 0) else "none")
        if break_even_sales <= 0:
            return default
        example_table = []
        for sales in [
            max(int(break_even_sales * 0.8), 0),
            int(break_even_sales),
            int(break_even_sales * 1.2),
            int(break_even_sales * 1.5),
        ]:
            if sales > 0:
                profit = sales - fixed_cost - (sales * variable_ratio)
                margin = (profit / sales * 100) if sales > 0 else 0.0
                example_table.append({"sales": sales, "profit": int(profit), "margin": round(margin, 1)})
        return {
            "source": source,
            "fixed_cost": int(fixed_cost),
            "variable_ratio": variable_ratio,
            "break_even_sales": int(break_even_sales),
            "example_table": example_table,
        }
    except Exception:
        return default


def get_monthly_memos(store_id: str, year: int, month: int, limit: int = 5) -> list:
    """이번 달 daily_close 메모 최신 N개."""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return []
        start = date(year, month, 1)
        end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
        r = supabase.table("daily_close").select("date, memo").eq("store_id", store_id).gte(
            "date", start.isoformat()
        ).lt("date", end.isoformat()).not_.is_("memo", "null").neq("memo", "").order(
            "date", desc=True
        ).limit(limit).execute()
        if not r.data:
            return []
        out = []
        for row in r.data:
            m = (row.get("memo") or "").strip()
            if m:
                out.append({"date": row.get("date"), "memo": m})
        return out
    except Exception:
        return []


def render_lazy_insights(store_id: str, year: int, month: int) -> None:
    """인사이트 더보기 expander: 숫자 구조, 미니 차트 placeholder, 운영 메모."""
    with st.expander("📊 인사이트 더보기", expanded=False):
        structure = get_store_financial_structure(store_id, year, month)
        if structure["source"] != "none":
            fc = structure["fixed_cost"]
            vr = structure["variable_ratio"]
            be = structure["break_even_sales"]
            ex = structure["example_table"] or []
            st.markdown("#### 🏪 우리 가게 숫자 구조")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("고정비/월", f"{fc:,}원")
            with c2:
                st.metric("변동비율", f"{int(vr * 100)}%")
            with c3:
                st.metric("손익분기 매출", f"{be:,}원")
            if be > 0:
                margin_100k = int(100000 * (1 - vr))
                st.caption(f"매출 10만 원 늘면 약 {margin_100k:,}원 남는 구조.")
            if ex:
                st.markdown("##### 매출 구간별 예상 이익")
                for item in ex[:3]:
                    profit = item["profit"]
                    st.metric(f"매출 {item['sales']:,}원", f"{profit:,}원", delta=f"이익률 {item['margin']}%")
        else:
            st.info("목표 비용구조 또는 실제 정산을 입력하면 숫자 구조가 만들어집니다.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💳 목표 비용구조", key="lazy_btn_cost", use_container_width=True):
                    st.session_state.current_page = "목표 비용구조"
                    st.rerun()
            with col2:
                if st.button("🧾 실제정산", key="lazy_btn_settle", use_container_width=True):
                    st.session_state.current_page = "실제정산"
                    st.rerun()

        st.markdown("#### 📈 미니 차트")
        st.caption("차트를 보려면 마감 데이터가 필요합니다.")
        if st.button("📋 점장 마감으로 이동", key="lazy_btn_chart", use_container_width=True):
            st.session_state.current_page = "점장 마감"
            st.rerun()

        st.markdown("#### 📝 이번 달 운영 메모")
        memos = get_monthly_memos(store_id, year, month, limit=5)
        if memos:
            for m in memos:
                d = m.get("date", "")
                try:
                    if isinstance(d, str):
                        dt = datetime.strptime(d, "%Y-%m-%d").date()
                    else:
                        dt = d
                    ds = f"{dt.month:02d}/{dt.day:02d}"
                except Exception:
                    ds = str(d)[:10] if d else ""
                st.markdown(f"**{ds}** {m.get('memo', '')}")
        else:
            st.caption("마감 때 특이사항을 남기면 여기에 모입니다.")
            if st.button("📋 점장 마감", key="lazy_btn_memo", use_container_width=True):
                st.session_state.current_page = "점장 마감"
                st.rerun()
