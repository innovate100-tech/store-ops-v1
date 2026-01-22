"""
공통 페이지 설정 모듈
모든 페이지에서 공통으로 사용하는 setup 로직
"""
import streamlit as st
import logging
import sys

logger = logging.getLogger(__name__)


def _diagnose_table(client, table_name: str, store_id: str = None):
    """
    테이블별 상세 진단 함수
    
    Args:
        client: Supabase 클라이언트
        table_name: 테이블명
        store_id: store_id 값 (선택)
    
    Returns:
        dict: 진단 결과
    """
    result = {
        "table": table_name,
        "no_filter_count": 0,
        "no_filter_success": False,
        "no_filter_error": None,
        "with_filter_count": 0,
        "with_filter_success": False,
        "with_filter_error": None,
        "store_column_candidates": [],
        "found_store_column": None,
        "diagnosis": None,
    }
    
    # 1) 필터 없이 조회
    try:
        no_filter_result = client.table(table_name).select("*").limit(3).execute()
        result["no_filter_count"] = len(no_filter_result.data) if no_filter_result.data else 0
        result["no_filter_success"] = True
    except Exception as e:
        result["no_filter_error"] = repr(e)
        result["no_filter_success"] = False
    
    # 2) store_id가 있으면 필터 조회 시도
    if store_id:
        # 가능한 컬럼명 후보
        column_candidates = ['store_id', 'store_uuid', 'storeId', 'store', 'id']
        
        for col_name in column_candidates:
            try:
                filtered_result = client.table(table_name).select("*").eq(col_name, store_id).limit(3).execute()
                filtered_count = len(filtered_result.data) if filtered_result.data else 0
                
                if result["found_store_column"] is None:
                    result["found_store_column"] = col_name
                    result["with_filter_count"] = filtered_count
                    result["with_filter_success"] = True
                    result["store_column_candidates"].append(f"{col_name}: {filtered_count}건")
                else:
                    result["store_column_candidates"].append(f"{col_name}: {filtered_count}건")
            except Exception as e:
                error_msg = str(e)
                # 컬럼 없음 에러는 정상 (다른 컬럼명일 수 있음)
                if "column" in error_msg.lower() or "does not exist" in error_msg.lower():
                    result["store_column_candidates"].append(f"{col_name}: 컬럼 없음")
                else:
                    result["store_column_candidates"].append(f"{col_name}: 에러 - {error_msg[:50]}")
                    if not result["with_filter_error"]:
                        result["with_filter_error"] = repr(e)
    
    # 3) 원인 진단
    if not result["no_filter_success"]:
        result["diagnosis"] = "A) 테이블 조회 실패 (테이블 없음 또는 권한 없음)"
    elif result["no_filter_count"] == 0:
        if store_id and result["found_store_column"]:
            if result["with_filter_count"] == 0:
                result["diagnosis"] = "A) 테이블에 데이터가 없음 (필터 적용해도 0건)"
            else:
                result["diagnosis"] = "정상 (필터 적용 시 데이터 존재)"
        else:
            result["diagnosis"] = "A) 테이블에 데이터가 없음"
    else:
        # 필터 없이 데이터가 있는 경우
        if store_id:
            if result["found_store_column"]:
                if result["with_filter_count"] == 0:
                    result["diagnosis"] = "B) RLS 또는 store_id 불일치 (필터 없이 데이터 있음, 필터 적용 시 0건)"
                else:
                    result["diagnosis"] = "정상 (필터 적용 시 데이터 존재)"
            else:
                result["diagnosis"] = "C) store 필터 컬럼명 불일치 (필터 없이 데이터 있음, store 필터 컬럼 찾기 실패)"
        else:
            result["diagnosis"] = "정상 (데이터 존재, store_id 없어 필터 테스트 불가)"
    
    return result


def _show_package_versions():
    """
    DEV MODE일 때 패키지 버전 정보를 출력 (디버깅용)
    세션당 1회만 실행
    """
    try:
        # Python 3.8+ 호환성을 위한 import
        try:
            from importlib import metadata
        except ImportError:
            # Python 3.7 이하 대비 (하지만 실제로는 3.8+ 사용)
            import importlib_metadata as metadata
        
        versions = {}
        packages = ["supabase", "gotrue", "httpx", "postgrest", "realtime", "storage"]
        
        for pkg in packages:
            try:
                version = metadata.version(pkg)
                versions[pkg] = version
            except metadata.PackageNotFoundError:
                versions[pkg] = "not installed"
        
        # Streamlit 버전도 추가
        try:
            versions["streamlit"] = metadata.version("streamlit")
        except:
            versions["streamlit"] = "unknown"
        
        with st.expander("🔧 DEV MODE: 패키지 버전 정보", expanded=False):
            st.write("**설치된 패키지 버전:**")
            st.json(versions)
            st.caption("이 정보는 디버깅 목적으로만 사용됩니다.")
    except Exception as e:
        # 버전 정보 출력 실패해도 앱은 계속 실행
        logger.warning(f"_show_package_versions: 버전 정보 출력 실패 - {e}")


