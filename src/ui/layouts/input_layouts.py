"""
입력센터 공통 레이아웃 컴포넌트
FORM형, CONSOLE형 레이아웃 및 공통 UI 컴포넌트 제공
"""
import streamlit as st
from typing import Optional, List, Dict, Any, Callable
from datetime import date, datetime


# ============================================
# CSS 스타일 (페이지별 스코프 적용)
# ============================================

INPUT_LAYOUT_CSS = """
<style>
/* FORM형 레이아웃 스타일 */
.ps-input-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.5rem;
    padding: 1.25rem 1.5rem;
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%);
    border-radius: 12px;
    border: 1px solid rgba(148, 163, 184, 0.2);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.ps-input-header-left {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.ps-input-header-icon {
    font-size: 2rem;
    line-height: 1;
}

.ps-input-header-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: #F8FAFC;
    margin: 0;
    letter-spacing: -0.02em;
}

.ps-input-header-badge {
    display: inline-flex;
    align-items: center;
    padding: 0.4rem 0.8rem;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
    white-space: nowrap;
}

.ps-input-header-badge-success {
    background: rgba(74, 222, 128, 0.2);
    color: #4ade80;
    border: 1px solid rgba(74, 222, 128, 0.4);
}

.ps-input-header-badge-warning {
    background: rgba(251, 191, 36, 0.2);
    color: #fbbf24;
    border: 1px solid rgba(251, 191, 36, 0.4);
}

.ps-input-header-badge-info {
    background: rgba(59, 130, 246, 0.2);
    color: #3b82f6;
    border: 1px solid rgba(59, 130, 246, 0.4);
}

.ps-input-header-badge-neutral {
    background: rgba(148, 163, 184, 0.2);
    color: #94a3b8;
    border: 1px solid rgba(148, 163, 184, 0.3);
}

/* GuideBox 스타일 */
.ps-guide-box {
    margin-bottom: 1.5rem;
    padding: 1.25rem 1.5rem;
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.6) 100%);
    border-radius: 12px;
    border-left: 4px solid;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.ps-guide-box-g1 {
    border-left-color: #3b82f6;
}

.ps-guide-box-g2 {
    border-left-color: #f59e0b;
}

.ps-guide-box-g3 {
    border-left-color: #8b5cf6;
}

.ps-guide-box-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #F8FAFC;
    margin: 0 0 0.75rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.ps-guide-box-content {
    color: #E2E8F0;
    font-size: 0.95rem;
    line-height: 1.6;
}

.ps-guide-box-content ul {
    margin: 0.5rem 0;
    padding-left: 1.5rem;
}

.ps-guide-box-content li {
    margin: 0.4rem 0;
}

.ps-guide-box-warning {
    margin-top: 0.75rem;
    padding: 0.75rem 1rem;
    background: rgba(239, 68, 68, 0.15);
    border-left: 3px solid #ef4444;
    border-radius: 6px;
    color: #fca5a5;
    font-size: 0.9rem;
}

/* ActionBar 스타일 */
.ps-action-bar {
    display: flex;
    gap: 0.75rem;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}

.ps-action-bar-primary {
    flex: 1;
    min-width: 200px;
}

.ps-action-bar-secondary {
    flex: 0 0 auto;
}

/* Summary Strip 스타일 */
.ps-summary-strip {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    padding: 1rem 1.5rem;
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%);
    border-radius: 10px;
    border: 1px solid rgba(148, 163, 184, 0.2);
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}

.ps-summary-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.ps-summary-label {
    font-size: 0.85rem;
    color: rgba(226, 232, 240, 0.7);
    font-weight: 500;
}

.ps-summary-value {
    font-size: 1rem;
    font-weight: 700;
    color: #F8FAFC;
}

.ps-summary-badge {
    display: inline-flex;
    align-items: center;
    padding: 0.25rem 0.6rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
    white-space: nowrap;
}

.ps-summary-badge-success {
    background: rgba(74, 222, 128, 0.2);
    color: #4ade80;
}

.ps-summary-badge-warning {
    background: rgba(251, 191, 36, 0.2);
    color: #fbbf24;
}

.ps-summary-badge-error {
    background: rgba(239, 68, 68, 0.2);
    color: #fca5a5;
}

/* Main Card 스타일 */
.ps-main-card {
    padding: 1.5rem;
    background: rgba(30, 41, 59, 0.4);
    border-radius: 12px;
    border: 1px solid rgba(148, 163, 184, 0.2);
    margin-bottom: 1.5rem;
}

/* CONSOLE형 레이아웃 스타일 */
.ps-console-dashboard {
    margin-bottom: 2rem;
}

.ps-console-work-area {
    margin-bottom: 1.5rem;
}

.ps-console-filter-bar {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
    padding: 1rem;
    background: rgba(30, 41, 59, 0.4);
    border-radius: 10px;
    border: 1px solid rgba(148, 163, 184, 0.2);
    flex-wrap: wrap;
    align-items: center;
}

.ps-console-cta {
    margin-top: 2rem;
    padding: 1rem 1.5rem;
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(37, 99, 235, 0.2) 100%);
    border-radius: 10px;
    border: 1px solid rgba(59, 130, 246, 0.3);
    text-align: center;
}
</style>
"""


