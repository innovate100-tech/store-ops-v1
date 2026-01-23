"""
매출 하락 원인 찾기 (원클릭 플로우)
3단 구조: 언제부터 떨어졌나? → 무엇이 떨어졌나? → 어디를 고치나?
"""
from __future__ import annotations

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from typing import Dict, List, Tuple, Optional

from src.bootstrap import bootstrap
from src.ui_helpers import render_page_header
from src.storage_supabase import (
    load_best_available_daily_sales,
    load_csv,
)
from src.auth import get_current_store_id, is_dev_mode
from ui_pages.design_lab.design_insights import get_design_insights

# 공통 설정 적용
bootstrap(page_title="매출 하락 원인 찾기")


def render_sales_drop_oneclick():
    """매출 하락 원인 찾기 페이지 렌더링"""
    render_page_header("📉 매출 하락 원인 찾기", "📉")
    
    st.markdown("**3분 안에 원인을 좁히고, 고칠 곳으로 바로 이동합니다.**")
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    # 공통 입력 (상단 한 줄)
    col1, col2, col3 = st.columns([2, 2, 3])
    with col1:
        period_days = st.selectbox("기간 선택", [7, 14, 30], index=1, key="period_days")
    with col2:
        compare_mode = st.selectbox("비교 방식", ["전주 대비", "전월 대비"], index=0, key="compare_mode")
    with col3:
        pass  # 여백
    
    with st.expander("고급 옵션", expanded=False):
        base_date = st.date_input("기준 날짜", value=date.today(), key="base_date")
    
    if 'base_date' not in locals():
        base_date = date.today()
    
    # 데이터 로드
    kst = ZoneInfo("Asia/Seoul")
    today = datetime.now(kst).date()
    if base_date > today:
        base_date = today
    
    start_date = (base_date - timedelta(days=period_days + 30)).isoformat()  # 비교 구간 포함
    end_date = base_date.isoformat()
    
    # STEP 1: 언제부터 떨어졌나?
    st.markdown("---")
    st.markdown("### 1️⃣ 언제부터 떨어졌나?")
    
    step1_result = _analyze_when_dropped(store_id, period_days, compare_mode, base_date, start_date, end_date)
    if not step1_result:
        st.warning("데이터가 부족합니다. 매출 데이터를 입력해주세요.")
        if st.button("📋 오늘 입력(마감/보정) 하러가기", key="goto_input"):
            st.session_state.current_page = "점장 마감"
            st.rerun()
        return
    
    _render_step1_result(step1_result, compare_mode)
    
    # STEP 2: 무엇이 떨어졌나?
    st.markdown("---")
    st.markdown("### 2️⃣ 무엇이 떨어졌나?")
    
    step2_result = _analyze_what_dropped(store_id, step1_result, period_days, compare_mode, base_date)
    if not step2_result:
        st.warning("판매량/방문자 데이터가 부족합니다.")
        return
    
    _render_step2_result(step2_result)
    
    # STEP 3: 어디를 고치나?
    _suggest_fixes(store_id, step1_result, step2_result)
    
    # 오늘의 전략 카드 추가 (결과 하단)
    try:
        from ui_pages.analysis.strategy_engine import pick_primary_strategy
        from ui_pages.common.today_strategy_card import render_today_strategy_card
        
        strategy = pick_primary_strategy(store_id, ref_date=base_date, window_days=period_days)
        if strategy:
            render_today_strategy_card(strategy, location="sales_drop_flow")
    except Exception as e:
        if is_dev_mode():
            st.error(f"오늘의 전략 카드 렌더링 오류: {e}")
        # 에러 발생해도 계속 진행


