"""Guard the examiner-facing artifact metadata against unsupported claims.

Every artifact module declares an ``__artifacts_v2__`` dict. Its ``name`` and
``description`` fields are not developer notes: they are rendered into the HTML
report, written into the LAVA manifest, and from there they get pasted into
examination notes and quoted in court. A description that says an artifact holds
"every file the user opened" is a statement about a person's conduct that the
underlying database does not make. The standard for these fields is therefore:

    Say what the data is and where it came from. Do not say what it means about
    the world, or who did it, unless the data itself establishes that or the
    description cites a source that documents it.

The failure mode this check exists to stop is a fix that goes stale. An audit of
all 34 artifact modules (merged as PR #48) reworded the claims it found in
docstrings, notes and these two fields alike. Nothing then watched the fields, so
the next description written by hand could reintroduce the same phrasing without
anyone noticing, and a later edit to a docstring could leave the `description`
above it asserting what the docstring no longer does. Prose corrections decay
exactly where nothing is checking them.

The check parses each artifact module with ``ast``, evaluates its
``__artifacts_v2__`` literal, and matches the ``name`` and ``description`` of
every entry against a vocabulary of phrasing that has historically signalled an
unsupported claim (completeness words, attributions of an act to "the user",
certainty words).

Two ways a match gets resolved:

* The wording overstates what the parser can show. Reword it to what the data
  shows -- name the table, file, or key, and drop the actor and the completeness
  word. This is the common case.
* The match is a false positive: a product feature literally named "All Files", a
  verbatim database enum value, a UI path reproduced from the app, or a
  cautionary sentence whose matched word is part of the hedge. Add a
  ``(filename, artifact_key, field)`` tuple to ALLOWLIST **with an inline comment
  saying why**. The allowlist is a record of decisions someone made on purpose;
  it is not a place to park a description nobody wanted to rewrite.

Two things the check reports rather than hides, because both are ways it can
quietly stop doing its job:

* An ALLOWLIST entry that no longer matches anything. It means the description
  was reworded or the artifact key changed, and the entry now shields nothing --
  except the next claim that lands under the same key. Stale entries fail the run
  and must be deleted.
* A module whose ``__artifacts_v2__`` is not a static literal (built by a helper,
  or absent). Its fields cannot be read without importing the module, so they are
  never checked. Those modules are printed as NOT CHECKED on every run, so the
  coverage hole stays visible.

Known coverage gap: ``scripts/artifacts/robloxWindows.py`` builds its four
entries through a ``_windows_artifact()`` helper that copies and mutates the dict
imported from the macOS parser module, so ``__artifacts_v2__`` there is a call
rather than a literal and this check cannot read it. Those four Windows artifacts
(``robloxWindowsPresence``, ``robloxWindowsNotifications``,
``robloxWindowsGameJoins``, ``robloxWindowsAccount``) inherit the ``description``
of their macOS counterparts, and a ``name`` derived from it, unchecked. The
macOS originals in ``robloxActivity.py``, ``robloxLogs.py`` and
``robloxAccount.py`` are checked, which covers the inherited description text but
not the substitution the helper performs on the name.

Usage:
    python3 admin/scripts/check_claim_language.py           # CI mode, exits 1 on a violation
    python3 admin/scripts/check_claim_language.py --list    # every match, allowlisted included
    python3 admin/scripts/check_claim_language.py --verbose # coverage and allowlist counts
"""

import argparse
import ast
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS_DIR = REPO_ROOT / "scripts" / "artifacts"

# The claim vocabulary. Each alternative is a phrasing that has, in past audits,
# turned out to be an assertion the parsed data does not support:
#   - completeness claims over a source that is rotated, cached, or truncated
#     ("all", "every", "complete", "full list", "entire")
#   - attributing an act to a person when the record only shows a stored value
#     ("the user viewed", "user-created", "searched by", "manually")
#   - certainty and inference-about-conduct words ("proves", "definitively",
#     "always", "reliable", "visited", "habits")
#
# Every alternative is anchored with an explicit \b. Do NOT express a boundary as
# a trailing space ("all ", "every ", "always "): that spelling matches inside
# "call log", "calllog.db" and similar, which is enough noise to make the check
# worth ignoring. Word boundaries also keep the hedges quiet -- neither
# "unreliable" nor "incomplete" trips, because there is no boundary mid-word.
#
# The stems below are left UNCLOSED on purpose so inflections still match:
#   \bcomplete -> complete, completeness, completely
#   \breliable -> reliable, reliably and its compounds
#   \bhabit    -> habit, habits, habitual, habitually
# "habitual" is the inference word most likely to appear in a description of app
# usage data, so the open stem is worth its one known false positive, "habitat":
# no artifact description or name in this repository contains that word today
# (verified by grep over scripts/artifacts). If a habitat-related artifact ever
# lands, close the stem to \bhabits?\b rather than allowlisting the artifact.
CLAIM_PATTERN = re.compile(
    r"\ball\b"
    r"|\bevery\b"
    r"|\bcomplete"
    r"|\bfull list\b"
    r"|\bentire\b"
    r"|\bthe user (?:searched|typed|viewed|visited|opened|selected|deleted|read|sent"
    r"|created|hid|chose)\b"
    r"|\buser[- ](?:created|entered|typed|searched|selected|initiated)\b"
    r"|\bsearched by\b"
    r"|\btyped by\b"
    r"|\bviewed by\b"
    r"|\bread by\b"
    r"|\bmanually\b"
    r"|\bproves?\b"
    r"|\bdefinitively\b"
    r"|\balways\b"
    r"|\breliable"
    r"|\bvisited\b"
    r"|\bhabits?\b",
    re.IGNORECASE)