def bootstrap(page_title: str = "황승진 외식경영 의사결정도구"):
    """
    공통 페이지 설정 적용
    
    Args:
        page_title: 페이지 제목 (기본값: "황승진 외식경영 의사결정도구")
    """
    # bootstrap 실행 여부 플래그 설정
    st.session_state["_bootstrap_ran"] = True
    
    # 주입 추적 리스트 초기화 (없으면 생성)
    if "_dev_inject_trace" not in st.session_state:
        st.session_state["_dev_inject_trace"] = []
    
    st.session_state["_dev_inject_trace"].append("bootstrap: 함수 시작")
    
    try:
        # 페이지 설정은 최상단에 위치 (다른 st.* 호출 전에)
        try:
            st.set_page_config(
                page_title=page_title,
                page_icon="🍽️",
                layout="wide",
                initial_sidebar_state="expanded",  # 사이드바 항상 열림
                menu_items={
                    'Get Help': None,
                    'Report a bug': None,
                    'About': None
                }
            )
            st.session_state["_dev_inject_trace"].append("bootstrap: set_page_config 완료")
        except Exception as e:
            # 이미 설정된 경우 무시
            st.session_state["_dev_inject_trace"].append(f"bootstrap: set_page_config 예외 (무시됨) - {str(e)}")
            pass
        
        # 테마 상태 초기화 (기본: 화이트 모드)
        if "theme" not in st.session_state:
            st.session_state.theme = "light"
        
        # DEV MODE 체크 (로컬 개발용) - import 시 DB 호출 없음
        from src.auth import apply_dev_mode_session, is_dev_mode, clear_session
        
        # DEV MODE일 때 패키지 버전 정보 출력 (세션당 1회만)
        if is_dev_mode() and not st.session_state.get("_version_info_shown", False):
            _show_package_versions()
            st.session_state["_version_info_shown"] = True
        
        # clear_session() 호출 추적 (호출되는지 확인)
        import inspect
        import traceback
        current_frame = inspect.currentframe()
        if current_frame:
            frame = current_frame.f_back
            if frame:
                # 호출 스택에서 clear_session 호출 여부 확인
                tb_str = ''.join(traceback.format_stack(frame))
                if 'clear_session' in tb_str:
                    st.session_state["_dev_inject_trace"].append("bootstrap: clear_session() 호출 감지됨 (스택에서)")
        
        # apply_dev_mode_session() 강제 호출 (dev_mode일 때) - 세션당 1회만
        if not st.session_state.get("_dev_mode_applied", False):
            if is_dev_mode() or st.secrets.get("app", {}).get("dev_mode", False):
                st.session_state["_dev_inject_trace"].append("bootstrap: apply_dev_mode_session() 호출 전")
                apply_dev_mode_session()
                st.session_state["_dev_inject_trace"].append("bootstrap: apply_dev_mode_session() 호출 후")
            else:
                apply_dev_mode_session()
        
        # DEV MODE일 때 dev_store_id 자동 주입 - 세션당 1회만
        if not st.session_state.get("_dev_store_id_injected", False):
            _inject_dev_store_id()
            st.session_state["_dev_store_id_injected"] = True
        
        # 개발 모드에서만 Supabase 연결 테스트 (st.stop() 호출 금지) - 세션당 1회만
        if is_dev_mode() and not st.session_state.get("_supabase_connection_tested", False):
            _test_supabase_connection()
            st.session_state["_supabase_connection_tested"] = True
            # _show_performance_monitor()는 Debug 페이지에서만 호출됨
        
        # bootstrap() 함수의 가장 마지막에 dev_store_id 강제 주입 (최종 보장) - 세션당 1회만
        if not st.session_state.get("_dev_store_id_force_injected", False):
            _force_inject_dev_store_id_at_bootstrap_end()
            st.session_state["_dev_store_id_force_injected"] = True
        
        st.session_state["_dev_inject_trace"].append("bootstrap: 정상 완료 (try 블록 끝)")
        
    except Exception as e:
        # 예외 발생 시 저장
        st.session_state["_bootstrap_exception"] = repr(e)
        st.session_state["_dev_inject_trace"].append(f"bootstrap: 예외 발생 - {repr(e)}")
        logger.error(f"bootstrap() 예외 발생: {e}", exc_info=True)
        raise  # 예외를 다시 발생시켜서 사용자에게 알림
    
    finally:
        # bootstrap 끝부분에서 session_state 값 덤프 (주입 후 덮어쓰기 확인용)
        # finally 블록에서 실행하여 예외가 발생해도 덤프는 반드시 남김
        try:
            from src.auth import is_dev_mode
            # session_state 키 검증
            all_keys = list(st.session_state.keys())
            store_related_keys = [k for k in all_keys if "store" in k.lower() or "active" in k.lower()]
            
            dump_values = {
                "_active_store_id": st.session_state.get("_active_store_id"),
                "store_id": st.session_state.get("store_id"),
                "current_store_id": st.session_state.get("current_store_id"),
                "store_id_widget": st.session_state.get("store_id_widget"),
                "_dev_store_id_injected_at": st.session_state.get("_dev_store_id_injected_at"),
                "_active_store_id_exists": "_active_store_id" in st.session_state,
                "_active_store_id_direct": st.session_state.get("_active_store_id") if "_active_store_id" in st.session_state else "KEY_NOT_EXISTS",
                "store_related_keys": store_related_keys,
                "is_dev_mode": is_dev_mode(),
            }
            st.session_state["_bootstrap_end_dump"] = dump_values
            st.session_state["_dev_inject_trace"].append(f"bootstrap_end (finally): session_state 덤프 완료")
        except Exception as dump_error:
            st.session_state["_bootstrap_end_dump"] = {"error": repr(dump_error)}
            st.session_state["_dev_inject_trace"].append(f"bootstrap_end (finally): 덤프 중 예외 - {repr(dump_error)}")


