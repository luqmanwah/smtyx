#!/usr/bin/env python3
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
for raw in (ROOT/'benchmarks/conformance_cases.jsonl').read_text(encoding='utf-8').splitlines():
    if not raw.strip():
        continue
    case = json.loads(raw)
    print(json.dumps({
        "case_id": case["case_id"],
        "state": {"intent":"", "object":"", "status":"", "confidence":0.0, "permissions":[], "payload":{}},
        "decision":""
    }, ensure_ascii=False))
