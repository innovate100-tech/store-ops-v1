# CSS 주입 지점 자동 수집 리포트

생성일: 2026-01-25 14:03:48

## st.markdown_style

### app.py

**패턴**: `st\.markdown\s*\([^)]*<style`

**매칭 라인**:

- 라인 821: `st.markdown("<style>.main { background-color: #020617 !important; color: #e5e7eb !important; }</styl...`



### ui_pages\home.py

**패턴**: `st\.markdown\s*\([^)]*style\s*[=:]`

**매칭 라인**:

- 라인 1457: `st.markdown(f'<div style="padding: 1rem; background: {mission1_bg}; border-radius: 8px; border-left:...`

- 라인 1460: `st.markdown(f"<div style='font-size: 1.5rem; text-align: center;'>{'✅' if mission1_complete else '⬜'...`

- 라인 1476: `st.markdown(f'<div style="padding: 1rem; background: {mission2_bg}; border-radius: 8px; border-left:...`

- 라인 1479: `st.markdown(f"<div style='font-size: 1.5rem; text-align: center;'>{'✅' if mission2_complete else '⬜'...`

- 라인 1500: `st.markdown(f'<div style="padding: 1rem; background: {mission3_bg}; border-radius: 8px; border-left:...`

- 라인 1503: `st.markdown(f"<div style='font-size: 1.5rem; text-align: center;'>{'✅' if mission3_complete else '⬜'...`



### ui_pages\home_legacy.py

**패턴**: `st\.markdown\s*\([^)]*style\s*[=:]`

**매칭 라인**:

- 라인 1476: `st.markdown(f'<div style="padding: 1rem; background: {mission1_bg}; border-radius: 8px; border-left:...`

- 라인 1479: `st.markdown(f"<div style='font-size: 1.5rem; text-align: center;'>{'✅' if mission1_complete else '⬜'...`

- 라인 1495: `st.markdown(f'<div style="padding: 1rem; background: {mission2_bg}; border-radius: 8px; border-left:...`

- 라인 1498: `st.markdown(f"<div style='font-size: 1.5rem; text-align: center;'>{'✅' if mission2_complete else '⬜'...`

- 라인 1519: `st.markdown(f'<div style="padding: 1rem; background: {mission3_bg}; border-radius: 8px; border-left:...`

- 라인 1522: `st.markdown(f"<div style='font-size: 1.5rem; text-align: center;'>{'✅' if mission3_complete else '⬜'...`



### ui_pages\ingredient_management.py

**패턴**: `st\.markdown\s*\([^)]*style\s*[=:]`

**매칭 라인**:

- 라인 830: `st.markdown("<hr style='margin: 0.5rem 0; border-color: rgba(255,255,255,0.2);'>", unsafe_allow_html...`

- 라인 981: `st.markdown("<hr style='margin: 0.5rem 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html...`



### ui_pages\recipe_management.py

**패턴**: `st\.markdown\s*\([^)]*style\s*[=:]`

**매칭 라인**:

- 라인 158: `st.markdown("<hr style='margin: 0.1rem 0; border-color: rgba(255,255,255,0.1); border-width: 0.5px;'...`

- 라인 233: `st.markdown(f"<div style='margin-top: 0.2rem; margin-bottom: 0.1rem; font-size: 0.85rem;'><strong>{u...`

- 라인 235: `st.markdown("<div style='margin-top: 0.2rem; margin-bottom: 0.1rem; font-size: 0.85rem;'>-</div>", u...`

- 라인 275: `st.markdown("<hr style='margin: 0.05rem 0; border-color: rgba(255,255,255,0.05); border-width: 0.5px...`

- 라인 524: `st.markdown("<hr style='margin: 0.3rem 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html...`

- 라인 538: `st.markdown(f"<div style='margin-top: 0.5rem;'><strong>{ing_name}</strong></div>", unsafe_allow_html...`

