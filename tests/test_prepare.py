"""Safety checks for archives supplied to the local preparation tool."""

import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location(
    "prepare", Path(__file__).resolve().parents[1] / "scripts/prepare.py")
prepare = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prepare)


class RuntimeArchiveTests(unittest.TestCase):
    def validate(self, name, kind=tarfile.REGTYPE):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runtime.tar.gz"
            with tarfile.open(path, "w:gz") as archive:
                member = tarfile.TarInfo(name)
                member.type = kind
                if kind == tarfile.SYMTYPE:
                    member.linkname = "/outside"
                archive.addfile(member, io.BytesIO(b""))
            prepare.validate_library_archive(path)

    def test_regular_runtime_file_is_accepted(self):
        self.validate("libs/libkernel.prx")

    def test_parent_traversal_is_rejected(self):
        with self.assertRaises(ValueError):
            self.validate("libs/../../outside")

    def test_absolute_path_is_rejected(self):
        with self.assertRaises(ValueError):
            self.validate("/outside")

    def test_symlink_is_rejected(self):
        with self.assertRaises(ValueError):
            self.validate("libs/escape", tarfile.SYMTYPE)

    def test_file_outside_library_tree_is_rejected(self):
        with self.assertRaises(ValueError):
            self.validate("elsewhere/file")


if __name__ == "__main__":
    unittest.main()
