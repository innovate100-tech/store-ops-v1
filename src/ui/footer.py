"""
CAUSE OS 전용 제품 푸터 컴포넌트
모든 페이지 하단에 표시되는 브랜드 시그니처
"""
import streamlit as st


def render_cause_os_footer(style="default"):
    """
    CAUSE OS 푸터 렌더링
    
    Args:
        style: "default" (기본형) 또는 "brand" (브랜드형)
    
    Note:
        - OS 명판 / 브랜드 시그니처 역할
        - 얇고 작은 폰트, 연한 톤
        - 페이지 맨 아래 마침표 역할
    """
    # CSS 주입 (1회만)
    if not st.session_state.get("_ps_footer_css_injected", False):
        css = """
        <style id="ps-footer-style">
        .ps-cause-footer {
            margin-top: 4rem;
            padding: 2.5rem 0 1.5rem 0;
            text-align: right !important;
            border-top: 1px solid rgba(148, 163, 184, 0.12);
            color: rgba(148, 163, 184, 0.65);
            font-size: 0.8rem;
            line-height: 1.7;
            font-weight: 400;
            letter-spacing: 0.02em;
            position: relative;
            display: block !important;
        }
        
        .ps-cause-footer::before {
            content: "";
            position: absolute;
            top: 0;
            right: 0;
            width: 60px;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(148, 163, 184, 0.3), transparent);
        }
        
        .ps-cause-footer > div,
        .ps-cause-footer div {
            text-align: right !important;
            display: block !important;
            width: 100% !important;
        }
        
        .ps-cause-footer > div:first-child {
            margin-bottom: 0.5rem;
        }
        
        .ps-cause-footer-brand,
        .ps-cause-footer-tagline,
        .ps-cause-footer-copyright,
        .ps-cause-footer-separator {
            text-align: right !important;
        }
        
        .ps-cause-footer-brand {
            font-weight: 700;
            color: rgba(148, 163, 184, 0.85);
            letter-spacing: 0.08em;
            font-size: 0.85rem;
        }
        
        .ps-cause-footer-tagline {
            color: rgba(148, 163, 184, 0.55);
            font-size: 0.75rem;
            font-weight: 400;
            letter-spacing: 0.01em;
        }
        
        .ps-cause-footer-copyright {
            color: rgba(148, 163, 184, 0.45);
            font-size: 0.7rem;
            margin-top: 0.75rem;
            font-weight: 300;
            letter-spacing: 0.03em;
        }
        
        .ps-cause-footer-separator {
            color: rgba(148, 163, 184, 0.35);
            margin: 0 0.6rem;
            font-weight: 300;
        }
        
        /* Streamlit 기본 스타일 오버라이드 - 모든 가능한 선택자 */
        [data-testid="stMarkdownContainer"] .ps-cause-footer,
        [data-testid="stMarkdownContainer"] .ps-cause-footer *,
        .stMarkdown .ps-cause-footer,
        .stMarkdown .ps-cause-footer *,
        .ps-cause-footer,
        .ps-cause-footer * {
            text-align: right !important;
            direction: rtl !important;
        }
        
        /* 방향을 다시 ltr로 (텍스트는 오른쪽 정렬) */
        .ps-cause-footer,
        .ps-cause-footer * {
            direction: ltr !important;
            text-align: right !important;
            margin-left: auto !important;
            margin-right: 0 !important;
        }
        
        /* 부모 컨테이너도 오른쪽 정렬 */
        [data-testid="stMarkdownContainer"]:has(.ps-cause-footer),
        .stMarkdown:has(.ps-cause-footer) {
            text-align: right !important;
        }
        
        /* 다크 모드 대응 */
        @media (prefers-color-scheme: dark) {
            .ps-cause-footer {
                border-top-color: rgba(148, 163, 184, 0.15);
            }
        }
        </style>
        <script>
        (function() {
            function forceFooterRightAlign() {
                var footers = document.querySelectorAll('.ps-cause-footer');
                footers.forEach(function(footer) {
                    footer.style.setProperty('text-align', 'right', 'important');
                    footer.style.setProperty('margin-left', 'auto', 'important');
                    footer.style.setProperty('margin-right', '0', 'important');
                    
                    var children = footer.querySelectorAll('*');
                    children.forEach(function(child) {
                        child.style.setProperty('text-align', 'right', 'important');
                    });
                });
            }
            
            // 즉시 실행
            forceFooterRightAlign();
            
            // DOM 로드 후 실행
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', forceFooterRightAlign);
            } else {
                setTimeout(forceFooterRightAlign, 100);
            }
            
            // MutationObserver로 새로 추가된 푸터 감지
            if (window.MutationObserver) {
                var observer = new MutationObserver(function() {
                    forceFooterRightAlign();
                });
                observer.observe(document.body, {
                    childList: true,
                    subtree: true
                });
            }
        })();
        </script>
        """
        st.markdown(css, unsafe_allow_html=True)
        st.session_state["_ps_footer_css_injected"] = True
    
    # 푸터 내용 렌더링
    if style == "brand":
        # 2안: 브랜드형
        st.markdown("""
        <div class="ps-cause-footer" style="text-align: right !important;">
            <div style="text-align: right !important;">
                <span class="ps-cause-footer-brand">CAUSE OS</span>
                <span class="ps-cause-footer-separator">·</span>
                <span class="ps-cause-footer-tagline">우리는 매출을 보지 않습니다. 원인을 봅니다.</span>
            </div>
            <div class="ps-cause-footer-copyright" style="text-align: right !important;">by INNOVATION100</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # 1안: 기본형
        st.markdown("""
        <div class="ps-cause-footer" style="text-align: right !important; margin-left: auto !important; margin-right: 0 !important; width: 100% !important; display: block !important;">
            <div style="text-align: right !important; margin-left: auto !important; margin-right: 0 !important; display: block !important;">
                <span class="ps-cause-footer-brand" style="text-align: right !important;">CAUSE OS</span>
                <span class="ps-cause-footer-separator">—</span>
                <span style="text-align: right !important;">성공에는 이유가 있습니다</span>
            </div>
            <div class="ps-cause-footer-copyright" style="text-align: right !important; margin-left: auto !important; margin-right: 0 !important; display: block !important;">© 2026 INNOVATION100. All rights reserved.</div>
        </div>
        """, unsafe_allow_html=True)
