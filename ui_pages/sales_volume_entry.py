"""
판매량 등록 페이지
"""
from src.bootstrap import bootstrap
import streamlit as st
from src.ui_helpers import render_page_header, render_section_divider
from src.utils.time_utils import today_kst
from src.storage_supabase import load_csv, save_daily_sales_item

# 공통 설정 적용
bootstrap(page_title="Sales Volume Entry")


def render_sales_volume_entry():
    """판매량 등록 페이지 렌더링"""
    render_page_header("판매량 등록", "📦")
    
    # STEP 3: 우선순위 안내
    st.info("💡 **이 값은 마감 입력보다 우선(최종값) 적용됩니다.** 마감 후에도 판매량등록으로 수정한 값이 최종 반영됩니다.")
    
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
        
        save_col, _ = st.columns([1, 3])
        with save_col:
            if st.button("💾 일괄 저장", type="primary", use_container_width=True, key="sales_volume_entry_daily_sales_full_save"):
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
                        st.success(f"✅ {sales_date} 기준 {success_count}개 메뉴의 판매 내역이 저장되었습니다.")
                        st.balloons()
                        st.rerun()


# Streamlit 멀티페이지에서 직접 실행될 때
# 주석 처리: app.py에서만 렌더되도록 함 (중복 호출 방지)
# render_sales_volume_entry()
