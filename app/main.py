#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2026-04-08

import curses
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    __package__ = "app"

from app import __version__
from app.core.ui import run_ui
from app.utils.doc_reader import read_app_doc


def print_help():
    doc = read_app_doc('pyle')

    desc = doc.get('description', 'Interactive disk usage explorer')
    usage = doc.get('usage', ['pyle [DIRECTORY]'])

    print(f"pyle - {desc}")
    print("\nUSAGE:")
    for u in usage:
        print(f"    {u}")
    print("\nOPTIONS:")
    print("    -h, --help        Show help message")
    print("    -v, --version     Show version information")
    print("\nKEYBINDINGS:")
    print("    space             Open search bar (filter entries by name)")
    print("    ↑/k               Move cursor up")
    print("    ↓/j               Move cursor down")
    print("    →/l/Enter         Open directory")
    print("    ←/h               Go to parent directory")
    print("    PgUp/PgDn         Page up/down")
    print("    g/G               Go to first/last entry")
    print("    s                 Toggle sort (size/name)")
    print("    d                 Delete selected entry (confirms)")
    print("    r                 Refresh current directory")
    print("    q/Esc             Quit")


def print_version():
    doc = read_app_doc('pyle')
    print(doc.get('version', __version__))


def main():
    args = sys.argv[1:]

    if args and args[0] in ("-h", "--help", "help"):
        print_help()
        return 0

    if args and args[0] in ("-v", "--version"):
        print_version()
        return 0

    target = args[0] if args else "."
    target_path = Path(target)

    if not target_path.exists():
        print(f"pyle: '{target}' does not exist", file=sys.stderr)
        return 1

    if not target_path.is_dir():
        print(f"pyle: '{target}' is not a directory", file=sys.stderr)
        return 1

    try:
        curses.wrapper(lambda stdscr: run_ui(stdscr, target_path))
    except KeyboardInterrupt:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
