#!/usr/bin/env python3
"""Check publishable files: documentation, original Python, and empty placeholders."""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def allowed(path):
    if path.as_posix() in {"README.md", "LICENSE", ".gitignore"}:
        return True
    if path.parts[0] == "docs" and path.suffix == ".md":
        return True
    if path.parts[0] in {"scripts", "tests"} and path.suffix == ".py":
        return True
    return path.parts[0] == "examples" and path.suffix == ".placeholder"


def main():
    # Inspect tracked, staged, and untracked publishable files. Also reject ignored
    # unexpected material physically present, so accidental outputs are noticed.
    paths = set()
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if ".git" in relative.parts or "__pycache__" in relative.parts:
            continue
        if path.is_file() or path.is_symlink():
            paths.add(relative)
    if (ROOT / ".git").exists():
        result = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT,
                                check=True, capture_output=True)
        paths.update(Path(p.decode()) for p in result.stdout.split(b"\0") if p)
    failures = []
    placeholders = 0
    for relative in sorted(paths):
        path = ROOT / relative
        if not allowed(relative) or path.is_symlink():
            failures.append(f"Unexpected file: {relative}")
        elif relative.suffix == ".placeholder":
            placeholders += 1
            if not path.is_file() or path.stat().st_size != 0:
                failures.append(f"Placeholder is not empty: {relative}")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"Audit passed: {len(paths)} files, {placeholders} empty placeholders.")
    print("Manually review documentation and code before publishing; this is not legal review.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
