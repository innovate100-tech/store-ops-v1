"""
Supabase 기반 저장소 모듈 (기존 storage.py의 DB 버전)
auth.uid() 기반 RLS로 보안 적용
"""
import pandas as pd
import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple
import json
from zoneinfo import ZoneInfo
from src.utils.time_utils import now_kst, today_kst, current_year_kst, current_month_kst

# auth.py에서 함수 import (is_dev_mode는 _is_dev_mode로 alias하여 이름 충돌 방지)
from src.auth import get_supabase_client, get_current_store_id, get_read_client, get_read_client_mode, is_dev_mode as _is_dev_mode
import streamlit as st
import time
from functools import wraps

# boot_perf에서 데이터 호출 계측 함수 import
try:
    from src.utils.boot_perf import record_data_call
except ImportError:
    # boot_perf가 없을 때를 대비한 fallback
    def record_data_call(name: str, ms: float, rows: int = None, source: str = None):
        pass

# cache_tokens에서 버전 토큰 함수 import
try:
    from src.utils.cache_tokens import bump_data_version, bump_versions
except ImportError:
    # cache_tokens가 없을 때를 대비한 fallback
    def bump_data_version(name: str):
        pass
    def bump_versions(names: List[str]):
        pass

logger = logging.getLogger(__name__)

# 쿼리 타이밍 로그 저장 (개발모드에서만)
_query_timing_log = []
_MAX_QUERY_LOG = 50  # 최대 저장할 쿼리 로그 개수

# 캐시 MISS 로그 저장 (개발모드에서만)
_cache_miss_log = []
_MAX_CACHE_LOG = 50  # 최대 저장할 캐시 MISS 로그 개수


def setup_logger():
    """로깅 시스템 설정"""
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger


setup_logger()


# ============================================
# Client Mode & Query Timing Functions
# ============================================

def get_client_mode() -> str:
    """
    현재 사용 중인 DB 클라이언트 모드 반환
    
    Returns:
        "anon" / "auth" / "service_role_dev"
    """
    try:
        return get_read_client_mode()
    except Exception:
        return "unknown"


def timed_select(query_name: str, query_func, *args, **kwargs):
    """
    Supabase select 쿼리를 실행하고 타이밍을 기록하는 헬퍼
    
    Args:
        query_name: 쿼리 이름 (로그에 표시될 이름)
        query_func: 실행할 쿼리 함수 (예: lambda: supabase.table("menu_master").select("*").execute())
        *args, **kwargs: query_func에 전달할 인자
    
    Returns:
        쿼리 실행 결과
    """
    global _query_timing_log  # 함수 최상단에 global 선언
    start_time = time.time()
    try:
        result = query_func(*args, **kwargs)
        elapsed_ms = (time.time() - start_time) * 1000
        row_count = len(result.data) if result.data else 0
        
        # 개발모드에서만 로그 저장
        if _is_dev_mode():
            _query_timing_log.append({
                "query_name": query_name,
                "ms": round(elapsed_ms, 2),
                "rows": row_count,
                "timestamp": time.time()
            })
            # 최대 개수 제한
            if len(_query_timing_log) > _MAX_QUERY_LOG:
                _query_timing_log[:] = _query_timing_log[-_MAX_QUERY_LOG:]
        
        logger.debug(f"Query '{query_name}': {elapsed_ms:.2f}ms, {row_count} rows")
        return result
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        logger.error(f"Query '{query_name}' failed after {elapsed_ms:.2f}ms: {e}")
        if _is_dev_mode():
            _query_timing_log.append({
                "query_name": f"{query_name} (ERROR)",
                "ms": round(elapsed_ms, 2),
                "rows": 0,
                "timestamp": time.time(),
                "error": str(e)
            })
        raise


def get_query_timing_log() -> list:
    """
    쿼리 타이밍 로그 반환 (개발모드에서만)
    
    Returns:
        최근 쿼리 로그 리스트
    """
    if _is_dev_mode():
        return _query_timing_log.copy()
    return []


def clear_query_timing_log():
    """쿼리 타이밍 로그 초기화"""
    global _query_timing_log
    _query_timing_log = []


def _log_cache_miss(function_name: str, **kwargs):
    """
    캐시 MISS 로그 기록 (개발모드에서만)
    
    Args:
        function_name: 함수 이름 (예: "load_csv", "load_expense_structure")
        **kwargs: 캐시 키에 포함된 파라미터들 (filename, store_id, client_mode, year, month 등)
    """
    try:
        if _is_dev_mode():
            global _cache_miss_log
            # 민감 정보 제거
            safe_kwargs = {}
            for key, value in kwargs.items():
                if key in ['store_id', 'client_mode', 'filename', 'year', 'month']:
                    # store_id는 일부만 표시 (보안)
                    if key == 'store_id' and value:
                        safe_kwargs[key] = f"{str(value)[:8]}..." if len(str(value)) > 8 else str(value)
                    else:
                        safe_kwargs[key] = value
            
            _cache_miss_log.append({
                "function": function_name,
                "timestamp": time.time(),
                "params": safe_kwargs
            })
            # 최대 개수 제한
            if len(_cache_miss_log) > _MAX_CACHE_LOG:
                _cache_miss_log = _cache_miss_log[-_MAX_CACHE_LOG:]
    except Exception:
        pass  # 로그 실패해도 계속 진행


def get_cache_miss_log() -> list:
    """
    캐시 MISS 로그 반환 (개발모드에서만)
    
    Returns:
        최근 캐시 MISS 로그 리스트
    """
    if _is_dev_mode():
        return _cache_miss_log.copy()
    return []


def clear_cache_miss_log():
    """캐시 MISS 로그 초기화"""
    global _cache_miss_log
    _cache_miss_log = []


# ============================================
# Helper Functions
# ============================================

def _get_id_by_name(supabase, table_name: str, name_column: str, name_value: str, store_id: str = None):
    """
    이름으로 ID 조회 (공통 헬퍼 함수)
    
    Args:
        supabase: Supabase 클라이언트
        table_name: 테이블명
        name_column: 이름 컬럼명 (예: 'name')
        name_value: 조회할 이름 값
        store_id: store_id 필터 (None이면 사용 안 함)
    
    Returns:
        str: ID (없으면 None)
    """
    try:
        query = supabase.table(table_name).select("id")
        if store_id:
            query = query.eq("store_id", store_id)
        query = query.eq(name_column, name_value)
        # timed_select로 쿼리 실행 및 타이밍 기록
        result = timed_select(
            f"_get_id_by_name({table_name}.{name_column}={name_value})",
            lambda: query.execute()
        )
        if result.data:
            return result.data[0]['id']
        return None
    except Exception as e:
        logger.error(f"Failed to get ID for {table_name}.{name_column}={name_value}: {e}")
        return None


def _check_duplicate(supabase, table_name: str, name_column: str, name_value: str, store_id: str):
    """
    중복 체크 (공통 헬퍼 함수)
    
    Args:
        supabase: Supabase 클라이언트
        table_name: 테이블명
        name_column: 이름 컬럼명
        name_value: 체크할 이름 값
        store_id: store_id
    
    Returns:
        bool: 중복이면 True
    """
    try:
        query = supabase.table(table_name).select("id").eq("store_id", store_id).eq(name_column, name_value)
        # timed_select로 쿼리 실행 및 타이밍 기록
        result = timed_select(
            f"_check_duplicate({table_name}.{name_column}={name_value})",
            lambda: query.execute()
        )
        return len(result.data) > 0
    except Exception:
        return False


def _check_supabase_for_dev_mode():
    """
    Supabase 클라이언트 반환 (에러 처리)
    
    DEV MODE(st.session_state['dev_mode'] == True)에서는
    Supabase를 사용하지 않으므로 None을 반환하고,
    호출하는 쪽에서 이를 감지해 로컬/빈 데이터로 처리하게 한다.
    """
    # DEV MODE에서는 Supabase를 사용하지 않음
    if st.session_state.get("dev_mode", False):
        logger.info("DEV MODE: Supabase client is disabled (returning None).")
        return None
    
    supabase = get_supabase_client()
    if not supabase:
        raise Exception("Supabase not available")
    return supabase


# ============================================
# Session Cache Utilities (세션 캐시 유틸)
# ============================================

def get_session_df(key: str, loader_fn, *args, **kwargs):
    """
    세션 캐시 기반 데이터 로드 유틸
    세션당 1회만 로드하여 중복 로드를 원천 차단
    
    Args:
        key: 세션 캐시 키 (예: "ss_menu_master_df")
        loader_fn: 데이터 로드 함수 (예: load_csv)
        *args, **kwargs: loader_fn에 전달할 인자
    
    Returns:
        pandas.DataFrame
    """
    # 세션 캐시에 있으면 즉시 반환 (렌더 중 매번 덮어쓰기 방지)
    if key in st.session_state:
        if _is_dev_mode():
            logger.debug(f"Session cache HIT: {key}")
        return st.session_state[key]
    
    # 세션 캐시에 없으면 로드 후 저장 (없을 때만 1회 세팅)
    if _is_dev_mode():
        logger.debug(f"Session cache MISS: {key} (로딩 중...)")
    
    try:
        df = loader_fn(*args, **kwargs)
        # 렌더 중 매번 덮어쓰기 방지: 없을 때만 저장
        if key not in st.session_state:
            st.session_state[key] = df
            if _is_dev_mode():
                logger.debug(f"Session cache SET: {key} ({len(df)} rows)")
        return df
    except Exception as e:
        logger.error(f"Session cache load failed for {key}: {e}")
        # 오류 시 빈 DataFrame 반환 (없을 때만 저장)
        empty_df = pd.DataFrame()
        if key not in st.session_state:
            st.session_state[key] = empty_df
        return empty_df


def clear_session_cache(*keys: str):
    """
    세션 캐시 무효화 (저장/수정/삭제 후 호출)
    
    Args:
        *keys: 삭제할 세션 캐시 키들 (예: "ss_menu_master_df", "ss_ingredient_master_df")
    """
    for key in keys:
        if key in st.session_state:
            del st.session_state[key]
            if _is_dev_mode():
                logger.debug(f"Session cache CLEARED: {key}")


def hard_clear_all(reason: str = "unknown"):
    """
    전체 캐시 강제 무효화 (비상/디버깅용)
    
    Args:
        reason: clear 이유 (디버깅용)
    """
    try:
        # @st.cache_data 캐시 전체 무효화
        load_csv.clear()
        load_expense_structure.clear()
        load_key_menus.clear()
        
        # dashboard.py의 compute 캐시도 무효화
        try:
            import ui_pages.dashboard as dashboard_module
            if hasattr(dashboard_module, 'compute_merged_sales_visitors'):
                dashboard_module.compute_merged_sales_visitors.clear()
            if hasattr(dashboard_module, 'compute_monthly_summary'):
                dashboard_module.compute_monthly_summary.clear()
            if hasattr(dashboard_module, 'compute_menu_sales_summary'):
                dashboard_module.compute_menu_sales_summary.clear()
        except Exception:
            pass
        
        # 세션 캐시 전체 정리 (ss_로 시작하는 키들)
        keys_to_remove = [key for key in st.session_state.keys() if key.startswith('ss_')]
        for key in keys_to_remove:
            del st.session_state[key]
        
        # LAST_INVALIDATION 기록
        try:
            from src.utils.boot_perf import record_invalidation
            record_invalidation(reason=reason, targets=["ALL"], mode="hard")
        except Exception:
            pass
        
        if _is_dev_mode():
            logger.warning(f"HARD CLEAR ALL: {reason}")
    except Exception as e:
        logger.error(f"hard_clear_all 실패: {e}")


def soft_invalidate(reason: str, targets: List[str], session_keys: List[str] = None):
    """
    소프트 무효화: token bump + 부분 캐시 clear
    
    Args:
        reason: 무효화 이유 (디버깅용)
        targets: 무효화할 데이터 타입 리스트 (예: ["sales", "visitors", "menus"])
        session_keys: 무효화할 세션 캐시 키 리스트 (선택, None이면 targets 기반으로 자동 결정)
    """
    try:
        # 1. 버전 토큰 증가
        from src.utils.cache_tokens import bump_versions
        bump_versions(targets)
        
        # 2. read 캐시 부분 clear (targets 기반)
        # targets 매핑: 어떤 데이터 타입이 어떤 로더에 영향을 주는지
        cache_mapping = {
            "sales": ["load_csv"],  # sales.csv
            "visitors": ["load_csv"],  # naver_visitors.csv
            "menus": ["load_csv"],  # menu_master.csv
            "recipes": ["load_csv"],  # recipes.csv
            "ingredients": ["load_csv"],  # ingredient_master.csv
            "cost": ["load_expense_structure"],  # expense_structure
            "expense_structure": ["load_expense_structure"],
        }
        
        loaders_to_clear = set()
        for target in targets:
            if target in cache_mapping:
                loaders_to_clear.update(cache_mapping[target])
        
        # 실제 clear 실행
        if "load_csv" in loaders_to_clear:
            load_csv.clear()
        if "load_expense_structure" in loaders_to_clear:
            load_expense_structure.clear()
        if "load_key_menus" in loaders_to_clear or "menus" in targets:
            load_key_menus.clear()
        
        # 3. 세션 캐시 부분 clear
        if session_keys is None:
            # targets 기반으로 자동 결정
            session_key_mapping = {
                "sales": ["ss_sales_df"],
                "visitors": ["ss_visitors_df"],
                "menus": ["ss_menu_master_df"],
                "recipes": ["ss_recipes_df"],
                "ingredients": ["ss_ingredient_master_df"],
                "cost": ["ss_expense_structure_df"],
                "expense_structure": ["ss_expense_structure_df"],
                "inventory": ["ss_inventory_df"],
            }
            session_keys = []
            for target in targets:
                if target in session_key_mapping:
                    session_keys.extend(session_key_mapping[target])
        
        for key in session_keys:
            if key in st.session_state:
                del st.session_state[key]
                if _is_dev_mode():
                    logger.debug(f"Session cache CLEARED: {key}")
        
        # 4. LAST_INVALIDATION 기록
        try:
            from src.utils.boot_perf import record_invalidation
            record_invalidation(reason=reason, targets=targets, mode="soft")
        except Exception:
            pass
        
        if _is_dev_mode():
            logger.info(f"SOFT INVALIDATE: {reason}, targets={targets}")
    except Exception as e:
        logger.error(f"soft_invalidate 실패: {e}")
        # 실패 시 안전을 위해 hard clear로 폴백 (dev_mode에서만)
        if _is_dev_mode() and st.session_state.get("force_hard_clear", False):
            hard_clear_all(reason=f"soft_invalidate 실패 후 폴백: {reason}")


