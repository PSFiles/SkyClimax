#!/usr/bin/env python3
"""Apply SkyClimax's patches to the vendored ps3recomp checkout.

The toolkit is vendored, pinned and never edited by hand (ADR-0001). Fixes that
must live in the runtime are expressed here as idempotent, asserted edits so
they can be re-applied after a fresh checkout and reviewed as code.

Usage:
    python tools/patches/apply.py            # apply
    python tools/patches/apply.py --revert   # undo
    python tools/patches/apply.py --check    # report state, change nothing
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
VENDOR = ROOT / ".vendor/ps3recomp-src"
GCM = VENDOR / "libs/video/cellGcmSys.c"

# ---------------------------------------------------------------------------
# Patch 0001 -- cellGcmSetQueueHandler must reach the guest
#
# The title registers a queue handler (NID 0x0A862772) with a guest OPD
# (0x004D9558 in this build) and then blocks in sys_event_queue_receive on its
# own queue, waiting for the handler to run. The runtime stores the pointer in a
# host function-pointer variable and never invokes it; the comment at the
# SetQueueHandler site in upstream admits the path "is not modelled".
#
# Calling a guest OPD as a host function pointer would jump into guest code and
# crash, so the fix mirrors what the runtime already does for the flip handler:
# keep the OPD as a 32-bit guest address and dispatch it through
# g_ps3_guest_caller.
# ---------------------------------------------------------------------------

EDITS_0001 = [
    # 1. storage: host function pointer -> guest OPD
    (
        "static CellGcmQueueHandler    s_queue_handler    = NULL;",
        "/* SkyClimax: guest OPD, not a host pointer -- dispatched via\n"
        " * g_ps3_guest_caller like the flip handler (see patch 0001). */\n"
        "static u32 s_queue_handler_opd = 0;",
    ),
    # 2. the reset sites (two spacing variants in the upstream file)
    (
        "    s_queue_handler = NULL;",
        "    s_queue_handler_opd = 0;",
    ),
    (
        "    s_queue_handler    = NULL;",
        "    s_queue_handler_opd = 0;",
    ),
    # 3. the setter stores the guest address
    (
        "void cellGcmSetQueueHandler(CellGcmQueueHandler handler)\n"
        "{\n"
        '    printf("[cellGcmSys] SetQueueHandler(%p)\\n", (void*)(size_t)handler);\n'
        "    s_queue_handler = handler;\n"
        "}",
        "void cellGcmSetQueueHandler(CellGcmQueueHandler handler)\n"
        "{\n"
        '    printf("[cellGcmSys] SetQueueHandler(%p)\\n", (void*)(size_t)handler);\n'
        "    /* SkyClimax patch 0001: the argument is a guest OPD. */\n"
        "    s_queue_handler_opd = (u32)(uintptr_t)handler;\n"
        "}",
    ),
    # 4. fire it wherever the flip handler fires
    (
        "    if (s_flip_handler_opd && g_ps3_guest_caller && !gcm_flipcb_on_tick_only())\n"
        "        g_ps3_guest_caller(s_flip_handler_opd, 0, 0, 0, 0, 0, 0, 0, 0);  /* head 0 = primary display */",
        "    if (s_flip_handler_opd && g_ps3_guest_caller && !gcm_flipcb_on_tick_only())\n"
        "        g_ps3_guest_caller(s_flip_handler_opd, 0, 0, 0, 0, 0, 0, 0, 0);  /* head 0 = primary display */\n"
        "    /* SkyClimax patch 0001: the queue handler fires with the flip. */\n"
        "    if (s_queue_handler_opd && g_ps3_guest_caller)\n"
        "        g_ps3_guest_caller(s_queue_handler_opd, 0, 0, 0, 0, 0, 0, 0, 0);",
    ),
    (
        "    if (s_flip_handler_opd && g_ps3_guest_caller && !gcm_flipcb_on_tick_only())\n"
        "        g_ps3_guest_caller(s_flip_handler_opd, 0, 0, 0, 0, 0, 0, 0, 0);\n"
        "\n"
        "    return CELL_OK;\n"
        "}\n"
        "\n"
        "/* NID: 0x1BFAB6EE */",
        "    if (s_flip_handler_opd && g_ps3_guest_caller && !gcm_flipcb_on_tick_only())\n"
        "        g_ps3_guest_caller(s_flip_handler_opd, 0, 0, 0, 0, 0, 0, 0, 0);\n"
        "    /* SkyClimax patch 0001: the queue handler fires with the flip. */\n"
        "    if (s_queue_handler_opd && g_ps3_guest_caller)\n"
        "        g_ps3_guest_caller(s_queue_handler_opd, 0, 0, 0, 0, 0, 0, 0, 0);\n"
        "\n"
        "    return CELL_OK;\n"
        "}\n"
        "\n"
        "/* NID: 0x1BFAB6EE */",
    ),
]


def state(text: str) -> str:
    if "s_queue_handler_opd" in text:
        return "applied"
    if "s_queue_handler" in text:
        return "clean"
    return "unexpected"


def apply(revert: bool) -> int:
    if not GCM.is_file():
        print(f"error: {GCM} not found; run scripts/install-tools.ps1 first", file=sys.stderr)
        return 2
    text = GCM.read_text(encoding="utf-8")
    current = state(text)

    if revert:
        if current == "clean":
            print("already clean")
            return 0
        # Reverse order so the longer contexts match first.
        for new, old in reversed(EDITS_0001):
            if new not in text:
                print(f"error: cannot revert, anchor missing:\n{new[:80]}", file=sys.stderr)
                return 1
            text = text.replace(new, old)
        GCM.write_text(text, encoding="utf-8")
        print("reverted patch 0001")
        return 0

    if current == "applied":
        print("already applied")
        return 0
    if current == "unexpected":
        print("error: cellGcmSys.c has neither the original nor the patched form", file=sys.stderr)
        return 1

    for old, new in EDITS_0001:
        count = text.count(old)
        if count == 0:
            print(f"error: anchor not found:\n{old[:100]}", file=sys.stderr)
            return 1
        text = text.replace(old, new)
        print(f"  patched ({count} site(s)): {old.splitlines()[0][:64]}")
    GCM.write_text(text, encoding="utf-8")
    print("applied patch 0001")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply SkyClimax patches to the vendored toolkit.")
    parser.add_argument("--revert", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        if not GCM.is_file():
            print("vendored toolkit not present")
            return 2
        print(f"patch 0001: {state(GCM.read_text(encoding='utf-8'))}")
        return 0
    return apply(args.revert)


if __name__ == "__main__":
    raise SystemExit(main())
