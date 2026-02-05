"""
매장 생성 페이지
로그인 후 store_id가 없을 때 자동으로 이동
"""
import streamlit as st
import logging
from src.auth import get_supabase_client, get_current_store_id
from src.ui.guards import require_auth_and_store

logger = logging.getLogger(__name__)


def create_store_for_user(user_id: str, store_name: str) -> tuple[bool, str, str]:
    """
    사용자를 위한 매장 생성
    
    Args:
        user_id: 사용자 UUID
        store_name: 매장명
    
    Returns:
        tuple: (성공 여부, 메시지, 생성된 store_id)
    """
    try:
        client = get_supabase_client()
        
        # 1. 매장 생성
        store_result = client.table("stores").insert({
            "name": store_name,
            "created_by": user_id
        }).execute()
        
        if not store_result.data:
            return False, "매장 생성에 실패했습니다.", None
        
        store_id = store_result.data[0]["id"]
        
        # 2. profiles(user_profiles)에 매장·역할만 업데이트 (store_members 폐기, 단일 소스)
        client.table("user_profiles").update({
            "store_id": store_id,
            "role": "owner"
        }).eq("id", user_id).execute()
        
        logger.info(f"Store created: {store_name} (store_id: {store_id}, owner: {user_id})")
        return True, "매장이 생성되었습니다.", store_id
    
    except Exception as e:
        logger.error(f"Failed to create store: {e}")
        return False, f"매장 생성 오류: {str(e)}", None


def render_store_setup_page():
    """
    매장 생성 페이지 렌더링
    """
    # 인증 확인 (store_id는 없어도 됨)
    if not st.session_state.get('user_id'):
        st.error("로그인이 필요합니다.")
        st.stop()
        return
    
    user_id = st.session_state.get('user_id')
    
    # 이미 store_id가 있으면 홈으로 리다이렉트
    store_id = get_current_store_id()
    if store_id:
        st.info("이미 매장이 설정되어 있습니다.")
        st.rerun()
        return
    
    st.title("🏪 매장 생성")
    st.markdown("""
    환영합니다! 매장 운영을 시작하기 위해 매장 정보를 입력해주세요.
    """)
    
    with st.form("store_setup_form"):
        store_name = st.text_input(
            "매장명 *",
            placeholder="예: Plate&Share",
            help="매장 이름을 입력하세요"
        )
        
        submit_button = st.form_submit_button("매장 생성", type="primary", use_container_width=True)
        
        if submit_button:
            if not store_name or not store_name.strip():
                st.error("매장명을 입력해주세요.")
            else:
                success, message, created_store_id = create_store_for_user(user_id, store_name.strip())
                
                if success:
                    # 세션에 store_id 설정
                    st.session_state.store_id = created_store_id
                    st.session_state._active_store_id = created_store_id
                    
                    st.success(message)
                    st.info("홈 화면으로 이동합니다...")
                    st.rerun()
                else:
                    st.error(message)
    
    # 안내
    with st.expander("💡 안내"):
        st.info("""
        **매장 생성 후:**
        
        1. 매장 정보가 자동으로 저장됩니다.
        2. 당신은 이 매장의 소유자(owner)로 등록됩니다.
        3. 홈 화면으로 이동하여 매장 운영을 시작할 수 있습니다.
        
        나중에 다른 매장을 추가하거나 매장을 전환할 수 있습니다.
        """)


if __name__ == "__main__":
    render_store_setup_page()
