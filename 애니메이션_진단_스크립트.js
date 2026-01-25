// ============================================
// 애니메이션 진단 스크립트
// Console에 복사해서 붙여넣으세요!
// ============================================

console.log('🔍 애니메이션 진단 시작...');

// 1단계: keyframes 확인
const keyframes = document.querySelectorAll('style');
let hasKeyframes = false;
keyframes.forEach(style => {
    if (style.textContent.includes('pulse-start-needed') || style.textContent.includes('glow-pulse')) {
        hasKeyframes = true;
    }
});

if (hasKeyframes) {
    console.log('✅ keyframes 발견됨');
} else {
    console.log('❌ keyframes 없음 - 생성 중...');
    const style = document.createElement('style');
    style.id = 'ps-diagnosis-keyframes';
    style.textContent = `
        @keyframes pulse-start-needed {
            0%, 100% { 
                transform: scale(1); 
                box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.7),
                            0 0 15px rgba(245, 158, 11, 0.5),
                            0 0 30px rgba(245, 158, 11, 0.3);
            }
            50% { 
                transform: scale(1.05); 
                box-shadow: 0 0 0 12px rgba(245, 158, 11, 0),
                            0 0 25px rgba(245, 158, 11, 0.8),
                            0 0 50px rgba(245, 158, 11, 0.6);
            }
        }
        @keyframes glow-pulse {
            0%, 100% { 
                box-shadow: 0 0 15px rgba(245, 158, 11, 0.6),
                            0 0 30px rgba(245, 158, 11, 0.4);
            }
            50% { 
                box-shadow: 0 0 25px rgba(245, 158, 11, 0.9),
                            0 0 50px rgba(245, 158, 11, 0.7);
            }
        }
    `;
    document.head.appendChild(style);
    console.log('✅ keyframes 생성 완료');
}

// 2단계: 카드 찾기 (여러 방법 시도)
const foundElements = [];
const processedDivs = new Set();

// 방법 1: 텍스트 기반 검색
const allElements = document.querySelectorAll('*');
allElements.forEach(el => {
    const text = el.textContent || '';
    if (text.includes('지금 시작하세요') || text.includes('🚨') || text.includes('시작 필요')) {
        // 텍스트 요소의 부모 div 찾기 (카드)
        let parentDiv = el;
        while (parentDiv && parentDiv.tagName !== 'DIV' && parentDiv.parentElement) {
            parentDiv = parentDiv.parentElement;
        }
        // div를 찾지 못하면 원래 요소 사용
        if (!parentDiv || parentDiv.tagName !== 'DIV') {
            parentDiv = el;
        }
        
        // 이미 처리한 div인지 확인
        if (processedDivs.has(parentDiv)) {
            return;
        }
        processedDivs.add(parentDiv);
        
        const inlineStyle = parentDiv.getAttribute('style') || '';
        const style = window.getComputedStyle(parentDiv);
        
        // 주황색 스타일이 있거나 카드처럼 보이는 div만 추가 (실제 코드와 동일한 로직)
        const hasOrangeStyle = 
            inlineStyle.includes('245, 158, 11') ||
            inlineStyle.includes('F59E0B') ||
            inlineStyle.includes('rgba(245, 158, 11') ||
            style.borderColor.includes('245') || 
            style.borderColor.includes('158') || 
            style.color.includes('245') ||
            style.color.includes('158') ||
            style.backgroundColor.includes('245') || 
            style.backgroundColor.includes('158');
        
        const looksLikeCard = (style.padding !== '0px' && style.padding !== '') || 
                             inlineStyle.includes('border-radius') ||
                             inlineStyle.includes('padding') ||
                             inlineStyle.includes('background');
        
        if (hasOrangeStyle || looksLikeCard) {
            foundElements.push(parentDiv);
        }
    }
});

