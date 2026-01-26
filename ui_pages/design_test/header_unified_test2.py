"""
홈화면 리뉴얼 테스트 페이지 2
다양한 디자인 변형 테스트
"""
import streamlit as st


def render_header_unified_test2():
    """홈화면 리뉴얼 구조 테스트 2 - 디자인 변형"""
    
    st.title("🎨 홈화면 리뉴얼 테스트 2")
    st.caption("디자인 변형 및 실험 페이지")
    
    # 리뉴얼 CSS
    css = """
    <style>
    /* 테스트 페이지 2 전용 스타일 */
    .test2-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem;
    }
    
    .test2-section {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.9) 100%);
        border-radius: 24px;
        padding: 3rem;
        margin-bottom: 2rem;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        border: 1px solid rgba(59, 130, 246, 0.2);
    }
    
    .test2-title {
        font-size: 2rem;
        font-weight: 800;
        color: #F8FAFC;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #60A5FA 0%, #3B82F6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .test2-description {
        font-size: 1.1rem;
        color: #CBD5E1;
        line-height: 1.6;
        margin-bottom: 2rem;
    }
    
    .test2-card {
        background: rgba(30, 41, 59, 0.6);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(59, 130, 246, 0.3);
        transition: all 0.3s ease;
    }
    
    .test2-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(59, 130, 246, 0.2);
        border-color: rgba(59, 130, 246, 0.5);
    }
    
    .test2-card-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-bottom: 0.5rem;
    }
    
    .test2-card-content {
        font-size: 1rem;
        color: #94A3B8;
        line-height: 1.6;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    
    # ============================================
    # 테스트 섹션들
    # ============================================
    st.markdown("""
    <div class="test2-container">
        <div class="test2-section">
            <div class="test2-title">테스트 페이지 2</div>
            <div class="test2-description">
                이 페이지는 다양한 디자인 변형과 실험을 위한 공간입니다.
            </div>
            
            <div class="test2-card">
                <div class="test2-card-title">카드 1: 기본 스타일</div>
                <div class="test2-card-content">
                    이것은 기본 스타일의 카드입니다. 호버 효과가 적용되어 있습니다.
                </div>
            </div>
            
            <div class="test2-card">
                <div class="test2-card-title">카드 2: 디자인 변형</div>
                <div class="test2-card-content">
                    다양한 디자인 변형을 테스트할 수 있는 공간입니다.
                </div>
            </div>
            
            <div class="test2-card">
                <div class="test2-card-title">카드 3: 실험 공간</div>
                <div class="test2-card-content">
                    새로운 UI/UX 아이디어를 실험해볼 수 있습니다.
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 추가 테스트 컨텐츠
    st.markdown("---")
    st.subheader("추가 테스트 영역")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("왼쪽 컬럼: 다양한 위젯 테스트")
        st.button("테스트 버튼 1", key="test2_btn1")
        st.slider("테스트 슬라이더", 0, 100, 50, key="test2_slider1")
    
    with col2:
        st.info("오른쪽 컬럼: 추가 기능 테스트")
        st.button("테스트 버튼 2", key="test2_btn2")
        st.selectbox("테스트 선택박스", ["옵션 1", "옵션 2", "옵션 3"], key="test2_select")