@st.cache_data(ttl=300)
def _analyze_when_dropped(
    store_id: str, 
    period_days: int, 
    compare_mode: str, 
    base_date: date,
    start_date: str,
    end_date: str
) -> Optional[Dict]:
    """STEP 1: 언제부터 떨어졌나?"""
    try:
        # 매출 데이터 로드 (SSOT best_available)
        sales_df = load_best_available_daily_sales(store_id=store_id, start_date=start_date, end_date=end_date)
        if sales_df.empty:
            return None
        
        sales_df['date'] = pd.to_datetime(sales_df['date']).dt.date
        sales_df = sales_df.sort_values('date')
        
        # 기간 구분
        recent_end = base_date
        recent_start = base_date - timedelta(days=period_days - 1)
        
        if compare_mode == "전주 대비":
            # 전주: 7일 shift
            compare_start = recent_start - timedelta(days=7)
            compare_end = recent_end - timedelta(days=7)
        else:  # 전월 대비
            # 전월: 28일 shift (간단화)
            compare_start = recent_start - timedelta(days=28)
            compare_end = recent_end - timedelta(days=28)
        
        # 최근 구간
        recent_df = sales_df[
            (sales_df['date'] >= recent_start) & 
            (sales_df['date'] <= recent_end)
        ].copy()
        
        # 비교 구간
        compare_df = sales_df[
            (sales_df['date'] >= compare_start) & 
            (sales_df['date'] <= compare_end)
        ].copy()
        
        if recent_df.empty or compare_df.empty:
            return None
        
        # 평균 매출 계산
        recent_avg = recent_df['total_sales'].mean() if 'total_sales' in recent_df.columns else 0
        compare_avg = compare_df['total_sales'].mean() if 'total_sales' in compare_df.columns else 0
        
        # 변화율/변화액
        change_pct = ((recent_avg - compare_avg) / compare_avg * 100) if compare_avg > 0 else 0
        change_amount = recent_avg - compare_avg
        
        # 하락 시작점 추정 (rolling avg가 baseline 아래로 지속 3일 연속)
        recent_df['rolling_avg'] = recent_df['total_sales'].rolling(window=3, min_periods=1).mean()
        drop_start_date = None
        for i in range(2, len(recent_df)):
            if recent_df.iloc[i]['rolling_avg'] < compare_avg:
                # 3일 연속 확인
                if (recent_df.iloc[i-2]['rolling_avg'] < compare_avg and
                    recent_df.iloc[i-1]['rolling_avg'] < compare_avg):
                    drop_start_date = recent_df.iloc[i-2]['date']
                    break
        
        # 최근 추세 (최근 3일 vs 그 전 3일)
        if len(recent_df) >= 6:
            last_3_avg = recent_df.tail(3)['total_sales'].mean()
            prev_3_avg = recent_df.iloc[-6:-3]['total_sales'].mean()
            trend_pct = ((last_3_avg - prev_3_avg) / prev_3_avg * 100) if prev_3_avg > 0 else 0
        else:
            trend_pct = 0
        
        return {
            "recent_avg": recent_avg,
            "compare_avg": compare_avg,
            "change_pct": change_pct,
            "change_amount": change_amount,
            "drop_start_date": drop_start_date,
            "trend_pct": trend_pct,
            "recent_df": recent_df,
            "compare_df": compare_df,
            "recent_start": recent_start,
            "recent_end": recent_end,
            "compare_start": compare_start,
            "compare_end": compare_end,
        }
    except Exception as e:
        if is_dev_mode():
            st.error(f"STEP 1 분석 오류: {e}")
        return None


