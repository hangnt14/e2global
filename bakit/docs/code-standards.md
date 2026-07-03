# BA-kit Code Standards

## Overview

BA-kit follows contract-first design with strict naming conventions, file organization patterns, and artifact structure standards. These standards ensure consistency across 251 files and enable reliable automation.

**Core Principle:** Self-documenting names and paths. When LLM tools (Grep, Glob) read filenames, they should understand purpose without reading content.

## Naming Conventions

### Slugs (Folder & File Names)

All slugs follow kebab-case with ASCII-only characters.

**Rules:**
- Lowercase only
- Kebab-case (hyphens, no underscores)
- ASCII only (no Vietnamese diacritics)
- No spaces, no special characters
- Strip leading/trailing hyphens
- Max 50 characters

**Examples:**

| Input | Slug |
|-------|------|
| "User Login" | `user-login` |
| "Forgot Password (v2)" | `forgot-password-v2` |
| "Thanh toán đơn hàng" | `payment-checkout` |
| "2FA / OTP" | `two-factor-auth` |
| "Báo cáo doanh thu" | `revenue-report` |

### Project Root Naming

**Format:** `plans/{slug}-{date}/`

- `{slug}`: Project slug (kebab-case, max 50 chars)
- `{date}`: ISO date + time token (format: `YYMMDD-HHmm`)

**Examples:**
- `plans/warehouse-rfp-260512-1430/`
- `plans/payment-checkout-260518-0905/`
- `plans/multivendor-ecommerce-260518-1241/`

### File Path Patterns

| Artifact Type | Path | Example |
|---------------|------|---------|
| Intake | `plans/{slug}-{date}/01_intake/intake.md` | `plans/payment-260518-1241/01_intake/intake.md` |
| Backbone | `plans/{slug}-{date}/02_backbone/backbone.md` | `plans/payment-260518-1241/02_backbone/backbone.md` |
| FRD | `plans/{slug}-{date}/03_modules/{module_slug}/frd.md` | `plans/payment-260518-1241/03_modules/checkout/frd.md` |
| User Stories | `plans/{slug}-{date}/03_modules/{module_slug}/user-stories.md` | `plans/payment-260518-1241/03_modules/checkout/user-stories.md` |
| SRS | `plans/{slug}-{date}/03_modules/{module_slug}/srs.md` | `plans/payment-260518-1241/03_modules/checkout/srs.md` |
| SRS Groups | `plans/{slug}-{date}/03_modules/{module_slug}/srs-groups/srs-group-{A-F}.md` | `plans/payment-260518-1241/03_modules/checkout/srs-groups/srs-group-a.md` |
| Screen Canon | `plans/{slug}-{date}/03_modules/{module_slug}/screens/{screen_slug}.md` | `plans/payment-260518-1241/03_modules/checkout/screens/scr-checkout.md` |
| Design System | `designs/{slug}/DESIGN.md` | `designs/payment/DESIGN.md` |
| Project Home | `plans/{slug}-{date}/PROJECT-HOME.md` | `plans/payment-260518-1241/PROJECT-HOME.md` |
| Collab Home | `plans/{slug}-{date}/COLLAB-HOME.md` | `plans/payment-260518-1241/COLLAB-HOME.md` |
| Module Home | `plans/{slug}-{date}/03_modules/{module_slug}/MODULE-HOME.md` | `plans/payment-260518-1241/03_modules/checkout/MODULE-HOME.md` |

### ID Conventions (Cross-Document References)

All IDs use format: `{TYPE}-{feature}-{NNN}` or `{TYPE}-{YYYYMMDD}-{NNN}` depending on scope.

**Feature-Scoped IDs** (per-feature, unique within feature folder):

| Type | Format | Example | Scope |
|------|--------|---------|-------|
| Business Objective | `BO-{feature}-{NNN}` | `BO-payment-01` | `docs/payment/brd.md` |
| PRD Capability | `CAP-{feature}-{NNN}` | `CAP-payment-01` | `docs/payment/prd.md` |
| Functional Requirement | `FR-{feature}-{NNN}` | `FR-payment-001` | `docs/payment/srs/spec.md` |
| Non-Functional Requirement | `NFR-{feature}-{NNN}` | `NFR-payment-001` | `docs/payment/srs/spec.md` |
| Business Rule | `BR-{feature}-{NNN}` | `BR-payment-001` | `docs/payment/srs/spec.md` |
| Error Code | `E-{feature}-{NNN}` | `E-payment-001` | `docs/payment/srs/spec.md` |

