"""Discord artifacts read from Local Storage, the renderer log and the app's own files."""

import json
import os
import pathlib
import tempfile
import unittest
from unittest import mock

from scripts.artifacts import discordAccount, discordLocalStorage, discordLogs
from scripts.chromium.local_storage import StorageRecord

ORIGIN = "https://discord.com"
MS = 1714564800000  # 2024-05-01 12:00:00 UTC


class FakeContext:
    def __init__(self, root, files=()):
        self.root = pathlib.Path(root)
        self.files = list(files)

    def get_files_found(self):
        return list(self.files)

    def get_relative_path(self, path):
        return pathlib.Path(path).relative_to(self.root).as_posix()


def _rows(headers, rows):
    names = [h[0] if isinstance(h, tuple) else h for h in headers]
    return [dict(zip(names, row)) for row in rows]


class LocalStorageLabelTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.log_a = os.path.join(self.root, "leveldb", "000003.log")
        self.log_b = os.path.join(self.root, "leveldb", "000005.ldb")

    def tearDown(self):
        self._tmp.cleanup()

    def _run(self, processor, records):
        with mock.patch.object(discordLocalStorage, "_records", return_value=records), \
                mock.patch.object(discordLocalStorage, "logfunc", lambda *_args: None):
            return processor.__wrapped__(FakeContext(self.root))

    def test_draft_types_use_the_client_names(self):
        drafts = {"42": {"100": {"0": {"timestamp": MS, "draft": "hello"},
                                 "5": {"timestamp": MS + 1, "draft": "/roll"},
                                 "9": {"timestamp": MS + 2, "draft": "other"}}}}
        records = [StorageRecord(ORIGIN, "DraftStore", json.dumps({"_state": drafts}), 7, "Live",
                                 self.log_a)]
        headers, rows, source = self._run(discordLocalStorage.discordDrafts, records)
        by_text = {row["Draft Text"]: row["Draft Type"] for row in _rows(headers, rows)}
        self.assertEqual(by_text, {"hello": "Channel message", "/roll": "Slash command",
                                   "other": "Type 9"})
        self.assertEqual(source, self.log_a)

    def test_activity_labels_follow_the_client_stores(self):
        records = [
            StorageRecord(ORIGIN, "FrecencyStore", json.dumps(
                {"_state": {"pendingUsages": [{"key": "200", "timestamp": MS}]}}), 9, "Live",
                self.log_a),
            StorageRecord(ORIGIN, "SelectedGuildStore", json.dumps(
                {"_state": {"selectedGuildTimestampMillis": {"300": MS}}}), 8, "Live", self.log_b),
            StorageRecord(ORIGIN, "QuickSwitcherStore", json.dumps(
                {"_state": {"channelHistory": ["400", "401"]}}), 7, "Live", self.log_b),
        ]
        headers, rows, source = self._run(discordLocalStorage.discordActivity, records)
        events = sorted((row["Event"], row["Target ID"], row["Detail"])
                        for row in _rows(headers, rows))
        self.assertEqual(events, [("Channel or server selected", "200", ""),
                                  ("Recently selected channel", "400", "position 1"),
                                  ("Recently selected channel", "401", "position 2"),
                                  ("Server selected or left", "300", "")])
        self.assertEqual(source, "\n".join(sorted([self.log_a, self.log_b])))

    def test_local_storage_cites_every_file(self):
        records = [StorageRecord(ORIGIN, "a", "1", 2, "Live", self.log_b),
                   StorageRecord(ORIGIN, "b", "", 1, "Deleted", self.log_a)]
        _headers, rows, source = self._run(discordLocalStorage.discordLocalStorage, records)
        self.assertEqual(len(rows), 2)
        self.assertEqual(source, "\n".join(sorted([self.log_a, self.log_b])))


class RendererLogTest(unittest.TestCase):
    LINES = {
        "renderer_js.old.log": [
            "[2026-07-20 09:00:00.500] [info] [Routing/Utils] Transitioning to /channels/111/222",
            "[2026-07-20 09:00:01.000] [info] [GatewaySocket] [CONNECT] wss://gateway.discord.gg, encoding: json",
        ],
        "renderer_js.log": [
            "[2026-07-26 10:15:30.123] [info] [Routing/Utils] Transitioning to /channels/@me/333",
        ],
    }

    def test_times_are_carried_as_written_and_every_log_is_cited(self):
        with tempfile.TemporaryDirectory() as root:
            logs = os.path.join(root, "discord", "logs")
            os.makedirs(logs)
            files = []
            for name, lines in self.LINES.items():
                path = os.path.join(logs, name)
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write("\n".join(lines) + "\n")
                files.append(path)
            context = FakeContext(root, files)
            with mock.patch.object(discordLogs, "logfunc", lambda *_args: None):
                nav_headers, nav_rows, nav_source = discordLogs.discordNavigation.__wrapped__(context)
                gw_headers, gw_rows, gw_source = discordLogs.discordGatewaySessions.__wrapped__(context)
        # The column is plain text: the log records no offset, so no instant is asserted.
        self.assertEqual(nav_headers[0], "Timestamp (Device Local Time)")
        self.assertEqual(gw_headers[0], "Timestamp (Device Local Time)")
        self.assertEqual([row[0] for row in nav_rows],
                         ["2026-07-20 09:00:00.500", "2026-07-26 10:15:30.123"])
        self.assertEqual([row[0] for row in gw_rows], ["2026-07-20 09:00:01.000"])
        self.assertEqual(nav_source, "\n".join(sorted(files)))
        self.assertEqual(gw_source, os.path.join(logs, "renderer_js.old.log"))


class AccountTest(unittest.TestCase):
    def test_every_file_that_gave_a_row_is_cited(self):
        with tempfile.TemporaryDirectory() as root:
            base = os.path.join(root, "discord")
            os.makedirs(os.path.join(base, "sentry"))
            files = {
                os.path.join(base, "sentry", "scope_v3.json"): {
                    "scope": {"user": {"id": "1100000000000000031", "username": "tester"}},
                    "event": {"contexts": {"os": {"name": "Windows"}}}},
                os.path.join(base, "settings.json"): {"IS_MAXIMIZED": False},
                os.path.join(base, "Preferences"): {"spellcheck": {"dictionaries": ["en-US"]}},
            }
            for path, payload in files.items():
                with open(path, "w", encoding="utf-8") as handle:
                    json.dump(payload, handle)
            context = FakeContext(root, files)
            with mock.patch.object(discordAccount, "logfunc", lambda *_args: None):
                _headers, rows, source = discordAccount.discordAccount.__wrapped__(context)
        self.assertEqual(source, "\n".join(sorted(files)))
        self.assertIn(("Operating System", "Windows", "discord/sentry/scope_v3.json"), rows)

    def test_local_state_is_not_searched(self):
        paths = discordAccount.__artifacts_v2__["discordAccount"]["paths"]
        self.assertFalse([p for p in paths if "Local State" in p])


if __name__ == "__main__":
    unittest.main()
