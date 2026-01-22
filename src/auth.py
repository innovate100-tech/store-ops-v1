"""
Supabase 인증 모듈
로그인/로그아웃/세션 관리
"""
import streamlit as st
import logging
import os
import traceback

try:
    from supabase import create_client, Client
    from typing import Optional
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    from typing import Optional

logger = logging.getLogger(__name__)


@st.cache_resource(show_spinner=False)
def get_anon_client() -> Optional[Client]:
    """
    Supabase 익명 클라이언트 생성 (토큰/로그인 상태 체크 없음)
    
    - st.secrets["supabase"]["url"] + st.secrets["supabase"]["anon_key"] 우선 사용
    - 없으면 os.getenv("SUPABASE_URL") / os.getenv("SUPABASE_ANON_KEY") fallback
    - 토큰/로그인 상태 체크 금지
    - clear_session 호출 금지
    - 데이터진단 및 단순 조회 테스트용
    
    Returns:
        Supabase Client 또는 None (설정 오류 시)
    """
    if not SUPABASE_AVAILABLE:
        logger.error("get_anon_client: supabase-py 패키지가 설치되지 않음")
        return None
    
    try:
        # Supabase URL과 anon key 가져오기 (st.secrets 우선, 없으면 os.getenv fallback)
        try:
            url = st.secrets["supabase"]["url"]
            anon_key = st.secrets["supabase"]["anon_key"]
            logger.info("get_anon_client: st.secrets에서 설정 로드 성공")
        except (KeyError, AttributeError):
            # st.secrets에 없으면 os.getenv로 fallback
            url = os.getenv("SUPABASE_URL", "")
            anon_key = os.getenv("SUPABASE_ANON_KEY", "")
            if url and anon_key:
                logger.info("get_anon_client: os.getenv에서 설정 로드 성공 (fallback)")
            else:
                logger.error("get_anon_client: secrets 및 환경변수 모두 로딩 실패")
                return None
        
        if not url or not anon_key:
            logger.error("get_anon_client: url 또는 anon_key가 비어있음")
            return None
        
        # 캐시 키 로깅 (디버깅용)
        logger.info(f"get_anon_client: 캐시 키 (url={url[:20]}..., key={anon_key[:10]}..., mode=anon)")
        
        # 클라이언트 생성 (토큰 설정 없음)
        client = create_client(url, anon_key)
        logger.info("get_anon_client: 익명 클라이언트 생성 성공 (캐시됨)")
        return client
        
    except Exception as e:
        logger.error(f"get_anon_client: 클라이언트 생성 실패 - {repr(e)}")
        # 상세 디버그 정보 출력
        st.error(f"❌ Supabase 익명 클라이언트 생성 실패: {type(e).__name__}: {e}")
        st.code(traceback.format_exc(), language="python")
        
        # 디버그 정보 (값 노출 없이)
        debug_info = {
            "has_secrets_supabase": "supabase" in st.secrets if hasattr(st, 'secrets') else False,
            "has_url": ("supabase" in st.secrets and "url" in st.secrets["supabase"]) if (hasattr(st, 'secrets') and "supabase" in st.secrets) else False,
            "has_anon_key": ("supabase" in st.secrets and "anon_key" in st.secrets["supabase"]) if (hasattr(st, 'secrets') and "supabase" in st.secrets) else False,
            "url_starts_https": str(url).startswith("https://") if url else False,
            "url_len": len(str(url)) if url else 0,
            "anon_key_len": len(str(anon_key)) if anon_key else 0,
            "has_env_url": bool(os.getenv("SUPABASE_URL")),
            "has_env_anon_key": bool(os.getenv("SUPABASE_ANON_KEY")),
        }
        st.write("**디버그 정보:**")
        st.json(debug_info)
        st.stop()
        return None


