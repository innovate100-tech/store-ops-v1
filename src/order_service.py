"""
발주 관련 비즈니스 로직 전용 모듈

목표
-----
- `app.py`에서 복잡하게 섞여 있던 발주 계산/단위 변환/예외 처리 로직을 이 모듈로 모아
  UI 코드는 최대한 "표시"에만 집중하도록 분리한다.
- 가능하면 **순수 함수 형태**로 작성해서, 스트림릿 rerun 이슈와 무관하게 테스트/디버깅이 쉽도록 한다.

주의
-----
- 이 모듈은 **DB 스키마(orders, ingredients, suppliers, ingredient_suppliers)** 에 의존하지만,
  가능한 한 ID/name 매핑, 단위 변환을 여기서 일관되게 처리한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd

from src.storage_supabase import save_order


# ============================================
# 데이터 모델 (UI/서비스 계층 사이에서 사용하는 DTO)
# ============================================


@dataclass
class OrderItem:
    """발주 1건에 대한 도메인 모델 (UI ↔ 서비스 계층 사이에서 사용).

    모든 수치는 명확한 기준을 가진다.
    - order_qty:   발주 단위 기준 수량 (예: '개', '박스')
    - base_qty:    DB에 저장되는 기본 단위 기준 수량 (예: g, ml)
    - unit_price:  기본 단위 단가 (원/기본단위) – orders.unit_price 에 저장
    - total_amount: 총 금액 (원)
    """

    ingredient_name: str
    supplier_name: str
    order_date: date

    order_unit: str
    order_qty: float

    base_unit: str
    base_qty: float

    conversion_rate: float

    unit_price: float  # 기본 단위 단가 (원/기본단위)
    total_amount: float

    status: str = "예정"
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = None


# ============================================
# 순수 계산/변환 함수
# ============================================


def compute_base_quantity(order_qty: float, conversion_rate: float) -> float:
    """발주단위 수량과 변환비율로 기본단위 수량을 계산."""
    conv = conversion_rate or 1.0
    try:
        conv_f = float(conv)
        qty_f = float(order_qty or 0)
    except Exception:
        return float(order_qty or 0)
    if conv_f <= 0:
        return qty_f
    return qty_f * conv_f


def compute_total_amount_base(base_qty: float, base_unit_price: float) -> float:
    """기본단위 수량 × 기본단위 단가로 총 금액 계산."""
    try:
        return float(base_qty or 0) * float(base_unit_price or 0)
    except Exception:
        return 0.0


def build_order_items_from_display_df(
    display_order_df: pd.DataFrame,
    selected_ingredient_names: List[str],
    order_date: date,
    suppliers_df: Optional[pd.DataFrame] = None,
) -> List[OrderItem]:
    """발주 추천 화면의 display_order_df + 선택된 재료명 리스트로 OrderItem 목록 생성.

    기대하는 display_order_df 컬럼 (있으면 사용, 없으면 최대한 유추/기본값 사용):
    - '재료명'
    - '공급업체'
    - '발주필요량_발주단위' 또는 '발주필요량'
    - '발주단위' 또는 '단위'
    - '변환비율'
    - '사용단가_실제' (기본단위 단가)
    - '예상금액_숫자' (선택 – 없으면 base_qty * unit_price 로 계산)
    """
    if display_order_df is None or display_order_df.empty:
        return []

    items: List[OrderItem] = []

    # 공급업체별 배송일 → expected_delivery_date 계산용 맵 (없으면 그대로 None)
    delivery_days_map: Dict[str, Optional[int]] = {}
    if suppliers_df is not None and not suppliers_df.empty:
        if "공급업체명" in suppliers_df.columns and "배송일" in suppliers_df.columns:
            for _, row in suppliers_df.iterrows():
                name = str(row.get("공급업체명", "")).strip()
                if not name:
                    continue
                raw_days = row.get("배송일")
                try:
                    delivery_days_map[name] = int(raw_days) if raw_days is not None and str(raw_days).strip() != "" else None
                except Exception:
                    delivery_days_map[name] = None

    for _, row in display_order_df.iterrows():
        ingredient_name = str(row.get("재료명", "")).strip()
        if not ingredient_name or ingredient_name not in selected_ingredient_names:
            continue

        supplier_name = str(row.get("공급업체", "미지정") or "미지정").strip()

        # 발주 수량/단위
        if "발주필요량_발주단위" in row:
            order_qty = float(row.get("발주필요량_발주단위") or 0)
            order_unit = str(row.get("발주단위", row.get("단위", "")) or "").strip()
        else:
            order_qty = float(row.get("발주필요량") or 0)
            order_unit = str(row.get("발주단위", row.get("단위", "")) or "").strip()

        base_unit = str(row.get("단위", order_unit) or "").strip()
        conversion_rate = float(row.get("변환비율", 1.0) or 1.0)

        base_qty = compute_base_quantity(order_qty, conversion_rate)

        unit_price = float(row.get("사용단가_실제", 0) or 0)

        if "예상금액_숫자" in row and pd.notna(row.get("예상금액_숫자")):
            total_amount = float(row.get("예상금액_숫자") or 0)
        else:
            total_amount = compute_total_amount_base(base_qty, unit_price)

        # 입고예정일 계산
        expected_delivery_date: Optional[date] = None
        days_value = delivery_days_map.get(supplier_name)
        if days_value is not None:
            try:
                expected_delivery_date = order_date + timedelta(days=int(days_value))
            except Exception:
                expected_delivery_date = None

        item = OrderItem(
            ingredient_name=ingredient_name,
            supplier_name=supplier_name,
            order_date=order_date,
            order_unit=order_unit,
            order_qty=order_qty,
            base_unit=base_unit,
            base_qty=base_qty,
            conversion_rate=conversion_rate,
            unit_price=unit_price,
            total_amount=total_amount,
            status="예정",
            expected_delivery_date=expected_delivery_date,
        )
        items.append(item)

    return items


# ============================================
# 저장 래퍼 (서비스 계층 → 저장소 계층)
# ============================================


def persist_orders(items: List[OrderItem]) -> Tuple[int, List[str]]:
    """OrderItem 목록을 Supabase `orders` 테이블에 저장.

    Returns
    -------
    (created_count, failed_messages)
    """
    created = 0
    failures: List[str] = []

    for item in items:
        # 공급업체 미지정은 실패로 처리 (UI 쪽에서 이미 차단하는 것이 이상적)
        if item.supplier_name == "미지정" or not item.supplier_name.strip():
            failures.append(f"{item.ingredient_name} (공급업체 미지정)")
            continue

        try:
            ok = save_order(
                order_date=item.order_date,
                ingredient_name=item.ingredient_name,
                supplier_name=item.supplier_name,
                quantity=item.base_qty,
                unit_price=item.unit_price,
                total_amount=item.total_amount,
                status=item.status,
                expected_delivery_date=item.expected_delivery_date,
                notes=item.notes,
            )
            if ok:
                created += 1
            else:
                failures.append(f"{item.ingredient_name} (저장 실패 - 반환값 False)")
        except Exception as e:
            failures.append(f"{item.ingredient_name} ({str(e)})")

    return created, failures