def _inject_dev_store_id():
    """
    DEV MODE일 때 dev_store_id를 session_state에 자동 주입
    
    apply_dev_mode_session()에서 이미 설정하지만,
    bootstrap 단계에서도 한 번 더 확인하여 주입 보장
    """
    try:
        from src.auth import is_dev_mode
        
        # 주입 추적 리스트 초기화 (없으면 생성)
        if "_dev_inject_trace" not in st.session_state:
            st.session_state["_dev_inject_trace"] = []
        
        st.session_state["_dev_inject_trace"].append("_inject_dev_store_id: 함수 시작")
        
        if is_dev_mode():
            st.session_state["_dev_inject_trace"].append("_inject_dev_store_id: dev_mode=True 확인")
            
            # _active_store_id가 비어있고 dev_store_id가 있으면 주입
            # 실제 dict 접근으로만 확인
            current_active_store_id = st.session_state.get("_active_store_id")
            key_exists = "_active_store_id" in st.session_state
            st.session_state["_dev_inject_trace"].append(f"_inject_dev_store_id: 키 존재 여부={key_exists}, 현재 _active_store_id={current_active_store_id}")
            
            if not current_active_store_id:
                try:
                    dev_store_id = st.secrets.get("app", {}).get("dev_store_id", "")
                    st.session_state["_dev_inject_trace"].append(f"_inject_dev_store_id: dev_store_id from secrets={dev_store_id}")
                    
                    if dev_store_id:
                        st.session_state["_active_store_id"] = dev_store_id  # 단일 소스 오브 트루스
                        st.session_state["store_id"] = dev_store_id  # 레거시 호환
                        
                        # 주입 직후 실제 dict 접근으로 확인
                        verify_active = st.session_state.get("_active_store_id")
                        verify_store = st.session_state.get("store_id")
                        verify_key_exists = "_active_store_id" in st.session_state
                        
                        # 주입 직후 스냅샷 저장
                        st.session_state["_inject_snapshot"] = {
                            "function": "_inject_dev_store_id",
                            "_active_store_id": verify_active,
                            "store_id": verify_store,
                            "_active_store_id_exists": verify_key_exists,
                            "timestamp": "bootstrap_inject"
                        }
                        
                        st.session_state["_dev_store_id_injected_at"] = "bootstrap_inject"
                        st.session_state["_dev_inject_trace"].append(f"_inject_dev_store_id: 주입 완료 - _active_store_id={verify_active}, 키 존재={verify_key_exists}")
                        logger.info(f"DEV MODE: dev_store_id 자동 주입됨 (bootstrap): {dev_store_id}")
                    else:
                        st.session_state["_dev_inject_trace"].append("_inject_dev_store_id: dev_store_id가 비어있음")
                except Exception as e:
                    st.session_state["_dev_inject_trace"].append(f"_inject_dev_store_id: 예외 발생 - {str(e)}")
                    logger.warning(f"dev_store_id 자동 주입 실패: {e}")
            else:
                st.session_state["_dev_inject_trace"].append(f"_inject_dev_store_id: _active_store_id가 이미 있음 - 주입 건너뜀")
        else:
            st.session_state["_dev_inject_trace"].append("_inject_dev_store_id: dev_mode=False - 주입 건너뜀")
    except Exception as e:
        if "_dev_inject_trace" not in st.session_state:
            st.session_state["_dev_inject_trace"] = []
        st.session_state["_dev_inject_trace"].append(f"_inject_dev_store_id: 함수 레벨 예외 - {str(e)}")
        logger.warning(f"dev_store_id 자동 주입 체크 중 오류: {e}")


def _force_inject_dev_store_id_at_bootstrap_end():
    """
    bootstrap() 함수의 가장 마지막에 dev_store_id 강제 주입 (최종 보장)
    
    다른 코드에서 store_id를 None으로 덮어쓴 경우를 대비하여
    bootstrap 단계의 마지막에 한 번 더 강제로 주입
    """
    try:
        from src.auth import is_dev_mode
        
        # 주입 추적 리스트 초기화 (없으면 생성)
        if "_dev_inject_trace" not in st.session_state:
            st.session_state["_dev_inject_trace"] = []
        
        st.session_state["_dev_inject_trace"].append("_force_inject_dev_store_id_at_bootstrap_end: 함수 시작")
        
        if is_dev_mode():
            st.session_state["_dev_inject_trace"].append("_force_inject_dev_store_id_at_bootstrap_end: dev_mode=True 확인")
            
            # 실제 dict 접근으로만 확인
            current_active_store_id = st.session_state.get("_active_store_id")
            key_exists = "_active_store_id" in st.session_state
            st.session_state["_dev_inject_trace"].append(f"_force_inject_dev_store_id_at_bootstrap_end: 키 존재 여부={key_exists}, 현재 _active_store_id={current_active_store_id}")
            
            try:
                dev_store_id = st.secrets.get("app", {}).get("dev_store_id", "")
                st.session_state["_dev_inject_trace"].append(f"_force_inject_dev_store_id_at_bootstrap_end: dev_store_id from secrets={dev_store_id}")
                
                if dev_store_id:
                    # _active_store_id가 비어있거나 dev_store_id와 다르면 강제 주입
                    if not current_active_store_id or current_active_store_id != dev_store_id:
                        st.session_state["_active_store_id"] = dev_store_id  # 단일 소스 오브 트루스
                        st.session_state["store_id"] = dev_store_id  # 레거시 호환
                        # store_id_widget도 동기화 (위젯이 있으면)
                        if "store_id_widget" in st.session_state:
                            st.session_state["store_id_widget"] = dev_store_id
                        
                        # 주입 직후 실제 dict 접근으로 확인
                        verify_active = st.session_state.get("_active_store_id")
                        verify_store = st.session_state.get("store_id")
                        verify_key_exists = "_active_store_id" in st.session_state
                        
                        # 주입 직후 스냅샷 저장
                        st.session_state["_inject_snapshot"] = {
                            "function": "_force_inject_dev_store_id_at_bootstrap_end",
                            "_active_store_id": verify_active,
                            "store_id": verify_store,
                            "_active_store_id_exists": verify_key_exists,
                            "timestamp": "bootstrap_end"
                        }
                        
                        st.session_state["_dev_store_id_injected_at"] = "bootstrap_end"
                        st.session_state["_dev_inject_trace"].append(f"_force_inject_dev_store_id_at_bootstrap_end: 주입 완료 - _active_store_id={verify_active}, 키 존재={verify_key_exists}")
                        logger.info(f"DEV MODE: dev_store_id 강제 주입됨 (bootstrap_end): {dev_store_id}")
                    else:
                        st.session_state["_dev_inject_trace"].append(f"_force_inject_dev_store_id_at_bootstrap_end: _active_store_id가 이미 올바른 값 - 주입 건너뜀")
                else:
                    st.session_state["_dev_inject_trace"].append("_force_inject_dev_store_id_at_bootstrap_end: dev_store_id가 비어있음")
            except Exception as e:
                st.session_state["_dev_inject_trace"].append(f"_force_inject_dev_store_id_at_bootstrap_end: 예외 발생 - {str(e)}")
                logger.warning(f"dev_store_id 강제 주입 실패 (bootstrap_end): {e}")
        else:
            st.session_state["_dev_inject_trace"].append("_force_inject_dev_store_id_at_bootstrap_end: dev_mode=False - 주입 건너뜀")
    except Exception as e:
        if "_dev_inject_trace" not in st.session_state:
            st.session_state["_dev_inject_trace"] = []
        st.session_state["_dev_inject_trace"].append(f"_force_inject_dev_store_id_at_bootstrap_end: 함수 레벨 예외 - {str(e)}")
        logger.warning(f"dev_store_id 강제 주입 체크 중 오류 (bootstrap_end): {e}")


