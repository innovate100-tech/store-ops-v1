"""
재료 등록 페이지
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
import logging
from src.ui_helpers import render_page_header, render_section_divider, safe_get_row_by_condition, handle_data_error
from src.ui import render_ingredient_input
from src.storage_supabase import load_csv, save_ingredient, update_ingredient, delete_ingredient, get_supabase_client, get_current_store_id

# 공통 설정 적용
bootstrap(page_title="Ingredient Management")


def _show_ingredient_query_diagnostics():
    """재료 등록 페이지에서 사용하는 실제 쿼리 정보 출력"""
    try:
        from src.auth import get_current_store_id
        from src.storage_supabase import get_read_client
        
        store_id = get_current_store_id()
        st.write(f"**사용된 store_id:** `{store_id}`")
        
        st.divider()
        st.write("**실제 쿼리 실행 결과:**")
        
        # 1. load_csv 호출 테스트
        st.write("**1. load_csv('ingredient_master.csv') 호출 결과:**")
        try:
            ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가', '발주단위', '변환비율'])
            st.write(f"- Row count: {len(ingredient_df)}")
            st.write(f"- DataFrame columns: {list(ingredient_df.columns)}")
            if not ingredient_df.empty:
                st.write("- 첫 row 샘플:")
                st.json(ingredient_df.iloc[0].to_dict())
            else:
                st.warning("⚠️ 데이터가 비어있습니다.")
        except Exception as e:
            st.error(f"❌ 에러: {type(e).__name__}: {str(e)}")
            st.code(str(e), language="text")
            st.exception(e)
        
        st.divider()
        
        # 2. 직접 Supabase 쿼리 테스트 (필터 없이)
        st.write("**2. 직접 Supabase 쿼리 (ingredients 테이블, 필터 없이):**")
        try:
            supabase = get_read_client()
            if supabase:
                # 필터 없이 조회
                result_no_filter = supabase.table("ingredients").select("*").limit(10).execute()
                st.write(f"- 필터 없이 Row count: {len(result_no_filter.data) if result_no_filter.data else 0}")
                
                if result_no_filter.data:
                    # store_id 목록 확인
                    store_ids = set([row.get('store_id') for row in result_no_filter.data if row.get('store_id')])
                    st.write(f"- 발견된 store_id 목록: {list(store_ids)}")
                    st.write("- 첫 row 샘플:")
                    st.json(result_no_filter.data[0])
                
                st.divider()
                
                # store_id 필터로 조회
                if store_id:
                    st.write(f"**3. 직접 Supabase 쿼리 (ingredients 테이블, store_id={store_id}):**")
                    result_with_filter = supabase.table("ingredients").select("*").eq("store_id", store_id).limit(10).execute()
                    st.write(f"- Row count: {len(result_with_filter.data) if result_with_filter.data else 0}")
                    st.write(f"- 쿼리 조건: `table('ingredients').select('*').eq('store_id', '{store_id}')`")
                    
                    if result_with_filter.data:
                        st.write("- 첫 row 샘플:")
                        st.json(result_with_filter.data[0])
                    else:
                        st.warning("⚠️ store_id 필터로 조회한 데이터가 비어있습니다.")
                        
                        # store_id가 다른 데이터가 있는지 확인
                        if result_no_filter.data:
                            st.warning(f"⚠️ 테이블에는 데이터가 있지만, store_id=`{store_id}` 조건으로는 조회되지 않습니다.")
                            st.info("💡 가능한 원인:")
                            st.info("1. RLS 정책 문제")
                            st.info("2. store_id 불일치 (데이터는 다른 store_id로 저장됨)")
                            st.info("3. 로그인 사용자의 권한 문제")
                else:
                    st.error("❌ store_id가 없어서 필터 쿼리를 실행할 수 없습니다.")
            else:
                st.error("❌ Supabase 클라이언트를 생성할 수 없습니다.")
        except Exception as e:
            st.error(f"❌ 에러: {type(e).__name__}: {str(e)}")
            st.code(str(e), language="text")
            st.exception(e)
            
    except Exception as e:
        st.error(f"진단 중 오류 발생: {type(e).__name__}: {str(e)}")
        st.exception(e)


def render_ingredient_management():
    """재료 등록 페이지 렌더링"""
    render_page_header("재료 등록", "🥬")
    
    # 쿼리 진단 기능 추가
    with st.expander("🔍 쿼리 진단 정보 (DEV)", expanded=False):
        _show_ingredient_query_diagnostics()
    
    # 재료 입력 폼
    ingredient_result = render_ingredient_input(key_prefix="ingredient_management")
    if len(ingredient_result) == 5:
        ingredient_name, unit, unit_price, order_unit, conversion_rate = ingredient_result
    else:
        # 기존 호환성 유지
        ingredient_name, unit, unit_price = ingredient_result[:3]
        order_unit = None
        conversion_rate = 1.0
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("💾 저장", type="primary", use_container_width=True):
            if not ingredient_name or ingredient_name.strip() == "":
                st.error("재료명을 입력해주세요.")
            elif unit_price <= 0:
                st.error("단가는 0보다 큰 값이어야 합니다.")
            else:
                try:
                    # 단위 자동 변환: kg → g, L → ml
                    final_unit = unit
                    final_unit_price = unit_price
                    
                    if unit == "kg":
                        # kg을 g로 변환: 1kg = 1000g, 단가는 1000으로 나눔
                        final_unit = "g"
                        final_unit_price = unit_price / 1000.0
                        st.info(f"💡 단위가 자동 변환되었습니다: {unit} → {final_unit} (단가: {unit_price:,.2f}원/{unit} → {final_unit_price:,.4f}원/{final_unit})")
                    elif unit == "L":
                        # L을 ml로 변환: 1L = 1000ml, 단가는 1000으로 나눔
                        final_unit = "ml"
                        final_unit_price = unit_price / 1000.0
                        st.info(f"💡 단위가 자동 변환되었습니다: {unit} → {final_unit} (단가: {unit_price:,.2f}원/{unit} → {final_unit_price:,.4f}원/{final_unit})")
                    
                    # 발주 단위도 변환 필요 시 조정
                    final_order_unit = order_unit if order_unit else final_unit
                    final_conversion_rate = conversion_rate
                    
                    # 발주 단위가 기본 단위와 다르면 변환 비율 적용
                    if final_order_unit != final_unit and final_conversion_rate == 1.0:
                        # 변환 비율이 설정되지 않았으면 기본값 1 유지
                        pass
                    
                    success, message = save_ingredient(ingredient_name, final_unit, final_unit_price, final_order_unit, final_conversion_rate)
                    if success:
                        unit_display = f"{final_unit_price:,.4f}원/{final_unit}"
                        if final_order_unit != final_unit:
                            unit_display += f" (발주: {final_order_unit}, 변환비율: {final_conversion_rate})"
                        # 캐시만 클리어하고 rerun 없이 성공 메시지만 표시
                        try:
                            st.cache_data.clear()
                        except Exception as e:
                            logging.getLogger(__name__).warning(f"캐시 클리어 실패 (재료 저장): {e}")
                        st.success(f"✅ 재료가 저장되었습니다! ({ingredient_name}, {unit_display})")
                        # 입력 필드 초기화 (session_state로, key_prefix 사용)
                        if 'ingredient_management_ingredient_name' in st.session_state:
                            st.session_state.ingredient_management_ingredient_name = ""
                        if 'ingredient_management_ingredient_unit_price' in st.session_state:
                            st.session_state.ingredient_management_ingredient_unit_price = 0.0
                    else:
                        st.error(message)
                except Exception as e:
                    # Phase 3: 에러 메시지 표준화
                    error_msg = handle_data_error("방문자 데이터 저장", e)
                    st.error(error_msg)
    
    render_section_divider()
    
    # 저장된 재료 표시 및 수정/삭제
    # 제목을 화이트 모드에서도 흰색으로 표시
    st.markdown("""
    <div style="margin: 2rem 0 1rem 0;">
        <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
            📋 등록된 재료 리스트
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    ingredient_df = load_csv('ingredient_master.csv', default_columns=['재료명', '단위', '단가', '발주단위', '변환비율'])
    
    if not ingredient_df.empty:
        # 간단 검색 필터 (재료명 부분 일치)
        ing_search = st.text_input("재료 검색 (재료명 일부 입력)", key="ingredient_management_ingredient_search")
        if ing_search:
            ingredient_df = ingredient_df[ingredient_df['재료명'].astype(str).str.contains(ing_search, case=False, na=False)]
    
    if not ingredient_df.empty:
        # 발주 단위 정보 처리
        if '발주단위' not in ingredient_df.columns:
            ingredient_df['발주단위'] = ingredient_df['단위']
        if '변환비율' not in ingredient_df.columns:
            ingredient_df['변환비율'] = 1.0
        
        ingredient_df['발주단위'] = ingredient_df['발주단위'].fillna(ingredient_df['단위'])
        ingredient_df['변환비율'] = ingredient_df['변환비율'].fillna(1.0)
        
        # 표시용 DataFrame 생성
        display_df = ingredient_df[['재료명', '단위', '발주단위', '단가', '변환비율']].copy()
        
        # 원본 발주단위 저장 (발주단위단가 계산용)
        display_df['원본발주단위'] = display_df['발주단위']
        
        # 발주단위 컬럼 포맷팅 (발주단위 + 변환 정보)
        def format_order_unit(row):
            order_unit = row['발주단위']
            base_unit = row['단위']
            conversion_rate = row['변환비율']
            
            if pd.isna(order_unit) or order_unit == base_unit or conversion_rate == 1.0:
                # 발주단위가 기본단위와 같거나 변환비율이 1이면 단위만 표시
                return order_unit if not pd.isna(order_unit) else base_unit
            else:
                # 1 발주단위 = 변환비율 기본단위 형식으로 표시
                return f"{order_unit} (1{order_unit} = {conversion_rate:,.0f}{base_unit})"
        
        display_df['발주단위'] = display_df.apply(format_order_unit, axis=1)
        
        # 1단위단가 (기본 단위 기준) - 소수점 1자리까지
        display_df['1단위단가'] = display_df.apply(
            lambda row: f"{row['단가']:,.1f}원/{row['단위']}",
            axis=1
        )
        
        # 발주단위단가 계산 (기본 단가 × 변환비율)
        display_df['발주단위단가'] = display_df.apply(
            lambda row: f"{(row['단가'] * row['변환비율']):,.1f}원/{row['원본발주단위']}",
            axis=1
        )
        
        # 표시할 컬럼 선택: 재료명, 단위, 발주단위, 1단위단가, 발주단위단가
        display_cols = ['재료명', '단위', '발주단위', '1단위단가', '발주단위단가']
        display_df = display_df[display_cols]
        
        # 표에 수정/삭제 버튼 추가
        st.write("**📋 등록된 재료 리스트** (표에서 바로 수정/삭제 가능)")
        
        # 표 헤더
        header_col_name, header_col_unit, header_col_order_unit, header_col_price1, header_col_price2, header_col_actions = st.columns([2, 1, 2, 1.5, 1.5, 1.5])
        with header_col_name:
            st.markdown("**재료명**")
        with header_col_unit:
            st.markdown("**단위**")
        with header_col_order_unit:
            st.markdown("**발주단위**")
        with header_col_price1:
            st.markdown("**1단위단가**")
        with header_col_price2:
            st.markdown("**발주단위단가**")
        with header_col_actions:
            st.markdown("**작업**")
        
        st.markdown("<hr style='margin: 0.5rem 0; border-color: rgba(255,255,255,0.2);'>", unsafe_allow_html=True)
        
        # 각 재료별로 수정/삭제 버튼이 있는 표 생성
        for idx, row in display_df.iterrows():
            ingredient_name = row['재료명']
            # Phase 1: 안전한 DataFrame 접근
            ingredient_info = safe_get_row_by_condition(ingredient_df, ingredient_df['재료명'] == ingredient_name)
            
            if ingredient_info is None:
                st.warning(f"재료 '{ingredient_name}' 정보를 찾을 수 없습니다. 건너뜁니다.")
                continue
            
            # 행 표시
            col_name, col_unit, col_order_unit, col_price1, col_price2, col_actions = st.columns([2, 1, 2, 1.5, 1.5, 1.5])
            
            with col_name:
                st.write(f"**{row['재료명']}**")
            with col_unit:
                st.write(row['단위'])
            with col_order_unit:
                st.write(row['발주단위'])
            with col_price1:
                st.write(row['1단위단가'])
            with col_price2:
                st.write(row['발주단위단가'])
            with col_actions:
                # 수정/삭제 버튼
                edit_col, delete_col = st.columns(2)
                with edit_col:
                    if st.button("✏️", key=f"edit_{ingredient_name}", help="수정"):
                        st.session_state[f'editing_{ingredient_name}'] = True
                        st.rerun()
                with delete_col:
                    if st.button("🗑️", key=f"delete_{ingredient_name}", help="삭제"):
                        st.session_state[f'deleting_{ingredient_name}'] = True
                        st.rerun()
            
            # 수정 모드
            if st.session_state.get(f'editing_{ingredient_name}', False):
                with st.expander(f"✏️ {ingredient_name} 수정", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_ingredient_name = st.text_input("재료명", value=ingredient_info['재료명'], key=f"edit_name_{ingredient_name}")
                        new_unit = st.selectbox(
                            "기본 단위",
                            options=["g", "ml", "ea", "개", "kg", "L"],
                            index=["g", "ml", "ea", "개", "kg", "L"].index(ingredient_info['단위']) if ingredient_info['단위'] in ["g", "ml", "ea", "개", "kg", "L"] else 0,
                            key=f"edit_unit_{ingredient_name}"
                        )
                        new_unit_price = st.number_input("단가 (원/기본단위)", min_value=0.0, value=float(ingredient_info['단가']), step=100.0, key=f"edit_price_{ingredient_name}")
                    
                    with col2:
                        new_order_unit = st.selectbox(
                            "발주 단위",
                            options=["", "g", "ml", "ea", "개", "kg", "L", "박스", "봉지"],
                            index=["", "g", "ml", "ea", "개", "kg", "L", "박스", "봉지"].index(ingredient_info.get('발주단위', '')) if ingredient_info.get('발주단위', '') in ["", "g", "ml", "ea", "개", "kg", "L", "박스", "봉지"] else 0,
                            key=f"edit_order_unit_{ingredient_name}"
                        )
                        new_conversion_rate = st.number_input(
                            "변환 비율 (1 발주단위 = ? 기본단위)",
                            min_value=0.0,
                            value=float(ingredient_info.get('변환비율', 1.0)),
                            step=0.1,
                            format="%.2f",
                            key=f"edit_conversion_{ingredient_name}"
                        )
                    
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.button("💾 저장", key=f"save_edit_{ingredient_name}", type="primary"):
                            try:
                                # 단위 자동 변환: kg → g, L → ml
                                final_unit = new_unit
                                final_unit_price = new_unit_price
                                
                                if new_unit == "kg":
                                    final_unit = "g"
                                    final_unit_price = new_unit_price / 1000.0
                                elif new_unit == "L":
                                    final_unit = "ml"
                                    final_unit_price = new_unit_price / 1000.0
                                
                                final_order_unit = new_order_unit if new_order_unit else final_unit
                                
                                # update_ingredient 함수는 기존 함수이므로 발주단위와 변환비율을 지원하도록 수정 필요
                                # 일단 기본 정보만 업데이트
                                success, message = update_ingredient(ingredient_info['재료명'], new_ingredient_name, final_unit, final_unit_price)
                                if success:
                                    # 발주단위와 변환비율은 별도로 업데이트 필요
                                    supabase = get_supabase_client()
                                    store_id = get_current_store_id()
                                    if supabase and store_id:
                                        # 재료 ID 찾기
                                        ing_result = supabase.table("ingredients").select("id").eq("store_id", store_id).eq("name", new_ingredient_name).execute()
                                        if ing_result.data:
                                            supabase.table("ingredients").update({
                                                "order_unit": final_order_unit,
                                                "conversion_rate": float(new_conversion_rate)
                                            }).eq("id", ing_result.data[0]['id']).execute()
                                    
                                    st.session_state[f'editing_{ingredient_name}'] = False
                                    # 캐시만 클리어하고 rerun 없이 성공 메시지만 표시
                                    try:
                                        st.cache_data.clear()
                                    except Exception as e:
                                        logging.getLogger(__name__).warning(f"캐시 클리어 실패 (재료 수정): {e}")
                                    st.success(f"✅ {message}")
                                else:
                                    st.error(message)
                            except Exception as e:
                                # Phase 3: 에러 메시지 표준화
                                error_msg = handle_data_error("재료 수정", e)
                                st.error(error_msg)
                    
                    with col_cancel:
                        if st.button("❌ 취소", key=f"cancel_edit_{ingredient_name}"):
                            st.session_state[f'editing_{ingredient_name}'] = False
                            # 취소는 상태만 변경, rerun 없음
            
            # 삭제 확인 모드
            if st.session_state.get(f'deleting_{ingredient_name}', False):
                with st.expander(f"🗑️ {ingredient_name} 삭제 확인", expanded=True):
                    st.warning(f"⚠️ '{ingredient_name}' 재료를 삭제하시겠습니까?")
                    col_del, col_cancel_del = st.columns(2)
                    with col_del:
                        if st.button("✅ 삭제 확인", key=f"confirm_delete_{ingredient_name}", type="primary"):
                            try:
                                success, message, refs = delete_ingredient(ingredient_name)
                                if success:
                                    st.session_state[f'deleting_{ingredient_name}'] = False
                                    # 캐시만 클리어하고 rerun 없이 성공 메시지만 표시
                                    try:
                                        st.cache_data.clear()
                                    except Exception as e:
                                        logging.getLogger(__name__).warning(f"캐시 클리어 실패 (재료 삭제): {e}")
                                    st.success(f"✅ {message}")
                                else:
                                    st.error(message)
                                    if refs:
                                        st.info(f"**참조 정보:** {', '.join([f'{k}: {v}개' for k, v in refs.items()])}")
                            except Exception as e:
                                # Phase 3: 에러 메시지 표준화
                                error_msg = handle_data_error("재료 삭제", e)
                                st.error(error_msg)
                    
                    with col_cancel_del:
                        if st.button("❌ 취소", key=f"cancel_delete_{ingredient_name}"):
                            st.session_state[f'deleting_{ingredient_name}'] = False
                            # 취소는 상태만 변경, rerun 없음
            
            # 구분선
            st.markdown("<hr style='margin: 0.5rem 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
    else:
        st.info("등록된 재료가 없습니다.")


# Streamlit 멀티페이지에서 직접 실행될 때
# 주석 처리: app.py에서만 렌더되도록 함 (중복 호출 방지)
# render_ingredient_management()
