
---

## Which file to download

| Platform | File |
|---|---|
| Windows 10 or 11, 64-bit Intel or AMD | `-windows-x64-portable.zip` |
| Windows 11 on ARM | `-windows-arm64-portable.zip` |
| macOS, Apple silicon | `-macos-arm64.dmg` |
| macOS, Intel | `-macos-x64.dmg` |
| Linux, 64-bit Intel or AMD (AppImage) | `-linux-x64.AppImage` |
| Linux on ARM (AppImage) | `-linux-arm64.AppImage` |
| Debian/Ubuntu, 64-bit Intel or AMD | `-linux-x64.deb` |
| Debian/Ubuntu on ARM | `-linux-arm64.deb` |
| Fedora/RHEL/openSUSE, 64-bit Intel or AMD | `-linux-x64.rpm` |
| Fedora/RHEL/openSUSE on ARM | `-linux-arm64.rpm` |

The `.deb` installs with `sudo dpkg -i`, the `.rpm` with `sudo dnf install`
(`zypper install` on openSUSE). Both carry the same frozen `dleapp` under
`/opt/dleapp` with a `/usr/bin/dleapp` symlink, so no Python setup is needed.

## One-line install

```bash
curl -fsSL https://raw.githubusercontent.com/abrignoni/DLEAPP/main/install.sh | bash
```

Picks the native package for the machine, verifies it against
`SHA256SUMS.txt`, and installs it; elsewhere it installs the AppImage.
Re-running it upgrades. `METHOD=`, `TAG=` and `PREFIX=` are documented at the
top of
[install.sh](https://github.com/abrignoni/DLEAPP/blob/main/install.sh).

## Arch Linux

`dleapp-bin` follows the latest release, `dleapp-git` the latest commit
(rebuild it on `--devel` upgrades):

```bash
paru -S dleapp-bin   # or: yay -S dleapp-bin
paru -S dleapp-git
```

Every download holds one program, `dleapp`. Started without arguments, from the
Applications folder or a double-click, it opens the window. Given arguments in a terminal,
it is the command line. On macOS the command line is inside the app:

```bash
/Applications/DLEAPP.app/Contents/MacOS/dleapp --help
```

**For tools that run DLEAPP themselves.** The options, output and exit codes of `dleapp`
are those of earlier releases, but there is no `dleappGUI` any more, since `dleapp`
without arguments opens the window. On Windows the zip holds the whole program as one
file, `dleapp.exe`, which can be put wherever the tool expects it; there is no installer.
The executable inside the macOS app needs the folder it came in; on Linux the AppImage is
the whole program.

**`dleapp.exe` on Windows** unpacks itself to a temporary folder each time it starts, so it
takes a few seconds to start, and it does not run where a policy (AppLocker, WDAC) forbids
running programs from the temporary folder. There, run DLEAPP from source; the README has
the steps.

## First launch

The macOS disk images are signed with a Developer ID and notarised by Apple, so they open
without a warning.

The Windows binaries are not signed yet, so SmartScreen says "Windows protected your PC"
the first time. Choose More info, then Run anyway.

On Linux, make the AppImage executable once (`chmod +x DLEAPP-*.AppImage`). It needs FUSE
to start; where FUSE is not available, run it with `--appimage-extract-and-run`.
The `.deb` and `.rpm` need neither: they install the same frozen `dleapp` under
`/opt/dleapp` with a `/usr/bin/dleapp` symlink (`sudo dpkg -i DLEAPP-*.deb`,
`sudo dnf install DLEAPP-*.rpm`). On Arch, `dleapp-bin` follows the latest
release and `dleapp-git` the latest commit.

If you would rather not clear a warning, run from source instead; the README has the steps.

## Verify what you downloaded

`SHA256SUMS.txt` covers every file in this release. On macOS or Linux, from the folder you
downloaded into:

```bash
grep <the file you downloaded> SHA256SUMS.txt | shasum -a 256 -c -
```

Use `sha256sum` in place of `shasum -a 256` on Linux. On Windows, in PowerShell:

```powershell
(Get-FileHash -Algorithm SHA256 .\<the file you downloaded>).Hash
```

and compare it with the line in `SHA256SUMS.txt`, which is lower case.

## Linux

The build is made on Ubuntu 22.04, so it needs glibc 2.35 or newer and will not start on
an older distribution.

## Third-party licences

DLEAPP's own code is MIT. To show HEIC images the packaged programs include heicreader, which is
MIT and built from MIT and BSD-3-Clause code. The licence texts are in the `LICENSES` folder
inside every download and in `LICENSES/THIRD-PARTY-NOTICES.md` in the repository.
`LICENSES/bundled/` in every download holds the licence of each Python package the program
carries and of each library it takes from the build machine, and its index names the ones under copyleft terms, such as simplekml (LGPL), with a
link to their source.

## Code signing policy

The [code signing policy](https://github.com/abrignoni/DLEAPP#code-signing-policy) covers
Windows signing, team roles and privacy.
