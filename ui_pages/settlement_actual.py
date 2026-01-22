"""
실제정산 페이지
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
import datetime as dt
import time
from src.ui_helpers import render_page_header, render_section_divider, safe_get_first_row, handle_data_error
from src.storage_supabase import load_csv, get_session_df, clear_session_cache
from src.utils.time_utils import now_kst, today_kst, current_year_kst, current_month_kst
from src.utils.boot_perf import record_compute_call

# 공통 설정 적용
bootstrap(page_title="Settlement Actual")

# [A] session_state write 추적기
_current_step = None
_render_phase = "init"  # init, loading, rendering, done

def set_state(key, value, tag="unknown"):
    """
    session_state write 추적 래퍼
    렌더 중 상태 변경을 감지하여 무한 rerun 원인 특정
    """
    global _current_step, _render_phase
    import traceback
    
    # 디버그 키 allowlist: 렌더 중에도 변경 허용
    DEBUG_KEY_ALLOWLIST = {
        "_dbg_rerun_count",
        "_render_phase",
        "_dbg_last_step",
        "_dbg_last_phase",
        "_actual_render_count",
        "_actual_run_id",
        "_actual_state_snapshot_start",
        "_actual_state_snapshot_end",
    }
    
    # 현재 STEP과 phase 정보
    step_info = f"STEP={_current_step}" if _current_step else "STEP=?"
    phase_info = f"phase={_render_phase}"
    rerun_count = st.session_state.get("_dbg_rerun_count", 0)
    render_count = st.session_state.get("_actual_render_count", 0)
    run_id = st.session_state.get("_actual_run_id", "unknown")
    
    print(f"[STATE WRITE] run_id={run_id} | render={render_count} | rerun={rerun_count} | {step_info} | {phase_info} | tag={tag} | key={key}")
    
    # [D] 임시 응급 차단: dev_mode에서 렌더 중 "로직 key" 변경 감지
    # 단, 디버그 키와 위젯 자동 생성 key는 예외 처리
    try:
        from src.auth import is_dev_mode
        if is_dev_mode() and _render_phase == "rendering":
            # 디버그 키는 allowlist에 있으면 차단하지 않음
            if key not in DEBUG_KEY_ALLOWLIST:
                # 위젯 자동 생성 key인지 확인
                is_ui_widget = (
                    "::" in key or
                    key.startswith("settlement_actual::") or
                    any(prefix in key for prefix in ["new_item", "fixed_editor", "add_item", "edit_name", "edit_amount", "save_", "del_", "settlement_actual_settlement_"])
                )
                
                # 로직 key인지 확인 (rerun 원인 후보)
                # ss_로 시작하는 키는 get_session_df가 관리하는 캐시 키이므로 제외
                # _actual_page_init은 최초 1회만 설정되므로 정상 (제외)
                # actual_expense_items_*는 이미 if key not in 체크를 하고 있으므로 정상 (제외)
                is_logic_key_check = (
                    not key.startswith("ss_") and
                    key != "_actual_page_init" and
                    not key.startswith("actual_expense_items_") and
                    any(pattern in key.lower() for pattern in ["expense", "actual_", "temp_", "init", "cache"])
                )
                
                # 로직 key만 차단 (위젯 자동 생성 key는 무시)
                if is_logic_key_check and not is_ui_widget:
                    # 위젯 이벤트 시에는 차단하지 않음 (버튼 클릭 등 정상 동작 허용)
                    _is_widget_event = st.session_state.get("_last_page", None) == "실제정산"
                    if not _is_widget_event:
                        # stack trace 출력
                        stack_trace = ''.join(traceback.format_stack()[-5:-1])  # 최근 4줄
                        print(f"[STATE WRITE] 🚨 렌더 중 로직 session_state 변경 감지!")
                        print(f"  run_id={run_id} | render_count={render_count} | rerun_count={rerun_count}")
                        print(f"  STEP={_current_step} | phase={_render_phase} | tag={tag} | key={key}")
                        print(f"  Stack trace:\n{stack_trace}")
                        st.error(f"🚨 렌더 중 로직 session_state 변경 감지! (run_id={run_id}, render={render_count}, rerun={rerun_count}, STEP={_current_step}, tag={tag}, key={key})")
                        st.stop()
                        return
                    else:
                        # 위젯 이벤트 시에는 로그만 출력
                        print(f"[STATE WRITE] 위젯 이벤트 중 session_state 변경 (정상): tag={tag}, key={key}")
    except Exception:
        pass  # is_dev_mode 실패해도 계속 진행
    
    # 실제 상태 변경
    st.session_state[key] = value


def _load_sales_with_filter(store_id: str, year: int, month: int):
    """
    매출 데이터를 Supabase에서 직접 필터링하여 로드 (서버 필터링)
    
    Args:
        store_id: 매장 ID
        year: 연도
        month: 월
    
    Returns:
        pandas.DataFrame
    """
    from src.storage_supabase import get_read_client
    
    try:
        supabase = get_read_client()
        if not supabase:
            return pd.DataFrame()
        
        # year/month 범위 계산
        start_date = dt.datetime(year, month, 1).date()
        if month == 12:
            end_date = dt.datetime(year + 1, 1, 1).date()
        else:
            end_date = dt.datetime(year, month + 1, 1).date()
        
        # Supabase 쿼리: store_id + 날짜 범위 필터 (서버 필터링)
        # 테이블명은 'sales' (storage_supabase.py의 table_mapping 참고)
        query = supabase.table("sales")\
            .select("date, store_id, total_sales")\
            .eq("store_id", store_id)\
            .gte("date", start_date.isoformat())\
            .lt("date", end_date.isoformat())\
            .order("date", desc=False)
        
        result = query.execute()
        
        if result.data:
            df = pd.DataFrame(result.data)
            # 컬럼명 매핑 (한글 컬럼명으로 변환)
            df = df.rename(columns={
                'date': '날짜',
                'store_id': '매장',
                'total_sales': '총매출'
            })
            # 날짜 변환
            if '날짜' in df.columns:
                df['날짜'] = pd.to_datetime(df['날짜'])
                df['연도'] = df['날짜'].dt.year
                df['월'] = df['날짜'].dt.month
            return df
        else:
            return pd.DataFrame(columns=['날짜', '매장', '총매출', '연도', '월'])
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"_load_sales_with_filter 실패: {e}")
        return pd.DataFrame()


def _load_actual_settlement_with_filter(store_id: str, year: int, month: int):
    """
    실제정산 데이터를 Supabase에서 직접 필터링하여 로드 (서버 필터링)
    
    Args:
        store_id: 매장 ID
        year: 연도
        month: 월
    
    Returns:
        pandas.DataFrame
    """
    from src.storage_supabase import get_read_client
    
    try:
        supabase = get_read_client()
        if not supabase:
            return pd.DataFrame()
        
        # Supabase 쿼리: store_id + year + month 필터 (서버 필터링)
        query = supabase.table("actual_settlement")\
            .select("year, month, actual_sales, actual_cost, actual_profit, actual_profit_rate")\
            .eq("store_id", store_id)\
            .eq("year", year)\
            .eq("month", month)
        
        result = query.execute()
        
        if result.data:
            df = pd.DataFrame(result.data)
            # 컬럼명 매핑 (한글 컬럼명으로 변환)
            df = df.rename(columns={
                'year': '연도',
                'month': '월',
                'actual_sales': '실제매출',
                'actual_cost': '실제비용',
                'actual_profit': '실제이익',
                'actual_profit_rate': '실제이익률'
            })
            return df
        else:
            return pd.DataFrame(columns=['연도', '월', '실제매출', '실제비용', '실제이익', '실제이익률'])
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"_load_actual_settlement_with_filter 실패: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)  # 5분 캐시 (store_id, year, month, safe_mode 기준)
def load_actual_settlement_data(store_id: str, year: int, month: int, safe_mode: bool = False):
    """
    실제정산 페이지 전용 데이터 로더
    모든 DB 호출을 render 이전 1회로 통합
    
    Args:
        store_id: 매장 ID
        year: 연도
        month: 월
        safe_mode: Safe Mode 활성화 여부 (True면 DB 로드 최소화)
    
    Returns:
        dict: {
            'sales_df': 매출 데이터 (전체, 날짜 변환 완료),
            'actual_df': 실제정산 데이터,
            'available_years': 사용 가능한 연도 목록,
            'available_months': 사용 가능한 월 목록 (선택된 연도 기준),
            'month_sales_df': 선택된 연/월의 매출 데이터,
            'month_total_sales': 선택된 연/월의 총 매출,
            'db_query_timings': 쿼리별 시간 (ms) 리스트,
            'cache_status': 캐시 히트/미스 정보,
        }
    """
    from src.storage_supabase import load_csv, get_session_df
    from src.auth import is_dev_mode
    import logging
    logger = logging.getLogger(__name__)
    
    # 캐시 히트/미스 감지 (함수 호출 전후로 판단)
    # 주의: @st.cache_data는 함수 내부에서 직접 확인할 수 없으므로,
    # 함수 시작 시점의 세션 캐시 상태로 판단
    cache_status = {
        'sales': 'UNKNOWN',
        'actual': 'UNKNOWN',
    }
    
    # 쿼리별 시간 측정
    db_query_timings = []
    total_db_time = 0.0
    
    result = {
        'sales_df': pd.DataFrame(),
        'actual_df': pd.DataFrame(),
        'available_years': [],
        'available_months': [],
        'month_sales_df': pd.DataFrame(),
        'month_total_sales': 0.0,
        'db_query_timings': [],
        'cache_status': cache_status,
    }
    
    try:
        # Safe Mode: 필수 쿼리만 실행
        if safe_mode:
            logger.warning("🧯 Safe Mode: 최소 DB 로드만 수행")
            # 필수 쿼리 1개만 실행 (매출 데이터)
            print(f"[DB] START: fetch_sales (Safe Mode)")
            t_start = time.perf_counter()
            sales_df = get_session_df('ss_sales_df', load_csv, 'sales.csv', default_columns=['날짜', '매장', '총매출'])
            t_elapsed = (time.perf_counter() - t_start) * 1000
            print(f"[DB] END: fetch_sales ({t_elapsed:.1f}ms)")
            db_query_timings.append(('fetch_sales', t_elapsed))
            total_db_time += t_elapsed
            
            if not sales_df.empty:
                if '날짜' in sales_df.columns and not pd.api.types.is_datetime64_any_dtype(sales_df['날짜']):
                    sales_df['날짜'] = pd.to_datetime(sales_df['날짜'])
                if '연도' not in sales_df.columns:
                    sales_df['연도'] = sales_df['날짜'].dt.year
                if '월' not in sales_df.columns:
                    sales_df['월'] = sales_df['날짜'].dt.month
                
                result['sales_df'] = sales_df.copy()
                result['available_years'] = sorted(sales_df['연도'].unique().tolist(), reverse=True)
                
                month_sales_df = sales_df[
                    (sales_df['연도'] == year) & (sales_df['월'] == month)
                ].copy()
                result['month_sales_df'] = month_sales_df
                result['month_total_sales'] = float(month_sales_df['총매출'].sum()) if not month_sales_df.empty else 0.0
                
                result['available_months'] = sorted(
                    sales_df[sales_df['연도'] == year]['월'].unique().tolist()
                )
            
            # actual_df는 빈 DataFrame으로 반환 (Safe Mode)
            result['actual_df'] = pd.DataFrame()
            result['db_query_timings'] = db_query_timings
            result['cache_status'] = cache_status
            result['_loaded_year'] = year
            result['_loaded_month'] = month
            return result
        
        # 1. 매출 데이터 로드 (DB 쿼리 시간 측정)
        print(f"[DB] START: fetch_sales")
        t_start = time.perf_counter()
        
        # 세션 캐시 확인 (캐시 히트/미스 판단)
        if 'ss_sales_df' in st.session_state:
            cache_status['sales'] = 'SESSION_CACHE_HIT'
        else:
            cache_status['sales'] = 'SESSION_CACHE_MISS'
        
        try:
            # 느린 쿼리(500ms 이상) 예상 시 서버 필터링 사용
            # 하지만 전체 데이터가 필요할 수도 있으므로, 일단 기존 방식 사용
            # 성능 측정 후 개선 결정
            sales_df = get_session_df('ss_sales_df', load_csv, 'sales.csv', default_columns=['날짜', '매장', '총매출'])
            t_elapsed = (time.perf_counter() - t_start) * 1000
            print(f"[DB] END: fetch_sales ({t_elapsed:.1f}ms)")
            db_query_timings.append(('fetch_sales', t_elapsed))
            total_db_time += t_elapsed
            
            # 느린 경우 서버 필터링으로 재시도 (개발모드에서만)
            if t_elapsed > 500 and is_dev_mode():
                logger.warning(f"⚠️ fetch_sales가 느림 ({t_elapsed:.1f}ms), 서버 필터링으로 재시도")
                t_start_filtered = time.perf_counter()
                try:
                    sales_df_filtered = _load_sales_with_filter(store_id, year, month)
                    t_elapsed_filtered = (time.perf_counter() - t_start_filtered) * 1000
                    if t_elapsed_filtered < t_elapsed:
                        logger.info(f"✅ 서버 필터링이 더 빠름: {t_elapsed_filtered:.1f}ms (기존: {t_elapsed:.1f}ms)")
                        sales_df = sales_df_filtered
                        db_query_timings[-1] = ('fetch_sales', t_elapsed_filtered)
                        total_db_time = total_db_time - t_elapsed + t_elapsed_filtered
                except Exception as e:
                    logger.warning(f"서버 필터링 실패, 기존 데이터 사용: {e}")
            
            if t_elapsed > 10000:
                logger.warning(f"⚠️ fetch_sales가 10초 이상 걸림: {t_elapsed:.1f}ms")
        except Exception as e:
            t_elapsed = (time.perf_counter() - t_start) * 1000
            logger.error(f"❌ fetch_sales 실패 ({t_elapsed:.1f}ms): {e}")
            sales_df = pd.DataFrame()
            db_query_timings.append(('fetch_sales', t_elapsed))
            total_db_time += t_elapsed
        
        if not sales_df.empty:
            # 날짜 변환
            if '날짜' in sales_df.columns and not pd.api.types.is_datetime64_any_dtype(sales_df['날짜']):
                sales_df['날짜'] = pd.to_datetime(sales_df['날짜'])
            if '연도' not in sales_df.columns:
                sales_df['연도'] = sales_df['날짜'].dt.year
            if '월' not in sales_df.columns:
                sales_df['월'] = sales_df['날짜'].dt.month
            
            result['sales_df'] = sales_df.copy()
            result['available_years'] = sorted(sales_df['연도'].unique().tolist(), reverse=True)
            
            # 선택된 연/월의 매출 데이터
            month_sales_df = sales_df[
                (sales_df['연도'] == year) & (sales_df['월'] == month)
            ].copy()
            result['month_sales_df'] = month_sales_df
            result['month_total_sales'] = float(month_sales_df['총매출'].sum()) if not month_sales_df.empty else 0.0
            
            # 선택된 연도의 사용 가능한 월
            result['available_months'] = sorted(
                sales_df[sales_df['연도'] == year]['월'].unique().tolist()
            )
        
        # 2. 실제정산 데이터 로드 (DB 쿼리 시간 측정)
        print(f"[DB] START: fetch_actual_settlement")
        t_start = time.perf_counter()
        
        # 세션 캐시 확인 (캐시 히트/미스 판단)
        if 'ss_actual_settlement_df' in st.session_state:
            cache_status['actual'] = 'SESSION_CACHE_HIT'
        else:
            cache_status['actual'] = 'SESSION_CACHE_MISS'
        
        try:
            # 느린 쿼리(500ms 이상) 예상 시 서버 필터링 사용
            actual_df = get_session_df('ss_actual_settlement_df', load_csv, "actual_settlement.csv", default_columns=["연도", "월", "실제매출", "실제비용", "실제이익", "실제이익률"])
            t_elapsed = (time.perf_counter() - t_start) * 1000
            print(f"[DB] END: fetch_actual_settlement ({t_elapsed:.1f}ms)")
            db_query_timings.append(('fetch_actual_settlement', t_elapsed))
            total_db_time += t_elapsed
            
            # 느린 경우 서버 필터링으로 재시도 (개발모드에서만)
            if t_elapsed > 500 and is_dev_mode():
                logger.warning(f"⚠️ fetch_actual_settlement가 느림 ({t_elapsed:.1f}ms), 서버 필터링으로 재시도")
                t_start_filtered = time.perf_counter()
                try:
                    actual_df_filtered = _load_actual_settlement_with_filter(store_id, year, month)
                    t_elapsed_filtered = (time.perf_counter() - t_start_filtered) * 1000
                    if t_elapsed_filtered < t_elapsed:
                        logger.info(f"✅ 서버 필터링이 더 빠름: {t_elapsed_filtered:.1f}ms (기존: {t_elapsed:.1f}ms)")
                        actual_df = actual_df_filtered
                        db_query_timings[-1] = ('fetch_actual_settlement', t_elapsed_filtered)
                        total_db_time = total_db_time - t_elapsed + t_elapsed_filtered
                except Exception as e:
                    logger.warning(f"서버 필터링 실패, 기존 데이터 사용: {e}")
            
            if t_elapsed > 10000:
                logger.warning(f"⚠️ fetch_actual_settlement가 10초 이상 걸림: {t_elapsed:.1f}ms")
        except Exception as e:
            t_elapsed = (time.perf_counter() - t_start) * 1000
            logger.error(f"❌ fetch_actual_settlement 실패 ({t_elapsed:.1f}ms): {e}")
            actual_df = pd.DataFrame()
            db_query_timings.append(('fetch_actual_settlement', t_elapsed))
            total_db_time += t_elapsed
        
        result['actual_df'] = actual_df
        db_query_timings.append(('total_db', total_db_time))
        
    except Exception as e:
        logger.error(f"load_actual_settlement_data 실패: {e}")
        # 빈 DataFrame 반환 (에러 발생해도 페이지는 계속 진행)
    
    # 로드된 연/월 정보 추가 (캐시 키 확인용)
    result['_loaded_year'] = year
    result['_loaded_month'] = month
    result['db_query_timings'] = db_query_timings
    result['cache_status'] = cache_status
    
    return result


def _timed_db_query(query_name, loader_fn, *args, db_query_timings=None, **kwargs):
    """
    DB 쿼리 시간 측정 헬퍼
    
    Args:
        query_name: 쿼리 이름 (예: 'fetch_sales')
        loader_fn: 데이터 로드 함수 (예: get_session_df)
        *args: loader_fn에 전달할 위치 인자
        db_query_timings: 타이밍 기록 리스트 (None이면 기록 안 함)
        **kwargs: loader_fn에 전달할 키워드 인자
    
    Returns:
        loader_fn의 반환값
    """
    t_start = time.perf_counter()
    result = loader_fn(*args, **kwargs)
    t_elapsed = (time.perf_counter() - t_start) * 1000
    
    # dev 모드에서만 타이밍 기록
    if db_query_timings is not None:
        try:
            from src.auth import is_dev_mode
            if is_dev_mode():
                db_query_timings.append((query_name, t_elapsed))
        except Exception:
            pass  # is_dev_mode 실패해도 계속 진행
    
    return result


def render_settlement_actual():
    """실제정산 페이지 렌더링"""
    global _current_step, _render_phase
    
    # ========== [RERUN 디버깅] 페이지 진입 카운터 및 run_id 시스템 ==========
    import uuid
    import traceback
    
    # run_id 생성/유지 (최초 진입 시 생성, rerun마다 유지)
    if "_actual_run_id" not in st.session_state:
        _actual_run_id = str(uuid.uuid4())[:8]
        set_state("_actual_run_id", _actual_run_id, "run_id_init")
        print(f"[RERUN DEBUG] 🆕 새로운 run_id 생성: {_actual_run_id}")
    else:
        _actual_run_id = st.session_state["_actual_run_id"]
        print(f"[RERUN DEBUG] 🔄 기존 run_id 유지: {_actual_run_id}")
    
    # 페이지 진입 카운터
    if "_actual_render_count" not in st.session_state:
        set_state("_actual_render_count", 0, "render_count_init")
    render_count = st.session_state.get("_actual_render_count", 0) + 1
    set_state("_actual_render_count", render_count, "render_count_increment")
    
    # session_state snapshot (렌더 시작 시점)
    session_state_snapshot_start = set(st.session_state.keys())
    set_state("_actual_state_snapshot_start", list(session_state_snapshot_start), "snapshot_start")
    
    # STEP 1: entered render (가장 먼저 phase를 init으로 설정)
    _current_step = 1
    _render_phase = "init"
    
    # [A] 무한 rerun 감지/차단 (phase='init' 상태에서만 수행)
    if "_dbg_rerun_count" not in st.session_state:
        set_state("_dbg_rerun_count", 0, "rerun_counter_init")
    set_state("_dbg_rerun_count", st.session_state.get("_dbg_rerun_count", 0) + 1, "rerun_counter_increment")
    rerun_count = st.session_state.get("_dbg_rerun_count", 0)
    t_step_start = time.perf_counter()
    print(f"[STEP 1] entered render | run_id={_actual_run_id} | render_count={render_count} | rerun_count={rerun_count} ({time.perf_counter() - t_step_start:.3f}s)")
    
    # ========== [RERUN 제거] 페이지 최초 1회 init 구역 ==========
    # expense_items 초기화는 페이지 최초 1회만 수행 (렌더 중 실행 금지)
    if "_actual_page_init" not in st.session_state:
        def init_actual_page_state():
            """실제정산 페이지 상태 초기화 (최초 1회만 실행)"""
            # 모든 가능한 연/월 조합에 대해 expense_items 초기화
            # 실제로는 사용자가 선택한 연/월만 초기화하지만, 
            # 여기서는 플레이스홀더만 설정하고 실제 초기화는 연/월 선택 후 수행
            set_state("_actual_page_init", True, "page_init")
            print(f"[INIT] 실제정산 페이지 초기화 완료 | run_id={_actual_run_id}")
        
        init_actual_page_state()
    
    # 실시간 디버깅을 위한 probe 생성 (최초 5줄 내) - REMOVED
    # start = time.perf_counter()
    # probe = st.empty()
    # probe.caption(f"🔍 STEP 1: entered render (rerun={rerun_count}) ({0:.1f}ms)")
    
    # 무한 rerun 차단 (위젯 이벤트 시에는 실행되지 않도록 조건 추가)
    # 페이지 이동이 아닌 위젯 이벤트로 인한 rerun은 차단하지 않음
    from src.auth import is_dev_mode
    _is_widget_event = st.session_state.get("_last_page", None) == "실제정산"
    
    if rerun_count >= 10 and not _is_widget_event:
        st.error(f"⚠️ 무한 rerun 감지! ({rerun_count}회) 페이지를 새로고침하세요.")
        print(f"[RERUN BLOCK] rerun_count={rerun_count}, last_step={_current_step}, last_phase={_render_phase}, is_widget_event={_is_widget_event}")
        st.stop()
        return
    elif rerun_count >= 5 and not _is_widget_event:
        st.warning(f"⚠️ rerun이 {rerun_count}회 발생했습니다. 문제가 있을 수 있습니다.")
    
    # UI 계측 변수 초기화 (에러 방지)
    t_ui_start = time.perf_counter()
    t_ui_end = None
    t0 = time.perf_counter()
    t_load_start = None
    t_load_end = None
    t_transform_start = None
    t_transform_end = None
    
    # UI 단계별 타이밍 저장용 (안전하게 초기화)
    ui_step_timings = []
    
    # ========== [UI 병목 측정] 큰 블록 타이밍 ==========
    # UI_TOTAL_BLOCK: render 함수 전체를 감싸는 블록 (첫 줄에서 시작)
    t_ui_total_block_start = time.perf_counter()  # render 함수 첫 줄에서 시작
    t_category_loop_block_start = None  # CATEGORY_LOOP_BLOCK 시작 시점
    t_editors_block_start = None  # EDITORS_BLOCK 시작 시점
    
    try:
        # 구간별 시간 측정 시작
        t0 = time.perf_counter()
        
        def _timed_step(step_name, func, *args, **kwargs):
            """UI 단계 타이밍 측정 헬퍼"""
            t_start = time.perf_counter()
            result = func(*args, **kwargs)
            t_elapsed = (time.perf_counter() - t_start) * 1000
            ui_step_timings.append((step_name, t_elapsed))
            return result
        
        t_header = time.perf_counter()
        # 실제정산 페이지 전용 헤더 (화이트 모드에서도 항상 흰색 텍스트로 표시)
        header_color = "#ffffff"
        page_title = "실제 정산 (월별 실적)"
        st.markdown(f"""
        <div style="margin: 0 0 1.0rem 0;">
            <h2 style="color: {header_color}; font-weight: 700; margin: 0;">
                🧾 {page_title}
            </h2>
        </div>
        """, unsafe_allow_html=True)
        ui_step_timings.append(("header", (time.perf_counter() - t_header) * 1000))
    
        # [Phase 1] 실제정산 전용 데이터 로더: render 이전 1회 통합 로드
        from src.auth import get_current_store_id, is_dev_mode
        
        store_id = get_current_store_id()
        if not store_id:
            st.error("매장 정보를 찾을 수 없습니다. 로그인 후 다시 시도해주세요.")
            return
        
        # Safe Mode 토글 (dev_mode에서만) - REMOVED
        safe_mode = False
        # if is_dev_mode():
        #     # KST 시간 표시 (검증용)
        #     st.caption(f"🕐 현재 시간 (KST): {now_kst().strftime('%Y-%m-%d %H:%M:%S')}")
        #     safe_mode = st.toggle("🧯 Safe Mode (DB/대용량 로드 생략)", value=False, key="settlement_safe_mode")
        #     if safe_mode:
        #         st.warning("⚠️ Safe Mode 활성화: DB 로드는 최소(필수 1개만) 수행하고 나머지는 빈 데이터로 진행합니다.")
        
        # [Phase 1] 실제정산 전용 데이터 로더: render 이전 1회 통합 로드
        # 연/월 선택을 위해 먼저 현재 연/월로 데이터 로드 (선택 UI 표시용) - KST 기준
        current_year = current_year_kst()
        current_month = current_month_kst()
        
        # 세션 상태에서 선택된 연/월 가져오기 (없으면 현재 연/월)
        selected_year = st.session_state.get("settlement_actual_settlement_year", current_year)
        selected_month = st.session_state.get("settlement_actual_settlement_month", current_month)
        
        # STEP 2: before load_actual_settlement_data
        _current_step = 2
        _render_phase = "loading"
        # t_step2 = time.perf_counter()
        # elapsed = (t_step2 - t_step_start) * 1000
        # print(f"[STEP 2] before load_actual_settlement_data (rerun={rerun_count}) ({elapsed:.1f}ms)")
        # probe.caption(f"🔍 STEP 2: before load_actual_settlement_data (rerun={rerun_count}) ({elapsed:.1f}ms)")
        
        # [Phase 1] 모든 데이터 통합 로드 (캐시 적용, render 이전 1회)
        # 렌더 중 DB 호출 금지: 이 함수 호출이 유일한 DB 접근 지점
        t_load_start = time.perf_counter()
        settlement_data = load_actual_settlement_data(store_id, selected_year, selected_month, safe_mode=safe_mode)
        t_load_end = time.perf_counter()
        
        # STEP 3: after load_actual_settlement_data
        _current_step = 3
        # t_step3 = time.perf_counter()
        # elapsed = (t_step3 - t_step_start) * 1000
        # load_time = (t_load_end - t_load_start) * 1000
        # print(f"[STEP 3] after load_actual_settlement_data (rerun={rerun_count}) ({elapsed:.1f}ms, load={load_time:.1f}ms)")
        # probe.caption(f"🔍 STEP 3: after load_actual_settlement_data (rerun={rerun_count}) ({elapsed:.1f}ms, load={load_time:.1f}ms)")
        
        # 데이터 추출
        sales_df = settlement_data['sales_df']
        actual_df = settlement_data['actual_df']
        month_sales_df = settlement_data['month_sales_df']
        month_total_sales = settlement_data['month_total_sales']
        available_years = settlement_data['available_years']
        available_months = settlement_data['available_months']
        db_query_timings = settlement_data.get('db_query_timings', [])
        cache_status = settlement_data.get('cache_status', {})
        
        # 개발모드에서 DB 쿼리 타이밍 및 캐시 상태 표시 - REMOVED
        # try:
        #     from src.auth import is_dev_mode
        #     if is_dev_mode() and db_query_timings:
        #         with st.expander("🔍 DB 쿼리 성능 분석", expanded=False):
        #             ...
        # except Exception:
        #     pass  # 개발모드 체크 실패 시 무시
        
        t_transform_start = time.perf_counter()
        t_transform_end = time.perf_counter()
        
        # 연/월 선택 UI (목표비용구조 페이지와 동일한 스타일)
        t_selectbox = time.perf_counter()
        
        # 기간 선택 (목표비용구조 페이지와 동일한 레이아웃)
        col1, col2, col3 = st.columns([2, 2, 2])
        with col1:
            widget_key = "settlement_actual_settlement_year"
            print(f"[WIDGET] number_input | key={widget_key} | rerun={rerun_count} | STEP={_current_step}")
            # session_state에서 이전 값 가져오기 (위젯 이벤트 시 값 유지)
            prev_year = st.session_state.get(widget_key, current_year)
            selected_year = st.number_input(
                "연도",
                min_value=2020,
                max_value=2100,
                value=prev_year,
                key=widget_key,
            )
            print(f"[WIDGET] selected_year={selected_year} | prev_year={prev_year} | rerun={rerun_count}")
        
        with col2:
            widget_key = "settlement_actual_settlement_month"
            print(f"[WIDGET] number_input | key={widget_key} | rerun={rerun_count} | STEP={_current_step}")
            # session_state에서 이전 값 가져오기 (위젯 이벤트 시 값 유지)
            prev_month = st.session_state.get(widget_key, current_month)
            selected_month = st.number_input(
                "월",
                min_value=1,
                max_value=12,
                value=prev_month,
                key=widget_key,
            )
            print(f"[WIDGET] selected_month={selected_month} | prev_month={prev_month} | rerun={rerun_count}")
        
        with col3:
            st.write("")
            st.write("")
            # 빈 공간 (목표비용구조 페이지와 동일한 레이아웃)
        
        ui_step_timings.append(("selectbox_year_month", (time.perf_counter() - t_selectbox) * 1000))
        
        render_section_divider()
        
        # ========== [기능 점검] 기능 점검 로그 (dev_mode) - REMOVED ==========
        # if is_dev_mode():
        #     with st.expander("🔍 기능 점검 (개발모드)", expanded=False):
        #         ...
        
        # [초기화] expense_items 초기화 (연/월 확정 후, 렌더 전에 1회만 수행)
        # 주의: 렌더 중에는 절대 초기화하지 않음 (phase='init' 또는 'loading' 상태에서만)
        expense_items_key = f'actual_expense_items_{selected_year}_{selected_month}'
        if expense_items_key not in st.session_state:
            # 렌더 중이 아닌 경우에만 초기화 (phase='init' 또는 'loading' 상태에서만)
            if _render_phase in ["init", "loading"]:
                expense_items = {cat: [] for cat in ['임차료', '인건비', '재료비', '공과금', '부가세&카드수수료']}
                
                # 고정 항목 초기화
                expense_items['임차료'] = [{'item_name': '임차료', 'amount': 0}]
                expense_items['인건비'] = [
                    {'item_name': '직원 실지급 인건비', 'amount': 0},
                    {'item_name': '사회보험(직원+회사분 통합)', 'amount': 0},
                    {'item_name': '원천징수(국세+지방세)', 'amount': 0},
                    {'item_name': '퇴직급여 충당금', 'amount': 0},
                    {'item_name': '보너스', 'amount': 0}
                ]
                expense_items['공과금'] = [
                    {'item_name': '전기', 'amount': 0},
                    {'item_name': '가스', 'amount': 0},
                    {'item_name': '수도', 'amount': 0}
                ]
                expense_items['부가세&카드수수료'] = [
                    {'item_name': '부가세', 'amount': 0.0},
                    {'item_name': '카드수수료', 'amount': 0.0}
                ]
                
                # 렌더 중이 아닐 때만 set_state 호출
                if _render_phase != "rendering":
                    set_state(expense_items_key, expense_items, "expense_items_init")
                    print(f"[INIT] expense_items 초기화 완료 | key={expense_items_key} | rerun={rerun_count} | STEP={_current_step} | phase={_render_phase}")
                else:
                    # 렌더 중에는 초기화하지 않고 빈 dict 반환 (다음 rerun에서 초기화)
                    print(f"[WARNING] expense_items 초기화 시도가 렌더 중에 발생했습니다. 다음 rerun에서 초기화됩니다. | key={expense_items_key}")
                    expense_items = {cat: [] for cat in ['임차료', '인건비', '재료비', '공과금', '부가세&카드수수료']}
        
        # 연/월이 변경되면 rerun하여 다시 로드 (캐시가 있으면 빠름)
        # settlement_data에서 로드된 연/월 확인
        loaded_year = settlement_data.get('_loaded_year')
        loaded_month = settlement_data.get('_loaded_month')
        
        # 로드된 연/월이 없으면 현재 선택된 값으로 간주 (첫 로드)
        if loaded_year is None or loaded_month is None:
            loaded_year = selected_year
            loaded_month = selected_month
        
        # 연/월이 실제로 변경되었을 때만 rerun
        if (selected_year != loaded_year or selected_month != loaded_month):
            print(f"[RERUN TRIGGER] 연/월 변경 감지: ({loaded_year}/{loaded_month}) -> ({selected_year}/{selected_month}) | rerun={rerun_count} | STEP={_current_step}")
            # 캐시 무효화 후 다시 로드
            load_actual_settlement_data.clear()
            print(f"[RERUN] st.rerun() 호출 | rerun={rerun_count} | STEP={_current_step} | reason=year_month_change")
            st.rerun()
        
        # 데이터 추출
        sales_df = settlement_data['sales_df']
        actual_df = settlement_data['actual_df']
        month_sales_df = settlement_data['month_sales_df']
        month_total_sales = settlement_data['month_total_sales']
        
        t_transform_start = time.perf_counter()
        t_transform_end = time.perf_counter()
        
        if sales_df.empty:
            st.info("저장된 매출 데이터가 없습니다. 먼저 매출 관리 페이지에서 일매출을 입력해주세요.")
            # probe.warning(f"PROBE 1: 매출 데이터 없음 ({(time.perf_counter()-start)*1000:.1f}ms)")
        elif month_sales_df.empty:
            st.info(f"{selected_year}년 {selected_month}월에 해당하는 매출 데이터가 없습니다.")
        else:
            # probe.info(f"PROBE 1: year/month 선택 UI 완료 ({(time.perf_counter()-start)*1000:.1f}ms)")
            
            t_summary_card = time.perf_counter()
            render_section_divider()
            
            # ========== [실험 1: UI 스킵 테스트] - REMOVED ==========
            # 성능 진단: UI 위젯이 병목인지 확인하기 위한 토글
            # 토글 ON 시 카테고리 렌더링을 스킵하여 UI 위젯 비용 측정
            skip_ui_test = False
            # if is_dev_mode():
            #     skip_ui_test = st.toggle("🔬 [실험 1] UI 스킵 테스트 (카테고리 렌더링 생략)", value=False, key="settlement_skip_ui_test")
            #     if skip_ui_test:
            #         st.info("⚠️ UI 스킵 모드: 카테고리 렌더링을 생략합니다. 데이터 로드/변환/기본 UI만 유지됩니다.")
            
            # 상단 요약 카드
            st.markdown(
                f"""
                <div class="info-box">
                    <strong>📅 정산 대상 기간</strong><br>
                    <span style="font-size: 0.9rem; opacity: 0.9;">
                        {selected_year}년 {selected_month}월의 실제 매출과 비용을 기준으로 정산합니다.
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            ui_step_timings.append(("summary_card", (time.perf_counter() - t_summary_card) * 1000))
            
            t_metric_sales = time.perf_counter()
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("해당 월 총 매출", f"{month_total_sales:,.0f}원")
            ui_step_timings.append(("metric_sales", (time.perf_counter() - t_metric_sales) * 1000))
            # 비용/이익은 아래 입력값 기준으로 다시 표시
            
            # probe.info(f"PROBE 2: 데이터 로드 완료 ({(time.perf_counter()-start)*1000:.1f}ms)")
            
            existing_row = None
            if not actual_df.empty:
                existing_row = actual_df[
                    (actual_df["연도"] == selected_year)
                    & (actual_df["월"] == selected_month)
                ]
                # Phase 1: 안전한 DataFrame 접근
                if not existing_row.empty:
                    existing_row = safe_get_first_row(existing_row)
                    if existing_row is None:
                        existing_row = pd.Series()
            
            render_section_divider()
            st.markdown("**💸 해당 월 실제 비용 입력 (5대 비용 항목별)**")
            
            # STEP 4: before UI render loops
            _current_step = 4
            _render_phase = "rendering"
            # t_step4 = time.perf_counter()
            # elapsed = (t_step4 - t_step_start) * 1000
            # print(f"[STEP 4] before UI render loops (rerun={rerun_count}) ({elapsed:.1f}ms)")
            # probe.caption(f"🔍 STEP 4: before UI render loops (rerun={rerun_count}) ({elapsed:.1f}ms)")
            
            # 5대 비용 항목 정의
            expense_categories = {
                '임차료': {'icon': '🏢', 'description': '임차료', 'type': 'fixed', 'fixed_items': ['임차료']},
                '인건비': {'icon': '👥', 'description': '인건비 관련 모든 비용', 'type': 'fixed', 'fixed_items': ['직원 실지급 인건비', '사회보험(직원+회사분 통합)', '원천징수(국세+지방세)', '퇴직급여 충당금', '보너스']},
                '재료비': {'icon': '🥬', 'description': '재료비 관련 모든 비용', 'type': 'variable'},
                '공과금': {'icon': '💡', 'description': '공과금 관련 모든 비용', 'type': 'mixed', 'fixed_items': ['전기', '가스', '수도']},
                '부가세&카드수수료': {'icon': '💳', 'description': '부가세 및 카드수수료 (매출 대비 비율)', 'type': 'rate', 'fixed_items': ['부가세', '카드수수료']}
            }
            
            # expense_items는 이미 위에서 초기화되었으므로 여기서는 읽기만 수행
            expense_items_key = f'actual_expense_items_{selected_year}_{selected_month}'
            if expense_items_key not in st.session_state:
                # 이 경우는 발생하지 않아야 하지만, 안전을 위해 빈 dict 반환
                st.error(f"⚠️ expense_items가 초기화되지 않았습니다. (key={expense_items_key})")
                expense_items = {cat: [] for cat in expense_categories.keys()}
            else:
                # expense_items는 이미 초기화되었으므로 읽기만 수행 (렌더 중 수정 금지)
                expense_items = st.session_state[expense_items_key]
            
            # 한글 원화 변환 함수
            def format_korean_currency(amount):
                """숫자를 한글 원화로 변환"""
                if amount == 0:
                    return "0원"
                eok = amount // 100000000
                remainder = amount % 100000000
                man = remainder // 10000
                remainder = remainder % 10000
                parts = []
                if eok > 0:
                    parts.append(f"{eok}억")
                if man > 0:
                    parts.append(f"{man}만")
                if remainder > 0:
                    parts.append(f"{remainder:,}".replace(",", ""))
                if not parts:
                    return "0원"
                return "".join(parts) + "원"
            
            # ========== [리팩토링] prepare/render 분리 ==========
            def prepare_all_categories_data(expense_categories, expense_items, month_total_sales):
                """
                모든 카테고리 데이터를 한번에 준비 (UI 생성 금지)
                
                Returns:
                    dict: {
                        'category_totals': {category: total},
                        'category_prepared_data': {category: {...}},
                    }
                """
                t_prepare = time.perf_counter()
                category_totals = {}
                category_prepared_data = {}
                
                for category, info in expense_categories.items():
                    # 카테고리별 총액 계산
                    if info['type'] == 'rate':
                        total_rate = sum(item.get('amount', 0) for item in expense_items[category])
                        category_total = (month_total_sales * total_rate / 100) if month_total_sales > 0 else 0
                    else:
                        category_total = sum(item.get('amount', 0) for item in expense_items[category])
                    category_totals[category] = category_total
                    
                    # 카테고리별 데이터 준비
                    is_fixed = 'fixed_items' in info and (info['type'] == 'fixed' or info['type'] == 'rate')
                    is_mixed = 'fixed_items' in info and info['type'] == 'mixed'
                    
                    prepared = {
                        'is_mixed': is_mixed,
                        'is_fixed': is_fixed,
                        'fixed_items_names': info.get('fixed_items', []) if is_mixed else [],
                        'category_total': category_total,
                        'total_rate': sum(item.get('amount', 0) for item in expense_items[category]) if info['type'] == 'rate' else None,
                    }
                    
                    if is_mixed:
                        prepared['fixed_items_list'] = [item for item in expense_items[category] if item.get('item_name') in prepared['fixed_items_names']]
                        prepared['variable_items_list'] = [item for item in expense_items[category] if item.get('item_name') not in prepared['fixed_items_names']]
                    
                    # fixed_display용 DataFrame 준비
                    if is_fixed and expense_items[category]:
                        items_for_editor = []
                        for idx, item in enumerate(expense_items[category]):
                            item_row = {
                                '항목명': item.get('item_name', ''),
                                '금액': float(item.get('amount', 0)),
                                '_idx': idx,
                            }
                            if info['type'] == 'rate':
                                item_row['비율 (%)'] = float(item.get('amount', 0))
                                item_row['계산금액'] = (month_total_sales * float(item.get('amount', 0)) / 100) if month_total_sales > 0 else 0
                            items_for_editor.append(item_row)
                        prepared['editor_df'] = pd.DataFrame(items_for_editor)
                    
                    # mixed 타입 고정 항목용 DataFrame 준비
                    if is_mixed and prepared.get('fixed_items_list'):
                        fixed_items_for_editor = []
                        for idx, item in enumerate(prepared['fixed_items_list']):
                            fixed_items_for_editor.append({
                                '항목명': item.get('item_name', ''),
                                '금액': int(item.get('amount', 0)),
                                '_idx': idx,
                            })
                        prepared['fixed_editor_df'] = pd.DataFrame(fixed_items_for_editor)
                    
                    category_prepared_data[category] = prepared
                
                elapsed = (time.perf_counter() - t_prepare) * 1000
                ui_step_timings.append(("prepare_all_categories_data", elapsed))
                
                return {
                    'category_totals': category_totals,
                    'category_prepared_data': category_prepared_data,
                }
            
            # 각 카테고리별 입력 섹션
            # probe.info(f"PROBE 3: 비용/카테고리 루프 시작 직전 ({(time.perf_counter()-start)*1000:.1f}ms)")
            
            # [D] 무한 루프 차단 - 카테고리/항목 수 표시
            categories_count = len(expense_categories)
            total_items_count = sum(len(expense_items.get(cat, [])) for cat in expense_categories.keys())
            print(f"[DEBUG] categories={categories_count}, total_items={total_items_count}")
            # if is_dev_mode():
            #     st.caption(f"📊 카테고리: {categories_count}개, 총 항목: {total_items_count}개")
            if total_items_count > 500:
                st.error(f"⚠️ 항목 수가 비정상적으로 많습니다 ({total_items_count}개). 페이지를 새로고침하세요.")
                # 위젯 이벤트 시에는 st.stop() 호출하지 않음
                _is_widget_event = st.session_state.get("_last_page", None) == "실제정산"
                if not _is_widget_event:
                    st.stop()
                    return
            
            # ========== [리팩토링] 데이터 준비 (UI 생성 없음) ==========
            prepared_data = prepare_all_categories_data(expense_categories, expense_items, month_total_sales)
            category_totals = prepared_data['category_totals']
            category_prepared_data = prepared_data['category_prepared_data']
            
            # [실험 1: UI 스킵 테스트] - 카테고리 렌더링 스킵
            if skip_ui_test:
                ui_step_timings.append(("all_categories_loop_skip_ui", 0))
                probe.info(f"PROBE 4: 카테고리 루프 스킵 완료 (UI 없이) ({(time.perf_counter()-start)*1000:.1f}ms)")
            else:
                # ========== [리팩토링] 정상 모드: 카테고리 렌더링 수행 ==========
                # prepare 데이터 재사용 (이미 위에서 준비됨)
                t_category_loop_start = time.perf_counter()
                
                # ========== [UI 병목 측정] CATEGORY_LOOP_BLOCK 시작 ==========
                t_category_loop_block_start = time.perf_counter()
                
                # ========== [UI 병목 측정] EDITORS_BLOCK 시작 ==========
                t_editors_block_start = time.perf_counter()
                
                # 카테고리별 렌더링 (prepare 데이터 사용)
                for category, info in expense_categories.items():
                    prepared = category_prepared_data[category]
                    category_total = prepared['category_total']
                    
                    # 카테고리 헤더 (columns 최소화: 카테고리당 1회만)
                    t_category_header = time.perf_counter()
                    header_col1, header_col2 = st.columns([3, 1])
                    with header_col1:
                        st.markdown(f"""
                        <div style="margin: 1.5rem 0 0.5rem 0;">
                            <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
                                {info['icon']} {category}
                            </h3>
                        </div>
                        """, unsafe_allow_html=True)
                        st.caption(f"{info['description']}")
                    with header_col2:
                        if category_total > 0:
                            if info['type'] == 'rate':
                                total_rate = prepared['total_rate']
                                st.markdown(f"""
                                <div style="text-align: right; margin-top: 0.5rem; padding-top: 0.5rem;">
                                    <strong style="color: #667eea; font-size: 1.1rem;">
                                        총 비율: {total_rate:.2f}%
                                    </strong>
                                    <div style="font-size: 0.85rem; color: #666;">
                                        ({category_total:,.0f}원)
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                <div style="text-align: right; margin-top: 0.5rem; padding-top: 0.5rem;">
                                    <strong style="color: #667eea; font-size: 1.1rem;">
                                        총액: {format_korean_currency(int(category_total))}
                                    </strong>
                                    <div style="font-size: 0.85rem; color: #666;">
                                        ({category_total:,.0f}원)
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                    ui_step_timings.append((f"category_header_{category}", (time.perf_counter() - t_category_header) * 1000))
                    
                    # 항목 표시 및 수정 (prepare 데이터 재사용)
                    t_category_render = time.perf_counter()
                    if expense_items[category]:
                        # mixed 타입인 경우 고정 항목과 가변 항목 분리 (prepare 데이터 사용)
                        if prepared['is_mixed']:
                            fixed_items_list = prepared['fixed_items_list']
                            variable_items_list = prepared['variable_items_list']
                            
                            # [B] 고정 항목은 st.data_editor로 통합 (prepare에서 준비된 DataFrame 사용)
                            if fixed_items_list:
                                t_fixed_items = time.perf_counter()
                                # prepare에서 준비된 DataFrame 사용 (중복 생성 제거)
                                fixed_editor_df = prepared['fixed_editor_df']
                                
                                # st.data_editor 1회 호출
                                widget_key = f"settlement_actual::fixed_items_editor::{category}::{selected_year}::{selected_month}"
                                print(f"[WIDGET] data_editor | key={widget_key} | rerun={rerun_count} | STEP={_current_step}")
                                t_editor_start = time.perf_counter()
                                edited_fixed_df = st.data_editor(
                                    fixed_editor_df[['항목명', '금액']],
                                    column_config={
                                        '항목명': st.column_config.TextColumn('항목명', disabled=True),
                                        '금액': st.column_config.NumberColumn('금액 (원)', min_value=0, step=10000, format="%d"),
                                    },
                                    use_container_width=True,
                                    hide_index=True,
                                    key=widget_key,
                                )
                                t_editor_elapsed = (time.perf_counter() - t_editor_start) * 1000
                                ui_step_timings.append((f"editor_fixed_items_{category}", t_editor_elapsed))
                                
                                # 저장 버튼 (columns 최소화: 버튼만)
                                if st.button("💾 저장", key=f"settlement_actual::save_fixed::{category}::{selected_year}::{selected_month}", use_container_width=True):
                                    # 버튼 클릭 시에만 data_editor의 결과를 읽어서 expense_items에 반영
                                    edited_data = edited_fixed_df.to_dict('records')
                                    for edited_row in edited_data:
                                        original_idx = int(edited_row.get('_idx', -1))
                                        if original_idx >= 0 and original_idx < len(fixed_items_list):
                                            new_amount = int(edited_row.get('금액', 0))
                                            fixed_items_list[original_idx]['amount'] = new_amount
                                    expense_items[category] = fixed_items_list + variable_items_list
                                    set_state(f'actual_expense_items_{selected_year}_{selected_month}', expense_items, "expense_items_save")
                                    print(f"[RERUN] st.rerun() 호출 | rerun={rerun_count} | STEP={_current_step} | tag=save_fixed")
                                    st.rerun()
                                
                                ui_step_timings.append((f"fixed_items_{category}", (time.perf_counter() - t_fixed_items) * 1000))
                            
                            if variable_items_list:
                                t_var_items = time.perf_counter()
                                st.markdown("---")
                                with st.expander(f"📋 추가 항목 ({len(variable_items_list)}개)", expanded=True):
                                    for idx, item in enumerate(variable_items_list):
                                        col_a, col_b, col_c = st.columns([3, 2, 1])
                                        with col_a:
                                            edit_key = f"settlement_actual::edit_name::{category}::var::{idx}::{selected_year}::{selected_month}"
                                            edited_name = st.text_input(
                                                "항목명",
                                                value=item.get('item_name', ''),
                                                key=edit_key,
                                            )
                                        with col_b:
                                            edit_amount_key = f"settlement_actual::edit_amount::{category}::var::{idx}::{selected_year}::{selected_month}"
                                            edited_amount = st.number_input(
                                                "금액 (원)",
                                                min_value=0,
                                                value=int(item.get('amount', 0)),
                                                step=10000,
                                                format="%d",
                                                key=edit_amount_key,
                                            )
                                        with col_c:
                                            if st.button("💾", key=f"settlement_actual::save_var::{category}::{idx}::{selected_year}::{selected_month}", help="저장"):
                                                # 버튼 클릭 시에만 session_state 업데이트
                                                if edited_name != item.get('item_name'):
                                                    item['item_name'] = edited_name
                                                if edited_amount != item.get('amount'):
                                                    item['amount'] = edited_amount
                                                set_state(f'actual_expense_items_{selected_year}_{selected_month}', expense_items, "expense_items_save")
                                                print(f"[RERUN] st.rerun() 호출 | rerun={rerun_count} | STEP={_current_step} | tag=save_fixed")
                                            st.rerun()
                                            if st.button("🗑️", key=f"settlement_actual::del_var::{category}::{idx}::{selected_year}::{selected_month}", help="삭제"):
                                                expense_items[category].remove(item)
                                                set_state(f'actual_expense_items_{selected_year}_{selected_month}', expense_items, "expense_items_save")
                                                print(f"[RERUN] st.rerun() 호출 | rerun={rerun_count} | STEP={_current_step} | tag=save_fixed")
                                            st.rerun()
                                ui_step_timings.append((f"variable_items_{category}", (time.perf_counter() - t_var_items) * 1000))
                        else:
                            # 고정 항목 또는 가변 항목만 있는 경우
                            # 가변 항목(재료비 등)은 expander로 표시
                            if not prepared['is_fixed'] and expense_items[category]:
                                t_expander = time.perf_counter()
                                with st.expander(f"📋 입력된 항목 ({len(expense_items[category])}개)", expanded=True):
                                    for idx, item in enumerate(expense_items[category]):
                                        col_a, col_b, col_c = st.columns([3, 2, 1])
                                        with col_a:
                                            # 수정 가능한 항목명
                                            edit_key = f"settlement_actual::edit_name::{category}::{idx}::{selected_year}::{selected_month}"
                                            edited_name = st.text_input(
                                                "항목명",
                                                value=item.get('item_name', ''),
                                                key=edit_key,
                                            )
                                        with col_b:
                                            # 절대 금액 입력
                                            edit_amount_key = f"settlement_actual::edit_amount::{category}::{idx}::{selected_year}::{selected_month}"
                                            edited_amount = st.number_input(
                                                "금액 (원)",
                                                min_value=0,
                                                value=int(item.get('amount', 0)),
                                                step=10000,
                                                format="%d",
                                                key=edit_amount_key,
                                            )
                                        with col_c:
                                            if st.button("💾", key=f"settlement_actual::save_item::{category}::{idx}::{selected_year}::{selected_month}", help="저장"):
                                                # 버튼 클릭 시에만 session_state 업데이트
                                                if edited_name != item.get('item_name'):
                                                    item['item_name'] = edited_name
                                                if edited_amount != item.get('amount'):
                                                    item['amount'] = edited_amount
                                                set_state(f'actual_expense_items_{selected_year}_{selected_month}', expense_items, "expense_items_save")
                                                print(f"[RERUN] st.rerun() 호출 | rerun={rerun_count} | STEP={_current_step} | tag=save_fixed")
                                            st.rerun()
                                            if st.button("🗑️", key=f"settlement_actual::del_item::{category}::{idx}::{selected_year}::{selected_month}", help="삭제"):
                                                expense_items[category].pop(idx)
                                                set_state(f'actual_expense_items_{selected_year}_{selected_month}', expense_items, "expense_items_save")
                                                print(f"[RERUN] st.rerun() 호출 | rerun={rerun_count} | STEP={_current_step} | tag=save_fixed")
                                            st.rerun()
                                ui_step_timings.append((f"expander_{category}", (time.perf_counter() - t_expander) * 1000))
                            elif prepared['is_fixed']:
                                # [B] 고정 항목은 st.data_editor로 통합 (prepare에서 준비된 DataFrame 사용)
                                t_fixed_display = time.perf_counter()
                                t_fixed_render = time.perf_counter()
                                
                                # prepare에서 준비된 DataFrame 사용 (중복 생성 제거)
                                editor_df = prepared['editor_df']
                                widget_key = f"settlement_actual::fixed_editor::{category}::{selected_year}::{selected_month}"
                                
                                if info['type'] == 'rate':
                                    # 비율 입력 모드
                                    print(f"[WIDGET] data_editor | key={widget_key} | rerun={rerun_count} | STEP={_current_step}")
                                    t_editor_start = time.perf_counter()
                                    edited_df = st.data_editor(
                                        editor_df[['항목명', '비율 (%)', '계산금액']],
                                        column_config={
                                            '항목명': st.column_config.TextColumn('항목명', disabled=True),
                                            '비율 (%)': st.column_config.NumberColumn('비율 (%)', min_value=0.0, max_value=100.0, step=0.1, format="%.2f"),
                                            '계산금액': st.column_config.NumberColumn('계산금액 (원)', disabled=True, format="%d"),
                                        },
                                        use_container_width=True,
                                        hide_index=True,
                                        key=widget_key,
                                    )
                                    t_editor_elapsed = (time.perf_counter() - t_editor_start) * 1000
                                    ui_step_timings.append((f"editor_fixed_{category}_rate", t_editor_elapsed))
                                else:
                                    # 절대 금액 입력 모드
                                    print(f"[WIDGET] data_editor | key={widget_key} | rerun={rerun_count} | STEP={_current_step}")
                                    t_editor_start = time.perf_counter()
                                    edited_df = st.data_editor(
                                        editor_df[['항목명', '금액']],
                                        column_config={
                                            '항목명': st.column_config.TextColumn('항목명', disabled=True),
                                            '금액': st.column_config.NumberColumn('금액 (원)', min_value=0, step=10000, format="%d"),
                                        },
                                        use_container_width=True,
                                        hide_index=True,
                                        key=widget_key,
                                    )
                                    t_editor_elapsed = (time.perf_counter() - t_editor_start) * 1000
                                    ui_step_timings.append((f"editor_fixed_{category}", t_editor_elapsed))
                                
                                # 저장 버튼 (columns 최소화: 버튼만)
                                if st.button("💾 저장", key=f"settlement_actual::save_editor::{category}::{selected_year}::{selected_month}", use_container_width=True):
                                    # 버튼 클릭 시에만 data_editor의 결과를 읽어서 expense_items에 반영
                                    edited_data = edited_df.to_dict('records')
                                    for edited_row in edited_data:
                                        original_idx = edited_row.get('_idx', -1)
                                        if original_idx >= 0 and original_idx < len(expense_items[category]):
                                            if info['type'] == 'rate':
                                                new_rate = float(edited_row.get('비율 (%)', 0))
                                                expense_items[category][original_idx]['amount'] = new_rate
                                            else:
                                                new_amount = int(edited_row.get('금액', 0))
                                                expense_items[category][original_idx]['amount'] = new_amount
                                    set_state(f'actual_expense_items_{selected_year}_{selected_month}', expense_items, "expense_items_save")
                                    print(f"[RERUN] st.rerun() 호출 | rerun={rerun_count} | STEP={_current_step} | tag=save_fixed")
                                    st.rerun()
                                ui_step_timings.append((f"fixed_display_{category}_render", (time.perf_counter() - t_fixed_render) * 1000))
                                ui_step_timings.append((f"fixed_display_{category}", (time.perf_counter() - t_fixed_display) * 1000))
                    
                    # 고정 항목이 아니거나 mixed 타입인 경우 새 항목 추가 (container 제거, columns 최소화)
                    if not prepared['is_fixed'] or prepared['is_mixed']:
                        t_add_item = time.perf_counter()
                        st.markdown("---")
                        add_col1, add_col2, add_col3 = st.columns([3, 2, 1])
                        with add_col1:
                            new_item_name = st.text_input(
                                "항목명",
                                key=f"settlement_actual::new_item_name::{category}::{selected_year}::{selected_month}",
                                placeholder="예: 월세, 관리비 등"
                            )
                        with add_col2:
                            new_item_amount = st.number_input(
                                "금액 (원)",
                                min_value=0,
                                value=0,
                                step=10000,
                                format="%d",
                                key=f"settlement_actual::new_item_amount::{category}::{selected_year}::{selected_month}"
                            )
                        with add_col3:
                            if st.button("➕ 추가", key=f"settlement_actual::add_item::{category}::{selected_year}::{selected_month}", use_container_width=True):
                                if new_item_name.strip():
                                    # mixed 타입인 경우 고정 항목 이름과 중복 체크
                                    if prepared['is_mixed']:
                                        fixed_items_names = prepared['fixed_items_names']
                                        if new_item_name.strip() in fixed_items_names:
                                            st.error(f"'{new_item_name.strip()}'는 고정 항목입니다.")
                                        else:
                                            expense_items[category].append({
                                                'item_name': new_item_name.strip(),
                                                'amount': new_item_amount
                                            })
                                            set_state(f'actual_expense_items_{selected_year}_{selected_month}', expense_items, "expense_items_save")
                                            print(f"[RERUN] st.rerun() 호출 | rerun={rerun_count} | STEP={_current_step} | tag=add_item")
                                            st.rerun()
                                    else:
                                        expense_items[category].append({
                                            'item_name': new_item_name.strip(),
                                            'amount': new_item_amount
                                        })
                                        set_state(f'actual_expense_items_{selected_year}_{selected_month}', expense_items, "expense_items_save")
                                        print(f"[RERUN] st.rerun() 호출 | rerun={rerun_count} | STEP={_current_step} | tag=add_item")
                                        st.rerun()
                                else:
                                    st.error("항목명을 입력해주세요.")
                        ui_step_timings.append((f"add_item_{category}", (time.perf_counter() - t_add_item) * 1000))
                    
                    ui_step_timings.append((f"category_loop_{category}_render", (time.perf_counter() - t_category_render) * 1000))
                
                # [실험 2 해석]
                # - *_prepare: 데이터 준비/연산 시간 (순수 Python 연산)
                # - *_render: st.* 호출로 UI 렌더링 시간 (Streamlit 위젯 생성)
                # - prepare가 크면: 데이터 처리/세션 접근이 병목
                # - render가 크면: UI 위젯 생성이 병목 (st.number_input, st.columns 등)
                
                ui_step_timings.append(("all_categories_loop", (time.perf_counter() - t_category_loop_start) * 1000))
                
                # ========== [UI 병목 측정] EDITORS_BLOCK 종료 ==========
                if t_editors_block_start is not None:
                    t_editors_block_elapsed = (time.perf_counter() - t_editors_block_start) * 1000
                    ui_step_timings.append(("EDITORS_BLOCK", t_editors_block_elapsed))
                
                # ========== [UI 병목 측정] CATEGORY_LOOP_BLOCK 종료 ==========
                if t_category_loop_block_start is not None:
                    t_category_loop_block_elapsed = (time.perf_counter() - t_category_loop_block_start) * 1000
                    ui_step_timings.append(("CATEGORY_LOOP_BLOCK", t_category_loop_block_elapsed))
                
                # probe.info(f"PROBE 4: 카테고리 루프 완료 ({(time.perf_counter()-start)*1000:.1f}ms)")
            
            # STEP 5: after UI render loops
            _current_step = 5
            _render_phase = "done"
            # t_step5 = time.perf_counter()
            # elapsed = (t_step5 - t_step_start) * 1000
            # print(f"[STEP 5] after UI render loops (rerun={rerun_count}) ({elapsed:.1f}ms)")
            # probe.caption(f"🔍 STEP 5: after UI render loops (rerun={rerun_count}) ({elapsed:.1f}ms)")
            
            # 전체 비용 합계 계산
            total_actual_cost = sum(category_totals.values())
            
            # 이익 및 이익률 계산
            actual_sales = month_total_sales
            actual_profit = actual_sales - total_actual_cost
            profit_margin = (actual_profit / actual_sales * 100) if actual_sales > 0 else 0.0
            
            t_summary = time.perf_counter()
            render_section_divider()
            
            # 요약 정보
            st.markdown("**📊 비용 합계 요약**")
            summary_col1, summary_col2, summary_col3 = st.columns(3)
            with summary_col1:
                st.metric("실제 총 비용", f"{total_actual_cost:,.0f}원")
            with summary_col2:
                st.metric("실제 이익", f"{actual_profit:,.0f}원")
            with summary_col3:
                st.metric("실제 이익률", f"{profit_margin:,.1f}%")
            ui_step_timings.append(("summary_metrics", (time.perf_counter() - t_summary) * 1000))
            
            # 카테고리별 비용 요약 테이블
            t_cost_table = time.perf_counter()
            cost_summary_data = []
            for category, total in category_totals.items():
                cost_summary_data.append({
                    '비용 항목': category,
                    '금액': f"{total:,.0f}원",
                    '비율': f"{(total / total_actual_cost * 100):.1f}%" if total_actual_cost > 0 else "0.0%"
                })
            cost_summary_df = pd.DataFrame(cost_summary_data)
            st.dataframe(cost_summary_df, use_container_width=True, hide_index=True)
            ui_step_timings.append(("cost_summary_table", (time.perf_counter() - t_cost_table) * 1000))
            
            render_section_divider()
            
            # 저장 버튼
            save_col, _ = st.columns([1, 4])
            with save_col:
                if st.button("💾 실제 정산 저장", type="primary", use_container_width=True, key="settlement_actual_save_button"):
                    try:
                        from src.storage_supabase import save_actual_settlement
                        
                        print(f"[SAVE] 저장 시작 | year={selected_year}, month={selected_month} | rerun={rerun_count} | STEP={_current_step}")
                        
                        # 기능 점검 로그 (dev_mode)
                        if is_dev_mode():
                            save_payload = {
                                "year": selected_year,
                                "month": selected_month,
                                "actual_sales": actual_sales,
                                "total_actual_cost": total_actual_cost,
                                "actual_profit": actual_profit,
                                "profit_margin": profit_margin,
                            }
                            st.info(f"💾 저장 시작: {save_payload}")
                        
                        # run_write로 통일
                        from src.utils.crud_guard import run_write
                        from src.storage_supabase import save_actual_settlement
                        
                        run_write(
                            "save_actual_settlement",
                            lambda: save_actual_settlement(
                                selected_year,
                                selected_month,
                                actual_sales,
                                total_actual_cost,
                                actual_profit,
                                profit_margin,
                            ),
                            targets=["cost", "expense_structure", "settlement_actual"],
                            extra={"year": selected_year, "month": selected_month},
                            success_message=f"✅ 실제 정산이 저장되었습니다! ({selected_year}년 {selected_month}월)"
                        )
                        # run_write가 성공/실패를 처리하고 rerun도 호출하므로 추가 코드 불필요
                    except Exception as e:
                        # Phase 3: 에러 메시지 표준화
                        error_msg = handle_data_error("실제 정산 데이터 저장", e)
                        print(f"[SAVE] 저장 중 에러: {e} | rerun={rerun_count}")
                        if is_dev_mode():
                            st.error(f"❌ 저장 에러: {error_msg}")
                            import traceback
                            st.code(traceback.format_exc())
                        st.error(error_msg)
            
            # [B] 하단에 기존 정산 이력 표시 (토글로 상세 표시 제어)
            # probe.info(f"PROBE 5: history 섹션 시작 직전 ({(time.perf_counter()-start)*1000:.1f}ms)")
            t_history = time.perf_counter()
            try:
                render_section_divider()
                st.markdown("**📜 실제 정산 이력 (월별)**")
                
                # actual_df가 비어있거나 None인 경우 처리
                if actual_df is None or actual_df.empty:
                    st.info("📝 정산 이력이 없습니다. (아직 저장된 실제정산 데이터가 없어요)")
                    ui_step_timings.append(("history_section_empty", (time.perf_counter() - t_history) * 1000))
                else:
                    # [B] 요약 정보는 항상 표시
                    history_df = actual_df.copy()
                    if "연도" in history_df.columns and "월" in history_df.columns:
                        history_df = history_df.sort_values(["연도", "월"], ascending=[False, False])
                    
                    # 요약 통계
                    total_count = len(history_df)
                    if total_count > 0:
                        if "실제매출" in history_df.columns:
                            total_sales = pd.to_numeric(history_df["실제매출"], errors='coerce').sum()
                            avg_sales = pd.to_numeric(history_df["실제매출"], errors='coerce').mean()
                            st.markdown(f"**요약:** 총 {total_count}개월 | 누적 매출: {total_sales:,.0f}원 | 월평균: {avg_sales:,.0f}원")
                    
                    # [B] 상세 테이블은 토글로 제어
                    show_history_detail = st.toggle("📋 히스토리 상세 보기", value=False, key="settlement_history_detail_toggle")
                    
                    if show_history_detail:
                        t_history_table = time.perf_counter()
                        display_history = history_df.copy()
                        
                        # 타입 변환을 한 번만 수행하고 apply (문자열 포맷팅은 apply 필요)
                        t0 = time.perf_counter()
                        if "실제매출" in display_history.columns:
                            display_history["실제매출"] = pd.to_numeric(display_history["실제매출"], errors='coerce').apply(lambda x: f"{x:,.0f}원")
                        if "실제비용" in display_history.columns:
                            display_history["실제비용"] = pd.to_numeric(display_history["실제비용"], errors='coerce').apply(lambda x: f"{x:,.0f}원")
                        if "실제이익" in display_history.columns:
                            display_history["실제이익"] = pd.to_numeric(display_history["실제이익"], errors='coerce').apply(lambda x: f"{x:,.0f}원")
                        if "실제이익률" in display_history.columns:
                            display_history["실제이익률"] = pd.to_numeric(display_history["실제이익률"], errors='coerce').apply(lambda x: f"{x:,.1f}%")
                        t1 = time.perf_counter()
                        record_compute_call("actual_settlement: format_history_apply", (t1 - t0) * 1000,
                                          rows_in=len(display_history), rows_out=len(display_history))
                        
                        # 큰 DataFrame 최적화: 최대 200행만 표시
                        if len(display_history) > 200:
                            st.info(f"⚠️ 전체 {len(display_history)}개 중 최근 200개만 표시합니다. 전체 데이터는 다운로드 버튼을 사용하세요.")
                            display_history = display_history.head(200)
                        
                        st.dataframe(display_history, use_container_width=True, hide_index=True)
                        ui_step_timings.append(("history_table", (time.perf_counter() - t_history_table) * 1000))
                    else:
                        ui_step_timings.append(("history_table_skipped", 0))
                
                ui_step_timings.append(("history_section", (time.perf_counter() - t_history) * 1000))
            except Exception as history_error:
                # 정산 이력 표시 중 에러가 발생해도 UI는 계속 진행
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"정산 이력 표시 중 에러: {history_error}")
                st.warning(f"⚠️ 정산 이력 표시 중 오류가 발생했습니다: {str(history_error)}")
                ui_step_timings.append(("history_section_error", (time.perf_counter() - t_history) * 1000))
            
            t_ui_end = time.perf_counter()
            # probe.success(f"PROBE 6: 페이지 끝 (마지막 줄) ({(time.perf_counter()-start)*1000:.1f}ms)")
            
            # ========== [RERUN 디버깅] session_state 변경 추적 (위젯 자동 생성 key 필터링) ==========
            # session_state snapshot (렌더 끝 시점)
            session_state_snapshot_end = set(st.session_state.keys())
            set_state("_actual_state_snapshot_end", list(session_state_snapshot_end), "snapshot_end")
            
            # 변경된 key 목록 계산
            changed_keys = session_state_snapshot_end - session_state_snapshot_start
            removed_keys = session_state_snapshot_start - session_state_snapshot_end  # 제거된 키들
            
            # 디버그 키 제외
            debug_keys = {
                "_actual_render_count", "_actual_run_id", "_actual_state_snapshot_start", 
                "_actual_state_snapshot_end", "_dbg_rerun_count", "_render_phase"
            }
            
            # ========== [필터] 위젯 자동 생성 key 분리 ==========
            def is_ui_widget_key(key):
                """위젯이 자동 생성하는 key인지 판단"""
                # "::" 포함된 key (위젯 key 패턴)
                if "::" in key:
                    return True
                # "settlement_actual::" prefix
                if key.startswith("settlement_actual::"):
                    return True
                # UI 위젯 prefix 패턴
                ui_widget_prefixes = [
                    "new_item", "fixed_editor", "add_item", "edit_name", "edit_amount",
                    "save_", "del_", "settlement_actual_settlement_", "settlement_skip_ui_test",
                    "settlement_safe_mode", "settlement_history_detail_toggle"
                ]
                for prefix in ui_widget_prefixes:
                    if key.startswith(prefix) or prefix in key:
                        return True
                return False
            
            def is_logic_key(key):
                """개발자 로직에 의한 key인지 판단 (rerun 원인 후보)"""
                # ss_로 시작하는 키는 get_session_df가 관리하는 캐시 키이므로 제외
                # (이미 @st.cache_data로 캐싱되어 있고, get_session_df 내부에서 if key not in 체크함)
                if key.startswith("ss_"):
                    return False
                
                # _actual_page_init은 최초 1회만 설정되므로 정상 (제외)
                if key == "_actual_page_init":
                    return False
                
                # actual_expense_items_*는 이미 if key not in 체크를 하고 있으므로 정상 (제외)
                if key.startswith("actual_expense_items_"):
                    return False
                
                # 감시 대상 패턴 (ss_, _actual_page_init, actual_expense_items_ 제외)
                logic_patterns = [
                    "expense", "actual_", "temp_", "init", "cache",
                    "_actual_", "_dbg_", "settlement_data", "month_sales", "sales_df"
                ]
                for pattern in logic_patterns:
                    if pattern in key.lower():
                        # ss_, _actual_page_init, actual_expense_items_는 이미 위에서 제외했으므로 여기서는 포함
                        return True
                return False
            
            # UI 위젯 key와 로직 key 분리
            changed_keys_ui = [k for k in changed_keys if is_ui_widget_key(k) and k not in debug_keys]
            changed_keys_logic = [k for k in changed_keys if is_logic_key(k) and k not in debug_keys and not is_ui_widget_key(k)]
            removed_keys_ui = [k for k in removed_keys if is_ui_widget_key(k) and k not in debug_keys]
            removed_keys_logic = [k for k in removed_keys if is_logic_key(k) and k not in debug_keys and not is_ui_widget_key(k)]
            
            # 로그 출력 (로직 key만)
            if changed_keys_logic or removed_keys_logic:
                print(f"[RERUN DEBUG] 🚨 로직 session_state 변경 감지!")
                print(f"  run_id={_actual_run_id} | render_count={render_count} | rerun_count={rerun_count}")
                if changed_keys_logic:
                    print(f"  추가/변경된 로직 키: {', '.join(changed_keys_logic)}")
                if removed_keys_logic:
                    print(f"  제거된 로직 키: {', '.join(removed_keys_logic)}")
            
            # [A] UI_STEP_TIMINGS 표를 페이지 상단/중간에 먼저 표시 (페이지 하단에 있으면 중간에서 멈출 때 안 보임) - REMOVED
            # try:
            #     from src.auth import is_dev_mode
            #     if is_dev_mode():
            #         # ========== [RERUN 디버깅] 개발모드 화면 표시 (UI/Logic 분리) ==========
            #         ...
            # except Exception as timing_error:
            #     st.error(f"UI_STEP_TIMINGS 표시 중 에러: {timing_error}")
            
            # ========== [UI 병목 측정] UI_TOTAL_BLOCK 종료 (render 함수 끝 직전) ==========
            if t_ui_total_block_start is not None:
                t_ui_total_block_elapsed = (time.perf_counter() - t_ui_total_block_start) * 1000
                ui_step_timings.append(("UI_TOTAL_BLOCK", t_ui_total_block_elapsed))
                
    except Exception as e:
        # 예외로 인해 아래 코드가 실행되지 않아도 최소 probe는 보이게
        st.error(f"실제정산 렌더 중 에러: {e}")
        st.exception(e)
        # probe.error(f"PROBE ERROR: 예외 발생 ({(time.perf_counter()-start)*1000:.1f}ms)")
        
        # 예외 발생 시에도 UI_TOTAL_BLOCK 종료 기록
        if t_ui_total_block_start is not None:
            t_ui_total_block_elapsed = (time.perf_counter() - t_ui_total_block_start) * 1000
            ui_step_timings.append(("UI_TOTAL_BLOCK", t_ui_total_block_elapsed))
        
        return


# Streamlit 멀티페이지에서 직접 실행될 때
# 주석 처리: app.py에서만 렌더되도록 함 (중복 호출 방지)
# render_settlement_actual()
