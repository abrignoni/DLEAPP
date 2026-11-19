"""Build native Linux packages (.deb and .rpm) from the PyInstaller one-folder build.

    python packaging/linux/build_linux_packages.py [--folder dist/DLEAPP] [--out dist] deb
    python packaging/linux/build_linux_packages.py [--folder dist/DLEAPP] [--out dist] rpm
    python packaging/linux/build_linux_packages.py all

Wraps ``dist/DLEAPP/`` (``python packaging/build.py exe`` on Linux) into
``/opt/dleapp`` plus a ``/usr/bin/dleapp`` symlink, a desktop entry, an icon
and a man page, so the installed program is the same frozen binary the
AppImage ships: no Python environment or pip install needed on the target.

The .deb is assembled with the standard library only (ar + gzip + tar), so
it builds anywhere. The .rpm needs ``rpmbuild`` (``sudo apt install rpm`` on
Debian/Ubuntu, ``sudo dnf install rpm-build`` on Fedora/RHEL).

Version: read from ``scripts/version_info.py`` as text, like packaging/build.py
does. A ``-dev`` suffix becomes ``~dev`` for dpkg (sorts before the release)
and a ``0.1.dev`` Release for rpm (Version takes numbers only).
Architecture comes from the build machine (``--arch`` overrides):
x86_64 -> amd64 (deb) / x86_64 (rpm), aarch64/arm64 -> arm64 (deb) / aarch64 (rpm).

Layout inside both packages:

    /opt/dleapp/...                 the one-folder build, whole
    /usr/bin/dleapp -> /opt/dleapp/dleapp
    /usr/share/applications/dleapp.desktop
    /usr/share/icons/hicolor/256x256/apps/dleapp.png
    /usr/share/pixmaps/dleapp.png
    /usr/share/doc/dleapp/copyright
    /usr/share/man/man1/dleapp.1.gz (deb: same path)

Check what came out with ``dpkg-deb -I`` / ``dpkg-deb -c`` and
``rpm -qip`` / ``rpm -qlp``. Install tests live in test_builds.yml.
"""

from __future__ import annotations

import argparse
import gzip
import io
import os
import platform
import re
import shutil
import struct
import subprocess
import sys
import time
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LINUX_PACKAGING = ROOT / "packaging" / "linux"
DESKTOP_FILE = LINUX_PACKAGING / "dleapp.desktop"
MAN_PAGE = LINUX_PACKAGING / "dleapp.1"
ICON_PNG = ROOT / "assets" / "icon.png"
FOLDER_BUILD = ROOT / "dist" / "DLEAPP"
EXE = "dleapp"
PKG = "dleapp"
MAINTAINER = "Alexis Brignoni <noreply@github.com>"
HOMEPAGE = "https://github.com/abrignoni/DLEAPP"
DESCRIPTION_SHORT = "Desktop Logs Events And Protobuf Parser"
DESCRIPTION_LONG = (
    " DLEAPP parses artifacts left behind by desktop applications: the logs,\n"
    " events, and stored data of Electron/Chromium-based desktop apps\n"
    " (IndexedDB/LevelDB stores including protobuf-encoded values, Local\n"
    " Storage, service-worker and HTTP caches, cookies, and application logs).\n"
    " .\n"
    " This package ships the frozen PyInstaller build under /opt/dleapp with a\n"
    " /usr/bin/dleapp symlink, so no Python environment is needed to run it."
)
LICENSE = "MIT"


def _mtime() -> int:
    """SOURCE_DATE_EPOCH when set (reproducible release builds), else now."""
    if os.environ.get("SOURCE_DATE_EPOCH"):
        try:
            return int(os.environ["SOURCE_DATE_EPOCH"])
        except ValueError:
            pass
    return int(time.time())


def read_version() -> str:
    """The version string from scripts/version_info.py, read as text (see build.py)."""
    text = (ROOT / "scripts" / "version_info.py").read_text(encoding="utf-8")
    m = re.search(r"""^dleapp_version\s*=\s*['"]([^'"]+)['"]""", text, re.M)
    if not m:
        sys.exit("build_linux_packages: could not find dleapp_version in scripts/version_info.py")
    return m.group(1)


def numeric_version(version: str) -> str:
    """Leading numbers of a version, '2026.4.2' from '2026.4.2-dev'."""
    m = re.match(r"\d+(?:\.\d+){0,3}", version)
    if not m:
        sys.exit(f"build_linux_packages: version {version!r} does not start with a number")
    return m.group(0)


