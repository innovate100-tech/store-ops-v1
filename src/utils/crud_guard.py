"""
CRUD 작업 공통 래퍼 및 감시 유틸리티
write 작업의 일관성, 가시성, 안정성 보장
"""
import time
import streamlit as st
from typing import Callable, List, Dict, Any, Optional
from datetime import datetime
from src.utils.time_utils import now_kst


def run_write(
    action_name: str,
    fn: Callable,
    *,
    targets: List[str],
    extra: Dict[str, Any] = None,
    rerun: bool = True,
    success_message: str = None
) -> Any:
    """
    공통 write 작업 래퍼
    
    Args:
        action_name: 작업 이름 (예: "save_sales", "delete_menu")
        fn: 실행할 함수 (Callable)
        targets: 무효화할 데이터 타입 리스트 (예: ["sales"], ["menus", "recipes"])
        extra: 추가 정보 (디버깅용, 예: {"date": "2024-01-01", "store_id": "xxx"})
        rerun: 성공 시 st.rerun() 호출 여부 (기본: True)
        success_message: 성공 시 표시할 메시지 (None이면 기본 메시지)
    
    Returns:
        함수 실행 결과
    
    Raises:
        원본 함수가 발생시킨 예외
    """
    start_time = time.perf_counter()
    error_type = None
    error_msg = None
    result = None
    ok = False
    
    try:
        # 함수 실행
        result = fn()
        ok = True
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        # 성공 처리
        try:
            # 1. soft_invalidate
            from src.storage_supabase import soft_invalidate
            soft_invalidate(
                reason=action_name,
                targets=targets,
                session_keys=None  # 자동 결정
            )
        except Exception as e:
            # invalidate 실패해도 계속 진행
            pass
        
        # 2. snapshot 기록 (dev_mode에서만)
        try:
            from src.auth import is_dev_mode
            if is_dev_mode():
                from src.utils.boot_perf import snapshot_current_metrics
                snapshot_current_metrics(f"WRITE: {action_name}")
        except Exception:
            pass
        
        # 3. write_audit_log 기록
        _record_write_audit(
            action=action_name,
            ok=True,
            ms=elapsed_ms,
            targets=targets,
            error_type=None,
            error_msg=None,
            extra=extra
        )
        
        # 4. 사용자 메시지
        if success_message:
            st.success(success_message)
        else:
            st.success(f"✅ {action_name} 완료")
        
        # 5. rerun (성공 시)
        if rerun:
            st.rerun()
        
        return result
        
    except Exception as e:
        # 실패 처리
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        error_type = type(e).__name__
        error_msg = str(e)
        ok = False
        
        # 1. snapshot 기록 (dev_mode에서만)
        try:
            from src.auth import is_dev_mode
            if is_dev_mode():
                from src.utils.boot_perf import snapshot_current_metrics
                snapshot_current_metrics(f"WRITE_FAIL: {action_name}")
        except Exception:
            pass
        
        # 2. write_audit_log 기록
        _record_write_audit(
            action=action_name,
            ok=False,
            ms=elapsed_ms,
            targets=targets,
            error_type=error_type,
            error_msg=error_msg,
            extra=extra
        )
        
        # 3. 사용자 메시지
        st.error(f"❌ {action_name} 실패: {error_msg}")
        
        # 4. 예외 재발생
        raise


def _record_write_audit(
    action: str,
    ok: bool,
    ms: float,
    targets: List[str],
    error_type: Optional[str] = None,
    error_msg: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None
):
    """
    write 작업 감사 로그 기록
    
    Args:
        action: 작업 이름
        ok: 성공 여부
        ms: 소요 시간 (밀리초)
        targets: 무효화 대상
        error_type: 에러 타입 (실패 시)
        error_msg: 에러 메시지 (실패 시)
        extra: 추가 정보
    """
    if "write_audit_log" not in st.session_state:
        st.session_state["write_audit_log"] = []
    
    log_entry = {
        "ts_kst": now_kst().isoformat(),
        "action": action,
        "ok": ok,
        "ms": round(ms, 2),
        "targets": targets,
        "error_type": error_type,
        "error_msg": error_msg,
        "extra": extra or {}
    }
    
    st.session_state["write_audit_log"].append(log_entry)
    
    # 최대 20개까지만 유지
    if len(st.session_state["write_audit_log"]) > 20:
        st.session_state["write_audit_log"] = st.session_state["write_audit_log"][-20:]


def get_write_audit_log() -> List[Dict]:
    """write 감사 로그 반환"""
    return st.session_state.get("write_audit_log", []).copy()


def clear_write_audit_log():
    """write 감사 로그 초기화"""
    if "write_audit_log" in st.session_state:
        st.session_state["write_audit_log"] = []
