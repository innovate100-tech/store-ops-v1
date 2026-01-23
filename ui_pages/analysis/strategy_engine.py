"""
원인→액션 매핑 엔진
매출 하락 신호를 감지하고 "오늘의 전략 카드(미션 1개)"로 변환
"""
from __future__ import annotations

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from typing import Dict, List, Optional

from src.storage_supabase import (
    load_best_available_daily_sales,
    load_csv,
    load_monthly_sales_total,
    get_fixed_costs,
    get_variable_cost_ratio,
    calculate_break_even_sales,
)
from src.auth import get_current_store_id
from ui_pages.design_lab.design_insights import get_design_insights
from src.analytics import calculate_menu_cost


@st.cache_data(ttl=300)
def get_sales_drop_signals(store_id: str, ref_date: date, window_days: int = 14) -> Dict:
    """
    매출 하락 신호 수집
    
    Args:
        store_id: 매장 ID
        ref_date: 기준 날짜
        window_days: 분석 기간 (7/14/30일)
    
    Returns:
        {
            "recent_sales_avg": float,
            "compare_sales_avg": float,
            "sales_change_pct": float,
            "recent_visitors_avg": float,
            "compare_visitors_avg": float,
            "visitors_change_pct": float,
            "recent_avgp": float,
            "compare_avgp": float,
            "avgp_change_pct": float,
            "recent_qty": float,
            "compare_qty": float,
            "qty_change_pct": float,
            "top_menu_changes": List[Dict],
            "high_cogs_menu_count": int,
            "avg_contribution_margin": float,
            "break_even_gap_ratio": float,
        }
    """
    if not store_id:
        return {}
    
    try:
        kst = ZoneInfo("Asia/Seoul")
        today = datetime.now(kst).date()
        if ref_date > today:
            ref_date = today
        
        # 기간 계산
        recent_end = ref_date
        recent_start = ref_date - timedelta(days=window_days - 1)
        compare_end = recent_start - timedelta(days=1)
        compare_start = compare_end - timedelta(days=window_days - 1)
        
        start_date = (compare_start - timedelta(days=7)).isoformat()  # 여유분
        end_date = recent_end.isoformat()
        
        # 매출 데이터 로드 (SSOT best_available)
        sales_df = load_best_available_daily_sales(store_id=store_id, start_date=start_date, end_date=end_date)
        if sales_df.empty:
            return {}
        
        sales_df['date'] = pd.to_datetime(sales_df['date']).dt.date
        
        # 최근 구간
        recent_df = sales_df[
            (sales_df['date'] >= recent_start) & 
            (sales_df['date'] <= recent_end)
        ].copy()
        
        # 비교 구간
        compare_df = sales_df[
            (sales_df['date'] >= compare_start) & 
            (sales_df['date'] <= compare_end)
        ].copy()
        
        if recent_df.empty or compare_df.empty:
            return {}
        
        # 매출 변화
        recent_sales_avg = recent_df['total_sales'].mean() if 'total_sales' in recent_df.columns else 0
        compare_sales_avg = compare_df['total_sales'].mean() if 'total_sales' in compare_df.columns else 0
        sales_change_pct = ((recent_sales_avg - compare_sales_avg) / compare_sales_avg * 100) if compare_sales_avg > 0 else 0
        
        # 네이버방문자 변화
        recent_visitors_avg = recent_df['visitors'].mean() if 'visitors' in recent_df.columns else 0
        compare_visitors_avg = compare_df['visitors'].mean() if 'visitors' in compare_df.columns else 0
        visitors_change_pct = ((recent_visitors_avg - compare_visitors_avg) / compare_visitors_avg * 100) if compare_visitors_avg > 0 else 0
        
        # 객단가 변화
        recent_avgp = (recent_sales_avg / recent_visitors_avg) if recent_visitors_avg > 0 else 0
        compare_avgp = (compare_sales_avg / compare_visitors_avg) if compare_visitors_avg > 0 else 0
        avgp_change_pct = ((recent_avgp - compare_avgp) / compare_avgp * 100) if compare_avgp > 0 else 0
        
        # 판매량 변화
        sales_items_df = load_csv('daily_sales_items.csv', store_id=store_id, default_columns=['날짜', '메뉴명', '판매수량'])
        recent_qty = 0
        compare_qty = 0
        if not sales_items_df.empty and '날짜' in sales_items_df.columns:
            sales_items_df['날짜'] = pd.to_datetime(sales_items_df['날짜']).dt.date
            recent_items = sales_items_df[
                (sales_items_df['날짜'] >= recent_start) &
                (sales_items_df['날짜'] <= recent_end)
            ]
            compare_items = sales_items_df[
                (sales_items_df['날짜'] >= compare_start) &
                (sales_items_df['날짜'] <= compare_end)
            ]
            recent_qty = recent_items['판매수량'].sum() if '판매수량' in recent_items.columns else 0
            compare_qty = compare_items['판매수량'].sum() if '판매수량' in compare_items.columns else 0
        qty_change_pct = ((recent_qty - compare_qty) / compare_qty * 100) if compare_qty > 0 else 0
        
        # 상위메뉴 변화
        top_menu_changes = _get_top_menu_changes(store_id, recent_start, recent_end, compare_start, compare_end)
        
        # 원가율/공헌이익 (설계 인사이트에서)
        now = datetime.now(kst)
        insights = get_design_insights(store_id, now.year, now.month)
        menu_profit = insights.get("menu_profit", {})
        high_cogs_menu_count = menu_profit.get("high_cogs_ratio_menu_count", 0)
        
        # 평균 공헌이익 계산 (간단 버전)
        menu_df = load_csv('menu_master.csv', store_id=store_id, default_columns=['메뉴명', '판매가'])
        recipe_df = load_csv('recipes.csv', store_id=store_id, default_columns=['메뉴명', '재료명', '사용량'])
        ingredient_df = load_csv('ingredient_master.csv', store_id=store_id, default_columns=['재료명', '단가'])
        avg_contribution_margin = 0.0
        if not menu_df.empty and not recipe_df.empty and not ingredient_df.empty:
            from src.analytics import calculate_menu_cost
            cost_df = calculate_menu_cost(menu_df, recipe_df, ingredient_df)
            if not cost_df.empty and '원가' in cost_df.columns and '판매가' in cost_df.columns:
                cost_df['공헌이익'] = cost_df['판매가'] - cost_df['원가']
                avg_contribution_margin = cost_df['공헌이익'].mean() if len(cost_df) > 0 else 0.0
        
        # 손익분기점 대비 비율
        revenue = insights.get("revenue_structure", {})
        break_even_gap_ratio = revenue.get("break_even_gap_ratio", 1.0) if revenue.get("has_data") else 1.0
        
        return {
            "recent_sales_avg": recent_sales_avg,
            "compare_sales_avg": compare_sales_avg,
            "sales_change_pct": sales_change_pct,
            "recent_visitors_avg": recent_visitors_avg,
            "compare_visitors_avg": compare_visitors_avg,
            "visitors_change_pct": visitors_change_pct,
            "recent_avgp": recent_avgp,
            "compare_avgp": compare_avgp,
            "avgp_change_pct": avgp_change_pct,
            "recent_qty": recent_qty,
            "compare_qty": compare_qty,
            "qty_change_pct": qty_change_pct,
            "top_menu_changes": top_menu_changes,
            "high_cogs_menu_count": high_cogs_menu_count,
            "avg_contribution_margin": avg_contribution_margin,
            "break_even_gap_ratio": break_even_gap_ratio,
        }
    except Exception as e:
        return {}


