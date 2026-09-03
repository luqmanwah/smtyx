from __future__ import annotations

import json
import platform
import re
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional


SAFE_POWER_TOOLS = {
    "powershell": {
        "notepad": {"fragments": ["start-process notepad"], "requires_confirmation": True},
        "notepad_executor": {"fragments": ["start notepad"], "requires_confirmation": True},
    },
}

MOCK_TOOL_COMMANDS = {"run_language_job", "analyze_or_fix", "delegate_to_llm", "list_path"}


@dataclass(frozen=True)
class ToolExecutionResult:
    tool: str
    action: str
    status: str
    command: str
    rationale: str
    exit_code: Optional[int]
    stdout: str
    stderr: str
    requires_confirmation: bool
    confirmation_used: bool
    dry_run: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ToolExecutor:
    def __init__(self, *, dry_run_default: bool = True, timeout_seconds: int = 20, log_path: Optional[Path | str] = None):
        self.dry_run_default = dry_run_default
        self.timeout_seconds = timeout_seconds
        self.log_path = Path(log_path) if log_path else None

    def _is_windows(self) -> bool:
        return platform.system().lower().startswith("win")

    def _normalize_command(self, command: str) -> str:
        return " ".join(str(command).strip().lower().split())

    def _has_disallowed_characters(self, command: str) -> bool:
        return any(ch in command for ch in (";", "&", "|", "`", "$(", "<", ">"))

    def _is_command_allowlisted(self, tool: str, command: str) -> bool:
        normalized = self._normalize_command(command)
        allowed = SAFE_POWER_TOOLS.get(tool.lower(), {})
        for spec in allowed.values():
            for fragment in spec.get("fragments", []):
                if normalized.startswith(fragment):
                    return True
        return False

    def execute_tool_call(
        self,
        tool_call: Dict[str, Any],
        *,
        confirm: bool = False,
        dry_run: Optional[bool] = None,
    ) -> ToolExecutionResult:
        tool = str(tool_call.get("tool", ""))
        action = str(tool_call.get("action", ""))
        command = str(tool_call.get("command", ""))
        arguments = tool_call.get("arguments", {}) if isinstance(tool_call, dict) else {}
        requires_confirmation = bool(arguments.get("requires_confirmation", False))
        should_dry_run = self.dry_run_default if dry_run is None else bool(dry_run)

        if self._has_disallowed_characters(command):
            return ToolExecutionResult(
                tool=tool,
                action=action,
                status="blocked",
                command=command,
                rationale="Command contains blocked shell metacharacter.",
                exit_code=None,
                stdout="",
                stderr="blocked by command policy",
                requires_confirmation=requires_confirmation,
                confirmation_used=False,
                dry_run=True,
            )

        if requires_confirmation and not confirm:
            return ToolExecutionResult(
                tool=tool,
                action=action,
                status="deferred",
                command=command,
                rationale="Tool call requires explicit confirmation before real execution.",
                exit_code=None,
                stdout="",
                stderr="",
                requires_confirmation=True,
                confirmation_used=False,
                dry_run=True,
            )

        if command in {"", "none"}:
            return ToolExecutionResult(
                tool=tool,
                action=action,
                status="blocked",
                command=command,
                rationale="Tool command missing.",
                exit_code=None,
                stdout="",
                stderr="no command defined",
                requires_confirmation=requires_confirmation,
                confirmation_used=False,
                dry_run=True,
            )

        if command in MOCK_TOOL_COMMANDS:
            return ToolExecutionResult(
                tool=tool,
                action=action,
                status="deferred",
                command=command,
                rationale="Command routed to adapter-only action; execution intentionally not implemented in this phase.",
                exit_code=None,
                stdout="",
                stderr="",
                requires_confirmation=requires_confirmation,
                confirmation_used=confirm,
                dry_run=should_dry_run,
            )

        if should_dry_run:
            return ToolExecutionResult(
                tool=tool,
                action=action,
                status="deferred",
                command=command,
                rationale="Dry-run enabled; command not executed.",
                exit_code=None,
                stdout="",
                stderr="",
                requires_confirmation=requires_confirmation,
                confirmation_used=confirm,
                dry_run=True,
            )

        if tool.lower() == "powershell" and self._is_windows():
            if not self._is_command_allowlisted(tool, command):
                return ToolExecutionResult(
                    tool=tool,
                    action=action,
                    status="blocked",
                    command=command,
                    rationale="Command not in allowlist.",
                    exit_code=None,
                    stdout="",
                    stderr="command blocked",
                    requires_confirmation=requires_confirmation,
                    confirmation_used=confirm,
                    dry_run=False,
                )
            completed = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            return ToolExecutionResult(
                tool=tool,
                action=action,
                status="executed" if completed.returncode == 0 else "failed",
                command=command,
                rationale="Executed via powershell." if completed.returncode == 0 else "Powershell returned non-zero code.",
                exit_code=completed.returncode,
                stdout=(completed.stdout or "").strip(),
                stderr=(completed.stderr or "").strip(),
                requires_confirmation=requires_confirmation,
                confirmation_used=confirm,
                dry_run=False,
            )

        return ToolExecutionResult(
            tool=tool,
            action=action,
            status="blocked",
            command=command,
            rationale="Tool execution only supported on Windows for this binding.",
            exit_code=None,
            stdout="",
            stderr="unsupported runtime",
            requires_confirmation=requires_confirmation,
            confirmation_used=confirm,
            dry_run=False,
        )

    def execute_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]],
        *,
        confirm: bool = False,
        dry_run: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        return [
            self.execute_tool_call(tool_call, confirm=confirm, dry_run=dry_run).to_dict()
            for tool_call in tool_calls
        ]

    def execute(self, route_output: Dict[str, Any], *, confirm: bool = False, dry_run: Optional[bool] = None) -> Dict[str, Any]:
        mode = route_output.get("mode", "assistant")
        if mode != "tool":
            return {
                "mode": mode,
                "executed": False,
                "results": [],
                "reason": "No executable tool route requested.",
            }

        tool_calls = route_output.get("tool_calls", []) or []
        if not tool_calls:
            return {
                "mode": "tool",
                "executed": False,
                "results": [],
                "reason": "No tool_calls returned by route.",
            }

        results = self.execute_tool_calls(tool_calls, confirm=confirm, dry_run=dry_run)
        return {
            "mode": "tool",
            "executed": any(item.get("status") in {"executed", "failed"} for item in results),
            "results": results,
        }

    def audit_results(self, route_output: Dict[str, Any], output_path: Optional[Path | str] = None) -> str:
        path = Path(output_path) if output_path else self.log_path
        if not path:
            raise ValueError("No log path configured")

        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"route": route_output}
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return str(path)


__all__ = [
    "ToolExecutionResult",
    "ToolExecutor",
]
