"""
매출 하락 원인 찾기 (DEPRECATED)
이 페이지는 **분석총평**으로 대체되었습니다. 라우팅은 app.py에서 "분석총평"으로 연결됩니다.

기존 3단 플로우(언제/무엇/어디)는 제거·미사용 처리됩니다.
"""
from __future__ import annotations

import streamlit as st
import pandas as pd
from datetime import datetime, date
from zoneinfo import ZoneInfo
from typing import Dict, Optional

from src.bootstrap import bootstrap
from src.ui_helpers import render_page_header
from src.auth import get_current_store_id, is_dev_mode
from core.sales_drop_engine import analyze_sales_drop
from ui_pages.design_lab.design_state_loader import get_design_state, get_primary_risk_area

# 공통 설정 적용
bootstrap(page_title="매출 하락 원인 찾기")


def render_sales_drop_investigation():
    """매출 하락 원인 찾기 페이지 렌더링"""
    render_page_header("📉 매출 하락 원인 찾기", "📉")
    
    st.markdown("**3분 안에 원인을 좁히고, 고칠 곳으로 바로 이동합니다.**")
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    # STEP 1: 언제부터 떨어졌나?
    _render_step1_when(store_id)
    
    # STEP 2: 무엇이 떨어졌나?
    if 'analysis_result' in st.session_state and st.session_state['analysis_result']:
        _render_step2_what(st.session_state['analysis_result'])
    
    # STEP 3: 어디를 고치나?
    if 'analysis_result' in st.session_state and st.session_state['analysis_result']:
        _render_step3_where(store_id, st.session_state['analysis_result'])


def _render_step1_when(store_id: str):
    """STEP 1: 언제부터 떨어졌나?"""
    st.markdown("---")
    st.markdown("### STEP 1: 언제부터 떨어졌나?")
    
    # 기간 선택
    col1, col2, col3 = st.columns([2, 2, 3])
    with col1:
        period_days = st.selectbox(
            "기간 선택",
            [7, 14, 30],
            index=1,
            key="step1_period_days"
        )
    with col2:
        compare_type_str = st.selectbox(
            "비교 방식",
            ["전주 대비", "전월 대비"],
            index=0,
            key="step1_compare_mode"
        )
        compare_type = "week" if compare_type_str == "전주 대비" else "month"
    with col3:
        pass
    
    # 기준 날짜 (기본값: 오늘)
    base_date = date.today()
    with st.expander("고급 옵션", expanded=False):
        base_date_input = st.date_input("기준 날짜", value=date.today(), key="step1_base_date")
        if base_date_input:
            base_date = base_date_input
    
    # 분석 실행
    if st.button("분석 시작", key="step1_analyze", type="primary", use_container_width=True):
        with st.spinner("분석 중..."):
            result = analyze_sales_drop(period_days, compare_type, store_id, base_date)
            st.session_state['analysis_result'] = result
            st.rerun()
    
    # 결과 표시
    if 'analysis_result' in st.session_state and st.session_state['analysis_result']:
        result = st.session_state['analysis_result']
        summary = result.get("summary", {})
        
        # 요약 카드
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            sales_delta = summary.get("sales_delta_pct", 0.0)
            st.metric("총매출", f"{sales_delta:+.1f}%")
        
        with col2:
            visitors_delta = summary.get("visitors_delta_pct", 0.0)
            st.metric("네이버방문자", f"{visitors_delta:+.1f}%")
        
        with col3:
            avgp_delta = summary.get("avgp_delta_pct", 0.0)
            st.metric("객단가", f"{avgp_delta:+.1f}%")
        
        with col4:
            quantity_delta = summary.get("quantity_delta_pct", 0.0)
            st.metric("총 판매수량", f"{quantity_delta:+.1f}%")
        
        # 결과 박스
        drop_start = summary.get("drop_start_date")
        recent_trend = summary.get("recent_trend", "")
        
        st.info(f"""
        **최근 {period_days}일 기준, 매출 {sales_delta:.1f}% 하락**
        
        - 네이버방문자 {visitors_delta:.1f}%, 객단가 {avgp_delta:.1f}%
        - 하락 시작 추정: {drop_start.strftime('%Y-%m-%d') if drop_start else '미확인'}
        - 최근 추세: {recent_trend}
        """)