@st.cache_data(ttl=300)
def _get_top_menu_changes(
    store_id: str,
    recent_start: date,
    recent_end: date,
    compare_start: date,
    compare_end: date
) -> List[Dict]:
    """상위메뉴 변화 분석"""
    try:
        sales_items_df = load_csv('daily_sales_items.csv', store_id=store_id, default_columns=['날짜', '메뉴명', '판매수량'])
        if sales_items_df.empty:
            return []
        
        sales_items_df['날짜'] = pd.to_datetime(sales_items_df['날짜']).dt.date
        
        # 최근 구간 Top10
        recent_items = sales_items_df[
            (sales_items_df['날짜'] >= recent_start) &
            (sales_items_df['날짜'] <= recent_end)
        ]
        recent_top = recent_items.groupby('메뉴명')['판매수량'].sum().nlargest(10).to_dict()
        
        # 비교 구간 Top10
        compare_items = sales_items_df[
            (sales_items_df['날짜'] >= compare_start) &
            (sales_items_df['날짜'] <= compare_end)
        ]
        compare_top = compare_items.groupby('메뉴명')['판매수량'].sum().nlargest(10).to_dict()
        
        # 변화 분석
        changes = []
        for menu_name, recent_qty in recent_top.items():
            compare_qty = compare_top.get(menu_name, 0)
            if compare_qty > 0:
                change_pct = ((recent_qty - compare_qty) / compare_qty * 100)
                changes.append({
                    "menu_name": menu_name,
                    "recent_qty": recent_qty,
                    "compare_qty": compare_qty,
                    "change_pct": change_pct
                })
        
        changes.sort(key=lambda x: x["change_pct"])
        return changes[:5]  # 최대 5개
    except Exception:
        return []