def deb_version(version: str) -> str:
    """A dpkg-parseable version: '-' would split upstream/revision, so it becomes '~'.

    '~' sorts before the empty string, so 2026.4.6~dev < 2026.4.6 and the
    release upgrade works.
    """
    return version.replace("-", "~").replace("_", "~")


def rpm_version_release(version: str) -> tuple[str, str]:
    """(Version, Release) for the spec: Version takes no '-', the rest is Release."""
    if "-" in version:
        upstream, suffix = version.split("-", 1)
        suffix = re.sub(r"[^A-Za-z0-9.+~]+", ".", suffix).strip(".") or "dev"
        return upstream, f"0.1.{suffix}"
    return version, "1"


def deb_arch(machine: str | None = None) -> str:
    machine = (machine or platform.machine()).lower()
    if machine in ("x86_64", "amd64"):
        return "amd64"
    if machine in ("aarch64", "arm64"):
        return "arm64"
    sys.exit(f"build_linux_packages: no .deb architecture mapping for {machine}")


def rpm_arch(machine: str | None = None) -> str:
    machine = (machine or platform.machine()).lower()
    if machine in ("x86_64", "amd64"):
        return "x86_64"
    if machine in ("aarch64", "arm64"):
        return "aarch64"
    sys.exit(f"build_linux_packages: no .rpm architecture mapping for {machine}")


def _tarinfo(tar: tarfile.TarFile, name: str, data: bytes, mode: int) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(data)
    info.mode = mode
    info.uid = 0
    info.gid = 0
    info.uname = "root"
    info.gname = "root"
    info.mtime = _mtime()
    tar.addfile(info, io.BytesIO(data))


def _mkdirs(tar: tarfile.TarFile, path: str, seen: set[str]) -> None:
    """Emit dir entries for path and every parent, once each (dpkg needs them)."""
    parts = [p for p in path.strip("/").split("/") if p]
    for i in range(1, len(parts) + 1):
        entry = "/".join(parts[:i])
        if entry in seen:
            continue
        seen.add(entry)
        info = tarfile.TarInfo(entry)
        info.type = tarfile.DIRTYPE
        info.mode = 0o755
        info.uid = 0
        info.gid = 0
        info.uname = "root"
        info.gname = "root"
        info.mtime = _mtime()
        tar.addfile(info)


def _add_tree(tar: tarfile.TarFile, source: Path, dest: str, seen: set[str]) -> None:
    """Append source/ under dest/, dirs as 0755, files keeping only their exec bits."""
    _mkdirs(tar, dest, seen)
    for dirpath, dirnames, filenames in os.walk(source):
        dirnames.sort()
        rel = Path(dirpath).relative_to(source)
        arc_dir = dest if str(rel) == "." else f"{dest}/{rel.as_posix()}"
        if arc_dir not in seen:
            seen.add(arc_dir)
            info = tarfile.TarInfo(arc_dir)
            info.type = tarfile.DIRTYPE
            info.mode = 0o755
            info.uid = 0
            info.gid = 0
            info.uname = "root"
            info.gname = "root"
            info.mtime = _mtime()
            tar.addfile(info)
        for name in sorted(filenames):
            path = Path(dirpath) / name
            if path.is_symlink():
                target = os.readlink(path)
                link = tarfile.TarInfo(f"{arc_dir}/{name}")
                link.type = tarfile.SYMTYPE
                link.linkname = target
                link.uid = 0
                link.gid = 0
                link.uname = "root"
                link.gname = "root"
                link.mtime = _mtime()
                tar.addfile(link)
                continue
            st = path.stat()
            mode = 0o755 if st.st_mode & 0o111 else 0o644
            info = tarfile.TarInfo(f"{arc_dir}/{name}")
            info.size = st.st_size
            info.mode = mode
            info.uid = 0
            info.gid = 0
            info.uname = "root"
            info.gname = "root"
            info.mtime = _mtime()
            with open(path, "rb") as handle:
                tar.addfile(info, handle)


def _add_symlink(tar: tarfile.TarFile, name: str, target: str) -> None:
    info = tarfile.TarInfo(name)
    info.type = tarfile.SYMTYPE
    info.linkname = target
    info.uid = 0
    info.gid = 0
    info.uname = "root"
    info.gname = "root"
    info.mtime = _mtime()
    tar.addfile(info)


