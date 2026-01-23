"""
매출 등록 페이지
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
import logging
from src.ui_helpers import render_page_header, render_section_divider, handle_data_error
from src.storage_supabase import save_sales, save_visitor, save_sales_entry, get_day_record_status
from src.ui import render_sales_input, render_sales_batch_input, render_visitor_input, render_visitor_batch_input
from src.utils.crud_guard import run_write
from src.auth import get_current_store_id

logger = logging.getLogger(__name__)

# 공통 설정 적용
bootstrap(page_title="Sales Entry")

# 로그인 체크
from src.auth import check_login, show_login_page
if not check_login():
    show_login_page()
    st.stop()


def render_sales_entry():
    """매출 등록 페이지 렌더링"""
    render_page_header("🛠 매출 보정 / 과거 매출 입력", "💰")
    
    # STEP 3: 보정/이관 성격 안내
    st.markdown("""
    <div style="padding: 1.2rem; background: #fff3cd; border-left: 4px solid #ffc107; 
                border-radius: 8px; margin-bottom: 1.5rem;">
        <div style="font-weight: 600; color: #856404; margin-bottom: 0.5rem;">🛠 보정 도구</div>
        <div style="color: #856404; font-size: 0.95rem; line-height: 1.6;">
            일반적인 매출 입력은 점장마감을 사용하세요. 이 화면은 과거 매출 입력 및 보정용입니다.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # DB 연결 상태 확인 및 표시 (디버그 모드)
    from src.auth import is_dev_mode, get_supabase_client, get_current_store_id
    from src.storage_supabase import _check_supabase_for_dev_mode
    
    if is_dev_mode():
        with st.expander("🔍 DB 연결 상태 (개발 모드)", expanded=False):
            supabase = _check_supabase_for_dev_mode()
            store_id = get_current_store_id()
            
            col1, col2 = st.columns(2)
            with col1:
                if supabase:
                    st.success("✅ Supabase 클라이언트: 연결됨")
                else:
                    st.error("❌ Supabase 클라이언트: 연결 실패")
            
            with col2:
                if store_id:
                    st.success(f"✅ Store ID: {store_id[:8]}...")
                else:
                    st.error("❌ Store ID: 없음")
    
    # 저장 후 메시지 표시 (세션 상태에서) - 통합된 세련된 디자인
    if "sales_entry_success_message" in st.session_state:
        msg = st.session_state["sales_entry_success_message"]
        msg_type = st.session_state.get("sales_entry_message_type", "success")
        
        # 통합된 세련된 알림 박스 (하나로 통합)
        # msg는 이미 HTML 형식으로 저장되어 있으므로 그대로 사용
        msg_html = str(msg)
        
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
                    {msg_html}
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
                    {msg_html}
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
                    {msg_html}
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
            
            # 날짜 선택 시 상태바 표시
            store_id = get_current_store_id()
            status = None
            if store_id and date:
                try:
                    status = get_day_record_status(store_id, date)
                except Exception:
                    pass
            
            # 상태바 표시
            if status:
                has_close = status["has_close"]
                has_sales = status["has_sales"]
                has_visitors = status["has_visitors"]
                
                if has_close:
                    # ① 마감 완료(공식)
                    st.markdown("""
                    <div style="padding: 1.2rem; background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                                border-radius: 12px; margin-bottom: 1.5rem; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                            <span style="font-size: 1.5rem; margin-right: 0.5rem;">✅</span>
                            <h3 style="color: white; margin: 0; font-size: 1.1rem; font-weight: 600;">마감 완료(공식)</h3>
                        </div>
                        <div style="font-size: 0.95rem; line-height: 1.6; color: #f0fdf4; margin-top: 0.5rem;">
                            이 화면에서는 매출과 네이버 방문자만 빠르게 수정합니다.<br>
                            판매량/메모는 점장마감에서 수정하세요.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                elif has_sales or has_visitors:
                    # ② 임시 기록(미마감)
                    st.markdown("""
                    <div style="padding: 1.2rem; background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); 
                                border-radius: 12px; margin-bottom: 1.5rem; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                            <span style="font-size: 1.5rem; margin-right: 0.5rem;">⚠️</span>
                            <h3 style="color: white; margin: 0; font-size: 1.1rem; font-weight: 600;">임시 기록(미마감)</h3>
                        </div>
                        <div style="font-size: 0.95rem; line-height: 1.6; color: #fffbeb; margin-top: 0.5rem;">
                            통계에는 반영되지만, 마감률/스트릭에는 반영되지 않습니다.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # CTA: 지금 마감으로 승격하기
                    if st.button("📋 지금 마감으로 승격하기", type="secondary", use_container_width=True, key="promote_to_close"):
                        st.session_state["current_page"] = "점장 마감"
                        st.session_state["manager_close_date"] = date
                        st.rerun()
                else:
                    # ③ 아직 기록 없음
                    st.markdown("""
                    <div style="padding: 1.2rem; background: #f0f2f6; border-left: 4px solid #667eea; 
                                border-radius: 12px; margin-bottom: 1.5rem;">
                        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                            <span style="font-size: 1.5rem; margin-right: 0.5rem;">📝</span>
                            <h3 style="color: #1f4788; margin: 0; font-size: 1.1rem; font-weight: 600;">아직 기록 없음</h3>
                        </div>
                        <div style="font-size: 0.95rem; line-height: 1.6; color: #495057; margin-top: 0.5rem;">
                            매출과 네이버 방문자를 입력하세요.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # 네이버 방문자 입력 (매출과 함께 저장 가능)
            st.markdown("---")
            st.write("**👥 네이버 방문자 (선택사항)**")
            visitors_input = st.number_input(
                "네이버 방문자 수",
                min_value=0,
                value=status["visitors_best"] if status and status["visitors_best"] is not None else 0,
                step=1,
                key="sales_entry_visitors"
            )
            
            col1, col2 = st.columns([1, 4])
            with col1:
                # 저장 버튼 텍스트 분기
                if status and status["has_close"]:
                    button_label = "💾 매출·네이버 방문자 수정(공식 반영)"
                elif status and (status["has_sales"] or status["has_visitors"]):
                    button_label = "💾 임시 저장"
                else:
                    button_label = "💾 저장"
                
                if st.button(button_label, type="primary", use_container_width=True):
                    if not store or store.strip() == "":
                        st.error("매장명을 입력해주세요.")
                    elif total_sales <= 0:
                        st.error("매출은 0보다 큰 값이어야 합니다.")
                    else:
                        # DB 연결 및 store_id 확인
                        from src.auth import get_supabase_client, get_current_store_id
                        from src.storage_supabase import _check_supabase_for_dev_mode
                        
                        # 1. Supabase 클라이언트 확인
                        supabase = _check_supabase_for_dev_mode()
                        if not supabase:
                            st.session_state["sales_entry_success_message"] = "❌ 데이터베이스 연결에 실패했습니다.<br><br>• Supabase 클라이언트를 초기화할 수 없습니다.<br>• 개발 모드가 활성화되어 있거나 연결 설정을 확인해주세요."
                            st.session_state["sales_entry_message_type"] = "error"
                            st.rerun()
                            return
                        
                        # 2. Store ID 확인
                        store_id = get_current_store_id()
                        if not store_id:
                            st.session_state["sales_entry_success_message"] = "❌ 매장 정보를 찾을 수 없습니다.<br><br>• 로그인 상태를 확인해주세요.<br>• 매장 정보가 올바르게 설정되어 있는지 확인해주세요."
                            st.session_state["sales_entry_message_type"] = "error"
                            st.rerun()
                            return
                        
                        # 3. save_sales_entry로 통합 저장
                        try:
                            visitors_value = visitors_input if visitors_input > 0 else None
                            result = save_sales_entry(
                                date=date,
                                store_name=store,
                                card_sales=card_sales,
                                cash_sales=cash_sales,
                                total_sales=total_sales,
                                visitors=visitors_value
                            )
                            
                            if result["success"]:
                                # 메시지 구성
                                if result["synced_to_close"]:
                                    message = f"""✅ {result["message"]}<br><br>📅 날짜: {date}<br>🏪 매장: {store}<br>💰 총매출: <strong>{total_sales:,}원</strong>"""
                                    if visitors_value is not None:
                                        message += f"<br>👥 네이버 방문자: <strong>{visitors_value:,}명</strong>"
                                else:
                                    message = f"""✅ {result["message"]}<br><br>📅 날짜: {date}<br>🏪 매장: {store}<br>💰 총매출: <strong>{total_sales:,}원</strong>"""
                                    if visitors_value is not None:
                                        message += f"<br>👥 네이버 방문자: <strong>{visitors_value:,}명</strong>"
                                
                                st.session_state["sales_entry_success_message"] = message
                                st.session_state["sales_entry_message_type"] = "success"
                                st.rerun()
                            else:
                                st.session_state["sales_entry_success_message"] = f"❌ 저장 실패: {result.get('message', '알 수 없는 오류')}"
                                st.session_state["sales_entry_message_type"] = "error"
                                st.rerun()
                        except Exception as e:
                            # 예외 발생 시 상세한 에러 메시지
                            error_msg = str(e)
                            logger.error(f"Sales entry save error: {error_msg}", exc_info=True)
                            
                            # 사용자 친화적인 에러 메시지 구성
                            if "No store_id found" in error_msg:
                                user_msg = "❌ 매장 정보를 찾을 수 없습니다.<br><br>• 로그인 상태를 확인해주세요.<br>• 매장 정보가 올바르게 설정되어 있는지 확인해주세요."
                            elif "Supabase not available" in error_msg or "Supabase" in error_msg:
                                user_msg = "❌ 데이터베이스 연결에 실패했습니다.<br><br>• Supabase 연결 설정을 확인해주세요.<br>• 네트워크 연결을 확인해주세요."
                            else:
                                user_msg = f"❌ 매출 저장 실패: {error_msg}<br><br>• 문제가 지속되면 관리자에게 문의해주세요."
                            
                            st.session_state["sales_entry_success_message"] = user_msg
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
                    if st.button("💾 매출 보정 일괄 저장", type="primary", use_container_width=True):
                        # DB 연결 및 store_id 사전 확인
                        from src.auth import get_supabase_client, get_current_store_id
                        from src.storage_supabase import _check_supabase_for_dev_mode
                        
                        supabase = _check_supabase_for_dev_mode()
                        if not supabase:
                            st.session_state["sales_entry_success_message"] = "❌ 데이터베이스 연결에 실패했습니다.<br><br>• Supabase 클라이언트를 초기화할 수 없습니다.<br>• 개발 모드가 활성화되어 있거나 연결 설정을 확인해주세요."
                            st.session_state["sales_entry_message_type"] = "error"
                            st.rerun()
                            return
                        
                        store_id = get_current_store_id()
                        if not store_id:
                            st.session_state["sales_entry_success_message"] = "❌ 매장 정보를 찾을 수 없습니다.<br><br>• 로그인 상태를 확인해주세요.<br>• 매장 정보가 올바르게 설정되어 있는지 확인해주세요."
                            st.session_state["sales_entry_message_type"] = "error"
                            st.rerun()
                            return
                        
                        errors = []
                        success_count = 0
                        
                        for date, store, card_sales, cash_sales, total_sales in sales_data:
                            if not store or store.strip() == "":
                                errors.append(f"{date}: 매장명이 없습니다.")
                            elif total_sales <= 0:
                                errors.append(f"{date}: 매출은 0보다 큰 값이어야 합니다.")
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
                                        
                                        # 캐시 무효화 (한 번만)
                                        if success_count == 0:
                                            from src.storage_supabase import soft_invalidate, load_monthly_sales_total
                                            soft_invalidate(reason="save_sales_batch", targets=["sales"])
                                            try:
                                                load_monthly_sales_total.clear()
                                            except Exception:
                                                pass
                                        
                                        success_count += 1
                                    else:
                                        errors.append(f"{date}: 저장 실패 (DB 연결 오류 가능)")
                                except Exception as e:
                                    error_msg = str(e)
                                    if "No store_id found" in error_msg:
                                        errors.append(f"{date}: 매장 정보 없음")
                                    elif "Supabase" in error_msg:
                                        errors.append(f"{date}: DB 연결 실패")
                                    else:
                                        errors.append(f"{date}: {error_msg}")
                        
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
                            message_parts.append(f"\n✅ **{success_count}일의 매출 보정이 저장되었습니다!**")
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
