"""
FormKit v2: 입력센터 제품급 입력 컴포넌트 시스템
"사장 전용 숫자 코치" 앱에 맞는 계기판 스타일 입력 컴포넌트

등급 체계:
- Primary: 핵심 수치 (매출, 비용, 목표, 판매량, 사용량, 재고)
- Secondary: 조정/조건 입력 (날짜, 카테고리, 상태, 옵션)
- Tertiary: 설명/보조 (메모, 조리법, 비고)
"""
import streamlit as st
from typing import Optional, Union, Callable, Dict, Any, List
import re
import hashlib

# ============================================
# 시각 스펙 상수 (고정값)
# ============================================
PRIMARY_INPUT_HEIGHT = 56  # px
PRIMARY_INPUT_FONT_SIZE = 22  # px
PRIMARY_INPUT_FONT_WEIGHT = 600
PRIMARY_INPUT_BORDER_RADIUS = 14  # px
PRIMARY_INPUT_PADDING_RIGHT = 120  # px (단위 박스 공간)

SECONDARY_INPUT_HEIGHT = 40  # px
SECONDARY_INPUT_FONT_SIZE = 14  # px

UNIT_BOX_FONT_SIZE = 13  # px
UNIT_BOX_HEIGHT = 40  # px
UNIT_BOX_PADDING_H = 10  # px

INPUT_BLOCK_PADDING = 16  # px
INPUT_BLOCK_BORDER_RADIUS = 14  # px
INPUT_BLOCK_MARGIN_BOTTOM = 16  # px

RESPONSIVE_BREAKPOINT = 900  # px (이하에서 1열로 변경)


