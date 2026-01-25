"""
홈 화면 (HOME v1)
앱 정체성 + 운영 원칙 + 3단 구조 안내 화면
"""
from src.bootstrap import bootstrap
import streamlit as st
import logging
from src.auth import get_current_store_id, get_current_store_name, check_login, show_login_page

logger = logging.getLogger(__name__)

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
    # 프리미엄 CSS 주입 (HOME에서만)
    from src.ui.home_premium_style import inject_home_premium_css
    inject_home_premium_css()
    
    # DEV 모드에서만 워터마크 표시
    from src.auth import is_dev_mode
    if is_dev_mode():
        st.error("HOME V1 LOADED ✅  ui_pages/home_page_v0.py  (2026-01-26)")
    
    # ============================================
    # SECTION 1: 앱 정체성 (Hero Section) - 프리미엄 카드
    # ============================================
    st.markdown("""
    <div class="ps-hero-card">
        <div class="ps-neon ps-neon-blue"></div>
        <div class="ps-hero-body">
            <div class="ps-hero-title">이 앱은 감이 아니라, 숫자로 매장을 운영하게 만드는 시스템입니다.</div>
            <div class="ps-hero-sub">매출은 결과이고, 숫자는 원인입니다.</div>
            <div class="ps-hero-desc">이 앱은 아래 3단계를 반복할수록 매장이 강해지도록 설계되어 있습니다.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ============================================
    # SECTION 2: 현재 위치 (Status Dashboard) - 프리미엄 카드
    # ============================================
    st.markdown("""
    <div class="ps-status-card">
        <div class="ps-neon ps-neon-amber"></div>
        <div class="ps-status-content">
            <div class="ps-status-title">📍 지금 당신의 매장은 이 단계에 있습니다</div>
    """, unsafe_allow_html=True)
    
    # 추천 엔진 호출
    try:
        from src.auth import get_current_store_id
        from src.home.home_reco_v1 import get_home_recommendation_v1
        from src.home.home_reco_log import log_reco_event, get_reco_weekly_counts
        
        store_id = get_current_store_id()
        user_id = st.session_state.get('user_id')
        
        if store_id and user_id:
            reco = get_home_recommendation_v1(user_id, store_id)
            status = reco.get("status", {})
            
            # 상태 표시 (3개 미니 카드)
            yesterday_closed = status.get("yesterday_closed", False)
            last7_close_days = status.get("last7_close_days", 0)
            recipe_cover_rate = status.get("recipe_cover_rate", 0.0)
            sales_goal_exists = status.get("sales_goal_exists", False)
            cost_goal_exists = status.get("cost_goal_exists", False)
            
            # 상태 미니 카드 3개 (st.columns 사용)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div class="ps-metric-card">
                    <div class="ps-metric-label">마감</div>
                    <div class="ps-metric-value">{"✅" if yesterday_closed else "❌"} / {last7_close_days}/7</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="ps-metric-card">
                    <div class="ps-metric-label">레시피</div>
                    <div class="ps-metric-value">{recipe_cover_rate * 100:.0f}%</div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div class="ps-metric-card">
                    <div class="ps-metric-label">목표</div>
                    <div class="ps-metric-value">{"✅" if sales_goal_exists else "❌"} / {"✅" if cost_goal_exists else "❌"}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # DEV 모드에서만 상세 상태 표시
            if is_dev_mode():
                st.caption(f"DEBUG: type={reco.get('type')}, status={status}")
            
            # 추천 블록
            st.markdown("""
            <div class="ps-reco-section">
                <div class="ps-reco-title">🎯 오늘 우리 매장 추천</div>
                <div class="ps-reco-subtitle">이 앱이 오늘 데이터를 보고 판단한, 가장 우선해야 할 한 가지입니다.</div>
                <div class="ps-reco-message-card">
                    <p>{}</p>
                </div>
            </div>
            """.format(reco.get("message", "상태 계산 중입니다.")), unsafe_allow_html=True)
            
            # 액션 버튼
            action_label = reco.get("action_label", "오늘 마감 시작하기")
            action_page = reco.get("action_page", "일일 입력(통합)")
            
            # shown 이벤트 로깅 (홈 진입 시 1회)
            try:
                log_reco_event(user_id, store_id, reco, "shown")
            except Exception as e:
                logger.warning(f"Failed to log shown event: {e}")
            
            # 버튼 클릭 처리
            button_clicked = st.button(f"▶ {action_label}", type="primary", use_container_width=True)
            if button_clicked:
                # clicked 이벤트 로깅
                try:
                    log_reco_event(user_id, store_id, reco, "clicked")
                except Exception as e:
                    logger.warning(f"Failed to log clicked event: {e}")
                
                st.session_state.current_page = action_page
                st.rerun()
            
            # 최근 7일 요약 표시
            try:
                shown_count, clicked_count = get_reco_weekly_counts(store_id, days=7)
                st.markdown(f"""
                <div class="ps-reco-summary-card">
                    <p>📊 최근 7일 코치 기록: 추천 {shown_count}회 · 실행 {clicked_count}회</p>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                logger.warning(f"Failed to get weekly counts: {e}")
                # 실패 시 숨김 (크래시 방지)
        else:
            # store_id나 user_id가 없는 경우 기본 표시
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("""
                <div class="ps-metric-card">
                    <div class="ps-metric-label">입력 완성도</div>
                    <div class="ps-metric-value">준비 중</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown("""
                <div class="ps-metric-card">
                    <div class="ps-metric-label">활성화된 분석</div>
                    <div class="ps-metric-value">준비 중</div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown("""
                <div class="ps-metric-card">
                    <div class="ps-metric-label">설계 가능 단계</div>
                    <div class="ps-metric-value">준비 중</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="ps-reco-section">
                <div class="ps-reco-message-card">
                    <p>👉 지금 가장 중요한 것은 "입력 → 분석 → 설계 흐름을 만드는 것"입니다.</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        # 에러 발생 시 기본 표시 (안전 가드)
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to load recommendation: {e}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            <div class="ps-metric-card">
                <div class="ps-metric-label">입력 완성도</div>
                <div class="ps-metric-value">준비 중</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div class="ps-metric-card">
                <div class="ps-metric-label">활성화된 분석</div>
                <div class="ps-metric-value">준비 중</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
            <div class="ps-metric-card">
                <div class="ps-metric-label">설계 가능 단계</div>
                <div class="ps-metric-value">준비 중</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="ps-reco-section">
            <div class="ps-reco-message-card">
                <p>👉 지금 가장 중요한 것은 "입력 → 분석 → 설계 흐름을 만드는 것"입니다.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ============================================
    # SECTION 3: 핵심 구조 (입력 → 분석 → 설계)
    # ============================================
    
    # STEP 1: 입력
    st.markdown("""
    <div class="ps-step-card ps-step-1">
        <div class="ps-step-title">STEP 1. 입력 — 매장을 '데이터 자산'으로 만든다</div>
        <div class="ps-step-highlight-box ps-color-blue">
            <p>
                입력은 기록이 아닙니다.<br>
                입력은 매장을 시스템으로 만드는 작업입니다.
            </p>
        </div>
        <div class="ps-step-description">
            - 메뉴 / 재료 / 레시피 / 매출 / 비용 / 마감<br>
            - 이 데이터들이 쌓여야 분석과 전략이 작동합니다.
        </div>
        <div class="ps-step-actions">
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶ 오늘 입력하기", type="primary", use_container_width=True):
            st.session_state.current_page = "일일 입력(통합)"
            st.rerun()
    with col2:
        if st.button("▶ 데이터 입력센터", type="secondary", use_container_width=True):
            st.session_state.current_page = "입력 허브"
            st.rerun()
    
    st.markdown("""
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # STEP 2: 분석
    st.markdown("""
    <div class="ps-step-card ps-step-2">
        <div class="ps-step-title">STEP 2. 분석 — 숫자가 문제를 말해준다</div>
        <div class="ps-step-highlight-box ps-color-green">
            <p>
                분석은 보고서가 아닙니다.<br>
                분석은 "왜 이런 결과가 나왔는지"를 알려주는 엔진입니다.
            </p>
        </div>
        <div class="ps-step-description">
            - 매출이 왜 이 숫자인지<br>
            - 어디서 새고 있는지<br>
            - 무엇을 키워야 하는지
        </div>
        <div class="ps-step-actions">
    """, unsafe_allow_html=True)
    
    if st.button("▶ 데이터 분석센터", type="primary", use_container_width=True, key="step2_btn"):
        st.session_state.current_page = "분석 허브"
        st.rerun()
    
    st.markdown("""
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # STEP 3: 설계
    st.markdown("""
    <div class="ps-step-card ps-step-3">
        <div class="ps-step-title">STEP 3. 설계 — 숫자를 행동으로 바꾼다</div>
        <div class="ps-step-highlight-box ps-color-purple">
            <p>
                설계는 조언이 아닙니다.<br>
                설계는 사장의 '다음 행동'을 만드는 단계입니다.
            </p>
        </div>
        <div class="ps-step-description">
            - 개선 우선순위<br>
            - 전략 보드<br>
            - 메뉴/비용/운영 방향
        </div>
        <div class="ps-step-actions">
    """, unsafe_allow_html=True)
    
    if st.button("▶ 가게 전략 센터", type="primary", use_container_width=True, key="step3_btn"):
        st.session_state.current_page = "가게 전략 센터"
        st.rerun()
    
    st.markdown("""
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ============================================
    # SECTION 4: 매일 각인 문장 (Quote Section) - 프리미엄 카드
    # ============================================
    st.markdown("""
    <div class="ps-quote-card">
        <p class="ps-quote-text">
            "입력 안 하면, 이 앱은 아무 의미 없습니다.<br>
            숫자를 안 보면, 장사는 항상 운입니다.<br>
            바쁜 매장이 망하고, 관리하는 매장이 남습니다."
        </p>
    </div>
    """, unsafe_allow_html=True)