# ============================================
# GuideBox 템플릿
# ============================================

def render_guide_box(
    kind: str = "G1",
    title: Optional[str] = None,
    bullets: Optional[List[str]] = None,
    warnings: Optional[List[str]] = None
):
    """
    GuideBox 렌더링 (G1/G2/G3 템플릿)
    
    Args:
        kind: "G1" (일일 입력), "G2" (보정 도구), "G3" (월간)
        title: 커스텀 제목 (None이면 기본 제목 사용)
        bullets: 안내 항목 리스트
        warnings: 경고 메시지 리스트
    """
    # CSS 주입
    st.markdown(INPUT_LAYOUT_CSS, unsafe_allow_html=True)
    
    # 기본 제목
    default_titles = {
        "G1": "💡 일일 입력 가이드",
        "G2": "⚠️ 보정 도구 안내",
        "G3": "📅 월간 입력 가이드"
    }
    display_title = title or default_titles.get(kind, "💡 안내")
    
    # 기본 bullets
    default_bullets = {
        "G1": [
            "오늘 입력할 내용을 단계별로 입력하세요",
            "임시 저장: 마감 전 수정 가능한 임시 기록",
            "마감하기: 최종 마감 저장 (이후 보정만 가능)",
            "매출이 있어야 분석이 시작됩니다"
        ],
        "G2": [
            "이 페이지는 과거 데이터 입력 및 보정용입니다",
            "일반적인 입력은 '일일 입력(통합)' 페이지를 사용하세요",
            "보정 시 충돌 감지 및 경고가 표시됩니다",
            "마감 완료된 날짜는 공식 반영됩니다"
        ],
        "G3": [
            "월 단위로 목표와 실제를 입력합니다",
            "목표 → 실제 → 성적표 순서로 진행됩니다",
            "확정 후에는 readonly 모드로 전환됩니다",
            "템플릿 저장/불러오기로 반복 입력을 최소화하세요"
        ]
    }
    display_bullets = bullets or default_bullets.get(kind, [])
    
    # 클래스명
    box_class = f"ps-guide-box ps-guide-box-{kind.lower()}"
    
    # HTML 생성
    bullets_html = ""
    if display_bullets:
        bullets_html = "<ul>"
        for bullet in display_bullets:
            bullets_html += f"<li>{bullet}</li>"
        bullets_html += "</ul>"
    
    warnings_html = ""
    if warnings:
        for warning in warnings:
            warnings_html += f'<div class="ps-guide-box-warning">⚠️ {warning}</div>'
    
    html = f"""
    <div class="{box_class}">
        <div class="ps-guide-box-title">{display_title}</div>
        <div class="ps-guide-box-content">
            {bullets_html}
            {warnings_html}
        </div>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)


# ============================================
# ActionBar 컴포넌트
# ============================================

def render_action_bar(
    primary_label: str,
    primary_key: str,
    primary_action: Callable,
    secondary_actions: Optional[List[Dict[str, Any]]] = None
):
    """
    ActionBar 렌더링 (Primary 1개 + Secondary 1~2개)
    
    Args:
        primary_label: Primary 버튼 라벨
        primary_key: Primary 버튼 key
        primary_action: Primary 버튼 클릭 시 실행할 함수
        secondary_actions: Secondary 버튼 리스트 [{"label": "...", "key": "...", "action": ...}, ...]
    """
    # 버튼 배치
    if secondary_actions and len(secondary_actions) > 0:
        cols = st.columns([2] + [1] * len(secondary_actions))
        
        with cols[0]:
            if st.button(primary_label, type="primary", key=primary_key, use_container_width=True):
                primary_action()
        
        for idx, sec_action in enumerate(secondary_actions):
            with cols[idx + 1]:
                if st.button(
                    sec_action.get("label", "버튼"),
                    type="secondary",
                    key=sec_action.get("key", f"secondary_{idx}"),
                    use_container_width=True
                ):
                    sec_action.get("action", lambda: None)()
    else:
        # Secondary가 없으면 Primary만
        if st.button(primary_label, type="primary", key=primary_key, use_container_width=True):
            primary_action()


# ============================================
# Summary Strip 컴포넌트
# ============================================

def render_summary_strip(
    items: List[Dict[str, Any]]
):
    """
    Summary Strip 렌더링 (날짜/월 + 핵심 숫자 + 배지)
    
    Args:
        items: [{"label": "...", "value": "...", "badge": "success|warning|error|None"}, ...]
    """
    st.markdown(INPUT_LAYOUT_CSS, unsafe_allow_html=True)
    
    items_html = ""
    for item in items:
        label = item.get("label", "")
        value = item.get("value", "")
        badge = item.get("badge")
        
        badge_html = ""
        if badge:
            badge_class = f"ps-summary-badge ps-summary-badge-{badge}"
            badge_html = f'<span class="{badge_class}">{badge}</span>'
        
        items_html += f"""
        <div class="ps-summary-item">
            <span class="ps-summary-label">{label}</span>
            <span class="ps-summary-value">{value}</span>
            {badge_html}
        </div>
        """
    
    html = f"""
    <div class="ps-summary-strip">
        {items_html}
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)