def control_content(version: str, arch: str) -> str:
    return (
        f"Package: {PKG}\n"
        f"Version: {version}\n"
        f"Architecture: {arch}\n"
        f"Maintainer: {MAINTAINER}\n"
        f"Installed-Size: 0\n"
        "Section: utils\n"
        "Priority: optional\n"
        "Depends: libc6 (>= 2.35)\n"
        f"Homepage: {HOMEPAGE}\n"
        f"Description: {DESCRIPTION_SHORT}\n"
        f"{DESCRIPTION_LONG}\n"
    )


def copyright_content() -> str:
    return (
        f"Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/\n"
        f"Source: {HOMEPAGE}\n"
        f"\n"
        f"Files: *\n"
        f"Copyright: 2020 Alexis Brignoni and contributors\n"
        f"License: {LICENSE}\n"
    )


def _write_ar(path: Path, members: list[tuple[str, bytes]]) -> None:
    """Write a GNU ar archive (what a .deb is) with zero padding for odd sizes."""
    with open(path, "wb") as out:
        out.write(b"!<arch>\n")
        for name, data in members:
            header = struct.pack(
                "16s12s6s6s8s10s2s",
                name.encode("ascii")[:16].ljust(16),
                str(0).encode("ascii").ljust(12),
                b"0".ljust(6),
                b"0".ljust(6),
                oct(0o100644)[2:].encode("ascii").ljust(8),
                str(len(data)).encode("ascii").ljust(10),
                b"`\n",
            )
            out.write(header)
            out.write(data)
            if len(data) % 2:
                out.write(b"\n")


def _gzip(data: bytes) -> bytes:
    buf = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buf, mtime=0) as gz:
        gz.write(data)
    return buf.getvalue()


def build_deb(folder: Path, out_dir: Path, version: str | None = None,
              arch: str | None = None) -> Path:
    """Assemble the .deb from the one-folder build with the stdlib only."""
    exe = folder / EXE
    if not exe.is_file():
        sys.exit(f"build_linux_packages: {exe} not found; run 'python packaging/build.py exe' first")
    if not DESKTOP_FILE.is_file():
        sys.exit(f"build_linux_packages: {DESKTOP_FILE} is missing")
    if not ICON_PNG.is_file():
        sys.exit(f"build_linux_packages: {ICON_PNG} is missing")
    version = deb_version(version or read_version())
    arch = arch or deb_arch()

    control_tar = io.BytesIO()
    with tarfile.open(fileobj=control_tar, mode="w") as tar:
        _tarinfo(tar, "control", control_content(version, arch).encode("utf-8"), 0o644)
    control_gz = _gzip(control_tar.getvalue())

    data_tar = io.BytesIO()
    with tarfile.open(fileobj=data_tar, mode="w") as tar:
        seen: set[str] = set()
        _add_tree(tar, folder, "opt/dleapp", seen)
        _mkdirs(tar, "usr/bin", seen)
        _add_symlink(tar, "usr/bin/dleapp", "/opt/dleapp/dleapp")
        for name in ("usr/share/applications",
                     "usr/share/icons/hicolor/256x256/apps",
                     "usr/share/pixmaps",
                     "usr/share/doc/dleapp",
                     "usr/share/man/man1"):
            _mkdirs(tar, name, seen)
        _tarinfo(tar, "usr/share/applications/dleapp.desktop",
                 DESKTOP_FILE.read_bytes(), 0o644)
        icon = ICON_PNG.read_bytes()
        _tarinfo(tar, "usr/share/icons/hicolor/256x256/apps/dleapp.png", icon, 0o644)
        _tarinfo(tar, "usr/share/pixmaps/dleapp.png", icon, 0o644)
        _tarinfo(tar, "usr/share/doc/dleapp/copyright",
                 copyright_content().encode("utf-8"), 0o644)
        if MAN_PAGE.is_file():
            with tempfile.TemporaryDirectory(prefix="dleapp-man-") as tmp:
                gz_path = Path(tmp) / "dleapp.1.gz"
                with open(MAN_PAGE, "rb") as src, open(gz_path, "wb") as raw:
                    with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as dst:
                        shutil.copyfileobj(src, dst)
                _tarinfo(tar, "usr/share/man/man1/dleapp.1.gz",
                         gz_path.read_bytes(), 0o644)
    data_gz = _gzip(data_tar.getvalue())

    out_dir.mkdir(parents=True, exist_ok=True)
    deb = out_dir / f"{PKG}_{version}_{arch}.deb"
    _write_ar(deb, [
        ("debian-binary", b"2.0\n"),
        ("control.tar.gz", control_gz),
        ("data.tar.gz", data_gz),
    ])
    print(f"==> .deb: {deb} ({deb.stat().st_size:,} bytes)")
    return deb


