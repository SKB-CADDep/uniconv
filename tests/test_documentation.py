import contextlib
import io
import re
import runpy
import subprocess
import sys
import unittest
from pathlib import Path

import uniconv

ROOT = Path(__file__).resolve().parents[1]


class TestDocumentation(unittest.TestCase):
    def test_public_exports(self):
        for name in uniconv.__all__:
            self.assertTrue(hasattr(uniconv, name))

    def test_python_snippets(self):
        pages = [ROOT / "README.md"] + [
            ROOT / "docs" / name for name in ("getting-started.md", "usage.md", "migration.md")
        ]
        for page in pages:
            blocks = re.findall(r"```python\n(.*?)```", page.read_text(encoding="utf-8"), re.S)
            self.assertTrue(blocks, page)
            for index, block in enumerate(blocks, 1):
                with self.subTest(page=page.name, block=index):
                    with contextlib.redirect_stdout(io.StringIO()):
                        exec(compile(block, str(page), "exec"), {})

    def test_runnable_examples(self):
        expectations = {
            "basic.py": ("1 МПа", "100 °C", "1007.5 HV"),
            "presets.py": ("1 МПа",),
            "custom_units.py": ("10 m/s",),
        }
        for name, expected_parts in expectations.items():
            with self.subTest(example=name):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    runpy.run_path(str(ROOT / "examples" / name), run_name="__main__")
                for part in expected_parts:
                    self.assertIn(part, output.getvalue())

    def test_unit_reference_is_up_to_date(self):
        subprocess.run(
            [sys.executable, str(ROOT / "tools" / "generate_units_reference.py"), "--check"],
            check=True,
        )
