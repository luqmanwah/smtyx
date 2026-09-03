from __future__ import annotations

import ast
import json
import operator
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from . import decoder, embedder, encoder, executor, parser, policy, semantic_protocol, validator

VERSION = parser.VERSION

BASE_DIR = Path(__file__).resolve().parent

_MATH_NUMBERS = {
    "NOL": 0,
    "SATU": 1,
    "DUA": 2,
    "TIGA": 3,
    "EMPAT": 4,
    "LIMA": 5,
    "ENAM": 6,
    "TUJUH": 7,
    "DELAPAN": 8,
    "SEMBILAN": 9,
    "SEPULUH": 10,
    "SEBELAS": 11,
    "DUA BELAS": 12,
    "TIGA BELAS": 13,
    "EMPAT BELAS": 14,
    "LIMA BELAS": 15,
    "ENAM BELAS": 16,
    "TUJUH BELAS": 17,
    "DELAPAN BELAS": 18,
    "SEMBILAN BELAS": 19,
    "DUA PULUH": 20,
}

_MATH_OPS = {
    "TAMBAH": "+",
    "PLUS": "+",
    "PERTAMBAHAN": "+",
    "KURANG": "-",
    "MINUS": "-",
    "KALI": "*",
    "X": "*",
    "PERKALIAN": "*",
    "BAGI": "/",
    "BAGIAN": "/",
    "DIBAGI": "/",
    "PANGKAT": "**",
    "PANGKATKAN": "**",
}

_MATH_STOPWORDS = {"TOLONG", "HITUNG", "HITUNGAN", "BERAPA", "BERAPA?", "SAMA", "SEBENTAR", "KALIAN"}


