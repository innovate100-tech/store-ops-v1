"""
공통 페이지 설정 모듈
모든 페이지에서 공통으로 사용하는 setup 로직
"""
import streamlit as st


def bootstrap(page_title: str = "황승진 외식경영 의사결정도구"):
    """
    공통 페이지 설정 적용
    
    Args:
        page_title: 페이지 제목 (기본값: "황승진 외식경영 의사결정도구")
    """
    # 페이지 설정은 최상단에 위치 (다른 st.* 호출 전에)
    try:
        st.set_page_config(
            page_title=page_title,
            page_icon="🍽️",
            layout="wide",
            initial_sidebar_state="expanded",  # 사이드바 항상 열림
            menu_items={
                'Get Help': None,
                'Report a bug': None,
                'About': None
            }
        )
    except Exception:
        # 이미 설정된 경우 무시
        pass
    
    # 테마 상태 초기화 (기본: 화이트 모드)
    if "theme" not in st.session_state:
        st.session_state.theme = "light"
    
    # DEV MODE 체크 (로컬 개발용) - import 시 DB 호출 없음
    from src.auth import apply_dev_mode_session
    apply_dev_mode_session()
