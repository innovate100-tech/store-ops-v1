"""
재료 구조 설계실 (원가 집중 · 대체재 · 발주 구조 전략화)
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
import logging
from src.ui_helpers import render_page_header, render_section_divider, safe_get_row_by_condition, handle_data_error
from src.ui import render_ingredient_input
from src.storage_supabase import load_csv, save_ingredient, update_ingredient, delete_ingredient, get_supabase_client, get_current_store_id
from ui_pages.design_lab.design_lab_frame import (
    render_coach_board,
    render_structure_map_container,
    render_school_cards,
    render_design_tools_container,
)
from ui_pages.design_lab.ingredient_structure_helpers import (
    calculate_ingredient_usage_cost,
    calculate_cost_concentration,
    identify_high_risk_ingredients,
    check_order_structure_status,
    get_ingredient_structure_verdict,
)

# 공통 설정 적용
bootstrap(page_title="Ingredient Management")


def _show_ingredient_query_diagnostics():
    """재료 등록 페이지에서 사용하는 실제 쿼리 정보 출력"""
    try:
        from src.auth import get_current_store_id
        from src.storage_supabase import get_read_client
        
        store_id = get_current_store_id()
        
        # 현재 클라이언트 모드 및 토큰 상태 표시 (항상 표시)
        from src.auth import get_read_client_mode
        client_mode = get_read_client_mode()
        has_token = 'access_token' in st.session_state and bool(st.session_state.get('access_token'))
        has_user_id = 'user_id' in st.session_state and bool(st.session_state.get('user_id'))
        is_dev = st.session_state.get('dev_mode', False)
        
        st.write("**🔐 인증 상태 (항상 표시):**")
        st.write(f"- **클라이언트 모드:** `{client_mode}`")
        st.write(f"- **토큰 존재:** {has_token}")
        st.write(f"- **User ID 존재:** {has_user_id}")
        st.write(f"- **DEV MODE:** {is_dev}")
        
        if client_mode == "anon" and not is_dev:
            st.error("❌ **경고:** 온라인 환경에서 anon 클라이언트를 사용 중입니다. 로그인 상태를 확인하세요.")
        elif client_mode == "auth":
            st.success("✅ **정상:** Auth 클라이언트를 사용 중입니다.")
        elif client_mode == "service_role_dev":
            st.warning("⚠️ **DEV MODE:** Service Role 클라이언트를 사용 중입니다 (RLS 우회).")
        
        st.divider()
        st.write(f"**사용된 store_id:** `{store_id}`")
        
        st.divider()
        st.write("**테이블명 매핑 확인:**")
        
        # 테이블명 매핑 정보 표시
        table_mapping = {
            'ingredient_master.csv': 'ingredients',
            'menu_master.csv': 'menu_master',
            'recipes.csv': 'recipes',
            'inventory.csv': 'inventory',
            'targets.csv': 'targets',
            'sales.csv': 'sales',
            'actual_settlement.csv': 'actual_settlement',
        }
        st.write(f"**앱에서 사용하는 매핑:** `ingredient_master.csv` → `{table_mapping.get('ingredient_master.csv', 'N/A')}`")
        
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
        supabase = None
        result_no_filter = None
        try:
            supabase = get_read_client()
            if supabase:
                # 필터 없이 조회
                try:
                    result_no_filter = supabase.table("ingredients").select("*").limit(10).execute()
                    st.write(f"- 필터 없이 Row count: {len(result_no_filter.data) if result_no_filter.data else 0}")
                    
                    if result_no_filter.data:
                        # store_id 목록 확인
                        store_ids = set([row.get('store_id') for row in result_no_filter.data if row.get('store_id')])
                        st.write(f"- 발견된 store_id 목록: {list(store_ids)}")
                        st.write("- 첫 row 샘플:")
                        st.json(result_no_filter.data[0])
                    else:
                        st.warning("⚠️ 필터 없이 조회해도 데이터가 없습니다.")
                except Exception as e:
                    error_msg = str(e)
                    st.error(f"❌ 필터 없이 조회 실패: {type(e).__name__}: {error_msg}")
                    st.code(str(e), language="text")
                    
                    # 테이블명 오류 확인
                    if "relation" in error_msg.lower() or "does not exist" in error_msg.lower() or "table" in error_msg.lower():
                        st.error("🚨 테이블명 불일치 가능성!")
                        st.warning(f"💡 `ingredients` 테이블이 존재하지 않을 수 있습니다.")
                        st.info("**확인 사항:**")
                        st.info("1. Supabase Dashboard에서 실제 테이블명 확인")
                        st.info("2. 테이블명이 `ingredients`가 아닐 수 있음 (예: `ingredient`, `ingredient_master` 등)")
                        st.info("3. `src/storage_supabase.py`의 `table_mapping`에서 매핑 확인")
                
                st.divider()
                
                # store_id 필터로 조회
                if store_id:
                    st.write(f"**3. 직접 Supabase 쿼리 (ingredients 테이블, store_id={store_id}):**")
                    try:
                        result_with_filter = supabase.table("ingredients").select("*").eq("store_id", store_id).limit(10).execute()
                        st.write(f"- Row count: {len(result_with_filter.data) if result_with_filter.data else 0}")
                        st.write(f"- 쿼리 조건: `table('ingredients').select('*').eq('store_id', '{store_id}')`")
                        
                        if result_with_filter.data:
                            st.write("- 첫 row 샘플:")
                            st.json(result_with_filter.data[0])
                        else:
                            st.warning("⚠️ store_id 필터로 조회한 데이터가 비어있습니다.")
                            
                            # store_id가 다른 데이터가 있는지 확인
                            if result_no_filter and result_no_filter.data:
                                st.warning(f"⚠️ 테이블에는 데이터가 있지만, store_id=`{store_id}` 조건으로는 조회되지 않습니다.")
                                st.info("💡 가능한 원인:")
                                st.info("1. RLS 정책 문제")
                                st.info("2. store_id 불일치 (데이터는 다른 store_id로 저장됨)")
                                st.info("3. 로그인 사용자의 권한 문제")
                    except Exception as e:
                        st.error(f"❌ store_id 필터 조회 실패: {type(e).__name__}: {str(e)}")
                        st.code(str(e), language="text")
                else:
                    st.error("❌ store_id가 없어서 필터 쿼리를 실행할 수 없습니다.")
            else:
                st.error("❌ Supabase 클라이언트를 생성할 수 없습니다.")
        except Exception as e:
            st.error(f"❌ 에러: {type(e).__name__}: {str(e)}")
            st.code(str(e), language="text")
            st.exception(e)
        
        st.divider()
        
        # 4. 다른 테이블로 비교 테스트 (menu_master)
        st.write("**4. 비교 테스트: menu_master 테이블 조회:**")
        try:
            if supabase and store_id:
                # menu_master도 같은 방식으로 조회
                menu_result = supabase.table("menu_master").select("*").eq("store_id", store_id).limit(5).execute()
                st.write(f"- menu_master Row count: {len(menu_result.data) if menu_result.data else 0}")
                
                if menu_result.data:
                    st.success("✅ menu_master는 조회 성공!")
                    st.write("- menu_master 샘플:")
                    st.json(menu_result.data[0])
                    st.info("💡 menu_master는 조회되는데 ingredients는 안 되면, ingredients 테이블명 불일치 또는 RLS 정책 문제일 수 있습니다.")
                else:
                    st.warning("⚠️ menu_master도 조회되지 않습니다. 전체적인 RLS 정책 문제일 수 있습니다.")
        except Exception as e:
            error_msg = str(e)
            st.error(f"❌ 비교 테스트 실패: {type(e).__name__}: {error_msg}")
            st.code(str(e), language="text")
            
            # 테이블명 오류 확인
            if "relation" in error_msg.lower() or "does not exist" in error_msg.lower():
                st.error("🚨 menu_master 테이블도 존재하지 않을 수 있습니다!")
        
        st.divider()
        
        # 5. 인증 토큰 및 클라이언트 상태 확인
        st.write("**5. 인증 토큰 및 클라이언트 상태 확인:**")
        try:
            from src.auth import get_read_client_mode, get_auth_client
            
            # 토큰 상태 확인
            has_access_token = 'access_token' in st.session_state and bool(st.session_state.get('access_token'))
            has_refresh_token = 'refresh_token' in st.session_state and bool(st.session_state.get('refresh_token'))
            has_user_id = 'user_id' in st.session_state and bool(st.session_state.get('user_id'))
            
            st.write(f"- `access_token` 존재: {has_access_token}")
            st.write(f"- `refresh_token` 존재: {has_refresh_token}")
            st.write(f"- `user_id` 존재: {has_user_id}")
            
            if has_access_token:
                token_preview = str(st.session_state.access_token)[:20] + "..." if len(str(st.session_state.access_token)) > 20 else str(st.session_state.access_token)
                st.write(f"- `access_token` 미리보기: `{token_preview}`")
            
            # 클라이언트 모드 확인
            client_mode = get_read_client_mode()
            st.write(f"- **현재 클라이언트 모드:** `{client_mode}`")
            
            if client_mode == "anon":
                st.warning("⚠️ Anon Client를 사용 중입니다. 로그인 토큰이 설정되지 않았을 수 있습니다.")
                if not has_access_token:
                    st.error("❌ `access_token`이 없습니다. 로그인 상태를 확인하세요.")
                else:
                    st.warning("💡 `access_token`은 있지만 `get_read_client()`가 Anon Client를 반환했습니다.")
                    st.info("**가능한 원인:**")
                    st.info("1. `get_read_client()`의 캐시 문제 (토큰 설정 전에 캐시됨)")
                    st.info("2. `get_auth_client()` 호출 실패")
            
            # Auth Client 직접 테스트
            st.divider()
            st.write("**6. Auth Client 직접 테스트:**")
            try:
                auth_client = get_auth_client(reset_session_on_fail=False)
                if auth_client:
                    # Auth Client로 ingredients 조회 테스트
                    auth_result = auth_client.table("ingredients").select("*").eq("store_id", store_id).limit(5).execute()
                    st.write(f"- Auth Client로 조회한 Row count: {len(auth_result.data) if auth_result.data else 0}")
                    
                    if auth_result.data:
                        st.success("✅ **Auth Client로는 데이터 조회 성공!**")
                        st.write("- 샘플 데이터:")
                        st.json(auth_result.data[0])
                        st.warning("💡 `get_read_client()`가 Anon Client를 반환하는 것이 문제입니다.")
                        st.info("**해결 방법:**")
                        st.info("1. `get_read_client()`의 캐시를 초기화하거나")
                        st.info("2. `storage_supabase.py`에서 `get_auth_client()`를 직접 사용")
                    else:
                        st.warning("⚠️ Auth Client로도 데이터가 조회되지 않습니다.")
            except Exception as e:
                st.error(f"❌ Auth Client 테스트 실패: {type(e).__name__}: {str(e)}")
                st.code(str(e), language="text")
            
        except Exception as e:
            st.error(f"❌ 인증 상태 확인 실패: {type(e).__name__}: {str(e)}")
            st.code(str(e), language="text")
        
        st.divider()
        
        # 7. 대체 테이블명 시도 (테이블명 불일치 확인)
        st.write("**7. 대체 테이블명 테스트 (테이블명 불일치 확인):**")
        if supabase and store_id:
            alternative_table_names = ['ingredient', 'ingredient_master', 'ingredients_master']
            for alt_name in alternative_table_names:
                try:
                    alt_result = supabase.table(alt_name).select("*").eq("store_id", store_id).limit(1).execute()
                    if alt_result.data and len(alt_result.data) > 0:
                        st.success(f"✅ **`{alt_name}` 테이블 발견!** (데이터 {len(alt_result.data)}건)")
                        st.warning(f"💡 실제 테이블명이 `{alt_name}`일 수 있습니다. `src/storage_supabase.py`의 `table_mapping`을 확인하세요.")
                        st.write(f"- 샘플 데이터:")
                        st.json(alt_result.data[0])
                        break
                except Exception as e:
                    error_msg = str(e)
                    if "relation" in error_msg.lower() or "does not exist" in error_msg.lower():
                        st.write(f"- `{alt_name}`: 테이블 없음")
                    else:
                        st.write(f"- `{alt_name}`: 에러 - {type(e).__name__}")
            
    except Exception as e:
        st.error(f"진단 중 오류 발생: {type(e).__name__}: {str(e)}")
        st.exception(e)


def render_ingredient_management():
    """재료 구조 설계실 페이지 렌더링 (Design Lab 공통 프레임 적용)"""
    render_page_header("재료 구조 설계실 (원가 집중 · 대체재 · 발주 구조)", "🥬")
    
    # 공통 네비게이션 버튼
    from ui_pages.design_lab.design_lab_nav import render_back_to_design_center_button
    render_back_to_design_center_button()
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    # 데이터 로드
    ingredient_df = load_csv('ingredient_master.csv', store_id=store_id, default_columns=['재료명', '단위', '단가'])
    ingredient_usage_df = calculate_ingredient_usage_cost(store_id)
    
    # 집중도 계산
    top3_concentration, top5_concentration = calculate_cost_concentration(ingredient_usage_df)
    
    # 고위험 재료 판별
    high_risk_df = identify_high_risk_ingredients(ingredient_usage_df, cost_threshold=20.0, menu_threshold=3)
    
    # 발주 구조 상태
    order_status, order_reason = check_order_structure_status(store_id)
    
    # ZONE A: Coach Board (Ingredient Structure Verdict)
    cards = []
    
    # 1) 총 재료 수
    ingredient_count = len(ingredient_df) if not ingredient_df.empty else 0
    cards.append({
        "title": "총 재료 수",
        "value": f"{ingredient_count}개",
        "subtitle": None
    })
    
    # 2) 원가 TOP3 집중도
    cards.append({
        "title": "원가 TOP3 집중도",
        "value": f"{top3_concentration:.1f}%",
        "subtitle": "⚠️ 70% 이상 위험" if top3_concentration >= 70 else "✅ 안정" if top3_concentration < 50 else "⚠️ 주의"
    })
    
    # 3) 고위험 재료 수
    high_risk_count = len(high_risk_df) if not high_risk_df.empty else 0
    risk_emoji = "🔴" if high_risk_count > 0 else "✅"
    cards.append({
        "title": "고위험 재료 수",
        "value": f"{high_risk_count}개",
        "subtitle": f"{risk_emoji} 원가 20%+ & 메뉴 3개+"
    })
    
    # 4) 발주 구조 상태
    status_emoji = "✅" if order_status == "안전" else "⚠️" if order_status == "주의" else "🔴"
    cards.append({
        "title": "발주 구조 상태",
        "value": order_status,
        "subtitle": f"{status_emoji} {order_reason}"
    })
    
    # 판결문 + 추천 액션
    verdict_text, action_title, action_target_page = get_ingredient_structure_verdict(
        store_id, ingredient_usage_df, high_risk_df, top3_concentration
    )
    
    # 전략 브리핑 / 전략 실행 탭 분리
    # session_state로 초기 탭 제어
    initial_tab_key = f"_initial_tab_재료 등록"
    should_show_execute_first = st.session_state.get(initial_tab_key) == "execute"
    
    if should_show_execute_first:
        tab1, tab2 = st.tabs(["🛠️ 전략 실행", "📊 전략 브리핑"])
        st.session_state.pop(initial_tab_key, None)
        execute_tab = tab1
        briefing_tab = tab2
    else:
        tab1, tab2 = st.tabs(["📊 전략 브리핑", "🛠️ 전략 실행"])
        briefing_tab = tab1
        execute_tab = tab2
    
    with briefing_tab:
        # ZONE A: Coach Board
        render_coach_board(
            cards=cards,
            verdict_text=verdict_text,
            action_title=action_title,
            action_reason=None,
            action_target_page=action_target_page,
            action_button_label=f"{action_title} 하러가기" if action_title else None
        )
        
        def _render_ingredient_structure_map():
            if ingredient_usage_df.empty:
                st.info("재료가 등록되지 않았습니다. 재료를 등록하면 구조 맵이 표시됩니다.")
                return
            
            # 1) 재료 원가 집중도 Pareto 차트
            st.markdown("#### 📊 재료 원가 집중도 (Pareto)")
            
            # 누적 비율 계산
            cumulative_pct = []
            cumulative_cost = 0.0
            total_cost = ingredient_usage_df['총_사용금액'].sum()
            
            for _, row in ingredient_usage_df.iterrows():
                cumulative_cost += row['총_사용금액']
                cumulative_pct.append((cumulative_cost / total_cost * 100) if total_cost > 0 else 0.0)
            
            pareto_df = ingredient_usage_df.copy()
            pareto_df['누적_비율_%'] = cumulative_pct
            
            # 차트 데이터 준비 (상위 10개)
            chart_df = pareto_df.head(10)[['재료명', '누적_비율_%']].copy()
            chart_df = chart_df.set_index('재료명')
            
            st.bar_chart(chart_df)
            
            # 70%, 90% 기준선 표시
            st.caption("📌 기준선: 70% (위험), 90% (매우 위험)")
            
            # 2) 재료 영향도 테이블
            st.markdown("#### 📋 재료 영향도 테이블")
            
            display_df = ingredient_usage_df[['재료명', '총_사용금액', '원가_비중_%', '연결_메뉴_수']].copy()
            display_df['총_사용금액'] = display_df['총_사용금액'].apply(lambda x: f"{x:,.0f}원")
            display_df['원가_비중_%'] = display_df['원가_비중_%'].apply(lambda x: f"{x:.1f}%")
            
            # 위험도 자동 판정
            def get_risk_level(row):
                if row['원가_비중_%'] >= 20 and row['연결_메뉴_수'] >= 3:
                    return "🔴 고위험"
                elif row['원가_비중_%'] >= 10:
                    return "⚠️ 주의"
                else:
                    return "✅ 안전"
            
            display_df['위험도'] = ingredient_usage_df.apply(get_risk_level, axis=1)
            display_df.columns = ['재료명', '총 사용금액', '원가 비중', '연결 메뉴 수', '위험도']
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        render_structure_map_container(
            content_func=_render_ingredient_structure_map,
            empty_message="재료가 등록되지 않았습니다.",
            empty_action_label="재료 등록하기",
            empty_action_page="재료 등록"
        )
        
        # ZONE C: Owner School (Ingredient Structure Theory)
        school_cards = [
        {
            "title": "원가는 \"비율\"이 아니라 \"집중도\"로 무너진다",
            "point1": "개별 재료의 원가율보다 상위 재료의 집중도가 더 위험합니다",
            "point2": "TOP 3 재료가 70% 이상이면 가격 변동에 매우 취약합니다"
        },
        {
            "title": "대체 불가능 재료는 사업 리스크다",
            "point1": "여러 메뉴에 동시에 사용되는 재료는 대체재를 미리 준비하세요",
            "point2": "연결 메뉴 3개 이상 + 원가 비중 20% 이상 = 고위험 재료"
        },
        {
            "title": "발주는 비용이 아니라 구조다",
            "point1": "단일 공급업체 의존은 공급 리스크를 높입니다",
            "point2": "발주 단위와 변환 비율을 정확히 설정하면 원가 계산이 정확해집니다"
        },
        ]
        render_school_cards(school_cards)
    
    with execute_tab:
        # ZONE D: Design Tools (Ingredient Strategy Tools)
        render_design_tools_container(lambda: _render_ingredient_strategy_tools(store_id, ingredient_usage_df, high_risk_df))


def _render_ingredient_strategy_tools(store_id: str, ingredient_usage_df: pd.DataFrame, high_risk_df: pd.DataFrame):
    """ZONE D: 재료 구조 전략 도구"""
    
    # 재료명 -> ingredient_id 매핑 생성
    from src.storage_supabase import load_csv
    ingredient_df = load_csv('ingredient_master.csv', store_id=store_id, default_columns=['재료명', '단위', '단가'])
    ingredient_id_map = {}
    if not ingredient_df.empty and 'id' in ingredient_df.columns:
        for _, row in ingredient_df.iterrows():
            ingredient_name = row.get('재료명', '')
            ingredient_id = row.get('id', '')
            if ingredient_name and ingredient_id:
                ingredient_id_map[ingredient_name] = ingredient_id
    
    # DB에서 재료 설계 상태 로드
    from src.storage_supabase import load_ingredient_structure_state
    db_states_by_id = load_ingredient_structure_state(store_id)
    ingredient_name_map = {v: k for k, v in ingredient_id_map.items()}  # 역매핑
    
    # DB 상태를 재료명 기준으로 변환
    db_states = {}
    for ingredient_id, state in db_states_by_id.items():
        ingredient_name = ingredient_name_map.get(ingredient_id)
        if ingredient_name:
            db_states[ingredient_name] = state
    
    # 1) 고위험 재료 테이블 (핵심)
    st.markdown("#### 🔴 고위험 재료 테이블")
    
    if high_risk_df.empty:
        st.info("고위험 재료가 없습니다. ✅")
    else:
        # 필터 옵션
        filter_option = st.radio(
            "필터",
            ["전체", "원가 비중 순", "연결 메뉴 수 순"],
            horizontal=True,
            key="ingredient_risk_filter"
        )
        
        display_risk_df = high_risk_df.copy()
        
        if filter_option == "원가 비중 순":
            display_risk_df = display_risk_df.sort_values('원가_비중_%', ascending=False)
        elif filter_option == "연결 메뉴 수 순":
            display_risk_df = display_risk_df.sort_values('연결_메뉴_수', ascending=False)
        
        # 테이블 표시
        for idx, row in display_risk_df.iterrows():
            ingredient_name = row['재료명']
            ingredient_id = ingredient_id_map.get(ingredient_name)
            
            # DB에서 초기값 로드 (없으면 기본값)
            db_state = db_states.get(ingredient_name, {})
            default_replaceable = db_state.get('is_substitutable', False)
            default_order_type = db_state.get('order_type', 'unset')
            
            # order_type 변환 (영문 -> 한글)
            if default_order_type == 'single':
                default_order_type = '단일'
            elif default_order_type == 'multi':
                default_order_type = '복수'
            else:
                default_order_type = '미설정'
            
            with st.expander(f"🔴 {ingredient_name} - 위험도: {row['위험_사유']}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**원가 비중:** {row['원가_비중_%']:.1f}%")
                    st.write(f"**총 사용금액:** {row['총_사용금액']:,.0f}원")
                
                with col2:
                    st.write(f"**연결 메뉴 수:** {row['연결_메뉴_수']}개")
                    st.write(f"**연결 메뉴:** {row['연결_메뉴_목록']}")
                
                # 대체 가능 여부 (DB 우선)
                new_replaceable = st.checkbox(
                    "대체 가능",
                    value=default_replaceable,
                    key=f"replaceable_{ingredient_name}"
                )
                
                # 발주 유형 (DB 우선)
                new_order_type = st.selectbox(
                    "발주 유형",
                    ["미설정", "단일", "복수"],
                    index=["미설정", "단일", "복수"].index(default_order_type) if default_order_type in ["미설정", "단일", "복수"] else 0,
                    key=f"order_type_{ingredient_name}"
                )
                
                # 변경 감지 및 DB 저장
                if ingredient_id:
                    from src.storage_supabase import upsert_ingredient_structure_state
                    from src.auth import is_dev_mode
                    
                    # 값이 변경되었는지 확인
                    if new_replaceable != default_replaceable or new_order_type != default_order_type:
                        # order_type 변환 (한글 -> 영문)
                        order_type_db = None
                        if new_order_type == '단일':
                            order_type_db = 'single'
                        elif new_order_type == '복수':
                            order_type_db = 'multi'
                        elif new_order_type == '미설정':
                            order_type_db = 'unset'
                        
                        success = upsert_ingredient_structure_state(
                            store_id,
                            ingredient_id,
                            is_substitutable=new_replaceable,
                            order_type=order_type_db
                        )
                        
                        if success:
                            # 성공 시 session_state 캐시 업데이트
                            cache_key = f"ingredient_structure_state::{store_id}"
                            if cache_key not in st.session_state:
                                st.session_state[cache_key] = {}
                            if ingredient_name not in st.session_state[cache_key]:
                                st.session_state[cache_key][ingredient_name] = {}
                            st.session_state[cache_key][ingredient_name]['is_substitutable'] = new_replaceable
                            st.session_state[cache_key][ingredient_name]['order_type'] = new_order_type
                        elif is_dev_mode():
                            st.warning(f"DB 저장 실패: {ingredient_name}")
                else:
                    # ingredient_id를 찾을 수 없으면 session_state만 저장 (폴백)
                    replaceable_key = f"ingredient_replaceable::{store_id}::{ingredient_name}"
                    order_type_key = f"ingredient_order_type::{store_id}::{ingredient_name}"
                    st.session_state[replaceable_key] = new_replaceable
                    st.session_state[order_type_key] = new_order_type
                    if is_dev_mode():
                        st.warning(f"재료 ID를 찾을 수 없어 session_state에만 저장했습니다: {ingredient_name}")
    
    render_section_divider()
    
    # 2) 대체 구조 설계 패널
    st.markdown("#### 🔄 대체 구조 설계")
    
    if ingredient_usage_df.empty:
        st.info("재료가 등록되지 않았습니다.")
    else:
        selected_ingredient = st.selectbox(
            "대체 구조를 설계할 재료 선택",
            ["선택하세요"] + ingredient_usage_df['재료명'].tolist(),
            key="ingredient_replacement_select"
        )
        
        if selected_ingredient != "선택하세요":
            # 선택된 재료 정보
            selected_row = ingredient_usage_df[ingredient_usage_df['재료명'] == selected_ingredient].iloc[0]
            
            st.markdown(f"**재료:** {selected_ingredient}")
            st.markdown(f"**원가 비중:** {selected_row['원가_비중_%']:.1f}%")
            st.markdown(f"**연결 메뉴 수:** {selected_row['연결_메뉴_수']}개")
            
            # 연결된 메뉴 리스트
            st.markdown("**이 재료가 빠지면 영향받는 메뉴:**")
            menu_list = selected_row['연결_메뉴_목록'].split(', ')
            for menu in menu_list:
                st.write(f"- {menu}")
            
            # DB에서 메모 초기값 로드
            selected_ingredient_id = ingredient_id_map.get(selected_ingredient)
            selected_db_state = db_states.get(selected_ingredient, {})
            default_substitute_memo = selected_db_state.get('substitute_memo', '')
            default_strategy_memo = selected_db_state.get('strategy_memo', '')
            
            # 대체 가능 재료 메모
            new_substitute_memo = st.text_area(
                "대체 가능 재료 메모",
                value=default_substitute_memo,
                key=f"replacement_memo_{selected_ingredient}",
                placeholder="예: 돼지고기 → 닭고기, 소고기 → 돼지고기 등"
            )
            
            # 구조 전략 메모
            new_strategy_memo = st.text_area(
                "구조 전략 메모",
                value=default_strategy_memo,
                key=f"strategy_memo_{selected_ingredient}",
                placeholder="예: 공급업체 다변화 필요, 계절별 대체재 확보 등"
            )
            
            # 저장 버튼
            if st.button("메모 저장", key=f"save_memo_{selected_ingredient}"):
                if selected_ingredient_id:
                    from src.storage_supabase import upsert_ingredient_structure_state
                    success = upsert_ingredient_structure_state(
                        store_id,
                        selected_ingredient_id,
                        substitute_memo=new_substitute_memo if new_substitute_memo else None,
                        strategy_memo=new_strategy_memo if new_strategy_memo else None
                    )
                    if success:
                        st.success("메모가 저장되었습니다.")
                        st.rerun()
                    else:
                        st.error("메모 저장에 실패했습니다.")
                else:
                    st.warning(f"재료 ID를 찾을 수 없습니다: {selected_ingredient}")
    
    render_section_divider()
    
    # 3) 기존 재료 관리 기능 (하단 유지)
    st.markdown("#### 📝 재료 등록/수정/삭제")
    _render_ingredient_management_tools()


def _render_ingredient_management_tools():
    """기존 재료 등록/수정/삭제 기능"""
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
