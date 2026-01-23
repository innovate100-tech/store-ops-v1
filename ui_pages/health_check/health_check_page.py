"""
건강검진 페이지
QSCPPPMHF 9개 영역 건강검진 UI
"""
from src.bootstrap import bootstrap
import streamlit as st
import logging
from datetime import datetime
from typing import Dict, Optional, List
from src.ui_helpers import render_page_header, handle_data_error
from src.auth import get_current_store_id
from src.health_check.storage import (
    create_health_session,
    upsert_health_answer,
    finalize_health_session,
    get_health_session,
    get_health_answers,
    get_health_results,
    load_latest_open_session,
    list_health_sessions
)
from src.health_check.questions_bank import (
    CATEGORIES_ORDER,
    CATEGORY_LABELS,
    QUESTIONS
)

logger = logging.getLogger(__name__)

# 공통 설정 적용
bootstrap(page_title="가게 건강검진")

# 로그인 체크
from src.auth import check_login, show_login_page
if not check_login():
    show_login_page()
    st.stop()

# 상수
MIN_COMPLETION_RATIO = 0.8  # 완료 가능 최소 비율 (80%)
TOTAL_QUESTIONS = 90  # 전체 문항 수


def render_health_check_page():
    """건강검진 페이지 렌더링"""
    render_page_header("가게 건강검진", "🩺")
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    # 페이지 설명
    st.info("""
    **월 2~3회, 7~10분 정기 건강검진**
    
    결과는 HOME/전략엔진에 반영됩니다(예정)
    """)
    
    # 세션 상태 확인
    session_id = st.session_state.get('health_session_id')
    view_mode = st.session_state.get('health_check_view_mode', 'input')  # 'input' or 'result' or 'history'
    
    # 최근 미완료 세션 확인
    if not session_id:
        latest_open = load_latest_open_session(store_id)
        if latest_open:
            session_id = latest_open['id']
            st.session_state['health_session_id'] = session_id
            st.info(f"📝 진행 중인 검진이 있습니다. 이어서 진행하세요. (시작: {latest_open['started_at'][:10]})")
    
    # 탭: 입력 / 결과 / 이력
    if session_id:
        tab1, tab2, tab3 = st.tabs(["📝 검진 입력", "📊 결과 리포트", "📋 검진 이력"])
        
        with tab1:
            render_input_form(store_id, session_id)
        
        with tab2:
            render_result_report(store_id, session_id)
        
        with tab3:
            render_history(store_id)
    else:
        # 세션이 없으면 시작 화면
        render_start_screen(store_id)
        
        # 이력은 별도 탭으로
        st.markdown("---")
        render_history(store_id)


