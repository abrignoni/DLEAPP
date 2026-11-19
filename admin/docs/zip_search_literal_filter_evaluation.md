# DLEAPP ZIP literal prefilter: validation

This ports the same conservative ZIP search optimization as [iLEAPP PR #2801](https://github.com/abrignoni/iLEAPP/pull/2801). The production change adds **19 lines and changes two lines** in `scripts/search_files.py`, plus separate fabricated regression tests and this note. Other seekers, `peek`, parsers and dependencies are unchanged.

## Matching and regression checks

A normalized pattern without brackets must contain every literal segment between `*` and `?`. The longest segment is used as a necessary-substring check before the existing wildcard matcher. Filenames retain the existing normalized `root/` prefix. Any bracket syntax, including malformed classes, or an empty literal retains the original matcher path. No retained filename index is added.

The new helper and ZIP search method have the same AST as the tested iLEAPP implementation. Nine new tests cover 24,008 generated POSIX/Windows-normalization comparisons, real ZIP staging/order/bytes, bracket fallback, sidecars/directories, cached first-hit behavior, forced re-staging, no matches, corrupt-member continuation and reduced matcher calls.

- macOS arm64, Python 3.14.6 baseline: 4,546 tests, zero failures/errors, 19 skips.
- Candidate: **4,555 tests, zero failures/errors, 19 skips**, including the nine new tests.
- Native Windows 11 ARM64: **35 fabricated ZIP/filter/repeated-member/Windows-name tests passed on both Python 3.11.9 and 3.12.10**, with zero failures/errors/skips. Existing isolated interpreters were used without dependency updates; source copies were verified unchanged. A full Windows suite and native Windows corpus/performance run were not performed for this port.

## Corpus profile comparison

A hash-verified local ZIP input was read without modification. Source size and mtime remained unchanged afterward. Baseline/candidate used the same code apart from the search method, input, profile, `--hash`, output naming and instrumentation. The saved original method was compiled before the baseline run. All eight fresh-process outputs were retained: unmeasured baseline/candidate warm-ups, then B1, C1, C2, B2, B3, C3. Medians exclude warm-ups. VMs were running but native tests, unit suites and other benchmark jobs had finished before these serial timing runs. These are warm shared-machine results, not cold or isolated-hardware measurements.

All eight outputs matched in ordered search fingerprints, cache flags, match/staged counts, typed/ordered evidence database contents and relationships, manifest, artifact HTML tables, media, exports, staged paths/bytes and non-SHM filesystem mtimes. Database integrity checks passed. Artifact execution timestamps/output folders and process-local framework file IDs were canonicalized; evidence dates and artifact-row order were retained. Framework file-ID records/relations preserve full record identity and multiplicity. Runtime SHM filesystem mtimes and export SQLite storage sidecars are excluded, with logical database contents read normally. No parser-error markers were found. Detailed reports and raw logs are retained locally.

| Focused measurement | Baseline | Candidate |
| --- | ---: | ---: |
| Wall median (range), seconds | 5.387059 (5.346850–5.462010) | 5.309442 (5.214308–5.536298) |
| Search median, seconds | 0.111617 | 0.114061 |
| Peak RSS median, MiB | 111.28 | 107.44 |

The input had 195 eligible members. Positive output comparison covered 1,702 rows across 3 artifact outputs, 8 database tables, 193 staged files and 5 exports. The profile selected `sysmonProcessEvents`, `sysmonNetworkConnections`, `sysmonDnsQueries`.

The compact input showed only a small overall difference. Short run times or overlapping ranges do not support a broad end-to-end speedup claim; startup/parsing can dominate these small-input workloads.

Small RSS differences are not claimed as memory savings.

## Controlled large-name scan

This separate enumeration-only probe used the actual baseline/candidate methods with an already-staged identity mapping. No archive extraction or corpus payload is involved. There are 250,000 fabricated cache paths plus three known matches, for **250,003 names**. Each pattern has three warm repetitions with alternating version order. Every ordered result matched both the other method and an independent `fnmatchcase` result.

| Pattern | Matches | Baseline median, seconds | Candidate median, seconds |
| --- | ---: | ---: | ---: |
| `*/databases/History` | 1 | 0.063495 | 0.032586 |
| `*/databases/contacts2.db` | 1 | 0.063385 | 0.034867 |
| `*/settings/*.json` | 1 | 0.163382 | 0.032615 |
| `*/not-present/file.db` | 0 | 0.063052 | 0.035554 |
| `*[ab].db` | 0 | 0.141657 | 0.147326 |
| `*` | 250,003 | 0.073328 | 0.078422 |

For the four selective patterns, the sum of per-pattern medians fell from **0.353312 to 0.135623 seconds**, or **2.61x**. This is a controlled search-stage result, not a complete extraction/report speedup.

Bracket-fallback and match-all controls can pay overhead; their exact medians are included above rather than claiming every pattern improves. Larger member lists and selective literals benefit most. The change adds no second retained filename collection.

## Provenance and reproduction

- Baseline commit: `8e123598130489a0be665d3a9f9480895b16df95`.
- Original search module SHA256: `1f283778f24fd569dd8e67fde114d70da2881792d7928ba97decec072d996f1d`.
- Candidate SHA256: `1082ded15fb6d37ff89c810928cda1fbef3f5e4d0e21c13a6b3da229cd400f57`.

Run the same input/profile/options in separate baseline and candidate output directories, warm both versions, alternate order and retain all repetitions. The private corpus payload is not part of this PR. A profile uses `leapp: "dleapp"`, `format_version: 1` and a `plugins` array of artifact IDs.

```sh
python3 -B dleapp.py -t zip -i /path/to/image.zip -o /path/to/new-output \
  -m /path/to/profile.ilprofile --hash --custom_output_folder report
python3 -B -m unittest discover -s admin/test/scripts -p 'test_seeker_zip_literal_filter.py'
python3 -B -m unittest discover -s admin/test/scripts -p 'test_*.py'
```

The filter-only implementation is a small change with workload-dependent speed benefits. Validation supports review without extending claims to other inputs, untested runtimes or unrelated parser behavior.
