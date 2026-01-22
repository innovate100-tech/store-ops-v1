"""
실제정산 페이지 (Phase B - 템플릿 저장/자동 로드)
UI 구조 + 상태관리 + 자동 계산 + 고정비 개념 + 템플릿 관리
"""
from src.bootstrap import bootstrap
import streamlit as st
from src.utils.time_utils import current_year_kst, current_month_kst
from src.ui_helpers import render_section_divider
from src.ui.guards import require_auth_and_store
from src.storage_supabase import (
    load_cost_item_templates,
    save_cost_item_template,
    soft_delete_cost_item_template,
    load_actual_settlement_items,
    upsert_actual_settlement_item
)

# 공통 설정 적용
bootstrap(page_title="Settlement Actual")


def _load_templates_to_session_state(store_id: str, year: int, month: int, force: bool = False, restore_values: bool = False, force_restore: bool = False):
    """
    템플릿을 session_state로 로드 + 저장된 값 복원 (Phase C)
    
    Args:
        store_id: 매장 ID
        year: 연도
        month: 월
        force: True면 기존 session_state를 덮어씀
        restore_values: True면 저장된 값(actual_settlement_items)을 복원
    
    Returns:
        dict: expense_items 구조
    """
    key = f"settlement_expense_items_{year}_{month}"
    
    # force=False이고 이미 존재하면 덮어쓰지 않음
    if not force and key in st.session_state:
        return st.session_state[key]
    
    # 템플릿 로드
    templates = load_cost_item_templates(store_id)
    
    # 카테고리별로 그룹화
    expense_items = {
        '임차료': [],
        '인건비': [],
        '재료비': [],
        '공과금': [],
        '부가세&카드수수료': [],
    }
    
    for template in templates:
        category = template.get('category')
        if category not in expense_items:
            continue
        
        # 템플릿에서 항목 생성 (Phase C: template_id 필수 포함)
        template_id = template.get('id')
        if not template_id:
            continue  # template_id가 없으면 건너뛰기
        
        item = {
            'name': template.get('item_name', ''),
            'template_id': template_id,  # Phase C: 필수
        }
        
        # item_type에 따라 amount 또는 rate 설정
        item_type = template.get('item_type', 'normal')
        if category in ['재료비', '부가세&카드수수료']:
            # 매출연동: rate 사용
            item['rate'] = 0.0
        else:
            # 고정비: amount 사용
            item['amount'] = 0
        
        expense_items[category].append(item)
    
    # Phase C: 저장된 값 복원
    if restore_values:
        saved_items = load_actual_settlement_items(store_id, year, month)
        # template_id를 키로 하는 딕셔너리 생성
        saved_dict = {item.get('template_id'): item for item in saved_items if item.get('template_id')}
        
        # 각 카테고리별 항목에 저장된 값 주입
        for category, items in expense_items.items():
            for item in items:
                template_id = item.get('template_id')
                if template_id and template_id in saved_dict:
                    saved_item = saved_dict[template_id]
                    # force_restore=True면 항상 복원, 아니면 값이 비어있을 때만 복원
                    if category in ['재료비', '부가세&카드수수료']:
                        # 매출연동: percent 복원
                        current_rate = item.get('rate', 0.0)
                        saved_percent = saved_item.get('percent')
                        if saved_percent is not None:
                            if force_restore or current_rate == 0.0:
                                item['rate'] = float(saved_percent)
                    else:
                        # 고정비: amount 복원
                        current_amount = item.get('amount', 0)
                        saved_amount = saved_item.get('amount')
                        if saved_amount is not None:
                            if force_restore or current_amount == 0:
                                item['amount'] = int(saved_amount)
    
    # session_state에 저장
    st.session_state[key] = expense_items
    return expense_items


def _initialize_expense_items(store_id: str, year: int, month: int, force: bool = False, restore_values: bool = True, force_restore: bool = False):
    """
    비용 항목 초기화 (템플릿에서 로드 + 저장된 값 복원, Phase C)
    
    Args:
        store_id: 매장 ID
        year: 연도
        month: 월
        force: True면 템플릿에서 강제로 다시 로드
        restore_values: True면 저장된 값 복원 (기본값: True)
        force_restore: True면 저장된 값으로 강제 덮어쓰기 (기본값: False)
    
    Returns:
        dict: expense_items 구조
    """
    key = f"settlement_expense_items_{year}_{month}"
    
    # force=False이고 이미 존재하면 그대로 반환
    if not force and key in st.session_state:
        return st.session_state[key]
    
    # 템플릿에서 로드 + 저장된 값 복원
    return _load_templates_to_session_state(store_id, year, month, force=True, restore_values=restore_values, force_restore=force_restore)


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


