"""
PDF 성적표 MVP 생성 모듈 (PHASE 7-4 / STEP 1)
ReportLab 기반 최소 6페이지 PDF 생성
"""
import logging
from io import BytesIO
from datetime import datetime, date
from zoneinfo import ZoneInfo
from typing import Tuple, Optional, Dict, List

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor, black, white
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

logger = logging.getLogger(__name__)

# 한글 폰트 등록 시도 (실패 시 fallback)
FONT_REGISTERED = False
try:
    # Windows 기본 한글 폰트 경로 시도
    import platform
    if platform.system() == "Windows":
        try:
            pdfmetrics.registerFont(TTFont('NanumGothic', 'C:/Windows/Fonts/malgun.ttf'))
            FONT_REGISTERED = True
        except:
            try:
                pdfmetrics.registerFont(TTFont('NanumGothic', 'C:/Windows/Fonts/gulim.ttc'))
                FONT_REGISTERED = True
            except:
                pass
except Exception:
    pass

# 폰트 설정
FONT_NAME = 'NanumGothic' if FONT_REGISTERED else 'Helvetica'
FONT_FALLBACK = not FONT_REGISTERED


def can_generate_scorecard(store_id: str, year: int, month: int) -> Tuple[bool, str]:
    """
    PDF 성적표 생성 가능 여부 확인
    
    최소 조건:
    - 이번 달 actual_settlement(final) 존재 OR
    - sales 월매출 존재 OR
    - daily_close 1건 이상
    
    Returns:
        (bool, str): (생성 가능 여부, 안내 문구)
    """
    if not store_id:
        return False, "매장 정보를 찾을 수 없습니다."
    
    try:
        from src.auth import get_supabase_client
        from src.storage_supabase import (
            get_month_settlement_status,
            load_monthly_sales_total
        )
        from ui_pages.home import get_close_count
        
        supabase = get_supabase_client()
        if not supabase:
            return False, "데이터베이스 연결에 실패했습니다."
        
        # 조건 1: actual_settlement(final) 존재
        month_status = get_month_settlement_status(store_id, year, month)
        if month_status == 'final':
            return True, ""
        
        # 조건 2: sales 월매출 존재
        monthly_sales = load_monthly_sales_total(store_id, year, month)
        if monthly_sales > 0:
            return True, ""
        
        # 조건 3: daily_close 1건 이상
        close_count = get_close_count(store_id)
        if close_count > 0:
            return True, ""
        
        return False, "이번 달 데이터가 없습니다. 마감을 1회 이상 진행하거나 매출을 입력해주세요."
        
    except Exception as e:
        logger.error(f"Failed to check scorecard generation: {e}")
        return False, f"데이터 확인 중 오류가 발생했습니다: {str(e)}"


