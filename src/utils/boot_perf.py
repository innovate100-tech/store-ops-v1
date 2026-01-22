"""
부팅 성능 계측 유틸리티
앱 첫 진입 속도 개선을 위한 성능 측정 도구
"""
import time
import streamlit as st
from typing import Dict, List, Tuple, Optional
from contextlib import contextmanager


# 전역 성능 측정 변수
_boot_perf_data = {
    "APP_START": None,
    "IMPORT_TOTAL_MS": None,
    "BOOTSTRAP_TOTAL_MS": None,
    "BOOTSTRAP_DB_CALLS": [],
    "BOOTSTRAP_DB_TIME_MS": 0.0,
    "PAGE_IMPORT_MS": None,
    "PAGE_RENDER_MS": None,
    "PAGE_TOTAL_MS": None,
    "DATA_CALLS": [],  # 데이터 호출 기록
    "DATA_CALLS_TOTAL_MS": 0.0,
    "DATA_CALLS_COUNT": 0,
    "COMPUTE_CALLS": [],  # 계산/가공 호출 기록
    "COMPUTE_CALLS_TOTAL_MS": 0.0,
    "COMPUTE_CALLS_COUNT": 0,
    "LAST_INVALIDATION": None,  # 마지막 캐시 무효화 정보
}

# 성능 스냅샷 저장 (최근 N개)
_perf_snapshots = []
_MAX_SNAPSHOTS = 20  # 최대 저장할 스냅샷 개수

# 최근 측정값 저장 (최근 2회)
_recent_measurements = {
    "IMPORT_TOTAL_MS": [],
    "BOOTSTRAP_TOTAL_MS": [],
    "BOOTSTRAP_DB_CALLS_COUNT": [],
    "BOOTSTRAP_DB_TIME_MS": [],
    "PAGE_IMPORT_MS": [],
    "PAGE_RENDER_MS": [],
    "PAGE_TOTAL_MS": [],
}


def init_boot_perf():
    """부팅 성능 측정 초기화"""
    _boot_perf_data["APP_START"] = time.perf_counter()


def record_import_time(end_time: float):
    """Import 완료 시간 기록"""
    if _boot_perf_data["APP_START"] is not None:
        _boot_perf_data["IMPORT_TOTAL_MS"] = (end_time - _boot_perf_data["APP_START"]) * 1000
        # 최근 측정값 저장 (최대 2개)
        _recent_measurements["IMPORT_TOTAL_MS"].append(_boot_perf_data["IMPORT_TOTAL_MS"])
        if len(_recent_measurements["IMPORT_TOTAL_MS"]) > 2:
            _recent_measurements["IMPORT_TOTAL_MS"].pop(0)


def record_bootstrap_time(start_time: float, end_time: float):
    """Bootstrap 완료 시간 기록"""
    _boot_perf_data["BOOTSTRAP_TOTAL_MS"] = (end_time - start_time) * 1000
    # 최근 측정값 저장 (최대 2개)
    _recent_measurements["BOOTSTRAP_TOTAL_MS"].append(_boot_perf_data["BOOTSTRAP_TOTAL_MS"])
    if len(_recent_measurements["BOOTSTRAP_TOTAL_MS"]) > 2:
        _recent_measurements["BOOTSTRAP_TOTAL_MS"].pop(0)