# ============================================
# FORM형 레이아웃
# ============================================

def render_form_layout(
    title: str,
    icon: str = "📝",
    status_badge: Optional[Dict[str, Any]] = None,
    guide_kind: Optional[str] = None,
    guide_bullets: Optional[List[str]] = None,
    guide_warnings: Optional[List[str]] = None,
    summary_items: Optional[List[Dict[str, Any]]] = None,
    action_primary: Optional[Dict[str, Any]] = None,
    action_secondary: Optional[List[Dict[str, Any]]] = None,
    main_content: Optional[Callable] = None
):
    """
    FORM형 레이아웃 렌더링
    
    Args:
        title: 페이지 제목
        icon: 페이지 아이콘
        status_badge: 상태 배지 {"text": "...", "type": "success|warning|info|neutral"}
        guide_kind: GuideBox 종류 ("G1"|"G2"|"G3")
        guide_bullets: GuideBox 안내 항목 (None이면 기본값 사용)
        guide_warnings: GuideBox 경고 메시지
        summary_items: Summary Strip 항목 리스트
        action_primary: Primary 액션 {"label": "...", "key": "...", "action": ...}
        action_secondary: Secondary 액션 리스트
        main_content: Main Card 내용 렌더링 함수
    """
    st.markdown(INPUT_LAYOUT_CSS, unsafe_allow_html=True)
    
    # Header
    badge_html = ""
    if status_badge:
        badge_type = status_badge.get("type", "neutral")
        badge_text = status_badge.get("text", "")
        badge_html = f'<span class="ps-input-header-badge ps-input-header-badge-{badge_type}">{badge_text}</span>'
    
    header_html = f"""
    <div class="ps-input-header">
        <div class="ps-input-header-left">
            <span class="ps-input-header-icon">{icon}</span>
            <h1 class="ps-input-header-title">{title}</h1>
        </div>
        {badge_html}
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)
    
    # GuideBox
    if guide_kind:
        render_guide_box(
            kind=guide_kind,
            bullets=guide_bullets,
            warnings=guide_warnings
        )
    
    # Summary Strip
    if summary_items:
        render_summary_strip(summary_items)
    
    # Main Card
    if main_content:
        st.markdown('<div class="ps-main-card">', unsafe_allow_html=True)
        main_content()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ActionBar
    if action_primary:
        render_action_bar(
            primary_label=action_primary.get("label", "저장"),
            primary_key=action_primary.get("key", "primary_action"),
            primary_action=action_primary.get("action", lambda: None),
            secondary_actions=action_secondary
        )


# ============================================
# CONSOLE형 레이아웃
# ============================================

def render_console_layout(
    title: str,
    icon: str = "📊",
    dashboard_content: Optional[Callable] = None,
    work_area_content: Optional[Callable] = None,
    filter_content: Optional[Callable] = None,
    list_content: Optional[Callable] = None,
    cta_label: Optional[str] = None,
    cta_action: Optional[Callable] = None
):
    """
    CONSOLE형 레이아웃 렌더링
    
    Args:
        title: 페이지 제목
        icon: 페이지 아이콘
        dashboard_content: Top Dashboard 렌더링 함수
        work_area_content: Work Area (입력 영역) 렌더링 함수
        filter_content: Filter Bar 렌더링 함수
        list_content: List/Editor 렌더링 함수
        cta_label: Bottom CTA 라벨
        cta_action: Bottom CTA 액션 함수
    """
    st.markdown(INPUT_LAYOUT_CSS, unsafe_allow_html=True)
    
    # Header (간단 버전)
    header_html = f"""
    <div class="ps-input-header">
        <div class="ps-input-header-left">
            <span class="ps-input-header-icon">{icon}</span>
            <h1 class="ps-input-header-title">{title}</h1>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)
    
    # Top Dashboard
    if dashboard_content:
        st.markdown('<div class="ps-console-dashboard">', unsafe_allow_html=True)
        dashboard_content()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Work Area
    if work_area_content:
        st.markdown('<div class="ps-console-work-area">', unsafe_allow_html=True)
        work_area_content()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Filter Bar
    if filter_content:
        st.markdown('<div class="ps-console-filter-bar">', unsafe_allow_html=True)
        filter_content()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # List/Editor
    if list_content:
        list_content()
    
    # Bottom CTA
    if cta_label and cta_action:
        st.markdown('<div class="ps-console-cta">', unsafe_allow_html=True)
        if st.button(cta_label, type="primary", key="console_cta", use_container_width=True):
            cta_action()
        st.markdown('</div>', unsafe_allow_html=True)
