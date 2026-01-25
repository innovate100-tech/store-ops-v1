"""
홈 코칭 최소 엔진 v1
Phase 1 STEP 4: 매출 1건만 있어도 홈 상단에 항상 (1) 한 줄 코칭 + (2) 오늘 할 일 1개(CTA) 표시
"""
from __future__ import annotations

import logging
import streamlit as st
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, Optional

from src.auth import get_supabase_client, get_current_store_id
from src.storage_supabase import load_best_available_daily_sales
from src.ui_helpers import safe_get_value

logger = logging.getLogger(__name__)


@st.cache_data(ttl=60, show_spinner=False)  # 1분 캐시 (짧은 TTL)
def _load_recent_sales_for_coach(store_id: str, days: int = 7) -> tuple[Optional[float], Optional[float]]:
    """
    최근 N일 매출 데이터 로드 (코칭 엔진용)
    
    Returns:
        tuple: (yesterday_sales, avg_sales)
        - yesterday_sales: 어제 매출 (없으면 가장 최근 매출일)
        - avg_sales: 최근 N일 평균 (데이터 부족 시 None)
    """
    if not store_id:
        return None, None
    
    try:
        kst = ZoneInfo("Asia/Seoul")
        now = datetime.now(kst)
        today = now.date()
        yesterday = today - timedelta(days=1)
        
        # 최근 N일 매출 조회
        start_date = (today - timedelta(days=days)).isoformat()
        end_date = (today - timedelta(days=1)).isoformat()  # 어제까지
        
        sales_df = load_best_available_daily_sales(
            store_id=store_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if sales_df.empty or 'total_sales' not in sales_df.columns:
            return None, None
        
        # 어제 매출 확인
        yesterday_sales = None
        yesterday_str = yesterday.isoformat()
        yesterday_row = sales_df[sales_df['date'] == yesterday_str]
        if not yesterday_row.empty and len(yesterday_row) > 0:
            # DataFrame에서 첫 행의 total_sales 가져오기 (안전하게)
            try:
                yesterday_sales = float(yesterday_row.iloc[0]['total_sales'] or 0)
            except (IndexError, KeyError):
                yesterday_sales = None
        else:
            # 어제가 없으면 가장 최근 매출일 사용
            if not sales_df.empty:
                try:
                    sales_df_sorted = sales_df.sort_values('date', ascending=False)
                    if len(sales_df_sorted) > 0:
                        yesterday_sales = float(sales_df_sorted.iloc[0]['total_sales'] or 0)
                except (IndexError, KeyError):
                    yesterday_sales = None
        
        # 평균 계산
        avg_sales = None
        valid_sales = sales_df[sales_df['total_sales'] > 0]['total_sales'].tolist()
        if valid_sales:
            avg_sales = sum(valid_sales) / len(valid_sales)
        
        return yesterday_sales, avg_sales
    
    except Exception as e:
        logger.warning(f"_load_recent_sales_for_coach 실패: {e}")
        return None, None


@st.cache_data(ttl=60, show_spinner=False)  # 1분 캐시
def _check_sales_count(store_id: str) -> int:
    """
    매출 건수 확인 (코칭 엔진용)
    
    Returns:
        int: 매출 건수 (0 이상)
    """
    if not store_id:
        return 0
    
    try:
        supabase = get_supabase_client()
        if not supabase:
            return 0
        
        result = supabase.table("sales")\
            .select("id", count="exact")\
            .eq("store_id", store_id)\
            .execute()
        
        count = result.count if hasattr(result, "count") and result.count is not None else (len(result.data) if result.data else 0)
        return count
    
    except Exception as e:
        logger.warning(f"_check_sales_count 실패: {e}")
        return 0


def build_minicoach_v1(store_id: str) -> Dict:
    """
    홈 코칭 최소 엔진 v1
    
    Phase 1 STEP 4: 매출 1건만 있어도 홈 상단에 항상 (1) 한 줄 코칭 + (2) 오늘 할 일 1개(CTA) 표시
    
    Args:
        store_id: 매장 ID
    
    Returns:
        dict: {
            "status": "NEED_SALES|FIRST_SALE|DOWN_STRONG|DOWN_MILD|UP_STRONG|STABLE",
            "title": "📌 오늘의 한 줄 코칭",
            "coach_line": "...",
            "action_line": "...",
            "cta": {"label": "...", "page": "..."},
            "debug": {... optional ...}
        }
    """
    if not store_id:
        return {
            "status": "NEED_SALES",
            "title": "📌 오늘의 한 줄 코칭",
            "coach_line": "매장 정보를 찾을 수 없습니다.",
            "action_line": "로그인 상태를 확인해주세요.",
            "cta": None,
            "debug": {"error": "store_id 없음"}
        }
    
    try:
        # 1. 매출 건수 확인
        sales_count = _check_sales_count(store_id)
        
        # 2. 매출 0건 → NEED_SALES
        if sales_count == 0:
            return {
                "status": "NEED_SALES",
                "title": "📌 오늘의 한 줄 코칭",
                "coach_line": "매출이 0건이라 코칭을 시작할 수 없어요.",
                "action_line": "오늘 매출(카드/현금/합계 중 1개)만 입력하면 시작됩니다.",
                "cta": {
                    "label": "💰 오늘 매출 입력하기",
                    "page": "일일 입력(통합)"
                },
                "debug": {"sales_count": 0}
            }
        
        # 3. 최근 매출 데이터 로드
        yesterday_sales, avg_sales_7 = _load_recent_sales_for_coach(store_id, days=7)
        
        # 4. 매출 1건 & 비교 평균 없음 → FIRST_SALE
        if sales_count == 1 and (avg_sales_7 is None or avg_sales_7 == 0):
            return {
                "status": "FIRST_SALE",
                "title": "📌 오늘의 한 줄 코칭",
                "coach_line": "첫 매출이 기록됐어요. 지금부터 2~3건만 쌓이면 패턴이 보입니다.",
                "action_line": "내일도 매출 1개만 입력하세요(30초 컷).",
                "cta": {
                    "label": "💰 오늘 매출 입력하기",
                    "page": "일일 입력(통합)"
                },
                "debug": {"sales_count": 1, "yesterday_sales": yesterday_sales, "avg_sales": avg_sales_7}
            }
        
        # 5. 비교 평균이 없으면 최근 3일로 재시도
        if avg_sales_7 is None or avg_sales_7 == 0:
            yesterday_sales, avg_sales_3 = _load_recent_sales_for_coach(store_id, days=3)
            avg_sales = avg_sales_3
        else:
            avg_sales = avg_sales_7
        
        # 6. 비교 평균이 여전히 없으면 FIRST_SALE
        if avg_sales is None or avg_sales == 0:
            return {
                "status": "FIRST_SALE",
                "title": "📌 오늘의 한 줄 코칭",
                "coach_line": "첫 매출이 기록됐어요. 지금부터 2~3건만 쌓이면 패턴이 보입니다.",
                "action_line": "내일도 매출 1개만 입력하세요(30초 컷).",
                "cta": {
                    "label": "💰 오늘 매출 입력하기",
                    "page": "일일 입력(통합)"
                },
                "debug": {"sales_count": sales_count, "yesterday_sales": yesterday_sales, "avg_sales": avg_sales}
            }
        
        # 7. 어제 매출이 없으면 가장 최근 매출일 사용 (이미 _load_recent_sales_for_coach에서 처리)
        if yesterday_sales is None or yesterday_sales == 0:
            return {
                "status": "FIRST_SALE",
                "title": "📌 오늘의 한 줄 코칭",
                "coach_line": "매출 데이터를 불러오는 중입니다.",
                "action_line": "오늘 매출을 입력하세요.",
                "cta": {
                    "label": "💰 오늘 매출 입력하기",
                    "page": "일일 입력(통합)"
                },
                "debug": {"sales_count": sales_count, "yesterday_sales": yesterday_sales, "avg_sales": avg_sales}
            }
        
        # 8. 비교 평균 있음 → 조건표에 따라 분기
        delta_pct = ((yesterday_sales - avg_sales) / avg_sales * 100) if avg_sales > 0 else 0
        
        if yesterday_sales < avg_sales * 0.80:
            # DOWN_STRONG
            return {
                "status": "DOWN_STRONG",
                "title": "📌 오늘의 한 줄 코칭",
                "coach_line": f"어제 매출 {int(yesterday_sales):,}원 → 최근 평균 {int(avg_sales):,}원 대비 {int(delta_pct)}% 입니다.",
                "action_line": "오늘은 유인메뉴 1개를 '첫 화면/첫 문장'에 고정하세요.",
                "cta": None,  # 홈 유지
                "debug": {"yesterday_sales": yesterday_sales, "avg_sales": avg_sales, "delta_pct": delta_pct}
            }
        elif yesterday_sales < avg_sales * 0.95:
            # DOWN_MILD
            abs_pct = abs(int(delta_pct))
            return {
                "status": "DOWN_MILD",
                "title": "📌 오늘의 한 줄 코칭",
                "coach_line": f"어제 매출이 최근 평균보다 약 {abs_pct}% 낮습니다.",
                "action_line": "추가 1개(사이드/주류/디저트) 제안을 전 테이블에 1회씩 하세요.",
                "cta": None,  # 홈 유지
                "debug": {"yesterday_sales": yesterday_sales, "avg_sales": avg_sales, "delta_pct": delta_pct}
            }
        elif yesterday_sales > avg_sales * 1.20:
            # UP_STRONG
            return {
                "status": "UP_STRONG",
                "title": "📌 오늘의 한 줄 코칭",
                "coach_line": f"어제 매출이 최근 평균보다 약 {int(delta_pct)}% 높습니다.",
                "action_line": "어제 잘 팔린 메뉴 1개를 '대표 자리'로 유지하세요.",
                "cta": None,  # 홈 유지
                "debug": {"yesterday_sales": yesterday_sales, "avg_sales": avg_sales, "delta_pct": delta_pct}
            }
        else:
            # STABLE
            abs_pct = abs(int(delta_pct))
            return {
                "status": "STABLE",
                "title": "📌 오늘의 한 줄 코칭",
                "coach_line": f"어제 매출은 최근 평균 근처입니다. (변동 {abs_pct}%)",
                "action_line": "오늘은 방문자 또는 메모 중 1개만 추가 입력해 정확도를 올리세요.",
                "cta": {
                    "label": "💰 오늘 데이터 입력하기",
                    "page": "일일 입력(통합)"
                },
                "debug": {"yesterday_sales": yesterday_sales, "avg_sales": avg_sales, "delta_pct": delta_pct}
            }
    
    except Exception as e:
        logger.error(f"build_minicoach_v1 실패: {e}", exc_info=True)
        return {
            "status": "NEED_SALES",
            "title": "📌 오늘의 한 줄 코칭",
            "coach_line": "코칭 데이터를 불러오는 중 오류가 발생했습니다.",
            "action_line": "오늘 매출을 입력해주세요.",
            "cta": {
                "label": "💰 오늘 매출 입력하기",
                "page": "일일 입력(통합)"
            },
            "debug": {"error": str(e)}
        }


def render_minicoach_card(coach: Dict) -> None:
    """
    미니 코칭 카드 렌더링
    
    Args:
        coach: build_minicoach_v1() 반환값
    """
    if not coach:
        return
    
    title = coach.get("title", "📌 오늘의 한 줄 코칭")
    coach_line = coach.get("coach_line", "")
    action_line = coach.get("action_line", "")
    cta = coach.get("cta")
    
    # 상태별 색상 (선택사항)
    status = coach.get("status", "")
    bg_color = "#667eea"  # 기본 보라색
    if status == "NEED_SALES":
        bg_color = "#f59e0b"  # 주황색
    elif status == "DOWN_STRONG":
        bg_color = "#ef4444"  # 빨간색
    elif status == "DOWN_MILD":
        bg_color = "#f97316"  # 주황색
    elif status == "UP_STRONG":
        bg_color = "#10b981"  # 초록색
    elif status == "STABLE":
        bg_color = "#3b82f6"  # 파란색
    
    # 카드 렌더링
    st.markdown(f"""
    <div style="padding: 1.5rem; background: linear-gradient(135deg, {bg_color} 0%, {bg_color}dd 100%); 
                border-radius: 12px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
                margin-bottom: 1.5rem;">
        <h3 style="color: white; margin: 0 0 0.8rem 0; font-size: 1.1rem; font-weight: 600;">{title}</h3>
        <p style="color: rgba(255,255,255,0.95); font-size: 1rem; font-weight: 600; margin: 0 0 0.5rem 0; line-height: 1.5;">
            {coach_line}
        </p>
        <p style="color: rgba(255,255,255,0.9); font-size: 0.95rem; margin: 0; line-height: 1.5;">
            {action_line}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # CTA 버튼
    if cta:
        cta_label = cta.get("label", "실행하기")
        cta_page = cta.get("page", "홈")
        
        if st.button(cta_label, type="primary", use_container_width=True, key=f"minicoach_cta_{status}_{cta_page}"):
            st.session_state["current_page"] = cta_page
            st.rerun()