- 라인 540: `st.markdown(f"<div style='margin-top: 0.5rem;'>{unit}</div>", unsafe_allow_html=True)...`

- 라인 590: `st.markdown("<hr style='margin: 0.2rem 0; border-color: rgba(255,255,255,0.05);'>", unsafe_allow_htm...`



### ui_pages\settlement_actual.py

**패턴**: `st\.markdown\s*\([^)]*style\s*[=:]`

**매칭 라인**:

- 라인 1452: `st.markdown('<div style="margin: 0.5rem 0;"></div>', unsafe_allow_html=True)...`



### ui_pages\dashboard\sections.py

**패턴**: `st\.markdown\s*\([^)]*style\s*[=:]`

**매칭 라인**:

- 라인 87: `st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)...`

- 라인 134: `st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)...`

- 라인 241: `st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)...`

- 라인 299: `st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)...`

- 라인 357: `st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)...`

- 라인 387: `st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)...`

- 라인 525: `st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)...`

- 라인 600: `st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)...`

- 라인 720: `st.markdown('<div style="margin: 0.75rem 0;"></div>', unsafe_allow_html=True)...`



### ui_pages\design_lab\design_lab_frame.py

**패턴**: `st\.markdown\s*\([^)]*style\s*[=:]`

**매칭 라인**:

- 라인 62: `st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)...`

- 라인 76: `st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)...`

- 라인 112: `st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)...`

- 라인 161: `st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)...`

- 라인 176: `st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)...`



### ui_pages\health_check\health_check_page.py

**패턴**: `st\.markdown\s*\([^)]*style\s*[=:]`

**매칭 라인**:

- 라인 413: `st.markdown('<div style="margin: 1rem 0;"></div>', unsafe_allow_html=True)...`

- 라인 439: `st.markdown('<div style="margin: 1rem 0;"></div>', unsafe_allow_html=True)...`

- 라인 485: `st.markdown('<div style="margin: 0.5rem 0;"></div>', unsafe_allow_html=True)...`



### ui_pages\home\home_page.py

**패턴**: `st\.markdown\s*\([^)]*style\s*[=:]`

**매칭 라인**:

- 라인 489: `st.markdown("""<div style="padding: 1.5rem; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef ...`

- 라인 505: `st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)...`

- 라인 730: `st.markdown(f"""<div style="padding: 1rem; background: #fff5f5; border: 1px solid #fecaca; border-le...`

- 라인 744: `st.markdown(f"""<div style="padding: 0.8rem; background: #fff5f5; border: 1px solid #fecaca; border-...`

- 라인 761: `st.markdown(f"""<div style="padding: 1rem; background: #f0fdf4; border: 1px solid #bbf7d0; border-le...`

- 라인 774: `st.markdown(f"""<div style="padding: 0.8rem; background: #f0fdf4; border: 1px solid #bbf7d0; border-...`

- 라인 1063: `st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)...`

- 라인 1080: `st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)...`

- 라인 1086: `st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)...`

- 라인 1089: `st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)...`

- 라인 1143: `st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)...`

- 라인 1175: `st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)...`

- 라인 1317: `st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)...`

- 라인 1388: `st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)...`



### ui_pages\home\home_v3_zones.py

**패턴**: `st\.markdown\s*\([^)]*style\s*[=:]`

**매칭 라인**:

- 라인 171: `st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)...`

- 라인 326: `st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)...`

- 라인 371: `st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)...`

- 라인 425: `st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)...`

- 라인 470: `st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)...`

- 라인 525: `st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)...`



### ui_pages\input\ingredient_input.py

**패턴**: `st\.markdown\s*\([^)]*style\s*[=:]`

**매칭 라인**:

- 라인 661: `st.markdown(f'<span style="background: {color}; padding: 0.2rem 0.5rem; border-radius: 4px; color: w...`



### ui_pages\input\input_hub.py

**패턴**: `st\.markdown\s*\([^)]*style\s*[=:]`

