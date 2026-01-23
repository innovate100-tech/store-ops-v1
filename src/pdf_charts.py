"""
PDF 차트 생성 모듈 (STEP 2-B)
matplotlib로 PNG 생성 후 ReportLab에 삽입
"""
import logging
from io import BytesIO
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

try:
    import matplotlib
    matplotlib.use('Agg')  # GUI 없이 사용
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


def make_daily_sales_line_chart(daily_series: List[Tuple[str, float]], title: str = "Daily Sales") -> Optional[bytes]:
    """
    일별 매출 라인 차트 생성 (PNG bytes)
    
    Args:
        daily_series: [(date_label, value), ...] 최소 3개 이상 필요
        title: 차트 제목
    
    Returns:
        bytes: PNG 이미지 바이트, 실패 시 None
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.warning("Matplotlib not available")
        return None
    
    if len(daily_series) < 3:
        logger.warning(f"Insufficient data for chart: {len(daily_series)} items")
        return None
    
    try:
        # 데이터 추출
        dates = [item[0] for item in daily_series]
        values = [item[1] for item in daily_series]
        
        # 차트 생성
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(dates, values, marker='o', linewidth=2, markersize=4)
        ax.set_title(title, fontsize=12)
        ax.set_xlabel("Date", fontsize=10)
        ax.set_ylabel("Sales (KRW)", fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # X축 레이블 회전 (날짜가 많을 때)
        if len(dates) > 7:
            plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        
        # PNG로 변환
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        png_bytes = buffer.getvalue()
        plt.close(fig)
        
        return png_bytes
        
    except Exception as e:
        logger.error(f"Failed to create line chart: {e}")
        if 'fig' in locals():
            plt.close(fig)
        return None


def make_weekday_sales_bar_chart(weekday_series: List[Tuple[str, float]], title: str = "Weekday Sales") -> Optional[bytes]:
    """
    요일별 매출 바 차트 생성 (PNG bytes)
    
    Args:
        weekday_series: [("Mon", value), ...]
        title: 차트 제목
    
    Returns:
        bytes: PNG 이미지 바이트, 실패 시 None
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.warning("Matplotlib not available")
        return None
    
    if not weekday_series or len(weekday_series) == 0:
        logger.warning("No weekday data")
        return None
    
    try:
        # 데이터 추출
        weekdays = [item[0] for item in weekday_series]
        values = [item[1] for item in weekday_series]
        
        # 차트 생성
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(weekdays, values, color='#667eea', alpha=0.7)
        ax.set_title(title, fontsize=12)
        ax.set_xlabel("Weekday", fontsize=10)
        ax.set_ylabel("Avg Sales (KRW)", fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        # PNG로 변환
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        png_bytes = buffer.getvalue()
        plt.close(fig)
        
        return png_bytes
        
    except Exception as e:
        logger.error(f"Failed to create bar chart: {e}")
        if 'fig' in locals():
            plt.close(fig)
        return None