def _coerce_result(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return str(value)


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError("Only numeric constants are supported")
    if hasattr(ast, "Num") and isinstance(node, ast.Num):  # Python compatibility
        return float(node.n)
    if isinstance(node, ast.BinOp):
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            if right == 0:
                raise ZeroDivisionError("division by zero")
            return left / right
        if isinstance(node.op, ast.Pow):
            return operator.pow(left, right)
        raise ValueError("Unsupported arithmetic operator")
    if isinstance(node, ast.UnaryOp):
        val = _safe_eval(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +val
        if isinstance(node.op, ast.USub):
            return -val
        raise ValueError("Unsupported unary operator")
    raise ValueError("Unsupported expression node")


def _evaluate_math(prompt: str) -> Optional[str]:
    normalized = prompt.upper()
    normalized = normalized.replace("**", " ** ")
    for op in "+-*/()":
        normalized = normalized.replace(op, f" {op} ")
    tokens = normalized.split()

    expr_tokens: List[str] = []
    for token in tokens:
        if token in _MATH_STOPWORDS:
            continue
        if token in _MATH_OPS:
            expr_tokens.append(_MATH_OPS[token])
            continue
        if token.isdigit():
            expr_tokens.append(str(int(token)))
            continue
        if token in _MATH_NUMBERS:
            expr_tokens.append(str(_MATH_NUMBERS[token]))
            continue
        if token == "X":
            expr_tokens.append("*")
            continue
        if token in {"+", "-", "*", "/", "(", ")"}:
            expr_tokens.append(token)
            continue
        if token == "**":
            expr_tokens.append("**")
            continue

    expr = " ".join([token for token in expr_tokens if token and token != " "]).strip()
    if not expr or not any(op in expr for op in ["+", "-", "*", "/", "**"]):
        return None
    if not re.fullmatch(r"[0-9+\-*/().\s\*]+", expr):
        return None
    if len(expr_tokens) > 25:
        return None

    try:
        tree = ast.parse(expr, mode="eval")
        result = _safe_eval(tree)
    except (SyntaxError, ValueError, ZeroDivisionError):
        return None

    return _coerce_result(result)


@dataclass(frozen=True)
class ToolCall:
    tool: str
    action: str
    command: str
    rationale: str
    arguments: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class VocabToolRule:
    def __init__(self, rule: Dict[str, Any]):
        self.id = str(rule.get("id", ""))
        self.name = str(rule.get("name", self.id))
        self.priority = int(rule.get("priority", 0))
        self.match_spec = rule.get("match", {}) or {}
        self.tool = rule.get("tool", {}) or {}
        self.requires_confirmation = bool(rule.get("requires_confirmation", False))
        self.execution_mode = str(rule.get("execution_mode", "deferred"))
        self.description = str(rule.get("description", ""))

    def _match_raw(self, raw: str) -> int:
        score = 0
        raw_contains = self.match_spec.get("raw_contains", [])
        for item in raw_contains:
            if str(item).upper() in raw:
                score += 1
        for item in self.match_spec.get("raw_contains_any", []):
            if str(item).upper() in raw:
                score += 1
        for item in self.match_spec.get("raw_regex", []):
            try:
                if re.search(str(item), raw, re.IGNORECASE):
                    score += 1
            except re.error:
                continue
        return score

    def _match_symbolic(self, canonical: Dict[str, Any]) -> int:
        score = 0
        match_actions = [a.upper() for a in self.match_spec.get("actions", [])]
        match_objects = [o.upper() for o in self.match_spec.get("objects", [])]

        canonical_actions = [str(action).upper() for action in canonical.get("actions", [])]
        canonical_object = str(canonical.get("object", "")).upper() if canonical.get("object") else ""
        canonical_target = str(canonical.get("target", "")).upper() if canonical.get("target") else ""
        canonical_destination = str(canonical.get("destination", "")).upper() if canonical.get("destination") else ""

        if match_actions:
            if any(action in canonical_actions for action in match_actions):
                score += 1
            else:
                return 0

        if match_objects:
            if any(obj in {canonical_object, canonical_target, canonical_destination} for obj in match_objects):
                score += 1
            else:
                return 0

        return score

    def _action_filter_passes(self, canonical: Dict[str, Any]) -> bool:
        """When a rule declares match.actions, the canonical action list
        must intersect it for the rule to be eligible at all. This applies
        globally (not just to the symbolic score) so that a raw-text hit
        (e.g. the word "file" or a path pattern) can't select a rule whose
        declared action scope doesn't cover the actual requested action
        (e.g. selecting a read-only rule for a DELETE instruction)."""
        match_actions = [a.upper() for a in self.match_spec.get("actions", [])]
        if not match_actions:
            return True
        canonical_actions = [str(action).upper() for action in canonical.get("actions", [])]
        return any(action in canonical_actions for action in match_actions)

    def match(self, raw: str, canonical: Dict[str, Any]) -> int:
        if not self._action_filter_passes(canonical):
            return 0
        raw_score = self._match_raw(raw)
        symbolic_score = self._match_symbolic(canonical)
        if raw_score == 0 and symbolic_score == 0:
            return 0
        return raw_score + symbolic_score

    def to_tool_call(self, canonical: Dict[str, Any], *, include_symbolic: bool = True) -> Dict[str, Any]:
        tool_name = str(self.tool.get("name", self.name))
        command = str(self.tool.get("command", ""))
        args = {
            "tool_rule_id": self.id,
            "canonical": canonical,
            "execution_mode": self.execution_mode,
            "description": self.description,
            "symbolic": None,
            "numeric": None,
        }
        if include_symbolic:
            try:
                args["symbolic"] = encoder.encode_symbolic(canonical)
                args["numeric"] = encoder.encode_numeric(canonical)
            except Exception:
                args["symbolic"] = None
                args["numeric"] = None
        args["requires_confirmation"] = self.requires_confirmation
        return ToolCall(
            tool=tool_name,
            action=self.id,
            command=command,
            rationale=self.description,
            arguments=args,
        ).to_dict()


class VocabOrchestrator:
    def __init__(
        self,
        config_path: Optional[Path | str] = None,
        *,
        execution_dry_run: bool = True,
        execution_timeout_seconds: int = 20,
        execution_log_path: Optional[Path | str] = None,
        audit_log_path: Optional[Path | str] = None,
    ):
        self.config_path = config_path
        self.audit_log_path = Path(audit_log_path) if audit_log_path else None
        loaded = policy.load_bridge_config(config_path)
        self.config = loaded
        self.policy = loaded.get("policy", {})
        self.language_objects = set((loaded.get("language_objects", [])))
        self.tool_rules = [VocabToolRule(rule) for rule in loaded.get("tool_rules", [])]
        self.tool_rules.sort(key=lambda r: r.priority, reverse=True)
        self._executor = executor.ToolExecutor(
            dry_run_default=execution_dry_run,
            timeout_seconds=execution_timeout_seconds,
            log_path=execution_log_path,
        )

    def _append_audit(self, record: Dict[str, Any]) -> None:
        if self.audit_log_path is None:
            return
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            **record,
        }
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        existing = self.audit_log_path.read_text(encoding="utf-8") if self.audit_log_path.exists() else ""
        self.audit_log_path.write_text(
            existing + json.dumps(entry, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def _looks_like_json_object(self, text: str) -> bool:
        t = (text or "").strip()
        return len(t) >= 2 and t[0] == "{" and t[-1] == "}"

    def _looks_structured_payload(self, text: str) -> bool:
        if not text:
            return False
        if re.fullmatch(r"(?:\d{3}(?:\s+\d{3})+|\d{3})(?:\s+)?", text):
            return True
        if re.fullmatch(r"[A-Z0-9#\-\s]+", text) and not re.search(r"[a-z]", text):
            return True
        return False

    def _parse_payload(self, prompt: str, vocab_path: Optional[Path | str] = None, require_end: bool = False) -> Tuple[Dict[str, Any], str]:
        upper_prompt = prompt.upper().strip()
        if self._looks_structured_payload(upper_prompt):
            canonical = decoder.decode_to_canonical(prompt, vocab_path=vocab_path, require_end=require_end)
            if not canonical.get("errors"):
                return canonical, "symbolic_or_numeric"

        return (
            parser.parse_human_instruction(
                prompt,
                vocab_path=vocab_path,
                require_end=require_end,
                include_end=True,
            ),
            "human",
        )

    def _parse_route_input(
        self,
        prompt_or_payload: Union[str, Dict[str, Any]],
        vocab_path: Optional[Path | str],
        require_end: bool,
    ) -> Tuple[Dict[str, Any], str, str]:
        if isinstance(prompt_or_payload, dict):
            canonical = dict(prompt_or_payload)
            if "version" not in canonical:
                canonical["version"] = VERSION
            return canonical, "canonical_dict", ""

        prompt = str(prompt_or_payload).strip()
        if self._looks_like_json_object(prompt):
            try:
                loaded = json.loads(prompt)
                if isinstance(loaded, dict):
                    canonical = dict(loaded)
                    if "version" not in canonical:
                        canonical["version"] = VERSION
                    return canonical, "canonical_json", ""
            except json.JSONDecodeError:
                pass

        canonical, parsed_from = self._parse_payload(prompt, vocab_path=vocab_path, require_end=require_end)
        return canonical, parsed_from, prompt

    def _validate(self, canonical: Dict[str, Any], vocab_path: Optional[Path | str] = None, require_end: bool = False) -> Dict[str, Any]:
        return validator.validate_canonical(
            canonical,
            vocab_path=vocab_path,
            policy_config=self.policy,
            require_end=require_end,
            version=VERSION,
        )

    def _resolve_tool_calls(self, raw: str, canonical: Dict[str, Any]) -> List[Dict[str, Any]]:
        upper_raw = raw.upper()
        scored: List[tuple[int, VocabToolRule]] = []
        for rule in self.tool_rules:
            score = rule.match(upper_raw, canonical)
            if score:
                scored.append((score, rule))
        if not scored:
            return []

        scored.sort(key=lambda item: (item[0], item[1].priority), reverse=True)
        _, best_rule = scored[0]
        return [best_rule.to_tool_call(canonical)]

    def _fallback_decision_for_complex(self, canonical: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        actions = [str(a).upper() for a in canonical.get("actions", [])]
        object_token = str(canonical.get("object", "")).upper()
        if object_token in self.language_objects and len(actions) > 1:
            return {
                "tool": "analysis_agent",
                "action": "fallback_orchestrator",
                "command": "analysis_orchestration",
                "rationale": "Complex language instruction routed through orchestrator fallback.",
                "arguments": {
                    "symbolic": None,
                    "numeric": None,
                    "canonical": canonical,
                },
            }
        return None

    def _vectorize(self, canonical: Dict[str, Any], *, embed_vector_size: int = 64) -> List[float] | None:
        try:
            return embedder.canonical_to_vector(
                canonical,
                max_vector_size=embed_vector_size,
            )
        except Exception:
            return None

    @staticmethod
    def _protocol_source_from_mode(input_mode: str) -> str:
        if input_mode == "canonical_dict":
            return "canonical"
        if input_mode == "canonical_json":
            return "canonical_json"
        if input_mode == "symbolic_or_numeric":
            return "symbolic"
        if input_mode == "math":
            return "math"
        return "human"

    def _attach_semantic_state(
        self,
        result: Dict[str, Any],
        *,
        canonical: Dict[str, Any],
        input_mode: str,
        raw_input: str,
        validation: Dict[str, Any],
        requires_confirmation: bool = False,
    ) -> Dict[str, Any]:
        protocol_state = semantic_protocol.enrich_canonical_state(
            canonical,
            source_kind=self._protocol_source_from_mode(input_mode),
            source_id="user_input",
            source_adapter="bridge",
            route_mode=result.get("mode", "assistant"),
            needs_confirmation=requires_confirmation,
            validation=validation,
            raw_input=raw_input,
        )
        result["semantic_state"] = protocol_state
        result["ack"] = protocol_state.get("ack", [])
        result["protocol_version"] = protocol_state.get("protocol_version")
        return result

    def route(
        self,
        prompt_or_payload: Union[str, Dict[str, Any]],
        *,
        vocab_path: Optional[Path | str] = None,
        require_end: bool = False,
        confirm_override: bool = False,
        embed_vector_size: int = 64,
    ) -> Dict[str, Any]:
        input_payload = prompt_or_payload
        if not isinstance(prompt_or_payload, (str, dict)):
            input_payload = ""

        if isinstance(input_payload, str):
            prompt = input_payload.strip()
        else:
            prompt = json.dumps(input_payload, sort_keys=True) if input_payload else ""

        def finalize(result: Dict[str, Any]) -> Dict[str, Any]:
            result.setdefault("input_mode", "unknown")
            canonical = result.get("canonical")
            if isinstance(canonical, dict):
                self._attach_semantic_state(
                    result,
                    canonical=canonical,
                    input_mode=result.get("input_mode", "unknown"),
                    raw_input=prompt,
                    validation=result.get("validation") or {
                        "valid": False,
                        "errors": [{"code": "NO_VALIDATION", "value": None}],
                        "warnings": [],
                    },
                    requires_confirmation=result.get("requires_confirmation", False),
                )
            self._append_audit({
                "prompt": prompt if isinstance(input_payload, str) else json.dumps(input_payload, sort_keys=True),
                "mode": result.get("mode"),
                "requires_confirmation": result.get("requires_confirmation", False),
                "tool_calls": result.get("tool_calls", []),
                "canonical": result.get("canonical"),
                "validation": result.get("validation"),
                "symbolic": result.get("symbolic"),
                "numeric": result.get("numeric"),
                "input_mode": result.get("input_mode"),
                "embedding": result.get("embedding"),
                "semantic_state": result.get("semantic_state"),
                "protocol_version": result.get("protocol_version"),
                "ack": result.get("ack"),
            })
            return result

        if not prompt:
            return finalize({
                "mode": "assistant",
                "answer": "Input is empty.",
                "tool_calls": [],
                "canonical": None,
                "validation": {"valid": False, "errors": [{"code": "EMPTY_PROMPT", "value": ""}], "warnings": []},
                "symbolic": None,
                "numeric": None,
                "input_mode": "empty",
                "embedding": None,
            })

        math_result = _evaluate_math(prompt)
        if math_result is not None and not isinstance(input_payload, dict):
            canonical = {
                "version": VERSION,
                "actions": ["CALCULATE"],
                "object": "DATA",
                "target": None,
                "state": None,
                "priority": None,
                "confidence": None,
                "destination": None,
                "end": bool(require_end),
                "errors": [],
            }
            symbolic = encoder.encode_symbolic(canonical)
            numeric = encoder.encode_numeric(canonical)
            return finalize({
                "mode": "assistant",
                "answer": math_result,
                "tool_calls": [],
                "canonical": canonical,
                "validation": {"valid": True, "errors": [], "warnings": []},
                "symbolic": symbolic,
                "numeric": numeric,
                "input_mode": "math",
                "embedding": self._vectorize(canonical, embed_vector_size=embed_vector_size),
            })

        canonical, input_mode, parse_probe = self._parse_route_input(
            prompt_or_payload=input_payload,
            vocab_path=vocab_path,
            require_end=require_end,
        )
        validation = self._validate(canonical, vocab_path=vocab_path, require_end=require_end)

        if not parse_probe and input_mode.startswith("canonical_"):
            try:
                parse_probe = encoder.encode_symbolic(canonical, vocab_path=vocab_path)
            except Exception:
                parse_probe = ""

        tool_calls = self._resolve_tool_calls(parse_probe, canonical)
        if not tool_calls:
            fallback = self._fallback_decision_for_complex(canonical)
            if fallback:
                tool_calls = [fallback]

        # Safety net: if the canonical action is flagged in
        # policy.confirm_required_actions but no tool_rule claimed it (e.g.
        # a DELETE with no dedicated delete rule configured), do not let it
        # fall through to a silent "assistant / no tool needed" response.
        # Surface it as a held tool route requiring explicit confirmation
        # instead of pretending nothing risky was requested.
        if not tool_calls:
            confirm_required_actions = {
                str(a).upper() for a in self.policy.get("confirm_required_actions", [])
            }
            canonical_actions = {str(a).upper() for a in canonical.get("actions", [])}
            if confirm_required_actions & canonical_actions:
                tool_calls = [{
                    "tool": "unrouted_risky_action",
                    "action": "unrouted_risky_action",
                    "command": "hold_for_review",
                    "rationale": (
                        "Action requires confirmation per policy but no tool_rule "
                        "is configured to handle it; holding for manual review "
                        "instead of silently treating it as no-op."
                    ),
                    "arguments": {
                        "canonical": canonical,
                        "execution_mode": "deferred",
                        "requires_confirmation": True,
                        "confirmation_reason": "policy.confirm_required_actions (unrouted)",
                    },
                }]

        try:
            symbolic = encoder.encode_symbolic(canonical, vocab_path=vocab_path)
            numeric = encoder.encode_numeric(canonical, vocab_path=vocab_path)
        except Exception:
            symbolic = None
            numeric = None
        embedding = self._vectorize(canonical, embed_vector_size=embed_vector_size)

        if tool_calls:
            requires_confirmation = any(call.get("arguments", {}).get("requires_confirmation", False) for call in tool_calls)

            # Policy-level safety net: regardless of which tool_rule matched,
            # any canonical action listed in policy.confirm_required_actions
            # must force confirmation. This closes a gap where a rule with
            # requires_confirmation=false (e.g. a read-only file rule) could
            # still be selected via raw-text matching for a risky action
            # (e.g. DELETE) whose symbolic match had actually failed.
            confirm_required_actions = {
                str(a).upper() for a in self.policy.get("confirm_required_actions", [])
            }
            canonical_actions = {str(a).upper() for a in canonical.get("actions", [])}
            policy_forces_confirmation = bool(confirm_required_actions & canonical_actions)
            if policy_forces_confirmation and not requires_confirmation:
                requires_confirmation = True
                for call in tool_calls:
                    call.setdefault("arguments", {})["requires_confirmation"] = True
                    call["arguments"]["confirmation_reason"] = "policy.confirm_required_actions"

            if requires_confirmation and not confirm_override:
                answer = (
                    "Tool route terdeteksi dan memerlukan konfirmasi eksplisit sebelum eksekusi, "
                    "mode saat ini tetap menghasilkan rencana eksekusi."
                )
            else:
                answer = "Tool route terdeteksi dan direncanakan untuk eksekusi adapter terkendali."
            return finalize({
                "mode": "tool",
                "answer": answer,
                "tool_calls": tool_calls,
                "canonical": canonical,
                "validation": validation,
                "symbolic": symbolic,
                "numeric": numeric,
                "input_mode": input_mode,
                "embedding": embedding,
                "requires_confirmation": requires_confirmation and not confirm_override,
            })

        if not validation["valid"]:
            return finalize({
                "mode": "assistant",
                "answer": "Input tidak bisa di-decode menjadi kanonikal yang aman.",
                "tool_calls": [],
                "canonical": canonical,
                "validation": validation,
                "symbolic": symbolic,
                "numeric": numeric,
                "input_mode": input_mode,
                "embedding": embedding,
            })

        return finalize({
            "mode": "assistant",
            "answer": "Permintaan dipahami, tetapi tidak memerlukan eksekusi alat tambahan.",
            "tool_calls": [],
            "canonical": canonical,
            "validation": validation,
            "symbolic": symbolic,
            "numeric": numeric,
            "input_mode": input_mode,
            "embedding": embedding,
        })

    def execute(
        self,
        prompt_or_route: Union[str, Dict[str, Any]],
        *,
        require_end: bool = False,
        confirm: bool = False,
        dry_run: Optional[bool] = None,
        **route_kwargs: Any,
    ) -> Dict[str, Any]:
        if isinstance(prompt_or_route, dict) and "mode" in prompt_or_route and "tool_calls" in prompt_or_route:
            route = dict(prompt_or_route)
        elif isinstance(prompt_or_route, (str, dict)):
            route = self.route(prompt_or_route, require_end=require_end, **route_kwargs)
        else:
            route = {
                "mode": "assistant",
                "answer": "Input type not supported.",
                "tool_calls": [],
                "canonical": None,
                "validation": {
                    "valid": False,
                    "errors": [{"code": "UNSUPPORTED_INPUT", "value": str(type(prompt_or_route))}],
                    "warnings": [],
                },
                "symbolic": None,
                "numeric": None,
                "input_mode": "unsupported",
                "embedding": None,
            }
        return self._executor.execute(route, confirm=confirm, dry_run=dry_run)


__all__ = ["ToolCall", "VocabToolRule", "VocabOrchestrator"]