**매칭 라인**:

- 라인 224: `if assets.get('missing_price', 0) > 0: st.markdown(f"<p class='animate-in delay-2' style='color: #F5...`

- 라인 225: `else: st.markdown("<p class='animate-in delay-2' style='color: #10B981; font-size: 0.8rem; margin: 0...`

- 라인 228: `if assets.get('missing_cost', 0) > 0: st.markdown(f"<p class='animate-in delay-3' style='color: #F59...`

- 라인 229: `else: st.markdown("<p class='animate-in delay-3' style='color: #10B981; font-size: 0.8rem; margin: 0...`

- 라인 232: `if assets.get('recipe_rate', 0) < 80: st.markdown("<p class='animate-in delay-4' style='color: #94A3...`

- 라인 233: `else: st.markdown("<p class='animate-in delay-4' style='color: #10B981; font-size: 0.8rem; margin: 0...`

- 라인 237: `if not assets.get('has_target'): st.markdown("<p class='animate-in delay-4' style='color: #F59E0B; f...`

- 라인 238: `else: st.markdown("<p class='animate-in delay-4' style='color: #10B981; font-size: 0.8rem; margin: 0...`



### ui_pages\input\inventory_input.py

**패턴**: `st\.markdown\s*\([^)]*style\s*[=:]`

**매칭 라인**:

- 라인 396: `st.markdown(f'<span style="background: {category_color}; padding: 0.2rem 0.5rem; border-radius: 4px;...`



### ui_pages\input\menu_input.py

**패턴**: `st\.markdown\s*\([^)]*style\s*[=:]`

**매칭 라인**:

- 라인 420: `st.markdown(f'<span style="background: {color}; padding: 0.2rem 0.5rem; border-radius: 4px; color: w...`

- 라인 427: `st.markdown(f'<span style="background: {role_color}; padding: 0.2rem 0.5rem; border-radius: 4px; col...`



### ui_pages\strategy\mission_detail.py

**패턴**: `st\.markdown\s*\([^)]*style\s*[=:]`

**매칭 라인**:

- 라인 206: `st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)...`



### src\ui\common_header.py

**패턴**: `st\.markdown\s*\([^)]*<style`

**매칭 라인**:

- 라인 240: `st.markdown(f"<style>{COMMON_HEADER_CSS}</style>", unsafe_allow_html=True)...`



## inject_function

### app.py

**패턴**: `def\s+inject.*css`

**매칭 라인**:

- 라인 88: `def inject_sidebar_premium_css():...`



### src\ui\components\form_kit.py

**패턴**: `def\s+inject.*css`

**매칭 라인**:

- 라인 78: `def inject_form_kit_css():...`



### src\ui\components\form_kit_v2.py

**패턴**: `def\s+inject.*css`

**매칭 라인**:

- 라인 371: `def inject_form_kit_v2_css(scope_id: Optional[str] = None):...`



## dangerous_properties

### app.py

**패턴**: `opacity\s*:\s*0`

**매칭 라인**:

- 라인 232: `opacity: 0;...`

- 라인 399: `from { opacity: 0; transform: translateY(20px); }...`

- 라인 421: `opacity: 0;...`



### app.py

**패턴**: `overflow\s*:\s*hidden`

**매칭 라인**:

- 라인 200: `overflow: hidden !important;...`



### app.py

**패턴**: `backdrop-filter`

**매칭 라인**:

- 라인 608: `backdrop-filter: blur(8px) !important;...`



### app.py

**패턴**: `transform\s*:`

**매칭 라인**:

- 라인 133: `text-transform: uppercase;...`

- 라인 251: `transform: scale(1.01) !important;...`

- 라인 399: `from { opacity: 0; transform: translateY(20px); }...`

- 라인 400: `to { opacity: 1; transform: translateY(0); }...`

- 라인 415: `0% { transform: translateX(-100%); }...`

