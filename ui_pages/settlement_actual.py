"""
실제정산 페이지 (Phase B - 템플릿 저장/자동 로드)
UI 구조 + 상태관리 + 자동 계산 + 고정비 개념 + 템플릿 관리
"""
from src.bootstrap import bootstrap
import streamlit as st
import pandas as pd
import logging
from src.utils.time_utils import current_year_kst, current_month_kst

# Phase G: 로깅 설정
logger = logging.getLogger(__name__)
from src.ui_helpers import render_section_divider
from src.ui.guards import require_auth_and_store
from src.storage_supabase import (
    load_cost_item_templates,
    save_cost_item_template,
    soft_delete_cost_item_template,
    load_actual_settlement_items,
    upsert_actual_settlement_item,
    load_monthly_sales_total,
    load_csv,
    load_expense_structure,
    get_month_settlement_status,
    set_month_settlement_status,
    load_available_settlement_months,
    load_monthly_settlement_snapshot
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


def _render_header_section(store_id: str, year: int, month: int, readonly: bool = False):
    """상단 영역: 연/월 선택, KPI 카드, 상태 배지 (Phase F: readonly 지원)"""
    # Phase H: 히스토리에서 이동한 경우 위젯 키를 강제로 변경하여 새 위젯으로 인식
    # 위젯이 이미 생성되어 있으면 세션 상태 변경만으로는 업데이트 안 됨
    widget_key_suffix = ""
    if "settlement_force_widget_update" in st.session_state:
        # 타임스탬프를 추가하여 새로운 위젯으로 인식
        import time
        widget_key_suffix = f"_{int(time.time())}"
        # 플래그 제거 (한 번만 적용)
        del st.session_state["settlement_force_widget_update"]
        # 네비게이션 플래그도 제거
        if "settlement_navigate_to_year" in st.session_state:
            del st.session_state["settlement_navigate_to_year"]
        if "settlement_navigate_to_month" in st.session_state:
            del st.session_state["settlement_navigate_to_month"]
    
    # 연/월 선택
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        selected_year = st.number_input(
            "연도",
            min_value=2020,
            max_value=2100,
            value=year,
            key=f"settlement_year{widget_key_suffix}"
        )
    with col2:
        selected_month = st.number_input(
            "월",
            min_value=1,
            max_value=12,
            value=month,
            key=f"settlement_month{widget_key_suffix}"
        )
    with col3:
        # 템플릿 리셋 버튼 (Phase B)
        # readonly는 아래에서 확인하므로, 여기서는 일단 활성화 (rerun 후 적용됨)
        if st.button("🔄 템플릿 다시 불러오기", key="settlement_reset_templates", 
                     use_container_width=True):
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
    
    # Phase F: 월별 정산 상태 확인 (selected_year/month 기준, 여기서 확인)
    month_status = get_month_settlement_status(store_id, selected_year, selected_month)
    readonly = readonly or (month_status == 'final')
    
    # 총매출 입력 (Phase D: sales 자동 불러오기, Phase F: readonly 지원)
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
    
    # Phase D: 매출 불러오기 버튼 (Phase F: readonly 지원)
    sales_col1, sales_col2, sales_col3 = st.columns([3, 1, 1])
    with sales_col1:
        total_sales_input = st.number_input(
            "총매출 (원)",
            min_value=0,
            value=_get_total_sales(selected_year, selected_month),
            step=100000,
            format="%d",
            disabled=readonly,  # Phase F: readonly일 때 비활성화
            key=f"settlement_total_sales_input_{selected_year}_{selected_month}"
        )
        if not readonly:
            _set_total_sales(selected_year, selected_month, total_sales_input)
        
        # Phase D: 자동값 표시
        if auto_sales > 0:
            st.caption(f"💡 sales 월합계(자동): {auto_sales:,.0f}원")
    with sales_col2:
        # Phase D: 매출 불러오기 버튼 (Phase F: readonly일 때 비활성화)
        # Phase G: 캐시 무효화 후 즉시 재조회
        if st.button("🔄 매출 불러오기", key=f"settlement_load_sales_{selected_year}_{selected_month}", 
                     disabled=readonly, use_container_width=True):
            try:
                # Phase G: 캐시 무효화
                load_monthly_sales_total.clear()
                # Phase G: 최신값 재조회 (캐시 우회)
                auto_sales = load_monthly_sales_total(store_id, selected_year, selected_month)
                # Phase G: session_state 갱신
                st.session_state[auto_sales_key] = auto_sales
                st.session_state[total_sales_key] = auto_sales
                st.success(f"✅ sales 월합계로 총매출을 업데이트했습니다: {auto_sales:,.0f}원")
                st.rerun()
            except Exception as e:
                # Phase G: 예외 발생 시 기존 값 유지, 에러 메시지 표시
                st.error(f"❌ 매출 불러오기 실패: {str(e)}")
                logger.error(f"Failed to reload monthly sales: {e}", exc_info=True)
    with sales_col3:
        # Phase D: 자동값으로 되돌리기 버튼 (Phase F: readonly일 때 비활성화)
        if st.button("↩️ 자동값으로", key=f"settlement_reset_sales_{selected_year}_{selected_month}", 
                     disabled=readonly, use_container_width=True):
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
    
    # Phase F: 상태 배지 및 확정/해제 버튼
    st.markdown('<div style="margin: 1rem 0;"></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        # Phase F: 상태 배지
        if month_status == 'final':
            st.markdown("""
            <div style="padding: 0.5rem 1rem; background-color: #10b981; border-radius: 0.5rem; display: inline-block;">
                <span style="color: #ffffff; font-weight: 600;">🟢 확정됨</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="padding: 0.5rem 1rem; background-color: #667eea; border-radius: 0.5rem; display: inline-block;">
                <span style="color: #ffffff; font-weight: 600;">🟡 작성중</span>
            </div>
            """, unsafe_allow_html=True)
    with col2:
        if month_status == 'final':
            st.markdown("""
            <div style="padding: 0.5rem 0;">
                <span style="color: #ffffff; font-size: 1rem;">
                    이번 달 정산이 확정되었습니다. (읽기 전용)
                </span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="padding: 0.5rem 0;">
                <span style="color: #ffffff; font-size: 1rem;">
                    이번 달 성적표를 작성 중입니다.
                </span>
            </div>
            """, unsafe_allow_html=True)
    with col3:
        # Phase F: 확정/해제 버튼
        if month_status == 'draft':
            if st.button("✅ 이번달 확정", key="settlement_finalize", type="primary", use_container_width=True):
                try:
                    # Phase F: 확정 전에 현재 입력값을 먼저 저장
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
                                # 금액 입력: amount 저장, percent는 None
                                amount = item.get('amount', 0)
                                upsert_actual_settlement_item(
                                    store_id, selected_year, selected_month,
                                    template_id, amount=float(int(amount)), percent=None
                                )
                                saved_count += 1
                            elif input_type == 'rate':
                                # 비율 입력: percent 저장, amount는 None
                                rate = item.get('rate', 0)
                                upsert_actual_settlement_item(
                                    store_id, selected_year, selected_month,
                                    template_id, amount=None, percent=float(rate)
                                )
                                saved_count += 1
                    
                    # 저장 완료 후 확정 처리
                    if saved_count > 0:
                        affected = set_month_settlement_status(store_id, selected_year, selected_month, 'final')
                        if affected >= 0:
                            # Phase F: 캐시 강제 클리어 후 즉시 상태 재확인
                            get_month_settlement_status.clear()
                            # 확정 후 DB 값 복원 (force_restore)
                            _initialize_expense_items(store_id, selected_year, selected_month, force=True, restore_values=True, force_restore=True)
                            st.success(f"✅ 이번달 정산이 확정되었습니다. ({saved_count}개 항목 저장됨, 읽기 전용)")
                            st.rerun()
                        else:
                            st.warning("⚠️ 확정 처리 중 오류가 발생했습니다.")
                    else:
                        st.warning("⚠️ 저장할 항목이 없습니다. 먼저 항목을 입력하세요.")
                except Exception as e:
                    st.error(f"❌ 확정 실패: {str(e)}")
                    st.exception(e)
        else:
            # Phase F: 확정 해제 버튼 (manager 이상만)
            user_role = st.session_state.get('user_role', 'manager')
            if user_role in ['manager', 'admin']:
                if st.button("🔓 확정 해제", key="settlement_unfinalize", use_container_width=True):
                    try:
                        affected = set_month_settlement_status(store_id, selected_year, selected_month, 'draft')
                        # Phase F: 캐시 강제 클리어 후 즉시 상태 재확인
                        get_month_settlement_status.clear()
                        st.warning("⚠️ 확정이 해제되었습니다. 다시 수정할 수 있습니다.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 확정 해제 실패: {str(e)}")
    
    # Phase C: 저장값 불러오기 버튼 (Phase F: readonly일 때 비활성화)
    st.markdown('<div style="margin: 0.5rem 0;"></div>', unsafe_allow_html=True)
    if st.button("📥 저장값 불러오기", key="settlement_load_saved_values", disabled=readonly, use_container_width=True):
        # 강제로 저장된 값 복원 (덮어쓰기)
        _initialize_expense_items(store_id, selected_year, selected_month, force=True, restore_values=True, force_restore=True)
        st.success("✅ 저장된 값을 불러왔습니다. (현재 입력값이 덮어쓰기됩니다)")
        st.rerun()
    
    # Phase C: 이번달 저장 버튼 (Phase F: readonly일 때 숨김)
    if not readonly:
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
    
    return selected_year, selected_month, expense_items, total_sales, totals, readonly


def _render_expense_category(
    store_id: str,
    category: str,
    category_info: dict,
    items: list,
    total_sales: int,
    year: int,
    month: int,
    readonly: bool = False
):
    """비용 카테고리별 입력 UI (Phase C.5: input_type 선택형, Phase F: readonly 지원)"""
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
                    disabled=readonly,  # Phase F: readonly일 때 비활성화
                    key=item_name_key
                )
            with col2:
                # Phase C.5: 입력방식 선택 라디오 (Phase F: readonly일 때 비활성화)
                input_type_key = f"settlement_input_type_{category}_{idx}_{year}_{month}"
                input_type_options = ["금액(원)", "%(매출대비)"]
                input_type_index = 0 if item.get('input_type') == 'amount' else 1
                selected_input_type_label = st.radio(
                    "입력방식",
                    options=input_type_options,
                    index=input_type_index,
                    key=input_type_key,
                    horizontal=True,
                    disabled=readonly,  # Phase F: readonly일 때 비활성화
                    label_visibility="collapsed"
                )
                selected_input_type = 'amount' if selected_input_type_label == "금액(원)" else 'rate'
                
                # input_type 변경 감지 및 업데이트 (readonly일 때는 업데이트 안 함)
                if not readonly and selected_input_type != item.get('input_type'):
                    expense_items = _initialize_expense_items(store_id, year, month)
                    if idx < len(expense_items[category]):
                        expense_items[category][idx]['input_type'] = selected_input_type
                        # 값은 유지 (amount와 rate 모두 보존)
            with col3:
                # Phase C.5: 선택된 input_type에 따라 입력칸 표시 (Phase F: readonly일 때 비활성화)
                if selected_input_type == 'amount':
                    # 금액 입력
                    amount_key = f"settlement_item_amount_{category}_{idx}_{year}_{month}"
                    amount = st.number_input(
                        "금액 (원)",
                        min_value=0,
                        value=int(item.get('amount', 0)),
                        step=1000,
                        format="%d",
                        disabled=readonly,  # Phase F: readonly일 때 비활성화
                        key=amount_key
                    )
                    # 금액 업데이트 (readonly일 때는 업데이트 안 함)
                    if not readonly and amount != item.get('amount', 0):
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
                        disabled=readonly,  # Phase F: readonly일 때 비활성화
                        key=rate_key
                    )
                    calculated = (float(total_sales) * rate / 100) if total_sales > 0 else 0.0
                    st.caption(f"→ {calculated:,.0f}원")
                    # 비율 업데이트 (readonly일 때는 업데이트 안 함)
                    if not readonly and rate != item.get('rate', 0.0):
                        expense_items = _initialize_expense_items(store_id, year, month)
                        if idx < len(expense_items[category]):
                            expense_items[category][idx]['rate'] = float(rate)
            with col4:
                col_save, col_delete = st.columns(2)
                with col_save:
                    # 항목명 수정 시 템플릿 업데이트 버튼 (Phase B, Phase F: readonly일 때 비활성화)
                    if st.button("💾", key=f"settlement_save_{category}_{idx}_{year}_{month}", 
                                 disabled=readonly, help="템플릿 저장"):
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
                    if st.button("🗑️", key=f"settlement_delete_{category}_{idx}_{year}_{month}", 
                                 disabled=readonly, help="삭제"):
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
    
    # 새 항목 추가 (Phase C.5: input_type 선택형, Phase F: readonly일 때 숨김)
    if not readonly:
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


