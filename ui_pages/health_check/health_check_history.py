"""
체크 히스토리 페이지
체크 회차별 비교 및 트렌드 표시
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
from src.health_check.questions_bank import CATEGORY_LABELS

logger = logging.getLogger(__name__)

# 공통 설정 적용
bootstrap(page_title="체크 히스토리")


def render_health_check_history():
    """체크 히스토리 페이지 렌더링"""
    render_page_header("체크 히스토리", "📊")
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    try:
        # 완료 체크 세션 리스트 로드 (최근 10개)
        sessions = _load_completed_sessions(store_id, limit=10)
        
        if not sessions:
            _render_no_history_view(store_id)
            return
        
        # 회차 리스트 표시
        st.markdown("### 📋 체크 회차 리스트")
        
        for idx, session in enumerate(sessions, 1):
            _render_session_card(session, idx)
        
        st.divider()
        
        # 축별 변화 표 (간단)
        if len(sessions) >= 2:
            _render_axis_trend_table(sessions)
    
    except Exception as e:
        logger.error(f"render_health_check_history: Error - {e}", exc_info=True)
        st.error("체크 히스토리를 불러오는 중 오류가 발생했습니다.")


@st.cache_data(ttl=300)
def _load_completed_sessions(store_id: str, limit: int = 10) -> List[Dict]:
    """완료 체크 세션 리스트 로드"""
    try:
        from src.auth import get_supabase_client
        supabase = get_supabase_client()
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


def _render_no_history_view(store_id: str):
    """히스토리 없음 안내"""
    st.info("""
    **완료된 체크가 없습니다.**
    
    첫 매장 체크리스트를 실시하면 여기서 회차별 변화를 추적할 수 있습니다.
    """)
    
    if st.button("매장 체크리스트 실시하기", type="primary", use_container_width=True):
        st.session_state["current_page"] = "건강검진 실시"
        st.rerun()


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
            st.session_state["current_page"] = "검진 결과 요약"  # page key 유지
            st.session_state["_health_check_session_id"] = session_id
            st.rerun()
    
    st.divider()


def _render_axis_trend_table(sessions: List[Dict]):
    """축별 변화 표 (간단)"""
    st.markdown("### 📈 축별 변화 추이")
    
    try:
        # 각 세션의 축별 점수 수집
        axis_data = {}  # {axis: [score1, score2, ...]}
        axis_order = ["Q", "S", "C", "P1", "P2", "P3", "M", "H", "F"]
        
        for session in sessions:
            session_id = session["id"]
            results = get_health_results(session_id)
            
            if results:
                for r in results:
                    axis = r.get("category")
                    score_avg = r.get("score_avg")
                    if axis and score_avg is not None:
                        score_10 = float(score_avg) / 10.0
                        if axis not in axis_data:
                            axis_data[axis] = []
                        axis_data[axis].append(score_10)
        
        # 표 생성
        if axis_data:
            import pandas as pd
            
            # 데이터 준비
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
        else:
            st.info("축별 점수 데이터가 없습니다.")
    
    except Exception as e:
        logger.warning(f"_render_axis_trend_table: Error - {e}")
        st.info("축별 변화 표를 생성할 수 없습니다.")