def _clear_cache_and_session(affected_keys: List[str]):
    """
    캐시 클리어 및 세션 캐시 무효화 헬퍼 함수 (레거시 호환)
    
    Args:
        affected_keys: 무효화할 세션 캐시 키 리스트
    """
    # force_hard_clear 플래그 확인 (dev_mode에서만)
    if _is_dev_mode() and st.session_state.get("force_hard_clear", False):
        hard_clear_all(reason="force_hard_clear 플래그 활성화")
        return
    
    # 기본 동작: soft_invalidate로 전환
    # affected_keys에서 targets 추론 (키 이름 기반)
    targets = []
    if any("menu" in key.lower() for key in affected_keys):
        targets.append("menus")
    if any("recipe" in key.lower() for key in affected_keys):
        targets.append("recipes")
    if any("ingredient" in key.lower() for key in affected_keys):
        targets.append("ingredients")
    if any("expense" in key.lower() for key in affected_keys):
        targets.append("cost")
        targets.append("expense_structure")
    
    if targets:
        soft_invalidate(reason="레거시 _clear_cache_and_session 호출", targets=targets, session_keys=affected_keys)
    else:
        # targets를 추론할 수 없으면 안전을 위해 hard clear (dev_mode에서만 경고)
        if _is_dev_mode():
            logger.warning(f"_clear_cache_and_session: targets 추론 실패, hard clear 실행. affected_keys={affected_keys}")
        hard_clear_all(reason="targets 추론 실패")


def invalidate_read_caches(table_name: str = None):
    """
    읽기 전용 캐시 무효화 (write 후 호출)
    
    Args:
        table_name: 무효화할 테이블명 (None이면 전체 무효화)
    """
    try:
        if table_name is None:
            # 전체 캐시 무효화
            load_csv.clear()
            load_expense_structure.clear()
            load_key_menus.clear()
        else:
            # 특정 테이블만 무효화 (필요시 구현)
            # 현재는 전체 무효화만 지원
            load_csv.clear()
            load_expense_structure.clear()
            load_key_menus.clear()
        
        # dashboard.py의 compute 캐시도 무효화
        try:
            import ui_pages.dashboard as dashboard_module
            if hasattr(dashboard_module, 'compute_merged_sales_visitors'):
                dashboard_module.compute_merged_sales_visitors.clear()
            if hasattr(dashboard_module, 'compute_monthly_summary'):
                dashboard_module.compute_monthly_summary.clear()
            if hasattr(dashboard_module, 'compute_menu_sales_summary'):
                dashboard_module.compute_menu_sales_summary.clear()
        except Exception:
            pass  # dashboard 모듈이 없거나 함수가 없으면 무시
    except Exception:
        pass


# ============================================
# Load Functions (CSV 호환 인터페이스 유지)
# ============================================

# Phase 2: 리소스 관리 - 데이터 타입별 TTL 분리
def _get_cache_ttl(filename: str) -> int:
    """
    파일명에 따라 적절한 캐시 TTL 반환
    
    - 마스터 데이터 (메뉴, 재료): 3600초 (1시간) - 자주 변경되지 않음
    - 트랜잭션 데이터 (매출, 방문자): 60초 (1분) - 자주 변경됨
    - 중간 데이터 (재고, 발주): 300초 (5분) - 중간 빈도
    """
    master_data = ['menu_master.csv', 'ingredient_master.csv', 'recipes.csv', 'suppliers.csv']
    transaction_data = ['sales.csv', 'naver_visitors.csv', 'daily_sales_items.csv']
    
    if filename in master_data:
        return 3600  # 1시간
    elif filename in transaction_data:
        return 60    # 1분
    else:
        return 300   # 5분 (기본값)

# Phase 3: 캐시 전략 개선
# Streamlit의 @st.cache_data는 데코레이터 레벨에서만 TTL을 설정할 수 있으므로,
# 파일명에 따라 적절한 TTL을 사용하도록 주석으로 가이드 제공
# 실제 구현은 기존 load_csv 함수를 유지하되, TTL을 300초(5분)로 조정하여 균형 유지