# `notes` reaches the examiner too, in the report and in the artifact info modal, so
# the same standard applies to it. It cannot use the same vocabulary, because notes do
# a job name and description do not: they state what was tested. "empty on all 18
# copies tested" and "NULL for every account tested" are the coverage discipline this
# project asks for, not claims about a person, and the completeness words fire on every
# one of them. Measured 2026-08-29: the full vocabulary flags 368 of the 1,477
# artifacts carrying notes across the five cores, dominated by `every` and `all`,
# almost all describing a test set.
#
# `read by` comes out for the same reason. In a note it means read by the code, not by
# a person: "columns are read by position", "not read by this artifact".
#
# What is left is attribution and certainty, which mean the same thing in a note as in
# a description.
NOTES_PATTERN = re.compile(
    r'\bthe user (?:searched|typed|viewed|visited|opened|selected|deleted|read|sent'
    r'|created|hid|chose)\b'
    r'|\buser[- ](?:created|entered|typed|searched|selected|initiated)\b'
    r'|\bsearched by\b'
    r'|\btyped by\b'
    r'|\bviewed by\b'
    r'|\bmanually\b'
    r'|\bproves?\b'
    r'|\bdefinitively\b'
    r'|\balways\b'
    r'|\breliable'
    r'|\bvisited\b'
    r'|\bhabits?\b',
    re.IGNORECASE)

# A note that *denies* a claim uses the same words as one that makes it: "not terms the
# user searched for", "does not establish that the user viewed them". That denial is the
# wording this project asks for, so matching it and demanding an allowlist entry would
# tax the correct behaviour and grow the allowlist without bound. A match in `notes`
# preceded by a negation inside the same clause is therefore not reported.
#
# The window is deliberately short. A negation two sentences back says nothing about
# this clause, and a long window would swallow real claims. Suppressed matches are
# counted and printed under --verbose, because a check that narrows its own scope
# silently is worse than no check.
NEGATION_WINDOW = 60
NEGATION_PATTERN = re.compile(
    r"\b(not|no|never|nor|neither|without|cannot|rather than|instead of"
    r"|isn't|doesn't|don't|does not|do not)\b",
    re.IGNORECASE)


def negated(text, start):
    """True when a negation appears close enough before `start` to govern it."""
    window = text[max(0, start - NEGATION_WINDOW):start]
    # A sentence boundary ends the clause, so a negation before it does not govern.
    window = window.rsplit('. ', 1)[-1]
    return bool(NEGATION_PATTERN.search(window))


# Fields that reach the examiner through the report and the LAVA manifest.
CHECKED_FIELDS = {
    'name': CLAIM_PATTERN,
    'description': CLAIM_PATTERN,
    'notes': NOTES_PATTERN,
}

# Reviewed exceptions, as (filename, artifact_key, field, term). Each needs a
# reason. The term is part of the key, so an entry silences the one word it was
# granted for and never the next claim added to the same text.
# needs a comment justifying it. See the module docstring before adding one.
ALLOWLIST = {
    # The match is inside the hedge itself: the description closes with "the
    # cache evicts over time, so this index is a partial record of what the
    # client fetched rather than a complete one". Removing the word would remove
    # the caution it belongs to.
    ("discordCacheRecords.py", "discordCacheRecords", "description", "complete"),
}


def unallowlisted(filename, artifact_key, field, terms):
    """The terms no ALLOWLIST entry covers for this field.

    An entry is keyed on the term it was granted for, so allowlisting one word does
    not pre-approve the next claim somebody adds to the same text.
    """
    return [term for term in terms
            if (filename, str(artifact_key), field, term) not in ALLOWLIST]

STANDARD_NOTE = (
    "Artifact name/description reach the examiner through the HTML report and the LAVA\n"
    "manifest and get quoted in casework. State what the data is and where it came from;\n"
    "do not state what it means in the real world, or who performed an act, unless the\n"
    "data establishes it or a cited source documents it.\n"
    "Reword to what the data shows, or -- if the match is a product name, a verbatim\n"
    "schema value, a UI path, or part of a hedge -- add it to ALLOWLIST in\n"
    "admin/scripts/check_claim_language.py with a comment saying why."
)