def classify_cause_type(signals: Dict) -> List[Dict]:
    """
    원인 타입 분류 (우선순위 높은 순)
    
    Returns:
        [{"type": str, "priority": int, "confidence": float, "details": Dict}, ...]
    """
    if not signals:
        return []
    
    causes = []
    
    # 1) 유입 감소형 (네이버방문자 하락)
    visitors_change = signals.get("visitors_change_pct", 0)
    if visitors_change < -10:
        causes.append({
            "type": "유입 감소형",
            "priority": 1,
            "confidence": min(abs(visitors_change) / 20.0, 1.0),  # -20% 이상이면 confidence=1.0
            "details": {
                "visitors_change_pct": visitors_change,
                "recent_visitors_avg": signals.get("recent_visitors_avg", 0),
                "compare_visitors_avg": signals.get("compare_visitors_avg", 0),
            }
        })
    
    # 2) 객단가 하락형
    avgp_change = signals.get("avgp_change_pct", 0)
    if avgp_change < -8 and abs(visitors_change) < 5:  # 네이버방문자 변화가 작을 때
        causes.append({
            "type": "객단가 하락형",
            "priority": 2,
            "confidence": min(abs(avgp_change) / 15.0, 1.0),
            "details": {
                "avgp_change_pct": avgp_change,
                "recent_avgp": signals.get("recent_avgp", 0),
                "compare_avgp": signals.get("compare_avgp", 0),
            }
        })
    
    # 3) 판매량 하락형
    qty_change = signals.get("qty_change_pct", 0)
    if qty_change < -10:
        causes.append({
            "type": "판매량 하락형",
            "priority": 3,
            "confidence": min(abs(qty_change) / 20.0, 1.0),
            "details": {
                "qty_change_pct": qty_change,
                "recent_qty": signals.get("recent_qty", 0),
                "compare_qty": signals.get("compare_qty", 0),
            }
        })
    
    # 4) 주력메뉴 붕괴형
    top_menu_changes = signals.get("top_menu_changes", [])
    severe_drops = [m for m in top_menu_changes if m.get("change_pct", 0) < -20]
    if len(severe_drops) >= 1:
        causes.append({
            "type": "주력메뉴 붕괴형",
            "priority": 4,
            "confidence": min(len(severe_drops) / 3.0, 1.0),
            "details": {
                "severe_drop_count": len(severe_drops),
                "top_drops": severe_drops[:3],
            }
        })
    
    # 5) 원가율 악화형
    high_cogs_count = signals.get("high_cogs_menu_count", 0)
    avg_contribution = signals.get("avg_contribution_margin", 0)
    if high_cogs_count >= 3 or avg_contribution < 5000:  # 공헌이익 5000원 미만
        causes.append({
            "type": "원가율 악화형",
            "priority": 5,
            "confidence": min(high_cogs_count / 5.0, 1.0) if high_cogs_count >= 3 else 0.5,
            "details": {
                "high_cogs_menu_count": high_cogs_count,
                "avg_contribution_margin": avg_contribution,
            }
        })
    
    # 6) 구조 리스크형
    break_even_gap = signals.get("break_even_gap_ratio", 1.0)
    if break_even_gap < 1.05:  # 손익분기점 대비 105% 미만
        causes.append({
            "type": "구조 리스크형",
            "priority": 6,
            "confidence": 1.0 - break_even_gap if break_even_gap < 1.0 else 0.3,
            "details": {
                "break_even_gap_ratio": break_even_gap,
            }
        })
    
    # 우선순위 + confidence 기준 정렬
    causes.sort(key=lambda x: (x["priority"], -x["confidence"]))
    
    return causes