def _load_csv_impl(filename: str, store_id: str, client_mode: str, default_columns: Optional[List[str]] = None):
    """
    캐시된 load_csv 내부 구현 (store_id와 client_mode를 캐시 키에 포함)
    이 함수가 실행되면 캐시 MISS임을 의미
    """
    # 데이터 호출 계측 시작
    start_time = time.perf_counter()
    
    # 캐시 MISS 로그 기록 (이 함수가 실행되었다는 것은 캐시가 MISS였다는 의미)
    _log_cache_miss("load_csv", filename=filename, store_id=store_id, client_mode=client_mode)
    
    # 가드: 온라인에서는 anon으로 read 금지 (DEV에서만 허용)
    if client_mode == "anon" and not _is_dev_mode():
        error_msg = f"❌ 보안 위반: 온라인 환경에서 anon 클라이언트로 데이터 조회 시도 (filename: {filename})"
        logger.error(error_msg)
        st.error(error_msg)
        st.warning("💡 로그인 상태를 확인하세요. 로그아웃 후 다시 로그인해 주세요.")
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        record_data_call(f"load_csv({filename}) [SECURITY_BLOCK]", elapsed_ms, rows=0, source="supabase")
        return pd.DataFrame(columns=default_columns) if default_columns else pd.DataFrame()
    
    # Supabase 조회용 클라이언트 사용 (DEV MODE에서 service_role_key 사용 가능)
    try:
        supabase = get_read_client()
    except Exception as e:
        logger.error(f"Supabase client init failed in load_csv('{filename}'): {e}")
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        record_data_call(f"load_csv({filename}) [ERROR]", elapsed_ms, rows=0, source="supabase")
        return pd.DataFrame(columns=default_columns) if default_columns else pd.DataFrame()

    if not supabase:
        logger.warning(f"Supabase not available, returning empty DataFrame for {filename}")
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        record_data_call(f"load_csv({filename}) [NO_CLIENT]", elapsed_ms, rows=0, source="supabase")
        return pd.DataFrame(columns=default_columns) if default_columns else pd.DataFrame()
    
    if not store_id:
        logger.warning(f"No store_id found, returning empty DataFrame for {filename}")
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        record_data_call(f"load_csv({filename}) [NO_STORE_ID]", elapsed_ms, rows=0, source="supabase")
        return pd.DataFrame(columns=default_columns) if default_columns else pd.DataFrame()
    
    try:
        # CSV 파일명 -> DB 테이블명 매핑
        table_mapping = {
            'sales.csv': 'sales',
            'naver_visitors.csv': 'naver_visitors',
            'menu_master.csv': 'menu_master',
            'ingredient_master.csv': 'ingredients',
            'recipes.csv': 'recipes',
            'daily_sales_items.csv': 'daily_sales_items',
            'inventory.csv': 'inventory',
            'targets.csv': 'targets',
            'abc_history.csv': 'abc_history',
            'daily_close.csv': 'daily_close',
            'actual_settlement.csv': 'actual_settlement',
            # 파일명 없이 테이블명으로 직접 호출 가능
            'sales': 'sales',
            'naver_visitors': 'naver_visitors',
            'menu_master': 'menu_master',
            'ingredient_master': 'ingredients',
            'recipes': 'recipes',
            'daily_sales_items': 'daily_sales_items',
            'inventory': 'inventory',
            'targets': 'targets',
            'abc_history': 'abc_history',
            'daily_close': 'daily_close',
            'actual_settlement': 'actual_settlement',
        }
        
        actual_table = table_mapping.get(filename, filename.replace('.csv', ''))
        
        # 대용량 테이블 필터 기본값 강제 (최근 90일)
        large_tables = ['sales', 'daily_close', 'daily_sales_items', 'naver_visitors']
        use_date_filter = actual_table in large_tables
        
        # store_id로 필터링하여 조회 (RLS가 자동으로 적용됨)
        try:
            query = supabase.table(actual_table).select("*").eq("store_id", store_id)
            
            # 대용량 테이블은 최근 90일 필터 강제 적용
            if use_date_filter:
                from datetime import timedelta
                cutoff_date = (now_kst() - timedelta(days=90)).date()
                query = query.gte("date", cutoff_date.isoformat())
            
            # 디버그: 실제 쿼리 정보 로깅 (온라인 환경 진단용)
            logger.info(f"load_csv({filename}): 테이블={actual_table}, store_id={store_id}, use_date_filter={use_date_filter}")
            if use_date_filter:
                logger.info(f"load_csv({filename}): 날짜 필터 적용 (cutoff_date={cutoff_date.isoformat()})")
            
            # timed_select로 쿼리 실행 및 타이밍 기록
            result = timed_select(
                f"load_csv({filename})",
                lambda: query.execute()
            )
            
            # 결과 로깅
            row_count = len(result.data) if result.data else 0
            logger.info(f"load_csv({filename}): 조회 결과 {row_count}건")
        except Exception as query_error:
            error_msg = str(query_error)
            logger.error(f"Query failed for {actual_table} (store_id: {store_id}): {error_msg}")
            
            # 개발 모드에서만 디버그 정보 표시
            if _is_dev_mode():
                import streamlit as st
                with st.expander(f"⚠️ 데이터 로드 실패: {filename}", expanded=False):
                    st.error(f"**테이블 조회 실패:** {actual_table}")
                    st.caption(f"**Store ID:** {store_id}")
                    st.caption(f"**에러:** {error_msg}")
                    
                    # 에러 타입별 안내
                    if "RLS" in error_msg or "policy" in error_msg.lower() or "permission" in error_msg.lower():
                        st.warning("💡 **RLS 정책 문제 가능성**")
                        st.caption("RLS 정책이 올바르게 설정되어 있는지 확인하세요.")
                    elif "JWT" in error_msg or "token" in error_msg.lower() or "authentication" in error_msg.lower():
                        st.warning("💡 **인증 문제 가능성**")
                        st.caption("로그인 상태를 확인하거나 다시 로그인하세요.")
                    elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                        st.warning("💡 **네트워크 연결 문제 가능성**")
                        st.caption("인터넷 연결을 확인하세요.")
            
            return pd.DataFrame(columns=default_columns) if default_columns else pd.DataFrame()
        
            # 데이터가 0건인 경우 디버그 정보 표시 (온라인 환경에서도 표시)
            if not result.data or len(result.data) == 0:
                # 온라인 환경에서도 진단 정보 표시 (항상 표시)
                import streamlit as st
                with st.expander(f"⚠️ 데이터 없음: {filename} (0건)", expanded=True):
                    st.error(f"**테이블:** {actual_table}")
                    st.write(f"**Store ID:** `{store_id}`")
                    st.write("**실행된 쿼리:**")
                    if use_date_filter:
                        st.code(f"table('{actual_table}').select('*').eq('store_id', '{store_id}').gte('date', '{cutoff_date.isoformat()}')", language="python")
                    else:
                        st.code(f"table('{actual_table}').select('*').eq('store_id', '{store_id}')", language="python")
                    
                    st.write("**가능한 원인:**")
                    st.write("1. 실제로 데이터가 없는 경우")
                    st.write("2. RLS 정책으로 인해 접근 불가")
                    st.write("3. store_id 필터 조건 불일치")
                    st.write("4. 로그인 상태 문제")
                    
                    # 추가 진단: 테이블 존재 여부 확인 (store_id 필터 없이)
                    st.divider()
                    st.write("**추가 진단: 필터 없이 조회:**")
                    try:
                        # 필터 없이 조회 시도
                        test_result = supabase.table(actual_table).select("*").limit(5).execute()
                        
                        if test_result.data:
                            test_count = len(test_result.data)
                            st.warning(f"⚠️ 테이블에는 데이터가 있습니다 ({test_count}건), 하지만 store_id={store_id} 조건으로는 조회되지 않습니다.")
                            
                            # 발견된 store_id 목록
                            store_ids_found = set([row.get('store_id') for row in test_result.data if row.get('store_id')])
                            st.write(f"**발견된 store_id 목록:** {list(store_ids_found)}")
                            
                            if store_id not in store_ids_found:
                                st.error(f"❌ 현재 store_id(`{store_id}`)가 발견된 store_id 목록에 없습니다!")
                                st.info("💡 해결 방법:")
                                st.info("1. 로그아웃 후 다시 로그인")
                                st.info("2. user_profiles 테이블에서 store_id 확인")
                                st.info("3. RLS 정책 확인")
                            
                            st.write("**샘플 데이터 (필터 없이):**")
                            st.json(test_result.data[0])
                        else:
                            st.error("❌ 필터 없이 조회해도 데이터가 없습니다!")
                            st.warning("💡 이것은 RLS 정책이 모든 데이터 접근을 차단하고 있다는 의미입니다.")
                            st.info("**확인 사항:**")
                            st.info("1. Supabase Dashboard → Authentication → Policies")
                            st.info(f"2. `{actual_table}` 테이블의 SELECT 정책 확인")
                            st.info("3. RLS 정책이 현재 사용자(`auth.uid()`)에게 데이터 접근을 허용하는지 확인")
                            st.info("4. 정책 예시:")
                            st.code("""
-- 예시: store_id 기반 RLS 정책
CREATE POLICY "Users can view their store data"
ON ingredients FOR SELECT
USING (
  store_id IN (
    SELECT store_id FROM user_profiles 
    WHERE id = auth.uid()
  )
);
                            """, language="sql")
                    except Exception as test_error:
                        error_msg = str(test_error)
                        st.error(f"❌ 테이블 접근 테스트 실패: {type(test_error).__name__}: {error_msg}")
                        st.code(str(test_error), language="text")
                        
                        # RLS 관련 에러 확인
                        if "permission" in error_msg.lower() or "policy" in error_msg.lower() or "RLS" in error_msg:
                            st.error("🚨 RLS 정책 문제로 보입니다!")
                            st.info("**해결 방법:**")
                            st.info(f"1. Supabase Dashboard에서 `{actual_table}` 테이블의 RLS 정책 확인")
                            st.info("2. SELECT 정책이 필요합니다")
                            st.info("3. 정책에서 `auth.uid()`와 `store_id`를 올바르게 연결해야 합니다")
            
            # 데이터가 0건이어도 빈 DataFrame 반환
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            record_data_call(f"load_csv({filename})", elapsed_ms, rows=0, source="supabase")
            return pd.DataFrame(columns=default_columns) if default_columns else pd.DataFrame()
        
        if result.data:
            df = pd.DataFrame(result.data)
            
            # 컬럼명 변환 (DB -> CSV 호환)
            if actual_table == 'sales':
                if 'date' in df.columns:
                    df['날짜'] = pd.to_datetime(df['date'])
                if 'card_sales' in df.columns:
                    df['카드매출'] = df['card_sales']
                if 'cash_sales' in df.columns:
                    df['현금매출'] = df['cash_sales']
                if 'total_sales' in df.columns:
                    df['총매출'] = df['total_sales']
                # store_id로 매장명 조회
                store_result = supabase.table("stores").select("name").eq("id", store_id).execute()
                if store_result.data:
                    df['매장'] = store_result.data[0]['name']
            
            elif actual_table == 'naver_visitors':
                if 'date' in df.columns:
                    df['날짜'] = pd.to_datetime(df['date'])
                if 'visitors' in df.columns:
                    df['방문자수'] = df['visitors']
            
            elif actual_table == 'menu_master':
                if 'name' in df.columns:
                    df['메뉴명'] = df['name']
                if 'price' in df.columns:
                    df['판매가'] = df['price']
            
            elif actual_table == 'ingredients':
                if 'name' in df.columns:
                    df['재료명'] = df['name']
                if 'unit' in df.columns:
                    df['단위'] = df['unit']
                if 'unit_cost' in df.columns:
                    df['단가'] = df['unit_cost']
                if 'order_unit' in df.columns:
                    df['발주단위'] = df['order_unit']
                if 'conversion_rate' in df.columns:
                    df['변환비율'] = df['conversion_rate']
            
            elif actual_table == 'recipes':
                # menu_id와 ingredient_id를 이름으로 변환
                if 'menu_id' in df.columns:
                    menu_ids = df['menu_id'].dropna().unique().tolist()
                    if menu_ids:
                        menu_result = supabase.table("menu_master").select("id,name").in_("id", menu_ids).execute()
                        menu_map = {m['id']: m['name'] for m in menu_result.data}
                        df['메뉴명'] = df['menu_id'].map(menu_map)
                
                if 'ingredient_id' in df.columns:
                    ing_ids = df['ingredient_id'].dropna().unique().tolist()
                    if ing_ids:
                        ing_result = supabase.table("ingredients").select("id,name").in_("id", ing_ids).execute()
                        ing_map = {i['id']: i['name'] for i in ing_result.data}
                        df['재료명'] = df['ingredient_id'].map(ing_map)
                
                if 'qty' in df.columns:
                    df['사용량'] = df['qty']
            
            elif actual_table == 'daily_sales_items':
                if 'date' in df.columns:
                    df['날짜'] = pd.to_datetime(df['date'])
                
                if 'menu_id' in df.columns:
                    menu_ids = df['menu_id'].dropna().unique().tolist()
                    if menu_ids:
                        menu_result = supabase.table("menu_master").select("id,name").in_("id", menu_ids).execute()
                        menu_map = {m['id']: m['name'] for m in menu_result.data}
                        df['메뉴명'] = df['menu_id'].map(menu_map)
                
                if 'qty' in df.columns:
                    df['판매수량'] = df['qty']
            
            elif actual_table == 'inventory':
                if 'ingredient_id' in df.columns:
                    ing_ids = df['ingredient_id'].dropna().unique().tolist()
                    if ing_ids:
                        ing_result = supabase.table("ingredients").select("id,name").in_("id", ing_ids).execute()
                        ing_map = {i['id']: i['name'] for i in ing_result.data}
                        df['재료명'] = df['ingredient_id'].map(ing_map)
                
                if 'on_hand' in df.columns:
                    df['현재고'] = df['on_hand']
                if 'safety_stock' in df.columns:
                    df['안전재고'] = df['safety_stock']
            
            elif actual_table == 'targets':
                if 'year' in df.columns:
                    df['연도'] = df['year']
                if 'month' in df.columns:
                    df['월'] = df['month']
                if 'target_sales' in df.columns:
                    df['목표매출'] = df['target_sales']
                if 'target_cost_rate' in df.columns:
                    df['목표원가율'] = df['target_cost_rate']
                if 'target_labor_rate' in df.columns:
                    df['목표인건비율'] = df['target_labor_rate']
                if 'target_rent_rate' in df.columns:
                    df['목표임대료율'] = df['target_rent_rate']
                if 'target_other_rate' in df.columns:
                    df['목표기타비용율'] = df['target_other_rate']
                if 'target_profit_rate' in df.columns:
                    df['목표순이익률'] = df['target_profit_rate']
            
            elif actual_table == 'actual_settlement':
                # 실제 정산 데이터 (월별 실적)
                if 'year' in df.columns:
                    df['연도'] = df['year']
                if 'month' in df.columns:
                    df['월'] = df['month']
                if 'actual_sales' in df.columns:
                    df['실제매출'] = df['actual_sales']
                if 'actual_cost' in df.columns:
                    df['실제비용'] = df['actual_cost']
                if 'actual_profit' in df.columns:
                    df['실제이익'] = df['actual_profit']
                if 'profit_margin' in df.columns:
                    df['실제이익률'] = df['profit_margin']
            
            elif actual_table == 'abc_history':
                # 컬럼명이 이미 일치하는 경우도 있음
                if 'menu_name' in df.columns:
                    df['메뉴명'] = df['menu_name']
                if 'sales_qty' in df.columns:
                    df['판매량'] = df['sales_qty']
                if 'sales_amount' in df.columns:
                    df['매출'] = df['sales_amount']
                if 'contribution_margin' in df.columns:
                    df['공헌이익'] = df['contribution_margin']
                if 'qty_ratio' in df.columns:
                    df['판매량비중'] = df['qty_ratio']
                if 'sales_ratio' in df.columns:
                    df['매출비중'] = df['sales_ratio']
                if 'margin_ratio' in df.columns:
                    df['공헌이익비중'] = df['margin_ratio']
                if 'abc_grade' in df.columns:
                    df['ABC등급'] = df['abc_grade']
                if 'year' in df.columns:
                    df['연도'] = df['year']
                if 'month' in df.columns:
                    df['월'] = df['month']
            
            elif actual_table == 'suppliers':
                if 'name' in df.columns:
                    df['공급업체명'] = df['name']
                if 'phone' in df.columns:
                    df['전화번호'] = df['phone']
                if 'email' in df.columns:
                    df['이메일'] = df['email']
                if 'delivery_days' in df.columns:
                    df['배송일'] = df['delivery_days']
                if 'min_order_amount' in df.columns:
                    df['최소주문금액'] = df['min_order_amount']
                if 'delivery_fee' in df.columns:
                    df['배송비'] = df['delivery_fee']
                if 'notes' in df.columns:
                    df['비고'] = df['notes']
            
            elif actual_table == 'ingredient_suppliers':
                # 재료 ID -> 재료명 변환
                if 'ingredient_id' in df.columns:
                    ing_ids = df['ingredient_id'].dropna().unique().tolist()
                    if ing_ids:
                        ing_result = supabase.table("ingredients").select("id,name").in_("id", ing_ids).execute()
                        ing_map = {i['id']: i['name'] for i in ing_result.data}
                        df['재료명'] = df['ingredient_id'].map(ing_map)
                
                # 공급업체 ID -> 공급업체명 변환
                if 'supplier_id' in df.columns:
                    sup_ids = df['supplier_id'].dropna().unique().tolist()
                    if sup_ids:
                        sup_result = supabase.table("suppliers").select("id,name").in_("id", sup_ids).execute()
                        sup_map = {s['id']: s['name'] for s in sup_result.data}
                        df['공급업체명'] = df['supplier_id'].map(sup_map)
                
                if 'unit_price' in df.columns:
                    df['단가'] = df['unit_price']
                if 'is_default' in df.columns:
                    df['기본공급업체'] = df['is_default']
            
            elif actual_table == 'orders':
                # id 컬럼 유지
                if 'id' not in df.columns:
                    df['id'] = df.index
                
                # 재료 ID -> 재료명 변환
                if 'ingredient_id' in df.columns:
                    ing_ids = df['ingredient_id'].dropna().unique().tolist()
                    if ing_ids:
                        ing_result = supabase.table("ingredients").select("id,name").in_("id", ing_ids).execute()
                        ing_map = {i['id']: i['name'] for i in ing_result.data}
                        df['재료명'] = df['ingredient_id'].map(ing_map)
                
                # 공급업체 ID -> 공급업체명 변환
                if 'supplier_id' in df.columns:
                    sup_ids = df['supplier_id'].dropna().unique().tolist()
                    if sup_ids:
                        sup_result = supabase.table("suppliers").select("id,name").in_("id", sup_ids).execute()
                        sup_map = {s['id']: s['name'] for s in sup_result.data}
                        df['공급업체명'] = df['supplier_id'].map(sup_map)
                
                if 'order_date' in df.columns:
                    df['발주일'] = pd.to_datetime(df['order_date'])
                if 'quantity' in df.columns:
                    df['수량'] = df['quantity']
                if 'unit_price' in df.columns:
                    df['단가'] = df['unit_price']
                if 'total_amount' in df.columns:
                    df['총금액'] = df['total_amount']
                if 'status' in df.columns:
                    df['상태'] = df['status']
                if 'expected_delivery_date' in df.columns:
                    df['입고예정일'] = pd.to_datetime(df['expected_delivery_date'])
                if 'actual_delivery_date' in df.columns:
                    df['입고일'] = pd.to_datetime(df['actual_delivery_date'])
                if 'notes' in df.columns:
                    df['비고'] = df['notes']
            
            return df
        else:
            return pd.DataFrame(columns=default_columns) if default_columns else pd.DataFrame()
    
    except Exception as e:
        logger.error(f"Failed to load {filename}: {e}")
        return pd.DataFrame(columns=default_columns) if default_columns else pd.DataFrame()