def _test_supabase_connection():
    """
    개발 모드에서 Supabase 연결 테스트
    """
    try:
        # Supabase 설정 로드 확인
        supabase_config = st.secrets.get("supabase", {})
        url = supabase_config.get("url", "")
        anon_key = supabase_config.get("anon_key", "")
        
        config_loaded = bool(url and anon_key)
        
        # 설정 로드 상태 표시
        with st.expander("🔧 개발 모드: Supabase 연결 상태", expanded=False):
            st.write("**설정 로드 상태:**")
            if config_loaded:
                st.success(f"✅ Supabase 설정 로드됨")
                st.caption(f"URL: {url[:30]}..." if len(url) > 30 else f"URL: {url}")
                st.caption(f"Anon Key: {anon_key[:20]}..." if len(anon_key) > 20 else f"Anon Key: {anon_key}")
            else:
                st.error("❌ Supabase 설정이 로드되지 않음")
                st.caption("`.streamlit/secrets.toml` 파일에 `[supabase]` 섹션과 `url`, `anon_key`가 설정되어 있는지 확인하세요.")
                return
            
            # 연결 테스트
            st.write("**연결 테스트:**")
            try:
                from src.auth import get_read_client, get_read_client_mode, is_dev_mode, get_current_store_id
                # 조회용 클라이언트 사용 (DEV MODE에서 service_role_key 사용 가능)
                client = get_read_client()
                client_mode = get_read_client_mode()
                st.session_state["_dev_inject_trace"].append(f"_test_supabase_connection: get_read_client() 호출 (mode: {client_mode})")
                
                if client is None:
                    st.warning("⚠️ Supabase 클라이언트 생성 실패")
                    st.caption("→ secrets.toml에 Supabase URL과 anon_key가 설정되어 있는지 확인하세요.")
                    return
                
                # 현재 사용 중인 client 모드 표시
                st.write("**READ CLIENT 모드:**")
                if client_mode == "service_role_dev":
                    st.warning(f"⚠️ **READ CLIENT: service_role_dev** (DEV MODE 전용, RLS 우회)")
                    st.caption("→ use_service_role_dev=true로 설정되어 Service Role Key를 사용 중입니다.")
                    st.caption("→ 프로덕션에서는 절대 사용되지 않습니다.")
                else:
                    st.info(f"ℹ️ **READ CLIENT: anon** (일반 모드)")
                    st.caption("→ Anon Key를 사용 중입니다. RLS 정책이 적용됩니다.")
                
                # 간단한 ping 테스트 (stores 테이블 조회)
                try:
                    result = client.table("stores").select("id").limit(1).execute()
                    st.success(f"✅ 연결 성공: stores 테이블 조회 성공")
                    st.caption(f"테스트 결과: {len(result.data)}건 조회됨")
                    
                    # 실제 사용 중인 store_id 확인
                    from src.auth import get_current_store_id
                    actual_store_id = get_current_store_id()
                    
                    # 핵심 테이블별 상세 진단
                    st.write("---")
                    st.write("**4. 핵심 테이블별 상세 진단:**")
                    
                    # 진단할 테이블 목록
                    tables_to_diagnose = [
                        "daily_close",
                        "menu_master",
                        "ingredients",
                        "inventory",
                        "expense_structure",
                        "sales",
                        "naver_visitors",
                    ]
                    
                    for table_name in tables_to_diagnose:
                        st.write(f"**{table_name} 테이블:**")
                        diagnosis = _diagnose_table(client, table_name, actual_store_id)
                        
                        # 필터 없이 조회 결과
                        if diagnosis["no_filter_success"]:
                            if diagnosis["no_filter_count"] > 0:
                                st.success(f"  ✅ 필터 없이 조회 성공: {diagnosis['no_filter_count']}건")
                            else:
                                st.warning(f"  ⚠️ 필터 없이 조회 성공 but 0건")
                        else:
                            st.error(f"  ❌ 필터 없이 조회 실패: {diagnosis['no_filter_error']}")
                        
                        # store 필터 조회 결과
                        if actual_store_id:
                            if diagnosis["found_store_column"]:
                                if diagnosis["with_filter_success"]:
                                    if diagnosis["with_filter_count"] > 0:
                                        st.success(f"  ✅ store 필터 ({diagnosis['found_store_column']}) 조회 성공: {diagnosis['with_filter_count']}건")
                                    else:
                                        st.warning(f"  ⚠️ store 필터 ({diagnosis['found_store_column']}) 조회 성공 but 0건")
                                else:
                                    st.error(f"  ❌ store 필터 ({diagnosis['found_store_column']}) 조회 실패: {diagnosis['with_filter_error']}")
                            else:
                                st.warning(f"  ⚠️ store 필터 컬럼 찾기 실패")
                                if diagnosis["store_column_candidates"]:
                                    st.caption(f"    시도한 컬럼: {', '.join(diagnosis['store_column_candidates'])}")
                        
                        # 진단 결과
                        if diagnosis["diagnosis"]:
                            if "정상" in diagnosis["diagnosis"]:
                                st.caption(f"  💡 {diagnosis['diagnosis']}")
                            elif diagnosis["diagnosis"].startswith("A)"):
                                st.error(f"  {diagnosis['diagnosis']}")
                            elif diagnosis["diagnosis"].startswith("B)"):
                                st.warning(f"  {diagnosis['diagnosis']}")
                            elif diagnosis["diagnosis"].startswith("C)"):
                                st.error(f"  {diagnosis['diagnosis']}")
                        
                        st.caption("")  # 구분선
                    
                    # 디버그 정보 강화
                    st.write("---")
                    st.write("**🔍 상세 디버그 정보:**")
                    
                    # 디버그: Python 실행 경로 및 주입 타이밍 정보
                    st.write("**0. 환경 정보:**")
                    st.caption(f"  Python 실행 경로: `{sys.executable}`")
                    bootstrap_ran = st.session_state.get("_bootstrap_ran", False)
                    st.caption(f"  bootstrap 실행 여부: `{bootstrap_ran}`")
                    injection_timing = st.session_state.get("_dev_store_id_injected_at", "미확인")
                    st.caption(f"  dev_store_id 주입 타이밍: `{injection_timing}`")
                    
                    # bootstrap 예외 정보
                    bootstrap_exception = st.session_state.get("_bootstrap_exception", None)
                    if bootstrap_exception:
                        st.error(f"  ⚠️ bootstrap 예외 발생: `{bootstrap_exception}`")
                    else:
                        st.caption("  bootstrap 예외 없음")
                    
                    # session_state 키 검증
                    st.write("**0-0. Session State 키 검증:**")
                    all_keys = list(st.session_state.keys())
                    store_related_keys = [k for k in all_keys if "store" in k.lower() or "active" in k.lower()]
                    st.caption(f"  'store' 또는 'active' 포함 키: {store_related_keys}")
                    st.caption(f"  '_active_store_id' 키 존재 여부: {'_active_store_id' in st.session_state}")
                    if "_active_store_id" in st.session_state:
                        active_value = st.session_state.get("_active_store_id")
                        st.caption(f"  '_active_store_id' 값 (get): `{active_value}`")
                        try:
                            active_direct = st.session_state["_active_store_id"]
                            st.caption(f"  '_active_store_id' 값 (직접 접근): `{active_direct}`")
                        except KeyError:
                            st.caption("  '_active_store_id' 직접 접근 실패 (KeyError)")
                    else:
                        st.caption("  '_active_store_id' 키가 존재하지 않음")
                    
                    # 주입 추적 정보 표시
                    st.write("**0-1. 주입 추적 (Trace):**")
                    inject_trace = st.session_state.get("_dev_inject_trace", [])
                    if inject_trace:
                        st.caption(f"  총 {len(inject_trace)}개 이벤트:")
                        for idx, trace_item in enumerate(inject_trace, 1):
                            st.caption(f"    {idx}. {trace_item}")
                    else:
                        st.caption("  추적 이벤트 없음 (주입 함수가 호출되지 않았을 수 있음)")
                    
                    # 주입 직후 스냅샷 표시
                    st.write("**0-2. 주입 직후 스냅샷:**")
                    inject_snapshot = st.session_state.get("_inject_snapshot", None)
                    if inject_snapshot:
                        st.caption(f"  함수: `{inject_snapshot.get('function', 'N/A')}`")
                        st.caption(f"  _active_store_id: `{inject_snapshot.get('_active_store_id', 'N/A')}`")
                        st.caption(f"  _active_store_id_exists: `{inject_snapshot.get('_active_store_id_exists', 'N/A')}`")
                        st.caption(f"  store_id: `{inject_snapshot.get('store_id', 'N/A')}`")
                        st.caption(f"  타이밍: `{inject_snapshot.get('timestamp', 'N/A')}`")
                    else:
                        st.caption("  스냅샷 없음 (주입이 실행되지 않았거나 덮어써졌을 수 있음)")
                    
                    # bootstrap_end 덤프 표시
                    st.write("**0-3. bootstrap_end 시점 덤프 (finally 블록):**")
                    bootstrap_end_dump = st.session_state.get("_bootstrap_end_dump", None)
                    if bootstrap_end_dump:
                        if "error" in bootstrap_end_dump:
                            st.error(f"  덤프 중 예외: `{bootstrap_end_dump['error']}`")
                        else:
                            for key, value in bootstrap_end_dump.items():
                                st.caption(f"  {key}: `{value}`")
                    else:
                        st.caption("  덤프 없음 (bootstrap_end finally 블록이 실행되지 않았을 수 있음)")
                    
                    # 1) 현재 store_id 후보 값 표시
                    st.write("**1. Store ID 후보 값:**")
                    store_id_candidates = {
                        "st.session_state._active_store_id": st.session_state.get("_active_store_id"),
                        "st.session_state.store_id": st.session_state.get("store_id"),
                        "st.session_state.current_store_id": st.session_state.get("current_store_id"),
                        "st.session_state.store_id_widget": st.session_state.get("store_id_widget"),
                    }
                    
                    # dev_store_id도 확인
                    try:
                        dev_store_id = st.secrets.get("app", {}).get("dev_store_id", "")
                        if dev_store_id:
                            store_id_candidates["st.secrets.app.dev_store_id"] = dev_store_id
                    except Exception:
                        dev_store_id = ""
                    
                    for key, value in store_id_candidates.items():
                        if value:
                            st.caption(f"  - {key}: `{value}`")
                        else:
                            st.caption(f"  - {key}: `None`")
                    
                    # dev_store_id 자동 주입 여부 확인
                    try:
                        dev_store_id_from_secrets = st.secrets.get("app", {}).get("dev_store_id", "")
                        current_active_store_id = st.session_state.get('_active_store_id')
                        current_session_store_id = st.session_state.get('store_id')
                        dev_store_id_injected = False
                        
                        if dev_store_id_from_secrets:
                            # dev_store_id가 _active_store_id와 일치하면 주입된 것으로 간주
                            if current_active_store_id == dev_store_id_from_secrets:
                                dev_store_id_injected = True
                    except Exception:
                        dev_store_id_from_secrets = ""
                        dev_store_id_injected = False
                    
                    # 실제 사용 중인 store_id 확인
                    from src.auth import get_current_store_id
                    actual_store_id = get_current_store_id()
                    
                    st.write("**1-1. dev_store_id 자동 주입 여부:**")
                    if dev_store_id_injected:
                        st.success(f"  ✅ dev_store_id가 _active_store_id에 자동 주입됨")
                        st.caption(f"    주입된 값: `{dev_store_id_from_secrets}`")
                    else:
                        if current_active_store_id:
                            st.caption(f"  ℹ️ _active_store_id가 이미 설정되어 있어 주입하지 않음")
                            st.caption(f"    현재 값: `{current_active_store_id}`")
                        elif dev_store_id_from_secrets:
                            st.warning(f"  ⚠️ dev_store_id는 있지만 주입되지 않음")
                            st.caption(f"    dev_store_id: `{dev_store_id_from_secrets}`")
                            st.caption(f"    (bootstrap 단계에서 주입 시도했지만 실패했을 수 있음)")
                        else:
                            st.caption(f"  ℹ️ dev_store_id가 설정되지 않음")
                    
                    st.write("**1-2. 최종 사용 store_id:**")
                    if actual_store_id:
                        st.info(f"  → **최종 store_id:** `{actual_store_id}`")
                        # 어디서 가져온 것인지 표시
                        source_info = []
                        if st.session_state.get('_active_store_id') == actual_store_id:
                            source_info.append("st.session_state._active_store_id (단일 소스)")
                        if st.session_state.get('store_id') == actual_store_id:
                            source_info.append("st.session_state.store_id (레거시)")
                        if st.session_state.get('current_store_id') == actual_store_id:
                            source_info.append("st.session_state.current_store_id")
                        if dev_store_id_from_secrets == actual_store_id:
                            source_info.append("st.secrets.app.dev_store_id")
                        
                        if source_info:
                            st.caption(f"    (출처: {' 또는 '.join(source_info)})")
                    else:
                        st.warning("  → **최종 store_id:** `None`")
                        st.caption("    ⚠️ store_id가 없어 데이터 조회가 실패할 수 있습니다.")
                    
                    # key="store_id" 사용 위젯 검색 결과 표시
                    st.write("**1-3. 위젯/코드 검색 결과:**")
                    st.caption("  `key=\"store_id\"`를 사용하는 위젯: 없음 (검색 결과)")
                    st.caption("  `session_state[\"store_id\"] = ...` 할당 위치:")
                    st.caption("    - src/auth.py: login() 함수 (로그인 시)")
                    st.caption("    - src/auth.py: apply_dev_mode_session() 함수 (DEV MODE)")
                    st.caption("    - src/bootstrap.py: _inject_dev_store_id() 함수")
                    st.caption("    - src/bootstrap.py: _force_inject_dev_store_id_at_bootstrap_end() 함수")
                    
                    # 2) stores 테이블을 필터 없이 select limit 5 실행
                    st.write("**2. Stores 테이블 전체 조회 (필터 없음):**")
                    try:
                        all_stores_result = client.table("stores").select("id, name").limit(5).execute()
                        all_count = len(all_stores_result.data) if all_stores_result.data else 0
                        st.caption(f"  조회 결과: {all_count}건 (limit 5)")
                        
                        if all_stores_result.data:
                            st.caption("  조회된 데이터:")
                            for idx, row in enumerate(all_stores_result.data[:3], 1):  # 최대 3개만 표시
                                row_id = row.get('id', 'N/A')
                                row_name = row.get('name', 'N/A')
                                st.caption(f"    {idx}. id={row_id}, name={row_name}")
                            if len(all_stores_result.data) > 3:
                                st.caption(f"    ... 외 {len(all_stores_result.data) - 3}건")
                    except Exception as e:
                        st.error(f"  ❌ 전체 조회 실패: {str(e)}")
                    
                    # 3) store_id 값이 있으면 필터를 걸어 조회
                    if actual_store_id:
                        st.write(f"**3. Stores 테이블 조회 (store_id={actual_store_id} 필터):**")
                        
                        # 가능한 컬럼명 후보로 시도
                        column_candidates = ['store_id', 'id', 'store_uuid']
                        found_column = None
                        
                        for col_name in column_candidates:
                            try:
                                filtered_result = client.table("stores").select("id, name").eq(col_name, actual_store_id).limit(5).execute()
                                filtered_count = len(filtered_result.data) if filtered_result.data else 0
                                
                                if found_column is None:  # 첫 번째 성공한 컬럼명
                                    found_column = col_name
                                    st.success(f"  ✅ 컬럼명 `{col_name}` 사용 성공")
                                    st.caption(f"  조회 결과: {filtered_count}건 (limit 5)")
                                    
                                    if filtered_result.data:
                                        st.caption("  조회된 데이터:")
                                        for idx, row in enumerate(filtered_result.data, 1):
                                            row_id = row.get('id', 'N/A')
                                            row_name = row.get('name', 'N/A')
                                            st.caption(f"    {idx}. id={row_id}, name={row_name}")
                                    else:
                                        st.warning(f"  ⚠️ `{col_name}={actual_store_id}` 조건으로는 데이터가 없습니다.")
                                        st.caption("  → RLS 정책 또는 store_id 불일치 가능성")
                                else:
                                    st.caption(f"  (컬럼명 `{col_name}`도 시도: {filtered_count}건)")
                                    
                            except Exception as col_error:
                                error_msg = str(col_error)
                                if found_column is None:
                                    st.caption(f"  - 컬럼명 `{col_name}` 시도 실패: {error_msg}")
                                # 컬럼 없음 에러는 정상 (다른 컬럼명일 수 있음)
                                if "column" in error_msg.lower() or "does not exist" in error_msg.lower():
                                    st.caption(f"    → 컬럼 `{col_name}`이 존재하지 않음 (정상)")
                        
                        if found_column is None:
                            st.error("  ❌ 모든 컬럼명 후보 시도 실패")
                            st.caption("  stores 테이블의 ID 컬럼명을 확인하세요.")
                    else:
                        st.write("**3. Stores 테이블 조회 (store_id 필터):**")
                        st.warning("  ⚠️ store_id가 없어 필터 조회를 건너뜁니다.")
                    
                except Exception as e:
                    error_msg = str(e)
                    st.error(f"❌ 연결 실패: 테이블 조회 중 오류 발생")
                    st.caption(f"에러: {error_msg}")
                    
                    # RLS 관련 에러인지 확인
                    if "RLS" in error_msg or "policy" in error_msg.lower() or "permission" in error_msg.lower():
                        st.warning("💡 RLS 정책 문제일 수 있습니다. 로그인 상태를 확인하세요.")
                    elif "JWT" in error_msg or "token" in error_msg.lower():
                        st.warning("💡 인증 토큰 문제일 수 있습니다. 로그인을 다시 시도하세요.")
                    elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                        st.warning("💡 네트워크 연결 문제일 수 있습니다. 인터넷 연결을 확인하세요.")
                    
            except Exception as e:
                st.error(f"❌ Supabase 클라이언트 생성 실패")
                st.caption(f"에러: {str(e)}")
                st.caption("`supabase-py` 패키지가 설치되어 있는지 확인하세요: `pip install supabase`")
                
    except Exception as e:
        logger.warning(f"Supabase 연결 테스트 중 오류: {e}")


