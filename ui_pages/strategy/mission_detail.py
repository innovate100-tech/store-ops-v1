"""
전략 실행 미션 상세 화면 (체크리스트)
"""
from __future__ import annotations

import streamlit as st
from datetime import date, datetime
from zoneinfo import ZoneInfo
from typing import Optional

from src.bootstrap import bootstrap
from src.ui_helpers import render_page_header
from src.storage_supabase import (
    load_active_mission,
    load_mission_tasks,
    create_or_get_today_mission,
    create_mission_tasks,
    update_task_done,
    set_mission_status,
)
from src.auth import get_current_store_id, is_dev_mode
from ui_pages.analysis.strategy_engine import (
    pick_primary_strategy,
    get_checklist_template,
)

# 공통 설정 적용
bootstrap(page_title="오늘의 전략 실행")


def render_mission_detail():
    """미션 상세 화면 렌더링"""
    render_page_header("🎯 오늘의 전략 실행", "🎯")
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    kst = ZoneInfo("Asia/Seoul")
    today = datetime.now(kst).date()
    
    # 오늘의 미션 로드 또는 생성
    mission = load_active_mission(store_id, today)
    
    if not mission:
        # 미션 생성
        strategy = pick_primary_strategy(store_id, ref_date=today, window_days=14)
        if not strategy:
            st.warning("오늘의 전략을 생성할 수 없습니다. 데이터가 부족할 수 있습니다.")
            if st.button("📋 오늘 입력(마감/보정) 하러가기", key="goto_input"):
                st.session_state["current_page"] = "점장 마감"
                st.rerun()
            return
        
        # 원인 타입 추론 (신호에서 직접 가져오기)
        from ui_pages.analysis.strategy_engine import get_sales_drop_signals, classify_cause_type
        signals = get_sales_drop_signals(store_id, today, 14)
        causes = classify_cause_type(signals)
        cause_type = causes[0].get("type", "판매량 하락형") if causes else "판매량 하락형"
        
        reason_json = {
            "bullets": strategy.get("reason_bullets", []),
        }
        
        mission_id = create_or_get_today_mission(
            store_id=store_id,
            mission_date=today,
            cause_type=cause_type,
            title=strategy.get("title", "오늘 할 일"),
            reason_json=reason_json,
            cta_page=strategy.get("cta_page", "홈")
        )
        
        if mission_id:
            # 체크리스트 생성
            tasks = get_checklist_template(cause_type)
            create_mission_tasks(mission_id, tasks)
            
            # 다시 로드
            mission = load_active_mission(store_id, today)
        else:
            st.error("미션 생성에 실패했습니다.")
            return
    
    if not mission:
        st.error("미션을 불러올 수 없습니다.")
        return
    
    # 미션 헤더
    _render_mission_header(mission)
    
    # 근거
    reason_json = mission.get("reason_json", {})
    if isinstance(reason_json, dict):
        bullets = reason_json.get("bullets", [])
        if bullets:
            st.markdown("**근거:**")
            for bullet in bullets:
                st.markdown(f"- {bullet}")
    
    st.markdown("---")
    
    # 체크리스트
    mission_id = mission["id"]
    tasks = load_mission_tasks(mission_id)
    
    if not tasks:
        # 체크리스트가 없으면 생성
        cause_type = mission.get("cause_type", "")
        tasks_template = get_checklist_template(cause_type)
        if create_mission_tasks(mission_id, tasks_template):
            tasks = load_mission_tasks(mission_id)
    
    if tasks:
        _render_checklist(mission_id, tasks)
    else:
        st.info("체크리스트를 생성하는 중입니다...")
    
    st.markdown("---")
    
    # 버튼
    col1, col2, col3 = st.columns(3)
    with col1:
        cta_page = mission.get("cta_page", "홈")
        if st.button("🔧 관련 도구 열기", key="goto_tool", use_container_width=True):
            st.session_state["current_page"] = cta_page
            st.rerun()
    
    with col2:
        # 진행률 계산
        done_count = sum(1 for t in tasks if t.get("is_done", False))
        total_count = len(tasks)
        all_done = (done_count == total_count) if total_count > 0 else False
        
        if st.button("✅ 오늘 미션 완료 처리", key="complete_mission", use_container_width=True):
            # completed → monitoring으로 자동 전환
            if set_mission_status(mission_id, "completed"):
                # monitoring 상태로 전환
                from src.storage_supabase import set_mission_status as update_status
                update_status(mission_id, "monitoring")
                st.success("미션이 완료되었습니다! 7일 후 자동으로 효과를 평가합니다.")
                st.rerun()
            else:
                st.error("완료 처리에 실패했습니다.")
    
    with col3:
        if st.button("❌ 미션 포기", key="abandon_mission", use_container_width=True):
            if set_mission_status(mission_id, "abandoned"):
                st.info("미션이 포기되었습니다.")
                st.session_state["current_page"] = "홈"
                st.rerun()
            else:
                st.error("포기 처리에 실패했습니다.")
    
    # 효과 비교 (7일 후) - monitoring/evaluated 미션
    if mission.get("status") in ["monitoring", "evaluated"]:
        _render_effect_comparison(store_id, mission)
    
    # 다음 개입 제안 (evaluated 미션만)
    if mission.get("status") == "evaluated":
        _render_next_intervention(store_id, mission)




