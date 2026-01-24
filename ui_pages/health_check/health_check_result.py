"""
체크결과 통합 페이지 (실행형 리포트)
선택 회차 결과 + 체크 히스토리 통합
"""
import streamlit as st
import logging
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, List, Optional, Tuple

from src.bootstrap import bootstrap
from src.ui_helpers import render_page_header
from src.auth import get_current_store_id
from src.health_check.storage import (
    get_health_session,
    get_health_results,
    get_health_diagnosis,
    get_health_answers
)
from src.health_check.health_diagnosis_engine import diagnose_health_check
from src.health_check.questions_bank import CATEGORY_LABELS, QUESTIONS, CATEGORIES_ORDER

logger = logging.getLogger(__name__)

# 공통 설정 적용
bootstrap(page_title="QSC 결과분석")


def render_health_check_result():
    """체크결과 통합 페이지 렌더링"""
    render_page_header("QSC 결과분석", "📋")
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    try:
        # 완료 세션 리스트 로드 (회차 선택용)
        completed_sessions = _load_completed_sessions(store_id, limit=10)
        
        if not completed_sessions:
            _render_no_session_view(store_id)
            return
        
        # ZONE A: 회차 선택 + 헤더
        session, session_id = _render_zone_a_session_selector(store_id, completed_sessions)
        
        if not session:
            _render_no_session_view(store_id)
            return
        
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
        _render_zone_b_scores_summary(results, store_id, session_id)
        _render_zone_b2_no_maybe_questions(session_id)
        _render_zone_c_top3_risks(health_diag)
        _render_zone_d_recommended_actions(health_diag)
        _render_zone_e_previous_comparison(store_id, session_id)
        _render_zone_f_history(store_id, completed_sessions)
        _render_zone_g_next_checkup(store_id)
    
    except Exception as e:
        logger.error(f"render_health_check_result: Error - {e}", exc_info=True)
        st.error("체크 결과를 불러오는 중 오류가 발생했습니다.")
        if st.button("매장 체크리스트 실시하기", key="error_retry_health_check"):
            st.session_state["current_page"] = "건강검진 실시"
            st.rerun()


@st.cache_data(ttl=300)
def _load_latest_completed_session(store_id: str) -> Optional[Dict]:
    """최신 완료 체크 세션 로드"""
    try:
        from src.auth import get_read_client
        supabase = get_read_client()
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


@st.cache_data(ttl=300)
def _load_completed_sessions(store_id: str, limit: int = 10) -> List[Dict]:
    """완료 체크 세션 리스트 로드"""
    try:
        from src.auth import get_read_client
        supabase = get_read_client()
        if not supabase:
            return []
        
        result = supabase.table("health_check_sessions").select(
            "id, completed_at, overall_score, overall_grade, main_bottleneck"
        ).eq("store_id", store_id).not_.is_("completed_at", "null").order(
            "completed_at", desc=True
        ).limit(limit).execute()
        
        return result.data if result.data else []
    
    except Exception as e:
        logger.warning(f"_load_completed_sessions: Error - {e}")
        return []


def _resolve_display_session(store_id: str, completed_sessions: List[Dict]) -> Tuple[Optional[Dict], Optional[str]]:
    """표시할 세션 결정"""
    session_id_from_state = st.session_state.get("_health_check_session_id")
    
    if session_id_from_state:
        # 세션 ID가 있으면 해당 세션 사용
        session = get_health_session(session_id_from_state)
        if session and session.get("completed_at"):
            # 완료된 세션이고 목록에 있으면 사용
            if any(s["id"] == session_id_from_state for s in completed_sessions):
                return session, session_id_from_state
    
    # 최신 완료 세션으로 fallback
    if completed_sessions:
        latest = completed_sessions[0]
        return latest, latest["id"]
    
    return None, None


