import contextlib
import io
import logging
import re
import unittest
from pathlib import Path

import uniconv


class TestDocumentation(unittest.TestCase):
    def test_public_exports_and_readme_examples(self):
        for name in uniconv.__all__:
            self.assertTrue(hasattr(uniconv, name))
        readme = Path(__file__).resolve().parents[1] / "README.md"
        blocks = re.findall(r"```python\n(.*?)```", readme.read_text(encoding="utf-8"), re.S)
        self.assertGreaterEqual(len(blocks), 5)
        namespace = {}
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertLogs("uniconv.converter", level="WARNING"):
                for block in blocks:
                    exec(compile(block, str(readme), "exec"), namespace)
