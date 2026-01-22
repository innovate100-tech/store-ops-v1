"""
UI 스크롤 제어 유틸리티
"""
import streamlit as st
import streamlit.components.v1 as components


def scroll_to_top(behavior: str = "auto"):
    """
    페이지 스크롤을 최상단으로 이동
    
    Args:
        behavior: 스크롤 동작 ('instant', 'smooth', 'auto')
            - 'instant': 즉시 이동
            - 'smooth': 부드럽게 이동
            - 'auto': 브라우저 기본 동작 (기본값)
    
    Note:
        - parent.window.scrollTo를 사용하여 메인 페이지를 스크롤
        - requestAnimationFrame으로 DOM 타이밍 문제 방지
        - iframe 내부에서 실행되므로 parent window를 타겟으로 함
    """
    try:
        # JavaScript로 메인 페이지 스크롤을 최상단으로 이동
        # parent.window.scrollTo를 사용하여 iframe이 아닌 메인 페이지를 스크롤
        # requestAnimationFrame으로 한 프레임 뒤 실행하여 DOM 타이밍 문제 방지
        # height=0, width=0으로 설정하여 화면에 보이지 않게 함
        components.html(
            f"""
            <script>
                requestAnimationFrame(() => {{
                    try {{
                        // 메인 페이지(부모 윈도우) 스크롤
                        parent.window.scrollTo({{
                            top: 0,
                            left: 0,
                            behavior: '{behavior}'
                        }});
                    }} catch (e) {{
                        // parent 접근 실패 시 현재 window 스크롤 (폴백)
                        window.scrollTo({{
                            top: 0,
                            left: 0,
                            behavior: '{behavior}'
                        }});
                    }}
                }});
            </script>
            """,
            height=0,
            width=0,
        )
    except Exception:
        # components.html 실패 시 무시 (안정성)
        pass