- 라인 416: `100% { transform: translateX(100%); }...`

- 라인 461: `text-transform: none !important;...`

- 라인 593: `transform: scale(1.02) !important;...`



### app.py

**패턴**: `filter\s*:`

**매칭 라인**:

- 라인 594: `filter: brightness(1.1) !important;...`

- 라인 608: `backdrop-filter: blur(8px) !important;...`



### scripts\css_audit.py

**패턴**: `backdrop-filter`

**매칭 라인**:

- 라인 45: `r'backdrop-filter',...`



### src\storage_supabase.py

**패턴**: `filter\s*:`

**매칭 라인**:

- 라인 656: `if use_date_filter:...`

- 라인 663: `if use_date_filter:...`

- 라인 709: `if use_date_filter:...`



### src\ui.py

**패턴**: `opacity\s*:\s*0`

**매칭 라인**:

- 라인 1136: `<div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">💰 총매출</div>...`



### ui_pages\home.py

**패턴**: `opacity\s*:\s*0`

**매칭 라인**:

- 라인 1352: `<div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">이번 달 매출</div>...`

- 라인 1379: `<div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">마감률</div>...`

- 라인 1381: `<div style="font-size: 0.85rem; opacity: 0.9;">({closed_days}/{total_days}일)</div>...`

- 라인 1382: `{f'<div style="font-size: 0.9rem; margin-top: 0.5rem; opacity: 0.9;">🔥 연속 {streak_days}일</div>' if s...`

- 라인 1589: `<div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">오늘 매출</div>...`

- 라인 1606: `<div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">이번 달 매출</div>...`

- 라인 1649: `<div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">객단가</div>...`

- 라인 1676: `<div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">이번 달 이익</div>...`

- 라인 1943: `<div style="font-size: 0.85rem; opacity: 0.9; margin-bottom: 0.3rem;">고정비</div>...`

- 라인 1945: `<div style="font-size: 0.75rem; opacity: 0.8; margin-top: 0.2rem;">/월</div>...`

- 라인 1952: `<div style="font-size: 0.85rem; opacity: 0.9; margin-bottom: 0.3rem;">변동비율</div>...`

- 라인 1959: `<div style="font-size: 0.85rem; opacity: 0.9; margin-bottom: 0.3rem;">손익분기점 매출</div>...`



### ui_pages\home_legacy.py

**패턴**: `opacity\s*:\s*0`

**매칭 라인**:

- 라인 1371: `<div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">이번 달 매출</div>...`

- 라인 1398: `<div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">마감률</div>...`

- 라인 1400: `<div style="font-size: 0.85rem; opacity: 0.9;">({closed_days}/{total_days}일)</div>...`

- 라인 1401: `{f'<div style="font-size: 0.9rem; margin-top: 0.5rem; opacity: 0.9;">🔥 연속 {streak_days}일</div>' if s...`

- 라인 1608: `<div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">오늘 매출</div>...`

- 라인 1625: `<div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">이번 달 매출</div>...`

- 라인 1668: `<div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">객단가</div>...`

- 라인 1695: `<div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">이번 달 이익</div>...`

- 라인 1962: `<div style="font-size: 0.85rem; opacity: 0.9; margin-bottom: 0.3rem;">고정비</div>...`

- 라인 1964: `<div style="font-size: 0.75rem; opacity: 0.8; margin-top: 0.2rem;">/월</div>...`

- 라인 1971: `<div style="font-size: 0.85rem; opacity: 0.9; margin-bottom: 0.3rem;">변동비율</div>...`

- 라인 1978: `<div style="font-size: 0.85rem; opacity: 0.9; margin-bottom: 0.3rem;">손익분기점 매출</div>...`



### ui_pages\onboarding_mode_select.py

**패턴**: `opacity\s*:\s*0`

**매칭 라인**:

- 라인 43: `<div style="font-size: 0.95rem; opacity: 0.95; line-height: 1.6;">...`



