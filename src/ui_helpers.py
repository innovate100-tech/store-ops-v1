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
    
    # 개발모드에서만 DB CLIENT MODE 표시
    try:
        from src.storage_supabase import get_client_mode
        from src.auth import is_dev_mode
        
        if is_dev_mode():
            client_mode = get_client_mode()
            if client_mode == "service_role_dev":
                st.info(f"🔧 **DB CLIENT MODE: service_role_dev** (DEV MODE 전용, RLS 우회)")
            elif client_mode == "anon":
                st.caption(f"🔧 **DB CLIENT MODE: anon** (일반 모드)")
            else:
                st.caption(f"🔧 **DB CLIENT MODE: {client_mode}**")
    except Exception:
        pass  # 표시 실패해도 페이지는 계속 동작


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
# Phase 0 STEP 2: Supabase 응답 안전 접근 헬퍼
# ============================================

def safe_first(list_like: Optional[list], default: Any = None) -> Any:
    """
    리스트/배열에서 첫 번째 요소를 안전하게 가져옴
    
    Args:
        list_like: 리스트 또는 배열 (None 가능)
        default: 비어있을 때 반환할 기본값
    
    Returns:
        첫 번째 요소 또는 기본값
    """
    if not list_like or len(list_like) == 0:
        return default
    try:
        return list_like[0]
    except (IndexError, TypeError) as e:
        logger.warning(f"safe_first: 접근 실패 - {e}")
        return default


def safe_resp_first_data(resp, default: Any = None) -> Any:
    """
    Supabase 응답 객체에서 첫 번째 데이터를 안전하게 가져옴
    
    Args:
        resp: Supabase 응답 객체 (result.data 속성 가짐)
        default: 데이터가 없을 때 반환할 기본값
    
    Returns:
        첫 번째 데이터 딕셔너리 또는 기본값
    """
    if resp is None:
        return default
    
    try:
        if not hasattr(resp, 'data'):
            logger.warning("safe_resp_first_data: 응답 객체에 'data' 속성이 없음")
            return default
        
        if not resp.data or len(resp.data) == 0:
            return default
        
        return resp.data[0]
    except (IndexError, AttributeError, TypeError) as e:
        logger.warning(f"safe_resp_first_data: 접근 실패 - {e}")
        return default


def require(condition: bool, message: str):
    """
    조건이 불만족 시 ValueError를 발생시킴
    
    Args:
        condition: 확인할 조건
        message: 조건 불만족 시 에러 메시지
    
    Raises:
        ValueError: 조건이 False일 때
    """
    if not condition:
        raise ValueError(message)


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


# ============================================
# Phase 3: 에러 메시지 표준화
# ============================================

class AppError(Exception):
    """애플리케이션 표준 에러 클래스"""
    def __init__(self, error_code: str, user_message: str, technical_message: str = None):
        self.error_code = error_code
        self.user_message = user_message
        self.technical_message = technical_message
        super().__init__(self.user_message)


def format_error_message(error_code: str, user_message: str, technical_details: str = None) -> str:
    """
    표준화된 에러 메시지 포맷
    
    Args:
        error_code: 에러 코드 (예: "ERR_DATA_LOAD_001")
        user_message: 사용자에게 보여줄 메시지
        technical_details: 기술적 상세 정보 (디버깅용, 선택적)
    
    Returns:
        포맷된 에러 메시지
    """
    if technical_details:
        logger.error(f"[{error_code}] {user_message} | 기술적 상세: {technical_details}")
    else:
        logger.error(f"[{error_code}] {user_message}")
    
    return f"⚠️ {user_message}"


def handle_data_error(operation: str, error: Exception, default_message: str = None) -> str:
    """
    데이터 관련 에러를 표준화된 형식으로 처리
    
    Args:
        operation: 수행 중이던 작업 (예: "매출 데이터 저장")
        error: 발생한 예외
        default_message: 기본 메시지 (없으면 자동 생성)
    
    Returns:
        사용자에게 표시할 에러 메시지
    """
    error_type = type(error).__name__
    
    if "No store_id found" in str(error):
        return format_error_message(
            "ERR_AUTH_001",
            "로그인 정보를 찾을 수 없습니다. 로그아웃 후 다시 로그인해주세요.",
            str(error)
        )
    elif "Supabase not available" in str(error) or "Supabase client" in str(error):
        return format_error_message(
            "ERR_CONN_001",
            "데이터베이스 연결에 실패했습니다. 잠시 후 다시 시도해주세요.",
            str(error)
        )
    elif "IndexError" in error_type or "KeyError" in error_type:
        return format_error_message(
            "ERR_DATA_001",
            f"{operation} 중 데이터를 찾을 수 없습니다. 데이터가 올바르게 입력되었는지 확인해주세요.",
            str(error)
        )
    elif default_message:
        return format_error_message(
            "ERR_GENERAL_001",
            default_message,
            str(error)
        )
    else:
        return format_error_message(
            "ERR_GENERAL_002",
            f"{operation} 중 오류가 발생했습니다. 문제가 지속되면 관리자에게 문의해주세요.",
            str(error)
        )


# ============================================
# Phase 4: 발주 관리 공통 유틸리티 함수
# ============================================

def format_quantity_with_unit(quantity: float, unit: str, decimal_places: int = 2) -> str:
    """수량을 단위와 함께 포맷팅"""
    return f"{quantity:,.{decimal_places}f} {unit}"


def format_price_with_unit(price: float, unit: str, decimal_places: int = 1) -> str:
    """가격을 단위와 함께 포맷팅"""
    return f"{price:,.{decimal_places}f}원/{unit}"


def convert_to_order_unit(base_qty: float, conversion_rate: float) -> float:
    """기본 단위 → 발주 단위 변환"""
    if conversion_rate == 0:
        return base_qty
    return base_qty / conversion_rate


def convert_to_base_unit(order_qty: float, conversion_rate: float) -> float:
    """발주 단위 → 기본 단위 변환"""
    return order_qty * conversion_rate


def merge_ingredient_with_inventory(ingredient_df: pd.DataFrame, inventory_df: pd.DataFrame) -> pd.DataFrame:
    """재료 정보와 재고 정보 조인 (공통 패턴)"""
    if ingredient_df.empty:
        return pd.DataFrame()
    
    ingredient_cols = ['재료명', '단위', '단가', '발주단위', '변환비율']
    available_cols = [col for col in ingredient_cols if col in ingredient_df.columns]
    
    inventory_cols = ['재료명', '현재고', '안전재고']
    available_inventory_cols = [col for col in inventory_cols if col in inventory_df.columns] if not inventory_df.empty else ['재료명']
    
    result = pd.merge(
        ingredient_df[available_cols],
        inventory_df[available_inventory_cols] if not inventory_df.empty else pd.DataFrame(columns=['재료명']),
        on='재료명',
        how='left'
    )
    
    # 기본값 처리
    if '발주단위' in result.columns and '단위' in result.columns:
        result['발주단위'] = result['발주단위'].fillna(result['단위'])
    elif '발주단위' in result.columns:
        result['발주단위'] = result['발주단위'].fillna('')
    if '변환비율' in result.columns:
        result['변환비율'] = result['변환비율'].fillna(1.0)
    if '단가' in result.columns:
        result['단가'] = result['단가'].fillna(0.0)
    if '현재고' in result.columns:
        result['현재고'] = result['현재고'].fillna(0.0)
    if '안전재고' in result.columns:
        result['안전재고'] = result['안전재고'].fillna(0.0)
    
    return result