# FormKit v2 CSS (입력 전용 스코프 - data-ps-scope 기반)
def _generate_form_kit_v2_css() -> str:
    """FormKit v2 CSS 생성 (data-ps-scope 기반 스코프)"""
    return f"""
<style>
/* ============================================
   스코프 기반 스타일 (data-ps-scope 속성 사용)
   ============================================ */
[data-ps-scope] {{
    /* 입력 전용 스코프 */
}}

/* ============================================
   Primary Input 스타일 (핵심 수치)
   ============================================ */
[data-ps-scope] .ps-primary-input-wrapper {{
    position: relative;
    margin-bottom: {INPUT_BLOCK_MARGIN_BOTTOM}px;
}}

[data-ps-scope] .ps-primary-input {{
    width: 100%;
    height: {PRIMARY_INPUT_HEIGHT}px;
    font-size: {PRIMARY_INPUT_FONT_SIZE}px;
    font-weight: {PRIMARY_INPUT_FONT_WEIGHT};
    color: #F8FAFC;
    background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03));
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: {PRIMARY_INPUT_BORDER_RADIUS}px;
    padding: 0 {PRIMARY_INPUT_PADDING_RIGHT}px 0 16px;
    transition: all 0.2s ease;
    outline: none;
}}

[data-ps-scope] .ps-primary-input::placeholder {{
    color: rgba(248,250,252,0.35);
}}

[data-ps-scope] .ps-primary-input:focus {{
    border: 1px solid rgba(96,165,250,0.9);
    box-shadow: 
        0 0 0 3px rgba(59,130,246,0.25),
        0 6px 20px rgba(0,0,0,0.4);
    background: linear-gradient(180deg, rgba(255,255,255,0.12), rgba(255,255,255,0.06));
}}

[data-ps-scope] .ps-primary-input:disabled {{
    opacity: 0.5;
    cursor: not-allowed;
}}

/* 상태별 스타일 */
[data-ps-scope] .ps-primary-input.ps-status-warn {{
    border-color: rgba(245,158,11,0.8);
    box-shadow: 0 0 0 2px rgba(245,158,11,0.2);
}}

[data-ps-scope] .ps-primary-input.ps-status-danger {{
    border-color: rgba(239,68,68,0.8);
    box-shadow: 0 0 0 2px rgba(239,68,68,0.2);
}}

[data-ps-scope] .ps-primary-input.ps-status-ok {{
    border-color: rgba(59,130,246,0.8);
}}

/* 단위 박스 (::after 사용, pointer-events:none 필수) */
[data-ps-scope] .ps-primary-input-wrapper::after {{
    content: attr(data-unit);
    position: absolute;
    right: 8px;
    top: 50%;
    transform: translateY(-50%);
    background: rgba(255,255,255,0.06);
    border-left: 1px solid rgba(255,255,255,0.12);
    padding: 0 {UNIT_BOX_PADDING_H}px;
    height: {UNIT_BOX_HEIGHT}px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: {UNIT_BOX_FONT_SIZE}px;
    color: rgba(248,250,252,0.8);
    border-radius: 0 10px 10px 0;
    pointer-events: none; /* 클릭 방해 방지 */
    z-index: 10;
}}

/* 반응형: 좁은 화면에서 단위 박스 숨김 */
@media (max-width: {RESPONSIVE_BREAKPOINT}px) {{
    [data-ps-scope] .ps-primary-input-wrapper::after {{
        display: none;
    }}
    [data-ps-scope] .ps-primary-input-wrapper [data-testid="stNumberInput"] > div > div {{
        padding-right: 16px !important;
    }}
}}

/* ============================================
   Secondary Input 스타일 (조정/조건)
   ============================================ */
[data-ps-scope] .ps-secondary-input {{
    width: 100%;
    height: {SECONDARY_INPUT_HEIGHT}px;
    font-size: {SECONDARY_INPUT_FONT_SIZE}px;
    color: #F8FAFC;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 8px;
    padding: 0 12px;
    transition: all 0.15s ease;
    outline: none;
}}

[data-ps-scope] .ps-secondary-input:focus {{
    outline: 2px solid rgba(96,165,250,0.5);
    outline-offset: 2px;
    border-color: rgba(96,165,250,0.6);
}}

[data-ps-scope] .ps-secondary-input:disabled {{
    opacity: 0.5;
    cursor: not-allowed;
}}

/* ============================================
   Input Block (입력 블록 컨테이너)
   ============================================ */
[data-ps-scope] .ps-input-block {{
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: {INPUT_BLOCK_BORDER_RADIUS}px;
    padding: {INPUT_BLOCK_PADDING}px;
    margin-bottom: {INPUT_BLOCK_MARGIN_BOTTOM}px;
}}

[data-ps-scope] .ps-input-block-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}}

[data-ps-scope] .ps-input-block-title {{
    font-size: 13px;
    font-weight: 600;
    color: #F8FAFC;
    margin: 0;
}}

[data-ps-scope] .ps-input-block-hint {{
    font-size: 11px;
    color: rgba(248,250,252,0.5);
    margin: 0;
}}

[data-ps-scope] .ps-input-block-description {{
    font-size: 12px;
    color: rgba(248,250,252,0.65);
    margin-bottom: 12px;
    line-height: 1.4;
}}

[data-ps-scope] .ps-input-block-body {{
    margin-bottom: 8px;
}}

[data-ps-scope] .ps-input-block-feedback {{
    margin-top: 8px;
    font-size: 12px;
}}

[data-ps-scope] .ps-input-block-warning {{
    margin-top: 8px;
    font-size: 11px;
    color: rgba(245,158,11,0.9);
}}

/* 블록 행 (반응형) */
[data-ps-scope] .ps-block-row {{
    display: grid;
    gap: {INPUT_BLOCK_MARGIN_BOTTOM}px;
    margin-bottom: {INPUT_BLOCK_MARGIN_BOTTOM}px;
}}

[data-ps-scope] .ps-block-row-cols-2 {{
    grid-template-columns: repeat(2, 1fr);
}}

[data-ps-scope] .ps-block-row-cols-3 {{
    grid-template-columns: repeat(3, 1fr);
}}

/* 반응형: 900px 이하에서 1열 */
@media (max-width: {RESPONSIVE_BREAKPOINT}px) {{
    [data-ps-scope] .ps-block-row-cols-2,
    [data-ps-scope] .ps-block-row-cols-3 {{
        grid-template-columns: 1fr;
    }}
}}

/* ============================================
   Inline Feedback (즉시 피드백)
   ============================================ */
[data-ps-scope] .ps-inline-feedback {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    margin-top: 8px;
}}

[data-ps-scope] .ps-inline-feedback-label {{
    color: rgba(248,250,252,0.7);
}}

[data-ps-scope] .ps-inline-feedback-value {{
    font-weight: 600;
}}

[data-ps-scope] .ps-inline-feedback-status-ok {{
    color: #60A5FA;
}}

[data-ps-scope] .ps-inline-feedback-status-warn {{
    color: #F59E0B;
}}

[data-ps-scope] .ps-inline-feedback-status-danger {{
    color: #EF4444;
}}

/* ============================================
   Input Status Badge (상태 배지)
   ============================================ */
[data-ps-scope] .ps-status-badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 500;
    margin-left: 8px;
}}

[data-ps-scope] .ps-status-badge-ok {{
    background: rgba(59,130,246,0.2);
    color: #60A5FA;
}}

[data-ps-scope] .ps-status-badge-warn {{
    background: rgba(245,158,11,0.2);
    color: #F59E0B;
}}

[data-ps-scope] .ps-status-badge-danger {{
    background: rgba(239,68,68,0.2);
    color: #EF4444;
}}

/* Streamlit 위젯 래퍼 스타일 (스코프 기반) */
[data-ps-scope] [data-testid="stNumberInput"] > div > div {{
    background: transparent !important;
}}

[data-ps-scope] [data-testid="stNumberInput"] input {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}

[data-ps-scope] [data-testid="stTextInput"] > div > div {{
    background: transparent !important;
}}

[data-ps-scope] [data-testid="stTextInput"] input {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}
</style>
"""


