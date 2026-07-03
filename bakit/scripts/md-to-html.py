#!/usr/bin/env python3
"""Convert BA markdown documents to unified BA-kit HTML with rendered diagrams and embedded images.

Usage:
    python scripts/md-to-html.py plans/reports/frd-260325-project.md
    python scripts/md-to-html.py plans/reports/srs-260325-project.md

Works with any BA-kit document: intake, FRD (Mermaid/PlantUML workflows), user stories,
SRS (wireframe images + diagrams), or any markdown file.

Supports:
    - Shared BA-kit HTML shell with metadata header and artifact-specific visual variants
    - Mermaid diagrams (rendered client-side via mermaid.js CDN)
    - PlantUML diagrams (rendered locally when available, or via an explicitly configured server)
    - Inline wireframe images from explicit PNG references in the markdown
    - In-browser editing without touching raw HTML code
    - Page breaks for PDF printing (browser Print → Save as PDF)
    - Table of contents generation
"""

import argparse
import base64
import os
import re
import shutil
import subprocess
import sys
import zlib
from datetime import datetime
from html import escape
from pathlib import Path

# Minimal markdown-to-html without external deps.
# Handles: headings, tables, bold, italic, code blocks, nested lists, blockquotes, links, images.

LIST_ITEM_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<marker>[-*]|\d+\.)\s+(?P<content>.+)$")
DATE_TOKEN_RE = r"\d{6}-\d{4}"
PLANTUML_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
ALLOWED_IMAGE_SUFFIXES = {".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"}
REPO_ROOT = Path(__file__).resolve().parent.parent

ARTIFACT_VARIANTS = {
    "generic": {
        "badge": "Tài liệu BA-kit",
        "label": "Tài liệu phân tích nghiệp vụ",
        "summary": "Tài liệu BA được đóng gói trong khung HTML dùng chung của BA-kit.",
    },
    "intake": {
        "badge": "Phiếu tiếp nhận",
        "label": "Tiếp nhận yêu cầu",
        "summary": "Thông tin đầu vào đã chuẩn hóa, dùng để xác định phạm vi, stakeholder, và các bước BA tiếp theo.",
    },
    "frd": {
        "badge": "FRD",
        "label": "Tài liệu yêu cầu chức năng",
        "summary": "Phạm vi chức năng, luồng nghiệp vụ, quy tắc kinh doanh, và tiêu chí chấp nhận được đóng gói trong khung stakeholder dùng chung.",
    },
    "stories": {
        "badge": "User Stories",
        "label": "Phạm vi bàn giao Agile",
        "summary": "Backlog theo story với tiêu chí chấp nhận có thể truy vết và định hướng triển khai.",
    },
    "srs": {
        "badge": "SRS",
        "label": "Đặc tả yêu cầu phần mềm",
        "summary": "Đặc tả hệ thống thống nhất với truy vết, use case, màn hình, và bằng chứng wireframe ASCII.",
    },
}

METADATA_ALIASES = {
    "project": ("tên dự án", "project"),
    "date": ("ngày", "date"),
    "requester": ("người yêu cầu", "requester"),
    "source": ("tài liệu gốc", "source file", "source"),
    "owner": ("chủ sở hữu", "owner"),
    "version": ("phiên bản", "version"),
    "epic": ("epic",),
    "feature": ("tính năng", "feature"),
    "story_id": ("mã story", "story id"),
}

DISPLAY_LABELS = {
    "project": "Dự án",
    "slug": "Slug",
    "date": "Ngày",
    "requester": "Người yêu cầu",
    "source": "Tài liệu gốc",
    "owner": "Chủ sở hữu",
    "version": "Phiên bản",
    "epic": "Epic",
    "feature": "Tính năng",
    "story_id": "Mã story",
}


def normalize_label(label: str) -> str | None:
    """Map raw metadata labels to shared metadata keys."""
    normalized = re.sub(r"\([^)]*\)", "", label).strip().lower()
    for key, aliases in METADATA_ALIASES.items():
        if any(alias in normalized for alias in aliases):
            return key
    return None


def detect_artifact_type(md_path: Path) -> str:
    """Infer the packaged artifact type from the markdown filename."""
    stem = md_path.stem
    if stem.startswith("intake-"):
        return "intake"
    if stem.startswith("frd-"):
        return "frd"
    if stem.startswith("user-stories-"):
        return "stories"
    if stem.startswith("srs-"):
        return "srs"
    return "generic"


def extract_artifact_identity(md_path: Path) -> dict[str, str]:
    """Extract slug and dated-set information from known BA-kit filenames."""
    stem = md_path.stem
    patterns = {
        "intake": re.compile(rf"^intake-(?P<slug>.+)-(?P<date>{DATE_TOKEN_RE})$"),
        "frd": re.compile(rf"^frd-(?P<date>{DATE_TOKEN_RE})-(?P<slug>.+)$"),
        "stories": re.compile(rf"^user-stories-(?P<date>{DATE_TOKEN_RE})-(?P<slug>.+)$"),
        "srs": re.compile(rf"^srs-(?P<date>{DATE_TOKEN_RE})-(?P<slug>.+?)(?:-group-[a-z0-9-]+)?$"),
    }
    doc_type = detect_artifact_type(md_path)
    pattern = patterns.get(doc_type)
    if not pattern:
        return {}
    match = pattern.match(stem)
    return match.groupdict() if match else {}


def extract_title(md: str, md_path: Path) -> str:
    """Read the first markdown heading as the document title."""
    for line in md.splitlines():
        match = re.match(r"^#\s+(.+)", line.strip())
        if match:
            return match.group(1).strip()
    return md_path.stem


def parse_emphasis_metadata(md: str) -> dict[str, str]:
    """Parse `**Label:** value` metadata lines commonly used in FRD/SRS/user stories."""
    metadata = {}
    for raw_line in md.splitlines():
        line = raw_line.strip()
        match = re.match(r"^\*\*(.+?)\*\*:\s*(.+)$", line)
        if not match:
            continue
        key = normalize_label(match.group(1))
        value = match.group(2).strip()
        if key and value and value != "|":
            metadata[key] = value
    return metadata


def parse_table_metadata(md: str) -> dict[str, str]:
    """Parse two-column metadata tables such as the intake project information block."""
    metadata = {}
    for raw_line in md.splitlines():
        line = raw_line.strip()
        if not (line.startswith("|") and "|" in line[1:]):
            continue
        if re.fullmatch(r"\|?[\s:-]+(?:\|[\s:-]+)+\|?", line):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        header_key = normalize_label(cells[0])
        value = cells[1].strip()
        if header_key and value and "giá trị" not in value.lower() and "value" not in value.lower():
            metadata[header_key] = value
    return metadata


