"""
전략 카드 v4 렌더링 공통 컴포넌트
"""
import streamlit as st
from typing import Dict


def render_strategy_card_v4(card: Dict):
    """
    전략 카드 v4 렌더링
    
    Args:
        card: {
            "rank": int,
            "title": str,
            "why": str,
            "evidence": [str, ...],
            "cta": {"label": str, "page": str, "params": {}},
            "impact": {"won": int|None, "kind": str, "assumptions": [str], "confidence": float},
            "action_plan": {"time_horizon": str, "difficulty": str, "steps": [...], ...},
            "success_prob": float
        }
    """
    rank = card.get("rank", 0)
    title = card.get("title", "")
    why = card.get("why", "")
    evidence = card.get("evidence", [])
    cta = card.get("cta", {})
    impact = card.get("impact", {})
    action_plan = card.get("action_plan", {})
    success_prob = card.get("success_prob", 0.55)
    
    # 카드 컨테이너
    with st.container():
        st.markdown(f"#### {rank}. {title}")
        
        # Impact 표시
        won = impact.get("won")
        if won is not None and won > 0:
            kind = impact.get("kind", "profit_up")
            kind_label = "예상 이익" if kind == "profit_up" else "리스크 회피" if kind == "risk_avoid" else "간접효과"
            confidence = impact.get("confidence", 0.5)
            
            col_impact1, col_impact2 = st.columns([2, 1])
            with col_impact1:
                st.metric(f"💰 {kind_label}", f"+{won:,}원/월")
            with col_impact2:
                st.caption(f"신뢰도 {confidence*100:.0f}%")
        elif won is None:
            st.info("💡 간접효과 (정량화 어려움)")
        
        # 성공 확률
        st.caption(f"성공 확률: {success_prob*100:.0f}%")
        
        # 근거
        if evidence:
            st.markdown("**근거:**")
            for ev in evidence[:2]:  # 최대 2줄
                st.markdown(f"- {ev}")
        
        # Action Plan (expander로 표시)
        if action_plan and action_plan.get("steps"):
            with st.expander("📋 이번 주 실행 체크리스트", expanded=False):
                steps = action_plan.get("steps", [])
                time_horizon = action_plan.get("time_horizon", "1주")
                difficulty = action_plan.get("difficulty", "중간")
                
                st.caption(f"⏱️ {time_horizon} | 난이도: {difficulty}")
                
                for idx, step in enumerate(steps, 1):
                    step_text = step.get("text", "")
                    eta_min = step.get("eta_min", 0)
                    done_when = step.get("done_when", "")
                    
                    st.markdown(f"**{idx}. {step_text}**")
                    if eta_min > 0:
                        st.caption(f"   ⏱️ 예상 {eta_min}분")
                    if done_when:
                        st.caption(f"   ✓ 완료 기준: {done_when}")
                
                # 주의사항
                watchouts = action_plan.get("watchouts", [])
                if watchouts:
                    st.markdown("**⚠️ 주의사항:**")
                    for watchout in watchouts:
                        st.caption(f"- {watchout}")
        
        # CTA 버튼
        col_cta1, col_cta2 = st.columns([1, 1])
        with col_cta1:
            cta_label = cta.get("label", "지금 실행하기")
            cta_page = cta.get("page", "")
            if cta_page:
                if st.button(cta_label, key=f"strategy_card_{rank}_cta", use_container_width=True):
                    st.session_state["current_page"] = cta_page
                    params = cta.get("params", {})
                    if params:
                        for key, value in params.items():
                            st.session_state[f"_strategy_param_{key}"] = value
                    st.rerun()
        
        with col_cta2:
            if action_plan and action_plan.get("steps"):
                if st.button("📋 실행 플랜 보기", key=f"strategy_card_{rank}_plan", use_container_width=True):
                    # expander는 이미 위에 있으므로 스크롤만 이동
                    pass
        
        st.divider()