def gather_scorecard_mvp_data(store_id: str, year: int, month: int) -> Dict:
    """
    PDF 성적표에 필요한 데이터 수집 (SSOT 함수만 사용)
    
    Returns:
        dict: PDF 생성에 필요한 모든 데이터
    """
    data = {
        "store_name": None,
        "period_label": f"{year}년 {month}월",
        "monthly_sales": 0.0,
        "operating_profit": None,
        "close_rate": None,
        "close_streak": None,
        "sales_daily_series": [],
        "sales_weekday_series": None,
        "fixed_cost": 0.0,
        "variable_ratio": 0.0,
        "break_even_sales": 0.0,
        "structure_sentence": "",
        "profit_examples": [],
        "problems_top3": [],
        "goods_top3": [],
        "anomaly_signals": [],
        "coach_summary": "",
        "coach_actions": [],
        "month_status_summary": ""
    }
    
    try:
        from src.auth import get_supabase_client
        from src.storage_supabase import (
            load_monthly_sales_total,
            get_fixed_costs,
            get_variable_cost_ratio,
            calculate_break_even_sales
        )
        from ui_pages.home import (
            get_problems_top3,
            get_good_points_top3,
            get_anomaly_signals,
            get_coach_summary,
            get_month_status_summary,
            get_monthly_close_stats,
            detect_owner_day_level,
            get_store_financial_structure
        )
        
        supabase = get_supabase_client()
        if not supabase:
            return data
        
        # 가게 이름
        try:
            store_result = supabase.table("stores").select("name").eq("id", store_id).limit(1).execute()
            if store_result.data:
                data["store_name"] = store_result.data[0].get("name", "가게")
        except:
            data["store_name"] = "가게"
        
        # 월매출
        data["monthly_sales"] = float(load_monthly_sales_total(store_id, year, month))
        
        # 영업이익 (actual_settlement에서)
        try:
            settlement_result = supabase.table("actual_settlement")\
                .select("operating_profit")\
                .eq("store_id", store_id)\
                .eq("year", year)\
                .eq("month", month)\
                .limit(1)\
                .execute()
            if settlement_result.data and settlement_result.data[0].get("operating_profit") is not None:
                data["operating_profit"] = float(settlement_result.data[0].get("operating_profit", 0))
        except:
            pass
        
        # 마감률/스트릭
        try:
            close_stats = get_monthly_close_stats(store_id, year, month)
            closed_days, total_days, close_rate, streak_days = close_stats
            if total_days > 0:
                data["close_rate"] = close_rate
            data["close_streak"] = streak_days
        except:
            pass
        
        # 일별 매출 시리즈
        try:
            KST = ZoneInfo("Asia/Seoul")
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1)
            else:
                end_date = date(year, month + 1, 1)
            
            sales_result = supabase.table("sales")\
                .select("date, total_sales")\
                .eq("store_id", store_id)\
                .gte("date", start_date.isoformat())\
                .lt("date", end_date.isoformat())\
                .order("date", desc=False)\
                .execute()
            
            if sales_result.data:
                for row in sales_result.data:
                    date_str = row.get("date", "")
                    total = float(row.get("total_sales", 0) or 0)
                    if date_str and total > 0:
                        # 날짜 포맷: MM-DD
                        try:
                            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                            date_label = f"{date_obj.month:02d}-{date_obj.day:02d}"
                            data["sales_daily_series"].append((date_label, total))
                        except:
                            pass
        except:
            pass
        
        # 요일별 평균 (선택적, 데이터 충분 시)
        if len(data["sales_daily_series"]) >= 7:
            try:
                weekday_totals = {"Mon": [], "Tue": [], "Wed": [], "Thu": [], "Fri": [], "Sat": [], "Sun": []}
                weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                
                for date_label, total in data["sales_daily_series"]:
                    try:
                        date_obj = datetime.strptime(f"{year}-{date_label}", "%Y-%m-%d").date()
                        weekday_idx = date_obj.weekday()
                        weekday_name = weekday_names[weekday_idx]
                        weekday_totals[weekday_name].append(total)
                    except:
                        pass
                
                weekday_avg = []
                for wd in weekday_names:
                    if weekday_totals[wd]:
                        avg = sum(weekday_totals[wd]) / len(weekday_totals[wd])
                        weekday_avg.append((wd, avg))
                
                if weekday_avg:
                    data["sales_weekday_series"] = weekday_avg
            except:
                pass
        
        # 손익 구조
        data["fixed_cost"] = float(get_fixed_costs(store_id, year, month))
        data["variable_ratio"] = float(get_variable_cost_ratio(store_id, year, month))
        data["break_even_sales"] = float(calculate_break_even_sales(store_id, year, month))
        
        # 구조 문장 및 예시
        try:
            structure = get_store_financial_structure(store_id, year, month)
            if structure["source"] != "none" and structure["break_even_sales"] > 0:
                break_even = structure["break_even_sales"]
                variable_ratio = structure["variable_ratio"]
                margin_per_100k = int((100000 * (1 - variable_ratio)))
                data["structure_sentence"] = f"이 가게는 매출 {int(break_even):,}원부터 흑자가 시작되고, 매출이 10만원 늘면 약 {margin_per_100k:,}원이 남는 구조입니다."
                
                # 예시 테이블 (3행)
                if structure.get("example_table"):
                    examples = structure["example_table"][:3]
                    for ex in examples:
                        sales_val = ex["sales"]
                        profit_val = ex["profit"]
                        label = f"{int(sales_val / break_even * 100)}%" if break_even > 0 else "100%"
                        data["profit_examples"].append((label, sales_val, profit_val))
        except:
            pass
        
        # 문제/잘한점/이상징후
        try:
            day_level = detect_owner_day_level(store_id)
            problems = get_problems_top3(store_id)
            goods = get_good_points_top3(store_id)
            signals = get_anomaly_signals(store_id)
            
            data["problems_top3"] = [p.get("text", "") for p in problems[:3] if "데이터를 불러올 수 없습니다" not in p.get("text", "") and "아직 분석할 데이터가 충분하지 않습니다" not in p.get("text", "")]
            data["goods_top3"] = [g.get("text", "") for g in goods[:3] if "데이터를 불러올 수 없습니다" not in g.get("text", "") and "데이터가 쌓이면 자동 분석됩니다" not in g.get("text", "")]
            data["anomaly_signals"] = [s.get("text", "") for s in signals[:3]]
            
            data["coach_summary"] = get_coach_summary(store_id, day_level)
            data["month_status_summary"] = get_month_status_summary(store_id, year, month, day_level)
        except:
            pass
        
        # 코치 액션 (간단 버전)
        if data["problems_top3"]:
            data["coach_actions"] = data["problems_top3"][:3]
        else:
            data["coach_actions"] = ["데이터가 쌓이면 자동으로 분석됩니다."]
        
    except Exception as e:
        logger.error(f"Failed to gather scorecard data: {e}")
    
    return data