def _render_mission_header(mission: dict):
    """미션 헤더 렌더링"""
    title = mission.get("title", "오늘 할 일")
    cause_type = mission.get("cause_type", "")
    mission_date = mission.get("mission_date", "")
    
    # 원인 타입 배지
    cause_badges = {
        "유입 감소형": "🔵",
        "객단가 하락형": "🟡",
        "판매량 하락형": "🟠",
        "주력메뉴 붕괴형": "🔴",
        "원가율 악화형": "🟣",
        "구조 리스크형": "⚫",
    }
    badge = cause_badges.get(cause_type, "📌")
    
    st.markdown(f"""
    <div style="padding: 1.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 1rem; color: white;">
        <h2 style="color: white; margin: 0 0 0.5rem 0;">{badge} {title}</h2>
        <div style="color: rgba(255,255,255,0.9); font-size: 0.9rem;">
            {cause_type} · 생성일: {mission_date}
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_checklist(mission_id: str, tasks: list):
    """체크리스트 렌더링"""
    st.markdown("### ✅ 체크리스트")
    
    done_count = sum(1 for t in tasks if t.get("is_done", False))
    total_count = len(tasks)
    progress = (done_count / total_count * 100) if total_count > 0 else 0
    
    # 진행률
    st.progress(progress / 100)
    st.caption(f"완료: {done_count} / {total_count} ({progress:.0f}%)")
    
    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
    
    # 체크리스트 항목
    for task in tasks:
        task_id = task["id"]
        task_title = task["task_title"]
        is_done = task.get("is_done", False)
        task_order = task.get("task_order", 0)
        
        col1, col2 = st.columns([1, 20])
        with col1:
            new_done = st.checkbox(
                "",
                value=is_done,
                key=f"task_{task_id}",
                label_visibility="collapsed"
            )
            if new_done != is_done:
                # 즉시 DB 업데이트
                if update_task_done(task_id, new_done):
                    st.rerun()
        
        with col2:
            style = "text-decoration: line-through; color: #888;" if is_done else ""
            st.markdown(f"""
            <div style="{style}">
                {task_order}. {task_title}
            </div>
            """, unsafe_allow_html=True)


def _render_effect_comparison(store_id: str, mission: dict):
    """7일 후 효과 비교 렌더링"""
    st.markdown("---")
    st.markdown("### 📊 전략 결과 판정")
    
    # 상태 타임라인
    status = mission.get("status", "active")
    status_labels = {
        "active": "🛠 실행중",
        "completed": "✅ 완료",
        "monitoring": "👀 감시중",
        "evaluated": "🧠 판정완료",
        "abandoned": "❌ 포기",
    }
    st.caption(f"상태: {status_labels.get(status, status)}")
    
    # 평가 결과가 있으면 표시
    result_type = mission.get("result_type")
    coach_comment = mission.get("coach_comment")
    
    if result_type and coach_comment:
        # 결과 배지
        result_badges = {
            "improved": "✅ 개선",
            "no_change": "➡️ 정체",
            "worsened": "⚠️ 악화",
            "data_insufficient": "📊 데이터 부족",
        }
        badge = result_badges.get(result_type, result_type)
        
        st.markdown(f"""
        <div style="padding: 1rem; background: #f8f9fa; border-left: 4px solid #667eea; border-radius: 5px; margin-bottom: 1rem;">
            <strong>{badge}</strong><br>
            {coach_comment}
        </div>
        """, unsafe_allow_html=True)
    
    # 효과 비교 데이터
    try:
        from src.storage_supabase import load_mission_result
        
        result = load_mission_result(mission["id"])
        if result:
            delta = result.get("delta_json", {})
            baseline = result.get("baseline_json", {})
            after = result.get("after_json", {})
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                sales_delta = delta.get("sales_delta_pct", 0)
                sales_emoji = "📈" if sales_delta > 0 else "📉" if sales_delta < 0 else "➡️"
                st.metric("매출(일평균)", f"{sales_delta:+.1f}%", delta=f"{sales_emoji}")
            
            with col2:
                visitors_delta = delta.get("visitors_delta_pct", 0)
                visitors_emoji = "📈" if visitors_delta > 0 else "📉" if visitors_delta < 0 else "➡️"
                st.metric("네이버방문자(일평균)", f"{visitors_delta:+.1f}%", delta=f"{visitors_emoji}")
            
            with col3:
                avgp_delta = delta.get("avgp_delta_pct", 0)
                avgp_emoji = "📈" if avgp_delta > 0 else "📉" if avgp_delta < 0 else "➡️"
                st.metric("객단가", f"{avgp_delta:+.1f}%", delta=f"{avgp_emoji}")
        else:
            # 평가 중이면 평가 시도
            if status == "monitoring":
                from src.strategy.strategy_monitor import evaluate_mission_effect
                evaluation = evaluate_mission_effect(mission, store_id)
                if evaluation:
                    if evaluation.get("result_type") != "data_insufficient":
                        # 자동 저장
                        from src.storage_supabase import update_mission_evaluation, save_mission_result
                        update_mission_evaluation(
                            mission["id"],
                            evaluation.get("result_type", "data_insufficient"),
                            evaluation.get("coach_comment", "")
                        )
                        save_mission_result(
                            mission["id"],
                            evaluation.get("baseline", {}),
                            evaluation.get("after", {}),
                            evaluation.get("delta", {})
                        )
                        st.rerun()
                    else:
                        st.info(evaluation.get("coach_comment", "데이터 수집 중입니다."))
    except Exception as e:
        if is_dev_mode():
            st.error(f"효과 비교 오류: {e}")
        st.info("효과 비교 데이터를 불러올 수 없습니다.")


def _render_next_intervention(store_id: str, mission: dict):
    """다음 개입 제안 렌더링"""
    st.markdown("---")
    st.markdown("### 🎯 다음 개입 제안")
    
    try:
        from src.strategy.strategy_monitor import evaluate_mission_effect
        from src.strategy.strategy_followup import decide_next_intervention
        
        # 평가 결과 로드
        evaluation = evaluate_mission_effect(mission, store_id)
        if not evaluation:
            return
        
        # 다음 개입 결정
        intervention = decide_next_intervention(mission, evaluation)
        if not intervention:
            return
        
        intervention_type = intervention.get("intervention_type", "")
        next_title = intervention.get("next_strategy_title", "")
        next_reason = intervention.get("next_reason_bullets", [])
        next_cta_page = intervention.get("next_cta_page", "홈")
        
        # 개입 타입별 UI
        if intervention_type == "maintain":
            st.success(f"✅ {next_title}")
        elif intervention_type == "pivot":
            st.warning(f"🔄 {next_title}")
        elif intervention_type == "escalate":
            st.error(f"⚠️ {next_title}")
        else:
            st.info(f"⏳ {next_title}")
        
        if next_reason:
            for reason in next_reason:
                st.markdown(f"- {reason}")
        
        if st.button("다음 전략 시작", key="next_strategy", use_container_width=True):
            st.session_state["current_page"] = next_cta_page
            st.rerun()
        
        if st.button("관련 전략 센터 이동", key="goto_design", use_container_width=True):
            st.session_state["current_page"] = "가게 전략 센터"
            st.rerun()
    except Exception as e:
        if is_dev_mode():
            st.error(f"다음 개입 제안 오류: {e}")