def extract_document_metadata(md: str, md_path: Path) -> dict[str, str]:
    """Build a shared metadata map for the HTML shell."""
    metadata = {}
    metadata.update(parse_table_metadata(md))
    metadata.update(parse_emphasis_metadata(md))
    metadata.update(extract_artifact_identity(md_path))
    return metadata


def format_document_meta(doc_type: str, metadata: dict[str, str], md_path: Path) -> str:
    """Build the metadata grid rendered above every HTML deliverable."""
    ordered_keys = [
        "project",
        "slug",
        "date",
        "version",
        "owner",
        "requester",
        "epic",
        "feature",
        "story_id",
        "source",
    ]
    rows = [('Loại tài liệu', ARTIFACT_VARIANTS[doc_type]["label"])]
    rows.extend((DISPLAY_LABELS[key], metadata[key]) for key in ordered_keys if metadata.get(key))
    rows.append(("Tệp markdown gốc", str(md_path)))
    rows.append(("Thời điểm tạo", datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")))
    return "\n".join(
        (
            '      <div class="doc-meta-card">'
            f'<dt>{escape(label)}</dt><dd>{escape(value)}</dd>'
            "</div>"
        )
        for label, value in rows
    )


def render_document_shell(md: str, md_path: Path) -> tuple[str, str]:
    """Render the shared HTML chrome for all BA-kit document types."""
    doc_type = detect_artifact_type(md_path)
    variant = ARTIFACT_VARIANTS[doc_type]
    title = extract_title(md, md_path)
    metadata = extract_document_metadata(md, md_path)
    summary = variant["summary"]
    if metadata.get("project"):
        summary = f"{summary} Dự án: {metadata['project']}."
    shell = f"""  <section class="document-chrome">
    <div class="doc-kicker">BA-kit — Tài liệu bàn giao</div>
    <div class="doc-hero">
      <div class="doc-hero__content">
        <div class="doc-type-badge">{escape(variant["badge"])}</div>
        <h1 class="doc-hero__title">{escape(title)}</h1>
        <p class="doc-hero__summary">{escape(summary)}</p>
      </div>
      <dl class="doc-meta-grid">
{format_document_meta(doc_type, metadata, md_path)}
      </dl>
    </div>
  </section>
"""
    return doc_type, shell


def resolve_asset_path(asset_path: str, base_dir: Path) -> tuple[Path | None, str | None]:
    """Resolve an asset path only when it stays inside the allowed base directory."""
    resolved_base = base_dir.resolve()
    candidate = Path(asset_path.strip())
    if candidate.is_absolute():
        return None, "Blocked image path outside base directory"
    resolved_path = (resolved_base / candidate).resolve()
    try:
        resolved_path.relative_to(resolved_base)
    except ValueError:
        return None, "Blocked image path outside base directory"
    if resolved_path.suffix.lower() not in ALLOWED_IMAGE_SUFFIXES:
        return None, f"Unsupported image type: {resolved_path.suffix or '[none]'}"
    if not resolved_path.exists() or not resolved_path.is_file():
        return None, "Missing image"
    return resolved_path, None


def embed_image(img_path: str, base_dir: Path) -> str:
    """Convert image path to base64 data URI."""
    full_path, error = resolve_asset_path(img_path, base_dir)
    if error:
        css_class = "missing-image" if error == "Missing image" else "blocked-image"
        return f'<span class="{css_class}">[{escape(error)}: {escape(img_path)}]</span>'
    suffix = full_path.suffix.lower()
    mime = {
        "gif": "image/gif",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "svg": "image/svg+xml",
        "webp": "image/webp",
    }.get(suffix.lstrip("."), "image/png")
    data = base64.b64encode(full_path.read_bytes()).decode()
    return (
        f'<img src="data:{mime};base64,{data}" alt="{escape(full_path.stem)}" '
        f'class="wireframe" loading="lazy" decoding="async">'
    )


def encode_plantuml(source: str) -> str:
    """Encode PlantUML text into the compact URL form expected by PlantUML servers."""
    compressor = zlib.compressobj(level=9, wbits=-15)
    compressed = compressor.compress(source.encode("utf-8")) + compressor.flush()
    encoded = []
    for index in range(0, len(compressed), 3):
        chunk = compressed[index:index + 3]
        b1 = chunk[0]
        b2 = chunk[1] if len(chunk) > 1 else 0
        b3 = chunk[2] if len(chunk) > 2 else 0
        for value in (
            b1 >> 2,
            ((b1 & 0x03) << 4) | (b2 >> 4),
            ((b2 & 0x0F) << 2) | (b3 >> 6),
            b3 & 0x3F,
        ):
            encoded.append(PLANTUML_ALPHABET[value & 0x3F])
    return "".join(encoded)


def normalize_plantuml_server(server: str | None) -> str | None:
    """Return a normalized PlantUML server URL with a trailing slash."""
    if not server:
        return None
    normalized = server.strip()
    if not normalized:
        return None
    return normalized if normalized.endswith("/") else f"{normalized}/"


def install_local_plantuml() -> tuple[str | None, str | None]:
    """Attempt to install PlantUML locally using the repo helper script."""
    installer = REPO_ROOT / "scripts" / "install-plantuml.sh"
    if not installer.exists():
        return None, f"Missing installer: {installer}"
    try:
        result = subprocess.run(
            [str(installer)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        return None, f"Failed to execute PlantUML installer: {exc}"
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        stdout = result.stdout.decode("utf-8", errors="replace").strip()
        details = stderr or stdout or f"exit code {result.returncode}"
        return None, f"Local PlantUML install failed: {details}"
    installed = shutil.which("plantuml")
    if not installed:
        return None, "Local PlantUML install completed but `plantuml` is still not on PATH"
    return installed, None


def resolve_plantuml_command(plantuml_command: str | None, auto_install: bool) -> tuple[str | None, str | None]:
    """Resolve a local PlantUML executable, optionally auto-installing it first."""
    candidate = None
    if plantuml_command:
        candidate = shutil.which(plantuml_command)
        if candidate is None and Path(plantuml_command).exists():
            candidate = str(Path(plantuml_command).resolve())
    else:
        candidate = shutil.which("plantuml")
    if candidate:
        return candidate, None
    if auto_install:
        return install_local_plantuml()
    return None, "Local `plantuml` executable not found"


def render_plantuml_locally(source: str, plantuml_command: str | None) -> tuple[str | None, str | None]:
    """Render PlantUML using a local executable when available."""
    executable = plantuml_command
    if not executable:
        return None, "Local `plantuml` executable not found"
    try:
        result = subprocess.run(
            [executable, "-tsvg", "-pipe"],
            input=source.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        return None, f"Failed to execute local `plantuml`: {exc}"
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        if stderr:
            return None, f"Local `plantuml` render failed: {stderr}"
        return None, f"Local `plantuml` render failed with exit code {result.returncode}"
    svg = result.stdout.decode("utf-8", errors="replace").strip()
    if "<svg" not in svg:
        return None, "Local `plantuml` output was not SVG"
    return svg, None


def render_plantuml(source: str, plantuml_server: str | None, plantuml_command: str | None) -> str:
    """Render a PlantUML fenced block without leaking to third-party services by default."""
    diagram = source.strip()
    if not diagram:
        return '<pre class="plantuml-render-error">[Empty PlantUML diagram]</pre>\n'
    normalized_server = normalize_plantuml_server(plantuml_server)
    local_svg, _ = render_plantuml_locally(diagram, plantuml_command)
    if local_svg:
        return (
            '<figure class="plantuml-diagram plantuml-diagram--inline">'
            f"{local_svg}"
            "</figure>\n"
        )
    if normalized_server:
        encoded = encode_plantuml(diagram)
        return (
            '<figure class="plantuml-diagram">'
            '<figcaption class="plantuml-render-warning">'
            'Local PlantUML was unavailable, so this diagram is using the configured server fallback.'
            '</figcaption>'
            f'<img src="{normalized_server}{encoded}" alt="PlantUML diagram" '
            'class="plantuml-image" loading="lazy" decoding="async">'
            "</figure>\n"
        )
    return (
        '<figure class="plantuml-diagram">'
        '<figcaption class="plantuml-render-warning">'
        'PlantUML was not rendered. Prefer local setup via `ba-kit install-plantuml` '
        'or rerun with `--auto-install-plantuml`. Only if local is unavailable should '
        'you use `--plantuml-server` / `BA_KIT_PLANTUML_SERVER`.'
        '</figcaption>'
        f'<pre class="plantuml-render-error">{escape(diagram)}</pre>'
        "</figure>\n"
    )


def md_to_html(
    md: str,
    base_dir: Path,
    *,
    plantuml_server: str | None = None,
    plantuml_command: str | None = None,
) -> str:
    """Convert markdown to HTML with embedded images."""
    lines = md.split("\n")
    html_parts = []
    toc = []
    in_code = False
    in_table = False
    code_lang = ""
    code_lines = []
    table_rows = []
    list_stack = []

    def flush_table():
        nonlocal table_rows, in_table
        if not table_rows:
            return ""
        out = '<table>\n<thead>\n<tr>'
        headers = [c.strip() for c in table_rows[0].strip("|").split("|")]
        for h in headers:
            out += f"<th>{inline(h)}</th>"
        out += "</tr>\n</thead>\n<tbody>\n"
        # Skip separator row (index 1)
        for row in table_rows[2:]:
            out += "<tr>"
            cells = [c.strip() for c in row.strip("|").split("|")]
            for c in cells:
                out += f"<td>{inline(c)}</td>"
            out += "</tr>\n"
        out += "</tbody>\n</table>\n"
        table_rows = []
        in_table = False
        return out

    def close_list_item():
        if list_stack and list_stack[-1]["item_open"]:
            html_parts.append("</li>\n")
            list_stack[-1]["item_open"] = False

    def close_list():
        close_list_item()
        current = list_stack.pop()
        html_parts.append(f"</{current['tag']}>\n")

    def flush_lists():
        while list_stack:
            close_list()

    def inline(text: str) -> str:
        """Process inline markdown: bold, italic, code, links, images."""
        text = escape(text)
        # Images: ![alt](path)
        text = re.sub(
            r"!\[([^\]]*)\]\(([^)]+)\)",
            lambda m: embed_image(m.group(2), base_dir),
            text,
        )
        # Links
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
        # Bold
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        # Italic
        text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
        # Inline code
        text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
        return text

    for line in lines:
        # Code blocks
        if line.startswith("```"):
            if in_code:
                if code_lang == "mermaid":
                    html_parts.append("</pre>\n")
                elif code_lang == "plantuml":
                    html_parts.append(
                        render_plantuml(
                            "".join(code_lines),
                            plantuml_server=plantuml_server,
                            plantuml_command=plantuml_command,
                        )
                    )
                else:
                    html_parts.append("</code></pre>\n")
                in_code = False
                code_lang = ""
                code_lines = []
            else:
                code_lang = line[3:].strip()
                cls = f' class="language-{code_lang}"' if code_lang else ""
                if code_lang == "mermaid":
                    html_parts.append(f'<pre class="mermaid">')
                elif code_lang == "plantuml":
                    code_lines = []
                else:
                    html_parts.append(f"<pre><code{cls}>")
                in_code = True
            continue
        if in_code:
            if code_lang == "mermaid":
                html_parts.append(line + "\n")
            elif code_lang == "plantuml":
                code_lines.append(line + "\n")
            else:
                html_parts.append(escape(line) + "\n")
            continue

        # Table detection
        if "|" in line and line.strip().startswith("|"):
            if not in_table:
                flush_lists()
                in_table = True
                table_rows = []
            table_rows.append(line)
            continue
        elif in_table:
            html_parts.append(flush_table())

        # List items
        list_match = LIST_ITEM_RE.match(line)
        if list_match:
            indent = len(list_match.group("indent").expandtabs(4))
            marker = list_match.group("marker")
            tag = "ol" if marker[0].isdigit() else "ul"
            item = list_match.group("content")

            while list_stack and indent < list_stack[-1]["indent"]:
                close_list()

            if list_stack and indent == list_stack[-1]["indent"] and tag != list_stack[-1]["tag"]:
                close_list()

            if not list_stack or indent > list_stack[-1]["indent"]:
                html_parts.append(f"<{tag}>\n")
                list_stack.append({"tag": tag, "indent": indent, "item_open": False})
            else:
                close_list_item()

            html_parts.append(f"<li>{inline(item)}")
            list_stack[-1]["item_open"] = True
            continue

        # Empty line
        if not line.strip():
            flush_lists()
            html_parts.append("\n")
            continue

        flush_lists()

        # Headings
        m = re.match(r"^(#{1,6})\s+(.+)", line)
        if m:
            level = len(m.group(1))
            text = m.group(2)
            slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
            toc.append((level, text, slug))
            # Page break before h1 and h2 (except first)
            if level <= 2 and len(toc) > 1:
                html_parts.append('<div class="page-break"></div>\n')
            html_parts.append(f'<h{level} id="{slug}">{inline(text)}</h{level}>\n')
            continue

        # Blockquote
        if line.startswith(">"):
            text = line.lstrip("> ")
            html_parts.append(f"<blockquote>{inline(text)}</blockquote>\n")
            continue

        # Horizontal rule
        if re.match(r"^[-*_]{3,}$", line.strip()):
            html_parts.append("<hr>\n")
            continue

        # Paragraph
        html_parts.append(f"<p>{inline(line)}</p>\n")

    # Flush remaining
    if in_table:
        html_parts.append(flush_table())
    if list_stack:
        flush_lists()

    # Build TOC
    toc_html = '<nav class="toc"><h2>Table of Contents</h2>\n<ul>\n'
    for level, text, slug in toc:
        indent = "  " * (level - 1)
        toc_html += f'{indent}<li class="toc-{level}"><a href="#{slug}">{escape(text)}</a></li>\n'
    toc_html += "</ul>\n</nav>\n"

    body = "".join(html_parts)
    return toc_html + body


CSS = """
:root {
    --primary: #1a1a2e;
    --accent: #0f3460;
    --accent-soft: #d9edf7;
    --bg: #ffffff;
    --text: #1a1a1a;
    --border: #e0e0e0;
    --code-bg: #f5f5f5;
    --toolbar-bg: rgba(255, 255, 255, 0.96);
    --danger: #b42318;
    --success: #0f7b6c;
    --hero-bg: linear-gradient(135deg, rgba(15, 52, 96, 0.08), rgba(217, 237, 247, 0.65));
    --muted: #52627a;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6; color: var(--text); background: #f5f7fb;
    margin: 0; padding: 0;
}
body[data-doc-type="intake"] {
    --primary: #134e4a;
    --accent: #0f766e;
    --accent-soft: #ccfbf1;
    --hero-bg: linear-gradient(135deg, rgba(15, 118, 110, 0.12), rgba(204, 251, 241, 0.72));
}
body[data-doc-type="frd"] {
    --primary: #1e3a8a;
    --accent: #1d4ed8;
    --accent-soft: #dbeafe;
    --hero-bg: linear-gradient(135deg, rgba(29, 78, 216, 0.12), rgba(219, 234, 254, 0.74));
}
body[data-doc-type="stories"] {
    --primary: #78350f;
    --accent: #b45309;
    --accent-soft: #fef3c7;
    --hero-bg: linear-gradient(135deg, rgba(180, 83, 9, 0.12), rgba(254, 243, 199, 0.78));
}
body[data-doc-type="srs"] {
    --primary: #115e59;
    --accent: #0f766e;
    --accent-soft: #d1fae5;
    --hero-bg: linear-gradient(135deg, rgba(15, 118, 110, 0.12), rgba(209, 250, 229, 0.75));
}
.editor-shell {
    max-width: 1180px;
    margin: 0 auto;
    padding: 24px 20px 48px;
}
.document-chrome {
    margin-bottom: 20px;
}
.doc-kicker {
    margin-bottom: 10px;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--accent);
}
.doc-hero {
    display: grid;
    gap: 18px;
    padding: 24px;
    border: 1px solid rgba(15, 52, 96, 0.12);
    border-radius: 24px;
    background: var(--hero-bg);
    box-shadow: 0 16px 36px rgba(15, 52, 96, 0.06);
}
.doc-hero__content {
    display: grid;
    gap: 12px;
}
.doc-type-badge {
    display: inline-flex;
    width: fit-content;
    padding: 6px 12px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.78);
    border: 1px solid rgba(15, 52, 96, 0.12);
    color: var(--accent);
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.02em;
}
.doc-hero__title {
    margin: 0;
    font-size: 2rem;
    line-height: 1.15;
    color: var(--primary);
}
.doc-hero__summary {
    margin: 0;
    max-width: 70ch;
    color: var(--muted);
    font-size: 1rem;
}
.doc-meta-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
}
.doc-meta-card {
    min-width: 0;
    padding: 14px 16px;
    border-radius: 16px;
    border: 1px solid rgba(15, 52, 96, 0.1);
    background: rgba(255, 255, 255, 0.82);
}
.doc-meta-card dt {
    margin-bottom: 6px;
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--accent);
}
.doc-meta-card dd {
    margin: 0;
    font-size: 0.95rem;
    color: var(--text);
    overflow-wrap: anywhere;
}
.editor-toolbar {
    position: sticky;
    top: 12px;
    z-index: 1000;
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
    padding: 14px 16px;
    margin-bottom: 20px;
    background: var(--toolbar-bg);
    border: 1px solid rgba(15, 52, 96, 0.14);
    border-radius: 14px;
    box-shadow: 0 10px 30px rgba(15, 52, 96, 0.08);
    backdrop-filter: blur(12px);
}
.editor-toolbar__group {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
}
.editor-toolbar__status {
    margin-left: auto;
    font-size: 0.92rem;
    color: #42526b;
}
.editor-button {
    appearance: none;
    border: 1px solid rgba(15, 52, 96, 0.16);
    background: #fff;
    color: var(--accent);
    padding: 9px 12px;
    border-radius: 10px;
    font-size: 0.92rem;
    font-weight: 600;
    cursor: pointer;
}
.editor-button:hover {
    background: #f0f6ff;
}
.editor-button.is-primary {
    background: var(--accent);
    border-color: var(--accent);
    color: #fff;
}
.editor-button.is-danger {
    color: var(--danger);
    border-color: rgba(180, 35, 24, 0.18);
}
.editor-help {
    width: 100%;
    font-size: 0.88rem;
    color: #52627a;
}
.document-surface {
    max-width: 900px;
    margin: 0 auto;
    padding: 40px 20px;
    background: var(--bg);
    border: 1px solid rgba(15, 52, 96, 0.08);
    border-radius: 18px;
    box-shadow: 0 16px 40px rgba(15, 52, 96, 0.08);
}
h1 { font-size: 2em; color: var(--primary); margin: 1.5em 0 0.5em; border-bottom: 2px solid var(--accent); padding-bottom: 0.3em; }
h2 { font-size: 1.5em; color: var(--accent); margin: 1.2em 0 0.4em; }
h3 { font-size: 1.2em; margin: 1em 0 0.3em; }
h4,h5,h6 { margin: 0.8em 0 0.2em; }
p { margin: 0.5em 0; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; font-size: 0.9em; }
th, td { border: 1px solid var(--border); padding: 8px 12px; text-align: left; }
th { background: var(--accent); color: white; font-weight: 600; }
tr:nth-child(even) { background: #f9f9f9; }
pre { background: var(--code-bg); padding: 16px; border-radius: 6px; overflow-x: auto; margin: 1em 0; }
code { font-family: 'SF Mono', Consolas, monospace; font-size: 0.9em; }
blockquote { border-left: 4px solid var(--accent); padding: 0.5em 1em; margin: 1em 0; background: #f0f4ff; font-style: italic; }
ul, ol { margin: 0.5em 0 0.5em 1.5em; }
li { margin: 0.2em 0; }
pre.mermaid,
.mermaid {
    padding: 20px;
    border: 1px solid rgba(15, 52, 96, 0.1);
    border-radius: 14px;
    background: linear-gradient(180deg, rgba(248, 250, 252, 0.98), rgba(255, 255, 255, 1));
    overflow-x: auto;
}
.mermaid svg {
    display: block;
    max-width: 100%;
    height: auto !important;
    margin: 0 auto;
}
.mermaid-render-error {
    color: #92400e;
    background: #fffbeb;
    border-color: rgba(146, 64, 14, 0.24);
}
.plantuml-diagram {
    margin: 1em 0;
    padding: 20px;
    border: 1px solid rgba(15, 52, 96, 0.1);
    border-radius: 14px;
    background: linear-gradient(180deg, rgba(248, 250, 252, 0.98), rgba(255, 255, 255, 1));
    overflow-x: auto;
}
.plantuml-diagram--inline svg {
    display: block;
    max-width: 100%;
    height: auto;
    margin: 0 auto;
}
.plantuml-image {
    display: block;
    max-width: 100%;
    height: auto;
    margin: 0 auto;
}
.plantuml-render-warning {
    margin: 0 0 12px;
    color: #92400e;
    font-size: 0.95rem;
    line-height: 1.5;
}
.plantuml-render-error {
    color: #92400e;
    background: #fffbeb;
    border: 1px solid rgba(146, 64, 14, 0.24);
    border-radius: 14px;
}
img.wireframe {
    display: block;
    width: auto;
    height: auto;
    max-width: min(100%, 760px);
    max-height: min(68vh, 960px);
    margin: 1.25em auto;
    padding: 12px;
    object-fit: contain;
    background: linear-gradient(180deg, #ffffff, #f8fafc);
    border: 1px solid var(--border);
    border-radius: 12px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
    cursor: zoom-in;
}
.missing-image,
.blocked-image { color: #d32f2f; font-style: italic; padding: 1em; background: #fff3f3; border: 1px dashed #d32f2f; border-radius: 4px; }
.toc { background: #f8f9fa; border: 1px solid var(--border); border-radius: 8px; padding: 1.5em; margin-bottom: 2em; }
.toc h2 { margin-top: 0; font-size: 1.2em; }
.toc ul { list-style: none; margin: 0; padding: 0; }
.toc li { margin: 0.3em 0; }
.toc .toc-1 { font-weight: 600; }
.toc .toc-2 { padding-left: 1.5em; }
.toc .toc-3 { padding-left: 3em; font-size: 0.9em; }
.toc a { color: var(--accent); text-decoration: none; }
.toc a:hover { text-decoration: underline; }
.page-break { page-break-before: always; }
.editable-block {
    position: relative;
    transition: outline-color 0.15s ease, box-shadow 0.15s ease;
}
.editing-active .editable-block:hover {
    outline: 2px dashed rgba(15, 52, 96, 0.24);
    outline-offset: 6px;
}
.editable-selected {
    outline: 2px solid var(--accent);
    outline-offset: 6px;
    box-shadow: 0 0 0 6px rgba(15, 52, 96, 0.08);
}
.editing-active [contenteditable="true"] {
    cursor: text;
}
.editing-active [contenteditable="true"]:focus {
    outline: 2px solid rgba(15, 52, 96, 0.24);
    border-radius: 6px;
    background: rgba(217, 237, 247, 0.22);
}
.editing-active img.wireframe {
    cursor: pointer;
}
.editor-hidden {
    display: none !important;
}
.wireframe-lightbox {
    position: fixed;
    inset: 0;
    z-index: 1600;
    display: none;
    align-items: center;
    justify-content: center;
    padding: 24px;
    background: rgba(15, 23, 42, 0.74);
    backdrop-filter: blur(8px);
}
.wireframe-lightbox.is-open {
    display: flex;
}
.wireframe-lightbox__dialog {
    position: relative;
    display: grid;
    gap: 12px;
    width: min(96vw, 1440px);
    max-height: 94vh;
    padding: 18px;
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.98);
    box-shadow: 0 30px 80px rgba(15, 23, 42, 0.28);
}
.wireframe-lightbox__image {
    display: block;
    width: auto;
    max-width: 100%;
    max-height: calc(94vh - 96px);
    margin: 0 auto;
    object-fit: contain;
}
.wireframe-lightbox__caption {
    font-size: 0.92rem;
    color: var(--muted);
    text-align: center;
}
.wireframe-lightbox__close {
    position: absolute;
    top: 12px;
    right: 12px;
}
@media print {
    body { background: #fff; }
    .editor-shell { max-width: none; padding: 0; }
    .document-chrome { margin-bottom: 18px; }
    .doc-hero { padding: 20px; box-shadow: none; }
    .document-surface { max-width: none; padding: 0; border: none; border-radius: 0; box-shadow: none; }
    .editor-toolbar { display: none !important; }
    .wireframe-lightbox { display: none !important; }
    .toc { page-break-after: always; }
    .page-break { page-break-before: always; }
    table { page-break-inside: avoid; }
    img.wireframe { page-break-inside: avoid; max-width: 100%; max-height: 80vh; }
}
"""


MERMAID_BOOTSTRAP_JS = r"""
const MermaidRenderer = (() => {
  async function init() {
    if (!window.mermaid) return;
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: 'loose',
      theme: 'neutral',
      fontFamily: 'inherit',
    });

    try {
      await mermaid.run({ querySelector: 'pre.mermaid' });
    } catch (error) {
      console.error('Failed to render Mermaid diagrams.', error);
      document.querySelectorAll('pre.mermaid').forEach((node) => {
        node.classList.add('mermaid-render-error');
      });
    }
  }

  return { init };
})();

window.addEventListener('DOMContentLoaded', () => {
  MermaidRenderer.init();
});
"""


EDITOR_JS = r"""
const EditorApp = (() => {
  const BLOCK_SELECTOR = 'p, h1, h2, h3, h4, h5, h6, blockquote, ul, ol, table, pre, img.wireframe, hr';
  const TEXT_SELECTOR = 'p, h1, h2, h3, h4, h5, h6, blockquote, li, td, th';
  let selectedBlock = null;
  let editMode = false;

  const qs = (selector) => document.querySelector(selector);
  const qsa = (selector) => Array.from(document.querySelectorAll(selector));

  function getSurface() {
    return qs('#document-surface');
  }

  function getStatus() {
    return qs('#editor-status');
  }

  function getLightbox() {
    return qs('#wireframe-lightbox');
  }

  function closeLightbox() {
    const lightbox = getLightbox();
    if (!lightbox) return;
    lightbox.classList.remove('is-open');
    lightbox.setAttribute('aria-hidden', 'true');
  }

  function openLightbox(imageNode) {
    if (!(imageNode instanceof HTMLImageElement)) return;
    const lightbox = getLightbox();
    if (!lightbox) return;
    const preview = qs('#wireframe-lightbox-image');
    const caption = qs('#wireframe-lightbox-caption');
    if (!preview || !caption) return;
    preview.src = imageNode.currentSrc || imageNode.src;
    preview.alt = imageNode.alt || 'Wireframe preview';
    caption.textContent = imageNode.alt || 'Wireframe preview';
    lightbox.classList.add('is-open');
    lightbox.setAttribute('aria-hidden', 'false');
  }

  function ensureEditableBlocks() {
    qsa('#document-surface .editable-block').forEach((node) => node.classList.remove('editable-block'));
    qsa('#document-surface ' + BLOCK_SELECTOR).forEach((node) => {
      if (node.closest('#editor-toolbar')) return;
      node.classList.add('editable-block');
    });
  }

  function applyEditMode() {
    document.body.classList.toggle('editing-active', editMode);
    qsa('#document-surface ' + TEXT_SELECTOR).forEach((node) => {
      node.setAttribute('contenteditable', editMode ? 'true' : 'false');
      node.setAttribute('spellcheck', editMode ? 'true' : 'false');
    });
    const toggle = qs('[data-action="toggle-edit"]');
    if (toggle) {
      toggle.textContent = editMode ? 'Disable Editing' : 'Enable Editing';
      toggle.classList.toggle('is-primary', editMode);
    }
    getStatus().textContent = editMode
      ? 'Editing enabled. Click a block to select it, then edit text or use the toolbar.'
      : 'Editing disabled. Enable it to modify text, replace images, or add/remove blocks.';
  }

  function selectBlock(node) {
    if (selectedBlock) selectedBlock.classList.remove('editable-selected');
    selectedBlock = node;
    if (selectedBlock) selectedBlock.classList.add('editable-selected');
    updateSelectionStatus();
  }

  function updateSelectionStatus() {
    if (!selectedBlock) return;
    const label = selectedBlock.tagName.toLowerCase();
    getStatus().textContent = editMode
      ? `Editing enabled. Selected ${label} block.`
      : `Selected ${label} block. Enable editing to modify it.`;
  }

  function closestBlock(target) {
    if (!(target instanceof Element)) return null;
    return target.closest(BLOCK_SELECTOR);
  }

  function addParagraph() {
    const p = document.createElement('p');
    p.textContent = 'New paragraph';
    insertAfterSelection(p);
  }

  function addHeading() {
    const h = document.createElement('h2');
    h.textContent = 'New section';
    insertAfterSelection(h);
  }

  function addImageFromFile(file, replace = false) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const img = replace && selectedBlock?.tagName === 'IMG'
        ? selectedBlock
        : document.createElement('img');
      img.src = reader.result;
      img.alt = file.name.replace(/\.[^.]+$/, '');
      img.className = 'wireframe editable-block';
      if (!replace || selectedBlock?.tagName !== 'IMG') {
        insertAfterSelection(img);
      }
      ensureEditableBlocks();
      selectBlock(img);
    };
    reader.readAsDataURL(file);
  }

  function requestImage(replace = false) {
    const input = qs('#editor-image-input');
    input.dataset.replace = replace ? 'true' : 'false';
    input.click();
  }

  function insertAfterSelection(node) {
    const surface = getSurface();
    if (!surface) return;
    if (selectedBlock && selectedBlock.parentNode) {
      selectedBlock.parentNode.insertBefore(node, selectedBlock.nextSibling);
    } else {
      surface.appendChild(node);
    }
    ensureEditableBlocks();
    applyEditMode();
    selectBlock(node);
    if (node.matches?.(TEXT_SELECTOR)) node.focus();
  }

  function deleteSelected() {
    if (!selectedBlock) return;
    const next = selectedBlock.nextElementSibling || selectedBlock.previousElementSibling;
    selectedBlock.remove();
    ensureEditableBlocks();
    selectBlock(next ? closestBlock(next) || next : null);
    if (!selectedBlock) getStatus().textContent = 'Block removed.';
  }

  function duplicateSelected() {
    if (!selectedBlock) return;
    const clone = selectedBlock.cloneNode(true);
    selectedBlock.parentNode.insertBefore(clone, selectedBlock.nextSibling);
    ensureEditableBlocks();
    applyEditMode();
    selectBlock(clone);
  }

  function rebuildToc() {
    const toc = qs('.toc');
    const surface = getSurface();
    if (!toc || !surface) return;
    const headings = qsa('#document-surface h1, #document-surface h2, #document-surface h3');
    const list = toc.querySelector('ul');
    if (!list) return;
    list.innerHTML = '';
    headings.forEach((heading) => {
      const level = Number(heading.tagName.slice(1));
      const rawText = heading.textContent.trim() || heading.tagName;
      const slug = rawText.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || `section-${level}`;
      heading.id = slug;
      const li = document.createElement('li');
      li.className = `toc-${level}`;
      const a = document.createElement('a');
      a.href = `#${slug}`;
      a.textContent = rawText;
      li.appendChild(a);
      list.appendChild(li);
    });
  }

  function prepareCleanClone() {
    const clone = document.documentElement.cloneNode(true);
    clone.querySelectorAll('.editable-selected').forEach((node) => node.classList.remove('editable-selected'));
    clone.querySelectorAll('.editable-block').forEach((node) => node.classList.remove('editable-block'));
    clone.querySelectorAll('[contenteditable]').forEach((node) => node.removeAttribute('contenteditable'));
    clone.querySelectorAll('[spellcheck]').forEach((node) => node.removeAttribute('spellcheck'));
    clone.querySelectorAll('body').forEach((body) => body.classList.remove('editing-active'));
    clone.querySelectorAll('.wireframe-lightbox').forEach((node) => {
      node.classList.remove('is-open');
      node.setAttribute('aria-hidden', 'true');
    });
    return clone;
  }

  function downloadEditedHtml() {
    rebuildToc();
    const html = '<!DOCTYPE html>\n' + prepareCleanClone().outerHTML;
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${document.title || 'ba-output'}-edited.html`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  function bindEvents() {
    document.addEventListener('click', (event) => {
      const actionTarget = event.target.closest('[data-action]');
      if (actionTarget) {
        const action = actionTarget.dataset.action;
        if (action === 'toggle-edit') {
          editMode = !editMode;
          applyEditMode();
        } else if (action === 'add-paragraph') {
          addParagraph();
        } else if (action === 'add-heading') {
          addHeading();
        } else if (action === 'add-image') {
          requestImage(false);
        } else if (action === 'replace-image') {
          requestImage(true);
        } else if (action === 'delete-block') {
          deleteSelected();
        } else if (action === 'duplicate-block') {
          duplicateSelected();
        } else if (action === 'rebuild-toc') {
          rebuildToc();
          getStatus().textContent = 'Table of contents refreshed.';
        } else if (action === 'download-html') {
          downloadEditedHtml();
        } else if (action === 'close-lightbox') {
          closeLightbox();
        }
        event.preventDefault();
        return;
      }

      const block = closestBlock(event.target);
      if (block && block.closest('#document-surface')) {
        selectBlock(block);
        if (!editMode && block.tagName === 'IMG' && block.classList.contains('wireframe')) {
          openLightbox(block);
        }
      }

      const lightbox = event.target.closest('#wireframe-lightbox');
      if (lightbox && event.target === lightbox) {
        closeLightbox();
      }
    });

    document.addEventListener('dblclick', (event) => {
      const image = event.target.closest('img.wireframe');
      if (!image || !image.closest('#document-surface')) return;
      openLightbox(image);
    });

    qs('#editor-image-input')?.addEventListener('change', (event) => {
      const input = event.target;
      const [file] = input.files || [];
      addImageFromFile(file, input.dataset.replace === 'true');
      input.value = '';
    });

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        closeLightbox();
      }
    });
  }

  function init() {
    ensureEditableBlocks();
    bindEvents();
    editMode = true;
    applyEditMode();
    rebuildToc();
  }

  return { init };
})();

window.addEventListener('DOMContentLoaded', EditorApp.init);
"""


def default_base_dir(md_path: Path) -> Path:
    """Preserve the original relative image lookup behavior."""
    return md_path.parent.parent.parent


def wrap_docsengine(html_path: Path) -> Path:
    """Re-wrap existing HTML output in DocsEngine Material Design 3 template."""
    import json as _json
    from datetime import datetime as _datetime

    template_dir = REPO_ROOT / "templates" / "html"
    shell_template = (template_dir / "doc-engine-shell.html").read_text(encoding="utf-8")
    tailwind_config = (template_dir / "doc-engine-tailwind.html").read_text(encoding="utf-8")

    orig_html = html_path.read_text(encoding="utf-8")

    # Extract title, body, doc_type from existing HTML
    title_m = re.search(r"<title>(.*?)</title>", orig_html)
    title = title_m.group(1) if title_m else "BA-kit Document"

    doc_type_m = re.search(r'data-doc-type="(\w+)"', orig_html)
    doc_type = doc_type_m.group(1) if doc_type_m else "srs"

    body_m = re.search(r'<main[^>]*>(.*?)</main>', orig_html, re.DOTALL)
    body = body_m.group(1) if body_m else orig_html

    # Extract headings for TOC
    headings = []
    for m in re.finditer(r'<(h[23])\s+id="([^"]+)"[^>]*>(.*?)</\1>', body, re.DOTALL):
        level = int(m.group(1)[1])
        text = re.sub(r'<[^>]+>', '', m.group(3)).strip()
        headings.append({"level": level, "id": m.group(2), "text": text})

    SECTION_ICONS = {
        "muc-dich-va-pham-vi": "info", "yeu-cau-chuc-nang": "checklist",
        "user-stories": "list_alt", "dac-ta-use-case": "account_tree",
        "mo-ta-man-hinh": "description", "yeu-cau-phi-chuc-nang": "speed",
        "so-do-luong-du-lieu": "account_tree", "so-do-thuc-the-quan-he": "storage",
        "tham-chieu-quy-tac-thong-diep-dung-chung": "bookmark",
    }
    toc_items = ""
    for h in headings:
        icon = SECTION_ICONS.get(h["id"], "article")
        indent = "ml-4" if h["level"] == 3 else ""
        toc_items += f"""<li>
<a class="group relative flex items-center px-6 py-1.5 {indent} text-on-surface-variant border-l-4 border-transparent hover:bg-surface-container-high transition-all" href="#{h['id']}">
<span class="material-symbols-outlined mr-3 text-[18px]">{icon}</span>
<span class="font-label-md text-label-md text-[13px]">{escape(h['text'])}</span>
</a>
</li>\n"""

    section_ids = _json.dumps([h["id"] for h in headings])

    # Badge mapping
    badges = {"srs": "SRS", "frd": "FRD", "stories": "User Stories", "intake": "Intake"}
    badge = badges.get(doc_type, "BA-kit")

    project_name = html_path.parent.name if html_path.parent.name != "." else "Project"

    fill = {
        "{title}": escape(title),
        "{doc_type}": doc_type,
        "{badge}": badge,
        "{project_name}": project_name,
        "{toc_items}": toc_items,
        "{section_ids_json}": section_ids,
        "{body}": body,
        "{summary}": f"Tài liệu {badge} — BA-kit compiled output",
        "{generated_date}": _datetime.now().strftime("%Y-%m-%d %H:%M"),
        "{footer_text}": "Generated by BA-kit",
        "{tailwind_config}": tailwind_config,
        "{print_styles}": "@media print { aside { display: none; } main { margin-left: 0 !important; } .content table { display: table; } .page-break { page-break-before: always; } }",
    }
    docs_html = shell_template
    for key, val in fill.items():
        docs_html = docs_html.replace(key, val)

    html_path.write_text(docs_html, encoding="utf-8")
    return html_path


def convert(md_path: Path, *, base_dir: Path | None = None, editor_enabled: bool = False, output: Path | None = None) -> Path:
    """Convert any BA markdown to HTML with embedded images and Mermaid support."""
    if base_dir is None:
        base_dir = default_base_dir(md_path)
    base_dir = base_dir.resolve()
    md = md_path.read_text(encoding="utf-8")

    # Convert wireframe file references to embedded images
    # Pattern: `path/to/image.png`
    md = re.sub(
        r"`([^`]+\.png)`",
        r"![\1](\1)",
        md,
    )

    plantuml_server = normalize_plantuml_server(os.environ.get("BA_KIT_PLANTUML_SERVER"))
    plantuml_command = os.environ.get("BA_KIT_PLANTUML_COMMAND")
    auto_install_plantuml = os.environ.get("BA_KIT_AUTO_INSTALL_PLANTUML") == "1"
    resolved_plantuml_command, _ = resolve_plantuml_command(
        plantuml_command,
        auto_install=auto_install_plantuml,
    )
    body = md_to_html(
        md,
        base_dir,
        plantuml_server=plantuml_server,
        plantuml_command=resolved_plantuml_command,
    )
    doc_type, document_shell = render_document_shell(md, md_path)
    title = extract_title(md, md_path)

    editor_script = f"<script>{EDITOR_JS}</script>" if editor_enabled else ""
    editor_toolbar = """  <div id="editor-toolbar" class="editor-toolbar">
    <div class="editor-toolbar__group">
      <button class="editor-button is-primary" data-action="toggle-edit" type="button">Tắt chỉnh sửa</button>
      <button class="editor-button" data-action="add-paragraph" type="button">Thêm đoạn văn</button>
      <button class="editor-button" data-action="add-heading" type="button">Thêm tiêu đề</button>
      <button class="editor-button" data-action="add-image" type="button">Thêm ảnh</button>
      <button class="editor-button" data-action="replace-image" type="button">Thay ảnh</button>
      <button class="editor-button" data-action="duplicate-block" type="button">Nhân đôi khối</button>
      <button class="editor-button is-danger" data-action="delete-block" type="button">Xóa khối</button>
      <button class="editor-button" data-action="rebuild-toc" type="button">Làm mới mục lục</button>
      <button class="editor-button" data-action="download-html" type="button">Tải HTML đã chỉnh</button>
    </div>
    <div id="editor-status" class="editor-toolbar__status">Chế độ chỉnh sửa đang bật. Nhấn vào một khối để chọn, sau đó chỉnh nội dung hoặc dùng thanh công cụ.</div>
    <div class="editor-help">Bạn có thể chỉnh văn bản trực tiếp, thay ảnh wireframe từ file local, thêm tiêu đề hoặc đoạn văn mới, xóa khối, rồi tải về bản HTML sạch mà không cần chạm vào mã nguồn.</div>
  </div>
""" if editor_enabled else ""
    editor_input = '  <input id="editor-image-input" class="editor-hidden" type="file" accept="image/png,image/jpeg,image/webp,image/gif,image/svg+xml">\n' if editor_enabled else ""

    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)}</title>
<style>{CSS}</style>
<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
{editor_script}
</head>
<body data-doc-type="{doc_type}">
<div class="editor-shell">
{document_shell}{editor_toolbar}{editor_input}  <main id="document-surface" class="document-surface">
{body}
  </main>
  <div id="wireframe-lightbox" class="wireframe-lightbox" aria-hidden="true">
    <div class="wireframe-lightbox__dialog" role="dialog" aria-modal="true" aria-label="Wireframe preview">
      <button class="editor-button wireframe-lightbox__close" data-action="close-lightbox" type="button">Close</button>
      <img id="wireframe-lightbox-image" class="wireframe-lightbox__image" alt="">
      <div id="wireframe-lightbox-caption" class="wireframe-lightbox__caption"></div>
    </div>
  </div>
</div>
<script>{MERMAID_BOOTSTRAP_JS}</script>
</body>
</html>"""

    out_path = output.resolve() if output else md_path.with_suffix(".html")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


def aggregate_modules(modules_dir: Path, base_dir: Path | None, editor_enabled: bool = False):
    """Aggregate FRD and SRS modules into unified HTML files."""
    compiled_dir = modules_dir.parent / "04_compiled"
    compiled_dir.mkdir(parents=True, exist_ok=True)
    
    for doc_type in ["frd", "srs"]:
        md_files = sorted(modules_dir.rglob(f"{doc_type}.md"))
        if not md_files:
            continue
            
        combined_md = []
        # Keep track of multiple copies of frontmatter/metadata.
        # We process them so we only keep the first file's metadata table.
        # But for MVP, concatenating them works because the parser reads 
        # the first valid title and sets the rest.
        for file in md_files:
            module_name = file.parent.name
            combined_md.append(f"## Module: {module_name.title().replace('-', ' ')}\n")
            combined_md.append(file.read_text(encoding="utf-8"))
            
        temp_md_path = compiled_dir / f"compiled-{doc_type}.md"
        temp_md_path.write_text("\n<br>\n".join(combined_md), encoding="utf-8")
        
        out = convert(temp_md_path, base_dir=base_dir, editor_enabled=editor_enabled)
        temp_md_path.unlink()  # Cleanup the temporary concatenated markdown file
        print(f"Generated aggregate: {out}")

def main():
    parser = argparse.ArgumentParser(description="Convert BA markdown to HTML with Mermaid/PlantUML diagrams and embedded images")
    parser.add_argument("input", help="Path to markdown file or 03_modules directory (for aggregate)")
    parser.add_argument(
        "--base-dir",
        help="Project root used to resolve relative image references",
    )
    parser.add_argument(
        "--plantuml-server",
        help=(
            "Optional approved PlantUML server URL. "
            "Defaults to BA_KIT_PLANTUML_SERVER; if unset, no remote PlantUML fetch is emitted."
        ),
    )
    parser.add_argument(
        "--plantuml-command",
        help=(
            "Path to a local `plantuml` executable. "
            "Defaults to BA_KIT_PLANTUML_COMMAND or `plantuml` on PATH."
        ),
    )
    parser.add_argument(
        "--auto-install-plantuml",
        action="store_true",
        help="Attempt to install PlantUML locally before falling back to a configured server.",
    )
    parser.add_argument(
        "--with-editor",
        action="store_true",
        help="Generate HTML with the in-browser editing toolbar",
    )
    parser.add_argument(
        "--no-editor",
        dest="with_editor",
        action="store_false",
        help="Generate HTML without the in-browser editing toolbar (default)",
    )
    parser.set_defaults(with_editor=False)
    parser.add_argument(
        "--aggregate",
        action="store_true",
        help="Crawl a directory and compile matching module deliverables into a unified html file under 04_compiled",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output HTML file path (default: auto from input name with .html suffix)",
    )
    parser.add_argument(
        "--docsengine",
        action="store_true",
        help="Use DocsEngine Material Design 3 template (sidebar TOC, Tailwind, Google Fonts)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    base = Path(args.base_dir).resolve() if args.base_dir else None
    if args.plantuml_server:
        os.environ["BA_KIT_PLANTUML_SERVER"] = normalize_plantuml_server(args.plantuml_server) or ""
    if args.plantuml_command:
        os.environ["BA_KIT_PLANTUML_COMMAND"] = args.plantuml_command
    if args.auto_install_plantuml:
        os.environ["BA_KIT_AUTO_INSTALL_PLANTUML"] = "1"

    if args.aggregate:
        aggregate_modules(input_path, base_dir=base, editor_enabled=args.with_editor)
    else:
        out = convert(
            input_path,
            base_dir=base,
            editor_enabled=args.with_editor,
            output=args.output,
        )
        if args.docsengine:
            out = wrap_docsengine(out)
        print(f"Generated: {out}")


if __name__ == "__main__":
    main()