def _build_session_select_options(completed_sessions: List[Dict]) -> List[Tuple[str, str]]:
    """회차 선택 옵션 생성"""
    options = []
    for idx, session in enumerate(completed_sessions):
        session_id = session["id"]
        completed_at = session.get("completed_at")
        
        if completed_at:
            try:
                dt = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
                kst = ZoneInfo("Asia/Seoul")
                dt_kst = dt.astimezone(kst)
                date_str = dt_kst.strftime("%Y-%m-%d")
            except Exception:
                date_str = completed_at[:10]
        else:
            date_str = "날짜 미확인"
        
        # 첫 번째는 "이번 체크" 표시
        if idx == 0:
            label = f"{date_str} (이번 체크)"
        else:
            label = date_str
        
        options.append((session_id, label))
    
    return options


def _no_maybe_questions(session_id: str) -> List[Dict]:
    """아니요·애매해요 질문 모아보기"""
    answers = get_health_answers(session_id)
    if not answers:
        return []
    
    # no, maybe 필터
    filtered = [
        a for a in answers
        if a.get("raw_value") in ["no", "maybe"]
    ]
    
    # 질문 문구 매핑
    result = []
    for ans in filtered:
        category = ans.get("category")
        question_code = ans.get("question_code")
        raw_value = ans.get("raw_value")
        memo = ans.get("memo")
        
        if not category or not question_code:
            continue
        
        # 질문 문구 찾기
        question_text = None
        if category in QUESTIONS:
            for q in QUESTIONS[category]:
                if q.get("code") == question_code:
                    question_text = q.get("text", "")
                    break
        
        if not question_text:
            question_text = f"{question_code} (질문 문구 없음)"
        
        # raw_value → 한글
        answer_kr = {"no": "아니요", "maybe": "애매해요"}.get(raw_value, raw_value)
        
        result.append({
            "축": category,
            "축한글": CATEGORY_LABELS.get(category, category),
            "질문": question_text,
            "답변": answer_kr,
            "memo": memo
        })
    
    # 축 순서 + 질문 코드 순 정렬
    def sort_key(item):
        axis_order = {ax: idx for idx, ax in enumerate(CATEGORIES_ORDER)}
        axis_idx = axis_order.get(item["축"], 999)
        question_code = item["질문"].split()[0] if item["질문"] else ""
        return (axis_idx, question_code)
    
    result.sort(key=sort_key)
    return result


def _render_no_session_view(store_id: str):
    """체크 없음 안내"""
    st.info("""
    **완료된 체크가 없습니다.**
    
    매장 체크리스트를 통해 운영 전반의 위험 신호를 조기에 발견할 수 있습니다.
    """)
    
    if st.button("매장 체크리스트 실시하기", type="primary", use_container_width=True):
        st.session_state["current_page"] = "건강검진 실시"
        st.rerun()


def _render_zone_a_session_selector(store_id: str, completed_sessions: List[Dict]) -> Tuple[Optional[Dict], Optional[str]]:
    """ZONE A: 회차 선택 + 헤더"""
    # 회차 선택 옵션 생성
    options = _build_session_select_options(completed_sessions)
    if not options:
        return None, None
    
    # 현재 선택된 세션 ID
    current_session_id = st.session_state.get("_health_check_session_id")
    if not current_session_id or not any(opt[0] == current_session_id for opt in options):
        current_session_id = options[0][0]  # 기본값: 최신
    
    # 회차 선택 UI
    option_labels = [opt[1] for opt in options]
    option_ids = [opt[0] for opt in options]
    current_idx = option_ids.index(current_session_id) if current_session_id in option_ids else 0
    
    def on_session_change():
        """회차 선택 변경 시 호출"""
        selected_idx = st.session_state.session_selector
        if selected_idx < len(option_ids):
            st.session_state["_health_check_session_id"] = option_ids[selected_idx]
    
    selected_idx = st.selectbox(
        "어떤 체크를 볼까요?",
        options=range(len(option_labels)),
        format_func=lambda i: option_labels[i],
        index=current_idx,
        key="session_selector",
        on_change=on_session_change
    )
    
    # 선택된 세션 ID 찾기
    selected_session_id = option_ids[selected_idx]
    
    # 세션 ID 업데이트 (on_change가 호출되지 않을 경우를 대비)
    if selected_session_id != current_session_id:
        st.session_state["_health_check_session_id"] = selected_session_id
    
    # 세션 로드
    session = get_health_session(selected_session_id)
    if not session:
        return None, None
    
    # 헤더 표시
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
    
    health_diag = get_health_diagnosis(selected_session_id)
    primary_pattern = health_diag.get("primary_pattern", {}) if health_diag else {}
    pattern_title = primary_pattern.get("title", "안정형")
    pattern_description = primary_pattern.get("description", "")
    
    insight_summary = health_diag.get("insight_summary", []) if health_diag else []
    verdict_line = insight_summary[0] if insight_summary else "체크 결과를 확인하세요."
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"### 체크: {date_str}")
        st.markdown(f"**{pattern_title}** 패턴")
    with col2:
        overall_score = session.get("overall_score", 0)
        overall_grade = session.get("overall_grade", "E")
        st.metric("종합 점수", f"{overall_score:.1f}점", f"등급: {overall_grade}")
    
    st.markdown(f"**💡 판결:** {verdict_line}")
    if pattern_description:
        st.caption(pattern_description)
    
    st.divider()
    
    return session, selected_session_id


