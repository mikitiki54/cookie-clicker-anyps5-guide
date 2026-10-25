"""Check complete name-only examples without copying fixture contents."""

import importlib.util
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location(
    "generate_examples", Path(__file__).resolve().parents[1] / "scripts/generate_examples.py")
examples = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(examples)


class ExampleTests(unittest.TestCase):
    def test_nested_files_preserved_logs_excluded_empty_directories_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, destination = root / "source", root / "output"
            (source / "assets/nested").mkdir(parents=True)
            (source / "empty").mkdir()
            (source / "assets/nested/image.png").write_bytes(b"fixture contents must not be copied")
            (source / "LICENSES.TXT").write_text("fixture")
            (source / "run.log").write_text("private log")
            (source / "webkit-image-inspection.txt").write_text("private diagnostics")
            count, _ = examples.sync_examples(source, destination)
            actual = {p.relative_to(destination) for p in destination.rglob("*") if p.is_file()}
            self.assertEqual(actual, {
                Path("assets/nested/image.png.placeholder"),
                Path("LICENSES.TXT.placeholder"),
                Path("empty/.directory.placeholder"),
            })
            self.assertEqual(count, 3)
            self.assertTrue(all((destination / path).stat().st_size == 0 for path in actual))

    def test_nonempty_destination_placeholder_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            source, destination = Path(directory) / "source", Path(directory) / "output"
            source.mkdir()
            destination.mkdir()
            target = destination / "file.placeholder"
            target.write_text("do not remove")
            with self.assertRaises(ValueError):
                examples.sync_examples(source, destination)
            self.assertEqual(target.read_text(), "do not remove")


if __name__ == "__main__":
    unittest.main()