def _show_performance_monitor():
    """
    개발모드에서 성능 모니터링 정보 표시 (쿼리 타이밍 로그)
    본문에 표시 (사이드바가 아닌 페이지 본문)
    """
    try:
        from src.storage_supabase import get_query_timing_log
        from src.auth import is_dev_mode
        
        if not is_dev_mode():
            return
        
        # 쿼리 타이밍 로그 표시 (로그가 없어도 expander는 표시)
        query_log = get_query_timing_log()
        with st.expander("⚡ 쿼리 성능 모니터링", expanded=True):
            st.write("**최근 쿼리 실행 로그:**")
            
            # 최근 20개만 표시
            recent_logs = query_log[-20:]
            if recent_logs:
                import pandas as pd
                log_df = pd.DataFrame(recent_logs)
                # timestamp 제거하고 표시
                display_df = log_df[['query_name', 'ms', 'rows']].copy()
                display_df.columns = ['쿼리명', '실행시간 (ms)', '결과 건수']
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # 통계 정보
                total_queries = len(recent_logs)
                total_time = display_df['실행시간 (ms)'].sum()
                avg_time = display_df['실행시간 (ms)'].mean()
                max_time = display_df['실행시간 (ms)'].max()
                
                st.caption(f"**통계:** 총 {total_queries}개 쿼리, 총 {total_time:.2f}ms, 평균 {avg_time:.2f}ms, 최대 {max_time:.2f}ms")
                
                # 느린 쿼리 경고 (100ms 이상)
                slow_queries = display_df[display_df['실행시간 (ms)'] >= 100]
                if not slow_queries.empty:
                    st.warning(f"⚠️ 느린 쿼리 ({len(slow_queries)}개):")
                    for _, row in slow_queries.iterrows():
                        st.caption(f"  - {row['쿼리명']}: {row['실행시간 (ms)']:.2f}ms ({row['결과 건수']}건)")
            else:
                st.caption("쿼리 로그가 없습니다. (아직 쿼리가 실행되지 않았거나 로그가 초기화되었습니다)")
            
            # 로그 초기화 버튼
            if st.button("🗑️ 쿼리 로그 초기화", key="clear_query_log_btn"):
                from src.storage_supabase import clear_query_timing_log
                clear_query_timing_log()
                st.rerun()
            
            # 캐시 우회 토글
            st.markdown("---")
            st.write("**캐시 우회 설정:**")
            bypass_cache = st.checkbox(
                "캐시 무시 (expense_structure 항상 fresh query)",
                value=st.session_state.get("_bypass_cache_expense_structure", False),
                key="bypass_cache_expense_structure_toggle",
                help="체크하면 expense_structure 조회 시 캐시를 우회하고 항상 최신 데이터를 가져옵니다."
            )
            st.session_state["_bypass_cache_expense_structure"] = bypass_cache
            if bypass_cache:
                st.warning("⚠️ 캐시 우회 모드 활성화됨 (성능 저하 가능)")
            else:
                st.caption("ℹ️ 캐시 사용 중 (30초 TTL)")
        
        # 캐시 MISS 로그 표시 (별도 expander)
        try:
            from src.storage_supabase import get_cache_miss_log, clear_cache_miss_log
            cache_miss_log = get_cache_miss_log()
            
            with st.expander("🔍 CACHE DEBUG", expanded=True):
                st.write("**캐시 MISS 로그:**")
                
                if cache_miss_log:
                    # 최근 20개만 표시
                    recent_misses = cache_miss_log[-20:]
                    st.write(f"**최근 캐시 MISS ({len(recent_misses)}개):**")
                    
                    import pandas as pd
                    miss_data = []
                    for miss in recent_misses:
                        params_str = ", ".join([f"{k}={v}" for k, v in miss.get("params", {}).items()])
                        miss_data.append({
                            "함수": miss.get("function", "unknown"),
                            "파라미터": params_str,
                            "시간": pd.Timestamp.fromtimestamp(miss.get("timestamp", 0)).strftime("%H:%M:%S.%f")[:-3]
                        })
                    
                    if miss_data:
                        miss_df = pd.DataFrame(miss_data)
                        st.dataframe(miss_df, use_container_width=True, hide_index=True)
                        
                        # 중복 MISS 경고
                        function_counts = {}
                        for miss in recent_misses:
                            func = miss.get("function", "unknown")
                            params = tuple(sorted(miss.get("params", {}).items()))
                            key = (func, params)
                            function_counts[key] = function_counts.get(key, 0) + 1
                        
                        duplicates = {k: v for k, v in function_counts.items() if v > 1}
                        if duplicates:
                            st.warning(f"⚠️ 동일한 키로 {len(duplicates)}개 이상의 MISS 발생 (캐시가 안 타는 가능성)")
                            for (func, params), count in list(duplicates.items())[:5]:
                                params_str = ", ".join([f"{k}={v}" for k, v in params])
                                st.caption(f"  - {func}({params_str}): {count}회 MISS")
                else:
                    st.caption("캐시 MISS 로그가 없습니다. (모든 조회가 캐시 HIT이거나 아직 조회가 없음)")
                    st.info("💡 **캐시 동작 확인 방법:**\n1. 다른 페이지로 이동하여 데이터를 조회하세요.\n2. 다시 이 페이지로 돌아오면 캐시 MISS 로그가 표시됩니다.\n3. 2회차 조회에서도 MISS가 발생하면 캐시가 작동하지 않는 것입니다.")
                
                # 로그 초기화 버튼
                if st.button("🗑️ 캐시 MISS 로그 초기화", key="clear_cache_miss_log_btn"):
                    clear_cache_miss_log()
                    st.rerun()
        except Exception as e:
            st.error(f"캐시 디버그 정보 로드 실패: {e}")
    except Exception as e:
        logger.warning(f"성능 모니터링 표시 중 오류: {e}")


