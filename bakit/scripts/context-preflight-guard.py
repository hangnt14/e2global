#!/usr/bin/env python3
"""Context preflight guard — PreToolUse hook for Claude Code.

Checks file size BEFORE Read tool executes, tracking reads to detect re-reads.
Blocks oversized reads that lack offset+limit. Warns on borderline sizes or re-reads.

Thresholds (configurable via env vars):
  CONTEXT_PREFLIGHT_WARN=5000       # bytes — warn on Read without limit
  CONTEXT_PREFLIGHT_BLOCK=10000     # bytes — BLOCK Read if no offset+limit
  CONTEXT_PREFLIGHT_ENABLED=1       # set to 0 to disable
  CONTEXT_PREFLIGHT_REREAD_WARN=1   # set to 0 to disable re-read warnings

Usage (called by Claude Code PreToolUse hook):
  echo '{"tool_name":"Read","tool_input":{"file_path":"/path/to/file"}}' \
    | python3 context-preflight-guard.py

Exit codes:
  0 — proceed (file size ok, or safe flags present, or warn-only)
  1 — BLOCK (file too large, no offset+limit). Stdout has explanation.
  2 — non-Read tool — silently exit 0 (not our concern)
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


WARN_THRESHOLD = int(os.environ.get("CONTEXT_PREFLIGHT_WARN", 5000))
BLOCK_THRESHOLD = int(os.environ.get("CONTEXT_PREFLIGHT_BLOCK", 10000))
STATE_DIR = Path(os.environ.get(
    "CONTEXT_GUARD_STATE_DIR",
    os.path.join(os.path.expanduser("~"), ".claude", "ba-kit", "state")
))
READS_MANIFEST = STATE_DIR / "context-reads-manifest.jsonl"


def load_input() -> dict:
    raw = sys.stdin.read().strip()
    if not raw:
        if len(sys.argv) > 1:
            raw = sys.argv[1]
        else:
            return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def has_safe_flags(tool_input: dict, file_size: int = 0) -> bool:
    """Read with limit is always safe. offset alone is safe only for small files."""
    has_limit = "limit" in tool_input
    has_offset = "offset" in tool_input
    if has_limit:
        return True
    if has_offset and file_size < BLOCK_THRESHOLD:
        return True
    return False


def file_size_bytes(file_path: str) -> int:
    """Get file size from disk. Returns -1 if file doesn't exist or can't be read."""
    try:
        return Path(file_path).stat().st_size
    except (OSError, PermissionError):
        return -1


def read_manifest() -> list:
    """Read the reads manifest (JSONL). Returns list of read entries."""
    if not READS_MANIFEST.exists():
        return []
    content = READS_MANIFEST.read_text(encoding="utf-8").strip()
    if not content:
        return []
    entries = []
    for line in content.split("\n"):
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return entries


def track_read(file_path: str, size_bytes: int, had_safe_flags: bool) -> None:
    """Record a file read in the manifest for re-read detection."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "file_path": str(Path(file_path).resolve()),
        "size_bytes": size_bytes,
        "had_safe_flags": had_safe_flags,
    }
    with READS_MANIFEST.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def find_prior_reads(file_path: str) -> list:
    """Find all prior reads of the same file in this session."""
    resolved = str(Path(file_path).resolve())
    manifest = read_manifest()
    return [
        e for e in manifest
        if e.get("file_path") == resolved
    ]


def build_reread_warning(prior_count: int, file_path: str) -> str:
    """Build a warning about re-reading the same file."""
    return (
        f"\nCONTEXT_GUARD_REREAD: {Path(file_path).name} has been read "
        f"{prior_count + 1} times in this session. "
        f"Re-reading files wastes context. Reference prior read by line numbers instead.\n"
        f"Previous read(s) are already in context. Use offset+limit to get specific sections if needed.\n"
    )


def build_warn(file_path: str, size_kb: float, token_est: int) -> str:
    """Build a warning message for borderline file sizes."""
    return (
        f"\nCONTEXT_GUARD_PREFLIGHT_WARN: {Path(file_path).name} is {size_kb:.1f}kB (~{token_est} tokens). "
        f"Consider using offset+limit to read only the sections you need.\n"
        f"Tip: read frontmatter + TOC first (limit=50), then target specific line ranges.\n"
    )


