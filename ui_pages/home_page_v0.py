"""
홈 화면 (HOME v1)
앱 정체성 + 운영 원칙 + 3단 구조 안내 화면
"""
from src.bootstrap import bootstrap
import streamlit as st
from src.auth import get_current_store_id, get_current_store_name, check_login, show_login_page

# 공통 설정 적용
bootstrap(page_title="Home")

# 로그인 체크
if not check_login():
    show_login_page()
    st.stop()


def render_home():
    """
    HOME v1 - 앱 정체성 + 운영 원칙 + 3단 구조 안내
    """
    # DEV 모드에서만 워터마크 표시
    from src.auth import is_dev_mode
    if is_dev_mode():
        st.error("HOME V1 LOADED ✅  ui_pages/home_page_v0.py  (2026-01-26)")
    
    # ============================================
    # SECTION 1: 앱 정체성 (최상단 고정)
    # ============================================
    st.markdown("""
    <div style="margin-bottom: 3rem;">
        <h1 style="font-size: 2rem; font-weight: 700; margin-bottom: 1rem; line-height: 1.3;">
            이 앱은 감이 아니라, 숫자로 매장을 운영하게 만드는 시스템입니다.
        </h1>
        <h2 style="font-size: 1.3rem; font-weight: 500; color: #94a3b8; margin-bottom: 1.5rem; line-height: 1.5;">
            매출은 결과이고,<br>
            숫자는 원인입니다.
        </h2>
        <p style="font-size: 1rem; color: #cbd5e1; line-height: 1.6;">
            이 앱은 아래 3단계를 반복할수록 매장이 강해지도록 설계되어 있습니다.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ============================================
    # SECTION 2: 현재 위치 (두 번째 핵심 타이틀)
    # ============================================
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h2 style="font-size: 1.8rem; font-weight: 700; margin-bottom: 1.5rem; line-height: 1.3;">
            📍 지금 당신의 매장은 이 단계에 있습니다
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    - **입력 완성도**: (준비 중)
    - **활성화된 분석**: (준비 중)
    - **설계 가능 단계**: (준비 중)
    """)
    
    st.markdown("""
    <div style="background: rgba(245, 158, 11, 0.1); border-left: 4px solid #F59E0B; padding: 1rem; margin: 1.5rem 0; border-radius: 4px;">
        <p style="font-weight: 600; margin: 0; font-size: 1.05rem;">
            👉 지금 가장 중요한 것은 "입력 → 분석 → 설계 흐름을 만드는 것"입니다.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ============================================
    # SECTION 3: 핵심 구조 (입력 → 분석 → 설계)
    # ============================================
    
    # STEP 1: 입력
    with st.container():
        st.markdown("### STEP 1. 입력 — 매장을 '데이터 자산'으로 만든다")
        
        st.markdown("""
        <div style="background: rgba(59, 130, 246, 0.1); border-left: 4px solid #3B82F6; padding: 1rem; margin: 1rem 0; border-radius: 4px;">
            <p style="font-weight: 600; margin-bottom: 0.5rem; font-size: 1.05rem;">
                입력은 기록이 아닙니다.<br>
                입력은 매장을 시스템으로 만드는 작업입니다.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        - 메뉴 / 재료 / 레시피 / 매출 / 비용 / 마감
        - 이 데이터들이 쌓여야 분석과 전략이 작동합니다.
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶ 오늘 입력하기", type="primary", use_container_width=True):
                st.session_state.current_page = "일일 입력(통합)"
                st.rerun()
        with col2:
            if st.button("▶ 데이터 입력센터", type="secondary", use_container_width=True):
                st.session_state.current_page = "입력 허브"
                st.rerun()
    
    st.markdown("---")
    
    # STEP 2: 분석
    with st.container():
        st.markdown("### STEP 2. 분석 — 숫자가 문제를 말해준다")
        
        st.markdown("""
        <div style="background: rgba(16, 185, 129, 0.1); border-left: 4px solid #10B981; padding: 1rem; margin: 1rem 0; border-radius: 4px;">
            <p style="font-weight: 600; margin-bottom: 0.5rem; font-size: 1.05rem;">
                분석은 보고서가 아닙니다.<br>
                분석은 "왜 이런 결과가 나왔는지"를 알려주는 엔진입니다.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        - 매출이 왜 이 숫자인지
        - 어디서 새고 있는지
        - 무엇을 키워야 하는지
        """)
        
        if st.button("▶ 데이터 분석센터", type="primary", use_container_width=True):
            st.session_state.current_page = "분석 허브"
            st.rerun()
    
    st.markdown("---")
    
    # STEP 3: 설계
    with st.container():
        st.markdown("### STEP 3. 설계 — 숫자를 행동으로 바꾼다")
        
        st.markdown("""
        <div style="background: rgba(168, 85, 247, 0.1); border-left: 4px solid #A855F7; padding: 1rem; margin: 1rem 0; border-radius: 4px;">
            <p style="font-weight: 600; margin-bottom: 0.5rem; font-size: 1.05rem;">
                설계는 조언이 아닙니다.<br>
                설계는 사장의 '다음 행동'을 만드는 단계입니다.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        - 개선 우선순위
        - 전략 보드
        - 메뉴/비용/운영 방향
        """)
        
        if st.button("▶ 가게 전략 센터", type="primary", use_container_width=True):
            st.session_state.current_page = "가게 전략 센터"
            st.rerun()
    
    st.markdown("---")
    
    # ============================================
    # SECTION 4: 매일 각인 문장 (하단 고정)
    # ============================================
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0; margin-top: 3rem;">
        <p style="font-size: 1.2rem; font-weight: 600; font-style: italic; color: #94a3b8; line-height: 1.8;">
            "입력 안 하면, 이 앱은 아무 의미 없습니다.<br>
            숫자를 안 보면, 장사는 항상 운입니다.<br>
            바쁜 매장이 망하고, 관리하는 매장이 남습니다."
        </p>
    </div>
    """, unsafe_allow_html=True)