@st.cache_resource(show_spinner=False)
def get_service_client() -> Optional[Client]:
    """
    Supabase Service Role 클라이언트 생성 (RLS 우회, DEV MODE 전용)
    
    ⚠️ 보안 경고: Service Role Key는 RLS를 우회하므로 프로덕션에서는 절대 사용 금지!
    
    - st.secrets["supabase"]["url"] + st.secrets["supabase"]["service_role_key"] 우선 사용
    - 없으면 os.getenv("SUPABASE_URL") / os.getenv("SUPABASE_SERVICE_ROLE_KEY") fallback
    - RLS 정책을 우회하여 모든 데이터 접근 가능
    - DEV MODE에서만 사용 (로컬 개발 전용)
    
    Returns:
        Supabase Client 또는 None (설정 오류 또는 프로덕션 환경 시)
    """
    if not SUPABASE_AVAILABLE:
        logger.error("get_service_client: supabase-py 패키지가 설치되지 않음")
        return None
    
    # 프로덕션 환경 체크
    if os.getenv('STREAMLIT_SERVER_ENVIRONMENT') == 'production':
        logger.error("get_service_client: 프로덕션 환경에서는 service_role_key 사용 금지")
        return None
    
    # DEV MODE 체크
    if not is_dev_mode():
        logger.error("get_service_client: DEV MODE가 아니면 service_role_key 사용 금지")
        return None
    
    try:
        # Supabase URL과 service_role_key 가져오기 (st.secrets 우선, 없으면 os.getenv fallback)
        try:
            url = st.secrets["supabase"]["url"]
            service_role_key = st.secrets["supabase"]["service_role_key"]
            logger.info("get_service_client: st.secrets에서 설정 로드 성공")
        except (KeyError, AttributeError):
            # st.secrets에 없으면 os.getenv로 fallback
            url = os.getenv("SUPABASE_URL", "")
            service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
            if url and service_role_key:
                logger.info("get_service_client: os.getenv에서 설정 로드 성공 (fallback)")
            else:
                logger.warning("get_service_client: secrets 및 환경변수 모두 로딩 실패 - url 또는 service_role_key가 없음")
                return None
        
        if not url or not service_role_key:
            logger.warning("get_service_client: url 또는 service_role_key가 비어있음")
            return None
        
        # 캐시 키 로깅 (디버깅용)
        logger.info(f"get_service_client: 캐시 키 (url={url[:20]}..., key={service_role_key[:10]}..., mode=service_role)")
        
        # 클라이언트 생성
        client = create_client(url, service_role_key)
        logger.info("get_service_client: Service Role 클라이언트 생성 성공 (DEV MODE, 캐시됨)")
        return client
        
    except Exception as e:
        logger.error(f"get_service_client: 클라이언트 생성 실패 - {repr(e)}")
        # 상세 디버그 정보 출력
        st.error(f"❌ Supabase Service Role 클라이언트 생성 실패: {type(e).__name__}: {e}")
        st.code(traceback.format_exc(), language="python")
        
        # 디버그 정보 (값 노출 없이)
        debug_info = {
            "has_secrets_supabase": "supabase" in st.secrets if hasattr(st, 'secrets') else False,
            "has_url": ("supabase" in st.secrets and "url" in st.secrets["supabase"]) if (hasattr(st, 'secrets') and "supabase" in st.secrets) else False,
            "has_service_role_key": ("supabase" in st.secrets and "service_role_key" in st.secrets["supabase"]) if (hasattr(st, 'secrets') and "supabase" in st.secrets) else False,
            "url_starts_https": str(url).startswith("https://") if url else False,
            "url_len": len(str(url)) if url else 0,
            "service_role_key_len": len(str(service_role_key)) if service_role_key else 0,
            "has_env_url": bool(os.getenv("SUPABASE_URL")),
            "has_env_service_role_key": bool(os.getenv("SUPABASE_SERVICE_ROLE_KEY")),
        }
        st.write("**디버그 정보:**")
        st.json(debug_info)
        st.stop()
        return None


