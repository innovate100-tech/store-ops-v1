"""
일일 입력 통합 페이지
점장 마감 / 매출·네이버방문자 보정 / 판매량 보정을 하나로 통합
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
import logging
from datetime import date
from src.ui_helpers import render_page_header, handle_data_error
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
    """일일 입력 통합 페이지 렌더링"""
    render_page_header("일일 입력(통합)", "📝")
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    # ===== ZONE A: 날짜 & 상태 =====
    st.markdown("### 📅 날짜 선택")
    
    # 날짜 선택
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
    
    # 상태 배지 표시
    col_status1, col_status2, col_status3 = st.columns(3)
    with col_status1:
        if has_close:
            st.success("✅ 마감 완료(보정 가능)")
        elif has_sales or has_visitors:
            st.warning("⚠️ 임시 기록")
        else:
            st.info("📝 미입력")
    
    with col_status2:
        if best_total_sales:
            st.metric("총 매출", f"{best_total_sales:,.0f}원")
        else:
            st.metric("총 매출", "—")
    
    with col_status3:
        if visitors_best:
            st.metric("네이버방문자", f"{visitors_best}명")
        else:
            st.metric("네이버방문자", "—")
    
    # 현재 값 요약 (간단히 표시)
    if has_sales or has_visitors or has_close:
        st.caption(f"💡 현재 저장된 값: 총 매출 {best_total_sales:,.0f}원" if best_total_sales else "💡 현재 저장된 값 없음")
    
    st.markdown("---")
    
    # ===== ZONE B: 입력 영역 =====
    st.markdown("### ✏️ 입력")
    
    # 기존 매출 값 로드
    supabase = get_supabase_client()
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
    default_total = default_card + default_cash if (default_card > 0 or default_cash > 0) else (float(best_total_sales) if best_total_sales else 0.0)
    
    # A) 매출 입력
    st.markdown("#### 💰 매출")
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
    
    # B) 네이버방문자 입력
    st.markdown("#### 👥 네이버방문자")
    visitors = st.number_input(
        "방문자 수",
        min_value=0,
        value=int(visitors_best) if visitors_best else 0,
        step=1,
        key="daily_input_visitors"
    )
    
    # C) 판매량 입력
    st.markdown("#### 📦 판매량")
    
    # 메뉴 목록 로드
    menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
    menu_list = menu_df['메뉴명'].tolist() if not menu_df.empty else []
    
    if not menu_list:
        st.warning("먼저 메뉴를 등록해주세요.")
        sales_items = []
    else:
        # 기존 판매량 로드
        supabase = get_supabase_client()
        existing_items = {}
        if supabase and selected_date:
            try:
                date_str = selected_date.strftime('%Y-%m-%d')
                # 메뉴 ID 매핑
                menu_result = supabase.table("menu_master")\
                    .select("id,name")\
                    .eq("store_id", store_id)\
                    .execute()
                menu_id_map = {m['name']: m['id'] for m in menu_result.data if menu_result.data}
                
                # 기존 판매량 조회
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
    
    st.markdown("---")
    
    # ===== ZONE C: 메모 & 저장 =====
    st.markdown("### 💾 저장")
    
    # 운영 메모 (optional)
    memo = st.text_area(
        "운영 메모 (선택사항)",
        placeholder="특이사항, 메모 등을 입력하세요...",
        key="daily_input_memo"
    )
    
    # 저장 버튼
    col_save, col_close = st.columns([2, 1])
    
    with col_save:
        if st.button("💾 저장", type="primary", use_container_width=True, key="daily_input_save"):
            try:
                # 매출/방문자 저장
                result = save_sales_entry(
                    date=selected_date,
                    store_name="",  # store_id로 처리되므로 불필요
                    card_sales=card_sales,
                    cash_sales=cash_sales,
                    total_sales=total_sales,
                    visitors=visitors if visitors > 0 else None
                )
                
                if not result.get("success"):
                    st.error(f"매출 저장 실패: {result.get('message', '알 수 없는 오류')}")
                    return
                
                # 판매량 저장 (모든 메뉴, 0도 저장)
                for menu_name in menu_list:
                    qty = 0
                    # sales_items에서 찾기
                    for item_name, item_qty in sales_items:
                        if item_name == menu_name:
                            qty = item_qty
                            break
                    
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
                
                # 성공 메시지
                synced_to_close = result.get("synced_to_close", False)
                if synced_to_close:
                    st.success("✅ 공식 마감 매출이 함께 수정되었습니다.")
                else:
                    st.success("✅ 임시 기록이 저장되었습니다.")
                
                st.balloons()
                st.rerun()
                
            except Exception as e:
                logger.error(f"저장 실패: {e}", exc_info=True)
                st.error(f"저장 실패: {str(e)}")
    
    with col_close:
        if st.button("📋 이 날짜 마감하기", use_container_width=True, key="daily_input_close"):
            try:
                # issues는 기본값으로 설정
                issues = {
                    '품절': False,
                    '컴플레인': False,
                    '단체손님': False,
                    '직원이슈': False
                }
                
                # 모든 메뉴의 판매량 수집 (0도 포함)
                all_sales_items = []
                for menu_name in menu_list:
                    qty = 0
                    # sales_items에서 찾기
                    for item_name, item_qty in sales_items:
                        if item_name == menu_name:
                            qty = item_qty
                            break
                    all_sales_items.append((menu_name, qty))
                
                # 마감 저장
                success = save_daily_close(
                    date=selected_date,
                    store_name="",  # store_id로 처리되므로 불필요
                    card_sales=card_sales,
                    cash_sales=cash_sales,
                    total_sales=total_sales,
                    visitors=visitors if visitors > 0 else 0,
                    sales_items=all_sales_items,
                    issues=issues,
                    memo=memo if memo else ""
                )
                
                if success:
                    st.success("✅ 마감이 완료되었습니다.")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("마감 저장에 실패했습니다.")
                    
            except Exception as e:
                logger.error(f"마감 저장 실패: {e}", exc_info=True)
                st.error(f"마감 저장 실패: {str(e)}")
    
    # 안내 메시지
    if has_close:
        st.info("ℹ️ **이미 마감된 날짜입니다.** 이번 저장은 보정 기록으로 반영됩니다.")
    else:
        st.info("ℹ️ **임시 기록으로 저장됩니다.** 나중에 마감 시 자동 반영됩니다.")


if __name__ == "__main__":
    render_daily_input_hub()
