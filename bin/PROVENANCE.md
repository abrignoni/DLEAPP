# bin/

Holds the third-party `unifiedlog_iterator` executable, which reads Apple Unified Log
`.tracev3` data directly, so DLEAPP can read the Unified Logs in a Mac extraction without a
Mac and without Apple's `log show`. See `scripts/unifiedlogs.py` for how DLEAPP calls it.

The executable is **not committed**. It is fetched per build:

```
python admin/scripts/fetch_unifiedlog_iterator.py
```

That verifies a pinned SHA-256 before writing anything, and also writes
`LICENSE-unifiedlog_iterator` next to the binary. A build without it still succeeds and
ships without native Unified Log support; when such a build finds tracev3 data, the run log
says the binary was not found.

## What is pinned

| Platform | Archive sha256 |
|---|---|
| macOS arm64 | `bf5c4a3418b133fbd403ca7893a2280acb8c2c3605b4ad6f87f9fc75b35a20b7` |
| macOS x86_64 | `32e23956c3ac6364f56e96243357cf02959f79a6e24a5afddba1047914bf7f1a` |
| Linux arm64 (gnu) | `ab40daf464376a2e52c4b51fd82b003b7f360a4e2726501ba853889fa3a959f4` |
| Linux x86_64 (musl) | `c1fea0f142850ac05e0faf66f3d69aca848793bc121e972238fb1927daf31004` |
| Linux x86_64 (gnu) | `7192a187f93c6fb8eafdad9885522e73dc2ae7a9a5000f5957edd4fcd0ca1c82` |
| Windows x86_64 | `4776ac9c677ad3bdec6a0cee3e92e27308f7493a0ac4e4fedde65555eb36373d` |

Project: [mandiant/macos-UnifiedLogs](https://github.com/mandiant/macos-UnifiedLogs),
version v0.7.0 (released 2026-09-14), Apache-2.0 (`LICENSE-unifiedlog_iterator`). The fetch
script, the pins and this table are the ones iLEAPP uses for the same release.

Digest comparison in the fetch script is case-insensitive: upstream publishes the Windows
`.sha256` in uppercase and the others in lowercase, and some of the files print the digest
twice on one line. When bumping PINNED_VERSION, download each archive, hash it yourself,
and pin all six.

`linux-x86_64` fetches the **musl** build, which carries no dynamic libc dependency. The
gnu build links the glibc of the machine that built it, and a binary built against a newer
glibc refuses to start on an older distribution with `version 'GLIBC_x.yy' not found`.
`--platform linux-x86_64-gnu` remains available. No musl build is published for aarch64.

## Why the version is pinned

An examiner needs to be able to say which parser produced a set of records. Pin the
version, record it here, and change both together. The run log records the version the
binary reports, `unifiedlog_iterator 0.7.0`, at the start of each import.

## License obligations

Apache-2.0 permits redistribution inside this MIT-licensed project. For any build that
includes the binary:

- `LICENSE-unifiedlog_iterator` ships beside it.
- `THIRD-PARTY-NOTICES-unifiedlog_iterator.txt` ships beside it. The binary statically
  links Rust crates published under their own licenses; every one of the 57 on the list
  offers MIT or Apache-2.0, alone or as one of the choices its declared license gives.
  Upstream's release archive carries only its own LICENSE, so the notices are generated
  here by `admin/scripts/make_unifiedlog_notices.py` and committed. Its `--verify` option
  checks a fetched binary against the committed file without network access, and the test
  builds run it after fetching.
- The PyInstaller specs refuse to build when the binary is present and either file is not.
- Attribution stays in the README's Acknowledgements.
