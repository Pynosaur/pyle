#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2026-04-08

import curses
from pathlib import Path
from .scanner import (
    scan_directory, format_size, size_ratio, bar_string,
    count_items, invalidate_cache,
)


COLOR_DIR = 1
COLOR_FILE = 2
COLOR_SYMLINK = 3
COLOR_ERROR = 4
COLOR_BAR_LOW = 5
COLOR_BAR_MED = 6
COLOR_BAR_HIGH = 7
COLOR_HEADER = 8
COLOR_SELECTED = 9
COLOR_STATUS = 10
COLOR_PERCENT = 11


def init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(COLOR_DIR, curses.COLOR_BLUE, -1)
    curses.init_pair(COLOR_FILE, curses.COLOR_WHITE, -1)
    curses.init_pair(COLOR_SYMLINK, curses.COLOR_CYAN, -1)
    curses.init_pair(COLOR_ERROR, curses.COLOR_RED, -1)
    curses.init_pair(COLOR_BAR_LOW, curses.COLOR_GREEN, -1)
    curses.init_pair(COLOR_BAR_MED, curses.COLOR_YELLOW, -1)
    curses.init_pair(COLOR_BAR_HIGH, curses.COLOR_RED, -1)
    curses.init_pair(COLOR_HEADER, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(COLOR_SELECTED, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(COLOR_STATUS, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(COLOR_PERCENT, curses.COLOR_MAGENTA, -1)


def bar_color(ratio):
    if ratio >= 0.5:
        return COLOR_BAR_HIGH
    if ratio >= 0.2:
        return COLOR_BAR_MED
    return COLOR_BAR_LOW


def _safe_addnstr(stdscr, row, col, text, length, attr=0):
    try:
        stdscr.addnstr(row, col, text, length, attr)
    except curses.error:
        pass


def draw_header(stdscr, current_path, total_size, max_x):
    header = f" pyle: {current_path}"
    total_str = f"Total: {format_size(total_size)} "
    pad = max(0, max_x - len(header) - len(total_str))
    line = (header + " " * pad + total_str)[:max_x]
    stdscr.attron(curses.color_pair(COLOR_HEADER) | curses.A_BOLD)
    _safe_addnstr(stdscr, 0, 0, line.ljust(max_x), max_x)
    stdscr.attroff(curses.color_pair(COLOR_HEADER) | curses.A_BOLD)


def draw_entry(stdscr, row, entry, total, selected, max_x, bar_width):
    if row < 0:
        return

    ratio = size_ratio(entry["size"], total)
    pct = ratio * 100
    size_str = format_size(entry["size"])
    pct_str = f"{pct:5.1f}%"
    bar = bar_string(ratio, bar_width)

    name = entry["name"]
    if entry["is_dir"]:
        name += "/"
    if entry["is_symlink"]:
        name = "@ " + name
    if entry["error"]:
        name += " [!]"

    size_col = 1
    pct_col = size_col + 8
    bar_col = pct_col + 7
    name_col = bar_col + bar_width + 1

    available = max_x - name_col - 1
    if available > 0 and len(name) > available:
        name = name[:available - 1] + "~"

    if selected:
        stdscr.attron(curses.color_pair(COLOR_SELECTED))
        _safe_addnstr(stdscr, row, 0, " " * max_x, max_x)
        stdscr.attroff(curses.color_pair(COLOR_SELECTED))

    attr = curses.color_pair(COLOR_SELECTED) if selected else 0

    _safe_addnstr(
        stdscr, row, size_col, f"{size_str:>7}", 7,
        attr | curses.A_BOLD,
    )

    pct_attr = attr if selected else curses.color_pair(COLOR_PERCENT)
    _safe_addnstr(stdscr, row, pct_col, pct_str, 6, pct_attr)

    bc = bar_color(ratio)
    b_attr = attr if selected else curses.color_pair(bc)
    _safe_addnstr(stdscr, row, bar_col, "[", 1, attr)
    _safe_addnstr(
        stdscr, row, bar_col + 1, bar, bar_width,
        b_attr | curses.A_BOLD,
    )
    _safe_addnstr(stdscr, row, bar_col + 1 + bar_width, "]", 1, attr)

    if available > 0:
        if selected:
            name_attr = curses.color_pair(COLOR_SELECTED) | curses.A_BOLD
        elif entry["error"]:
            name_attr = curses.color_pair(COLOR_ERROR)
        elif entry["is_symlink"]:
            name_attr = curses.color_pair(COLOR_SYMLINK)
        elif entry["is_dir"]:
            name_attr = curses.color_pair(COLOR_DIR) | curses.A_BOLD
        else:
            name_attr = curses.color_pair(COLOR_FILE)
        _safe_addnstr(stdscr, row, name_col, name, available, name_attr)


def draw_status(stdscr, row, current_path, entries, cursor, max_x):
    files, dirs = count_items(current_path)
    entry = entries[cursor] if entries else None

    left = f" {dirs} dirs, {files} files"
    right = f" {entry['name']} {format_size(entry['size'])} " if entry else ""

    pad = max(0, max_x - len(left) - len(right))
    line = (left + " " * pad + right)[:max_x]

    stdscr.attron(curses.color_pair(COLOR_STATUS))
    _safe_addnstr(stdscr, row, 0, line.ljust(max_x), max_x)
    stdscr.attroff(curses.color_pair(COLOR_STATUS))


def draw_help(stdscr, row, max_x):
    keys = (" q:quit  jk:nav  l/enter:open"
            "  h:back  d:del  r:refresh  s:sort")
    _safe_addnstr(stdscr, row, 0, keys[:max_x], max_x, curses.A_DIM)


def run_ui(stdscr, start_path):
    curses.curs_set(0)
    init_colors()
    stdscr.timeout(50)

    history = []
    current_path = Path(start_path).resolve()
    entries, total = scan_directory(current_path)
    cursor = 0
    scroll_offset = 0
    sort_by_name = False

    while True:
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()

        if max_y < 5 or max_x < 40:
            _safe_addnstr(stdscr, 0, 0, "Terminal too small", 18)
            stdscr.refresh()
            key = stdscr.getch()
            if key == ord("q"):
                break
            continue

        bar_width = min(20, max(8, (max_x - 30) // 3))

        draw_header(stdscr, str(current_path), total, max_x)

        content_start = 1
        content_end = max_y - 2
        visible_rows = content_end - content_start

        if cursor < scroll_offset:
            scroll_offset = cursor
        elif cursor >= scroll_offset + visible_rows:
            scroll_offset = cursor - visible_rows + 1

        if not entries:
            _safe_addnstr(
                stdscr, content_start, 2,
                "(empty directory)", 17, curses.A_DIM,
            )
        else:
            for i in range(visible_rows):
                idx = scroll_offset + i
                if idx >= len(entries):
                    break
                draw_entry(
                    stdscr, content_start + i, entries[idx],
                    total, idx == cursor, max_x, bar_width,
                )

        draw_status(
            stdscr, max_y - 2, current_path,
            entries, cursor, max_x,
        )
        draw_help(stdscr, max_y - 1, max_x)

        stdscr.refresh()

        key = stdscr.getch()

        if key == -1:
            continue

        if key == ord("q") or key == 27:
            break

        elif key == curses.KEY_UP or key == ord("k"):
            if cursor > 0:
                cursor -= 1

        elif key == curses.KEY_DOWN or key == ord("j"):
            if cursor < len(entries) - 1:
                cursor += 1

        elif key in (
            curses.KEY_RIGHT, ord("l"), ord("\n"), curses.KEY_ENTER,
        ):
            if (entries and entries[cursor]["is_dir"]
                    and not entries[cursor]["error"]):
                history.append(
                    (current_path, cursor, scroll_offset, entries, total),
                )
                current_path = entries[cursor]["path"]
                entries, total = scan_directory(current_path)
                if sort_by_name:
                    entries.sort(key=lambda e: e["name"].lower())
                cursor = 0
                scroll_offset = 0

        elif key == curses.KEY_LEFT or key == ord("h"):
            if history:
                prev = history.pop()
                current_path = prev[0]
                cursor = prev[1]
                scroll_offset = prev[2]
                entries = prev[3]
                total = prev[4]
            elif current_path.parent != current_path:
                old_name = current_path.name
                current_path = current_path.parent
                entries, total = scan_directory(current_path)
                if sort_by_name:
                    entries.sort(key=lambda e: e["name"].lower())
                cursor = 0
                for i, e in enumerate(entries):
                    if e["name"] == old_name:
                        cursor = i
                        break
                scroll_offset = max(0, cursor - visible_rows // 2)

        elif key == ord("r"):
            invalidate_cache(str(current_path))
            entries, total = scan_directory(current_path)
            if sort_by_name:
                entries.sort(key=lambda e: e["name"].lower())
            if cursor >= len(entries):
                cursor = max(0, len(entries) - 1)

        elif key == ord("s"):
            sort_by_name = not sort_by_name
            if sort_by_name:
                entries.sort(key=lambda e: e["name"].lower())
            else:
                entries.sort(key=lambda e: e["size"], reverse=True)

        elif key == ord("d"):
            if entries:
                entry = entries[cursor]
                target = entry["path"]
                _safe_addnstr(
                    stdscr, max_y - 1, 0,
                    f" Delete {entry['name']}? (y/N) ".ljust(max_x),
                    max_x,
                    curses.color_pair(COLOR_ERROR) | curses.A_BOLD,
                )
                stdscr.refresh()
                stdscr.timeout(-1)
                confirm = stdscr.getch()
                stdscr.timeout(50)
                if confirm in (ord("y"), ord("Y")):
                    try:
                        if target.is_file() or target.is_symlink():
                            target.unlink()
                        elif target.is_dir():
                            _rmtree(target)
                        invalidate_cache(str(current_path))
                        entries, total = scan_directory(current_path)
                        if sort_by_name:
                            entries.sort(
                                key=lambda e: e["name"].lower(),
                            )
                        if cursor >= len(entries):
                            cursor = max(0, len(entries) - 1)
                    except OSError:
                        pass

        elif key == curses.KEY_PPAGE:
            cursor = max(0, cursor - visible_rows)

        elif key == curses.KEY_NPAGE:
            cursor = min(len(entries) - 1, cursor + visible_rows)

        elif key == curses.KEY_HOME or key == ord("g"):
            cursor = 0
            scroll_offset = 0

        elif key == ord("G"):
            cursor = max(0, len(entries) - 1)


def _rmtree(path):
    for child in path.iterdir():
        if child.is_dir() and not child.is_symlink():
            _rmtree(child)
        else:
            child.unlink()
    path.rmdir()
