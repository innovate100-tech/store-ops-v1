"""
매출 등록 페이지 (보정 도구)
FormKit v2 + 블록 리듬 적용 (G2 GuideBox, ActionBar만 저장)
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
import logging
from src.ui_helpers import handle_data_error
from src.storage_supabase import save_sales, save_visitor, save_sales_entry, get_day_record_status
from src.ui import render_sales_batch_input, render_visitor_batch_input
from src.utils.crud_guard import run_write
from src.auth import get_current_store_id
from src.ui.layouts.input_layouts import render_form_layout
from src.ui.components.form_kit import inject_form_kit_css
from src.ui.components.form_kit_v2 import (
    inject_form_kit_v2_css,
    ps_input_block,
    ps_primary_money_input,
    ps_primary_quantity_input,
    ps_secondary_date,
    ps_inline_feedback,
)
from src.utils.time_utils import today_kst

logger = logging.getLogger(__name__)

# 공통 설정 적용
bootstrap(page_title="Sales Entry")

# 로그인 체크
from src.auth import check_login, show_login_page
if not check_login():
    show_login_page()
    st.stop()


def render_sales_entry():
    """매출 등록 페이지 (FormKit v2 + 블록 리듬, G2, ActionBar만 저장)"""
    inject_form_kit_css()
    inject_form_kit_v2_css("sales_entry")
    
    # 저장 액션 함수들 (action bar에서 호출)
    def handle_save_single_sales():
        """단일 매출 저장 처리"""
        # 폼 내부 위젯 값 읽기
        date = st.session_state.get("sales_date")
        store = st.session_state.get("sales_store", "")
        card_sales = st.session_state.get("sales_card", 0)
        cash_sales = st.session_state.get("sales_cash", 0)
        total_sales = card_sales + cash_sales
        visitors_input = st.session_state.get("sales_entry_visitors", 0)
        
        if not store or store.strip() == "":
            st.session_state["sales_entry_success_message"] = "❌ 매장명을 입력해주세요."
            st.session_state["sales_entry_message_type"] = "error"
            return
        
        if total_sales <= 0:
            st.session_state["sales_entry_success_message"] = "❌ 매출은 0보다 큰 값이어야 합니다."
            st.session_state["sales_entry_message_type"] = "error"
            return
        
        # DB 연결 및 store_id 확인
        from src.auth import get_supabase_client, get_current_store_id
        from src.storage_supabase import _check_supabase_for_dev_mode
        
        supabase = _check_supabase_for_dev_mode()
        if not supabase:
            st.session_state["sales_entry_success_message"] = "❌ 데이터베이스 연결에 실패했습니다.<br><br>• Supabase 클라이언트를 초기화할 수 없습니다.<br>• 개발 모드가 활성화되어 있거나 연결 설정을 확인해주세요."
            st.session_state["sales_entry_message_type"] = "error"
            return
        
        store_id = get_current_store_id()
        if not store_id:
            st.session_state["sales_entry_success_message"] = "❌ 매장 정보를 찾을 수 없습니다.<br><br>• 로그인 상태를 확인해주세요.<br>• 매장 정보가 올바르게 설정되어 있는지 확인해주세요."
            st.session_state["sales_entry_message_type"] = "error"
            return
        
        # save_sales_entry로 통합 저장
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
                message = f"""✅ {result["message"]}<br><br>📅 날짜: {date}<br>🏪 매장: {store}<br>💰 총매출: <strong>{total_sales:,}원</strong>"""
                if visitors_value is not None:
                    message += f"<br>👥 네이버 방문자: <strong>{visitors_value:,}명</strong>"
                st.session_state["sales_entry_success_message"] = message
                st.session_state["sales_entry_message_type"] = "success"
            else:
                st.session_state["sales_entry_success_message"] = f"❌ 저장 실패: {result.get('message', '알 수 없는 오류')}"
                st.session_state["sales_entry_message_type"] = "error"
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Sales entry save error: {error_msg}", exc_info=True)
            
            if "No store_id found" in error_msg:
                user_msg = "❌ 매장 정보를 찾을 수 없습니다.<br><br>• 로그인 상태를 확인해주세요.<br>• 매장 정보가 올바르게 설정되어 있는지 확인해주세요."
            elif "Supabase not available" in error_msg or "Supabase" in error_msg:
                user_msg = "❌ 데이터베이스 연결에 실패했습니다.<br><br>• Supabase 연결 설정을 확인해주세요.<br>• 네트워크 연결을 확인해주세요."
            else:
                user_msg = f"❌ 매출 저장 실패: {error_msg}<br><br>• 문제가 지속되면 관리자에게 문의해주세요."
            
            st.session_state["sales_entry_success_message"] = user_msg
            st.session_state["sales_entry_message_type"] = "error"
    
    def handle_save_batch_sales():
        """일괄 매출 저장 처리"""
        sales_data = render_sales_batch_input()
        
        if not sales_data:
            st.session_state["sales_entry_success_message"] = "💡 저장할 데이터가 없습니다."
            st.session_state["sales_entry_message_type"] = "error"
            return
        
        # DB 연결 및 store_id 확인
        from src.auth import get_supabase_client, get_current_store_id
        from src.storage_supabase import _check_supabase_for_dev_mode
        
        supabase = _check_supabase_for_dev_mode()
        if not supabase:
            st.session_state["sales_entry_success_message"] = "❌ 데이터베이스 연결에 실패했습니다.<br><br>• Supabase 클라이언트를 초기화할 수 없습니다.<br>• 개발 모드가 활성화되어 있거나 연결 설정을 확인해주세요."
            st.session_state["sales_entry_message_type"] = "error"
            return
        
        store_id = get_current_store_id()
        if not store_id:
            st.session_state["sales_entry_success_message"] = "❌ 매장 정보를 찾을 수 없습니다.<br><br>• 로그인 상태를 확인해주세요.<br>• 매장 정보가 올바르게 설정되어 있는지 확인해주세요."
            st.session_state["sales_entry_message_type"] = "error"
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
                    success, conflict_info = save_sales(date, store, card_sales, cash_sales, total_sales, check_conflict=True)
                    
                    if success:
                        if conflict_info:
                            existing = conflict_info.get('existing_total_sales', 0)
                            has_daily_close = conflict_info.get('has_daily_close', False)
                            if has_daily_close:
                                errors.append(f"{date}: ⚠️ 마감보고와 충돌 (기존: {existing:,.0f}원 → 새: {total_sales:,.0f}원, 덮어쓰기됨)")
                            else:
                                errors.append(f"{date}: ⚠️ 기존 값과 충돌 (기존: {existing:,.0f}원 → 새: {total_sales:,.0f}원, 덮어쓰기됨)")
                        
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
        
        warnings = [e for e in errors if "⚠️" in e]
        real_errors = [e for e in errors if "⚠️" not in e]
        
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
            st.rerun()
        elif real_errors:
            message = "\n".join(message_parts)
            st.session_state["sales_entry_success_message"] = message
            st.session_state["sales_entry_message_type"] = "error"
        elif not real_errors and not warnings:
            st.session_state["sales_entry_success_message"] = "💡 저장할 데이터가 없습니다."
            st.session_state["sales_entry_message_type"] = "error"
    
    def handle_save_single_visitor():
        """단일 방문자 저장 처리"""
        date = st.session_state.get("visitor_date")
        visitors = st.session_state.get("visitor_count", 0)
        
        if not date:
            st.session_state["sales_entry_success_message"] = "❌ 날짜를 선택해주세요."
            st.session_state["sales_entry_message_type"] = "error"
            return
        
        if visitors <= 0:
            st.session_state["sales_entry_success_message"] = "❌ 네이버 스마트플레이스 방문자수는 0보다 큰 값이어야 합니다."
            st.session_state["sales_entry_message_type"] = "error"
            return
        
        run_write(
            "save_visitor",
            lambda: save_visitor(date, visitors),
            targets=["visitors"],
            extra={"date": str(date), "visitors": visitors},
            success_message=f"✅ 네이버 스마트플레이스 방문자수가 저장되었습니다! ({date}, {visitors}명)"
        )
    
    def handle_save_batch_visitor():
        """일괄 방문자 저장 처리"""
        visitor_data = render_visitor_batch_input()
        
        if not visitor_data:
            st.session_state["sales_entry_success_message"] = "💡 저장할 데이터가 없습니다."
            st.session_state["sales_entry_message_type"] = "error"
            return
        
        errors = []
        success_count = 0
        
        for date, visitors in visitor_data:
            try:
                run_write(
                    "save_visitor_batch",
                    lambda d=date, v=visitors: save_visitor(d, v),
                    targets=["visitors"],
                    extra={"date": str(date)},
                    rerun=False
                )
                success_count += 1
            except Exception as e:
                errors.append(f"{date}: {e}")
        
        if errors:
            error_msg = "\n".join(errors)
            st.session_state["sales_entry_success_message"] = f"❌ 저장 중 오류가 발생했습니다:\n{error_msg}"
            st.session_state["sales_entry_message_type"] = "error"
        elif success_count > 0:
            st.session_state["sales_entry_success_message"] = f"✅ {success_count}일의 네이버 스마트플레이스 방문자수가 저장되었습니다!"
            st.session_state["sales_entry_message_type"] = "success"
            st.balloons()
    
    def render_main_content():
        """Main Card 내용: 매출/방문자 입력 UI"""
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
                    # Phase 0 STEP 3: 플래그 삭제만으로 조건부 렌더링이 자동 업데이트되므로 rerun 불필요
        
        # Block: 카테고리 선택
        def _body_category():
            return st.radio(
                "카테고리",
                ["💰 매출", "👥 네이버 스마트플레이스 방문자"],
                horizontal=True,
                key="sales_entry_sales_category"
            )
        ps_input_block(title="카테고리 선택", description="매출 또는 방문자 입력", level="secondary", body_fn=lambda: _body_category())
        category = st.session_state.get("sales_entry_sales_category", "💰 매출")
        
        if category == "💰 매출":
            def _body_mode():
                return st.radio("입력 모드", ["단일 입력", "일괄 입력 (여러 날짜)"], horizontal=True, key="sales_input_mode")
            ps_input_block(title="입력 모드", level="secondary", body_fn=_body_mode)
            input_mode = st.session_state.get("sales_input_mode", "단일 입력")
            
            if input_mode == "단일 입력":
                # Block 1: 날짜·매장
                def _body_date_store():
                    c1, c2 = st.columns(2)
                    with c1:
                        ps_secondary_date("날짜", key="sales_date", value=today_kst())
                    with c2:
                        store = st.text_input("매장", value="Plate&Share", key="sales_store")
                ps_input_block(title="날짜 · 매장", level="secondary", body_fn=_body_date_store)
                
                date = st.session_state.get("sales_date", today_kst())
                store_id = get_current_store_id()
                status = None
                if store_id and date:
                    try:
                        status = get_day_record_status(store_id, date)
                    except Exception:
                        pass
                status_line = "✅ 마감 완료(공식)" if status and status.get("has_close") else "⚠️ 임시(미마감)" if status and (status.get("has_sales") or status.get("has_visitors")) else "📝 기록 없음"
                ps_inline_feedback(label="상태", value=status_line, status="ok" if status and status.get("has_close") else ("warn" if status and (status.get("has_sales") or status.get("has_visitors")) else "warn"))
                
                # Block 2: 카드·현금 (Primary 1개: 총매출 대표)
                def _body_money():
                    c1, c2 = st.columns(2)
                    with c1:
                        ps_primary_money_input("카드매출 (원)", key="sales_card", value=0, min_value=0, step=1000, unit="원", compact=True)
                    with c2:
                        ps_primary_money_input("현금매출 (원)", key="sales_cash", value=0, min_value=0, step=1000, unit="원", compact=True)
                    card = st.session_state.get("sales_card", 0) or 0
                    cash = st.session_state.get("sales_cash", 0) or 0
                    total = card + cash
                    ps_inline_feedback(label="총매출", value=f"{total:,.0f}원", status="ok" if total > 0 else "warn")
                ps_input_block(title="매출 입력", description="카드/현금 입력", level="primary", body_fn=_body_money)
                
                # Block 3: 방문자 (선택)
                def _body_visitors():
                    v0 = 0
                    if status and status.get("visitors_best") is not None:
                        v0 = int(status["visitors_best"])
                    ps_primary_quantity_input("네이버 방문자 (선택)", key="sales_entry_visitors", value=v0, min_value=0, step=1, unit="명")
                ps_input_block(title="네이버 방문자", description="선택 입력", level="secondary", body_fn=_body_visitors)
                
                if status and status.get("has_close"):
                    primary_label = "💾 매출·네이버 방문자 수정(공식 반영)"
                elif status and (status.get("has_sales") or status.get("has_visitors")):
                    primary_label = "💾 임시 저장"
                else:
                    primary_label = "💾 저장"
                st.session_state["_sales_entry_single_save"] = handle_save_single_sales
                st.session_state["_sales_entry_primary_label"] = primary_label
            
            else:
                _batch_out = []
                def _body_batch():
                    _batch_out.clear()
                    data = render_sales_batch_input()
                    _batch_out.append(data)
                ps_input_block(title="매출 일괄 입력", description="시작일~종료일, 매장 입력 후 날짜별 카드/현금 입력", level="secondary", body_fn=_body_batch)
                sales_data = _batch_out[0] if _batch_out else []
                
                if sales_data:
                    summary_df = pd.DataFrame(
                        [(d.strftime('%Y-%m-%d'), s, f"{card:,}원", f"{cash:,}원", f"{total:,}원")
                         for d, s, card, cash, total in sales_data],
                        columns=['날짜', '매장', '카드매출', '현금매출', '총매출']
                    )
                    st.dataframe(summary_df, use_container_width=True, hide_index=True)
                    total_all = sum(t for _, _, _, _, t in sales_data)
                    ps_inline_feedback(label="합계", value=f"{len(sales_data)}일 · {total_all:,.0f}원", status="ok")
                    st.session_state["_sales_entry_batch_save"] = handle_save_batch_sales
                    st.session_state["_sales_entry_primary_label"] = "💾 매출 보정 일괄 저장"
        
        else:
            def _body_vmode():
                return st.radio("입력 모드", ["단일 입력", "일괄 입력 (여러 날짜)"], horizontal=True, key="sales_entry_visitor_input_mode")
            ps_input_block(title="입력 모드", level="secondary", body_fn=_body_vmode)
            input_mode = st.session_state.get("sales_entry_visitor_input_mode", "단일 입력")
            
            if input_mode == "단일 입력":
                def _body_visitor_single():
                    ps_secondary_date("날짜", key="visitor_date", value=today_kst())
                    ps_primary_quantity_input("네이버 방문자 수", key="visitor_count", value=0, min_value=0, step=1, unit="명")
                ps_input_block(title="방문자 입력", description="날짜별 방문자 수", level="secondary", body_fn=_body_visitor_single)
                st.session_state["_sales_entry_single_visitor_save"] = handle_save_single_visitor
                st.session_state["_sales_entry_primary_label"] = "💾 저장"
            
            else:
                _v_batch_out = []
                def _body_v_batch():
                    _v_batch_out.clear()
                    data = render_visitor_batch_input()
                    _v_batch_out.append(data)
                ps_input_block(title="방문자 일괄 입력", description="시작일~종료일, 날짜별 방문자 입력", level="secondary", body_fn=_body_v_batch)
                visitor_data = _v_batch_out[0] if _v_batch_out else []
                if visitor_data:
                    summary_df = pd.DataFrame(
                        [(d.strftime('%Y-%m-%d'), f"{v}명") for d, v in visitor_data],
                        columns=['날짜', '네이버 스마트플레이스 방문자수']
                    )
                    st.dataframe(summary_df, use_container_width=True, hide_index=True)
                    total_v = sum(v for _, v in visitor_data)
                    ps_inline_feedback(label="합계", value=f"{len(visitor_data)}일 · {total_v:,}명", status="ok")
                    st.session_state["_sales_entry_batch_visitor_save"] = handle_save_batch_visitor
                    st.session_state["_sales_entry_primary_label"] = "💾 일괄 저장"
    
    # Action Bar 설정 (카테고리/모드에 따라 동적 변경)
    action_primary = None
    action_secondary = None
    
    # 저장 함수가 설정되어 있으면 action bar에 연결
    if "_sales_entry_single_save" in st.session_state:
        action_primary = {
            "label": st.session_state.get("_sales_entry_primary_label", "💾 저장"),
            "key": "sales_entry_primary_save",
            "action": st.session_state["_sales_entry_single_save"]
        }
        # 세션 상태 정리
        del st.session_state["_sales_entry_single_save"]
        if "_sales_entry_primary_label" in st.session_state:
            del st.session_state["_sales_entry_primary_label"]
    elif "_sales_entry_batch_save" in st.session_state:
        action_primary = {
            "label": st.session_state.get("_sales_entry_primary_label", "💾 매출 보정 일괄 저장"),
            "key": "sales_entry_batch_save",
            "action": st.session_state["_sales_entry_batch_save"]
        }
        del st.session_state["_sales_entry_batch_save"]
        if "_sales_entry_primary_label" in st.session_state:
            del st.session_state["_sales_entry_primary_label"]
    elif "_sales_entry_single_visitor_save" in st.session_state:
        action_primary = {
            "label": st.session_state.get("_sales_entry_primary_label", "💾 저장"),
            "key": "sales_entry_visitor_save",
            "action": st.session_state["_sales_entry_single_visitor_save"]
        }
        del st.session_state["_sales_entry_single_visitor_save"]
        if "_sales_entry_primary_label" in st.session_state:
            del st.session_state["_sales_entry_primary_label"]
    elif "_sales_entry_batch_visitor_save" in st.session_state:
        action_primary = {
            "label": st.session_state.get("_sales_entry_primary_label", "💾 일괄 저장"),
            "key": "sales_entry_batch_visitor_save",
            "action": st.session_state["_sales_entry_batch_visitor_save"]
        }
        del st.session_state["_sales_entry_batch_visitor_save"]
        if "_sales_entry_primary_label" in st.session_state:
            del st.session_state["_sales_entry_primary_label"]
    
    # FORM형 레이아웃 적용
    render_form_layout(
        title="매출/방문자 입력",
        icon="💰",
        status_badge=None,
        guide_kind="G2",
        guide_conclusion=None,  # 기본값 사용
        guide_bullets=None,  # 기본값 사용
        guide_next_action=None,  # 기본값 사용
        summary_items=None,  # Summary Strip 사용 안 함 (여러 날짜 입력 가능)
        mini_progress_items=None,  # Mini Progress Panel 사용 안 함
        action_primary=action_primary,
        action_secondary=action_secondary,
        main_content=render_main_content
    )


# Streamlit 멀티페이지에서 직접 실행될 때
# 주석 처리: app.py에서만 렌더되도록 함 (중복 호출 방지)
# render_sales_entry()
