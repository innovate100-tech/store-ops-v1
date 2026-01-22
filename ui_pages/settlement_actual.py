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
    upsert_actual_settlement_item,
    load_monthly_sales_total
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
        
        # Phase C.5: input_type 지원 구조로 초기화
        item = {
            'name': template.get('item_name', ''),
            'template_id': template_id,  # Phase C: 필수
            'input_type': None,  # Phase C.5: 복원 시 추론 또는 기본값 설정
            'amount': 0,  # Phase C.5: 항상 초기화
            'rate': 0.0,  # Phase C.5: 항상 초기화
        }
        
        # 카테고리 기본값으로 input_type 설정 (복원 시 덮어쓰기 가능)
        if category in ['재료비', '부가세&카드수수료']:
            item['input_type'] = 'rate'  # 기본값: 매출연동
        else:
            item['input_type'] = 'amount'  # 기본값: 고정비
        
        expense_items[category].append(item)
    
    # Phase C: 저장된 값 복원 + Phase C.5: input_type 추론
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
                    
                    # Phase C.5: 저장된 값 추출
                    saved_amount = saved_item.get('amount')
                    saved_percent = saved_item.get('percent')
                    
                    # Phase C.5: input_type 추론 규칙
                    # 1. amount가 존재하고 > 0이고 percent가 null/0이면 input_type='amount'
                    # 2. percent가 존재하고 > 0이고 amount가 null/0이면 input_type='rate'
                    # 3. 둘 다 있으면 amount 우선
                    # 4. 둘 다 없으면 카테고리 기본값 유지 (이미 설정됨)
                    
                    # None 체크와 값 체크를 분리
                    saved_amount_val = float(saved_amount) if saved_amount is not None else 0.0
                    saved_percent_val = float(saved_percent) if saved_percent is not None else 0.0
                    
                    has_amount = saved_amount is not None and saved_amount_val > 0
                    has_percent = saved_percent is not None and saved_percent_val > 0
                    
                    if has_amount and not has_percent:
                        item['input_type'] = 'amount'
                    elif has_percent and not has_amount:
                        item['input_type'] = 'rate'
                    elif has_amount and has_percent:
                        item['input_type'] = 'amount'  # amount 우선
                    # 둘 다 없으면 카테고리 기본값 유지 (이미 설정됨)
                    
                    # 값 복원 (force_restore 정책 유지)
                    if force_restore:
                        # 강제 복원: 항상 DB 값으로 덮어쓰기
                        if saved_amount is not None:
                            item['amount'] = int(saved_amount or 0)
                        if saved_percent is not None:
                            item['rate'] = float(saved_percent or 0.0)
                    else:
                        # 기본 복원: 값이 비어있을 때만 복원
                        if saved_amount is not None and item.get('amount', 0) == 0:
                            item['amount'] = int(saved_amount or 0)
                        if saved_percent is not None and item.get('rate', 0.0) == 0.0:
                            item['rate'] = float(saved_percent or 0.0)
    
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


def _get_total_sales(year: int, month: int) -> int:
    """총매출 반환 (임시값 0)"""
    key = f"settlement_total_sales_{year}_{month}"
    return int(st.session_state.get(key, 0))


def _set_total_sales(year: int, month: int, value):
    """총매출 설정"""
    key = f"settlement_total_sales_{year}_{month}"
    st.session_state[key] = int(value) if value is not None else 0


def _calculate_category_total(category: str, items: list, total_sales: int) -> float:
    """카테고리별 총액 계산 (Phase C.5: input_type 기준)"""
    category_total = 0.0
    
    for item in items:
        input_type = item.get('input_type', 'amount')  # 기본값: amount
        
        if input_type == 'amount':
            # 금액 입력: amount 직접 사용
            used_amount = float(item.get('amount', 0))
        else:
            # 비율 입력: total_sales * rate / 100
            rate = item.get('rate', 0.0)
            used_amount = (float(total_sales) * rate / 100) if total_sales > 0 else 0.0
        
        category_total += used_amount
    
    return category_total


