"""
CSS Manager: CSS 주입 통합 관리 모듈
모든 CSS 주입을 단일 창구로 통합하여 계층별 관리

계층 구조:
- BASE: CSS 변수, 폰트, reset (1회 주입)
- THEME: 다크모드, 기본 버튼/사이드바 기본 구조 (1회 주입)
- FX: Ultra, 배경, 애니메이션, glow (1회 주입)
- DOM: form_kit, input_layouts, 페이지 박스, sidebar 꾸밈 (rerun마다 주입)
- RESCUE: FINAL_SAFETY_PIN (1회 주입)
"""
import streamlit as st

try:
    from src.debug.nav_trace import push_render_step
except ImportError:
    def push_render_step(*args, **kwargs):
        pass


def _inject_once(layer: str, css: str, key: str, name: str):
    """
    1회 주입 계층 (TYPE A) 내부 함수
    
    Args:
        layer: 계층명 (BASE/THEME/FX/RESCUE)
        css: CSS 문자열
        key: session_state 키
        name: 로그용 이름
    """
    if st.session_state.get(key, False):
        return
    
    st.markdown(css, unsafe_allow_html=True)
    push_render_step(f"CSS_{layer}_INJECT", extra={"where": layer.lower(), "name": name})
    st.session_state[key] = True


def _inject_always(layer: str, css: str, name: str, scope: str = None):
    """
    DOM 종속 계층 (TYPE B) 내부 함수
    
    Args:
        layer: 계층명 (DOM)
        css: CSS 문자열
        name: 로그용 이름
        scope: 스코프 ID (선택사항)
    """
    st.markdown(css, unsafe_allow_html=True)
    extra = {"where": layer.lower(), "name": name}
    if scope:
        extra["scope"] = scope
    push_render_step(f"CSS_{layer}_INJECT", extra=extra)


# ============================================
# TYPE A: 1회 주입 계층
# ============================================

def inject_base(css: str, name: str):
    """
    BASE 계층 CSS 주입 (1회만)
    
    Args:
        css: CSS 문자열
        name: 식별자 이름
    """
    key = f"_ps_css_base_{name}"
    _inject_once("BASE", css, key, name)


def inject_theme(css: str, name: str):
    """
    THEME 계층 CSS 주입 (1회만)
    
    Args:
        css: CSS 문자열
        name: 식별자 이름
    """
    key = f"_ps_css_theme_{name}"
    _inject_once("THEME", css, key, name)


def inject_fx(css: str, name: str):
    """
    FX 계층 CSS 주입 (1회만)
    
    Args:
        css: CSS 문자열
        name: 식별자 이름
    """
    key = f"_ps_css_fx_{name}"
    _inject_once("FX", css, key, name)


def inject_rescue(css: str, name: str):
    """
    RESCUE 계층 CSS 주입 (1회만)
    
    Args:
        css: CSS 문자열
        name: 식별자 이름
    """
    key = f"_ps_css_rescue_{name}"
    _inject_once("RESCUE", css, key, name)


# ============================================
# TYPE B: DOM 종속 계층
# ============================================

def inject_dom(css: str, name: str, scope: str = None):
    """
    DOM 계층 CSS 주입 (rerun마다)
    
    Args:
        css: CSS 문자열
        name: 식별자 이름
        scope: 스코프 ID (선택사항)
    """
    _inject_always("DOM", css, name, scope)
