#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2026-04-08

from pathlib import Path


def format_size(size_bytes):
    if size_bytes >= 1024 ** 4:
        return f"{size_bytes / (1024 ** 4):.1f}T"
    if size_bytes >= 1024 ** 3:
        return f"{size_bytes / (1024 ** 3):.1f}G"
    if size_bytes >= 1024 ** 2:
        return f"{size_bytes / (1024 ** 2):.1f}M"
    if size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f}K"
    return f"{size_bytes}B"


def size_ratio(size, total):
    if total == 0:
        return 0.0
    return size / total


def bar_string(ratio, width):
    filled = int(ratio * width)
    return "#" * filled + " " * (width - filled)


def scan_entry(path):
    try:
        if path.is_symlink():
            stat = path.lstat()
            return {
                "path": path,
                "name": path.name,
                "size": stat.st_size,
                "is_dir": False,
                "is_symlink": True,
                "error": None,
            }
        if path.is_file():
            return {
                "path": path,
                "name": path.name,
                "size": path.stat().st_size,
                "is_dir": False,
                "is_symlink": False,
                "error": None,
            }
        if path.is_dir():
            total = dir_size(path)
            return {
                "path": path,
                "name": path.name,
                "size": total,
                "is_dir": True,
                "is_symlink": False,
                "error": None,
            }
    except PermissionError:
        return {
            "path": path,
            "name": path.name,
            "size": 0,
            "is_dir": path.is_dir() if not path.is_symlink() else False,
            "is_symlink": path.is_symlink(),
            "error": "permission denied",
        }
    except OSError as e:
        return {
            "path": path,
            "name": path.name,
            "size": 0,
            "is_dir": False,
            "is_symlink": False,
            "error": str(e),
        }
    return {
        "path": path,
        "name": path.name,
        "size": 0,
        "is_dir": False,
        "is_symlink": False,
        "error": "unknown type",
    }


def dir_size(path):
    total = 0
    try:
        for child in path.iterdir():
            try:
                if child.is_symlink():
                    total += child.lstat().st_size
                elif child.is_file():
                    total += child.stat().st_size
                elif child.is_dir():
                    total += dir_size(child)
            except (PermissionError, OSError):
                continue
    except (PermissionError, OSError):
        pass
    return total


def scan_directory(path):
    path = Path(path).resolve()
    entries = []
    try:
        for child in path.iterdir():
            entries.append(scan_entry(child))
    except PermissionError:
        return [], 0
    except OSError:
        return [], 0

    entries.sort(key=lambda e: e["size"], reverse=True)
    total = sum(e["size"] for e in entries)
    return entries, total


def count_items(path):
    files = 0
    dirs = 0
    try:
        for child in Path(path).iterdir():
            if child.is_symlink():
                files += 1
            elif child.is_file():
                files += 1
            elif child.is_dir():
                dirs += 1
    except (PermissionError, OSError):
        pass
    return files, dirs
