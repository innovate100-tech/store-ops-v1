"""
발주 관리 페이지 UI 렌더링 함수 모듈

목적: app.py의 발주 관리 섹션 코드를 모듈화하여 가독성과 유지보수성 향상
"""
import streamlit as st
import pandas as pd
from typing import Optional
from src.ui_helpers import (
    render_section_header,
    render_section_divider,
    handle_data_error,
    format_quantity_with_unit,
    format_price_with_unit,
    convert_to_order_unit,
    convert_to_base_unit,
    merge_ingredient_with_inventory,
    safe_get_value
)
from src.storage_supabase import load_csv, save_inventory


def render_safety_stock_tab(ingredient_df: pd.DataFrame, load_csv_func):
    """안전재고 등록 탭 렌더링"""
    render_section_header("안전재고 등록", "🛡️")
    
    # 탭 진입 시 최신 재고 데이터 로드
    tab1_inventory_df = load_csv_func('inventory.csv', default_columns=['재료명', '현재고', '안전재고'])
    
    if ingredient_df.empty:
        st.info("먼저 재료를 등록해주세요.")
    else:
        st.caption("전체 재료를 한 번에 펼쳐서 발주단위 기준 안전재고를 등록·수정할 수 있습니다.")
        
        # 재료 목록과 기존 안전재고를 조인 (발주단위/변환비율 포함)
        safety_df = merge_ingredient_with_inventory(
            ingredient_df,
            tab1_inventory_df
        )
        
        # 사용단가 / 발주단가 계산
        safety_df['발주단위단가_숫자'] = safety_df['단가'] * safety_df['변환비율']
        
        # 재료가 많을 경우 페이지네이션 적용 (성능 최적화)
        items_per_page = 20
        total_items = len(safety_df)
        total_pages = (total_items + items_per_page - 1) // items_per_page if total_items > 0 else 1
        
        if total_items > items_per_page:
            page_num = st.number_input(
                f"페이지 (총 {total_pages}페이지, {total_items}개 재료)",
                min_value=1,
                max_value=total_pages,
                value=1,
                step=1,
                key="safety_stock_page"
            )
            start_idx = (page_num - 1) * items_per_page
            end_idx = min(start_idx + items_per_page, total_items)
            safety_df_page = safety_df.iloc[start_idx:end_idx].copy()
        else:
            safety_df_page = safety_df
        
        # 헤더 행 (테이블 느낌으로)
        h1, h2, h3, h4, h5, h6, h7 = st.columns([3, 1.2, 1.2, 1.8, 1.8, 2, 1])
        h1.markdown("**재료명**")
        h2.markdown("**사용단위**")
        h3.markdown("**발주단위**")
        h4.markdown("**사용단가**")
        h5.markdown("**발주단가**")
        h6.markdown("**안전재고 (발주단위)**")
        h7.markdown("**저장**")
        
        for idx, row in safety_df_page.iterrows():
            # 기존 안전재고를 발주단위 기준으로 변환
            current_safety_order = convert_to_order_unit(
                float(row['안전재고'] or 0.0),
                float(row['변환비율'] or 1.0)
            )
            
            col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 1.2, 1.2, 1.8, 1.8, 2, 1])
            with col1:
                st.write(f"**{row['재료명']}**")
            with col2:
                st.write(row['단위'])
            with col3:
                st.write(row['발주단위'])
            with col4:
                st.write(format_price_with_unit(row['단가'], row['단위']))
            with col5:
                st.write(format_price_with_unit(row['발주단위단가_숫자'], row['발주단위']))
            with col6:
                new_safety_order = st.number_input(
                    f"발주단위: {row['발주단위']}",
                    min_value=0.0,
                    value=current_safety_order,
                    step=1.0,
                    format="%.2f",
                    key=f"safety_stock_order_{row['재료명']}",
                )
            with col7:
                if st.button("저장", key=f"safety_save_{row['재료명']}", use_container_width=True):
                    try:
                        # 기존 현재고는 그대로 두고, 안전재고만 수정 (기본단위 기준으로 저장)
                        if not tab1_inventory_df.empty and row['재료명'] in tab1_inventory_df['재료명'].values:
                            cur_row = tab1_inventory_df[tab1_inventory_df['재료명'] == row['재료명']].iloc[0]
                            current_stock_base = float(cur_row.get('현재고', 0) or 0)
                        else:
                            current_stock_base = 0.0
                        
                        new_safety_base = convert_to_base_unit(
                            float(new_safety_order),
                            float(row['변환비율'] or 1.0)
                        )
                        
                        save_inventory(row['재료명'], current_stock_base, new_safety_base)
                        # inventory.csv 캐시 클리어하여 다음 로드 시 최신 데이터 반영
                        try:
                            load_csv_func.clear()
                        except Exception:
                            pass
                        st.success(
                            f"✅ '{row['재료명']}'의 안전재고가 "
                            f"{format_quantity_with_unit(new_safety_order, row['발주단위'])} "
                            f"(기본단위 기준 {format_quantity_with_unit(new_safety_base, row['단위'])})로 저장되었습니다."
                        )
                    except Exception as e:
                        error_msg = handle_data_error("안전재고 저장", e)
                        st.error(error_msg)