# 캐시 적용 (store_id와 client_mode를 캐시 키에 포함)
# 주의: 데코레이터 레벨에서 is_dev_mode() 호출 시 모듈 로드 시점에 session_state가 없어 캐시가 재생성됨
# 따라서 TTL을 고정값(300초)으로 설정하여 캐시 안정성 확보
@st.cache_data(ttl=300)  # 5분 캐시 (고정값으로 설정하여 캐시 안정성 확보)
def load_csv(filename: str, default_columns: Optional[List[str]] = None, store_id: str = None, client_mode: str = None):
    """
    테이블에서 데이터 로드 (CSV 호환 인터페이스)
    캐시 키에 store_id와 client_mode를 포함하여 매장별/클라이언트별로 캐시 분리
    
    Args:
        filename: CSV 파일명 (예: "sales.csv") -> 테이블명으로 매핑
        default_columns: 기본 컬럼 리스트
        store_id: store_id (None이면 get_current_store_id() 사용)
        client_mode: client_mode (None이면 get_read_client_mode() 사용, 캐시 키에 포함)
    
    Returns:
        pandas.DataFrame
    """
    # 세션 캐시 키 매핑 (마스터 데이터만 세션 캐시 사용)
    session_cache_keys = {
        'menu_master.csv': 'ss_menu_master_df',
        'ingredient_master.csv': 'ss_ingredient_master_df',
        'inventory.csv': 'ss_inventory_df',
        'recipes.csv': 'ss_recipes_df',
        'targets.csv': 'ss_targets_df',
        # 파일명 없이 테이블명으로 직접 호출 가능
        'menu_master': 'ss_menu_master_df',
        'ingredient_master': 'ss_ingredient_master_df',
        'inventory': 'ss_inventory_df',
        'recipes': 'ss_recipes_df',
        'targets': 'ss_targets_df',
    }
    
    # 세션 캐시 키 확인
    session_key = session_cache_keys.get(filename)
    if session_key and session_key in st.session_state:
        # 세션 캐시에 있으면 즉시 반환
        if _is_dev_mode():
            logger.debug(f"load_csv: Session cache HIT for {filename}")
        df = st.session_state[session_key]
        # 캐시 히트도 계측 (매우 빠름)
        record_data_call(f"load_csv({filename})", 0.1, rows=len(df), source="session_cache")
        return df
    
    # store_id와 client_mode를 캐시 키에 명시적으로 포함하기 위해 가져오기
    if store_id is None:
        store_id = get_current_store_id()
    if client_mode is None:
        try:
            client_mode = get_read_client_mode()
        except Exception:
            client_mode = "unknown"
    
    if not store_id:
        logger.warning(f"No store_id found, returning empty DataFrame for {filename}")
        return pd.DataFrame(columns=default_columns) if default_columns else pd.DataFrame()
    
    # @st.cache_data 캐시 또는 DB 조회
    df = _load_csv_impl(filename, store_id, client_mode, default_columns)
    
    # 세션 캐시에 저장 (마스터 데이터만)
    if session_key:
        st.session_state[session_key] = df
        if _is_dev_mode():
            logger.debug(f"load_csv: Session cache SET for {filename} ({len(df)} rows)")
    
    return df


@st.cache_data(ttl=300)  # 5분 캐시 (마스터 데이터, 고정값으로 설정하여 캐시 안정성 확보)
def load_key_menus() -> List[str]:
    """핵심 메뉴 목록 로드 (is_core=True인 메뉴들)"""
    supabase = get_supabase_client()
    if not supabase:
        return []
    
    store_id = get_current_store_id()
    if not store_id:
        return []
    
    try:
        result = supabase.table("menu_master").select("name").eq("store_id", store_id).eq("is_core", True).execute()
        if result.data:
            return [m['name'] for m in result.data]
        return []
    except Exception as e:
        logger.error(f"Failed to load key menus: {e}")
        return []


# ============================================
# Save Functions
# ============================================

def save_sales(date, store_name, card_sales, cash_sales, total_sales=None):
    """매출 데이터 저장"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    if total_sales is None:
        total_sales = card_sales + cash_sales
    
    try:
        date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
        
        result = supabase.table("sales").upsert({
            "store_id": store_id,
            "date": date_str,
            "card_sales": float(card_sales),
            "cash_sales": float(cash_sales),
            "total_sales": float(total_sales)
        }, on_conflict="store_id,date").execute()
        
        logger.info(f"Sales saved: {date_str}, {total_sales}")
        
        # 소프트 무효화 (token bump + 부분 clear)
        soft_invalidate(
            reason=f"save_sales: {date_str}",
            targets=["sales"]
        )
        
        # S5: 매출 저장 직후 스냅샷 (dev_mode에서만)
        try:
            from src.auth import is_dev_mode
            if is_dev_mode():
                from src.utils.boot_perf import snapshot_current_metrics
                snapshot_current_metrics("S5: 매출 저장 직후 rerun")
        except Exception:
            pass
        
        return True
    except Exception as e:
        logger.error(f"Failed to save sales: {e}")
        raise


def save_visitor(date, visitors):
    """방문자 데이터 저장"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
        
        result = supabase.table("naver_visitors").upsert({
            "store_id": store_id,
            "date": date_str,
            "visitors": int(visitors)
        }, on_conflict="store_id,date").execute()
        
        logger.info(f"Visitor saved: {date_str}, {visitors}")
        
        # 소프트 무효화 (token bump + 부분 clear)
        soft_invalidate(
            reason=f"save_visitor: {date_str}",
            targets=["visitors"]
        )
        
        return True
    except Exception as e:
        logger.error(f"Failed to save visitor: {e}")
        raise


def save_menu(menu_name, price):
    """
    메뉴 저장
    
    Phase 2: 동시성 보호 - Optimistic Locking 적용
    """
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 저장할 수 없습니다."
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 중복 체크 (헬퍼 함수 사용)
        if _check_duplicate(supabase, "menu_master", "name", menu_name, store_id):
            return False, f"'{menu_name}' 메뉴는 이미 등록되어 있습니다."
        
        result = supabase.table("menu_master").insert({
            "store_id": store_id,
            "name": menu_name,
            "price": float(price),
            "is_core": False
        }).execute()
        
        logger.info(f"Menu saved: {menu_name}, {price}")
        
        # 소프트 무효화 (token bump + 부분 clear)
        soft_invalidate(
            reason=f"save_menu: {menu_name}",
            targets=["menus", "recipes"],
            session_keys=['ss_menu_master_df', 'ss_recipes_df']
        )
        
        return True, "저장 성공"
    except Exception as e:
        logger.error(f"Failed to save menu: {e}")
        raise


def update_menu(old_menu_name, new_menu_name, new_price, category=None, expected_updated_at=None):
    """
    메뉴 수정
    
    Phase 2: 동시성 보호 - Optimistic Locking
    - expected_updated_at: 수정 전의 updated_at 값 (충돌 감지용)
    """
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 수정할 수 없습니다."
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 기존 메뉴 찾기 (updated_at 포함)
        existing = supabase.table("menu_master").select("id,updated_at").eq("store_id", store_id).eq("name", old_menu_name).execute()
        if not existing.data:
            return False, f"'{old_menu_name}' 메뉴를 찾을 수 없습니다."
        
        menu_id = existing.data[0]['id']
        current_updated_at = existing.data[0].get('updated_at')
        
        # Phase 2: 동시성 보호 - Optimistic Locking
        if expected_updated_at and current_updated_at != expected_updated_at:
            return False, f"다른 사용자가 '{old_menu_name}' 메뉴를 수정했습니다. 페이지를 새로고침한 후 다시 시도해주세요."
        
        # 새 메뉴명이 다른 경우 중복 체크 (헬퍼 함수 사용)
        if new_menu_name != old_menu_name:
            if _check_duplicate(supabase, "menu_master", "name", new_menu_name, store_id):
                return False, f"'{new_menu_name}' 메뉴명은 이미 사용 중입니다."
        
        # 업데이트 데이터 준비
        update_data = {
            "name": new_menu_name,
            "price": float(new_price)
        }
        if category is not None:
            update_data["category"] = category
        
        # 업데이트
        supabase.table("menu_master").update(update_data).eq("id", menu_id).execute()
        
        logger.info(f"Menu updated: {old_menu_name} -> {new_menu_name}")
        
        # 캐시 클리어 (데이터 변경 후)
        try:
            load_csv.clear()
        except Exception:
            pass
        
        return True, "수정 성공"
    except Exception as e:
        logger.error(f"Failed to update menu: {e}")
        raise


def update_menu_category(menu_name, category):
    """메뉴 카테고리 업데이트"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 수정할 수 없습니다."
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 기존 메뉴 찾기
        existing = supabase.table("menu_master").select("id").eq("store_id", store_id).eq("name", menu_name).execute()
        if not existing.data:
            return False, f"'{menu_name}' 메뉴를 찾을 수 없습니다."
        
        menu_id = existing.data[0]['id']
        
        # 카테고리 업데이트
        supabase.table("menu_master").update({
            "category": category
        }).eq("id", menu_id).execute()
        
        logger.info(f"Menu category updated: {menu_name} -> {category}")
        
        # 소프트 무효화 (token bump + 부분 clear)
        soft_invalidate(
            reason=f"update_menu_category: {menu_name}",
            targets=["menus"],
            session_keys=['ss_menu_master_df']
        )
        
        return True, "카테고리 수정 성공"
    except Exception as e:
        logger.error(f"Failed to update menu category: {e}")
        raise


def update_menu_cooking_method(menu_name, cooking_method):
    """메뉴 조리방법 업데이트"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 수정할 수 없습니다."
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 기존 메뉴 찾기
        existing = supabase.table("menu_master").select("id").eq("store_id", store_id).eq("name", menu_name).execute()
        if not existing.data:
            return False, f"'{menu_name}' 메뉴를 찾을 수 없습니다."
        
        menu_id = existing.data[0]['id']
        
        # 조리방법 업데이트 (cooking_method 컬럼이 있다면)
        try:
            supabase.table("menu_master").update({
                "cooking_method": cooking_method.strip()
            }).eq("id", menu_id).execute()
            logger.info(f"Menu cooking method updated: {menu_name}")
            return True, "조리방법 저장 성공"
        except Exception as e:
            # 컬럼이 없으면 경고만 하고 성공으로 처리 (나중에 스키마 업데이트 필요)
            logger.warning(f"Cooking method column may not exist: {e}")
            return True, "조리방법 저장 성공 (스키마 업데이트 필요할 수 있음)"
    except Exception as e:
        logger.error(f"Failed to update menu cooking method: {e}")
        raise


def delete_menu(menu_name, check_references=True):
    """메뉴 삭제"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 삭제할 수 없습니다.", None
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 메뉴 찾기
        menu_result = supabase.table("menu_master").select("id").eq("store_id", store_id).eq("name", menu_name).execute()
        if not menu_result.data:
            return False, f"'{menu_name}' 메뉴를 찾을 수 없습니다.", None
        
        menu_id = menu_result.data[0]['id']
        
        references = {}
        if check_references:
            # 레시피 참조 확인
            recipe_check = supabase.table("recipes").select("id").eq("menu_id", menu_id).execute()
            if recipe_check.data:
                references['레시피'] = len(recipe_check.data)
            
            # 판매 내역 참조 확인
            sales_check = supabase.table("daily_sales_items").select("id").eq("menu_id", menu_id).execute()
            if sales_check.data:
                references['판매내역'] = len(sales_check.data)
        
        if references:
            ref_info = ", ".join([f"{k}: {v}개" for k, v in references.items()])
            return False, f"'{menu_name}' 메뉴는 다음 데이터에서 사용 중입니다: {ref_info}", references
        
        # 삭제
        supabase.table("menu_master").delete().eq("id", menu_id).execute()
        logger.info(f"Menu deleted: {menu_name}")
        
        # 소프트 무효화 (token bump + 부분 clear)
        soft_invalidate(
            reason=f"delete_menu: {menu_name}",
            targets=["menus", "recipes"],
            session_keys=['ss_menu_master_df', 'ss_recipes_df']
        )
        
        return True, "삭제 성공", None
    except Exception as e:
        logger.error(f"Failed to delete menu: {e}")
        raise


def save_ingredient(ingredient_name, unit, unit_price, order_unit=None, conversion_rate=1.0):
    """재료 저장"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 저장할 수 없습니다."
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 중복 체크 (헬퍼 함수 사용)
        if _check_duplicate(supabase, "ingredients", "name", ingredient_name, store_id):
            return False, f"'{ingredient_name}' 재료는 이미 등록되어 있습니다."
        
        # 발주 단위가 없으면 기본 단위와 동일하게 설정
        if not order_unit:
            order_unit = unit
        
        insert_data = {
            "store_id": store_id,
            "name": ingredient_name,
            "unit": unit,
            "unit_cost": float(unit_price),
            "order_unit": order_unit,
            "conversion_rate": float(conversion_rate)
        }
        
        result = supabase.table("ingredients").insert(insert_data).execute()
        
        logger.info(f"Ingredient saved: {ingredient_name}")
        
        # 소프트 무효화 (token bump + 부분 clear)
        soft_invalidate(
            reason=f"save_ingredient: {ingredient_name}",
            targets=["ingredients", "recipes", "cost"],
            session_keys=['ss_ingredient_master_df', 'ss_recipes_df', 'ss_inventory_df']
        )
        
        return True, "저장 성공"
    except Exception as e:
        logger.error(f"Failed to save ingredient: {e}")
        raise