def _render_zone_b_scores_summary(results: List[Dict], store_id: str, session_id: str):
    """ZONE B: 9축 점수 요약"""
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


def _render_zone_b2_no_maybe_questions(session_id: str):
    """ZONE B2: 아니요·애매해요 질문 모아보기"""
    questions = _no_maybe_questions(session_id)
    
    if not questions:
        st.markdown("### ✅ 아니요·애매해요 질문 모아보기")
        st.info("이번 체크에서 '아니요' 또는 '애매해요'로 답한 질문이 없습니다. 모든 항목이 양호합니다! 🎉")
        st.divider()
        return
    
    count = len(questions)
    with st.expander(f"### ⚠️ 아니요·애매해요 질문 모아보기 ({count}개)", expanded=True):
        # 데이터프레임 생성
        df_data = []
        for q in questions:
            row = {
                "축": q["축한글"],
                "질문": q["질문"],
                "답변": q["답변"]
            }
            if q.get("memo"):
                row["메모"] = q["memo"]
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        
        # 컬럼 설정
        column_config = {
            "축": st.column_config.TextColumn("축", width="small"),
            "질문": st.column_config.TextColumn("질문", width="large"),
            "답변": st.column_config.TextColumn("답변", width="small")
        }
        if "메모" in df.columns:
            column_config["메모"] = st.column_config.TextColumn("메모", width="medium")
        
        st.dataframe(df, use_container_width=True, hide_index=True, column_config=column_config)
        
        st.caption(f"총 {count}개의 질문에서 개선이 필요합니다.")
    
    st.divider()


def _render_zone_c_top3_risks(health_diag: Optional[Dict]):
    """ZONE C: Top3 리스크"""
    st.markdown("### ⚠️ Top3 리스크")
    
    if not health_diag:
        st.info("체크 판독 데이터가 없습니다.")
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
                        "H": "매장 체크리스트",  # 운영 개선
                        "S": "매장 체크리스트",
                        "C": "매장 체크리스트",
                        "P1": "수익 구조 설계실",
                        "F": "수익 구조 설계실",
                        "Q": "메뉴 포트폴리오 설계실",
                        "M": "분석총평"
                    }
                    route = route_map.get(axis, "가게 설계 센터")
                    st.session_state["current_page"] = route
                    st.rerun()
        
        st.divider()


def _render_zone_d_recommended_actions(health_diag: Optional[Dict]):
    """ZONE D: 권장 액션 TOP3"""
    st.markdown("### 🎯 권장 액션 TOP3")
    
    if not health_diag:
        st.info("체크 판독 데이터가 없습니다.")
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
            "route": "건강검진 실시"  # page key 유지
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
            "title": "분석총평",
            "reason": "마케팅 축이 낮아 유입 구조가 부재합니다.",
            "route": "분석총평"
        })
    
    return actions


