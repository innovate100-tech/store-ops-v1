// ============================================
// 애니메이션 강제 적용 스크립트 v2 (개선 버전)
// Console에 복사해서 붙여넣으세요!
// ============================================

// 1단계: keyframes 생성
const style = document.createElement('style');
style.id = 'ps-animation-fix';
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

// 기존 스타일이 있으면 제거
const existingStyle = document.getElementById('ps-animation-fix');
if (existingStyle) {
    existingStyle.remove();
}

document.head.appendChild(style);
console.log('✅ keyframes 생성 완료!');

// 2단계: 카드 찾기 (여러 선택자 + 대기)
function findCards() {
    // 여러 선택자 시도 (우선순위 순)
    const selectors = [
        '[data-ps-scope="input_hub"] .ps-start-needed-card',
        '.ps-start-needed-card',
        'div.ps-start-needed-card',
        '[class*="ps-start-needed-card"]',
        '[class*="start-needed"]'
    ];
    
    for (const selector of selectors) {
        try {
            const cards = document.querySelectorAll(selector);
            if (cards.length > 0) {
                console.log(`✅ 선택자 "${selector}"로 ${cards.length}개 카드 발견!`);
                return cards;
            }
        } catch (e) {
            // 선택자 오류 무시하고 다음 시도
        }
    }
    return null;
}

// 요소가 나타날 때까지 대기 (최대 10초)
function waitForCards(maxWait = 10000) {
    return new Promise((resolve) => {
        const startTime = Date.now();
        const checkInterval = 200; // 200ms마다 확인
        
        // 즉시 한 번 확인
        const immediateCards = findCards();
        if (immediateCards && immediateCards.length > 0) {
            resolve(immediateCards);
            return;
        }
        
        const interval = setInterval(() => {
            const cards = findCards();
            if (cards && cards.length > 0) {
                clearInterval(interval);
                resolve(cards);
            } else if (Date.now() - startTime > maxWait) {
                clearInterval(interval);
                console.warn(`⏱️ ${maxWait/1000}초 동안 대기했지만 카드를 찾지 못했습니다.`);
                resolve(null);
            }
        }, checkInterval);
    });
}

// 3단계: 모든 div 요소 검색하여 디버깅 정보 제공
function debugFindCards() {
    console.log('🔍 디버깅: 페이지의 모든 요소 검색 중...');
    const allDivs = document.querySelectorAll('div');
    const matchingDivs = [];
    
    allDivs.forEach(div => {
        const className = div.className || '';
        const text = div.textContent || '';
        
        // "시작 필요" 또는 관련 클래스가 있는 div 찾기
        if (className.includes('start') || 
            className.includes('needed') || 
            className.includes('card') ||
            text.includes('시작 필요') ||
            text.includes('지금 시작')) {
            matchingDivs.push({
                element: div,
                className: className,
                text: text.substring(0, 50) // 처음 50자만
            });
        }
    });
    
    if (matchingDivs.length > 0) {
        console.log(`📊 관련 요소 ${matchingDivs.length}개 발견:`);
        matchingDivs.slice(0, 10).forEach((item, i) => {
            console.log(`   ${i + 1}. 클래스: "${item.className}"`);
            console.log(`      텍스트: "${item.text}..."`);
        });
        
        // 첫 번째 요소에 직접 애니메이션 적용 시도
        if (matchingDivs.length > 0) {
            console.log('💡 발견된 첫 번째 요소에 애니메이션 적용 시도...');
            const firstDiv = matchingDivs[0].element;
            firstDiv.style.setProperty('animation', 'pulse-start-needed 2s ease-in-out infinite, glow-pulse 3s ease-in-out infinite', 'important');
            firstDiv.style.setProperty('animation-name', 'pulse-start-needed, glow-pulse', 'important');
            firstDiv.style.setProperty('animation-duration', '2s, 3s', 'important');
            firstDiv.style.setProperty('animation-timing-function', 'ease-in-out, ease-in-out', 'important');
            firstDiv.style.setProperty('animation-iteration-count', 'infinite, infinite', 'important');
            firstDiv.style.setProperty('transform', 'scale(1)', 'important');
            firstDiv.style.setProperty('will-change', 'transform, box-shadow', 'important');
            console.log('✅ 첫 번째 요소에 애니메이션 적용 완료!');
        }
    } else {
        console.log('❌ 관련 요소를 찾을 수 없습니다.');
    }
}

// 메인 실행
console.log('🔍 카드 요소 찾는 중... (최대 10초 대기)');
waitForCards().then(cards => {
    if (!cards || cards.length === 0) {
        console.error('❌ 카드를 찾을 수 없습니다!');
        console.log('💡 디버깅 모드로 전환합니다...');
        debugFindCards();
    } else {
        // 4단계: 각 카드에 애니메이션 강제 적용
        cards.forEach((card, index) => {
            // 인라인 스타일로 강제 적용 (최고 우선순위)
            card.style.setProperty('animation', 'pulse-start-needed 2s ease-in-out infinite, glow-pulse 3s ease-in-out infinite', 'important');
            card.style.setProperty('animation-name', 'pulse-start-needed, glow-pulse', 'important');
            card.style.setProperty('animation-duration', '2s, 3s', 'important');
            card.style.setProperty('animation-timing-function', 'ease-in-out, ease-in-out', 'important');
            card.style.setProperty('animation-iteration-count', 'infinite, infinite', 'important');
            card.style.setProperty('animation-fill-mode', 'both, both', 'important');
            card.style.setProperty('transform', 'scale(1)', 'important');
            card.style.setProperty('will-change', 'transform, box-shadow', 'important');
            
            console.log(`✅ 카드 ${index + 1}에 애니메이션 적용 완료!`);
        });
        
        // 5단계: 적용 확인
        const firstCard = cards[0];
        const computedStyle = window.getComputedStyle(firstCard);
        console.log('🔍 적용된 애니메이션:', computedStyle.animation);
        console.log('🔍 애니메이션 이름:', computedStyle.animationName);
        
        if (computedStyle.animation && computedStyle.animation !== 'none') {
            console.log('🎉 성공! 애니메이션이 적용되었습니다!');
            console.log('💡 이제 카드가 펄스 효과와 함께 움직여야 합니다.');
        } else {
            console.warn('⚠️ 애니메이션이 적용되지 않았습니다. 다른 CSS가 덮어쓰고 있을 수 있습니다.');
        }
    }
});
