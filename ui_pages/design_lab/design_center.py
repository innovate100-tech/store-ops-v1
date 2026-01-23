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
from ui_pages.design_lab.design_insights import get_design_insights
from ui_pages.coach.coach_adapters import get_design_center_verdict
from ui_pages.coach.coach_renderer import render_verdict_card
from ui_pages.routines.routine_state import get_routine_status, mark_weekly_check_done
from src.auth import get_current_store_id
from datetime import datetime
from zoneinfo import ZoneInfo

# 공통 설정 적용
bootstrap(page_title="Design Center")


def render_design_center():
    """가게 설계 센터 페이지 렌더링"""
    render_page_header("가게 설계 센터 (통합 진단실)", "🏗️")
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    # 이번 주 점검 완료 버튼
    routine_status = get_routine_status(store_id)
    if not routine_status["weekly_design_check_done"]:
        if st.button("✅ 이번 주 구조 점검 완료 처리", key="mark_weekly_check_done", use_container_width=True):
            mark_weekly_check_done(store_id)
            st.success("이번 주 구조 점검 완료 처리되었습니다!")
            st.rerun()
    else:
        st.info("✅ 이번 주 점검 완료")
    
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
    
    # 최근 전략 결과 요약 (ZONE A 하단)
    try:
        from src.storage_supabase import load_recent_evaluated_missions
        recent_evaluated = load_recent_evaluated_missions(store_id, limit=1)
        if recent_evaluated:
            recent_mission = recent_evaluated[0]
            result_type = recent_mission.get("result_type")
            coach_comment = recent_mission.get("coach_comment", "")
            if result_type and coach_comment:
                result_badges = {
                    "improved": "✅ 개선",
                    "no_change": "➡️ 정체",
                    "worsened": "⚠️ 악화",
                }
                badge = result_badges.get(result_type, "")
                
                st.markdown("---")
                st.markdown("### 📊 최근 전략 결과")
                st.markdown(f"""
                <div style="padding: 1rem; background: #f8f9fa; border-left: 4px solid #667eea; border-radius: 5px;">
                    <strong>{badge}</strong><br>
                    {coach_comment}
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("근거 보기", key="design_center_view_result", use_container_width=True):
                    st.session_state["current_page"] = "오늘의 전략 실행"
                    st.rerun()
    except Exception:
        pass
    
    # 오늘의 전략 카드 추가
    try:
        from ui_pages.analysis.strategy_engine import pick_primary_strategy
        from ui_pages.common.today_strategy_card import render_today_strategy_card
        from datetime import date
        
        strategy = pick_primary_strategy(store_id, ref_date=date.today(), window_days=14)
        if strategy:
            render_today_strategy_card(strategy, location="design_center")
    except Exception as e:
        # 에러 발생해도 계속 진행
        pass
    
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
    
    # CoachVerdict 표준 형식으로 변환
    verdict = get_design_center_verdict(store_id)
    render_verdict_card(verdict, compact=False)
    
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
    
    # 진행 중 미션 카드 (ZONE D 위에)
    try:
        from src.storage_supabase import load_active_mission, load_recent_evaluated_missions
        from datetime import date
        from zoneinfo import ZoneInfo
        from datetime import datetime
        
        kst = ZoneInfo("Asia/Seoul")
        today = datetime.now(kst).date()
        active_mission = load_active_mission(store_id, today)
        
        if active_mission:
            from src.storage_supabase import load_mission_tasks
            tasks = load_mission_tasks(active_mission["id"])
            if tasks:
                done_count = sum(1 for t in tasks if t.get("is_done", False))
                total_count = len(tasks)
                progress = (done_count / total_count * 100) if total_count > 0 else 0
                
                # 상태 배지
                status = active_mission.get("status", "active")
                status_labels = {
                    "active": "🛠 실행중",
                    "monitoring": "👀 감시중",
                    "evaluated": "🧠 판정완료",
                }
                status_label = status_labels.get(status, "🛠 실행중")
                
                st.markdown("---")
                st.markdown("### 🎯 진행 중 미션")
                st.markdown(f"**{active_mission.get('title', '오늘 할 일')}**")
                st.progress(progress / 100)
                st.caption(f"{status_label} · 진행률: {done_count}/{total_count} ({progress:.0f}%)")
                if st.button("📋 미션 열기", key="design_center_mission_open", use_container_width=True):
                    st.session_state["current_page"] = "오늘의 전략 실행"
                    st.rerun()
        
        # 코치 재개입 (evaluated 미션 중 worsened/no_change)
        recent_evaluated = load_recent_evaluated_missions(store_id, limit=1)
        if recent_evaluated:
            recent_mission = recent_evaluated[0]
            result_type = recent_mission.get("result_type")
            if result_type in ["worsened", "no_change"]:
                st.markdown("---")
                st.markdown("### 🚨 코치 재개입")
                coach_comment = recent_mission.get("coach_comment", "")
                st.warning(f"{coach_comment}")
                if st.button("다음 전략 받기", key="design_center_next_strategy", use_container_width=True):
                    # 다음 전략 생성
                    from ui_pages.analysis.strategy_engine import pick_primary_strategy
                    from ui_pages.common.today_strategy_card import render_today_strategy_card
                    next_strategy = pick_primary_strategy(store_id, ref_date=today, window_days=14)
                    if next_strategy:
                        render_today_strategy_card(next_strategy, location="design_center")
    except Exception:
        pass  # 에러 발생해도 계속 진행
    
    # ZONE D: 전략 실행 런치패드 (Top3 개인화)
    st.markdown("---")
    st.markdown("### 🚀 전략 실행 런치패드")
    
    # 설계 인사이트 기반 Top3 액션 선정
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    top3_actions = _get_top3_launchpad_actions(store_id, now.year, now.month)
    
    # 우선 노출 3개
    st.markdown("**우선 실행 (상태 기반 추천)**")
    col1, col2 = st.columns(2)
    
    for idx, action in enumerate(top3_actions[:3]):
        col = col1 if idx % 2 == 0 else col2
        with col:
            if st.button(action["label"], key=f"top3_action_{idx}", use_container_width=True):
                st.session_state.current_page = action["page"]
                # 전략 실행 탭으로 이동하기 위한 플래그 설정
                if action.get("tab") == "execute":
                    st.session_state[f"_initial_tab_{action['page']}"] = "execute"
                st.rerun()
    
    # 나머지 액션은 expander로
    remaining_actions = top3_actions[3:] if len(top3_actions) > 3 else []
    all_actions = [
        {"label": "📉 매출 하락 원인 찾기", "page": "매출 하락 원인 찾기", "tab": None},
        {"label": "💰 고원가율 메뉴 정리", "page": "메뉴 수익 구조 설계실", "tab": "execute"},
        {"label": "📊 포트폴리오 미분류 정리", "page": "메뉴 등록", "tab": "execute"},
        {"label": "🥬 원가 집중/대체재 설계", "page": "재료 등록", "tab": "execute"},
        {"label": "📈 손익분기점 갱신", "page": "수익 구조 설계실", "tab": "execute"},
        {"label": "🏠 홈으로 돌아가기", "page": "홈", "tab": None},
    ]
    
    # Top3에 포함되지 않은 액션만 표시
    shown_pages = {a["page"] for a in top3_actions[:3]}
    other_actions = [a for a in all_actions if a["page"] not in shown_pages]
    
    if other_actions:
        with st.expander("더보기 (기타 액션)", expanded=False):
            for action in other_actions:
                if st.button(action["label"], key=f"other_action_{action['page']}", use_container_width=True):
                    st.session_state.current_page = action["page"]
                    if action.get("tab") == "execute":
                        st.session_state[f"_initial_tab_{action['page']}"] = "execute"
                    st.rerun()


def _get_top3_launchpad_actions(store_id: str, year: int, month: int) -> list:
    """
    설계 인사이트 기반 Top3 액션 선정
    
    Returns:
        [{"label": str, "page": str, "tab": str | None, "score": int}, ...]
    """
    try:
        insights = get_design_insights(store_id, year, month)
        
        # 액션 후보와 점수 계산
        actions = []
        
        # 1) 수익 구조 위험 (break_even_gap_ratio < 0.9)
        revenue = insights.get("revenue_structure", {})
        if revenue.get("has_data"):
            gap_ratio = revenue.get("break_even_gap_ratio", 1.0)
            if gap_ratio < 0.9:
                score = 100 if gap_ratio < 0.8 else 80
                actions.append({
                    "label": "📈 손익분기점 갱신",
                    "page": "수익 구조 설계실",
                    "tab": "execute",
                    "score": score
                })
        
        # 2) 재료 구조 위험 (top3_concentration >= 0.7 AND missing_substitute_count > 0)
        ingredient = insights.get("ingredient_structure", {})
        if ingredient.get("has_data"):
            top3_concentration = ingredient.get("top3_concentration", 0.0)
            missing_substitute = ingredient.get("missing_substitute_count", 0)
            if top3_concentration >= 0.7 and missing_substitute > 0:
                actions.append({
                    "label": "🥬 원가 집중/대체재 설계",
                    "page": "재료 등록",
                    "tab": "execute",
                    "score": 90
                })
        
        # 3) 마진 메뉴 0개
        menu_portfolio = insights.get("menu_portfolio", {})
        if menu_portfolio.get("has_data"):
            margin_count = menu_portfolio.get("margin_menu_count", 0)
            if margin_count == 0:
                actions.append({
                    "label": "💰 고원가율 메뉴 정리",
                    "page": "메뉴 수익 구조 설계실",
                    "tab": "execute",
                    "score": 85
                })
        
        # 4) 역할 미분류 비율 >= 30%
        if menu_portfolio.get("has_data"):
            unclassified_ratio = menu_portfolio.get("role_unclassified_ratio", 0.0)
            if unclassified_ratio >= 30.0:
                actions.append({
                    "label": "📊 포트폴리오 미분류 정리",
                    "page": "메뉴 등록",
                    "tab": "execute",
                    "score": 60
                })
        
        # 5) 고원가율 메뉴 >= 3개
        menu_profit = insights.get("menu_profit", {})
        if menu_profit.get("has_data"):
            high_cogs_count = menu_profit.get("high_cogs_ratio_menu_count", 0)
            if high_cogs_count >= 3:
                actions.append({
                    "label": "💰 고원가율 메뉴 정리",
                    "page": "메뉴 수익 구조 설계실",
                    "tab": "execute",
                    "score": 70
                })
        
        # 6) 운영 데이터 기반 (매출 급락 등 - 기존 로직 활용 가능)
        # 여기서는 간단히 기본 액션 추가
        if not actions:
            actions.append({
                "label": "📉 매출 하락 원인 찾기",
                "page": "매출 하락 원인 찾기",
                "tab": None,
                "score": 50
            })
        
        # 점수 기준 정렬 (높은 순)
        actions.sort(key=lambda x: x["score"], reverse=True)
        
        # 중복 제거 (같은 page는 최고 점수만)
        seen_pages = set()
        unique_actions = []
        for action in actions:
            if action["page"] not in seen_pages:
                unique_actions.append(action)
                seen_pages.add(action["page"])
        
        # 최대 6개까지 반환 (Top3 + 나머지 3개)
        return unique_actions[:6]
    except Exception:
        # 에러 시 기본 액션 반환
        return [
            {"label": "📉 매출 하락 원인 찾기", "page": "매출 하락 원인 찾기", "tab": None, "score": 50},
            {"label": "💰 고원가율 메뉴 정리", "page": "메뉴 수익 구조 설계실", "tab": "execute", "score": 40},
            {"label": "📊 포트폴리오 미분류 정리", "page": "메뉴 등록", "tab": "execute", "score": 30},
        ]