def _render_expense_section(store_id: str, year: int, month: int, total_sales: int, readonly: bool = False):
    """비용 입력 영역 (Phase F: readonly 지원)"""
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
    
    # 각 카테고리 렌더링 (Phase F: readonly 전달)
    for category, info in categories.items():
        _render_expense_category(
            store_id,
            category,
            info,
            expense_items[category],
            total_sales,
            year,
            month,
            readonly
        )
        st.markdown('<div style="margin: 1rem 0;"></div>', unsafe_allow_html=True)


def _load_targets_for_month(store_id: str, year: int, month: int):
    """
    Phase E: 목표 데이터 로드 (매출 + 비용구조)
    
    Returns:
        dict: {
            'target_sales': int,
            'target_expense_structure': pd.DataFrame,
            'has_targets': bool
        }
    """
    try:
        # 목표 매출 로드
        targets_df = load_csv('targets.csv', default_columns=[
            '연도', '월', '목표매출', '목표원가율', '목표인건비율',
            '목표임대료율', '목표기타비용율', '목표순이익률'
        ])
        
        target_sales = 0
        if not targets_df.empty:
            target_row = targets_df[(targets_df['연도'] == year) & (targets_df['월'] == month)]
            if not target_row.empty:
                target_sales = int(target_row.iloc[0].get('목표매출', 0) or 0)
        
        # 목표 비용구조 로드
        expense_df = load_expense_structure(year, month, store_id=store_id)
        
        has_targets = target_sales > 0 or (not expense_df.empty)
        
        return {
            'target_sales': target_sales,
            'target_expense_structure': expense_df,
            'has_targets': has_targets
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to load targets: {e}")
        return {
            'target_sales': 0,
            'target_expense_structure': pd.DataFrame(),
            'has_targets': False
        }


def _normalize_targets(target_expense_df, total_sales: int, target_sales: int):
    """
    Phase E: 목표 값 정규화 (금액/비율 둘 다 만들기)
    
    Args:
        target_expense_df: expense_structure DataFrame
        total_sales: 실제 매출 (목표 금액 계산용)
        target_sales: 목표 매출
    
    Returns:
        dict: 카테고리별 목표 값
        {
            '임차료': {'amount': int, 'rate': float},
            ...
        }
    """
    import pandas as pd
    
    categories = ['임차료', '인건비', '재료비', '공과금', '부가세&카드수수료']
    normalized = {cat: {'amount': 0, 'rate': 0.0} for cat in categories}
    
    if target_expense_df.empty:
        return normalized
    
    # 카테고리별 합산
    for category in categories:
        cat_df = target_expense_df[target_expense_df['category'] == category]
        if not cat_df.empty:
            total_amount = float(cat_df['amount'].sum())
            
            if category in ['재료비', '부가세&카드수수료']:
                # 변동비: amount가 비율(%)로 저장됨
                normalized[category]['rate'] = total_amount
                # 금액으로 변환 (target_sales 기준)
                if target_sales > 0:
                    normalized[category]['amount'] = int(target_sales * total_amount / 100)
            else:
                # 고정비: amount가 금액(원)으로 저장됨
                normalized[category]['amount'] = int(total_amount)
                # 비율로 변환 (target_sales 기준)
                if target_sales > 0:
                    normalized[category]['rate'] = (total_amount / target_sales * 100)
    
    return normalized


def _compute_scorecard(expense_items: dict, totals: dict, total_sales: int, 
                       target_sales: int, target_expense: dict):
    """
    Phase E: 성적표 계산 (실제 vs 목표 비교)
    
    Returns:
        dict: 성적표 데이터
    """
    # 실제 카테고리별 금액/비율 계산
    actual_by_category = {}
    for category, items in expense_items.items():
        category_total = totals['category_totals'].get(category, 0.0)
        actual_rate = (category_total / total_sales * 100) if total_sales > 0 else 0.0
        
        actual_by_category[category] = {
            'amount': int(category_total),
            'rate': actual_rate
        }
    
    # 목표 vs 실제 비교
    comparisons = {}
    for category in ['임차료', '인건비', '재료비', '공과금', '부가세&카드수수료']:
        actual = actual_by_category[category]
        target = target_expense.get(category, {'amount': 0, 'rate': 0.0})
        
        diff_amount = actual['amount'] - target['amount']
        diff_rate = actual['rate'] - target['rate']
        
        # 평가 등급 (비용은 낮을수록 좋음)
        if category in ['재료비', '부가세&카드수수료']:
            # 변동비: 비율 기준
            if diff_rate <= 0:
                grade = 'GOOD'  # 🟢
            elif diff_rate <= 5.0:
                grade = 'WARN'  # 🟡
            else:
                grade = 'BAD'  # 🔴
        else:
            # 고정비: 금액 기준
            if diff_amount <= 0:
                grade = 'GOOD'  # 🟢
            elif diff_amount <= target['amount'] * 0.05:  # 5% 초과
                grade = 'WARN'  # 🟡
            else:
                grade = 'BAD'  # 🔴
        
        comparisons[category] = {
            'actual_amount': actual['amount'],
            'target_amount': target['amount'],
            'diff_amount': diff_amount,
            'actual_rate': actual['rate'],
            'target_rate': target['rate'],
            'diff_rate': diff_rate,
            'grade': grade
        }
    
    # 총비용 비교
    actual_total_cost = totals['total_cost']
    target_total_cost = sum(target_expense[cat]['amount'] for cat in target_expense.keys())
    actual_total_cost_rate = (actual_total_cost / total_sales * 100) if total_sales > 0 else 0.0
    target_total_cost_rate = (target_total_cost / target_sales * 100) if target_sales > 0 else 0.0
    
    # 영업이익 비교
    actual_profit = totals['operating_profit']
    target_profit = target_sales - target_total_cost
    actual_profit_rate = totals['profit_margin']
    target_profit_rate = (target_profit / target_sales * 100) if target_sales > 0 else 0.0
    
    # 매출 달성률
    sales_achievement = (total_sales / target_sales * 100) if target_sales > 0 else 0.0
    
    return {
        'comparisons': comparisons,
        'total_cost': {
            'actual': actual_total_cost,
            'target': target_total_cost,
            'actual_rate': actual_total_cost_rate,
            'target_rate': target_total_cost_rate
        },
        'profit': {
            'actual': actual_profit,
            'target': target_profit,
            'actual_rate': actual_profit_rate,
            'target_rate': target_profit_rate
        },
        'sales': {
            'actual': total_sales,
            'target': target_sales,
            'achievement': sales_achievement
        }
    }


def _render_scorecard(scorecard: dict, has_targets: bool):
    """
    Phase E: 성적표 UI 렌더링
    """
    render_section_divider()
    st.markdown("### 📊 이번 달 성적표 (목표 대비)")
    
    if not has_targets:
        st.info("💡 이번 달 목표가 설정되지 않았습니다. **목표비용구조** 및 **목표매출구조** 페이지에서 먼저 설정하세요.")
        return
    
    # 요약 카드
    sales = scorecard['sales']
    total_cost = scorecard['total_cost']
    profit = scorecard['profit']
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        achievement_emoji = "🟢" if sales['achievement'] >= 100 else "🟡" if sales['achievement'] >= 90 else "🔴"
        st.metric(
            "목표 매출 달성률",
            f"{sales['achievement']:.1f}%",
            delta=f"{sales['actual'] - sales['target']:,.0f}원",
            delta_color="normal" if sales['achievement'] >= 100 else "inverse"
        )
    with col2:
        cost_diff_rate = total_cost['actual_rate'] - total_cost['target_rate']
        cost_emoji = "🟢" if cost_diff_rate <= 0 else "🟡" if cost_diff_rate <= 5.0 else "🔴"
        st.metric(
            "총비용률",
            f"{total_cost['actual_rate']:.1f}%",
            delta=f"{cost_diff_rate:+.1f}%p",
            delta_color="normal" if cost_diff_rate <= 0 else "inverse"
        )
    with col3:
        profit_diff = profit['actual'] - profit['target']
        profit_emoji = "🟢" if profit_diff >= 0 else "🟡" if profit_diff >= -profit['target'] * 0.1 else "🔴"
        st.metric(
            "영업이익",
            f"{profit['actual']:,.0f}원",
            delta=f"{profit_diff:+,.0f}원",
            delta_color="normal" if profit_diff >= 0 else "inverse"
        )
    with col4:
        profit_diff_rate = profit['actual_rate'] - profit['target_rate']
        st.metric(
            "이익률",
            f"{profit['actual_rate']:.1f}%",
            delta=f"{profit_diff_rate:+.1f}%p",
            delta_color="normal" if profit_diff_rate >= 0 else "inverse"
        )
    
    # 한 줄 코멘트
    comments = []
    if sales['achievement'] < 100:
        comments.append(f"매출은 목표 대비 {100 - sales['achievement']:.1f}% 미달")
    elif sales['achievement'] > 100:
        comments.append(f"매출은 목표 대비 +{sales['achievement'] - 100:.1f}% 초과")
    
    for category, comp in scorecard['comparisons'].items():
        if comp['grade'] == 'BAD':
            if category in ['재료비', '부가세&카드수수료']:
                comments.append(f"{category}율이 +{comp['diff_rate']:.1f}%p로 초과")
            else:
                comments.append(f"{category}이 +{comp['diff_amount']:,.0f}원으로 초과")
    
    if comments:
        st.info("💬 " + ", ".join(comments) + "했습니다.")
    
    # 5대 항목 비교 테이블
    st.markdown("#### 📋 카테고리별 비교")
    import pandas as pd
    
    table_data = []
    for category in ['임차료', '인건비', '재료비', '공과금', '부가세&카드수수료']:
        comp = scorecard['comparisons'][category]
        grade_emoji = {'GOOD': '🟢', 'WARN': '🟡', 'BAD': '🔴'}[comp['grade']]
        
        table_data.append({
            '항목': category,
            '실제(원)': f"{comp['actual_amount']:,}",
            '목표(원)': f"{comp['target_amount']:,}",
            '차이(원)': f"{comp['diff_amount']:+,}",
            '실제(%)': f"{comp['actual_rate']:.2f}",
            '목표(%)': f"{comp['target_rate']:.2f}",
            '차이(%p)': f"{comp['diff_rate']:+.2f}",
            '평가': grade_emoji
        })
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # 문제 원인 TOP 3
    st.markdown("#### ⚠️ 문제 원인 TOP 3")
    
    # 초과 기여도 계산 (양수만)
    issues = []
    for category, comp in scorecard['comparisons'].items():
        if comp['grade'] in ['WARN', 'BAD']:
            if category in ['재료비', '부가세&카드수수료']:
                contribution = comp['diff_rate']  # 비율 기준
            else:
                contribution = comp['diff_amount']  # 금액 기준
            
            if contribution > 0:
                issues.append({
                    'category': category,
                    'contribution': contribution,
                    'comp': comp
                })
    
    # 기여도 큰 순으로 정렬
    issues.sort(key=lambda x: x['contribution'], reverse=True)
    
    if issues:
        hints = {
            '재료비': '원가 누수(폐기/서비스) 또는 단가 상승을 점검하세요.',
            '인건비': '인건비 효율(시간당 매출)을 개선하세요.',
            '임차료': '임대료 재협상 또는 공간 활용도를 높이세요.',
            '공과금': '에너지 효율 개선을 검토하세요.',
            '부가세&카드수수료': '카드 수수료 할인 제도를 활용하세요.'
        }
        
        for i, issue in enumerate(issues[:3], 1):
            comp = issue['comp']
            category = issue['category']
            hint = hints.get(category, '해당 항목의 효율을 개선하세요.')
            
            with st.container():
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.markdown(f"**{i}. {category}**")
                    st.markdown(f"{'🟡' if comp['grade'] == 'WARN' else '🔴'}")
                with col2:
                    if category in ['재료비', '부가세&카드수수료']:
                        st.write(f"비율 초과: +{comp['diff_rate']:.2f}%p")
                    else:
                        st.write(f"금액 초과: +{comp['diff_amount']:,}원")
                    st.caption(f"💡 {hint}")
    else:
        st.success("🎉 모든 항목이 목표 범위 내에 있습니다!")


def _render_analysis_section(store_id: str, year: int, month: int, expense_items: dict, totals: dict, total_sales: int):
    """분석 영역 (Phase E: 성적표)"""
    # 목표 데이터 로드
    targets = _load_targets_for_month(store_id, year, month)
    
    if not targets['has_targets']:
        _render_scorecard({}, False)
        return
    
    # 목표 정규화
    normalized_targets = _normalize_targets(
        targets['target_expense_structure'],
        total_sales,
        targets['target_sales']
    )
    
    # 성적표 계산
    scorecard = _compute_scorecard(
        expense_items,
        totals,
        total_sales,
        targets['target_sales'],
        normalized_targets
    )
    
    # 성적표 렌더링
    _render_scorecard(scorecard, True)


def _load_settlement_history(store_id: str, limit: int = 6) -> list:
    """
    Phase H: 월별 히스토리 데이터 로드
    
    Returns:
        list: [
            {
                'year': int,
                'month': int,
                'status': str,
                'total_sales': int,
                'total_cost': float,
                'operating_profit': float,
                'profit_margin': float,
                'grade': str  # 'GOOD' | 'WARN' | 'BAD' | None
            },
            ...
        ]
    """
    try:
        # 사용 가능한 월 목록 조회
        months = load_available_settlement_months(store_id, limit=limit)
        
        if not months:
            return []
        
        history = []
        for year, month in months:
            # 스냅샷 로드
            snapshot = load_monthly_settlement_snapshot(store_id, year, month)
            
            # Phase H: 성적표 평가 (간단 버전)
            # 목표 데이터 로드
            targets = _load_targets_for_month(store_id, year, month)
            grade = None
            
            if targets['has_targets']:
                # 목표 정규화
                normalized_targets = _normalize_targets(
                    targets['target_expense_structure'],
                    snapshot['total_sales'],
                    targets['target_sales']
                )
                
                # 간단 평가: 총비용/이익 기준
                target_total_cost = sum(normalized_targets[cat]['amount'] for cat in normalized_targets.keys())
                actual_total_cost = snapshot['total_cost']
                cost_diff = actual_total_cost - target_total_cost
                
                target_profit = targets['target_sales'] - target_total_cost
                actual_profit = snapshot['operating_profit']
                profit_diff = actual_profit - target_profit
                
                # 평가: 이익 기준 우선, 비용 기준 보조
                if profit_diff >= 0:
                    grade = 'GOOD'  # 🟢
                elif profit_diff >= -target_profit * 0.1:  # 10% 이내
                    grade = 'WARN'  # 🟡
                else:
                    grade = 'BAD'  # 🔴
            
            history.append({
                'year': year,
                'month': month,
                'status': snapshot['status'],
                'total_sales': snapshot['total_sales'],
                'total_cost': snapshot['total_cost'],
                'operating_profit': snapshot['operating_profit'],
                'profit_margin': snapshot['profit_margin'],
                'grade': grade
            })
        
        return history
    except Exception as e:
        logger.error(f"Failed to load settlement history: {e}")
        return []


def _render_settlement_history(store_id: str):
    """Phase H: 월별 히스토리 섹션 렌더링"""
    render_section_divider()
    st.markdown("### 📊 월별 성적 히스토리")
    
    # 히스토리 로드
    history = _load_settlement_history(store_id, limit=6)
    
    if not history:
        st.info("💡 아직 작성된 실제정산 내역이 없습니다.")
        return
    
    # 표 데이터 준비
    table_data = []
    for row in history:
        year = row['year']
        month = row['month']
        status_emoji = "🟢 확정" if row['status'] == 'final' else "🟡 작성중"
        
        # 성적 아이콘
        if row['grade'] == 'GOOD':
            grade_emoji = "🟢"
        elif row['grade'] == 'WARN':
            grade_emoji = "🟡"
        elif row['grade'] == 'BAD':
            grade_emoji = "🔴"
        else:
            grade_emoji = "⚪"  # 목표 없음
        
        table_data.append({
            '월': f"{year}-{month:02d}",
            '매출': f"{row['total_sales']:,.0f}원",
            '총비용': f"{row['total_cost']:,.0f}원",
            '영업이익': f"{row['operating_profit']:,.0f}원",
            '이익률': f"{row['profit_margin']:.1f}%",
            '상태': status_emoji,
            '성적': grade_emoji,
            '_year': year,  # 내부용
            '_month': month  # 내부용
        })
    
    # 표 렌더링
    if table_data:
        # DataFrame 생성
        df = pd.DataFrame(table_data)
        display_df = df[['월', '매출', '총비용', '영업이익', '이익률', '상태', '성적']].copy()
        
        # 표 표시
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # 각 행에 "보기" 버튼 추가
        st.markdown('<div style="margin: 0.5rem 0;"></div>', unsafe_allow_html=True)
        st.markdown("**월별 상세 보기:**")
        
        cols = st.columns(min(len(table_data), 6))  # 최대 6개 열
        for idx, row in enumerate(table_data):
            col_idx = idx % 6
            with cols[col_idx]:
                year = row['_year']
                month = row['_month']
                if st.button(
                    f"{year}-{month:02d}",
                    key=f"history_view_{year}_{month}",
                    use_container_width=True
                ):
                    # Phase H: 월 이동 (별도 플래그 사용)
                    # st.number_input이 이미 settlement_year 키를 사용하므로 직접 수정 불가
                    st.session_state['settlement_navigate_to_year'] = year
                    st.session_state['settlement_navigate_to_month'] = month
                    st.rerun()
        
        # 더 보기 버튼 (선택)
        if len(history) >= 6:
            if st.button("📅 더 보기 (최근 24개월)", key="history_more"):
                # 24개월 로드
                history_24 = _load_settlement_history(store_id, limit=24)
                if history_24:
                    table_data_24 = []
                    for row in history_24:
                        year = row['year']
                        month = row['month']
                        status_emoji = "🟢 확정" if row['status'] == 'final' else "🟡 작성중"
                        
                        if row['grade'] == 'GOOD':
                            grade_emoji = "🟢"
                        elif row['grade'] == 'WARN':
                            grade_emoji = "🟡"
                        elif row['grade'] == 'BAD':
                            grade_emoji = "🔴"
                        else:
                            grade_emoji = "⚪"
                        
                        table_data_24.append({
                            '월': f"{year}-{month:02d}",
                            '매출': f"{row['total_sales']:,.0f}원",
                            '총비용': f"{row['total_cost']:,.0f}원",
                            '영업이익': f"{row['operating_profit']:,.0f}원",
                            '이익률': f"{row['profit_margin']:.1f}%",
                            '상태': status_emoji,
                            '성적': grade_emoji,
                            '_year': year,
                            '_month': month
                        })
                    
                    df_24 = pd.DataFrame(table_data_24)
                    display_df_24 = df_24[['월', '매출', '총비용', '영업이익', '이익률', '상태', '성적']].copy()
                    st.dataframe(display_df_24, use_container_width=True, hide_index=True)


def render_settlement_actual():
    """실제정산 페이지 렌더링 (Phase B - 템플릿 저장/자동 로드)"""
    try:
        # 안전장치: 함수 실행 확인 (DEV용)
        st.caption("✅ Settlement Phase H ACTIVE")
        
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
        
        # Phase H: 히스토리에서 이동한 경우 우선 처리
        # 플래그가 있으면 해당 연/월을 사용하고, 위젯 키를 강제로 변경하기 위한 플래그 설정
        if "settlement_navigate_to_year" in st.session_state:
            initial_year = st.session_state["settlement_navigate_to_year"]
            initial_month = st.session_state["settlement_navigate_to_month"]
            # Phase H: 위젯 키를 강제로 변경하기 위한 플래그 설정
            # 플래그는 _render_header_section에서 확인 후 삭제
            st.session_state["settlement_force_widget_update"] = True
        else:
            # 현재 연/월 (세션 상태에서 선택된 값이 있으면 사용, 없으면 현재 월 사용)
            if "settlement_year" in st.session_state:
                initial_year = st.session_state["settlement_year"]
            else:
                initial_year = current_year_kst()
            
            if "settlement_month" in st.session_state:
                initial_month = st.session_state["settlement_month"]
            else:
                initial_month = current_month_kst()
        
        # 상단 영역 (연/월 선택, KPI 카드, 템플릿 리셋 버튼, Phase F: readonly는 내부에서 확인)
        # _render_header_section 내부에서 month_status를 확인하므로 여기서는 readonly를 False로 전달
        year, month, expense_items, total_sales, totals, readonly = _render_header_section(
            store_id, initial_year, initial_month, readonly=False
        )
        
        # 비용 입력 영역 (템플릿 저장/삭제 포함, Phase F: readonly 전달)
        _render_expense_section(store_id, year, month, total_sales, readonly)
        
        # 분석 영역 (Phase E: 성적표)
        _render_analysis_section(store_id, year, month, expense_items, totals, total_sales)
        
        # Phase H: 월별 히스토리 섹션
        _render_settlement_history(store_id)
        
    except Exception as e:
        # 에러 발생 시 최소한의 UI 표시
        st.error(f"❌ 실제정산 페이지 로드 중 오류가 발생했습니다: {str(e)}")
        st.exception(e)
        st.info("""
        **Phase F 실제정산 페이지**
        
        - 연/월 선택
        - 총매출 입력 (sales 테이블 자동 불러오기)
        - 비용 입력 (5개 카테고리, 항목별 입력방식 선택)
        - 자동 계산 (총비용, 영업이익, 이익률)
        - 템플릿 저장/자동 로드
        - Soft Delete
        - 항목별 금액/% 선택형 입력
        - sales 월합계 자동 불러오기
        - 목표 대비 성적표
        - 확정(Final) + 잠금(읽기전용) + 확정 해제
        """)