def get_read_client() -> Optional[Client]:
    """
    데이터 조회용 클라이언트 생성 (읽기 전용)
    
    우선순위:
    1. DEV MODE && use_service_role_dev=true && service_role_key 존재 → Service Role Client
    2. 그 외 → Anon Client
    
    ⚠️ 보안: 프로덕션에서는 항상 anon client만 사용됩니다.
    
    Returns:
        Supabase Client (Service Role 또는 Anon) 또는 None
    """
    # DEV MODE에서 service_role_key 사용 옵션 확인
    use_service_role = False
    if is_dev_mode():
        try:
            app_config = st.secrets.get("app", {})
            use_service_role = app_config.get("use_service_role_dev", False)
        except Exception:
            use_service_role = False
    
    # Service Role Client 사용 조건:
    # 1. DEV MODE
    # 2. use_service_role_dev = true
    # 3. service_role_key 존재
    if use_service_role:
        service_client = get_service_client()
        if service_client:
            logger.info("get_read_client: Service Role Client 사용 (DEV MODE)")
            return service_client
        else:
            logger.warning("get_read_client: Service Role Client 생성 실패, Anon Client로 대체")
    
    # 기본: Anon Client
    logger.info("get_read_client: Anon Client 사용")
    return get_anon_client()


def get_read_client_mode() -> str:
    """
    현재 사용 중인 read client 모드 반환 (디버깅용)
    
    Returns:
        "anon" 또는 "service_role_dev"
    """
    # DEV MODE에서 service_role_key 사용 옵션 확인
    use_service_role = False
    if is_dev_mode():
        try:
            app_config = st.secrets.get("app", {})
            use_service_role = app_config.get("use_service_role_dev", False)
        except Exception:
            use_service_role = False
    
    if use_service_role:
        # service_role_key 존재 여부 확인
        try:
            supabase_config = st.secrets.get("supabase", {})
            service_role_key = supabase_config.get("service_role_key", "")
            if service_role_key:
                return "service_role_dev"
        except Exception:
            pass
    
    return "anon"


