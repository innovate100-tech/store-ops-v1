"""
홈 페이지
메인 헤더 표시
"""
from src.bootstrap import bootstrap
import streamlit as st

# 공통 설정 적용
bootstrap(page_title="Home")

# 커스텀 CSS 적용 (헤더 스타일만 - app.py와 동일)
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Noto Sans KR', sans-serif !important;
    }
    
    /* ========== 반응형 기본 설정 ========== */
    :root {
        --mobile-breakpoint: 768px;
        --tablet-breakpoint: 1024px;
    }
    
    /* ========== 메인 헤더 CSS는 src/ui/common_header.py에서 관리 ========== */
    /* 중복 제거: common_header.py에서 자동으로 주입/교체됨 */
</style>
""", unsafe_allow_html=True)

# 헤더는 app.py에서 공통으로 렌더되므로 여기서는 제거
# (common_header.py에서 자동으로 주입/교체됨)
