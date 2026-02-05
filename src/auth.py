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


@st.cache_resource(show_spinner=False)
def get_read_client() -> Optional[Client]:
    """
    데이터 조회용 클라이언트 생성 (읽기 전용)
    
    우선순위:
    1. DEV MODE && use_service_role_dev=true && service_role_key 존재 → Service Role Client
    2. 로그인 토큰이 있으면 → Auth Client (토큰 설정됨)
    3. 그 외 → Anon Client
    
    ⚠️ 보안: 프로덕션에서는 항상 anon client만 사용됩니다.
    ⚠️ 중요: 로그인된 사용자의 경우 토큰이 자동으로 설정되어 RLS 정책이 적용됩니다.
    ⚠️ 캐시: 토큰이 캐시 키에 포함되어 토큰 변경 시 새 클라이언트가 생성됩니다.
    
    Returns:
        Supabase Client (Service Role / Auth / Anon) 또는 None
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
            logger.warning("get_read_client: Service Role Client 생성 실패, Auth/Anon Client로 대체")
    
    # 로그인 토큰이 있으면 Auth Client 사용 (토큰이 설정되어 RLS 정책 적용)
    # 단일화된 조건: token + user_id 모두 존재
    has_token = 'access_token' in st.session_state and bool(st.session_state.get('access_token'))
    has_user_id = 'user_id' in st.session_state and bool(st.session_state.get('user_id'))
    
    if has_token and has_user_id:
        try:
            auth_client = get_auth_client(reset_session_on_fail=False)
            logger.info("get_read_client: Auth Client 사용 (로그인 토큰 설정됨)")
            return auth_client
        except Exception as e:
            logger.warning(f"get_read_client: Auth Client 생성 실패, Anon Client로 대체 - {e}")
    
    # 기본: Anon Client (토큰 없음)
    logger.info("get_read_client: Anon Client 사용 (토큰 없음)")
    return get_anon_client()


def get_read_client_mode() -> str:
    """
    현재 사용 중인 read client 모드 반환 (디버깅용)
    
    Returns:
        "anon", "auth", 또는 "service_role_dev"
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
    
    # 로그인 토큰이 있으면 "auth" 반환 (단일화된 조건: token + user_id 모두 존재)
    has_token = 'access_token' in st.session_state and bool(st.session_state.get('access_token'))
    has_user_id = 'user_id' in st.session_state and bool(st.session_state.get('user_id'))
    
    if has_token and has_user_id:
        return "auth"
    
    return "anon"


@st.cache_resource(show_spinner=False)
def get_auth_client(reset_session_on_fail: bool = True) -> Client:
    """
    Supabase 인증 클라이언트 생성
    
    - st.secrets["supabase"]["url"] + st.secrets["supabase"]["anon_key"] 우선 사용
    - 없으면 os.getenv("SUPABASE_URL") / os.getenv("SUPABASE_ANON_KEY") fallback
    - 클라이언트는 항상 생성하여 반환 (토큰 체크는 별도 함수에서 처리)
    - 실패 시 예외를 상세히 출력하고 st.stop()
    
    Args:
        reset_session_on_fail: 세션 설정 실패 시 clear_session() 호출 여부 (기본값: True)
    
    Returns:
        Supabase Client (절대 None 반환 안 함)
    """
    # DEV MODE일 때도 클라이언트는 생성 (토큰 체크는 별도 처리)
    if st.session_state.get('dev_mode', False):
        logger.info("get_auth_client: DEV MODE - 클라이언트 생성 (토큰 체크는 별도 처리)")
    
    if not SUPABASE_AVAILABLE:
        logger.error("get_auth_client: supabase-py 패키지가 설치되지 않음")
        error_msg = "❌ Supabase 클라이언트 생성 실패\n\n"
        error_msg += "`supabase-py` 패키지가 설치되지 않았습니다.\n\n"
        error_msg += "다음 명령어로 설치하세요:\n"
        error_msg += "```bash\npip install supabase\n```"
        st.error(error_msg)
        st.stop()
        raise ImportError("supabase-py 패키지가 설치되지 않았습니다.")
    
    # Supabase URL과 anon key 가져오기 (st.secrets 우선, 없으면 os.getenv fallback)
    url = None
    anon_key = None
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
            raise ValueError("Supabase URL 또는 anon_key가 설정되지 않았습니다.")
    
    if not url or not anon_key:
        logger.error("get_auth_client: url 또는 anon_key가 비어있음")
        error_msg = "❌ Supabase 클라이언트 생성 실패\n\n"
        error_msg += "Supabase URL 또는 anon_key가 비어있습니다.\n\n"
        error_msg += "`.streamlit/secrets.toml` 파일 또는 환경변수를 확인하세요."
        st.error(error_msg)
        st.stop()
        raise ValueError("Supabase URL 또는 anon_key가 비어있습니다.")
    
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
        st.error(f"❌ Auth client init failed: {type(e).__name__}: {e}")
        st.code(traceback.format_exc(), language="python")
        
        # 디버그 정보 (값 노출 없이)
        debug_info = {
            "url_len": len(str(url)) if url else 0,
            "anon_key_len": len(str(anon_key)) if anon_key else 0,
            "url_starts_https": str(url).startswith("https://") if url else False,
            "has_secrets_supabase": "supabase" in st.secrets if hasattr(st, 'secrets') else False,
            "has_url": ("supabase" in st.secrets and "url" in st.secrets["supabase"]) if (hasattr(st, 'secrets') and "supabase" in st.secrets) else False,
            "has_anon_key": ("supabase" in st.secrets and "anon_key" in st.secrets["supabase"]) if (hasattr(st, 'secrets') and "supabase" in st.secrets) else False,
            "has_env_url": bool(os.getenv("SUPABASE_URL")),
            "has_env_anon_key": bool(os.getenv("SUPABASE_ANON_KEY")),
        }
        st.write("**디버그 정보:**")
        st.json(debug_info)
        st.stop()
        raise  # 예외를 다시 발생시켜서 함수가 None을 반환하지 않도록
    
    # 세션에 access_token이 있으면 설정 (토큰이 없어도 클라이언트는 반환)
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
        logger.info("get_auth_client: 토큰 없음 - 클라이언트만 반환 (토큰 체크는 별도 함수에서 처리)")
    
    # 클라이언트는 항상 반환 (토큰 체크는 별도 함수에서 처리)
    return client