def _calculate_totals(expense_items: dict, total_sales: int) -> dict:
    """전체 합계 계산"""
    category_totals = {}
    for category, items in expense_items.items():
        category_totals[category] = _calculate_category_total(category, items, total_sales)
    
    total_cost = sum(category_totals.values())
    operating_profit = float(total_sales) - total_cost
    profit_margin = (operating_profit / float(total_sales) * 100) if total_sales > 0 else 0.0
    
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
    
    # 연/월이 변경되면 rerun (템플릿 자동 로드 + Phase D: 자동매출 재계산)
    if selected_year != year or selected_month != month:
        # Phase D: 월 변경 시 자동매출 재계산
        auto_sales_key = f"settlement_auto_sales_{selected_year}_{selected_month}"
        if auto_sales_key not in st.session_state:
            auto_sales = load_monthly_sales_total(store_id, selected_year, selected_month)
            st.session_state[auto_sales_key] = auto_sales
        st.rerun()
    
    render_section_divider()
    
    # 총매출 입력 (Phase D: sales 자동 불러오기)
    st.markdown("### 📊 이번 달 성적표")
    
    # Phase D: sales에서 월매출 자동 계산
    auto_sales_key = f"settlement_auto_sales_{selected_year}_{selected_month}"
    if auto_sales_key not in st.session_state:
        # 첫 진입 시 자동 계산
        auto_sales = load_monthly_sales_total(store_id, selected_year, selected_month)
        st.session_state[auto_sales_key] = auto_sales
    else:
        auto_sales = st.session_state[auto_sales_key]
    
    # Phase D: 초기 주입 정책 (total_sales가 없거나 0이면 자동값으로 채움)
    total_sales_key = f"settlement_total_sales_{selected_year}_{selected_month}"
    if total_sales_key not in st.session_state or st.session_state[total_sales_key] == 0:
        # 자동값으로 초기화
        st.session_state[total_sales_key] = auto_sales
    
    # Phase D: 매출 불러오기 버튼
    sales_col1, sales_col2, sales_col3 = st.columns([3, 1, 1])
    with sales_col1:
        total_sales_input = st.number_input(
            "총매출 (원)",
            min_value=0,
            value=_get_total_sales(selected_year, selected_month),
            step=100000,
            format="%d",
            key=f"settlement_total_sales_input_{selected_year}_{selected_month}"
        )
        _set_total_sales(selected_year, selected_month, total_sales_input)
        
        # Phase D: 자동값 표시
        if auto_sales > 0:
            st.caption(f"💡 sales 월합계(자동): {auto_sales:,.0f}원")
    with sales_col2:
        # Phase D: 매출 불러오기 버튼
        if st.button("🔄 매출 불러오기", key=f"settlement_load_sales_{selected_year}_{selected_month}", use_container_width=True):
            # sales에서 다시 계산
            auto_sales = load_monthly_sales_total(store_id, selected_year, selected_month)
            st.session_state[auto_sales_key] = auto_sales
            st.session_state[total_sales_key] = auto_sales
            st.success(f"✅ sales 월합계로 총매출을 업데이트했습니다: {auto_sales:,.0f}원")
            st.rerun()
    with sales_col3:
        # Phase D: 자동값으로 되돌리기 버튼
        if st.button("↩️ 자동값으로", key=f"settlement_reset_sales_{selected_year}_{selected_month}", use_container_width=True):
            if auto_sales_key in st.session_state:
                st.session_state[total_sales_key] = st.session_state[auto_sales_key]
                st.success(f"✅ 자동값으로 되돌렸습니다: {st.session_state[auto_sales_key]:,.0f}원")
                st.rerun()
            else:
                st.warning("자동값이 없습니다. '매출 불러오기'를 먼저 클릭하세요.")
    
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
                
                # 모든 항목 순회하며 저장 (Phase C.5: input_type 기준)
                for category, items in expense_items.items():
                    for item in items:
                        template_id = item.get('template_id')
                        if not template_id:
                            continue
                        
                        input_type = item.get('input_type', 'amount')  # 기본값: amount
                        
                        if input_type == 'amount':
                            # 금액 입력: amount 저장, percent는 None (또는 0)
                            amount = item.get('amount', 0)
                            upsert_actual_settlement_item(
                                store_id, selected_year, selected_month,
                                template_id, amount=float(int(amount)), percent=None, status='draft'
                            )
                            saved_count += 1
                        else:
                            # 비율 입력: percent 저장, amount는 None (또는 0)
                            percent = item.get('rate', 0.0)
                            upsert_actual_settlement_item(
                                store_id, selected_year, selected_month,
                                template_id, amount=None, percent=percent, status='draft'
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
    
    # Phase D: sales 월합계 진단 (DEV 모드에서만)
    try:
        from src.auth import is_dev_mode
        if is_dev_mode():
            with st.expander("🔍 sales 월합계 진단 (DEV)", expanded=False):
                st.markdown("### 진단 정보")
                st.write(f"**store_id:** `{store_id}`")
                st.write(f"**year/month:** {selected_year}-{selected_month}")
                
                # 날짜 범위 계산
                from src.utils.time_utils import now_kst
                from datetime import datetime
                from zoneinfo import ZoneInfo
                KST = ZoneInfo("Asia/Seoul")
                start_kst = datetime(selected_year, selected_month, 1, 0, 0, 0, tzinfo=KST)
                if selected_month == 12:
                    end_kst = datetime(selected_year + 1, 1, 1, 0, 0, 0, tzinfo=KST)
                else:
                    end_kst = datetime(selected_year, selected_month + 1, 1, 0, 0, 0, tzinfo=KST)
                start_date_str = start_kst.date().isoformat()
                end_date_str = end_kst.date().isoformat()
                
                st.write(f"**필터 범위:** `date >= {start_date_str} AND date < {end_date_str}`")
                
                # 실제 조회 테스트
                try:
                    from src.storage_supabase import get_read_client
                    supabase = get_read_client()
                    if supabase:
                        result = supabase.table("sales")\
                            .select("total_sales, date")\
                            .eq("store_id", store_id)\
                            .gte("date", start_date_str)\
                            .lt("date", end_date_str)\
                            .execute()
                        
                        row_count = len(result.data) if result.data else 0
                        total_sum = sum(float(row.get('total_sales', 0) or 0) for row in (result.data or []))
                        
                        st.write(f"**조회 row count:** {row_count}")
                        st.write(f"**합계 값:** {total_sum:,.0f}원")
                        st.write(f"**자동값 (session_state):** {auto_sales:,.0f}원")
                        
                        if result.data:
                            st.write("**조회된 데이터 (최대 10건):**")
                            import pandas as pd
                            df = pd.DataFrame(result.data[:10])
                            st.dataframe(df, use_container_width=True)
                    else:
                        st.error("Supabase client를 가져올 수 없습니다.")
                except Exception as e:
                    st.error(f"진단 조회 실패: {str(e)}")
                    st.exception(e)
    except Exception:
        pass  # DEV 모드가 아니면 무시
    
    return selected_year, selected_month, expense_items, total_sales, totals


def _render_expense_category(
    store_id: str,
    category: str,
    category_info: dict,
    items: list,
    total_sales: int,
    year: int,
    month: int
):
    """비용 카테고리별 입력 UI (Phase C.5: input_type 선택형)"""
    # Phase C.5: is_linked는 더 이상 사용하지 않지만, 기본값 설정용으로 유지
    is_linked_default = category_info['type'] == 'linked'  # 기본값 설정용
    
    # 카테고리 헤더
    st.markdown(f"""
    <div style="margin: 1.5rem 0 0.5rem 0;">
        <h3 style="color: #ffffff; font-weight: 600; margin: 0;">
            {category_info['icon']} {category}
        </h3>
    </div>
    """, unsafe_allow_html=True)
    st.caption(category_info['description'])
    
    # 카테고리 총액 표시 (Phase C.5: input_type 기준 계산)
    category_total = _calculate_category_total(category, items, total_sales)
    if category_total > 0:
        # Phase C.5: input_type 기준으로 표시 (단순화: 총액만 표시)
        st.markdown(f"""
        <div style="text-align: right; margin: 0.5rem 0;">
            <strong style="color: #667eea; font-size: 1.1rem;">
                카테고리 합계: {category_total:,.0f}원
            </strong>
        </div>
        """, unsafe_allow_html=True)
    
    # 기존 항목 표시 및 수정 (Phase C.5: input_type 선택형)
    if items:
        for idx, item in enumerate(items):
            # Phase C.5: input_type 기본값 설정 (없으면 카테고리 기본값)
            if 'input_type' not in item or item.get('input_type') is None:
                if category in ['재료비', '부가세&카드수수료']:
                    item['input_type'] = 'rate'
                else:
                    item['input_type'] = 'amount'
            
            col1, col2, col3, col4 = st.columns([2, 1.5, 2, 1])
            with col1:
                item_name_key = f"settlement_item_name_{category}_{idx}_{year}_{month}"
                item_name = st.text_input(
                    "항목명",
                    value=item.get('name', ''),
                    key=item_name_key
                )
            with col2:
                # Phase C.5: 입력방식 선택 라디오
                input_type_key = f"settlement_input_type_{category}_{idx}_{year}_{month}"
                input_type_options = ["금액(원)", "%(매출대비)"]
                input_type_index = 0 if item.get('input_type') == 'amount' else 1
                selected_input_type_label = st.radio(
                    "입력방식",
                    options=input_type_options,
                    index=input_type_index,
                    key=input_type_key,
                    horizontal=True,
                    label_visibility="collapsed"
                )
                selected_input_type = 'amount' if selected_input_type_label == "금액(원)" else 'rate'
                
                # input_type 변경 감지 및 업데이트
                if selected_input_type != item.get('input_type'):
                    expense_items = _initialize_expense_items(store_id, year, month)
                    if idx < len(expense_items[category]):
                        expense_items[category][idx]['input_type'] = selected_input_type
                        # 값은 유지 (amount와 rate 모두 보존)
            with col3:
                # Phase C.5: 선택된 input_type에 따라 입력칸 표시
                if selected_input_type == 'amount':
                    # 금액 입력
                    amount_key = f"settlement_item_amount_{category}_{idx}_{year}_{month}"
                    amount = st.number_input(
                        "금액 (원)",
                        min_value=0,
                        value=int(item.get('amount', 0)),
                        step=1000,
                        format="%d",
                        key=amount_key
                    )
                    # 금액 업데이트
                    if amount != item.get('amount', 0):
                        expense_items = _initialize_expense_items(store_id, year, month)
                        if idx < len(expense_items[category]):
                            expense_items[category][idx]['amount'] = int(amount)
                else:
                    # 비율 입력
                    rate_key = f"settlement_item_rate_{category}_{idx}_{year}_{month}"
                    rate = st.number_input(
                        "비율 (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(item.get('rate', 0.0)),
                        step=0.1,
                        format="%.2f",
                        key=rate_key
                    )
                    calculated = (float(total_sales) * rate / 100) if total_sales > 0 else 0.0
                    st.caption(f"→ {calculated:,.0f}원")
                    # 비율 업데이트
                    if rate != item.get('rate', 0.0):
                        expense_items = _initialize_expense_items(store_id, year, month)
                        if idx < len(expense_items[category]):
                            expense_items[category][idx]['rate'] = float(rate)
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
                                    # Phase C.5: input_type 기준으로 item_type 결정
                                    current_input_type = expense_items[category][idx].get('input_type', 'amount')
                                    item_type = 'percent' if current_input_type == 'rate' else 'normal'
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
    
    # 새 항목 추가 (Phase C.5: input_type 선택형)
    st.markdown("---")
    add_col1, add_col2, add_col3, add_col4 = st.columns([2, 1.5, 2, 1])
    with add_col1:
        new_name = st.text_input(
            "항목명",
            key=f"settlement_new_name_{category}_{year}_{month}",
            placeholder="예: 월세, 관리비 등"
        )
    with add_col2:
        # Phase C.5: 새 항목 입력방식 선택
        new_input_type_key = f"settlement_new_input_type_{category}_{year}_{month}"
        new_input_type_options = ["금액(원)", "%(매출대비)"]
        # 기본값: 카테고리 기본값
        new_input_type_default = 0 if category not in ['재료비', '부가세&카드수수료'] else 1
        new_input_type_label = st.radio(
            "입력방식",
            options=new_input_type_options,
            index=new_input_type_default,
            key=new_input_type_key,
            horizontal=True,
            label_visibility="collapsed"
        )
        new_input_type = 'amount' if new_input_type_label == "금액(원)" else 'rate'
    with add_col3:
        # Phase C.5: 선택된 input_type에 따라 입력칸 표시
        if new_input_type == 'amount':
            new_value = st.number_input(
                "금액 (원)",
                min_value=0,
                value=0,
                step=1000,
                format="%d",
                key=f"settlement_new_amount_{category}_{year}_{month}"
            )
        else:
            new_value = st.number_input(
                "비율 (%)",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=0.1,
                format="%.2f",
                key=f"settlement_new_rate_{category}_{year}_{month}"
            )
    with add_col4:
        if st.button("➕ 추가", key=f"settlement_add_{category}_{year}_{month}", use_container_width=True):
            if new_name.strip():
                expense_items = _initialize_expense_items(store_id, year, month)
                
                # 템플릿에 저장 (Phase B)
                try:
                    item_type = 'percent' if new_input_type == 'rate' else 'normal'
                    sort_order = len(expense_items[category])  # 현재 항목 수를 sort_order로 사용
                    save_cost_item_template(
                        store_id, category, new_name.strip(),
                        item_type=item_type, sort_order=sort_order
                    )
                    st.caption("✅ 템플릿에 저장됨")
                except Exception as e:
                    st.error(f"템플릿 저장 실패: {e}")
                
                # Phase C.5: session_state에 추가 (input_type 포함)
                new_item = {
                    'name': new_name.strip(),
                    'input_type': new_input_type,
                    'amount': int(new_value) if new_input_type == 'amount' else 0,
                    'rate': float(new_value) if new_input_type == 'rate' else 0.0,
                }
                expense_items[category].append(new_item)
                st.rerun()
            else:
                st.error("항목명을 입력해주세요.")


def _render_expense_section(store_id: str, year: int, month: int, total_sales: int):
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
        st.caption("✅ Settlement Phase D ACTIVE")
        
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
        **Phase D 실제정산 페이지**
        
        - 연/월 선택
        - 총매출 입력 (sales 테이블 자동 불러오기)
        - 비용 입력 (5개 카테고리, 항목별 입력방식 선택)
        - 자동 계산 (총비용, 영업이익, 이익률)
        - 템플릿 저장/자동 로드
        - Soft Delete
        - 항목별 금액/% 선택형 입력
        - sales 월합계 자동 불러오기
        """)
