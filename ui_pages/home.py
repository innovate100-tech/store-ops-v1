"""
홈 (사장 계기판) 페이지
Phase 3 / STEP 1: 뼈대 + 데이터 단계 판별만 구현
Phase 3 / STEP 2: 이번 달 매출, 마감률/스트릭, 운영 메모 추가
"""
from src.bootstrap import bootstrap
import streamlit as st
from src.ui_helpers import render_page_header, render_section_divider
from src.auth import get_current_store_id, get_supabase_client
from src.storage_supabase import load_monthly_sales_total
from datetime import datetime, date
from zoneinfo import ZoneInfo

# 공통 설정 적용
bootstrap(page_title="Home Dashboard")

# 로그인 체크
from src.auth import check_login, show_login_page
if not check_login():
    show_login_page()
    st.stop()


def get_monthly_close_stats(store_id: str, year: int, month: int) -> tuple:
    """
    이번 달 마감률과 연속 마감(스트릭) 계산
    
    Returns:
        tuple: (closed_days, total_days, close_rate, streak_days)
        - closed_days: 마감된 일수
        - total_days: 이번 달 총 일수
        - close_rate: 마감률 (0.0 ~ 1.0)
        - streak_days: 연속 마감 일수 (최대 31일)
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return (0, 0, 0.0, 0)
        
        # 이번 달 시작/끝 날짜
        KST = ZoneInfo("Asia/Seoul")
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        
        # 이번 달 총 일수
        total_days = (end_date - start_date).days
        
        # daily_close 조회 (이번 달)
        result = supabase.table("daily_close")\
            .select("date")\
            .eq("store_id", store_id)\
            .gte("date", start_date.isoformat())\
            .lt("date", end_date.isoformat())\
            .order("date", desc=True)\
            .execute()
        
        if not result.data:
            return (0, total_days, 0.0, 0)
        
        closed_days = len(result.data)
        close_rate = closed_days / total_days if total_days > 0 else 0.0
        
        # 스트릭 계산: 최근 날짜부터 연속으로 daily_close가 있는 날 카운트
        today = datetime.now(KST).date()
        streak_days = 0
        check_date = today
        
        # 최근 날짜부터 역순으로 확인
        closed_dates = {row['date'] for row in result.data if row.get('date')}
        
        while check_date >= start_date and check_date < end_date:
            if check_date in closed_dates:
                streak_days += 1
                # 하루 전으로 이동
                from datetime import timedelta
                check_date = check_date - timedelta(days=1)
            else:
                break
        
        return (closed_days, total_days, close_rate, streak_days)
        
    except Exception as e:
        return (0, 0, 0.0, 0)


def get_problems_top3(store_id: str) -> list:
    """
    문제 TOP3 추출 (룰 기반)
    
    Returns:
        list: [{"text": str, "target_page": str}, ...] 최대 3개
    """
    problems = []
    
    try:
        supabase = get_supabase_client()
        if not supabase:
            return [{"text": "데이터를 불러올 수 없습니다.", "target_page": "점장 마감"}]
        
        KST = ZoneInfo("Asia/Seoul")
        today = datetime.now(KST).date()
        
        # 최근 6일 매출 데이터 조회 (최근 3일 vs 그 전 3일 비교용)
        from datetime import timedelta
        six_days_ago = today - timedelta(days=6)
        
        sales_recent = supabase.table("sales")\
            .select("date, total_sales")\
            .eq("store_id", store_id)\
            .gte("date", six_days_ago.isoformat())\
            .lte("date", today.isoformat())\
            .order("date", desc=False)\
            .execute()
        
        sales_data = {}
        if sales_recent.data:
            for row in sales_recent.data:
                date_str = row.get('date')
                total = float(row.get('total_sales', 0) or 0)
                if date_str:
                    sales_data[date_str] = total
        
        # A. 최근 3일 평균 매출 < 그 전 3일 평균
        if len(sales_data) >= 6:
            recent_3_days = list(sales_data.values())[-3:]
            prev_3_days = list(sales_data.values())[-6:-3]
            if recent_3_days and prev_3_days:
                recent_avg = sum(recent_3_days) / len(recent_3_days)
                prev_avg = sum(prev_3_days) / len(prev_3_days)
                if recent_avg < prev_avg and prev_avg > 0:
                    problems.append({
                        "text": "최근 3일 평균 매출이 직전 기간보다 감소했습니다.",
                        "target_page": "매출 관리"
                    })
        
        # 이번 달 매출 데이터 조회
        current_year = today.year
        current_month = today.month
        start_of_month = date(current_year, current_month, 1)
        if current_month == 12:
            end_of_month = date(current_year + 1, 1, 1)
        else:
            end_of_month = date(current_year, current_month + 1, 1)
        
        sales_month = supabase.table("sales")\
            .select("date, total_sales")\
            .eq("store_id", store_id)\
            .gte("date", start_of_month.isoformat())\
            .lt("date", end_of_month.isoformat())\
            .execute()
        
        month_sales = {}
        if sales_month.data:
            for row in sales_month.data:
                date_str = row.get('date')
                total = float(row.get('total_sales', 0) or 0)
                if date_str and total > 0:
                    month_sales[date_str] = total
        
        # B. 이번 달 매출 최저일 발생 (최근 3일 내)
        if month_sales:
            min_sales = min(month_sales.values())
            min_date = min([d for d, s in month_sales.items() if s == min_sales])
            min_date_obj = datetime.strptime(min_date, '%Y-%m-%d').date() if isinstance(min_date, str) else min_date
            days_ago = (today - min_date_obj).days
            if days_ago <= 3 and days_ago >= 0:
                problems.append({
                    "text": "이번 달 최저 매출일이 최근에 발생했습니다.",
                    "target_page": "매출 관리"
                })
        
        # C. 마감 공백 존재
        daily_close_month = supabase.table("daily_close")\
            .select("date")\
            .eq("store_id", store_id)\
            .gte("date", start_of_month.isoformat())\
            .lt("date", end_of_month.isoformat())\
            .execute()
        
        closed_dates = set()
        if daily_close_month.data:
            for row in daily_close_month.data:
                date_str = row.get('date')
                if date_str:
                    closed_dates.add(date_str)
        
        # 오늘까지의 날짜 중 마감 안 된 날 확인
        check_date = start_of_month
        gap_found = False
        while check_date < today and check_date < end_of_month:
            if check_date.isoformat() not in closed_dates:
                gap_found = True
                break
            check_date += timedelta(days=1)
        
        if gap_found:
            problems.append({
                "text": "이번 달 마감하지 않은 날이 있습니다.",
                "target_page": "점장 마감"
            })
        
        # D. 판매 메뉴 쏠림 (상위 1개 메뉴가 50% 이상)
        seven_days_ago = today - timedelta(days=7)
        sales_items_recent = supabase.table("v_daily_sales_items_effective")\
            .select("menu_id, qty")\
            .eq("store_id", store_id)\
            .gte("date", seven_days_ago.isoformat())\
            .lte("date", today.isoformat())\
            .execute()
        
        if sales_items_recent.data:
            menu_totals = {}
            total_qty = 0
            for row in sales_items_recent.data:
                menu_id = row.get('menu_id')
                qty = int(row.get('qty', 0) or 0)
                if menu_id and qty > 0:
                    menu_totals[menu_id] = menu_totals.get(menu_id, 0) + qty
                    total_qty += qty
            
            if menu_totals and total_qty > 0:
                max_menu_qty = max(menu_totals.values())
                max_ratio = max_menu_qty / total_qty
                if max_ratio >= 0.5:
                    problems.append({
                        "text": "상위 1개 메뉴가 전체 판매의 50% 이상을 차지합니다.",
                        "target_page": "판매 관리"
                    })
        
        # E. 최근 7일 판매 데이터 거의 없음
        if sales_items_recent.data:
            unique_dates = set()
            for row in sales_items_recent.data:
                date_str = row.get('date')
                if date_str:
                    unique_dates.add(date_str)
            
            if len(unique_dates) <= 2:  # 2일 이하
                problems.append({
                    "text": "최근 일주일 판매 데이터가 거의 없습니다.",
                    "target_page": "점장 마감"
                })
        
        # 최대 3개만 반환
        return problems[:3] if problems else [{"text": "아직 분석할 데이터가 충분하지 않습니다.", "target_page": "점장 마감"}]
        
    except Exception as e:
        return [{"text": "문제 분석 중 오류가 발생했습니다.", "target_page": "점장 마감"}]


def get_good_points_top3(store_id: str) -> list:
    """
    잘한 점 TOP3 추출 (룰 기반)
    
    Returns:
        list: [{"text": str, "target_page": str}, ...] 최대 3개
    """
    good_points = []
    
    try:
        supabase = get_supabase_client()
        if not supabase:
            return [{"text": "데이터를 불러올 수 없습니다.", "target_page": "점장 마감"}]
        
        KST = ZoneInfo("Asia/Seoul")
        today = datetime.now(KST).date()
        
        # 최근 6일 매출 데이터 조회
        from datetime import timedelta
        six_days_ago = today - timedelta(days=6)
        
        sales_recent = supabase.table("sales")\
            .select("date, total_sales")\
            .eq("store_id", store_id)\
            .gte("date", six_days_ago.isoformat())\
            .lte("date", today.isoformat())\
            .order("date", desc=False)\
            .execute()
        
        sales_data = {}
        if sales_recent.data:
            for row in sales_recent.data:
                date_str = row.get('date')
                total = float(row.get('total_sales', 0) or 0)
                if date_str:
                    sales_data[date_str] = total
        
        # A. 최근 3일 평균 매출 > 그 전 3일 평균
        if len(sales_data) >= 6:
            recent_3_days = list(sales_data.values())[-3:]
            prev_3_days = list(sales_data.values())[-6:-3]
            if recent_3_days and prev_3_days:
                recent_avg = sum(recent_3_days) / len(recent_3_days)
                prev_avg = sum(prev_3_days) / len(prev_3_days)
                if recent_avg > prev_avg and prev_avg > 0:
                    good_points.append({
                        "text": "최근 3일 평균 매출이 이전 기간보다 증가했습니다.",
                        "target_page": "매출 관리"
                    })
        
        # 이번 달 매출 데이터 조회
        current_year = today.year
        current_month = today.month
        start_of_month = date(current_year, current_month, 1)
        if current_month == 12:
            end_of_month = date(current_year + 1, 1, 1)
        else:
            end_of_month = date(current_year, current_month + 1, 1)
        
        sales_month = supabase.table("sales")\
            .select("date, total_sales")\
            .eq("store_id", store_id)\
            .gte("date", start_of_month.isoformat())\
            .lt("date", end_of_month.isoformat())\
            .execute()
        
        month_sales = {}
        if sales_month.data:
            for row in sales_month.data:
                date_str = row.get('date')
                total = float(row.get('total_sales', 0) or 0)
                if date_str and total > 0:
                    month_sales[date_str] = total
        
        # B. 이번 달 최고 매출일 발생 (최근 3일 내)
        if month_sales:
            max_sales = max(month_sales.values())
            max_date = max([d for d, s in month_sales.items() if s == max_sales])
            max_date_obj = datetime.strptime(max_date, '%Y-%m-%d').date() if isinstance(max_date, str) else max_date
            days_ago = (today - max_date_obj).days
            if days_ago <= 3 and days_ago >= 0:
                good_points.append({
                    "text": "이번 달 최고 매출일이 최근에 발생했습니다.",
                    "target_page": "매출 관리"
                })
        
        # C. 마감 스트릭 유지 (이미 get_monthly_close_stats에서 계산됨)
        close_stats = get_monthly_close_stats(store_id, current_year, current_month)
        streak_days = close_stats[3]
        if streak_days >= 3:
            good_points.append({
                "text": "연속 마감 기록이 유지되고 있습니다.",
                "target_page": "점장 마감"
            })
        
        # D. 판매 메뉴 다양화 (상위 1개 메뉴가 50% 미만)
        seven_days_ago = today - timedelta(days=7)
        sales_items_recent = supabase.table("v_daily_sales_items_effective")\
            .select("menu_id, qty")\
            .eq("store_id", store_id)\
            .gte("date", seven_days_ago.isoformat())\
            .lte("date", today.isoformat())\
            .execute()
        
        if sales_items_recent.data:
            menu_totals = {}
            total_qty = 0
            for row in sales_items_recent.data:
                menu_id = row.get('menu_id')
                qty = int(row.get('qty', 0) or 0)
                if menu_id and qty > 0:
                    menu_totals[menu_id] = menu_totals.get(menu_id, 0) + qty
                    total_qty += qty
            
            if menu_totals and total_qty > 0:
                max_menu_qty = max(menu_totals.values())
                max_ratio = max_menu_qty / total_qty
                if max_ratio < 0.5 and len(menu_totals) >= 3:  # 3개 이상 메뉴, 최대 비율 50% 미만
                    good_points.append({
                        "text": "최근 판매가 여러 메뉴로 분산되고 있습니다.",
                        "target_page": "판매 관리"
                    })
        
        # E. 판매 데이터 꾸준 (최근 7일 중 5일 이상)
        if sales_items_recent.data:
            unique_dates = set()
            for row in sales_items_recent.data:
                date_str = row.get('date')
                if date_str:
                    unique_dates.add(date_str)
            
            if len(unique_dates) >= 5:
                good_points.append({
                    "text": "최근 일주일 판매 입력이 꾸준히 이루어지고 있습니다.",
                    "target_page": "판매 관리"
                })
        
        # 최대 3개만 반환
        return good_points[:3] if good_points else [{"text": "데이터가 쌓이면 자동 분석됩니다.", "target_page": "점장 마감"}]
        
    except Exception as e:
        return [{"text": "잘한 점 분석 중 오류가 발생했습니다.", "target_page": "점장 마감"}]


def check_actual_settlement_exists(store_id: str, year: int, month: int) -> bool:
    """
    이번 달 actual_settlement 데이터 존재 여부 확인
    
    Returns:
        bool: 존재하면 True, 없으면 False
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        result = supabase.table("actual_settlement")\
            .select("id", count="exact")\
            .eq("store_id", store_id)\
            .eq("year", year)\
            .eq("month", month)\
            .limit(1)\
            .execute()
        
        count = result.count if hasattr(result, 'count') and result.count is not None else (len(result.data) if result.data else 0)
        return count > 0
        
    except Exception as e:
        return False


