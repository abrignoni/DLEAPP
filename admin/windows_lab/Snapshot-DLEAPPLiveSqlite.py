#!/usr/bin/env python3
"""Create examiner-derived SQLite snapshots from a running Windows lab VM.

The SQLite backup API includes committed WAL content in a consistent database
copy. The result is suitable for parser testing, but it is not a byte-for-byte
copy of the acquired source and must remain labeled as derived evidence.

Authors: @AlexisBrignoni, Codex
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


TARGETS = (
    (
        "ActivitiesCache",
        "ConnectedDevicesPlatform/*/ActivitiesCache.db",
    ),
    (
        "Windows Notifications",
        "Microsoft/Windows/Notifications/wpndatabase.db",
    ),
    (
        "Windows Photos",
        "Packages/Microsoft.Windows.Photos_*/LocalState/MediaDb*.sqlite",
    ),
    (
        "Windows Photos",
        "Packages/Microsoft.Windows.Photos_*/LocalState/shared.sqlite",
    ),
    (
        "Windows Photos",
        "Packages/Microsoft.Windows.Photos_*/LocalState/standalone.sqlite",
    ),
    (
        "Windows Sticky Notes",
        "Packages/Microsoft.MicrosoftStickyNotes_*/LocalState/plum.sqlite",
    ),
)


def utc_iso(timestamp: float | None = None) -> str:
    value = datetime.now(timezone.utc) if timestamp is None else datetime.fromtimestamp(
        timestamp, timezone.utc
    )
    return value.isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def windows_relative_path(path: Path) -> Path:
    drive = path.drive.rstrip(":") or "C"
    relative = str(path)[len(path.drive) :].lstrip("\\/")
    return Path(drive, *Path(relative).parts)


def discover(local_app_data: Path) -> list[tuple[str, Path]]:
    discovered: list[tuple[str, Path]] = []
    seen: set[str] = set()
    for artifact, pattern in TARGETS:
        for path in local_app_data.glob(pattern):
            key = str(path).lower()
            if path.is_file() and key not in seen:
                seen.add(key)
                discovered.append((artifact, path))
    return discovered


def snapshot_database(source: Path, destination: Path) -> tuple[str, int, int]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()

    source_uri = f"file:{source.as_posix()}?mode=ro"
    with sqlite3.connect(source_uri, uri=True, timeout=10) as source_db:
        source_db.execute("PRAGMA query_only=ON")
        with sqlite3.connect(destination) as destination_db:
            source_db.backup(destination_db)
            integrity = destination_db.execute("PRAGMA quick_check").fetchone()[0]
            page_count = destination_db.execute("PRAGMA page_count").fetchone()[0]
            user_version = destination_db.execute("PRAGMA user_version").fetchone()[0]
    return str(integrity), int(page_count), int(user_version)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination-root", type=Path, required=True)
    parser.add_argument("--stage", default="live-sqlite-snapshots")
    args = parser.parse_args()

    local_app_data_value = os.environ.get("LOCALAPPDATA")
    if not local_app_data_value:
        raise SystemExit("LOCALAPPDATA is unavailable; run this script in Windows.")

    stage_root = args.destination_root / args.stage
    files_root = stage_root / "files"
    stage_root.mkdir(parents=True, exist_ok=True)
    snapshot_utc = utc_iso()
    rows: list[dict[str, object]] = []

    for artifact, source in discover(Path(local_app_data_value)):
        stat = source.stat()
        destination = files_root / windows_relative_path(source)
        error = ""
        integrity = ""
        page_count = ""
        user_version = ""
        snapshot_hash = ""
        snapshot_size = ""
        succeeded = False
        try:
            integrity, page_count, user_version = snapshot_database(
                source, destination
            )
            snapshot_hash = sha256(destination)
            snapshot_size = destination.stat().st_size
            succeeded = integrity == "ok"
        except (OSError, sqlite3.Error) as exception:
            error = str(exception)

        rows.append(
            {
                "SnapshotUtc": snapshot_utc,
                "SourceCreatedUtc": utc_iso(stat.st_ctime),
                "SourceModifiedUtc": utc_iso(stat.st_mtime),
                "Artifact": artifact,
                "SourcePath": str(source),
                "SnapshotPath": str(destination),
                "SourceSize": stat.st_size,
                "SnapshotSize": snapshot_size,
                "SnapshotSHA256": snapshot_hash,
                "QuickCheck": integrity,
                "PageCount": page_count,
                "UserVersion": user_version,
                "Succeeded": succeeded,
                "SnapshotError": error,
                "AcquisitionMethod": (
                    "Python sqlite3 backup API from read-only source connection"
                ),
                "EvidenceStatus": (
                    "Examiner-derived logical SQLite snapshot; not byte-for-byte"
                ),
            }
        )

    manifest_path = stage_root / "snapshot-manifest.tsv"
    with manifest_path.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(
            output,
            fieldnames=list(rows[0]) if rows else [
                "SnapshotUtc",
                "SourceCreatedUtc",
                "SourceModifiedUtc",
                "Artifact",
                "SourcePath",
                "SnapshotPath",
                "SourceSize",
                "SnapshotSize",
                "SnapshotSHA256",
                "QuickCheck",
                "PageCount",
                "UserVersion",
                "Succeeded",
                "SnapshotError",
                "AcquisitionMethod",
                "EvidenceStatus",
            ],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)

    metadata = {
        "SnapshotUtc": snapshot_utc,
        "Stage": args.stage,
        "DatabaseCount": sum(bool(row["Succeeded"]) for row in rows),
        "FailedCount": sum(not bool(row["Succeeded"]) for row in rows),
        "EvidenceStatus": (
            "Examiner-derived logical SQLite snapshots for parser testing"
        ),
    }
    (stage_root / "snapshot-metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    print(f"SQLite snapshot stage written to {stage_root}")
    print(
        f"Succeeded: {metadata['DatabaseCount']}; "
        f"failed: {metadata['FailedCount']}"
    )
    return 0 if metadata["FailedCount"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
