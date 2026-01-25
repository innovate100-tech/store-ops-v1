"""
전역 UI 주입 베이스 - CSS 변수 및 최소 스타일 관리
"""
import streamlit as st
from src.ui.css_manager import inject_base, inject_theme


def inject_global_ui():
    """
    전역 UI 베이스를 주입합니다.
    prefers-color-scheme에 따라 자동으로 라이트/다크 모드 토큰을 전환합니다.
    최소한의 CSS 변수와 기본 스타일만 적용합니다.
    """
    # 1회 주입 가드 (css_manager 내부에서 처리)
    if st.session_state.get("_ps_global_ui_injected", False):
        return
    
    # AgGrid 다크 테마 JavaScript (전역 주입)
    aggrid_dark_js = """
    <script>
    (function() {
        var intervalId = null;
        
        function applyDarkTheme() {
            try {
                var allIframes = document.querySelectorAll('iframe');
                
                for (var i = 0; i < allIframes.length; i++) {
                    try {
                        var iframe = allIframes[i];
                        var iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                        
                        if (!iframeDoc || !iframeDoc.body) {
                            continue;
                        }
                        
                        // AgGrid 요소 확인
                        var allAgElements = iframeDoc.querySelectorAll('[class*="ag-"]');
                        if (allAgElements.length === 0) {
                            continue;
                        }
                        
                        // 1. iframe 자체 배경색
                        iframe.style.backgroundColor = '#0f1720';
                        
                        // 2. body 배경색
                        var body = iframeDoc.body;
                        body.style.setProperty('background-color', '#0f1720', 'important');
                        body.style.setProperty('color', '#e8eef7', 'important');
                        
                        // 3. 모든 ag- 요소에 스타일 적용
                        allAgElements.forEach(function(el) {
                            var className = String(el.className || '');
                            
                            if (className.includes('header')) {
                                el.style.setProperty('background-color', '#101823', 'important');
                                el.style.setProperty('color', '#e8eef7', 'important');
                            } else {
                                el.style.setProperty('background-color', '#0f1720', 'important');
                                el.style.setProperty('color', '#e8eef7', 'important');
                            }
                            
                            // 모든 자식 요소에도 텍스트 색상 강제 적용
                            var children = el.querySelectorAll('*');
                            children.forEach(function(child) {
                                child.style.setProperty('color', '#e8eef7', 'important');
                            });
                        });
                        
                        // 4. 모든 텍스트 요소에 색상 강제
                        var allTextElements = iframeDoc.querySelectorAll('div, span, p, td, th, label');
                        allTextElements.forEach(function(el) {
                            var computedStyle = window.getComputedStyle(el);
                            var textColor = computedStyle.color;
                            // 검은색이거나 어두운 색이면 밝은 색으로 변경
                            if (textColor && (textColor.includes('rgb(0,') || textColor.includes('rgb(16,') || textColor.includes('rgb(17,') || textColor === 'black' || textColor.includes('0, 0, 0') || textColor === 'transparent')) {
                                el.style.setProperty('color', '#e8eef7', 'important');
                            }
                        });
                        
                        // 5. CSS 변수 설정
                        var root = iframeDoc.documentElement;
                        root.style.setProperty('--ag-background-color', '#0f1720', 'important');
                        root.style.setProperty('--ag-foreground-color', '#e8eef7', 'important');
                        root.style.setProperty('--ag-header-background-color', '#101823', 'important');
                        root.style.setProperty('--ag-header-foreground-color', '#e8eef7', 'important');
                        
                        // 6. ag-theme 요소
                        var agThemes = iframeDoc.querySelectorAll('[class*="ag-theme"]');
                        agThemes.forEach(function(theme) {
                            theme.style.setProperty('background-color', '#0f1720', 'important');
                            theme.style.setProperty('color', '#e8eef7', 'important');
                        });
                        
                        // 7. 특정 클래스 직접 적용
                        var selectors = ['.ag-root-wrapper', '.ag-header', '.ag-header-cell', '.ag-row', '.ag-cell'];
                        selectors.forEach(function(selector) {
                            var elements = iframeDoc.querySelectorAll(selector);
                            elements.forEach(function(el) {
                                if (selector.includes('header')) {
                                    el.style.setProperty('background-color', '#101823', 'important');
                                    el.style.setProperty('color', '#e8eef7', 'important');
                                } else {
                                    el.style.setProperty('background-color', '#0f1720', 'important');
                                    el.style.setProperty('color', '#e8eef7', 'important');
                                }
                            });
                        });
                        
                    } catch (e) {
                        // 에러 무시
                    }
                }
            } catch (e) {
                // 에러 무시
            }
        }
        
        // 여러 시점에서 실행
        function startApplying() {
            setTimeout(applyDarkTheme, 1000);
            setTimeout(applyDarkTheme, 2000);
            setTimeout(applyDarkTheme, 3000);
            setTimeout(applyDarkTheme, 5000);
            setTimeout(applyDarkTheme, 8000);
            
            // 지속적으로 재적용
            intervalId = setInterval(function() {
                applyDarkTheme();
            }, 2000);
        }
        
        // DOMContentLoaded 또는 이미 로드된 경우
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', startApplying);
        } else {
            startApplying();
        }
        
        // window.load 이벤트도 대기
        window.addEventListener('load', function() {
            setTimeout(applyDarkTheme, 1000);
            setTimeout(applyDarkTheme, 3000);
        });
        
        // DOM 변경 감지
        if (window.MutationObserver) {
            var observer = new MutationObserver(function() {
                setTimeout(applyDarkTheme, 200);
            });
            observer.observe(document.body, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ['style', 'class']
            });
        }
        
        // iframe 로드 이벤트 직접 감지
        var checkIframes = setInterval(function() {
            var iframes = document.querySelectorAll('iframe');
            iframes.forEach(function(iframe) {
                if (iframe.onload) return;
                iframe.onload = function() {
                    setTimeout(applyDarkTheme, 500);
                    setTimeout(applyDarkTheme, 1500);
                };
            });
        }, 1000);
        
        setTimeout(function() {
            clearInterval(checkIframes);
        }, 10000);
        
        window.addEventListener('beforeunload', function() {
            if (intervalId) {
                clearInterval(intervalId);
            }
        });
    })();
    </script>
    """
    
    st.markdown(aggrid_dark_js, unsafe_allow_html=True)
    try:
        from src.debug.nav_trace import push_render_step
        push_render_step("CSS_INJECT: theme_manager.py:180 inject_global_ui (aggrid_dark_js)", extra={"where": "global"})
    except ImportError:
        pass
    
    # BASE 계층: CSS 변수
    base_css = f"""
    <style id="ps-ui-base">
        /* 라이트 모드 토큰 (기본) */
        :root {{
            --ps-bg: #f4f6f8;
            --ps-surface: #ffffff;
            --ps-surface-2: #eef2f6;
            --ps-text: #101417;
            --ps-muted: rgba(16,20,23,0.62);
            --ps-border: rgba(16,20,23,0.12);
            --ps-accent: #39ff14;
            --ps-accent-weak: rgba(57,255,20,0.20);
        }}
        
        /* 다크 모드 토큰 (prefers-color-scheme: dark) */
        @media (prefers-color-scheme: dark) {{
            :root {{
                --ps-bg: #0b0f14;
                --ps-surface: #101823;
                --ps-surface-2: #0f1720;
                --ps-text: #e8eef7;
                --ps-muted: rgba(232,238,247,0.62);
                --ps-border: rgba(232,238,247,0.12);
                --ps-accent: #39ff14;
                --ps-accent-weak: rgba(57,255,20,0.25);
                /* 입력 위젯 토큰 */
                --ps-input-bg: #0f1720;
                --ps-input-border: rgba(0,0,0,0.65);
                --ps-input-border-soft: rgba(255,255,255,0.06);
                --ps-input-text: var(--ps-text);
                --ps-input-placeholder: var(--ps-muted);
            }}
        }}
    </style>
    """
    inject_base(base_css, "global_ui_vars")
    
    # THEME 계층: 기본 스타일
    theme_css = f"""
    <style>
        /* 최소 적용 규칙 (안전 범위만) */
        .stApp,
        [data-testid="stAppViewContainer"] {{
            background: var(--ps-bg);
            color: var(--ps-text);
        }}
        
        /* 좌측 패널 전체 배경 (회색 뒤판 제거 핵심) */
        /* Streamlit의 실제 좌측 컬럼 컨테이너를 타겟팅 */
        [data-testid="stSidebar"] {{
            background: var(--ps-surface) !important;
            color: var(--ps-text) !important;
            border-right: 1px solid var(--ps-border);
        }}
        
        /* ps-leftpanel은 내부 구조용으로 유지 */
        .ps-leftpanel {{
            /* 배경은 상위 [data-testid="stSidebar"]에서 처리 */
        }}
        
        /* 커스텀 사이드바 베이스 (투명 배경, 텍스트/버튼만 토큰 적용) */
        .ps-sidebar {{
            background: transparent !important;
            color: var(--ps-text) !important;
        }}
        
        /* 사이드바 제목 및 항목 */
        .ps-sidebar h1,
        .ps-sidebar h2,
        .ps-sidebar h3,
        .ps-sidebar p,
        .ps-sidebar span,
        .ps-sidebar label {{
            color: var(--ps-text);
        }}
        
        /* 사이드바 작은 글자 */
        .ps-sidebar small,
        .ps-sidebar .muted {{
            color: var(--ps-muted);
        }}
        
        /***** PS SIDEBAR BUTTONS (FORCE BASE BG) *****/
        
        /* 2-1) 버튼을 담는 흔한 wrapper들까지 배경을 강제로 어둡게 */
        .ps-sidebar .element-container,
        .ps-sidebar .stButton,
        .ps-sidebar .stButton > div,
        .ps-sidebar .stButton > div > div,
        .ps-sidebar .stButton > div > div > div {{
            background: var(--ps-surface) !important;
        }}
        
        /* 2-2) 실제 클릭 요소(button/role=button)도 동일 톤으로 통일 */
        .ps-sidebar .stButton > button,
        .ps-sidebar button,
        .ps-sidebar [role="button"] {{
            background: var(--ps-surface) !important;
            color: var(--ps-text) !important;
            border: 1px solid var(--ps-border) !important;
        }}
        
        /* 2-3) hover는 배경 바꾸지 말고 "눌림/반응"만 */
        .ps-sidebar .stButton > button:hover,
        .ps-sidebar button:hover,
        .ps-sidebar [role="button"]:hover {{
            background: var(--ps-surface) !important;
            filter: brightness(1.06) !important;
            box-shadow: 0 0 0 1px var(--ps-accent-weak) inset !important;
        }}
        
        /* 2-4) 선택(클릭) 상태 유지: 기존 파란색 룰이 있으면 그것을 우선, 없으면 아래로 보장 */
        .ps-sidebar .stButton > button[aria-pressed="true"],
        .ps-sidebar button[aria-pressed="true"],
        .ps-sidebar [role="button"][aria-pressed="true"] {{
            background: #1f77b4 !important;
            color: #ffffff !important;
            border-color: var(--ps-accent-weak) !important;
        }}
        
        /* 2-5) 아이콘 색 */
        .ps-sidebar svg {{
            color: var(--ps-text) !important;
        }}
        
        /***** END PS SIDEBAR BUTTONS *****/
        
        /* 페이지 안 작은 글자 토큰 연결 (안전 범위) */
        .stApp small,
        .stApp .stCaption {{
            color: var(--ps-muted);
        }}
        
        .stApp label {{
            color: var(--ps-text);
        }}
        
        /* ===== FINAL: SIDEBAR BUTTON THEME ===== */
        [data-testid="stSidebar"] button,
        [data-testid="stSidebar"] [role="button"],
        [data-testid="stSidebar"] div[role="button"],
        [data-testid="stSidebar"] a {{
            background: var(--ps-surface) !important;
            color: var(--ps-text) !important;
            border: 1px solid var(--ps-border) !important;
        }}
        
        /* hover: 배경 유지 + 눌림 느낌 */
        [data-testid="stSidebar"] button:hover,
        [data-testid="stSidebar"] [role="button"]:hover,
        [data-testid="stSidebar"] div[role="button"]:hover,
        [data-testid="stSidebar"] a:hover {{
            background: var(--ps-surface) !important;
            filter: brightness(1.06) !important;
            box-shadow: 0 0 0 1px var(--ps-accent-weak) inset !important;
        }}
        
        /* selected: 파란색 유지 (aria-pressed / aria-current 둘 다 커버) */
        [data-testid="stSidebar"] button[aria-pressed="true"],
        [data-testid="stSidebar"] [role="button"][aria-pressed="true"],
        [data-testid="stSidebar"] div[role="button"][aria-pressed="true"],
        [data-testid="stSidebar"] a[aria-current="page"] {{
            background: #1f77b4 !important;
            color: #ffffff !important;
            border-color: var(--ps-accent-weak) !important;
        }}
        /* ===== END FINAL ===== */
        
        /* --- remove Streamlit top header bar line --- */
        header[data-testid="stHeader"] {{
            background: transparent !important;
            border-bottom: 0 !important;
            box-shadow: none !important;
        }}
        
        /* sometimes the app toolbar container draws a line */
        div[data-testid="stToolbar"] {{
            background: transparent !important;
            border: 0 !important;
            box-shadow: none !important;
        }}
        
        /* optional: remove top padding gap if any (NO layout risky props) */
        section.main > div {{
            padding-top: 0rem !important;
        }}
        
        /* 다크 모드 입력 위젯 스타일 */
        @media (prefers-color-scheme: dark) {{
            /* checkbox label text */
            [data-testid="stCheckbox"] * {{
                color: var(--ps-text) !important;
            }}
            /* hint/caption tone (너무 쨍하면 muted로) */
            [data-testid="stCheckbox"] small,
            [data-testid="stCheckbox"] .stCaption {{
                color: var(--ps-muted) !important;
            }}
            
            /* text/number/date/time inputs */
            [data-testid="stTextInput"] input,
            [data-testid="stNumberInput"] input,
            [data-testid="stDateInput"] input,
            [data-testid="stTimeInput"] input,
            [data-testid="stTextArea"] textarea {{
                background: var(--ps-input-bg) !important;
                color: var(--ps-text) !important;
                border: 1px solid var(--ps-input-border) !important;
                box-shadow:
                    0 1px 0 var(--ps-input-border-soft) inset,
                    0 -1px 0 rgba(0,0,0,0.75) inset !important;
            }}
            
            /* selectboxes often render as divs */
            [data-testid="stSelectbox"] div[role="button"],
            [data-testid="stMultiSelect"] div[role="button"] {{
                background: var(--ps-input-bg) !important;
                color: var(--ps-text) !important;
                border: 1px solid var(--ps-input-border) !important;
                box-shadow:
                    0 1px 0 var(--ps-input-border-soft) inset,
                    0 -1px 0 rgba(0,0,0,0.75) inset !important;
            }}
            
            /* hover: 살짝만 */
            [data-testid="stTextInput"] input:hover,
            [data-testid="stNumberInput"] input:hover,
            [data-testid="stDateInput"] input:hover,
            [data-testid="stTimeInput"] input:hover,
            [data-testid="stTextArea"] textarea:hover,
            [data-testid="stSelectbox"] div[role="button"]:hover,
            [data-testid="stMultiSelect"] div[role="button"]:hover {{
                filter: brightness(1.04) !important;
            }}
            
            /* placeholder */
            [data-testid="stTextInput"] input::placeholder,
            [data-testid="stNumberInput"] input::placeholder,
            [data-testid="stTextArea"] textarea::placeholder {{
                color: var(--ps-input-placeholder) !important;
            }}
            
            /* focus: accent inset만 추가 */
            [data-testid="stTextInput"] input:focus,
            [data-testid="stNumberInput"] input:focus,
            [data-testid="stDateInput"] input:focus,
            [data-testid="stTimeInput"] input:focus,
            [data-testid="stTextArea"] textarea:focus,
            [data-testid="stSelectbox"] div[role="button"]:focus,
            [data-testid="stMultiSelect"] div[role="button"]:focus {{
                outline: none !important;
                box-shadow:
                    0 1px 0 var(--ps-input-border-soft) inset,
                    0 -1px 0 rgba(0,0,0,0.75) inset,
                    0 0 0 1px var(--ps-accent-weak) inset !important;
            }}
            
            /* st.metric 계열 색 고정 */
            [data-testid="stMetric"] * {{
                color: var(--ps-text) !important;
            }}
            [data-testid="stMetric"] [data-testid="stMetricDelta"] * {{
                color: inherit !important;
            }}
            
            /* markdown 숫자 (h1/h2/h3/strong만 안전하게) */
            [data-testid="stMarkdownContainer"] strong,
            [data-testid="stMarkdownContainer"] h1,
            [data-testid="stMarkdownContainer"] h2,
            [data-testid="stMarkdownContainer"] h3 {{
                color: var(--ps-text) !important;
            }}
        }}
        
        /* ============================================
           메인 콘텐츠 영역 상단 여백 축소
           ============================================ */
        
        /* Reduce excessive top spacing in main content */
        [data-testid="stMainBlockContainer"] {{
            padding-top: 0.75rem !important;  /* 기본보다 줄임 */
        }}
        
        [data-testid="stAppViewContainer"] .main {{
            padding-top: 0.75rem !important;
        }}
        
        /* 어떤 경우 margin이 원인일 수도 있으니 방어적으로 */
        [data-testid="stMainBlockContainer"] > div:first-child {{
            margin-top: 0 !important;
        }}
    </style>
    """
    inject_theme(theme_css, "global_ui_theme")
    
    st.session_state["_ps_global_ui_injected"] = True
    