def get_today_one_action(store_id: str, level: int) -> dict:
    """
    오늘 하나만 추천 액션 결정 (룰 기반)
    
    Returns:
        dict: {
            "title": str,
            "reason": str,
            "button_label": str,
            "target_page": str
        }
    """
    # Fallback 기본값
    fallback = {
        "title": "오늘 마감부터 시작",
        "reason": "데이터가 없어서 분석이 불가능합니다. 오늘 마감 1회만 하면 홈이 채워집니다.",
        "button_label": "📋 점장 마감 하러가기",
        "target_page": "점장 마감"
    }
    
    try:
        KST = ZoneInfo("Asia/Seoul")
        now_kst = datetime.now(KST)
        current_year = now_kst.year
        current_month = now_kst.month
        
        if level == 0:
            return {
                "title": "오늘 마감부터 시작",
                "reason": "데이터가 없어서 분석이 불가능합니다. 오늘 마감 1회만 하면 홈이 채워집니다.",
                "button_label": "📋 점장 마감 하러가기",
                "target_page": "점장 마감"
            }
        
        elif level == 1:
            return {
                "title": "이번 주는 마감 루틴 만들기",
                "reason": "매출은 들어오고 있습니다. 마감이 쌓이면 판매/원가/발주까지 자동으로 연결됩니다.",
                "button_label": "📋 점장 마감 하러가기",
                "target_page": "점장 마감"
            }
        
        elif level == 2:
            # 운영 메모 존재 여부 확인
            memos = get_monthly_memos(store_id, current_year, current_month, limit=1)
            has_memos = len(memos) > 0
            
            if not has_memos:
                # A) 운영 메모가 0이면
                return {
                    "title": "마감에 특이사항 1줄 남기기",
                    "reason": "숫자 변화의 원인을 기억하면 다음 달 전략이 쉬워집니다.",
                    "button_label": "📋 점장 마감 하러가기",
                    "target_page": "점장 마감"
                }
            else:
                # B) 운영 메모가 있으면
                return {
                    "title": "판매 흐름 3분 점검",
                    "reason": "판매 데이터가 쌓였습니다. 메뉴별 흐름을 보고 오늘 밀 메뉴를 정하세요.",
                    "button_label": "📦 판매 관리 보러가기",
                    "target_page": "판매 관리"
                }
        
        elif level == 3:
            # actual_settlement(이번 달) 존재 여부 확인
            has_settlement = check_actual_settlement_exists(store_id, current_year, current_month)
            
            if not has_settlement:
                # A) actual_settlement(이번 달) 데이터가 없으면
                return {
                    "title": "이번 달 성적표 만들기",
                    "reason": "정산이 있어야 이익/구조판이 자동으로 작동합니다.",
                    "button_label": "🧾 실제정산 하러가기",
                    "target_page": "실제정산"
                }
            else:
                # B) actual_settlement(이번 달) 데이터가 있으면
                return {
                    "title": "숫자 구조 10초 복습",
                    "reason": "매출이 오르면 얼마가 남는지 알고 있으면 의사결정이 빨라집니다.",
                    "button_label": "💳 목표 비용구조 보기",
                    "target_page": "목표 비용구조"
                }
        
        else:
            return fallback
            
    except Exception as e:
        # 예외 발생 시 안전한 fallback
        return fallback


