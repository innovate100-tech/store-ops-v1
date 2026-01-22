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
    
    # 저장 후 메시지 표시 (세션 상태에서) - 통합된 세련된 디자인
    if "sales_entry_success_message" in st.session_state:
        msg = st.session_state["sales_entry_success_message"]
        msg_type = st.session_state.get("sales_entry_message_type", "success")
        
        # 통합된 세련된 알림 박스 (하나로 통합)
        if msg_type == "success":
            st.markdown(f"""
            <div style="
                padding: 1.5rem; 
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                border-radius: 12px; 
                margin: 1rem 0;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                color: #ffffff;
            ">
                <div style="display: flex; align-items: center; margin-bottom: 0.75rem;">
                    <span style="font-size: 1.5rem; margin-right: 0.5rem;">✅</span>
                    <h3 style="color: #ffffff; margin: 0; font-size: 1.25rem; font-weight: 600;">매출 저장 완료</h3>
                </div>
                <div style="font-size: 0.95rem; line-height: 1.6; color: #f0fdf4;">
                    {msg.replace(chr(10), '<br>')}
                </div>
            </div>
            """, unsafe_allow_html=True)
            try:
                st.toast("✅ 매출 저장 완료!", icon="✅")
            except:
                pass
        elif msg_type == "warning":
            st.markdown(f"""
            <div style="
                padding: 1.5rem; 
                background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
                border-radius: 12px; 
                margin: 1rem 0;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                color: #ffffff;
            ">
                <div style="display: flex; align-items: center; margin-bottom: 0.75rem;">
                    <span style="font-size: 1.5rem; margin-right: 0.5rem;">⚠️</span>
                    <h3 style="color: #ffffff; margin: 0; font-size: 1.25rem; font-weight: 600;">충돌 감지</h3>
                </div>
                <div style="font-size: 0.95rem; line-height: 1.6; color: #fffbeb;">
                    {msg.replace(chr(10), '<br>')}
                </div>
            </div>
            """, unsafe_allow_html=True)
            try:
                st.toast("⚠️ 충돌 감지", icon="⚠️")
            except:
                pass
        elif msg_type == "error":
            st.markdown(f"""
            <div style="
                padding: 1.5rem; 
                background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                border-radius: 12px; 
                margin: 1rem 0;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                color: #ffffff;
            ">
                <div style="display: flex; align-items: center; margin-bottom: 0.75rem;">
                    <span style="font-size: 1.5rem; margin-right: 0.5rem;">❌</span>
                    <h3 style="color: #ffffff; margin: 0; font-size: 1.25rem; font-weight: 600;">저장 실패</h3>
                </div>
                <div style="font-size: 0.95rem; line-height: 1.6; color: #fef2f2;">
                    {msg.replace(chr(10), '<br>')}
                </div>
            </div>
            """, unsafe_allow_html=True)
            try:
                st.toast("❌ 저장 실패", icon="❌")
            except:
                pass
        
        # 닫기 버튼 (더 세련된 스타일)
        col1, col2, col3 = st.columns([4, 1, 4])
        with col2:
            if st.button("✕ 닫기", key="close_sales_message", use_container_width=True, type="secondary"):
                del st.session_state["sales_entry_success_message"]
                if "sales_entry_message_type" in st.session_state:
                    del st.session_state["sales_entry_message_type"]
                st.rerun()
        
        render_section_divider()
    
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
                        try:
                            # 충돌 확인을 위해 직접 save_sales 호출
                            success, conflict_info = save_sales(date, store, card_sales, cash_sales, total_sales, check_conflict=True)
                            
                            if success:
                                # 캐시 무효화
                                from src.storage_supabase import soft_invalidate, load_monthly_sales_total
                                soft_invalidate(reason="save_sales", targets=["sales"])
                                try:
                                    load_monthly_sales_total.clear()
                                except Exception:
                                    pass
                                
                                # 메시지 구성
                                if conflict_info:
                                    existing = conflict_info.get('existing_total_sales', 0)
                                    has_daily_close = conflict_info.get('has_daily_close', False)
                                    
                                    if has_daily_close:
                                        daily_close_total = conflict_info.get('daily_close_total_sales', 0)
                                        message = f"""⚠️ 주의: 해당 날짜에 마감보고가 이미 등록되어 있습니다!<br><br>• 마감보고 매출: <strong>{daily_close_total:,.0f}원</strong><br>• 기존 매출등록 값: <strong>{existing:,.0f}원</strong><br>• 새로 입력한 값: <strong>{total_sales:,.0f}원</strong><br><br>→ 새 값으로 덮어쓰기되었습니다.<br><br>✅ 매출이 저장되었습니다!<br>📅 날짜: {date}  |  🏪 매장: {store}  |  💰 총매출: <strong>{total_sales:,}원</strong>"""
                                        st.session_state["sales_entry_success_message"] = message
                                        st.session_state["sales_entry_message_type"] = "warning"
                                else:
                                    message = f"""⚠️ 주의: 해당 날짜에 이미 다른 매출 값이 등록되어 있습니다.<br><br>• 기존 값: <strong>{existing:,.0f}원</strong><br>• 새 값: <strong>{total_sales:,.0f}원</strong><br><br>→ 새 값으로 덮어쓰기되었습니다.<br><br>✅ 매출이 저장되었습니다!<br>📅 날짜: {date}  |  🏪 매장: {store}  |  💰 총매출: <strong>{total_sales:,}원</strong>"""
                                    st.session_state["sales_entry_success_message"] = message
                                    st.session_state["sales_entry_message_type"] = "warning"
                                else:
                                    # 성공 메시지 (간결하고 가독성 있게)
                                    message = f"""✅ 매출이 저장되었습니다!<br><br>📅 날짜: {date}<br>🏪 매장: {store}<br>💰 총매출: <strong>{total_sales:,}원</strong>"""
                                    st.session_state["sales_entry_success_message"] = message
                                    st.session_state["sales_entry_message_type"] = "success"
                                
                                st.rerun()
                            else:
                                st.session_state["sales_entry_success_message"] = "❌ 매출 저장에 실패했습니다."
                                st.session_state["sales_entry_message_type"] = "error"
                                st.rerun()
                        except Exception as e:
                            st.session_state["sales_entry_success_message"] = f"❌ 매출 저장 실패: {str(e)}"
                            st.session_state["sales_entry_message_type"] = "error"
                            st.rerun()
        
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
                                    # 충돌 확인을 위해 직접 save_sales 호출
                                    success, conflict_info = save_sales(date, store, card_sales, cash_sales, total_sales, check_conflict=True)
                                    
                                    if success:
                                        # 충돌이 있으면 경고 (일괄 저장에서는 로그만)
                                        if conflict_info:
                                            existing = conflict_info.get('existing_total_sales', 0)
                                            has_daily_close = conflict_info.get('has_daily_close', False)
                                            if has_daily_close:
                                                errors.append(f"{date}: ⚠️ 마감보고와 충돌 (기존: {existing:,.0f}원 → 새: {total_sales:,.0f}원, 덮어쓰기됨)")
                                            else:
                                                errors.append(f"{date}: ⚠️ 기존 값과 충돌 (기존: {existing:,.0f}원 → 새: {total_sales:,.0f}원, 덮어쓰기됨)")
                                        
                                        # 캐시 무효화
                                        from src.storage_supabase import soft_invalidate, load_monthly_sales_total
                                        soft_invalidate(reason="save_sales_batch", targets=["sales"])
                                        try:
                                            load_monthly_sales_total.clear()
                                        except Exception:
                                            pass
                                        
                                        success_count += 1
                                    else:
                                        errors.append(f"{date}: 저장 실패")
                                except Exception as e:
                                    errors.append(f"{date}: {e}")
                        
                        # 에러와 경고를 구분하여 표시
                        warnings = [e for e in errors if "⚠️" in e]
                        real_errors = [e for e in errors if "⚠️" not in e]
                        
                        # 메시지 구성
                        message_parts = []
                        
                        if warnings:
                            message_parts.append(f"⚠️ **{len(warnings)}건의 충돌이 감지되었습니다:**")
                            for warning in warnings:
                                message_parts.append(f"- {warning}")
                        
                        if real_errors:
                            message_parts.append(f"\n❌ **{len(real_errors)}건의 오류가 발생했습니다:**")
                            for error in real_errors:
                                message_parts.append(f"- {error}")
                        
                        if success_count > 0:
                            message_parts.append(f"\n✅ **{success_count}일의 매출이 저장되었습니다!**")
                            message = "\n".join(message_parts)
                            
                            if warnings:
                                st.session_state["sales_entry_success_message"] = message
                                st.session_state["sales_entry_message_type"] = "warning"
                            else:
                                st.session_state["sales_entry_success_message"] = message
                                st.session_state["sales_entry_message_type"] = "success"
                            
                            st.balloons()
                            st.rerun()  # 일괄 저장 완료 후 한 번만 rerun
                        elif real_errors:
                            message = "\n".join(message_parts)
                            st.session_state["sales_entry_success_message"] = message
                            st.session_state["sales_entry_message_type"] = "error"
                            st.rerun()
                        elif not real_errors and not warnings:
                            st.info("💡 저장할 데이터가 없습니다.")
    
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
