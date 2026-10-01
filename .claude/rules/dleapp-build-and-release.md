# Build and release

One driver, `packaging/build.py`, on every platform, in two phases so a signed build is
possible. It replaced six PyInstaller specs, one per program and platform, each with its own
hand-kept list of hidden imports and its own copy of the version. It is a port of iLEAPP's
(abrignoni/iLEAPP#2298), Unified Log parser included, with what RLEAPP and VLEAPP added
since: `compression.zstd` named outright, and an Inno Setup `AppId` of its own. Before it,
only the Windows builds were made in CI; macOS and Linux were not built anywhere.

    python packaging/build.py exe               phase 1: dist/DLEAPP/ holding dleapp; on macOS also dist/DLEAPP.app
    python packaging/build.py exe --onefile     phase 1: dist/dleapp, a single file; no installer from this
    python packaging/build.py smoke             run what phase 1 built, headlessly (xvfb-run on Linux)
    python packaging/build.py installer         phase 2: Windows dist/DLEAPP-Setup-<v>.exe, macOS dist/DLEAPP-<v>.dmg,
                                                Linux dist/DLEAPP-<v>.AppImage
    python packaging/build.py installer --sign-tool NAME
                                                Windows: Inno Setup signs the installer and the uninstaller
    python packaging/build.py all               both phases, unsigned; refuses --sign-tool and --onefile
    python packaging/build.py verify PATH ...   a signature is present and valid; --subject checks the signer

## One executable, the window or the command line

The spec builds `packaging/entrypoint.py`, not `dleapp.py` or `dleappGUI.py`, which stay the
way to run from source. The result is one executable, `dleapp`, and there is no `dleappGUI`
in a build. Started without arguments, as a double-click, the Start menu or the Finder
start it, it opens the window. Given arguments it is the command line, exactly as before,
so tools that run `dleapp -t fs -i ... -o ...` see no change. Where no window can open
(Linux with no display, as over SSH) it prints the command line's help.

It is a console program. On Windows `hide_console="hide-early"`, which the old GUI build
used, hides the console when nobody started it from one: from the desktop there is no
terminal, from a terminal it prints and returns its exit code. On macOS it is the bundle's
own executable, `DLEAPP.app/Contents/MacOS/dleapp`. `console=True` makes PyInstaller mark
the bundle `LSBackgroundOnly`, which leaves the window without a Dock icon or menu bar, so
the spec sets it back to false.

The bundle identifier is `org.leapps.DLEAPP`. It replaced `4n6.brigs.DLEAPP`, the earlier
GUI bundle's, so macOS treats the two as different apps: permissions granted to the old
one, Full Disk Access included, have to be granted again.

`scripts/lavafuncs.py` records `leapp_mode` from the script name from source and, in a
build, from whether a `*leappGUI` module was loaded, which only the window's path does.
That file is shared across the LEAPPs; the check is the one iLEAPP, ALEAPP, RLEAPP and
VLEAPP carry.

The Inno Setup `AppId` is DLEAPP's own GUID. The script was ported from iLEAPP's, and
Windows identifies an installed program by that GUID: a shared one makes installing one
LEAPP upgrade or uninstall another. A test holds it apart from the other four LEAPPs'.

## What goes into the bundle

Decided in `build.py`, which the spec loads, so it is tested without running PyInstaller
(`admin/test/scripts/test_packaging_build.py`, which also exec's the spec with PyInstaller
stubbed out).

- `scripts/`, `leapp_functions/` and `assets/` ship as files, without `__pycache__`. The
  plugin loader reads the artifacts from `scripts/artifacts` as source, the report copies
  `scripts/_elements`, and the window loads its images from `assets/`.
- **Every artifact module is also a hidden import.** Shipped as source, the artifacts were
  invisible to PyInstaller's analysis, and everything they imported had to be listed by
  hand in each spec, and the Windows GUI spec had lost `leapp_functions`. Now their imports
  are followed: Registry, Evtx, olefile, Crypto, argon2, nacl and the rest. What it still
  cannot follow is a module imported by a name built at run time, and an artifact whose
  file name is not a valid module name, which ships and loads but is not analysed.
- `compression.zstd` is named outright: `scripts/search_files.py` imports it by a name
  built at run time, and a zstd tar, SquashFS or UBIFS needs it. It exists from Python
  3.14, which the builds use.
- `Evtx`, `PIL` and `leapp_functions` are collected whole: a macOS build without all of
  python-evtx read no event log. The old specs' explicit list is kept, `pefile` among it,
  which only the Defender artifacts reach through `scripts/windows_messages.py`.
- `pdfminer.six` is in `requirements.txt` but nothing imports it, so nothing collects it.
  It still pulls in `cryptography`, which is why the Windows ARM64 legs build OpenSSL.
- The Unified Log parser, when `admin/scripts/fetch_unifiedlog_iterator.py` has put it in
  `bin/`, as a binary at `bin/` (only binaries keep their execute bit), never without its
  Apache-2.0 licence and its third-party notices. `scripts/unifiedlogs.py` looks for it at
  `sys._MEIPASS/bin`. Without it the build still succeeds.

## Signing goes between the phases

Sign `dleapp.exe` in `dist/DLEAPP/`, or codesign `dist/DLEAPP.app`, after phase 1 and
before phase 2, or the installer ships an unsigned executable inside a signed wrapper.
`all` refuses `--sign-tool` for exactly that reason. PyInstaller signs every macOS build
ad hoc; a Developer ID signature replaces that one. `verify` is the last step before
anything is uploaded.

## What the driver guarantees

The version is read from `scripts/version_info.py` as text and passed to the spec (the
Windows version resource, the bundle's `Info.plist`) and to Inno Setup; `installer.iss`
refuses to compile without it. Windows and macOS take only numbers there, so
`2026.4.2-dev` becomes `2026.4.2` in those fields. `ONEFILE` reaches the spec through
`DLEAPP_ONEFILE`; the spec is never edited by a build. PyInstaller and dmgbuild are pinned
in `packaging/requirements-build.txt`, which phase 1 installs with `requirements.txt`.
Every artifact is asserted to exist after the step that makes it; an exit code is not
evidence. `--clean` removes `build/` and the driver's own output in `dist/`, never the rest
of `dist/`, where release archives get made by hand.

`dist/dleapp` and `dist/DLEAPP/` are the same path on a case-insensitive file system, the
default on macOS, and PyInstaller's `--noconfirm` deletes whatever is there. The driver
refuses to build one layout over the other; `--clean` is the explicit way.

## What `smoke` checks, and why each

`--version` against `scripts/version_info.py`; a run over an empty extraction, which loads
and runs every artifact and writes a report; a run over the NTFS raw fixture, whose log has
to show the walk; the bundled parser, run from where the app looks for it, with its
licence and notices beside it (read from the archive inside the executable for
`--onefile`); and `dleapp --selfcheck`, which takes the window's path, starts Tk, loads the
images from `assets/` and every artifact, then exits before drawing a window. The
self-check reports how many artifacts it loaded and `smoke` compares that with the count
from source, which is how a module missing from the build shows up. On Linux it also
starts `dleapp` with no arguments and no display, which must print the command line's
help. On macOS all of it runs against the `.app`, the layout that ships, not the one-folder
build beside it.

Measured on 2026-10-01, macOS arm64, Python 3.14.7, PyInstaller 6.22.3, with the parser
fetched: phase 1 in 29 s (requirements installed in the same run), `smoke` in 5 s, 479
artifacts loaded by the build and from source, a 107 MB bundle and a 49 MB disk image.

## What is and is not wired up

Windows (x64 and ARM64): the folder build and an Inno Setup installer, which on ARM64
installs only on ARM64. macOS (Apple silicon and Intel): `.app` and `.dmg`. The `.dmg` is
laid out by dmgbuild from `packaging/dmg_settings.py`: the app and an Applications link
either side of the arrow on `packaging/dmg_background.png`. The settings place the icons
for that 960x540 image, so a new background keeps its size and its arrow where it is.
The arrow's centre is at x=479, 44 points right of where the LEAPPs drew it before their
backgrounds of 2026-10-01, so the icons are at (304, 290) and (654, 290), as in iLEAPP,
ALEAPP, RLEAPP and VLEAPP. A test finds the arrow on the background and requires the two
icons to straddle it, so a background that moves it again fails there rather than on a Mac.
`dmg_background@2x.png` beside it, at exactly 1920x1080, is what a Retina screen shows:
dmgbuild finds it by name and joins the two into one TIFF with `tiffutil
-cathidpicheck`, which refuses a pair that is not exactly 1x and 2x. Without it the
background is scaled up and blurred on every Retina Mac. Export both from the source;
upscaling the 1x brings the blur back.
Linux (x64 and ARM64): the folder build and an AppImage, made by appimagetool 1.9.1 with the
type2 runtime 20251108, both pinned by digest in `build.py` and run with
`APPIMAGE_EXTRACT_AND_RUN` so the build machine needs no FUSE. The finished AppImage is run
once and has to report the version. Linux builds are made on Ubuntu 22.04 for its glibc
2.35. `test_builds.yml` builds and smoke-tests all six legs weekly, on dispatch, and on pull
requests that touch packaging.

`release.yml` runs the same steps when a `v*` tag is pushed, refuses a tag that is not
`v` + `dleapp_version`, names the assets `DLEAPP-<version>-<platform>-<arch>` (setup.exe and
portable.zip on Windows, .dmg on macOS, .AppImage on Linux; no Linux .tar.gz), stages them
in `release-assets/` (never `assets/`, which holds the window's images), adds
`SHA256SUMS.txt`, and creates a **draft** release; publishing is a click. Dispatched by
hand, it builds the assets without creating a release. `.github/release-footer.md` is
appended to the notes. macOS is signed with a Developer ID, smoke-tested again as signed
(the hardened runtime is what breaks a frozen app), notarised and stapled when the
`MACOS_CERT_P12`, `MACOS_CERT_PASSWORD`, `MACOS_SIGN_IDENTITY`, `MACOS_TEAM_ID`,
`MACOS_NOTARY_KEY`, `MACOS_NOTARY_KEY_ID` and `MACOS_NOTARY_ISSUER_ID` secrets are set.
A tag refuses to publish without them, and the macOS legs check that first, before
building; a dispatched rehearsal builds unsigned. The footer tells users the disk images
are notarised, which holds only because of that refusal. Windows signing is not wired.

Set the release version in `scripts/version_info.py` first, tag that commit, then bump to
the next `-dev`: the tag check compares the two.

These names replaced the per-program downloads (`dleappGUI-v*-Windows_x86_64.zip`,
`dleapp-v*-macOS_Apple_Silicon.zip`, `dleappGUI-v*-macOS_Mac_Intel.dmg` and the like, up to
v2026.4.1), which leapps.org links to. Tools that run `dleapp` from a release are told by
the footer what changed for them: on Windows and macOS the
executable needs its folder, and `dleappGUI` is gone. Keep that note while those names are new.
