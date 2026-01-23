"""
오늘의 전략 카드 공통 컴포넌트
"""
import streamlit as st
from typing import Dict, Optional
from src.auth import get_current_store_id


def render_today_strategy_card(strategy: Dict, location: str = "home"):
    """
    오늘의 전략 카드 렌더링
    
    Args:
        strategy: {
            "title": str,  # 짧고 명령형 (예: "마진 메뉴 1개 가격 시뮬")
            "reason_bullets": List[str],  # 근거 2~3개 (반드시 숫자 포함)
            "cta_label": str,  # 버튼 텍스트
            "cta_page": str,  # 이동할 page key
            "cta_context": Optional[Dict],  # 초기 상태를 잡기 위한 힌트
        }
        location: "home" | "design_center" | "sales_drop_flow" 등
    """
    if not strategy:
        _render_data_insufficient_card()
        return
    
    title = strategy.get("title", "오늘 할 일")
    reason_bullets = strategy.get("reason_bullets", [])
    cta_label = strategy.get("cta_label", "확인하기")
    cta_page = strategy.get("cta_page", "홈")
    cta_context = strategy.get("cta_context", {})
    
    # 카드 UI
    st.markdown("---")
    st.markdown("### 🎯 오늘의 전략 카드")
    
    # 제목 (굵게)
    st.markdown(f"""
    <div style="padding: 1.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 1rem; color: white;">
        <h3 style="color: white; margin: 0 0 1rem 0; font-size: 1.2rem;">{title}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # 근거 bullet
    if reason_bullets:
        st.markdown("**근거:**")
        for bullet in reason_bullets:
            st.markdown(f"- {bullet}")
    
    # 미션 진행률 표시 (있는 경우)
    from src.storage_supabase import load_active_mission, load_recent_evaluated_missions
    from datetime import date
    from zoneinfo import ZoneInfo
    from datetime import datetime
    
    store_id = get_current_store_id()
    if store_id:
        kst = ZoneInfo("Asia/Seoul")
        today = datetime.now(kst).date()
        active_mission = load_active_mission(store_id, today)
        
        # 최근 평가 완료 미션 (있는 경우)
        recent_evaluated = load_recent_evaluated_missions(store_id, limit=1)
        recent_mission = recent_evaluated[0] if recent_evaluated else None
    else:
        active_mission = None
        recent_mission = None
    
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
            
            st.progress(progress / 100)
            st.caption(f"{status_label} · 진행률: {done_count}/{total_count} ({progress:.0f}%)")
            
            if st.button("📋 미션 열기", key=f"mission_open_{location}", use_container_width=True):
                st.session_state["current_page"] = "오늘의 전략 실행"
                st.rerun()
    
    # 최근 평가 완료 미션 결과 요약 (있는 경우)
    if recent_mission and location == "home":
        result_type = recent_mission.get("result_type")
        coach_comment = recent_mission.get("coach_comment", "")
        if result_type and coach_comment:
            result_badges = {
                "improved": "✅ 개선",
                "no_change": "➡️ 정체",
                "worsened": "⚠️ 악화",
            }
            badge = result_badges.get(result_type, "")
            
            st.markdown(f"""
            <div style="padding: 0.8rem; background: #f8f9fa; border-left: 4px solid #667eea; border-radius: 5px; margin-top: 0.5rem;">
                <strong>최근 전략 결과: {badge}</strong><br>
                <small>{coach_comment}</small>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("근거 보기", key=f"view_result_{location}", use_container_width=True):
                st.session_state["current_page"] = "오늘의 전략 실행"
                st.rerun()
    
    # CTA 버튼 (미션 없을 때만 또는 항상 표시)
    col1, col2 = st.columns(2) if active_mission else st.columns(1)
    with col1:
        if st.button(cta_label, key=f"strategy_cta_{location}", use_container_width=True, type="primary"):
            # 세션 변수 세팅
            st.session_state["current_page"] = cta_page
            
            # 컨텍스트 세팅
            if cta_context:
                for key, value in cta_context.items():
                    st.session_state[key] = value
            
            st.rerun()
    
    # 미션이 있으면 "미션으로 시작" 버튼도 표시
    if active_mission:
        with col2:
            if st.button("🎯 미션으로 시작", key=f"mission_start_{location}", use_container_width=True):
                st.session_state["current_page"] = "오늘의 전략 실행"
                st.rerun()
    
    # 후보 2개가 있으면 expander로 표시
    alternatives = strategy.get("alternatives", [])
    if alternatives:
        with st.expander("다른 추천 보기", expanded=False):
            for alt in alternatives:
                alt_title = alt.get("title", "")
                alt_reason = alt.get("reason", "")
                alt_cta_label = alt.get("cta_label", "확인하기")
                alt_cta_page = alt.get("cta_page", "홈")
                alt_cta_context = alt.get("cta_context", {})
                
                st.markdown(f"**{alt_title}**")
                st.caption(alt_reason)
                if st.button(alt_cta_label, key=f"alt_strategy_{alt_cta_page}_{location}", use_container_width=True):
                    st.session_state["current_page"] = alt_cta_page
                    if alt_cta_context:
                        for key, value in alt_cta_context.items():
                            st.session_state[key] = value
                    st.rerun()


def _render_data_insufficient_card():
    """데이터 부족 시 입력 유도 카드"""
    st.markdown("---")
    st.markdown("### 🎯 오늘의 전략 카드")
    
    st.info("데이터가 부족해요. 먼저 마감/보정을 입력해 주세요.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 점장 마감 하러가기", key="insufficient_goto_close", use_container_width=True):
            st.session_state["current_page"] = "점장 마감"
            st.rerun()
    with col2:
        if st.button("💰 매출·네이버방문자 보정", key="insufficient_goto_sales", use_container_width=True):
            st.session_state["current_page"] = "매출 등록"
            st.rerun()
