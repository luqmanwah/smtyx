#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "benchmarks" / "conformance_cases.jsonl"


def load_jsonl(path: Path):
    out = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            out.append(json.loads(raw))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSONL at {path}:{lineno}: {exc}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Score AI outputs against SMTYX conformance cases")
    ap.add_argument("answers", type=Path, help="JSONL file produced by the tested AI")
    args = ap.parse_args()

    oracle = {x["case_id"]: x for x in load_jsonl(CASES)}
    answers = {x.get("case_id"): x for x in load_jsonl(args.answers)}

    total_fields = 0
    passed_fields = 0
    details = []
    for case_id, case in oracle.items():
        answer = answers.get(case_id)
        expected = dict(case["expected"])
        if "expected_payload" in case:
            expected["payload"] = case["expected_payload"]
        row = {"case_id": case_id, "passed": 0, "total": 0, "errors": []}
        state = (answer or {}).get("state", {}) if isinstance(answer, dict) else {}
        for key, value in expected.items():
            if key == "payload":
                for pkey, pvalue in value.items():
                    row["total"] += 1; total_fields += 1
                    if isinstance(state.get("payload"), dict) and state["payload"].get(pkey) == pvalue:
                        row["passed"] += 1; passed_fields += 1
                    else:
                        row["errors"].append(f"payload.{pkey}: expected {pvalue!r}, got {(state.get('payload') or {}).get(pkey)!r}")
                continue
            row["total"] += 1; total_fields += 1
            actual = state.get(key)
            if key == "permissions":
                ok = sorted(actual or []) == sorted(value)
            else:
                ok = actual == value
            if ok:
                row["passed"] += 1; passed_fields += 1
            else:
                row["errors"].append(f"{key}: expected {value!r}, got {actual!r}")
        details.append(row)

    score = 100.0 * passed_fields / total_fields if total_fields else 0.0
    print(f"SMTYX conformance score: {passed_fields}/{total_fields} fields = {score:.1f}%")
    print(f"Cases supplied: {len(answers)}/{len(oracle)}")
    for row in details:
        if row["errors"]:
            print(f"- {row['case_id']}: {row['passed']}/{row['total']} :: " + "; ".join(row["errors"]))
    return 0 if passed_fields == total_fields else 1


if __name__ == "__main__":
    raise SystemExit(main())
