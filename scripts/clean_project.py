#!/usr/bin/env python3
"""Cross-platform cleanup script for local build/test artifacts."""

from __future__ import annotations

import argparse
import fnmatch
import os
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REMOVE_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".next",
}
REMOVE_FILE_PATTERNS = [
    "*.pyc",
    "*.pyo",
    "*.tsbuildinfo",
    "*.tmp",
    "*.temp",
]
PRUNE_DIR_NAMES = {
    ".git",
    "venv",
    ".venv",
    "env",
    "ENV",
    "node_modules",
}


def iter_cleanup_targets(root: Path) -> tuple[list[Path], list[Path]]:
    dirs_to_remove: list[Path] = []
    files_to_remove: list[Path] = []

    for current_root, dir_names, file_names in os.walk(root, topdown=True):
        dir_names[:] = [d for d in dir_names if d not in PRUNE_DIR_NAMES]

        removable_dir_names = [d for d in dir_names if d in REMOVE_DIR_NAMES]
        for removable in removable_dir_names:
            dirs_to_remove.append(Path(current_root) / removable)

        dir_names[:] = [d for d in dir_names if d not in REMOVE_DIR_NAMES]

        current_root_path = Path(current_root)
        for file_name in file_names:
            if any(fnmatch.fnmatch(file_name, pattern) for pattern in REMOVE_FILE_PATTERNS):
                files_to_remove.append(current_root_path / file_name)

    unique_dirs = sorted(set(dirs_to_remove))
    unique_files = sorted(set(files_to_remove))
    return unique_dirs, unique_files


def delete_targets(dirs_to_remove: list[Path], files_to_remove: list[Path], dry_run: bool) -> int:
    removed = 0

    for directory in dirs_to_remove:
        print(f"[dir ] {directory.relative_to(ROOT)}")
        if not dry_run:
            shutil.rmtree(directory, ignore_errors=True)
        removed += 1

    for file_path in files_to_remove:
        print(f"[file] {file_path.relative_to(ROOT)}")
        if not dry_run:
            try:
                file_path.unlink()
            except FileNotFoundError:
                pass
        removed += 1

    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean local build/test artifacts.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be removed.")
    args = parser.parse_args()

    dirs_to_remove, files_to_remove = iter_cleanup_targets(ROOT)
    removed_count = delete_targets(dirs_to_remove, files_to_remove, args.dry_run)

    mode = "would be removed" if args.dry_run else "removed"
    print(f"Cleanup complete: {removed_count} target(s) {mode}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
