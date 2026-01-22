"""
홈 (사장 계기판) 페이지
Phase 3 / STEP 1: 뼈대 + 데이터 단계 판별만 구현
Phase 3 / STEP 2: 이번 달 매출, 마감률/스트릭, 운영 메모 추가
"""
from src.bootstrap import bootstrap
import streamlit as st
from src.ui_helpers import render_page_header, render_section_divider
from src.auth import get_current_store_id, get_supabase_client
from src.storage_supabase import load_monthly_sales_total, load_expense_structure, load_csv, get_fixed_costs, get_variable_cost_ratio, calculate_break_even_sales
from datetime import datetime, date
from zoneinfo import ZoneInfo
import pandas as pd

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


def get_anomaly_signals(store_id: str) -> list:
    """
    이상 징후 감지 (조기경보 시스템, 룰 기반)
    
    Returns:
        list: [{"icon": str, "text": str, "target_page": str}, ...] 최대 3개
    """
    signals = []
    
    try:
        supabase = get_supabase_client()
        if not supabase:
            return []
        
        KST = ZoneInfo("Asia/Seoul")
        today = datetime.now(KST).date()
        from datetime import timedelta
        
        # 최근 7일 매출 데이터 조회
        seven_days_ago = today - timedelta(days=7)
        sales_recent = supabase.table("sales")\
            .select("date, total_sales")\
            .eq("store_id", store_id)\
            .gte("date", seven_days_ago.isoformat())\
            .lte("date", today.isoformat())\
            .order("date", desc=False)\
            .execute()
        
        sales_data = {}
        if sales_recent.data:
            for row in sales_recent.data:
                date_str = row.get('date')
                total = float(row.get('total_sales', 0) or 0)
                if date_str and total > 0:
                    sales_data[date_str] = total
        
        # A. 최근 3일 연속 매출 감소
        if len(sales_data) >= 3:
            recent_dates = sorted(sales_data.keys())[-3:]
            recent_values = [sales_data[d] for d in recent_dates]
            if len(recent_values) == 3:
                is_decreasing = recent_values[0] > recent_values[1] > recent_values[2]
                if is_decreasing:
                    signals.append({
                        "icon": "📉",
                        "text": "최근 3일 연속 매출이 감소하고 있습니다.",
                        "target_page": "매출 관리"
                    })
                    if len(signals) >= 3:
                        return signals[:3]
        
        # B. 최근 7일 중 매출 공백 2일 이상
        expected_dates = set()
        check_date = seven_days_ago
        while check_date <= today:
            expected_dates.add(check_date.isoformat())
            check_date += timedelta(days=1)
        
        sales_dates = set(sales_data.keys())
        missing_days = expected_dates - sales_dates
        if len(missing_days) >= 2:
            signals.append({
                "icon": "⚠️",
                "text": "최근 7일 중 매출이 입력되지 않은 날이 2일 이상 있습니다.",
                "target_page": "매출 관리"
            })
            if len(signals) >= 3:
                return signals[:3]
        
        # 이번 달 매출 데이터 조회 (C 규칙용)
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
        
        month_sales_list = []
        if sales_month.data:
            for row in sales_month.data:
                total = float(row.get('total_sales', 0) or 0)
                if total > 0:
                    month_sales_list.append(total)
        
        # C. 최근 3일 평균 매출이 이번 달 평균 대비 ±30% 이상 변동
        if len(sales_data) >= 3 and len(month_sales_list) >= 3:
            recent_3_days = list(sales_data.values())[-3:]
            recent_avg = sum(recent_3_days) / len(recent_3_days)
            month_avg = sum(month_sales_list) / len(month_sales_list)
            
            if month_avg > 0:
                ratio = recent_avg / month_avg
                if ratio <= 0.7 or ratio >= 1.3:  # ±30% 이상 변동
                    signals.append({
                        "icon": "📊",
                        "text": "최근 매출 흐름이 이번 달 평균 대비 크게 변했습니다.",
                        "target_page": "매출 관리"
                    })
                    if len(signals) >= 3:
                        return signals[:3]
        
        # D. 특정 메뉴 비중 급등 (최근 3일 vs 그 전 3일)
        if len(sales_data) >= 6:
            # 최근 3일과 그 전 3일 판매 데이터 비교
            recent_3_start = today - timedelta(days=3)
            prev_3_start = today - timedelta(days=6)
            
            sales_items_recent_3 = supabase.table("v_daily_sales_items_effective")\
                .select("menu_id, qty")\
                .eq("store_id", store_id)\
                .gte("date", recent_3_start.isoformat())\
                .lte("date", today.isoformat())\
                .execute()
            
            sales_items_prev_3 = supabase.table("v_daily_sales_items_effective")\
                .select("menu_id, qty")\
                .eq("store_id", store_id)\
                .gte("date", prev_3_start.isoformat())\
                .lt("date", recent_3_start.isoformat())\
                .execute()
            
            if sales_items_recent_3.data and sales_items_prev_3.data:
                # 최근 3일 메뉴별 합계
                recent_menu_totals = {}
                recent_total = 0
                for row in sales_items_recent_3.data:
                    menu_id = row.get('menu_id')
                    qty = int(row.get('qty', 0) or 0)
                    if menu_id and qty > 0:
                        recent_menu_totals[menu_id] = recent_menu_totals.get(menu_id, 0) + qty
                        recent_total += qty
                
                # 그 전 3일 메뉴별 합계
                prev_menu_totals = {}
                prev_total = 0
                for row in sales_items_prev_3.data:
                    menu_id = row.get('menu_id')
                    qty = int(row.get('qty', 0) or 0)
                    if menu_id and qty > 0:
                        prev_menu_totals[menu_id] = prev_menu_totals.get(menu_id, 0) + qty
                        prev_total += qty
                
                # 특정 메뉴 비중 급등 체크
                if recent_total > 0 and prev_total > 0:
                    for menu_id in recent_menu_totals:
                        recent_ratio = recent_menu_totals[menu_id] / recent_total
                        prev_ratio = prev_menu_totals.get(menu_id, 0) / prev_total if prev_total > 0 else 0
                        
                        if prev_ratio > 0 and recent_ratio >= prev_ratio * 1.5:  # 50% 이상 증가
                            signals.append({
                                "icon": "🍽️",
                                "text": "최근 판매에서 특정 메뉴 비중이 급격히 증가했습니다.",
                                "target_page": "판매 관리"
                            })
                            if len(signals) >= 3:
                                return signals[:3]
                            break
        
        # E. 최근 5일 판매량 급감
        five_days_ago = today - timedelta(days=5)
        sales_items_recent_5 = supabase.table("v_daily_sales_items_effective")\
            .select("qty")\
            .eq("store_id", store_id)\
            .gte("date", five_days_ago.isoformat())\
            .lte("date", today.isoformat())\
            .execute()
        
        sales_items_prev_5 = supabase.table("v_daily_sales_items_effective")\
            .select("qty")\
            .eq("store_id", store_id)\
            .gte("date", (five_days_ago - timedelta(days=5)).isoformat())\
            .lt("date", five_days_ago.isoformat())\
            .execute()
        
        if sales_items_recent_5.data and sales_items_prev_5.data:
            recent_total_qty = sum(int(row.get('qty', 0) or 0) for row in sales_items_recent_5.data)
            prev_total_qty = sum(int(row.get('qty', 0) or 0) for row in sales_items_prev_5.data)
            
            if prev_total_qty > 0:
                decline_ratio = recent_total_qty / prev_total_qty
                if decline_ratio <= 0.7:  # 30% 이상 감소
                    signals.append({
                        "icon": "📉",
                        "text": "최근 판매량이 눈에 띄게 줄었습니다.",
                        "target_page": "판매 관리"
                    })
                    if len(signals) >= 3:
                        return signals[:3]
        
        # F. 최근 3일 연속 마감 누락
        daily_close_recent = supabase.table("daily_close")\
            .select("date")\
            .eq("store_id", store_id)\
            .gte("date", (today - timedelta(days=3)).isoformat())\
            .lte("date", today.isoformat())\
            .execute()
        
        closed_dates_recent = set()
        if daily_close_recent.data:
            for row in daily_close_recent.data:
                date_str = row.get('date')
                if date_str:
                    closed_dates_recent.add(date_str)
        
        # 최근 3일 중 마감 없는 날 확인
        missing_close_count = 0
        check_date = today - timedelta(days=2)  # 어제부터 3일 전까지
        while check_date <= today:
            if check_date.isoformat() not in closed_dates_recent:
                missing_close_count += 1
            check_date += timedelta(days=1)
        
        if missing_close_count >= 3:
            signals.append({
                "icon": "⏰",
                "text": "최근 3일 연속 마감이 없습니다.",
                "target_page": "점장 마감"
            })
        
        # 최대 3개만 반환
        return signals[:3]
        
    except Exception as e:
        return []


