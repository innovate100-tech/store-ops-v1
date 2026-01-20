"""
UI 헬퍼 함수 모듈 (디자인 개선)
"""
import streamlit as st
import pandas as pd
from typing import Optional, Any, Dict
import logging

logger = logging.getLogger(__name__)


def render_page_header(title, icon="📋"):
    """페이지 헤더 렌더링 (개선된 디자인)

    화이트/다크 테마 상관없이 제목 텍스트는 항상 흰색으로 표시.
    배경은 각 페이지의 레이아웃/CSS에서 제어하도록 분리한다.
    """
    st.markdown(f"""
    <div style="margin-bottom: 2rem;">
        <h2 style="color: #ffffff; border-bottom: 3px solid #667eea; padding-bottom: 0.5rem; margin-bottom: 1rem;">
            {icon} {title}
        </h2>
    </div>
    """, unsafe_allow_html=True)


def render_section_header(title, icon="📋"):
    """섹션 헤더 렌더링 (개선된 디자인)"""
    st.markdown(f"""
    <div style="margin: 2rem 0 1rem 0;">
        <h3 style="color: #2c3e50; font-weight: 600; margin: 0;">
            {icon} {title}
        </h3>
    </div>
    """, unsafe_allow_html=True)


def render_section_divider():
    """섹션 구분선 렌더링"""
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)


# ============================================
# Phase 1: 안전한 DataFrame 접근 헬퍼 함수
# ============================================

def safe_get_first_row(df: pd.DataFrame, default: Optional[Dict[str, Any]] = None) -> Optional[pd.Series]:
    """
    DataFrame에서 첫 번째 행을 안전하게 가져옴
    
    Args:
        df: pandas DataFrame
        default: 빈 DataFrame일 때 반환할 기본값 (None이면 None 반환)
    
    Returns:
        첫 번째 행 (Series) 또는 None/기본값
    """
    if df is None or df.empty:
        if default is not None:
            return pd.Series(default)
        return None
    
    try:
        return df.iloc[0]
    except (IndexError, KeyError) as e:
        logger.warning(f"safe_get_first_row: IndexError/KeyError - {e}")
        if default is not None:
            return pd.Series(default)
        return None


def safe_get_value(df: pd.DataFrame, column: str, default: Any = None) -> Any:
    """
    DataFrame의 첫 번째 행에서 특정 컬럼 값을 안전하게 가져옴
    
    Args:
        df: pandas DataFrame
        column: 컬럼명
        default: 값이 없을 때 반환할 기본값
    
    Returns:
        컬럼 값 또는 기본값
    """
    if df is None or df.empty:
        return default
    
    try:
        first_row = df.iloc[0]
        return first_row.get(column, default)
    except (IndexError, KeyError) as e:
        logger.warning(f"safe_get_value: IndexError/KeyError for column '{column}' - {e}")
        return default


def safe_get_row_by_condition(df: pd.DataFrame, condition, default: Optional[Dict[str, Any]] = None) -> Optional[pd.Series]:
    """
    조건에 맞는 첫 번째 행을 안전하게 가져옴
    
    Args:
        df: pandas DataFrame
        condition: boolean Series 또는 조건식
        default: 조건에 맞는 행이 없을 때 반환할 기본값
    
    Returns:
        조건에 맞는 첫 번째 행 (Series) 또는 None/기본값
    """
    if df is None or df.empty:
        if default is not None:
            return pd.Series(default)
        return None
    
    try:
        filtered = df[condition]
        if filtered.empty:
            if default is not None:
                return pd.Series(default)
            return None
        return filtered.iloc[0]
    except (IndexError, KeyError) as e:
        logger.warning(f"safe_get_row_by_condition: IndexError/KeyError - {e}")
        if default is not None:
            return pd.Series(default)
        return None


# ============================================
# Phase 2: 리소스 관리 - 안전한 캐시 클리어
# ============================================

def safe_clear_cache(cache_func=None, filename: str = None):
    """
    캐시를 안전하게 클리어 (리소스 누수 방지)
    
    Args:
        cache_func: 클리어할 캐시 함수 (예: load_csv)
        filename: 특정 파일의 캐시만 클리어할 경우 파일명
    
    Returns:
        성공 여부 (bool)
    """
    try:
        if cache_func:
            if filename:
                # 특정 파일의 캐시만 클리어 (가능한 경우)
                # Streamlit의 캐시는 함수별로 관리되므로 전체 클리어
                cache_func.clear()
            else:
                cache_func.clear()
        else:
            # 전체 캐시 클리어 (최후의 수단)
            import streamlit as st
            st.cache_data.clear()
        return True
    except Exception as e:
        logger.warning(f"캐시 클리어 실패: {e}")
        return False
