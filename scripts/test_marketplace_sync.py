"""Regression tests for toolkit and catalogue version synchronisation."""

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import check_marketplace_sync as sync


class MarketplaceSyncTests(unittest.TestCase):
    """Exercise the command against a small marketplace on disk."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = "./toolkits/example/engineering"
        self.toolkit = self.root / "toolkits/example/engineering/apm.yml"
        self.toolkit.parent.mkdir(parents=True)
        self.manifest = self.root / "apm.yml"
        self.marketplace = self.root / ".claude-plugin/marketplace.json"
        self.marketplace.parent.mkdir()
        self.write_versions("1.2.0", "1.2.0", "1.2.0")
        for name, value in (
            ("ROOT", str(self.root)),
            ("APM_MANIFEST", str(self.manifest)),
            ("MARKETPLACE_JSON", str(self.marketplace)),
            ("TOOLKITS_DIR", str(self.root / "toolkits")),
        ):
            patcher = patch.object(sync, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def write_versions(self, toolkit, package, plugin):
        """Write a toolkit and its two catalogue entries."""
        self.toolkit.write_text(
            f"---\nname: example\nversion: {toolkit}\n"
            "dependencies:\n  version: ignored\n",
            encoding="utf-8",
        )
        self.manifest.write_text(
            "marketplace:\n  packages:\n    - name: example\n"
            "      description: Example toolkit\n"
            f"      source: {self.source}\n      version: {package}\n",
            encoding="utf-8",
        )
        self.marketplace.write_text(
            json.dumps(
                {
                    "plugins": [
                        {
                            "name": "example",
                            "description": "Example toolkit",
                            "source": self.source,
                            "version": plugin,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

    def run_check(self):
        """Return the command's exit code and captured output."""
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = sync.main()
        return status, output.getvalue()

    def test_matching_versions_pass(self):
        status, _ = self.run_check()
        self.assertEqual(status, 0)

    def test_both_catalogues_stale_fail(self):
        self.write_versions("1.2.0", "1.0.0", "1.0.0")
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
            status, output = self.run_check()
        self.assertEqual(status, 1)
        self.assertIn("toolkit apm.yml='1.2.0' but root apm.yml='1.0.0'", output)
        self.assertIn("toolkit apm.yml='1.2.0' but marketplace.json='1.0.0'", output)
        self.assertIn("::error file=.claude-plugin/marketplace.json::", output)
        self.assertIn("apm pack --check-versions --check-clean", output)

    def test_one_catalogue_stale_fails(self):
        for package, plugin in (("1.0.0", "1.2.0"), ("1.2.0", "1.0.0")):
            with self.subTest(package=package, plugin=plugin):
                self.write_versions("1.2.0", package, plugin)
                status, output = self.run_check()
                self.assertEqual(status, 1)
                self.assertIn("Version mismatch", output)

    def test_missing_or_empty_toolkit_version_fails(self):
        for content in ("name: example\n", "version:\n", "version: ''\n"):
            with self.subTest(content=content):
                self.toolkit.write_text(content, encoding="utf-8")
                status, output = self.run_check()
                self.assertEqual(status, 1)
                self.assertIn("no non-empty top-level version", output)

    def test_quoted_toolkit_version_passes(self):
        self.write_versions("'1.2.0'", "1.2.0", "1.2.0")
        status, _ = self.run_check()
        self.assertEqual(status, 0)

    def test_missing_catalogue_versions_fail(self):
        self.write_versions("1.2.0", "", None)
        status, output = self.run_check()
        self.assertEqual(status, 1)
        self.assertIn("Version mismatch", output)

    def test_existing_catalogue_metadata_check_is_preserved(self):
        self.marketplace.write_text(
            self.marketplace.read_text(encoding="utf-8").replace(
                "Example toolkit", "Different description"
            ),
            encoding="utf-8",
        )
        status, output = self.run_check()
        self.assertEqual(status, 1)
        self.assertIn("field 'description'", output)

    def test_missing_toolkit_still_fails(self):
        self.toolkit.unlink()
        status, output = self.run_check()
        self.assertEqual(status, 1)
        self.assertIn("no toolkit exists at that path", output)


if __name__ == "__main__":
    unittest.main()