def update_ingredient(old_ingredient_name, new_ingredient_name, new_unit, new_unit_price):
    """재료 수정"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 수정할 수 없습니다."
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 기존 재료 찾기
        existing = supabase.table("ingredients").select("id").eq("store_id", store_id).eq("name", old_ingredient_name).execute()
        if not existing.data:
            return False, f"'{old_ingredient_name}' 재료를 찾을 수 없습니다."
        
        ing_id = existing.data[0]['id']
        
        # 새 재료명이 다른 경우 중복 체크 (헬퍼 함수 사용)
        if new_ingredient_name != old_ingredient_name:
            if _check_duplicate(supabase, "ingredients", "name", new_ingredient_name, store_id):
                return False, f"'{new_ingredient_name}' 재료명은 이미 사용 중입니다."
        
        # 업데이트
        supabase.table("ingredients").update({
            "name": new_ingredient_name,
            "unit": new_unit,
            "unit_cost": float(new_unit_price)
        }).eq("id", ing_id).execute()
        
        logger.info(f"Ingredient updated: {old_ingredient_name} -> {new_ingredient_name}")
        
        # 소프트 무효화 (token bump + 부분 clear)
        soft_invalidate(
            reason=f"update_ingredient: {old_ingredient_name}",
            targets=["ingredients", "recipes", "cost"],
            session_keys=['ss_ingredient_master_df', 'ss_recipes_df', 'ss_inventory_df']
        )
        
        return True, "수정 성공"
    except Exception as e:
        logger.error(f"Failed to update ingredient: {e}")
        raise


def delete_ingredient(ingredient_name, check_references=True):
    """재료 삭제"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 삭제할 수 없습니다.", None
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 재료 찾기
        ing_result = supabase.table("ingredients").select("id").eq("store_id", store_id).eq("name", ingredient_name).execute()
        if not ing_result.data:
            return False, f"'{ingredient_name}' 재료를 찾을 수 없습니다.", None
        
        ing_id = ing_result.data[0]['id']
        
        references = {}
        if check_references:
            # 레시피 참조 확인
            recipe_check = supabase.table("recipes").select("id").eq("ingredient_id", ing_id).execute()
            if recipe_check.data:
                references['레시피'] = len(recipe_check.data)
            
            # 재고 정보 참조 확인
            inv_check = supabase.table("inventory").select("id").eq("ingredient_id", ing_id).execute()
            if inv_check.data:
                references['재고정보'] = 1
        
        if references:
            ref_info = ", ".join([f"{k}: {v}개" for k, v in references.items()])
            return False, f"'{ingredient_name}' 재료는 다음 데이터에서 사용 중입니다: {ref_info}", references
        
        # 삭제
        supabase.table("ingredients").delete().eq("id", ing_id).execute()
        logger.info(f"Ingredient deleted: {ingredient_name}")
        
        # 소프트 무효화 (token bump + 부분 clear)
        soft_invalidate(
            reason=f"delete_ingredient: {ingredient_name}",
            targets=["ingredients", "recipes", "cost"],
            session_keys=['ss_ingredient_master_df', 'ss_recipes_df', 'ss_inventory_df']
        )
        
        return True, "삭제 성공", None
    except Exception as e:
        logger.error(f"Failed to delete ingredient: {e}")
        raise


def save_recipe(menu_name, ingredient_name, quantity):
    """레시피 저장"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 메뉴 ID 찾기
        menu_result = supabase.table("menu_master").select("id").eq("store_id", store_id).eq("name", menu_name).execute()
        if not menu_result.data:
            raise Exception(f"메뉴 '{menu_name}'를 찾을 수 없습니다.")
        menu_id = menu_result.data[0]['id']
        
        # 재료 ID 찾기
        ing_result = supabase.table("ingredients").select("id").eq("store_id", store_id).eq("name", ingredient_name).execute()
        if not ing_result.data:
            raise Exception(f"재료 '{ingredient_name}'를 찾을 수 없습니다.")
        ingredient_id = ing_result.data[0]['id']
        
        # 레시피 저장
        result = supabase.table("recipes").upsert({
            "store_id": store_id,
            "menu_id": menu_id,
            "ingredient_id": ingredient_id,
            "qty": float(quantity)
        }, on_conflict="store_id,menu_id,ingredient_id").execute()
        
        logger.info(f"Recipe saved: {menu_name} - {ingredient_name}")
        
        # 소프트 무효화 (token bump + 부분 clear)
        soft_invalidate(
            reason=f"save_recipe: {menu_name}-{ingredient_name}",
            targets=["recipes", "cost"],
            session_keys=['ss_recipes_df']
        )
        
        return True
    except Exception as e:
        logger.error(f"Failed to save recipe: {e}")
        raise


def delete_recipe(menu_name, ingredient_name):
    """레시피 삭제"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 삭제할 수 없습니다."
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 메뉴 ID 찾기
        menu_result = supabase.table("menu_master").select("id").eq("store_id", store_id).eq("name", menu_name).execute()
        if not menu_result.data:
            return False, f"'{menu_name}' 메뉴를 찾을 수 없습니다."
        menu_id = menu_result.data[0]['id']
        
        # 재료 ID 찾기
        ing_result = supabase.table("ingredients").select("id").eq("store_id", store_id).eq("name", ingredient_name).execute()
        if not ing_result.data:
            return False, f"'{ingredient_name}' 재료를 찾을 수 없습니다."
        ingredient_id = ing_result.data[0]['id']
        
        # 레시피 삭제
        supabase.table("recipes").delete().eq("store_id", store_id).eq("menu_id", menu_id).eq("ingredient_id", ingredient_id).execute()
        
        logger.info(f"Recipe deleted: {menu_name} - {ingredient_name}")
        
        # 소프트 무효화 (token bump + 부분 clear)
        soft_invalidate(
            reason=f"delete_recipe: {menu_name}-{ingredient_name}",
            targets=["recipes", "cost"],
            session_keys=['ss_recipes_df']
        )
        
        return True, "삭제 성공"
    except Exception as e:
        logger.error(f"Failed to delete recipe: {e}")
        raise


def save_daily_sales_item(date, menu_name, quantity):
    """일일 판매 아이템 저장 (같은 날짜/메뉴가 있으면 수량 합산)"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
        
        # 메뉴 ID 찾기
        menu_result = supabase.table("menu_master").select("id").eq("store_id", store_id).eq("name", menu_name).execute()
        if not menu_result.data:
            raise Exception(f"메뉴 '{menu_name}'를 찾을 수 없습니다.")
        menu_id = menu_result.data[0]['id']
        
        # 기존 데이터 확인
        existing = supabase.table("daily_sales_items").select("qty").eq("store_id", store_id).eq("date", date_str).eq("menu_id", menu_id).execute()
        
        if existing.data:
            # 기존 수량에 추가
            new_qty = existing.data[0]['qty'] + quantity
            supabase.table("daily_sales_items").update({"qty": new_qty}).eq("store_id", store_id).eq("date", date_str).eq("menu_id", menu_id).execute()
        else:
            # 새로 추가
            supabase.table("daily_sales_items").insert({
                "store_id": store_id,
                "date": date_str,
                "menu_id": menu_id,
                "qty": int(quantity)
            }).execute()
        
        logger.info(f"Daily sales item saved: {date_str}, {menu_name}, {quantity}")
        return True
    except Exception as e:
        logger.error(f"Failed to save daily sales item: {e}")
        raise


def save_inventory(ingredient_name, current_stock, safety_stock):
    """재고 정보 저장"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 재료 ID 찾기
        ing_result = supabase.table("ingredients").select("id").eq("store_id", store_id).eq("name", ingredient_name).execute()
        if not ing_result.data:
            raise Exception(f"재료 '{ingredient_name}'를 찾을 수 없습니다.")
        ingredient_id = ing_result.data[0]['id']
        
        # 재고 정보 저장/업데이트
        supabase.table("inventory").upsert({
            "store_id": store_id,
            "ingredient_id": ingredient_id,
            "on_hand": float(current_stock),
            "safety_stock": float(safety_stock)
        }, on_conflict="store_id,ingredient_id").execute()
        
        logger.info(f"Inventory saved: {ingredient_name}")
        
        # 소프트 무효화 (token bump + 부분 clear)
        soft_invalidate(
            reason=f"save_inventory: {ingredient_name}",
            targets=["inventory"],
            session_keys=['ss_inventory_df']
        )
        
        return True
    except Exception as e:
        logger.error(f"Failed to save inventory: {e}")
        raise


def save_targets(year, month, target_sales, target_cost_rate, target_labor_rate, 
                 target_rent_rate, target_other_rate, target_profit_rate):
    """목표 매출/비용 구조 저장"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        supabase.table("targets").upsert({
            "store_id": store_id,
            "year": int(year),
            "month": int(month),
            "target_sales": float(target_sales),
            "target_cost_rate": float(target_cost_rate),
            "target_labor_rate": float(target_labor_rate),
            "target_rent_rate": float(target_rent_rate),
            "target_other_rate": float(target_other_rate),
            "target_profit_rate": float(target_profit_rate)
        }, on_conflict="store_id,year,month").execute()
        
        logger.info(f"Targets saved: {year}-{month}")
        return True
    except Exception as e:
        logger.error(f"Failed to save targets: {e}")
        raise


def save_actual_settlement(year, month, actual_sales, actual_cost, actual_profit, profit_margin):
    """월별 실제 정산 데이터 저장"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        supabase.table("actual_settlement").upsert(
            {
                "store_id": store_id,
                "year": int(year),
                "month": int(month),
                "actual_sales": float(actual_sales),
                "actual_cost": float(actual_cost),
                "actual_profit": float(actual_profit),
                "profit_margin": float(profit_margin),
            },
            on_conflict="store_id,year,month",
        ).execute()
        logger.info(f"Actual settlement saved: {year}-{month}")
        return True
    except Exception as e:
        logger.error(f"Failed to save actual settlement: {e}")
        raise


def save_abc_history(year, month, abc_df):
    """
    ABC 분석 히스토리 저장
    
    Phase 2: 트랜잭션 처리 개선
    - 삭제 후 삽입 작업의 원자성 보장
    - 실패 시 롤백 시도
    """
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    # Phase 2: 트랜잭션 처리 - 기존 데이터 백업
    old_data_backup = None
    try:
        # 기존 데이터 백업 (롤백용)
        old_result = supabase.table("abc_history").select("*").eq("store_id", store_id).eq("year", year).eq("month", month).execute()
        old_data_backup = old_result.data if old_result.data else []
        
        # 기존 데이터 삭제 (해당 연도/월)
        supabase.table("abc_history").delete().eq("store_id", store_id).eq("year", year).eq("month", month).execute()
        
        # 새 데이터 추가
        records = []
        for _, row in abc_df.iterrows():
            records.append({
                "store_id": store_id,
                "year": int(year),
                "month": int(month),
                "menu_name": str(row.get('메뉴명', '')),
                "sales_qty": int(row.get('판매량', 0)),
                "sales_amount": float(row.get('매출', 0)),
                "contribution_margin": float(row.get('공헌이익', 0)),
                "qty_ratio": float(row.get('판매량비중', 0)),
                "sales_ratio": float(row.get('매출비중', 0)),
                "margin_ratio": float(row.get('공헌이익비중', 0)),
                "abc_grade": str(row.get('ABC등급', ''))
            })
        
        if records:
            supabase.table("abc_history").insert(records).execute()
        
        logger.info(f"ABC history saved: {year}-{month}")
        return True
    except Exception as e:
        logger.error(f"Failed to save abc history: {e}")
        # Phase 2: 트랜잭션 처리 - 실패 시 롤백 시도
        if old_data_backup:
            try:
                logger.warning(f"Rolling back ABC history for {year}-{month}")
                # 기존 데이터 복원 시도
                if old_data_backup:
                    supabase.table("abc_history").insert(old_data_backup).execute()
                logger.info(f"ABC history rollback successful for {year}-{month}")
            except Exception as rollback_error:
                logger.error(f"Failed to rollback ABC history: {rollback_error}")
        raise