### ui_pages\analysis\cost_analysis.py

**패턴**: `opacity\s*:\s*0`

**매칭 라인**:

- 라인 370: `<div style="font-size: 0.9rem; margin-bottom: 0.8rem; opacity: 0.9;">목표 매출</div>...`

- 라인 378: `<div style="font-size: 0.9rem; margin-bottom: 0.8rem; opacity: 0.9;">예상 순이익</div>...`

- 라인 380: `<div style="font-size: 0.85rem; margin-top: 0.5rem; opacity: 0.8;">{profit_rate:.1f}%</div>...`



### ui_pages\analysis\inventory_analysis.py

**패턴**: `filter\s*:`

**매칭 라인**:

- 라인 664: `if "전체" not in category_filter:...`

- 라인 667: `if "미지정" in category_filter:...`



### ui_pages\analysis\sales_drop_investigation.py

**패턴**: `opacity\s*:\s*0`

**매칭 라인**:

- 라인 150: `<p style="margin: 0; opacity: 0.9;">신뢰도: {confidence}%</p>...`



### ui_pages\dashboard\sections.py

**패턴**: `opacity\s*:\s*0`

**매칭 라인**:

- 라인 58: `<div style="font-size: 1.1rem; margin-bottom: 0.4rem; opacity: 0.9;">📊 손익분기 월매출</div>...`

- 라인 60: `<div style="font-size: 1.1rem; margin-top: 0.75rem; opacity: 0.9; border-top: 1px solid rgba(255,255...`

- 라인 71: `<div style="font-size: 1.1rem; margin-bottom: 0.4rem; opacity: 0.9;">🎯 목표 월매출</div>...`

- 라인 73: `<div style="font-size: 1.1rem; margin-top: 0.75rem; opacity: 0.9; border-top: 1px solid rgba(255,255...`

- 라인 103: `<div style="font-size: 1.1rem; margin-bottom: 0.3rem; opacity: 0.9; text-align: center;">📅 평일 일일 매출<...`

- 라인 105: `{f'<div style="font-size: 1.1rem; font-weight: 700;">일일목표매출: {int(weekday_daily_target):,}원</div>' i...`

- 라인 106: `<div style="font-size: 1rem; margin-top: 0.7rem; opacity: 0.9; border-top: 1px solid rgba(255,255,25...`

- 라인 110: `{f'<div style="font-size: 0.85rem; font-weight: 600; color: {weekday_profit_color};">목표시 영업이익: {int(...`

- 라인 111: `<div style="font-size: 0.7rem; margin-top: 0.4rem; opacity: 0.8; border-top: 1px solid rgba(255,255,...`

- 라인 120: `<div style="font-size: 1.1rem; margin-bottom: 0.3rem; opacity: 0.9; text-align: center;">🎉 주말 일일 매출<...`

- 라인 122: `{f'<div style="font-size: 1.1rem; font-weight: 700;">일일목표매출: {int(weekend_daily_target):,}원</div>' i...`

- 라인 123: `<div style="font-size: 1rem; margin-top: 0.7rem; opacity: 0.9; border-top: 1px solid rgba(255,255,25...`

- 라인 127: `{f'<div style="font-size: 0.85rem; font-weight: 600; color: {weekend_profit_color};">목표시 영업이익: {int(...`

- 라인 128: `<div style="font-size: 0.7rem; margin-top: 0.4rem; opacity: 0.8; border-top: 1px solid rgba(255,255,...`

- 라인 210: `<div style="font-size: 0.85rem; margin-bottom: 0.3rem; opacity: 0.9;">{label}</div>...`

- 라인 469: `<div style="font-size: 1rem; margin-bottom: 0.4rem; opacity: 0.9;">🟢 A등급</div>...`

- 라인 472: `<div style="font-size: 0.85rem; opacity: 0.8;">매출 비중: {a_ratio:.1f}%</div>...`

