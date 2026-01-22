"""
통합 대시보드 페이지
"""
from src.bootstrap import bootstrap
from src.ui_helpers import render_page_header

# perf_span import (fallback 포함)
try:
    from src.utils.boot_perf import perf_span
except ImportError:
    # fallback: perf_span이 없으면 빈 컨텍스트 매니저 제공
    from contextlib import contextmanager
    @contextmanager
    def perf_span(*args, **kwargs):
        yield

# 공통 설정 적용
bootstrap(page_title="Dashboard")

# 모듈에서 함수들 import
from ui_pages.dashboard.context import _create_dashboard_context
from ui_pages.dashboard.data_loaders import _load_dashboard_data
from ui_pages.dashboard.metrics import _compute_dashboard_metrics
from ui_pages.dashboard.diagnostics import _render_dashboard_diagnostics
from ui_pages.dashboard.sections import (
    _render_breakeven_section,
    _render_sales_sections,
    _render_menu_sections
)


def render_dashboard():
    """통합 대시보드 페이지 렌더링 (조립 함수)"""
    render_page_header("통합 대시보드", "📊")
    
    # 공통 컨텍스트 생성
    ctx = _create_dashboard_context()
    
    # 진단 정보 표시
    _render_dashboard_diagnostics(ctx)
    
    # 데이터 로드
    raw_data = _load_dashboard_data(ctx)
    
    # 메트릭 계산
    metrics = _compute_dashboard_metrics(ctx, raw_data)
    
    # UI 섹션 렌더링
    _render_breakeven_section(ctx, metrics, raw_data)
    _render_sales_sections(ctx, metrics, raw_data)
    _render_menu_sections(ctx, metrics, raw_data)