@st.cache_resource(show_spinner=False)
def get_auth_client(reset_session_on_fail: bool = True) -> Optional[Client]:
    """
    Supabase 인증 클라이언트 생성 (로그인 세션 필요)
    
    - st.secrets["supabase"]["url"] + st.secrets["supabase"]["anon_key"] 우선 사용
    - 없으면 os.getenv("SUPABASE_URL") / os.getenv("SUPABASE_ANON_KEY") fallback
    - 로그인 세션(토큰)이 있을 때만 생성
    - 없으면 None 반환 (예외 발생 안 함)
    
    Args:
        reset_session_on_fail: 세션 설정 실패 시 clear_session() 호출 여부 (기본값: True)
    
    Returns:
        Supabase Client 또는 None (DEV MODE 또는 로그인 없음)
    """
    # DEV MODE일 때는 None 반환 (예외 발생 안 함)
    if st.session_state.get('dev_mode', False):
        logger.info("get_auth_client: DEV MODE - None 반환")
        return None
    
    if not SUPABASE_AVAILABLE:
        logger.error("get_auth_client: supabase-py 패키지가 설치되지 않음")
        error_msg = "❌ Supabase 클라이언트 생성 실패\n\n"
        error_msg += "`supabase-py` 패키지가 설치되지 않았습니다.\n\n"
        error_msg += "다음 명령어로 설치하세요:\n"
        error_msg += "```bash\npip install supabase\n```"
        st.error(error_msg)
        st.stop()
        return None
    
    # Supabase URL과 anon key 가져오기 (st.secrets 우선, 없으면 os.getenv fallback)
    try:
        url = st.secrets["supabase"]["url"]
        anon_key = st.secrets["supabase"]["anon_key"]
        logger.info("get_auth_client: st.secrets에서 설정 로드 성공")
    except (KeyError, AttributeError):
        # st.secrets에 없으면 os.getenv로 fallback
        url = os.getenv("SUPABASE_URL", "")
        anon_key = os.getenv("SUPABASE_ANON_KEY", "")
        if url and anon_key:
            logger.info("get_auth_client: os.getenv에서 설정 로드 성공 (fallback)")
        else:
            logger.error("get_auth_client: secrets 및 환경변수 모두 로딩 실패 - url 또는 anon_key가 없음")
            error_msg = "❌ Supabase 클라이언트 생성 실패\n\n"
            error_msg += "Supabase URL 또는 anon_key가 설정되지 않았습니다.\n\n"
            error_msg += "**Streamlit Secrets 설정 방법:**\n"
            error_msg += "`.streamlit/secrets.toml` 파일에 다음 형식으로 설정하세요:\n"
            error_msg += "```toml\n"
            error_msg += "[supabase]\n"
            error_msg += "url = \"https://your-project.supabase.co\"\n"
            error_msg += "anon_key = \"your-anon-key-here\"\n"
            error_msg += "```\n\n"
            error_msg += "**또는 환경변수 설정:**\n"
            error_msg += "```bash\n"
            error_msg += "export SUPABASE_URL=\"https://your-project.supabase.co\"\n"
            error_msg += "export SUPABASE_ANON_KEY=\"your-anon-key-here\"\n"
            error_msg += "```"
            st.error(error_msg)
            st.stop()
            return None
    
    if not url or not anon_key:
        logger.error("get_auth_client: url 또는 anon_key가 비어있음")
        error_msg = "❌ Supabase 클라이언트 생성 실패\n\n"
        error_msg += "Supabase URL 또는 anon_key가 비어있습니다.\n\n"
        error_msg += "`.streamlit/secrets.toml` 파일 또는 환경변수를 확인하세요."
        st.error(error_msg)
        st.stop()
        return None
    
    # 클라이언트 생성
    try:
        # 캐시 키 로깅 (디버깅용)
        access_token_hash = hash(st.session_state.get('access_token', '')) if 'access_token' in st.session_state else None
        logger.info(f"get_auth_client: 캐시 키 (url={url[:20]}..., key={anon_key[:10]}..., mode=auth, token_hash={access_token_hash})")
        
        client = create_client(url, anon_key)
        logger.info("get_auth_client: 클라이언트 생성 성공 (캐시됨)")
    except Exception as e:
        logger.error(f"get_auth_client: 클라이언트 생성 실패 - {repr(e)}")
        # 상세 디버그 정보 출력
        st.error(f"❌ Supabase 인증 클라이언트 생성 실패: {type(e).__name__}: {e}")
        st.code(traceback.format_exc(), language="python")
        
        # 디버그 정보 (값 노출 없이)
        debug_info = {
            "has_secrets_supabase": "supabase" in st.secrets if hasattr(st, 'secrets') else False,
            "has_url": ("supabase" in st.secrets and "url" in st.secrets["supabase"]) if (hasattr(st, 'secrets') and "supabase" in st.secrets) else False,
            "has_anon_key": ("supabase" in st.secrets and "anon_key" in st.secrets["supabase"]) if (hasattr(st, 'secrets') and "supabase" in st.secrets) else False,
            "url_starts_https": str(url).startswith("https://") if url else False,
            "url_len": len(str(url)) if url else 0,
            "anon_key_len": len(str(anon_key)) if anon_key else 0,
            "has_env_url": bool(os.getenv("SUPABASE_URL")),
            "has_env_anon_key": bool(os.getenv("SUPABASE_ANON_KEY")),
        }
        st.write("**디버그 정보:**")
        st.json(debug_info)
        st.stop()
        return None
    
    # 세션에 access_token이 있으면 설정
    if 'access_token' in st.session_state:
        access_token = st.session_state.access_token
        if access_token:
            try:
                refresh_token = st.session_state.get('refresh_token', '')
                if refresh_token:
                    client.auth.set_session(
                        access_token=access_token,
                        refresh_token=refresh_token
                    )
                    logger.info("get_auth_client: 세션 설정 성공 (refresh_token 있음)")
                else:
                    # refresh_token이 없으면 access_token만 설정 시도
                    try:
                        client.auth.set_session(
                            access_token=access_token,
                            refresh_token=''
                        )
                        logger.info("get_auth_client: 세션 설정 성공 (refresh_token 없음)")
                    except Exception:
                        # 세션 설정 실패 시 세션 정보 초기화 (옵션)
                        logger.warning("get_auth_client: 세션 설정 실패 (refresh_token 없음)")
                        if reset_session_on_fail:
                            clear_session(reason="get_auth_client: 세션 설정 실패 (refresh_token 없음)")
                        else:
                            logger.warning("reset_session_on_fail=False: 세션 초기화 건너뜀")
            except Exception as e:
                # 세션 설정 중 에러 발생 시 (토큰 만료 등)
                logger.warning(f"get_auth_client: 세션 설정 중 오류 발생 - {repr(e)}")
                # 세션 정보 초기화하여 재로그인 유도 (옵션)
                if reset_session_on_fail:
                    clear_session(reason=f"get_auth_client: 세션 설정 중 오류 - {str(e)}")
                else:
                    logger.warning("reset_session_on_fail=False: 세션 초기화 건너뜀")
                # 에러를 다시 발생시키지 않고 클라이언트만 반환 (재로그인 필요)
                pass
    else:
        logger.warning("get_auth_client: 토큰 없음 - 로그인 필요")
        return None
    
    return client


