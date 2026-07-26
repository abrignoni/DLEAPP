"""Records the baseline an output regression test compares against.

Parses a registered corpus and writes a fingerprint of everything every
artifact produced to ``admin/test/results/<corpus>.json``. Run it when the
output is known to be correct: after adding a parser, or after a deliberate
change to what one reports.

    python3 admin/test/scripts/make_test_data.py \\
        --registry "/path/to/samples.json" --corpus discord_win_ptb

Encrypted corpora need their secret, exactly as a normal run does::

    ... --corpus signal_macos_needed --secret signal

Given ``--secret signal`` with no value the secret is prompted for without
echo, so it stays out of shell history. The baseline that comes out carries
digests and counts, never rows, so it is safe to commit.
"""

import argparse
import getpass
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from admin.scripts import module_output  # noqa: E402  pylint: disable=wrong-import-position


def resolve_secrets(pairs):
    """Turn --secret arguments into {app: value}, prompting where needed."""
    secrets = {}
    for pair in pairs or []:
        app, separator, value = pair.partition("=")
        app = app.strip()
        if not app:
            raise SystemExit("--secret needs an application name, for example --secret signal")
        if not separator or not value:
            if not sys.stdin.isatty():
                raise SystemExit(f"--secret {app} was given no value and this is not an "
                                 f"interactive terminal")
            value = getpass.getpass(f"{app} key (input hidden): ").strip()
            if not value:
                raise SystemExit(f"no {app} key was entered")
        elif os.path.isfile(value):
            with open(value, "r", encoding="utf-8", errors="replace") as handle:
                value = handle.read(4096).strip()
        secrets[app] = value
    return secrets


def main():
    parser = argparse.ArgumentParser(
        description="Record the output fingerprint of a registered corpus.")
    parser.add_argument("--registry", default=os.environ.get("DLEAPP_SAMPLES"),
                        required=not os.environ.get("DLEAPP_SAMPLES"),
                        help="path to samples.json (or set DLEAPP_SAMPLES)")
    parser.add_argument("--corpus", required=True, help="corpus key to record")
    parser.add_argument("--secret", action="append", metavar="APP[=VALUE_OR_FILE]",
                        help="secret for an encrypted corpus; omit the value to be prompted")
    args = parser.parse_args()

    secrets = resolve_secrets(args.secret)
    registry = module_output.load_registry(args.registry)
    zip_path = module_output.corpus_zip(registry, args.registry, args.corpus)

    print(f"parsing {zip_path.name} ...")
    report_folder, output_root = module_output.run_corpus(zip_path, secrets)
    try:
        fingerprints = module_output.fingerprint_output(report_folder)
    finally:
        shutil.rmtree(output_root, ignore_errors=True)

    if not fingerprints:
        raise SystemExit("the run produced no artifacts, so there is nothing to record")

    written = module_output.save_baseline(args.corpus, fingerprints)
    total = sum(f["rows"] for f in fingerprints.values())
    print(f"recorded {len(fingerprints)} artifact(s), {total:,} row(s) in total")
    print(f"  {written.relative_to(module_output.REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