def inject_form_kit_v2_css(scope_id: Optional[str] = None):
    """
    FormKit v2 CSS 주입 (data-ps-scope 기반 스코프)
    
    Args:
        scope_id: 고유 스코프 ID (None이면 자동 생성)
    
    Returns:
        scope_id: 사용된 스코프 ID
    """
    if scope_id is None:
        # 페이지 경로 기반으로 고유 ID 생성
        import inspect
        frame = inspect.currentframe()
        try:
            caller_file = frame.f_back.f_globals.get('__file__', 'default')
            scope_id = hashlib.md5(caller_file.encode()).hexdigest()[:8]
        finally:
            del frame
    
    css = _generate_form_kit_v2_css()
    st.markdown(css, unsafe_allow_html=True)
    st.markdown(f'<div data-ps-scope="{scope_id}">', unsafe_allow_html=True)
    return scope_id


def _format_number_with_commas(value: Union[int, float]) -> str:
    """숫자를 천단위 콤마 포맷으로 변환"""
    if value is None:
        return ""
    return f"{value:,.0f}" if isinstance(value, (int, float)) else str(value)


def _parse_formatted_number(formatted_str: str) -> Union[int, float, None]:
    """포맷된 문자열을 숫자로 파싱"""
    if not formatted_str:
        return None
    # 콤마 제거
    cleaned = formatted_str.replace(",", "").strip()
    try:
        # 정수로 변환 시도
        if "." not in cleaned:
            return int(cleaned)
        return float(cleaned)
    except ValueError:
        return None


def _get_input_status(value: Union[int, float], min_value: Optional[float] = None, 
                     max_value: Optional[float] = None, warn_threshold: Optional[float] = None) -> str:
    """입력값 상태 판단 (ok/warn/danger)"""
    if value is None:
        return "ok"
    
    # 음수 체크
    if value < 0:
        return "danger"
    
    # 최소값 체크
    if min_value is not None and value < min_value:
        return "danger"
    
    # 최대값 체크
    if max_value is not None and value > max_value:
        return "danger"
    
    # 경고 임계값 체크
    if warn_threshold is not None and value < warn_threshold:
        return "warn"
    
    # 0 체크 (경고)
    if value == 0:
        return "warn"
    
    return "ok"