def _render_header_section(store_id: str, year: int, month: int):
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
        # 템플릿 리셋 버튼 (Phase B)
        if st.button("🔄 템플릿 다시 불러오기", key="settlement_reset_templates", use_container_width=True):
            # 강제로 템플릿에서 다시 로드 (값 복원 포함)
            _initialize_expense_items(store_id, selected_year, selected_month, force=True, restore_values=True)
            st.success("✅ 템플릿을 다시 불러왔습니다. (저장된 값도 복원됩니다)")
            st.rerun()
    
    # 연/월이 변경되면 rerun (템플릿 자동 로드)
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
        format="%.0f",  # Phase C: float 경고 해결
        key=f"settlement_total_sales_input_{selected_year}_{selected_month}"
    )
    _set_total_sales(selected_year, selected_month, total_sales_input)
    
    # KPI 카드
    expense_items = _initialize_expense_items(store_id, selected_year, selected_month)
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
    col1, col2, col3 = st.columns([1, 2, 1])
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
    with col3:
        # Phase C: 저장값 불러오기 버튼
        if st.button("📥 저장값 불러오기", key="settlement_load_saved_values", use_container_width=True):
            # 강제로 저장된 값 복원 (덮어쓰기)
            _initialize_expense_items(store_id, selected_year, selected_month, force=True, restore_values=True, force_restore=True)
            st.success("✅ 저장된 값을 불러왔습니다. (현재 입력값이 덮어쓰기됩니다)")
            st.rerun()
    
    # Phase C: 이번달 저장 버튼
    st.markdown('<div style="margin: 0.5rem 0;"></div>', unsafe_allow_html=True)
    save_col1, save_col2 = st.columns([1, 4])
    with save_col1:
        if st.button("💾 이번달 저장(draft)", key="settlement_save_month", type="primary", use_container_width=True):
            try:
                expense_items = _initialize_expense_items(store_id, selected_year, selected_month)
                saved_count = 0
                
                # 모든 항목 순회하며 저장
                for category, items in expense_items.items():
                    is_linked = category in ['재료비', '부가세&카드수수료']
                    for item in items:
                        template_id = item.get('template_id')
                        if not template_id:
                            continue
                        
                        if is_linked:
                            # 매출연동: percent 저장 (0이어도 저장)
                            percent = item.get('rate', 0.0)
                            upsert_actual_settlement_item(
                                store_id, selected_year, selected_month,
                                template_id, percent=percent, status='draft'
                            )
                            saved_count += 1
                        else:
                            # 고정비: amount 저장 (0이어도 저장)
                            amount = item.get('amount', 0)
                            upsert_actual_settlement_item(
                                store_id, selected_year, selected_month,
                                template_id, amount=float(amount), status='draft'
                            )
                            saved_count += 1
                
                if saved_count > 0:
                    st.success(f"✅ {saved_count}개 항목이 저장되었습니다.")
                else:
                    st.info("💡 저장할 항목이 없습니다. (템플릿 항목이 없습니다)")
                st.rerun()
            except Exception as e:
                st.error(f"❌ 저장 실패: {str(e)}")
    
    render_section_divider()
    
    return selected_year, selected_month, expense_items, total_sales, totals


