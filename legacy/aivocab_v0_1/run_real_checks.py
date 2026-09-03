#!/usr/bin/env python3
"""
Real-world readiness checks for Vocab_Agent.

Script ini mensimulasikan alur produksi:
- route input manusia / canonical / symbolic / numeric
- cek protocol semantic state (status + ack)
- cek keputusan tool/assistant
- jalankan eksekusi dalam mode dry-run (aman, tidak buka aplikasi nyata)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src import parser, bridge


def _case_ok(description: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    if detail:
        print(f"[{status}] {description} :: {detail}")
    else:
        print(f"[{status}] {description}")


def _check_route(
    orchestrator: bridge.VocabOrchestrator,
    *,
    description: str,
    input_payload: Any,
    expected_mode: Optional[str] = None,
    expected_status: Optional[str] = None,
    expect_confirmation: Optional[bool] = None,
) -> bool:
    route = orchestrator.route(input_payload, require_end=True)
    semantic = route.get("semantic_state", {}) or {}
    status = semantic.get("status")
    mode = route.get("mode")

    ok = True
    if expected_mode is not None and mode != expected_mode:
        ok = False
    if expected_status is not None and status != expected_status:
        ok = False
    if expect_confirmation is not None and route.get("requires_confirmation") != expect_confirmation:
        ok = False

    if route.get("protocol_version") != "TS/0.1":
        ok = False

    if ok and route.get("mode") == "assistant":
        if not route.get("answer"):
            ok = False

    detail_parts = [
        f"mode={mode}",
        f"status={status}",
        f"protocol={route.get('protocol_version')}",
        f"ack={len(semantic.get('ack', []))}",
        f"requires_confirmation={route.get('requires_confirmation', False)}",
    ]
    if route.get("mode") == "tool":
        details = ", ".join(detail_parts)
        exec_result = orchestrator.execute(route, dry_run=True, confirm=False)
        tool_status = (exec_result.get("results") or [{}])[0].get("status", "noop") if exec_result.get("results") else "noop"
        if exec_result.get("mode") != "tool":
            ok = False
            details += ", exec.mode=invalid"
        else:
            details += f", tool_status={tool_status}"
            if route.get("requires_confirmation") and tool_status != "deferred":
                ok = False
            if not route.get("requires_confirmation") and tool_status not in {"deferred", "executed", "failed"}:
                ok = False
    else:
        details = ", ".join(detail_parts)

    _case_ok(description, ok, details)
    return ok


def _check_parser_prompt(parser_input: str, expected_actions: List[str], expected_object: str) -> bool:
    parsed = parser.parse_human_instruction(parser_input, require_end=True)
    ok = (
        parsed.get("actions") == expected_actions
        and parsed.get("object") == expected_object
        and parsed.get("end") is True
    )
    _case_ok(
        "parser_human",
        ok,
        f"actions={parsed.get('actions')}, object={parsed.get('object')}, target={parsed.get('target')}",
    )
    return ok


def main() -> int:
    orchestrator = bridge.VocabOrchestrator()
    total_failed = 0

    print("=== Realistic bridge + parser checks ===")
    total_failed += 0 if _check_parser_prompt(
        "Jalankan Python lalu verifikasi error.",
        ["RUN", "VERIFY"],
        "PYTHON",
    ) else 1

    bridge_cases = [
        {
            "description": "notepad -> tool route + confirmation",
            "input_payload": "Tolong buka Windows Notepad",
            "expected_mode": "tool",
            "expected_status": "PARSED",
            "expect_confirmation": True,
        },
        {
            "description": "math sentence -> assistant final",
            "input_payload": "hitung satu tambah satu",
            "expected_mode": "assistant",
            "expected_status": "FINAL",
            "expect_confirmation": None,
        },
        {
            "description": "numeric command -> verified tool",
            "input_payload": "026 013 101 079 100",
            "expected_mode": "tool",
            "expected_status": "VERIFIED",
            "expect_confirmation": None,
        },
        {
            "description": "human language -> tool route",
            "input_payload": "Jalankan Python lalu verifikasi error.",
            "expected_mode": "tool",
            "expected_status": "VERIFIED",
            "expect_confirmation": False,
        },
        {
            "description": "canonical dict -> tool route",
            "input_payload": {
                "version": "0.1",
                "actions": ["RUN", "VERIFY"],
                "object": "PYTHON",
                "target": "ERROR",
                "end": True,
            },
            "expected_mode": "tool",
            "expected_status": "VERIFIED",
            "expect_confirmation": False,
        },
        {
            "description": "canonical verify pdf -> assistant final",
            "input_payload": {
                "version": "0.1",
                "actions": ["VERIFY"],
                "object": "PDF",
                "end": True,
            },
            "expected_mode": "assistant",
            "expected_status": "FINAL",
            "expect_confirmation": None,
        },
        {
            "description": "symbolic command -> parsed tool route",
            "input_payload": "VERIFY PDF ERROR END",
            "expected_mode": "assistant",
            "expected_status": "FINAL",
            "expect_confirmation": None,
        },
    ]

    for case in bridge_cases:
        ok = _check_route(orchestrator, **case)
        total_failed += 0 if ok else 1

    print(f"=== Result: total failed: {total_failed} ===")
    return total_failed


if __name__ == "__main__":
    raise SystemExit(main())