def save_key_menus(menu_list):
    """핵심 메뉴 저장"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 먼저 모든 메뉴의 is_core를 False로
        supabase.table("menu_master").update({"is_core": False}).eq("store_id", store_id).execute()
        
        # 선택된 메뉴들의 is_core를 True로
        if menu_list:
            for menu_name in menu_list:
                supabase.table("menu_master").update({"is_core": True}).eq("store_id", store_id).eq("name", menu_name).execute()
        
        logger.info(f"Key menus saved: {len(menu_list)} menus")
        return True
    except Exception as e:
        logger.error(f"Failed to save key menus: {e}")
        raise


def save_daily_close(date, store_name, card_sales, cash_sales, total_sales, 
                     visitors, sales_items, issues, memo):
    """
    일일 마감 데이터 통합 저장 (트랜잭션 처리)
    
    Phase 3: SQL 함수 기반 트랜잭션 처리
    - 여러 테이블 저장 작업의 원자성 보장
    - 실패 시 자동 롤백
    """
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
    
    try:
        # sales_items를 JSONB 형식으로 변환
        sales_items_json = None
        if sales_items:
            # sales_items가 [(menu_name, qty), ...] 형식인 경우 JSONB 배열로 변환
            sales_items_array = [
                {"menu_name": menu_name, "quantity": int(qty)}
                for menu_name, qty in sales_items
            ]
            sales_items_json = json.dumps(sales_items_array, ensure_ascii=False)
        
        # 트랜잭션 함수 호출 (원자적 저장)
        supabase.rpc('save_daily_close_transaction', {
            'p_date': date_str,
            'p_store_id': str(store_id),
            'p_card_sales': float(card_sales),
            'p_cash_sales': float(cash_sales),
            'p_total_sales': float(total_sales),
            'p_visitors': int(visitors),
            'p_out_of_stock': bool(issues.get('품절', False)),
            'p_complaint': bool(issues.get('컴플레인', False)),
            'p_group_customer': bool(issues.get('단체손님', False)),
            'p_staff_issue': bool(issues.get('직원이슈', False)),
            'p_memo': str(memo) if memo else None,
            'p_sales_items': sales_items_json
        }).execute()
        
        logger.info(f"Daily close saved (transactional): {date_str}")
        
        # 캐시 클리어 (데이터 변경 후)
        try:
            load_csv.clear()
        except Exception:
            pass
        
        # ========== 재고 자동 차감 기능 ==========
        # 판매된 메뉴의 레시피를 기반으로 재료 사용량 계산 후 재고 차감
        # 주의: 재고 차감은 트랜잭션 외부에서 실행 (마감 저장과 독립적)
        if sales_items:
            try:
                # 레시피 데이터 로드
                recipe_result = supabase.table("recipes").select("menu_id,ingredient_id,qty").eq("store_id", store_id).execute()
                
                if recipe_result.data:
                    # 메뉴명 -> 메뉴 ID 매핑
                    menu_result = supabase.table("menu_master").select("id,name").eq("store_id", store_id).execute()
                    menu_map = {m['name']: m['id'] for m in menu_result.data}
                    
                    # 재료 ID -> 재료명 매핑
                    ingredient_result = supabase.table("ingredients").select("id,name").eq("store_id", store_id).execute()
                    ingredient_map = {i['id']: i['name'] for i in ingredient_result.data}
                    
                    # 재료별 사용량 계산
                    ingredient_usage = {}  # {ingredient_id: total_usage}
                    
                    for menu_name, sales_qty in sales_items:
                        if sales_qty > 0 and menu_name in menu_map:
                            menu_id = menu_map[menu_name]
                            
                            # 해당 메뉴의 레시피 찾기
                            menu_recipes = [r for r in recipe_result.data if r['menu_id'] == menu_id]
                            
                            for recipe in menu_recipes:
                                ingredient_id = recipe['ingredient_id']
                                recipe_qty = float(recipe['qty'])
                                
                                # 재료 사용량 = 판매수량 × 레시피 사용량
                                usage = sales_qty * recipe_qty
                                
                                if ingredient_id in ingredient_usage:
                                    ingredient_usage[ingredient_id] += usage
                                else:
                                    ingredient_usage[ingredient_id] = usage
                    
                    # 재고 차감
                    for ingredient_id, usage_amount in ingredient_usage.items():
                        # 현재 재고 조회
                        inventory_result = supabase.table("inventory").select("on_hand").eq("store_id", store_id).eq("ingredient_id", ingredient_id).execute()
                        
                        if inventory_result.data:
                            current_stock = float(inventory_result.data[0]['on_hand'])
                            new_stock = max(0, current_stock - usage_amount)  # 음수 방지
                            
                            # 재고 업데이트
                            supabase.table("inventory").update({
                                "on_hand": new_stock
                            }).eq("store_id", store_id).eq("ingredient_id", ingredient_id).execute()
                            
                            ingredient_name = ingredient_map.get(ingredient_id, f"ID:{ingredient_id}")
                            logger.info(f"Inventory updated: {ingredient_name} - {current_stock:.2f} → {new_stock:.2f} (사용량: {usage_amount:.2f})")
            except Exception as e:
                # 재고 차감 실패해도 마감 저장은 성공으로 처리 (경고만 로깅)
                logger.warning(f"재고 자동 차감 중 오류 발생 (마감은 저장됨): {e}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to save daily close: {e}")
        # 트랜잭션 함수가 실패하면 자동 롤백됨
        raise


def delete_sales(date, store=None):
    """매출 데이터 삭제"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 삭제할 수 없습니다."
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
        supabase.table("sales").delete().eq("store_id", store_id).eq("date", date_str).execute()
        logger.info(f"Sales deleted: {date_str}")
        
        # 소프트 무효화 (token bump + 부분 clear)
        soft_invalidate(
            reason=f"delete_sales: {date_str}",
            targets=["sales"]
        )
        
        return True, "삭제 성공"
    except Exception as e:
        logger.error(f"Failed to delete sales: {e}")
        raise


def delete_visitor(date):
    """방문자 데이터 삭제"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 삭제할 수 없습니다."
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
        supabase.table("naver_visitors").delete().eq("store_id", store_id).eq("date", date_str).execute()
        logger.info(f"Visitor deleted: {date_str}")
        
        # 소프트 무효화 (token bump + 부분 clear)
        soft_invalidate(
            reason=f"delete_visitor: {date_str}",
            targets=["visitors"]
        )
        
        return True, "삭제 성공"
    except Exception as e:
        logger.error(f"Failed to delete visitor: {e}")
        raise


def save_expense_item(year, month, category, item_name, amount, notes=None):
    """비용구조 항목 저장"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        supabase.table("expense_structure").insert({
            "store_id": store_id,
            "year": int(year),
            "month": int(month),
            "category": category,
            "item_name": item_name,
            "amount": float(amount),
            "notes": notes if notes else None
        }).execute()
        
        logger.info(f"Expense item saved: {year}-{month}, {category}, {item_name}")
        
        # 소프트 무효화 (token bump + 부분 clear)
        soft_invalidate(
            reason=f"save_expense_item: {year}-{month}",
            targets=["cost", "expense_structure"],
            session_keys=['ss_expense_structure_df']
        )
        
        # S6: 비용 저장 직후 스냅샷 (dev_mode에서만)
        try:
            from src.auth import is_dev_mode
            if is_dev_mode():
                from src.utils.boot_perf import snapshot_current_metrics
                snapshot_current_metrics("S6: 비용 저장 직후 rerun")
        except Exception:
            pass
        
        return True
    except Exception as e:
        logger.error(f"Failed to save expense item: {e}")
        raise


def update_expense_item(expense_id, item_name, amount, notes=None):
    """비용구조 항목 수정"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 수정할 수 없습니다."
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        update_data = {
            "item_name": item_name,
            "amount": float(amount),
            "updated_at": datetime.now(timezone.utc).isoformat()  # DB 저장은 UTC
        }
        if notes is not None:
            update_data["notes"] = notes
        
        supabase.table("expense_structure")\
            .update(update_data)\
            .eq("id", expense_id)\
            .eq("store_id", store_id)\
            .execute()
        
        logger.info(f"Expense item updated: {expense_id}")
        
        # 소프트 무효화 (token bump + 부분 clear)
        soft_invalidate(
            reason=f"update_expense_item: {expense_id}",
            targets=["cost", "expense_structure"],
            session_keys=['ss_expense_structure_df']
        )
        
        # S6: 비용 저장 직후 스냅샷 (dev_mode에서만)
        try:
            from src.auth import is_dev_mode
            if is_dev_mode():
                from src.utils.boot_perf import snapshot_current_metrics
                snapshot_current_metrics("S6: 비용 저장 직후 rerun")
        except Exception:
            pass
        
        return True, "수정 성공"
    except Exception as e:
        logger.error(f"Failed to update expense item: {e}")
        raise


def delete_expense_item(expense_id):
    """비용구조 항목 삭제"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 삭제할 수 없습니다."
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        supabase.table("expense_structure").delete().eq("id", expense_id).eq("store_id", store_id).execute()
        logger.info(f"Expense item deleted: {expense_id}")
        
        # 소프트 무효화 (token bump + 부분 clear)
        soft_invalidate(
            reason=f"delete_expense_item: {expense_id}",
            targets=["cost", "expense_structure"],
            session_keys=['ss_expense_structure_df']
        )
        
        return True, "삭제 성공"
    except Exception as e:
        logger.error(f"Failed to delete expense item: {e}")
        raise


def _load_expense_structure_impl(year, month, store_id: str, client_mode: str, bypass_cache: bool = False):
    """
    load_expense_structure 내부 구현 (캐시 우회 옵션)
    이 함수가 실행되면 캐시 MISS임을 의미 (bypass_cache=True일 때는 제외)
    """
    # 데이터 호출 계측 시작
    start_time = time.perf_counter()
    
    # 캐시 MISS 로그 기록 (bypass_cache가 False일 때만, 즉 캐시를 사용하려고 했을 때만)
    if not bypass_cache:
        _log_cache_miss("load_expense_structure", year=year, month=month, store_id=store_id, client_mode=client_mode)
    
    # 조회용 클라이언트 사용 (DEV MODE에서 service_role_key 사용 가능)
    try:
        supabase = get_read_client()
    except Exception as e:
        logger.error(f"Supabase client init failed in load_expense_structure: {e}")
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        record_data_call(f"load_expense_structure({year}-{month}) [ERROR]", elapsed_ms, rows=0, source="supabase")
        return pd.DataFrame()
    
    if not supabase:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        record_data_call(f"load_expense_structure({year}-{month}) [NO_CLIENT]", elapsed_ms, rows=0, source="supabase")
        return pd.DataFrame()
    
    # store_id는 이미 파라미터로 받았지만, 검증용으로 다시 확인
    if not store_id:
        store_id = get_current_store_id()
        if not store_id:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            record_data_call(f"load_expense_structure({year}-{month}) [NO_STORE_ID]", elapsed_ms, rows=0, source="supabase")
            return pd.DataFrame()
    
    # 개발모드 디버그 정보 수집
    debug_info = {}
    try:
        from src.auth import get_read_client_mode
        if _is_dev_mode():
            debug_info['store_id'] = store_id
            debug_info['client_mode'] = get_read_client_mode()
            
            # Supabase URL 추출 (프로젝트 식별용, 앞부분만)
            try:
                supabase_url = st.secrets.get("supabase", {}).get("url", "")
                if supabase_url:
                    # https://xxxx.supabase.co 에서 xxxx 부분만 추출
                    import re
                    match = re.search(r'https://([^.]+)\.supabase\.co', supabase_url)
                    if match:
                        debug_info['supabase_project'] = match.group(1)
                    else:
                        debug_info['supabase_project'] = "unknown"
                else:
                    debug_info['supabase_project'] = "not_configured"
            except Exception:
                debug_info['supabase_project'] = "error"
            
            # 쿼리 필터 조건 수집
            debug_info['filters'] = [
                f"store_id={store_id}",
                f"year={int(year)}",
                f"month={int(month)}"
            ]
    except Exception:
        pass
    
    try:
        # 쿼리 빌드
        query = supabase.table("expense_structure")\
            .select("*")\
            .eq("store_id", store_id)\
            .eq("year", int(year))\
            .eq("month", int(month))
        
        # timed_select로 쿼리 실행 및 타이밍 기록
        result = timed_select(
            f"load_expense_structure(year={year}, month={month})",
            lambda: query.execute()
        )
        
        # 개발모드 디버그 정보 출력
        if debug_info:
            try:
                import streamlit as st
                with st.expander("🔍 DEBUG: expense_structure 조회", expanded=False):
                    st.write(f"**CURRENT STORE ID:** {debug_info.get('store_id', 'N/A')}")
                    st.write(f"**DB CLIENT MODE:** {debug_info.get('client_mode', 'N/A')}")
                    st.write(f"**Supabase 프로젝트:** {debug_info.get('supabase_project', 'N/A')}")
                    st.write("**쿼리 필터 조건:**")
                    for filter_cond in debug_info.get('filters', []):
                        st.caption(f"  - {filter_cond}")
                    
                    st.write("**쿼리 직후 결과:**")
                    row_count = len(result.data) if result.data else 0
                    st.write(f"  - row_count: {row_count}")
                    if result.data and len(result.data) > 0:
                        st.write("  - data[:3]:")
                        import json
                        # 민감한 정보 제거하고 표시
                        display_data = []
                        for item in result.data[:3]:
                            safe_item = {k: v for k, v in item.items() if k not in ['id', 'store_id']}
                            display_data.append(safe_item)
                        st.json(display_data)
                    else:
                        st.caption("  (데이터 없음)")
                    
                    # 캐시 상태 표시
                    if bypass_cache:
                        st.caption("  ⚠️ 캐시 우회 모드로 실행됨")
                    else:
                        st.caption("  ℹ️ 캐시 적용됨 (캐시 우회하려면 사이드바 토글 사용)")
            except Exception:
                pass  # 디버그 출력 실패해도 계속 진행
        
        if result.data:
            df = pd.DataFrame(result.data)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            record_data_call(f"load_expense_structure({year}-{month})", elapsed_ms, rows=len(df), source="supabase")
            return df
        else:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            record_data_call(f"load_expense_structure({year}-{month})", elapsed_ms, rows=0, source="supabase")
            return pd.DataFrame(columns=['id', 'category', 'item_name', 'amount', 'notes'])
    except Exception as e:
        logger.error(f"Failed to load expense structure: {e}")
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        record_data_call(f"load_expense_structure({year}-{month}) [EXCEPTION]", elapsed_ms, rows=0, source="supabase")
        # 에러도 디버그에 표시
        if debug_info:
            try:
                import streamlit as st
                with st.expander("🔍 DEBUG: expense_structure 조회", expanded=False):
                    st.error(f"**쿼리 실행 실패:** {str(e)}")
            except Exception:
                pass
        return pd.DataFrame()


