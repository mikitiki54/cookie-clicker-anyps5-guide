#!/usr/bin/env python3
"""Prepare a user-supplied Cookie Clicker copy. No game content is bundled."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

RELINKER_SHA256 = "bd2a959885830e14f091477edf297fc4c3f45b83a29171c47f5719d721fedb45"
LIBRARIES_SHA256 = "0a4eb4dcfb1321a24faac09d9d8c4a2ba62e58f77764f4b7f7fd9e0f6bdfce3a"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}
FONTS = ("NotoSansJP-Regular.ttf", "NotoSansKR-Regular.ttf", "NotoSansSC-Regular.ttf")


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require_elf(path):
    with path.open("rb") as stream:
        if stream.read(4) != b"\x7fELF":
            raise ValueError(f"Not a plain ELF: {path}. Prepare a separate ELF copy first.")


def validate_library_archive(path):
    """Accept only regular files/directories inside the expected libs/ tree."""
    with tarfile.open(path, "r:gz") as archive:
        for member in archive.getmembers():
            parts = Path(member.name).parts
            if (not parts or Path(member.name).is_absolute() or ".." in parts
                    or parts[0] != "libs" or not (member.isfile() or member.isdir())):
                raise ValueError(f"Unexpected runtime archive member: {member.name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "output", "relinker", "libraries"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    output = args.output.resolve()
    relinker = args.relinker.resolve(strict=True)
    libraries = args.libraries.resolve(strict=True)

    if sys.version_info < (3, 12):
        raise ValueError("Python 3.12 or newer is required.")
    if output == source or source in output.parents:
        raise ValueError("Output must be outside the source directory.")
    if output.exists():
        raise ValueError("Output already exists; select a new directory.")
    if not source.is_dir():
        raise ValueError("Source must be the original game directory.")
    magick = shutil.which("magick")
    sevenzip = shutil.which("7z") or shutil.which("7zz")
    if not magick or not sevenzip:
        raise ValueError("Install ImageMagick 7 (magick) and 7-Zip (7z or 7zz).")
    if not os.access(relinker, os.X_OK):
        raise ValueError("The relinker needs execute permission (chmod +x).")
    if sha256(relinker) != RELINKER_SHA256 or sha256(libraries) != LIBRARIES_SHA256:
        raise ValueError("Use the official v0.1.3 Linux relinker and prx-linux-v0.1.3.tar.gz.")
    validate_library_archive(libraries)

    for relative in ("eboot.bin", "eawk_EAWebKitDLL.prx", "sce_module/libc.prx",
                     "sce_module/libSceNpCppWebApi.prx"):
        require_elf(source / relative)
    for relative in ("sce_sys/param.json", "spiwebkit_assets/Crimson.ttf",
                     *(f"spiwebkit_assets/{name}" for name in FONTS)):
        if not (source / relative).is_file():
            raise ValueError(f"Missing source resource: {relative}")
    metadata = json.loads((source / "sce_sys/param.json").read_text())
    if (metadata.get("titleId"), metadata.get("contentVersion")) != ("PPSA19546", "01.007.000"):
        raise ValueError("This recipe targets PPSA19546 version 01.007.000 only.")
    image_source = source / "clicker/img"
    if not (image_source / "icons/28,6.png").is_file():
        image_source = source / "clicker"
    images = sorted(p for p in image_source.rglob("*")
                    if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS)
    if not (image_source / "icons/28,6.png").is_file() or not images:
        raise ValueError("Could not find the loose images, including icons/28,6.png.")
    if not (image_source / "cursor/0,0.png").is_file():
        raise ValueError("Missing cursor/0,0.png in the loose image tree.")

    output.mkdir(parents=True, exist_ok=False)
    print(f"Output: {output}", flush=True)
    print("Converting executable and bundled WebKit...", flush=True)
    with (output / "conversion.log").open("w") as log:
        subprocess.run([str(relinker), "--to-intel", "--module-dir", ".",
                        str(source / "eboot.bin"), str(output / "eboot.elf")],
                       stdout=log, stderr=subprocess.STDOUT, check=True)

    print("Copying resources; the source remains untouched...", flush=True)
    app0 = output / "app0"
    shutil.copytree(source, app0, dirs_exist_ok=True)
    with tarfile.open(libraries, "r:gz") as archive:
        archive.extractall(output, filter="data")

    image_output = app0 / "clicker/img"
    for path in images:
        target = image_output / path.relative_to(image_source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    diagnostics = output / "diagnostics"
    diagnostics.mkdir()
    original = diagnostics / "28,6.original.png"
    normalized = diagnostics / "28,6.normalized.png"
    shutil.copy2(image_source / "icons/28,6.png", original)
    print("Re-encoding the affected icon and checking pixel equality...", flush=True)
    subprocess.run([magick, str(original), "-strip", "-define", "png:color-type=6",
                    "-define", "png:compression-level=6", str(normalized)], check=True)
    subprocess.run([magick, "compare", "-metric", "AE", str(original),
                    str(normalized), "null:"], check=True)
    shutil.copy2(normalized, image_output / "icons/28,6.png")

    print(f"Building images.tar with {len(images)} images...", flush=True)
    with tarfile.open(app0 / "clicker/images.tar", "w", format=tarfile.USTAR_FORMAT) as archive:
        for path in images:
            relative = path.relative_to(image_source)
            archive.add(image_output / relative, arcname=relative.as_posix(), recursive=False)

    font_dir = app0 / "spiwebkit_assets"
    shutil.copy2(font_dir / "Crimson.ttf", font_dir / "crimson.ttf")
    # Build a fresh archive in diagnostics so stale archive entries cannot survive.
    font_archive = diagnostics / "Fonts.7z"
    print("Building Fonts.7z...", flush=True)
    subprocess.run([sevenzip, "a", "-t7z", "-m0=lzma", "-mx=3", str(font_archive),
                    "crimson.ttf", *FONTS], cwd=font_dir, check=True)
    subprocess.run([sevenzip, "t", str(font_archive)], check=True)
    shutil.copy2(font_archive, font_dir / "Fonts.7z")
    launcher = output / "launch.sh"
    launcher.write_text('#!/usr/bin/env bash\nset -eu\ncd -- "$(dirname -- "$0")"\nexec ./eboot.elf "$@"\n')
    launcher.chmod(0o755)
    executable = output / "eboot.elf"
    executable.chmod(executable.stat().st_mode | 0o111)
    print(f"\nPrepared successfully. Run: {launcher}")
    print("Conversion success does not guarantee gameplay compatibility.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError, tarfile.TarError) as error:
        print(f"Preparation failed: {error}", file=sys.stderr)
        sys.exit(1)