- 라인 481: `<div style="font-size: 1rem; margin-bottom: 0.4rem; opacity: 0.9;">🟡 B등급</div>...`

- 라인 484: `<div style="font-size: 0.85rem; opacity: 0.8;">매출 비중: {b_ratio:.1f}%</div>...`

- 라인 493: `<div style="font-size: 1rem; margin-bottom: 0.4rem; opacity: 0.9;">🔴 C등급</div>...`

- 라인 496: `<div style="font-size: 0.85rem; opacity: 0.8;">매출 비중: {c_ratio:.1f}%</div>...`

- 라인 670: `<div style="font-size: 0.85rem; margin-bottom: 0.4rem; opacity: 0.9;">판매가</div>...`

- 라인 677: `<div style="font-size: 0.85rem; margin-bottom: 0.4rem; opacity: 0.9;">원가</div>...`

- 라인 684: `<div style="font-size: 0.85rem; margin-bottom: 0.4rem; opacity: 0.9;">원가율</div>...`



### ui_pages\health_check\health_check_page.py

**패턴**: `filter\s*:`

**매칭 라인**:

- 라인 455: `if "전체" not in category_filter:...`



### ui_pages\home\home_components.py

**패턴**: `opacity\s*:\s*0`

**매칭 라인**:

- 라인 14: `<div style="font-size: 0.85rem; opacity: 0.9; margin-bottom: 0.3rem;">{label}</div>...`

- 라인 33: `<div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">{col1_label}</div>...`

- 라인 38: `sub = f"<div style='font-size: 0.85rem; opacity: 0.9;'>{col2_sub}</div>" if col2_sub else ""...`

- 라인 41: `<div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem;">{col2_label}</div>...`



### ui_pages\home\home_page.py

**패턴**: `opacity\s*:\s*0`

**매칭 라인**:

- 라인 948: `<div style="color: {text_color}; font-size: 0.875rem; opacity: 0.9; line-height: 1.4; font-weight: 4...`



### ui_pages\home\home_v3_zones.py

**패턴**: `opacity\s*:\s*0`

**매칭 라인**:

- 라인 138: `<div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.3rem;">💰 {kind_label}</div>...`

- 라인 140: `<div style="font-size: 0.8rem; opacity: 0.8; margin-top: 0.3rem;">신뢰도 {confidence*100:.0f}%</div>...`



### ui_pages\input\ingredient_input.py

**패턴**: `filter\s*:`

**매칭 라인**:

- 라인 573: `if "전체" not in category_filter:...`

- 라인 576: `if "미지정" in category_filter:...`



### ui_pages\input\input_hub.py

**패턴**: `opacity\s*:\s*0`

**매칭 라인**:

- 라인 162: `@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: ...`

- 라인 165: `@keyframes pulse-ring { 0% { transform: scale(0.9); opacity: 0.7; } 50% { transform: scale(1.1); opa...`



### ui_pages\input\input_hub.py

**패턴**: `overflow\s*:\s*hidden`

**매칭 라인**:

- 라인 115: `<div class="animate-in {delay_class}" style="padding: 1.5rem; background: {bg}; border-radius: 16px;...`

- 라인 177: `<div class="guide-card-animated" style="padding: 1.8rem; background: linear-gradient(135deg, #1E293B...`

- 라인 192: `<div style="background-color: rgba(255,255,255,0.05); border-radius: 20px; height: 12px; margin-bott...`

- 라인 193: `<div style="background: linear-gradient(90deg, #3B82F6 0%, #60A5FA 100%); width: {score}%; height: 1...`



### ui_pages\input\input_hub.py

**패턴**: `backdrop-filter`

**매칭 라인**:

- 라인 115: `<div class="animate-in {delay_class}" style="padding: 1.5rem; background: {bg}; border-radius: 16px;...`



### ui_pages\input\input_hub.py

**패턴**: `transform\s*:`

**매칭 라인**:

- 라인 162: `@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: ...`