**Feature-Implicit IDs** (scope via path, no feature prefix):

| Type | Format | Example | Scope |
|------|--------|---------|-------|
| User Story | `US-{NNN}` | `US-001` | `docs/payment/userstories/us-001.md` |
| Use Case | `UC-{slug}` | `UC-checkout` | `docs/payment/usecases/uc-checkout.md` |
| Acceptance Criterion | `AC-{NNN}` | `AC-001` | Within `us-{NNN}.md` |

**Project-Wide IDs** (date-scoped, global):

| Type | Format | Example | Scope |
|------|--------|---------|-------|
| Change Request | `CR-{YYYYMMDD}-{NNN}` | `CR-20260512-001` | `docs/changes/` |
| Decision | `D-{YYYY-MM-DD}-{slug}` | `D-2026-05-12-stripe-vs-momo` | `docs/decisions/` |
| Blocker | `B-{YYYY-MM-DD}-{slug}` | `B-2026-05-12-vendor-delay` | `docs/blockers/` |

**Rules:**
- Feature prefix **required** for BO/CAP/FR/NFR/BR/E (prevents collision in cross-feature aggregation)
- US/AC/UC scope via path (no feature prefix needed)
- NNN = 3-digit zero-padded (001, 042, 999)
- IDs never reused when deleted (always increment max + 1)
- Slug in ID: kebab-case, max 30 chars

### Wikilinks (Cross-References)

Use full paths from project root. Compatible with Obsidian and GitHub markdown rendering.

**Format:** `[[docs/payment/srs/spec.md|Display Text]]` or `[[docs/payment/srs/spec.md#FR-payment-001|FR-payment-001]]`

**Examples:**
```markdown
[[docs/payment/srs/spec.md|Payment SRS]]
[[docs/payment/srs/spec.md#FR-payment-001|FR-payment-001]]
[[plans/payment-260518-1241/02_backbone/backbone.md|Backbone]]
```

## File Organization

### Skill Files

**Structure:**
```
skills/{skill-name}/
├── SKILL.md              # Skill definition (40-260 LOC)
├── steps/                # Lifecycle step files
│   ├── step-1.md
│   ├── step-2.md
│   └── ...
└── README.md             # Optional: skill overview
```

**Naming:** Skill folders use kebab-case (e.g., `ba-start`, `ba-collab`, `qc-uc-review`)

**SKILL.md Structure:**
- Metadata (name, description, activation level)
- Prerequisites
- Processing steps
- Output format
- References

### Script Files

**Naming Convention:** kebab-case with descriptive names

**Examples:**
- `guardrail-preflight.py` (not `gp.py` or `preflight.py`)
- `reverse-drift-check.py` (not `drift_check.py`)
- `validate-navigation-consistency.py` (not `nav_validate.py`)
- `md-to-html.py` (not `convert.py`)

**Organization:**
```
scripts/
├── guardrail-*.py        # Index-first read enforcement
├── reverse-*.py          # As-built documentation
├── validate-*.py         # Quality validation
├── install*.sh           # Installation scripts
└── __pycache__/          # Python cache (gitignored)
```

**Python Conventions:**
- Use `#!/usr/bin/env python3` shebang
- Follow PEP 8 (4-space indentation)
- Type hints for function signatures
- Docstrings for modules and functions
- Error handling with try/except
- Logging instead of print() for production scripts

**Bash Conventions:**
- Use `#!/bin/bash` shebang
- Set `set -euo pipefail` for safety
- Quote variables: `"$var"` not `$var`
- Use `local` for function variables
- Comment complex logic

### Template Files

**Naming:** `{artifact-type}-template.md`

**Examples:**
- `intake-form-template.md`
- `frd-template.md`
- `userstory-item-template.md`
- `ascii-screen-template.md`
- `project-home-template.md`

**Structure:**
- Frontmatter with metadata
- Sections matching artifact type
- Placeholder text in `{curly braces}`
- Examples where helpful
- Comments for guidance

### Behavior Shard Files

**Location:** `core/behavior/`

**Naming:** `{command-name}.md`

**Examples:**
- `intake.md`
- `backbone.md`
- `srs.md`
- `wireframes.md`
- `qc-review.md`

**Structure:**
- Prerequisites
- Workflow steps (numbered)
- Quality gate criteria
- Error handling
- State transitions

## YAML Structure (contract.yaml)

**Top-level keys:**
```yaml
version: 1
defaults: {...}
states: {...}
paths: {...}
artifact_profiles: {...}
commands: {...}
quality_gates: {...}
activation_levels: {...}
resolution: {...}
patterns: {...}
legacy: {...}
```

