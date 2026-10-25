# Cookie Clicker on Linux with AnyPS5

An unofficial compatibility guide and local preparation tool for **Cookie Clicker PS5, PPSA19546, version 01.007.000**.

This setup reached the game in a user-confirmed test on Linux with an Intel Core i5-11600K and NVIDIA RTX 3060. It uses AnyPS5's converted executables and replacement libraries; it is not an official Linux release. Long-term stability and completion of the game have not been verified.

**No game files are included.** Supply your own lawfully obtained, decrypted copy. This project does not download games, provide keys, decrypt protected content, or grant rights to redistribute game files. It is not affiliated with the game's creators, publisher, Sony, or AnyPS5.

## What fixed startup

The successful setup needed four changes:

1. Convert the root-level `eawk_EAWebKitDLL.prx` together with `eboot.bin`, using the native relinker and `--module-dir .`. Restoring the unconverted library afterward was insufficient.
2. Build `Fonts.7z` from the supplied loose fonts. Its root must contain lowercase `crimson.ttf` plus the three original `NotoSans*-Regular.ttf` files.
3. Build `clicker/images.tar` from the supplied loose images. Archive paths must look like `cursor/0,0.png`, **without an `img/` prefix**: the game adds that prefix itself.
4. Losslessly re-encode `icons/28,6.png` as stripped RGBA PNG before archiving it. The original was readable by other decoders but consistently failed in this WebKit path. Re-encoding preserved every pixel and resolved the loading stall.

The final archive contained 2,787 images. Only `icons/28,6.png` differed from the source. The successful log reported `PRELOAD ALL IMAGES: 2949ms`, after which the user confirmed the game ran. See [the investigation](docs/investigation.md) for evidence and limitations.

## Requirements

- Linux x86-64 and a Vulkan-capable graphics stack.
- Python 3.12 or newer, ImageMagick 7 (`magick`), and 7-Zip (`7z` or `7zz`).
- The official **AnyPS5 v0.1.3 Linux relinker** and **`prx-linux-v0.1.3.tar.gz`** from [the upstream release](https://github.com/boykopovar/AnyPS5/releases/tag/v0.1.3).
- The original, decrypted game folder, including `eboot.bin`, `eawk_EAWebKitDLL.prx`, `sce_module/`, `sce_sys/`, and all resources. The executable and required modules must already be ELF files. This tool refuses SELF containers; see [upstream preparation instructions](https://github.com/boykopovar/AnyPS5/blob/v0.1.3/docs/user/USAGE.md).

The script verifies the official converter and library archive checksums. Custom AnyPS5 builds are outside this recipe's tested scope.

## Prepare your copy

Make the downloaded relinker executable, then run:

```bash
chmod +x /path/to/relinker-v0.1.3

python3 scripts/prepare.py \
  --source '/path/to/original-game-folder' \
  --output '/path/to/new-output-folder' \
  --relinker '/path/to/relinker-v0.1.3' \
  --libraries '/path/to/prx-linux-v0.1.3.tar.gz'
```

The output folder must not exist and must be outside the source folder. The source is left untouched. The script converts the main executable and root-level WebKit, copies the resources, prepares the archives, verifies that the PNG's pixels are unchanged, and adds a launcher. It does not launch the game automatically. If preparation fails, it retains the partial output and logs for inspection; choose another fresh output path for a retry.

Run the result:

```bash
cd '/path/to/new-output-folder'
./launch.sh
```

Allow up to five minutes when investigating startup:

```bash
timeout 300s ./launch.sh > run.log 2>&1
```

Status `124` means the timeout expired, not that the process segfaulted. **Controller input is confirmed working by the user.** Mouse input did not work in the initial user test; keyboard/mouse support and individual controller mappings have not been systematically tested.

## Before and after examples

Browse [before conversion](examples/before/) and [after conversion](examples/after/). These are **complete filename/directory snapshots** of the original dump and the working conversion, excluding run logs and saved debugger-output logs. Every `*.placeholder` is an **empty, zero-byte file**, not a usable executable, library, font, or image. The suffix is part of the example name only; real files do not use it.

The after snapshot includes the full runtime library list and the working folder's generated shader cache, save-file names, diagnostic scripts, and backup-file names. These are a record of the tested folder, not a claim that every generated or diagnostic file is required to run. Empty directories contain a zero-byte `.directory.placeholder` marker so Git retains them. No source file contents are copied. See [the snapshot notes](docs/example-layouts.md) for counts and regeneration instructions.

The following is only an overview; the linked example directories contain the full listings:

```text
Before: original-game/                 After: prepared-game/
  eboot.bin                             eboot.elf
  eawk_EAWebKitDLL.prx                   run-diagnostic.sh
  sce_module/                           libs/              (AnyPS5 libraries)
  clicker/                              app0/
    icons/28,6.png                        eboot.bin          (original resource)
    cursor/0,0.png                        eawk_EAWebKitDLL.prx.guest.prx
  spiwebkit_assets/                       sce_module/        (converted modules)
    Crimson.ttf                           clicker/
    NotoSansJP-Regular.ttf                  images.tar
    NotoSansKR-Regular.ttf                  img/icons/28,6.png (re-encoded)
    NotoSansSC-Regular.ttf                spiwebkit_assets/Fonts.7z
```

## Publishing and contributing

Publish documentation and original tools, not generated game outputs. Do not attach dumps, converted binaries, WebKit, game JavaScript, images, fonts, populated archives, saves, or core dumps to issues or releases. A changed image is still game artwork. Keep AnyPS5 downloads upstream, and follow their licenses if redistributing their software separately.

The repository uses an allowlist-style `.gitignore` and an audit tool to help prevent accidental inclusion of game files:

```bash
python3 scripts/audit_repo.py
```

Review logs for personal paths before sharing excerpts. A compatibility recipe is not a guarantee that acquisition, circumvention, conversion, or redistribution is permitted in every jurisdiction.

The [MIT license](LICENSE) covers only this repository's original documentation and tooling. It grants no rights to Cookie Clicker, its assets, EAWebKit, PlayStation software, or AnyPS5.
