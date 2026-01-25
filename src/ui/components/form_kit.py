"""
FormKit: 입력센터 통일 UI 컴포넌트
모든 입력 위젯의 spacing/label/help/placeholder 규격을 통일합니다.
"""
import streamlit as st
from typing import Optional, List, Dict, Any, Callable

try:
    from src.debug.nav_trace import push_render_step
except ImportError:
    def push_render_step(*args, **kwargs):
        pass


# CSS 스코프 클래스 (페이지별로 주입)
FORM_KIT_CSS = """
<style>
.ps-form-scope {
    /* 폼 전체 스코프 */
}

.ps-form-scope .ps-section {
    margin-bottom: 1.5rem;
}

.ps-form-scope .ps-field-row {
    margin-bottom: 1rem;
}

.ps-form-scope .ps-field-label {
    font-weight: 600;
    font-size: 0.95rem;
    margin-bottom: 0.5rem;
    color: var(--text-color, #1f2937);
}

.ps-form-scope .ps-field-help {
    font-size: 0.85rem;
    color: var(--text-secondary-color, #6b7280);
    margin-top: 0.25rem;
    margin-bottom: 0.5rem;
}

.ps-form-scope .ps-notice {
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
    border-left: 4px solid;
}

.ps-form-scope .ps-notice-info {
    background-color: rgba(59, 130, 246, 0.1);
    border-left-color: #3b82f6;
    color: #1e40af;
}

.ps-form-scope .ps-notice-warning {
    background-color: rgba(245, 158, 11, 0.1);
    border-left-color: #f59e0b;
    color: #92400e;
}

.ps-form-scope .ps-notice-success {
    background-color: rgba(16, 185, 129, 0.1);
    border-left-color: #10b981;
    color: #065f46;
}

.ps-form-scope .ps-row-container {
    margin-bottom: 0.75rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid rgba(229, 231, 235, 0.5);
}

.ps-form-scope .ps-row-container:last-child {
    border-bottom: none;
    margin-bottom: 0;
    padding-bottom: 0;
}
</style>
"""


def inject_form_kit_css():
    """FormKit CSS 주입 (rerun마다 실행, DOM 종속 CSS)"""
    # 주의: 1회 가드 없음 - DOM 재생성 시마다 CSS 재적용 필요
    # 안전장치: 모든 셀렉터는 .ps-form-scope로 제한되어 있어 전역 영향 없음
    
    st.markdown(FORM_KIT_CSS, unsafe_allow_html=True)
    push_render_step("CSS_INJECT: form_kit", extra={"where": "form_kit"})
    # 주의: 플래그 설정 없음 - 매 rerun마다 CSS 재적용


def ps_section(title: str, icon: Optional[str] = None, help_text: Optional[str] = None):
    """
    섹션 헤더 (통일된 스타일)
    
    Args:
        title: 섹션 제목
        icon: 아이콘 (선택사항)
        help_text: 도움말 텍스트 (선택사항)
    """
    title_text = f"{icon} {title}" if icon else title
    st.markdown(f"### {title_text}")
    if help_text:
        st.caption(help_text)
    st.markdown('<div class="ps-section"></div>', unsafe_allow_html=True)


def ps_field_row(
    label: str,
    required: bool = False,
    help_text: Optional[str] = None,
    columns: Optional[List[float]] = None
):
    """
    필드 행 컨테이너 (라벨 + 입력 영역)
    
    Args:
        label: 필드 라벨
        required: 필수 여부
        help_text: 도움말 텍스트
        columns: 컬럼 비율 (예: [1, 2] = 라벨 1, 입력 2)
    
    Returns:
        컬럼 컨텍스트 매니저
    """
    label_text = f"{label} {'*' if required else ''}"
    
    if columns:
        cols = st.columns(columns)
        with cols[0]:
            st.markdown(f'<div class="ps-field-label">{label_text}</div>', unsafe_allow_html=True)
            if help_text:
                st.markdown(f'<div class="ps-field-help">{help_text}</div>', unsafe_allow_html=True)
        return cols[1] if len(cols) > 1 else cols[0]
    else:
        st.markdown(f'<div class="ps-field-label">{label_text}</div>', unsafe_allow_html=True)
        if help_text:
            st.markdown(f'<div class="ps-field-help">{help_text}</div>', unsafe_allow_html=True)
        return None


def ps_money_input(
    label: str,
    key: str,
    value: float = 0.0,
    min_value: float = 0.0,
    step: float = 1000.0,
    help_text: Optional[str] = None,
    disabled: bool = False,
    required: bool = False,
    placeholder: Optional[str] = None
):
    """
    금액 입력 필드 (통일된 포맷)
    
    Args:
        label: 라벨
        key: 위젯 키 (기존 키 유지)
        value: 초기값
        min_value: 최소값
        step: 증가 단위
        help_text: 도움말
        disabled: 비활성화 여부
        required: 필수 여부
        placeholder: 플레이스홀더 (사용 안 함, 호환성용)
    
    Returns:
        입력된 값
    """
    ps_field_row(label, required=required, help_text=help_text)
    return st.number_input(
        label,
        min_value=min_value,
        value=value,
        step=step,
        format="%d",
        key=key,
        disabled=disabled,
        label_visibility="collapsed"
    )