def _render_step2_what(result: Dict):
    """STEP 2: 무엇이 떨어졌나?"""
    st.markdown("---")
    st.markdown("### STEP 2: 무엇이 떨어졌나?")
    
    primary_cause = result.get("primary_cause", "")
    confidence = result.get("confidence", 0)
    evidence = result.get("evidence", [])
    metrics = result.get("metrics", {})
    menu_changes = result.get("menu_changes", [])
    
    # 원인 카드
    cause_labels = {
        "traffic": "유입 감소",
        "menu": "메뉴 문제",
        "price": "가격/구조 문제",
        "cost": "원가 구조 문제",
        "structure": "생존선 문제",
    }
    
    cause_label = cause_labels.get(primary_cause, "원인 미확인")
    
    st.markdown(f"""
    <div style="padding: 1.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                border-radius: 12px; color: white; margin: 1rem 0;">
        <h3 style="color: white; margin: 0 0 1rem 0;">📉 이번 하락은 '{cause_label}'가 1차 원인입니다.</h3>
        <p style="margin: 0; opacity: 0.9;">신뢰도: {confidence}%</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 근거
    if evidence:
        st.markdown("**근거:**")
        for ev in evidence:
            st.markdown(f"- {ev}")
    
    # 세부 지표 비교 테이블
    st.markdown("#### 세부 지표 비교")
    
    baseline = metrics.get("baseline", {})
    recent = metrics.get("recent", {})
    delta = metrics.get("delta", {})
    
    comparison_data = {
        "항목": ["총매출(일평균)", "네이버방문자(일평균)", "객단가", "총 판매수량(일평균)"],
        "이전": [
            f"{baseline.get('sales_avg', 0):,.0f}원",
            f"{baseline.get('visitors_avg', 0):,.0f}명",
            f"{baseline.get('avgp', 0):,.0f}원",
            "—",  # 판매수량은 별도 계산
        ],
        "현재": [
            f"{recent.get('sales_avg', 0):,.0f}원",
            f"{recent.get('visitors_avg', 0):,.0f}명",
            f"{recent.get('avgp', 0):,.0f}원",
            "—",
        ],
        "증감": [
            f"{delta.get('sales_delta_pct', 0):+.1f}%",
            f"{delta.get('visitors_delta_pct', 0):+.1f}%",
            f"{delta.get('avgp_delta_pct', 0):+.1f}%",
            f"{delta.get('quantity_delta_pct', 0):+.1f}%",
        ],
        "상태": [
            "🔴" if delta.get('sales_delta_pct', 0) < -5 else "⚠️" if delta.get('sales_delta_pct', 0) < 0 else "✅",
            "🔴" if delta.get('visitors_delta_pct', 0) < -5 else "⚠️" if delta.get('visitors_delta_pct', 0) < 0 else "✅",
            "🔴" if delta.get('avgp_delta_pct', 0) < -5 else "⚠️" if delta.get('avgp_delta_pct', 0) < 0 else "✅",
            "🔴" if delta.get('quantity_delta_pct', 0) < -5 else "⚠️" if delta.get('quantity_delta_pct', 0) < 0 else "✅",
        ],
    }
    
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)
    
    # 상위 메뉴 변화
    if menu_changes:
        st.markdown("#### 상위 메뉴 변화")
        
        menu_data = {
            "메뉴명": [m.get("menu_name", "") for m in menu_changes[:5]],
            "판매량 증감": [f"{m.get('qty_delta_pct', 0):+.1f}%" for m in menu_changes[:5]],
            "매출 증감": [f"{m.get('sales_delta_pct', 0):+.1f}%" for m in menu_changes[:5]],
            "순위 변화": [f"{m.get('rank_change', 0):+d}" for m in menu_changes[:5]],
        }
        
        menu_df = pd.DataFrame(menu_data)
        st.dataframe(menu_df, use_container_width=True, hide_index=True)


def _render_step3_where(store_id: str, result: Dict):
    """STEP 3: 어디를 고치나?"""
    st.markdown("---")
    st.markdown("### STEP 3: 어디를 고치나?")
    
    primary_cause = result.get("primary_cause", "")
    
    # 설계 상태 로드
    kst = ZoneInfo("Asia/Seoul")
    now = datetime.now(kst)
    design_state = get_design_state(store_id, now.year, now.month)
    primary_risk = get_primary_risk_area(design_state)
    
    # 코치 판결
    cause_labels = {
        "traffic": "유입 감소",
        "menu": "메뉴 문제",
        "price": "가격/구조 문제",
        "cost": "원가 구조 문제",
        "structure": "생존선 문제",
    }
    
    cause_label = cause_labels.get(primary_cause, "원인 미확인")
    
    # 구조 매핑
    action_map = {
        "traffic": {
            "primary": {"label": "📊 매출 분석", "page": "매출 분석"},
            "secondary": [
                {"label": "📈 홈으로 돌아가기", "page": "홈"},
            ],
        },
        "menu": {
            "primary": {"label": "📊 메뉴 포트폴리오 설계", "page": "메뉴 등록"},
            "secondary": [
                {"label": "💰 메뉴 수익 구조 설계", "page": "메뉴 수익 구조 설계실"},
                {"label": "📈 판매·메뉴 분석", "page": "판매·메뉴 분석"},
            ],
        },
        "price": {
            "primary": {"label": "💰 메뉴 수익 구조 설계", "page": "메뉴 수익 구조 설계실"},
            "secondary": [
                {"label": "📊 메뉴 포트폴리오 설계", "page": "메뉴 등록"},
                {"label": "📈 수익 구조 설계", "page": "수익 구조 설계실"},
            ],
        },
        "cost": {
            "primary": {"label": "🥬 재료 구조 설계", "page": "재료 등록"},
            "secondary": [
                {"label": "💰 메뉴 수익 구조 설계", "page": "메뉴 수익 구조 설계실"},
                {"label": "📈 수익 구조 설계", "page": "수익 구조 설계실"},
            ],
        },
        "structure": {
            "primary": {"label": "📈 수익 구조 설계", "page": "수익 구조 설계실"},
            "secondary": [
                {"label": "💰 메뉴 수익 구조 설계", "page": "메뉴 수익 구조 설계실"},
                {"label": "🥬 재료 구조 설계", "page": "재료 등록"},
            ],
        },
    }
    
    # 설계 상태 기반 우선순위 조정
    if primary_risk:
        risk_action_map = {
            "menu_portfolio": {"label": "📊 메뉴 포트폴리오 설계", "page": "메뉴 등록"},
            "menu_profit": {"label": "💰 메뉴 수익 구조 설계", "page": "메뉴 수익 구조 설계실"},
            "ingredient_structure": {"label": "🥬 재료 구조 설계", "page": "재료 등록"},
            "revenue_structure": {"label": "📈 수익 구조 설계", "page": "수익 구조 설계실"},
        }
        
        if primary_risk in risk_action_map:
            # 설계 상태 위험이 있으면 우선
            primary_action = risk_action_map[primary_risk]
            st.markdown(f"""
            <div style="padding: 1.5rem; background: #fff3cd; border-left: 4px solid #ffc107; 
                        border-radius: 8px; margin: 1rem 0;">
                <strong>이번 매출 하락은 '{cause_label}' + '{primary_risk} 구조 위험'이 동시에 작용 중입니다.</strong>
            </div>
            """, unsafe_allow_html=True)
        else:
            primary_action = action_map.get(primary_cause, {}).get("primary", {"label": "홈", "page": "홈"})
    else:
        primary_action = action_map.get(primary_cause, {}).get("primary", {"label": "홈", "page": "홈"})
    
    # 지금 1순위 액션
    st.markdown("#### 🔥 지금 1순위 액션")
    
    if st.button(
        primary_action["label"],
        key="step3_primary_action",
        type="primary",
        use_container_width=True
    ):
        st.session_state["current_page"] = primary_action["page"]
        if primary_action["page"] in ["메뉴 등록", "메뉴 수익 구조 설계실", "재료 등록", "수익 구조 설계실"]:
            st.session_state[f"_initial_tab_{primary_action['page']}"] = "execute"
        st.rerun()
    
    # 보조 액션
    secondary_actions = action_map.get(primary_cause, {}).get("secondary", [])
    if secondary_actions:
        st.markdown("#### 보조 액션")
        for idx, action in enumerate(secondary_actions[:2]):
            if st.button(
                action["label"],
                key=f"step3_secondary_{idx}",
                use_container_width=True
            ):
                st.session_state["current_page"] = action["page"]
                if action["page"] in ["메뉴 등록", "메뉴 수익 구조 설계실", "재료 등록", "수익 구조 설계실"]:
                    st.session_state[f"_initial_tab_{action['page']}"] = "execute"
                st.rerun()
