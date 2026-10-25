# Complete before/after filename snapshots

These examples mirror the original dump and the actual working conversion folder as inspected on 25 October 2026. They supersede the earlier abbreviated examples.

| Snapshot | Original file paths included | Empty-directory markers | Total zero-byte placeholders |
| --- | ---: | ---: | ---: |
| [Before conversion](../examples/before/original-game/) | 3,078 | 0 | 3,078 |
| [After conversion](../examples/after/prepared-game/) | 6,739 | 1 | 6,740 |

The after snapshot excludes 15 logs: `*.log` run outputs, `crash-after-images.txt`, and the saved `webkit-*-inspection.txt` debugger outputs. Ordinary game text files such as licenses and build identifiers remain listed.

Every source filename is represented by the same relative path with `.placeholder` appended. **Every placeholder has zero-byte contents.** For example, `app0/clicker/images.tar.placeholder` describes where a real archive belongs; it is not an archive. Empty directories use `.directory.placeholder` because Git does not preserve empty directories by themselves.

The after snapshot also lists the complete `libs/` directory, generated shader-cache filenames, save-file names, diagnostic scripts, and backup filenames present in the working folder. Their names are included for completeness; their contents are not distributed. These generated/diagnostic files are not all required startup dependencies, and caches or saves can change with subsequent runs.

The working folder was assembled interactively and contains `run-diagnostic.sh`. The automated preparation script additionally creates a convenient `launch.sh`; this generated launcher's absence from the interactive snapshot is intentional. The examples describe the real directories, rather than inventing a cleaned-up layout.

## Regenerate from local copies

Run from the repository root:

```bash
python3 scripts/generate_examples.py \
  --source '/path/to/original-game-folder' \
  --prepared '/path/to/working-conversion'

git add -- examples
python3 scripts/audit_repo.py
```

The generator reads names only. It never opens a source file to copy its contents. It can remove outdated example files only if they are already empty `.placeholder` files; it refuses to change a nonempty or unexpected example file. Stage those removals before running the audit, because the audit also checks tracked files.

All source game files, caches, and saves stay outside this repository. Large directories may be truncated by GitHub's browser view; cloning or downloading the repository provides the full example trees.
