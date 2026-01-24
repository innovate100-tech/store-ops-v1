"""
수익 구조 설계실 (가게 전체 돈 구조)
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
from datetime import datetime
from calendar import monthrange
from zoneinfo import ZoneInfo
from src.ui_helpers import render_page_header, render_section_divider
from src.storage_supabase import (
    get_fixed_costs,
    get_variable_cost_ratio,
    calculate_break_even_sales,
    load_monthly_sales_total,
    load_best_available_daily_sales,
    load_expense_structure,
)
from src.utils.time_utils import current_year_kst, current_month_kst
from ui_pages.design_lab.design_lab_frame import (
    render_coach_board,
    render_structure_map_container,
    render_school_cards,
    render_design_tools_container,
)
from ui_pages.design_lab.design_lab_coach_data import get_revenue_structure_design_coach_data
from src.auth import get_current_store_id
from src.design.baseline_loader import load_baseline_structure, get_baseline_structure

# 공통 설정 적용
bootstrap(page_title="Revenue Structure Design Lab")


def _calculate_monthly_sales_forecast(store_id: str, year: int, month: int) -> float:
    """이번 달 예상 매출 계산 (단순 추정)"""
    try:
        # 월 누적 매출
        monthly_accumulated = load_monthly_sales_total(store_id, year, month) or 0
        
        # 경과 일수 계산
        kst = ZoneInfo("Asia/Seoul")
        today = datetime.now(kst).date()
        first_day = datetime(year, month, 1).date()
        
        # 이번 달이면 경과 일수, 아니면 월 총 일수
        if today.year == year and today.month == month:
            days_passed = (today - first_day).days + 1
            total_days = monthrange(year, month)[1]
            
            if days_passed > 0:
                # (월 누적 / 경과일수) * 월 총일수
                forecast = (monthly_accumulated / days_passed) * total_days
                return forecast
        else:
            # 과거 월이면 누적 매출 그대로 반환
            return monthly_accumulated
        
        return monthly_accumulated
    except Exception:
        return 0.0


def render_revenue_structure_design_lab():
    """수익 구조 설계실 페이지 렌더링 (Design Lab 공통 프레임 적용)"""
    render_page_header("수익 구조 설계실", "💳")
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    current_year = current_year_kst()
    current_month = current_month_kst()
    
    # 데이터 로드
    fixed_costs = get_fixed_costs(store_id, current_year, current_month)
    variable_ratio = get_variable_cost_ratio(store_id, current_year, current_month)
    break_even = calculate_break_even_sales(store_id, current_year, current_month)
    monthly_sales = load_monthly_sales_total(store_id, current_year, current_month) or 0
    forecast_sales = _calculate_monthly_sales_forecast(store_id, current_year, current_month)
    
    # ZONE A: Coach Board
    coach_data = get_revenue_structure_design_coach_data(store_id, current_year, current_month)
    
    # 예상 매출 카드 추가 (4번째 카드)
    if forecast_sales > 0:
        coach_data["cards"].append({
            "title": "이번 달 예상 매출",
            "value": f"{int(forecast_sales):,}원",
            "subtitle": None
        })
    
    # 판결문 개선 (예상 매출 기반)
    if forecast_sales > 0 and break_even > 0:
        if forecast_sales < break_even:
            gap = break_even - forecast_sales
            coach_data["verdict_text"] = f"예상 매출이 손익분기점보다 약 {gap:,.0f}원 부족합니다. 매출 증대 또는 비용 절감이 필요합니다."
            coach_data["action_title"] = "수익 구조 분석하기"
            coach_data["action_reason"] = "손익분기점 미달 시 구조 조정이 필요합니다."
            coach_data["action_target_page"] = "수익 구조 설계실"
        elif forecast_sales >= break_even * 1.2:
            coach_data["verdict_text"] = "예상 매출이 손익분기점을 충분히 상회합니다. 수익 구조가 안정적입니다."
            coach_data["action_title"] = None
            coach_data["action_reason"] = None
            coach_data["action_target_page"] = None
    
    # 전략 브리핑 / 전략 실행 탭 분리
    # session_state로 초기 탭 제어
    initial_tab_key = f"_initial_tab_수익 구조 설계실"
    should_show_execute_first = st.session_state.get(initial_tab_key) == "execute"
    
    if should_show_execute_first:
        tab1, tab2 = st.tabs(["🛠️ 전략 실행", "📊 전략 브리핑"])
        st.session_state.pop(initial_tab_key, None)
        execute_tab = tab1
        briefing_tab = tab2
    else:
        tab1, tab2 = st.tabs(["📊 전략 브리핑", "🛠️ 전략 실행"])
        briefing_tab = tab1
        execute_tab = tab2
    
    with briefing_tab:
        # ZONE A: Coach Board
        render_coach_board(
            cards=coach_data["cards"],
            verdict_text=coach_data["verdict_text"],
            action_title=coach_data.get("action_title"),
            action_reason=coach_data.get("action_reason"),
            action_target_page=coach_data.get("action_target_page"),
            action_button_label=coach_data.get("action_button_label")
        )
        
        # ZONE B: 기준 구조 (1층 Baseline)
        st.markdown("#### 📐 기준 구조 (우리 매장 기본 설계도)")
        baseline = get_baseline_structure(store_id, current_year, current_month)
        if baseline is None:
            if st.button("🔄 현재 구조 불러오기", key="revenue_lab_load_baseline", use_container_width=True, type="primary"):
                try:
                    load_baseline_structure(store_id, current_year, current_month)
                    st.success("기준 구조를 불러왔습니다. 아래 조작 레버에서 시뮬레이션하세요.")
                    st.rerun()
                except Exception as e:
                    st.error(f"기준 구조 불러오기 실패: {e}")
            st.caption("매출·비용 분석 데이터에서 현재 월 구조를 자동 수집합니다. 가게 전략 센터에서 먼저 불러올 수도 있습니다.")
        else:
            sales_b = baseline.get("sales", {})
            cost_b = baseline.get("cost", {})
            profit_b = baseline.get("profit", {})
            b1, b2, b3, b4 = st.columns(4)
            with b1:
                st.metric("월매출(기준)", f"{int(sales_b.get('monthly_sales', 0) or sales_b.get('forecast_sales', 0)):,.0f}원")
                st.caption(f"일방문객 {sales_b.get('daily_visitors', 0):.0f} · 객단가 {sales_b.get('avg_price_per_customer', 0):,.0f}원")
            with b2:
                st.metric("고정비", f"{int(cost_b.get('fixed_costs', 0)):,.0f}원")
                vr = (cost_b.get("variable_cost_ratio") or 0) * 100
                st.caption(f"변동비율 {vr:.1f}%")
            with b3:
                st.metric("손익분기점", f"{int(profit_b.get('break_even_sales', 0)):,.0f}원")
                st.caption(f"예상이익 {int(profit_b.get('expected_profit', 0)):,.0f}원")
            with b4:
                if st.button("🔄 기준 구조 다시 불러오기", key="revenue_lab_reload_baseline", use_container_width=True):
                    try:
                        load_baseline_structure(store_id, current_year, current_month)
                        st.success("기준 구조를 다시 불러왔습니다.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"기준 구조 불러오기 실패: {e}")
        
        # ZONE C: 조작 레버 (2층 Levers) — 세션에 저장, 결과판 반영
        st.markdown("#### ⚙️ 조작 레버 (시뮬레이션)")
        lever_key = f"_revenue_levers_{store_id}_{current_year}_{current_month}"
        levers = st.session_state.get(lever_key) or {}
        safe_baseline = baseline or {}
        sales_b0 = safe_baseline.get("sales", {})
        def _default(name, default):
            return levers.get(name, default)
        daily_visitors = st.number_input("일 방문객 수", min_value=0, value=int(_default("daily_visitors", sales_b0.get("daily_visitors") or 0)) or 0, key="rev_daily_visitors")
        avg_price = st.number_input("객단가 (원)", min_value=0, value=int(_default("avg_price", sales_b0.get("avg_price_per_customer") or 0)) or 0, key="rev_avg_price")
        operating_days = st.number_input("영업일수", min_value=1, max_value=31, value=int(_default("operating_days", sales_b0.get("operating_days") or 30)) or 30, key="rev_operating_days")
        lever_fixed = st.number_input("고정비 (원)", min_value=0, value=int(_default("fixed_costs", fixed_costs or 0)) or 0, key="rev_fixed")
        vr_raw = _default("variable_ratio", variable_ratio or 0)
        vr_display = (float(vr_raw) * 100) if isinstance(vr_raw, (int, float)) else (float(variable_ratio or 0) * 100)
        lever_var_pct = st.number_input("변동비율 (%)", min_value=0.0, max_value=100.0, value=vr_display, step=1.0, key="rev_var_pct") / 100.0
        if st.button("레버 값으로 시뮬레이션 적용", key="rev_apply_levers"):
            st.session_state[lever_key] = {
                "daily_visitors": daily_visitors,
                "avg_price": avg_price,
                "operating_days": operating_days,
                "fixed_costs": lever_fixed,
                "variable_ratio": lever_var_pct,
            }
            st.rerun()
        
        # 레버 적용 시 사용할 값
        has_levers = bool(st.session_state.get(lever_key))
        use_fixed = lever_fixed if has_levers else (fixed_costs or 0)
        use_var = lever_var_pct if has_levers else (variable_ratio or 0)
        use_forecast = (daily_visitors * avg_price * operating_days) if (daily_visitors and avg_price and has_levers) else forecast_sales
        use_be = (use_fixed / (1 - use_var)) if (use_var < 1 and use_fixed) else (break_even or 0)
        
        # ZONE D: 결과판 (3층 Impact Board) — 살아남는 구조 판정 + 구조 맵
        st.markdown("#### 📊 결과판 (Impact Board)")
        if use_be > 0 and use_forecast > 0:
            if use_forecast >= use_be * 1.2:
                st.success("✅ **이 설계안은 살아남는 구조입니다.** 예상 매출이 손익분기점을 충분히 상회합니다.")
            elif use_forecast >= use_be:
                st.warning("⚠️ **주의가 필요합니다.** 예상 매출이 손익분기점을 넘지만 여유가 적습니다.")
            else:
                st.error("🔴 **이 설계안은 위험합니다.** 예상 매출이 손익분기점 미달입니다. 매출 증대 또는 비용 절감이 필요합니다.")
        else:
            st.info("고정비·변동비를 입력하고, 레버를 조정한 뒤 '레버 값으로 시뮬레이션 적용'을 누르면 결과판이 갱신됩니다.")
        
        def _render_revenue_structure_map():
            if use_fixed <= 0 or use_be <= 0:
                st.info("고정비와 변동비율을 입력하면 구조 맵이 표시됩니다.")
                return
            
            # 1) 매출 구간별 예상 이익 테이블 (레버 반영)
            st.markdown("#### 📊 매출 구간별 예상 이익")
            base_sales = use_be
            sales_ranges = []
            for offset in [-10000000, -5000000, 0, 5000000, 10000000, 15000000]:
                sales = base_sales + offset
                if sales > 0:
                    variable_cost = sales * use_var
                    total_cost = use_fixed + variable_cost
                    profit = sales - total_cost
                    profit_rate = (profit / sales * 100) if sales > 0 else 0
                    sales_ranges.append({
                        '매출': f"{int(sales):,}원",
                        '변동비': f"{int(variable_cost):,}원",
                        '고정비': f"{int(use_fixed):,}원",
                        '총비용': f"{int(total_cost):,}원",
                        '추정이익': f"{int(profit):,}원",
                        '이익률': f"{profit_rate:.1f}%"
                    })
            if sales_ranges:
                range_df = pd.DataFrame(sales_ranges)
                st.dataframe(range_df, use_container_width=True, hide_index=True)
            
            st.markdown("#### 📈 손익분기점 vs 예상 매출")
            if use_forecast > 0:
                comparison_data = pd.DataFrame({
                    '항목': ['손익분기점', '예상 매출'],
                    '금액': [use_be, use_forecast]
                })
                st.bar_chart(comparison_data.set_index('항목'))
                diff = use_forecast - use_be
                diff_pct = (diff / use_be * 100) if use_be > 0 else 0
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("손익분기점", f"{int(use_be):,}원")
                with col2:
                    st.metric("예상 매출", f"{int(use_forecast):,}원", delta=f"{diff_pct:.1f}%")
            else:
                st.info("예상 매출을 계산할 수 없습니다.")
        
        render_structure_map_container(
            content_func=_render_revenue_structure_map,
            empty_message="고정비와 변동비율을 입력하면 구조 맵이 표시됩니다.",
            empty_action_label="비용 구조 입력하기",
            empty_action_page="비용구조"
        )
        
        # ZONE C: Owner School
        school_cards = [
        {
            "title": "손익분기점은 생존선",
            "point1": "손익분기점은 목표가 아니라 생존선입니다",
            "point2": "손익분기점을 넘어야 비로소 이익이 나기 시작합니다"
        },
        {
            "title": "고정비는 시간을 먹고, 변동비는 매출을 먹는다",
            "point1": "고정비는 매출이 없어도 나가는 돈입니다",
            "point2": "변동비는 매출에 비례하므로 원가 관리가 중요합니다"
        },
        {
            "title": "목표 매출은 '희망'이 아니라 '구조'에서 나온다",
            "point1": "목표 매출은 손익분기점과 이익 목표에서 역산됩니다",
            "point2": "구조(고정비/변동비율)를 바꾸면 목표 매출도 달라집니다"
        },
        ]
        render_school_cards(school_cards)
    
    with execute_tab:
        # ZONE D: Design Tools
        render_design_tools_container(
            lambda: _render_revenue_structure_design_tools(store_id, current_year, current_month, fixed_costs, variable_ratio, break_even)
        )


def _render_revenue_structure_design_tools(store_id: str, year: int, month: int, fixed_costs: float, variable_ratio: float, break_even: float):
    """ZONE D: 수익 구조 설계 도구"""
    
    # 1) 구조 파라미터 편집 (읽기+이동 중심)
    st.markdown("#### ⚙️ 구조 파라미터")
    
    expense_df = load_expense_structure(year, month, store_id)
    
    if not expense_df.empty:
        # 고정비 요약
        fixed_categories = ['임차료', '인건비', '공과금']
        fixed_df = expense_df[expense_df['category'].isin(fixed_categories)]
        fixed_total = fixed_df['amount'].sum() if not fixed_df.empty else 0
        
        # 변동비 요약
        variable_categories = ['재료비', '부가세&카드수수료']
        variable_df = expense_df[expense_df['category'].isin(variable_categories)]
        variable_total = variable_df['amount'].sum() if not variable_df.empty else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("고정비 합계", f"{int(fixed_total):,}원")
        with col2:
            st.metric("변동비율", f"{variable_ratio * 100:.1f}%")
        with col3:
            st.metric("손익분기점", f"{int(break_even):,}원" if break_even > 0 else "-")
        
        st.info("💡 구조 파라미터를 수정하려면 아래 버튼을 클릭하세요.")
        
        if st.button("📋 비용 구조로 이동", key="goto_cost_structure", use_container_width=True, type="primary"):
            st.session_state["current_page"] = "비용구조"
            st.rerun()
    else:
        st.warning("비용 구조 데이터가 없습니다. 비용 구조를 먼저 입력하세요.")
        if st.button("📋 비용 구조로 이동", key="goto_cost_structure_empty", use_container_width=True, type="primary"):
            st.session_state["current_page"] = "비용구조"
            st.rerun()
    
    render_section_divider()
    
    # 2) 시나리오 시뮬레이터
    st.markdown("#### 🎯 시나리오 시뮬레이터")
    
    if fixed_costs > 0 and variable_ratio > 0:
        assumed_sales = st.number_input(
            "가정 매출 (원)",
            min_value=0,
            value=int(break_even) if break_even > 0 else 10000000,
            step=1000000,
            key="revenue_structure_simulator_sales"
        )
        
        if assumed_sales > 0:
            variable_cost = assumed_sales * variable_ratio
            total_cost = fixed_costs + variable_cost
            estimated_profit = assumed_sales - total_cost
            profit_rate = (estimated_profit / assumed_sales * 100) if assumed_sales > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("변동비", f"{int(variable_cost):,}원")
            with col2:
                st.metric("총비용", f"{int(total_cost):,}원")
            with col3:
                st.metric("추정이익", f"{int(estimated_profit):,}원", delta=f"{profit_rate:.1f}%")
            with col4:
                st.metric("이익률", f"{profit_rate:.1f}%")
            
            # 손익분기점과 비교
            if break_even > 0:
                if assumed_sales < break_even:
                    gap = break_even - assumed_sales
                    st.warning(f"⚠️ 손익분기점보다 {gap:,.0f}원 부족합니다. (손실 예상)")
                elif assumed_sales == break_even:
                    st.info("📊 손익분기점과 동일합니다. (이익 0원)")
                else:
                    excess = assumed_sales - break_even
                    st.success(f"✅ 손익분기점을 {excess:,.0f}원 초과합니다. (이익 예상)")
    else:
        st.info("고정비와 변동비율을 입력하면 시뮬레이터를 사용할 수 있습니다.")
