-- ============================================
-- SSOT 빠른 검증 쿼리 (왕초보용)
-- ============================================
-- 사용법:
-- 1. 아래 "🔧 여기 수정" 부분의 store_id를 실제 값으로 변경
-- 2. 각 쿼리를 하나씩 실행 (전체 선택 후 실행도 가능)
-- ============================================

-- 🔧 여기 수정: store_id 찾는 방법
-- Supabase → Table Editor → stores 테이블 → id 컬럼 값 복사
-- 또는 아래 쿼리로 찾기:
-- SELECT id, name FROM stores;

-- ⚠️ 아래 'your-store-id-here'를 실제 store_id로 변경하세요!
-- 예시: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'

-- ============================================
-- 1단계: store_id 찾기 (처음 한 번만)
-- ============================================

-- 1-1. stores 테이블에서 store_id 확인
-- ⚠️ 중요: 아래 쿼리는 그대로 실행하세요! 수정하지 마세요!
SELECT 
    id AS store_id,  -- ⬅️ 이 값이 store_id입니다! (AS 뒤는 별칭이므로 수정 금지!)
    name AS 매장명,
    created_at AS 생성일
FROM stores
ORDER BY created_at DESC;
-- 기대 결과: 매장 목록이 나옵니다. id 컬럼 값을 복사하세요.
-- ⚠️ 주의: "id AS store_id"에서 "store_id"는 컬럼 이름일 뿐입니다!
--          실제 store_id 값은 결과 표의 "store_id" 컬럼에 나옵니다!

-- ============================================
-- 2단계: 객체 존재 확인 (한 번만)
-- ============================================

-- 2-1. VIEW 2개가 생성되었는지 확인
SELECT 
    table_name AS 뷰이름,
    'VIEW 생성됨' AS 상태
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('v_daily_sales_official', 'v_daily_sales_best_available')
ORDER BY table_name;
-- 기대 결과: 2개 행 (v_daily_sales_official, v_daily_sales_best_available)

-- 2-2. audit 테이블이 생성되었는지 확인
SELECT 
    COUNT(*) AS 컬럼개수,
    'audit 테이블 생성됨' AS 상태
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'daily_sales_items_audit';
-- 기대 결과: 11 (컬럼이 11개면 정상)

-- 2-3. 함수가 생성되었는지 확인
SELECT 
    routine_name AS 함수이름,
    '함수 생성됨' AS 상태
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND routine_name IN ('log_daily_sales_item_change', 'save_daily_close_transaction')
ORDER BY routine_name;
-- 기대 결과: 2개 행 (2개 함수 모두 존재)

-- ============================================
-- 3단계: VIEW 동작 확인 (store_id 필요!)
-- ============================================
-- ⚠️ 아래 'your-store-id-here'를 실제 store_id로 변경하세요!

-- 3-1. 공식 매출 뷰 조회 (daily_close만)
SELECT 
    date AS 날짜,
    total_sales AS 총매출,
    is_official AS 공식여부,
    source AS 출처
FROM v_daily_sales_official
WHERE store_id = 'your-store-id-here'::UUID  -- ⚠️ 여기 수정!
ORDER BY date DESC
LIMIT 10;
-- 기대 결과: daily_close가 있는 날짜만 나옴, is_official=true, source='daily_close'

-- 3-2. 최선의 매출 뷰 조회 (daily_close 우선, 없으면 sales)
SELECT 
    date AS 날짜,
    total_sales AS 총매출,
    is_official AS 공식여부,
    source AS 출처
FROM v_daily_sales_best_available
WHERE store_id = 'your-store-id-here'::UUID  -- ⚠️ 여기 수정!
ORDER BY date DESC
LIMIT 10;
-- 기대 결과: 모든 날짜 나옴, daily_close 있으면 is_official=true, sales만 있으면 false

-- ============================================
-- 4단계: SSOT 분리 확인 (핵심 테스트!)
-- ============================================
-- ⚠️ 아래 'your-store-id-here'를 실제 store_id로 변경하세요!

-- 4-1. sales만 있는 날짜 확인 (가장 중요!)
SELECT 
    s.date AS 날짜,
    'sales만 존재' AS 상황,
    (SELECT COUNT(*) FROM v_daily_sales_official WHERE store_id = s.store_id AND date = s.date) AS 공식뷰_개수,
    (SELECT COUNT(*) FROM v_daily_sales_best_available WHERE store_id = s.store_id AND date = s.date) AS 최선뷰_개수,
    (SELECT is_official FROM v_daily_sales_best_available WHERE store_id = s.store_id AND date = s.date LIMIT 1) AS 공식여부,
    (SELECT source FROM v_daily_sales_best_available WHERE store_id = s.store_id AND date = s.date LIMIT 1) AS 출처
FROM sales s
WHERE s.store_id = 'your-store-id-here'::UUID  -- ⚠️ 여기 수정!
  AND NOT EXISTS (
      SELECT 1 FROM daily_close dc 
      WHERE dc.store_id = s.store_id AND dc.date = s.date
  )
ORDER BY s.date DESC
LIMIT 5;
-- 기대 결과: 공식뷰_개수=0, 최선뷰_개수=1, 공식여부=false, 출처='sales'
-- ⬅️ 이게 맞으면 SSOT가 제대로 작동하는 것입니다!

