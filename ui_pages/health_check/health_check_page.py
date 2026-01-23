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
    **월 2-3회, 7-10분 정기 건강검진**
    
    결과는 HOME/전략엔진에 반영됩니다(예정)
    """)
    
    # 세션 상태 확인
    session_id = st.session_state.get('health_session_id')
    view_mode = st.session_state.get('health_check_view_mode', 'input')  # 'input' or 'result' or 'history'
    
    # 세션이 있으면 완료 여부 확인
    if session_id:
        session = get_health_session(session_id)
        if session and session.get('completed_at'):
            # 완료된 세션이지만 view_mode가 'result'면 결과 보기 모드이므로 유지
            # view_mode가 'input'이고 완료된 세션이면 초기화하고 시작 화면으로
            if view_mode == 'input':
                # 완료된 세션을 입력 모드로 보려고 하면 초기화
                if 'health_session_id' in st.session_state:
                    del st.session_state['health_session_id']
                if 'health_check_view_mode' in st.session_state:
                    del st.session_state['health_check_view_mode']
                # 답변 개수 캐시도 초기화
                answer_count_key = f"health_check_answer_count_{session_id}"
                if answer_count_key in st.session_state:
                    del st.session_state[answer_count_key]
                session_id = None
    
    # 최근 미완료 세션 확인
    if not session_id:
        latest_open = load_latest_open_session(store_id)
        if latest_open:
            session_id = latest_open['id']
            st.session_state['health_session_id'] = session_id
            st.info(f"📝 진행 중인 검진이 있습니다. 이어서 진행하세요. (시작: {latest_open['started_at'][:10]})")
    
    # 탭: 입력 / 결과 / 이력
    if session_id:
        # view_mode가 'result'이고 세션이 완료되었으면 결과 리포트를 먼저 표시
        session = get_health_session(session_id)
        if view_mode == 'result' and session and session.get('completed_at'):
            # 결과 리포트를 먼저 표시 (보기 버튼 클릭 시)
            st.info("📊 검진 결과를 확인하세요.")
            try:
                render_result_report(store_id, session_id)
            except Exception as e:
                logger.error(f"Error rendering result report: {e}", exc_info=True)
                st.error(f"결과 리포트를 표시하는 중 오류가 발생했습니다: {e}")
                with st.expander("🔧 에러 상세 정보"):
                    import traceback
                    st.code(traceback.format_exc(), language="python")
            
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("← 검진 입력으로 돌아가기", use_container_width=True):
                    st.session_state['health_check_view_mode'] = 'input'
                    st.rerun()
        else:
            tab1, tab2, tab3 = st.tabs(["📝 검진 입력", "📊 결과 리포트", "📋 검진 이력"])
            
            with tab1:
                render_input_form(store_id, session_id)
            
            with tab2:
                # 결과 리포트 탭
                try:
                    render_result_report(store_id, session_id)
                except Exception as e:
                    logger.error(f"Error rendering result report in tab: {e}", exc_info=True)
                    st.error(f"결과 리포트를 표시하는 중 오류가 발생했습니다: {e}")
                    with st.expander("🔧 에러 상세 정보"):
                        import traceback
                        st.code(traceback.format_exc(), language="python")
            
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
        
        **예상 소요 시간**: 7-10분
        """)
    
    with col2:
        if st.button("🩺 새 검진 시작", type="primary", use_container_width=True):
            session_id, error_msg = create_health_session(store_id, check_type='monthly')
            if session_id:
                st.session_state['health_session_id'] = session_id
                st.session_state['health_check_view_mode'] = 'input'
                st.success("검진이 시작되었습니다!")
                st.rerun()
            else:
                st.error(f"검진 시작에 실패했습니다.\n\n{error_msg or '알 수 없는 오류가 발생했습니다.'}")
                
                # 테이블 미생성 안내
                if error_msg and "테이블이 생성되지 않았습니다" in error_msg:
                    st.info("""
                    **해결 방법:**
                    1. Supabase 대시보드 → SQL Editor로 이동
                    2. `sql/health_check_phase1.sql` 파일 내용을 복사하여 실행
                    3. 페이지를 새로고침하고 다시 시도
                    """)
                
                # 디버그 정보 (DEV 모드에서만)
                if st.session_state.get("dev_mode", False):
                    with st.expander("🔧 디버그 정보"):
                        st.write(f"**store_id**: {store_id}")
                        st.write(f"**에러 메시지**: {error_msg}")
                        try:
                            from src.auth import get_supabase_client
                            supabase = get_supabase_client()
                            st.write(f"**Supabase 클라이언트**: {'있음' if supabase else '없음'}")
                            
                            # 테이블 존재 여부 확인
                            if supabase:
                                try:
                                    test_result = supabase.table("health_check_sessions").select("id").limit(1).execute()
                                    st.write(f"**health_check_sessions 테이블**: 존재함")
                                except Exception as table_error:
                                    st.write(f"**health_check_sessions 테이블**: 존재하지 않음 또는 접근 불가")
                                    st.write(f"**테이블 확인 오류**: {table_error}")
                        except Exception as e:
                            st.write(f"**Supabase 클라이언트 확인 오류**: {e}")