def _render_zone_e_previous_comparison(store_id: str, current_session_id: str):
    """ZONE E: 이전 체크 대비"""
    st.markdown("### 📈 이전 체크 대비")
    
    try:
        from src.auth import get_read_client
        supabase = get_read_client()
        if not supabase:
            st.info("이전 체크 데이터를 불러올 수 없습니다.")
            return
        
        # 현재 체크 제외하고 이전 체크 1개 조회
        result = supabase.table("health_check_sessions").select(
            "id, completed_at, overall_score"
        ).eq("store_id", store_id).not_.is_("completed_at", "null").neq(
            "id", current_session_id
        ).order("completed_at", desc=True).limit(1).execute()
        
        if not result.data:
            st.info("첫 체크입니다. 다음 체크에서 변화가 추적됩니다.")
            return
        
        prev_session = result.data[0]
        prev_diag = get_health_diagnosis(prev_session["id"])
        current_diag = get_health_diagnosis(current_session_id)
        
        if not prev_diag or not current_diag:
            st.info("이전 체크 판독 데이터가 없습니다.")
            return
        
        # 축별 점수 비교
        prev_results = get_health_results(prev_session["id"])
        current_results = get_health_results(current_session_id)
        
        if not prev_results or not current_results:
            st.info("이전 체크 점수 데이터가 없습니다.")
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
            st.info("이전 체크 대비 큰 변화가 없습니다.")
    
    except Exception as e:
        logger.warning(f"_render_zone_e_previous_comparison: Error - {e}")
        st.info("이전 체크 비교 데이터를 불러올 수 없습니다.")


def _render_zone_f_history(store_id: str, completed_sessions: List[Dict]):
    """ZONE F: 체크 히스토리"""
    st.markdown("### 📊 체크 히스토리")
    
    if len(completed_sessions) == 0:
        st.info("완료된 체크가 없습니다.")
        return
    
    # 회차 카드 리스트
    st.markdown("#### 📋 체크 회차 리스트")
    for idx, session in enumerate(completed_sessions, 1):
        _render_session_card(session, idx)
    
    st.divider()
    
    # 축별 변화 추이
    if len(completed_sessions) >= 2:
        _render_axis_trend(completed_sessions)


def _render_session_card(session: Dict, rank: int):
    """체크 회차 카드 렌더링"""
    session_id = session["id"]
    completed_at = session.get("completed_at")
    overall_score = session.get("overall_score", 0)
    overall_grade = session.get("overall_grade", "E")
    main_bottleneck = session.get("main_bottleneck")
    
    # 날짜 포맷팅
    if completed_at:
        try:
            dt = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
            kst = ZoneInfo("Asia/Seoul")
            dt_kst = dt.astimezone(kst)
            date_str = dt_kst.strftime("%Y-%m-%d %H:%M")
        except Exception:
            date_str = completed_at[:10]
    else:
        date_str = "날짜 미확인"
    
    # 판독 데이터 로드
    health_diag = get_health_diagnosis(session_id)
    primary_pattern = health_diag.get("primary_pattern", {}) if health_diag else {}
    pattern_title = primary_pattern.get("title", "안정형")
    
    risk_axes = health_diag.get("risk_axes", []) if health_diag else []
    top_risk = risk_axes[0] if risk_axes else None
    
    # 카드 렌더링
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"**{rank}. {date_str}**")
        st.markdown(f"패턴: {pattern_title}")
        if top_risk:
            risk_axis = top_risk.get("axis", "")
            risk_reason = top_risk.get("reason", "")
            axis_name = CATEGORY_LABELS.get(risk_axis, risk_axis)
            st.caption(f"주요 위험: {axis_name} - {risk_reason}")
        elif main_bottleneck:
            bottleneck_name = CATEGORY_LABELS.get(main_bottleneck, main_bottleneck)
            st.caption(f"병목: {bottleneck_name}")
    
    with col2:
        st.metric("종합 점수", f"{overall_score:.1f}점", f"등급: {overall_grade}")
    
    with col3:
        if st.button("결과 보기", key=f"history_{session_id}_view", use_container_width=True):
            st.session_state["_health_check_session_id"] = session_id
            st.rerun()
    
    st.divider()