// 방법 2: 오렌지색 스타일 기반 검색 (텍스트 검색이 실패한 경우)
if (foundElements.length === 0) {
    console.log('⚠️ 텍스트 검색 실패 - 스타일 기반 검색 시도...');
    const allDivs = document.querySelectorAll('div');
    allDivs.forEach(div => {
        const inlineStyle = div.getAttribute('style') || '';
        const computedStyle = window.getComputedStyle(div);
        
        // 오렌지색 확인 (여러 방법) - 실제 코드와 동일한 로직
        const hasOrangeStyle = 
            inlineStyle.includes('245, 158, 11') || 
            inlineStyle.includes('F59E0B') || 
            inlineStyle.includes('rgba(245, 158, 11') ||
            computedStyle.borderColor.includes('245') || 
            computedStyle.borderColor.includes('158') || 
            computedStyle.color.includes('245') || 
            computedStyle.color.includes('158') ||
            computedStyle.backgroundColor.includes('245') || 
            computedStyle.backgroundColor.includes('158');
        
        // 카드처럼 보이는지 확인 - 실제 코드와 동일한 로직
        const looksLikeCard = 
            (computedStyle.padding !== '0px' && computedStyle.padding !== '') || 
            inlineStyle.includes('border-radius') ||
            inlineStyle.includes('padding') || 
            inlineStyle.includes('background');
        
        if ((hasOrangeStyle || looksLikeCard) && !processedDivs.has(div)) {
            processedDivs.add(div);
            foundElements.push(div);
        }
    });
}

console.log(`📊 발견된 카드: ${foundElements.length}개`);

// 3단계: 각 카드의 현재 상태 확인
foundElements.forEach((card, i) => {
    const computedStyle = window.getComputedStyle(card);
    const animation = computedStyle.animation;
    const animationName = computedStyle.animationName;
    const transform = computedStyle.transform;
    const boxShadow = computedStyle.boxShadow;
    
    console.log(`\n카드 ${i + 1}:`);
    console.log(`  animation: ${animation}`);
    console.log(`  animation-name: ${animationName}`);
    console.log(`  transform: ${transform}`);
    console.log(`  box-shadow: ${boxShadow.substring(0, 80)}...`);
    
    // 애니메이션이 없거나 작동하지 않으면 강제 적용
    if (!animation || animation === 'none' || !animation.includes('pulse-start-needed')) {
        console.log(`  ⚠️ 애니메이션 없음 - 강제 적용 중...`);
        
        // 기존 스타일 백업
        const originalStyle = card.getAttribute('style') || '';
        
        // 애니메이션 강제 적용 (더 강력한 방법)
        card.style.cssText = originalStyle + '; animation: pulse-start-needed 2s ease-in-out infinite, glow-pulse 3s ease-in-out infinite !important; transform: scale(1) !important; will-change: transform, box-shadow !important;';
        
        // 개별 속성도 설정
        card.style.setProperty('animation-name', 'pulse-start-needed, glow-pulse', 'important');
        card.style.setProperty('animation-duration', '2s, 3s', 'important');
        card.style.setProperty('animation-timing-function', 'ease-in-out, ease-in-out', 'important');
        card.style.setProperty('animation-iteration-count', 'infinite, infinite', 'important');
        card.style.setProperty('animation-fill-mode', 'both, both', 'important');
        card.style.setProperty('animation-play-state', 'running', 'important');
        card.style.setProperty('transform', 'scale(1)', 'important');
        card.style.setProperty('box-shadow', '0 0 20px rgba(245, 158, 11, 0.6), 0 0 40px rgba(245, 158, 11, 0.4)', 'important');
        card.style.setProperty('will-change', 'transform, box-shadow', 'important');
        
        // 애니메이션 재시작
        card.style.animation = 'none';
        setTimeout(() => {
            card.style.setProperty('animation', 'pulse-start-needed 2s ease-in-out infinite, glow-pulse 3s ease-in-out infinite', 'important');
        }, 10);
        
        console.log(`  ✅ 강제 적용 완료`);
    } else {
        console.log(`  ✅ 애니메이션 이미 적용됨`);
    }
});

// 4단계: 최종 확인
setTimeout(() => {
    console.log('\n🔍 최종 확인:');
    foundElements.forEach((card, i) => {
        const computedStyle = window.getComputedStyle(card);
        const animation = computedStyle.animation;
        if (animation && animation !== 'none' && animation.includes('pulse-start-needed')) {
            console.log(`  ✅ 카드 ${i + 1}: 애니메이션 작동 중`);
        } else {
            console.log(`  ❌ 카드 ${i + 1}: 애니메이션 없음`);
        }
    });
}, 500);

console.log('\n💡 이제 카드가 움직여야 합니다!');
console.log('💡 Elements 탭에서 카드를 선택하고 Styles 탭에서 "animation" 속성을 확인하세요.');