def render_inventory_status_tab(ingredient_df: pd.DataFrame, load_csv_func):
    """현재 재고 현황 탭 렌더링"""
    render_section_header("현재 재고 현황", "📦")
    
    # 탭 진입 시 최신 재고 데이터 로드
    tab2_inventory_df = load_csv_func('inventory.csv', default_columns=['재료명', '현재고', '안전재고'])
    
    if not ingredient_df.empty:
        # 전체 재료 기준으로 조인해서 재고가 없는 재료도 모두 표시
        display_inventory_df = merge_ingredient_with_inventory(ingredient_df, tab2_inventory_df)
        
        # 발주단위단가 계산
        display_inventory_df['발주단위단가_숫자'] = display_inventory_df['단가'] * display_inventory_df['변환비율']
        
        # 재료사용단가 포맷팅
        display_inventory_df['재료사용단가'] = display_inventory_df.apply(
            lambda row: format_price_with_unit(row['단가'], row['단위']), axis=1
        )
        display_inventory_df['발주단위단가'] = display_inventory_df.apply(
            lambda row: format_price_with_unit(row['발주단위단가_숫자'], row['발주단위']), axis=1
        )
        
        # 현재고와 안전재고를 발주 단위로 변환
        display_inventory_df['현재고_발주단위'] = display_inventory_df.apply(
            lambda row: convert_to_order_unit(row['현재고'], row['변환비율']), axis=1
        )
        display_inventory_df['안전재고_발주단위'] = display_inventory_df.apply(
            lambda row: convert_to_order_unit(row['안전재고'], row['변환비율']), axis=1
        )
        
        # 현재고/안전재고/차이 표시
        display_inventory_df['현재고표시'] = display_inventory_df.apply(
            lambda row: format_quantity_with_unit(row['현재고_발주단위'], row['발주단위']), axis=1
        )
        display_inventory_df['안전재고표시'] = display_inventory_df.apply(
            lambda row: format_quantity_with_unit(row['안전재고_발주단위'], row['발주단위']), axis=1
        )
        display_inventory_df['차이'] = display_inventory_df['현재고_발주단위'] - display_inventory_df['안전재고_발주단위']
        display_inventory_df['차이(+/-)'] = display_inventory_df.apply(
            lambda row: f"{row['차이']:+,.2f} {row['발주단위']}", axis=1
        )
        
        # 표 표시
        view_cols = [
            '재료명', '단위', '재료사용단가',
            '발주단위', '발주단위단가',
            '현재고표시', '안전재고표시', '차이(+/-)'
        ]
        rename_map = {
            '단위': '재료사용단위',
            '현재고표시': '현재고',
            '안전재고표시': '기준 안전재고',
        }
        st.dataframe(
            display_inventory_df[view_cols].rename(columns=rename_map),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("먼저 재료를 등록해주세요.")
    
    render_section_divider()
    render_section_header("현재고 수정 (안전재고는 1번 탭에서 관리)", "✏️")
    
    if not ingredient_df.empty:
        # 전체 재료 기준으로 현재고/안전재고를 한 번에 수정
        edit_df = merge_ingredient_with_inventory(ingredient_df, tab2_inventory_df)
        
        # 발주단가 계산
        edit_df['발주단위단가_숫자'] = edit_df['단가'] * edit_df['변환비율']
        
        # 현재고/안전재고를 발주단위 기준으로 변환
        edit_df['현재고_발주단위'] = edit_df.apply(
            lambda row: convert_to_order_unit(row['현재고'], row['변환비율']), axis=1
        )
        edit_df['안전재고_발주단위'] = edit_df.apply(
            lambda row: convert_to_order_unit(row['안전재고'], row['변환비율']), axis=1
        )
        
        # 재료가 많을 경우 페이지네이션 적용
        items_per_page = 20
        total_items = len(edit_df)
        total_pages = (total_items + items_per_page - 1) // items_per_page if total_items > 0 else 1
        
        if total_items > items_per_page:
            page_num = st.number_input(
                f"페이지 (총 {total_pages}페이지, {total_items}개 재료)",
                min_value=1,
                max_value=total_pages,
                value=1,
                step=1,
                key="inventory_edit_page"
            )
            start_idx = (page_num - 1) * items_per_page
            end_idx = min(start_idx + items_per_page, total_items)
            edit_df_page = edit_df.iloc[start_idx:end_idx].copy()
        else:
            edit_df_page = edit_df
        
        # 헤더
        h1, h2, h3, h4, h5, h6, h7, h8 = st.columns([3, 1.2, 1.2, 1.8, 1.8, 2, 2, 1])
        h1.markdown("**재료명**")
        h2.markdown("**사용단위**")
        h3.markdown("**발주단위**")
        h4.markdown("**사용단가**")
        h5.markdown("**발주단가**")
        h6.markdown("**기준 안전재고 (발주단위)**")
        h7.markdown("**현재고 입력 (발주단위)**")
        h8.markdown("**저장**")
        
        for idx, row in edit_df_page.iterrows():
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([3, 1.2, 1.2, 1.8, 1.8, 2, 2, 1])
            with col1:
                st.write(f"**{row['재료명']}**")
            with col2:
                st.write(row['단위'])
            with col3:
                st.write(row['발주단위'])
            with col4:
                st.write(format_price_with_unit(row['단가'], row['단위']))
            with col5:
                st.write(format_price_with_unit(row['발주단위단가_숫자'], row['발주단위']))
            with col6:
                # 기준 안전재고는 읽기 전용
                st.write(format_quantity_with_unit(float(row['안전재고_발주단위']), row['발주단위']))
            with col7:
                # 현재고만 입력/수정
                new_current_order = st.number_input(
                    f"발주단위: {row['발주단위']}",
                    min_value=0.0,
                    value=float(row['현재고_발주단위']),
                    step=1.0,
                    format="%.2f",
                    key=f"edit_current_order_{row['재료명']}"
                )
            with col8:
                if st.button("저장", key=f"edit_inventory_save_{row['재료명']}", use_container_width=True):
                    try:
                        # 발주단위를 기본단위로 변환해서 저장
                        new_current_base = convert_to_base_unit(
                            float(new_current_order),
                            float(row['변환비율'] or 1.0)
                        )
                        # 기존 안전재고는 그대로 사용
                        new_safety_base = float(row['안전재고'] or 0.0)
                        
                        save_inventory(row['재료명'], new_current_base, new_safety_base)
                        # 캐시 클리어
                        try:
                            load_csv_func.clear()
                        except Exception:
                            pass
                        st.success(
                            f"✅ '{row['재료명']}'의 현재고가 "
                            f"{format_quantity_with_unit(new_current_order, row['발주단위'])} "
                            f"(기본단위 기준 {format_quantity_with_unit(new_current_base, row['단위'])})로 수정되었습니다. "
                            f"(안전재고는 변경되지 않았습니다.)"
                        )
                    except Exception as e:
                        error_msg = handle_data_error("재고 수정", e)
                        st.error(error_msg)


def render_order_recommendation_tab(ingredient_df: pd.DataFrame, inventory_df: pd.DataFrame, load_csv_func):
    """발주 추천 탭 렌더링 (복잡한 탭 - 나중에 세부 함수로 분리 예정)"""
    # 이 함수는 매우 복잡하므로(800줄), 
    # 일단 기본 구조만 만들고 app.py에서 직접 호출하도록 함
    # 향후 세부 함수로 분리 예정
    render_section_header("발주 추천", "🛒")
    st.info("발주 추천 기능은 현재 app.py에서 직접 렌더링됩니다. 향후 이 모듈로 이동 예정입니다.")


def render_order_history_tab(ingredient_df: pd.DataFrame, load_csv_func):
    """발주 이력 탭 렌더링"""
    render_section_header("진행 현황", "📋")
    
    from datetime import datetime
    
    # 발주 이력 로드
    orders_df = load_csv_func('orders.csv', default_columns=['id', '재료명', '공급업체명', '발주일', '수량', '단가', '총금액'])
    
    if not orders_df.empty:
        # 재료 정보와 조인하여 단위/발주단위/변환비율 확보
        orders_display = pd.merge(
            orders_df,
            ingredient_df[['재료명', '단위', '발주단위', '변환비율']] if not ingredient_df.empty else pd.DataFrame(columns=['재료명', '단위', '발주단위', '변환비율']),
            on='재료명',
            how='left'
        )
        orders_display['발주단위'] = orders_display['발주단위'].fillna(orders_display['단위'])
        orders_display['변환비율'] = orders_display['변환비율'].fillna(1.0)
        
        # 발주일 정리
        if '발주일' in orders_display.columns:
            orders_display['발주일'] = pd.to_datetime(orders_display['발주일'], errors='coerce')
        else:
            orders_display['발주일'] = pd.NaT
        
        # 생성 시각
        if 'created_at' in orders_display.columns:
            orders_display['생성시각'] = pd.to_datetime(orders_display['created_at'], errors='coerce')
        else:
            orders_display['생성시각'] = pd.NaT
        
        # 발주 수량/단가를 발주단위 기준으로 변환
        orders_display['수량_발주단위'] = orders_display.apply(
            lambda row: convert_to_order_unit(row['수량'], row['변환비율']), axis=1
        )
        orders_display['발주단위단가'] = orders_display['단가'] * orders_display['변환비율']
        
        # 발주 생성 배치 기준 그룹 키
        orders_display['그룹키'] = orders_display['생성시각'].dt.floor('S')
        fallback_mask = orders_display['그룹키'].isna()
        orders_display.loc[fallback_mask, '그룹키'] = orders_display.loc[fallback_mask, '발주일']
        
        # 최신 발주부터 표시
        orders_display = orders_display.sort_values('그룹키', ascending=False)
        grouped = orders_display.groupby('그룹키')
        
        for group_key, group in grouped:
            # 헤더용 일시 문자열 구성
            header_dt = pd.to_datetime(group_key, errors='coerce')
            if pd.isna(header_dt):
                date_time_str = "발주일시 미지정"
            else:
                date_time_str = header_dt.strftime("%Y-%m-%d %H:%M:%S")
            
            total_amount = group['총금액'].fillna(0).sum()
            
            st.markdown(f"""
            <div style="background: rgba(15,23,42,0.9); border-radius: 10px; padding: 1rem; margin-bottom: 1rem; border: 1px solid rgba(148,163,184,0.3);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <div style="font-size: 1rem; font-weight: 600; color: #e5e7eb;">📅 발주일시: {date_time_str}</div>
                    <div style="font-size: 0.95rem; color: #93c5fd;">총 발주 금액: {int(total_amount):,}원</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            display_cols = ['재료명', '공급업체명', '단위', '발주단위', '수량_발주단위', '발주단위단가', '총금액']
            disp = group[display_cols].copy()
            disp.rename(columns={
                '단위': '사용단위',
                '수량_발주단위': '수량(발주단위)',
                '발주단위단가': '발주단가(발주단위)',
            }, inplace=True)
            
            disp['수량(발주단위)'] = disp['수량(발주단위)'].apply(lambda x: f"{x:,.2f}")
            disp['발주단가(발주단위)'] = disp['발주단가(발주단위)'].apply(lambda x: f"{int(x):,}원")
            disp['총금액'] = disp['총금액'].apply(lambda x: f"{int(x):,}원")
            
            st.dataframe(disp, use_container_width=True, hide_index=True)
    else:
        st.info("아직 생성된 발주 이력이 없습니다. 발주 추천 탭에서 발주를 생성해 주세요.")


def render_supplier_management_tab(ingredient_df: pd.DataFrame, load_csv_func):
    """공급업체 관리 탭 렌더링"""
    render_section_header("공급업체 관리", "🏢")
    
    from src.storage_supabase import save_supplier, delete_supplier, save_ingredient_supplier, delete_ingredient_supplier
    
    # 성공/삭제 메시지 표시
    if 'supplier_success_message' in st.session_state and st.session_state.supplier_success_message:
        st.success(st.session_state.supplier_success_message)
        del st.session_state.supplier_success_message
    
    # 입력 필드 초기화
    if st.session_state.get('supplier_form_reset', False):
        if 'supplier_form_key_counter' not in st.session_state:
            st.session_state.supplier_form_key_counter = 0
        st.session_state.supplier_form_key_counter += 1
        st.session_state.supplier_form_reset = False
    
    if 'supplier_form_key_counter' not in st.session_state:
        st.session_state.supplier_form_key_counter = 0
    
    with st.expander("➕ 공급업체 등록", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            supplier_name = st.text_input("공급업체명 *", key=f"new_supplier_name_{st.session_state.supplier_form_key_counter}")
            phone = st.text_input("전화번호", key=f"new_supplier_phone_{st.session_state.supplier_form_key_counter}")
            email = st.text_input("이메일", key=f"new_supplier_email_{st.session_state.supplier_form_key_counter}")
        with col2:
            delivery_days = st.text_input("배송일 (일수)", key=f"new_supplier_delivery_days_{st.session_state.supplier_form_key_counter}", help="예: 2 (2일 소요)")
            min_order_amount = st.number_input("최소 주문금액 (원)", min_value=0, value=0, key=f"new_supplier_min_order_{st.session_state.supplier_form_key_counter}")
            delivery_fee = st.number_input("배송비 (원)", min_value=0, value=0, key=f"new_supplier_delivery_fee_{st.session_state.supplier_form_key_counter}")
        
        notes = st.text_area("비고", key=f"new_supplier_notes_{st.session_state.supplier_form_key_counter}")
        
        if st.button("💾 공급업체 등록", type="primary", key=f"save_supplier_{st.session_state.supplier_form_key_counter}"):
            if supplier_name:
                try:
                    save_supplier(supplier_name, phone, email, delivery_days, min_order_amount, delivery_fee, notes)
                    try:
                        load_csv_func.clear()
                    except Exception:
                        pass
                    st.success(f"✅ 공급업체 '{supplier_name}'가 등록되었습니다!")
                    st.session_state.supplier_form_reset = True
                    st.session_state.supplier_form_key_counter += 1
                    st.session_state.supplier_data_refresh = True
                except Exception as e:
                    st.error(f"등록 중 오류가 발생했습니다: {e}")
            else:
                st.warning("공급업체명을 입력해주세요.")
    
    render_section_divider()
    
    # 공급업체 목록
    if st.session_state.get('supplier_data_refresh', False):
        try:
            load_csv_func.clear()
        except Exception:
            pass
        st.session_state.supplier_data_refresh = False
    
    suppliers_df = load_csv_func('suppliers.csv', default_columns=['공급업체명', '전화번호', '이메일', '배송일', '최소주문금액', '배송비', '비고'])
    
    # 삭제된 공급업체가 있으면 목록에서 즉시 제외
    deleted_supplier = st.session_state.get('just_deleted_supplier', None)
    if deleted_supplier and not suppliers_df.empty and deleted_supplier in suppliers_df['공급업체명'].values:
        suppliers_df = suppliers_df[suppliers_df['공급업체명'] != deleted_supplier].copy()
        del st.session_state.just_deleted_supplier
    
    if not suppliers_df.empty:
        supplier_search = st.text_input("공급업체 검색 (이름 일부 입력)", key="supplier_search")
        if supplier_search:
            suppliers_df = suppliers_df[
                suppliers_df['공급업체명'].astype(str).str.contains(supplier_search, case=False, na=False)
            ]
    
    if not suppliers_df.empty:
        st.write("**📋 등록된 공급업체**")
        
        # 재료-공급업체 매핑을 이용해 업체별 취급 품목 목록 생성
        ingredient_suppliers_all = load_csv_func('ingredient_suppliers.csv', default_columns=['재료명', '공급업체명'])
        supplier_items_map = {}
        if not ingredient_suppliers_all.empty:
            for sup_name in suppliers_df['공급업체명'].tolist():
                items = ingredient_suppliers_all[ingredient_suppliers_all['공급업체명'] == sup_name]['재료명'].dropna().unique().tolist()
                if items:
                    supplier_items_map[sup_name] = ", ".join(items)
                else:
                    supplier_items_map[sup_name] = ""
        else:
            supplier_items_map = {sup_name: "" for sup_name in suppliers_df['공급업체명'].tolist()}
        
        # 표시용 DataFrame 구성
        display_suppliers = suppliers_df.copy()
        for col in ['name', 'phone', 'email', 'delivery_days', 'min_order_amount', 'delivery_fee', 'notes']:
            if col in display_suppliers.columns:
                display_suppliers.drop(columns=[col], inplace=True)
        
        display_suppliers['취급품목'] = display_suppliers['공급업체명'].map(supplier_items_map).fillna("")
        
        display_cols = ['공급업체명', '전화번호', '이메일', '배송일', '최소주문금액', '배송비', '비고', '취급품목']
        display_cols = [c for c in display_cols if c in display_suppliers.columns]
        
        st.dataframe(display_suppliers[display_cols], use_container_width=True, hide_index=True)
        
        # 공급업체 삭제
        if 'supplier_delete_key_counter' not in st.session_state:
            st.session_state.supplier_delete_key_counter = 0
        
        supplier_options = suppliers_df['공급업체명'].tolist() if not suppliers_df.empty else []
        default_index = 0 if supplier_options else None
        
        supplier_to_delete = st.selectbox(
            "삭제할 공급업체", 
            options=supplier_options if supplier_options else ["삭제할 공급업체가 없습니다"],
            index=default_index,
            key=f"delete_supplier_select_{st.session_state.supplier_delete_key_counter}"
        )
        
        if st.button("🗑️ 공급업체 삭제", key=f"delete_supplier_{st.session_state.supplier_delete_key_counter}"):
            try:
                mapped_count = 0
                if not ingredient_suppliers_all.empty:
                    mapped_count = int((ingredient_suppliers_all['공급업체명'] == supplier_to_delete).sum())
                
                delete_supplier(supplier_to_delete)
                
                warn_suffix = f" (연결된 매핑 {mapped_count}건도 함께 삭제되었습니다.)" if mapped_count > 0 else ""
                st.success(f"✅ 공급업체 '{supplier_to_delete}'가 삭제되었습니다!{warn_suffix}")
                st.session_state.just_deleted_supplier = supplier_to_delete
                st.session_state.supplier_delete_key_counter += 1
                try:
                    load_csv_func.clear()
                except Exception:
                    pass
                st.session_state.supplier_data_refresh = True
            except Exception as e:
                st.error(f"삭제 중 오류가 발생했습니다: {e}")
    else:
        st.info("등록된 공급업체가 없습니다.")
    
    render_section_divider()
    
    # 재료-공급업체 매핑
    render_section_header("재료-공급업체 매핑", "🔗")
    
    ingredient_list = ingredient_df['재료명'].tolist() if not ingredient_df.empty else []
    
    if not suppliers_df.empty and not ingredient_df.empty:
        with st.expander("➕ 재료-공급업체 매핑 추가", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                ingredient_options = []
                if '발주단위' in ingredient_df.columns:
                    for ing in ingredient_list:
                        ing_row = ingredient_df[ingredient_df['재료명'] == ing]
                        if not ing_row.empty:
                            unit = safe_get_value(ing_row, '단위', '')
                            order_unit = safe_get_value(ing_row, '발주단위', unit)
                            if order_unit != unit:
                                ingredient_options.append(f"{ing} ({unit} / 발주: {order_unit})")
                            else:
                                ingredient_options.append(f"{ing} ({unit})")
                        else:
                            ingredient_options.append(ing)
                else:
                    ingredient_options = ingredient_list
                
                default_ingredient_index = 0
                if 'mapping_ingredient' in st.session_state and st.session_state.mapping_ingredient in ingredient_options:
                    try:
                        default_ingredient_index = ingredient_options.index(st.session_state.mapping_ingredient)
                    except ValueError:
                        default_ingredient_index = 0
                
                mapping_ingredient_option = st.selectbox(
                    "재료 선택", 
                    options=ingredient_options, 
                    index=default_ingredient_index,
                    key="mapping_ingredient"
                )
                mapping_ingredient = mapping_ingredient_option.split(" (")[0] if " (" in mapping_ingredient_option else mapping_ingredient_option
                
                supplier_options = suppliers_df['공급업체명'].tolist()
                default_supplier_index = 0
                if 'mapping_supplier' in st.session_state and st.session_state.mapping_supplier in supplier_options:
                    try:
                        default_supplier_index = supplier_options.index(st.session_state.mapping_supplier)
                    except ValueError:
                        default_supplier_index = 0
                
                mapping_supplier = st.selectbox(
                    "공급업체 선택", 
                    options=supplier_options, 
                    index=default_supplier_index,
                    key="mapping_supplier"
                )
            with col2:
                mapping_price = st.number_input(
                    "발주 단위 기준 단가 (원/발주단위)",
                    min_value=0.0,
                    value=0.0,
                    key="mapping_price",
                    help="예: 1박스 가격, 1개 가격 등 발주 단위 기준 금액을 입력하세요."
                )
                is_default = st.checkbox("기본 공급업체로 설정", value=True, key="mapping_is_default")
            
            if st.button("💾 매핑 저장", type="primary", key="save_mapping"):
                try:
                    save_ingredient_supplier(mapping_ingredient, mapping_supplier, mapping_price, is_default)
                    try:
                        load_csv_func.clear()
                    except Exception:
                        pass
                    st.success(f"✅ 매핑이 저장되었습니다! ({mapping_ingredient} → {mapping_supplier})")
                except Exception as e:
                    error_msg = handle_data_error("메뉴 저장", e)
                    st.error(error_msg)
        
        # 매핑 목록
        ingredient_suppliers_df = load_csv_func('ingredient_suppliers.csv', default_columns=['재료명', '공급업체명', '단가', '기본공급업체'])
        
        if not ingredient_suppliers_df.empty:
            st.write("**📋 재료-공급업체 매핑 목록**")
            display_mapping = ingredient_suppliers_df.copy()
            
            # 재료 단위/발주단위 정보 추가
            unit_map = dict(zip(ingredient_df['재료명'], ingredient_df.get('단위', pd.Series(index=ingredient_df.index, dtype=str))))
            order_unit_map = dict(zip(ingredient_df['재료명'], ingredient_df.get('발주단위', ingredient_df.get('단위', pd.Series(index=ingredient_df.index, dtype=str)))))
            conv_map = dict(zip(ingredient_df['재료명'], ingredient_df.get('변환비율', pd.Series(index=ingredient_df.index, dtype=float)).fillna(1.0)))
            base_unit_cost_map = dict(zip(ingredient_df['재료명'], ingredient_df.get('단가', pd.Series(index=ingredient_df.index, dtype=float)).fillna(0.0)))
            
            display_mapping['사용단위'] = display_mapping['재료명'].map(unit_map).fillna('')
            display_mapping['발주단위'] = display_mapping['재료명'].map(order_unit_map).fillna(display_mapping['사용단위'])
            
            base_price_series = display_mapping.get('단가', pd.Series(index=display_mapping.index, dtype=float)).fillna(0)
            conv_series = display_mapping['재료명'].map(conv_map).fillna(1.0)
            
            display_mapping['사용단가'] = base_price_series.astype(float).round(1)
            display_mapping['발주단가'] = (base_price_series * conv_series).astype(float).round(1)
            
            display_mapping['사용단가표시'] = display_mapping.apply(
                lambda row: format_price_with_unit(row['사용단가'], row['사용단위']), axis=1
            )
            display_mapping['발주단가표시'] = display_mapping.apply(
                lambda row: format_price_with_unit(row['발주단가'], row['발주단위']), axis=1
            )
            
            display_cols = ['재료명', '공급업체명', '사용단위', '발주단위', '사용단가표시', '발주단가표시', '기본공급업체']
            st.dataframe(display_mapping[display_cols].rename(columns={
                '사용단가표시': '사용단가',
                '발주단가표시': '발주단가',
                '기본공급업체': '기본'
            }), use_container_width=True, hide_index=True)
            
            # 매핑 삭제
            if not ingredient_suppliers_df.empty:
                delete_options = []
                for idx, row in ingredient_suppliers_df.iterrows():
                    delete_options.append(f"{row['재료명']} - {row['공급업체명']}")
                
                if delete_options:
                    selected_mapping = st.selectbox("삭제할 매핑", options=delete_options, key="delete_mapping_select")
                    
                    if st.button("🗑️ 매핑 삭제", key="delete_mapping"):
                        try:
                            parts = selected_mapping.split(" - ")
                            if len(parts) == 2:
                                delete_ingredient_supplier(parts[0], parts[1])
                                try:
                                    load_csv_func.clear()
                                except Exception:
                                    pass
                                st.success(f"✅ 매핑이 삭제되었습니다! ({parts[0]} - {parts[1]})")
                                st.rerun()
                        except Exception as e:
                            error_msg = handle_data_error("매핑 삭제", e)
                            st.error(error_msg)
    else:
        st.info("공급업체와 재료를 먼저 등록해주세요.")


def render_order_analysis_tab():
    """발주 분석 대시보드 탭 렌더링"""
    render_section_header("발주 분석 대시보드", "📊")
    st.info("📊 발주 분석 대시보드는 현재 일시적으로 비활성화되었습니다.\n안정성 개선 이후에 다시 제공할 예정입니다.")