def get_supabase_client(reset_session_on_fail: bool = True) -> Optional[Client]:
    """
    Supabase 클라이언트 생성 (레거시 호환 - get_auth_client()로 위임)
    
    Args:
        reset_session_on_fail: 세션 설정 실패 시 clear_session() 호출 여부 (기본값: True)
    
    Returns:
        Supabase Client 또는 None (DEV MODE일 때)
    """
    return get_auth_client(reset_session_on_fail=reset_session_on_fail)


def check_login() -> bool:
    """
    로그인 상태 확인
    
    Returns:
        bool: 로그인 여부
    """
    # 세션에 user_id와 access_token이 있으면 로그인 상태
    if 'user_id' in st.session_state and 'access_token' in st.session_state:
        # access_token이 있으면 로그인된 것으로 간주
        # (실제 검증은 Supabase RLS에서 처리됨)
        return True
    
    return False


def login(email: str, password: str) -> tuple[bool, str]:
    """
    로그인 실행
    
    Args:
        email: 사용자 이메일
        password: 비밀번호
    
    Returns:
        tuple: (성공 여부, 메시지)
    """
    try:
        client = get_supabase_client()
        
        # client 생성 실패 시 방어 코드
        if client is None:
            st.error("❌ Supabase 클라이언트를 생성할 수 없습니다.")
            
            # 디버그 정보 출력
            try:
                url = st.secrets["supabase"]["url"] if (hasattr(st, 'secrets') and "supabase" in st.secrets and "url" in st.secrets["supabase"]) else os.getenv("SUPABASE_URL", "")
                anon_key = st.secrets["supabase"]["anon_key"] if (hasattr(st, 'secrets') and "supabase" in st.secrets and "anon_key" in st.secrets["supabase"]) else os.getenv("SUPABASE_ANON_KEY", "")
            except (KeyError, AttributeError):
                url = os.getenv("SUPABASE_URL", "")
                anon_key = os.getenv("SUPABASE_ANON_KEY", "")
            
            debug_info = {
                "has_secrets_supabase": "supabase" in st.secrets if hasattr(st, 'secrets') else False,
                "has_url": ("supabase" in st.secrets and "url" in st.secrets["supabase"]) if (hasattr(st, 'secrets') and "supabase" in st.secrets) else False,
                "has_anon_key": ("supabase" in st.secrets and "anon_key" in st.secrets["supabase"]) if (hasattr(st, 'secrets') and "supabase" in st.secrets) else False,
                "url_starts_https": str(url).startswith("https://") if url else False,
                "url_len": len(str(url)) if url else 0,
                "anon_key_len": len(str(anon_key)) if anon_key else 0,
                "has_env_url": bool(os.getenv("SUPABASE_URL")),
                "has_env_anon_key": bool(os.getenv("SUPABASE_ANON_KEY")),
                "SUPABASE_AVAILABLE": SUPABASE_AVAILABLE,
            }
            st.write("**디버그 정보:**")
            st.json(debug_info)
            st.write("\n**get_auth_client()가 None을 반환했습니다.**")
            st.write("위의 디버그 정보를 확인하고, Supabase 설정을 점검하세요.")
            st.stop()
            return False, "Supabase 클라이언트 생성 실패"
        
        # 로그인 시도
        response = client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            # 세션에 정보 저장
            st.session_state.user_id = response.user.id
            st.session_state.access_token = response.session.access_token
            st.session_state.refresh_token = response.session.refresh_token
            
            # user_profiles에서 store_id 확인
            profile_result = client.table("user_profiles").select("store_id, role").eq("id", response.user.id).execute()
            
            if not profile_result.data:
                return False, "사용자 프로필이 설정되지 않았습니다. 관리자에게 문의하세요."
            
            store_id = profile_result.data[0].get('store_id')
            if not store_id:
                return False, "매장이 연결되지 않았습니다. 관리자에게 문의하세요."
            
            st.session_state.store_id = store_id  # 레거시 호환
            st.session_state._active_store_id = store_id  # 단일 소스 오브 트루스
            st.session_state.user_role = profile_result.data[0].get('role', 'manager')
            
            logger.info(f"User logged in: {email} (store_id: {store_id})")
            return True, "로그인 성공"
        else:
            return False, "로그인에 실패했습니다."
    
    except Exception as e:
        logger.error(f"Login error: {e}")
        error_msg = str(e)
        if "Invalid login credentials" in error_msg:
            return False, "이메일 또는 비밀번호가 올바르지 않습니다."
        elif "Email not confirmed" in error_msg:
            return False, "이메일 인증이 필요합니다."
        else:
            return False, f"로그인 오류: {error_msg}"


