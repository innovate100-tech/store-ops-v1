"""
매장 체크리스트 페이지 (리디자인)
QSCPPPMHF 9개 영역 매장 체크리스트 UI - 빠른 입력 중심
"""
from src.bootstrap import bootstrap
import streamlit as st
import logging
import time
from datetime import datetime
from typing import Dict, Optional, List
from src.ui_helpers import render_page_header, handle_data_error, render_section_header
from src.auth import get_current_store_id
from src.health_check.storage import (
    create_health_session,
    upsert_health_answers_batch,
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

# 상수
MIN_COMPLETION_RATIO = 0.8  # 완료 가능 최소 비율 (80%)
TOTAL_QUESTIONS = 90  # 전체 문항 수
AUTO_SAVE_DELAY = 2.0  # 자동 저장 지연 시간 (초)


def render_health_check_page():
    """매장 체크리스트 페이지 렌더링 (리디자인)"""
    render_page_header("QSC 입력", "📋")
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    # 페이지 설명
    st.info("""
    **월 2-3회, 7-10분 정기 매장 체크리스트**
    
    결과는 HOME/전략엔진에 반영됩니다(예정)
    """)
    
    # 세션 상태 확인
    session_id = st.session_state.get('health_session_id')
    view_mode = st.session_state.get('health_check_view_mode', 'input')
    
    # 세션이 있으면 완료 여부 확인
    if session_id:
        session = get_health_session(session_id)
        if session and session.get('completed_at'):
            if view_mode == 'input':
                # 완료된 세션을 입력 모드로 보려고 하면 초기화
                _clear_session_state()
                session_id = None
        else:
            # 진행 중인 세션
            pass
    
    # 최근 미완료 세션 확인
    if not session_id:
        latest_open = load_latest_open_session(store_id)
        if latest_open:
            session_id = latest_open['id']
            st.session_state['health_session_id'] = session_id
            _clear_session_state()
            st.info(f"📝 진행 중인 체크가 있습니다. 이어서 진행하세요. (시작: {latest_open['started_at'][:10]})")
    
    # view_mode가 'result'이고 세션이 완료되었으면 결과 리포트 표시
    if session_id and view_mode == 'result':
        session = get_health_session(session_id)
        if session and session.get('completed_at'):
            st.info("📊 체크 결과를 확인하세요.")
            try:
                render_result_report(store_id, session_id)
            except Exception as e:
                logger.error(f"Error rendering result report: {e}", exc_info=True)
                st.error(f"결과 리포트를 표시하는 중 오류가 발생했습니다: {e}")
            
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("← 체크 입력으로 돌아가기", use_container_width=True):
                    st.session_state['health_check_view_mode'] = 'input'
                    st.rerun()
            return
    
    # 세션이 있으면 입력 폼 표시
    if session_id:
        # 탭: 입력 / 결과 / 이력
        tab1, tab2, tab3 = st.tabs(["📝 체크 입력", "📊 결과 리포트", "📋 체크 이력"])
        
        with tab1:
            render_input_form_redesigned(store_id, session_id)
        
        with tab2:
            try:
                render_result_report(store_id, session_id)
            except Exception as e:
                logger.error(f"Error rendering result report in tab: {e}", exc_info=True)
                st.error(f"결과 리포트를 표시하는 중 오류가 발생했습니다: {e}")
        
        with tab3:
            render_history(store_id)
    else:
        # 세션이 없으면 시작 화면
        render_start_screen(store_id)
        
        # 이력은 별도 섹션으로
        st.markdown("---")
        render_history(store_id)


def _clear_session_state():
    """세션 상태 초기화"""
    keys_to_remove = []
    for key in list(st.session_state.keys()):
        if (key.startswith("hc_") or 
            key.startswith("qsc_") or
            key.startswith("answer_") or 
            key.startswith("q_") or 
            key.startswith("health_check_answer_count_")):
            keys_to_remove.append(key)
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]


