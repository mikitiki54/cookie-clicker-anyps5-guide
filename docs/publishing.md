# Publishing this repository

This folder contains only original documentation, original preparation/audit code, tests, and empty example files. The actual working game and generated output must stay outside the repository.

Suggested repository name: `cookie-clicker-anyps5-guide`.

Suggested description:

> Unofficial Cookie Clicker PS5 compatibility guide and local preparation tools for AnyPS5 on Linux. No game files included.

Before publishing:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/audit_repo.py
git diff --cached --stat
```

The audit is a technical file check, not legal review. Inspect the text and history as well. Do not force-add files rejected by `.gitignore` without understanding why they are excluded.

An original-copy integration check successfully regenerated the executable, converted WebKit, normalized PNG, and all 2,787 archived image contents. Those artifacts were written outside this repository. They are not part of the published project.

Create an empty GitHub repository under your own account, then set its remote and push this folder's `main` branch after committing. Use your own Git author identity; do not publish a real email address if you prefer GitHub's private noreply address. The GitHub connection or CLI must be authenticated to the account that will own the repository.

Do not upload the entire separate working-game folder. ZIP releases, if provided, must contain only the same publishable files tracked in this repository. Do not put proprietary game content in Git history, Git LFS, release attachments, or issue attachments.