def record_db_call(call_name: str, duration_ms: float):
    """DB 호출 기록"""
    _boot_perf_data["BOOTSTRAP_DB_CALLS"].append({
        "name": call_name,
        "ms": duration_ms
    })
    _boot_perf_data["BOOTSTRAP_DB_TIME_MS"] += duration_ms
    # 최근 측정값 저장 (최대 2개) - DB 호출 완료 시점에 저장
    if len(_recent_measurements["BOOTSTRAP_DB_CALLS_COUNT"]) == 0 or \
       len(_boot_perf_data["BOOTSTRAP_DB_CALLS"]) == 1:
        # 첫 호출이거나 새로운 부팅 시작
        _recent_measurements["BOOTSTRAP_DB_CALLS_COUNT"].append(len(_boot_perf_data["BOOTSTRAP_DB_CALLS"]))
        _recent_measurements["BOOTSTRAP_DB_TIME_MS"].append(_boot_perf_data["BOOTSTRAP_DB_TIME_MS"])
        if len(_recent_measurements["BOOTSTRAP_DB_CALLS_COUNT"]) > 2:
            _recent_measurements["BOOTSTRAP_DB_CALLS_COUNT"].pop(0)
            _recent_measurements["BOOTSTRAP_DB_TIME_MS"].pop(0)
    else:
        # 기존 측정값 업데이트
        _recent_measurements["BOOTSTRAP_DB_CALLS_COUNT"][-1] = len(_boot_perf_data["BOOTSTRAP_DB_CALLS"])
        _recent_measurements["BOOTSTRAP_DB_TIME_MS"][-1] = _boot_perf_data["BOOTSTRAP_DB_TIME_MS"]


def record_page_import_time(duration_ms: float):
    """페이지 import 시간 기록"""
    _boot_perf_data["PAGE_IMPORT_MS"] = duration_ms
    # 최근 측정값 저장 (최대 2개)
    _recent_measurements["PAGE_IMPORT_MS"].append(duration_ms)
    if len(_recent_measurements["PAGE_IMPORT_MS"]) > 2:
        _recent_measurements["PAGE_IMPORT_MS"].pop(0)


def record_page_render_time(duration_ms: float):
    """페이지 render 시간 기록"""
    _boot_perf_data["PAGE_RENDER_MS"] = duration_ms
    # 최근 측정값 저장 (최대 2개)
    _recent_measurements["PAGE_RENDER_MS"].append(duration_ms)
    if len(_recent_measurements["PAGE_RENDER_MS"]) > 2:
        _recent_measurements["PAGE_RENDER_MS"].pop(0)


def record_page_total_time(duration_ms: float):
    """페이지 전체 시간 기록"""
    _boot_perf_data["PAGE_TOTAL_MS"] = duration_ms
    # 최근 측정값 저장 (최대 2개)
    _recent_measurements["PAGE_TOTAL_MS"].append(duration_ms)
    if len(_recent_measurements["PAGE_TOTAL_MS"]) > 2:
        _recent_measurements["PAGE_TOTAL_MS"].pop(0)


def get_boot_perf_data() -> Dict:
    """부팅 성능 데이터 반환"""
    return _boot_perf_data.copy()


def get_recent_measurements() -> Dict:
    """최근 측정값 반환 (최대 2회)"""
    return _recent_measurements.copy()


