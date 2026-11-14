#!/usr/bin/env python3
"""Verify that the en-US and pt-BR documentation trees are in parity.

Checks, in order:

1. every ``docs/en-US/**.md`` has a twin under ``docs/pt-BR/`` and vice versa;
2. both files have the same heading *structure* (count and nesting levels); the
   heading text is translated, so it is compared by level, not by wording;
3. both files contain the same number of fenced code blocks, with the same
   language tags, and identical bodies for code languages;
4. every relative link resolves inside its own language tree;
5. ``docs/README.md`` lists every document and its recorded status matches the
   status this script computes.

Exit codes: 0 = parity, 1 = parity violation, 2 = usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

SOURCE_LANG = "en-US"
TARGET_LANG = "pt-BR"

#: Fenced-block languages whose bodies must be byte-identical across languages.
CODE_LANGS = {
    "bash",
    "console",
    "powershell",
    "ps1",
    "cmd",
    "json",
    "yaml",
    "toml",
    "ini",
    "c",
    "cpp",
    "h",
    "python",
    "py",
    "cmake",
    "diff",
    "text",
    "log",
}

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
FENCE_RE = re.compile(r"^\s*```(\S*)")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
TODO_RE = re.compile(r"TODO\((pt-BR|en-US)\)")
STATUS_ROW_RE = re.compile(r"^\|\s*`?([^|`]+?)`?\s*\|\s*([a-z]+)\s*\|")


@dataclass
class DocInfo:
    path: Path
    headings: list[tuple[int, str]] = field(default_factory=list)
    code_blocks: list[tuple[str, str]] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    todos: list[str] = field(default_factory=list)


def read_doc(path: Path) -> DocInfo:
    info = DocInfo(path=path)
    lines = path.read_text(encoding="utf-8").splitlines()
    fence: tuple[str, list[str]] | None = None
    for line in lines:
        if fence is None:
            m = FENCE_RE.match(line)
            if m:
                fence = (m.group(1).lower(), [])
                continue
            m = HEADING_RE.match(line)
            if m:
                info.headings.append((len(m.group(1)), m.group(2)))
            info.links.extend(LINK_RE.findall(line))
            info.todos.extend(TODO_RE.findall(line))
        else:
            if line.strip().startswith("```"):
                info.code_blocks.append((fence[0], "\n".join(fence[1])))
                fence = None
            else:
                fence[1].append(line)
    return info


def relative_docs(root: Path) -> set[str]:
    return {p.relative_to(root).as_posix() for p in root.rglob("*.md")}


def check_pair(source: DocInfo, target: DocInfo) -> list[str]:
    problems: list[str] = []
    rel = source.path.name

    src_levels = [level for level, _ in source.headings]
    dst_levels = [level for level, _ in target.headings]
    if src_levels != dst_levels:
        problems.append(
            f"{rel}: heading structure differs "
            f"({len(src_levels)} heading(s) in {SOURCE_LANG} {src_levels[:8]}, "
            f"{len(dst_levels)} in {TARGET_LANG} {dst_levels[:8]})"
        )

    if len(source.code_blocks) != len(target.code_blocks):
        problems.append(
            f"{rel}: {len(source.code_blocks)} code block(s) in {SOURCE_LANG} vs "
            f"{len(target.code_blocks)} in {TARGET_LANG}"
        )
    else:
        for i, ((lang_a, body_a), (lang_b, body_b)) in enumerate(
            zip(source.code_blocks, target.code_blocks)
        ):
            if lang_a != lang_b:
                problems.append(f"{rel}: code block #{i + 1} language {lang_a!r} != {lang_b!r}")
            elif lang_a in CODE_LANGS and body_a != body_b:
                problems.append(f"{rel}: code block #{i + 1} ({lang_a}) body differs")

    return problems


def check_links(info: DocInfo, docs_root: Path) -> list[str]:
    problems: list[str] = []
    for target in info.links:
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        path_part = target.split("#", 1)[0]
        if not path_part:
            continue
        resolved = (info.path.parent / path_part).resolve()
        if not resolved.exists():
            problems.append(
                f"{info.path.name}: broken relative link {target!r} "
                f"(resolved to {resolved})"
            )
    return problems


def compute_status(source: DocInfo, target: DocInfo) -> str:
    if source.todos or target.todos:
        return "todo"
    return "synced"


def read_index(index_path: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    if not index_path.is_file():
        return rows
    for line in index_path.read_text(encoding="utf-8").splitlines():
        m = STATUS_ROW_RE.match(line.strip())
        if m and m.group(1) not in {"Document", "Documento"} and not set(m.group(1)) <= {"-"}:
            rows[m.group(1).strip()] = m.group(2)
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check parity between docs/en-US and docs/pt-BR."
    )
    parser.add_argument("--docs", default="docs", help="documentation root (default: docs)")
    parser.add_argument("--json", help="write the report as JSON to this path")
    parser.add_argument("--quiet", action="store_true", help="only print failures")
    args = parser.parse_args(argv)

    docs_root = Path(args.docs)
    src_root = docs_root / SOURCE_LANG
    dst_root = docs_root / TARGET_LANG
    if not src_root.is_dir() or not dst_root.is_dir():
        print(f"error: expected {src_root} and {dst_root}", file=sys.stderr)
        return 2

    src_files = relative_docs(src_root)
    dst_files = relative_docs(dst_root)

    problems: list[str] = []
    for missing in sorted(src_files - dst_files):
        problems.append(f"missing in {TARGET_LANG}: {missing}")
    for extra in sorted(dst_files - src_files):
        problems.append(f"missing in {SOURCE_LANG}: {extra}")

    statuses: dict[str, str] = {}
    for rel in sorted(src_files & dst_files):
        source = read_doc(src_root / rel)
        target = read_doc(dst_root / rel)
        problems.extend(check_pair(source, target))
        problems.extend(check_links(source, src_root))
        problems.extend(check_links(target, dst_root))
        statuses[rel] = compute_status(source, target)

    index_rows = read_index(docs_root / "README.md")
    for rel, status in sorted(statuses.items()):
        recorded = index_rows.get(rel)
        if recorded is None:
            problems.append(f"docs/README.md does not list {rel}")
        elif recorded != status:
            problems.append(
                f"docs/README.md records {rel} as {recorded!r} but it is {status!r}"
            )
    for rel in sorted(set(index_rows) - set(statuses)):
        problems.append(f"docs/README.md lists {rel}, which does not exist in both languages")

    report = {
        "source_language": SOURCE_LANG,
        "target_language": TARGET_LANG,
        "documents": len(statuses),
        "statuses": statuses,
        "problems": problems,
        "ok": not problems,
    }
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if problems:
        for problem in problems:
            print(f"FAIL {problem}", file=sys.stderr)
        print(f"\n{len(problems)} parity problem(s) across {len(statuses)} document pair(s).", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"docs parity OK: {len(statuses)} document pair(s) in sync")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
