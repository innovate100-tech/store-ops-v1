"""
점장 마감 페이지
"""
from src.bootstrap import bootstrap
import streamlit as st
from src.ui_helpers import render_page_header, handle_data_error
from src.storage_supabase import load_csv, save_daily_close
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
    
    st.markdown("""
    <div class="info-box">
        <strong>⏱️ 목표:</strong> 하루 1번, 1분 안에 입력하고 끝내는 간단한 마감 입력 화면입니다.
    </div>
    """, unsafe_allow_html=True)
    
    # 전체 메뉴 로드
    menu_df = load_csv('menu_master.csv', default_columns=['메뉴명', '판매가'])
    menu_list = menu_df['메뉴명'].tolist() if not menu_df.empty else []
    
    # 점장 마감 입력 폼
    date, store, card_sales, cash_sales, total_sales, visitors, sales_items, issues, memo = render_manager_closing_input(menu_list)
    
    # STEP 3: 선택한 날짜에 판매량 보정(overrides) 존재 여부 확인
    from src.auth import get_current_store_id, get_supabase_client
    store_id = get_current_store_id()
    if store_id and date:
        try:
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
        if st.button("✅ 마감 완료", type="primary", use_container_width=True, key="manager_close_btn"):
            errors = []
            
            if not store or store.strip() == "":
                errors.append("매장명을 입력해주세요.")
            
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
                        st.success("✅ 마감이 완료되었습니다! 데이터가 저장되었습니다.")
                    else:
                        # DEV MODE 등에서 저장되지 않은 경우
                        st.warning("⚠️ DEV MODE: 마감 정보는 표시되지만 실제 데이터는 저장되지 않았습니다.")
                        st.info("💡 실제 저장을 원하시면 Supabase를 설정하고 DEV MODE를 비활성화하세요.")
                    
                    # 저장 성공 여부와 관계없이 풍선 애니메이션 및 마감 완료 메시지 표시
                    st.balloons()  # 항상 풍선 애니메이션 표시
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
                            <div style="font-size: 0.9rem; color: #7f8c8d; margin-bottom: 0.5rem;">방문자수</div>
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
