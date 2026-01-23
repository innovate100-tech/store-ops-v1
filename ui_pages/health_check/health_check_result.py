"""
검진 결과 요약 페이지 (실행형 리포트)
최근 완료 검진 기준으로 상세 결과 표시
"""
import streamlit as st
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, List, Optional

from src.bootstrap import bootstrap
from src.ui_helpers import render_page_header
from src.auth import get_current_store_id
from src.health_check.storage import (
    get_health_session,
    get_health_results,
    get_health_diagnosis
)
from src.health_check.health_diagnosis_engine import diagnose_health_check
from src.health_check.questions_bank import CATEGORY_LABELS
from ui_pages.home.home_data import load_latest_health_diag

logger = logging.getLogger(__name__)

# 공통 설정 적용
bootstrap(page_title="검진 결과 요약")


def render_health_check_result():
    """검진 결과 요약 페이지 렌더링"""
    render_page_header("검진 결과 요약", "🩺")
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    try:
        # 세션 ID가 전달되었으면 해당 세션 사용, 없으면 최신 세션
        session_id_from_state = st.session_state.get("_health_check_session_id")
        
        if session_id_from_state:
            session = get_health_session(session_id_from_state)
            if not session or not session.get("completed_at"):
                # 완료되지 않은 세션이면 최신 완료 세션으로 fallback
                session = _load_latest_completed_session(store_id)
        else:
            # 최신 완료 검진 세션 로드
            session = _load_latest_completed_session(store_id)
        
        if not session:
            _render_no_session_view(store_id)
            return
        
        session_id = session["id"]
        completed_at = session.get("completed_at")
        
        # 판독 데이터 로드
        health_diag = get_health_diagnosis(session_id)
        if not health_diag:
            # 판독 결과가 없으면 생성
            results = get_health_results(session_id)
            if results:
                axis_scores = {
                    r.get("category"): float(r.get("score_avg", 0))
                    for r in results
                    if r.get("category") and r.get("score_avg") is not None
                }
                health_diag = diagnose_health_check(
                    session_id=session_id,
                    store_id=store_id,
                    axis_scores=axis_scores,
                    axis_raw=None,
                    meta=None
                )
        
        # 결과 데이터 로드
        results = get_health_results(session_id)
        
        # ZONE별 렌더링
        _render_zone0_header(session, health_diag)
        _render_zone1_scores_summary(results)
        _render_zone2_top3_risks(health_diag)
        _render_zone3_recommended_actions(health_diag)
        _render_zone4_previous_comparison(store_id, session_id)
        _render_zone5_next_checkup(store_id)
    
    except Exception as e:
        logger.error(f"render_health_check_result: Error - {e}", exc_info=True)
        st.error("검진 결과를 불러오는 중 오류가 발생했습니다.")
        if st.button("건강검진 실시하기", key="error_retry_health_check"):
            st.session_state["current_page"] = "건강검진 실시"
            st.rerun()


@st.cache_data(ttl=300)
def _load_latest_completed_session(store_id: str) -> Optional[Dict]:
    """최신 완료 검진 세션 로드"""
    try:
        from src.auth import get_supabase_client
        supabase = get_supabase_client()
        if not supabase:
            return None
        
        result = supabase.table("health_check_sessions").select(
            "id, completed_at, overall_score, overall_grade, main_bottleneck"
        ).eq("store_id", store_id).not_.is_("completed_at", "null").order(
            "completed_at", desc=True
        ).limit(1).execute()
        
        if result.data:
            return result.data[0]
        return None
    
    except Exception as e:
        logger.warning(f"_load_latest_completed_session: Error - {e}")
        return None


def _render_no_session_view(store_id: str):
    """검진 없음 안내"""
    st.info("""
    **완료된 검진이 없습니다.**
    
    건강검진을 통해 운영 전반의 위험 신호를 조기에 발견할 수 있습니다.
    """)
    
    if st.button("건강검진 실시하기", type="primary", use_container_width=True):
        st.session_state["current_page"] = "건강검진 실시"
        st.rerun()


def _render_zone0_header(session: Dict, health_diag: Optional[Dict]):
    """ZONE 0: 헤더 요약"""
    completed_at = session.get("completed_at")
    if completed_at:
        try:
            dt = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
            kst = ZoneInfo("Asia/Seoul")
            dt_kst = dt.astimezone(kst)
            date_str = dt_kst.strftime("%Y년 %m월 %d일")
        except Exception:
            date_str = completed_at[:10]
    else:
        date_str = "날짜 미확인"
    
    primary_pattern = health_diag.get("primary_pattern", {}) if health_diag else {}
    pattern_title = primary_pattern.get("title", "안정형")
    pattern_description = primary_pattern.get("description", "")
    
    insight_summary = health_diag.get("insight_summary", []) if health_diag else []
    verdict_line = insight_summary[0] if insight_summary else "검진 결과를 확인하세요."
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"### 최근 검진: {date_str}")
        st.markdown(f"**{pattern_title}** 패턴")
    with col2:
        overall_score = session.get("overall_score", 0)
        overall_grade = session.get("overall_grade", "E")
        st.metric("종합 점수", f"{overall_score:.1f}점", f"등급: {overall_grade}")
    
    st.markdown(f"**💡 판결:** {verdict_line}")
    if pattern_description:
        st.caption(pattern_description)
    
    st.divider()


