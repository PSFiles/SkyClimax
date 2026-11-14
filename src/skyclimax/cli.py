"""Command line interface for the SkyClimax analysis tools.

Every subcommand is read-only: nothing in the extracted package is modified and
nothing is written except an explicit ``--json`` / ``--out`` destination.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from . import __version__
from .adx import parse_adx
from .farc import extract_all, parse_farc
from .inventory import build_inventory, write_json
from .pkg import parse_pkg_header
from .psarc import parse_psarc
from .selfheader import parse_self_header
from .sfo import sfo_summary


def _emit(document: dict[str, Any], json_path: str | None) -> None:
    if json_path:
        write_json(document, json_path)
        print(f"wrote {json_path}")
        return
    print(json.dumps(document, indent=2))


def cmd_pkg_info(args: argparse.Namespace) -> int:
    _emit(parse_pkg_header(args.pkg).to_dict(), args.json)
    return 0


def cmd_self_info(args: argparse.Namespace) -> int:
    _emit(parse_self_header(args.self_file).to_dict(), args.json)
    return 0


def cmd_sfo(args: argparse.Namespace) -> int:
    _emit(sfo_summary(args.sfo), args.json)
    return 0


def cmd_farc(args: argparse.Namespace) -> int:
    archive = parse_farc(args.farc)
    if args.extract:
        written = extract_all(archive, args.extract)
        print(f"extracted {len(written)} file(s) to {args.extract}")
    _emit(archive.to_dict(), args.json)
    return 0


def cmd_adx(args: argparse.Namespace) -> int:
    _emit(parse_adx(args.adx).to_dict(), args.json)
    return 0


def cmd_psarc(args: argparse.Namespace) -> int:
    _emit(parse_psarc(args.psarc).to_dict(), args.json)
    return 0


def cmd_inventory(args: argparse.Namespace) -> int:
    inventory = build_inventory(args.root)
    _emit(inventory.to_dict(), args.json)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skyclimax",
        description="Read-only analysis tools for After Burner Climax (PS3, NPUB30151).",
    )
    parser.add_argument("--version", action="version", version=f"skyclimax {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("pkg-info", help="parse the plaintext header of a PS3 .pkg")
    p.add_argument("pkg", type=Path)
    p.add_argument("--json", help="write the report to this path")
    p.set_defaults(func=cmd_pkg_info)

    p = sub.add_parser("self-info", help="parse a SELF header (no decryption)")
    p.add_argument("self_file", type=Path, metavar="SELF")
    p.add_argument("--json", help="write the report to this path")
    p.set_defaults(func=cmd_self_info)

    p = sub.add_parser("sfo", help="parse PARAM.SFO")
    p.add_argument("sfo", type=Path)
    p.add_argument("--json", help="write the report to this path")
    p.set_defaults(func=cmd_sfo)

    p = sub.add_parser("farc", help="list or extract a Sega FArc archive")
    p.add_argument("farc", type=Path)
    p.add_argument("--extract", metavar="DIR", help="write entry payloads to DIR")
    p.add_argument("--json", help="write the report to this path")
    p.set_defaults(func=cmd_farc)

    p = sub.add_parser("adx", help="parse a CRI ADX header")
    p.add_argument("adx", type=Path)
    p.add_argument("--json", help="write the report to this path")
    p.set_defaults(func=cmd_adx)

    p = sub.add_parser("psarc", help="parse a PSARC header and report TOC state")
    p.add_argument("psarc", type=Path)
    p.add_argument("--json", help="write the report to this path")
    p.set_defaults(func=cmd_psarc)

    p = sub.add_parser("inventory", help="classify every file below a directory")
    p.add_argument("root", type=Path)
    p.add_argument("--json", help="write the report to this path")
    p.set_defaults(func=cmd_inventory)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (OSError, ValueError, EOFError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
