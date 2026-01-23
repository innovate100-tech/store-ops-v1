"""
가게 설계 센터 (통합 진단실)
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
from src.ui_helpers import render_page_header
from ui_pages.design_lab.design_lab_frame import (
    render_coach_board,
    render_structure_map_container,
    render_school_cards,
    render_design_tools_container,
)
from ui_pages.design_lab.design_center_data import (
    get_design_center_summary,
    get_primary_concern,
)
from src.auth import get_current_store_id

# 공통 설정 적용
bootstrap(page_title="Design Center")


def render_design_center():
    """가게 설계 센터 페이지 렌더링"""
    render_page_header("가게 설계 센터 (통합 진단실)", "🏗️")
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    # 통합 요약 데이터 로드
    summary = get_design_center_summary(store_id)
    
    # ZONE A: 코치 요약 (통합)
    cards = []
    
    # 1) 메뉴 포트폴리오 상태
    mp = summary["menu_portfolio"]
    status_emoji = "✅" if mp["status"] == "균형" else "⚠️" if mp["status"] == "주의" else "🔴"
    cards.append({
        "title": "메뉴 포트폴리오",
        "value": f"{mp['balance_score']}점",
        "subtitle": f"{status_emoji} {mp['status']}"
    })
    
    # 2) 메뉴 수익 구조 상태
    mpr = summary["menu_profit"]
    status_emoji = "✅" if mpr["status"] == "안정" else "⚠️" if mpr["status"] == "주의" else "🔴"
    cards.append({
        "title": "메뉴 수익 구조",
        "value": f"{mpr['high_cost_rate_count']}개",
        "subtitle": f"{status_emoji} 고원가율 메뉴"
    })
    
    # 3) 재료 구조 상태
    ing = summary["ingredient_structure"]
    status_emoji = "✅" if ing["status"] == "안정" else "⚠️" if ing["status"] == "주의" else "🔴"
    cards.append({
        "title": "재료 구조",
        "value": f"{ing['top3_concentration']:.1f}%",
        "subtitle": f"{status_emoji} TOP3 집중도"
    })
    
    # 4) 수익 구조 상태
    rev = summary["revenue_structure"]
    status_emoji = "✅" if rev["status"] == "안정" else "⚠️" if rev["status"] == "주의" else "🔴"
    breakeven_ratio = (rev["estimated_sales"] / rev["breakeven"] * 100) if rev["breakeven"] > 0 else 0
    cards.append({
        "title": "수익 구조",
        "value": f"{breakeven_ratio:.0f}%",
        "subtitle": f"{status_emoji} 손익분기점 대비"
    })
    
    # 판결문 (가장 의심되는 구조)
    concern_name, verdict_text, target_page = get_primary_concern(summary)
    
    render_coach_board(
        cards=cards,
        verdict_text=verdict_text,
        action_title=f"{concern_name} 점검하기",
        action_reason=None,
        action_target_page=target_page,
        action_button_label=f"{concern_name} 점검하기"
    )
    
    # 카드별 바로가기 버튼 추가
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📊 메뉴 포트폴리오 설계실", key="nav_menu_portfolio", use_container_width=True):
            st.session_state.current_page = "메뉴 등록"
            st.rerun()
    with col2:
        if st.button("💰 메뉴 수익 구조 설계실", key="nav_menu_profit", use_container_width=True):
            st.session_state.current_page = "메뉴 수익 구조 설계실"
            st.rerun()
    with col3:
        if st.button("🥬 재료 구조 설계실", key="nav_ingredient", use_container_width=True):
            st.session_state.current_page = "재료 등록"
            st.rerun()
    with col4:
        if st.button("📈 수익 구조 설계실", key="nav_revenue", use_container_width=True):
            st.session_state.current_page = "수익 구조 설계실"
            st.rerun()
    
    # ZONE B: 구조 레이더/요약 맵
    def _render_structure_radar():
        st.markdown("#### 📊 구조 상태 비교")
        
        # 4열 비교 테이블
        comparison_data = {
            "구조": ["메뉴 포트폴리오", "메뉴 수익 구조", "재료 구조", "수익 구조"],
            "점수": [
                mp["score"],
                mpr["score"],
                ing["score"],
                rev["score"]
            ],
            "상태": [
                mp["status"],
                mpr["status"],
                ing["status"],
                rev["status"]
            ],
            "요약": [
                mp["message"],
                mpr["message"],
                ing["message"],
                rev["message"]
            ]
        }
        
        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)
        
        # 간단 bar chart
        st.markdown("#### 📈 구조 점수 비교")
        score_df = pd.DataFrame({
            "구조": comparison_data["구조"],
            "점수": comparison_data["점수"]
        })
        score_df = score_df.set_index("구조")
        st.bar_chart(score_df)
    
    render_structure_map_container(
        content_func=_render_structure_radar,
        empty_message="데이터를 불러올 수 없습니다.",
        empty_action_label="데이터 입력하기",
        empty_action_page="홈"
    )
    
    # ZONE C: 코치 1차 판결 (핵심)
    st.markdown("---")
    st.markdown("### 🎯 코치 1차 판결")
    
    st.info(f"**{concern_name}** 구조가 가장 의심됩니다.")
    st.write(verdict_text)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button(f"🔍 {concern_name} 점검하기", key="primary_concern_action", type="primary", use_container_width=True):
            st.session_state.current_page = target_page
            st.rerun()
    
    # 두 번째 후보 (옵션)
    with st.expander("📋 두 번째 후보 보기", expanded=False):
        # 점수 기준으로 정렬
        all_concerns = [
            ("메뉴 포트폴리오", mp["score"], "메뉴 등록"),
            ("메뉴 수익 구조", mpr["score"], "메뉴 수익 구조 설계실"),
            ("재료 구조", ing["score"], "재료 등록"),
            ("수익 구조", rev["score"], "수익 구조 설계실"),
        ]
        all_concerns.sort(key=lambda x: x[1])
        
        if len(all_concerns) > 1:
            second_name, second_score, second_page = all_concerns[1]
            st.write(f"**{second_name}** (점수: {second_score}점)")
            if st.button(f"{second_name} 점검하기", key="secondary_concern_action", use_container_width=True):
                st.session_state.current_page = second_page
                st.rerun()
    
    # ZONE D: 전략 실행 런치패드
    st.markdown("---")
    st.markdown("### 🚀 전략 실행 런치패드")
    
    st.markdown("**문제 상황별 실행 버튼**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📉 매출 하락 원인 찾기", key="action_sales_drop", use_container_width=True):
            st.session_state.current_page = "매출 분석"
            st.rerun()
        
        if st.button("💰 고원가율 메뉴 정리", key="action_high_cost", use_container_width=True):
            st.session_state.current_page = "메뉴 수익 구조 설계실"
            st.rerun()
        
        if st.button("📊 포트폴리오 미분류 정리", key="action_portfolio", use_container_width=True):
            st.session_state.current_page = "메뉴 등록"
            st.rerun()
    
    with col2:
        if st.button("🥬 원가 집중/대체재 설계", key="action_ingredient", use_container_width=True):
            st.session_state.current_page = "재료 등록"
            st.rerun()
        
        if st.button("📈 손익분기점 갱신", key="action_breakeven", use_container_width=True):
            st.session_state.current_page = "수익 구조 설계실"
            st.rerun()
        
        if st.button("🏠 홈으로 돌아가기", key="action_home", use_container_width=True):
            st.session_state.current_page = "홈"
            st.rerun()
