"""Native Linux packages (.deb/.rpm), the AUR PKGBUILDs and install.sh.

Builds a .deb from a fake one-folder tree with the standard library only and
checks its structure (ar members, control fields, install layout). The .rpm
path needs rpmbuild and is covered the same way when it is present. The AUR
PKGBUILDs and install.sh are checked statically: syntax, required fields,
and .SRCINFO consistency for dleapp-bin.
"""
import os
import pathlib
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import importlib.util as _importlib_util


def _load_builder():
    # Loaded by path, not as packaging.linux: `packaging` is also the name of
    # a PyPI dependency, which shadows the local directory (see
    # test_packaging_build.py, which loads packaging/build.py the same way).
    path = REPO_ROOT / "packaging" / "linux" / "build_linux_packages.py"
    spec = _importlib_util.spec_from_file_location("dleapp_linux_packages", path)
    module = _importlib_util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pkg = _load_builder()


class VersionMappingTest(unittest.TestCase):
    def test_deb_version_keeps_stable(self):
        self.assertEqual(pkg.deb_version("2026.4.5"), "2026.4.5")

    def test_deb_version_sorts_dev_before_release(self):
        # '~' sorts before the empty string in dpkg, so the dev package
        # upgrades cleanly to the release.
        self.assertEqual(pkg.deb_version("2026.4.6-dev"), "2026.4.6~dev")
        self.assertNotIn("-", pkg.deb_version("2026.4.6-dev"))

    def test_rpm_version_release_stable(self):
        self.assertEqual(pkg.rpm_version_release("2026.4.5"), ("2026.4.5", "1"))

    def test_rpm_version_release_dev_has_no_hyphen(self):
        version, release = pkg.rpm_version_release("2026.4.6-dev")
        self.assertEqual(version, "2026.4.6")
        self.assertNotIn("-", version + release)

    def test_arch_mappings(self):
        self.assertEqual(pkg.deb_arch("x86_64"), "amd64")
        self.assertEqual(pkg.deb_arch("aarch64"), "arm64")
        self.assertEqual(pkg.rpm_arch("x86_64"), "x86_64")
        self.assertEqual(pkg.rpm_arch("aarch64"), "aarch64")

    def test_read_version_matches_repo(self):
        version = pkg.read_version()
        self.assertRegex(version, r"^\d{4}\.\d+\.\d+")
        text = (REPO_ROOT / "scripts" / "version_info.py").read_text(encoding="utf-8")
        self.assertIn(version, text)