def _rpm_spec_template() -> str:
    return (LINUX_PACKAGING / "dleapp.spec").read_text(encoding="utf-8")


def build_rpm(folder: Path, out_dir: Path, version: str | None = None,
              arch: str | None = None) -> Path:
    """Build the .rpm with rpmbuild from the one-folder build."""
    exe = folder / EXE
    if not exe.is_file():
        sys.exit(f"build_linux_packages: {exe} not found; run 'python packaging/build.py exe' first")
    rpmbuild = shutil.which("rpmbuild")
    if rpmbuild is None:
        sys.exit("build_linux_packages: rpmbuild not found "
                 "('sudo apt install rpm' / 'sudo dnf install rpm-build'), "
                 "cannot build the .rpm")
    version = version or read_version()
    rpm_version, rpm_release = rpm_version_release(version)
    arch = arch or rpm_arch()

    with tempfile.TemporaryDirectory(prefix="dleapp-rpm-") as tmp:
        topdir = Path(tmp) / "rpmbuild"
        for sub in ("BUILD", "RPMS", "SOURCES", "SPECS", "SRPMS"):
            (topdir / sub).mkdir(parents=True)
        copyright_file = Path(tmp) / "copyright"
        copyright_file.write_text(copyright_content(), encoding="utf-8")
        spec = _rpm_spec_template().format(
            rpm_version=rpm_version,
            rpm_release=rpm_release,
            summary=DESCRIPTION_SHORT,
            license=LICENSE,
            homepage=HOMEPAGE,
            rpm_arch=arch,
            description=DESCRIPTION_SHORT + ".",
            folder=str(folder.resolve()),
            desktop=str(DESKTOP_FILE.resolve()),
            icon=str(ICON_PNG.resolve()),
            man=str(MAN_PAGE.resolve()),
            copyright=str(copyright_file),
        )
        spec_path = topdir / "SPECS" / "dleapp.spec"
        spec_path.write_text(spec, encoding="utf-8")
        result = subprocess.run(
            [rpmbuild, "-bb", str(spec_path),
             "--define", f"_topdir {topdir}",
             "--define", "_build_id_links none",
             "--target", arch],
            capture_output=False, check=False)
        if result.returncode != 0:
            sys.exit(f"build_linux_packages: rpmbuild exited {result.returncode}")
        rpms = sorted((topdir / "RPMS").rglob("*.rpm"))
        if not rpms:
            sys.exit("build_linux_packages: rpmbuild produced no .rpm")
        out_dir.mkdir(parents=True, exist_ok=True)
        dest = out_dir / rpms[0].name
        if dest.exists():
            dest.unlink()
        shutil.copyfile(rpms[0], dest)
        print(f"==> .rpm: {dest} ({dest.stat().st_size:,} bytes)")
        return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="build_linux_packages.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("what", nargs="*", default=["all"],
                        help="deb, rpm, or all (default)")
    parser.add_argument("--folder", default=str(FOLDER_BUILD),
                        help="the one-folder build to wrap (default: %(default)s)")
    parser.add_argument("--out", default="dist",
                        help="where to write the packages (default: %(default)s)")
    parser.add_argument("--arch", default=None,
                        help="override the architecture detection (deb: amd64/arm64; rpm: x86_64/aarch64)")
    args = parser.parse_args(argv)

    folder = Path(args.folder)
    out_dir = Path(args.out)
    wants = set(args.what)
    if wants == {"all"}:
        wants = {"deb", "rpm"}
    unknown = wants - {"deb", "rpm"}
    if unknown:
        parser.error(f"unknown package(s): {', '.join(sorted(unknown))} (want deb, rpm or all)")

    version = read_version()
    print(f"==> DLEAPP {version} -> {', '.join(sorted(wants))}")
    if "deb" in wants:
        build_deb(folder, out_dir, version, args.arch or deb_arch())
    if "rpm" in wants:
        build_rpm(folder, out_dir, version, args.arch or rpm_arch())
    return 0


if __name__ == "__main__":
    sys.exit(main())
