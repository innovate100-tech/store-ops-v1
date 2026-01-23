"""
온보딩 완료 페이지
최초 로그인 시 1회 노출되는 환영 화면 (모드 선택 제거됨)
"""
import streamlit as st
from src.auth import get_supabase_client, get_current_store_id, set_onboarding_mode


def render_onboarding_mode_select():
    """
    온보딩 완료 화면 렌더링 (모드 선택 없이 자동 완료)
    """
    # 인증 확인 (store_id는 없어도 됨)
    if not st.session_state.get('user_id'):
        st.error("로그인이 필요합니다.")
        st.stop()
        return
    
    user_id = st.session_state.get('user_id')
    
    # 자동으로 온보딩 완료 처리 (기본값: 'coach'로 설정, 실제로는 사용 안 함)
    # 하위호환성을 위해 DB에는 저장하되, 앱에서는 모드 구분 없이 사용
    try:
        set_onboarding_mode(user_id, 'coach')  # 기본값으로 저장 (실제 사용 안 함)
    except Exception as e:
        st.warning(f"온보딩 설정 저장 중 오류: {e}")
    
    # 환영 메시지 표시
    st.title("환영합니다! 🎉")
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <p style="font-size: 1.1rem; color: #666; line-height: 1.6;">
            가게 운영을 시작하세요!<br>
            홈 화면에서 오늘의 운영 지시를 확인하고, 가게 설계 센터에서 구조를 점검하세요.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 간단한 안내 카드
    st.markdown("""
    <div style="padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 16px; color: white; margin-bottom: 2rem;">
        <div style="font-size: 1.3rem; font-weight: 700; margin-bottom: 1rem;">시작하기</div>
        <div style="font-size: 0.95rem; opacity: 0.95; line-height: 1.6;">
            <div style="margin-bottom: 0.5rem;">✓ 홈에서 오늘의 운영 지시 확인</div>
            <div style="margin-bottom: 0.5rem;">✓ 점장 마감으로 매출 입력</div>
            <div style="margin-bottom: 0.5rem;">✓ 가게 설계 센터에서 구조 점검</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 시작하기 버튼
    if st.button("시작하기", type="primary", use_container_width=True, key="btn_start"):
        st.session_state["_onboarding_completed"] = True
        st.rerun()


if __name__ == "__main__":
    render_onboarding_mode_select()
