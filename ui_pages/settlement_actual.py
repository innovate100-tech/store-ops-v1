"""
실제정산 페이지 (Phase A+ - UI/UX 뼈대)
DB 연결 없이 UI 구조 + 상태관리 + 자동 계산 + 고정비 개념 구현
"""
from src.bootstrap import bootstrap
import streamlit as st
from src.utils.time_utils import current_year_kst, current_month_kst
from src.ui_helpers import render_section_divider

# 공통 설정 적용
bootstrap(page_title="Settlement Actual")


def _initialize_expense_items(year: int, month: int):
    """비용 항목 초기화 (session_state)"""
    key = f"settlement_expense_items_{year}_{month}"
    if key not in st.session_state:
        st.session_state[key] = {
            '임차료': [],
            '인건비': [],
            '재료비': [],
            '공과금': [],
            '부가세&카드수수료': [],
        }
    return st.session_state[key]


def _get_total_sales(year: int, month: int) -> float:
    """총매출 반환 (임시값 0)"""
    key = f"settlement_total_sales_{year}_{month}"
    return st.session_state.get(key, 0.0)


def _set_total_sales(year: int, month: int, value: float):
    """총매출 설정"""
    key = f"settlement_total_sales_{year}_{month}"
    st.session_state[key] = value


def _calculate_category_total(category: str, items: list, total_sales: float) -> float:
    """카테고리별 총액 계산"""
    if category in ['재료비', '부가세&카드수수료']:
        # 매출연동: 비율 합계 * 매출
        total_rate = sum(item.get('rate', 0) for item in items)
        return (total_sales * total_rate / 100) if total_sales > 0 else 0.0
    else:
        # 고정비: 금액 합계
        return sum(item.get('amount', 0) for item in items)


def _calculate_totals(expense_items: dict, total_sales: float) -> dict:
    """전체 합계 계산"""
    category_totals = {}
    for category, items in expense_items.items():
        category_totals[category] = _calculate_category_total(category, items, total_sales)
    
    total_cost = sum(category_totals.values())
    operating_profit = total_sales - total_cost
    profit_margin = (operating_profit / total_sales * 100) if total_sales > 0 else 0.0
    
    return {
        'category_totals': category_totals,
        'total_cost': total_cost,
        'operating_profit': operating_profit,
        'profit_margin': profit_margin,
    }