def ps_primary_money_input(
    label: str,
    key: str,
    value: Optional[Union[int, float]] = 0,
    min_value: Optional[float] = 0,
    max_value: Optional[float] = None,
    step: Optional[float] = 1000,
    disabled: bool = False,
    help_text: Optional[str] = None,
    unit: str = "원",
    status: Optional[str] = None
) -> Union[int, float]:
    """
    Primary 등급: 금액 입력 (핵심 수치)
    
    Args:
        label: 라벨
        key: 위젯 키
        value: 초기값
        min_value: 최소값
        max_value: 최대값
        step: 증감 단위
        disabled: 비활성화 여부
        help_text: 도움말
        unit: 단위 (기본: "원")
        status: 상태 (ok/warn/danger, None이면 자동 판단)
    
    Returns:
        입력된 숫자값
    """
    # 상태 자동 판단
    if status is None:
        status = _get_input_status(value, min_value, max_value)
    
    # 상태 클래스
    status_class = f" ps-status-{status}" if status != "ok" else ""
    
    # 입력 필드 래퍼 시작 (data-unit 속성으로 단위 전달)
    safe_key = key.replace('.', '-').replace('_', '-')
    st.markdown(f"""
    <div class="ps-primary-input-wrapper" data-unit="{unit}" id="ps-wrapper-{safe_key}">
    """, unsafe_allow_html=True)
    
    # Streamlit number_input 사용 (모든 숫자 인자를 float로 통일)
    result = st.number_input(
        label,
        min_value=float(min_value) if min_value is not None else None,
        max_value=float(max_value) if max_value is not None else None,
        value=float(value) if value else 0.0,
        step=float(step) if step else 1.0,
        disabled=disabled,
        key=key,
        help=help_text,
        format="%d" if isinstance(value, int) or (isinstance(value, float) and value.is_integer()) else "%.0f"
    )
    
    # 스타일 적용 (data-ps-scope 기반, 단위는 ::after로 자동 처리)
    st.markdown(f"""
    <style>
    #ps-wrapper-{safe_key} {{
        position: relative;
    }}
    #ps-wrapper-{safe_key} [data-testid="stNumberInput"] {{
        position: relative;
    }}
    #ps-wrapper-{safe_key} [data-testid="stNumberInput"] > div > div {{
        background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03)) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: {PRIMARY_INPUT_BORDER_RADIUS}px !important;
        height: {PRIMARY_INPUT_HEIGHT}px !important;
        padding-right: {PRIMARY_INPUT_PADDING_RIGHT}px !important;
        position: relative;
    }}
    #ps-wrapper-{safe_key} [data-testid="stNumberInput"] input {{
        font-size: {PRIMARY_INPUT_FONT_SIZE}px !important;
        font-weight: {PRIMARY_INPUT_FONT_WEIGHT} !important;
        color: #F8FAFC !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 16px !important;
        height: 100% !important;
    }}
    #ps-wrapper-{safe_key} [data-testid="stNumberInput"] input::placeholder {{
        color: rgba(248,250,252,0.35) !important;
    }}
    #ps-wrapper-{safe_key} [data-testid="stNumberInput"]:focus-within > div > div {{
        border: 1px solid rgba(96,165,250,0.9) !important;
        box-shadow: 0 0 0 3px rgba(59,130,246,0.25), 0 6px 20px rgba(0,0,0,0.4) !important;
        background: linear-gradient(180deg, rgba(255,255,255,0.12), rgba(255,255,255,0.06)) !important;
    }}
    #ps-wrapper-{safe_key}::after {{
        content: attr(data-unit);
        position: absolute;
        right: 8px;
        top: 50%;
        transform: translateY(-50%);
        background: rgba(255,255,255,0.06);
        border-left: 1px solid rgba(255,255,255,0.12);
        padding: 0 {UNIT_BOX_PADDING_H}px;
        height: {UNIT_BOX_HEIGHT}px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: {UNIT_BOX_FONT_SIZE}px;
        color: rgba(248,250,252,0.8);
        border-radius: 0 10px 10px 0;
        pointer-events: none;
        z-index: 10;
    }}
    @media (max-width: {RESPONSIVE_BREAKPOINT}px) {{
        #ps-wrapper-{safe_key}::after {{
            display: none;
        }}
        #ps-wrapper-{safe_key} [data-testid="stNumberInput"] > div > div {{
            padding-right: 16px !important;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # 상태별 스타일 추가
    if status != "ok":
        st.markdown(f"""
        <style>
        #ps-wrapper-{safe_key} [data-testid="stNumberInput"] > div > div {{
            border-color: {'rgba(245,158,11,0.8)' if status == 'warn' else 'rgba(239,68,68,0.8)'} !important;
            box-shadow: 0 0 0 2px {'rgba(245,158,11,0.2)' if status == 'warn' else 'rgba(239,68,68,0.2)'} !important;
        }}
        </style>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    return int(result) if isinstance(result, float) and result.is_integer() else result