def find_artifacts_dict(tree):
    """Return the AST node assigned to `__artifacts_v2__`, or None."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__artifacts_v2__":
                return node.value
    return None


def load_artifacts(path):
    """Return (artifacts_dict, skip_reason). Exactly one of the two is None."""
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as ex:
        return None, f"could not read file: {ex}"

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as ex:
        return None, f"could not parse module: {ex}"

    node = find_artifacts_dict(tree)
    if node is None:
        return None, "no __artifacts_v2__ assignment"

    # Modules that build the dict dynamically cannot be evaluated statically.
    try:
        artifacts = ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError) as ex:
        return None, f"__artifacts_v2__ is not a literal: {ex}"

    if not isinstance(artifacts, dict):
        return None, "__artifacts_v2__ is not a dict"
    return artifacts, None


def scan_file(path):
    """Return (matches, skip_reason, negated_count) for one artifact module.

    Each match is a (path, artifact_key, field, text, matched_terms, allowlisted)
    tuple.
    """
    artifacts, skip_reason = load_artifacts(path)
    if artifacts is None:
        return [], skip_reason, 0

    matches = []
    negated_count = 0
    for artifact_key, entry in artifacts.items():
        if not isinstance(entry, dict):
            continue
        for field, pattern in CHECKED_FIELDS.items():
            text = entry.get(field)
            if not isinstance(text, str):
                continue
            hits = list(pattern.finditer(text))
            if field == 'notes':
                kept = [hit for hit in hits if not negated(text, hit.start())]
                negated_count += len(hits) - len(kept)
                hits = kept
            found = sorted({hit.group(0).lower() for hit in hits})
            if not found:
                continue
            remaining = unallowlisted(path.name, artifact_key, field, found)
            matches.append((path, str(artifact_key), field, text,
                            remaining or found, not remaining, found))
    return matches, None, negated_count


def format_match(match):
    """Render one match as `path:artifact_key:field: <text>`."""
    path, artifact_key, field, text, terms = match[:5]
    collapsed = " ".join(text.split())
    if len(collapsed) > 300:
        collapsed = collapsed[:297] + "..."
    quoted = ", ".join(sorted({term.lower() for term in terms}))
    return f"{path}:{artifact_key}:{field}: {collapsed}\n    matched: {quoted}"


def main():
    """Scan the artifact modules and report unallowlisted claim language."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--list", action="store_true", dest="list_all",
                        help="print every match, including allowlisted ones")
    parser.add_argument("--verbose", action="store_true",
                        help="also report modules whose __artifacts_v2__ could not be read")
    args = parser.parse_args()

    paths = sorted(ARTIFACTS_DIR.glob("*.py"))
    if not paths:
        print(f"No artifact modules found under {ARTIFACTS_DIR}", file=sys.stderr)
        return 2

    violations = []
    allowlisted = []
    skipped = []
    fired = set()
    negated_total = 0
    for path in paths:
        rel_path = os.path.relpath(path, REPO_ROOT)
        matches, skip_reason, negated_here = scan_file(path)
        negated_total += negated_here
        if skip_reason:
            skipped.append((rel_path, skip_reason))
            continue
        for match in matches:
            entry = (rel_path,) + match[1:]
            for term in match[6]:
                fired.add((path.name, match[1], match[2], term))
            if match[5]:
                allowlisted.append(entry)
            else:
                violations.append(entry)

    # An allowlist entry that no longer matches anything is either a fixed
    # description or a stale key, and it hides the next real claim behind a name
    # nobody rechecks. Surface it so the allowlist stays a list of live decisions.
    stale = sorted(ALLOWLIST - fired)

    # A module whose __artifacts_v2__ cannot be evaluated statically is a real
    # coverage hole: its fields are never checked. Report it rather than hide it.
    if skipped:
        print(f"NOT CHECKED -- {len(skipped)} module(s) have no statically readable "
              f"__artifacts_v2__:")
        for rel_path, reason in skipped:
            print(f"  {rel_path}: {reason}")
        print()

    if args.verbose:
        print(f"Scanned {len(paths)} module(s); {len(paths) - len(skipped)} checked, "
              f"{len(skipped)} skipped.")
        print(f"Allowlist holds {len(ALLOWLIST)} entr(ies); {len(allowlisted)} fired "
              f"this run.")
        print(f'{negated_total} match(es) in notes were preceded by a negation and '
              f'not reported.')
        print()

    if stale:
        print(f"Stale ALLOWLIST entr(ies) ({len(stale)}) -- these no longer match "
              f"anything and should be deleted:")
        for entry in stale:
            print(f"  {entry[0]}:{entry[1]}:{entry[2]}  [{entry[3]}]")
        print()

    if args.list_all and allowlisted:
        print(f"Allowlisted matches ({len(allowlisted)}):")
        for match in allowlisted:
            print(f"  {format_match(match)}")
        print()

    if violations:
        print(f"Unsupported claim language in examiner-facing artifact fields "
              f"({len(violations)}):")
        for match in violations:
            print(f"  {format_match(match)}")
        print()
        print(STANDARD_NOTE)
        return 1

    if stale:
        print("Remove the stale entr(ies) above from ALLOWLIST in "
              "admin/scripts/check_claim_language.py.")
        return 1

    summary = (f"Checked {len(paths) - len(skipped)} artifact module(s): no unsupported "
               f"claim language ({len(allowlisted)} reviewed exception(s) allowlisted).")
    if skipped:
        summary += f" {len(skipped)} module(s) NOT checked, listed above."
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