def render_boot_perf_panel(container, key_prefix="panel"):
    """
    컨테이너에 부팅 성능 정보 표시 (dev_mode)
    
    Args:
        container: Streamlit container (예: st.sidebar, st.container())
        key_prefix: 위젯 키의 접두사 (중복 방지용, 기본값: "panel")
    """
    import streamlit as st
    try:
        from src.auth import is_dev_mode
        if not is_dev_mode():
            return
        
        # 1회 렌더 가드 (같은 run 내 중복 방지)
        guard_key = f"_dev_panel_rendered_{key_prefix}"
        if st.session_state.get(guard_key, False):
            return
        st.session_state[guard_key] = True
        
        with container:
            # force_hard_clear 토글 (dev_mode에서만)
            st.markdown("---")
            with st.expander("🔧 캐시 무효화 설정", expanded=False):
                force_hard_clear = st.toggle(
                    "🔴 강제 전체 캐시 클리어 (비상용)",
                    value=st.session_state.get("force_hard_clear", False),
                    key=f"{key_prefix}_force_hard_clear_toggle",
                    help="활성화하면 모든 write 후 전체 캐시가 강제로 클리어됩니다. (성능 저하)"
                )
                st.session_state["force_hard_clear"] = force_hard_clear
                if force_hard_clear:
                    st.warning("⚠️ 전체 캐시 클리어 모드 활성화됨")
                else:
                    st.caption("ℹ️ 소프트 무효화 모드 (권장)")
            
            with st.expander("🚀 부팅 성능", expanded=False):
                data = get_boot_perf_data()
                
                st.write("**부팅 단계**")
                if data["IMPORT_TOTAL_MS"] is not None:
                    st.metric("IMPORT_TOTAL", f"{data['IMPORT_TOTAL_MS']:.1f}ms")
                if data["BOOTSTRAP_TOTAL_MS"] is not None:
                    st.metric("BOOTSTRAP_TOTAL", f"{data['BOOTSTRAP_TOTAL_MS']:.1f}ms")
                
                if data["BOOTSTRAP_DB_CALLS"]:
                    st.write("**부팅 중 DB 호출**")
                    st.write(f"총 {len(data['BOOTSTRAP_DB_CALLS'])}회, {data['BOOTSTRAP_DB_TIME_MS']:.1f}ms")
                    for call in data["BOOTSTRAP_DB_CALLS"]:
                        st.caption(f"  • {call['name']}: {call['ms']:.1f}ms")
                
                st.write("**페이지 로딩**")
                if data["PAGE_IMPORT_MS"] is not None:
                    recent = get_recent_measurements()
                    if len(recent["PAGE_IMPORT_MS"]) >= 2:
                        prev = recent["PAGE_IMPORT_MS"][-2]
                        diff = data["PAGE_IMPORT_MS"] - prev
                        delta = f"{diff:+.1f}ms" if diff != 0 else "±0.0ms"
                        st.metric("PAGE_IMPORT", f"{data['PAGE_IMPORT_MS']:.1f}ms", delta=delta)
                    else:
                        st.metric("PAGE_IMPORT", f"{data['PAGE_IMPORT_MS']:.1f}ms")
                if data["PAGE_RENDER_MS"] is not None:
                    recent = get_recent_measurements()
                    if len(recent["PAGE_RENDER_MS"]) >= 2:
                        prev = recent["PAGE_RENDER_MS"][-2]
                        diff = data["PAGE_RENDER_MS"] - prev
                        delta = f"{diff:+.1f}ms" if diff != 0 else "±0.0ms"
                        st.metric("PAGE_RENDER", f"{data['PAGE_RENDER_MS']:.1f}ms", delta=delta)
                    else:
                        st.metric("PAGE_RENDER", f"{data['PAGE_RENDER_MS']:.1f}ms")
                if data["PAGE_TOTAL_MS"] is not None:
                    recent = get_recent_measurements()
                    if len(recent["PAGE_TOTAL_MS"]) >= 2:
                        prev = recent["PAGE_TOTAL_MS"][-2]
                        diff = data["PAGE_TOTAL_MS"] - prev
                        delta = f"{diff:+.1f}ms" if diff != 0 else "±0.0ms"
                        st.metric("PAGE_TOTAL", f"{data['PAGE_TOTAL_MS']:.1f}ms", delta=delta)
                    else:
                        st.metric("PAGE_TOTAL", f"{data['PAGE_TOTAL_MS']:.1f}ms")
                
                # 최근 2회 측정값 비교
                recent = get_recent_measurements()
                if len(recent["BOOTSTRAP_TOTAL_MS"]) >= 2:
                    st.write("**최근 2회 비교**")
                    prev_bootstrap = recent["BOOTSTRAP_TOTAL_MS"][-2]
                    curr_bootstrap = recent["BOOTSTRAP_TOTAL_MS"][-1]
                    bootstrap_diff = curr_bootstrap - prev_bootstrap
                    st.caption(f"BOOTSTRAP: {prev_bootstrap:.1f}ms → {curr_bootstrap:.1f}ms ({bootstrap_diff:+.1f}ms)")
            
            # 데이터 호출 통계
            st.write("**데이터 호출**")
            data_summary = get_data_calls_summary()
            if data_summary["total_count"] > 0:
                st.metric("총 호출", f"{data_summary['total_count']}회", f"{data_summary['total_ms']:.1f}ms")
                
                if data_summary["top_10"]:
                    st.write("**상위 10개 (시간 기준)**")
                    for i, call in enumerate(data_summary["top_10"], 1):
                        rows_info = f", {call['rows']}행" if call.get('rows') is not None else ""
                        source_info = f" [{call['source']}]" if call.get('source') else ""
                        st.caption(f"{i}. {call['name']}{source_info}: {call['ms']:.1f}ms{rows_info}")
            else:
                st.caption("아직 데이터 호출 기록이 없습니다.")
            
            # 계산 호출 통계
            st.write("**계산/가공 호출**")
            compute_summary = get_compute_calls_summary()
            if compute_summary["total_count"] > 0:
                st.metric("총 호출", f"{compute_summary['total_count']}회", f"{compute_summary['total_ms']:.1f}ms")
                
                if compute_summary["top_10"]:
                    st.write("**상위 10개 (시간 기준)**")
                    for i, call in enumerate(compute_summary["top_10"], 1):
                        rows_info = ""
                        if call.get('rows_in') is not None or call.get('rows_out') is not None:
                            in_info = f"{call['rows_in']}→" if call.get('rows_in') is not None else ""
                            out_info = f"{call['rows_out']}" if call.get('rows_out') is not None else ""
                            rows_info = f" ({in_info}{out_info}행)" if in_info or out_info else ""
                        note_info = f" [{call['note']}]" if call.get('note') else ""
                        st.caption(f"{i}. {call['name']}{note_info}: {call['ms']:.1f}ms{rows_info}")
            else:
                st.caption("아직 계산 호출 기록이 없습니다.")
            
            # 마지막 캐시 무효화 정보
            st.write("**마지막 캐시 무효화**")
            if _boot_perf_data.get("LAST_INVALIDATION"):
                inv = _boot_perf_data["LAST_INVALIDATION"]
                mode_color = "🔴" if inv["mode"] == "hard" else "🟢"
                st.caption(f"{mode_color} {inv['mode'].upper()}: {inv['reason']}")
                st.caption(f"대상: {', '.join(inv['targets'])}")
            else:
                st.caption("아직 캐시 무효화 기록이 없습니다.")
            
            # 성능 스냅샷 표
            st.write("**성능 스냅샷**")
            snapshots = get_perf_snapshots()
            if snapshots:
                st.caption(f"총 {len(snapshots)}개 스냅샷")
                
                # 스냅샷을 표로 표시
                snapshot_data = []
                for snap in snapshots[-10:]:  # 최근 10개만 표시
                    m = snap["metrics"]
                    snapshot_data.append({
                        "라벨": snap["label"],
                        "BOOTSTRAP": f"{m.get('BOOTSTRAP_TOTAL_MS', 0):.1f}ms" if m.get('BOOTSTRAP_TOTAL_MS') else "-",
                        "PAGE_RENDER": f"{m.get('PAGE_RENDER_MS', 0):.1f}ms" if m.get('PAGE_RENDER_MS') else "-",
                        "DATA_CALLS": f"{m.get('DATA_CALLS_COUNT', 0)}회/{m.get('DATA_CALLS_TOTAL_MS', 0):.1f}ms",
                        "COMPUTE": f"{m.get('COMPUTE_CALLS_COUNT', 0)}회/{m.get('COMPUTE_CALLS_TOTAL_MS', 0):.1f}ms",
                    })
                
                if snapshot_data:
                    import pandas as pd
                    df_snapshots = pd.DataFrame(snapshot_data)
                    st.dataframe(df_snapshots, use_container_width=True, hide_index=True)
                
                # 스냅샷 관리 버튼
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📸 현재 스냅샷 저장", key=f"{key_prefix}_snapshot_save_btn"):
                        from datetime import datetime
                        label = f"수동: {datetime.now().strftime('%H:%M:%S')}"
                        snapshot_current_metrics(label)
                        st.success(f"스냅샷 저장: {label}")
                        st.rerun()
                with col2:
                    if st.button("🗑️ 스냅샷 초기화", key=f"{key_prefix}_snapshot_clear_btn"):
                        clear_perf_snapshots()
                        st.success("스냅샷 초기화됨")
                        st.rerun()
            else:
                st.caption("아직 스냅샷이 없습니다. 저장/삭제 버튼을 눌러보세요.")
            
            # QA 패널: Write 감사 로그
            st.write("**Write 감사 로그**")
            try:
                from src.utils.crud_guard import get_write_audit_log, clear_write_audit_log
                audit_log = get_write_audit_log()
                if audit_log:
                    st.caption(f"최근 {len(audit_log)}개 작업")
                    
                    # 로그를 표로 표시
                    import pandas as pd
                    audit_data = []
                    for entry in audit_log[-10:]:  # 최근 10개만 표시
                        status = "✅" if entry["ok"] else "❌"
                        audit_data.append({
                            "시간": entry["ts_kst"][11:19] if len(entry["ts_kst"]) > 19 else entry["ts_kst"],
                            "작업": entry["action"],
                            "상태": status,
                            "시간(ms)": f"{entry['ms']:.1f}ms",
                            "대상": ", ".join(entry["targets"]),
                            "에러": entry.get("error_type", "-") if not entry["ok"] else "-"
                        })
                    
                    if audit_data:
                        df_audit = pd.DataFrame(audit_data)
                        st.dataframe(df_audit, use_container_width=True, hide_index=True)
                    
                    if st.button("🗑️ 감사 로그 초기화", key=f"{key_prefix}_audit_log_clear_btn"):
                        clear_write_audit_log()
                        st.success("감사 로그 초기화됨")
                        st.rerun()
                else:
                    st.caption("아직 write 작업 기록이 없습니다. 저장/삭제 버튼을 눌러보세요.")
            except Exception as e:
                st.error("Write 감사 로그 로드 중 오류")
                if is_dev_mode():
                    st.exception(e)
            
            # 테마 토큰 미리보기 (검증용)
            st.write("**🎨 테마 토큰 미리보기**")
            st.caption("OS 테마에 따라 자동으로 전환됩니다. 브라우저/OS 테마를 변경해보세요.")
            st.markdown("""
            <div style="
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 0.5rem;
                margin-top: 0.5rem;
            ">
                <div style="
                    background: var(--ps-bg);
                    color: var(--ps-text);
                    padding: 0.5rem;
                    border-radius: 4px;
                    border: 1px solid var(--ps-border);
                    font-size: 0.75rem;
                ">
                    <strong>--ps-bg</strong><br>
                    <code style="font-size: 0.7rem;">배경</code>
                </div>
                <div style="
                    background: var(--ps-surface);
                    color: var(--ps-text);
                    padding: 0.5rem;
                    border-radius: 4px;
                    border: 1px solid var(--ps-border);
                    font-size: 0.75rem;
                ">
                    <strong>--ps-surface</strong><br>
                    <code style="font-size: 0.7rem;">표면</code>
                </div>
                <div style="
                    background: var(--ps-text);
                    color: var(--ps-bg);
                    padding: 0.5rem;
                    border-radius: 4px;
                    border: 1px solid var(--ps-border);
                    font-size: 0.75rem;
                ">
                    <strong>--ps-text</strong><br>
                    <code style="font-size: 0.7rem;">텍스트</code>
                </div>
                <div style="
                    background: var(--ps-muted);
                    color: var(--ps-bg);
                    padding: 0.5rem;
                    border-radius: 4px;
                    border: 1px solid var(--ps-border);
                    font-size: 0.75rem;
                ">
                    <strong>--ps-muted</strong><br>
                    <code style="font-size: 0.7rem;">보조 텍스트</code>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 표 data-testid 확인 가이드 (DEV 모드에서만)
            with st.expander("🔍 표 컴포넌트 data-testid 확인 가이드", expanded=False):
                st.caption("""
                **표가 테마 토큰이 적용되지 않을 때:**
                
                1. 브라우저 개발자도구(F12) 열기
                2. 요소 선택 도구(왼쪽 상단 아이콘) 클릭
                3. 문제가 있는 표를 클릭
                4. Elements 탭에서 해당 요소의 `data-testid` 속성 확인
                5. 확인된 `data-testid` 값을 알려주시면 CSS에 추가하겠습니다
                
                **현재 지원하는 testid:**
                - `stDataFrame` (기본 표)
                - `stTable` (간단한 표)
                - `stDataEditor` (엑셀 스타일 편집 가능 표)
                - `stArrowTable` (Arrow 기반 표)
                - `stAgGrid` (AgGrid 표)
                - 와일드카드: `*Table`, `*DataFrame`, `*DataEditor` (포괄 커버)
                """)
            
            # CSS 주입 확인 (워터마크 배지)
            st.write("**🎨 CSS 주입 확인**")
            st.caption("우측 하단에 'PS_THEME_V3' 배지가 보이면 CSS가 정상 주입된 것입니다.")
            st.info("""
            **워터마크 배지 확인:**
            - 우측 하단에 "PS_THEME_V3" 배지가 보이면 → CSS 주입 성공 ✅
            - 배지가 안 보이면 → CSS 주입 실패 또는 DEV 모드 비활성화 ❌
            - 배지는 `position: fixed`로 항상 같은 위치에 표시됩니다.
            """)
    except Exception as e:
        # 패널 내부 예외를 표시 (dev_mode에서만)
        try:
            from src.auth import is_dev_mode
            if is_dev_mode():
                st.error("DEV 패널 렌더 중 오류 발생")
                st.exception(e)
        except Exception:
            pass  # is_dev_mode도 실패하면 무시


def timed_db_call(call_name: str):
    """DB 호출 시간 측정 데코레이터"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start) * 1000
                record_db_call(call_name, duration_ms)
                return result
            except Exception as e:
                duration_ms = (time.perf_counter() - start) * 1000
                record_db_call(f"{call_name} (ERROR)", duration_ms)
                raise
        return wrapper
    return decorator


def record_data_call(name: str, ms: float, rows: int = None, source: str = None):
    """
    데이터 호출 기록 (페이지 렌더링 중 데이터 로드)
    
    Args:
        name: 호출 이름 (예: "load_csv(sales.csv)")
        ms: 소요 시간 (밀리초)
        rows: 반환된 행 수 (선택)
        source: 데이터 소스 (예: "supabase", "cache", "csv")
    """
    call_info = {
        "name": name,
        "ms": round(ms, 2),
        "rows": rows,
        "source": source,
        "timestamp": time.time()
    }
    _boot_perf_data["DATA_CALLS"].append(call_info)
    _boot_perf_data["DATA_CALLS_TOTAL_MS"] += ms
    _boot_perf_data["DATA_CALLS_COUNT"] += 1
    
    # 최대 100개까지만 유지 (메모리 관리)
    if len(_boot_perf_data["DATA_CALLS"]) > 100:
        removed = _boot_perf_data["DATA_CALLS"].pop(0)
        _boot_perf_data["DATA_CALLS_TOTAL_MS"] -= removed["ms"]


def get_data_calls_summary() -> Dict:
    """
    데이터 호출 요약 반환 (상위 10개, 시간 기준)
    
    Returns:
        dict: {
            "top_10": [...],  # 상위 10개
            "total_ms": float,
            "total_count": int
        }
    """
    calls = _boot_perf_data["DATA_CALLS"]
    # 시간 기준으로 정렬 (최신 순)
    sorted_calls = sorted(calls, key=lambda x: x["ms"], reverse=True)
    return {
        "top_10": sorted_calls[:10],
        "total_ms": _boot_perf_data["DATA_CALLS_TOTAL_MS"],
        "total_count": _boot_perf_data["DATA_CALLS_COUNT"]
    }


def clear_data_calls():
    """데이터 호출 기록 초기화 (페이지 변경 시 호출)"""
    _boot_perf_data["DATA_CALLS"] = []
    _boot_perf_data["DATA_CALLS_TOTAL_MS"] = 0.0
    _boot_perf_data["DATA_CALLS_COUNT"] = 0


def record_compute_call(name: str, ms: float, rows_in: int = None, rows_out: int = None, note: str = None):
    """
    계산/가공 호출 기록 (페이지 렌더링 중 데이터 처리)
    
    Args:
        name: 호출 이름 (예: "dashboard: sales_agg")
        ms: 소요 시간 (밀리초)
        rows_in: 입력 행 수 (선택)
        rows_out: 출력 행 수 (선택)
        note: 추가 메모 (선택)
    """
    call_info = {
        "name": name,
        "ms": round(ms, 2),
        "rows_in": rows_in,
        "rows_out": rows_out,
        "note": note,
        "timestamp": time.time()
    }
    _boot_perf_data["COMPUTE_CALLS"].append(call_info)
    _boot_perf_data["COMPUTE_CALLS_TOTAL_MS"] += ms
    _boot_perf_data["COMPUTE_CALLS_COUNT"] += 1
    
    # 최대 100개까지만 유지 (메모리 관리)
    if len(_boot_perf_data["COMPUTE_CALLS"]) > 100:
        removed = _boot_perf_data["COMPUTE_CALLS"].pop(0)
        _boot_perf_data["COMPUTE_CALLS_TOTAL_MS"] -= removed["ms"]


def get_compute_calls_summary() -> Dict:
    """
    계산 호출 요약 반환 (상위 10개, 시간 기준)
    
    Returns:
        dict: {
            "top_10": [...],  # 상위 10개
            "total_ms": float,
            "total_count": int
        }
    """
    calls = _boot_perf_data["COMPUTE_CALLS"]
    # 시간 기준으로 정렬 (최신 순)
    sorted_calls = sorted(calls, key=lambda x: x["ms"], reverse=True)
    return {
        "top_10": sorted_calls[:10],
        "total_ms": _boot_perf_data["COMPUTE_CALLS_TOTAL_MS"],
        "total_count": _boot_perf_data["COMPUTE_CALLS_COUNT"]
    }


def clear_compute_calls():
    """계산 호출 기록 초기화 (페이지 변경 시 호출)"""
    _boot_perf_data["COMPUTE_CALLS"] = []
    _boot_perf_data["COMPUTE_CALLS_TOTAL_MS"] = 0.0
    _boot_perf_data["COMPUTE_CALLS_COUNT"] = 0


def record_invalidation(reason: str, targets: List[str], mode: str = "soft"):
    """
    캐시 무효화 기록
    
    Args:
        reason: 무효화 이유
        targets: 무효화 대상 리스트
        mode: "soft" 또는 "hard"
    """
    _boot_perf_data["LAST_INVALIDATION"] = {
        "reason": reason,
        "targets": targets,
        "mode": mode,
        "timestamp": time.time()
    }


def snapshot_current_metrics(label: str):
    """
    현재 성능 지표를 스냅샷으로 저장
    
    Args:
        label: 스냅샷 라벨 (예: "S1: 앱 첫 실행", "S2: 대시보드 첫 진입")
    """
    global _perf_snapshots
    
    data = get_boot_perf_data()
    data_summary = get_data_calls_summary()
    compute_summary = get_compute_calls_summary()
    
    snapshot = {
        "label": label,
        "timestamp": time.time(),
        "metrics": {
            "IMPORT_TOTAL_MS": data.get("IMPORT_TOTAL_MS"),
            "BOOTSTRAP_TOTAL_MS": data.get("BOOTSTRAP_TOTAL_MS"),
            "BOOTSTRAP_DB_CALLS_COUNT": len(data.get("BOOTSTRAP_DB_CALLS", [])),
            "BOOTSTRAP_DB_TIME_MS": data.get("BOOTSTRAP_DB_TIME_MS", 0.0),
            "PAGE_IMPORT_MS": data.get("PAGE_IMPORT_MS"),
            "PAGE_RENDER_MS": data.get("PAGE_RENDER_MS"),
            "PAGE_TOTAL_MS": data.get("PAGE_TOTAL_MS"),
            "DATA_CALLS_COUNT": data_summary.get("total_count", 0),
            "DATA_CALLS_TOTAL_MS": data_summary.get("total_ms", 0.0),
            "COMPUTE_CALLS_COUNT": compute_summary.get("total_count", 0),
            "COMPUTE_CALLS_TOTAL_MS": compute_summary.get("total_ms", 0.0),
        },
        "last_invalidation": _boot_perf_data.get("LAST_INVALIDATION"),
    }
    
    _perf_snapshots.append(snapshot)
    
    # 최대 개수 제한
    if len(_perf_snapshots) > _MAX_SNAPSHOTS:
        _perf_snapshots = _perf_snapshots[-_MAX_SNAPSHOTS:]
    
    return snapshot


def get_perf_snapshots() -> List[Dict]:
    """저장된 성능 스냅샷 리스트 반환"""
    return _perf_snapshots.copy()


def clear_perf_snapshots():
    """성능 스냅샷 초기화"""
    global _perf_snapshots
    _perf_snapshots = []


@contextmanager
def perf_span(name: str, rows_in: Optional[int] = None, rows_out: Optional[int] = None, note: Optional[str] = None):
    """
    계산 구간 시간 측정 컨텍스트 매니저
    
    사용 예:
        with perf_span("dashboard: sales_agg", rows_in=len(df)):
            result = df.groupby('date').sum()
            # rows_out는 호출자가 별도로 기록해야 함
            record_compute_call(..., rows_out=len(result))
    
    또는 자동으로 rows_out을 기록하려면:
        with perf_span("dashboard: sales_agg", rows_in=len(df)) as span:
            result = df.groupby('date').sum()
            span.rows_out = len(result)  # 이렇게 설정하면 자동 기록
    
    Args:
        name: 호출 이름 (예: "dashboard: sales_agg")
        rows_in: 입력 행 수 (선택)
        rows_out: 출력 행 수 (선택, 컨텍스트 종료 시 자동 기록)
        note: 추가 메모 (선택)
    
    Yields:
        span 객체 (rows_out 속성 설정 가능)
    """
    start_time = time.perf_counter()
    span = type('Span', (), {'rows_out': rows_out})()  # 간단한 객체로 rows_out 저장
    
    try:
        yield span
    finally:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        # span.rows_out이 설정되었으면 사용, 아니면 원래 rows_out 사용
        final_rows_out = span.rows_out if hasattr(span, 'rows_out') and span.rows_out is not None else rows_out
        record_compute_call(name, elapsed_ms, rows_in=rows_in, rows_out=final_rows_out, note=note)


def render_boot_perf_sidebar():
    """
    사이드바에 부팅 성능 정보 표시 (dev_mode) - 호환성 유지 wrapper
    
    이 함수는 render_boot_perf_panel(st.sidebar)를 호출하는 wrapper입니다.
    기존 코드와의 호환성을 위해 유지됩니다.
    """
    import streamlit as st
    return render_boot_perf_panel(st.sidebar, key_prefix="sidebar")