- 라인 164: `@keyframes wave-move { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }...`

- 라인 165: `@keyframes pulse-ring { 0% { transform: scale(0.9); opacity: 0.7; } 50% { transform: scale(1.1); opa...`



### ui_pages\input\input_hub.py

**패턴**: `filter\s*:`

**매칭 라인**:

- 라인 115: `<div class="animate-in {delay_class}" style="padding: 1.5rem; background: {bg}; border-radius: 16px;...`



### ui_pages\input\inventory_input.py

**패턴**: `filter\s*:`

**매칭 라인**:

- 라인 199: `if "전체" not in category_filter:...`

- 라인 202: `if "미지정" in category_filter:...`



### ui_pages\input\menu_input.py

**패턴**: `filter\s*:`

**매칭 라인**:

- 라인 341: `if "전체" not in category_filter:...`

- 라인 344: `if "미지정" in category_filter:...`

- 라인 350: `if "전체" not in role_filter:...`

- 라인 353: `if "미분류" in role_filter:...`



### src\ui\common_header.py

**패턴**: `opacity\s*:\s*0`

**매칭 라인**:

- 라인 174: `50% { opacity: 0.85; }...`

- 라인 198: `0% { opacity: 0.5; }...`



### src\ui\common_header.py

**패턴**: `overflow\s*:\s*hidden`

**매칭 라인**:

- 라인 21: `overflow: hidden !important;...`

- 라인 105: `overflow: hidden !important;...`

- 라인 134: `overflow: hidden !important;...`



### src\ui\common_header.py

**패턴**: `transform\s*:`

**매칭 라인**:

- 라인 179: `transform: translateX(0);...`

- 라인 182: `transform: translateX(-50%);...`

- 라인 193: `0% { transform: rotate(0deg); }...`

- 라인 194: `100% { transform: rotate(360deg); }...`



### src\ui\common_header.py

**패턴**: `filter\s*:`

**매칭 라인**:

- 라인 81: `filter: none !important;...`

- 라인 169: `filter: none !important;...`



### src\ui\theme_manager.py

**패턴**: `filter\s*:`

**매칭 라인**:

- 라인 151: `attributeFilter: ['style', 'class']...`

- 라인 283: `filter: brightness(1.06) !important;...`

- 라인 329: `filter: brightness(1.06) !important;...`

- 라인 408: `filter: brightness(1.04) !important;...`



### src\ui\components\form_kit_v2.py

**패턴**: `opacity\s*:\s*0`

**매칭 라인**:

- 라인 113: `opacity: 0.5;...`

- 라인 209: `opacity: 0.5;...`



### src\ui\components\form_kit_v2.py

**패턴**: `display\s*:\s*none`

**매칭 라인**:

- 라인 156: `display: none;...`

- 라인 573: `display: none;...`

- 라인 759: `display: none;...`



### src\ui\components\form_kit_v2.py

**패턴**: `transform\s*:`

**매칭 라인**:

- 라인 138: `transform: translateY(-50%);...`

- 라인 557: `transform: translateY(-50%);...`

- 라인 743: `transform: translateY(-50%);...`



## animation_keywords

### app.py

**패턴**: `ultra|mesh|overlay|animation|background.*animation`

**매칭 라인**:

- 라인 91: `<style id="ps-ultra-sleek-css">...`

- 라인 93: `ULTRA SLEEK SIDEBAR v3...`

- 라인 97: `@keyframes ultra-neon-pulse {...`

- 라인 110: `@keyframes ultra-gradient-shift {...`

- 라인 121: `animation: none !important;...`

- 라인 127: `[data-testid="stSidebar"] .ultra-category {...`

- 라인 141: `animation: ultra-gradient-shift 4.5s ease infinite;...`

- 라인 147: `[data-testid="stSidebar"] .ultra-category {...`

- 라인 154: `[data-testid="stSidebar"] .ultra-category::before {...`

