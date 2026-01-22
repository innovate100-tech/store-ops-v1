"""
리포트 생성 모듈 (PDF)
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO


# 한글 폰트 설정 (matplotlib)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False


def get_reports_dir():
    """reports 디렉토리 경로 반환"""
    base_dir = Path(__file__).parent.parent
    reports_dir = base_dir / "reports"
    reports_dir.mkdir(exist_ok=True)
    return reports_dir


def create_sales_visitor_chart(sales_df, visitors_df, start_date, end_date):
    """매출 vs 방문자 추세 차트 생성"""
    fig, ax1 = plt.subplots(figsize=(10, 5))
    
    # 날짜 기준 조인
    merged = pd.merge(
        sales_df[['날짜', '총매출']],
        visitors_df[['날짜', '방문자수']],
        on='날짜',
        how='outer'
    )
    merged = merged.sort_values('날짜')
    
    # 매출 차트 (왼쪽 Y축)
    ax1.set_xlabel('날짜')
    ax1.set_ylabel('매출 (원)', color='blue')
    ax1.plot(merged['날짜'], merged['총매출'], marker='o', color='blue', linewidth=2, label='매출')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.grid(True, alpha=0.3)
    
    # 방문자 차트 (오른쪽 Y축)
    ax2 = ax1.twinx()
    ax2.set_ylabel('방문자수', color='red')
    ax2.plot(merged['날짜'], merged['방문자수'], marker='s', color='red', linewidth=2, label='방문자수')
    ax2.tick_params(axis='y', labelcolor='red')
    
    plt.title('매출 vs 방문자 추세', fontsize=14, pad=20)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # 이미지로 변환
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
    img_buffer.seek(0)
    plt.close()
    
    return img_buffer


def generate_weekly_report(
    sales_df,
    visitors_df,
    daily_sales_df,
    recipe_df,
    ingredient_df,
    inventory_df,
    usage_df,
    start_date,
    end_date,
    filename=None
):
    """
    주간 리포트 PDF 생성
    
    Args:
        sales_df: 매출 DataFrame
        visitors_df: 방문자 DataFrame
        daily_sales_df: 일일 판매 DataFrame
        recipe_df: 레시피 DataFrame
        ingredient_df: 재료 마스터 DataFrame
        inventory_df: 재고 DataFrame
        usage_df: 재료 사용량 DataFrame
        start_date: 시작일
        end_date: 종료일
        filename: 파일명 (없으면 자동 생성)
    
    Returns:
        str: 생성된 PDF 파일 경로
    """
    reports_dir = get_reports_dir()
    
    # 파일명 생성
    if filename is None:
        filename = f"주간리포트_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf"
    
    filepath = reports_dir / filename
    
    # PDF 문서 생성
    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # 스타일 설정
    styles = getSampleStyleSheet()
    
    # 한글 지원을 위한 스타일 (기본 스타일 사용)
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # 스토리 리스트
    story = []
    
    # 제목
    title = Paragraph(f"매장 운영 주간 리포트", title_style)
    story.append(title)
    story.append(Spacer(1, 0.5*cm))
    
    # 기간 정보
    period_text = f"기간: {start_date.strftime('%Y년 %m월 %d일')} ~ {end_date.strftime('%Y년 %m월 %d일')}"
    story.append(Paragraph(period_text, styles['Normal']))
    story.append(Spacer(1, 0.3*cm))
    from src.utils.time_utils import now_kst
    story.append(Paragraph(f"생성일시: {now_kst().strftime('%Y년 %m월 %d일 %H:%M')} (KST)", styles['Normal']))
    story.append(Spacer(1, 1*cm))
    
    # 1. 매출 정보
    story.append(Paragraph("1. 매출 현황", heading_style))
    
    if not sales_df.empty:
        period_sales = sales_df[
            (sales_df['날짜'] >= pd.to_datetime(start_date)) &
            (sales_df['날짜'] <= pd.to_datetime(end_date))
        ]
        
        if not period_sales.empty:
            total_sales = period_sales['총매출'].sum()
            avg_sales = total_sales / len(period_sales)
            
            sales_data = [
                ['항목', '값'],
                ['총매출', f"{int(total_sales):,}원"],
                ['일평균 매출', f"{int(avg_sales):,}원"],
                ['기간 일수', f"{len(period_sales)}일"]
            ]
            
            sales_table = Table(sales_data, colWidths=[6*cm, 6*cm])
            sales_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(sales_table)
        else:
            story.append(Paragraph("해당 기간의 매출 데이터가 없습니다.", styles['Normal']))
    else:
        story.append(Paragraph("매출 데이터가 없습니다.", styles['Normal']))
    
    story.append(Spacer(1, 0.5*cm))
    
    # 2. 방문자 정보
    story.append(Paragraph("2. 방문자 현황", heading_style))
    
    if not visitors_df.empty:
        period_visitors = visitors_df[
            (visitors_df['날짜'] >= pd.to_datetime(start_date)) &
            (visitors_df['날짜'] <= pd.to_datetime(end_date))
        ]
        
        if not period_visitors.empty:
            total_visitors = period_visitors['방문자수'].sum()
            avg_visitors = total_visitors / len(period_visitors)
            
            visitor_data = [
                ['항목', '값'],
                ['총 방문자수', f"{int(total_visitors):,}명"],
                ['일평균 방문자수', f"{avg_visitors:.1f}명"],
                ['기간 일수', f"{len(period_visitors)}일"]
            ]
            
            visitor_table = Table(visitor_data, colWidths=[6*cm, 6*cm])
            visitor_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(visitor_table)
        else:
            story.append(Paragraph("해당 기간의 방문자 데이터가 없습니다.", styles['Normal']))
    else:
        story.append(Paragraph("방문자 데이터가 없습니다.", styles['Normal']))
    
    story.append(Spacer(1, 0.5*cm))
    
    # 3. 매출 vs 방문자 추세 차트
    if not sales_df.empty and not visitors_df.empty:
        story.append(Paragraph("3. 매출 vs 방문자 추세", heading_style))
        try:
            chart_img = create_sales_visitor_chart(sales_df, visitors_df, start_date, end_date)
            img = Image(chart_img, width=16*cm, height=8*cm)
            story.append(img)
            story.append(Spacer(1, 0.5*cm))
        except Exception as e:
            story.append(Paragraph(f"차트 생성 중 오류: {str(e)}", styles['Normal']))
    
    # 4. 메뉴별 판매 TOP 10
    story.append(Paragraph("4. 메뉴별 판매 TOP 10", heading_style))
    
    if not daily_sales_df.empty:
        period_sales_items = daily_sales_df[
            (pd.to_datetime(daily_sales_df['날짜']) >= pd.to_datetime(start_date)) &
            (pd.to_datetime(daily_sales_df['날짜']) <= pd.to_datetime(end_date))
        ]
        
        if not period_sales_items.empty:
            menu_sales = period_sales_items.groupby('메뉴명')['판매수량'].sum().reset_index()
            menu_sales = menu_sales.sort_values('판매수량', ascending=False).head(10)
            
            menu_data = [['순위', '메뉴명', '판매수량']]
            for idx, row in menu_sales.iterrows():
                menu_data.append([
                    str(len(menu_data)),
                    row['메뉴명'],
                    f"{int(row['판매수량'])}개"
                ])
            
            menu_table = Table(menu_data, colWidths=[1.5*cm, 8*cm, 2.5*cm])
            menu_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (1, 0), (1, -1), 'LEFT')
            ]))
            story.append(menu_table)
        else:
            story.append(Paragraph("해당 기간의 판매 데이터가 없습니다.", styles['Normal']))
    else:
        story.append(Paragraph("판매 데이터가 없습니다.", styles['Normal']))
    
    story.append(Spacer(1, 0.5*cm))
    
    # 5. 재료 사용량 TOP 10
    story.append(Paragraph("5. 재료 사용량 TOP 10", heading_style))
    
    if not usage_df.empty:
        period_usage = usage_df[
            (pd.to_datetime(usage_df['날짜']) >= pd.to_datetime(start_date)) &
            (pd.to_datetime(usage_df['날짜']) <= pd.to_datetime(end_date))
        ]
        
        if not period_usage.empty:
            ingredient_usage = period_usage.groupby('재료명')['총사용량'].sum().reset_index()
            ingredient_usage = ingredient_usage.sort_values('총사용량', ascending=False).head(10)
            
            # 재료 단위 정보 추가
            if not ingredient_df.empty:
                ingredient_usage = pd.merge(
                    ingredient_usage,
                    ingredient_df[['재료명', '단위']],
                    on='재료명',
                    how='left'
                )
                ingredient_usage['단위'] = ingredient_usage['단위'].fillna('')
            else:
                ingredient_usage['단위'] = ''
            
            usage_data = [['순위', '재료명', '총 사용량']]
            for idx, row in ingredient_usage.iterrows():
                unit_text = f"{row['단위']}" if row['단위'] else ""
                usage_data.append([
                    str(len(usage_data)),
                    row['재료명'],
                    f"{row['총사용량']:.2f}{unit_text}"
                ])
            
            usage_table = Table(usage_data, colWidths=[1.5*cm, 8*cm, 2.5*cm])
            usage_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (1, 0), (1, -1), 'LEFT')
            ]))
            story.append(usage_table)
        else:
            story.append(Paragraph("해당 기간의 재료 사용량 데이터가 없습니다.", styles['Normal']))
    else:
        story.append(Paragraph("재료 사용량 데이터가 없습니다.", styles['Normal']))
    
    story.append(Spacer(1, 0.5*cm))
    
    # 6. 발주 추천 TOP 10
    story.append(Paragraph("6. 발주 추천 TOP 10", heading_style))
    
    if not inventory_df.empty and not ingredient_df.empty:
        # 발주 추천 계산 (간단 버전)
        from src.analytics import calculate_order_recommendation
        
        try:
            order_df = calculate_order_recommendation(
                ingredient_df,
                inventory_df,
                usage_df if not usage_df.empty else pd.DataFrame(),
                days_for_avg=7,
                forecast_days=3
            )
            
            if not order_df.empty:
                order_top10 = order_df.head(10)
                
                order_data = [['순위', '재료명', '발주필요량', '예상금액']]
                for idx, row in order_top10.iterrows():
                    unit_text = f"{row['단위']}" if '단위' in row else ""
                    order_data.append([
                        str(len(order_data)),
                        row['재료명'],
                        f"{row['발주필요량']:.2f}{unit_text}",
                        f"{int(row['예상금액']):,}원"
                    ])
                
                order_table = Table(order_data, colWidths=[1.5*cm, 5*cm, 3*cm, 2.5*cm])
                order_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT')
                ]))
                story.append(order_table)
                
                # 총 예상 금액
                total_order_amount = order_df['예상금액'].sum()
                story.append(Spacer(1, 0.3*cm))
                story.append(Paragraph(f"총 예상 발주 금액: {int(total_order_amount):,}원", styles['Normal']))
            else:
                story.append(Paragraph("현재 발주가 필요한 재료가 없습니다.", styles['Normal']))
        except Exception as e:
            story.append(Paragraph(f"발주 추천 계산 중 오류: {str(e)}", styles['Normal']))
    else:
        story.append(Paragraph("재고 또는 재료 데이터가 없습니다.", styles['Normal']))
    
    # PDF 빌드
    doc.build(story)
    
    return str(filepath)