def get_supabase_client(reset_session_on_fail: bool = True) -> Client:
    """
    Supabase 클라이언트 생성 (레거시 호환 - get_auth_client()로 위임)
    
    Args:
        reset_session_on_fail: 세션 설정 실패 시 clear_session() 호출 여부 (기본값: True)
    
    Returns:
        Supabase Client (절대 None 반환 안 함)
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


def signup(email: str, password: str) -> tuple[bool, str]:
    """
    회원가입 실행
    
    Args:
        email: 사용자 이메일
        password: 비밀번호
    
    Returns:
        tuple: (성공 여부, 메시지)
    """
    try:
        client = get_supabase_client()
        
        # 회원가입 시도
        response = client.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if response.user:
            # user_profiles 자동 생성 (onboarding_mode는 NULL로 두어 온보딩 화면으로 유도)
            ensure_user_profile(response.user.id)
            
            logger.info(f"User signed up: {email} (user_id: {response.user.id})")
            return True, "회원가입이 완료되었습니다."
        else:
            return False, "회원가입에 실패했습니다."
    
    except Exception as e:
        logger.error(f"Signup error: {e}")
        error_msg = str(e)
        if "User already registered" in error_msg or "already exists" in error_msg.lower():
            return False, "이미 등록된 이메일입니다."
        elif "Password should be at least" in error_msg:
            return False, "비밀번호는 최소 6자 이상이어야 합니다."
        elif "Invalid email" in error_msg:
            return False, "올바른 이메일 형식이 아닙니다."
        else:
            return False, f"회원가입 오류: {error_msg}"


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
        # get_supabase_client()는 절대 None을 반환하지 않음 (실패 시 예외 발생)
        client = get_supabase_client()
        
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
            
            # user_profiles 확인 (없으면 생성)
            profile_result = client.table("user_profiles").select("id, default_store_id, store_id, role").eq("id", response.user.id).execute()
            
            if not profile_result.data:
                # 프로필이 없으면 자동 생성
                ensure_user_profile(response.user.id)
                profile_result = client.table("user_profiles").select("id, default_store_id, store_id, role").eq("id", response.user.id).execute()
            
            # store_id·역할: profiles(user_profiles) 단일 소스 (store_members 폐기)
            store_id = None
            if profile_result.data:
                from src.ui_helpers import safe_resp_first_data
                profile_data = safe_resp_first_data(profile_result)
                if profile_data:
                    store_id = profile_data.get('store_id') or profile_data.get('default_store_id')
                    st.session_state.user_role = profile_data.get('role', 'manager')
            
            # store_id가 없어도 로그인은 성공 (매장 생성 플로우로 연결)
            if store_id:
                st.session_state.store_id = store_id  # 레거시 호환
                st.session_state._active_store_id = store_id  # 단일 소스 오브 트루스
                logger.info(f"User logged in: {email} (store_id: {store_id})")
            else:
                # store_id가 없으면 매장 생성 필요 플래그 설정
                st.session_state._needs_store_setup = True
                logger.info(f"User logged in: {email} (no store_id - needs setup)")
            
            return True, "로그인 성공"
        else:
            return False, "로그인에 실패했습니다."
    
    except Exception as e:
        logger.error(f"Login error: {e}")
        error_msg = str(e)
        if "Invalid login credentials" in error_msg:
            return False, "이메일 또는 비밀번호가 올바르지 않습니다."
        elif "Email not confirmed" in error_msg or "email_not_confirmed" in error_msg.lower():
            return False, "이메일 인증이 필요합니다. Supabase 대시보드에서 이메일을 확인하거나, 관리자에게 문의하세요."
        else:
            return False, f"로그인 오류: {error_msg}"


def ensure_user_profile(user_id: str) -> bool:
    """
    user_profiles row를 자동 생성 (없으면 생성)
    
    Args:
        user_id: 사용자 UUID
    
    Returns:
        bool: 성공 여부
    """
    try:
        client = get_supabase_client()
        
        # 기존 프로필 확인
        profile_result = client.table("user_profiles").select("id, onboarding_mode").eq("id", user_id).execute()
        
        if not profile_result.data:
            # 프로필이 없으면 생성 (onboarding_mode는 NULL로 두어 온보딩 화면으로 유도)
            # DB 기본값이 'coach'로 설정되어 있을 수 있으므로 명시적으로 NULL을 설정
            try:
                client.table("user_profiles").insert({
                    "id": user_id,
                    "onboarding_mode": None  # 명시적으로 NULL 설정
                }).execute()
            except Exception as e:
                # NOT NULL 제약이 있으면 기본값으로 생성하고 나중에 NULL로 업데이트 시도
                logger.warning(f"onboarding_mode를 NULL로 설정 실패 (NOT NULL 제약?), 기본값으로 생성: {e}")
                client.table("user_profiles").insert({
                    "id": user_id
                }).execute()
                # 생성 후 NULL로 업데이트 시도 (제약이 있으면 실패하지만 시도)
                try:
                    client.table("user_profiles").update({
                        "onboarding_mode": None
                    }).eq("id", user_id).execute()
                except:
                    pass  # NOT NULL 제약이 있으면 무시
            
            logger.info(f"User profile created: {user_id}")
            return True
        else:
            logger.info(f"User profile already exists: {user_id}")
            return True
    
    except Exception as e:
        logger.error(f"Failed to ensure user profile: {e}")
        return False


def get_onboarding_mode(user_id: str = None) -> str:
    """
    사용자의 온보딩 모드 조회
    
    Args:
        user_id: 사용자 UUID (None이면 현재 로그인한 사용자)
    
    Returns:
        str: 'coach' | 'fast' | None (온보딩 미완료)
    """
    try:
        if not user_id:
            try:
                user_id = st.session_state.get('user_id')
            except (AttributeError, RuntimeError):
                # Streamlit이 아직 초기화되지 않은 경우
                return None
        
        if not user_id:
            return None
        
        client = get_supabase_client()
        # 캐시 무효화를 위해 매번 DB에서 직접 조회 (캐시 사용 안 함)
        profile_result = client.table("user_profiles").select("onboarding_mode").eq("id", user_id).execute()
        
        from src.ui_helpers import safe_resp_first_data
        profile_data = safe_resp_first_data(profile_result)
        if not profile_data:
            logger.warning(f"get_onboarding_mode: user_profiles가 없음 (user_id={user_id})")
            return None
        
        mode = profile_data.get('onboarding_mode')
        logger.info(f"get_onboarding_mode: user_id={user_id}, mode={mode}, type={type(mode)}")
        
        # NULL이면 None 반환 (온보딩 필요)
        if mode is None:
            logger.info(f"get_onboarding_mode: mode가 None이므로 None 반환")
            return None
        
        # 값 검증 (coach 또는 fast만 허용)
        if mode in ['coach', 'fast']:
            return mode
        else:
            # 잘못된 값이면 'coach'로 fallback
            logger.warning(f"Invalid onboarding_mode '{mode}' for user {user_id}, falling back to 'coach'")
            return 'coach'
    
    except Exception as e:
        logger.error(f"Failed to get onboarding mode: {e}")
        return None


def set_onboarding_mode(user_id: str, mode: str) -> bool:
    """
    사용자의 온보딩 모드 설정
    
    Args:
        user_id: 사용자 UUID
        mode: 'coach' | 'fast'
    
    Returns:
        bool: 성공 여부
    """
    try:
        if mode not in ['coach', 'fast']:
            logger.error(f"Invalid onboarding mode: {mode}")
            return False
        
        client = get_supabase_client()
        client.table("user_profiles").update({
            "onboarding_mode": mode
        }).eq("id", user_id).execute()
        
        logger.info(f"Onboarding mode set: {user_id} -> {mode}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to set onboarding mode: {e}")
        return False


def reset_onboarding(user_id: str = None) -> bool:
    """
    온보딩을 리셋하여 다시 온보딩 선택 화면으로 이동하게 함
    
    조건:
    - user_profiles.onboarding_mode를 NULL로 설정
    
    Args:
        user_id: 사용자 UUID (None이면 현재 로그인한 사용자)
    
    Returns:
        bool: 성공 여부
    """
    try:
        if not user_id:
            try:
                user_id = st.session_state.get('user_id')
            except (AttributeError, RuntimeError):
                # Streamlit이 아직 초기화되지 않은 경우
                logger.debug("reset_onboarding: Streamlit이 아직 초기화되지 않음")
                return False
        
        if not user_id:
            logger.warning("reset_onboarding: user_id가 없음")
            return False
        
        try:
            client = get_supabase_client()
        except (AttributeError, RuntimeError):
            # Streamlit이 아직 초기화되지 않은 경우
            logger.debug("reset_onboarding: get_supabase_client 호출 실패 (Streamlit 미초기화)")
            return False
        
        if not client:
            logger.error("reset_onboarding: Supabase client를 가져올 수 없음")
            return False
        
        # onboarding_mode를 NULL로 설정
        client.table("user_profiles").update({
            "onboarding_mode": None
        }).eq("id", user_id).execute()
        
        logger.info(f"Onboarding reset: {user_id} -> NULL")
        return True
    
    except Exception as e:
        logger.error(f"Failed to reset onboarding: {e}")
        return False


def needs_onboarding(user_id: str = None) -> bool:
    """
    온보딩이 필요한지 확인
    
    조건:
    - user_profiles.onboarding_mode가 NULL이면 온보딩 필요
    
    Args:
        user_id: 사용자 UUID (None이면 현재 로그인한 사용자)
    
    Returns:
        bool: 온보딩이 필요하면 True
    """
    try:
        if not user_id:
            try:
                user_id = st.session_state.get('user_id')
            except (AttributeError, RuntimeError):
                # Streamlit이 아직 초기화되지 않은 경우
                return False
        
        if not user_id:
            logger.debug("needs_onboarding: user_id가 없음")
            return False
        
        mode = get_onboarding_mode(user_id)
        needs = mode is None
        logger.info(f"needs_onboarding: user_id={user_id}, mode={mode}, needs={needs}")
        return needs
    
    except Exception as e:
        logger.error(f"Failed to check onboarding status: {e}")
        return False


def logout():
    """로그아웃 실행"""
    try:
        client = get_supabase_client()
        if client:  # DEV MODE일 때는 None이므로 체크
            client.auth.sign_out()
    except Exception as e:
        logger.warning(f"Logout error (non-critical): {e}")
    finally:
        # 캐시 리소스 전체 클리어 (클라이언트 캐시 무효화)
        try:
            st.cache_resource.clear()
            logger.info("logout: st.cache_resource.clear() 호출 완료")
        except Exception as e:
            logger.warning(f"logout: st.cache_resource.clear() 실패 (non-critical): {e}")
        
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


def get_user_stores() -> list[dict]:
    """
    현재 사용자가 소속된 모든 매장 목록 반환
    
    Returns:
        list[dict]: 매장 정보 리스트 [{"id": store_id, "name": store_name, "role": role}, ...]
    """
    try:
        try:
            user_id = st.session_state.get('user_id')
        except (AttributeError, RuntimeError):
            # Streamlit이 아직 초기화되지 않은 경우
            return []
        if not user_id:
            return []
        
        client = get_supabase_client()
        
        # store_members에서 사용자의 매장 목록 조회
        members_result = client.table("store_members").select(
            "store_id, role, stores(id, name)"
        ).eq("user_id", user_id).execute()
        
        if not members_result.data:
            return []
        
        stores = []
        for member in members_result.data:
            store_info = member.get("stores")
            if store_info:
                stores.append({
                    "id": store_info.get("id"),
                    "name": store_info.get("name"),
                    "role": member.get("role", "manager")
                })
        
        # role 순서로 정렬 (owner 우선)
        role_order = {"owner": 1, "manager": 2, "staff": 3}
        stores.sort(key=lambda x: (role_order.get(x.get("role", "manager"), 99), x.get("name", "")))
        
        return stores
    
    except Exception as e:
        logger.error(f"Failed to get user stores: {e}")
        return []


def switch_store(store_id: str) -> bool:
    """
    현재 매장 전환
    
    Args:
        store_id: 전환할 매장 ID
    
    Returns:
        bool: 성공 여부
    """
    try:
        try:
            user_id = st.session_state.get('user_id')
        except (AttributeError, RuntimeError):
            # Streamlit이 아직 초기화되지 않은 경우
            return False
        if not user_id:
            return False
        
        # 사용자가 해당 매장에 소속되어 있는지 확인
        client = get_supabase_client()
        member_result = client.table("store_members").select("store_id").eq("user_id", user_id).eq("store_id", store_id).execute()
        
        if not member_result.data:
            return False
        
        # 세션 업데이트
        st.session_state.store_id = store_id  # 레거시 호환
        st.session_state._active_store_id = store_id  # 단일 소스 오브 트루스
        
        # 매장명 캐시 무효화
        if '_cached_store_name' in st.session_state:
            del st.session_state['_cached_store_name']
        
        logger.info(f"Store switched: {store_id} (user: {user_id})")
        return True
    
    except Exception as e:
        logger.error(f"Failed to switch store: {e}")
        return False


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
        from src.ui_helpers import safe_resp_first_data
        client = get_supabase_client()
        result = client.table("stores").select("name").eq("id", store_id).execute()
        
        store_data = safe_resp_first_data(result)
        if store_data:
            store_name = store_data.get('name', '매장 정보 없음')
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


def show_signup_page():
    """
    회원가입 페이지 UI 표시
    """
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
    st.markdown("### 회원가입")
    st.markdown("</div>", unsafe_allow_html=True)
    
    with st.form("signup_form"):
        email = st.text_input("이메일", placeholder="example@email.com")
        password = st.text_input("비밀번호", type="password", help="최소 6자 이상")
        password_confirm = st.text_input("비밀번호 확인", type="password")
        submit_button = st.form_submit_button("회원가입", type="primary", use_container_width=True)
        
        if submit_button:
            if not email or not password:
                st.error("이메일과 비밀번호를 모두 입력해주세요.")
            elif password != password_confirm:
                st.error("비밀번호가 일치하지 않습니다.")
            elif len(password) < 6:
                st.error("비밀번호는 최소 6자 이상이어야 합니다.")
            else:
                success, message = signup(email, password)
                if success:
                    st.success(message)
                    st.info("로그인 페이지로 이동합니다...")
                    st.session_state["_show_signup"] = False
                    # Phase 0 STEP 3: 플래그 변경만으로 조건부 렌더링이 자동 업데이트되므로 rerun 불필요
                else:
                    st.error(message)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 로그인으로 돌아가기
    if st.button("← 로그인으로 돌아가기", use_container_width=True):
        st.session_state["_show_signup"] = False
        # Phase 0 STEP 3: 플래그 변경만으로 조건부 렌더링이 자동 업데이트되므로 rerun 불필요


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
    
    # 회원가입/로그인 탭
    tab1, tab2 = st.tabs(["로그인", "회원가입"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("이메일", placeholder="example@email.com", key="login_email")
            password = st.text_input("비밀번호", type="password", key="login_password")
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
    
    with tab2:
        with st.form("signup_form_tab"):
            email = st.text_input("이메일", placeholder="example@email.com", key="signup_email")
            password = st.text_input("비밀번호", type="password", help="최소 6자 이상", key="signup_password")
            password_confirm = st.text_input("비밀번호 확인", type="password", key="signup_password_confirm")
            submit_button = st.form_submit_button("회원가입", type="primary", use_container_width=True)
            
            if submit_button:
                if not email or not password:
                    st.error("이메일과 비밀번호를 모두 입력해주세요.")
                elif password != password_confirm:
                    st.error("비밀번호가 일치하지 않습니다.")
                elif len(password) < 6:
                    st.error("비밀번호는 최소 6자 이상이어야 합니다.")
                else:
                    success, message = signup(email, password)
                    if success:
                        st.success(message)
                        st.info("로그인 탭에서 로그인해주세요.")
                    else:
                        st.error(message)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 도움말
    with st.expander("도움말"):
        st.info("""
        **로그인이 안 되나요?**
        
        1. 회원가입을 먼저 진행해주세요.
        2. 회원가입 후 자동으로 user_profiles가 생성됩니다.
        3. 첫 로그인 시 매장 생성 화면으로 이동합니다.
        
        문제가 지속되면 관리자에게 문의하세요.
        """)
