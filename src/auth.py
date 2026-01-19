"""
Supabase 인증 모듈
로그인/로그아웃/세션 관리
"""
import streamlit as st
import logging

try:
    from supabase import create_client, Client
    from typing import Optional
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    from typing import Optional

logger = logging.getLogger(__name__)


def get_supabase_client() -> Optional[Client]:
    """
    Supabase 클라이언트 생성 (anon key + access_token 사용)
    
    Returns:
        Supabase Client 또는 None (DEV MODE일 때)
    """
    # DEV MODE일 때는 None 반환 (예외 발생 안 함)
    if st.session_state.get('dev_mode', False):
        return None
    
    if not SUPABASE_AVAILABLE:
        raise ImportError("supabase-py가 설치되지 않았습니다. pip install supabase 실행하세요.")
    
    # Supabase URL과 anon key 가져오기
    url = st.secrets.get("supabase", {}).get("url", "")
    anon_key = st.secrets.get("supabase", {}).get("anon_key", "")
    
    if not url or not anon_key:
        raise ValueError("Supabase URL 또는 anon_key가 설정되지 않았습니다. .streamlit/secrets.toml을 확인하세요.")
    
    # 클라이언트 생성
    client = create_client(url, anon_key)
    
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
                else:
                    # refresh_token이 없으면 access_token만 설정 시도
                    try:
                        client.auth.set_session(
                            access_token=access_token,
                            refresh_token=''
                        )
                    except Exception:
                        # 세션 설정 실패 시 세션 정보 초기화
                        logger.warning("세션 설정 실패. 세션 정보를 초기화합니다.")
                        clear_session()
            except Exception as e:
                # 세션 설정 중 에러 발생 시 (토큰 만료 등)
                logger.warning(f"세션 설정 중 오류 발생: {e}. 세션 정보를 초기화합니다.")
                # 세션 정보 초기화하여 재로그인 유도
                clear_session()
                # 에러를 다시 발생시키지 않고 클라이언트만 반환 (재로그인 필요)
                pass
    
    return client


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
            
            st.session_state.store_id = store_id
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
        clear_session()


def clear_session():
    """세션 정보 정리"""
    if 'user_id' in st.session_state:
        del st.session_state.user_id
    if 'access_token' in st.session_state:
        del st.session_state.access_token
    if 'refresh_token' in st.session_state:
        del st.session_state.refresh_token
    if 'store_id' in st.session_state:
        del st.session_state.store_id
    if 'user_role' in st.session_state:
        del st.session_state.user_role


def apply_dev_mode_session():
    """
    DEV MODE 세션 설정
    로컬 개발 시 로그인 없이 앱을 사용하기 위한 더미 세션 값 설정
    
    Returns:
        bool: DEV MODE 활성화 여부
    """
    try:
        dev_mode = st.secrets.get("app", {}).get("dev_mode", False)
        
        if dev_mode:
            dev_store_id = st.secrets.get("app", {}).get("dev_store_id", "")
            
            if not dev_store_id:
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
                st.stop()
                return False
            
            # DEV MODE 세션 값 설정
            st.session_state.user_id = "dev-user"
            st.session_state.access_token = "dev"
            st.session_state.refresh_token = "dev"
            st.session_state.store_id = dev_store_id
            st.session_state.user_role = "manager"
            st.session_state.dev_mode = True
            
            logger.info(f"DEV MODE activated (store_id: {dev_store_id})")
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
    
    Returns:
        str: store_id (UUID)
    """
    return st.session_state.get('store_id')


def get_current_store_name() -> str:
    """
    현재 로그인한 사용자의 매장명 반환
    
    Returns:
        str: 매장명
    """
    # DEV MODE일 때는 Supabase를 호출하지 않고 기본값 반환
    if is_dev_mode():
        return "DEV MODE (로컬 개발)"
    
    store_id = get_current_store_id()
    if not store_id:
        return "매장 정보 없음"
    
    try:
        client = get_supabase_client()
        result = client.table("stores").select("name").eq("id", store_id).execute()
        
        if result.data:
            return result.data[0]['name']
        return "매장 정보 없음"
    except Exception as e:
        logger.error(f"Failed to get store name: {e}")
        return "매장 정보 없음"


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