def _analyze_what_dropped(
    store_id: str,
    step1_result: Dict,
    period_days: int,
    compare_mode: str,
    base_date: date
) -> Optional[Dict]:
    """STEP 2: 무엇이 떨어졌나?"""
    try:
        recent_df = step1_result["recent_df"]
        compare_df = step1_result["compare_df"]
        
        # A) 네이버방문자 변화
        recent_visitors = recent_df['visitors'].mean() if 'visitors' in recent_df.columns else 0
        compare_visitors = compare_df['visitors'].mean() if 'visitors' in compare_df.columns else 0
        visitors_change_pct = ((recent_visitors - compare_visitors) / compare_visitors * 100) if compare_visitors > 0 else 0
        
        # B) 객단가 변화
        recent_avg_sales = recent_df['total_sales'].mean()
        compare_avg_sales = compare_df['total_sales'].mean()
        recent_avgp = (recent_avg_sales / recent_visitors) if recent_visitors > 0 else 0
        compare_avgp = (compare_avg_sales / compare_visitors) if compare_visitors > 0 else 0
        avgp_change_pct = ((recent_avgp - compare_avgp) / compare_avgp * 100) if compare_avgp > 0 else 0
        
        # C) 판매량 변화
        sales_items_df = load_csv('daily_sales_items.csv', store_id=store_id, default_columns=['날짜', '메뉴명', '판매수량'])
        if not sales_items_df.empty and '날짜' in sales_items_df.columns:
            sales_items_df['날짜'] = pd.to_datetime(sales_items_df['날짜']).dt.date
            
            recent_items = sales_items_df[
                (sales_items_df['날짜'] >= step1_result["recent_start"]) &
                (sales_items_df['날짜'] <= step1_result["recent_end"])
            ]
            compare_items = sales_items_df[
                (sales_items_df['날짜'] >= step1_result["compare_start"]) &
                (sales_items_df['날짜'] <= step1_result["compare_end"])
            ]
            
            recent_qty = recent_items['판매수량'].sum() if '판매수량' in recent_items.columns else 0
            compare_qty = compare_items['판매수량'].sum() if '판매수량' in compare_items.columns else 0
            qty_change_pct = ((recent_qty - compare_qty) / compare_qty * 100) if compare_qty > 0 else 0
        else:
            recent_qty = 0
            compare_qty = 0
            qty_change_pct = 0
        
        # D) 상위메뉴 변화
        top_menu_changes = _analyze_top_menu_changes(
            store_id, 
            step1_result["recent_start"], 
            step1_result["recent_end"],
            step1_result["compare_start"],
            step1_result["compare_end"]
        )
        
        # 원인 후보 생성
        causes = []
        if visitors_change_pct < -10:
            causes.append({
                "type": "네이버방문자",
                "change_pct": visitors_change_pct,
                "label": f"네이버방문자 {visitors_change_pct:.1f}% → 유입 감소형"
            })
        if avgp_change_pct < -10:
            causes.append({
                "type": "객단가",
                "change_pct": avgp_change_pct,
                "label": f"객단가 {avgp_change_pct:.1f}% → 할인/구성/업셀 실패형"
            })
        if qty_change_pct < -10:
            causes.append({
                "type": "판매량",
                "change_pct": qty_change_pct,
                "label": f"판매량 {qty_change_pct:.1f}% → 주문 감소형"
            })
        if top_menu_changes and len([m for m in top_menu_changes if m.get("change_pct", 0) < -20]) >= 2:
            causes.append({
                "type": "상위메뉴",
                "change_pct": -30,  # 추정
                "label": f"Top 메뉴 2개 이상 급감 → 주력메뉴 흔들림형"
            })
        
        return {
            "visitors_change_pct": visitors_change_pct,
            "avgp_change_pct": avgp_change_pct,
            "qty_change_pct": qty_change_pct,
            "top_menu_changes": top_menu_changes,
            "causes": causes,
            "recent_visitors": recent_visitors,
            "compare_visitors": compare_visitors,
            "recent_avgp": recent_avgp,
            "compare_avgp": compare_avgp,
            "recent_qty": recent_qty,
            "compare_qty": compare_qty,
        }
    except Exception as e:
        if is_dev_mode():
            st.error(f"STEP 2 분석 오류: {e}")
        return None


@st.cache_data(ttl=300)
def _analyze_top_menu_changes(
    store_id: str,
    recent_start: date,
    recent_end: date,
    compare_start: date,
    compare_end: date
) -> List[Dict]:
    """상위메뉴 변화 분석"""
    try:
        sales_items_df = load_csv('daily_sales_items.csv', store_id=store_id, default_columns=['날짜', '메뉴명', '판매수량'])
        if sales_items_df.empty:
            return []
        
        sales_items_df['날짜'] = pd.to_datetime(sales_items_df['날짜']).dt.date
        
        # 최근 구간 Top10
        recent_items = sales_items_df[
            (sales_items_df['날짜'] >= recent_start) &
            (sales_items_df['날짜'] <= recent_end)
        ]
        recent_top = recent_items.groupby('메뉴명')['판매수량'].sum().nlargest(10).to_dict()
        
        # 비교 구간 Top10
        compare_items = sales_items_df[
            (sales_items_df['날짜'] >= compare_start) &
            (sales_items_df['날짜'] <= compare_end)
        ]
        compare_top = compare_items.groupby('메뉴명')['판매수량'].sum().nlargest(10).to_dict()
        
        # 변화 분석
        changes = []
        for menu_name, recent_qty in recent_top.items():
            compare_qty = compare_top.get(menu_name, 0)
            if compare_qty > 0:
                change_pct = ((recent_qty - compare_qty) / compare_qty * 100)
                changes.append({
                    "menu_name": menu_name,
                    "recent_qty": recent_qty,
                    "compare_qty": compare_qty,
                    "change_pct": change_pct
                })
        
        # 순위 하락/이탈 메뉴
        changes.sort(key=lambda x: x["change_pct"])
        return changes[:5]  # 최대 5개
    except Exception:
        return []