def preload_common_data():
    """
    세션 시작 시 공통 데이터 프리로딩
    모든 페이지에서 사용하는 데이터를 미리 로드하여 캐시에 저장
    
    세션당 1회만 실행되며, 이후 페이지 진입 시 캐시 HIT가 발생하여 빠른 로딩 가능
    """
    # 세션당 1회만 실행
    if st.session_state.get("preload_done", False):
        return
    
    # 로그인 체크 (store_id 필요)
    try:
        from src.auth import get_current_store_id, is_dev_mode
        store_id = get_current_store_id()
        if not store_id:
            logger.warning("preload_common_data: store_id가 없어 프리로딩을 건너뜁니다.")
            return
    except Exception as e:
        logger.warning(f"preload_common_data: 로그인 체크 실패 - {e}")
        return
    
    # 프리로딩 시작
    import time
    start_time = time.perf_counter()
    
    try:
        # storage 함수 import (순환 참조 방지)
        from src.storage_supabase import load_csv, load_expense_structure
        from src.utils.time_utils import current_year_kst, current_month_kst
        
        # 현재 연도/월 (KST 기준)
        current_year = current_year_kst()
        current_month = current_month_kst()
        
        # 프리로딩 중 UX 표시
        from src.utils.boot_perf import record_db_call
        import time as time_module
        
        with st.spinner("초기 데이터를 준비하는 중..."):
            # 부팅 단계에서는 필수 데이터만 로드 (최소화)
            # 나머지는 각 페이지 진입 시 lazy load
            
            # 1. menu_master (메뉴 마스터) - 필수 (많은 페이지에서 사용)
            try:
                t_start = time_module.perf_counter()
                df = load_csv('menu_master.csv')
                t_end = time_module.perf_counter()
                st.session_state['ss_menu_master_df'] = df
                record_db_call("preload: menu_master", (t_end - t_start) * 1000)
            except Exception as e:
                logger.warning(f"preload: menu_master 로드 실패 - {e}")
            
            # 2. stores (현재 매장 정보) - 필수 (인증/권한 체크용)
            try:
                t_start = time_module.perf_counter()
                from src.auth import get_supabase_client
                supabase = get_supabase_client()
                if supabase:
                    supabase.table("stores").select("id,name").eq("id", store_id).limit(1).execute()
                t_end = time_module.perf_counter()
                record_db_call("preload: stores", (t_end - t_start) * 1000)
            except Exception as e:
                logger.warning(f"preload: stores 조회 실패 - {e}")
            
            # 나머지 데이터는 각 페이지 진입 시 lazy load로 이동
            # - ingredient_master: 재료 등록/레시피 등록 페이지에서만 필요
            # - inventory: 발주 관리 페이지에서만 필요
            # - recipes: 레시피 등록/원가 파악 페이지에서만 필요
            # - expense_structure: 비용구조/실제정산 페이지에서만 필요
            # - targets: 목표 설정 페이지에서만 필요
        
        # 프리로딩 완료 플래그 설정
        st.session_state["preload_done"] = True
        
        # 개발모드에서 시간 출력
        elapsed_time = time.perf_counter() - start_time
        if is_dev_mode():
            logger.info(f"✅ 프리로드 완료: {elapsed_time:.3f}초")
            # 개발모드에서는 콘솔에만 출력 (화면에는 표시하지 않음)
        
    except Exception as e:
        logger.error(f"preload_common_data: 프리로딩 중 오류 - {e}")
        # 오류가 발생해도 플래그는 설정하여 재시도 방지
        st.session_state["preload_done"] = True