def ps_primary_quantity_input(
    label: str,
    key: str,
    value: Optional[Union[int, float]] = 0,
    min_value: Optional[float] = 0,
    max_value: Optional[float] = None,
    step: Optional[float] = 1,
    disabled: bool = False,
    help_text: Optional[str] = None,
    unit: str = "개",
    status: Optional[str] = None
) -> Union[int, float]:
    """
    Primary 등급: 수량 입력 (핵심 수치)
    
    Args:
        label: 라벨
        key: 위젯 키
        value: 초기값
        min_value: 최소값
        max_value: 최대값
        step: 증감 단위
        disabled: 비활성화 여부
        help_text: 도움말
        unit: 단위 (기본: "개")
        status: 상태 (ok/warn/danger, None이면 자동 판단)
    
    Returns:
        입력된 숫자값
    """
    return ps_primary_money_input(
        label=label,
        key=key,
        value=value,
        min_value=min_value,
        max_value=max_value,
        step=step,
        disabled=disabled,
        help_text=help_text,
        unit=unit,
        status=status
    )


def ps_primary_ratio_input(
    label: str,
    key: str,
    value: Optional[float] = 0.0,
    min_value: Optional[float] = 0.0,
    max_value: Optional[float] = 100.0,
    step: Optional[float] = 0.1,
    disabled: bool = False,
    help_text: Optional[str] = None,
    unit: str = "%",
    status: Optional[str] = None
) -> float:
    """
    Primary 등급: 비율 입력 (핵심 수치)
    
    Args:
        label: 라벨
        key: 위젯 키
        value: 초기값
        min_value: 최소값
        max_value: 최대값
        step: 증감 단위
        disabled: 비활성화 여부
        help_text: 도움말
        unit: 단위 (기본: "%")
        status: 상태 (ok/warn/danger, None이면 자동 판단)
    
    Returns:
        입력된 비율값
    """
    # 상태 자동 판단
    if status is None:
        status = _get_input_status(value, min_value, max_value, warn_threshold=0.1)
    
    # 입력 필드 래퍼 시작 (data-unit 속성으로 단위 전달)
    safe_key = key.replace('.', '-').replace('_', '-')
    st.markdown(f"""
    <div class="ps-primary-input-wrapper" data-unit="{unit}" id="ps-wrapper-{safe_key}">
    """, unsafe_allow_html=True)
    
    result = st.number_input(
        label,
        min_value=float(min_value) if min_value is not None else None,
        max_value=float(max_value) if max_value is not None else None,
        value=float(value) if value else 0.0,
        step=float(step) if step else 0.1,
        disabled=disabled,
        key=key,
        help=help_text,
        format="%.2f"
    )
    
    # 스타일 적용 (data-ps-scope 기반, 단위는 ::after로 자동 처리)
    st.markdown(f"""
    <style>
    #ps-wrapper-{safe_key} {{
        position: relative;
    }}
    #ps-wrapper-{safe_key} [data-testid="stNumberInput"] {{
        position: relative;
    }}
    #ps-wrapper-{safe_key} [data-testid="stNumberInput"] > div > div {{
        background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03)) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: {PRIMARY_INPUT_BORDER_RADIUS}px !important;
        height: {PRIMARY_INPUT_HEIGHT}px !important;
        padding-right: {PRIMARY_INPUT_PADDING_RIGHT}px !important;
        position: relative;
    }}
    #ps-wrapper-{safe_key} [data-testid="stNumberInput"] input {{
        font-size: {PRIMARY_INPUT_FONT_SIZE}px !important;
        font-weight: {PRIMARY_INPUT_FONT_WEIGHT} !important;
        color: #F8FAFC !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 16px !important;
        height: 100% !important;
    }}
    #ps-wrapper-{safe_key} [data-testid="stNumberInput"] input::placeholder {{
        color: rgba(248,250,252,0.35) !important;
    }}
    #ps-wrapper-{safe_key} [data-testid="stNumberInput"]:focus-within > div > div {{
        border: 1px solid rgba(96,165,250,0.9) !important;
        box-shadow: 0 0 0 3px rgba(59,130,246,0.25), 0 6px 20px rgba(0,0,0,0.4) !important;
        background: linear-gradient(180deg, rgba(255,255,255,0.12), rgba(255,255,255,0.06)) !important;
    }}
    #ps-wrapper-{safe_key}::after {{
        content: attr(data-unit);
        position: absolute;
        right: 8px;
        top: 50%;
        transform: translateY(-50%);
        background: rgba(255,255,255,0.06);
        border-left: 1px solid rgba(255,255,255,0.12);
        padding: 0 {UNIT_BOX_PADDING_H}px;
        height: {UNIT_BOX_HEIGHT}px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: {UNIT_BOX_FONT_SIZE}px;
        color: rgba(248,250,252,0.8);
        border-radius: 0 10px 10px 0;
        pointer-events: none;
        z-index: 10;
    }}
    @media (max-width: {RESPONSIVE_BREAKPOINT}px) {{
        #ps-wrapper-{safe_key}::after {{
            display: none;
        }}
        #ps-wrapper-{safe_key} [data-testid="stNumberInput"] > div > div {{
            padding-right: 16px !important;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # 상태별 스타일 추가
    if status != "ok":
        st.markdown(f"""
        <style>
        #ps-wrapper-{safe_key} [data-testid="stNumberInput"] > div > div {{
            border-color: {'rgba(245,158,11,0.8)' if status == 'warn' else 'rgba(239,68,68,0.8)'} !important;
            box-shadow: 0 0 0 2px {'rgba(245,158,11,0.2)' if status == 'warn' else 'rgba(239,68,68,0.2)'} !important;
        }}
        </style>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    return float(result)


