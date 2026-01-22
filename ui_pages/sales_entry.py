"""
매출 등록 페이지
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
import logging
from src.ui_helpers import render_page_header, render_section_divider, handle_data_error
from src.storage_supabase import save_sales, save_visitor
from src.ui import render_sales_input, render_sales_batch_input, render_visitor_input, render_visitor_batch_input
from src.utils.crud_guard import run_write
from src.auth import get_current_store_id

# 공통 설정 적용
bootstrap(page_title="Sales Entry")

# 로그인 체크
from src.auth import check_login, show_login_page
if not check_login():
    show_login_page()
    st.stop()


def render_sales_entry():
    """매출 등록 페이지 렌더링"""
    render_page_header("매출 등록", "💰")
    
    # 카테고리 선택 (매출 / 네이버 스마트플레이스 방문자)
    category = st.radio(
        "카테고리",
        ["💰 매출", "👥 네이버 스마트플레이스 방문자"],
        horizontal=True,
        key="sales_entry_sales_category"
    )
    
    render_section_divider()
    
    # ========== 매출 입력 섹션 ==========
    if category == "💰 매출":
        # 입력 모드 선택 (단일 / 일괄)
        input_mode = st.radio(
            "입력 모드",
            ["단일 입력", "일괄 입력 (여러 날짜)"],
            horizontal=True,
            key="sales_input_mode"
        )
        
        render_section_divider()
        
        if input_mode == "단일 입력":
            # 단일 입력 폼
            date, store, card_sales, cash_sales, total_sales = render_sales_input()
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("💾 저장", type="primary", use_container_width=True):
                    if not store or store.strip() == "":
                        st.error("매장명을 입력해주세요.")
                    elif total_sales <= 0:
                        st.error("매출은 0보다 큰 값이어야 합니다.")
                    else:
                        # run_write로 통일
                        run_write(
                            "save_sales",
                            lambda: save_sales(date, store, card_sales, cash_sales, total_sales),
                            targets=["sales"],
                            extra={"date": str(date), "store": store, "total_sales": total_sales},
                            success_message=f"✅ 매출이 저장되었습니다! ({date}, {store}, 총매출: {total_sales:,}원)"
                        )
        
        else:
            # 일괄 입력 폼
            sales_data = render_sales_batch_input()
            
            if sales_data:
                render_section_divider()
                
                # 입력 요약 표시
                st.write("**📊 입력 요약**")
                summary_df = pd.DataFrame(
                    [(d.strftime('%Y-%m-%d'), s, f"{card:,}원", f"{cash:,}원", f"{total:,}원") 
                     for d, s, card, cash, total in sales_data],
                    columns=['날짜', '매장', '카드매출', '현금매출', '총매출']
                )
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
                
                total_card = sum(card for _, _, card, _, _ in sales_data)
                total_cash = sum(cash for _, _, _, cash, _ in sales_data)
                total_all = sum(total for _, _, _, _, total in sales_data)
                
                st.markdown(f"**총 {len(sales_data)}일, 카드매출: {total_card:,}원, 현금매출: {total_cash:,}원, 총 매출: {total_all:,}원**")
                
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("💾 일괄 저장", type="primary", use_container_width=True):
                        errors = []
                        success_count = 0
                        
                        for date, store, card_sales, cash_sales, total_sales in sales_data:
                            if not store or store.strip() == "":
                                errors.append(f"{date}: 매장명이 없습니다.")
                            else:
                                try:
                                    run_write(
                                        "save_sales_batch",
                                        lambda d=date, s=store, c=card_sales, ca=cash_sales, t=total_sales: save_sales(d, s, c, ca, t),
                                        targets=["sales"],
                                        extra={"date": str(date), "store": store},
                                        rerun=False  # 일괄 저장은 마지막에 한 번만 rerun
                                    )
                                    success_count += 1
                                except Exception as e:
                                    errors.append(f"{date}: {e}")
                        
                        if errors:
                            for error in errors:
                                st.error(error)
                        
                        if success_count > 0:
                            st.success(f"✅ {success_count}일의 매출이 저장되었습니다!")
                            st.balloons()
                            st.rerun()  # 일괄 저장 완료 후 한 번만 rerun
    
    # ========== 네이버 스마트플레이스 방문자 입력 섹션 ==========
    else:
        # 입력 모드 선택 (단일 / 일괄)
        input_mode = st.radio(
            "입력 모드",
            ["단일 입력", "일괄 입력 (여러 날짜)"],
            horizontal=True,
            key="sales_entry_visitor_input_mode"
        )
        
        render_section_divider()
        
        if input_mode == "단일 입력":
            # 단일 입력 폼
            date, visitors = render_visitor_input()
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("💾 저장", type="primary", use_container_width=True):
                    if visitors <= 0:
                        st.error("네이버 스마트플레이스 방문자수는 0보다 큰 값이어야 합니다.")
                    else:
                        # run_write로 통일
                        run_write(
                            "save_visitor",
                            lambda: save_visitor(date, visitors),
                            targets=["visitors"],
                            extra={"date": str(date), "visitors": visitors},
                            success_message=f"✅ 네이버 스마트플레이스 방문자수가 저장되었습니다! ({date}, {visitors}명)"
                        )
        
        else:
            # 일괄 입력 폼
            visitor_data = render_visitor_batch_input()
            
            if visitor_data:
                render_section_divider()
                
                # 입력 요약 표시
                st.write("**📊 입력 요약**")
                summary_df = pd.DataFrame(
                    [(d.strftime('%Y-%m-%d'), f"{v}명") for d, v in visitor_data],
                    columns=['날짜', '네이버 스마트플레이스 방문자수']
                )
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
                
                st.markdown(f"**총 {len(visitor_data)}일, 총 네이버 스마트플레이스 방문자수: {sum(v for _, v in visitor_data):,}명**")
                
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("💾 일괄 저장", type="primary", use_container_width=True):
                        errors = []
                        success_count = 0
                        
                        for date, visitors in visitor_data:
                            try:
                                run_write(
                                    "save_visitor_batch",
                                    lambda d=date, v=visitors: save_visitor(d, v),
                                    targets=["visitors"],
                                    extra={"date": str(date)},
                                    rerun=False  # 일괄 저장은 마지막에 한 번만 rerun
                                )
                                success_count += 1
                            except Exception as e:
                                errors.append(f"{date}: {e}")
                        
                        if errors:
                            for error in errors:
                                st.error(error)
                        
                        if success_count > 0:
                            st.success(f"✅ {success_count}일의 네이버 스마트플레이스 방문자수가 저장되었습니다!")
                            st.balloons()
                            st.rerun()  # 일괄 저장 완료 후 한 번만 rerun


# Streamlit 멀티페이지에서 직접 실행될 때
# 주석 처리: app.py에서만 렌더되도록 함 (중복 호출 방지)
# render_sales_entry()