def _initialize_health_check_state(store_id: str, session_id: str):
    """건강검진 session_state 초기화 (초기 1회만 DB 로드)"""
    hc_loaded_key = "hc_loaded_session_id"
    hc_answers_key = "hc_answers"
    hc_dirty_key = "hc_dirty"
    
    # 이미 로드된 세션이면 스킵
    if st.session_state.get(hc_loaded_key) == session_id:
        return
    
    # 답변 초기화
    st.session_state[hc_answers_key] = {}
    st.session_state[hc_dirty_key] = set()
    
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
    hc_answers_key = "hc_answers"
    hc_dirty_key = "hc_dirty"
    
    dirty = st.session_state.get(hc_dirty_key, set())
    if not dirty:
        return True, None
    
    answers = st.session_state.get(hc_answers_key, {})
    rows = []
    for (category, question_code) in dirty:
        raw_value = answers.get((category, question_code))
        if raw_value:
            rows.append({
                "category": category,
                "question_code": question_code,
                "raw_value": raw_value
            })
    
    if not rows:
        return True, None
    
    success, error_msg = upsert_health_answers_batch(store_id, session_id, rows)
    if success:
        # 저장 성공 시 dirty 비우기
        st.session_state[hc_dirty_key] = set()
    return success, error_msg

def render_input_form(store_id: str, session_id: str):
    """입력 폼 렌더링 (9개 섹션) - 임시 저장 방식"""
    # session_state 초기화 (초기 1회만 DB 로드)
    _initialize_health_check_state(store_id, session_id)
    
    hc_answers_key = "hc_answers"
    hc_dirty_key = "hc_dirty"
    
    # 답변 개수 계산
    answers = st.session_state.get(hc_answers_key, {})
    answered_count = len([v for v in answers.values() if v])
    dirty_count = len(st.session_state.get(hc_dirty_key, set()))
    
    progress_ratio = answered_count / TOTAL_QUESTIONS if TOTAL_QUESTIONS > 0 else 0
    can_complete = answered_count >= 60  # 최소 60개 이상
    
    # 진행률 표시
    st.progress(progress_ratio)
    st.caption(f"진행률: {answered_count}/{TOTAL_QUESTIONS} 문항 완료 ({progress_ratio*100:.1f}%)")
    
    # 저장 상태 표시
    if dirty_count > 0:
        st.warning(f"💾 저장되지 않은 변경: {dirty_count}개")
    else:
        st.success("✅ 모든 변경사항이 저장되었습니다.")
    
    if can_complete:
        st.success(f"✅ 완료 가능합니다! ({answered_count}개 답변 완료)")
    else:
        needed = 60
        remaining = needed - answered_count
        st.info(f"💡 최소 {needed}개 문항을 답변해야 완료할 수 있습니다. (현재: {answered_count}개, 남은 문항: {remaining}개)")
    
    st.markdown("---")
    
    # 저장 버튼
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col2:
        if st.button("💾 임시저장(서버에 반영)", use_container_width=True, disabled=dirty_count == 0):
            success, error_msg = _save_answers_batch(store_id, session_id)
            if success:
                st.success("저장되었습니다!")
                st.rerun()
            else:
                st.error(f"저장 실패: {error_msg}")
    
    # 9개 섹션 탭
    category_tabs = st.tabs([f"{cat} ({CATEGORY_LABELS.get(cat, cat)})" for cat in CATEGORIES_ORDER])
    
    for idx, category in enumerate(CATEGORIES_ORDER):
        with category_tabs[idx]:
            render_category_questions(store_id, session_id, category)
    
    # 완료 버튼
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if can_complete:
            if st.button("✅ 검진 완료", type="primary", use_container_width=True):
                # dirty가 있으면 먼저 저장
                if dirty_count > 0:
                    success, error_msg = _save_answers_batch(store_id, session_id)
                    if not success:
                        st.error(f"저장 실패: {error_msg}")
                        return
                
                # finalize 실행
                success = finalize_health_session(store_id, session_id)
                if success:
                    # 세션 상태 초기화
                    if 'health_session_id' in st.session_state:
                        del st.session_state['health_session_id']
                    if 'health_check_view_mode' in st.session_state:
                        del st.session_state['health_check_view_mode']
                    # 답변 상태 초기화
                    for key in ["hc_answers", "hc_dirty", "hc_loaded_session_id"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.success("검진이 완료되었습니다!")
                    st.rerun()
                else:
                    st.error("검진 완료 처리에 실패했습니다.")
        else:
            st.button("⏳ 완료 불가", disabled=True, use_container_width=True)
    
    # DEV 모드 디버그 정보
    if st.session_state.get("dev_mode", False):
        with st.expander("🔧 디버그 정보"):
            st.write(f"**session_id**: {session_id}")
            st.write(f"**답변 개수**: {answered_count}")
            st.write(f"**dirty 개수**: {dirty_count}")
            st.write(f"**hc_loaded_session_id**: {st.session_state.get('hc_loaded_session_id')}")


def render_category_questions(store_id: str, session_id: str, category: str):
    """카테고리별 질문 렌더링 (임시 저장 방식, 1클릭 라디오)"""
    category_questions = QUESTIONS.get(category, [])
    hc_answers_key = "hc_answers"
    hc_dirty_key = "hc_dirty"
    
    # session_state에서 답변 가져오기
    answers = st.session_state.get(hc_answers_key, {})
    
    # radio 옵션
    options = ["예", "애매함", "아니다"]
    raw_value_map = {"예": "yes", "애매함": "maybe", "아니다": "no"}
    
    # 각 질문을 1행으로 표시 (질문 텍스트 + 오른쪽 라디오)
    for question_item in category_questions:
        question_code = question_item.get("code", "")
        question_text = question_item.get("text", "")
        if not question_code or not question_text:
            continue
        
        # session_state에서 현재 값 가져오기
        key = (category, question_code)
        current_value = answers.get(key)
        
        # 현재 값에 맞는 인덱스 찾기
        index = None
        if current_value:
            for i, opt in enumerate(options):
                if raw_value_map[opt] == current_value:
                    index = i
                    break
        
        # index가 None이면 기본값 0 사용 (첫 번째 옵션)
        radio_index = index if (index is not None and 0 <= index < len(options)) else 0
        
        # 1행 레이아웃: 질문 텍스트(왼쪽) + 라디오 버튼(오른쪽)
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**{question_code}** {question_text}")
        
        with col2:
            try:
                selected = st.radio(
                    "",  # 라벨 없음 (col1에 질문 표시)
                    options=options,
                    index=radio_index,
                    key=f"hc_{session_id}_{category}_{question_code}",
                    horizontal=True,
                    label_visibility="collapsed"
                )
            except Exception as e:
                logger.error(f"Error rendering radio for {question_code}: {e}")
                continue
            
            # selected가 None이거나 options에 없거나 raw_value_map에 없으면 스킵
            if selected is None or selected not in options or selected not in raw_value_map:
                continue
            
            # 값 변환
            new_raw_value = raw_value_map[selected]
            
            # 값이 변경되었으면 session_state에 저장 (DB 저장 안 함)
            if new_raw_value != current_value:
                # session_state 업데이트
                if hc_answers_key not in st.session_state:
                    st.session_state[hc_answers_key] = {}
                st.session_state[hc_answers_key][key] = new_raw_value
                
                # dirty에 추가
                if hc_dirty_key not in st.session_state:
                    st.session_state[hc_dirty_key] = set()
                st.session_state[hc_dirty_key].add(key)
        
        # 질문 간 간격
        st.markdown("<br>", unsafe_allow_html=True)


def render_result_report(store_id: str, session_id: str):
    """결과 리포트 렌더링"""
    try:
        session = get_health_session(session_id)
        if not session:
            st.warning("세션 정보를 찾을 수 없습니다.")
            return
        
        # 완료되지 않은 세션
        if not session.get('completed_at'):
            st.info("검진을 완료하면 결과를 확인할 수 있습니다.")
            return
    except Exception as e:
        logger.error(f"Error loading session: {e}")
        st.error(f"세션 정보를 불러오는 중 오류가 발생했습니다: {e}")
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
    try:
        results = get_health_results(session_id)
    except Exception as e:
        logger.error(f"Error loading results: {e}", exc_info=True)
        st.error(f"결과를 불러오는 중 오류가 발생했습니다: {e}")
        return
    
    if not results:
        st.warning("결과 데이터가 없습니다. 검진이 완료되었지만 결과가 저장되지 않았을 수 있습니다.")
        return
    
    try:
        st.markdown("### 📋 영역별 결과")
        
        # 결과를 카테고리별로 정리 (안전하게)
        results_dict = {}
        for r in results:
            if r and isinstance(r, dict) and 'category' in r:
                results_dict[r['category']] = r
        
        # 테이블 데이터 준비
        table_data = []
        for category in CATEGORIES_ORDER:
            if category in results_dict:
                r = results_dict[category]
                # 안전하게 값 추출
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
        
        # 점수가 낮은 순으로 정렬 (안전하게)
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
        검진 결과를 바탕으로 HOME에서 요약을 확인하고,
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
                # 보기 버튼 클릭 시 세션 ID와 view_mode 설정
                st.session_state['health_session_id'] = session['id']
                st.session_state['health_check_view_mode'] = 'result'
                # 캐시 무효화
                _invalidate_answers_cache(session['id'])
                st.rerun()
        
        st.markdown("---")