def _format_currency(amount: float) -> str:
    """금액 포맷팅 (만원 단위)"""
    if amount == 0:
        return "0원"
    if abs(amount) >= 10000:
        return f"{amount/10000:.1f}만원"
    return f"{int(amount):,}원"


def _create_page_1_cover(data: Dict, styles) -> List:
    """1P. 표지"""
    story = []
    
    # 가게 이름
    store_name = data.get("store_name") or "가게"
    story.append(Spacer(1, 40*mm))
    story.append(Paragraph(store_name, ParagraphStyle(
        'CoverTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#667eea'),
        alignment=1,  # 중앙
        spaceAfter=20
    )))
    
    # 기간
    period = data.get("period_label", "")
    story.append(Paragraph(period + " 성적표", ParagraphStyle(
        'CoverPeriod',
        parent=styles['Normal'],
        fontSize=16,
        alignment=1,
        spaceAfter=30
    )))
    
    # 핵심 숫자
    monthly_sales = data.get("monthly_sales", 0)
    operating_profit = data.get("operating_profit")
    
    if monthly_sales > 0:
        sales_text = _format_currency(monthly_sales)
        if operating_profit is not None:
            profit_text = _format_currency(operating_profit)
            summary_text = f"이번 달은 <b>{sales_text}</b> 매출, <b>{profit_text}</b> 이익"
        else:
            summary_text = f"이번 달은 <b>{sales_text}</b> 매출"
        
        story.append(Paragraph(summary_text, ParagraphStyle(
            'CoverSummary',
            parent=styles['Normal'],
            fontSize=18,
            textColor=HexColor('#667eea'),
            alignment=1,
            spaceAfter=50
        )))
    
    # 하단 문구
    story.append(Spacer(1, 60*mm))
    story.append(Paragraph("선택받는 가게는, 숫자가 다릅니다", ParagraphStyle(
        'CoverFooter',
        parent=styles['Normal'],
        fontSize=12,
        textColor=HexColor('#6c757d'),
        alignment=1
    )))
    
    return story


def _create_page_2_summary(data: Dict, styles) -> List:
    """2P. 매장 요약"""
    story = []
    
    story.append(Paragraph("매장 요약", ParagraphStyle(
        'PageTitle',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=15
    )))
    
    # KPI 카드 2x2
    monthly_sales = data.get("monthly_sales", 0)
    operating_profit = data.get("operating_profit")
    break_even = data.get("break_even_sales", 0)
    
    # 목표 달성률 (간단 버전, 목표가 없으면 "-")
    target_rate = "-"
    
    kpi_data = [
        [f"이번 달 매출<br/>{_format_currency(monthly_sales)}", 
         f"영업이익<br/>{_format_currency(operating_profit) if operating_profit is not None else '-'}"],
        [f"손익분기점<br/>{_format_currency(break_even) if break_even > 0 else '-'}", 
         f"목표 달성률<br/>{target_rate}"]
    ]
    
    kpi_table = Table(kpi_data, colWidths=[80*mm, 80*mm], rowHeights=[30*mm, 30*mm])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, -1), white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, white),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 10*mm))
    
    # 마감률
    close_rate = data.get("close_rate")
    close_streak = data.get("close_streak", 0)
    if close_rate is not None:
        rate_text = f"마감률: {int(close_rate * 100)}%"
        if close_streak > 0:
            rate_text += f" (연속 {close_streak}일)"
        story.append(Paragraph(rate_text, styles['Normal']))
    
    story.append(Spacer(1, 10*mm))
    
    # 상태 한 줄
    status = data.get("month_status_summary", "이번 달 상태를 확인 중입니다.")
    story.append(Paragraph(status, ParagraphStyle(
        'StatusBox',
        parent=styles['Normal'],
        fontSize=12,
        backColor=HexColor('#e7f3ff'),
        borderPadding=10,
        spaceAfter=10
    )))
    
    return story


