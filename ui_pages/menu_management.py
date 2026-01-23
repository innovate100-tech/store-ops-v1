"""
메뉴 포트폴리오 설계실
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
import logging
from src.ui_helpers import render_page_header, render_section_divider, safe_get_row_by_condition, handle_data_error
from src.ui import render_menu_input, render_menu_batch_input
from src.storage_supabase import load_csv, save_menu, update_menu, update_menu_category, delete_menu
from ui_pages.design_lab.design_lab_frame import (
    render_coach_board,
    render_structure_map_container,
    render_school_cards,
    render_design_tools_container,
)
from ui_pages.design_lab.menu_portfolio_helpers import (
    get_menu_portfolio_tags,
    set_menu_portfolio_tag,
    get_menu_portfolio_categories,
    set_menu_portfolio_category,
    calculate_portfolio_balance_score,
    get_portfolio_verdict,
)
from typing import Dict
from src.auth import get_current_store_id

# 공통 설정 적용
bootstrap(page_title="Menu Management")


def render_menu_management():
    """메뉴 포트폴리오 설계실 페이지 렌더링 (Design Lab 공통 프레임 적용)"""
    render_page_header("메뉴 포트폴리오 설계실", "🍽️")
    
    # 공통 네비게이션 버튼
    from ui_pages.design_lab.design_lab_nav import render_back_to_design_center_button
    render_back_to_design_center_button()
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다.")
        return
    
    # 데이터 로드
    menu_df = load_csv('menu_master.csv', store_id=store_id, default_columns=['메뉴명', '판매가'])
    roles = get_menu_portfolio_tags(store_id)
    categories = get_menu_portfolio_categories(store_id)
    
    # ZONE A: Coach Board (Portfolio Verdict)
    cards = []
    
    # 1) 총 메뉴 수
    menu_count = len(menu_df) if not menu_df.empty else 0
    cards.append({
        "title": "총 메뉴 수",
        "value": f"{menu_count}개",
        "subtitle": None
    })
    
    # 2) 평균 가격
    if not menu_df.empty and '판매가' in menu_df.columns:
        avg_price = menu_df['판매가'].mean()
        cards.append({
            "title": "평균 가격",
            "value": f"{int(avg_price):,}원",
            "subtitle": None
        })
    else:
        avg_price = 0
    
    # 3) 포트폴리오 균형 점수
    balance_score, balance_status = calculate_portfolio_balance_score(menu_df, roles, categories)
    status_emoji = "✅" if balance_status == "균형" else "⚠️" if balance_status == "주의" else "🔴"
    cards.append({
        "title": "포트폴리오 균형",
        "value": f"{balance_score}점",
        "subtitle": f"{status_emoji} {balance_status}"
    })
    
    # 4) 역할 분포 요약
    role_counts = {"미끼": 0, "볼륨": 0, "마진": 0, "미분류": 0}
    for menu_name in menu_df['메뉴명'].tolist() if not menu_df.empty else []:
        role = roles.get(menu_name, "미분류")
        if role in role_counts:
            role_counts[role] += 1
        else:
            role_counts["미분류"] += 1
    
    role_summary = f"미끼 {role_counts['미끼']} / 볼륨 {role_counts['볼륨']} / 마진 {role_counts['마진']}"
    if role_counts['미분류'] > 0:
        role_summary += f" (미분류 {role_counts['미분류']})"
    cards.append({
        "title": "역할 분포",
        "value": role_summary,
        "subtitle": None
    })
    
    # 판결문 + 추천 액션
    verdict_text, action_title, action_target_page = get_portfolio_verdict(menu_df, roles, categories, avg_price)
    
    # 전략 브리핑 / 전략 실행 탭 분리
    tab1, tab2 = st.tabs(["📊 전략 브리핑", "🛠️ 전략 실행"])
    
    with tab1:
        # ZONE A: Coach Board
        render_coach_board(
            cards=cards,
            verdict_text=verdict_text,
            action_title=action_title,
            action_reason=None,
            action_target_page=action_target_page,
            action_button_label=f"{action_title} 하러가기" if action_title else None
        )
        
        # ZONE B: Structure Map (Portfolio Map)
        def _render_menu_portfolio_map():
            if menu_df.empty:
                st.info("메뉴가 등록되지 않았습니다. 메뉴를 등록하면 포트폴리오 맵이 표시됩니다.")
                return
            
            # A) 가격대 분포
            st.markdown("#### 💰 가격대 분포")
            if '판매가' in menu_df.columns:
                # 1만원 단위로 구간 나누기
                menu_df['가격대'] = (menu_df['판매가'] / 10000).astype(int) * 10000
                price_dist = menu_df['가격대'].value_counts().sort_index()
                if not price_dist.empty:
                    st.bar_chart(price_dist)
            
            # B) 역할 x 카테고리 매트릭스
            st.markdown("#### 📊 역할 x 카테고리 매트릭스")
            
            # 매트릭스 생성
            role_list = ["미끼", "볼륨", "마진", "미분류"]
            category_list = ["대표메뉴", "주력메뉴", "유인메뉴", "보조메뉴", "기타메뉴"]
            
            matrix_data = []
            for role in role_list:
                row = {"역할": role}
                for category in category_list:
                    count = 0
                    for menu_name in menu_df['메뉴명'].tolist():
                        menu_role = roles.get(menu_name, "미분류")
                        menu_category = categories.get(menu_name, "기타메뉴")
                        if menu_role == role and menu_category == category:
                            count += 1
                    row[category] = count
                matrix_data.append(row)
            
            matrix_df = pd.DataFrame(matrix_data)
            matrix_df = matrix_df.set_index("역할")
            st.dataframe(matrix_df, use_container_width=True)
        
        render_structure_map_container(
            content_func=_render_menu_portfolio_map,
            empty_message="메뉴가 등록되지 않았습니다.",
            empty_action_label="메뉴 등록하기",
            empty_action_page="메뉴 등록"
        )
        
        # ZONE C: Owner School (Portfolio Theory)
        school_cards = [
        {
            "title": "대표/주력/유인/보조는 역할이 다르다",
            "point1": "대표메뉴는 브랜드 정체성, 주력메뉴는 매출 기여, 유인메뉴는 손님 유입",
            "point2": "보조메뉴는 선택의 폭을 넓혀 만족도를 높입니다"
        },
        {
            "title": "메뉴는 개별 최적화가 아니라 조합 최적화",
            "point1": "개별 메뉴의 원가율보다 포트폴리오 전체의 수익 구조가 중요합니다",
            "point2": "미끼/볼륨/마진 메뉴의 균형이 핵심입니다"
        },
        {
            "title": "볼륨은 회전을 만들고, 마진은 생존을 만든다",
            "point1": "볼륨 메뉴는 판매량으로 회전율을 높입니다",
            "point2": "마진 메뉴는 수익 기여도로 생존력을 높입니다"
        },
        ]
        render_school_cards(school_cards)
    
    with tab2:
        # ZONE D: Design Tools (Portfolio Tools)
        render_design_tools_container(lambda: _render_menu_portfolio_tools(store_id, menu_df, roles, categories))


def _render_menu_portfolio_tools(store_id: str, menu_df: pd.DataFrame, roles: Dict[str, str], categories: Dict[str, str]):
    """ZONE D: 메뉴 포트폴리오 설계 도구"""
    
    # 1) 메뉴 분류 테이블 (핵심)
    st.markdown("#### 🏷️ 메뉴 포트폴리오 분류")
    
    if menu_df.empty:
        st.info("메뉴가 등록되지 않았습니다.")
    else:
        # 필터 옵션
        filter_option = st.radio(
            "필터",
            ["전체", "미분류만", "카테고리별", "역할별"],
            horizontal=True,
            key="menu_portfolio_filter"
        )
        
        # 필터링
        display_df = menu_df.copy()
        if filter_option == "미분류만":
            # 역할 또는 카테고리가 미분류인 메뉴만
            unclassified = []
            for menu_name in menu_df['메뉴명'].tolist():
                role = roles.get(menu_name, "미분류")
                category = categories.get(menu_name, "기타메뉴")
                if role == "미분류" or category == "기타메뉴":
                    unclassified.append(menu_name)
            display_df = display_df[display_df['메뉴명'].isin(unclassified)]
        elif filter_option == "카테고리별":
            category_filter = st.selectbox(
                "카테고리 선택",
                ["대표메뉴", "주력메뉴", "유인메뉴", "보조메뉴", "기타메뉴"],
                key="menu_portfolio_category_filter"
            )
            filtered_menus = [name for name, cat in categories.items() if cat == category_filter]
            display_df = display_df[display_df['메뉴명'].isin(filtered_menus)]
        elif filter_option == "역할별":
            role_filter = st.selectbox(
                "역할 선택",
                ["미끼", "볼륨", "마진", "미분류"],
                key="menu_portfolio_role_filter"
            )
            filtered_menus = [name for name, role in roles.items() if role == role_filter]
            display_df = display_df[display_df['메뉴명'].isin(filtered_menus)]
        
        if not display_df.empty:
            # 분류 테이블
            st.markdown("**메뉴 포트폴리오 분류 테이블**")
            
            for idx, row in display_df.iterrows():
                menu_name = row['메뉴명']
                price = int(row['판매가'])
                
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.write(f"**{menu_name}**")
                    st.caption(f"{price:,}원")
                
                with col2:
                    current_category = categories.get(menu_name, "기타메뉴")
                    category_options = ["대표메뉴", "주력메뉴", "유인메뉴", "보조메뉴", "기타메뉴"]
                    new_category = st.selectbox(
                        "카테고리",
                        category_options,
                        index=category_options.index(current_category) if current_category in category_options else 4,
                        key=f"portfolio_category_{menu_name}_{store_id}",
                        label_visibility="collapsed"
                    )
                    if new_category != current_category:
                        set_menu_portfolio_category(store_id, menu_name, new_category)
                        st.rerun()
                
                with col3:
                    current_role = roles.get(menu_name, "미분류")
                    role_options = ["미끼", "볼륨", "마진", "미분류"]
                    new_role = st.selectbox(
                        "역할",
                        role_options,
                        index=role_options.index(current_role) if current_role in role_options else 3,
                        key=f"portfolio_role_{menu_name}_{store_id}",
                        label_visibility="collapsed"
                    )
                    if new_role != current_role:
                        set_menu_portfolio_tag(store_id, menu_name, new_role)
                        st.rerun()
                
                with col4:
                    st.write("")  # 공간 확보
            
            st.caption(f"총 {len(display_df)}개 메뉴")
        else:
            st.info("해당 조건의 메뉴가 없습니다.")
    
    render_section_divider()
    
    # 2) 포트폴리오 권장 조합 가이드
    st.markdown("#### 📋 포트폴리오 권장 조합")
    st.info("""
    **권장 메뉴 구성:**
    - 대표메뉴: 1~2개 (브랜드 정체성)
    - 주력메뉴: 3~6개 (매출 기여)
    - 유인메뉴: 1~3개 (손님 유입)
    - 보조메뉴: 4~8개 (선택의 폭)
    
    **권장 역할 구성:**
    - 미끼: 1~2개 (저가 유인)
    - 볼륨: 3~5개 (판매량 중심)
    - 마진: 2~4개 (수익 기여)
    """)
    
    render_section_divider()
    
    # 3) 기존 등록/수정/삭제 기능 (하단 유지)
    _render_menu_management_tools(store_id, menu_df, roles, categories)


def _render_menu_management_tools(store_id: str, menu_df: pd.DataFrame, roles: Dict[str, str], categories: Dict[str, str]):
    """기존 메뉴 등록/수정/삭제 기능"""
    st.markdown("#### 📝 메뉴 등록/수정/삭제")
    
    # 입력 모드 선택 (단일 / 일괄)
    input_mode = st.radio(
        "입력 모드",
        ["단일 입력", "일괄 입력 (여러 메뉴)"],
        horizontal=True,
        key="menu_management_menu_input_mode"
    )
    
    render_section_divider()
    
    if input_mode == "단일 입력":
        # 단일 입력 폼
        menu_name, price = render_menu_input(key_prefix="menu_management")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("💾 저장", type="primary", use_container_width=True):
                if not menu_name or menu_name.strip() == "":
                    st.error("메뉴명을 입력해주세요.")
                elif price <= 0:
                    st.error("판매가는 0보다 큰 값이어야 합니다.")
                else:
                    try:
                        success, message = save_menu(menu_name, price)
                        if success:
                            # 캐시만 클리어하고 rerun 없이 성공 메시지만 표시
                            try:
                                st.cache_data.clear()
                            except Exception as cache_error:
                                # Phase 1: 예외 처리 개선 - 로깅 추가
                                logging.getLogger(__name__).warning(f"캐시 클리어 실패 (메뉴 저장): {cache_error}")
                            st.success(f"✅ 메뉴가 저장되었습니다! ({menu_name}, {price:,}원)")
                            # 입력 필드 초기화 (session_state로, key_prefix 사용)
                            if 'menu_management_menu_name' in st.session_state:
                                st.session_state.menu_management_menu_name = ""
                            if 'menu_management_menu_price' in st.session_state:
                                st.session_state.menu_management_menu_price = 0
                        else:
                            st.error(message)
                    except Exception as e:
                        # Phase 3: 에러 메시지 표준화
                        error_msg = handle_data_error("메뉴 저장", e)
                        st.error(error_msg)
    
    else:
        # 일괄 입력 폼
        menu_data = render_menu_batch_input(key_prefix="menu_management")
        
        # 입력할 메뉴 개수 가져오기
        menu_count = st.session_state.get("menu_management_batch_menu_count", 5)
        
        if menu_data:
            render_section_divider()
            
            # 입력 요약 표시
            st.write("**📊 입력 요약**")
            summary_df = pd.DataFrame(
                [(name, f"{price:,}원") for name, price in menu_data],
                columns=['메뉴명', '판매가']
            )
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            
            st.markdown(f"**총 {len(menu_data)}개 메뉴**")
            
            # 버튼 클릭 시 현재 입력값을 직접 읽어오기
            col1, col2 = st.columns([1, 4])
            with col1:
                save_button_clicked = st.button("💾 일괄 저장", type="primary", use_container_width=True)
            
            if save_button_clicked:
                # 버튼 클릭 시 현재 입력된 모든 값 읽기
                current_menu_data = []
                for i in range(menu_count):
                    menu_name_key = f"menu_management_batch_menu_name_{i}"
                    price_key = f"menu_management_batch_menu_price_{i}"
                    
                    menu_name = st.session_state.get(menu_name_key, "")
                    price = st.session_state.get(price_key, 0)
                    
                    if menu_name and menu_name.strip() and price > 0:
                        current_menu_data.append((menu_name.strip(), price))
                
                if not current_menu_data:
                    st.error("⚠️ 저장할 메뉴가 없습니다. 메뉴명과 판매가를 모두 입력해주세요.")
                else:
                    errors = []
                    success_count = 0
                    
                    for menu_name, price in current_menu_data:
                        try:
                            success, message = save_menu(menu_name, price)
                            if success:
                                success_count += 1
                            else:
                                errors.append(f"{menu_name}: {message}")
                        except Exception as e:
                            errors.append(f"{menu_name}: {e}")
                    
                    if errors:
                        for error in errors:
                            st.error(error)
                    
                    if success_count > 0:
                        # 캐시만 클리어하고 rerun 없이 성공 메시지만 표시
                        try:
                            st.cache_data.clear()
                        except Exception as cache_error:
                            # Phase 1: 예외 처리 개선 - 로깅 추가
                            logging.getLogger(__name__).warning(f"캐시 클리어 실패 (메뉴 일괄 저장): {cache_error}")
                        st.success(f"✅ {success_count}개 메뉴가 저장되었습니다!")
                        st.balloons()
                        # 입력 필드 초기화 (session_state로, key_prefix 사용)
                        for i in range(menu_count):
                            if f"menu_management_batch_menu_name_{i}" in st.session_state:
                                st.session_state[f"menu_management_batch_menu_name_{i}"] = ""
                            if f"menu_management_batch_menu_price_{i}" in st.session_state:
                                st.session_state[f"menu_management_batch_menu_price_{i}"] = 0
    
    # 저장된 메뉴 표시 및 수정/삭제 (ZONE D 내부)
    render_section_divider()
    
    # 저장된 메뉴 표시 및 수정/삭제
    # 제목을 화이트 모드에서도 흰색으로 표시
    st.markdown("""
    <div style="margin: 2rem 0 1rem 0;">
        <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
            📋 등록된 메뉴 리스트
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    # menu_df는 이미 상단에서 로드됨 (파라미터로 받음)
    # 다시 로드하지 않고 파라미터 사용
    # roles와 categories도 파라미터로 받음
    
    if not menu_df.empty:
        # 간단 검색 필터 (메뉴명 부분 일치)
        search_keyword = st.text_input("메뉴 검색 (메뉴명 일부 입력)", key="menu_management_menu_search")
        if search_keyword:
            menu_df = menu_df[menu_df['메뉴명'].astype(str).str.contains(search_keyword, case=False, na=False)]
    
    if not menu_df.empty:
        # 카테고리 컬럼이 없으면 추가 (기본값: '기타메뉴')
        if 'category' not in menu_df.columns:
            menu_df['category'] = '기타메뉴'
        elif '카테고리' in menu_df.columns:
            menu_df['category'] = menu_df['카테고리']
        # 카테고리가 None이거나 빈 값인 경우 기본값 설정
        menu_df['category'] = menu_df['category'].fillna('기타메뉴')
        menu_df['category'] = menu_df['category'].replace('', '기타메뉴')
        
        # 카테고리 색상 매핑
        category_colors = {
            '대표메뉴': '#1e3a8a',      # 진한 파란색
            '주력메뉴': '#166534',      # 진한 초록색
            '유인메뉴': '#ea580c',      # 진한 주황색
            '보조메뉴': '#6b7280',      # 회색
            '기타메뉴': '#3b82f6'       # 연한 파란색
        }
        
        # 순서 정보를 session_state에 저장 (초기화)
        menu_order_key = "menu_management_menu_display_order"
        if menu_order_key not in st.session_state:
            # 초기 순서 설정 (메뉴명 기준)
            menu_names = menu_df['메뉴명'].tolist()
            st.session_state[menu_order_key] = {name: idx + 1 for idx, name in enumerate(menu_names)}
        
        # 순서에 따라 정렬
        menu_df['순서'] = menu_df['메뉴명'].map(st.session_state[menu_order_key])
        menu_df = menu_df.sort_values('순서').reset_index(drop=True)
        
        # 메뉴 번호 매기기
        menu_df['번호'] = range(1, len(menu_df) + 1)
        
        # 메뉴 리스트 표시 (체크박스, 번호, 메뉴명, 판매가, 카테고리, 순서 변경 버튼, 삭제 버튼)
        st.markdown("**📋 메뉴 목록**")
        
        # 선택된 메뉴 인덱스 수집
        selected_indices = []
        
        # 헤더 행
        header_col1, header_col2, header_col3, header_col4, header_col5, header_col6, header_col7, header_col8 = st.columns([0.3, 0.5, 2.5, 1.5, 1.5, 1, 1, 1])
        with header_col1:
            st.write("**선택**")
        with header_col2:
            st.write("**번호**")
        with header_col3:
            st.write("**메뉴명**")
        with header_col4:
            st.write("**판매가**")
        with header_col5:
            st.write("**카테고리**")
        with header_col6:
            st.write("**위로**")
        with header_col7:
            st.write("**아래로**")
        with header_col8:
            st.write("**삭제**")
        
        st.markdown("---")
        
        # 카테고리별 배경색 CSS 스타일 정의 (더 진하고 넓게)
        st.markdown("""
        <style>
        .menu-row-wrapper {
            padding: 1rem 0.75rem;
            margin: 0.5rem 0;
            border-radius: 8px;
            border-left: 6px solid;
            min-height: 60px;
            display: flex;
            align-items: center;
        }
        .menu-row-대표메뉴 {
            background-color: #1e3a8a80;
            border-left-color: #1e40af;
        }
        .menu-row-주력메뉴 {
            background-color: #16653480;
            border-left-color: #15803d;
        }
        .menu-row-유인메뉴 {
            background-color: #ea580c80;
            border-left-color: #f97316;
        }
        .menu-row-보조메뉴 {
            background-color: #6b728080;
            border-left-color: #9ca3af;
        }
        .menu-row-기타메뉴 {
            background-color: #3b82f680;
            border-left-color: #60a5fa;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 각 메뉴 행
        for idx, row in menu_df.iterrows():
            # 카테고리별 배경색 설정
            category = row.get('category', '기타메뉴')
            category_class = category if category in category_colors else '기타메뉴'
            
            # 행 시작 - 배경색 적용
            st.markdown(f'<div class="menu-row-wrapper menu-row-{category_class}">', unsafe_allow_html=True)
            
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([0.3, 0.5, 2.5, 1.5, 1.5, 1, 1, 1])
            
            with col1:
                checkbox_key = f"menu_management_menu_checkbox_{idx}"
                if st.checkbox("", key=checkbox_key, label_visibility="collapsed"):
                    selected_indices.append(idx)
            
            with col2:
                st.write(f"**{row['번호']}**")
            
            with col3:
                st.write(f"**{row['메뉴명']}**")
            
            with col4:
                st.write(f"{int(row['판매가']):,}원")
            
            with col5:
                # 카테고리 선택
                category_options = ['대표메뉴', '주력메뉴', '유인메뉴', '보조메뉴', '기타메뉴']
                current_category = category if category in category_options else '기타메뉴'
                category_key = f"menu_management_category_select_{idx}"
                new_category = st.selectbox(
                    "",
                    category_options,
                    index=category_options.index(current_category) if current_category in category_options else 4,
                    key=category_key,
                    label_visibility="collapsed"
                )
                
                # 카테고리가 변경되었으면 업데이트
                if new_category != current_category:
                    try:
                        success, message = update_menu_category(row['메뉴명'], new_category)
                        if success:
                            # session_state도 업데이트
                            set_menu_portfolio_category(store_id, row['메뉴명'], new_category)
                            # 캐시만 클리어하고 rerun 없이 성공 메시지만 표시
                            try:
                                st.cache_data.clear()
                            except Exception as e:
                                logging.getLogger(__name__).warning(f"캐시 클리어 실패 (카테고리 변경): {e}")
                            st.success(f"✅ 카테고리가 '{new_category}'로 변경되었습니다.")
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"카테고리 업데이트 중 오류: {e}")
            
            with col6:
                # 위로 이동 버튼
                if idx > 0:
                    if st.button("⬆️", key=f"menu_management_move_up_{idx}", help="위로 이동", use_container_width=True):
                        # 순서 변경: 현재 항목과 위 항목의 순서 교환
                        current_menu = row['메뉴명']
                        prev_menu = menu_df.iloc[idx - 1]['메뉴명']
                        current_order = st.session_state[menu_order_key][current_menu]
                        prev_order = st.session_state[menu_order_key][prev_menu]
                        st.session_state[menu_order_key][current_menu] = prev_order
                        st.session_state[menu_order_key][prev_menu] = current_order
                        # 순서 변경은 session_state만 업데이트, rerun 없이 즉시 반영
                        st.success("✅ 순서가 변경되었습니다.")
            
            with col7:
                # 아래로 이동 버튼
                if idx < len(menu_df) - 1:
                    if st.button("⬇️", key=f"menu_management_move_down_{idx}", help="아래로 이동", use_container_width=True):
                        # 순서 변경: 현재 항목과 아래 항목의 순서 교환
                        current_menu = row['메뉴명']
                        next_menu = menu_df.iloc[idx + 1]['메뉴명']
                        current_order = st.session_state[menu_order_key][current_menu]
                        next_order = st.session_state[menu_order_key][next_menu]
                        st.session_state[menu_order_key][current_menu] = next_order
                        st.session_state[menu_order_key][next_menu] = current_order
                        # 순서 변경은 session_state만 업데이트, rerun 없이 즉시 반영
                        st.success("✅ 순서가 변경되었습니다.")
            
            with col8:
                # 개별 삭제 버튼
                if st.button("🗑️", key=f"menu_management_delete_single_{idx}", help="삭제", use_container_width=True, type="secondary"):
                    menu_name = row['메뉴명']
                    try:
                        success, message, refs = delete_menu(menu_name)
                        if success:
                            # 캐시만 클리어하고 rerun 없이 성공 메시지만 표시
                            try:
                                st.cache_data.clear()
                            except Exception as e:
                                logging.getLogger(__name__).warning(f"캐시 클리어 실패 (메뉴 삭제): {e}")
                            # session_state에서도 제거
                            if menu_name in st.session_state[menu_order_key]:
                                del st.session_state[menu_order_key][menu_name]
                            # 순서 재정렬
                            remaining_menus = list(st.session_state[menu_order_key].keys())
                            st.session_state[menu_order_key] = {name: idx + 1 for idx, name in enumerate(remaining_menus)}
                            st.success(f"✅ '{menu_name}' 메뉴가 삭제되었습니다!")
                        else:
                            st.error(message)
                            if refs:
                                st.info(f"**참조 정보:** {', '.join([f'{k}: {v}개' for k, v in refs.items()])}")
                    except Exception as e:
                        # Phase 3: 에러 메시지 표준화
                        error_msg = handle_data_error("메뉴 삭제", e)
                        st.error(error_msg)
            
            # 행 종료
            st.markdown('</div>', unsafe_allow_html=True)
            
            if idx < len(menu_df) - 1:
                st.markdown("---")
        
        # 선택된 메뉴 일괄 삭제 버튼
        if selected_indices:
            st.markdown("---")
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button(f"🗑️ 선택한 {len(selected_indices)}개 삭제", type="primary", key="menu_management_delete_selected_menus", use_container_width=True):
                    errors = []
                    success_count = 0
                    
                    for idx in selected_indices:
                        menu_name = menu_df.iloc[idx]['메뉴명']
                        try:
                            success, message, refs = delete_menu(menu_name)
                            if success:
                                success_count += 1
                                # session_state에서도 제거
                                if menu_name in st.session_state[menu_order_key]:
                                    del st.session_state[menu_order_key][menu_name]
                            else:
                                errors.append(f"{menu_name}: {message}")
                        except Exception as e:
                            errors.append(f"{menu_name}: {e}")
                    
                    if errors:
                        for error in errors:
                            st.error(error)
                    
                    if success_count > 0:
                        # 캐시만 클리어하고 rerun 없이 성공 메시지만 표시
                        try:
                            st.cache_data.clear()
                        except Exception as e:
                            logging.getLogger(__name__).warning(f"캐시 클리어 실패 (메뉴 일괄 저장): {e}")
                        # 순서 재정렬
                        remaining_menus = list(st.session_state[menu_order_key].keys())
                        st.session_state[menu_order_key] = {name: idx + 1 for idx, name in enumerate(remaining_menus)}
                        st.success(f"✅ {success_count}개 메뉴가 삭제되었습니다!")
        
        render_section_divider()
        
        # 수정 기능
        render_section_divider()
        st.markdown("**📝 메뉴 수정**")
        menu_list = menu_df['메뉴명'].tolist()
        selected_menu = st.selectbox(
            "수정할 메뉴 선택",
            ["선택하세요"] + menu_list,
            key="menu_management_menu_edit_select"
        )
        
        if selected_menu != "선택하세요":
            # Phase 1: 안전한 DataFrame 접근
            menu_info = safe_get_row_by_condition(menu_df, menu_df['메뉴명'] == selected_menu)
            
            if menu_info is None:
                st.error(f"메뉴 '{selected_menu}'를 찾을 수 없습니다.")
            else:
                new_menu_name = st.text_input("메뉴명", value=menu_info.get('메뉴명', ''), key="menu_management_menu_edit_name")
                new_price = st.number_input("판매가 (원)", min_value=0, value=int(menu_info.get('판매가', 0)), step=1000, key="menu_management_menu_edit_price")
                if st.button("✅ 수정", key="menu_management_menu_edit_btn"):
                    try:
                        success, message = update_menu(menu_info.get('메뉴명', ''), new_menu_name, new_price)
                        if success:
                            # 캐시만 클리어하고 rerun 없이 성공 메시지만 표시
                            try:
                                st.cache_data.clear()
                            except Exception as cache_error:
                                # Phase 1: 예외 처리 개선 - 로깅 추가
                                logging.getLogger(__name__).warning(f"캐시 클리어 실패 (메뉴 수정): {cache_error}")
                            st.success(f"✅ {message}")
                        else:
                            st.error(message)
                    except Exception as e:
                        # Phase 3: 에러 메시지 표준화
                        error_msg = handle_data_error("메뉴 수정", e)
                        st.error(error_msg)
    else:
        st.info("등록된 메뉴가 없습니다.")


# Streamlit 멀티페이지에서 직접 실행될 때
# 주석 처리: app.py에서만 렌더되도록 함 (중복 호출 방지)
# render_menu_management()