def get_monthly_memos(store_id: str, year: int, month: int, limit: int = 5) -> list:
    """
    이번 달 daily_close에서 메모 최신 N개 조회
    
    Returns:
        list: [{"date": "2025-01-22", "memo": "단체 2팀, 재료 소진 빠름"}, ...]
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return []
        
        # 이번 달 시작/끝 날짜
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        
        # daily_close에서 memo가 있는 것만 조회 (최신순)
        result = supabase.table("daily_close")\
            .select("date, memo")\
            .eq("store_id", store_id)\
            .gte("date", start_date.isoformat())\
            .lt("date", end_date.isoformat())\
            .not_.is_("memo", "null")\
            .neq("memo", "")\
            .order("date", desc=True)\
            .limit(limit)\
            .execute()
        
        if not result.data:
            return []
        
        memos = []
        for row in result.data:
            memo_text = row.get('memo', '').strip()
            if memo_text:
                memos.append({
                    "date": row.get('date'),
                    "memo": memo_text
                })
        
        return memos
        
    except Exception as e:
        return []


def detect_data_level(store_id: str) -> int:
    """
    현재 매장의 데이터 성숙도 단계를 판별
    
    LEVEL 0: 데이터 거의 없음 (sales 0건)
    LEVEL 1: 매출만 있음 (sales 존재, daily_close 거의 없음)
    LEVEL 2: 운영 데이터 있음 (daily_close 또는 daily_sales_items 존재)
    LEVEL 3: 재무 구조 있음 (expense_structure 또는 actual_settlement 존재)
    
    Returns:
        int: 0, 1, 2, 또는 3
    """
    if not store_id:
        return 0
    
    try:
        supabase = get_supabase_client()
        if not supabase:
            return 0
        
        # LEVEL 0 체크: sales 0건
        sales_check = supabase.table("sales")\
            .select("id", count="exact")\
            .eq("store_id", store_id)\
            .limit(1)\
            .execute()
        
        sales_count = sales_check.count if hasattr(sales_check, 'count') and sales_check.count is not None else (len(sales_check.data) if sales_check.data else 0)
        
        if sales_count == 0:
            return 0
        
        # LEVEL 1 체크: sales 존재, daily_close 거의 없음 (3건 이하)
        daily_close_check = supabase.table("daily_close")\
            .select("id", count="exact")\
            .eq("store_id", store_id)\
            .limit(1)\
            .execute()
        
        daily_close_count = daily_close_check.count if hasattr(daily_close_check, 'count') and daily_close_check.count is not None else (len(daily_close_check.data) if daily_close_check.data else 0)
        
        if daily_close_count <= 3:
            return 1
        
        # LEVEL 2 체크: daily_close 또는 daily_sales_items 존재
        # daily_close는 이미 체크했으므로, daily_sales_items도 확인
        daily_sales_check = supabase.table("v_daily_sales_items_effective")\
            .select("menu_id", count="exact")\
            .eq("store_id", store_id)\
            .limit(1)\
            .execute()
        
        daily_sales_count = daily_sales_check.count if hasattr(daily_sales_check, 'count') and daily_sales_check.count is not None else (len(daily_sales_check.data) if daily_sales_check.data else 0)
        
        if daily_close_count > 3 or daily_sales_count > 0:
            # LEVEL 3 체크: expense_structure 또는 actual_settlement 존재
            try:
                expense_check = supabase.table("expense_structure")\
                    .select("id", count="exact")\
                    .eq("store_id", store_id)\
                    .limit(1)\
                    .execute()
                
                expense_count = expense_check.count if hasattr(expense_check, 'count') and expense_check.count is not None else (len(expense_check.data) if expense_check.data else 0)
                
                if expense_count > 0:
                    return 3
            except Exception:
                pass
            
            try:
                settlement_check = supabase.table("actual_settlement")\
                    .select("id", count="exact")\
                    .eq("store_id", store_id)\
                    .limit(1)\
                    .execute()
                
                settlement_count = settlement_check.count if hasattr(settlement_check, 'count') and settlement_check.count is not None else (len(settlement_check.data) if settlement_check.data else 0)
                
                if settlement_count > 0:
                    return 3
            except Exception:
                pass
            
            return 2
        
        return 1
        
    except Exception as e:
        # 에러 발생 시 안전하게 0 리턴
        return 0


def render_home():
    """홈 (사장 계기판) 페이지 렌더링"""
    render_page_header("사장 계기판", "🏠")
    
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다. 로그인 상태를 확인해주세요.")
        return
    
    # 데이터 단계 판별 (최초 1회만)
    if 'home_data_level' not in st.session_state:
        st.session_state.home_data_level = detect_data_level(store_id)
    
    data_level = st.session_state.home_data_level
    
    # 단계별 안내
    level_labels = {
        0: "LEVEL 0: 데이터 거의 없음",
        1: "LEVEL 1: 매출만 있음",
        2: "LEVEL 2: 운영 데이터 있음",
        3: "LEVEL 3: 재무 구조 있음",
    }
    
    st.info(f"📊 현재 데이터 단계: **{level_labels.get(data_level, '알 수 없음')}**")
    
    render_section_divider()
    
    # ========== 섹션 1: 상태판 ==========
    with st.container():
        st.markdown("### 📊 상태판")
        
        # 이번 달 정보
        KST = ZoneInfo("Asia/Seoul")
        now_kst = datetime.now(KST)
        current_year = now_kst.year
        current_month = now_kst.month
        
        # A) 이번 달 매출
        monthly_sales = 0
        try:
            monthly_sales = load_monthly_sales_total(store_id, current_year, current_month)
        except Exception as e:
            pass
        
        # B) 마감률/스트릭
        close_stats = (0, 0, 0.0, 0)
        try:
            close_stats = get_monthly_close_stats(store_id, current_year, current_month)
        except Exception as e:
            pass
        
        closed_days, total_days, close_rate, streak_days = close_stats
        
        # 상태판 레이아웃: 2열
        col1, col2 = st.columns(2)
        
        with col1:
            # 이번 달 매출
            if monthly_sales > 0:
                st.markdown(f"""
                <div style="padding: 1.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; color: white; text-align: center;">
                    <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">이번 달 매출</div>
                    <div style="font-size: 2rem; font-weight: 700;">{monthly_sales:,}원</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="padding: 1.5rem; background: #fff3cd; border-radius: 12px; border-left: 4px solid #ffc107;">
                    <h4 style="color: #856404; margin-bottom: 0.5rem;">이번 달 매출 데이터가 없습니다</h4>
                    <p style="color: #856404; margin-bottom: 1rem; font-size: 0.9rem;">점장마감 또는 매출 입력을 시작하세요.</p>
                </div>
                """, unsafe_allow_html=True)
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("📋 점장 마감", use_container_width=True, key="home_btn_close_sales"):
                        st.session_state.current_page = "점장 마감"
                        st.rerun()
                with col_btn2:
                    if st.button("💰 매출 보정", use_container_width=True, key="home_btn_sales_entry"):
                        st.session_state.current_page = "매출 등록"
                        st.rerun()
        
        with col2:
            # 마감률/스트릭
            if closed_days > 0:
                close_rate_pct = int(close_rate * 100)
                st.markdown(f"""
                <div style="padding: 1.5rem; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 12px; color: white; text-align: center;">
                    <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">마감률</div>
                    <div style="font-size: 2rem; font-weight: 700; margin-bottom: 0.5rem;">{close_rate_pct}%</div>
                    <div style="font-size: 0.85rem; opacity: 0.9;">({closed_days}/{total_days}일)</div>
                    {f'<div style="font-size: 0.9rem; margin-top: 0.5rem; opacity: 0.9;">🔥 연속 {streak_days}일</div>' if streak_days > 0 else ''}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="padding: 1.5rem; background: #fff3cd; border-radius: 12px; border-left: 4px solid #ffc107;">
                    <h4 style="color: #856404; margin-bottom: 0.5rem;">마감 데이터가 없습니다</h4>
                    <p style="color: #856404; margin-bottom: 1rem; font-size: 0.9rem;">오늘부터 마감을 시작하세요.</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("📋 점장 마감", type="primary", use_container_width=True, key="home_btn_close_rate"):
                    st.session_state.current_page = "점장 마감"
                    st.rerun()
    
    render_section_divider()
    
    # ========== 섹션 2: 핵심 숫자 카드 ==========
    with st.container():
        st.markdown("### 💰 핵심 숫자 카드")
        
        # 이번 달 매출 재조회 (카드용)
        KST = ZoneInfo("Asia/Seoul")
        now_kst = datetime.now(KST)
        monthly_sales_card = 0
        try:
            monthly_sales_card = load_monthly_sales_total(store_id, now_kst.year, now_kst.month)
        except Exception:
            pass
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            try:
                if data_level == 0:
                    st.markdown("""
                    <div style="padding: 1.5rem; background: #f8f9fa; border-radius: 8px; text-align: center;">
                        <div style="font-size: 0.9rem; color: #6c757d; margin-bottom: 0.5rem;">오늘 매출</div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: #6c757d;">-</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="padding: 1.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px; text-align: center; color: white;">
                        <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">오늘 매출</div>
                        <div style="font-size: 1.5rem; font-weight: 700;">계산 예정</div>
                    </div>
                    """, unsafe_allow_html=True)
            except Exception:
                pass
        
        with col2:
            try:
                if monthly_sales_card > 0:
                    st.markdown(f"""
                    <div style="padding: 1.5rem; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 8px; text-align: center; color: white;">
                        <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">이번 달 매출</div>
                        <div style="font-size: 1.5rem; font-weight: 700;">{monthly_sales_card:,}원</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="padding: 1.5rem; background: #f8f9fa; border-radius: 8px; text-align: center;">
                        <div style="font-size: 0.9rem; color: #6c757d; margin-bottom: 0.5rem;">이번 달 매출</div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: #6c757d;">-</div>
                    </div>
                    """, unsafe_allow_html=True)
            except Exception:
                pass
        
        with col3:
            if data_level < 2:
                st.markdown("""
                <div style="padding: 1.5rem; background: #f8f9fa; border-radius: 8px; text-align: center;">
                    <div style="font-size: 0.9rem; color: #6c757d; margin-bottom: 0.5rem;">객단가</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #6c757d;">-</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="padding: 1.5rem; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 8px; text-align: center; color: white;">
                    <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">객단가</div>
                    <div style="font-size: 1.5rem; font-weight: 700;">계산 예정</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col4:
            if data_level < 3:
                st.markdown("""
                <div style="padding: 1.5rem; background: #f8f9fa; border-radius: 8px; text-align: center;">
                    <div style="font-size: 0.9rem; color: #6c757d; margin-bottom: 0.5rem;">이번 달 이익</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #6c757d;">-</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="padding: 1.5rem; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); border-radius: 8px; text-align: center; color: white;">
                    <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">이번 달 이익</div>
                    <div style="font-size: 1.5rem; font-weight: 700;">계산 예정</div>
                </div>
                """, unsafe_allow_html=True)
    
    render_section_divider()
    
    # ========== 섹션 3: 오늘 하나만 ==========
    try:
        with st.container():
            st.markdown("### 🎯 오늘 하나만 (매일 1개 추천)")
            
            # 추천 액션 결정
            action = get_today_one_action(store_id, data_level)
            
            # 추천 카드 표시
            st.markdown(f"""
            <div style="padding: 1.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; color: white; margin-bottom: 1rem;">
                <h4 style="color: white; margin-bottom: 0.5rem; font-size: 1.2rem;">{action['title']}</h4>
                <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 0.95rem; line-height: 1.5;">{action['reason']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # 버튼
            if st.button(action['button_label'], type="primary", use_container_width=True, key="home_btn_today_one"):
                st.session_state.current_page = action['target_page']
                st.rerun()
    except Exception as e:
        # Fallback: 예외 발생 시 기본 추천
        try:
            st.markdown("""
            <div style="padding: 1.5rem; background: #fff3cd; border-radius: 12px; border-left: 4px solid #ffc107;">
                <h4 style="color: #856404; margin-bottom: 0.5rem;">오늘 마감부터 시작</h4>
                <p style="color: #856404; margin-bottom: 1rem; font-size: 0.9rem;">데이터가 없어서 분석이 불가능합니다. 오늘 마감 1회만 하면 홈이 채워집니다.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("📋 점장 마감 하러가기", type="primary", use_container_width=True, key="home_btn_fallback"):
                st.session_state.current_page = "점장 마감"
                st.rerun()
        except Exception:
            pass
    
    render_section_divider()
    
    # ========== 섹션 4: 문제 / 잘한 점 ==========
    try:
        with st.container():
            st.markdown("### 🔴 문제 TOP3 / 🟢 잘한 점 TOP3")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🔴 문제 TOP3")
                try:
                    problems = get_problems_top3(store_id)
                    
                    if not problems:
                        st.markdown("""
                        <div style="padding: 1.5rem; background: #fff3cd; border-radius: 8px; border-left: 4px solid #ffc107;">
                            <p style="color: #856404; margin: 0; margin-bottom: 1rem;">아직 분석할 데이터가 충분하지 않습니다.</p>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("📋 점장 마감 시작하기", use_container_width=True, key="home_btn_problems_fallback"):
                            st.session_state.current_page = "점장 마감"
                            st.rerun()
                    else:
                        for idx, problem in enumerate(problems, 1):
                            st.markdown(f"""
                            <div style="padding: 1rem; background: #f8d7da; border-radius: 8px; border-left: 4px solid #dc3545; margin-bottom: 0.5rem;">
                                <div style="font-weight: 600; color: #721c24; margin-bottom: 0.3rem;">{idx}. {problem['text']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            if st.button(f"보러가기", key=f"home_btn_problem_{idx}", use_container_width=True):
                                st.session_state.current_page = problem['target_page']
                                st.rerun()
                except Exception as e:
                    st.markdown("""
                    <div style="padding: 1.5rem; background: #f8d7da; border-radius: 8px; border-left: 4px solid #dc3545;">
                        <p style="color: #721c24; margin: 0;">문제 분석 중 오류가 발생했습니다.</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("#### 🟢 잘한 점 TOP3")
                try:
                    good_points = get_good_points_top3(store_id)
                    
                    if not good_points:
                        st.markdown("""
                        <div style="padding: 1.5rem; background: #fff3cd; border-radius: 8px; border-left: 4px solid #ffc107;">
                            <p style="color: #856404; margin: 0; margin-bottom: 1rem;">데이터가 쌓이면 자동 분석됩니다.</p>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("📋 점장 마감 시작하기", use_container_width=True, key="home_btn_good_fallback"):
                            st.session_state.current_page = "점장 마감"
                            st.rerun()
                    else:
                        for idx, point in enumerate(good_points, 1):
                            st.markdown(f"""
                            <div style="padding: 1rem; background: #d4edda; border-radius: 8px; border-left: 4px solid #28a745; margin-bottom: 0.5rem;">
                                <div style="font-weight: 600; color: #155724; margin-bottom: 0.3rem;">{idx}. {point['text']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            if st.button(f"보러가기", key=f"home_btn_good_{idx}", use_container_width=True):
                                st.session_state.current_page = point['target_page']
                                st.rerun()
                except Exception as e:
                    st.markdown("""
                    <div style="padding: 1.5rem; background: #d4edda; border-radius: 8px; border-left: 4px solid #28a745;">
                        <p style="color: #155724; margin: 0;">잘한 점 분석 중 오류가 발생했습니다.</p>
                    </div>
                    """, unsafe_allow_html=True)
    except Exception:
        pass
    
    render_section_divider()
    
    # ========== 섹션 5: 이상 징후 ==========
    try:
        with st.container():
            st.markdown("### 🔍 이상 징후")
            
            if data_level < 2:
                st.markdown("""
                <div style="padding: 1.5rem; background: #fff3cd; border-radius: 8px; border-left: 4px solid #ffc107;">
                    <p style="color: #856404; margin: 0;">이상 징후 분석을 위해서는 운영 데이터가 필요합니다. 마감을 꾸준히 입력해주세요.</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="padding: 1.5rem; background: #d1ecf1; border-radius: 8px; border-left: 4px solid #17a2b8;">
                    <p style="color: #0c5460; margin: 0;">이상 징후 분석은 다음 단계에서 추가됩니다.</p>
                </div>
                """, unsafe_allow_html=True)
    except Exception:
        pass
    
    render_section_divider()
    
    # ========== 섹션 6: 미니 차트 ==========
    try:
        with st.container():
            st.markdown("### 📈 미니 차트")
            
            if data_level == 0:
                st.markdown("""
                <div style="padding: 2rem; background: #f8f9fa; border-radius: 8px; text-align: center; border: 2px dashed #dee2e6;">
                    <p style="color: #6c757d; margin: 0;">차트를 표시하려면 데이터가 필요합니다. 마감을 입력해주세요.</p>
                </div>
                """, unsafe_allow_html=True)
            elif data_level == 1:
                st.markdown("""
                <div style="padding: 2rem; background: #fff3cd; border-radius: 8px; text-align: center; border: 2px solid #ffc107;">
                    <p style="color: #856404; margin: 0;">더 많은 차트를 보려면 마감을 꾸준히 입력해주세요.</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="padding: 2rem; background: #d1ecf1; border-radius: 8px; text-align: center; border: 2px solid #17a2b8;">
                    <p style="color: #0c5460; margin: 0;">미니 차트는 다음 단계에서 추가됩니다.</p>
                </div>
                """, unsafe_allow_html=True)
    except Exception:
        pass
    
    render_section_divider()
    
    # ========== 섹션 7: 우리 가게 숫자 구조 ==========
    try:
        with st.container():
            st.markdown("### 🏪 우리 가게 숫자 구조")
            
            if data_level < 3:
                st.markdown("""
                <div style="padding: 1.5rem; background: #fff3cd; border-radius: 8px; border-left: 4px solid #ffc107;">
                    <h4 style="color: #856404; margin-bottom: 0.5rem;">재무 구조를 입력하세요</h4>
                    <p style="color: #856404; margin-bottom: 1rem;">비용 구조와 실제 정산을 입력하면 우리 가게의 숫자 구조를 볼 수 있습니다.</p>
                </div>
                """, unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💳 목표 비용구조", use_container_width=True, key="home_btn_cost"):
                        st.session_state.current_page = "목표 비용구조"
                        st.rerun()
                with col2:
                    if st.button("🧾 실제정산", use_container_width=True, key="home_btn_settlement"):
                        st.session_state.current_page = "실제정산"
                        st.rerun()
            else:
                st.markdown("""
                <div style="padding: 1.5rem; background: #d4edda; border-radius: 8px; border-left: 4px solid #28a745;">
                    <h4 style="color: #155724; margin-bottom: 0.5rem;">우리 가게 숫자 구조가 여기에 표시됩니다</h4>
                    <p style="color: #155724; margin: 0;">숫자 구조 분석은 다음 단계에서 추가됩니다.</p>
                </div>
                """, unsafe_allow_html=True)
    except Exception:
        pass
    
    render_section_divider()
    
    # ========== 섹션 8: 이번 달 운영 메모 ==========
    with st.container():
        st.markdown("### 📝 이번 달 운영 메모")
        
        try:
            # C) 이번 달 운영 메모 최신 5개
            KST = ZoneInfo("Asia/Seoul")
            now_kst = datetime.now(KST)
            memos = get_monthly_memos(store_id, now_kst.year, now_kst.month, limit=5)
            
            if memos:
                for memo_item in memos:
                    memo_date = memo_item.get('date', '')
                    memo_text = memo_item.get('memo', '')
                    
                    # 날짜 포맷: YYYY-MM-DD -> MM/DD
                    try:
                        if isinstance(memo_date, str):
                            date_obj = datetime.strptime(memo_date, '%Y-%m-%d').date()
                        else:
                            date_obj = memo_date
                        date_str = f"{date_obj.month:02d}/{date_obj.day:02d}"
                    except:
                        date_str = str(memo_date)[:10] if memo_date else ""
                    
                    st.markdown(f"""
                    <div style="padding: 1rem; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #17a2b8; margin-bottom: 0.5rem;">
                        <div style="font-weight: 600; color: #0c5460; margin-bottom: 0.3rem;">{date_str}</div>
                        <div style="color: #495057; font-size: 0.95rem;">{memo_text}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="padding: 1.5rem; background: #fff3cd; border-radius: 8px; border-left: 4px solid #ffc107;">
                    <h4 style="color: #856404; margin-bottom: 0.5rem;">운영 메모가 아직 없습니다</h4>
                    <p style="color: #856404; margin-bottom: 1rem; font-size: 0.9rem;">마감 때 특이사항을 남기면 여기에 모입니다.</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("📋 점장 마감", type="primary", use_container_width=True, key="home_btn_memo"):
                    st.session_state.current_page = "점장 마감"
                    st.rerun()
        except Exception as e:
            st.markdown("""
            <div style="padding: 1.5rem; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #6c757d;">
                <p style="color: #495057; margin: 0;">운영 메모를 불러오는 중 오류가 발생했습니다.</p>
            </div>
            """, unsafe_allow_html=True)