def _create_page_3_sales_flow(data: Dict, styles) -> List:
    """3P. 매출 흐름"""
    story = []
    
    story.append(Paragraph("매출 흐름", ParagraphStyle(
        'PageTitle',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=15
    )))
    
    # 일별 매출 시리즈
    daily_series = data.get("sales_daily_series", [])
    
    if daily_series:
        # 최근 7일 표
        recent_7 = daily_series[-7:] if len(daily_series) >= 7 else daily_series
        
        table_data = [["날짜", "매출"]]
        for date_label, total in recent_7:
            table_data.append([date_label, _format_currency(total)])
        
        sales_table = Table(table_data, colWidths=[40*mm, 60*mm])
        sales_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (-1, 0), black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#dee2e6')),
        ]))
        story.append(sales_table)
        story.append(Spacer(1, 10*mm))
        
        # 요약 지표
        if len(daily_series) >= 3:
            recent_3_avg = sum([s[1] for s in daily_series[-3:]]) / 3
            prev_3_avg = sum([s[1] for s in daily_series[-6:-3]]) / 3 if len(daily_series) >= 6 else recent_3_avg
            change_pct = ((recent_3_avg - prev_3_avg) / prev_3_avg * 100) if prev_3_avg > 0 else 0
            story.append(Paragraph(f"최근 3일 평균: {_format_currency(recent_3_avg)}", styles['Normal']))
            if len(daily_series) >= 6:
                change_text = "증가" if change_pct > 0 else "감소"
                story.append(Paragraph(f"직전 3일 대비 {abs(change_pct):.1f}% {change_text}", styles['Normal']))
    else:
        story.append(Paragraph("아직 매출 데이터가 없습니다.", styles['Normal']))
    
    return story


def _create_page_4_profit_structure(data: Dict, styles) -> List:
    """4P. 손익 구조"""
    story = []
    
    story.append(Paragraph("손익 구조", ParagraphStyle(
        'PageTitle',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=15
    )))
    
    # 구조 요약
    fixed_cost = data.get("fixed_cost", 0)
    variable_ratio = data.get("variable_ratio", 0)
    break_even = data.get("break_even_sales", 0)
    
    if break_even > 0:
        structure_data = [
            [f"고정비<br/>{_format_currency(fixed_cost)}", 
             f"변동비율<br/>{int(variable_ratio * 100)}%", 
             f"손익분기점<br/>{_format_currency(break_even)}"]
        ]
        
        structure_table = Table(structure_data, colWidths=[50*mm, 50*mm, 50*mm])
        structure_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, -1), white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, white),
        ]))
        story.append(structure_table)
        story.append(Spacer(1, 10*mm))
        
        # 구조 문장
        structure_sentence = data.get("structure_sentence", "")
        if structure_sentence:
            story.append(Paragraph(structure_sentence, ParagraphStyle(
                'StructureSentence',
                parent=styles['Normal'],
                fontSize=12,
                backColor=HexColor('#d1ecf1'),
                borderPadding=10,
                spaceAfter=10
            )))
        
        # 예시 테이블
        examples = data.get("profit_examples", [])
        if examples:
            story.append(Spacer(1, 10*mm))
            example_data = [["매출 구간", "매출", "이익"]]
            for label, sales_val, profit_val in examples:
                example_data.append([label, _format_currency(sales_val), _format_currency(profit_val)])
            
            example_table = Table(example_data, colWidths=[40*mm, 50*mm, 50*mm])
            example_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f8f9fa')),
                ('TEXTCOLOR', (0, 0), (-1, 0), black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#dee2e6')),
            ]))
            story.append(example_table)
    else:
        story.append(Paragraph("손익 구조 데이터가 없습니다. 목표 비용구조 또는 실제정산을 입력해주세요.", styles['Normal']))
    
    return story