@st.cache_data(ttl=60)  # 1분 캐시 (비용구조는 자주 변경될 수 있으므로 짧게, 고정값으로 설정하여 캐시 안정성 확보)
def load_expense_structure(year, month, store_id: str = None, client_mode: str = None):
    """
    비용 구조 데이터 로드
    
    Args:
        year: 연도
        month: 월
        store_id: store_id (None이면 get_current_store_id() 사용)
        client_mode: client_mode (None이면 get_read_client_mode() 사용)
    """
    # 가드: 온라인에서는 anon으로 read 금지 (DEV에서만 허용)
    if client_mode is None:
        client_mode = get_read_client_mode()
    
    if client_mode == "anon" and not _is_dev_mode():
        error_msg = f"❌ 보안 위반: 온라인 환경에서 anon 클라이언트로 데이터 조회 시도 (load_expense_structure)"
        logger.error(error_msg)
        st.error(error_msg)
        st.warning("💡 로그인 상태를 확인하세요. 로그아웃 후 다시 로그인해 주세요.")
        return {}
    """
    비용구조 데이터 로드 (특정 연도/월)
    세션 캐시 우선 사용 (현재 연도/월만) → 없으면 @st.cache_data 캐시 사용 → 없으면 DB 조회
    """
    from datetime import datetime
    
    # 현재 연도/월과 일치하면 세션 캐시 확인 (KST 기준)
    current_year = current_year_kst()
    current_month = current_month_kst()
    if year == current_year and month == current_month:
        session_key = 'ss_expense_structure_df'
        if session_key in st.session_state:
            if _is_dev_mode():
                logger.debug(f"load_expense_structure: Session cache HIT for {year}-{month}")
            df = st.session_state[session_key]
            # 캐시 히트도 계측 (매우 빠름)
            record_data_call(f"load_expense_structure({year}-{month})", 0.1, rows=len(df), source="session_cache")
            return df
    
    # store_id와 client_mode를 캐시 키에 명시적으로 포함하기 위해 가져오기
    if store_id is None:
        store_id = get_current_store_id()
    if client_mode is None:
        try:
            client_mode = get_read_client_mode()
        except Exception:
            client_mode = "unknown"
    
    # 가드: 온라인에서는 anon으로 read 금지 (DEV에서만 허용)
    if client_mode == "anon" and not _is_dev_mode():
        error_msg = f"❌ 보안 위반: 온라인 환경에서 anon 클라이언트로 데이터 조회 시도 (load_expense_structure)"
        logger.error(error_msg)
        st.error(error_msg)
        st.warning("💡 로그인 상태를 확인하세요. 로그아웃 후 다시 로그인해 주세요.")
        return pd.DataFrame()
    
    # 개발모드에서 캐시 우회 옵션 확인
    bypass_cache = False
    try:
        if _is_dev_mode():
            bypass_cache = st.session_state.get("_bypass_cache_expense_structure", False)
    except Exception:
        pass
    
    # @st.cache_data 캐시 또는 DB 조회
    df = _load_expense_structure_impl(year, month, store_id, client_mode, bypass_cache=bypass_cache)
    
    # 현재 연도/월이면 세션 캐시에 저장
    if year == current_year and month == current_month:
        st.session_state['ss_expense_structure_df'] = df
        if _is_dev_mode():
            logger.debug(f"load_expense_structure: Session cache SET for {year}-{month} ({len(df)} rows)")
    
    return df


@st.cache_data(ttl=60)  # 1분 캐시
def load_expense_structure_range(year_start, month_start, year_end, month_end):
    """비용구조 데이터 로드 (기간 범위)"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return pd.DataFrame()
    
    store_id = get_current_store_id()
    if not store_id:
        return pd.DataFrame()
    
    try:
        # 모든 데이터를 가져온 후 필터링
        result = supabase.table("expense_structure")\
            .select("*")\
            .eq("store_id", store_id)\
            .execute()
        
        if result.data:
            df = pd.DataFrame(result.data)
            # 기간 필터링
            def in_range(row):
                y, m = row['year'], row['month']
                if y < year_start or y > year_end:
                    return False
                if y == year_start and m < month_start:
                    return False
                if y == year_end and m > month_end:
                    return False
                return True
            
            df = df[df.apply(in_range, axis=1)]
            return df
        else:
            return pd.DataFrame(columns=['id', 'category', 'item_name', 'amount', 'notes', 'year', 'month'])
    except Exception as e:
        logger.error(f"Failed to load expense structure range: {e}")
        return pd.DataFrame()


def copy_expense_structure_from_previous_month(year, month):
    """전월 비용구조 데이터를 현재 월로 복사"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False, "DEV MODE에서는 복사할 수 없습니다."
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 전월 계산
        prev_month = month - 1
        prev_year = year
        if prev_month == 0:
            prev_month = 12
            prev_year = year - 1
        
        # 전월 데이터 로드
        prev_data = load_expense_structure(prev_year, prev_month)
        if prev_data.empty:
            return False, "복사할 전월 데이터가 없습니다."
        
        # 현재 월 데이터 확인
        current_data = load_expense_structure(year, month)
        if not current_data.empty:
            return False, "이미 현재 월에 데이터가 있습니다. 먼저 삭제해주세요."
        
        # 전월 데이터 복사
        records = []
        for _, row in prev_data.iterrows():
            records.append({
                "store_id": store_id,
                "year": int(year),
                "month": int(month),
                "category": row['category'],
                "item_name": row['item_name'],
                "amount": float(row['amount']),
                "notes": row.get('notes')
            })
        
        if records:
            supabase.table("expense_structure").insert(records).execute()
            logger.info(f"Expense structure copied from {prev_year}-{prev_month} to {year}-{month}")
            return True, f"전월({prev_year}년 {prev_month}월) 데이터가 복사되었습니다."
        else:
            return False, "복사할 데이터가 없습니다."
    except Exception as e:
        logger.error(f"Failed to copy expense structure: {e}")
        raise


def create_backup():
    """데이터 백업 (DB 기반에서는 단순 로그만)"""
    logger = logging.getLogger(__name__)
    logger.info("Backup requested (DB mode - data is already persisted in Supabase)")
    return True, "데이터는 Supabase에 자동으로 영구 저장됩니다."


# ============================================
# Phase 1: 공급업체 및 발주 이력 관리 함수
# ============================================

def save_supplier(supplier_name, phone=None, email=None, delivery_days=None, 
                  min_order_amount=0, delivery_fee=0, notes=None):
    """공급업체 등록/수정"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        supabase.table("suppliers").upsert({
            "store_id": store_id,
            "name": supplier_name,
            "phone": phone or "",
            "email": email or "",
            "delivery_days": delivery_days or "",
            "min_order_amount": float(min_order_amount) if min_order_amount else 0,
            "delivery_fee": float(delivery_fee) if delivery_fee else 0,
            "notes": notes or ""
        }, on_conflict="store_id,name").execute()
        
        logger.info(f"Supplier saved: {supplier_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to save supplier: {e}")
        raise


def delete_supplier(supplier_name):
    """공급업체 삭제"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        supabase.table("suppliers").delete().eq("store_id", store_id).eq("name", supplier_name).execute()
        logger.info(f"Supplier deleted: {supplier_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete supplier: {e}")
        raise


def save_ingredient_supplier(ingredient_name, supplier_name, unit_price, is_default=True):
    """재료-공급업체 매핑 저장

    Notes
    -----
    - unit_price 인자는 **발주 단위 기준 단가(원/발주단위)** 로 전달된다고 가정한다.
    - ingredients 테이블의 conversion_rate 컬럼을 사용해
      기본 단위 단가(원/기본단위)로 환산해서 DB에 저장한다.
      (1 발주단위 = conversion_rate * 기본단위)
    """
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 재료 ID 및 변환 비율 찾기
        ing_result = supabase.table("ingredients").select("id,conversion_rate").eq("store_id", store_id).eq("name", ingredient_name).execute()
        if not ing_result.data:
            raise Exception(f"재료 '{ingredient_name}'를 찾을 수 없습니다.")
        ingredient_row = ing_result.data[0]
        ingredient_id = ingredient_row['id']
        conversion_rate = ingredient_row.get('conversion_rate', 1.0) or 1.0
        
        # 공급업체 ID 찾기
        sup_result = supabase.table("suppliers").select("id").eq("store_id", store_id).eq("name", supplier_name).execute()
        if not sup_result.data:
            raise Exception(f"공급업체 '{supplier_name}'를 찾을 수 없습니다.")
        supplier_id = sup_result.data[0]['id']
        
        # 기본 공급업체인 경우, 다른 기본 공급업체 해제
        if is_default:
            # 해당 재료의 다른 기본 공급업체 해제
            existing = supabase.table("ingredient_suppliers").select("id").eq("store_id", store_id).eq("ingredient_id", ingredient_id).eq("is_default", True).execute()
            if existing.data:
                for item in existing.data:
                    supabase.table("ingredient_suppliers").update({"is_default": False}).eq("id", item['id']).execute()
        
        # 발주 단가(원/발주단위)를 기본 단위 단가(원/기본단위)로 환산
        try:
            conv = float(conversion_rate)
            price_per_order_unit = float(unit_price)
            if conv > 0:
                base_unit_price = price_per_order_unit / conv
            else:
                base_unit_price = price_per_order_unit
        except Exception:
            base_unit_price = float(unit_price)

        # 재료-공급업체 매핑 저장 (기본 단위 단가 기준)
        supabase.table("ingredient_suppliers").upsert({
            "store_id": store_id,
            "ingredient_id": ingredient_id,
            "supplier_id": supplier_id,
            "unit_price": float(base_unit_price),
            "is_default": is_default
        }, on_conflict="store_id,ingredient_id,supplier_id").execute()
        
        logger.info(f"Ingredient-supplier mapping saved: {ingredient_name} -> {supplier_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to save ingredient-supplier mapping: {e}")
        raise


def delete_ingredient_supplier(ingredient_name, supplier_name):
    """재료-공급업체 매핑 삭제"""
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 재료 ID 찾기
        ing_result = supabase.table("ingredients").select("id").eq("store_id", store_id).eq("name", ingredient_name).execute()
        if not ing_result.data:
            raise Exception(f"재료 '{ingredient_name}'를 찾을 수 없습니다.")
        ingredient_id = ing_result.data[0]['id']
        
        # 공급업체 ID 찾기
        sup_result = supabase.table("suppliers").select("id").eq("store_id", store_id).eq("name", supplier_name).execute()
        if not sup_result.data:
            raise Exception(f"공급업체 '{supplier_name}'를 찾을 수 없습니다.")
        supplier_id = sup_result.data[0]['id']
        
        supabase.table("ingredient_suppliers").delete().eq("store_id", store_id).eq("ingredient_id", ingredient_id).eq("supplier_id", supplier_id).execute()
        logger.info(f"Ingredient-supplier mapping deleted: {ingredient_name} -> {supplier_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete ingredient-supplier mapping: {e}")
        raise


def save_order(order_date, ingredient_name, supplier_name, quantity, unit_price, 
               total_amount, status="예정", expected_delivery_date=None, notes=None):
    """발주 이력 저장
    
    주의
    ----
    - quantity, unit_price 는 **기본 단위 기준** 값이다.
      (예: quantity = g, unit_price = 원/g)
    - UI 단에서 발주단위(개, 박스 등)를 사용하더라도,
      이 함수에 들어올 때는 반드시 기본 단위로 환산해서 넣어야 한다.
      (환산 로직은 `order_service.py` 등에 모아 관리한다.)
    """
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        # 재료 ID 찾기
        ing_result = supabase.table("ingredients").select("id").eq("store_id", store_id).eq("name", ingredient_name).execute()
        if not ing_result.data:
            raise Exception(f"재료 '{ingredient_name}'를 찾을 수 없습니다.")
        ingredient_id = ing_result.data[0]['id']
        
        # 공급업체 ID 찾기
        sup_result = supabase.table("suppliers").select("id").eq("store_id", store_id).eq("name", supplier_name).execute()
        if not sup_result.data:
            raise Exception(f"공급업체 '{supplier_name}'를 찾을 수 없습니다.")
        supplier_id = sup_result.data[0]['id']
        
        # 발주 저장
        result = supabase.table("orders").insert({
            "store_id": store_id,
            "order_date": order_date.strftime("%Y-%m-%d") if isinstance(order_date, datetime) else str(order_date),
            "ingredient_id": ingredient_id,
            "supplier_id": supplier_id,
            "quantity": float(quantity),
            "unit_price": float(unit_price),
            "total_amount": float(total_amount),
            "status": status,
            "expected_delivery_date": expected_delivery_date.strftime("%Y-%m-%d") if expected_delivery_date and isinstance(expected_delivery_date, datetime) else (str(expected_delivery_date) if expected_delivery_date else None),
            "notes": notes or ""
        }).execute()
        
        logger.info(f"Order saved: {ingredient_name} from {supplier_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to save order: {e}")
        raise