def build_block(file_path: str, size_kb: float, token_est: int) -> str:
    """Build a block message for oversized files."""
    return (
        f"CONTEXT_GUARD_PREFLIGHT_BLOCK: {Path(file_path).name} is {size_kb:.1f}kB (~{token_est} tokens) "
        f"with no offset or limit.\n"
        f"This output would waste ~{token_est} tokens across every subsequent turn.\n"
        f"ACTION REQUIRED: re-invoke Read with offset+limit:\n"
        f"  - Read {Path(file_path).name} with limit=50 to see frontmatter/TOC first\n"
        f"  - Then Read with offset=N, limit=M for the specific sections you need\n"
        f"If the full file is genuinely required, set limit=0 to bypass this guard.\n"
    )


def estimate_tokens(byte_size: int) -> int:
    return max(1, byte_size // 4)


def classify_glob_pattern(pattern: str) -> str:
    """Classify Glob pattern as 'critical', 'warn', or 'allow'.

    Returns 'critical' for truly unbounded patterns (**/* with no filter).
    Returns 'warn' for broad patterns (**/* scoped to a directory).
    Returns 'allow' for patterns with extension filters or specific paths.
    """
    if not pattern:
        return "allow"
    # Bare **/* with no path prefix or extension filter = truly unbounded
    if pattern == "**/*":
        return "critical"
    # **/* without extension filter but scoped to a dir = broad but not fully unbounded
    if "**/*" in pattern and "." not in pattern.rsplit("/", 1)[-1]:
        return "warn"
    return "allow"


def main() -> int:
    enabled = os.environ.get("CONTEXT_PREFLIGHT_ENABLED", "1")
    if enabled in ("0", "false", "no"):
        return 0

    data = load_input()
    if not data:
        return 0

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    if not isinstance(tool_input, dict):
        tool_input = {}

    # Glob handler — advisory-only, always exits 0
    if tool_name == "Glob":
        pattern = tool_input.get("pattern", "")
        verdict = classify_glob_pattern(pattern)
        if verdict == "critical":
            print(
                f"CONTEXT_GUARD_PREFLIGHT_GLOB_CRITICAL: pattern '{pattern}' is unbounded. "
                f"ADVISORY: Use narrower patterns with file extensions or specific subdirectories. "
                f"PostToolUse guard will still measure actual output."
            )
        elif verdict == "warn":
            print(
                f"CONTEXT_GUARD_PREFLIGHT_GLOB_WARN: pattern '{pattern}' is broad. "
                f"Consider narrowing to specific subdirectories or file extensions."
            )
        return 0

    if tool_name != "Read":
        return 0

    file_path = tool_input.get("file_path", "")
    if not file_path:
        return 0

    # Check for safe flags first — if present, allow through but still track
    size = file_size_bytes(file_path)

    if size < 0:
        # File doesn't exist yet (e.g., Write about to create it)
        # Don't block — let the tool handle the error
        return 0

    safe = has_safe_flags(tool_input, size)

    # Check for re-reads BEFORE tracking this read
    if os.environ.get("CONTEXT_PREFLIGHT_REREAD_WARN", "1") not in ("0", "false", "no"):
        prior = find_prior_reads(file_path)
        if prior:
            print(build_reread_warning(len(prior), file_path))

    # Track this read AFTER re-read check so first read doesn't self-match
    track_read(file_path, size, safe)

    if safe:
        # Has limit (or offset for small files) — always allow
        return 0

    kb_size = size / 1024.0
    token_est = estimate_tokens(size)

    # BLOCK: file exceeds block threshold with no limit/offset
    if size > BLOCK_THRESHOLD:
        print(build_block(file_path, kb_size, token_est))
        return 1

    # WARN: file exceeds warn threshold but under block threshold
    if size > WARN_THRESHOLD:
        print(build_warn(file_path, kb_size, token_est))
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