def _render_zone1_scores_summary(results: List[Dict]):
    """ZONE 1: 9축 점수 요약"""
    st.markdown("### 📊 9축 점수 요약")
    
    if not results:
        st.info("점수 데이터가 없습니다.")
        return
    
    # 축별 점수 정리
    axis_scores = {}
    for r in results:
        category = r.get("category")
        score_avg = r.get("score_avg")
        risk_level = r.get("risk_level", "unknown")
        if category and score_avg is not None:
            axis_scores[category] = {
                "score": float(score_avg),
                "risk": risk_level
            }
    
    # 3x3 그리드로 표시
    cols = st.columns(3)
    axis_order = ["Q", "S", "C", "P1", "P2", "P3", "M", "H", "F"]
    
    for idx, axis in enumerate(axis_order):
        col_idx = idx % 3
        with cols[col_idx]:
            if axis in axis_scores:
                score_data = axis_scores[axis]
                score = score_data["score"]
                risk = score_data["risk"]
                
                # 점수를 10점 만점으로 변환
                score_10 = score / 10.0
                
                # 위험도 배지
                risk_emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(risk, "⚪")
                
                axis_name = CATEGORY_LABELS.get(axis, axis)
                st.markdown(f"**{axis_name} ({axis})**")
                st.metric("", f"{score_10:.1f}/10", f"{risk_emoji} {risk}")
            else:
                axis_name = CATEGORY_LABELS.get(axis, axis)
                st.markdown(f"**{axis_name} ({axis})**")
                st.caption("데이터 없음")
    
    st.divider()


def _render_zone2_top3_risks(health_diag: Optional[Dict]):
    """ZONE 2: Top3 리스크"""
    st.markdown("### ⚠️ Top3 리스크")
    
    if not health_diag:
        st.info("검진 판독 데이터가 없습니다.")
        return
    
    risk_axes = health_diag.get("risk_axes", [])
    if not risk_axes:
        st.info("현재 위험 신호가 감지되지 않았습니다.")
        return
    
    for idx, risk in enumerate(risk_axes[:3], 1):
        axis = risk.get("axis", "")
        score = risk.get("score", 0)
        level = risk.get("level", "mid")
        reason = risk.get("reason", "")
        
        axis_name = CATEGORY_LABELS.get(axis, axis)
        level_emoji = {"high": "🔴", "mid": "🟡", "good": "🟢"}.get(level, "⚪")
        
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{idx}. {axis_name} ({axis}) 축**")
                st.markdown(f"{level_emoji} {reason}")
                st.caption(f"점수: {score}/10")
            with col2:
                if st.button("바로 고치기", key=f"risk_{idx}_fix", use_container_width=True):
                    # 해당 축에 맞는 페이지로 이동
                    route_map = {
                        "H": "건강검진 실시",  # 운영 개선
                        "S": "건강검진 실시",
                        "C": "건강검진 실시",
                        "P1": "수익 구조 설계실",
                        "F": "수익 구조 설계실",
                        "Q": "메뉴 포트폴리오 설계실",
                        "M": "매출 하락 원인 찾기"
                    }
                    route = route_map.get(axis, "가게 설계 센터")
                    st.session_state["current_page"] = route
                    st.rerun()
        
        st.divider()


def _render_zone3_recommended_actions(health_diag: Optional[Dict]):
    """ZONE 3: 권장 액션 TOP3"""
    st.markdown("### 🎯 권장 액션 TOP3")
    
    if not health_diag:
        st.info("검진 판독 데이터가 없습니다.")
        return
    
    actions = _build_health_actions(health_diag)
    
    if not actions:
        st.info("현재 권장 액션이 없습니다.")
        return
    
    for idx, action in enumerate(actions[:3], 1):
        action_code = action.get("code", "")
        title = action.get("title", "")
        reason = action.get("reason", "")
        route = action.get("route", "")
        
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{idx}. {title}**")
                st.caption(reason)
            with col2:
                if st.button("실행하기", key=f"action_{idx}_execute", use_container_width=True):
                    st.session_state["current_page"] = route
                    st.rerun()
        
        st.divider()


