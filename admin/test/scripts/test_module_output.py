"""Checks artifact output against a recorded baseline.

Parses a registered corpus and compares what every artifact produced against
the fingerprint ``make_test_data.py`` recorded, reporting any difference.

    python3 admin/test/scripts/test_module_output.py \\
        --registry "/path/to/samples.json" --corpus discord_win_ptb

    python3 admin/test/scripts/test_module_output.py --registry ... --all

Encrypted corpora need their secret, and ``--secret signal`` with no value
prompts for it without echo::

    ... --corpus signal_macos_needed --secret signal

This deliberately defines no test case and does nothing on import, so the
``unittest discover`` run in CI collects nothing from it. It cannot run there
anyway: the corpora are private and not in the repository.

Exit status is 1 when a corpus differs from its baseline or has none recorded.
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from admin.scripts import module_output  # noqa: E402  pylint: disable=wrong-import-position
from admin.test.scripts.make_test_data import resolve_secrets  # noqa: E402  pylint: disable=wrong-import-position


def check_corpus(registry, registry_path, corpus, secrets):
    """Parse one corpus and compare it to its baseline. Returns True when clean."""
    recorded = module_output.load_baseline(corpus)
    if recorded is None:
        print(f"{corpus}: no baseline recorded, run make_test_data.py first")
        return False

    try:
        zip_path = module_output.corpus_zip(registry, registry_path, corpus)
    except (KeyError, ValueError, FileNotFoundError) as error:
        print(f"{corpus}: {error}")
        return False

    print(f"{corpus}: parsing {zip_path.name} ...")
    try:
        report_folder, output_root = module_output.run_corpus(zip_path, secrets)
    except RuntimeError as error:
        print(f"{corpus}: {error}")
        return False
    try:
        current = module_output.fingerprint_output(report_folder)
    finally:
        shutil.rmtree(output_root, ignore_errors=True)

    differences = module_output.compare(recorded, current)
    if not differences:
        rows = sum(f["rows"] for f in current.values())
        print(f"{corpus}: matches the baseline, {len(current)} artifact(s), {rows:,} row(s)")
        return True

    print(f"{corpus}: {len(differences)} difference(s) from the baseline")
    for difference in differences:
        print(f"    {difference}")
    print("  If the change was intended, re-record with make_test_data.py.")
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Compare artifact output against its recorded baseline.")
    parser.add_argument("--registry", default=os.environ.get("DLEAPP_SAMPLES"),
                        required=not os.environ.get("DLEAPP_SAMPLES"),
                        help="path to samples.json (or set DLEAPP_SAMPLES)")
    parser.add_argument("--corpus", action="append", help="corpus key to check; repeatable")
    parser.add_argument("--all", action="store_true",
                        help="check every corpus that has a baseline recorded")
    parser.add_argument("--secret", action="append", metavar="APP[=VALUE_OR_FILE]",
                        help="secret for an encrypted corpus; omit the value to be prompted")
    args = parser.parse_args()

    registry = module_output.load_registry(args.registry)
    if args.all:
        corpora = sorted(key for key in registry["samples"]
                         if module_output.baseline_path(key).is_file())
        if not corpora:
            raise SystemExit("no corpus has a baseline recorded yet")
    elif args.corpus:
        corpora = args.corpus
    else:
        raise SystemExit("give --corpus KEY or --all")

    secrets = resolve_secrets(args.secret)
    clean = True
    for corpus in corpora:
        clean &= check_corpus(registry, args.registry, corpus, secrets)
        print()
    return 0 if clean else 1


if __name__ == "__main__":
    sys.exit(main())
