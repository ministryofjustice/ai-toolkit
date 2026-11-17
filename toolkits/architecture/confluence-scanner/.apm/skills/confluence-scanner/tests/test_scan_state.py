import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import scan_state as scanner

SITE = "https://example.atlassian.net"


def metadata(page_id="1", **changes):
    value = {
        "site": SITE,
        "id": page_id,
        "title": "Synthetic page " + page_id,
        "version": 1,
        "status": "current",
        "space_id": "10",
    }
    value.update(changes)
    return value


class ScannerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.output = self.root / "index"
        self.output.mkdir()
        self.store = scanner.Store(self.output, self.root)
        self.state = scanner.new_state("scan-test", SITE, "10")

    def discover(self, pages=None):
        scanner.inventory(
            self.state,
            {
                "cursor": None,
                "pages": pages if pages is not None else [metadata()],
                "next_cursor": None,
            },
        )

    def record(self, **changes):
        value = {
            "site": SITE,
            "id": "1",
            "version": 1,
            "source_status": "current",
            "body": "<p>Synthetic text</p>",
            "summary": "A concise synthetic summary.",
            "body_complete": True,
            "links_complete": True,
            "urls_complete": True,
            "gaps": [],
            "retrieved_at": "2026-10-30T18:00:00Z",
            "expected_summary_sha256": None,
        }
        value.update(changes)
        scanner.record(self.store, self.state, value)

    def test_949_page_inventory_survives_each_cursor_and_restart(self):
        for offset in range(0, 949, 100):
            cursor = None if offset == 0 else str(offset)
            next_cursor = str(offset + 100) if offset + 100 < 949 else None
            scanner.inventory(
                self.state,
                {
                    "cursor": cursor,
                    "next_cursor": next_cursor,
                    "pages": [metadata(str(i)) for i in range(offset + 1, min(offset + 101, 950))],
                },
            )
            self.store.save(self.state)
            self.state = self.store.load("scan-test")
        status = scanner.counts(self.state)
        self.assertEqual(status["base"]["discovered"], 949)
        self.assertEqual(status["base"]["pending"], 949)
        self.assertTrue(status["discovery_complete"])
        self.assertFalse(status["complete"])
        self.assertEqual(len(scanner.select(self.store, self.state, 10, False)["pages"]), 10)
        processed = 0
        while True:
            batch = scanner.select(self.store, self.state, 10, False)["pages"]
            if not batch:
                break
            for page in batch:
                self.record(id=page["id"])
                processed += 1
            self.store.save(self.state)
            self.state = self.store.load("scan-test")
        status = scanner.counts(self.state)
        self.assertEqual(processed, 949)
        self.assertEqual(status["base"]["complete"], 949)
        self.assertEqual(status["base"]["pending"], 0)
        self.assertTrue(status["complete"])

    def test_wrong_space_and_archived_inventory_rejected(self):
        for page in [
            metadata(space_id="11"),
            metadata(status="archived"),
            metadata(site="https://another.example"),
        ]:
            with self.assertRaises(scanner.ScanError):
                self.discover([page])

    def test_duplicate_page_is_deduplicated(self):
        self.discover([metadata(), metadata()])
        self.assertEqual(len(self.state["pages"]), 1)

    def test_cursor_loop_and_missing_cursor_rejected(self):
        scanner.inventory(self.state, {"cursor": None, "next_cursor": "100", "pages": []})
        with self.assertRaises(scanner.ScanError):
            scanner.inventory(self.state, {"cursor": "100", "next_cursor": "100", "pages": []})
        with self.assertRaises(scanner.ScanError):
            scanner.inventory(self.state, {"pages": [], "next_cursor": None})

    def test_resume_rejects_different_event(self):
        self.store.save(self.state)
        with self.assertRaises(scanner.ScanError):
            self.store.load("scan-other")

    def test_complete_requires_substantive_results_not_enumeration(self):
        self.discover()
        self.assertFalse(scanner.counts(self.state)["complete"])
        self.record()
        self.assertTrue(scanner.counts(self.state)["complete"])

    def test_batch_selection_does_not_repeat_completed_pages(self):
        self.discover([metadata(str(i)) for i in range(1, 26)])
        for expected_size in (10, 10, 5):
            batch = scanner.select(self.store, self.state, 10, False)["pages"]
            self.assertEqual(len(batch), expected_size)
            for page in batch:
                self.record(id=page["id"])
            self.store.save(self.state)
            self.state = self.store.load("scan-test")
        self.assertEqual(scanner.select(self.store, self.state, 10, False)["pages"], [])
        self.assertTrue(scanner.counts(self.state)["complete"])

    def test_retries_are_bounded(self):
        self.discover()
        for attempt in range(3):
            self.record(
                body_complete=False,
                expected_summary_sha256=scanner.digest(self.output / "pages/1.md"),
            )
        self.assertEqual(scanner.select(self.store, self.state, 10, True)["pages"], [])

    def test_base_links_are_not_added_to_depth_one_queue(self):
        self.discover([metadata("1"), metadata("2")])
        self.record(body='<a href="/wiki/spaces/BASE/pages/2/P">Existing base</a>')
        self.record(id="2")
        self.assertEqual(scanner.counts(self.state)["unresolved_links"], 0)
        self.assertTrue(scanner.counts(self.state)["complete"])

    def test_full_body_is_not_persisted(self):
        self.discover()
        self.record(body="<p>UNIQUE_RAW_BODY_MARKER</p>")
        self.store.save(self.state)
        scanner.report(self.store, self.state)
        for path in self.output.rglob("*"):
            if path.is_file():
                self.assertNotIn("UNIQUE_RAW_BODY_MARKER", path.read_text())

    def test_incomplete_flags_and_gaps_block_completion(self):
        self.discover()
        self.record(links_complete=False, gaps=["Rendered macro not available"])
        self.assertFalse(scanner.counts(self.state)["complete"])
        self.assertEqual(scanner.counts(self.state)["base"]["incomplete"], 1)

    def test_version_mismatch_and_absent_summary_are_rejected(self):
        self.discover()
        for changes in (
            {"version": 2},
            {"summary": ""},
            {"body_complete": "true"},
            {"source_status": "archived"},
        ):
            with self.assertRaises(scanner.ScanError):
                self.record(**changes)
        self.assertFalse((self.output / "pages/1.md").exists())

    def test_previous_summary_preserved_on_incomplete_read(self):
        self.discover()
        self.record()
        path = self.output / "pages/1.md"
        before = path.read_bytes()
        self.record(expected_summary_sha256=scanner.digest(path), body_complete=False)
        self.assertEqual(before, path.read_bytes())

    def test_external_summary_edit_causes_conflict(self):
        self.discover()
        self.record()
        path = self.output / "pages/1.md"
        original_hash = scanner.digest(path)
        path.write_text("Manually edited")
        with self.assertRaises(scanner.ScanError):
            self.record(expected_summary_sha256=original_hash)
        self.assertEqual(path.read_text(), "Manually edited")

    def test_duplicate_links_merge_referrers_and_do_not_expand_depth_one(self):
        self.discover([metadata("1"), metadata("2")])
        target = SITE + "/wiki/spaces/OTHER/pages/3/Target"
        self.record(body='<a href="' + target + '">Target</a>')
        self.record(id="2", body='<a href="' + target + '#section">Target</a>')
        self.assertEqual(len(self.state["links"][target]["referrers"]), 2)
        scanner.resolve_link(
            self.state,
            {"url": target, "disposition": "current", "page": metadata("3", space_id="20")},
        )
        self.record(id="3", body='<a href="/wiki/spaces/OTHER/pages/4/No">No</a>')
        self.assertEqual(len(self.state["pages"]), 3)
        self.assertEqual(len(self.state["links"]), 1)
        self.assertTrue(scanner.counts(self.state)["complete"])

    def test_denied_target_stays_unresolved(self):
        self.discover()
        target = SITE + "/wiki/spaces/OTHER/pages/3/Target"
        self.record(body='<a href="' + target + '">Target</a>')
        scanner.resolve_link(self.state, {"url": target, "disposition": "denied"})
        self.assertEqual(scanner.counts(self.state)["unresolved_links"], 1)
        self.assertFalse(scanner.counts(self.state)["complete"])

    def test_archived_target_excluded_without_queueing(self):
        self.discover()
        target = SITE + "/wiki/spaces/OTHER/pages/3/Target"
        self.record(body='<a href="' + target + '">Target</a>')
        scanner.resolve_link(self.state, {"url": target, "disposition": "archived"})
        self.assertEqual(len(self.state["pages"]), 1)
        self.assertTrue(scanner.counts(self.state)["complete"])

    def test_title_link_can_be_resolved_but_cannot_be_fabricated(self):
        self.discover()
        self.record(body='<ac:link><ri:page ri:content-title="Target"/></ac:link>')
        marker = next(iter(self.state["links"]))
        scanner.resolve_link(
            self.state, {"url": marker, "disposition": "current", "page": metadata("3")}
        )
        with self.assertRaises(scanner.ScanError):
            scanner.resolve_link(
                self.state,
                {
                    "url": "unresolved-title:Never observed",
                    "disposition": "current",
                    "page": metadata("4"),
                },
            )

    def test_title_links_keep_source_context(self):
        self.discover([metadata("1"), metadata("2")])
        body = '<ac:link><ri:page ri:content-title="Target"/></ac:link>'
        self.record(body=body)
        self.record(id="2", body=body)
        self.assertEqual(len(self.state["links"]), 2)

    def test_explicitly_authorised_cross_site_target(self):
        self.state = scanner.new_state("scan-test", SITE, "10", ["https://other.example"])
        self.discover()
        target = "https://other.example/wiki/spaces/OTHER/pages/3/Target"
        self.record(body='<a href="' + target + '">Target</a>')
        scanner.resolve_link(
            self.state,
            {
                "url": target,
                "disposition": "current",
                "page": metadata("3", site="https://other.example"),
            },
        )
        self.assertEqual(self.state["pages"]["https://other.example|3"]["depth"], 1)

    def test_cross_site_target_is_not_queued(self):
        self.discover()
        target = "https://other.example/wiki/spaces/OTHER/pages/3/Target"
        self.record(body='<a href="' + target + '">Target</a>')
        with self.assertRaises(scanner.ScanError):
            scanner.resolve_link(
                self.state,
                {
                    "url": target,
                    "disposition": "current",
                    "page": metadata("3", site="https://other.example"),
                },
            )

    def test_plain_text_embeds_redaction_and_attachment_classification(self):
        urls = scanner.extract(
            "<p>https://docs.example/file?token=SECRET&ouid=PERSON#private</p>"
            '<img src="https://images.example/image.png">'
            '<a href="/wiki/download/attachments/5/image.png">Image</a>'
            '<a href="/wiki/x/AbC">Short link</a>',
            SITE + "/wiki/spaces/BASE/pages/1/P",
        )
        self.assertEqual({u["kind"] for u in urls}, {"external", "attachment", "unresolved"})
        self.assertNotIn("SECRET", json.dumps(urls))
        self.assertNotIn("PERSON", json.dumps(urls))
        self.assertNotIn("#private", json.dumps(urls))

    def test_confluence_gadget_security_tickets_are_not_persisted(self):
        self.discover()
        self.record(
            body=(
                '<a href="/wiki/plugins/servlet/gadgets/ifr?'
                "st=SYNTHETIC_GADGET_TICKET&amp;status=current"
                '#rpctoken=SYNTHETIC_RPC_TOKEN">Gadget</a>'
                '<a href="/wiki/plugins/servlet/gadgets/ifr?'
                'ST=SYNTHETIC_UPPERCASE_TICKET">Gadget</a>'
            )
        )
        self.store.save(self.state)
        scanner.report(self.store, self.state)
        urls = json.dumps(self.state["pages"][SITE + "|1"]["urls"])
        self.assertIn("st=REDACTED", urls)
        self.assertIn("ST=REDACTED", urls)
        self.assertIn("status=current", urls)
        for path in self.output.rglob("*"):
            if path.is_file():
                saved = path.read_text()
                for marker in (
                    "SYNTHETIC_GADGET_TICKET",
                    "SYNTHETIC_RPC_TOKEN",
                    "SYNTHETIC_UPPERCASE_TICKET",
                ):
                    self.assertNotIn(marker, saved)

    def test_malformed_and_credentialed_urls_are_not_persisted(self):
        urls = scanner.extract(
            '<a href="https://user:SECRET@docs.example/file">No</a>'
            '<a href="https://[broken">Invalid</a>',
            SITE,
        )
        self.assertEqual(len(urls), 2)
        self.assertTrue(all(u["kind"] == "unresolved" for u in urls))
        self.assertNotIn("SECRET", json.dumps(urls))

    def test_symlink_output_escape_is_rejected(self):
        other = self.root.parent / "outside-scanner-synthetic"
        (self.output / "pages").symlink_to(other)
        self.discover()
        with self.assertRaises(scanner.ScanError):
            self.record()

    def test_checkpoint_symlink_escape_is_rejected(self):
        outside = self.root.parent / "outside-checkpoint-synthetic"
        self.store.path.symlink_to(outside)
        with self.assertRaises(scanner.ScanError):
            scanner.Store(self.output, self.root)

    def test_report_lists_all_pages_with_escaped_titles(self):
        self.discover([metadata(title="Table | title\nnext")])
        scanner.report(self.store, self.state)
        report = (self.output / ".scanner/progress.md").read_text()
        self.assertIn("Table \\| title next", report)
        self.assertIn("Not available", report)

    def test_lock_prevents_concurrent_commands(self):
        with self.store.locked():
            with self.assertRaises(scanner.ScanError):
                with self.store.locked():
                    self.fail("Lock unexpectedly acquired twice.")

    def test_cli_batch_and_explicit_failure(self):
        common = [
            "--output",
            str(self.output),
            "--knowledge-base",
            str(self.root),
            "--scan-id",
            "scan-test",
        ]

        def cli(command, payload=None):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                with mock.patch("sys.stdin", io.StringIO(json.dumps(payload))):
                    code = scanner.main(common + command)
            return code, out.getvalue(), err.getvalue()

        self.assertEqual(cli(["init", "--site", SITE, "--space-id", "10"])[0], 0)
        self.assertEqual(
            cli(["inventory"], {"cursor": None, "pages": [metadata()], "next_cursor": None})[0], 0
        )
        code, output, error = cli(
            ["fail"], {"site": SITE, "id": "1", "error": "HTTP 429", "retryable": True}
        )
        self.assertEqual(code, 0, error)
        self.assertEqual(json.loads(output)["base"]["failed"], 1)
        self.assertEqual(len(json.loads(cli(["next", "--retry"])[1])["pages"]), 1)
        self.assertEqual(cli(["init", "--site", SITE, "--space-id", "10"])[0], 2)
        self.assertEqual(
            cli(["init", "--site", SITE, "--space-id", "10", "--previous-scan-id", "wrong"])[0], 2
        )

    def test_denial_is_not_retried(self):
        self.discover()
        page = self.state["pages"][SITE + "|1"]
        page.update(status="failed", retryable=False, attempts=1)
        self.assertEqual(scanner.select(self.store, self.state, 10, True)["pages"], [])

    def test_cli_partial_batch_commits_each_success_before_later_failure(self):
        self.discover([metadata("1"), metadata("2")])
        self.store.save(self.state)
        payload = {
            "pages": [
                {
                    "site": SITE,
                    "id": page_id,
                    "version": version,
                    "source_status": "current",
                    "retrieved_at": "2026-10-30T18:00:00Z",
                    "body": "<p>Synthetic input</p>",
                    "summary": "Synthetic summary",
                    "body_complete": True,
                    "links_complete": True,
                    "urls_complete": True,
                    "gaps": [],
                    "expected_summary_sha256": None,
                }
                for page_id, version in (("1", 1), ("2", 999))
            ]
        }
        common = [
            "--output",
            str(self.output),
            "--knowledge-base",
            str(self.root),
            "--scan-id",
            "scan-test",
            "record",
        ]
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            with mock.patch("sys.stdin", io.StringIO(json.dumps(payload))):
                self.assertEqual(scanner.main(common), 2)
        persisted = self.store.load("scan-test")
        self.assertEqual(persisted["pages"][SITE + "|1"]["status"], "complete")
        self.assertEqual(persisted["pages"][SITE + "|2"]["status"], "pending")
        self.assertTrue((self.output / "pages/1.md").exists())
        self.assertFalse((self.output / "pages/2.md").exists())

    def test_new_finalized_event_requires_explicit_prior_identity(self):
        self.store.save(self.state)
        common = [
            "--output",
            str(self.output),
            "--knowledge-base",
            str(self.root),
            "--scan-id",
            "scan-new",
            "init",
            "--site",
            SITE,
            "--space-id",
            "10",
            "--previous-scan-id",
            "scan-test",
        ]
        manifest = self.output / "TEST-scanned.md"
        manifest.write_text("- Latest state: in-progress\n- Latest scan ID: scan-test\n")
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(scanner.main(common), 2)
            self.assertEqual(self.store.load("scan-test")["scan_id"], "scan-test")
            manifest.write_text("- Latest state: partial\n- Latest scan ID: scan-test\n")
            self.assertEqual(scanner.main(common), 0)
        self.assertEqual(self.store.load("scan-new")["scan_id"], "scan-new")


if __name__ == "__main__":
    unittest.main()
