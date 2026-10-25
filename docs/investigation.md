# Investigation notes

These observations concern PPSA19546, version 01.007.000, AnyPS5 v0.1.3, Linux/Wayland, an Intel i5-11600K, and an RTX 3060. They should not be generalized to every game or dump.

## 1. Missing image archive

The first run failed to open `/app0/clicker/images.tar` and then segfaulted. Loose images were present in the dump, but the archive was absent. A valid empty tar advanced startup; it did not provide the image data needed later.

## 2. Missing font archive

Startup then encountered `/app0/spiwebkit_assets/Fonts.7z`. A valid empty 7z advanced startup again. Once WebKit loaded, it failed at `/spiwebkit_fonts/crimson.ttf`. Copying fonts into `app0/spiwebkit_fonts/` or merely adding a lowercase filename under `spiwebkit_assets/` did not fix that error.

A populated LZMA 7z archive, with the four fonts at its root and `crimson.ttf` lowercase, resolved it. Font unpacking may create a `spiwebkit_fonts/` directory next to the executable. Archive fonts are supplied by the user; none are distributed here.

## 3. WebKit had to participate in conversion

The game reported an unresolved `WrapCreateEAWebkitInstance`. Its root-level `eawk_EAWebKitDLL.prx` had been removed while using the browser converter. Restoring the console PRX afterward did not create a Linux-compatible version.

The native command explicitly selected the executable and included root-level modules:

```bash
relinker --to-intel --module-dir . /path/to/source/eboot.bin /path/to/output/eboot.elf
```

The conversion reported three modules: `libc.prx`, `libSceNpCppWebApi.prx`, and `eawk_EAWebKitDLL.prx`.

## 4. The loading-screen segfault was an image-handle access

The crash dump placed the fault at converted WebKit offset `0x6dd1a5`:

```asm
mov 0x1c8(%rax), %ecx
```

`rax` was zero, producing an invalid read at address `0x1c8`. Inspection of the binary's binding records associated the enclosing function with `HTMLImageElement.rataGetCairoHandle`. The game script called it on `Game.CursorRingPic`, resolved to `img/cursor/0,0.png`. The image-frame call returned null and the handle code accessed it without checking.

Copying loose images into `clicker/img/` did not resolve this crash while the archive remained empty. A populated `images.tar` got past it. Archive members need names such as `cursor/0,0.png`; putting `img/` in member names introduced duplicated `img/img/` requests.

## 5. One valid PNG prevented preload completion

The game then stayed on the loading screen with its background and spinner visible. A five-minute test produced no segfault, but loading did not complete.

The script's original image-error handler logged only a generic message and an event object. Adding a diagnostic log of the event target's `src` and `alt` identified `img/icons/28,6.png`. It failed consistently across repeated runs.

The original PNG was 308 bytes, 48×48, 8-bit RGBA, with valid IHDR, IDAT, and IEND checksums. Its scanlines decompressed correctly. The loose and archived files had identical SHA-256 hashes. ImageMagick decoded it successfully. These checks do not establish why this WebKit path rejected it.

The error handler did not remove failed images from the pending set. The preload callback therefore waited indefinitely. We did not bypass that check or mark failed images as loaded.

Re-encoding with ImageMagick 7 resolved the failure:

```bash
magick original.png -strip -define png:color-type=6 \
  -define png:compression-level=6 normalized.png
magick compare -metric AE original.png normalized.png null:
```

The pixel comparison returned zero. The original image's SHA-256 was `cd86f6b5016be0ed7e7332801743e2f69d8fe3216709550c6fd57e3d015d6d58`; the successful re-encoding in that environment was `1dbd7bf526c090f3bdc64b9879aec5466954d1e5323fc8d90cfd68dfb16e1577`. Encoded bytes may differ between ImageMagick versions; pixel equality is the relevant check.

After rebuilding the archive, the log recorded `PRELOAD ALL IMAGES: 2949ms` and the user confirmed the game ran. Comparing the final archive to the original source found 2,787 image entries, all present in the source, with only `icons/28,6.png` changed.

## Limits

- The exact PNG decoder or graphics-backend defect was not isolated.
- The successful setup retained loose images under `clicker/img/`; removing that directory after creating the archive was not tested.
- `preload = True` remained enabled. Game logic and binary null checks were not patched.
- Missing `dlcsettings.json`, a fresh-save index, and `devConfig.js` appeared in earlier logs; they were not established as blockers and were not repaired to obtain this result.
- This is a report of one working setup, not a general AnyPS5 compatibility guarantee.