def _render_expense_category(
    store_id: str,
    category: str,
    category_info: dict,
    items: list,
    total_sales: float,
    year: int,
    month: int
):
    """비용 카테고리별 입력 UI (Phase B: 템플릿 저장/삭제 포함)"""
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
                    # 비율 업데이트 (템플릿에는 저장하지 않음, 월별 값이므로)
                    if rate != item.get('rate', 0.0):
                        expense_items = _initialize_expense_items(store_id, year, month)
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
                        format="%.0f",  # Phase C: float 경고 해결
                        key=amount_key
                    )
                    # 금액 업데이트 (템플릿에는 저장하지 않음, 월별 값이므로)
                    if amount != item.get('amount', 0):
                        expense_items = _initialize_expense_items(store_id, year, month)
                        if idx < len(expense_items[category]):
                            expense_items[category][idx]['amount'] = amount
            with col3:
                col_save, col_delete = st.columns(2)
                with col_save:
                    # 항목명 수정 시 템플릿 업데이트 버튼 (Phase B)
                    if st.button("💾", key=f"settlement_save_{category}_{idx}_{year}_{month}", help="템플릿 저장"):
                        expense_items = _initialize_expense_items(store_id, year, month)
                        if idx < len(expense_items[category]):
                            current_item = expense_items[category][idx]
                            old_name = current_item.get('name', '')
                            # 위젯에서 최신 값 가져오기
                            new_name = st.session_state.get(item_name_key, old_name)
                            
                            if new_name.strip() and new_name != old_name:
                                try:
                                    item_type = 'percent' if is_linked else 'normal'
                                    save_cost_item_template(
                                        store_id, category, new_name.strip(),
                                        item_type=item_type, sort_order=idx
                                    )
                                    # 기존 항목명이 있고 다르면 soft delete
                                    if old_name and old_name != new_name.strip():
                                        soft_delete_cost_item_template(store_id, category, old_name)
                                    expense_items[category][idx]['name'] = new_name.strip()
                                    st.caption("✅ 템플릿 업데이트됨")
                                except Exception as e:
                                    st.error(f"템플릿 업데이트 실패: {e}")
                        st.rerun()
                with col_delete:
                    if st.button("🗑️", key=f"settlement_delete_{category}_{idx}_{year}_{month}", help="삭제"):
                        expense_items = _initialize_expense_items(store_id, year, month)
                        if idx < len(expense_items[category]):
                            item_to_delete = expense_items[category][idx]
                            item_name_to_delete = item_to_delete.get('name', '')
                            
                            # Soft delete (Phase B)
                            if item_name_to_delete:
                                try:
                                    soft_delete_cost_item_template(store_id, category, item_name_to_delete)
                                    st.caption("✅ 템플릿에서 삭제됨")
                                except Exception as e:
                                    st.error(f"템플릿 삭제 실패: {e}")
                            
                            # session_state에서도 제거
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
                format="%.0f",  # Phase C: float 경고 해결
                key=f"settlement_new_amount_{category}_{year}_{month}"
            )
    with add_col3:
        if st.button("➕ 추가", key=f"settlement_add_{category}_{year}_{month}", use_container_width=True):
            if new_name.strip():
                expense_items = _initialize_expense_items(store_id, year, month)
                
                # 템플릿에 저장 (Phase B)
                try:
                    item_type = 'percent' if is_linked else 'normal'
                    sort_order = len(expense_items[category])  # 현재 항목 수를 sort_order로 사용
                    save_cost_item_template(
                        store_id, category, new_name.strip(),
                        item_type=item_type, sort_order=sort_order
                    )
                    st.caption("✅ 템플릿에 저장됨")
                except Exception as e:
                    st.error(f"템플릿 저장 실패: {e}")
                
                # session_state에 추가
                new_item = {'name': new_name.strip()}
                if is_linked:
                    new_item['rate'] = new_value
                else:
                    new_item['amount'] = int(new_value)
                expense_items[category].append(new_item)
                st.rerun()
            else:
                st.error("항목명을 입력해주세요.")


def _render_expense_section(store_id: str, year: int, month: int, total_sales: float):
    """비용 입력 영역"""
    st.markdown("### 💸 비용 입력")
    
    expense_items = _initialize_expense_items(store_id, year, month)
    
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
            store_id,
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
    """실제정산 페이지 렌더링 (Phase B - 템플릿 저장/자동 로드)"""
    try:
        # 안전장치: 함수 실행 확인 (DEV용)
        st.caption("✅ Settlement Phase B ACTIVE")
        
        # 인증 및 store_id 확인 (Phase B)
        user_id, store_id = require_auth_and_store()
        
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
        
        # 상단 영역 (연/월 선택, KPI 카드, 템플릿 리셋 버튼)
        year, month, expense_items, total_sales, totals = _render_header_section(
            store_id, current_year, current_month
        )
        
        # 비용 입력 영역 (템플릿 저장/삭제 포함)
        _render_expense_section(store_id, year, month, total_sales)
        
        # 분석 영역
        _render_analysis_section()
        
    except Exception as e:
        # 에러 발생 시 최소한의 UI 표시
        st.error(f"❌ 실제정산 페이지 로드 중 오류가 발생했습니다: {str(e)}")
        st.exception(e)
        st.info("""
        **Phase B 실제정산 페이지**
        
        - 연/월 선택
        - 총매출 입력
        - 비용 입력 (5개 카테고리)
        - 자동 계산 (총비용, 영업이익, 이익률)
        - 템플릿 저장/자동 로드
        - Soft Delete
        """)