def logout():
    """로그아웃 실행"""
    try:
        client = get_supabase_client()
        if client:  # DEV MODE일 때는 None이므로 체크
            client.auth.sign_out()
    except Exception as e:
        logger.warning(f"Logout error (non-critical): {e}")
    finally:
        clear_session(reason="logout: 사용자 로그아웃")


def clear_session(reason: str = "unknown"):
    """
    세션 정보 정리
    
    Args:
        reason: clear_session() 호출 이유 (디버깅용)
    """
    # DEV MODE에서는 clear_session() 호출을 경고만 남기고 실제 삭제는 하지 않음
    # (디버그 ping 등이 세션을 지우는 것을 방지)
    if st.session_state.get('dev_mode', False):
        logger.warning(f"DEV MODE: clear_session() 호출 차단됨 (reason: {reason})")
        # clear_session() 호출 추적 (dev_mode에서는 실제 삭제 안 함)
        if "_dev_inject_trace" in st.session_state:
            st.session_state["_dev_inject_trace"].append(f"clear_session() 호출 차단됨 (DEV MODE) - reason: {reason}")
        return
    
    # clear_session() 호출 추적
    if "_dev_inject_trace" in st.session_state:
        import traceback
        call_stack = ''.join(traceback.format_stack()[-3:-1])  # 호출 스택 일부만
        st.session_state["_dev_inject_trace"].append(f"clear_session() 호출됨 - reason: {reason}, 스택: {call_stack[:200]}")
    
    if 'user_id' in st.session_state:
        del st.session_state.user_id
    if 'access_token' in st.session_state:
        del st.session_state.access_token
    if 'refresh_token' in st.session_state:
        del st.session_state.refresh_token
    if 'store_id' in st.session_state:
        del st.session_state.store_id
    if '_active_store_id' in st.session_state:
        del st.session_state._active_store_id
    if 'user_role' in st.session_state:
        del st.session_state.user_role


