"""
실제정산 페이지
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
from datetime import datetime
from src.ui_helpers import render_page_header, render_section_divider, safe_get_first_row, handle_data_error
from src.storage_supabase import load_csv

# 공통 설정 적용
bootstrap(page_title="Settlement Actual")


def render_settlement_actual():
    """실제정산 페이지 렌더링"""
    render_page_header("실제 정산 (월별 실적)", "🧾")
    
    # 매출 데이터 로드 (일별 총매출)
    sales_df = load_csv('sales.csv', default_columns=['날짜', '매장', '총매출'])
    
    if sales_df.empty:
        st.info("저장된 매출 데이터가 없습니다. 먼저 매출 관리 페이지에서 일매출을 입력해주세요.")
    else:
        # 날짜 컬럼을 datetime으로 변환
        sales_df['날짜'] = pd.to_datetime(sales_df['날짜'])
        sales_df['연도'] = sales_df['날짜'].dt.year
        sales_df['월'] = sales_df['날짜'].dt.month
        
        # 사용 가능한 연/월 목록
        available_years = sorted(sales_df['연도'].unique().tolist(), reverse=True)
        
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        col1, col2 = st.columns(2)
        with col1:
            selected_year = st.selectbox(
                "정산 연도 선택",
                options=available_years,
                index=0 if current_year in available_years else 0,
                key="settlement_year",
            )
        
        # 선택한 연도의 사용 가능한 월만 표시
        available_months = sorted(
            sales_df[sales_df['연도'] == selected_year]['월'].unique().tolist()
        )
        if current_month in available_months:
            default_month_index = available_months.index(current_month)
        else:
            default_month_index = len(available_months) - 1
        
        with col2:
            selected_month = st.selectbox(
                "정산 월 선택",
                options=available_months,
                index=default_month_index,
                key="settlement_month",
            )
        
        # 선택한 연/월의 매출 합계 계산
        month_sales_df = sales_df[
            (sales_df['연도'] == selected_year) & (sales_df['월'] == selected_month)
        ].copy()
        
        if month_sales_df.empty:
            st.info(f"{selected_year}년 {selected_month}월에 해당하는 매출 데이터가 없습니다.")
        else:
            month_total_sales = float(month_sales_df['총매출'].sum())
            
            render_section_divider()
            
            # 상단 요약 카드
            st.markdown(
                f"""
                <div class="info-box">
                    <strong>📅 정산 대상 기간</strong><br>
                    <span style="font-size: 0.9rem; opacity: 0.9;">
                        {selected_year}년 {selected_month}월의 실제 매출과 비용을 기준으로 정산합니다.
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("해당 월 총 매출", f"{month_total_sales:,.0f}원")
            # 비용/이익은 아래 입력값 기준으로 다시 표시
            
            # 기존 실제 정산 데이터 로드
            actual_df = load_csv(
                "actual_settlement.csv",
                default_columns=["연도", "월", "실제매출", "실제비용", "실제이익", "실제이익률"],
            )
            
            existing_row = None
            if not actual_df.empty:
                existing_row = actual_df[
                    (actual_df["연도"] == selected_year)
                    & (actual_df["월"] == selected_month)
                ]
                # Phase 1: 안전한 DataFrame 접근
                if not existing_row.empty:
                    existing_row = safe_get_first_row(existing_row)
                    if existing_row is None:
                        existing_row = pd.Series()
            
            render_section_divider()
            st.markdown("**💸 해당 월 실제 비용 입력 (5대 비용 항목별)**")
            
            # 5대 비용 항목 정의
            expense_categories = {
                '임차료': {'icon': '🏢', 'description': '임차료', 'type': 'fixed', 'fixed_items': ['임차료']},
                '인건비': {'icon': '👥', 'description': '인건비 관련 모든 비용', 'type': 'fixed', 'fixed_items': ['직원 실지급 인건비', '사회보험(직원+회사분 통합)', '원천징수(국세+지방세)', '퇴직급여 충당금', '보너스']},
                '재료비': {'icon': '🥬', 'description': '재료비 관련 모든 비용', 'type': 'variable'},
                '공과금': {'icon': '💡', 'description': '공과금 관련 모든 비용', 'type': 'mixed', 'fixed_items': ['전기', '가스', '수도']},
                '부가세&카드수수료': {'icon': '💳', 'description': '부가세 및 카드수수료 (매출 대비 비율)', 'type': 'rate', 'fixed_items': ['부가세', '카드수수료']}
            }
            
            # 세션 상태에 비용 항목별 세부 데이터 저장 및 고정 항목 초기화
            if f'actual_expense_items_{selected_year}_{selected_month}' not in st.session_state:
                expense_items = {cat: [] for cat in expense_categories.keys()}
                
                # 고정 항목 초기화
                # 임차료: 임차료 1개 항목
                if '임차료' in expense_items:
                    expense_items['임차료'] = [{'item_name': '임차료', 'amount': 0}]
                
                # 인건비: 5개 고정 항목
                if '인건비' in expense_items:
                    expense_items['인건비'] = [
                        {'item_name': '직원 실지급 인건비', 'amount': 0},
                        {'item_name': '사회보험(직원+회사분 통합)', 'amount': 0},
                        {'item_name': '원천징수(국세+지방세)', 'amount': 0},
                        {'item_name': '퇴직급여 충당금', 'amount': 0},
                        {'item_name': '보너스', 'amount': 0}
                    ]
                
                # 공과금: 전기, 가스, 수도 3개 고정 항목
                if '공과금' in expense_items:
                    expense_items['공과금'] = [
                        {'item_name': '전기', 'amount': 0},
                        {'item_name': '가스', 'amount': 0},
                        {'item_name': '수도', 'amount': 0}
                    ]
                
                # 부가세&카드수수료: 부가세, 카드수수료 2개 항목 (비율로 저장)
                if '부가세&카드수수료' in expense_items:
                    expense_items['부가세&카드수수료'] = [
                        {'item_name': '부가세', 'amount': 0.0},  # 비율(%)
                        {'item_name': '카드수수료', 'amount': 0.0}  # 비율(%)
                    ]
                
                st.session_state[f'actual_expense_items_{selected_year}_{selected_month}'] = expense_items
            else:
                expense_items = st.session_state[f'actual_expense_items_{selected_year}_{selected_month}']
                
                # 고정 항목이 없으면 초기화
                if '임차료' in expense_items and not expense_items['임차료']:
                    expense_items['임차료'] = [{'item_name': '임차료', 'amount': 0}]
                
                if '인건비' in expense_items:
                    fixed_items = ['직원 실지급 인건비', '사회보험(직원+회사분 통합)', '원천징수(국세+지방세)', '퇴직급여 충당금', '보너스']
                    existing_names = [item.get('item_name') for item in expense_items['인건비']]
                    for fixed_name in fixed_items:
                        if fixed_name not in existing_names:
                            expense_items['인건비'].append({'item_name': fixed_name, 'amount': 0})
                    # 순서 정렬
                    expense_items['인건비'] = sorted(
                        expense_items['인건비'],
                        key=lambda x: fixed_items.index(x['item_name']) if x['item_name'] in fixed_items else 999
                    )
                
                if '공과금' in expense_items:
                    fixed_items = ['전기', '가스', '수도']
                    existing_names = [item.get('item_name') for item in expense_items['공과금']]
                    # 고정 항목이 없으면 추가 (기존 가변 항목은 유지)
                    for fixed_name in fixed_items:
                        if fixed_name not in existing_names:
                            expense_items['공과금'].insert(0, {'item_name': fixed_name, 'amount': 0})
                    # 고정 항목을 상단에 정렬 (가변 항목은 하단)
                    fixed_items_list = [item for item in expense_items['공과금'] if item.get('item_name') in fixed_items]
                    variable_items_list = [item for item in expense_items['공과금'] if item.get('item_name') not in fixed_items]
                    # 고정 항목 순서 정렬
                    fixed_items_list = sorted(
                        fixed_items_list,
                        key=lambda x: fixed_items.index(x['item_name']) if x['item_name'] in fixed_items else 999
                    )
                    expense_items['공과금'] = fixed_items_list + variable_items_list
                
                if '부가세&카드수수료' in expense_items:
                    fixed_items = ['부가세', '카드수수료']
                    existing_names = [item.get('item_name') for item in expense_items['부가세&카드수수료']]
                    for fixed_name in fixed_items:
                        if fixed_name not in existing_names:
                            expense_items['부가세&카드수수료'].append({'item_name': fixed_name, 'amount': 0.0})
                    # 순서 정렬
                    expense_items['부가세&카드수수료'] = sorted(
                        expense_items['부가세&카드수수료'],
                        key=lambda x: fixed_items.index(x['item_name']) if x['item_name'] in fixed_items else 999
                    )
            
            # 한글 원화 변환 함수
            def format_korean_currency(amount):
                """숫자를 한글 원화로 변환"""
                if amount == 0:
                    return "0원"
                eok = amount // 100000000
                remainder = amount % 100000000
                man = remainder // 10000
                remainder = remainder % 10000
                parts = []
                if eok > 0:
                    parts.append(f"{eok}억")
                if man > 0:
                    parts.append(f"{man}만")
                if remainder > 0:
                    parts.append(f"{remainder:,}".replace(",", ""))
                if not parts:
                    return "0원"
                return "".join(parts) + "원"
            
            # 각 카테고리별 입력 섹션
            category_totals = {}
            for category, info in expense_categories.items():
                # 카테고리 헤더
                col1, col2 = st.columns([3, 1])
                with col1:
                    header_color = "#ffffff"
                    st.markdown(f"""
                    <div style="margin: 1.5rem 0 0.5rem 0;">
                        <h3 style="color: {header_color}; font-weight: 600; margin: 0;">
                            {info['icon']} {category}
                        </h3>
                    </div>
                    """, unsafe_allow_html=True)
                    st.caption(f"{info['description']}")
                
                # 카테고리별 총액 계산
                if info['type'] == 'rate':
                    # 부가세&카드수수료: 비율 합계를 금액으로 변환
                    total_rate = sum(item.get('amount', 0) for item in expense_items[category])
                    category_total = (month_total_sales * total_rate / 100) if month_total_sales > 0 else 0
                else:
                    # 절대 금액
                    category_total = sum(item.get('amount', 0) for item in expense_items[category])
                
                category_totals[category] = category_total
                
                with col2:
                    if category_total > 0:
                        if info['type'] == 'rate':
                            total_rate = sum(item.get('amount', 0) for item in expense_items[category])
                            st.markdown(f"""
                            <div style="text-align: right; margin-top: 0.5rem; padding-top: 0.5rem;">
                                <strong style="color: #667eea; font-size: 1.1rem;">
                                    총 비율: {total_rate:.2f}%
                                </strong>
                                <div style="font-size: 0.85rem; color: #666;">
                                    ({category_total:,.0f}원)
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style="text-align: right; margin-top: 0.5rem; padding-top: 0.5rem;">
                                <strong style="color: #667eea; font-size: 1.1rem;">
                                    총액: {format_korean_currency(int(category_total))}
                                </strong>
                                <div style="font-size: 0.85rem; color: #666;">
                                    ({category_total:,.0f}원)
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                
                # 고정 항목인지 확인
                is_fixed = 'fixed_items' in info and (info['type'] == 'fixed' or info['type'] == 'rate')
                is_mixed = 'fixed_items' in info and info['type'] == 'mixed'
                
                # 항목 표시 및 수정
                if expense_items[category]:
                    # mixed 타입인 경우 고정 항목과 가변 항목 분리
                    if is_mixed:
                        fixed_items_names = info.get('fixed_items', [])
                        fixed_items_list = [item for item in expense_items[category] if item.get('item_name') in fixed_items_names]
                        variable_items_list = [item for item in expense_items[category] if item.get('item_name') not in fixed_items_names]
                        
                        # 고정 항목 먼저 표시
                        if fixed_items_list:
                            for idx, item in enumerate(fixed_items_list):
                                col_a, col_b, col_c = st.columns([3, 2, 1])
                                with col_a:
                                    st.write(f"**{item.get('item_name', '')}**")
                                with col_b:
                                    edit_amount_key = f"edit_amount_{category}_fixed_{item.get('item_name')}_{selected_year}_{selected_month}"
                                    edited_amount = st.number_input(
                                        "금액 (원)",
                                        min_value=0,
                                        value=int(item.get('amount', 0)),
                                        step=10000,
                                        format="%d",
                                        key=edit_amount_key,
                                    )
                                    if edited_amount != item.get('amount'):
                                        item['amount'] = edited_amount
                                        st.session_state[f'actual_expense_items_{selected_year}_{selected_month}'] = expense_items
                                with col_c:
                                    st.write("")  # 삭제 버튼 없음
                            
                            if variable_items_list:
                                st.markdown("---")
                                with st.expander(f"📋 추가 항목 ({len(variable_items_list)}개)", expanded=True):
                                    for idx, item in enumerate(variable_items_list):
                                        col_a, col_b, col_c = st.columns([3, 2, 1])
                                        with col_a:
                                            edit_key = f"edit_name_{category}_var_{idx}_{selected_year}_{selected_month}"
                                            if edit_key not in st.session_state:
                                                st.session_state[edit_key] = item.get('item_name', '')
                                            edited_name = st.text_input(
                                                "항목명",
                                                value=st.session_state[edit_key],
                                                key=edit_key,
                                            )
                                            if edited_name != item.get('item_name'):
                                                item['item_name'] = edited_name
                                                st.session_state[f'actual_expense_items_{selected_year}_{selected_month}'] = expense_items
                                        with col_b:
                                            edit_amount_key = f"edit_amount_{category}_var_{idx}_{selected_year}_{selected_month}"
                                            edited_amount = st.number_input(
                                                "금액 (원)",
                                                min_value=0,
                                                value=int(item.get('amount', 0)),
                                                step=10000,
                                                format="%d",
                                                key=edit_amount_key,
                                            )
                                            if edited_amount != item.get('amount'):
                                                item['amount'] = edited_amount
                                                st.session_state[f'actual_expense_items_{selected_year}_{selected_month}'] = expense_items
                                        with col_c:
                                            if st.button("🗑️", key=f"del_{category}_var_{idx}_{selected_year}_{selected_month}", help="삭제"):
                                                expense_items[category].remove(item)
                                                st.session_state[f'actual_expense_items_{selected_year}_{selected_month}'] = expense_items
                                                st.rerun()
                    else:
                        # 고정 항목 또는 가변 항목만 있는 경우
                        # 가변 항목(재료비 등)은 expander로 표시
                        if not is_fixed and expense_items[category]:
                            with st.expander(f"📋 입력된 항목 ({len(expense_items[category])}개)", expanded=True):
                                for idx, item in enumerate(expense_items[category]):
                                    col_a, col_b, col_c = st.columns([3, 2, 1])
                                    with col_a:
                                        # 수정 가능한 항목명
                                        edit_key = f"edit_name_{category}_{idx}_{selected_year}_{selected_month}"
                                        if edit_key not in st.session_state:
                                            st.session_state[edit_key] = item.get('item_name', '')
                                        edited_name = st.text_input(
                                            "항목명",
                                            value=st.session_state[edit_key],
                                            key=edit_key,
                                        )
                                        if edited_name != item.get('item_name'):
                                            item['item_name'] = edited_name
                                            st.session_state[f'actual_expense_items_{selected_year}_{selected_month}'] = expense_items
                                    
                                    with col_b:
                                        # 절대 금액 입력
                                        edit_amount_key = f"edit_amount_{category}_{idx}_{selected_year}_{selected_month}"
                                        edited_amount = st.number_input(
                                            "금액 (원)",
                                            min_value=0,
                                            value=int(item.get('amount', 0)),
                                            step=10000,
                                            format="%d",
                                            key=edit_amount_key,
                                        )
                                        
                                        # 변경된 값 저장
                                        if edited_amount != item.get('amount'):
                                            item['amount'] = edited_amount
                                            st.session_state[f'actual_expense_items_{selected_year}_{selected_month}'] = expense_items
                                    
                                    with col_c:
                                        if st.button("🗑️", key=f"del_{category}_{idx}_{selected_year}_{selected_month}", help="삭제"):
                                            expense_items[category].pop(idx)
                                            st.session_state[f'actual_expense_items_{selected_year}_{selected_month}'] = expense_items
                                            st.rerun()
                        elif is_fixed:
                            # 고정 항목은 expander 없이 직접 표시
                            for idx, item in enumerate(expense_items[category]):
                                col_a, col_b, col_c = st.columns([3, 2, 1])
                                with col_a:
                                    # 고정 항목: 항목명 표시만
                                    st.write(f"**{item.get('item_name', '')}**")
                                
                                with col_b:
                                    if info['type'] == 'rate':
                                        # 비율 입력
                                        edit_amount_key = f"edit_amount_{category}_{idx}_{selected_year}_{selected_month}"
                                        edited_rate = st.number_input(
                                            "매출 대비 비율 (%)",
                                            min_value=0.0,
                                            max_value=100.0,
                                            value=float(item.get('amount', 0)),
                                            step=0.1,
                                            format="%.2f",
                                            key=edit_amount_key,
                                        )
                                        
                                        # 변경된 값 저장
                                        if edited_rate != item.get('amount'):
                                            item['amount'] = edited_rate
                                            st.session_state[f'actual_expense_items_{selected_year}_{selected_month}'] = expense_items
                                        
                                        # 계산된 금액 표시
                                        calculated_amount = (month_total_sales * edited_rate / 100) if month_total_sales > 0 else 0
                                        st.caption(f"→ {calculated_amount:,.0f}원")
                                    else:
                                        # 절대 금액 입력
                                        edit_amount_key = f"edit_amount_{category}_{idx}_{selected_year}_{selected_month}"
                                        edited_amount = st.number_input(
                                            "금액 (원)",
                                            min_value=0,
                                            value=int(item.get('amount', 0)),
                                            step=10000,
                                            format="%d",
                                            key=edit_amount_key,
                                        )
                                        
                                        # 변경된 값 저장
                                        if edited_amount != item.get('amount'):
                                            item['amount'] = edited_amount
                                            st.session_state[f'actual_expense_items_{selected_year}_{selected_month}'] = expense_items
                                
                                with col_c:
                                    st.write("")  # 삭제 버튼 없음
                
                # 고정 항목이 아니거나 mixed 타입인 경우 새 항목 추가
                if not is_fixed or is_mixed:
                    with st.container():
                        st.markdown("---")
                        col1, col2, col3 = st.columns([3, 2, 1])
                        with col1:
                            new_item_name = st.text_input(
                                "항목명",
                                key=f"new_item_name_{category}_{selected_year}_{selected_month}",
                                placeholder="예: 월세, 관리비 등"
                            )
                        with col2:
                            new_item_amount = st.number_input(
                                "금액 (원)",
                                min_value=0,
                                value=0,
                                step=10000,
                                format="%d",
                                key=f"new_item_amount_{category}_{selected_year}_{selected_month}"
                            )
                        with col3:
                            st.write("")
                            st.write("")
                            if st.button("➕ 추가", key=f"add_{category}_{selected_year}_{selected_month}", use_container_width=True):
                                if new_item_name.strip():
                                    # mixed 타입인 경우 고정 항목 이름과 중복 체크
                                    if is_mixed:
                                        fixed_items_names = info.get('fixed_items', [])
                                        if new_item_name.strip() in fixed_items_names:
                                            st.error(f"'{new_item_name.strip()}'는 고정 항목입니다.")
                                        else:
                                            expense_items[category].append({
                                                'item_name': new_item_name.strip(),
                                                'amount': new_item_amount
                                            })
                                            st.session_state[f'actual_expense_items_{selected_year}_{selected_month}'] = expense_items
                                            st.rerun()
                                    else:
                                        expense_items[category].append({
                                            'item_name': new_item_name.strip(),
                                            'amount': new_item_amount
                                        })
                                        st.session_state[f'actual_expense_items_{selected_year}_{selected_month}'] = expense_items
                                        st.rerun()
                                else:
                                    st.error("항목명을 입력해주세요.")
            
            # 전체 비용 합계 계산
            total_actual_cost = sum(category_totals.values())
            
            # 이익 및 이익률 계산
            actual_sales = month_total_sales
            actual_profit = actual_sales - total_actual_cost
            profit_margin = (actual_profit / actual_sales * 100) if actual_sales > 0 else 0.0
            
            render_section_divider()
            
            # 요약 정보
            st.markdown("**📊 비용 합계 요약**")
            summary_col1, summary_col2, summary_col3 = st.columns(3)
            with summary_col1:
                st.metric("실제 총 비용", f"{total_actual_cost:,.0f}원")
            with summary_col2:
                st.metric("실제 이익", f"{actual_profit:,.0f}원")
            with summary_col3:
                st.metric("실제 이익률", f"{profit_margin:,.1f}%")
            
            # 카테고리별 비용 요약 테이블
            cost_summary_data = []
            for category, total in category_totals.items():
                cost_summary_data.append({
                    '비용 항목': category,
                    '금액': f"{total:,.0f}원",
                    '비율': f"{(total / total_actual_cost * 100):.1f}%" if total_actual_cost > 0 else "0.0%"
                })
            cost_summary_df = pd.DataFrame(cost_summary_data)
            st.dataframe(cost_summary_df, use_container_width=True, hide_index=True)
            
            render_section_divider()
            
            # 저장 버튼
            save_col, _ = st.columns([1, 4])
            with save_col:
                if st.button("💾 실제 정산 저장", type="primary", use_container_width=True):
                    try:
                        from src.storage_supabase import save_actual_settlement
                        
                        success = save_actual_settlement(
                            selected_year,
                            selected_month,
                            actual_sales,
                            total_actual_cost,
                            actual_profit,
                            profit_margin,
                        )
                        if success:
                            st.success(
                                f"{selected_year}년 {selected_month}월 실제 정산 데이터가 저장되었습니다."
                            )
                            try:
                                load_csv.clear()
                            except Exception as e:
                                import logging
                                logging.getLogger(__name__).warning(f"캐시 클리어 실패 (실제 정산 저장): {e}")
                            st.rerun()
                    except Exception as e:
                        # Phase 3: 에러 메시지 표준화
                        error_msg = handle_data_error("실제 정산 데이터 저장", e)
                        st.error(error_msg)
            
            # 하단에 기존 정산 이력 표시
            render_section_divider()
            st.markdown("**📜 실제 정산 이력 (월별)**")
            history_df = load_csv(
                "actual_settlement.csv",
                default_columns=["연도", "월", "실제매출", "실제비용", "실제이익", "실제이익률"],
            )
            if not history_df.empty:
                history_df = history_df.sort_values(["연도", "월"], ascending=[False, False])
                display_history = history_df.copy()
                display_history["실제매출"] = display_history["실제매출"].apply(
                    lambda x: f"{float(x):,.0f}원"
                )
                display_history["실제비용"] = display_history["실제비용"].apply(
                    lambda x: f"{float(x):,.0f}원"
                )
                display_history["실제이익"] = display_history["실제이익"].apply(
                    lambda x: f"{float(x):,.0f}원"
                )
                display_history["실제이익률"] = display_history["실제이익률"].apply(
                    lambda x: f"{float(x):,.1f}%"
                )
                st.dataframe(display_history, use_container_width=True, hide_index=True)
            else:
                st.info("저장된 실제 정산 데이터가 없습니다.")


# Streamlit 멀티페이지에서 직접 실행될 때
render_settlement_actual()