def _render_axis_trend(sessions: List[Dict]):
    """축별 변화 추이 (표 + 라인 차트)"""
    st.markdown("#### 📈 축별 변화 추이")
    
    try:
        # 각 세션의 축별 점수 수집
        axis_data = {}  # {axis: [score1, score2, ...]}
        axis_order = ["Q", "S", "C", "P1", "P2", "P3", "M", "H", "F"]
        session_dates = []
        
        for session in sessions:
            session_id = session["id"]
            results = get_health_results(session_id)
            
            # 날짜 수집
            completed_at = session.get("completed_at")
            if completed_at:
                try:
                    dt = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
                    kst = ZoneInfo("Asia/Seoul")
                    dt_kst = dt.astimezone(kst)
                    date_str = dt_kst.strftime("%Y-%m-%d")
                except Exception:
                    date_str = completed_at[:10]
            else:
                date_str = "날짜 미확인"
            session_dates.append(date_str)
            
            if results:
                for r in results:
                    axis = r.get("category")
                    score_avg = r.get("score_avg")
                    if axis and score_avg is not None:
                        score_10 = float(score_avg) / 10.0
                        if axis not in axis_data:
                            axis_data[axis] = []
                        axis_data[axis].append(score_10)
        
        if not axis_data:
            st.info("축별 점수 데이터가 없습니다.")
            return
        
        # 탭: 표 | 차트
        tab1, tab2 = st.tabs(["표", "차트"])
        
        with tab1:
            # 표 생성
            table_data = []
            for axis in axis_order:
                if axis in axis_data:
                    scores = axis_data[axis]
                    axis_name = CATEGORY_LABELS.get(axis, axis)
                    
                    # 최신 3개 회차만 표시
                    recent_scores = scores[:3]
                    if len(recent_scores) < 3:
                        recent_scores = recent_scores + [None] * (3 - len(recent_scores))
                    
                    row = {"축": axis_name}
                    for idx, score in enumerate(recent_scores[:3], 1):
                        if score is not None:
                            row[f"회차 {idx}"] = f"{score:.1f}"
                        else:
                            row[f"회차 {idx}"] = "-"
                    
                    # 변화 방향
                    if len(scores) >= 2:
                        latest = scores[0]
                        previous = scores[1]
                        diff = latest - previous
                        if abs(diff) > 0.1:
                            direction = "↑" if diff > 0 else "↓"
                            row["변화"] = f"{direction} {abs(diff):.1f}"
                        else:
                            row["변화"] = "→"
                    else:
                        row["변화"] = "-"
                    
                    table_data.append(row)
            
            if table_data:
                df = pd.DataFrame(table_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("축별 변화 데이터가 없습니다.")
        
        with tab2:
            # 라인 차트 생성
            chart_data = {}
            for axis in axis_order:
                if axis in axis_data:
                    axis_name = CATEGORY_LABELS.get(axis, axis)
                    scores = axis_data[axis][:10]  # 최신 10개만
                    # 날짜와 매칭 (역순이므로 뒤집기)
                    dates = list(reversed(session_dates[:len(scores)]))
                    chart_data[axis_name] = dict(zip(dates, scores))
            
            if chart_data:
                df_chart = pd.DataFrame(chart_data)
                st.line_chart(df_chart, use_container_width=True)
            else:
                st.info("차트 데이터가 없습니다.")
    
    except Exception as e:
        logger.warning(f"_render_axis_trend: Error - {e}")
        st.info("축별 변화 추이를 생성할 수 없습니다.")


def _render_zone_g_next_checkup(store_id: str):
    """ZONE G: 다음 체크 & CTA"""
    st.markdown("### 📅 다음 체크")
    
    st.info("""
    **권장 주기:** 월 2-3회 (약 2주마다)
    
    정기적인 매장 체크리스트를 통해 운영 전반의 위험 신호를 조기에 발견하고 개선할 수 있습니다.
    """)
    
    if st.button("매장 체크리스트 다시하기", type="primary", use_container_width=True):
        st.session_state["current_page"] = "건강검진 실시"
        st.rerun()