def apply_dev_mode_session():
    """
    DEV MODE 세션 설정
    로컬 개발 시 로그인 없이 앱을 사용하기 위한 더미 세션 값 설정
    
    ⚠️ 프로덕션 환경에서는 자동으로 비활성화됩니다.
    ⚠️ 세션당 1회만 실행 (플래그로 보호)
    
    Returns:
        bool: DEV MODE 활성화 여부
    """
    # 세션당 1회만 실행
    if st.session_state.get("_dev_mode_applied", False):
        return st.session_state.get("dev_mode", False)
    
    try:
        # 프로덕션 환경 체크
        import os
        # Streamlit Cloud 환경 변수 체크
        if os.getenv('STREAMLIT_SERVER_ENVIRONMENT') == 'production':
            logger.info("프로덕션 환경 감지: DEV MODE 비활성화")
            st.session_state["_dev_mode_applied"] = True
            return False
        
        # 로컬 환경에서만 DEV MODE 허용
        dev_mode = st.secrets.get("app", {}).get("dev_mode", False)
        
        if dev_mode:
            dev_store_id = st.secrets.get("app", {}).get("dev_store_id", "")
            
            if not dev_store_id:
                # bootstrap 내부에서 st.stop() 호출 금지 - 에러만 표시
                st.error("""
                **DEV MODE 오류:**
                
                `.streamlit/secrets.toml` 파일에 `dev_store_id`가 설정되지 않았습니다.
                
                다음과 같이 설정하세요:
                ```toml
                [app]
                dev_mode = true
                dev_store_id = "your-store-id-here"
                ```
                """)
                # st.stop() 대신 False 반환 (bootstrap이 끝까지 실행되도록)
                logger.error("DEV MODE: dev_store_id가 설정되지 않음")
                return False
            
            # DEV MODE 세션 값 설정
            st.session_state.user_id = "dev-user"
            st.session_state.access_token = "dev"
            st.session_state.refresh_token = "dev"
            st.session_state.store_id = dev_store_id  # 레거시 호환
            st.session_state._active_store_id = dev_store_id  # 단일 소스 오브 트루스
            st.session_state.user_role = "manager"
            st.session_state.dev_mode = True
            st.session_state["_dev_mode_applied"] = True  # 플래그 설정
            
            # auto_login_dev 옵션 확인 (새로고침 시 자동 로그인)
            auto_login = st.secrets.get("app", {}).get("auto_login_dev", True)  # 기본값: True
            if auto_login:
                st.session_state["_auto_logged_in"] = True
            
            logger.info(f"DEV MODE activated (store_id: {dev_store_id}, auto_login_dev: {auto_login})")
            return True
        
        return False
    except Exception as e:
        logger.warning(f"DEV MODE check failed: {e}")
        return False


def is_dev_mode() -> bool:
    """DEV MODE 여부 확인"""
    return st.session_state.get('dev_mode', False)


def get_current_store_id() -> str:
    """
    현재 로그인한 사용자의 store_id 반환
    
    우선순위:
    1. st.session_state["_active_store_id"] (단일 소스 오브 트루스)
    2. st.session_state["store_id"] (레거시 호환)
    3. st.session_state["current_store_id"]
    4. (dev_mode일 때만) st.secrets["app"]["dev_store_id"]
    
    dev_mode에서 _active_store_id가 None이면 자동으로 dev_store_id를 주입합니다.
    
    Returns:
        str: store_id (UUID) 또는 None
    """
    # 우선순위 1: st.session_state["_active_store_id"] (단일 소스 오브 트루스)
    store_id = st.session_state.get('_active_store_id')
    if store_id:
        return store_id
    
    # 우선순위 2: st.session_state["store_id"] (레거시 호환)
    store_id = st.session_state.get('store_id')
    if store_id:
        return store_id
    
    # 우선순위 3: st.session_state["current_store_id"]
    store_id = st.session_state.get('current_store_id')
    if store_id:
        return store_id
    
    # 우선순위 4: (dev_mode일 때만) st.secrets["app"]["dev_store_id"]
    if is_dev_mode():
        try:
            dev_store_id = st.secrets.get("app", {}).get("dev_store_id", "")
            if dev_store_id:
                # _active_store_id가 None이면 강제 주입 (bootstrap 호출 누락 대비)
                if not st.session_state.get('_active_store_id'):
                    st.session_state["_active_store_id"] = dev_store_id  # 단일 소스 오브 트루스
                    st.session_state["store_id"] = dev_store_id  # 레거시 호환
                    st.session_state["_dev_store_id_injected_at"] = "get_current_store_id"
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"DEV MODE: dev_store_id 강제 주입됨 (get_current_store_id): {dev_store_id}")
                return dev_store_id
        except Exception:
            pass
    
    return None


