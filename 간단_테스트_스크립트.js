// ============================================
// 간단한 테스트 스크립트
// Console에 복사해서 붙여넣으세요!
// ============================================

// 1단계: "지금 시작하세요" 텍스트가 있는 모든 요소 찾기
console.log('🔍 "지금 시작하세요" 텍스트 검색 중...');
const allElements = document.querySelectorAll('*');
const foundElements = [];

allElements.forEach(el => {
    const text = el.textContent || '';
    if (text.includes('지금 시작하세요') || text.includes('🚨 지금 시작하세요')) {
        // 텍스트 요소가 아니라 부모 div를 찾기
        let targetEl = el;
        // div를 찾을 때까지 부모로 올라가기
        while (targetEl && targetEl.tagName !== 'DIV' && targetEl.parentElement) {
            targetEl = targetEl.parentElement;
        }
        // div를 찾지 못하면 원래 요소 사용
        if (!targetEl || targetEl.tagName !== 'DIV') {
            targetEl = el;
        }
        
        foundElements.push({
            element: targetEl,
            tagName: targetEl.tagName,
            text: text.trim().substring(0, 100),
            className: targetEl.className,
            style: targetEl.getAttribute('style') || ''
        });
    }
});

console.log(`📊 발견된 요소: ${foundElements.length}개`);

if (foundElements.length > 0) {
    console.log('✅ 발견된 요소들:');
    foundElements.forEach((item, i) => {
        console.log(`\n${i + 1}. 태그: <${item.tagName}>`);
        console.log(`   클래스: "${item.className}"`);
        console.log(`   텍스트: "${item.text}..."`);
        console.log(`   인라인 스타일: ${item.style.substring(0, 150)}...`);
        console.log('   요소:', item.element);
    });
    
    // 모든 발견된 요소에 애니메이션 적용
    console.log('\n💡 발견된 모든 요소에 애니메이션 적용 시도...');
    
    // keyframes 생성
    const style = document.createElement('style');
    style.id = 'ps-test-animation';
    style.textContent = `
        @keyframes pulse-start-needed {
            0%, 100% { 
                transform: scale(1); 
                box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.7),
                            0 0 15px rgba(245, 158, 11, 0.5),
                            0 0 30px rgba(245, 158, 11, 0.3);
            }
            50% { 
                transform: scale(1.02); 
                box-shadow: 0 0 0 8px rgba(245, 158, 11, 0),
                            0 0 20px rgba(245, 158, 11, 0.7),
                            0 0 40px rgba(245, 158, 11, 0.5);
            }
        }
        @keyframes glow-pulse {
            0%, 100% { 
                box-shadow: 0 0 10px rgba(245, 158, 11, 0.5),
                            0 0 20px rgba(245, 158, 11, 0.3);
            }
            50% { 
                box-shadow: 0 0 15px rgba(245, 158, 11, 0.7),
                            0 0 30px rgba(245, 158, 11, 0.5);
            }
        }
    `;
    if (!document.getElementById('ps-test-animation')) {
        document.head.appendChild(style);
    }
    
    // 각 요소에 애니메이션 적용
    foundElements.forEach((item, i) => {
        const el = item.element;
        el.style.setProperty('animation', 'pulse-start-needed 2s ease-in-out infinite, glow-pulse 3s ease-in-out infinite', 'important');
        el.style.setProperty('animation-name', 'pulse-start-needed, glow-pulse', 'important');
        el.style.setProperty('animation-duration', '2s, 3s', 'important');
        el.style.setProperty('animation-timing-function', 'ease-in-out, ease-in-out', 'important');
        el.style.setProperty('animation-iteration-count', 'infinite, infinite', 'important');
        el.style.setProperty('animation-fill-mode', 'both, both', 'important');
        el.style.setProperty('box-shadow', '0 0 15px rgba(245, 158, 11, 0.5), 0 0 30px rgba(245, 158, 11, 0.3)', 'important');
        el.style.setProperty('transform', 'scale(1)', 'important');
        el.style.setProperty('will-change', 'transform, box-shadow', 'important');
        console.log(`✅ 요소 ${i + 1}에 애니메이션 적용 완료!`);
    });
    
    console.log('🎉 모든 요소에 애니메이션 적용 완료! 이제 카드가 움직여야 합니다.');
} else {
    console.log('❌ "지금 시작하세요" 텍스트를 찾을 수 없습니다.');
    console.log('💡 페이지에 "시작 필요" 상태인 항목이 없을 수 있습니다.');
    console.log('💡 또는 텍스트가 다른 형태로 표시되고 있을 수 있습니다.');
}
