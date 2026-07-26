"""Fingerprints an artifact's output so changes to it can be detected.

iLEAPP records the actual rows an artifact produced and diffs them on the next
run. That works there because its corpora are published research images. The
DLEAPP corpora are private application profiles, so recording rows would put
someone's messages, contacts and phone numbers into this repository.

This records a fingerprint instead: row counts, the column list, per-column
digests and how many values in each column were populated. A digest changes if
any value changes, so a regression is still caught, while the baseline itself
carries no content and is safe to commit and review in a pull request.

What a fingerprint catches:

* rows appearing or disappearing
* a column added, removed, renamed or retyped
* any change to any value, localised to the column it happened in
* a column that silently stopped being populated
* a timestamp falling outside a plausible range, which is the shape a broken
  epoch conversion takes

What it does not catch: a change that leaves every value identical, and the
order rows are written in. Rows are sorted before hashing so that a tie broken
differently between runs does not read as a regression.
"""

import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = REPO_ROOT / "admin" / "test" / "results"

# A parsed timestamp outside this window is almost certainly an epoch mistake
# rather than real data: 1990-01-01 to 2100-01-01 as unix seconds.
_MIN_PLAUSIBLE_EPOCH = 631152000
_MAX_PLAUSIBLE_EPOCH = 4102444800

_FIELD_SEPARATOR = "\x1f"


def load_registry(registry_path):
    """Read a samples.json corpus registry."""
    with open(registry_path, "r", encoding="utf-8") as handle:
        registry = json.load(handle)
    if not isinstance(registry, dict) or not isinstance(registry.get("samples"), dict):
        raise ValueError(f"{registry_path} has no 'samples' object")
    return registry


def corpus_zip(registry, registry_path, corpus):
    """Resolve a corpus key to its zip, verifying the recorded hash."""
    entry = registry["samples"].get(corpus)
    if entry is None:
        raise KeyError(f"'{corpus}' is not in the registry")
    relative = (entry.get("match") or {}).get("zip")
    if not relative:
        raise ValueError(f"'{corpus}' has no match.zip")
    path = Path(registry_path).resolve().parent / relative
    if not path.is_file():
        raise FileNotFoundError(f"'{corpus}' points at a missing file: {path}")

    expected = (entry.get("match") or {}).get("sha256")
    if expected:
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 22), b""):
                digest.update(chunk)
        if digest.hexdigest() != expected:
            raise ValueError(f"'{corpus}' does not match its recorded sha256; "
                             f"the corpus changed, so any baseline for it is stale")
    return path


def run_corpus(zip_path, secrets=None, keep=False):
    """Parse a corpus with dleapp.py and return its output folder.

    ``secrets`` maps an application to the value its --<app>-key flag takes,
    for corpora that are encrypted.
    """
    output_root = tempfile.mkdtemp(prefix="dleapp-output-")
    folder = "regression"
    command = [sys.executable, str(REPO_ROOT / "dleapp.py"), "-t", "zip",
               "-i", str(zip_path), "-o", output_root,
               "--custom_output_folder", folder]
    for app, value in (secrets or {}).items():
        command += [f"--{app}-key", value]

    completed = subprocess.run(command, cwd=str(REPO_ROOT), capture_output=True,
                               text=True, check=False)
    if completed.returncode != 0:
        if not keep:
            shutil.rmtree(output_root, ignore_errors=True)
        raise RuntimeError(f"dleapp.py exited {completed.returncode}\n"
                           f"{completed.stdout[-1500:]}")
    return Path(output_root) / folder, output_root


def _column_values(connection, table, column):
    try:
        rows = connection.execute(f'SELECT "{column}" FROM "{table}"').fetchall()
    except sqlite3.Error:
        return []
    return [row[0] for row in rows]


def _digest(values):
    hasher = hashlib.sha256()
    for value in values:
        hasher.update(("" if value is None else str(value)).encode("utf-8", "replace"))
        hasher.update(_FIELD_SEPARATOR.encode())
    return hasher.hexdigest()


