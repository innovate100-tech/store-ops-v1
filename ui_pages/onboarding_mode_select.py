"""
온보딩 모드 선택 페이지
최초 로그인 시 1회 노출되는 사용 모드 선택 화면
"""
import streamlit as st
from src.auth import get_supabase_client, get_current_store_id, set_onboarding_mode


def render_onboarding_mode_select():
    """
    온보딩 모드 선택 화면 렌더링
    """
    # 인증 확인 (store_id는 없어도 됨)
    if not st.session_state.get('user_id'):
        st.error("로그인이 필요합니다.")
        st.stop()
        return
    
    user_id = st.session_state.get('user_id')
    
    st.title("어떤 방식으로 사용할까요?")
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <p style="font-size: 1.1rem; color: #666; line-height: 1.6;">
            처음 사용하시는 사장님을 위해 두 가지 모드를 준비했습니다.<br>
            나중에 언제든 변경할 수 있습니다.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 16px; color: white; height: 100%;">
            <div style="font-size: 1.5rem; font-weight: 700; margin-bottom: 1rem;">🎯 코치 모드</div>
            <div style="font-size: 0.9rem; opacity: 0.95; margin-bottom: 1.5rem; line-height: 1.6;">
                <div style="margin-bottom: 0.5rem;">✓ 안내 + 미션</div>
                <div style="margin-bottom: 0.5rem;">✓ 자동 코치</div>
                <div style="margin-bottom: 0.5rem;">✓ 성장 단계 표시</div>
                <div style="margin-top: 1rem; font-size: 0.85rem; opacity: 0.9;">
                    처음 쓰는 사장에게 추천
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("안내 받으면서 시작하기", type="primary", use_container_width=True, key="btn_coach"):
            if set_onboarding_mode(user_id, 'coach'):
                st.success("코치 모드로 설정되었습니다.")
                st.session_state["_onboarding_completed"] = True
                st.rerun()
            else:
                st.error("모드 설정에 실패했습니다.")
    
    with col2:
        st.markdown("""
        <div style="padding: 2rem; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 16px; color: white; height: 100%;">
            <div style="font-size: 1.5rem; font-weight: 700; margin-bottom: 1rem;">⚡ 빠른 사용 모드</div>
            <div style="font-size: 0.9rem; opacity: 0.95; margin-bottom: 1.5rem; line-height: 1.6;">
                <div style="margin-bottom: 0.5rem;">✓ 바로 입력</div>
                <div style="margin-bottom: 0.5rem;">✓ 숫자 중심</div>
                <div style="margin-bottom: 0.5rem;">✓ 미션/안내 최소</div>
                <div style="margin-top: 1rem; font-size: 0.85rem; opacity: 0.9;">
                    기존 관리툴 사용자용
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("바로 사용하기", type="primary", use_container_width=True, key="btn_fast"):
            if set_onboarding_mode(user_id, 'fast'):
                st.success("빠른 사용 모드로 설정되었습니다.")
                st.session_state["_onboarding_completed"] = True
                st.rerun()
            else:
                st.error("모드 설정에 실패했습니다.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 안내
    with st.expander("💡 두 모드의 차이점"):
        st.info("""
        **코치 모드:**
        - 매일 가게 상태를 분석하고 문제점을 알려줍니다
        - 미션을 통해 단계적으로 기능을 익힐 수 있습니다
        - 처음 사용하는 사장님에게 추천합니다
        
        **빠른 사용 모드:**
        - 핵심 숫자와 바로가기 버튼만 표시합니다
        - 미션과 안내 메시지가 최소화됩니다
        - 기존 관리툴을 사용하던 사장님에게 추천합니다
        
        언제든지 홈 화면에서 모드를 변경할 수 있습니다.
        """)


if __name__ == "__main__":
    render_onboarding_mode_select()