def build_strategy_card(cause: Dict, signals: Dict, store_id: str) -> Dict:
    """
    원인 타입 → 전략 카드 변환
    
    Returns:
        {
            "title": str,
            "reason_bullets": List[str],
            "cta_label": str,
            "cta_page": str,
            "cta_context": Dict,
            "alternatives": List[Dict],
        }
    """
    cause_type = cause.get("type", "")
    details = cause.get("details", {})
    
    strategy = {
        "title": "",
        "reason_bullets": [],
        "cta_label": "",
        "cta_page": "",
        "cta_context": {},
        "alternatives": [],
    }
    
    if cause_type == "유입 감소형":
        visitors_change = details.get("visitors_change_pct", 0)
        strategy["title"] = "포트폴리오 미분류 메뉴 1개 정리"
        strategy["reason_bullets"] = [
            f"네이버방문자 {visitors_change:.1f}% 감소",
            "유인메뉴/대표메뉴 구성 점검 필요",
        ]
        strategy["cta_label"] = "메뉴 포트폴리오 설계실 열기"
        strategy["cta_page"] = "메뉴 등록"
        strategy["cta_context"] = {"_filter_unclassified": True}
        strategy["alternatives"] = [{
            "title": "매출 분석으로 유입 원인 파악",
            "reason": "네이버방문자 하락 원인을 자세히 분석하세요.",
            "cta_label": "매출 분석 열기",
            "cta_page": "매출 관리",
            "cta_context": {"_period_days": 14},
        }]
    
    elif cause_type == "객단가 하락형":
        avgp_change = details.get("avgp_change_pct", 0)
        strategy["title"] = "고원가율 메뉴 1개 가격 시뮬"
        strategy["reason_bullets"] = [
            f"객단가 {avgp_change:.1f}% 하락",
            "가격/마진 구조 점검 필요",
        ]
        strategy["cta_label"] = "가격 시뮬레이터 열기"
        strategy["cta_page"] = "메뉴 수익 구조 설계실"
        strategy["cta_context"] = {"_filter_high_cogs": True, "_initial_tab_메뉴 수익 구조 설계실": "execute"}
        strategy["alternatives"] = [{
            "title": "포트폴리오 분류 점검",
            "reason": "메뉴 역할(미끼/볼륨/마진) 균형을 확인하세요.",
            "cta_label": "포트폴리오 설계실 열기",
            "cta_page": "메뉴 등록",
            "cta_context": {"_initial_tab_메뉴 등록": "execute"},
        }]
    
    elif cause_type == "판매량 하락형":
        qty_change = details.get("qty_change_pct", 0)
        strategy["title"] = "주력메뉴 판매량 1개 점검"
        strategy["reason_bullets"] = [
            f"총 판매량 {qty_change:.1f}% 감소",
            "주력메뉴 판매 추이 확인 필요",
        ]
        strategy["cta_label"] = "판매·메뉴 분석 열기"
        strategy["cta_page"] = "판매 관리"
        strategy["cta_context"] = {"_period_days": 14}
        strategy["alternatives"] = [{
            "title": "포트폴리오 균형 점검",
            "reason": "메뉴 조합이 판매량에 영향을 줄 수 있습니다.",
            "cta_label": "포트폴리오 설계실 열기",
            "cta_page": "메뉴 등록",
            "cta_context": {"_initial_tab_메뉴 등록": "execute"},
        }]
    
    elif cause_type == "주력메뉴 붕괴형":
        severe_drops = details.get("top_drops", [])
        top_menu = severe_drops[0] if severe_drops else {}
        menu_name = top_menu.get("menu_name", "주력메뉴")
        change_pct = top_menu.get("change_pct", 0)
        strategy["title"] = f"{menu_name} 가격/마진 시뮬"
        strategy["reason_bullets"] = [
            f"{menu_name} 판매량 {change_pct:.1f}% 급감",
            "가격/마진 구조 재점검 필요",
        ]
        strategy["cta_label"] = "가격 시뮬레이터 열기"
        strategy["cta_page"] = "메뉴 수익 구조 설계실"
        strategy["cta_context"] = {"_selected_menu": menu_name, "_initial_tab_메뉴 수익 구조 설계실": "execute"}
        strategy["alternatives"] = [{
            "title": "판매·메뉴 분석",
            "reason": "주력메뉴 판매 추이를 자세히 분석하세요.",
            "cta_label": "판매·메뉴 분석 열기",
            "cta_page": "판매 관리",
            "cta_context": {"_period_days": 14},
        }]
    
    elif cause_type == "원가율 악화형":
        high_cogs_count = details.get("high_cogs_menu_count", 0)
        strategy["title"] = "고원가율 메뉴 1개 가격 시뮬"
        strategy["reason_bullets"] = [
            f"고원가율 메뉴 {high_cogs_count}개 확인",
            "가격 조정 또는 원가 절감 필요",
        ]
        strategy["cta_label"] = "가격 시뮬레이터 열기"
        strategy["cta_page"] = "메뉴 수익 구조 설계실"
        strategy["cta_context"] = {"_filter_high_cogs": True, "_initial_tab_메뉴 수익 구조 설계실": "execute"}
        strategy["alternatives"] = [{
            "title": "재료 구조 설계실",
            "reason": "원가 집중도가 높으면 재료 대체재를 검토하세요.",
            "cta_label": "재료 구조 설계실 열기",
            "cta_page": "재료 등록",
            "cta_context": {"_filter_high_risk": True, "_initial_tab_재료 등록": "execute"},
        }]
    
    elif cause_type == "구조 리스크형":
        break_even_gap = details.get("break_even_gap_ratio", 1.0)
        strategy["title"] = "손익분기점 시나리오 시뮬"
        strategy["reason_bullets"] = [
            f"손익분기점 대비 {break_even_gap * 100:.0f}%",
            "고정비/변동비 구조 점검 필요",
        ]
        strategy["cta_label"] = "시나리오 시뮬레이터 열기"
        strategy["cta_page"] = "수익 구조 설계실"
        strategy["cta_context"] = {"_initial_tab_수익 구조 설계실": "execute"}
        strategy["alternatives"] = [{
            "title": "목표 비용 구조 입력",
            "reason": "고정비/변동비 구조를 재설정하세요.",
            "cta_label": "목표 비용 구조 열기",
            "cta_page": "목표 비용구조",
            "cta_context": {},
        }]
    
    else:
        # 기본 전략
        strategy["title"] = "매출 하락 원인 찾기"
        strategy["reason_bullets"] = [
            "매출 하락 원인을 자세히 분석하세요.",
        ]
        strategy["cta_label"] = "원인 찾기 시작"
        strategy["cta_page"] = "매출 하락 원인 찾기"
        strategy["cta_context"] = {}
    
    return strategy


