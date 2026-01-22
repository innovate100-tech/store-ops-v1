"""
공통 인증 및 권한 가드
페이지에서 로그인 상태와 store_id를 일관되게 확인
"""
import streamlit as st
from typing import Tuple, Optional
from src.auth import get_auth_client, get_current_store_id


def require_auth_and_store() -> Tuple[str, str]:
    """
    로그인 상태와 store_id를 확인하고 반환하는 공통 가드
    
    - 로그인 확인 (access_token, user_id)
    - get_auth_client() 호출하여 인증 클라이언트 생성
    - get_current_store_id() 호출하여 store_id 가져오기
    - 실패 시 st.error() 및 st.stop() 호출
    
    Returns:
        Tuple[user_id, store_id]: 로그인한 사용자의 user_id와 store_id
        
    Raises:
        SystemExit: 로그인 실패 또는 store_id 없음 시 st.stop()으로 인한 종료
    """
    # 1. 로그인 상태 확인
    has_token = 'access_token' in st.session_state and bool(st.session_state.get('access_token'))
    has_user_id = 'user_id' in st.session_state and bool(st.session_state.get('user_id'))
    
    if not has_token or not has_user_id:
        st.error("❌ 로그인이 필요합니다. 로그인 후 다시 시도해주세요.")
        st.stop()
        return None, None  # st.stop() 후에는 실행되지 않지만 타입 체크를 위해
    
    user_id = st.session_state.get('user_id')
    
    # 2. Auth Client 생성 (RLS 정책 적용을 위해)
    try:
        client = get_auth_client(reset_session_on_fail=False)
        if client is None:
            st.error("❌ Supabase 클라이언트를 생성할 수 없습니다. Supabase 설정을 확인하세요.")
            st.stop()
            return None, None
    except Exception as e:
        st.error(f"❌ Supabase 클라이언트 생성 실패: {str(e)}")
        st.stop()
        return None, None
    
    # 3. store_id 가져오기
    store_id = get_current_store_id()
    if not store_id:
        st.error("❌ 매장 정보를 찾을 수 없습니다. 로그인 후 다시 시도해주세요.")
        st.stop()
        return None, None
    
    return user_id, store_id