def get_store_financial_structure(store_id: str, target_year: int, target_month: int) -> dict:
    """
    우리 가게 숫자 구조 데이터 조회
    
    우선순위:
    1. actual_settlement (해당 월 final 존재 시)
    2. expense_structure + targets
    3. 없으면 None
    
    Returns:
        dict: {
            "source": "actual" | "target" | "none",
            "fixed_cost": int,
            "variable_ratio": float (0~1),
            "break_even_sales": int,
            "example_table": [{"sales": int, "profit": int, "margin": float}, ...] or None
        }
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return {"source": "none", "fixed_cost": 0, "variable_ratio": 0.0, "break_even_sales": 0, "example_table": None}
        
        # 공식 엔진 함수 사용 (헌법 준수)
        # 우선순위는 엔진 함수 내부에서 처리됨 (actual_settlement final → expense_structure)
        fixed_cost = get_fixed_costs(store_id, target_year, target_month)
        variable_ratio = get_variable_cost_ratio(store_id, target_year, target_month)
        break_even_sales = calculate_break_even_sales(store_id, target_year, target_month)
        
        # source 판별: actual_settlement final 존재 여부 확인
        from src.storage_supabase import get_month_settlement_status
        month_status = get_month_settlement_status(store_id, target_year, target_month)
        source = "actual" if month_status == 'final' else "target" if fixed_cost > 0 or variable_ratio > 0 else "none"
        
        # 손익분기점이 0이면 데이터 없음으로 처리
        if break_even_sales <= 0:
            return {"source": "none", "fixed_cost": 0, "variable_ratio": 0.0, "break_even_sales": 0, "example_table": None}
        
        # example_table 생성
        example_table = None
        if break_even_sales > 0:
            example_sales = [
                max(int(break_even_sales * 0.8), 0),
                int(break_even_sales),
                int(break_even_sales * 1.2),
                int(break_even_sales * 1.5)
            ]
            example_table = []
            for sales in example_sales:
                if sales > 0:
                    profit = sales - fixed_cost - (sales * variable_ratio)
                    margin = (profit / sales * 100) if sales > 0 else 0.0
                    example_table.append({
                        "sales": sales,
                        "profit": int(profit),
                        "margin": round(margin, 1)
                    })
        
        return {
            "source": source,
            "fixed_cost": int(fixed_cost),
            "variable_ratio": variable_ratio,
            "break_even_sales": int(break_even_sales),
            "example_table": example_table
        }
        
    except Exception as e:
        return {"source": "none", "fixed_cost": 0, "variable_ratio": 0.0, "break_even_sales": 0, "example_table": None}


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


def get_menu_count(store_id: str) -> int:
    """
    메뉴 개수 조회 (온보딩 미션용)
    
    Returns:
        int: menu_master 개수 (실패 시 0)
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return 0
        
        result = supabase.table("menu_master")\
            .select("id", count="exact")\
            .eq("store_id", store_id)\
            .execute()
        
        count = result.count if hasattr(result, 'count') and result.count is not None else (len(result.data) if result.data else 0)
        return count
        
    except Exception as e:
        return 0