def render_start_screen(store_id: str):
    """체크 시작 화면"""
    st.markdown("### 🚀 새 체크 시작")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        매장 체크리스트를 시작하면 9개 영역(Q, S, C, P1, P2, P3, M, H, F)에 대해
        각 10문항씩 총 90문항을 답변하게 됩니다.
        
        **예상 소요 시간**: 7-10분
        """)
    
    with col2:
        if st.button("📋 새 체크 시작", type="primary", use_container_width=True):
            session_id, error_msg = create_health_session(store_id, check_type='monthly')
            if session_id:
                _clear_session_state()
                st.session_state['health_session_id'] = session_id
                st.session_state['health_check_view_mode'] = 'input'
                st.success("체크가 시작되었습니다!")
                st.rerun()
            else:
                st.error(f"체크 시작에 실패했습니다.\n\n{error_msg or '알 수 없는 오류가 발생했습니다.'}")
                
                if error_msg and "테이블이 생성되지 않았습니다" in error_msg:
                    st.info("""
                    **해결 방법:**
                    1. Supabase 대시보드 → SQL Editor로 이동
                    2. `sql/health_check_phase1.sql` 파일 내용을 복사하여 실행
                    3. 페이지를 새로고침하고 다시 시도
                    """)


def _initialize_health_check_state(store_id: str, session_id: str):
    """매장 체크리스트 session_state 초기화 (초기 1회만 DB 로드)"""
    hc_loaded_key = "qsc_loaded_session_id"
    hc_answers_key = "qsc_answers"
    hc_dirty_key = "qsc_dirty"
    
    # 세션이 변경되었거나 처음 로드하는 경우
    current_loaded = st.session_state.get(hc_loaded_key)
    if current_loaded != session_id:
        # 기존 답변 상태 초기화
        st.session_state[hc_answers_key] = {}
        st.session_state[hc_dirty_key] = set()
        
        # 기존 session_state 키들 정리
        keys_to_remove = []
        for key in st.session_state.keys():
            if (key.startswith("qsc_btn_") or 
                key.startswith("answer_") or 
                key.startswith("q_") or 
                key.startswith("health_check_answer_count_")):
                keys_to_remove.append(key)
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
        
        # DB에서 기존 답변 로드 (초기 1회만)
        try:
            existing_answers = get_health_answers(session_id)
            for ans in existing_answers:
                category = ans.get('category')
                question_code = ans.get('question_code')
                raw_value = ans.get('raw_value')
                if category and question_code and raw_value:
                    key = (category, question_code)
                    st.session_state[hc_answers_key][key] = raw_value
        except Exception as e:
            logger.error(f"Error loading answers: {e}")
        
        # 로드 완료 표시
        st.session_state[hc_loaded_key] = session_id


def _save_answers_batch(store_id: str, session_id: str) -> tuple[bool, Optional[str]]:
    """dirty 답변 일괄 저장"""
    hc_answers_key = "qsc_answers"
    hc_dirty_key = "qsc_dirty"
    
    dirty = st.session_state.get(hc_dirty_key, set())
    if not dirty:
        return True, None
    
    answers = st.session_state.get(hc_answers_key, {})
    rows = []
    for (category, question_code) in dirty:
        raw_value = answers.get((category, question_code))
        if raw_value and raw_value in ["yes", "maybe", "no"]:
            rows.append({
                "category": category,
                "question_code": question_code,
                "raw_value": raw_value
            })
    
    if not rows:
        return True, None
    
    success, error_msg = upsert_health_answers_batch(store_id, session_id, rows)
    if success:
        st.session_state[hc_dirty_key] = set()
    return success, error_msg


def render_input_form_redesigned(store_id: str, session_id: str):
    """입력 폼 렌더링 (리디자인) - 버튼 그리드 방식"""
    # session_state 초기화 (초기 1회만 DB 로드)
    _initialize_health_check_state(store_id, session_id)
    
    hc_answers_key = "qsc_answers"
    hc_dirty_key = "qsc_dirty"
    
    # 답변 개수 계산
    answers = st.session_state.get(hc_answers_key, {})
    valid_values = ["yes", "maybe", "no"]
    answered_count = len([v for v in answers.values() if v in valid_values])
    dirty_count = len(st.session_state.get(hc_dirty_key, set()))
    
    # 영역별 진행률 계산
    category_progress = {}
    for category in CATEGORIES_ORDER:
        category_questions = QUESTIONS.get(category, [])
        category_answered = 0
        for q in category_questions:
            key = (category, q['code'])
            if answers.get(key) in valid_values:
                category_answered += 1
        category_progress[category] = {
            'answered': category_answered,
            'total': len(category_questions),
            'ratio': category_answered / len(category_questions) if len(category_questions) > 0 else 0
        }
    
    # 진행률 계산
    progress_ratio = answered_count / TOTAL_QUESTIONS if TOTAL_QUESTIONS > 0 else 0.0
    can_complete = answered_count >= 60  # 최소 60개 이상
    
    # ============================================
    # ZONE A: 대시보드 & 진행 상황
    # ============================================
    render_section_header("📊 진행 상황 대시보드", "📊")
    
    # 핵심 지표 카드
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("전체 문항", f"{TOTAL_QUESTIONS}개")
    with col2:
        st.metric("완료 문항", f"{answered_count}개", delta=f"{TOTAL_QUESTIONS - answered_count}개 남음")
    with col3:
        st.metric("미완료", f"{TOTAL_QUESTIONS - answered_count}개")
    with col4:
        completion_rate = (answered_count / TOTAL_QUESTIONS * 100) if TOTAL_QUESTIONS > 0 else 0
        st.metric("완료율", f"{completion_rate:.0f}%")
    
    # 진행률 바
    st.progress(min(progress_ratio, 1.0))
    st.caption(f"진행률: {answered_count}/{TOTAL_QUESTIONS} 문항 완료 ({progress_ratio*100:.1f}%)")
    
    # 영역별 진행률
    st.markdown("### 영역별 진행률")
    progress_cols = st.columns(9)
    for idx, category in enumerate(CATEGORIES_ORDER):
        with progress_cols[idx]:
            cat_progress = category_progress[category]
            st.progress(cat_progress['ratio'])
            st.caption(f"{category}: {cat_progress['answered']}/{cat_progress['total']}")
    
    # 스마트 알림
    alerts = []
    if dirty_count > 0:
        alerts.append(f"💾 저장되지 않은 변경: {dirty_count}개")
    else:
        alerts.append("✅ 모든 변경사항이 저장되었습니다.")
    
    incomplete_categories = [cat for cat, prog in category_progress.items() if prog['answered'] < prog['total']]
    if incomplete_categories:
        alerts.append(f"ℹ️ 미완료 영역: {', '.join(incomplete_categories)}")
    
    if can_complete:
        alerts.append(f"✅ 완료 가능합니다! ({answered_count}개 답변 완료)")
    else:
        needed = 60
        remaining = needed - answered_count
        alerts.append(f"💡 최소 {needed}개 문항을 답변해야 완료할 수 있습니다. (현재: {answered_count}개, 남은 문항: {remaining}개)")
    
    for alert in alerts:
        if "저장되지 않은" in alert:
            st.warning(alert)
        elif "완료 가능" in alert:
            st.success(alert)
        else:
            st.info(alert)
    
    st.markdown("---")
    
    # ============================================
    # 필터 & 네비게이션
    # ============================================
    col1, col2 = st.columns([2, 1])
    with col1:
        category_filter = st.multiselect(
            "영역 필터",
            options=["전체"] + CATEGORIES_ORDER,
            default=["전체"],
            key="qsc_category_filter"
        )
    with col2:
        search_term = st.text_input(
            "🔍 질문 검색",
            key="qsc_search",
            placeholder="질문 코드 또는 텍스트로 검색..."
        )
    
    st.markdown("---")
    
    # ============================================
    # ZONE B: 빠른 입력 테이블 (핵심)
    # ============================================
    render_section_header("📝 빠른 입력", "📝")
    
    # 모든 질문 수집
    all_questions = []
    for category in CATEGORIES_ORDER:
        category_questions = QUESTIONS.get(category, [])
        for q in category_questions:
            all_questions.append({
                'category': category,
                'code': q['code'],
                'text': q['text']
            })
    
    # 필터링 적용
    filtered_questions = all_questions.copy()
    
    # 영역 필터
    if "전체" not in category_filter:
        filtered_questions = [q for q in filtered_questions if q['category'] in category_filter]
    
    # 검색 필터
    if search_term and search_term.strip():
        search_lower = search_term.lower()
        filtered_questions = [
            q for q in filtered_questions
            if search_lower in q['code'].lower() or search_lower in q['text'].lower()
        ]
    
    # 질문 렌더링 (영역별로 그룹화)
    current_category = None
    for question in filtered_questions:
        category = question['category']
        
        # 영역 헤더 표시
        if category != current_category:
            if current_category is not None:
                st.markdown("---")
            st.markdown(f"### {category} ({CATEGORY_LABELS.get(category, category)})")
            current_category = category
        
        # 질문별 버튼 그리드 렌더링
        render_question_buttons(store_id, session_id, category, question['code'], question['text'])
    
    st.markdown("---")
    
    # ============================================
    # ZONE C: 저장 & 완료
    # ============================================
    render_section_header("💾 저장 & 완료", "💾")
    
    # 저장 상태 표시
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if dirty_count > 0:
            st.warning(f"💾 저장되지 않은 변경: {dirty_count}개")
        else:
            st.success("✅ 모든 변경사항이 저장되었습니다.")
        
        # 마지막 저장 시간 표시
        last_save_time = st.session_state.get('qsc_last_save_time')
        if last_save_time:
            st.caption(f"마지막 저장: {datetime.fromtimestamp(last_save_time).strftime('%Y-%m-%d %H:%M:%S')}")
    
    with col2:
        if st.button("💾 수동 저장", use_container_width=True, disabled=dirty_count == 0):
            success, error_msg = _save_answers_batch(store_id, session_id)
            if success:
                st.session_state['qsc_last_save_time'] = time.time()
                st.success("저장되었습니다!")
                st.rerun()
            else:
                st.error(f"저장 실패: {error_msg}")
    
    with col3:
        if st.button("🔄 초기화", use_container_width=True, type="secondary"):
            _clear_session_state()
            st.success("상태가 초기화되었습니다.")
            st.rerun()
    
    # 완료 버튼
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if can_complete:
            if st.button("✅ 체크 완료", type="primary", use_container_width=True):
                # dirty가 있으면 먼저 저장
                if dirty_count > 0:
                    success, error_msg = _save_answers_batch(store_id, session_id)
                    if not success:
                        st.error(f"저장 실패: {error_msg}")
                        return
                
                # finalize 실행
                success = finalize_health_session(store_id, session_id)
                if success:
                    _clear_session_state()
                    if 'health_session_id' in st.session_state:
                        del st.session_state['health_session_id']
                    if 'health_check_view_mode' in st.session_state:
                        del st.session_state['health_check_view_mode']
                    st.success("체크가 완료되었습니다!")
                    st.rerun()
                else:
                    st.error("체크 완료 처리에 실패했습니다.")
        else:
            st.button("⏳ 완료 불가", disabled=True, use_container_width=True)


def render_question_buttons(store_id: str, session_id: str, category: str, question_code: str, question_text: str):
    """질문별 버튼 그리드 렌더링"""
    hc_answers_key = "qsc_answers"
    hc_dirty_key = "qsc_dirty"
    
    # 현재 답변 가져오기
    key = (category, question_code)
    answers = st.session_state.get(hc_answers_key, {})
    current_value = answers.get(key)
    
    # 버튼 옵션
    options = [
        ("예", "yes", "#22C55E"),
        ("애매함", "maybe", "#F59E0B"),
        ("아니다", "no", "#EF4444")
    ]
    
    # 질문 텍스트와 버튼 그리드
    col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
    
    with col1:
        st.markdown(f"**{question_code}** {question_text}")
    
    # 버튼 그리드
    for idx, (label, raw_value, color) in enumerate(options):
        with [col2, col3, col4][idx]:
            is_selected = current_value == raw_value
            button_type = "primary" if is_selected else "secondary"
            
            button_key = f"qsc_btn_{session_id}_{category}_{question_code}_{raw_value}"
            
            if st.button(
                label,
                key=button_key,
                type=button_type,
                use_container_width=True
            ):
                # 답변 업데이트
                if hc_answers_key not in st.session_state:
                    st.session_state[hc_answers_key] = {}
                st.session_state[hc_answers_key][key] = raw_value
                
                # dirty에 추가
                if hc_dirty_key not in st.session_state:
                    st.session_state[hc_dirty_key] = set()
                st.session_state[hc_dirty_key].add(key)
                
                # 즉시 저장 (단일 답변)
                try:
                    rows = [{
                        "category": category,
                        "question_code": question_code,
                        "raw_value": raw_value
                    }]
                    success, error_msg = upsert_health_answers_batch(store_id, session_id, rows)
                    if success:
                        st.session_state[hc_dirty_key].discard(key)
                        st.session_state['qsc_last_save_time'] = time.time()
                    else:
                        logger.warning(f"Auto-save failed for {question_code}: {error_msg}")
                except Exception as e:
                    logger.error(f"Auto-save error for {question_code}: {e}")
                
                st.rerun()


def render_result_report(store_id: str, session_id: str):
    """결과 리포트 렌더링"""
    try:
        session = get_health_session(session_id)
        if not session:
            st.warning("세션 정보를 찾을 수 없습니다.")
            return
        
        # 완료되지 않은 세션
        if not session.get('completed_at'):
            st.info("체크를 완료하면 결과를 확인할 수 있습니다.")
            return
    except Exception as e:
        logger.error(f"Error loading session: {e}")
        st.error(f"세션 정보를 불러오는 중 오류가 발생했습니다: {e}")
        return
    
    # 전체 점수/등급/병목
    st.markdown("### 📊 체크 결과")
    
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
    try:
        results = get_health_results(session_id)
    except Exception as e:
        logger.error(f"Error loading results: {e}", exc_info=True)
        st.error(f"결과를 불러오는 중 오류가 발생했습니다: {e}")
        return
    
    if not results:
        st.warning("결과 데이터가 없습니다. 체크가 완료되었지만 결과가 저장되지 않았을 수 있습니다.")
        return
    
    try:
        st.markdown("### 📋 영역별 결과")
        
        # 결과를 카테고리별로 정리
        results_dict = {}
        for r in results:
            if r and isinstance(r, dict) and 'category' in r:
                results_dict[r['category']] = r
        
        # 테이블 데이터 준비
        table_data = []
        for category in CATEGORIES_ORDER:
            if category in results_dict:
                r = results_dict[category]
                score_avg = r.get('score_avg')
                risk_level = r.get('risk_level', 'unknown')
                
                if score_avg is None:
                    continue
                
                try:
                    risk_emoji = {'green': '🟢', 'yellow': '🟡', 'red': '🔴'}.get(risk_level, '⚪')
                    table_data.append({
                        '영역': f"{category} ({CATEGORY_LABELS.get(category, category)})",
                        '점수': f"{float(score_avg):.1f}점",
                        '리스크': f"{risk_emoji} {risk_level}"
                    })
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error formatting result for category {category}: {e}")
                    continue
        
        if table_data:
            import pandas as pd
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("표시할 결과 데이터가 없습니다.")
        
        # 병목 TOP 2 요약
        st.markdown("---")
        st.markdown("### ⚠️ 주요 병목")
        
        sorted_results = []
        for r in results:
            if r and isinstance(r, dict):
                score_avg = r.get('score_avg')
                if score_avg is not None:
                    try:
                        score = float(score_avg)
                        if score < 75:
                            sorted_results.append(r)
                    except (ValueError, TypeError):
                        continue
        
        sorted_results = sorted(
            sorted_results,
            key=lambda x: float(x.get('score_avg', 100))
        )[:2]
        
        if sorted_results:
            for i, r in enumerate(sorted_results, 1):
                try:
                    category = r.get('category', 'N/A')
                    score_avg = r.get('score_avg', 0)
                    risk_level = r.get('risk_level', 'unknown')
                    
                    score = float(score_avg) if score_avg is not None else 0
                    category_name = CATEGORY_LABELS.get(category, category)
                    risk_emoji = {'green': '🟢', 'yellow': '🟡', 'red': '🔴'}.get(risk_level, '⚪')
                    
                    st.markdown(f"""
                    **{i}. {category_name} ({category})**
                    - 점수: {score:.1f}점
                    - 리스크: {risk_emoji} {risk_level}
                    """)
                except Exception as e:
                    logger.warning(f"Error displaying bottleneck {i}: {e}")
                    continue
        else:
            st.success("✅ 모든 영역이 양호합니다!")
        
        # 다음에 할 것 CTA
        st.markdown("---")
        st.markdown("### 💡 다음에 할 것")
        st.info("""
        체크 결과를 바탕으로 HOME에서 요약을 확인하고,
        전략 엔진에서 개선 전략을 수립하세요.
        
        (향후 HOME/전략엔진 연결 예정)
        """)
    except Exception as e:
        logger.error(f"Error rendering results: {e}", exc_info=True)
        st.error(f"결과를 표시하는 중 오류가 발생했습니다: {e}")
        import traceback
        with st.expander("🔧 에러 상세 정보"):
            st.code(traceback.format_exc(), language="python")


def render_history(store_id: str):
    """체크 이력 렌더링"""
    st.markdown("### 📋 체크 이력 (최근 10개)")
    
    sessions = list_health_sessions(store_id, limit=10)
    
    if not sessions:
        st.info("완료된 체크가 없습니다.")
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