def get_checklist_template(cause_type: str) -> List[dict]:
    """
    원인 타입별 체크리스트 템플릿 반환
    
    Returns:
        [{"task_order": int, "task_title": str}, ...]
    """
    templates = {
        "유입 감소형": [
            {"task_order": 1, "task_title": "최근 14일 네이버방문자 추이 확인"},
            {"task_order": 2, "task_title": "리뷰/사진 1개 업데이트 계획 메모"},
            {"task_order": 3, "task_title": "대표 메뉴 1개 '유인' 포인트 문장 정리"},
            {"task_order": 4, "task_title": "오늘 운영 중 고객 응대 문구 1개 개선(메모)"},
        ],
        "객단가 하락형": [
            {"task_order": 1, "task_title": "고원가율(>=35%) 메뉴 TOP3 확인"},
            {"task_order": 2, "task_title": "1개 메뉴 가격 시뮬(목표 원가율 32~35%)"},
            {"task_order": 3, "task_title": "업셀 메뉴 1개 추천 문구 정리"},
            {"task_order": 4, "task_title": "가격 조정 후보 1개 최종 결정"},
        ],
        "판매량 하락형": [
            {"task_order": 1, "task_title": "주력메뉴 판매량 추이 확인"},
            {"task_order": 2, "task_title": "판매량 급감 메뉴 1개 원인 분석"},
            {"task_order": 3, "task_title": "메뉴 구성/조합 개선 아이디어 메모"},
            {"task_order": 4, "task_title": "오늘 운영 중 판매 전략 1개 적용"},
        ],
        "주력메뉴 붕괴형": [
            {"task_order": 1, "task_title": "주력메뉴 가격/마진 구조 재점검"},
            {"task_order": 2, "task_title": "가격 시뮬(목표 원가율 32~35%)"},
            {"task_order": 3, "task_title": "대체 주력메뉴 후보 1개 선정"},
            {"task_order": 4, "task_title": "가격 조정 또는 메뉴 교체 결정"},
        ],
        "원가율 악화형": [
            {"task_order": 1, "task_title": "고원가율(>=35%) 메뉴 TOP3 확인"},
            {"task_order": 2, "task_title": "1개 메뉴 가격 시뮬(목표 원가율 32~35%)"},
            {"task_order": 3, "task_title": "대체재 후보 1개 메모"},
            {"task_order": 4, "task_title": "\"마진 역할\" 메뉴 1개 지정"},
        ],
        "구조 리스크형": [
            {"task_order": 1, "task_title": "손익분기점 vs 예상매출 비교 확인"},
            {"task_order": 2, "task_title": "고정비 구조 점검(목표 비용 구조 확인)"},
            {"task_order": 3, "task_title": "변동비율 개선 방안 1개 메모"},
            {"task_order": 4, "task_title": "시나리오 시뮬(목표 매출 입력)"},
            {"task_order": 5, "task_title": "고정비 조정 또는 매출 목표 재설정"},
        ],
    }
    
    return templates.get(cause_type, [
        {"task_order": 1, "task_title": "매출 하락 원인 분석"},
        {"task_order": 2, "task_title": "개선 방안 1개 정리"},
    ])


