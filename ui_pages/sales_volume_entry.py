"""
판매량 등록 페이지
FormKit v2 + 블록 리듬 적용 (날짜 블록, ps_block_row 반응형, ActionBar 1개)
"""
from src.bootstrap import bootstrap
import streamlit as st
from src.ui_helpers import ui_flash_success, ui_flash_error, ui_flash_warning
from src.utils.time_utils import today_kst
from src.storage_supabase import load_csv, save_daily_sales_item, verify_overrides_saved
from src.auth import get_current_store_id, is_dev_mode, get_supabase_client
from src.ui.layouts.input_layouts import render_form_layout
from src.ui.components.form_kit import inject_form_kit_css
from src.ui.components.form_kit_v2 import (
    inject_form_kit_v2_css,
    ps_input_block,
    ps_secondary_date,
    ps_primary_quantity_input,
    ps_inline_feedback,
)

bootstrap(page_title="Sales Volume Entry")


def render_sales_volume_entry():
    """판매량 등록 (FormKit v2 + 블록 리듬, ActionBar 1개)"""
    inject_form_kit_css()
    inject_form_kit_v2_css("sales_volume_entry")
    
    def render_main_content():
        if st.session_state.get("sales_volume_entry_success"):
            msg = st.session_state.pop("sales_volume_entry_success", None)
            verify_msg = st.session_state.pop("sales_volume_entry_verify", None)
            st.success(msg)
            st.balloons()
            if verify_msg:
                st.info(verify_msg)
            if st.button("닫기", key="sales_volume_entry_close_msg"):
                st.rerun()
        
        menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
        menu_list = menu_df['메뉴명'].tolist() if not menu_df.empty else []
        
        if not menu_list:
            st.warning("먼저 메뉴를 등록해주세요.")
            return
        
        # Block 1: 날짜 선택
        def _body_date():
            ps_secondary_date("판매 날짜", key="sales_volume_entry_daily_sales_full_date", value=today_kst())
        ps_input_block(title="판매 날짜 선택", description="보정할 날짜를 선택하세요", level="secondary", body_fn=_body_date)
        
        sales_date = st.session_state.get("sales_volume_entry_daily_sales_full_date", today_kst())
        store_id = get_current_store_id()
        has_daily_close = False
        if store_id and sales_date:
            try:
                supabase = get_supabase_client()
                if supabase:
                    date_str = sales_date.strftime('%Y-%m-%d') if hasattr(sales_date, 'strftime') else str(sales_date)
                    r = supabase.table("daily_close").select("id", count="exact").eq("store_id", store_id).eq("date", date_str).limit(1).execute()
                    has_daily_close = r.count and r.count > 0
            except Exception:
                pass
        ps_inline_feedback(label="마감 상태", value="✅ 마감 완료" if has_daily_close else "⚠️ 미마감", status="ok" if has_daily_close else "warn")
        
        # Block 2: 판매량 입력 (3열 그리드, compact quantity)
        def _body_qty_grid():
            num_rows = (len(menu_list) + 2) // 3
            for row in range(num_rows):
                c1, c2, c3 = st.columns(3)
                for col_idx, col in enumerate([c1, c2, c3]):
                    menu_idx = row * 3 + col_idx
                    if menu_idx < len(menu_list):
                        menu_name = menu_list[menu_idx]
                        with col:
                            ps_primary_quantity_input(
                                menu_name,
                                key=f"sales_volume_entry_daily_sales_full_{menu_name}",
                                value=0,
                                min_value=0,
                                step=1,
                                unit="개",
                            )
        
        ps_input_block(title="판매량 입력", description="메뉴별 수량 (0=미판매)", level="primary", body_fn=_body_qty_grid)
        
        sales_items = []
        for menu_name in menu_list:
            q = st.session_state.get(f"sales_volume_entry_daily_sales_full_{menu_name}", 0) or 0
            if int(q) > 0:
                sales_items.append((menu_name, int(q)))
        
        def handle_save_sales_volume():
            if not sales_items:
                ui_flash_error("저장할 판매 내역이 없습니다. 한 개 이상의 메뉴에 판매 수량을 입력해주세요.")
                return
            sd = st.session_state.get("sales_volume_entry_daily_sales_full_date", today_kst())
            success_count = 0
            errors = []
            for menu_name, quantity in sales_items:
                try:
                    save_daily_sales_item(sd, menu_name, quantity)
                    success_count += 1
                except Exception as e:
                    errors.append(f"{menu_name}: {e}")
            if errors:
                for m in errors:
                    ui_flash_error(m)
            if success_count > 0:
                st.session_state["sales_volume_entry_success"] = "✅ 판매량 보정 저장 완료! (마감 입력보다 우선 적용)"
                if is_dev_mode():
                    sid = get_current_store_id()
                    if sid and verify_overrides_saved(sid, sd, success_count):
                        st.session_state["sales_volume_entry_verify"] = "🔧 override 저장 확인됨 (DEV)"
                st.rerun()
        
        st.session_state["_sales_volume_save"] = handle_save_sales_volume
    
    # 메뉴 목록 로드 (SummaryStrip용)
    menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
    menu_list = menu_df['메뉴명'].tolist() if not menu_df.empty else []
    
    # 날짜 선택 (SummaryStrip용)
    sales_date = today_kst()
    if "sales_volume_entry_daily_sales_full_date" in st.session_state:
        sales_date = st.session_state["sales_volume_entry_daily_sales_full_date"]
    
    # 마감 상태 확인 (SummaryStrip용)
    store_id = get_current_store_id()
    has_daily_close = False
    if store_id and sales_date:
        try:
            supabase = get_supabase_client()
            if supabase:
                date_str = sales_date.strftime('%Y-%m-%d') if hasattr(sales_date, 'strftime') else str(sales_date)
                daily_close_check = supabase.table("daily_close")\
                    .select("id", count="exact")\
                    .eq("store_id", store_id)\
                    .eq("date", date_str)\
                    .limit(1)\
                    .execute()
                has_daily_close = daily_close_check.count and daily_close_check.count > 0
        except Exception:
            pass
    
    # SummaryStrip 항목 구성 (기존 값 사용)
    summary_items = [
        {
            "label": "판매 날짜",
            "value": sales_date.strftime('%Y-%m-%d') if hasattr(sales_date, 'strftime') else str(sales_date),
            "badge": None
        },
        {
            "label": "마감 상태",
            "value": "마감 완료" if has_daily_close else "미마감",
            "badge": "success" if has_daily_close else "warning"
        },
        {
            "label": "등록 메뉴",
            "value": f"{len(menu_list)}개",
            "badge": None
        }
    ]
    
    # Action Bar 설정
    action_primary = None
    action_secondary = None
    
    # Primary 액션 설정
    if "_sales_volume_save" in st.session_state:
        action_primary = {
            "label": "💾 판매량 보정 저장",
            "key": "sales_volume_primary_save",
            "action": st.session_state["_sales_volume_save"]
        }
        del st.session_state["_sales_volume_save"]
    
    # FORM형 레이아웃 적용
    render_form_layout(
        title="판매량 입력",
        icon="📦",
        status_badge=None,
        guide_kind="G2",
        guide_conclusion=None,  # 기본값 사용
        guide_bullets=None,  # 기본값 사용
        guide_next_action=None,  # 기본값 사용
        summary_items=summary_items,
        mini_progress_items=None,  # Mini Progress Panel 사용 안 함
        action_primary=action_primary,
        action_secondary=action_secondary,
        main_content=render_main_content
    )


# Streamlit 멀티페이지에서 직접 실행될 때
# 주석 처리: app.py에서만 렌더되도록 함 (중복 호출 방지)
# render_sales_volume_entry()