def _render_header_section(year: int, month: int):
    """상단 영역: 연/월 선택, KPI 카드, 상태 배지"""
    # 연/월 선택
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        selected_year = st.number_input(
            "연도",
            min_value=2020,
            max_value=2100,
            value=year,
            key="settlement_year"
        )
    with col2:
        selected_month = st.number_input(
            "월",
            min_value=1,
            max_value=12,
            value=month,
            key="settlement_month"
        )
    with col3:
        st.write("")  # 빈 공간
    
    # 연/월이 변경되면 rerun
    if selected_year != year or selected_month != month:
        st.rerun()
    
    render_section_divider()
    
    # 총매출 입력
    st.markdown("### 📊 이번 달 성적표")
    total_sales_input = st.number_input(
        "총매출 (원)",
        min_value=0.0,
        value=_get_total_sales(selected_year, selected_month),
        step=100000.0,
        format="%d",
        key=f"settlement_total_sales_input_{selected_year}_{selected_month}"
    )
    _set_total_sales(selected_year, selected_month, total_sales_input)
    
    # KPI 카드
    expense_items = _initialize_expense_items(selected_year, selected_month)
    total_sales = _get_total_sales(selected_year, selected_month)
    totals = _calculate_totals(expense_items, total_sales)
    
    st.markdown('<div style="margin: 1rem 0;"></div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("총매출", f"{total_sales:,.0f}원")
    with col2:
        st.metric("총비용", f"{totals['total_cost']:,.0f}원")
    with col3:
        profit_delta = f"{totals['operating_profit']:,.0f}원"
        st.metric("영업이익", profit_delta)
    with col4:
        st.metric("이익률", f"{totals['profit_margin']:.1f}%")
    
    # 상태 배지 및 평가 문구
    st.markdown('<div style="margin: 1rem 0;"></div>', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown("""
        <div style="padding: 0.5rem 1rem; background-color: #667eea; border-radius: 0.5rem; display: inline-block;">
            <span style="color: #ffffff; font-weight: 600;">작성중</span>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="padding: 0.5rem 0;">
            <span style="color: #ffffff; font-size: 1rem;">
                이번 달 성적표를 작성 중입니다.
            </span>
        </div>
        """, unsafe_allow_html=True)
    
    render_section_divider()
    
    return selected_year, selected_month, expense_items, total_sales, totals


def _render_expense_category(
    category: str,
    category_info: dict,
    items: list,
    total_sales: float,
    year: int,
    month: int
):
    """비용 카테고리별 입력 UI"""
    is_linked = category_info['type'] == 'linked'  # 매출연동 여부
    
    # 카테고리 헤더
    st.markdown(f"""
    <div style="margin: 1.5rem 0 0.5rem 0;">
        <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
            {category_info['icon']} {category}
        </h3>
    </div>
    """, unsafe_allow_html=True)
    st.caption(category_info['description'])
    
    # 카테고리 총액 표시
    category_total = _calculate_category_total(category, items, total_sales)
    if category_total > 0:
        if is_linked:
            total_rate = sum(item.get('rate', 0) for item in items)
            st.markdown(f"""
            <div style="text-align: right; margin: 0.5rem 0;">
                <strong style="color: #667eea; font-size: 1.1rem;">
                    총 비율: {total_rate:.2f}% → {category_total:,.0f}원
                </strong>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="text-align: right; margin: 0.5rem 0;">
                <strong style="color: #667eea; font-size: 1.1rem;">
                    총액: {category_total:,.0f}원
                </strong>
            </div>
            """, unsafe_allow_html=True)
    
    # 기존 항목 표시 및 수정
    if items:
        for idx, item in enumerate(items):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                item_name_key = f"settlement_item_name_{category}_{idx}_{year}_{month}"
                item_name = st.text_input(
                    "항목명",
                    value=item.get('name', ''),
                    key=item_name_key
                )
                # 실시간 업데이트
                if item_name != item.get('name', ''):
                    expense_items = _initialize_expense_items(year, month)
                    if idx < len(expense_items[category]):
                        expense_items[category][idx]['name'] = item_name
            with col2:
                if is_linked:
                    # 매출연동: 비율 입력
                    rate_key = f"settlement_item_rate_{category}_{idx}_{year}_{month}"
                    rate = st.number_input(
                        "비율 (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=item.get('rate', 0.0),
                        step=0.1,
                        format="%.2f",
                        key=rate_key
                    )
                    calculated = (total_sales * rate / 100) if total_sales > 0 else 0.0
                    st.caption(f"→ {calculated:,.0f}원")
                    # 실시간 업데이트
                    if rate != item.get('rate', 0.0):
                        expense_items = _initialize_expense_items(year, month)
                        if idx < len(expense_items[category]):
                            expense_items[category][idx]['rate'] = rate
                else:
                    # 고정비: 금액 입력
                    amount_key = f"settlement_item_amount_{category}_{idx}_{year}_{month}"
                    amount = st.number_input(
                        "금액 (원)",
                        min_value=0,
                        value=int(item.get('amount', 0)),
                        step=10000,
                        format="%d",
                        key=amount_key
                    )
                    # 실시간 업데이트
                    if amount != item.get('amount', 0):
                        expense_items = _initialize_expense_items(year, month)
                        if idx < len(expense_items[category]):
                            expense_items[category][idx]['amount'] = amount
            with col3:
                if st.button("🗑️", key=f"settlement_delete_{category}_{idx}_{year}_{month}", help="삭제"):
                    expense_items = _initialize_expense_items(year, month)
                    if idx < len(expense_items[category]):
                        expense_items[category].pop(idx)
                    st.rerun()
    
    # 새 항목 추가
    st.markdown("---")
    add_col1, add_col2, add_col3 = st.columns([3, 2, 1])
    with add_col1:
        new_name = st.text_input(
            "항목명",
            key=f"settlement_new_name_{category}_{year}_{month}",
            placeholder="예: 월세, 관리비 등"
        )
    with add_col2:
        if is_linked:
            new_value = st.number_input(
                "비율 (%)",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=0.1,
                format="%.2f",
                key=f"settlement_new_rate_{category}_{year}_{month}"
            )
        else:
            new_value = st.number_input(
                "금액 (원)",
                min_value=0,
                value=0,
                step=10000,
                format="%d",
                key=f"settlement_new_amount_{category}_{year}_{month}"
            )
    with add_col3:
        if st.button("➕ 추가", key=f"settlement_add_{category}_{year}_{month}", use_container_width=True):
            if new_name.strip():
                expense_items = _initialize_expense_items(year, month)
                new_item = {'name': new_name.strip()}
                if is_linked:
                    new_item['rate'] = new_value
                else:
                    new_item['amount'] = int(new_value)
                expense_items[category].append(new_item)
                st.rerun()
            else:
                st.error("항목명을 입력해주세요.")


def _render_expense_section(year: int, month: int, total_sales: float):
    """비용 입력 영역"""
    st.markdown("### 💸 비용 입력")
    
    expense_items = _initialize_expense_items(year, month)
    
    # 카테고리 정의
    categories = {
        '임차료': {
            'icon': '🏢',
            'description': '임차료',
            'type': 'fixed',  # 고정비
        },
        '인건비': {
            'icon': '👥',
            'description': '인건비 관련 모든 비용',
            'type': 'fixed',  # 고정비
        },
        '재료비': {
            'icon': '🥬',
            'description': '재료비 관련 모든 비용 (매출 연동)',
            'type': 'linked',  # 매출연동
        },
        '공과금': {
            'icon': '💡',
            'description': '공과금 관련 모든 비용',
            'type': 'fixed',  # 고정비
        },
        '부가세&카드수수료': {
            'icon': '💳',
            'description': '부가세 및 카드수수료 (매출 연동)',
            'type': 'linked',  # 매출연동
        },
    }
    
    # 각 카테고리 렌더링
    for category, info in categories.items():
        _render_expense_category(
            category,
            info,
            expense_items[category],
            total_sales,
            year,
            month
        )
        st.markdown('<div style="margin: 1rem 0;"></div>', unsafe_allow_html=True)


def _render_analysis_section():
    """분석 영역 (임시)"""
    render_section_divider()
    st.markdown("### 📊 분석")
    st.info("분석 기능은 추후 구현 예정입니다.")


def render_settlement_actual():
    """실제정산 페이지 렌더링 (Phase A+)"""
    try:
        # 안전장치: 함수 실행 확인 (DEV용)
        st.caption("✅ Settlement Phase A+ ACTIVE")
        
        # 페이지 제목
        st.markdown("""
        <div style="margin: 0 0 1.0rem 0;">
            <h2 style="color: #ffffff; font-weight: 700; margin: 0;">
                🧾 실제정산
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        # 현재 연/월
        current_year = current_year_kst()
        current_month = current_month_kst()
        
        # 상단 영역 (연/월 선택, KPI 카드)
        year, month, expense_items, total_sales, totals = _render_header_section(
            current_year, current_month
        )
        
        # 비용 입력 영역
        _render_expense_section(year, month, total_sales)
        
        # 분석 영역
        _render_analysis_section()
        
    except Exception as e:
        # 에러 발생 시 최소한의 UI 표시
        st.error(f"❌ 실제정산 페이지 로드 중 오류가 발생했습니다: {str(e)}")
        st.exception(e)
        st.info("""
        **Phase A+ 실제정산 페이지**
        
        - 연/월 선택
        - 총매출 입력
        - 비용 입력 (5개 카테고리)
        - 자동 계산 (총비용, 영업이익, 이익률)
        """)