def ps_secondary_select(
    label: str,
    key: str,
    options: list,
    index: Optional[int] = 0,
    disabled: bool = False,
    help_text: Optional[str] = None
) -> Any:
    """
    Secondary 등급: 선택 입력 (조정/조건)
    
    Args:
        label: 라벨
        key: 위젯 키
        options: 옵션 리스트
        index: 기본 선택 인덱스
        disabled: 비활성화 여부
        help_text: 도움말
    
    Returns:
        선택된 값
    """
    return st.selectbox(
        label,
        options=options,
        index=index,
        disabled=disabled,
        key=key,
        help=help_text
    )


def ps_secondary_date(
    label: str,
    key: str,
    value: Optional[Any] = None,
    disabled: bool = False,
    help_text: Optional[str] = None
) -> Any:
    """
    Secondary 등급: 날짜 입력 (조정/조건)
    
    Args:
        label: 라벨
        key: 위젯 키
        value: 초기값
        disabled: 비활성화 여부
        help_text: 도움말
    
    Returns:
        선택된 날짜
    """
    return st.date_input(
        label,
        value=value,
        disabled=disabled,
        key=key,
        help=help_text
    )


def ps_note_input(
    label: str,
    key: str,
    value: str = "",
    height: int = 100,
    disabled: bool = False,
    help_text: Optional[str] = None,
    placeholder: Optional[str] = None
) -> str:
    """
    Tertiary 등급: 메모 입력 (설명/보조)
    
    Args:
        label: 라벨
        key: 위젯 키
        value: 초기값
        height: 높이
        disabled: 비활성화 여부
        help_text: 도움말
        placeholder: 플레이스홀더
    
    Returns:
        입력된 텍스트
    """
    return st.text_area(
        label,
        value=value,
        height=height,
        disabled=disabled,
        key=key,
        help=help_text,
        placeholder=placeholder
    )