def ensure_store_context():
    """
    Store 컨텍스트 가드: store_id가 없으면 명확히 차단
    
    - dev_mode: st.warning + 필요한 설정 안내
    - prod_mode: st.error + st.stop()
    
    Returns:
        str: store_id (있으면), None (없으면)
    """
    store_id = get_current_store_id()
    
    if not store_id:
        if is_dev_mode():
            st.warning("""
            **⚠️ Store 컨텍스트 없음 (DEV MODE)**
            
            `.streamlit/secrets.toml` 파일에 다음을 설정하세요:
            ```toml
            [app]
            dev_mode = true
            dev_store_id = "your-store-id-here"
            ```
            
            또는 로그인하여 store_id를 설정하세요.
            """)
        else:
            st.error("""
            **❌ Store 컨텍스트 없음**
            
            로그인이 필요합니다. 페이지를 새로고침하거나 로그인 페이지로 이동하세요.
            """)
            st.stop()
    
    return store_id


def get_current_store_name() -> str:
    """
    현재 로그인한 사용자의 매장명 반환
    세션 캐시 사용으로 DB 조회 최소화
    
    Returns:
        str: 매장명
    """
    # 세션 캐시 확인
    if '_cached_store_name' in st.session_state:
        return st.session_state['_cached_store_name']
    
    # DEV MODE일 때는 Supabase를 호출하지 않고 기본값 반환
    if is_dev_mode():
        store_name = "DEV MODE (로컬 개발)"
        st.session_state['_cached_store_name'] = store_name
        return store_name
    
    store_id = get_current_store_id()
    if not store_id:
        store_name = "매장 정보 없음"
        st.session_state['_cached_store_name'] = store_name
        return store_name
    
    try:
        client = get_supabase_client()
        result = client.table("stores").select("name").eq("id", store_id).execute()
        
        if result.data:
            store_name = result.data[0]['name']
        else:
            store_name = "매장 정보 없음"
        
        # 세션 캐시에 저장
        st.session_state['_cached_store_name'] = store_name
        return store_name
    except Exception as e:
        logger.error(f"Failed to get store name: {e}")
        store_name = "매장 정보 없음"
        st.session_state['_cached_store_name'] = store_name
        return store_name


def show_login_page():
    """
    로그인 페이지 UI 표시
    """
    # st.set_page_config()는 이미 app.py에서 호출되었으므로 제거
    # 로그인 페이지는 layout="centered"로 표시하기 위해 컨테이너 사용
    
    st.markdown("""
    <style>
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
        }
        .login-header {
            text-align: center;
            margin-bottom: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-header">', unsafe_allow_html=True)
    st.title("🏪 매장 운영 시스템")
    st.markdown("</div>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        email = st.text_input("이메일", placeholder="example@email.com")
        password = st.text_input("비밀번호", type="password")
        submit_button = st.form_submit_button("로그인", type="primary", use_container_width=True)
        
        if submit_button:
            if not email or not password:
                st.error("이메일과 비밀번호를 모두 입력해주세요.")
            else:
                success, message = login(email, password)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 도움말
    with st.expander("도움말"):
        st.info("""
        **로그인이 안 되나요?**
        
        1. Supabase에서 사용자 계정이 생성되어 있는지 확인
        2. user_profiles 테이블에 프로필이 등록되어 있는지 확인
        3. store_id가 올바르게 연결되어 있는지 확인
        
        관리자에게 문의하세요.
        """)
