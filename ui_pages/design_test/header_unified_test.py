"""
홈화면 리뉴얼 테스트 페이지
통합형 2단 구조 테스트
"""
import streamlit as st


def render_header_unified_test():
    """홈화면 리뉴얼 구조 테스트"""
    
    st.title("🎨 홈화면 리뉴얼 테스트")
    st.caption("통합형 2단 구조 - 브랜드 히어로 + 오늘의 액션 센터")
    
    # 테스트용 데이터
    yesterday_closed = True
    last7_close_days = 5
    recipe_cover_rate = 0.75
    sales_goal_exists = True
    cost_goal_exists = False
    reco_message = "오늘은 어제 마감 데이터를 입력하세요. 매출과 방문자 수를 기록하면 분석 리포트가 자동으로 생성됩니다."
    action_label = "오늘 마감 시작하기"
    shown_count = 12
    clicked_count = 8
    
    # 리뉴얼 CSS
    css = """
    <style>
    /* 브랜드 히어로 (기존 유지) */
    .ps-brand-hero {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.9) 50%, rgba(15, 23, 42, 0.95) 100%);
        border-radius: 24px;
        padding: 5rem 3rem;
        margin: 0 0 3rem 0;
        text-align: center;
        position: relative;
        overflow: hidden;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5), 0 0 80px rgba(59, 130, 246, 0.15);
        border: 1px solid rgba(59, 130, 246, 0.2);
    }
    
    .ps-brand-hero::after {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.6), rgba(96, 165, 250, 0.8), rgba(59, 130, 246, 0.6), transparent);
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
    }
    
    .ps-brand-name {
        font-size: 5rem;
        font-weight: 900;
        background: linear-gradient(135deg, #60A5FA 0%, #3B82F6 30%, #2563EB 50%, #3B82F6 70%, #60A5FA 100%);
        background-size: 200% 200%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.05em;
        line-height: 1.1;
        margin-bottom: 1.5rem;
        color: #60A5FA;
    }
    
    .ps-brand-tagline {
        font-size: 1.8rem;
        font-weight: 700;
        color: #F8FAFC;
        line-height: 1.6;
        margin-bottom: 1rem;
    }
    
    .ps-brand-subtitle {
        font-size: 1.2rem;
        font-weight: 500;
        color: #94A3B8;
        margin-bottom: 3rem;
    }
    
    /* 오늘의 액션 센터 (통합 카드) */
    .ps-action-center {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.85) 0%, rgba(15, 23, 42, 0.75) 100%);
        border-radius: 20px;
        padding: 2.5rem;
        margin: 0 0 2rem 0;
        border: 1px solid rgba(59, 130, 246, 0.3);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4), 0 0 50px rgba(59, 130, 246, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    .ps-action-center::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 6px;
        background: linear-gradient(90deg, #F59E0B 0%, #FBBF24 50%, #F59E0B 100%);
        box-shadow: 0 0 20px rgba(245, 158, 11, 0.5);
    }
    
    /* 블록 1: 상태 요약 */
    .ps-status-summary {
        margin-bottom: 2rem;
        padding-bottom: 2rem;
        border-bottom: 1px solid rgba(148, 163, 184, 0.15);
    }
    
    .ps-status-summary-title {
        font-size: 1.75rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    
    .ps-metric-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .ps-metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
        border-color: rgba(59, 130, 246, 0.4);
    }
    
    .ps-metric-label {
        font-size: 0.85rem;
        color: #94A3B8;
        margin-bottom: 0.5rem;
        font-weight: 500;
    }
    
    .ps-metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #F8FAFC;
    }
    
    /* 블록 2: 오늘 추천 */
    .ps-today-reco {
        margin-bottom: 2rem;
        padding-bottom: 2rem;
        border-bottom: 1px solid rgba(148, 163, 184, 0.15);
    }
    
    .ps-reco-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-bottom: 0.75rem;
        text-align: center;
    }
    
    .ps-reco-subtitle {
        font-size: 0.9rem;
        color: #94A3B8;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    
    .ps-reco-message-card {
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid rgba(245, 158, 11, 0.3);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    
    .ps-reco-message-card p {
        font-size: 1rem;
        color: #F8FAFC;
        line-height: 1.6;
        margin: 0;
    }
    
    .ps-reco-summary-card {
        background: rgba(15, 23, 42, 0.4);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-top: 1rem;
        text-align: center;
    }
    
    .ps-reco-summary-card p {
        font-size: 0.8rem;
        color: #94A3B8;
        margin: 0;
    }
    
    /* 블록 3: STEP 가이드 (압축) */
    .ps-step-guide-compact {
        margin-top: 1rem;
    }
    
    .ps-step-guide-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    
    .ps-step-buttons-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
    }
    
    .ps-step-button {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.6) 100%);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 12px;
        padding: 1.5rem 1rem;
        text-align: center;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .ps-step-button:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(59, 130, 246, 0.4);
        border-color: rgba(59, 130, 246, 0.6);
    }
    
    .ps-step-button.step-1 {
        border-color: rgba(59, 130, 246, 0.4);
    }
    
    .ps-step-button.step-2 {
        border-color: rgba(16, 185, 129, 0.4);
    }
    
    .ps-step-button.step-3 {
        border-color: rgba(168, 85, 247, 0.4);
    }
    
    .ps-step-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    
    .ps-step-name {
        font-size: 1rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-bottom: 0.25rem;
    }
    
    .ps-step-desc {
        font-size: 0.75rem;
        color: #94A3B8;
    }
    
    /* 앱 가이드 블록 (맥락 추가) */
    .ps-app-guide {
        background: rgba(15, 23, 42, 0.4);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin: 0 0 2.5rem 0;
        text-align: center;
    }
    
    .ps-app-guide p {
        font-size: 0.95rem;
        color: #94A3B8;
        line-height: 1.7;
        margin: 0.5rem 0;
    }
    
    .ps-app-guide p:first-child {
        font-size: 1.05rem;
        color: #E2E8F0;
        font-weight: 500;
    }
    
    /* STEP 카드 (설명 포함) */
    .ps-step-card-full {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.85) 0%, rgba(15, 23, 42, 0.75) 100%);
        border-radius: 16px;
        padding: 2rem;
        margin: 0 0 1.5rem 0;
        border: 1px solid rgba(59, 130, 246, 0.3);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .ps-step-card-full::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        border-radius: 16px 16px 0 0;
    }
    
    .ps-step-card-full.step-1::before {
        background: linear-gradient(90deg, #3B82F6 0%, #60A5FA 50%, #3B82F6 100%);
    }
    
    .ps-step-card-full.step-2::before {
        background: linear-gradient(90deg, #10B981 0%, #34D399 50%, #10B981 100%);
    }
    
    .ps-step-card-full.step-3::before {
        background: linear-gradient(90deg, #A855F7 0%, #C084FC 50%, #A855F7 100%);
    }
    
    .ps-step-title-full {
        font-size: 1.5rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-bottom: 0.5rem;
    }
    
    .ps-step-subtitle-full {
        font-size: 1rem;
        font-weight: 500;
        color: #94A3B8;
        margin-bottom: 1rem;
        font-style: italic;
    }
    
    .ps-step-desc-full {
        font-size: 0.9rem;
        color: #CBD5E1;
        line-height: 1.6;
        margin-bottom: 1.5rem;
    }
    
    /* 반응형 */
    @media (max-width: 768px) {
        .ps-step-buttons-grid {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    
    # ============================================
    # SECTION 1: 브랜드 히어로
    # ============================================
    st.markdown("""
    <div class="ps-brand-hero">
        <div class="ps-brand-hero-content">
            <div class="ps-brand-name">CAUSE OS</div>
            <div class="ps-brand-tagline">
                우리는 매출을 보지 않습니다.<br>
                원인을 봅니다.
            </div>
            <div class="ps-brand-subtitle">사장을 위한 숫자 운영체제</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 메인 CTA 버튼
    if st.button("오늘 숫자 입력하기", type="primary", use_container_width=True, key="test_brand_hero_cta"):
        st.info("테스트: 일일 입력(통합) 페이지로 이동")
    
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    
    # ============================================
    # SECTION 2: 오늘의 액션 센터 (통합)
    # ============================================
    st.markdown("""
    <div class="ps-action-center">
        <!-- 블록 1: 상태 요약 -->
        <div class="ps-status-summary">
            <div class="ps-status-summary-title">📍 오늘 당신의 매장은</div>
    """, unsafe_allow_html=True)
    
    # 상태 미니 카드 3개
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
    
    st.markdown("""
        </div>
        
        <!-- 블록 2: 오늘 추천 -->
        <div class="ps-today-reco">
            <div class="ps-reco-title">🎯 오늘 우리 매장 추천</div>
            <div class="ps-reco-subtitle">이 앱이 오늘 데이터를 보고 판단한, 가장 우선해야 할 한 가지입니다.</div>
            <div class="ps-reco-message-card">
                <p>{}</p>
            </div>
    """.format(reco_message), unsafe_allow_html=True)
    
    # 액션 버튼
    if st.button(f"▶ {action_label}", type="primary", use_container_width=True, key="test_reco_action_btn"):
        st.info("테스트: 추천 액션 실행")
    
    # 7일 요약
    st.markdown(f"""
            <div class="ps-reco-summary-card">
                <p>📊 최근 7일 코치 기록: 추천 {shown_count}회 · 실행 {clicked_count}회</p>
            </div>
        </div>
        
        <!-- 블록 3: STEP 가이드 (압축) -->
        <div class="ps-step-guide-compact">
            <div class="ps-step-guide-title">3단계 운영 흐름</div>
            <div class="ps-step-buttons-grid">
    """, unsafe_allow_html=True)
    
    # STEP 버튼 그룹 (3개 컬럼)
    step_col1, step_col2, step_col3 = st.columns(3)
    
    with step_col1:
        st.markdown("""
        <div class="ps-step-button step-1">
            <div class="ps-step-icon">📝</div>
            <div class="ps-step-name">STEP 1: 입력</div>
            <div class="ps-step-desc">데이터 자산 만들기</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("▶ 입력하기", type="primary", use_container_width=True, key="test_step1_btn"):
            st.info("테스트: 입력 허브로 이동")
    
    with step_col2:
        st.markdown("""
        <div class="ps-step-button step-2">
            <div class="ps-step-icon">📊</div>
            <div class="ps-step-name">STEP 2: 분석</div>
            <div class="ps-step-desc">숫자가 말하는 문제</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("▶ 분석하기", type="primary", use_container_width=True, key="test_step2_btn"):
            st.info("테스트: 분석 허브로 이동")
    
    with step_col3:
        st.markdown("""
        <div class="ps-step-button step-3">
            <div class="ps-step-icon">🎯</div>
            <div class="ps-step-name">STEP 3: 설계</div>
            <div class="ps-step-desc">행동으로 바꾸기</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("▶ 설계하기", type="primary", use_container_width=True, key="test_step3_btn"):
            st.info("테스트: 전략 센터로 이동")
    
    st.markdown("""
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 비교 안내
    st.markdown("---")
    st.info("💡 **위: 통합형 2단 구조 (상태+추천+STEP 통합)**")
    
    st.markdown("---")
    st.markdown("### 🎯 최대 간결형 + 맥락 추가 버전")
    st.caption("상태+추천 제거 + 앱 설명 블록 추가 + STEP 설명 포함")
    
    # ============================================
    # 맥락 추가 버전: 히어로 + 앱 가이드 + STEP (설명 포함)
    # ============================================
    st.markdown("""
    <div class="ps-brand-hero">
        <div class="ps-brand-hero-content">
            <div class="ps-brand-name">CAUSE OS</div>
            <div class="ps-brand-tagline">
                우리는 매출을 보지 않습니다.<br>
                원인을 봅니다.
            </div>
            <div class="ps-brand-subtitle">사장을 위한 숫자 운영체제</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 메인 CTA 버튼
    if st.button("오늘 숫자 입력하기", type="primary", use_container_width=True, key="test_brand_hero_cta_context"):
        st.info("테스트: 일일 입력(통합) 페이지로 이동")
    
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    
    # 앱 가이드 블록 (맥락 추가)
    st.markdown("""
    <div class="ps-app-guide">
        <p>입력 → 분석 → 설계 3단계로 매장을 데이터 기반으로 운영합니다.</p>
        <p>레시피만 등록하면 원가율이 자동 계산되고, 원가율 5% 개선으로 월 100만원 추가 이익을 만들 수 있습니다.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    
    # STEP 1: 입력 (설명 포함)
    st.markdown("""
    <div class="ps-step-card-full step-1">
        <div class="ps-step-title-full">STEP 1. 입력</div>
        <div class="ps-step-subtitle-full">매장을 '데이터 자산'으로 만든다</div>
        <div class="ps-step-desc-full">
            메뉴, 재료, 레시피, 매출, 비용을 입력하면 분석과 전략이 자동으로 작동합니다.<br>
            입력은 기록이 아니라 매장을 시스템으로 만드는 작업입니다.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1_v3, col2_v3 = st.columns(2)
    with col1_v3:
        if st.button("▶ 오늘 입력하기", type="primary", use_container_width=True, key="test_step1_btn_v3"):
            st.info("테스트: 일일 입력(통합) 페이지로 이동")
    with col2_v3:
        if st.button("▶ 데이터 입력센터", type="secondary", use_container_width=True, key="test_step1_btn2_v3"):
            st.info("테스트: 입력 허브로 이동")
    
    # STEP 2: 분석 (설명 포함)
    st.markdown("""
    <div class="ps-step-card-full step-2">
        <div class="ps-step-title-full">STEP 2. 분석</div>
        <div class="ps-step-subtitle-full">숫자가 문제를 말해준다</div>
        <div class="ps-step-desc-full">
            분석은 보고서가 아니라 "왜 이런 결과가 나왔는지"를 알려주는 엔진입니다.<br>
            매출이 왜 이 숫자인지, 어디서 새고 있는지, 무엇을 키워야 하는지를 데이터로 확인합니다.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("▶ 데이터 분석센터", type="primary", use_container_width=True, key="test_step2_btn_v3"):
        st.info("테스트: 분석 허브로 이동")
    
    # STEP 3: 설계 (설명 포함)
    st.markdown("""
    <div class="ps-step-card-full step-3">
        <div class="ps-step-title-full">STEP 3. 설계</div>
        <div class="ps-step-subtitle-full">숫자를 행동으로 바꾼다</div>
        <div class="ps-step-desc-full">
            설계는 조언이 아니라 사장의 '다음 행동'을 만드는 단계입니다.<br>
            개선 우선순위, 전략 보드, 메뉴/비용/운영 방향을 데이터 기반으로 결정합니다.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("▶ 가게 전략 센터", type="primary", use_container_width=True, key="test_step3_btn_v3"):
        st.info("테스트: 전략 센터로 이동")
    
    # 비교 요약
    st.markdown("---")
    st.success("✅ **맥락 추가 버전의 특징:**")
    st.markdown("""
    - 섹션 수: 4개 (히어로 + 가이드 + STEP 3개)
    - 간결함 유지하면서 앱 설명 추가
    - 각 STEP에 활용 맥락 포함
    - "어렵다"는 느낌 해소 + 이해도 향상
    """)
    
    st.info("💡 **구조:** 브랜드 히어로 → 앱 가이드(얇은 설명) → STEP 1-3(각각 설명 포함)")