- 라인 163: `[data-testid="stSidebar"] .ultra-category::after {...`

- 라인 221: `/* hover sweep overlay via ::after */...`

- 라인 290: `animation: ultra-neon-pulse 3.6s ease-in-out infinite, ultra-gradient-shift 4.2s ease infinite !impo...`

- 라인 350: `[data-testid="stSidebar"] .ultra-system {...`

- 라인 357: `[data-testid="stSidebar"] .ultra-system::before {...`

- 라인 369: `[data-testid="stSidebar"] .ultra-system .stButton > button,...`

- 라인 370: `[data-testid="stSidebar"] .ultra-system button {...`

- 라인 420: `animation: fadeInUp 0.6s ease-out forwards;...`

- 라인 424: `.delay-1 { animation-delay: 0.1s; }...`

- 라인 425: `.delay-2 { animation-delay: 0.2s; }...`

- 라인 426: `.delay-3 { animation-delay: 0.3s; }...`

- 라인 427: `.delay-4 { animation-delay: 0.4s; }...`

- 라인 602: `animation: pulse-glow 3s infinite !important;...`

- 라인 885: `# 카테고리 제목 (ultra-category 클래스)...`

- 라인 887: `f'<div class="ultra-category">{cat}</div>',...`

- 라인 911: `# 시스템 버튼 (ultra-system wrapper)...`

- 라인 912: `st.markdown('<div class="ultra-system">', unsafe_allow_html=True)...`



### scripts\css_audit.py

**패턴**: `ultra|mesh|overlay|animation|background.*animation`

**매칭 라인**:

- 라인 54: `"fixed_overlay": [...`

- 라인 60: `"animation_keywords": [...`

- 라인 61: `r'ultra|mesh|overlay|animation|background.*animation',...`



### ui_pages\input\input_hub.py

**패턴**: `ultra|mesh|overlay|animation|background.*animation`

**매칭 라인**:

- 라인 167: `.guide-card-animated { animation: fadeInUp 0.8s ease-out forwards; }...`

- 라인 168: `.shimmer-overlay {...`

- 라인 171: `background-size: 400% 400%; animation: shimmer-bg 10s ease infinite;...`

- 라인 178: `<div class="shimmer-overlay"></div>...`

- 라인 194: `<div style="position: absolute; top: 0; left: 0; width: 200%; height: 100%; background: linear-gradi...`

- 라인 198: `<div style="width: 8px; height: 8px; border-radius: 50%; background: {status_color}; animation: puls...`



### src\ui\common_header.py

**패턴**: `ultra|mesh|overlay|animation|background.*animation`

**매칭 라인**:

- 라인 14: `animation: ps-gradientShift 8s ease infinite !important;...`

- 라인 33: `animation: ps-rotate 20s linear infinite !important;...`

- 라인 47: `animation: ps-sparkle 4s ease-in-out infinite alternate !important;...`

- 라인 146: `animation: ps-marquee-move 45.5s linear infinite !important;...`

- 라인 158: `animation: ps-ledBlink 1.5s ease-in-out infinite !important;...`



### src\utils\ui_scroll.py

**패턴**: `ultra|mesh|overlay|animation|background.*animation`

**매칭 라인**:

- 라인 20: `- requestAnimationFrame으로 DOM 타이밍 문제 방지...`

- 라인 26: `# requestAnimationFrame으로 한 프레임 뒤 실행하여 DOM 타이밍 문제 방지...`

- 라인 31: `requestAnimationFrame(() => {{...`



## stMain_selectors

### src\ui\theme_manager.py

**패턴**: `\[data-testid\s*=\s*["\']stAppViewContainer`

**매칭 라인**:

- 라인 218: `[data-testid="stAppViewContainer"] {{...`



## components_html

### src\utils\ui_scroll.py

**패턴**: `components\.html\s*\(`

**매칭 라인**:

- 라인 28: `components.html(...`


