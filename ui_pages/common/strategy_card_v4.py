"""
전략 카드 v4 렌더링 공통 컴포넌트
"""
import streamlit as st
from typing import Dict, List


def _get_additional_ctas(card_type: str, card: Dict) -> List[Dict]:
    """
    카드 타입별 추가 CTA 생성
    
    Args:
        card_type: "SURVIVAL" | "MARGIN" | "COST" | "PORTFOLIO" | "ACQUISITION" | "OPERATIONS"
        card: 카드 전체 정보
    
    Returns:
        추가 CTA 리스트
    """
    additional_ctas = []
    
    # 카드 타입 → 추가 CTA 매핑
    if card_type == "SURVIVAL" or "생존선" in card.get("title", ""):
        additional_ctas.extend([
            {"label": "월간 성적표로", "page": "월간 성적표", "params": {}, "is_primary": False},
            {"label": "왜 위험한가?", "page": "", "params": {}, "is_primary": False}  # expander로 처리
        ])
    elif card_type == "MARGIN" or "마진" in card.get("title", ""):
        additional_ctas.extend([
            {"label": "원가 분석으로", "page": "원가 파악", "params": {}, "is_primary": False},
            {"label": "가격 시뮬레이터", "page": "메뉴 수익 구조 설계실", "params": {"tab": "simulator"}, "is_primary": False}
        ])
    elif card_type == "PORTFOLIO" or "포트폴리오" in card.get("title", ""):
        additional_ctas.extend([
            {"label": "판매·메뉴 분석으로", "page": "판매 관리", "params": {}, "is_primary": False},
            {"label": "역할 태그 정리하기", "page": "메뉴 등록", "params": {"tab": "portfolio"}, "is_primary": False}
        ])
    elif card_type == "COST" or "원가" in card.get("title", ""):
        additional_ctas.extend([
            {"label": "원가 분석으로", "page": "원가 파악", "params": {}, "is_primary": False},
            {"label": "대체재 정리하기", "page": "재료 등록", "params": {"tab": "alternatives"}, "is_primary": False}
        ])
    elif card_type == "ACQUISITION" or "매출 하락" in card.get("title", ""):
        additional_ctas.extend([
            {"label": "매출 분석", "page": "매출 관리", "params": {}, "is_primary": False},
            {"label": "분석총평", "page": "분석총평", "params": {}, "is_primary": False}
        ])
    elif card_type == "OPERATIONS" or "운영" in card.get("title", ""):
        additional_ctas.extend([
            {"label": "건강검진 다시하기", "page": "건강검진 실시", "params": {}, "is_primary": False},
            {"label": "이번 주 운영 개선 TOP3", "page": "체크결과", "params": {"section": "actions"}, "is_primary": False}
        ])
    
    return additional_ctas


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
        
        # Impact 표시 (won이 None이거나 0 이하일 때는 표시하지 않음 - 과도한 노출 방지)
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
        # won이 None이면 메시지 표시하지 않음 (데이터 부족 시 과도한 노출 방지)
        
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
        
        # CTA 버튼 (2~3개)
        # 기본 CTA + 추가 CTA (카드 타입별)
        cta_list = []
        
        # 기본 CTA
        if cta and cta.get("page"):
            cta_list.append({
                "label": cta.get("label", "지금 실행하기"),
                "page": cta.get("page", ""),
                "params": cta.get("params", {}),
                "is_primary": True
            })
        
        # 추가 CTA (카드 타입별)
        card_type = card.get("type", "")  # strategy_cards.py에서 전달 필요
        additional_ctas = _get_additional_ctas(card_type, card)
        cta_list.extend(additional_ctas)
        
        # 최대 3개
        cta_list = cta_list[:3]
        
        # 버튼 렌더링
        if len(cta_list) == 1:
            cta_item = cta_list[0]
            if cta_item.get("page"):
                if st.button(cta_item["label"], key=f"strategy_card_{rank}_cta_0", use_container_width=True, type="primary" if cta_item.get("is_primary") else "secondary"):
                    st.session_state["current_page"] = cta_item["page"]
                    if cta_item.get("params"):
                        for key, value in cta_item["params"].items():
                            st.session_state[f"_strategy_param_{key}"] = value
                    st.rerun()
        elif len(cta_list) >= 2:
            cols = st.columns(len(cta_list))
            for idx, cta_item in enumerate(cta_list):
                with cols[idx]:
                    if cta_item.get("page"):
                        if st.button(cta_item["label"], key=f"strategy_card_{rank}_cta_{idx}", use_container_width=True, type="primary" if cta_item.get("is_primary") and idx == 0 else "secondary"):
                            st.session_state["current_page"] = cta_item["page"]
                            if cta_item.get("params"):
                                for key, value in cta_item["params"].items():
                                    st.session_state[f"_strategy_param_{key}"] = value
                            st.rerun()
                    else:
                        # "왜 이건가?" 같은 expander 버튼
                        with st.expander(cta_item["label"], expanded=False):
                            if evidence:
                                st.markdown("**상세 근거:**")
                                for ev in evidence:
                                    st.markdown(f"- {ev}")
                            if why:
                                st.markdown(f"**이유:** {why}")
        
        st.divider()
