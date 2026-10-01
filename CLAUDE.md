# DLEAPP

Desktop application forensics parser, built from RLEAPP. Parses desktop app data for
Telegram, Signal Desktop, Discord, Wire and Roblox, on Windows, macOS and Linux.

## What that changes

- **The input is a desktop filesystem**, so paths are OS-dependent in a way the mobile
  cores are not. The same app stores data under `%APPDATA%`, `~/Library/Application Support`
  and `~/.config` depending on platform. An artifact meant to be cross-platform needs a
  pattern for each, and `.claude/rules/leapp-artifact-paths.md` matters more here because of it.
- **Desktop apps encrypt at rest more often than mobile ones.** Several parsers here depend
  on unwrapping a key first, and the key may come from the OS credential store rather than
  the app. Where a key must be supplied by the examiner, take it as an explicit CLI input;
  never attempt to read a live credential store.

## Before changing an artifact

This repo does not carry the module-authoring docs. **iLEAPP's
[`admin/docs/artifact_info_block.md`](https://github.com/abrignoni/iLEAPP/blob/main/admin/docs/artifact_info_block.md)
is the reference for the `__artifacts_v2__` block** and applies here unchanged: same
loader, same seekers, same glob semantics.

## Repo-specific things worth knowing

- App-specific helpers live beside the framework in `scripts/` (`telegram.py`,
  `whatsapp.py`, `signal_desktop.py`, `roblox.py`) rather than inside
  `scripts/artifacts/`. Artifacts import from them.
- Some modules build `__artifacts_v2__` through a helper instead of declaring it literally.
  The CI checkers `ast.literal_eval` the block, so those modules are silently skipped.
  Prefer a literal dict in new modules.
- This is the newest core, so it is usually last to receive a shared fix. When porting,
  read the local helper rather than assuming it matches the source you copied from.
- `admin/docs/why-no-login-keychain-recovery.md` records a deliberate scope decision. Read
  it before proposing keychain-based recovery.
- **Builds are made by `packaging/build.py`**, one PyInstaller spec for every platform and
  one executable, `dleapp`, that opens the window without arguments. Every artifact module
  is a hidden import, so what the artifacts import is followed without a list. What it
  cannot follow is a name built at run time (`importlib.import_module(some_variable)`) or a
  data file kept outside `scripts/`, `leapp_functions/` or `assets/`: expect a working dev
  run and a broken build, and run `python packaging/build.py smoke` or `test_builds.yml`.
  The Unified Log parser ships only when fetched into `bin/`, and never without its licence
  and notices. See `.claude/rules/dleapp-build-and-release.md`.

## Rules

`.claude/rules/` holds the detail. Files prefixed `leapp-` are shared across all five
extractors and `lava-` across all six repos. **Edit those at their canonical source, not
here**, or the next sync overwrites you.
