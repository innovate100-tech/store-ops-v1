"""
일일 마감 페이지
매출, 네이버 방문자, 판매량, 메모를 입력하고 마감하는 통합 페이지
FORM형 레이아웃 적용
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
import logging
from datetime import date
from src.ui_helpers import handle_data_error
from src.ui.layouts.input_layouts import render_form_layout
from src.storage_supabase import (
    load_csv, 
    get_day_record_status, 
    save_sales_entry, 
    save_daily_sales_item,
    save_daily_close,
    load_best_available_daily_sales
)
from src.auth import get_current_store_id, get_supabase_client
from src.utils.time_utils import today_kst

logger = logging.getLogger(__name__)

# 공통 설정 적용
bootstrap(page_title="Daily Input Hub")

# 로그인 체크
from src.auth import check_login, show_login_page
if not check_login():
    show_login_page()
    st.stop()


def render_daily_input_hub():
    """일일 마감 페이지 렌더링 (FORM형 레이아웃 적용)"""
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    # 날짜 선택 (레이아웃 외부에서 처리 - Summary Strip에 포함)
    selected_date = st.date_input(
        "입력할 날짜",
        value=today_kst(),
        key="daily_input_hub_date"
    )
    
    # 날짜 상태 확인
    status = get_day_record_status(store_id, selected_date)
    has_close = status.get("has_close", False)
    has_sales = status.get("has_sales", False)
    has_visitors = status.get("has_visitors", False)
    best_total_sales = status.get("best_total_sales")
    visitors_best = status.get("visitors_best")
    
    # 판매량 확인
    supabase = get_supabase_client()
    has_sales_items = False
    sales_items_count = 0
    if supabase and selected_date:
        try:
            date_str = selected_date.strftime('%Y-%m-%d')
            menu_result = supabase.table("menu_master").select("id").eq("store_id", store_id).execute()
            menu_ids = [m['id'] for m in menu_result.data] if menu_result.data else []
            if menu_ids:
                items_result = supabase.table("daily_sales_items")\
                    .select("menu_id", count="exact")\
                    .eq("store_id", store_id)\
                    .eq("date", date_str)\
                    .in_("menu_id", menu_ids)\
                    .execute()
                sales_items_count = items_result.count if items_result.count else 0
                has_sales_items = sales_items_count > 0
        except:
            pass
    
    # 메모 확인
    has_memo = False
    
    # 진행률 계산
    total_items = 4
    completed_items = sum([
        1 if has_sales else 0,
        1 if has_visitors else 0,
        1 if has_sales_items else 0,
        1 if has_memo else 0
    ])
    progress_rate = (completed_items / total_items * 100) if total_items > 0 else 0
    
    # 상태 배지
    if has_close:
        status_badge = {"text": "✅ 마감 완료", "type": "success"}
    elif has_sales or has_visitors:
        status_badge = {"text": "⚠️ 임시 기록", "type": "warning"}
    else:
        status_badge = {"text": "📝 미입력", "type": "neutral"}
    
    # Summary Strip 항목
    summary_items = [
        {
            "label": "날짜",
            "value": f"{selected_date.strftime('%Y-%m-%d')} ({['월', '화', '수', '목', '금', '토', '일'][selected_date.weekday()]})",
            "badge": None
        },
        {
            "label": "진행률",
            "value": f"{completed_items}/{total_items}",
            "badge": "success" if has_close else "warning" if progress_rate > 0 else None
        },
        {
            "label": "매출",
            "value": f"{best_total_sales:,.0f}원" if best_total_sales else "—",
            "badge": "success" if has_sales else None
        },
        {
            "label": "방문자",
            "value": f"{visitors_best}명" if visitors_best else "—",
            "badge": "success" if has_visitors else None
        },
        {
            "label": "판매량",
            "value": f"{sales_items_count}개" if has_sales_items else "—",
            "badge": "success" if has_sales_items else "warning" if (has_sales or has_visitors) else None
        }
    ]
    
    # 기존 매출 값 로드
    existing_card_sales = 0.0
    existing_cash_sales = 0.0
    if supabase and selected_date:
        try:
            date_str = selected_date.strftime('%Y-%m-%d')
            sales_result = supabase.table("sales")\
                .select("card_sales,cash_sales")\
                .eq("store_id", store_id)\
                .eq("date", date_str)\
                .limit(1)\
                .execute()
            if sales_result.data:
                existing_card_sales = float(sales_result.data[0].get('card_sales', 0) or 0)
                existing_cash_sales = float(sales_result.data[0].get('cash_sales', 0) or 0)
        except Exception as e:
            logger.warning(f"기존 매출 로드 실패: {e}")
    
    # 기본값: 기존 값 또는 best_total_sales 기반
    default_card = existing_card_sales if existing_card_sales > 0 else (float(best_total_sales * 0.7) if best_total_sales else 0.0)
    default_cash = existing_cash_sales if existing_cash_sales > 0 else (float(best_total_sales * 0.3) if best_total_sales else 0.0)
    
    # 메뉴 목록 로드
    menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
    menu_list = menu_df['메뉴명'].tolist() if not menu_df.empty else []
    
    # 기존 판매량 로드
    existing_items = {}
    if supabase and selected_date:
        try:
            date_str = selected_date.strftime('%Y-%m-%d')
            menu_result = supabase.table("menu_master")\
                .select("id,name")\
                .eq("store_id", store_id)\
                .execute()
            menu_id_map = {m['name']: m['id'] for m in menu_result.data if menu_result.data}
            
            if menu_id_map:
                menu_ids = list(menu_id_map.values())
                items_result = supabase.table("daily_sales_items")\
                    .select("menu_id,qty")\
                    .eq("store_id", store_id)\
                    .eq("date", date_str)\
                    .in_("menu_id", menu_ids)\
                    .execute()
                
                id_to_name = {v: k for k, v in menu_id_map.items()}
                for item in items_result.data if items_result.data else []:
                    menu_id = item['menu_id']
                    menu_name = id_to_name.get(menu_id)
                    if menu_name:
                        existing_items[menu_name] = item.get('qty', 0)
        except Exception as e:
            logger.warning(f"기존 판매량 로드 실패: {e}")
    
    # Main Content 함수 정의 (탭 기반 입력)
    def render_main_content():
        """Main Card 내용: 탭 기반 단계별 입력"""
        # Phase 1 STEP 2 최종: 저장/분석 정책 안내
        st.info("""
        💡 **네이버 방문자·메모·판매량만 입력해도 기록은 저장됩니다.**  
        하지만 분석과 코칭은 **'매출'**이 있어야 시작됩니다.
        """)
        
        # 탭 생성
        tab1, tab2, tab3, tab4 = st.tabs(["💰 매출", "👥 네이버 방문자", "📦 판매량", "📝 메모"])
        
        # 탭 1: 매출 입력
        with tab1:
            st.markdown("#### 💰 매출 입력")
            col_card, col_cash, col_total = st.columns(3)
            with col_card:
                card_sales = st.number_input(
                    "카드 매출",
                    min_value=0.0,
                    value=default_card,
                    step=1000.0,
                    key="daily_input_card_sales"
                )
            with col_cash:
                cash_sales = st.number_input(
                    "현금 매출",
                    min_value=0.0,
                    value=default_cash,
                    step=1000.0,
                    key="daily_input_cash_sales"
                )
            with col_total:
                # 총 매출은 자동 계산 (카드 + 현금)
                total_sales = card_sales + cash_sales
                st.metric("총 매출 (자동 계산)", f"{total_sales:,.0f}원")
            
            st.caption("💡 팁: 카드/현금 중 하나만 입력해도 됩니다.")
            
            # 임시 저장 버튼
            col_save1, col_next1 = st.columns([1, 1])
            with col_save1:
                if st.button("💾 임시 저장", key="temp_save_sales", use_container_width=True):
                    try:
                        from src.ui_helpers import has_any_input, ui_flash_warning, ui_flash_success
                        has_sales = card_sales > 0 or cash_sales > 0
                        if has_sales:
                            result = save_sales_entry(
                                date=selected_date,
                                store_name="",
                                card_sales=card_sales,
                                cash_sales=cash_sales,
                                total_sales=total_sales,
                                visitors=None
                            )
                            if result.get("success"):
                                ui_flash_success("매출이 임시 저장되었습니다.")
                                st.rerun()
                            else:
                                st.error(f"저장 실패: {result.get('message', '알 수 없는 오류')}")
                        else:
                            ui_flash_warning("매출을 입력해주세요.")
                    except Exception as e:
                        logger.error(f"임시 저장 실패: {e}")
                        st.error(f"저장 실패: {str(e)}")
        
        # 탭 2: 네이버 방문자 입력
        with tab2:
            st.markdown("#### 👥 네이버 방문자 입력")
            visitors = st.number_input(
                "네이버 스마트플레이스 방문자 수",
                min_value=0,
                value=int(visitors_best) if visitors_best else 0,
                step=1,
                key="daily_input_visitors"
            )
            
            st.caption("💡 네이버 스마트플레이스에서 확인한 방문자 수를 입력하세요.")
            
            # 임시 저장 버튼
            col_save2, col_next2 = st.columns([1, 1])
            with col_save2:
                if st.button("💾 임시 저장", key="temp_save_visitors", use_container_width=True):
                    try:
                        from src.ui_helpers import ui_flash_success
                        if visitors > 0:
                            result = save_sales_entry(
                                date=selected_date,
                                store_name="",
                                card_sales=0,
                                cash_sales=0,
                                total_sales=0,
                                visitors=visitors
                            )
                            if result.get("success"):
                                ui_flash_success("네이버 방문자 수가 임시 저장되었습니다.")
                                st.rerun()
                            else:
                                st.error(f"저장 실패: {result.get('message', '알 수 없는 오류')}")
                        else:
                            st.warning("방문자 수를 입력해주세요.")
                    except Exception as e:
                        logger.error(f"임시 저장 실패: {e}")
                        st.error(f"저장 실패: {str(e)}")
        
        # 탭 3: 판매량 입력
        with tab3:
            st.markdown("#### 📦 판매량 입력")
            
            if not menu_list:
                st.warning("먼저 메뉴를 등록해주세요.")
                sales_items = []
            else:
                # 메뉴별 판매량 입력 (3열 그리드)
                sales_items = []
                num_rows = (len(menu_list) + 2) // 3
                for row in range(num_rows):
                    cols = st.columns(3)
                    for col_idx in range(3):
                        menu_idx = row * 3 + col_idx
                        if menu_idx < len(menu_list):
                            menu_name = menu_list[menu_idx]
                            with cols[col_idx]:
                                qty = st.number_input(
                                    menu_name,
                                    min_value=0,
                                    value=existing_items.get(menu_name, 0),
                                    step=1,
                                    key=f"daily_input_sales_item_{menu_name}_{selected_date}"
                                )
                                if qty > 0:
                                    sales_items.append((menu_name, qty))
            
            # 임시 저장 버튼
            col_save3, col_next3 = st.columns([1, 1])
            with col_save3:
                if st.button("💾 임시 저장", key="temp_save_sales_items", use_container_width=True):
                    try:
                        from src.ui_helpers import ui_flash_success
                        has_sales_items = False
                        if sales_items:
                            for menu_name, qty in sales_items:
                                if qty > 0:
                                    has_sales_items = True
                                    try:
                                        save_daily_sales_item(
                                            date=selected_date,
                                            menu_name=menu_name,
                                            quantity=qty,
                                            reason="일일 마감 페이지"
                                        )
                                    except Exception as e:
                                        logger.error(f"판매량 저장 실패 ({menu_name}): {e}")
                                        st.warning(f"판매량 저장 실패: {menu_name}")
                        
                        if has_sales_items:
                            ui_flash_success("판매량이 임시 저장되었습니다.")
                            st.rerun()
                        else:
                            st.warning("판매량을 입력해주세요.")
                    except Exception as e:
                        logger.error(f"임시 저장 실패: {e}")
                        st.error(f"저장 실패: {str(e)}")
        
        # 탭 4: 메모 입력
        with tab4:
            st.markdown("#### 📝 운영 메모")
            memo = st.text_area(
                "운영 메모 (선택사항)",
                placeholder="특이사항, 메모 등을 입력하세요...",
                key="daily_input_memo",
                height=150
            )
            
            st.caption("💡 특이사항이나 메모를 기록하세요. 마감 시 함께 저장됩니다.")
    
    # 액션 함수 정의 (session_state에서 값 읽기)
    def handle_temp_save():
        """임시 저장 액션"""
        try:
            from src.ui_helpers import has_any_input, ui_flash_warning, ui_flash_success
            
            # session_state에서 값 읽기
            card_sales = st.session_state.get("daily_input_card_sales", 0.0)
            cash_sales = st.session_state.get("daily_input_cash_sales", 0.0)
            total_sales = card_sales + cash_sales
            visitors = st.session_state.get("daily_input_visitors", 0)
            memo = st.session_state.get("daily_input_memo", "")
            
            # 판매량 수집
            sales_items = []
            for menu_name in menu_list:
                qty_key = f"daily_input_sales_item_{menu_name}_{selected_date}"
                qty = st.session_state.get(qty_key, 0)
                if qty > 0:
                    sales_items.append((menu_name, qty))
            
            # 입력 유효성 판정
            if not has_any_input(
                card_sales=card_sales,
                cash_sales=cash_sales,
                total_sales=total_sales,
                visitors=visitors,
                sales_items=sales_items,
                memo=memo
            ):
                ui_flash_warning("아무것도 입력되지 않았습니다. 하나만 입력해도 저장됩니다.")
                return
            
            # 매출/방문자 저장 (값이 있는 것만)
            has_sales = card_sales > 0 or cash_sales > 0 or total_sales > 0
            has_visitors = visitors > 0
            
            if has_sales or has_visitors:
                result = save_sales_entry(
                    date=selected_date,
                    store_name="",
                    card_sales=card_sales,
                    cash_sales=cash_sales,
                    total_sales=total_sales,
                    visitors=visitors if has_visitors else None
                )
                
                if not result.get("success"):
                    st.error(f"매출 저장 실패: {result.get('message', '알 수 없는 오류')}")
                    return
            
            # 판매량 저장 (값이 있는 것만)
            has_sales_items = False
            if sales_items:
                for menu_name, qty in sales_items:
                    if qty > 0:
                        has_sales_items = True
                        try:
                            save_daily_sales_item(
                                date=selected_date,
                                menu_name=menu_name,
                                quantity=qty,
                                reason="일일 입력 통합 페이지"
                            )
                        except Exception as e:
                            logger.error(f"판매량 저장 실패 ({menu_name}): {e}")
                            st.warning(f"판매량 저장 실패: {menu_name}")
            
            # Phase 1 STEP 2 최종: 저장 후 메시지 분기 (매출 있음/없음)
            from src.ui_helpers import has_sales_input
            
            has_sales = has_sales_input(card_sales, cash_sales, total_sales)
            
            if has_sales:
                saved_items = []
                if has_sales:
                    saved_items.append("매출")
                if has_visitors:
                    saved_items.append("네이버 방문자")
                if has_sales_items:
                    saved_items.append("판매량")
                if memo and memo.strip():
                    saved_items.append("메모")
                
                if len(saved_items) > 1:
                    ui_flash_success(f"저장 완료! 매출이 입력되어 분석이 시작됩니다. ({', '.join(saved_items)})")
                else:
                    ui_flash_success("저장 완료! 매출이 입력되어 분석이 시작됩니다.")
            else:
                saved_items = []
                if has_visitors:
                    saved_items.append("네이버 방문자")
                if has_sales_items:
                    saved_items.append("판매량")
                if memo and memo.strip():
                    saved_items.append("메모")
                
                if saved_items:
                    ui_flash_warning(f"기록은 저장되었습니다 ({', '.join(saved_items)}). 분석을 시작하려면 오늘 매출을 입력해 주세요.")
                else:
                    ui_flash_warning("기록은 저장되었습니다. 분석을 시작하려면 오늘 매출을 입력해 주세요.")
            
            st.balloons()
            st.rerun()
            
        except Exception as e:
            logger.error(f"저장 실패: {e}", exc_info=True)
            st.error(f"저장 실패: {str(e)}")
    
    def handle_close():
        """마감하기 액션"""
        try:
            from src.ui_helpers import has_any_input, ui_flash_warning, ui_flash_success
            
            # issues는 기본값으로 설정
            issues = {
                '품절': False,
                '컴플레인': False,
                '단체손님': False,
                '직원이슈': False
            }
            
            # session_state에서 값 읽기
            card_sales = st.session_state.get("daily_input_card_sales", 0.0)
            cash_sales = st.session_state.get("daily_input_cash_sales", 0.0)
            total_sales = card_sales + cash_sales
            visitors = st.session_state.get("daily_input_visitors", 0)
            memo = st.session_state.get("daily_input_memo", "")
            
            # 모든 메뉴의 판매량 수집 (0도 포함)
            all_sales_items = []
            for menu_name in menu_list:
                qty_key = f"daily_input_sales_item_{menu_name}_{selected_date}"
                qty = st.session_state.get(qty_key, 0)
                all_sales_items.append((menu_name, qty))
            
            # 입력 유효성 판정
            if not has_any_input(
                card_sales=card_sales,
                cash_sales=cash_sales,
                total_sales=total_sales,
                visitors=visitors,
                sales_items=all_sales_items,
                memo=memo,
                issues=issues
            ):
                ui_flash_warning("아무것도 입력되지 않았습니다. 하나만 입력해도 저장됩니다.")
                return
            
            # 마감 저장
            success = save_daily_close(
                date=selected_date,
                store_name="",
                card_sales=card_sales,
                cash_sales=cash_sales,
                total_sales=total_sales,
                visitors=visitors if visitors > 0 else 0,
                sales_items=all_sales_items,
                issues=issues,
                memo=memo if memo else ""
            )
            
            if success:
                from src.ui_helpers import has_sales_input
                has_sales = has_sales_input(card_sales, cash_sales, total_sales)
                
                if has_sales:
                    saved_items = []
                    if has_sales:
                        saved_items.append("매출")
                    if visitors > 0:
                        saved_items.append("방문자")
                    if any(qty > 0 for _, qty in all_sales_items):
                        saved_items.append("판매량")
                    if memo and memo.strip():
                        saved_items.append("메모")
                    if any(issues.values()):
                        saved_items.append("이슈")
                    
                    if len(saved_items) > 1:
                        ui_flash_success(f"저장 완료! 매출이 입력되어 분석이 시작됩니다. ({', '.join(saved_items)})")
                    else:
                        ui_flash_success("저장 완료! 매출이 입력되어 분석이 시작됩니다.")
                else:
                    saved_items = []
                    if visitors > 0:
                        saved_items.append("방문자")
                    if any(qty > 0 for _, qty in all_sales_items):
                        saved_items.append("판매량")
                    if memo and memo.strip():
                        saved_items.append("메모")
                    if any(issues.values()):
                        saved_items.append("이슈")
                    
                    if saved_items:
                        ui_flash_warning(f"기록은 저장되었습니다 ({', '.join(saved_items)}). 분석을 시작하려면 오늘 매출을 입력해 주세요.")
                    else:
                        ui_flash_warning("기록은 저장되었습니다. 분석을 시작하려면 오늘 매출을 입력해 주세요.")
                
                st.balloons()
                st.rerun()
            else:
                st.error("마감 저장에 실패했습니다.")
                
        except Exception as e:
            logger.error(f"마감 저장 실패: {e}", exc_info=True)
            st.error(f"마감 저장 실패: {str(e)}")
    
    # FORM형 레이아웃 적용
    render_form_layout(
        title="오늘 마감 입력",
        icon="📝",
        status_badge=status_badge,
        guide_kind="G1",
        guide_bullets=None,  # 기본값 사용
        guide_warnings=None,
        summary_items=summary_items,
        action_primary={
            "label": "📋 마감하기",
            "key": "daily_input_close",
            "action": handle_close
        },
        action_secondary=[
            {
                "label": "💾 임시 저장",
                "key": "daily_input_save",
                "action": handle_temp_save
            }
        ],
        main_content=render_main_content
    )
    
    # 안내 메시지 (레이아웃 외부)
    if has_close:
        st.info("ℹ️ **이미 마감된 날짜입니다.** 이번 저장은 보정 기록으로 반영됩니다.")
    else:
        st.info("ℹ️ **임시 기록으로 저장됩니다.** 나중에 마감 시 자동 반영됩니다.")


if __name__ == "__main__":
    render_daily_input_hub()
