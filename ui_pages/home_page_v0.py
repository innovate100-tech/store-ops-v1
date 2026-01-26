"""
홈 화면 (HOME v2)
CAUSE OS 브랜드 첫 화면 + 오늘 행동 시작점
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


def render_brand_hero():
    """
    CAUSE OS 브랜드 히어로 영역
    홈 화면 최상단에 표시되는 브랜드 정체성 영역
    """
    pass


def render_home():
    """
    HOME v2 - CAUSE OS 브랜드 첫 화면 + 오늘 행동 시작점
    """
    pass