def get_close_count(store_id: str) -> int:
    """
    점장마감 개수 조회 (온보딩 미션용)
    
    Returns:
        int: daily_close 개수 (실패 시 0)
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return 0
        
        result = supabase.table("daily_close")\
            .select("id", count="exact")\
            .eq("store_id", store_id)\
            .execute()
        
        count = result.count if hasattr(result, 'count') and result.count is not None else (len(result.data) if result.data else 0)
        return count
        
    except Exception as e:
        return 0


def get_today_one_action(store_id: str, level: int) -> dict:
    """
    오늘 하나만 추천 액션 결정 (룰 기반)
    미션 진행률을 고려하여 추천
    
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
        
        # 미션 진행률 체크 (미션 2 미완료 시 무조건 점장마감 유도)
        close_count = get_close_count(store_id)
        if close_count < 3:
            return {
                "title": "점장마감 3회 달성하기",
                "reason": f"현재 {close_count}회 완료. 3번만 하면 홈이 자동으로 흐름을 읽기 시작합니다.",
                "button_label": "📋 점장 마감 하러가기",
                "target_page": "점장 마감"
            }
        
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


def render_day0_home():
    """DAY 0 전용 홈 화면 (데이터 0단계용)"""
    try:
        store_id = get_current_store_id()
        if not store_id:
            st.error("매장 정보를 찾을 수 없습니다. 로그인 상태를 확인해주세요.")
            return
        
        # ========== [A] HERO 영역 ==========
        st.markdown("""
        <div style="padding: 3rem 2rem; text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 16px; color: white; margin-bottom: 2rem;">
            <div style="font-size: 1.2rem; margin-bottom: 1rem; opacity: 0.95;">👋 사장님, 환영합니다.</div>
            <div style="font-size: 2.5rem; font-weight: 700; margin-bottom: 1rem; line-height: 1.2;">
                ⭐ 선택받는 가게는, 숫자가 다릅니다.
            </div>
            <div style="font-size: 1.5rem; font-weight: 500; margin-bottom: 1.5rem; opacity: 0.95;">
                이제 장사는, 숫자가 알려줍니다.
            </div>
            <div style="font-size: 1.1rem; line-height: 1.8; margin-bottom: 1rem; opacity: 0.9;">
                이 앱은 매출을 올리는 방법을<br>
                감이 아니라 숫자로 알려주는 사장 전용 화면입니다.
            </div>
            <div style="font-size: 1.1rem; font-weight: 600; opacity: 0.95;">
                오늘부터, 장사는 느낌이 아니라 판단으로 합니다.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # ========== [B] 첫 행동 카드 ==========
        st.markdown("""
        <div style="padding: 2.5rem; background: #ffffff; border-radius: 16px; border: 3px solid #667eea; margin-bottom: 2rem; text-align: center;">
            <h2 style="color: #333; margin-bottom: 1rem; font-size: 1.8rem;">오늘 장사를 마감해보세요</h2>
            <p style="color: #666; font-size: 1.1rem; line-height: 1.6; margin-bottom: 2rem;">
                하루를 정리해야, 이 화면이 사장님 가게 계기판으로 바뀝니다.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # 점장마감 버튼
        if st.button("👉 점장마감 하러 가기", type="primary", use_container_width=True, key="day0_btn_close"):
            st.session_state.current_page = "점장 마감"
            st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # ========== [C] 처음 오신 사장님을 위한 3단계 ==========
        st.markdown("### 처음 오신 사장님을 위한 3단계")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style="padding: 1.5rem; background: #f8f9fa; border-radius: 12px; border-left: 4px solid #667eea; height: 100%;">
                <div style="font-size: 1.1rem; font-weight: 700; color: #667eea; margin-bottom: 0.5rem;">STEP 1</div>
                <div style="font-size: 1rem; color: #333; line-height: 1.6; margin-bottom: 1rem;">
                    메뉴·재료 3개만 등록하기<br>
                    <span style="font-size: 0.9rem; color: #666;">(가게 구조 만들기)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            col1_btn1, col1_btn2 = st.columns(2)
            with col1_btn1:
                if st.button("메뉴 등록", use_container_width=True, key="day0_btn_menu"):
                    st.session_state.current_page = "메뉴 관리"
                    st.rerun()
            with col1_btn2:
                if st.button("재료 등록", use_container_width=True, key="day0_btn_ingredient"):
                    st.session_state.current_page = "재료 관리"
                    st.rerun()
        
        with col2:
            st.markdown("""
            <div style="padding: 1.5rem; background: #f8f9fa; border-radius: 12px; border-left: 4px solid #4facfe; height: 100%;">
                <div style="font-size: 1.1rem; font-weight: 700; color: #4facfe; margin-bottom: 0.5rem;">STEP 2</div>
                <div style="font-size: 1rem; color: #333; line-height: 1.6; margin-bottom: 1rem;">
                    오늘 장사 마감 한 번<br>
                    <span style="font-size: 0.9rem; color: #666;">(홈 화면이 바뀌기 시작)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("점장 마감", use_container_width=True, key="day0_btn_close_step2"):
                st.session_state.current_page = "점장 마감"
                st.rerun()
        
        with col3:
            st.markdown("""
            <div style="padding: 1.5rem; background: #f8f9fa; border-radius: 12px; border-left: 4px solid #43e97b; height: 100%;">
                <div style="font-size: 1.1rem; font-weight: 700; color: #43e97b; margin-bottom: 0.5rem;">STEP 3</div>
                <div style="font-size: 1rem; color: #333; line-height: 1.6; margin-bottom: 1rem;">
                    이번 달 성적표 만들기<br>
                    <span style="font-size: 0.9rem; color: #666;">(사장님 가게 돈 구조 완성)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("실제정산", use_container_width=True, key="day0_btn_settlement"):
                st.session_state.current_page = "실제정산"
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # ========== [D] 불안 제거 블록 ==========
        st.markdown("""
        <div style="padding: 2rem; background: #e7f3ff; border-radius: 12px; border-left: 4px solid #4facfe; text-align: center; margin-top: 2rem;">
            <p style="color: #0c5460; font-size: 1.1rem; line-height: 1.8; margin: 0;">
                지금은 아무 숫자도 없어도 괜찮습니다.<br>
                사장님 가게는 오늘부터 만들어집니다.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"DAY 0 홈 화면을 표시하는 중 오류가 발생했습니다: {str(e)}")
        # 오류 발생 시 기본 안내 표시
        st.info("오늘부터 마감을 시작하세요. 점장 마감 페이지로 이동해주세요.")
        if st.button("점장 마감 하러 가기", type="primary"):
            st.session_state.current_page = "점장 마감"
            st.rerun()


def render_home():
    """홈 (사장 계기판) 페이지 렌더링"""
    store_id = get_current_store_id()
    if not store_id:
        st.error("매장 정보를 찾을 수 없습니다. 로그인 상태를 확인해주세요.")
        return
    
    # 데이터 단계 판별 (매번 체크하여 최신 상태 유지)
    data_level = detect_data_level(store_id)
    st.session_state.home_data_level = data_level
    
    # DAY 0 전용 홈 화면 표시
    if data_level == 0:
        render_day0_home()
        return
    
    # 기존 홈 화면 렌더링
    render_page_header("사장 계기판", "🏠")
    
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
    
    # ========== 섹션 1.5: 시작 미션 3개 ==========
    try:
        with st.container():
            st.markdown("### 🚀 시작 미션 3개")
            
            # 미션 진행률 조회
            menu_count = get_menu_count(store_id)
            close_count = get_close_count(store_id)
            KST = ZoneInfo("Asia/Seoul")
            now_kst = datetime.now(KST)
            has_settlement = check_actual_settlement_exists(store_id, now_kst.year, now_kst.month)
            
            # 미션 완료 여부 계산
            mission1_complete = menu_count >= 3
            mission2_complete = close_count >= 3
            mission3_complete = has_settlement
            
            # 진행률 계산 (각 미션 0~1점, 총점/3)
            completed_count = sum([mission1_complete, mission2_complete, mission3_complete])
            progress_percentage = (completed_count / 3.0) * 100
            
            # 진행률 바 표시
            st.progress(progress_percentage / 100.0)
            
            # 상태 메시지 결정
            if progress_percentage <= 33:
                status_msg = "기본 데이터 만드는 단계"
            elif progress_percentage <= 66:
                status_msg = "가게가 숫자로 보이기 시작하는 구간"
            elif progress_percentage < 100:
                remaining = 3 - completed_count
                status_msg = f"이제 거의 완성 단계 — {remaining}개만 더 하면 홈이 '자동 코치 모드'로 진화합니다."
            else:
                status_msg = "✅ 자동 코치 모드 활성화"
            
            # 진행률 상태 메시지 표시
            st.caption(f"온보딩 진행률 {int(progress_percentage)}% — {status_msg}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # 완료 보상 문장 표시
            reward_messages = []
            if mission1_complete:
                reward_messages.append("✅ 메뉴 기반이 생겨서 판매/원가 분석이 정확해졌습니다.")
            if mission2_complete:
                reward_messages.append("✅ 점장마감 데이터가 쌓여서 홈이 자동으로 흐름을 읽기 시작합니다.")
            if mission3_complete:
                reward_messages.append("✅ 이번 달 성적표가 완성되어 손익 구조가 잠겼습니다.")
            
            if reward_messages:
                for msg in reward_messages:
                    st.info(msg)
                st.markdown("<br>", unsafe_allow_html=True)
            
            # 미션 1: 메뉴 3개 등록
            mission1_icon = "✅" if mission1_complete else "⬜"
            mission1_bg = "#d4edda" if mission1_complete else "#f8f9fa"
            mission1_border = "#28a745" if mission1_complete else "#6c757d"
            mission1_progress = f'<span style="font-size: 0.9rem; color: #666; font-weight: normal;">({menu_count}/3)</span>' if not mission1_complete else ""
            
            mission1_html = (
                f'<div style="padding: 1.2rem; background: {mission1_bg}; border-radius: 8px; '
                f'border-left: 4px solid {mission1_border}; margin-bottom: 1rem;">'
                f'<div style="display: flex; align-items: center; margin-bottom: 0.5rem;">'
                f'<span style="font-size: 1.5rem; margin-right: 0.8rem;">{mission1_icon}</span>'
                f'<div style="flex: 1;">'
                f'<div style="font-weight: 600; color: #333; font-size: 1.1rem; margin-bottom: 0.3rem;">'
                f'미션 1: 메뉴 3개 등록하기 {mission1_progress}'
                f'</div>'
                f'<div style="color: #666; font-size: 0.95rem;">메뉴가 있어야 판매/원가/분석이 의미가 생깁니다.</div>'
                f'</div></div></div>'
            )
            st.markdown(mission1_html, unsafe_allow_html=True)
            if not mission1_complete:
                if st.button("메뉴 등록", key="mission1_btn", use_container_width=True):
                    st.session_state.current_page = "메뉴 등록"
                    st.rerun()
            
            # 미션 2: 점장마감 3회
            mission2_icon = "✅" if mission2_complete else "⬜"
            mission2_bg = "#d4edda" if mission2_complete else "#f8f9fa"
            mission2_border = "#28a745" if mission2_complete else "#6c757d"
            mission2_progress = f'<span style="font-size: 0.9rem; color: #666; font-weight: normal;">({close_count}/3)</span>' if not mission2_complete else ""
            
            mission2_html = (
                f'<div style="padding: 1.2rem; background: {mission2_bg}; border-radius: 8px; '
                f'border-left: 4px solid {mission2_border}; margin-bottom: 1rem;">'
                f'<div style="display: flex; align-items: center; margin-bottom: 0.5rem;">'
                f'<span style="font-size: 1.5rem; margin-right: 0.8rem;">{mission2_icon}</span>'
                f'<div style="flex: 1;">'
                f'<div style="font-weight: 600; color: #333; font-size: 1.1rem; margin-bottom: 0.3rem;">'
                f'미션 2: 점장마감 3회 하기 {mission2_progress}'
                f'</div>'
                f'<div style="color: #666; font-size: 0.95rem;">3번만 하면 홈이 자동으로 흐름을 읽기 시작합니다.</div>'
                f'</div></div></div>'
            )
            st.markdown(mission2_html, unsafe_allow_html=True)
            if not mission2_complete:
                if st.button("점장 마감", key="mission2_btn", use_container_width=True):
                    st.session_state.current_page = "점장 마감"
                    st.rerun()
            
            # 미션 3: 이번 달 성적표 1회
            mission3_icon = "✅" if mission3_complete else "⬜"
            mission3_bg = "#d4edda" if mission3_complete else "#f8f9fa"
            mission3_border = "#28a745" if mission3_complete else "#6c757d"
            
            mission3_html = (
                f'<div style="padding: 1.2rem; background: {mission3_bg}; border-radius: 8px; '
                f'border-left: 4px solid {mission3_border}; margin-bottom: 1rem;">'
                f'<div style="display: flex; align-items: center; margin-bottom: 0.5rem;">'
                f'<span style="font-size: 1.5rem; margin-right: 0.8rem;">{mission3_icon}</span>'
                f'<div style="flex: 1;">'
                f'<div style="font-weight: 600; color: #333; font-size: 1.1rem; margin-bottom: 0.3rem;">'
                f'미션 3: 이번 달 성적표 1회 만들기'
                f'</div>'
                f'<div style="color: #666; font-size: 0.95rem;">우리 가게 돈 구조(손익분기점/이익구조)가 완성됩니다.</div>'
                f'</div></div></div>'
            )
            st.markdown(mission3_html, unsafe_allow_html=True)
            if not mission3_complete:
                if st.button("실제정산", key="mission3_btn", use_container_width=True):
                    st.session_state.current_page = "실제정산"
                    st.rerun()
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # ========== 추천 다음 행동 1개 ==========
            st.markdown("#### 💡 지금 가장 좋은 다음 행동")
            
            # 우선순위에 따라 추천 행동 결정
            if not mission2_complete:
                # 우선순위 1: 점장마감 미완료
                st.info("점장마감을 3회 하면 홈이 자동으로 흐름을 읽기 시작합니다.")
                if st.button("점장 마감 하러 가기", type="primary", use_container_width=True, key="mission_next_close"):
                    st.session_state.current_page = "점장 마감"
                    st.rerun()
            elif not mission1_complete:
                # 우선순위 2: 메뉴 미완료
                st.info("메뉴가 있어야 판매/원가/분석이 의미가 생깁니다.")
                if st.button("메뉴 등록 하러 가기", type="primary", use_container_width=True, key="mission_next_menu"):
                    st.session_state.current_page = "메뉴 등록"
                    st.rerun()
            elif not mission3_complete:
                # 우선순위 3: 실제정산 미완료
                st.info("이번 달 성적표가 완성되면 손익 구조가 잠깁니다.")
                if st.button("실제정산 하러 가기", type="primary", use_container_width=True, key="mission_next_settlement"):
                    st.session_state.current_page = "실제정산"
                    st.rerun()
            else:
                # 모두 완료
                st.success("🎉 기본 세팅이 끝났습니다. 이제 홈이 매일 가게를 읽어드립니다.")
                st.caption("💡 팁: 매일 점장마감을 하시면 홈이 자동으로 매출 흐름과 문제점을 분석해드립니다.")
    except Exception as e:
        # 미션 섹션 오류 시에도 홈이 죽지 않도록
        pass
    
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
            st.markdown("### ⚠️ 이상 징후")
            
            try:
                signals = get_anomaly_signals(store_id)
                
                if not signals:
                    st.markdown("""
                    <div style="padding: 1.5rem; background: #d4edda; border-radius: 8px; border-left: 4px solid #28a745;">
                        <p style="color: #155724; margin: 0; font-weight: 500;">현재 감지된 이상 징후가 없습니다.</p>
                        <p style="color: #155724; margin: 0.5rem 0 0 0; font-size: 0.9rem;">정상 범위로 보입니다.</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    for idx, signal in enumerate(signals, 1):
                        st.markdown(f"""
                        <div style="padding: 1rem; background: #fff3cd; border-radius: 8px; border-left: 4px solid #ffc107; margin-bottom: 0.5rem;">
                            <div style="display: flex; align-items: center; margin-bottom: 0.3rem;">
                                <span style="font-size: 1.2rem; margin-right: 0.5rem;">{signal['icon']}</span>
                                <div style="font-weight: 600; color: #856404; flex: 1;">{signal['text']}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button(f"보러가기", key=f"home_btn_anomaly_{idx}", use_container_width=True):
                            st.session_state.current_page = signal['target_page']
                            st.rerun()
            except Exception as e:
                st.markdown("""
                <div style="padding: 1.5rem; background: #f8d7da; border-radius: 8px; border-left: 4px solid #dc3545;">
                    <p style="color: #721c24; margin: 0;">이상 징후 분석 중 오류가 발생했습니다.</p>
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
            
            # 이번 달 정보
            KST = ZoneInfo("Asia/Seoul")
            now_kst = datetime.now(KST)
            current_year = now_kst.year
            current_month = now_kst.month
            
            # 숫자 구조 데이터 조회
            try:
                structure = get_store_financial_structure(store_id, current_year, current_month)
                
                if structure["source"] == "none":
                    # 데이터 없을 때
                    st.markdown("""
                    <div style="padding: 1.5rem; background: #fff3cd; border-radius: 8px; border-left: 4px solid #ffc107;">
                        <h4 style="color: #856404; margin-bottom: 0.5rem;">아직 우리 가게의 숫자 구조가 만들어지지 않았습니다</h4>
                        <p style="color: #856404; margin-bottom: 1rem; font-size: 0.9rem;">목표 비용구조 또는 실제 정산을 먼저 입력하면 자동으로 생성됩니다.</p>
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
                    # 데이터 있을 때
                    fixed_cost = structure["fixed_cost"]
                    variable_ratio = structure["variable_ratio"]
                    break_even = structure["break_even_sales"]
                    example_table = structure["example_table"]
                    source_label = "이번 달 실제 정산 기준" if structure["source"] == "actual" else "현재 목표 구조 기준"
                    
                    # 상단 요약 카드 3개
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown(f"""
                        <div style="padding: 1.2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px; text-align: center; color: white;">
                            <div style="font-size: 0.85rem; opacity: 0.9; margin-bottom: 0.3rem;">고정비</div>
                            <div style="font-size: 1.3rem; font-weight: 700;">{fixed_cost:,}원</div>
                            <div style="font-size: 0.75rem; opacity: 0.8; margin-top: 0.2rem;">/월</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        variable_pct = int(variable_ratio * 100)
                        st.markdown(f"""
                        <div style="padding: 1.2rem; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 8px; text-align: center; color: white;">
                            <div style="font-size: 0.85rem; opacity: 0.9; margin-bottom: 0.3rem;">변동비율</div>
                            <div style="font-size: 1.3rem; font-weight: 700;">{variable_pct}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col3:
                        st.markdown(f"""
                        <div style="padding: 1.2rem; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 8px; text-align: center; color: white;">
                            <div style="font-size: 0.85rem; opacity: 0.9; margin-bottom: 0.3rem;">손익분기점 매출</div>
                            <div style="font-size: 1.3rem; font-weight: 700;">{break_even:,}원</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # 한 줄 구조 문장
                    if break_even > 0:
                        margin_per_100k = int((100000 * (1 - variable_ratio)))
                        st.markdown(f"""
                        <div style="padding: 1rem; background: #d1ecf1; border-radius: 8px; border-left: 4px solid #17a2b8; margin-top: 1rem;">
                            <p style="color: #0c5460; margin: 0; font-size: 0.95rem; line-height: 1.6;">
                                이 가게는 매출 <strong>{break_even:,}원</strong>부터 흑자가 시작되고,<br>
                                매출이 10만 원 늘면 약 <strong>{margin_per_100k:,}원</strong>이 남는 구조입니다.
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # 미니 테이블
                    if example_table and len(example_table) > 0:
                        st.markdown("---")
                        st.markdown("#### 📊 매출 구간별 예상 이익")
                        
                        # 최대 3행만 표시
                        display_table = example_table[:3]
                        
                        for item in display_table:
                            sales = item["sales"]
                            profit = item["profit"]
                            margin = item["margin"]
                            profit_color = "#28a745" if profit >= 0 else "#dc3545"
                            st.markdown(f"""
                            <div style="padding: 0.8rem; background: #f8f9fa; border-radius: 6px; margin-bottom: 0.5rem; border-left: 3px solid {profit_color};">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div style="font-weight: 600; color: #495057;">매출 {sales:,}원</div>
                                    <div style="text-align: right;">
                                        <div style="font-weight: 600; color: {profit_color};">{profit:,}원</div>
                                        <div style="font-size: 0.85rem; color: #6c757d;">이익률 {margin}%</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # 출처 배지
                    st.caption(f"📌 {source_label}")
                    
            except Exception as e:
                st.markdown("""
                <div style="padding: 1.5rem; background: #fff3cd; border-radius: 8px; border-left: 4px solid #ffc107;">
                    <h4 style="color: #856404; margin-bottom: 0.5rem;">숫자 구조를 불러오는 중 오류가 발생했습니다</h4>
                    <p style="color: #856404; margin-bottom: 1rem; font-size: 0.9rem;">목표 비용구조 또는 실제 정산을 먼저 입력해주세요.</p>
                </div>
                """, unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💳 목표 비용구조", use_container_width=True, key="home_btn_cost_error"):
                        st.session_state.current_page = "목표 비용구조"
                        st.rerun()
                with col2:
                    if st.button("🧾 실제정산", use_container_width=True, key="home_btn_settlement_error"):
                        st.session_state.current_page = "실제정산"
                        st.rerun()
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