def ps_qty_input(
    label: str,
    key: str,
    value: float = 0.0,
    min_value: float = 0.0,
    step: float = 1.0,
    help_text: Optional[str] = None,
    disabled: bool = False,
    required: bool = False,
    placeholder: Optional[str] = None
):
    """
    수량 입력 필드 (통일된 포맷)
    
    Args:
        label: 라벨
        key: 위젯 키 (기존 키 유지)
        value: 초기값
        min_value: 최소값
        step: 증가 단위
        help_text: 도움말
        disabled: 비활성화 여부
        required: 필수 여부
        placeholder: 플레이스홀더 (사용 안 함, 호환성용)
    
    Returns:
        입력된 값
    """
    ps_field_row(label, required=required, help_text=help_text)
    return st.number_input(
        label,
        min_value=min_value,
        value=value,
        step=step,
        format="%.2f",
        key=key,
        disabled=disabled,
        label_visibility="collapsed"
    )


def ps_choice(
    label: str,
    options: List[str],
    key: str,
    index: Optional[int] = None,
    help_text: Optional[str] = None,
    disabled: bool = False,
    required: bool = False,
    placeholder: Optional[str] = None,
    widget_type: str = "selectbox"  # "selectbox", "radio", "multiselect"
):
    """
    선택 필드 (통일된 스타일)
    
    Args:
        label: 라벨
        options: 선택 옵션 리스트
        key: 위젯 키 (기존 키 유지)
        index: 기본 선택 인덱스
        help_text: 도움말
        disabled: 비활성화 여부
        required: 필수 여부
        placeholder: 플레이스홀더 (selectbox용)
        widget_type: 위젯 타입 ("selectbox", "radio", "multiselect")
    
    Returns:
        선택된 값
    """
    ps_field_row(label, required=required, help_text=help_text)
    
    if widget_type == "radio":
        return st.radio(
            label,
            options=options,
            index=index,
            key=key,
            disabled=disabled,
            horizontal=True,
            label_visibility="collapsed"
        )
    elif widget_type == "multiselect":
        return st.multiselect(
            label,
            options=options,
            default=options[index] if index is not None and index < len(options) else None,
            key=key,
            disabled=disabled,
            label_visibility="collapsed"
        )
    else:  # selectbox
        # placeholder 처리: "Choose an option" 같은 기본 텍스트 제거
        if placeholder:
            # Streamlit selectbox는 placeholder를 직접 지원하지 않으므로
            # 첫 번째 옵션으로 placeholder를 추가하고 None 처리
            if index is None:
                options_with_placeholder = [placeholder] + options
                selected = st.selectbox(
                    label,
                    options=options_with_placeholder,
                    index=0,
                    key=key,
                    disabled=disabled,
                    label_visibility="collapsed"
                )
                return None if selected == placeholder else selected
        return st.selectbox(
            label,
            options=options,
            index=index,
            key=key,
            disabled=disabled,
            label_visibility="collapsed"
        )


def ps_notice(
    message: str,
    notice_type: str = "info",  # "info", "warning", "success"
    icon: Optional[str] = None
):
    """
    알림 박스 (통일된 스타일)
    
    Args:
        message: 메시지
        notice_type: 타입 ("info", "warning", "success")
        icon: 아이콘 (선택사항)
    """
    icon_text = f"{icon} " if icon else ""
    st.markdown(
        f'<div class="ps-notice ps-notice-{notice_type}">{icon_text}{message}</div>',
        unsafe_allow_html=True
    )


def ps_action_bar(
    primary_label: Optional[str] = None,
    primary_action: Optional[Callable] = None,
    secondary_labels: Optional[List[str]] = None,
    secondary_actions: Optional[List[Callable]] = None,
    columns: Optional[List[float]] = None
):
    """
    액션 바 (하단 버튼 영역 통일)
    
    Args:
        primary_label: Primary 버튼 라벨
        primary_action: Primary 버튼 액션 함수
        secondary_labels: Secondary 버튼 라벨 리스트
        secondary_actions: Secondary 버튼 액션 함수 리스트
        columns: 컬럼 비율 (예: [1, 1, 4] = Primary 1, Secondary 1, 빈 공간 4)
    
    Returns:
        버튼 클릭 여부 (primary_clicked, secondary_clicks)
    """
    if columns is None:
        # 기본: Primary 1, Secondary들, 빈 공간
        num_secondary = len(secondary_labels) if secondary_labels else 0
        total_width = 1 + num_secondary + 4
        columns = [1] + ([1] * num_secondary) + [4]
    
    cols = st.columns(columns)
    col_idx = 0
    
    primary_clicked = False
    secondary_clicks = []
    
    # Primary 버튼
    if primary_label and primary_action:
        with cols[col_idx]:
            if st.button(primary_label, type="primary", use_container_width=True):
                primary_action()
                primary_clicked = True
        col_idx += 1
    
    # Secondary 버튼들
    if secondary_labels and secondary_actions:
        for label, action in zip(secondary_labels, secondary_actions):
            if col_idx < len(cols):
                with cols[col_idx]:
                    if st.button(label, type="secondary", use_container_width=True):
                        action()
                        secondary_clicks.append(True)
                col_idx += 1
    
    return primary_clicked, secondary_clicks


def ps_row_container(render_func: Callable, key_suffix: str = ""):
    """
    반복 행 컨테이너 (레시피 일괄등록 등에서 사용)
    
    Args:
        render_func: 행 렌더링 함수
        key_suffix: 키 접미사
    """
    st.markdown('<div class="ps-row-container">', unsafe_allow_html=True)
    render_func()
    st.markdown('</div>', unsafe_allow_html=True)