def _suggest_fixes(store_id: str, step1_result: Dict, step2_result: Dict):
    """STEP 3: 어디를 고치나?"""
    st.markdown("---")
    st.markdown("### 🔧 어디를 고치나? (추천 수리 액션)")
    
    causes = step2_result.get("causes", [])
    if not causes:
        st.info("명확한 원인이 감지되지 않았습니다. 전체적인 점검이 필요합니다.")
        _render_default_actions()
        return
    
    # 가장 큰 변화율의 원인 우선
    primary_cause = max(causes, key=lambda x: abs(x.get("change_pct", 0)))
    
    # 설계 인사이트 로드 (추가 판단용)
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    insights = get_design_insights(store_id, now.year, now.month)
    
    # 추천 액션 생성
    actions = []
    
    if primary_cause["type"] == "네이버방문자":
        actions.append({
            "priority": 1,
            "title": "매출 분석으로 유입 원인 파악",
            "reason": f"네이버방문자가 {primary_cause['change_pct']:.1f}% 감소했습니다.",
            "page": "매출 관리",
            "tab": None
        })
        actions.append({
            "priority": 2,
            "title": "메뉴 포트폴리오 설계실 점검",
            "reason": "유인메뉴/대표메뉴 구성이 방문자 유입에 영향을 줄 수 있습니다.",
            "page": "메뉴 등록",
            "tab": "execute"
        })
    
    elif primary_cause["type"] == "객단가":
        actions.append({
            "priority": 1,
            "title": "메뉴 수익 구조 설계실 (가격·마진)",
            "reason": f"객단가가 {primary_cause['change_pct']:.1f}% 하락했습니다. 가격/마진 구조 점검이 필요합니다.",
            "page": "메뉴 수익 구조 설계실",
            "tab": "execute"
        })
    
    elif primary_cause["type"] == "판매량" or primary_cause["type"] == "상위메뉴":
        actions.append({
            "priority": 1,
            "title": "메뉴 포트폴리오 설계실",
            "reason": f"주력메뉴 판매량이 급감했습니다. 포트폴리오 균형을 점검하세요.",
            "page": "메뉴 등록",
            "tab": "execute"
        })
        actions.append({
            "priority": 2,
            "title": "판매·메뉴 분석",
            "reason": "메뉴별 판매 추이를 자세히 분석하세요.",
            "page": "판매 관리",
            "tab": None
        })
    
    # 설계 인사이트 기반 추가 추천
    ingredient = insights.get("ingredient_structure", {})
    if ingredient.get("has_data") and ingredient.get("top3_concentration", 0) >= 0.7:
        actions.append({
            "priority": 3,
            "title": "재료 구조 설계실",
            "reason": "원가 집중도가 높아 재료 리스크가 영향을 줄 수 있습니다.",
            "page": "재료 등록",
            "tab": "execute"
        })
    
    revenue = insights.get("revenue_structure", {})
    if revenue.get("has_data") and revenue.get("break_even_gap_ratio", 1.0) < 1.0:
        actions.append({
            "priority": 3,
            "title": "수익 구조 설계실",
            "reason": "손익분기점 위험이 확인되었습니다.",
            "page": "수익 구조 설계실",
            "tab": "execute"
        })
    
    # 우선순위 정렬
    actions.sort(key=lambda x: x["priority"])
    
    # 우선 액션 1개 강조
    if actions:
        primary_action = actions[0]
        st.markdown(f"""
        <div style="padding: 1.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 1rem; color: white;">
            <h3 style="color: white; margin: 0 0 0.5rem 0;">⭐ {primary_action['title']}</h3>
            <p style="color: rgba(255,255,255,0.9); margin: 0 0 1rem 0;">{primary_action['reason']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"→ {primary_action['title']}", key="primary_action", use_container_width=True):
            st.session_state.current_page = primary_action["page"]
            if primary_action.get("tab") == "execute":
                st.session_state[f"_initial_tab_{primary_action['page']}"] = "execute"
            st.rerun()
    
    # 나머지 액션
    if len(actions) > 1:
        with st.expander("다른 가능성 보기", expanded=False):
            for action in actions[1:]:
                st.markdown(f"**{action['title']}**")
                st.caption(action['reason'])
                if st.button(f"→ {action['title']}", key=f"action_{action['priority']}", use_container_width=True):
                    st.session_state.current_page = action["page"]
                    if action.get("tab") == "execute":
                        st.session_state[f"_initial_tab_{action['page']}"] = "execute"
                    st.rerun()


def _render_step1_result(step1_result: Dict, compare_mode: str):
    """STEP 1 결과 렌더링"""
    recent_avg = step1_result["recent_avg"]
    compare_avg = step1_result["compare_avg"]
    change_pct = step1_result["change_pct"]
    change_amount = step1_result["change_amount"]
    drop_start_date = step1_result["drop_start_date"]
    trend_pct = step1_result["trend_pct"]
    
    # 요약 카드 3개
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "최근 평균 매출",
            f"{recent_avg:,.0f}원",
            delta=f"{change_pct:.1f}%"
        )
    with col2:
        st.metric(
            f"{compare_mode} 평균 매출",
            f"{compare_avg:,.0f}원"
        )
    with col3:
        st.metric(
            "변화액",
            f"{change_amount:,.0f}원",
            delta=f"{change_pct:.1f}%"
        )
    
    # 하락 시작점
    if drop_start_date:
        st.info(f"📅 하락 시작 추정일: {drop_start_date}")
    
    # 최근 추세
    if trend_pct < -5:
        st.warning(f"⚠️ 최근 3일 추세: {trend_pct:.1f}% (계속 하락 중)")
    elif trend_pct > 5:
        st.success(f"✅ 최근 3일 추세: {trend_pct:.1f}% (회복 중)")
    else:
        st.info(f"📊 최근 3일 추세: {trend_pct:.1f}% (변동 없음)")
    
    # 간단 라인차트
    recent_df = step1_result["recent_df"]
    compare_df = step1_result["compare_df"]
    
    chart_data = pd.DataFrame({
        "날짜": pd.concat([
            recent_df['date'],
            compare_df['date']
        ]),
        "매출": pd.concat([
            recent_df['total_sales'],
            compare_df['total_sales']
        ]),
        "구간": ["최근"] * len(recent_df) + [compare_mode] * len(compare_df)
    })
    
    if not chart_data.empty:
        st.line_chart(
            chart_data.set_index("날짜")[["매출"]],
            use_container_width=True
        )


def _render_step2_result(step2_result: Dict):
    """STEP 2 결과 렌더링"""
    causes = step2_result.get("causes", [])
    
    # 원인 후보 카드
    if causes:
        st.markdown("**원인 후보 (자동 감지)**")
        for cause in causes[:3]:
            emoji = "🔴" if cause["change_pct"] < -20 else "⚠️"
            st.markdown(f"""
            <div style="padding: 1rem; background: #f8f9fa; border-left: 4px solid #dc3545; border-radius: 5px; margin-bottom: 0.5rem;">
                {emoji} {cause['label']}
            </div>
            """, unsafe_allow_html=True)
    
    # KPI delta 테이블
    st.markdown("**KPI 변화 비교**")
    kpi_data = {
        "지표": ["네이버방문자", "객단가", "판매량"],
        "최근": [
            f"{step2_result.get('recent_visitors', 0):.0f}명",
            f"{step2_result.get('recent_avgp', 0):,.0f}원",
            f"{step2_result.get('recent_qty', 0):,.0f}개"
        ],
        "비교": [
            f"{step2_result.get('compare_visitors', 0):.0f}명",
            f"{step2_result.get('compare_avgp', 0):,.0f}원",
            f"{step2_result.get('compare_qty', 0):,.0f}개"
        ],
        "변화율": [
            f"{step2_result.get('visitors_change_pct', 0):.1f}%",
            f"{step2_result.get('avgp_change_pct', 0):.1f}%",
            f"{step2_result.get('qty_change_pct', 0):.1f}%"
        ]
    }
    kpi_df = pd.DataFrame(kpi_data)
    st.dataframe(kpi_df, use_container_width=True, hide_index=True)
    
    # 상위메뉴 변화 테이블
    top_menu_changes = step2_result.get("top_menu_changes", [])
    if top_menu_changes:
        st.markdown("**상위메뉴 변화 (순위 하락/이탈)**")
        menu_data = {
            "메뉴명": [m["menu_name"] for m in top_menu_changes],
            "최근 판매량": [f"{m['recent_qty']:,.0f}개" for m in top_menu_changes],
            "비교 판매량": [f"{m['compare_qty']:,.0f}개" for m in top_menu_changes],
            "변화율": [f"{m['change_pct']:.1f}%" for m in top_menu_changes]
        }
        menu_df = pd.DataFrame(menu_data)
        st.dataframe(menu_df, use_container_width=True, hide_index=True)


def _render_default_actions():
    """기본 액션 (원인 불명확 시)"""
    default_actions = [
        {"title": "매출 분석", "page": "매출 관리"},
        {"title": "메뉴 포트폴리오 설계실", "page": "메뉴 등록", "tab": "execute"},
        {"title": "수익 구조 설계실", "page": "수익 구조 설계실", "tab": "execute"},
    ]
    
    for action in default_actions:
        if st.button(f"→ {action['title']}", key=f"default_{action['page']}", use_container_width=True):
            st.session_state.current_page = action["page"]
            if action.get("tab") == "execute":
                st.session_state[f"_initial_tab_{action['page']}"] = "execute"
            st.rerun()