class StaticFilesTest(unittest.TestCase):
    def test_desktop_entry(self):
        text = (REPO_ROOT / "packaging" / "linux" / "dleapp.desktop").read_text(encoding="utf-8")
        self.assertIn("[Desktop Entry]", text)
        self.assertIn("Exec=/usr/bin/dleapp", text)
        self.assertIn("Icon=dleapp", text)

    def test_man_page(self):
        man = REPO_ROOT / "packaging" / "linux" / "dleapp.1"
        self.assertTrue(man.is_file())
        self.assertIn(".TH DLEAPP", man.read_text(encoding="utf-8"))

    def test_spec_template_formats(self):
        spec = (REPO_ROOT / "packaging" / "linux" / "dleapp.spec").read_text(encoding="utf-8")
        formatted = spec.format(
            rpm_version="2026.4.5", rpm_release="1", summary="s", license="MIT",
            homepage="https://example.com", rpm_arch="x86_64", description="d.",
            folder="/tmp/f", desktop="/tmp/d", icon="/tmp/i", man="/tmp/m",
            copyright="/tmp/c")
        self.assertIn("Name:           dleapp", formatted)
        self.assertIn("/opt/dleapp/", formatted)
        self.assertNotIn("{rpm_version}", formatted)

    def test_install_sh_syntax(self):
        install_sh = REPO_ROOT / "install.sh"
        self.assertTrue(install_sh.is_file())
        self.assertTrue(bool(install_sh.stat().st_mode & stat.S_IXUSR))
        result = subprocess.run(["bash", "-n", str(install_sh)],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        text = install_sh.read_text(encoding="utf-8")
        self.assertIn("DLEAPP-${VER}-linux-${FARCH}.deb", text)
        self.assertIn("DLEAPP-${VER}-linux-${FARCH}.rpm", text)
        self.assertIn("DLEAPP-${VER}-linux-${FARCH}.AppImage", text)
        self.assertIn("dleapp-bin", text)
        self.assertIn("dleapp-git", text)
        self.assertIn("SHA256SUMS", text)


class AurTest(unittest.TestCase):
    BIN = REPO_ROOT / "packaging" / "aur" / "dleapp-bin"
    GIT = REPO_ROOT / "packaging" / "aur" / "dleapp-git"

    def _read(self, path):
        return (path / "PKGBUILD").read_text(encoding="utf-8")

    def test_bin_tracks_latest_release(self):
        text = self._read(self.BIN)
        self.assertIn("pkgver=2026.4.5", text)
        # AppImage checksums are those of the 2026.4.5 release assets.
        self.assertIn("15e584d32f45d06a17ddcb62bf447f1c63a988c928fec554d29c5d03b8a15169", text)
        self.assertIn("e9f6928df29be97c53de1b9aa36ec0524a45b6c8859acc321b70a778ebe25818", text)
        makepkg = shutil.which("makepkg")
        if makepkg is not None:
            result = subprocess.run([makepkg, "--printsrcinfo"], cwd=str(self.BIN),
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(),
                             (self.BIN / ".SRCINFO").read_text(encoding="utf-8").strip())

    def test_git_builds_latest_commit(self):
        text = self._read(self.GIT)
        self.assertIn("git+https://github.com/abrignoni/DLEAPP.git", text)
        self.assertIn("pkgver()", text)
        self.assertIn("packaging/build.py exe", text)
        # Frozen build bundles its own interpreter: no python runtime dep.
        depends = re.search(r"(?m)^depends=\((.*)\)", text)
        self.assertIsNotNone(depends)
        self.assertNotIn("python", depends.group(1))

    def test_pkgbuild_bash_syntax(self):
        for base in (self.BIN, self.GIT):
            result = subprocess.run(["bash", "-n", str(base / "PKGBUILD")],
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)


class DebBuildTest(unittest.TestCase):
    def _fake_tree(self, tmp):
        folder = pathlib.Path(tmp) / "DLEAPP"
        folder.mkdir()
        exe = folder / "dleapp"
        exe.write_bytes(b"#!/bin/sh\necho hi\n")
        exe.chmod(0o755)
        (folder / "lib.txt").write_text("x", encoding="utf-8")
        return folder

    def _ar_members(self, deb):
        # Minimal ar reader: magic + 60-byte headers, data padded to even size.
        with open(deb, "rb") as handle:
            self.assertEqual(handle.read(8), b"!<arch>\n")
            members = {}
            while True:
                header = handle.read(60)
                if not header:
                    break
                self.assertEqual(len(header), 60)
                name = header[:16].decode("ascii").strip()
                size = int(header[48:58].decode("ascii").strip())
                self.assertEqual(header[58:60], b"`\n")
                members[name] = handle.read(size)
                if size % 2:
                    handle.read(1)
        return members

    def test_deb_structure(self):
        with tempfile.TemporaryDirectory(prefix="dleapp-deb-test-") as tmp:
            folder = self._fake_tree(tmp)
            out = pathlib.Path(tmp) / "out"
            deb = pkg.build_deb(folder, out, version="2026.4.5", arch="amd64")
            self.assertEqual(deb.name, "dleapp_2026.4.5_amd64.deb")
            members = self._ar_members(deb)
            self.assertEqual(set(members), {"debian-binary", "control.tar.gz", "data.tar.gz"})
            self.assertEqual(members["debian-binary"], b"2.0\n")
            names = tarfile.open(fileobj=__import__("io").BytesIO(members["data.tar.gz"]),
                                 mode="r:gz").getnames()
            for want in ("opt/dleapp/dleapp", "usr/bin/dleapp",
                         "usr/share/applications/dleapp.desktop",
                         "usr/share/icons/hicolor/256x256/apps/dleapp.png",
                         "usr/share/pixmaps/dleapp.png",
                         "usr/share/doc/dleapp/copyright",
                         "usr/share/man/man1/dleapp.1.gz",
                         "opt", "usr/bin", "usr/share/doc/dleapp"):
                self.assertIn(want, names)
            dpkg_deb = shutil.which("dpkg-deb")
            if dpkg_deb is not None:
                info = subprocess.run([dpkg_deb, "-f", str(deb),
                                         "Package", "Version", "Architecture"],
                                      capture_output=True, text=True, check=False)
                self.assertEqual(info.returncode, 0, info.stderr)
                self.assertIn("Package: dleapp", info.stdout)
                self.assertIn("Version: 2026.4.5", info.stdout)
                self.assertIn("Architecture: amd64", info.stdout)

    def test_rpm_when_rpmbuild_present(self):
        if shutil.which("rpmbuild") is None:
            self.skipTest("rpmbuild not installed")
        with tempfile.TemporaryDirectory(prefix="dleapp-rpm-test-") as tmp:
            folder = self._fake_tree(tmp)
            out = pathlib.Path(tmp) / "out"
            rpm = pkg.build_rpm(folder, out, version="2026.4.5", arch="x86_64")
            self.assertTrue(rpm.name.startswith("dleapp-2026.4.5-"))
            self.assertTrue(rpm.name.endswith(".x86_64.rpm"))

    def test_missing_folder_fails(self):
        with tempfile.TemporaryDirectory(prefix="dleapp-missing-") as tmp:
            with self.assertRaises(SystemExit):
                pkg.build_deb(pathlib.Path(tmp) / "nope",
                              pathlib.Path(tmp) / "out", version="1", arch="amd64")


if __name__ == "__main__":
    unittest.main()
