#!/usr/bin/env python3
"""Context output guard — PostToolUse hook for Claude Code.

Checks tool output size after Bash, Read, and Grep calls.
Injects context warning when output exceeds thresholds.
Tracks violations for end-of-session audit.

Thresholds (configurable via env vars):
  CONTEXT_GUARD_WARN=5000     # bytes — soft warning (5kB, tuned for BA-kit files)
  CONTEXT_GUARD_CRITICAL=8000 # bytes — strong warning
  CONTEXT_GUARD_ENABLED=1     # set to 0 to disable

Usage (called by Claude Code PostToolUse hook):
  echo '{"tool_name":"Bash","tool_input":{...},"tool_response":"..."}' \
    | python3 context-output-guard.py --state-dir ~/.claude/ba-kit/state

Output (to stdout): context injection text (empty if under threshold, or warning message)
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


WARN_THRESHOLD = int(os.environ.get("CONTEXT_GUARD_WARN", 5000))
CRITICAL_THRESHOLD = int(os.environ.get("CONTEXT_GUARD_CRITICAL", 8000))
SESSION_BUDGET_WARN = int(os.environ.get("SESSION_BUDGET_WARN", 50000))
SESSION_BUDGET_CRITICAL = int(os.environ.get("SESSION_BUDGET_CRITICAL", 100000))
GUARD_TOOLS = frozenset({"Bash", "Read", "Grep", "Glob"})


def load_input() -> dict:
    raw = sys.stdin.read().strip()
    if not raw:
        # Try CLI args as fallback
        if len(sys.argv) > 1:
            raw = sys.argv[1]
        else:
            return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def tool_has_safe_flags(tool_name: str, tool_input: dict) -> bool:
    """Check if the tool call already uses output-limiting flags."""
    if tool_name == "Read":
        return "limit" in tool_input or "offset" in tool_input
    if tool_name == "Grep":
        return "head_limit" in tool_input or "offset" in tool_input
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        return any(f" {flag}" in command or f"|{flag}" in command for flag in ("head", "tail"))
    return False


def output_size_bytes(tool_response) -> int:
    """Get byte size of tool response regardless of type."""
    if isinstance(tool_response, str):
        return len(tool_response.encode("utf-8", errors="replace"))
    if isinstance(tool_response, (list, dict)):
        return len(json.dumps(tool_response, ensure_ascii=False).encode("utf-8"))
    if tool_response is None:
        return 0
    return len(str(tool_response).encode("utf-8", errors="replace"))


def estimate_tokens(byte_size: int) -> int:
    """Rough token estimate: ~4 chars per token for English text."""
    return max(1, byte_size // 4)


def read_violations(state_dir: Path) -> list:
    violations_file = state_dir / "context-violations.jsonl"
    if not violations_file.exists():
        return []
    violations = []
    for line in violations_file.read_text(encoding="utf-8").strip().split("\n"):
        if line:
            try:
                violations.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return violations


def write_violation(state_dir: Path, entry: dict) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    violations_file = state_dir / "context-violations.jsonl"
    with violations_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def emit_warning(level: str, tool_name: str, kb_size: float, token_est: int,
                 hint: str, repeat_count: int) -> str:
    """Build the context injection warning message."""
    if level == "critical":
        prefix = "CONTEXT_GUARD_CRITICAL"
        action = "STRONGLY RECOMMEND filtering output next time."
    else:
        prefix = "CONTEXT_GUARD_WARN"
        action = "Consider filtering output next time."

    repeat_note = ""
    if repeat_count > 1:
        repeat_note = f"\n[REPEAT #{repeat_count} in this session] "
        repeat_note += "Each unfiltered large output wastes context across ALL subsequent turns."

    return (
        f"\n{prefix}: {tool_name} returned {kb_size:.1f}kB (~{token_est} tokens). "
        f"{action}{repeat_note}\n"
        f"Hint: {hint}\n"
        f"Threshold: warn={WARN_THRESHOLD // 1000}kB, critical={CRITICAL_THRESHOLD // 1000}kB.\n"
    )


def get_hint(tool_name: str, tool_input: dict) -> str:
    """Generate a specific hint for the tool that was misused."""
    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        if cmd.startswith("find ") or "find " in cmd:
            return (
                "Use Glob tool instead of 'find' for file search. "
                "If you must use find, pipe through 'head -20'."
            )
        if "cat " in cmd:
            return "Use Read tool instead of 'cat'. Read supports offset + limit for large files."
        if "ls " in cmd:
            return "Use Glob tool instead of 'ls' for file listing. Pipe through head if listing dirs."
        return "Pipe through head/tail when output may be large. Use Glob instead of find/ls."
    if tool_name == "Read":
        path = tool_input.get("file_path", "")
        return (
            f"File may be large. Use offset+limit to read specific sections. "
            f"First read the TOC/frontmatter, then target specific line ranges."
        )
    if tool_name == "Grep":
        return "Use head_limit to cap results. Use output_mode=files_with_matches first, then content with head_limit."
    if tool_name == "Glob":
        pattern = tool_input.get("pattern", "")
        if "**/*" in pattern and "." not in pattern.rsplit("/", 1)[-1]:
            return (
                "Broad Glob detected. Use narrower patterns (e.g., *.md, **/index.md) "
                "or limit to specific subdirectories. For file discovery, prefer rg --files | head."
            )
        return "Use exact paths or narrower patterns to keep Glob output small."
    return "Filter output to keep context lean."


def read_session_budget(state_dir: Path) -> int:
    """Read cumulative session budget in bytes."""
    budget_file = state_dir / "context-session-budget.txt"
    if not budget_file.exists():
        return 0
    try:
        return int(budget_file.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return 0


def update_session_budget(state_dir: Path, byte_size: int) -> int:
    """Add byte_size to the session budget. Returns new total."""
    state_dir.mkdir(parents=True, exist_ok=True)
    current = read_session_budget(state_dir)
    new_total = current + byte_size
    budget_file = state_dir / "context-session-budget.txt"
    budget_file.write_text(str(new_total), encoding="utf-8")
    return new_total


def emit_budget_warning(total_bytes: int) -> str:
    """Build a session budget warning message."""
    total_kb = total_bytes / 1024.0
    total_tok = total_bytes // 4
    if total_bytes > SESSION_BUDGET_CRITICAL:
        return (
            f"CONTEXT_GUARD_BUDGET_CRITICAL: session context budget EXCEEDED "
            f"({total_kb:.0f}KB, ~{total_tok} tok). "
            f"Use offset+limit or bounded patterns on all remaining tools."
        )
    return (
        f"CONTEXT_GUARD_BUDGET_WARN: session context budget {total_kb:.0f}KB used "
        f"(~{total_tok} tok). Subsequent unbounded output will be flagged."
    )


def main() -> int:
    enabled = os.environ.get("CONTEXT_GUARD_ENABLED", "1")
    if enabled in ("0", "false", "no"):
        return 0

    data = load_input()
    if not data:
        return 0

    tool_name = data.get("tool_name", "")
    if tool_name not in GUARD_TOOLS:
        return 0

    tool_input = data.get("tool_input", {})
    if not isinstance(tool_input, dict):
        tool_input = {}

    # Skip if tool already uses safe filtering flags
    if tool_has_safe_flags(tool_name, tool_input):
        return 0

    tool_response = data.get("tool_response", "")
    size = output_size_bytes(tool_response)

    # ── Session budget tracking (runs for ALL non-safe tools) ──
    state_dir = Path(os.environ.get(
        "CONTEXT_GUARD_STATE_DIR",
        os.path.join(os.path.expanduser("~"), ".claude", "ba-kit", "state")
    ))
    budget_total = update_session_budget(state_dir, size)
    budget_msg = ""
    if budget_total > SESSION_BUDGET_WARN:
        budget_msg = emit_budget_warning(budget_total)

    if size <= WARN_THRESHOLD and not budget_msg:
        return 0

    kb_size = size / 1024.0
    token_est = estimate_tokens(size)
    hint = get_hint(tool_name, tool_input)

    # Determine level
    if size > CRITICAL_THRESHOLD:
        level = "critical"
    else:
        level = "warn"

    # Track violation
    violation = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "tool_name": tool_name,
        "size_bytes": size,
        "estimated_tokens": token_est,
        "tool_input_summary": (
            tool_input.get("command", "")
            or tool_input.get("file_path", "")
            or tool_input.get("pattern", "")
        )[:200],
    }
    write_violation(state_dir, violation)

    # Count repeats
    violations = read_violations(state_dir)
    repeat_count = sum(
        1 for v in violations
        if v.get("tool_name") == tool_name and v.get("level") == level
    )

    # Emit per-tool warning (only if size exceeds WARN threshold)
    if size > WARN_THRESHOLD:
        print(emit_warning(level, tool_name, kb_size, token_est, hint, repeat_count))

    # Emit budget warning if cumulative budget exceeded
    if budget_msg:
        print(budget_msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
