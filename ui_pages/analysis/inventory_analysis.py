"""
재고 분석 페이지 (고도화)
안전재고 vs 현재고 차이, 재고 회전율·가치, 예측·시뮬레이션, 내보내기 강화
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from src.ui_helpers import render_page_header, ui_flash_success, ui_flash_error, render_section_header
from src.storage_supabase import load_csv
from src.auth import get_current_store_id, get_supabase_client
from src.analytics import calculate_ingredient_usage, calculate_order_recommendation

logger = logging.getLogger(__name__)

# 공통 설정 적용
bootstrap(page_title="재고 분석")

# 재료 분류 옵션
INGREDIENT_CATEGORIES = ["채소", "육류", "해산물", "조미료", "기타"]

# 우선순위 색상
PRIORITY_COLORS = {
    "긴급": "#EF4444",
    "높음": "#F97316",
    "보통": "#F59E0B",
    "낮음": "#22C55E"
}

STATUS_COLORS = {
    "긴급": "#EF4444",
    "주의": "#F59E0B",
    "정상": "#22C55E"
}


def _safe_float(x, default=0.0):
    try:
        v = float(x)
        return v if not np.isnan(v) else default
    except (TypeError, ValueError):
        return default


def _normalize_usage_date(usage_df):
    """usage_df에 '날짜' 컬럼 확보 (date -> 날짜 등)"""
    if usage_df is None or usage_df.empty:
        return usage_df
    u = usage_df.copy()
    if "날짜" not in u.columns and "date" in u.columns:
        u["날짜"] = pd.to_datetime(u["date"])
    elif "날짜" in u.columns:
        u["날짜"] = pd.to_datetime(u["날짜"])
    return u


def _calculate_safety_stock_gap(inventory_df, usage_df=None):
    """
    안전재고 vs 현재고 차이.
    부족량 = 안전재고 - 현재고 (양수=부족, 음수=과다)
    출력: 재료명, 현재고, 안전재고, 부족량, 부족비율(%), 예상소진일, 위험도
    """
    if inventory_df is None or inventory_df.empty:
        return pd.DataFrame(columns=["재료명", "현재고", "안전재고", "부족량", "부족비율(%)", "예상소진일", "위험도"])
    out = []
    u = _normalize_usage_date(usage_df) if usage_df is not None else None
    daily_by_ing = {}
    if u is not None and not u.empty and "재료명" in u.columns and "총사용량" in u.columns:
        recent = u[u["날짜"] >= u["날짜"].max() - timedelta(days=7)]
        if not recent.empty:
            days = max(1, (recent["날짜"].max() - recent["날짜"].min()).days + 1)
            agg = recent.groupby("재료명")["총사용량"].sum()
            for k, v in agg.items():
                daily_by_ing[k] = v / days
    for _, row in inventory_df.iterrows():
        name = row.get("재료명") or row.get("name")
        if pd.isna(name) or name == "":
            continue
        cur = _safe_float(row.get("현재고", row.get("on_hand", 0)))
        safety = _safe_float(row.get("안전재고", row.get("safety_stock", 0)))
        gap = safety - cur
        pct = (gap / safety * 100) if safety > 0 else 0.0
        daily = daily_by_ing.get(name, 0)
        days_left = (cur / daily) if daily and daily > 0 else None
        if cur < safety * 0.5:
            risk = "긴급"
        elif cur < safety:
            risk = "주의"
        else:
            risk = "정상"
        out.append({
            "재료명": name,
            "현재고": cur,
            "안전재고": safety,
            "부족량": gap,
            "부족비율(%)": round(pct, 1),
            "예상소진일": round(days_left, 1) if days_left is not None else None,
            "위험도": risk,
        })
    df = pd.DataFrame(out)
    if df.empty:
        return df
    return df.sort_values("부족량", ascending=False)


def _calculate_inventory_turnover_df(inventory_df, usage_df, period_days=30):
    """기간 내 사용량/현재고 = 회전율. 출력: 재료명, 현재고, 총사용량, 재고회전율"""
    if inventory_df is None or inventory_df.empty or usage_df is None or usage_df.empty:
        return pd.DataFrame(columns=["재료명", "현재고", "총사용량", "재고회전율"])
    u = _normalize_usage_date(usage_df)
    if u.empty or "재료명" not in u.columns or "총사용량" not in u.columns:
        return pd.DataFrame(columns=["재료명", "현재고", "총사용량", "재고회전율"])
    cutoff = u["날짜"].max() - timedelta(days=period_days)
    recent = u[u["날짜"] >= cutoff]
    if recent.empty:
        return pd.DataFrame(columns=["재료명", "현재고", "총사용량", "재고회전율"])
    agg = recent.groupby("재료명")["총사용량"].sum().reset_index()
    agg.columns = ["재료명", "총사용량"]
    inv = inventory_df[["재료명", "현재고"]].copy()
    inv["현재고"] = inv["현재고"].apply(lambda x: _safe_float(x))
    m = pd.merge(agg, inv, on="재료명", how="inner")
    m["재고회전율"] = np.where(m["현재고"] > 0, m["총사용량"] / m["현재고"], 0.0)
    return m[["재료명", "현재고", "총사용량", "재고회전율"]].sort_values("재고회전율", ascending=False)


def _calculate_inventory_value(inventory_df, ingredient_df):
    """재료별 현재고 × 단가 = 재고가치. 출력: 재료명, 현재고, 단가, 재고가치"""
    if inventory_df is None or inventory_df.empty:
        return pd.DataFrame(columns=["재료명", "현재고", "단가", "재고가치"])
    ing = ingredient_df
    if ing is None or ing.empty or "재료명" not in ing.columns or "단가" not in ing.columns:
        inv = inventory_df.copy()
        inv["단가"] = 0.0
        inv["재고가치"] = 0.0
        inv["현재고"] = inv["현재고"].apply(lambda x: _safe_float(x))
        return inv[["재료명", "현재고", "단가", "재고가치"]]
    inv = inventory_df[["재료명", "현재고"]].copy()
    inv["현재고"] = inv["현재고"].apply(lambda x: _safe_float(x))
    price = ing.set_index("재료명")["단가"].to_dict()
    inv["단가"] = inv["재료명"].map(lambda n: _safe_float(price.get(n, 0)))
    inv["재고가치"] = inv["현재고"] * inv["단가"]
    return inv[["재료명", "현재고", "단가", "재고가치"]].sort_values("재고가치", ascending=False)


def _predict_inventory_usage(usage_df, days_for_avg=7, forecast_days=3, consider_trend=True):
    """예상소요량(일평균×예측일수), 예측신뢰도(%). 트렌드 반영 시 전반/후반 비교."""
    if usage_df is None or usage_df.empty:
        return pd.DataFrame(columns=["재료명", "예상소요량", "일평균", "예측신뢰도(%)"])
    u = _normalize_usage_date(usage_df)
    if u.empty or "재료명" not in u.columns or "총사용량" not in u.columns:
        return pd.DataFrame(columns=["재료명", "예상소요량", "일평균", "예측신뢰도(%)"])
    maxd = u["날짜"].max()
    cutoff = maxd - timedelta(days=min(days_for_avg * 2, 60))
    recent = u[u["날짜"] >= cutoff].copy()
    if recent.empty:
        return pd.DataFrame(columns=["재료명", "예상소요량", "일평균", "예측신뢰도(%)"])
    days_span = max(1, (recent["날짜"].max() - recent["날짜"].min()).days + 1)
    agg = recent.groupby("재료명")["총사용량"].sum().reset_index()
    agg.columns = ["재료명", "총사용량"]
    agg["일평균"] = agg["총사용량"] / days_span
    if consider_trend and len(recent) >= 4:
        mid = recent["날짜"].min() + (recent["날짜"].max() - recent["날짜"].min()) / 2
        first = recent[recent["날짜"] < mid].groupby("재료명")["총사용량"].sum()
        second = recent[recent["날짜"] >= mid].groupby("재료명")["총사용량"].sum()
        def adj(row):
            s1, s2 = first.get(row["재료명"], 0), second.get(row["재료명"], 0)
            if s1 and s2:
                t = max(-0.5, min(0.5, (s2 - s1) / s1))
                return row["일평균"] * (1 + 0.3 * t)
            return row["일평균"]
        agg["일평균"] = agg.apply(adj, axis=1)
    agg["예상소요량"] = (agg["일평균"] * forecast_days).round(2)
    agg["예측신뢰도(%)"] = 85.0
    return agg[["재료명", "예상소요량", "일평균", "예측신뢰도(%)"]]


def _simulate_safety_stock_change(ingredient_name, safety_stock_change_pct, inventory_df, usage_df, ingredient_df):
    """안전재고 변경 시뮬레이션. 변경 전/후 회전율·가치·품절위험."""
    res = {"before": {}, "after": {}, "delta": {}}
    inv = inventory_df[inventory_df["재료명"] == ingredient_name]
    if inv.empty:
        return res
    row = inv.iloc[0]
    cur = _safe_float(row.get("현재고", 0))
    safety = _safe_float(row.get("안전재고", 0))
    new_safety = max(0, safety * (1 + safety_stock_change_pct / 100))
    gap_before = safety - cur
    gap_after = new_safety - cur
    risk_before = "긴급" if cur < safety * 0.5 else ("주의" if cur < safety else "정상")
    risk_after = "긴급" if cur < new_safety * 0.5 else ("주의" if cur < new_safety else "정상")
    unit_price = 0.0
    if ingredient_df is not None and not ingredient_df.empty:
        ir = ingredient_df[ingredient_df["재료명"] == ingredient_name]
        if not ir.empty:
            unit_price = _safe_float(ir.iloc[0].get("단가", 0))
    val = cur * unit_price
    usage_30 = 0.0
    if usage_df is not None and not usage_df.empty:
        u = _normalize_usage_date(usage_df)
        if "재료명" in u.columns and "총사용량" in u.columns:
            cut = u["날짜"].max() - timedelta(days=30)
            su = u[(u["날짜"] >= cut) & (u["재료명"] == ingredient_name)]["총사용량"].sum()
            usage_30 = su
    turn_before = (usage_30 / cur) if cur > 0 else 0
    res["before"] = {"재고회전율": turn_before, "재고가치": val, "품절위험": risk_before, "안전재고": safety, "부족량": gap_before}
    res["after"] = {"재고회전율": turn_before, "재고가치": val, "품절위험": risk_after, "안전재고": new_safety, "부족량": gap_after}
    res["delta"] = {"재고가치": 0, "품절위험변화": risk_before != risk_after, "부족량변화": gap_after - gap_before}
    return res


def _get_ingredient_categories(store_id, ingredient_df):
    """재료 분류 조회 (DB에서)"""
    categories = {}
    if ingredient_df.empty:
        return categories
    
    supabase = get_supabase_client()
    if supabase:
        try:
            result = supabase.table("ingredients")\
                .select("name,category")\
                .eq("store_id", store_id)\
                .execute()
            
            if result.data:
                for row in result.data:
                    ingredient_name = row.get('name')
                    category_value = row.get('category')
                    if ingredient_name and category_value and category_value.strip():
                        categories[ingredient_name] = category_value.strip()
        except Exception as e:
            logger.warning(f"재료 분류 조회 실패: {e}")
    
    return categories


def _calculate_priority(current, safety):
    """우선순위 계산"""
    if current is None or safety is None or safety == 0:
        return "낮음"
    
    ratio = current / safety if safety > 0 else 1.0
    
    if ratio < 0.5:
        return "긴급"
    elif ratio < 0.8:
        return "높음"
    elif ratio < 1.0:
        return "보통"
    else:
        return "낮음"


def _calculate_status(current, safety):
    """상태 계산"""
    if current is None or safety is None:
        return "정상", "#22C55E"
    if current < safety * 0.5:
        return "긴급", "#EF4444"
    elif current < safety:
        return "주의", "#F59E0B"
    else:
        return "정상", "#22C55E"


def render_inventory_analysis():
    """재고 분석 페이지 렌더링"""
    render_page_header("📊 재고 분석", "📊")
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    # 데이터 로드
    ingredient_df = load_csv('ingredient_master.csv', store_id=store_id, 
                            default_columns=['재료명', '단위', '단가', '발주단위', '변환비율'])
    inventory_df = load_csv('inventory.csv', store_id=store_id, 
                           default_columns=['재료명', '현재고', '안전재고'])
    recipe_df = load_csv('recipes.csv', store_id=store_id, default_columns=['메뉴명', '재료명', '사용량'])
    daily_sales_df = load_csv('daily_sales_items.csv', store_id=store_id, 
                              default_columns=['날짜', '메뉴명', '판매수량'])
    
    if ingredient_df.empty:
        st.warning("먼저 재료를 등록해주세요.")
        if st.button("🧺 사용 재료 입력으로 이동", key="go_to_ingredient_input"):
            st.session_state["current_page"] = "재료 입력"
            st.rerun()
        return
    
    if inventory_df.empty:
        st.warning("먼저 재고 정보를 등록해주세요.")
        if st.button("📦 재고 입력으로 이동", key="go_to_inventory_input"):
            st.session_state["current_page"] = "재고 입력"
            st.rerun()
        return
    
    # 재료 분류 로드
    categories = _get_ingredient_categories(store_id, ingredient_df)
    
    # 사용량 계산
    usage_df = pd.DataFrame()
    if not daily_sales_df.empty and not recipe_df.empty:
        try:
            usage_df = calculate_ingredient_usage(daily_sales_df, recipe_df)
        except Exception as e:
            logger.warning(f"사용량 계산 실패: {e}")
    
    # 발주 추천 계산
    order_recommendation = pd.DataFrame()
    if not ingredient_df.empty and not inventory_df.empty:
        try:
            order_recommendation = calculate_order_recommendation(
                ingredient_df, inventory_df, usage_df, days_for_avg=7, forecast_days=3
            )
        except Exception as e:
            logger.warning(f"발주 추천 계산 실패: {e}")
    
    # 고도화용 데이터
    gap_df = _calculate_safety_stock_gap(inventory_df, usage_df)
    value_df = _calculate_inventory_value(inventory_df, ingredient_df)
    turnover_df = pd.DataFrame()
    if not usage_df.empty and not inventory_df.empty:
        turnover_df = _calculate_inventory_turnover_df(inventory_df, usage_df, period_days=30)
    predict_df = pd.DataFrame()
    if not usage_df.empty:
        predict_df = _predict_inventory_usage(usage_df, days_for_avg=7, forecast_days=3, consider_trend=True)
    
    # ============================================
    # ZONE A: 핵심 지표 (강화)
    # ============================================
    _render_zone_a_dashboard(ingredient_df, inventory_df, order_recommendation, value_df, turnover_df, gap_df)
    
    st.markdown("---")
    
    # ============================================
    # ZONE B: 안전재고 vs 현재고 차이 + 발주 필요량
    # ============================================
    _render_zone_b_gap_and_order(gap_df, order_recommendation, ingredient_df, inventory_df, categories)
    
    st.markdown("---")
    
    # ============================================
    # 필터 & 검색 (발주 필요량용)
    # ============================================
    filtered_order_df = _render_filters(order_recommendation, categories, ingredient_df, inventory_df)
    
    # ============================================
    # ZONE B-2: 발주 필요량 테이블 (기존)
    # ============================================
    _render_zone_b_order_analysis(filtered_order_df, ingredient_df, categories)
    
    st.markdown("---")
    
    # ============================================
    # ZONE C: 재고 회전율·가치 분석
    # ============================================
    _render_zone_c_turnover_value(ingredient_df, inventory_df, usage_df, value_df, turnover_df, categories)
    
    st.markdown("---")
    
    # ============================================
    # ZONE D: 재고 예측 강화
    # ============================================
    _render_zone_d_forecast(inventory_df, usage_df, predict_df)
    
    st.markdown("---")
    
    # ============================================
    # ZONE E: 재고 최적화 시뮬레이션
    # ============================================
    _render_zone_e_simulation(ingredient_df, inventory_df, usage_df, value_df, turnover_df)
    
    st.markdown("---")
    
    # ============================================
    # ZONE F: 사용량 트렌드
    # ============================================
    _render_zone_f_usage_trend(usage_df, inventory_df)
    
    st.markdown("---")
    
    # ============================================
    # ZONE G: 목표 vs 실제 회전율
    # ============================================
    _render_zone_g_target_vs_actual(turnover_df, inventory_df)
    
    st.markdown("---")
    
    # ============================================
    # ZONE H: 재고 최적화 액션
    # ============================================
    _render_zone_h_actions(gap_df, value_df, turnover_df, inventory_df)
    
    st.markdown("---")
    
    # ============================================
    # ZONE I: 재고 현황 분석 (기존 유지)
    # ============================================
    _render_zone_i_inventory_status(ingredient_df, inventory_df, usage_df, categories)
    
    st.markdown("---")
    
    # ============================================
    # ZONE J: 내보내기 & 액션 (강화)
    # ============================================
    _render_zone_j_export_actions(gap_df, value_df, turnover_df, order_recommendation, inventory_df, ingredient_df, store_id)


def _render_zone_a_dashboard(ingredient_df, inventory_df, order_recommendation, value_df, turnover_df, gap_df):
    """ZONE A: 핵심 지표 (총 재고가치, 평균 회전율, 품절위험/과다재고 수 등)"""
    render_section_header("📊 재고 현황 대시보드", "📊")
    
    order_needed_count = len(order_recommendation) if not order_recommendation.empty else 0
    urgent_count = 0
    warning_count = 0
    normal_count = 0
    excess_count = 0
    
    if not inventory_df.empty:
        for _, row in inventory_df.iterrows():
            current = _safe_float(row.get("현재고", 0))
            safety = _safe_float(row.get("안전재고", 0))
            if safety > 0:
                if current < safety * 0.5:
                    urgent_count += 1
                elif current < safety:
                    warning_count += 1
                else:
                    normal_count += 1
                if current > safety * 2:
                    excess_count += 1
    
    total_value = 0.0
    if value_df is not None and not value_df.empty and "재고가치" in value_df.columns:
        total_value = value_df["재고가치"].sum()
    
    avg_turnover = None
    if turnover_df is not None and not turnover_df.empty and "재고회전율" in turnover_df.columns:
        avg_turnover = turnover_df["재고회전율"].mean()
    
    total_expected_cost = 0.0
    if not order_recommendation.empty and "예상금액" in order_recommendation.columns:
        total_expected_cost = order_recommendation["예상금액"].sum()
    
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.metric("발주 필요", f"{order_needed_count}개", delta=f"-{order_needed_count}" if order_needed_count > 0 else None)
    with c2:
        st.metric("긴급 발주", f"{urgent_count}개", delta=f"-{urgent_count}" if urgent_count > 0 else None)
    with c3:
        st.metric("주의 재고", f"{warning_count}개")
    with c4:
        st.metric("정상 재고", f"{normal_count}개")
    with c5:
        st.metric("총 재고 가치", f"{int(total_value):,}원" if total_value else "0원")
    with c6:
        t = f"{avg_turnover:.2f}" if avg_turnover is not None else "-"
        st.metric("평균 재고 회전율", t)
    
    c7, c8 = st.columns(2)
    with c7:
        st.metric("품절 위험 재료", f"{urgent_count}개")
    with c8:
        st.metric("과다재고 재료", f"{excess_count}개")
    
    st.markdown("#### 예상 발주 비용")
    st.metric("총 예상 발주 비용", f"{int(total_expected_cost):,}원" if total_expected_cost else "0원")
    
    alerts = []
    if urgent_count > 0:
        alerts.append(f"⚠️ 긴급 발주 필요 재고가 {urgent_count}개 있습니다.")
    if order_needed_count > 0:
        alerts.append(f"ℹ️ 발주 필요 재고가 {order_needed_count}개 있습니다.")
    if alerts:
        for a in alerts:
            st.warning(a)


def _render_zone_b_gap_and_order(gap_df, order_recommendation, ingredient_df, inventory_df, categories):
    """ZONE B: 안전재고 vs 현재고 차이 분석 (테이블, 부족량/과다재고 TOP10)"""
    render_section_header("📐 안전재고 vs 현재고 차이 분석", "📐")
    
    if gap_df is None or gap_df.empty:
        st.info("재고 데이터가 없어 안전재고 대비 차이를 계산할 수 없습니다.")
        return
    
    search = st.text_input("🔍 재료명 검색 (차이 분석)", key="gap_search", placeholder="재료명으로 필터...")
    risk_filter = st.selectbox("위험도", ["전체", "긴급", "주의", "정상"], key="gap_risk")
    
    g = gap_df.copy()
    if search and search.strip():
        g = g[g["재료명"].str.contains(search, case=False, na=False)]
    if risk_filter != "전체":
        g = g[g["위험도"] == risk_filter]
    
    st.markdown("##### 안전재고 vs 현재고 비교")
    display_cols = ["재료명", "현재고", "안전재고", "부족량", "부족비율(%)", "예상소진일", "위험도"]
    cfg = {
        "재료명": st.column_config.TextColumn("재료명", width="medium"),
        "현재고": st.column_config.NumberColumn("현재고", format="%.2f"),
        "안전재고": st.column_config.NumberColumn("안전재고", format="%.2f"),
        "부족량": st.column_config.NumberColumn("부족량", format="%.2f"),
        "부족비율(%)": st.column_config.NumberColumn("부족비율(%)", format="%.1f"),
        "예상소진일": st.column_config.NumberColumn("예상소진일", format="%.1f"),
        "위험도": st.column_config.TextColumn("위험도", width="small"),
    }
    st.dataframe(g[display_cols], use_container_width=True, hide_index=True, column_config=cfg)
    
    shortage = gap_df[gap_df["부족량"] > 0].nlargest(10, "부족량")
    excess = gap_df[gap_df["부족량"] < 0].nsmallest(10, "부족량")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### 부족량 TOP 10")
        if shortage.empty:
            st.caption("부족 재고 없음")
        else:
            st.dataframe(shortage[["재료명", "현재고", "안전재고", "부족량", "위험도"]], use_container_width=True, hide_index=True)
    with col2:
        st.markdown("##### 과다재고 TOP 10")
        if excess.empty:
            st.caption("과다재고 없음")
        else:
            excess_d = excess.copy()
            excess_d["과다량"] = -excess_d["부족량"]
            st.dataframe(excess_d[["재료명", "현재고", "안전재고", "과다량"]], use_container_width=True, hide_index=True)
    
    st.caption("인벤토리 시점별 비교는 재고 이력 데이터가 없어 현재 제공하지 않습니다. (발주/입고 자동화 시 확장 예정)")


def _render_filters(order_recommendation, categories, ingredient_df, inventory_df):
    """필터 & 검색"""
    if order_recommendation.empty:
        return pd.DataFrame()
    
    col1, col2, col3, col4 = st.columns([2, 2, 2, 4])
    
    with col1:
        category_filter = st.multiselect("재료 분류", options=["전체"] + INGREDIENT_CATEGORIES + ["미지정"], 
                                         default=["전체"], key="inventory_analysis_filter_category")
    with col2:
        priority_filter = st.selectbox("우선순위", options=["전체", "긴급", "높음", "보통", "낮음"], 
                                      key="inventory_analysis_filter_priority")
    with col3:
        status_filter = st.selectbox("상태", options=["전체", "긴급", "주의", "정상"], 
                                     key="inventory_analysis_filter_status")
    with col4:
        search_term = st.text_input("🔍 재료명 검색", key="inventory_analysis_search", placeholder="재료명으로 검색...")
    
    # 필터링 적용
    filtered_df = order_recommendation.copy()
    
    # 재료 분류 필터
    if "전체" not in category_filter:
        def category_match(name):
            cat = categories.get(name, "미지정")
            if "미지정" in category_filter:
                return cat == "미지정" or cat not in INGREDIENT_CATEGORIES
            return cat in category_filter
        filtered_df = filtered_df[filtered_df['재료명'].apply(category_match)]
    
    # 우선순위 필터
    if priority_filter != "전체":
        # 재고 정보와 조인하여 우선순위 계산
        merged_df = pd.merge(
            filtered_df[['재료명']],
            inventory_df[['재료명', '현재고', '안전재고']],
            on='재료명',
            how='left'
        )
        merged_df['우선순위'] = merged_df.apply(
            lambda row: _calculate_priority(
                float(row.get('현재고', 0)) if row.get('현재고') else 0,
                float(row.get('안전재고', 0)) if row.get('안전재고') else 0
            ),
            axis=1
        )
        filtered_df = filtered_df[filtered_df['재료명'].isin(
            merged_df[merged_df['우선순위'] == priority_filter]['재료명']
        )]
    
    # 상태 필터
    if status_filter != "전체":
        merged_df = pd.merge(
            filtered_df[['재료명']],
            inventory_df[['재료명', '현재고', '안전재고']],
            on='재료명',
            how='left'
        )
        merged_df['상태'] = merged_df.apply(
            lambda row: _calculate_status(
                float(row.get('현재고', 0)) if row.get('현재고') else 0,
                float(row.get('안전재고', 0)) if row.get('안전재고') else 0
            )[0],
            axis=1
        )
        filtered_df = filtered_df[filtered_df['재료명'].isin(
            merged_df[merged_df['상태'] == status_filter]['재료명']
        )]
    
    # 검색 필터
    if search_term and search_term.strip():
        filtered_df = filtered_df[filtered_df['재료명'].str.contains(search_term, case=False, na=False)]
    
    return filtered_df


def _render_zone_b_order_analysis(order_df, ingredient_df, categories):
    """ZONE B: 발주 필요량 분석 (핵심)"""
    render_section_header("🛒 발주 필요량 분석", "🛒")
    
    if order_df.empty:
        st.info("발주 필요 재고가 없습니다. 모든 재고가 정상입니다.")
        return
    
    # 재고 정보와 조인하여 우선순위 및 상태 계산
    inventory_df = load_csv('inventory.csv', store_id=get_current_store_id(), 
                           default_columns=['재료명', '현재고', '안전재고'])
    
    # 발주 단위 변환을 위한 재료 정보 매핑
    ingredient_info_map = {}
    for _, row in ingredient_df.iterrows():
        ingredient_name = row['재료명']
        unit = row.get('단위', '')
        order_unit = row.get('발주단위', unit)
        conversion_rate = float(row.get('변환비율', 1.0)) if row.get('변환비율') else 1.0
        ingredient_info_map[ingredient_name] = {
            'unit': unit,
            'order_unit': order_unit,
            'conversion_rate': conversion_rate
        }
    
    # 분석 결과 데이터프레임 준비
    analysis_data = []
    
    for _, row in order_df.iterrows():
        ingredient_name = row['재료명']
        current_base = float(row.get('현재고', 0))
        safety_base = float(row.get('안전재고', 0))
        order_amount_base = float(row.get('발주필요량', 0))  # 기본 단위
        expected_usage_base = float(row.get('예상소요량', 0)) if '예상소요량' in row else 0  # 기본 단위
        expected_cost = float(row.get('예상금액', 0))
        
        # 발주 단위로 변환
        info = ingredient_info_map.get(ingredient_name, {'order_unit': '', 'conversion_rate': 1.0})
        conversion_rate = info['conversion_rate']
        order_unit = info['order_unit']
        
        current_order = current_base / conversion_rate if conversion_rate > 0 else current_base
        safety_order = safety_base / conversion_rate if conversion_rate > 0 else safety_base
        shortage_order = max(0, safety_order - current_order)
        expected_usage_order = expected_usage_base / conversion_rate if conversion_rate > 0 else expected_usage_base
        order_amount_order = order_amount_base / conversion_rate if conversion_rate > 0 else order_amount_base
        
        # 우선순위 및 상태 계산
        priority = _calculate_priority(current_base, safety_base)
        status_text, _ = _calculate_status(current_base, safety_base)
        
        category = categories.get(ingredient_name, "미지정")
        
        analysis_data.append({
            '재료명': ingredient_name,
            '재료분류': category if category in INGREDIENT_CATEGORIES else "미지정",
            '단위': order_unit,
            '현재고': current_order,
            '안전재고': safety_order,
            '부족량': shortage_order,
            '예상소요량': expected_usage_order,
            '발주필요량': order_amount_order,
            '예상금액': expected_cost,
            '우선순위': priority,
            '상태': status_text
        })
    
    analysis_df = pd.DataFrame(analysis_data)
    
    # 정렬 (우선순위 우선, 발주 필요량 내림차순)
    priority_order = {"긴급": 0, "높음": 1, "보통": 2, "낮음": 3}
    analysis_df['우선순위_순서'] = analysis_df['우선순위'].map(priority_order)
    analysis_df = analysis_df.sort_values(['우선순위_순서', '발주필요량'], ascending=[True, False])
    analysis_df = analysis_df.drop('우선순위_순서', axis=1)
    
    # 테이블 표시
    st.dataframe(
        analysis_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            '재료명': st.column_config.TextColumn('재료명', width="medium"),
            '재료분류': st.column_config.TextColumn('재료분류', width="small"),
            '단위': st.column_config.TextColumn('단위', width="small"),
            '현재고': st.column_config.NumberColumn('현재고', format="%.2f", width="small"),
            '안전재고': st.column_config.NumberColumn('안전재고', format="%.2f", width="small"),
            '부족량': st.column_config.NumberColumn('부족량', format="%.2f", width="small"),
            '예상소요량': st.column_config.NumberColumn('예상소요량', format="%.2f", width="small"),
            '발주필요량': st.column_config.NumberColumn('발주필요량', format="%.2f", width="small"),
            '예상금액': st.column_config.NumberColumn('예상금액', format="%,.0f", width="medium"),
            '우선순위': st.column_config.TextColumn('우선순위', width="small"),
            '상태': st.column_config.TextColumn('상태', width="small"),
        }
    )


def _render_zone_c_turnover_value(ingredient_df, inventory_df, usage_df, value_df, turnover_df, categories):
    """ZONE C: 재고 회전율·가치 분석"""
    render_section_header("📈 재고 회전율·가치 분석", "📈")
    
    if inventory_df.empty:
        st.info("재고 정보가 없습니다.")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### 재고 회전율")
        if turnover_df is not None and not turnover_df.empty:
            avg = turnover_df["재고회전율"].mean()
            hi = (turnover_df["재고회전율"] > 1.0).sum()
            mid = ((turnover_df["재고회전율"] >= 0.5) & (turnover_df["재고회전율"] <= 1.0)).sum()
            lo = (turnover_df["재고회전율"] < 0.5).sum()
            st.metric("평균 회전율", f"{avg:.2f}")
            st.caption(f"높음(>1.0): {hi}개 / 보통(0.5~1.0): {mid}개 / 낮음(<0.5): {lo}개")
            top10 = turnover_df.nlargest(10, "재고회전율")[["재료명", "재고회전율", "총사용량"]]
            st.dataframe(top10, use_container_width=True, hide_index=True)
            st.markdown("##### 회전율 BOTTOM 10")
            bot10 = turnover_df.nsmallest(10, "재고회전율")[["재료명", "재고회전율", "총사용량"]]
            st.dataframe(bot10, use_container_width=True, hide_index=True)
        else:
            st.info("사용량 데이터가 없어 회전율을 계산할 수 없습니다.")
    with col2:
        st.markdown("##### 재고 가치")
        if value_df is not None and not value_df.empty:
            total = value_df["재고가치"].sum()
            st.metric("총 재고 가치", f"{int(total):,}원")
            top10v = value_df.nlargest(10, "재고가치")[["재료명", "현재고", "단가", "재고가치"]]
            st.dataframe(top10v, use_container_width=True, hide_index=True, column_config={
                "재고가치": st.column_config.NumberColumn("재고가치", format="%,.0f"),
                "단가": st.column_config.NumberColumn("단가", format="%,.0f"),
            })
        else:
            st.info("재료 단가 정보가 없어 재고 가치를 계산할 수 없습니다.")
    
    if turnover_df is not None and not turnover_df.empty and value_df is not None and not value_df.empty:
        m = pd.merge(turnover_df[["재료명", "재고회전율"]], value_df[["재료명", "재고가치"]], on="재료명", how="inner")
        if not m.empty:
            st.markdown("##### 재고 회전율 vs 가치 (상위 20)")
            m = m.nlargest(20, "재고가치")
            st.dataframe(m, use_container_width=True, hide_index=True, column_config={"재고가치": st.column_config.NumberColumn("재고가치", format="%,.0f")})


def _render_zone_d_forecast(inventory_df, usage_df, predict_df):
    """ZONE D: 재고 예측 강화"""
    render_section_header("🔮 재고 예측", "🔮")
    
    if usage_df is None or usage_df.empty:
        st.info("사용량 데이터가 없어 예측할 수 없습니다. 일일 판매·레시피를 입력해 주세요.")
        return
    
    if predict_df is None or predict_df.empty:
        st.info("예상 소요량을 계산할 수 없습니다.")
        return
    
    days = st.selectbox("예측 기간 (일)", [3, 7, 14], key="forecast_days")
    pred = _predict_inventory_usage(usage_df, days_for_avg=7, forecast_days=days, consider_trend=True)
    if pred.empty:
        st.info("예측 결과가 없습니다.")
        return
    
    if not inventory_df.empty and "재료명" in inventory_df.columns and "현재고" in inventory_df.columns:
        inv = inventory_df.set_index("재료명")["현재고"]
        pred["현재고"] = pred["재료명"].map(lambda x: _safe_float(inv.get(x, 0)))
        pred["예상소진일"] = np.where(pred["일평균"] > 0, (pred["현재고"] / pred["일평균"]).round(1), None)
    
    st.dataframe(pred, use_container_width=True, hide_index=True)
    st.caption("예상소요량 = 최근 7일 기준 일평균 사용량 × 예측일수 (트렌드 반영). 예상소진일 = 현재고 ÷ 일평균.")


def _render_zone_e_simulation(ingredient_df, inventory_df, usage_df, value_df, turnover_df):
    """ZONE E: 안전재고 조정 시뮬레이션"""
    render_section_header("🎛️ 재고 최적화 시뮬레이션", "🎛️")
    
    if inventory_df.empty:
        st.info("재고 정보가 없습니다.")
        return
    
    names = inventory_df["재료명"].tolist()
    sel = st.selectbox("재료 선택", names, key="sim_ingredient")
    pct = st.slider("안전재고 변경 (%)", -50, 100, 0, 10, key="sim_pct")
    
    sim = _simulate_safety_stock_change(sel, pct, inventory_df, usage_df, ingredient_df)
    b, a = sim.get("before", {}), sim.get("after", {})
    st.markdown("##### 변경 전")
    st.json({"안전재고": b.get("안전재고"), "부족량": b.get("부족량"), "품절위험": b.get("품절위험")})
    st.markdown("##### 변경 후")
    st.json({"안전재고": a.get("안전재고"), "부족량": a.get("부족량"), "품절위험": a.get("품절위험")})
    delta = sim.get("delta", {})
    if delta.get("품절위험변화"):
        st.warning("품절 위험 등급이 변경됩니다.")


def _render_zone_f_usage_trend(usage_df, inventory_df):
    """ZONE F: 사용량 트렌드"""
    render_section_header("📉 사용량 트렌드", "📉")
    
    if usage_df is None or usage_df.empty:
        st.info("사용량 데이터가 없습니다.")
        return
    
    u = _normalize_usage_date(usage_df)
    if u.empty or "날짜" not in u.columns or "재료명" not in u.columns or "총사용량" not in u.columns:
        st.info("사용량 데이터 형식이 맞지 않습니다.")
        return
    
    u["년월"] = u["날짜"].dt.to_period("M").astype(str)
    monthly = u.groupby(["년월", "재료명"])["총사용량"].sum().reset_index()
    piv = monthly.pivot(index="재료명", columns="년월", values="총사용량").fillna(0)
    if piv.empty or piv.shape[1] < 2:
        st.caption("월별 데이터가 2개 이상 필요합니다.")
        return
    
    cols = sorted(piv.columns)
    piv = piv[cols]
    chg = (piv[cols[-1]] - piv[cols[-2]]) / piv[cols[-2]].replace(0, np.nan)
    chg = chg.dropna().sort_values(ascending=False)
    up = chg[chg > 0].head(10)
    dn = chg[chg < 0].head(10)
    
    st.markdown("##### 전월 대비 사용량 증감 (TOP 10)")
    c1, c2 = st.columns(2)
    with c1:
        st.write("증가")
        if not up.empty:
            st.dataframe(up.round(2).to_frame("변화율"), use_container_width=True, hide_index=True)
    with c2:
        st.write("감소")
        if not dn.empty:
            st.dataframe(dn.round(2).to_frame("변화율"), use_container_width=True, hide_index=True)
    
    sel_ing = st.selectbox("재료별 월별 추이", list(piv.index)[:50], key="trend_ing")
    row = piv.loc[sel_ing]
    chart_df = pd.DataFrame({"월": row.index, "사용량": row.values})
    st.line_chart(chart_df.set_index("월"))


def _render_zone_g_target_vs_actual(turnover_df, inventory_df):
    """ZONE G: 목표 vs 실제 재고 회전율"""
    render_section_header("🎯 목표 vs 실제 회전율", "🎯")
    
    if turnover_df is None or turnover_df.empty:
        st.info("회전율 데이터가 없습니다.")
        return
    
    target = st.number_input("목표 회전율 (기본 1.0)", value=1.0, min_value=0.1, step=0.1, key="target_turnover")
    t = turnover_df.copy()
    t["목표"] = target
    t["차이"] = t["재고회전율"] - target
    t["달성"] = t["재고회전율"] >= target
    achieved = t["달성"].sum()
    total = len(t)
    st.metric("목표 달성률", f"{100 * achieved / total:.0f}%" if total else "0%", f"{achieved}/{total}개")
    miss = t[~t["달성"]].sort_values("차이")[["재료명", "재고회전율", "목표", "차이"]]
    st.markdown("##### 목표 미달 재료")
    st.dataframe(miss, use_container_width=True, hide_index=True)


def _render_zone_h_actions(gap_df, value_df, turnover_df, inventory_df):
    """ZONE H: 재고 최적화 액션"""
    render_section_header("💡 재고 최적화 액션", "💡")
    
    actions = []
    if gap_df is not None and not gap_df.empty:
        urgent = gap_df[gap_df["위험도"] == "긴급"]
        if not urgent.empty:
            actions.append(f"⚠️ **품절 위험** {len(urgent)}개: {', '.join(urgent['재료명'].head(5).tolist())}{' …' if len(urgent) > 5 else ''} → 안전재고 확보 또는 발주 검토")
        excess = gap_df[gap_df["부족량"] < 0].nsmallest(5, "부족량")
        if not excess.empty:
            actions.append(f"📦 **과다재고** 우선 점검: {', '.join(excess['재료명'].tolist())} → 안전재고 조정 검토")
    
    if turnover_df is not None and not turnover_df.empty and value_df is not None and not value_df.empty:
        m = pd.merge(turnover_df, value_df[["재료명", "재고가치"]], on="재료명", how="inner")
        low_val = m[(m["재고회전율"] < 0.5) & (m["재고가치"] > 0)].nlargest(5, "재고가치")
        if not low_val.empty:
            actions.append(f"🔄 **저회전·고가치** {len(low_val)}개 → 재고 최적화 우선: {', '.join(low_val['재료명'].tolist())}")
    
    if not actions:
        st.info("현재 권장 액션이 없습니다.")
        return
    for a in actions:
        st.markdown(f"- {a}")


def _render_zone_i_inventory_status(ingredient_df, inventory_df, usage_df, categories):
    """ZONE I: 재고 현황 분석 (기존)"""
    render_section_header("📊 재고 현황 분석", "📊")
    
    if inventory_df.empty:
        st.info("재고 정보가 없습니다.")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 재고 상태 분포")
        status_counts = {"정상": 0, "주의": 0, "긴급": 0}
        for _, row in inventory_df.iterrows():
            current = _safe_float(row.get("현재고", 0))
            safety = _safe_float(row.get("안전재고", 0))
            status, _ = _calculate_status(current, safety)
            status_counts[status] = status_counts.get(status, 0) + 1
        if sum(status_counts.values()) > 0:
            chart_data = pd.DataFrame({"상태": list(status_counts.keys()), "개수": list(status_counts.values())})
            st.bar_chart(chart_data.set_index("상태"))
    with col2:
        st.markdown("### 재고 회전율 TOP 10")
        if not usage_df.empty and not inventory_df.empty:
            u = _normalize_usage_date(usage_df)
            if not u.empty:
                max_date = u["날짜"].max()
                recent = u[u["날짜"] >= max_date - timedelta(days=7)]
                if not recent.empty:
                    daily_avg = recent.groupby("재료명")["총사용량"].sum() / 7
                    daily_avg = daily_avg.reset_index()
                    daily_avg.columns = ["재료명", "평균사용량"]
                    merged = pd.merge(daily_avg, inventory_df[["재료명", "현재고"]], on="재료명", how="inner")
                    merged["회전율"] = merged.apply(lambda r: r["평균사용량"] / r["현재고"] if r["현재고"] > 0 else 0, axis=1)
                    top10 = merged.nlargest(10, "회전율")[["재료명", "회전율"]]
                    st.dataframe(top10, use_container_width=True, hide_index=True)
    
    st.markdown("### 과다재고 경고")
    excess_inventory = []
    for _, row in inventory_df.iterrows():
        current = _safe_float(row.get("현재고", 0))
        safety = _safe_float(row.get("안전재고", 0))
        if safety > 0 and current > safety * 2:
            excess_inventory.append({"재료명": row["재료명"], "현재고": current, "안전재고": safety, "비율": current / safety})
    if excess_inventory:
        st.dataframe(pd.DataFrame(excess_inventory), use_container_width=True, hide_index=True)
    else:
        st.info("과다재고 재료가 없습니다.")


def _render_zone_j_export_actions(gap_df, value_df, turnover_df, order_df, inventory_df, ingredient_df, store_id):
    """ZONE J: 내보내기 & 액션 (강화)"""
    render_section_header("💾 내보내기 & 액션", "💾")
    
    ts = datetime.now().strftime("%Y%m%d")
    
    def csv_download(df, cols, fname, label, key):
        if df is None or df.empty or not all(c in df.columns for c in cols):
            return
        sub = df[[c for c in cols if c in df.columns]]
        csv = sub.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(label=label, data=csv, file_name=fname, mime="text/csv", key=key)
    
    gap_cols = ["재료명", "현재고", "안전재고", "부족량", "부족비율(%)", "예상소진일", "위험도"]
    if gap_df is not None and not gap_df.empty:
        csv_download(gap_df, gap_cols, f"안전재고대비차이_{ts}.csv", "📥 안전재고 대비 차이 (CSV)", "export_gap")
    
    if value_df is not None and not value_df.empty and turnover_df is not None and not turnover_df.empty:
        m = pd.merge(value_df, turnover_df[["재료명", "재고회전율"]], on="재료명", how="left")
        status = []
        for _, r in m.iterrows():
            n = inventory_df[inventory_df["재료명"] == r["재료명"]]
            cur = _safe_float(n.iloc[0]["현재고"]) if not n.empty else 0
            safe = _safe_float(n.iloc[0]["안전재고"]) if not n.empty else 0
            s, _ = _calculate_status(cur, safe)
            status.append(s)
        m["상태"] = status
        csv_download(m, ["재료명", "현재고", "단가", "재고가치", "재고회전율", "상태"], f"재고현황종합_{ts}.csv", "📥 재고 현황 종합 (CSV)", "export_value")
    
    if gap_df is not None and not gap_df.empty:
        urgent = gap_df[gap_df["위험도"] == "긴급"]
        if not urgent.empty:
            csv_download(urgent, gap_cols, f"품절위험목록_{ts}.csv", "📥 품절 위험 목록 (CSV)", "export_urgent")
        excess = gap_df[gap_df["부족량"] < 0]
        if not excess.empty:
            ex = excess.copy()
            ex["과다량"] = -ex["부족량"]
            csv_download(ex, ["재료명", "현재고", "안전재고", "과다량"], f"과다재고목록_{ts}.csv", "📥 과다재고 목록 (CSV)", "export_excess")
    
    if not order_df.empty and "발주필요량" in order_df.columns and "예상금액" in order_df.columns:
        csv = order_df[["재료명", "발주필요량", "예상금액"]].to_csv(index=False, encoding="utf-8-sig")
        st.download_button("📥 발주 필요량 (CSV)", data=csv, file_name=f"발주필요량_{ts}.csv", mime="text/csv", key="export_order")
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📦 재고 입력으로 이동", key="go_to_inventory_input", use_container_width=True):
            st.session_state["current_page"] = "재고 입력"
            st.rerun()
    with col2:
        if st.button("🧺 사용 재료 입력으로 이동", key="go_to_ingredient_input", use_container_width=True):
            st.session_state["current_page"] = "재료 입력"
            st.rerun()