def fingerprint_output(report_folder):
    """Build a content-free fingerprint of every artifact in a parsed report."""
    report_folder = Path(report_folder)
    with open(report_folder / "_lava_data.lava", "r", encoding="utf-8") as handle:
        lava = json.load(handle)

    connection = sqlite3.connect(f"file:{report_folder / '_lava_artifacts.db'}?mode=ro", uri=True)
    fingerprints = {}
    for artifacts in (lava.get("artifacts") or {}).values():
        for artifact in artifacts:
            name = artifact.get("name")
            table = artifact.get("tablename")
            if not name or not table:
                continue
            types = {column["name"]: column["type"]
                     for column in artifact.get("object_columns", [])}
            try:
                columns = [row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')]
            except sqlite3.Error:
                continue

            rows = connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            column_digests, non_empty, datetimes = {}, {}, {}
            row_strings = None
            for column in columns:
                values = _column_values(connection, table, column)
                column_digests[column] = _digest(values)
                non_empty[column] = sum(
                    1 for value in values if value not in (None, "", b""))
                if types.get(column) in ("datetime", "date"):
                    parsed = [v for v in values if isinstance(v, (int, float))]
                    datetimes[column] = {
                        "parsed": len(parsed),
                        "in_plausible_range": all(
                            _MIN_PLAUSIBLE_EPOCH <= v <= _MAX_PLAUSIBLE_EPOCH
                            for v in parsed),
                    }
                # Build the whole-table digest from the same reads
                if row_strings is None:
                    row_strings = ["" for _ in range(len(values))]
                for index, value in enumerate(values):
                    if index < len(row_strings):
                        row_strings[index] += ("" if value is None else str(value)) + _FIELD_SEPARATOR

            fingerprints[name] = {
                "rows": rows,
                "columns": [{"name": c, "type": types.get(c, "text")} for c in columns],
                "digest": _digest(sorted(row_strings or [])),
                "column_digests": column_digests,
                "non_empty": non_empty,
                "datetime_columns": datetimes,
            }
    connection.close()
    return fingerprints


def baseline_path(corpus):
    return RESULTS_DIR / f"{corpus}.json"


def load_baseline(corpus):
    path = baseline_path(corpus)
    if not path.is_file():
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_baseline(corpus, fingerprints, commit=None):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "corpus": corpus,
        "recorded_with_commit": commit or _current_commit(),
        "note": "Content-free fingerprint. Digests and counts only, no rows, "
                "because the corpora are private application profiles.",
        "artifacts": fingerprints,
    }
    with open(baseline_path(corpus), "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return baseline_path(corpus)


def _current_commit():
    try:
        result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT),
                                capture_output=True, text=True, check=False)
        return result.stdout.strip() or None
    except OSError:
        return None


def compare(recorded, current):
    """Compare a recorded fingerprint against a fresh one.

    Returns a list of human-readable differences, empty when they agree.
    """
    differences = []
    recorded_artifacts = recorded.get("artifacts", {})

    for name in sorted(set(recorded_artifacts) | set(current)):
        was = recorded_artifacts.get(name)
        now = current.get(name)
        if was is None:
            differences.append(f"{name}: new artifact, {now['rows']} row(s), not in the baseline")
            continue
        if now is None:
            differences.append(f"{name}: produced nothing; the baseline has {was['rows']} row(s)")
            continue

        if was["rows"] != now["rows"]:
            differences.append(f"{name}: {was['rows']} row(s) recorded, {now['rows']} now")

        was_columns = [(c["name"], c["type"]) for c in was["columns"]]
        now_columns = [(c["name"], c["type"]) for c in now["columns"]]
        if was_columns != now_columns:
            removed = [c for c in was_columns if c not in now_columns]
            added = [c for c in now_columns if c not in was_columns]
            if removed:
                differences.append(f"{name}: column(s) gone: "
                                   + ", ".join(f"{n} ({t})" for n, t in removed))
            if added:
                differences.append(f"{name}: column(s) added: "
                                   + ", ".join(f"{n} ({t})" for n, t in added))
            if not removed and not added:
                differences.append(f"{name}: columns reordered")

        if was["digest"] != now["digest"]:
            changed = [column for column, digest in was["column_digests"].items()
                       if column in now["column_digests"]
                       and now["column_digests"][column] != digest]
            if changed:
                differences.append(f"{name}: value(s) changed in " + ", ".join(sorted(changed)))
            else:
                differences.append(f"{name}: contents changed")

        for column, count in was.get("non_empty", {}).items():
            now_count = now.get("non_empty", {}).get(column)
            if now_count is not None and now_count != count:
                differences.append(f"{name}: {column} had {count} populated value(s), "
                                   f"now {now_count}")

        for column, stats in now.get("datetime_columns", {}).items():
            if not stats.get("in_plausible_range", True):
                differences.append(f"{name}: {column} holds a timestamp outside "
                                   f"1990-2100, which usually means a broken "
                                   f"epoch conversion")
    return differences
