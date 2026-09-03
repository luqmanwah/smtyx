#!/usr/bin/env python3
"""
Quick smoke test utility for Vocab_Agent.

Tujuan:
- validasi cepat jalur manusia -> canonical -> symbolic -> numeric -> decode balik
- validasi interoperability_cases yang terkait bahasa pemrograman
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from src import parser, encoder, decoder
from src.bridge import VocabOrchestrator


ROOT_DIR = Path(__file__).resolve().parent
VOCAB_PATH = ROOT_DIR / "vocab" / "core_vocab.json"
INTEROP_PATH = ROOT_DIR / "examples" / "interoperability_cases.jsonl"


def _subset_ok(actual: Dict[str, Any], expected: Dict[str, Any]) -> bool:
    return all(actual.get(key) == value for key, value in expected.items())


def _print_result(ok: bool, idx: int, label: str, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    if detail:
        print(f"[{status}] #{idx:02d} {label} :: {detail}")
    else:
        print(f"[{status}] #{idx:02d} {label}")


def run_manual_smoke(manual_cases: List[Dict[str, Any]]) -> int:
    failed = 0
    for idx, case in enumerate(manual_cases, start=1):
        expected = case["expected"]
        parsed = parser.parse_human_instruction(
            case["human_instruction"],
            vocab_path=VOCAB_PATH,
            require_end=True,
        )
        ok = _subset_ok(parsed, expected)
        detail = ""
        if not ok:
            failed += 1
            detail = f"parsed={parsed}"

        try:
            symbolic = encoder.encode_symbolic(parsed, vocab_path=VOCAB_PATH)
            numeric = encoder.encode_numeric(parsed, vocab_path=VOCAB_PATH)
            recovered_symbolic = decoder.decode_to_canonical(symbolic, vocab_path=VOCAB_PATH, require_end=True)
            recovered_numeric = decoder.decode_to_canonical(numeric, vocab_path=VOCAB_PATH, require_end=True)
            roundtrip_ok = _subset_ok(recovered_symbolic, expected) and _subset_ok(recovered_numeric, expected)
            if not roundtrip_ok:
                failed += 1
                detail = detail or "roundtrip mismatch"
                _print_result(False, idx, case["human_instruction"], detail=f"symbolic={symbolic}, numeric={numeric}")
                continue
        except Exception as exc:
            failed += 1
            detail = str(exc)
            _print_result(False, idx, case["human_instruction"], detail=detail)
            continue

        if ok:
            _print_result(True, idx, case["human_instruction"], detail=f"symbolic={symbolic}, numeric={numeric}")
        else:
            _print_result(False, idx, case["human_instruction"], detail=detail)

    return failed


def run_interop_smoke(limit: int = 10) -> int:
    failed = 0
    lines = [
        json.loads(line)
        for line in INTEROP_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    language_names = {
        "PYTHON", "JAVASCRIPT", "TYPESCRIPT", "JAVA", "CSHARP", "CPP",
        "GO", "RUST", "PHP", "SQL", "R", "KOTLIN", "SWIFT", "RUBY",
    }
    language_cases = []
    for case in lines:
        expected = case.get("expected_canonical_state", {})
        obj = expected.get("object")
        dst = expected.get("destination")
        if obj in language_names or dst in language_names:
            language_cases.append(case)
        if len(language_cases) >= limit:
            break

    for idx, case in enumerate(language_cases, start=1):
        symbolic = case["symbolic_vocab"]
        numeric = case["numeric_vocab"]
        expected = case["expected_canonical_state"]

        symbolic_canonical = decoder.decode_to_canonical(symbolic, vocab_path=VOCAB_PATH, require_end=True)
        numeric_canonical = decoder.decode_to_canonical(numeric, vocab_path=VOCAB_PATH, require_end=True)

        ok_symbolic = _subset_ok(symbolic_canonical, expected)
        ok_numeric = _subset_ok(numeric_canonical, expected)
        if ok_symbolic and ok_numeric:
            _print_result(True, idx, case["human_instruction"])
            continue

        failed += 1
        detail = f"symbolic={symbolic_canonical}, numeric={numeric_canonical}, expected={expected}"
        _print_result(False, idx, case["human_instruction"], detail=detail)

    return failed


def main() -> int:
    manual_cases = [
        {
            "human_instruction": "Jalankan Python lalu verifikasi error.",
            "expected": {
                "actions": ["RUN", "VERIFY"],
                "object": "PYTHON",
                "target": "ERROR",
                "end": True,
            },
        },
        {
            "human_instruction": "Analisis JavaScript lalu bandingkan dan verifikasi.",
            "expected": {
                "actions": ["ANALYZE", "COMPARE", "VERIFY"],
                "object": "JAVASCRIPT",
                "end": True,
            },
        },
        {
            "human_instruction": "Jalankan Go lalu kirim ke model dan verifikasi.",
            "expected": {
                "actions": ["RUN", "SEND", "VERIFY"],
                "object": "GO",
                "destination": "MODEL",
                "end": True,
            },
        },
        {
            "human_instruction": "Perbaiki TypeScript lalu verifikasi.",
            "expected": {
                "actions": ["FIX", "VERIFY"],
                "object": "TYPESCRIPT",
                "end": True,
            },
        },
        {
            "human_instruction": "Jalankan Java lalu cek error.",
            "expected": {
                "actions": ["RUN", "CHECK"],
                "object": "JAVA",
                "target": "ERROR",
                "end": True,
            },
        },
        {
            "human_instruction": "Analisis Ruby, perbaiki, lalu verifikasi.",
            "expected": {
                "actions": ["ANALYZE", "FIX", "VERIFY"],
                "object": "RUBY",
                "end": True,
            },
        },
        {
            "human_instruction": "Konversi SQL lalu verifikasi.",
            "expected": {
                "actions": ["CONVERT", "VERIFY"],
                "object": "SQL",
                "end": True,
            },
        },
        {
            "human_instruction": "Validasi Rust dan kirim ke model.",
            "expected": {
                "actions": ["VALIDATE", "SEND"],
                "object": "RUST",
                "destination": "MODEL",
                "end": True,
            },
        },
        {
            "human_instruction": "Jalankan PHP lalu periksa error.",
            "expected": {
                "actions": ["RUN", "CHECK"],
                "object": "PHP",
                "target": "ERROR",
                "end": True,
            },
        },
        {
            "human_instruction": "Verifikasi C++ error.",
            "expected": {
                "actions": ["VERIFY"],
                "object": "CPP",
                "target": "ERROR",
                "end": True,
            },
        },
    ]

    print("=== Manual Human Smoke ===")
    manual_fail = run_manual_smoke(manual_cases)

    print("=== Interop Language Smoke ===")
    interop_fail = run_interop_smoke(limit=10)

    bridge = VocabOrchestrator()
    print("=== Bridge Smoke ===")
    bridge_cases = [
        {"prompt": "Tolong buka Windows Notepad", "expect_mode": "tool"},
        {"prompt": "hitung satu tambah satu", "expect_mode": "assistant"},
        {"prompt": "026 013 101 079 100", "expect_mode": "tool"},
        {"prompt": "Jalankan Python lalu verifikasi error.", "expect_mode": "tool"},
        {"prompt": '{"version":"0.1","actions":["RUN","VERIFY"],"object":"PYTHON","target":"ERROR","end":true}', "expect_mode": "tool"},
        {"prompt": '{"version":"0.1","actions":["VERIFY"],"object":"PDF","end":true}', "expect_mode": "assistant"},
    ]
    bridge_fail = 0
    for idx, case in enumerate(bridge_cases, start=1):
        result = bridge.route(case["prompt"])
        ok = result.get("mode") == case["expect_mode"]
        proto = result.get("semantic_state", {})
        status = proto.get("status", "-")
        if ok:
            if result.get("mode") == "tool":
                execution = bridge.execute(result, dry_run=True, confirm=False)
                status = "dry-run" if execution.get("results") else "noop"
                print(
                    f"[PASS] #{idx} {case['prompt']} => "
                    f"{result.get('mode')} ({status}) | protocol={proto.get('protocol_version')} "
                    f"state={proto.get('status')} ack={len(proto.get('ack', []))}"
                )
            else:
                print(
                    f"[PASS] #{idx} {case['prompt']} => "
                    f"{result.get('mode')} | protocol={proto.get('protocol_version')} "
                    f"state={proto.get('status')}"
                )
        else:
            bridge_fail += 1
            print(f"[FAIL] #{idx} {case['prompt']} => {result}")

    total = manual_fail + interop_fail
    total += bridge_fail
    print(
        f"=== Result: {10 - manual_fail} manual passed, {10 - interop_fail} interop passed, "
        f"{len(bridge_cases) - bridge_fail} bridge passed, total failed: {total} ==="
    )
    return total


if __name__ == "__main__":
    raise SystemExit(main())
