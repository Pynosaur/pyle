#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: @spacemany2k38
# 2026-04-08

import os
from pathlib import Path

_size_cache = {}


def invalidate_cache(path=None):
    if path is None:
        _size_cache.clear()
    else:
        key = str(path)
        to_remove = [k for k in _size_cache if k.startswith(key)]
        for k in to_remove:
            del _size_cache[k]


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


def dir_size(path):
    """Recursive directory size using os.scandir (C-backed, avoids
    extra stat syscalls since DirEntry caches inode info)."""
    key = str(path)
    if key in _size_cache:
        return _size_cache[key]

    total = 0
    try:
        with os.scandir(path) as it:
            for entry in it:
                try:
                    if entry.is_symlink():
                        total += entry.stat(follow_symlinks=False).st_size
                    elif entry.is_file(follow_symlinks=False):
                        total += entry.stat(follow_symlinks=False).st_size
                    elif entry.is_dir(follow_symlinks=False):
                        total += dir_size(entry.path)
                except (PermissionError, OSError):
                    continue
    except (PermissionError, OSError):
        pass

    _size_cache[key] = total
    return total


def scan_entry_from_direntry(entry):
    """Build entry dict from an os.DirEntry (already has cached stat)."""
    try:
        if entry.is_symlink():
            st = entry.stat(follow_symlinks=False)
            return {
                "path": Path(entry.path),
                "name": entry.name,
                "size": st.st_size,
                "is_dir": False,
                "is_symlink": True,
                "error": None,
            }
        if entry.is_file(follow_symlinks=False):
            st = entry.stat(follow_symlinks=False)
            return {
                "path": Path(entry.path),
                "name": entry.name,
                "size": st.st_size,
                "is_dir": False,
                "is_symlink": False,
                "error": None,
            }
        if entry.is_dir(follow_symlinks=False):
            return {
                "path": Path(entry.path),
                "name": entry.name,
                "size": dir_size(entry.path),
                "is_dir": True,
                "is_symlink": False,
                "error": None,
            }
    except PermissionError:
        return {
            "path": Path(entry.path),
            "name": entry.name,
            "size": 0,
            "is_dir": False,
            "is_symlink": False,
            "error": "permission denied",
        }
    except OSError as e:
        return {
            "path": Path(entry.path),
            "name": entry.name,
            "size": 0,
            "is_dir": False,
            "is_symlink": False,
            "error": str(e),
        }
    return {
        "path": Path(entry.path),
        "name": entry.name,
        "size": 0,
        "is_dir": False,
        "is_symlink": False,
        "error": "unknown type",
    }


def scan_entry(path):
    """Scan a single path (fallback for non-DirEntry calls)."""
    try:
        if path.is_symlink():
            st = path.lstat()
            return {
                "path": path,
                "name": path.name,
                "size": st.st_size,
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
            return {
                "path": path,
                "name": path.name,
                "size": dir_size(str(path)),
                "is_dir": True,
                "is_symlink": False,
                "error": None,
            }
    except PermissionError:
        return {
            "path": path,
            "name": path.name,
            "size": 0,
            "is_dir": False,
            "is_symlink": False,
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


def scan_directory(path):
    """Scan directory using os.scandir for speed. Returns (entries, total)."""
    resolved = str(Path(path).resolve())
    entries = []
    try:
        with os.scandir(resolved) as it:
            for de in it:
                entries.append(scan_entry_from_direntry(de))
    except PermissionError:
        return [], 0
    except OSError:
        return [], 0

    entries.sort(key=lambda e: e["size"], reverse=True)
    total = sum(e["size"] for e in entries)
    return entries, total


def count_items(path):
    """Fast item count using os.scandir."""
    files = 0
    dirs = 0
    try:
        with os.scandir(str(path)) as it:
            for entry in it:
                try:
                    if entry.is_symlink():
                        files += 1
                    elif entry.is_file(follow_symlinks=False):
                        files += 1
                    elif entry.is_dir(follow_symlinks=False):
                        dirs += 1
                except (PermissionError, OSError):
                    continue
    except (PermissionError, OSError):
        pass
    return files, dirs
