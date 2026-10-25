#!/usr/bin/env python3
"""Mirror file/directory names as zero-byte placeholders, excluding run logs."""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def is_log(path):
    name = path.name.lower()
    return (name.endswith(".log") or ".log." in name
            or name == "crash-after-images.txt"
            or (name.startswith("webkit-") and name.endswith("-inspection.txt")))


def inventory(source):
    """Read names only; do not open or copy any source file's contents."""
    source = source.resolve(strict=True)
    if not source.is_dir():
        raise ValueError(f"Not a directory: {source}")
    files, directories = set(), set()
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        if path.is_dir() and not path.is_symlink():
            directories.add(relative)
        elif (path.is_file() or path.is_symlink()) and not is_log(relative):
            files.add(relative.with_name(relative.name + ".placeholder"))
    # Git does not retain empty directories. Add explicitly named empty markers
    # only where no other placeholder would preserve a directory.
    populated = {parent for path in files for parent in path.parents}
    for directory in sorted(directories, key=lambda p: len(p.parts), reverse=True):
        if directory not in populated:
            marker = directory / ".directory.placeholder"
            files.add(marker)
            populated.update(marker.parents)
    return files


def sync_examples(source, destination):
    expected = inventory(source)
    existing = set()
    if destination.exists():
        for path in destination.rglob("*"):
            if path.is_file() or path.is_symlink():
                if path.is_symlink() or path.suffix != ".placeholder" or path.stat().st_size:
                    raise ValueError(f"Refusing to alter a nonempty or unexpected file: {path}")
                existing.add(path.relative_to(destination))
    for relative in existing - expected:
        (destination / relative).unlink()
    for relative in expected:
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)
    return len(expected), len(existing - expected)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--prepared", type=Path, required=True)
    args = parser.parse_args()
    for label, source, destination in (
        ("Before", args.source, ROOT / "examples/before/original-game"),
        ("After", args.prepared, ROOT / "examples/after/prepared-game"),
    ):
        count, removed = sync_examples(source, destination)
        print(f"{label}: {count} zero-byte placeholders; {removed} outdated placeholders removed.")
    print("Only file/directory names were read. No game contents were copied.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
