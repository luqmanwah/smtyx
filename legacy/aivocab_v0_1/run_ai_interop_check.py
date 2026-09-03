#!/usr/bin/env python3
"""
AI-to-AI interoperability checker for Vocab_Agent.

Flow:
- AI-A (front) routes prompt/canonical/symbolic/numeric into canonical + protocol state.
- AI-B (back) consumes symbolic and canonical payloads from AI-A.
- Each hop is validated for protocol consistency and optionally preview-dry-run tool execution.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from src.bridge import VocabOrchestrator


Payload = Union[str, Dict[str, Any]]


@dataclass
class Scenario:
    label: str
    input_payload: Payload
    expected_mode: Optional[str] = None
    expected_status: Optional[str] = None
    expect_confirmation: Optional[bool] = None
    strict_issue: Optional[str] = None


def _norm_mode(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    v = str(value).strip().lower()
    if not v:
        return None
    if v not in {"assistant", "tool"}:
        raise ValueError(f"invalid mode expectation: {value!r}")
    return v


def _norm_status(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    v = str(value).strip().upper()
    if not v:
        return None
    if v not in {"PARSED", "VERIFIED", "FINAL"}:
        raise ValueError(f"invalid status expectation: {value!r}")
    return v


def _norm_bool(value: Any) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        low = value.strip().lower()
        if low in {"true", "1", "yes", "y", "on"}:
            return True
        if low in {"false", "0", "no", "n", "off"}:
            return False
    raise ValueError(f"invalid boolean expectation: {value!r}")


def _check_route(route: Dict[str, Any], scenario: Scenario) -> Tuple[bool, str]:
    protocol = route.get("protocol_version")
    semantic = route.get("semantic_state", {}) or {}
    mode = route.get("mode")
    status = semantic.get("status")
    requires_confirmation = bool(route.get("requires_confirmation", False))

    detail = [
        f"mode={mode}",
        f"status={status}",
        f"protocol={protocol}",
        f"requires_confirmation={requires_confirmation}",
        f"ack={len(semantic.get('ack', []))}",
    ]

    ok = protocol == "TS/0.1"
    if scenario.expected_mode is not None:
        ok &= mode == scenario.expected_mode
    if scenario.expected_status is not None:
        ok &= status == scenario.expected_status
    if scenario.expect_confirmation is not None:
        ok &= requires_confirmation == scenario.expect_confirmation

    return ok, ", ".join(detail)


def _run_tool_execute_preview(orchestrator: VocabOrchestrator, route: Dict[str, Any]) -> Tuple[bool, str]:
    execution = orchestrator.execute(route, confirm=False, dry_run=True)
    results = execution.get("results") or []
    if not results:
        return False, "no execution results"

    first = results[0]
    status = str(first.get("status"))
    requires_confirmation = bool(first.get("requires_confirmation", False))
    if route.get("requires_confirmation", False):
        if status != "deferred":
            return False, f"expected deferred when confirmation required, got {status}"
        return True, f"tool_status={status} (expected for confirmation-required)"

    if status not in {"deferred", "executed", "failed"}:
        return False, f"unexpected tool_status={status}"
    return True, f"tool_status={status}"


def _print_case_result(case_id: int, label: str, ok: bool, detail: str) -> bool:
    prefix = "PASS" if ok else "FAIL"
    print(f"[{prefix}] #{case_id:02d} {label} :: {detail}")
    return ok


def _append_case_record(
    records: List[Dict[str, Any]],
    case_id: int,
    stage: str,
    ok: bool,
    detail: str,
    scenario: Scenario,
    extra: Optional[Dict[str, Any]] = None,
) -> bool:
    record = {
        "case_id": case_id,
        "stage": stage,
        "label": scenario.label,
        "ok": bool(ok),
        "detail": detail,
        "expected_mode": scenario.expected_mode,
        "expected_status": scenario.expected_status,
        "expected_confirmation": scenario.expect_confirmation,
        "strict_issue": scenario.strict_issue,
    }
    if extra:
        record.update(extra)
    records.append(record)
    return _print_case_result(case_id, stage.replace("_", " "), ok, detail)


def _run_one_case(
    case_id: int,
    scenario: Scenario,
    ai_front: VocabOrchestrator,
    ai_back: VocabOrchestrator,
    *,
    dry_run_preview: bool = True,
    verbose_records: Optional[List[Dict[str, Any]]] = None,
) -> int:
    failed = 0
    records: List[Dict[str, Any]] = verbose_records if verbose_records is not None else []

    if scenario.strict_issue:
        _append_case_record(
            records,
            case_id,
            "expectation check",
            False,
            f"strict check failed: {scenario.strict_issue}",
            scenario,
            {"hop": "strict", "input": scenario.input_payload},
        )
        return 1

    route_front = ai_front.route(scenario.input_payload, require_end=True)
    ok_front, detail_front = _check_route(route_front, scenario)
    _append_case_record(
        records,
        case_id,
        "AI_A route",
        ok_front,
        detail_front,
        scenario,
        {
            "hop": "A",
            "input": scenario.input_payload,
            "route": route_front,
        },
    )
    if not ok_front:
        failed += 1

    symbolic = route_front.get("symbolic")
    canonical = route_front.get("canonical")

    if isinstance(symbolic, str) and symbolic.strip():
        route_back_sym = ai_back.route(symbolic, require_end=True)
        ok_back_sym, detail_sym = _check_route(route_back_sym, scenario)
        ok_passed = _append_case_record(
            records,
            case_id,
            "AI_B route via symbolic",
            ok_back_sym,
            detail_sym + " | payload=symbolic",
            scenario,
            {
                "hop": "B-symbolic",
                "input": symbolic,
                "route": route_back_sym,
            },
        )
        if not ok_passed:
            failed += 1
            return failed
        if route_back_sym.get("mode") == "tool" and dry_run_preview:
            ok_exec, detail_exec = _run_tool_execute_preview(ai_back, route_back_sym)
            if not _append_case_record(
                records,
                case_id,
                "AI_B tool dry-run via symbolic",
                ok_exec,
                detail_exec,
                scenario,
                {
                    "hop": "B-symbolic",
                    "execution": ai_back.execute(route_back_sym, confirm=False, dry_run=True),
                },
            ):
                failed += 1
                return failed
    else:
        if not _append_case_record(
            records,
            case_id,
            "AI_B route via symbolic",
            False,
            "symbolic unavailable",
            scenario,
        ):
            failed += 1

    if isinstance(canonical, dict):
        route_back_canon = ai_back.route(canonical, require_end=True)
        ok_back_can, detail_can = _check_route(route_back_canon, scenario)
        ok_passed = _append_case_record(
            records,
            case_id,
            "AI_B route via canonical",
            ok_back_can,
            detail_can + " | payload=canonical",
            scenario,
            {
                "hop": "B-canonical",
                "input": canonical,
                "route": route_back_canon,
            },
        )
        if not ok_passed:
            failed += 1
            return failed
        if route_back_canon.get("mode") == "tool" and dry_run_preview:
            ok_exec, detail_exec = _run_tool_execute_preview(ai_back, route_back_canon)
            if not _append_case_record(
                records,
                case_id,
                "AI_B tool dry-run via canonical",
                ok_exec,
                detail_exec,
                scenario,
                {
                    "hop": "B-canonical",
                    "execution": ai_back.execute(route_back_canon, confirm=False, dry_run=True),
                },
            ):
                failed += 1
    else:
        if not _append_case_record(
            records,
            case_id,
            "AI_B route via canonical",
            False,
            "canonical unavailable",
            scenario,
        ):
            failed += 1

    return failed


def _collect_strict_issue(
    scenario: Scenario,
    *,
    strict_mode: bool,
) -> Optional[str]:
    if not strict_mode:
        return None
    missing: List[str] = []
    if scenario.expected_mode is None:
        missing.append("expected_mode")
    if scenario.expected_status is None:
        missing.append("expected_status")
    if scenario.expect_confirmation is None:
        missing.append("expect_confirmation")
    if not missing:
        return None
    return "missing " + ", ".join(missing)


def _label_matches(patterns: Optional[Sequence[str]], value: str, *, exclude: bool = False) -> bool:
    if not patterns:
        return not exclude
    return any(re.search(pattern, value, re.IGNORECASE) for pattern in patterns)


def _apply_case_filters(
    scenarios: Sequence[Scenario],
    *,
    include_patterns: Optional[Sequence[str]] = None,
    exclude_patterns: Optional[Sequence[str]] = None,
) -> List[Scenario]:
    filtered: List[Scenario] = []
    for scenario in scenarios:
        label = scenario.label
        if include_patterns and not _label_matches(include_patterns, label):
            continue
        if _label_matches(exclude_patterns, label, exclude=True):
            continue
        filtered.append(scenario)
    return filtered


def _validate_regex_patterns(patterns: Optional[Sequence[str]], field_name: str) -> None:
    for raw in patterns or []:
        try:
            re.compile(raw)
        except re.error as exc:
            raise ValueError(f"Invalid {field_name} regex: {raw!r} ({exc})")


def _normalize_custom_entry(
    raw: Any,
    *,
    default_label: str,
    default_mode: Optional[str],
    default_status: Optional[str],
    default_confirmation: Optional[bool],
) -> Scenario:
    if isinstance(raw, str):
        payload = raw
        label = default_label
        expected_mode = default_mode
        expected_status = default_status
        expect_confirmation = default_confirmation
    elif isinstance(raw, dict):
        keys = raw
        if "label" in keys and keys["label"]:
            label = str(keys["label"])
        elif "name" in keys and keys["name"]:
            label = str(keys["name"])
        elif "human_instruction" in keys and keys["human_instruction"]:
            label = str(keys["human_instruction"])
        elif "input" in keys and isinstance(keys["input"], str) and keys["input"].strip():
            label = str(keys["input"]).strip()
        else:
            label = default_label

        if "input_payload" in keys:
            payload = keys["input_payload"]
        elif "payload" in keys:
            payload = keys["payload"]
        elif "input" in keys:
            payload = keys["input"]
        elif "canonical" in keys and isinstance(keys["canonical"], dict):
            payload = keys["canonical"]
        else:
            # assume raw dict is canonical payload
            payload = keys

        expected_mode = _norm_mode(keys.get("expected_mode", keys.get("mode", default_mode)))
        expected_status = _norm_status(keys.get("expected_status", keys.get("status", default_status)))
        expect_confirmation = _norm_bool(
            keys.get(
                "expect_confirmation",
                keys.get("expected_confirmation", keys.get("confirmation_required", default_confirmation)),
            )
        )
        if expect_confirmation is None:
            expect_confirmation = default_confirmation
    else:
        raise ValueError(f"Unsupported custom entry type: {type(raw)!r}")

    if not isinstance(payload, (str, dict)):
        raise ValueError(f"Unsupported payload type in custom entry: {type(payload)!r}")

    return Scenario(
        label=label,
        input_payload=payload,
        expected_mode=expected_mode,
        expected_status=expected_status,
        expect_confirmation=expect_confirmation,
    )


def _load_json_inputs(path: Path) -> List[Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        if "cases" in raw and isinstance(raw["cases"], list):
            return raw["cases"]
        return [raw]
    raise ValueError(f"Unsupported JSON structure in {path}: {type(raw)!r}")


def _strip_quotes(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    v = value.strip()
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    return value


def _build_default_scenarios() -> Sequence[Scenario]:
    return [
        Scenario(
            label="jalankan python lalu verifikasi",
            input_payload="Jalankan Python lalu verifikasi error.",
            expected_mode="tool",
            expected_status="VERIFIED",
            expect_confirmation=False,
        ),
        Scenario(
            label="buka windows notepad (confirmation)",
            input_payload="Tolong buka Windows Notepad",
            expected_mode="tool",
            expected_status="PARSED",
            expect_confirmation=True,
        ),
        Scenario(
            label="hitung sederhana",
            input_payload="hitung satu tambah satu",
            expected_mode="assistant",
            expected_status="FINAL",
            expect_confirmation=False,
        ),
        Scenario(
            label="symbolic direct numeric",
            input_payload="026 013 101 079 100",
            expected_mode="tool",
            expected_status="VERIFIED",
            expect_confirmation=False,
        ),
        Scenario(
            label="canonical direct",
            input_payload={
                "version": "0.1",
                "actions": ["RUN", "VERIFY"],
                "object": "PYTHON",
                "target": "ERROR",
                "end": True,
            },
            expected_mode="tool",
            expected_status="VERIFIED",
            expect_confirmation=False,
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AI interoperability check for Vocab_Agent",
    )
    parser.add_argument(
        "--input",
        action="append",
        help="Custom prompt/custom payload to validate. Can be repeated.",
    )
    parser.add_argument(
        "--expect-mode",
        dest="expect_mode",
        help="Expected mode for CLI custom checks. Options: assistant|tool.",
    )
    parser.add_argument(
        "--expect-status",
        dest="expect_status",
        help="Expected semantic status for CLI custom checks. Options: PARSED|VERIFIED|FINAL.",
    )
    parser.add_argument(
        "--expect-confirmation",
        dest="expect_confirmation",
        choices=["true", "false"],
        help="Expected confirmation flag for CLI custom checks.",
    )
    parser.add_argument(
        "--input-json",
        action="append",
        help="Custom JSON payload (stringified) to validate. Can be repeated.",
    )
    parser.add_argument(
        "--jsonl",
        action="append",
        help="Path to JSONL file containing custom payloads. Can be repeated.",
    )
    parser.add_argument(
        "--json",
        action="append",
        help="Path to JSON file containing custom payloads (list/object or {\"cases\": [...]}) . Can be repeated.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--output",
        help="Path to write JSON report when --format json.",
    )
    parser.add_argument(
        "--no-dry-run",
        action="store_true",
        help="Skip dry-run execution preview.",
    )
    parser.add_argument(
        "--case-label",
        action="append",
        help="Include only cases with label matching this regex (case-insensitive). Can be repeated.",
    )
    parser.add_argument(
        "--skip-case-label",
        action="append",
        help="Skip cases with label matching this regex (case-insensitive). Can be repeated.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Require explicit expectations (mode/status/confirmation) for each scenario.",
    )
    parser.add_argument(
        "--max-failures",
        type=int,
        default=None,
        help="Stop when failed cases reaches this number.",
    )
    args = parser.parse_args()

    if args.max_failures is not None and args.max_failures < 1:
        parser.error("--max-failures must be >= 1")

    try:
        _validate_regex_patterns(args.case_label, "--case-label")
        _validate_regex_patterns(args.skip_case_label, "--skip-case-label")
    except ValueError as exc:
        raise SystemExit(str(exc))

    expect_mode = _norm_mode(args.expect_mode)
    expect_status = _norm_status(args.expect_status)
    expect_confirmation = _norm_bool(args.expect_confirmation)

    scenarios: List[Scenario] = list(_build_default_scenarios())
    custom_scenarios: List[Scenario] = []

    # CLI prompts (as strings)
    for idx, raw_input in enumerate(args.input or [], start=1):
        inp = _strip_quotes(raw_input)
        if inp is None:
            continue
        custom_scenarios.append(
            Scenario(
                label=f"CLI input {idx}",
                input_payload=inp,
                expected_mode=expect_mode,
                expected_status=expect_status,
                expect_confirmation=expect_confirmation,
            )
        )

    # Inline JSON objects
    for idx, raw_json in enumerate(args.input_json or [], start=1):
        parsed = json.loads(raw_json)
        custom_scenarios.append(
            _normalize_custom_entry(
                parsed,
                default_label=f"CLI JSON {idx}",
                default_mode=expect_mode,
                default_status=expect_status,
                default_confirmation=expect_confirmation,
            )
        )

    # JSON file entries
    for path_idx, path_raw in enumerate(args.json or [], start=1):
        path = Path(_strip_quotes(path_raw))
        for item in _load_json_inputs(path):
            custom_scenarios.append(
                _normalize_custom_entry(
                    item,
                    default_label=f"JSON {path_idx}",
                    default_mode=expect_mode,
                    default_status=expect_status,
                    default_confirmation=expect_confirmation,
                )
            )

    # JSONL file entries
    for path_idx, path_raw in enumerate(args.jsonl or [], start=1):
        path = Path(_strip_quotes(path_raw))
        for line_idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            parsed = json.loads(line)
            custom_scenarios.append(
                _normalize_custom_entry(
                    parsed,
                    default_label=f"JSONL {path_idx}:{line_idx}",
                    default_mode=expect_mode,
                    default_status=expect_status,
                    default_confirmation=expect_confirmation,
                )
            )

    if custom_scenarios:
        scenarios = custom_scenarios

    if args.strict:
        for scenario in scenarios:
            scenario.strict_issue = _collect_strict_issue(scenario, strict_mode=True)

    scenarios = _apply_case_filters(
        scenarios,
        include_patterns=args.case_label,
        exclude_patterns=args.skip_case_label,
    )
    if not scenarios:
        print("No scenarios matched selected filters.")
        return 1

    ai_a = VocabOrchestrator()
    ai_b = VocabOrchestrator()

    print("=== AI Interop Protocol Check ===")
    total_failed = 0
    cases_run = 0
    case_records: List[Dict[str, Any]] = []
    max_failures = args.max_failures
    for i, scenario in enumerate(scenarios, start=1):
        cases_run += 1
        total_failed += _run_one_case(
            i,
            scenario,
            ai_a,
            ai_b,
            dry_run_preview=not args.no_dry_run,
            verbose_records=case_records,
        )

        if max_failures is not None and total_failed >= max_failures:
            print(f"=== Stop early: max_failures={max_failures} ===")
            break

    result = {
        "status": "PASS" if total_failed == 0 else "FAIL",
        "total_failed": total_failed,
        "cases_count": len(scenarios),
        "cases_run": cases_run,
        "max_failures": max_failures,
        "strict": bool(args.strict),
        "case_filters": {
            "include": args.case_label or [],
            "exclude": args.skip_case_label or [],
        },
        "format": args.format,
        "scenarios": [
            {"label": s.label, "input_type": "dict" if isinstance(s.input_payload, dict) else "str"}
            for s in scenarios
        ],
        "records": case_records,
    }

    if args.format == "json":
        output = json.dumps(result, ensure_ascii=False, indent=2)
        if args.output:
            Path(args.output).write_text(output + "\n", encoding="utf-8")
        print(output)
    else:
        print(f"=== Result: total failed: {total_failed} ===")

    return total_failed


if __name__ == "__main__":
    raise SystemExit(main())