def _build_health_actions(health_diag: Dict) -> List[Dict]:
    """검진 판독 기반 권장 액션 생성"""
    actions = []
    
    risk_axes = health_diag.get("risk_axes", [])
    primary_pattern = health_diag.get("primary_pattern", {})
    pattern_code = primary_pattern.get("code", "")
    
    # 위험 축별 액션 매핑
    high_risk_axes = [r["axis"] for r in risk_axes if r.get("level") == "high"]
    
    # H/S/C 위험 → OPERATION_QSC_RECOVERY
    if any(axis in high_risk_axes for axis in ["H", "S", "C"]) or pattern_code in ["OPERATION_BREAKDOWN", "REVISIT_COLLAPSE"]:
        actions.append({
            "code": "OPERATION_QSC_RECOVERY",
            "title": "운영 품질(QSC) 복구",
            "reason": "인적자원/서비스/청결 축이 동시에 낮아 운영 붕괴 위험이 큽니다.",
            "route": "건강검진 실시"
        })
    
    # P1/F 위험 → FINANCE_SURVIVAL_LINE
    if "P1" in high_risk_axes or "F" in high_risk_axes or pattern_code == "PRICE_STRUCTURE_RISK":
        actions.append({
            "code": "FINANCE_SURVIVAL_LINE",
            "title": "수익 구조 복구",
            "reason": "가격 신뢰도와 재무 구조가 동시에 약화되어 수익성이 위협받고 있습니다.",
            "route": "수익 구조 설계실"
        })
    
    # Q 위험 → MENU_PORTFOLIO_REBALANCE
    if "Q" in high_risk_axes or pattern_code == "PRODUCT_STRUCTURE_WEAK":
        actions.append({
            "code": "MENU_PORTFOLIO_REBALANCE",
            "title": "메뉴 포트폴리오 재배치",
            "reason": "품질 축이 낮아 고객 만족도가 급격히 하락하고 있습니다.",
            "route": "메뉴 등록"
        })
    
    # M 위험 → SALES_DROP_INVESTIGATION
    if "M" in high_risk_axes or pattern_code == "GROWTH_BLOCKED":
        actions.append({
            "code": "SALES_DROP_INVESTIGATION",
            "title": "매출 하락 원인 찾기",
            "reason": "마케팅 축이 낮아 유입 구조가 부재합니다.",
            "route": "매출 하락 원인 찾기"
        })
    
    return actions


def _render_zone4_previous_comparison(store_id: str, current_session_id: str):
    """ZONE 4: 이전 검진 대비"""
    st.markdown("### 📈 이전 검진 대비")
    
    try:
        from src.auth import get_supabase_client
        supabase = get_supabase_client()
        if not supabase:
            st.info("이전 검진 데이터를 불러올 수 없습니다.")
            return
        
        # 현재 검진 제외하고 이전 검진 1개 조회
        result = supabase.table("health_check_sessions").select(
            "id, completed_at, overall_score"
        ).eq("store_id", store_id).not_.is_("completed_at", "null").neq(
            "id", current_session_id
        ).order("completed_at", desc=True).limit(1).execute()
        
        if not result.data:
            st.info("첫 검진입니다. 다음 검진에서 변화가 추적됩니다.")
            return
        
        prev_session = result.data[0]
        prev_diag = get_health_diagnosis(prev_session["id"])
        current_diag = get_health_diagnosis(current_session_id)
        
        if not prev_diag or not current_diag:
            st.info("이전 검진 판독 데이터가 없습니다.")
            return
        
        # 축별 점수 비교
        prev_results = get_health_results(prev_session["id"])
        current_results = get_health_results(current_session_id)
        
        if not prev_results or not current_results:
            st.info("이전 검진 점수 데이터가 없습니다.")
            return
        
        # 축별 점수 매핑
        prev_scores = {r["category"]: float(r["score_avg"]) for r in prev_results if r.get("category")}
        current_scores = {r["category"]: float(r["score_avg"]) for r in current_results if r.get("category")}
        
        # 변화 표시
        changes = []
        for axis in ["Q", "S", "C", "P1", "P2", "P3", "M", "H", "F"]:
            if axis in prev_scores and axis in current_scores:
                prev_score = prev_scores[axis] / 10.0
                current_score = current_scores[axis] / 10.0
                diff = current_score - prev_score
                
                if abs(diff) > 0.1:  # 0.1점 이상 변화
                    axis_name = CATEGORY_LABELS.get(axis, axis)
                    direction = "↑" if diff > 0 else "↓"
                    changes.append({
                        "axis": axis_name,
                        "change": diff,
                        "direction": direction
                    })
        
        if changes:
            st.markdown("**변화가 큰 축:**")
            for change in changes[:3]:
                st.markdown(f"- {change['axis']}: {change['direction']} {abs(change['change']):.1f}점")
        else:
            st.info("이전 검진 대비 큰 변화가 없습니다.")
    
    except Exception as e:
        logger.warning(f"_render_zone4_previous_comparison: Error - {e}")
        st.info("이전 검진 비교 데이터를 불러올 수 없습니다.")


def _render_zone5_next_checkup(store_id: str):
    """ZONE 5: 다음 검진 안내"""
    st.markdown("### 📅 다음 검진")
    
    st.info("""
    **권장 주기:** 월 2-3회 (약 2주마다)
    
    정기적인 건강검진을 통해 운영 전반의 위험 신호를 조기에 발견하고 개선할 수 있습니다.
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("건강검진 다시하기", type="primary", use_container_width=True):
            st.session_state["current_page"] = "건강검진 실시"
            st.rerun()
    with col2:
        if st.button("검진 히스토리 보기", use_container_width=True):
            st.session_state["current_page"] = "검진 히스토리"
            st.rerun()
