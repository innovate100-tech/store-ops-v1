"""
주간 리포트 페이지
"""
from src.bootstrap import bootstrap
import streamlit as st
from datetime import datetime
from pathlib import Path
from src.ui_helpers import render_page_header, render_section_header, render_section_divider
from src.ui import render_report_input
from src.storage_supabase import load_csv
from src.reporting import generate_weekly_report
from src.analytics import calculate_ingredient_usage

# 공통 설정 적용
bootstrap(page_title="Weekly Report")


def render_weekly_report():
    """주간 리포트 페이지 렌더링"""
    render_page_header("주간 리포트 생성", "📄")
    
    # 리포트 입력 폼
    start_date, end_date = render_report_input()
    
    # 날짜 유효성 검사
    if start_date > end_date:
        st.error("시작일이 종료일보다 늦을 수 없습니다.")
    else:
        st.markdown("---")
        
        # 리포트 생성 버튼
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("📄 리포트 생성", type="primary", use_container_width=True):
                try:
                    # 필요한 데이터 로드
                    sales_df = load_csv('sales.csv', default_columns=['날짜', '매장', '총매출'])
                    visitors_df = load_csv('naver_visitors.csv', default_columns=['날짜', '방문자수'])
                    daily_sales_df = load_csv('daily_sales_items.csv', default_columns=['날짜', '메뉴명', '판매수량'])
                    recipe_df = load_csv('recipes.csv', default_columns=['메뉴명', '재료명', '사용량'])
                    ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가'])
                    inventory_df = load_csv('inventory.csv', default_columns=['재료명', '현재고', '안전재고'])
                    
                    # 재료 사용량 계산
                    usage_df = calculate_ingredient_usage(daily_sales_df, recipe_df)
                    
                    # 리포트 생성
                    with st.spinner("리포트 생성 중..."):
                        try:
                            pdf_path = generate_weekly_report(
                                sales_df,
                                visitors_df,
                                daily_sales_df,
                                recipe_df,
                                ingredient_df,
                                inventory_df,
                                usage_df,
                                start_date,
                                end_date
                            )
                            
                            # 폰트 등록 상태 확인
                            from src.reporting import KOREAN_FONT_SUCCESS, KOREAN_FONT_NAME
                            if not KOREAN_FONT_SUCCESS:
                                st.warning("⚠️ **한글 폰트 등록 실패**: PDF의 한글이 깨져 보일 수 있습니다. Windows 폰트 폴더에 한글 폰트가 있는지 확인해주세요.")
                                st.info("💡 해결 방법: `C:\\Windows\\Fonts\\` 폴더에 `malgun.ttf` 파일이 있는지 확인하세요.")
                            else:
                                st.success(f"리포트가 생성되었습니다! 📄 (폰트: {KOREAN_FONT_NAME})")
                        except Exception as e:
                            st.error(f"리포트 생성 중 오류가 발생했습니다: {e}")
                            raise
                    
                    # PDF 다운로드 버튼
                    with open(pdf_path, 'rb') as f:
                        pdf_data = f.read()
                    
                    st.download_button(
                        label="📥 PDF 다운로드",
                        data=pdf_data,
                        file_name=f"주간리포트_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf",
                        mime="application/pdf"
                    )
                    
                    # 리포트 미리보기 정보
                    render_section_divider()
                    render_section_header("리포트 포함 내용", "📋")
                    st.info("""
                    - 총매출 및 일평균 매출
                    - 방문자수 총합 및 일평균
                    - 매출 vs 방문자 추세 차트
                    - 메뉴별 판매 TOP 10
                    - 재료 사용량 TOP 10
                    - 발주 추천 TOP 10
                    """)
                    
                except Exception as e:
                    st.error(f"리포트 생성 중 오류가 발생했습니다: {e}")
                    st.exception(e)
        
        # 기존 리포트 목록 표시
        render_section_divider()
        render_section_header("생성된 리포트 목록", "📁")
        
        reports_dir = Path(__file__).parent / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        pdf_files = list(reports_dir.glob("*.pdf"))
        if pdf_files:
            pdf_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for pdf_file in pdf_files[:10]:  # 최근 10개만 표시
                with open(pdf_file, 'rb') as f:
                    pdf_data = f.read()
                
                file_size = len(pdf_data) / 1024  # KB
                file_date = datetime.fromtimestamp(pdf_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"📄 {pdf_file.name}")
                with col2:
                    st.write(f"{file_size:.1f} KB ({file_date})")
                with col3:
                    st.download_button(
                        label="다운로드",
                        data=pdf_data,
                        file_name=pdf_file.name,
                        mime="application/pdf",
                        key=f"download_{pdf_file.name}"
                    )
        else:
            st.info("생성된 리포트가 없습니다.")


# Streamlit 멀티페이지에서 직접 실행될 때
# 주석 처리: app.py에서만 렌더되도록 함 (중복 호출 방지)
# render_weekly_report()