**Conventions:**
- Use snake_case for keys
- Paths use `{token}` substitution (e.g., `{slug}`, `{date}`, `{module_slug}`)
- State enums are canonical (e.g., `recommended`, `in-progress`, `completed`)
- Commands list all 18 BA commands with metadata
- Quality gates specify profile, criteria, block conditions

## Frontmatter Requirements

Every artifact file MUST have YAML frontmatter at the top:

```yaml
---
type: srs                    # Artifact type (see types below)
status: draft                # Lifecycle status
created: 2026-05-18          # ISO date
updated: 2026-05-18          # ISO date
owner: "@hoang"              # Optional: handle
priority: P0                 # Optional: P0/P1/P2
version: 0.1.0               # Optional: semver
tags: []                     # Optional: list of strings
links: []                    # Optional: related doc paths
---
```

**Artifact Type Values:**

| Type | Use For |
|------|---------|
| `srs` | SRS spec document |
| `frd` | Functional requirements |
| `urd` | User requirements |
| `brd` | Business requirements |
| `prd` | Product requirements |
| `user-story` | User story format |
| `use-case` | Use case document |
| `screen` | Screen specification |
| `brainstorm` | Brainstorm capture |
| `design-md` | Design system document |
| `intake` | Intake form |
| `backbone` | Requirements backbone |
| `project-home` | Project dashboard |
| `collab-home` | Collaboration dashboard |
| `change-request` | Change request |
| `impact-report` | Impact analysis |
| `meeting` | Meeting notes |
| `decision` | Decision record |
| `blocker` | Blocker tracking |

## Markdown Conventions

### Headings

