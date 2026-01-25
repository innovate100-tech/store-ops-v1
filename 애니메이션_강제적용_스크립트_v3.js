// ============================================
// 애니메이션 강제 적용 스크립트 v3 (data 속성 기반)
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

// 2단계: 카드 찾기 (data 속성 기반)
function findCards() {
    // data 속성으로 찾기 (Streamlit이 클래스를 제거할 수 있으므로)
    const selectors = [
        '[data-ps-start-needed="true"]',
        'div[data-ps-start-needed="true"]',
        '[data-ps-scope="input_hub"] [data-ps-start-needed="true"]'
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

// 메인 실행
console.log('🔍 카드 요소 찾는 중... (data 속성 기반, 최대 10초 대기)');
waitForCards().then(cards => {
    if (!cards || cards.length === 0) {
        console.error('❌ 카드를 찾을 수 없습니다!');
        console.log('💡 Elements 탭에서 [data-ps-start-needed="true"] 속성이 있는 요소를 확인해주세요.');
        
        // 디버깅: 모든 요소에서 data 속성 검색
        console.log('🔍 디버깅: 모든 요소에서 data-ps-start-needed 속성 검색 중...');
        const allElements = document.querySelectorAll('*');
        const matchingElements = Array.from(allElements).filter(el => {
            return el.hasAttribute('data-ps-start-needed');
        });
        console.log(`📊 data-ps-start-needed 속성을 가진 요소: ${matchingElements.length}개`);
    } else {
        // 3단계: 각 카드에 애니메이션 강제 적용
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
        
        // 4단계: 적용 확인
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
