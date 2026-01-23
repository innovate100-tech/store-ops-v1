"""
대시보드 진단 기능
"""
import streamlit as st
from src.storage_supabase import load_csv, load_expense_structure, get_read_client
from src.utils.time_utils import current_year_kst, current_month_kst


def _show_query_diagnostics():
    """대시보드 페이지에서 사용하는 실제 쿼리 정보 출력"""
    try:
        from src.auth import get_current_store_id
        
        store_id = get_current_store_id()
        st.write(f"**사용된 store_id:** `{store_id}`")
        
        # store_id 출처 확인
        st.write("**store_id 출처 확인:**")
        st.write(f"- `get_current_store_id()`: `{store_id}`")
        st.write(f"- `st.session_state.get('_active_store_id')`: `{st.session_state.get('_active_store_id', 'N/A')}`")
        st.write(f"- `st.session_state.get('store_id')`: `{st.session_state.get('store_id', 'N/A')}`")
        
        current_year = current_year_kst()
        current_month = current_month_kst()
        st.write(f"**필터 값:** 연도={current_year}, 월={current_month}")
        
        st.divider()
        st.write("**실제 쿼리 실행 결과:**")
        
        # 1. load_csv 호출 테스트 (menu_master)
        st.write("**1. load_csv('menu_master.csv') 호출 결과:**")
        try:
            menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
            st.write(f"- Row count: {len(menu_df)}")
            st.write(f"- DataFrame columns: {list(menu_df.columns)}")
            if not menu_df.empty:
                st.write("- 첫 row 샘플:")
                from src.ui_helpers import safe_get_first_row
                first_row = safe_get_first_row(menu_df)
                if first_row is not None and not first_row.empty:
                    st.json(first_row.to_dict())
                else:
                    st.warning("⚠️ 첫 번째 행을 가져올 수 없습니다.")
            else:
                st.warning("⚠️ 데이터가 비어있습니다.")
        except Exception as e:
            st.error(f"❌ 에러: {type(e).__name__}: {str(e)}")
            st.code(str(e), language="text")
            st.exception(e)
        
        st.divider()
        
        # 2. 직접 Supabase 쿼리 테스트 (store_id 필터 없이)
        st.write("**2. 직접 Supabase 쿼리 (menu_master, store_id 필터 없이):**")
        try:
            supabase = get_read_client()
            if supabase:
                # 필터 없이 조회 (RLS 정책 확인용)
                result_no_filter = supabase.table("menu_master").select("*").limit(5).execute()
                st.write(f"- 필터 없이 Row count: {len(result_no_filter.data) if result_no_filter.data else 0}")
                
                # store_id 필터로 조회
                if store_id:
                    result_with_filter = supabase.table("menu_master").select("*").eq("store_id", store_id).limit(5).execute()
                    st.write(f"- store_id={store_id} 필터 Row count: {len(result_with_filter.data) if result_with_filter.data else 0}")
                    st.write(f"- 쿼리 조건: `table('menu_master').select('*').eq('store_id', '{store_id}')`")
                    
                    if result_with_filter.data:
                        st.write("- 첫 row 샘플:")
                        st.json(result_with_filter.data[0])
                    else:
                        st.warning("⚠️ store_id 필터로 조회한 데이터가 비어있습니다.")
                        
                        # store_id가 다른 데이터가 있는지 확인
                        if result_no_filter.data:
                            st.write("**다른 store_id 데이터 확인:**")
                            sample_store_ids = set([row.get('store_id') for row in result_no_filter.data[:5] if row.get('store_id')])
                            st.write(f"- 발견된 store_id 목록: {list(sample_store_ids)}")
                            st.warning(f"⚠️ 현재 store_id(`{store_id}`)와 다른 store_id가 발견되었습니다!")
                else:
                    st.error("❌ store_id가 없어서 필터 쿼리를 실행할 수 없습니다.")
            else:
                st.error("❌ Supabase 클라이언트를 생성할 수 없습니다.")
        except Exception as e:
            st.error(f"❌ 에러: {type(e).__name__}: {str(e)}")
            st.code(str(e), language="text")
            st.exception(e)
        
        st.divider()
        
        # 3. load_expense_structure 호출 테스트
        st.write("**3. load_expense_structure 호출 결과:**")
        try:
            expense_df = load_expense_structure(current_year, current_month)
            st.write(f"- Row count: {len(expense_df)}")
            if not expense_df.empty:
                st.write("- 첫 row 샘플:")
                from src.ui_helpers import safe_get_first_row
                first_row = safe_get_first_row(expense_df)
                if first_row is not None and not first_row.empty:
                    st.json(first_row.to_dict())
                else:
                    st.warning("⚠️ 첫 번째 행을 가져올 수 없습니다.")
            else:
                st.warning("⚠️ 데이터가 비어있습니다.")
        except Exception as e:
            st.error(f"❌ 에러: {type(e).__name__}: {str(e)}")
            st.code(str(e), language="text")
            st.exception(e)
        
        st.divider()
        
        # 4. targets 테이블 조회
        st.write("**4. targets 테이블 조회:**")
        try:
            targets_df = load_csv('targets.csv', default_columns=[
                '연도', '월', '목표매출', '목표원가율', '목표인건비율',
                '목표임대료율', '목표기타비용율', '목표순이익률'
            ])
            filtered_df = targets_df[(targets_df['연도'] == current_year) & (targets_df['월'] == current_month)]
            st.write(f"- 전체 Row count: {len(targets_df)}")
            st.write(f"- 필터링 후 Row count (연도={current_year}, 월={current_month}): {len(filtered_df)}")
            if not filtered_df.empty:
                st.write("- 첫 row 샘플:")
                from src.ui_helpers import safe_get_first_row
                first_row = safe_get_first_row(filtered_df)
                if first_row is not None and not first_row.empty:
                    st.json(first_row.to_dict())
                else:
                    st.warning("⚠️ 첫 번째 행을 가져올 수 없습니다.")
            else:
                st.warning("⚠️ 필터링된 데이터가 비어있습니다.")
        except Exception as e:
            st.error(f"❌ 에러: {type(e).__name__}: {str(e)}")
            st.code(str(e), language="text")
            st.exception(e)
            
    except Exception as e:
        st.error(f"진단 중 오류 발생: {type(e).__name__}: {str(e)}")
        st.exception(e)


def _render_dashboard_diagnostics(ctx):
    """대시보드 진단 정보 렌더링"""
    with st.expander("🔍 쿼리 진단 정보 (DEV)", expanded=False):
        _show_query_diagnostics()
    
    # dev_mode에서 store_id 표시 (선택)
    try:
        from src.auth import is_dev_mode
        if is_dev_mode():
            store_id_debug = ctx['store_id'] or "default"
            with st.sidebar.expander("🔧 디버그 정보", expanded=False):
                st.caption(f"store_id: {store_id_debug}")
    except Exception:
        pass
