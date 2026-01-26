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
        - CSS는 theme_manager.py의 전역 CSS에 포함되어 모든 페이지에서 자동 적용됨
    """
    # JavaScript 주입 (모든 페이지에서 실행되도록 매번 주입)
    # CSS는 theme_manager.py의 전역 CSS에 포함되어 있으므로 여기서는 JavaScript만 주입
    footer_js = """
    <script>
    (function() {
        function forceFooterRightAlign() {
            var wrappers = document.querySelectorAll('.ps-cause-footer-wrapper');
            wrappers.forEach(function(wrapper) {
                // 푸터 자체
                wrapper.style.setProperty('text-align', 'right', 'important');
                wrapper.style.setProperty('direction', 'ltr', 'important');
                wrapper.style.setProperty('width', '100%', 'important');
                wrapper.style.setProperty('display', 'block', 'important');
                
                // 모든 자식 요소
                var allChildren = wrapper.querySelectorAll('*');
                allChildren.forEach(function(child) {
                    child.style.setProperty('text-align', 'right', 'important');
                    child.style.setProperty('direction', 'ltr', 'important');
                });
                
                // 모든 부모 요소를 찾아서 오른쪽 정렬 강제
                var parent = wrapper.parentElement;
                var depth = 0;
                while (parent && depth < 10) { // 최대 10단계까지
                    parent.style.setProperty('text-align', 'right', 'important');
                    parent.style.setProperty('direction', 'ltr', 'important');
                    
                    // Streamlit 마크다운 컨테이너인 경우 특별 처리
                    if (parent.hasAttribute && parent.hasAttribute('data-testid')) {
                        var testid = parent.getAttribute('data-testid');
                        if (testid === 'stMarkdownContainer' || testid.includes('Markdown')) {
                            parent.style.setProperty('text-align', 'right', 'important');
                            parent.style.setProperty('direction', 'ltr', 'important');
                            parent.style.setProperty('display', 'block', 'important');
                        }
                    }
                    
                    // 클래스명으로도 확인
                    if (parent.classList && parent.classList.contains('stMarkdown')) {
                        parent.style.setProperty('text-align', 'right', 'important');
                        parent.style.setProperty('direction', 'ltr', 'important');
                    }
                    
                    parent = parent.parentElement;
                    depth++;
                }
            });
        }
        
        // 즉시 실행
        forceFooterRightAlign();
        
        // DOM 로드 후 실행
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                forceFooterRightAlign();
                setTimeout(forceFooterRightAlign, 50);
                setTimeout(forceFooterRightAlign, 200);
                setTimeout(forceFooterRightAlign, 500);
            });
        } else {
            setTimeout(forceFooterRightAlign, 50);
            setTimeout(forceFooterRightAlign, 200);
            setTimeout(forceFooterRightAlign, 500);
        }
        
        // load 이벤트
        window.addEventListener('load', function() {
            setTimeout(forceFooterRightAlign, 100);
            setTimeout(forceFooterRightAlign, 500);
        });
        
        // MutationObserver로 새로 추가된 푸터 감지
        if (window.MutationObserver) {
            var observer = new MutationObserver(function(mutations) {
                var hasFooter = false;
                mutations.forEach(function(mutation) {
                    if (mutation.addedNodes) {
                        mutation.addedNodes.forEach(function(node) {
                            if (node.nodeType === 1) {
                                if (node.classList && (node.classList.contains('ps-cause-footer-wrapper') || node.classList.contains('ps-cause-footer'))) {
                                    hasFooter = true;
                                } else if (node.querySelector && node.querySelector('.ps-cause-footer-wrapper, .ps-cause-footer')) {
                                    hasFooter = true;
                                }
                            }
                        });
                    }
                });
                if (hasFooter) {
                    setTimeout(forceFooterRightAlign, 10);
                    setTimeout(forceFooterRightAlign, 100);
                }
            });
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }
        
        // 주기적 확인 (더 자주)
        setInterval(forceFooterRightAlign, 1000);
    })();
    </script>
    """
    st.markdown(footer_js, unsafe_allow_html=True)
    
    # 푸터 내용 렌더링 - 인라인 스타일로 강제
    if style == "brand":
        # 2안: 브랜드형
        st.markdown("""
        <div class="ps-cause-footer-wrapper" style="text-align: right !important; direction: ltr !important; width: 100% !important; display: block !important;">
            <div class="ps-cause-footer" style="text-align: right !important; direction: ltr !important; width: 100% !important; display: block !important;">
                <div style="text-align: right !important; direction: ltr !important; display: block !important;">
                    <span class="ps-cause-footer-brand" style="text-align: right !important;">CAUSE OS</span>
                    <span class="ps-cause-footer-separator">·</span>
                    <span class="ps-cause-footer-tagline" style="text-align: right !important;">우리는 매출을 보지 않습니다. 원인을 봅니다.</span>
                </div>
                <div class="ps-cause-footer-copyright" style="text-align: right !important; direction: ltr !important; display: block !important;">by INNOVATION100</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # 1안: 기본형
        st.markdown("""
        <div class="ps-cause-footer-wrapper" style="text-align: right !important; direction: ltr !important; width: 100% !important; display: block !important;">
            <div class="ps-cause-footer" style="text-align: right !important; direction: ltr !important; width: 100% !important; display: block !important;">
                <div style="text-align: right !important; direction: ltr !important; display: block !important;">
                    <span class="ps-cause-footer-brand" style="text-align: right !important;">CAUSE OS</span>
                    <span class="ps-cause-footer-separator">—</span>
                    <span style="text-align: right !important;">성공에는 이유가 있습니다</span>
                </div>
                <div class="ps-cause-footer-copyright" style="text-align: right !important; direction: ltr !important; display: block !important;">© 2026 INNOVATION100. All rights reserved.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