Use ATX-style headings (# not underlines). Hierarchy:
- `#` — Document title (one per file)
- `##` — Major sections
- `###` — Subsections
- `####` — Details (avoid deeper nesting)

### Lists

Use `-` for unordered lists, `1.` for ordered. Indent with 2 spaces:

```markdown
- Item 1
  - Nested item 1a
  - Nested item 1b
- Item 2

1. First step
   1. Substep 1a
   2. Substep 1b
2. Second step
```

### Code Blocks

Use triple backticks with language identifier:

````markdown
```python
def hello():
    print("world")
```

```yaml
key: value
nested:
  - item1
  - item2
```

```bash
#!/bin/bash
set -euo pipefail
echo "Hello"
```
````

### Tables

Use pipe-delimited format with header separator:

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Value 4  | Value 5  | Value 6  |
```

### Links

Use full paths from project root:

```markdown
[Getting Started](docs/getting-started.md)
[Payment SRS](docs/payment/srs/spec.md)
[[docs/payment/srs/spec.md#FR-payment-001|FR-payment-001]]
```

## Commit Message Format

Use conventional commits:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`

**Scope:** Optional, e.g., `core`, `skills`, `scripts`, `templates`

**Subject:** Imperative, present tense, no period, max 50 chars

**Examples:**
```
feat(core): add qc-review behavior shard

fix(scripts): handle missing module in reverse-drift-check

docs(codebase): update naming conventions

refactor(skills): consolidate ba-start step files

test(runtime-parity): add Codex adapter tests
```

**Rules:**
- No AI references in commit messages
- Keep commits focused on actual code changes
- One logical change per commit
- Reference issue numbers in footer if applicable

## Python Code Standards

### File Structure

```python
#!/usr/bin/env python3
"""Module docstring: one-line summary.

Longer description if needed. Explain purpose and usage.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional

# Constants
DEFAULT_TIMEOUT = 30
VALID_STATES = {"draft", "in-progress", "completed"}

# Functions
def main() -> int:
    """Main entry point."""
    try:
        # Implementation
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### Naming

- **Functions/variables:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`
- **Private:** prefix with `_`

### Type Hints

Always include type hints:

```python
def process_artifact(path: str, mode: str = "hybrid") -> Dict[str, any]:
    """Process artifact file.

    Args:
        path: File path to process
        mode: Processing mode (lite, hybrid, formal)

    Returns:
        Dictionary with processing results
    """
    pass
```

### Error Handling

Use specific exceptions:

```python
try:
    with open(path) as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"File not found: {path}", file=sys.stderr)
    return None
except json.JSONDecodeError as e:
    print(f"Invalid JSON: {e}", file=sys.stderr)
    return None
```

## Bash Code Standards

### File Structure

```bash
#!/bin/bash
set -euo pipefail

# Script description
# Usage: script-name.sh [options]

# Constants
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Functions
main() {
    local arg1="$1"
    # Implementation
}

# Entry point
main "$@"
```

### Naming

- **Functions:** `snake_case`
- **Variables:** `UPPER_SNAKE_CASE` for constants, `lower_snake_case` for locals
- **Private functions:** prefix with `_`

### Safety

Always use:
```bash
set -euo pipefail
```

- `-e`: Exit on error
- `-u`: Error on undefined variables
- `-o pipefail`: Propagate pipe errors

### Quoting

Always quote variables:

```bash
# Good
echo "$var"
if [[ -f "$file" ]]; then

# Bad
echo $var
if [ -f $file ]; then
```

## JSON Structure (manifest.json)

**Template Manifest:**
```json
{
  "version": 1,
  "templates": [
    {
      "id": "intake-form",
      "name": "Intake Form",
      "type": "intake",
      "path": "templates/intake-form-template.md",
      "description": "Structured intake normalization",
      "activation_level": "base"
    }
  ]
}
```

**Configuration (ba-kit.config.json):**
```json
{
  "version": 1,
  "defaults": {
    "language": "vi",
    "mode": "hybrid",
    "ui_baseline": "Shadcn UI"
  }
}
```

## File Size Management

**Target:** Keep individual files under 200 LOC for optimal context management

**When to split:**
- Skill step files > 150 LOC → split into substeps
- Behavior shards > 200 LOC → extract common patterns
- Template files > 300 LOC → create separate templates
- Script files > 300 LOC → extract utilities into separate modules

**How to split:**
1. Identify semantic boundaries (distinct concerns)
2. Extract into separate file with descriptive name
3. Import/reference from parent file
4. Update documentation with new structure

## Documentation Standards

### README Files

Every major directory should have a README.md:

```markdown
# Directory Name

Brief description of what this directory contains.

## Contents

- `file1.md` — Description
- `file2.md` — Description

## Usage

How to use files in this directory.

## Related

Links to related documentation.
```

### Inline Comments

Use comments for "why", not "what":

```python
# Good: explains intent
# Retry with exponential backoff to handle transient failures
for attempt in range(max_retries):
    try:
        return fetch_data(url)
    except ConnectionError:
        time.sleep(2 ** attempt)

# Bad: restates code
# Loop through attempts
for attempt in range(max_retries):
```

### Docstrings

Use Google-style docstrings:

```python
def process_artifact(path: str, mode: str = "hybrid") -> Dict[str, any]:
    """Process artifact file and return results.

    Validates artifact structure, applies quality gates, and generates
    output based on specified mode.

    Args:
        path: File path to process
        mode: Processing mode (lite, hybrid, formal)

    Returns:
        Dictionary with keys:
        - status: "ok" or "error"
        - data: Processed artifact data
        - errors: List of validation errors (if any)

    Raises:
        FileNotFoundError: If artifact file not found
        ValueError: If artifact structure invalid
    """
```

## Cross-File Consistency

### Terminology

Use consistent terminology across all files:

| Term | Usage |
|------|-------|
| Backbone | Requirements backbone (source of truth) |
| Module | Feature module (e.g., checkout, auth) |
| Artifact | Deliverable document (FRD, SRS, etc.) |
| Skill | BA workflow automation (ba-start, ba-collab) |
| Shard | Command-specific behavior file |
| Gate | Quality checkpoint (post-SRS module QC, package validation) |
| Slug | Project identifier (kebab-case) |

### Cross-References

Always use full paths:
- ✅ `docs/getting-started.md`
- ✅ `plans/payment-260518-1241/02_backbone/backbone.md`
- ❌ `getting-started.md` (relative, breaks in different contexts)
- ❌ `./docs/getting-started.md` (relative, breaks in different contexts)

### Link Validation

Before committing, verify:
- All wikilinks use full paths from project root
- All file references exist
- All ID references are valid
- No broken cross-references

## Quality Checklist

Before committing code or documentation:

- [ ] Filenames follow kebab-case convention
- [ ] Paths use `{token}` substitution where applicable
- [ ] Frontmatter present and valid
- [ ] Headings use ATX-style (#)
- [ ] Code blocks have language identifier
- [ ] Links use full paths from project root
- [ ] IDs follow format conventions
- [ ] No trailing whitespace
- [ ] No mixed line endings
- [ ] Commit message follows conventional format
- [ ] No AI references in code/commit messages
- [ ] File size < 200 LOC (or justified exception)