def render_start_screen(store_id: str):
    """검진 시작 화면"""
    st.markdown("### 🚀 새 검진 시작")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        건강검진을 시작하면 9개 영역(Q, S, C, P1, P2, P3, M, H, F)에 대해
        각 10문항씩 총 90문항을 답변하게 됩니다.
        
        **예상 소요 시간**: 7~10분
        """)
    
    with col2:
        if st.button("🩺 새 검진 시작", type="primary", use_container_width=True):
            session_id = create_health_session(store_id, check_type='monthly')
            if session_id:
                st.session_state['health_session_id'] = session_id
                st.session_state['health_check_view_mode'] = 'input'
                st.success("검진이 시작되었습니다!")
                st.rerun()
            else:
                st.error("검진 시작에 실패했습니다.")


def render_input_form(store_id: str, session_id: str):
    """입력 폼 렌더링 (9개 섹션)"""
    # 기존 답변 로드
    existing_answers = get_health_answers(session_id)
    answers_dict = {}
    for ans in existing_answers:
        key = f"{ans['category']}_{ans['question_code']}"
        answers_dict[key] = ans['raw_value']
    
    # 진행률 계산
    answered_count = len(answers_dict)
    progress_ratio = answered_count / TOTAL_QUESTIONS if TOTAL_QUESTIONS > 0 else 0
    can_complete = progress_ratio >= MIN_COMPLETION_RATIO
    
    # 진행률 표시
    st.progress(progress_ratio)
    st.caption(f"진행률: {answered_count}/{TOTAL_QUESTIONS} 문항 완료 ({progress_ratio*100:.1f}%)")
    
    if can_complete:
        st.success(f"✅ 완료 가능합니다! ({answered_count}개 답변 완료)")
    else:
        needed = int(TOTAL_QUESTIONS * MIN_COMPLETION_RATIO)
        st.info(f"💡 최소 {needed}개 문항을 답변해야 완료할 수 있습니다. (현재: {answered_count}개)")
    
    st.markdown("---")
    
    # 저장 상태 추적 (rerun 폭발 방지)
    if 'last_saved_key' not in st.session_state:
        st.session_state['last_saved_key'] = None
    if 'last_saved_time' not in st.session_state:
        st.session_state['last_saved_time'] = None
    
    # 9개 섹션 탭
    category_tabs = st.tabs([f"{cat} ({CATEGORY_LABELS.get(cat, cat)})" for cat in CATEGORIES_ORDER])
    
    for idx, category in enumerate(CATEGORIES_ORDER):
        with category_tabs[idx]:
            render_category_questions(
                store_id, session_id, category, 
                answers_dict, 
                st.session_state.get('last_saved_key'),
                st.session_state.get('last_saved_time')
            )
    
    # 완료 버튼
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if can_complete:
            if st.button("✅ 검진 완료", type="primary", use_container_width=True):
                success = finalize_health_session(store_id, session_id)
                if success:
                    st.session_state['health_check_view_mode'] = 'result'
                    st.success("검진이 완료되었습니다!")
                    st.rerun()
                else:
                    st.error("검진 완료 처리에 실패했습니다.")
        else:
            st.button("⏳ 완료 불가", disabled=True, use_container_width=True)


def render_category_questions(
    store_id: str, 
    session_id: str, 
    category: str, 
    answers_dict: Dict[str, str],
    last_saved_key: Optional[str],
    last_saved_time: Optional[datetime]
):
    """카테고리별 질문 렌더링"""
    category_questions = QUESTIONS.get(category, [])
    
    # 저장 상태 표시
    if last_saved_key and last_saved_key.startswith(category) and last_saved_time:
        time_str = last_saved_time.strftime("%H:%M:%S") if isinstance(last_saved_time, datetime) else str(last_saved_time)
        st.caption(f"💾 마지막 저장: {time_str}")
    
    # 각 질문 렌더링
    for question_item in category_questions:
        question_code = question_item.get("code", "")
        question_text = question_item.get("text", "")
        if not question_code or not question_text:
            continue
        
        key = f"{category}_{question_code}"
        current_value = answers_dict.get(key, None)
        
        # radio 옵션
        options = ["예", "애매함", "아니다"]
        raw_value_map = {"예": "yes", "애매함": "maybe", "아니다": "no"}
        
        # 현재 값에 맞는 인덱스 찾기
        index = None
        if current_value:
            for i, opt in enumerate(options):
                if raw_value_map[opt] == current_value:
                    index = i
                    break
        
        # session_state에 변경사항 추적
        answer_state_key = f"answer_{category}_{question_code}"
        if answer_state_key not in st.session_state:
            st.session_state[answer_state_key] = current_value
        
        selected = st.radio(
            question_text,
            options=options,
            index=index,
            key=f"q_{category}_{question_code}",
            horizontal=True
        )
        
        # 값이 변경되었고, 이전에 저장한 키와 다르면 저장 (rerun 폭발 방지)
        new_raw_value = raw_value_map[selected]
        stored_value = st.session_state.get(answer_state_key)
        
        if new_raw_value != stored_value:
            # debounce: 같은 키를 연속으로 저장하지 않음
            if last_saved_key != key:
                try:
                    success = upsert_health_answer(
                        store_id=store_id,
                        session_id=session_id,
                        category=category,
                        question_code=question_code,
                        raw_value=new_raw_value,
                        memo=None
                    )
                    if success:
                        st.session_state['last_saved_key'] = key
                        st.session_state['last_saved_time'] = datetime.now()
                        st.session_state[answer_state_key] = new_raw_value
                        # 작은 성공 메시지 (선택적, rerun 방지를 위해 주석 처리)
                        # st.success("✓", icon="✅")
                    else:
                        st.warning(f"⚠️ 저장 실패: {question_code}")
                except Exception as e:
                    logger.error(f"Error saving answer: {e}")
                    st.warning(f"⚠️ 저장 중 오류 발생: {question_code}")


def render_result_report(store_id: str, session_id: str):
    """결과 리포트 렌더링"""
    session = get_health_session(session_id)
    if not session:
        st.warning("세션 정보를 찾을 수 없습니다.")
        return
    
    # 완료되지 않은 세션
    if not session.get('completed_at'):
        st.info("검진을 완료하면 결과를 확인할 수 있습니다.")
        return
    
    # 전체 점수/등급/병목
    st.markdown("### 📊 검진 결과")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        overall_score = session.get('overall_score', 0)
        st.metric("전체 점수", f"{overall_score:.1f}점")
    
    with col2:
        overall_grade = session.get('overall_grade', 'E')
        grade_colors = {'A': '🟢', 'B': '🟡', 'C': '🟠', 'D': '🔴', 'E': '⚫'}
        st.metric("등급", f"{grade_colors.get(overall_grade, '⚪')} {overall_grade}")
    
    with col3:
        main_bottleneck = session.get('main_bottleneck', 'N/A')
        bottleneck_name = CATEGORY_LABELS.get(main_bottleneck, main_bottleneck)
        st.metric("주요 병목", bottleneck_name)
    
    st.markdown("---")
    
    # 카테고리별 결과
    results = get_health_results(session_id)
    if results:
        st.markdown("### 📋 영역별 결과")
        
        # 결과를 카테고리별로 정리
        results_dict = {r['category']: r for r in results}
        
        # 테이블 데이터 준비
        table_data = []
        for category in CATEGORIES_ORDER:
            if category in results_dict:
                r = results_dict[category]
                risk_emoji = {'green': '🟢', 'yellow': '🟡', 'red': '🔴'}.get(r['risk_level'], '⚪')
                table_data.append({
                    '영역': f"{category} ({CATEGORY_LABELS.get(category, category)})",
                    '점수': f"{r['score_avg']:.1f}점",
                    '리스크': f"{risk_emoji} {r['risk_level']}"
                })
        
        if table_data:
            import pandas as pd
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        # 병목 TOP 2 요약
        st.markdown("---")
        st.markdown("### ⚠️ 주요 병목")
        
        # 점수가 낮은 순으로 정렬
        sorted_results = sorted(
            [r for r in results if r.get('score_avg', 100) < 75],
            key=lambda x: x.get('score_avg', 100)
        )[:2]
        
        if sorted_results:
            for i, r in enumerate(sorted_results, 1):
                category = r['category']
                score = r['score_avg']
                risk = r['risk_level']
                category_name = CATEGORY_NAMES.get(category, category)
                risk_emoji = {'green': '🟢', 'yellow': '🟡', 'red': '🔴'}.get(risk, '⚪')
                
                st.markdown(f"""
                **{i}. {category_name} ({category})**
                - 점수: {score:.1f}점
                - 리스크: {risk_emoji} {risk}
                """)
        else:
            st.success("✅ 모든 영역이 양호합니다!")
        
        # 다음에 할 것 CTA
        st.markdown("---")
        st.markdown("### 💡 다음에 할 것")
        st.info("""
        검진 결과를 바탕으로 HOME에서 요약을 확인하고,
        전략 엔진에서 개선 전략을 수립하세요.
        
        (향후 HOME/전략엔진 연결 예정)
        """)
    else:
        st.warning("결과 데이터를 찾을 수 없습니다.")


def render_history(store_id: str):
    """검진 이력 렌더링"""
    st.markdown("### 📋 검진 이력 (최근 10개)")
    
    sessions = list_health_sessions(store_id, limit=10)
    
    if not sessions:
        st.info("완료된 검진이 없습니다.")
        return
    
    # 이력 목록
    for session in sessions:
        completed_at = session.get('completed_at', '')
        overall_score = session.get('overall_score', 0)
        overall_grade = session.get('overall_grade', 'E')
        main_bottleneck = session.get('main_bottleneck', 'N/A')
        
        # 날짜 포맷
        date_str = completed_at[:10] if completed_at else 'N/A'
        
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.write(f"**{date_str}**")
        with col2:
            st.write(f"{overall_score:.1f}점")
        with col3:
            grade_colors = {'A': '🟢', 'B': '🟡', 'C': '🟠', 'D': '🔴', 'E': '⚫'}
            st.write(f"{grade_colors.get(overall_grade, '⚪')} {overall_grade}")
        with col4:
            if st.button("보기", key=f"view_{session['id']}"):
                st.session_state['health_session_id'] = session['id']
                st.session_state['health_check_view_mode'] = 'result'
                st.rerun()
        
        st.markdown("---")