def _create_page_6_problems_goods(data: Dict, styles) -> List:
    """6P. 문제 & 잘한 점"""
    story = []
    
    story.append(Paragraph("문제 & 잘한 점", ParagraphStyle(
        'PageTitle',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=15
    )))
    
    # 문제 TOP 3
    problems = data.get("problems_top3", [])
    if problems:
        story.append(Paragraph("문제 TOP 3", ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=HexColor('#dc3545'),
            spaceAfter=5
        )))
        for idx, problem in enumerate(problems, 1):
            story.append(Paragraph(f"{idx}. {problem}", ParagraphStyle(
                'ProblemItem',
                parent=styles['Normal'],
                fontSize=10,
                backColor=HexColor('#f8d7da'),
                borderPadding=5,
                leftIndent=10,
                spaceAfter=5
            )))
    else:
        story.append(Paragraph("발견된 문제가 없습니다.", styles['Normal']))
    
    story.append(Spacer(1, 10*mm))
    
    # 잘한 점 TOP 3
    goods = data.get("goods_top3", [])
    if goods:
        story.append(Paragraph("잘한 점 TOP 3", ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=HexColor('#28a745'),
            spaceAfter=5
        )))
        for idx, good in enumerate(goods, 1):
            story.append(Paragraph(f"{idx}. {good}", ParagraphStyle(
                'GoodItem',
                parent=styles['Normal'],
                fontSize=10,
                backColor=HexColor('#d4edda'),
                borderPadding=5,
                leftIndent=10,
                spaceAfter=5
            )))
    else:
        story.append(Paragraph("데이터가 쌓이면 자동 분석됩니다.", styles['Normal']))
    
    story.append(Spacer(1, 10*mm))
    
    # 이상 징후
    signals = data.get("anomaly_signals", [])
    if signals:
        story.append(Paragraph("이상 징후", ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=HexColor('#ffc107'),
            spaceAfter=5
        )))
        for signal in signals:
            story.append(Paragraph(f"⚠️ {signal}", ParagraphStyle(
                'SignalItem',
                parent=styles['Normal'],
                fontSize=10,
                backColor=HexColor('#fff3cd'),
                borderPadding=5,
                leftIndent=10,
                spaceAfter=5
            )))
    
    return story


def _create_page_8_coach_summary(data: Dict, styles) -> List:
    """8P. 코치 총평"""
    story = []
    
    story.append(Paragraph("코치 총평", ParagraphStyle(
        'PageTitle',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=15
    )))
    
    # 코치 요약
    coach_summary = data.get("coach_summary", "이번 달 가게 상태를 확인 중입니다.")
    story.append(Paragraph(coach_summary, ParagraphStyle(
        'CoachSummary',
        parent=styles['Normal'],
        fontSize=14,
        backColor=HexColor('#e7f3ff'),
        borderPadding=15,
        spaceAfter=15
    )))
    
    story.append(Spacer(1, 10*mm))
    
    # 개선 포인트
    actions = data.get("coach_actions", [])
    if actions:
        story.append(Paragraph("핵심 개선 포인트", ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=5
        )))
        for idx, action in enumerate(actions, 1):
            story.append(Paragraph(f"{idx}. {action}", ParagraphStyle(
                'ActionItem',
                parent=styles['Normal'],
                fontSize=10,
                backColor=HexColor('#fff3cd'),
                borderPadding=5,
                leftIndent=10,
                spaceAfter=5
            )))
    
    story.append(Spacer(1, 10*mm))
    
    # 다음 달 제안 (간단 버전)
    monthly_sales = data.get("monthly_sales", 0)
    if monthly_sales > 0:
        next_target = monthly_sales * 1.1  # 10% 성장 가정
        story.append(Paragraph("다음 달 제안", ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=5
        )))
        story.append(Paragraph(f"목표 매출: {_format_currency(next_target)}", styles['Normal']))
    
    return story


def build_scorecard_pdf_bytes(store_id: str, year: int, month: int) -> bytes:
    """
    PDF 성적표 생성 (bytes 반환)
    
    Args:
        store_id: 매장 ID
        year: 연도
        month: 월
    
    Returns:
        bytes: PDF 파일 바이트
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError("ReportLab이 설치되지 않았습니다. requirements.txt에 reportlab을 추가해주세요.")
    
    # 데이터 수집
    data = gather_scorecard_mvp_data(store_id, year, month)
    
    # PDF 생성
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )
    
    # 스타일 설정
    styles = getSampleStyleSheet()
    
    # 스타일 한글 폰트 적용
    for style_name in styles.byName:
        style = styles[style_name]
        if hasattr(style, 'fontName'):
            style.fontName = FONT_NAME
    
    # 스토리 구성
    story = []
    
    # 1P. 표지
    story.extend(_create_page_1_cover(data, styles))
    story.append(PageBreak())
    
    # 2P. 매장 요약
    story.extend(_create_page_2_summary(data, styles))
    story.append(PageBreak())
    
    # 3P. 매출 흐름
    story.extend(_create_page_3_sales_flow(data, styles))
    story.append(PageBreak())
    
    # 4P. 손익 구조
    story.extend(_create_page_4_profit_structure(data, styles))
    story.append(PageBreak())
    
    # 6P. 문제 & 잘한 점
    story.extend(_create_page_6_problems_goods(data, styles))
    story.append(PageBreak())
    
    # 8P. 코치 총평
    story.extend(_create_page_8_coach_summary(data, styles))
    
    # PDF 빌드
    doc.build(story)
    
    # bytes 반환
    buffer.seek(0)
    return buffer.getvalue()
