"""
판매량 등록 페이지
"""
from src.bootstrap import bootstrap
import streamlit as st
from src.ui_helpers import render_page_header, render_section_divider
from src.utils.time_utils import today_kst
from src.storage_supabase import load_csv, save_daily_sales_item, verify_overrides_saved
from src.auth import get_current_store_id, is_dev_mode

# 공통 설정 적용
bootstrap(page_title="Sales Volume Entry")


def render_sales_volume_entry():
    """판매량 등록 페이지 렌더링"""
    render_page_header("판매량 입력", "📦")
    
    # STEP 2: 보정 도구 안내
    st.markdown("""
    <div style="padding: 1.2rem; background: #fff3cd; border-left: 4px solid #ffc107; 
                border-radius: 8px; margin-bottom: 1.5rem;">
        <div style="font-weight: 600; color: #856404; margin-bottom: 0.5rem;">🛠 보정 도구</div>
        <div style="color: #856404; font-size: 0.95rem; line-height: 1.6;">
            이 화면은 점장마감 이후 판매량 수정, 과거 데이터 입력용입니다.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 저장 직후 알림 (rerun 후에도 유지)
    if st.session_state.get("sales_volume_entry_success"):
        msg = st.session_state.pop("sales_volume_entry_success", None)
        verify_msg = st.session_state.pop("sales_volume_entry_verify", None)
        st.success(msg)
        st.balloons()
        if verify_msg:
            st.info(verify_msg)
        if st.button("닫기", key="sales_volume_entry_close_msg"):
            st.rerun()
        render_section_divider()
    
    # 메뉴 목록 로드
    menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
    menu_list = menu_df['메뉴명'].tolist() if not menu_df.empty else []
    
    # ========== 일일 판매 입력 (점장 마감 스타일 - 지정 날짜에 전 메뉴 수량 입력) ==========
    st.subheader("📦 일일 판매 입력 (전 메뉴 일괄 입력)")
    
    if not menu_list:
        st.warning("먼저 메뉴를 등록해주세요.")
    else:
        col_date, _ = st.columns([1, 3])
        with col_date:
            sales_date = st.date_input(
                "판매 날짜 선택",
                value=today_kst(),
                key="sales_volume_entry_daily_sales_full_date",
            )
        
        # STEP 2: 선택한 날짜에 마감 존재 여부 확인 및 안내
        from src.auth import get_current_store_id, get_supabase_client
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
        
        if has_daily_close:
            st.success("✅ **이 날짜는 이미 마감되었습니다.** 여기에 입력한 값이 최종 판매량으로 적용됩니다.")
        else:
            st.warning("⚠️ **이 날짜는 아직 마감되지 않았습니다.** 이후 점장마감을 하면 기본 판매량이 다시 생성됩니다.")
        
        st.markdown("---")
        st.write("**선택한 날짜의 각 메뉴별 판매 수량을 한 번에 입력하세요. (0은 미판매)**")
        
        sales_items = []
        # 메뉴를 3열 그리드로 표시 (점장 마감 페이지와 동일한 스타일)
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
                            value=0,
                            step=1,
                            key=f"sales_volume_entry_daily_sales_full_{menu_name}",
                        )
                        if qty > 0:
                            sales_items.append((menu_name, qty))
        
        render_section_divider()
        
        # STEP 2: 저장 버튼 근처 고정 문구
        st.info("💡 **이 입력은 점장마감 판매량보다 우선 적용됩니다.**")
        
        save_col, _ = st.columns([1, 3])
        with save_col:
            if st.button("💾 판매량 보정 저장", type="primary", use_container_width=True, key="sales_volume_entry_daily_sales_full_save"):
                if not sales_items:
                    st.error("저장할 판매 내역이 없습니다. 한 개 이상의 메뉴에 판매 수량을 입력해주세요.")
                else:
                    success_count = 0
                    errors = []
                    for menu_name, quantity in sales_items:
                        try:
                            save_daily_sales_item(sales_date, menu_name, quantity)
                            success_count += 1
                        except Exception as e:
                            errors.append(f"{menu_name}: {e}")
                    
                    if errors:
                        for msg in errors:
                            st.error(msg)
                    
                    if success_count > 0:
                        st.session_state["sales_volume_entry_success"] = "✅ 판매량 보정 저장 완료! (마감 입력보다 우선 적용)"
                        if is_dev_mode():
                            store_id = get_current_store_id()
                            if store_id and verify_overrides_saved(store_id, sales_date, success_count):
                                st.session_state["sales_volume_entry_verify"] = "🔧 override 저장 확인됨 (DEV)"
                        st.rerun()


# Streamlit 멀티페이지에서 직접 실행될 때
# 주석 처리: app.py에서만 렌더되도록 함 (중복 호출 방지)
# render_sales_volume_entry()