-- 4-2. daily_close만 있는 날짜 확인
SELECT 
    dc.date AS 날짜,
    'daily_close만 존재' AS 상황,
    (SELECT COUNT(*) FROM v_daily_sales_official WHERE store_id = dc.store_id AND date = dc.date) AS 공식뷰_개수,
    (SELECT COUNT(*) FROM v_daily_sales_best_available WHERE store_id = dc.store_id AND date = dc.date) AS 최선뷰_개수,
    (SELECT is_official FROM v_daily_sales_best_available WHERE store_id = dc.store_id AND date = dc.date LIMIT 1) AS 공식여부,
    (SELECT source FROM v_daily_sales_best_available WHERE store_id = dc.store_id AND date = dc.date LIMIT 1) AS 출처
FROM daily_close dc
WHERE dc.store_id = 'your-store-id-here'::UUID  -- ⚠️ 여기 수정!
  AND NOT EXISTS (
      SELECT 1 FROM sales s 
      WHERE s.store_id = dc.store_id AND s.date = dc.date
      AND NOT EXISTS (
          SELECT 1 FROM daily_close dc2 
          WHERE dc2.store_id = s.store_id AND dc2.date = s.date
      )
  )
ORDER BY dc.date DESC
LIMIT 5;
-- 기대 결과: 공식뷰_개수=1, 최선뷰_개수=1, 공식여부=true, 출처='daily_close'

-- ============================================
-- 5단계: Audit 확인 (점장 마감 후 확인)
-- ============================================
-- ⚠️ 아래 'your-store-id-here'를 실제 store_id로 변경하세요!

-- 5-1. audit 최신 10개 조회
SELECT 
    date AS 날짜,
    action AS 동작,
    old_qty AS 이전수량,
    new_qty AS 새수량,
    source AS 출처,
    changed_at AS 변경시간
FROM daily_sales_items_audit
WHERE store_id = 'your-store-id-here'::UUID  -- ⚠️ 여기 수정!
ORDER BY changed_at DESC
LIMIT 10;
-- 기대 결과: 최근 변경 이력 10개, action은 'insert'/'update'/'soft_delete', source는 'close'/'override'

-- 5-2. audit 통계
SELECT 
    source AS 출처,
    action AS 동작,
    COUNT(*) AS 횟수
FROM daily_sales_items_audit
WHERE store_id = 'your-store-id-here'::UUID  -- ⚠️ 여기 수정!
GROUP BY source, action
ORDER BY source, action;
-- 기대 결과: source별, action별 통계

-- ============================================
-- 6단계: 점장 마감 저장 후 확인 (실제 테스트)
-- ============================================
-- ⚠️ 점장 마감을 저장한 후 아래 쿼리 실행하세요!

-- 6-1. 특정 날짜의 daily_sales_items 확인
-- ⚠️ 'your-store-id-here'와 '2024-01-20'을 실제 값으로 변경하세요!
SELECT 
    dsi.date AS 날짜,
    mm.name AS 메뉴명,
    dsi.qty AS 판매량,
    dsi.updated_at AS 업데이트시간
FROM daily_sales_items dsi
JOIN menu_master mm ON dsi.menu_id = mm.id
WHERE dsi.store_id = 'your-store-id-here'::UUID  -- ⚠️ 여기 수정!
  AND dsi.date = '2024-01-20'::DATE  -- ⚠️ 여기를 테스트한 날짜로 변경!
ORDER BY mm.name;
-- 기대 결과: 해당 날짜의 모든 메뉴별 판매량 (DELETE 없이 UPSERT만 됨)

-- 6-2. 특정 날짜의 audit 기록 확인
SELECT 
    a.date AS 날짜,
    mm.name AS 메뉴명,
    a.action AS 동작,
    a.old_qty AS 이전수량,
    a.new_qty AS 새수량,
    a.source AS 출처,
    a.reason AS 사유,
    a.changed_at AS 변경시간
FROM daily_sales_items_audit a
JOIN menu_master mm ON a.menu_id = mm.id
WHERE a.store_id = 'your-store-id-here'::UUID  -- ⚠️ 여기 수정!
  AND a.date = '2024-01-20'::DATE  -- ⚠️ 여기를 테스트한 날짜로 변경!
ORDER BY a.changed_at DESC;
-- 기대 결과: 해당 날짜의 모든 변경 이력 (source='close', action은 'insert' 또는 'update')

-- ============================================
-- 💡 사용 팁
-- ============================================
-- 1. 먼저 1단계로 store_id를 찾으세요
-- 2. 2단계로 객체가 생성되었는지 확인하세요
-- 3. 3단계로 VIEW가 동작하는지 확인하세요
-- 4. 4단계가 가장 중요합니다! SSOT 분리가 제대로 되는지 확인하세요
-- 5. 점장 마감 저장 후 6단계로 실제 동작을 확인하세요

-- ============================================
-- 🔍 Find & Replace 사용법 (store_id 한 번에 변경)
-- ============================================
-- 1. SQL Editor에서 Ctrl + H (또는 Cmd + H) 누르기
-- 2. Find: your-store-id-here
-- 3. Replace: 실제-store-id-값
-- 4. "Replace All" 클릭
-- 5. 완료!