def update_order_status(order_id, status, actual_delivery_date=None):
    """발주 상태 업데이트
    
    - status 가 '입고완료' 이고 actual_delivery_date 가 있을 때 재고(on_hand)를 증가시킨다.
    - 중복 입고 반영을 막기 위해 orders.inventory_applied 플래그를 사용한다.
      (단, 해당 컬럼이 아직 없을 수도 있으므로, 없으면 조용히 건너뛴다.)
    """
    supabase = _check_supabase_for_dev_mode()
    if not supabase:
        return False
    
    store_id = get_current_store_id()
    if not store_id:
        raise Exception("No store_id found")
    
    try:
        update_data = {"status": status}
        if actual_delivery_date:
            update_data["actual_delivery_date"] = actual_delivery_date.strftime("%Y-%m-%d") if isinstance(actual_delivery_date, datetime) else str(actual_delivery_date)
        
        # 입고 완료 시 재고 반영 (inventory_applied 플래그 기반, idempotent)
        if status == "입고완료" and actual_delivery_date:
            # 발주 정보 가져오기 (inventory_applied 포함 시도)
            order_result = supabase.table("orders")\
                .select("ingredient_id,quantity,inventory_applied")\
                .eq("id", order_id)\
                .eq("store_id", store_id)\
                .execute()
            if order_result.data:
                row = order_result.data[0]
                ingredient_id = row.get("ingredient_id")
                quantity = row.get("quantity", 0)
                inventory_applied = bool(row.get("inventory_applied", False))

                # 아직 재고 반영이 안 된 경우에만 처리
                if ingredient_id and not inventory_applied:
                    inv_result = supabase.table("inventory")\
                        .select("on_hand")\
                        .eq("store_id", store_id)\
                        .eq("ingredient_id", ingredient_id)\
                        .execute()
                    if inv_result.data:
                        current_stock = float(inv_result.data[0].get("on_hand", 0) or 0)
                        new_stock = current_stock + float(quantity or 0)
                        supabase.table("inventory")\
                            .update({"on_hand": new_stock})\
                            .eq("store_id", store_id)\
                            .eq("ingredient_id", ingredient_id)\
                            .execute()

                    # 재고 반영 완료 표시 (컬럼이 없으면 조용히 무시)
                    try:
                        supabase.table("orders")\
                            .update({"inventory_applied": True})\
                            .eq("id", order_id)\
                            .eq("store_id", store_id)\
                            .execute()
                    except Exception as e:
                        logger.warning(f"inventory_applied 업데이트 실패 (마이그레이션 필요할 수 있음): {e}")

        # 상태/입고일 업데이트
        supabase.table("orders").update(update_data).eq("id", order_id).eq("store_id", store_id).execute()
        logger.info(f"Order status updated: {order_id} -> {status}")
        return True
    except Exception as e:
        logger.error(f"Failed to update order status: {e}")
        raise


# ============================================
# Phase B: 실제정산 비용 항목 템플릿 관리
# ============================================

def load_cost_item_templates(store_id: str):
    """
    비용 항목 템플릿 로드 (is_active=true만)
    
    Args:
        store_id: 매장 ID
    
    Returns:
        list: 템플릿 항목 리스트 (category, item_name, item_type, is_recurring, recurring_value, sort_order)
    """
    try:
        supabase = get_read_client()
        if not supabase:
            logger.warning("Supabase client not available")
            return []
        
        result = supabase.table("cost_item_templates")\
            .select("*")\
            .eq("store_id", store_id)\
            .eq("is_active", True)\
            .order("category")\
            .order("sort_order")\
            .order("item_name")\
            .execute()
        
        logger.info(f"Loaded {len(result.data) if result.data else 0} cost item templates")
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Failed to load cost item templates: {e}")
        return []


def save_cost_item_template(
    store_id: str,
    category: str,
    item_name: str,
    item_type: str = 'normal',
    is_recurring: bool = False,
    recurring_value: float = 0.0,
    sort_order: int = 0
):
    """
    비용 항목 템플릿 저장/업데이트 (upsert)
    
    Args:
        store_id: 매장 ID
        category: 카테고리 (임차료, 인건비, 재료비, 공과금, 부가세&카드수수료)
        item_name: 항목명
        item_type: 항목 유형 ('normal' | 'fixed' | 'percent')
        is_recurring: 반복 여부
        recurring_value: 반복 값
        sort_order: 정렬 순서
    
    Returns:
        bool: 성공 여부
    """
    try:
        supabase = get_read_client()
        if not supabase:
            logger.warning("Supabase client not available")
            return False
        
        # upsert (store_id, category, item_name 기준)
        supabase.table("cost_item_templates").upsert({
            "store_id": store_id,
            "category": category,
            "item_name": item_name,
            "item_type": item_type,
            "is_recurring": is_recurring,
            "recurring_value": float(recurring_value),
            "sort_order": int(sort_order),
            "is_active": True
        }, on_conflict="store_id,category,item_name").execute()
        
        logger.info(f"Cost item template saved: {category} - {item_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to save cost item template: {e}")
        raise


def soft_delete_cost_item_template(store_id: str, category: str, item_name: str):
    """
    비용 항목 템플릿 Soft Delete (is_active=false로 업데이트)
    
    Args:
        store_id: 매장 ID
        category: 카테고리
        item_name: 항목명
    
    Returns:
        bool: 성공 여부
    """
    try:
        supabase = get_read_client()
        if not supabase:
            logger.warning("Supabase client not available")
            return False
        
        supabase.table("cost_item_templates")\
            .update({"is_active": False})\
            .eq("store_id", store_id)\
            .eq("category", category)\
            .eq("item_name", item_name)\
            .execute()
        
        logger.info(f"Cost item template soft deleted: {category} - {item_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to soft delete cost item template: {e}")
        raise


# ============================================
# Phase C: 실제정산 월별 금액/비율 저장/불러오기
# ============================================

def load_actual_settlement_items(store_id: str, year: int, month: int):
    """
    실제정산 월별 항목 값 로드
    
    Args:
        store_id: 매장 ID
        year: 연도
        month: 월
    
    Returns:
        list: 저장된 항목 값 리스트 (template_id, amount, percent, status)
    """
    try:
        supabase = get_read_client()
        if not supabase:
            logger.warning("Supabase client not available")
            return []
        
        result = supabase.table("actual_settlement_items")\
            .select("*")\
            .eq("store_id", store_id)\
            .eq("year", int(year))\
            .eq("month", int(month))\
            .execute()
        
        logger.info(f"Loaded {len(result.data) if result.data else 0} actual settlement items for {year}-{month}")
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Failed to load actual settlement items: {e}")
        return []


def upsert_actual_settlement_item(
    store_id: str,
    year: int,
    month: int,
    template_id: int,
    amount: float = None,
    percent: float = None,
    status: str = 'draft'
):
    """
    실제정산 월별 항목 값 저장/업데이트 (upsert)
    Phase C.5: input_type에 따라 amount 또는 percent만 저장 (다른 값은 None 또는 0)
    
    Args:
        store_id: 매장 ID
        year: 연도
        month: 월
        template_id: 템플릿 ID (cost_item_templates.id)
        amount: 금액 (input_type='amount'일 때)
        percent: 비율 (input_type='rate'일 때)
        status: 상태 ('draft' | 'final')
    
    Returns:
        bool: 성공 여부
    """
    try:
        supabase = get_read_client()
        if not supabase:
            logger.warning("Supabase client not available")
            return False
        
        upsert_data = {
            "store_id": store_id,
            "year": int(year),
            "month": int(month),
            "template_id": int(template_id),
            "status": status,
        }
        
        # Phase C.5: input_type에 따라 선택적 저장
        # amount가 있으면 amount 저장, percent는 None (의미 명확)
        # percent가 있으면 percent 저장, amount는 None
        if amount is not None:
            upsert_data["amount"] = float(amount)
            upsert_data["percent"] = None  # Phase C.5: 명확성을 위해 None
        elif percent is not None:
            upsert_data["percent"] = float(percent)
            upsert_data["amount"] = None  # Phase C.5: 명확성을 위해 None
        else:
            # 둘 다 None이면 0으로 저장 (기존 정책 유지)
            upsert_data["amount"] = 0.0
            upsert_data["percent"] = 0.0
        
        # upsert (store_id, year, month, template_id 기준)
        supabase.table("actual_settlement_items").upsert(
            upsert_data,
            on_conflict="store_id,year,month,template_id"
        ).execute()
        
        logger.info(f"Actual settlement item saved: {year}-{month}, template_id={template_id}, amount={amount}, percent={percent}")
        return True
    except Exception as e:
        logger.error(f"Failed to upsert actual settlement_item: {e}")
        raise


# ============================================
# Phase D: 실제정산 - sales 테이블에서 월매출 자동 불러오기
# ============================================

@st.cache_data(ttl=60, show_spinner=False)  # 1분 캐시 (월이 바뀌거나 입력 즉시 반영)
def load_monthly_sales_total(store_id: str, year: int, month: int) -> int:
    """
    sales 테이블에서 월매출 합계 조회 (KST 기준)
    
    Args:
        store_id: 매장 ID
        year: 연도
        month: 월
    
    Returns:
        int: 월매출 합계 (원 단위)
    """
    try:
        supabase = get_read_client()
        if not supabase:
            logger.warning("Supabase client not available")
            return 0
        
        # KST 기준 월 시작/끝 계산
        KST = ZoneInfo("Asia/Seoul")
        start_kst = datetime(year, month, 1, 0, 0, 0, tzinfo=KST)
        
        # 다음달 1일 0시 (미포함)
        if month == 12:
            end_kst = datetime(year + 1, 1, 1, 0, 0, 0, tzinfo=KST)
        else:
            end_kst = datetime(year, month + 1, 1, 0, 0, 0, tzinfo=KST)
        
        # DATE 타입이므로 문자열로 변환 (YYYY-MM-DD)
        start_date_str = start_kst.date().isoformat()
        end_date_str = end_kst.date().isoformat()
        
        # sales 테이블 조회: store_id + 날짜 범위 필터
        # date >= start_date AND date < end_date
        result = supabase.table("sales")\
            .select("total_sales")\
            .eq("store_id", store_id)\
            .gte("date", start_date_str)\
            .lt("date", end_date_str)\
            .execute()
        
        # 합산 (total_sales 컬럼 사용)
        if result.data:
            total = sum(float(row.get('total_sales', 0) or 0) for row in result.data)
            row_count = len(result.data)
            logger.info(f"Monthly sales total loaded: {year}-{month}, {row_count} rows, total={total:,.0f}원")
            return int(total)
        else:
            logger.info(f"Monthly sales total loaded: {year}-{month}, 0 rows, total=0원")
            return 0
    except Exception as e:
        logger.error(f"Failed to load monthly sales total: {e}")
        return 0


# ============================================
# Phase F: 실제정산 확정(Final) + 잠금(읽기전용) + 확정 해제
# ============================================

@st.cache_data(ttl=30, show_spinner=False)  # 30초 캐시
def get_month_settlement_status(store_id: str, year: int, month: int) -> str:
    """
    월별 정산 상태 조회 (draft | final)
    
    Args:
        store_id: 매장 ID
        year: 연도
        month: 월
    
    Returns:
        str: 'draft' 또는 'final'
    """
    try:
        supabase = get_read_client()
        if not supabase:
            logger.warning("Supabase client not available")
            return 'draft'
        
        # status='final'이 1개라도 있으면 'final', 아니면 'draft'
        result = supabase.table("actual_settlement_items")\
            .select("status", count='exact')\
            .eq("store_id", store_id)\
            .eq("year", int(year))\
            .eq("month", int(month))\
            .eq("status", "final")\
            .limit(1)\
            .execute()
        
        # final이 1개라도 있으면 'final'
        if result.data and len(result.data) > 0:
            logger.info(f"Month settlement status: {year}-{month} = final")
            return 'final'
        else:
            logger.info(f"Month settlement status: {year}-{month} = draft")
            return 'draft'
    except Exception as e:
        logger.error(f"Failed to get month settlement status: {e}")
        return 'draft'  # 에러 시 기본값은 draft


def set_month_settlement_status(store_id: str, year: int, month: int, status: str) -> int:
    """
    월별 정산 상태 설정 (draft | final)
    
    Args:
        store_id: 매장 ID
        year: 연도
        month: 월
        status: 'draft' 또는 'final'
    
    Returns:
        int: 업데이트된 row count
    """
    if status not in ['draft', 'final']:
        raise ValueError(f"Invalid status: {status}. Must be 'draft' or 'final'")
    
    try:
        supabase = get_read_client()
        if not supabase:
            logger.warning("Supabase client not available")
            return 0
        
        # 월 전체 일괄 업데이트
        result = supabase.table("actual_settlement_items")\
            .update({
                "status": status,
                "updated_at": datetime.now(timezone.utc).isoformat()
            })\
            .eq("store_id", store_id)\
            .eq("year", int(year))\
            .eq("month", int(month))\
            .execute()
        
        affected_count = len(result.data) if result.data else 0
        logger.info(f"Month settlement status updated: {year}-{month} = {status}, affected={affected_count} rows")
        
        # 캐시 무효화
        try:
            get_month_settlement_status.clear()
            # load_actual_settlement_items는 함수가 아니므로 직접 clear 불가
            # 대신 캐시 키 기반으로 무효화 (필요 시)
        except Exception:
            pass
        
        return affected_count
    except Exception as e:
        logger.error(f"Failed to set month settlement status: {e}")
        raise