def ps_input_block(
    title: str,
    description: Optional[str] = None,
    right_hint: Optional[str] = None,
    level: str = "primary",
    body_fn: Optional[Callable] = None,
    feedback: Optional[Dict[str, Any]] = None,
    warning: Optional[str] = None
):
    """
    입력 블록 컨테이너 (모든 핵심 입력은 이 블록 안에)
    
    Args:
        title: 블록 제목
        description: 설명 (1줄 권장)
        right_hint: 우측 힌트 텍스트
        level: 블록 등급 (primary/secondary/tertiary)
        body_fn: 본문 렌더링 함수 (호출 가능한 함수)
        feedback: 피드백 정보 {label, value, status}
        warning: 경고 메시지
    """
    st.markdown(f"""
    <div class="ps-input-block">
        <div class="ps-input-block-header">
            <div class="ps-input-block-title">{title}</div>
            {f'<div class="ps-input-block-hint">{right_hint}</div>' if right_hint else ''}
        </div>
        {f'<div class="ps-input-block-description">{description}</div>' if description else ''}
        <div class="ps-input-block-body">
    """, unsafe_allow_html=True)
    
    # 본문 렌더링 (호출)
    if body_fn:
        body_fn()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 피드백 표시
    if feedback:
        ps_inline_feedback(
            label=feedback.get("label", ""),
            value=feedback.get("value", ""),
            status=feedback.get("status", "ok")
        )
    
    # 경고 표시
    if warning:
        st.markdown(f'<div class="ps-input-block-warning">⚠️ {warning}</div>', unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)


def ps_block_row(
    cols: int = 2,
    body_fn: Optional[Callable] = None
):
    """
    블록 행 (반응형 그리드)
    
    Args:
        cols: 열 개수 (2 또는 3)
        body_fn: 본문 렌더링 함수 (호출 가능한 함수, 내부에서 st.columns 사용)
    """
    cols_class = f"ps-block-row-cols-{cols}" if cols in [2, 3] else "ps-block-row-cols-2"
    st.markdown(f'<div class="ps-block-row {cols_class}">', unsafe_allow_html=True)
    
    if body_fn:
        body_fn()
    
    st.markdown("</div>", unsafe_allow_html=True)


def ps_inline_feedback(
    label: str,
    value: Union[str, int, float],
    status: str = "ok"
):
    """
    인라인 피드백 (즉시 피드백)
    
    Args:
        label: 라벨
        value: 값
        status: 상태 (ok/warn/danger)
    """
    value_str = f"{value:,.0f}" if isinstance(value, (int, float)) else str(value)
    st.markdown(f"""
    <div class="ps-inline-feedback">
        <span class="ps-inline-feedback-label">{label}:</span>
        <span class="ps-inline-feedback-value ps-inline-feedback-status-{status}">{value_str}</span>
    </div>
    """, unsafe_allow_html=True)


def ps_inline_warning(message: str):
    """
    인라인 경고
    
    Args:
        message: 경고 메시지
    """
    st.markdown(f'<div class="ps-input-block-warning">⚠️ {message}</div>', unsafe_allow_html=True)


def ps_input_status_badge(status: str, text: str):
    """
    입력 상태 배지
    
    Args:
        status: 상태 (ok/warn/danger)
        text: 배지 텍스트
    """
    st.markdown(f'<span class="ps-status-badge ps-status-badge-{status}">{text}</span>', unsafe_allow_html=True)
