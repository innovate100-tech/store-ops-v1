"""
점장 마감 페이지
"""
from src.bootstrap import bootstrap
import streamlit as st
from src.ui_helpers import render_page_header, handle_data_error
from src.storage_supabase import load_csv, save_daily_close, get_day_record_status
from src.ui import render_manager_closing_input

# 공통 설정 적용
bootstrap(page_title="Manager Close")

# 로그인 체크
from src.auth import check_login, show_login_page
if not check_login():
    show_login_page()
    st.stop()


def render_manager_close():
    """점장 마감 페이지 렌더링"""
    render_page_header("점장 마감", "📋")
    
    # STEP 1: 공식 입력 안내 박스
    st.markdown("""
    <div style="padding: 1.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                border-radius: 12px; color: white; margin-bottom: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-size: 1.5rem; margin-right: 0.5rem;">📘</span>
            <h3 style="color: white; margin: 0; font-size: 1.2rem; font-weight: 600;">점장마감은 이 날짜의 공식 기록입니다</h3>
        </div>
        <div style="font-size: 0.95rem; line-height: 1.6; color: #f0f0f0; margin-top: 0.5rem;">
            매출·판매량·방문자 기준으로 이 날짜의 공식 입력 루트입니다.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Phase 1 STEP 2 최종: 저장/분석 정책 안내
    st.info("""
    💡 **네이버 방문자·메모·판매량만 입력해도 기록은 저장됩니다.**  
    하지만 분석과 코칭은 **'매출'**이 있어야 시작됩니다.
    """)
    
    # 전체 메뉴 로드
    menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
    menu_list = menu_df['메뉴명'].tolist() if not menu_df.empty else []
    
    # query params 또는 session_state에서 날짜 가져오기
    from src.auth import get_current_store_id, get_supabase_client
    from datetime import date as date_type
    import urllib.parse
    
    # query params 확인
    query_params = st.query_params
    initial_date = None
    if "date" in query_params:
        try:
            initial_date = date_type.fromisoformat(query_params["date"])
        except:
            pass
    
    # session_state에서 날짜 확인 (매출보정에서 승격 버튼 클릭 시)
    if initial_date is None and "manager_close_date" in st.session_state:
        initial_date = st.session_state["manager_close_date"]
        del st.session_state["manager_close_date"]  # 사용 후 삭제
    
    # 점장 마감 입력 폼 (초기 날짜 전달)
    date, store, card_sales, cash_sales, total_sales, visitors, sales_items, issues, memo = render_manager_closing_input(menu_list, initial_date=initial_date)
    
    # 날짜 상태 확인
    store_id = get_current_store_id()
    status = None
    has_daily_close = False
    if store_id and date:
        try:
            status = get_day_record_status(store_id, date)
            has_daily_close = status["has_close"]
            
            # daily_close 없고 sales/naver_visitors 있으면 승격 안내
            if not has_daily_close and (status["has_sales"] or status["has_visitors"]):
                st.markdown("""
                <div style="padding: 1.2rem; background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); 
                            border-radius: 12px; margin-bottom: 1.5rem; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                        <span style="font-size: 1.5rem; margin-right: 0.5rem;">📋</span>
                        <h3 style="color: white; margin: 0; font-size: 1.1rem; font-weight: 600;">임시 매출/네이버 방문자 승격</h3>
                    </div>
                    <div style="font-size: 0.95rem; line-height: 1.6; color: #fffbeb; margin-top: 0.5rem;">
                        임시 매출/네이버 방문자가 있습니다. 이 값을 공식 마감으로 확정합니다.
                    </div>
                </div>
                """, unsafe_allow_html=True)
            elif has_daily_close:
                st.info("ℹ️ **이미 마감된 날짜입니다.** 수정 시 기존 마감 기록이 갱신됩니다.")
            
            # 판매량 보정(overrides) 존재 여부 확인
            supabase = get_supabase_client()
            if supabase:
                date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
                overrides_check = supabase.table("daily_sales_items_overrides")\
                    .select("menu_id", count="exact")\
                    .eq("store_id", store_id)\
                    .eq("sale_date", date_str)\
                    .limit(1)\
                    .execute()
                
                if overrides_check.count and overrides_check.count > 0:
                    st.warning(f"⚠️ **이 날짜에는 판매량 보정이 존재하며, 보정값이 최종 적용됩니다.** (보정 항목: {overrides_check.count}개)")
        except Exception as e:
            # 에러 발생 시 무시 (UI 경고이므로)
            pass
    
    st.markdown("---")
    
    # 마감 완료 버튼
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        button_label = "✅ 마감 완료" if not has_daily_close else "✅ 마감 수정 저장"
        if st.button(button_label, type="primary", use_container_width=True, key="manager_close_btn"):
            # Phase 1 STEP 2: 입력 유효성 체크
            from src.ui_helpers import has_any_input, ui_flash_warning, ui_flash_success
            
            errors = []
            
            if not store or store.strip() == "":
                errors.append("매장명을 입력해주세요.")
            
            # 입력 유효성 판정
            if not has_any_input(
                card_sales=card_sales,
                cash_sales=cash_sales,
                total_sales=total_sales,
                visitors=visitors,
                sales_items=sales_items,
                memo=memo,
                issues=issues
            ):
                ui_flash_warning("아무것도 입력되지 않았습니다. 하나만 입력해도 저장됩니다.")
                return
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                try:
                    # daily_close에 저장
                    result = save_daily_close(
                        date, store, card_sales, cash_sales, total_sales,
                        visitors, sales_items, issues, memo
                    )
                    
                    # 저장 결과에 따라 메시지 표시
                    if result:
                        # Phase 1 STEP 2 최종: 저장 후 메시지 분기 (매출 있음/없음)
                        from src.ui_helpers import has_sales_input
                        
                        has_sales = has_sales_input(card_sales, cash_sales, total_sales)
                        
                        if has_sales:
                            # 매출이 있으면 분석 시작 안내
                            saved_items = []
                            if has_sales:
                                saved_items.append("매출")
                            if visitors > 0:
                                saved_items.append("네이버 방문자")
                            if sales_items and any(qty > 0 for _, qty in sales_items):
                                saved_items.append("판매량")
                            if memo and memo.strip():
                                saved_items.append("메모")
                            if issues and any(issues.values()):
                                saved_items.append("이슈")
                            
                            if has_daily_close:
                                if len(saved_items) > 1:
                                    ui_flash_success(f"저장 완료! 매출이 입력되어 분석이 시작됩니다. ({', '.join(saved_items)}) - 기존 마감 기록이 갱신되었습니다.")
                                else:
                                    ui_flash_success("저장 완료! 매출이 입력되어 분석이 시작됩니다. (기존 마감 기록이 갱신되었습니다.)")
                            else:
                                if len(saved_items) > 1:
                                    ui_flash_success(f"저장 완료! 매출이 입력되어 분석이 시작됩니다. ({', '.join(saved_items)})")
                                else:
                                    ui_flash_success("저장 완료! 매출이 입력되어 분석이 시작됩니다.")
                        else:
                            # 매출이 없으면 기록만 저장 안내 + 다음 행동 유도
                            saved_items = []
                            if visitors > 0:
                                saved_items.append("네이버 방문자")
                            if sales_items and any(qty > 0 for _, qty in sales_items):
                                saved_items.append("판매량")
                            if memo and memo.strip():
                                saved_items.append("메모")
                            if issues and any(issues.values()):
                                saved_items.append("이슈")
                            
                            if saved_items:
                                ui_flash_warning(f"기록은 저장되었습니다 ({', '.join(saved_items)}). 분석을 시작하려면 오늘 매출을 입력해 주세요.")
                            else:
                                ui_flash_warning("기록은 저장되었습니다. 분석을 시작하려면 오늘 매출을 입력해 주세요.")
                            
                            # 매출 입력하러 가기 버튼 표시
                            if st.button("💰 오늘 매출 입력하러 가기", type="primary", use_container_width=True, key="go_to_sales_input_manager"):
                                st.session_state["current_page"] = "일일 입력(통합)"
                                st.rerun()
                    else:
                        # DEV MODE 등에서 저장되지 않은 경우
                        st.warning("⚠️ DEV MODE: 마감 정보는 표시되지만 실제 데이터는 저장되지 않았습니다.")
                        st.info("💡 실제 저장을 원하시면 Supabase를 설정하고 DEV MODE를 비활성화하세요.")
                    
                    # 저장 성공 여부와 관계없이 풍선 애니메이션 및 마감 완료 메시지 표시
                    st.balloons()  # 항상 풍선 애니메이션 표시
                    
                    # 마감 완료 요약 카드
                    st.markdown("---")
                    st.markdown("### ✅ 마감 완료")
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.success(f"📅 **날짜**: {date}")
                        st.success(f"💰 **총매출**: {total_sales:,}원")
                        st.success(f"👥 **네이버 방문자**: {visitors}명")
                    with col2:
                        if st.button("🛠 매출보정으로 돌아가기", use_container_width=True, key="back_to_sales_entry"):
                            st.session_state["current_page"] = "매출 보정"
                            st.rerun()
                    
                    st.info("💡 **마감 수정 방법**: 같은 날짜로 다시 마감을 입력하시면 기존 데이터가 자동으로 업데이트됩니다.")
                    
                    # 오늘 요약 카드 표시 (rerun 없이 현재 세션에서만 표시)
                    st.markdown("---")
                    st.markdown("### 📊 오늘 요약")
                    
                    # 객단가 계산
                    avg_price = (total_sales / visitors) if visitors > 0 else 0
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div style="font-size: 0.9rem; color: #7f8c8d; margin-bottom: 0.5rem;">총매출</div>
                            <div style="font-size: 1.8rem; font-weight: 700; color: #28a745;">{total_sales:,}원</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div style="font-size: 0.9rem; color: #7f8c8d; margin-bottom: 0.5rem;">네이버 방문자</div>
                            <div style="font-size: 1.8rem; font-weight: 700; color: #17a2b8;">{visitors}명</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div style="font-size: 0.9rem; color: #7f8c8d; margin-bottom: 0.5rem;">객단가</div>
                            <div style="font-size: 1.8rem; font-weight: 700; color: #ffc107;">{avg_price:,.0f}원</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col4:
                        menu_count = len([q for _, q in sales_items if q > 0])
                        st.markdown(f"""
                        <div class="metric-card">
                            <div style="font-size: 0.9rem; color: #7f8c8d; margin-bottom: 0.5rem;">판매 메뉴 수</div>
                            <div style="font-size: 1.8rem; font-weight: 700; color: #667eea;">{menu_count}개</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # 판매량 TOP 3
                    if sales_items:
                        st.markdown("---")
                        st.markdown("### 🔝 판매량 TOP 3")
                        
                        sorted_items = sorted([(m, q) for m, q in sales_items if q > 0], key=lambda x: x[1], reverse=True)
                        top3_items = sorted_items[:3]
                        
                        if top3_items:
                            top3_cols = st.columns(len(top3_items))
                            for idx, (menu_name, quantity) in enumerate(top3_items):
                                with top3_cols[idx]:
                                    st.markdown(f"""
                                    <div class="metric-card">
                                        <div style="font-size: 0.9rem; color: #7f8c8d; margin-bottom: 0.5rem;">{menu_name}</div>
                                        <div style="font-size: 1.5rem; font-weight: 700; color: #667eea;">{quantity}개</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                    
                except Exception as e:
                    error_msg = handle_data_error("마감 저장", e)
                    st.error(error_msg)
                    with st.expander("🔍 오류 상세 (복구/문의용)"):
                        st.code(str(e), language=None)
                        st.caption("위 내용을 복사해 관리자에게 전달하시면 원인 파악에 도움이 됩니다.")
                        st.caption("💡 Supabase SQL Editor에서 save_daily_close_transaction 함수가 생성되어 있는지 확인하세요. (sql/save_daily_close_transaction.sql)")


# Streamlit 멀티페이지에서 직접 실행될 때
# 주석 처리: app.py에서만 렌더되도록 함 (중복 호출 방지)
# render_manager_close()