def pick_primary_strategy(store_id: str, ref_date: Optional[date] = None, window_days: int = 14) -> Dict:
    """
    최종적으로 "오늘의 전략 카드 1개" 반환
    
    Args:
        store_id: 매장 ID
        ref_date: 기준 날짜 (None이면 오늘)
        window_days: 분석 기간 (7/14/30일)
    
    Returns:
        {
            "title": str,
            "reason_bullets": List[str],
            "cta_label": str,
            "cta_page": str,
            "cta_context": Dict,
            "alternatives": List[Dict],
        }
    """
    if not store_id:
        return {}
    
    if ref_date is None:
        kst = ZoneInfo("Asia/Seoul")
        ref_date = datetime.now(kst).date()
    
    # 신호 수집
    signals = get_sales_drop_signals(store_id, ref_date, window_days)
    if not signals:
        return {}  # 데이터 부족
    
    # 원인 분류
    causes = classify_cause_type(signals)
    if not causes:
        # 원인 없음 → 기본 전략
        return {
            "title": "매출 하락 원인 찾기",
            "reason_bullets": [
                "현재 특별한 하락 신호가 감지되지 않았습니다.",
                "정기적으로 원인 분석을 진행하세요.",
            ],
            "cta_label": "원인 찾기 시작",
            "cta_page": "매출 하락 원인 찾기",
            "cta_context": {},
            "alternatives": [],
        }
    
    # 최우선 원인 선택
    primary_cause = causes[0]
    
    # 전략 카드 생성
    strategy = build_strategy_card(primary_cause, signals, store_id)
    
    # 후보 2개 추가 (나머지 원인 중 상위 2개)
    if len(causes) > 1:
        for cause in causes[1:3]:  # 최대 2개
            alt_strategy = build_strategy_card(cause, signals, store_id)
            if alt_strategy.get("title"):
                strategy["alternatives"].append({
                    "title": alt_strategy["title"],
                    "reason": " / ".join(alt_strategy.get("reason_bullets", [])),
                    "cta_label": alt_strategy["cta_label"],
                    "cta_page": alt_strategy["cta_page"],
                    "cta_context": alt_strategy.get("cta_context", {}),
                })
    
    return strategy
