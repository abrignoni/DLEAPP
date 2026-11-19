# DLEAPP RPM spec template, filled in by packaging/linux/build_linux_packages.py
# (single braces are the builder's placeholders; doubled braces are literal
# rpm macros). Wraps the frozen PyInstaller one-folder build in dist/DLEAPP/
# (python packaging/build.py exe) as /opt/dleapp with a /usr/bin/dleapp
# symlink, so the installed program needs no Python environment.
#
# Build with: python packaging/linux/build_linux_packages.py rpm
# (needs rpmbuild: sudo dnf install rpm-build, or sudo apt install rpm).

Name:           dleapp
Version:        {rpm_version}
Release:        {rpm_release}%{{?dist}}
Summary:        {summary}
License:        {license}
URL:            {homepage}
BuildArch:      {rpm_arch}
Requires:       glibc >= 2.35

%description
{description}

%install
rm -rf %{{buildroot}}
mkdir -p %{{buildroot}}/opt/dleapp %{{buildroot}}/usr/bin
cp -a "{folder}/." %{{buildroot}}/opt/dleapp/
ln -s /opt/dleapp/dleapp %{{buildroot}}/usr/bin/dleapp
mkdir -p %{{buildroot}}/usr/share/applications
install -m 644 "{desktop}" %{{buildroot}}/usr/share/applications/dleapp.desktop
mkdir -p %{{buildroot}}/usr/share/icons/hicolor/256x256/apps %{{buildroot}}/usr/share/pixmaps
install -m 644 "{icon}" %{{buildroot}}/usr/share/icons/hicolor/256x256/apps/dleapp.png
install -m 644 "{icon}" %{{buildroot}}/usr/share/pixmaps/dleapp.png
mkdir -p %{{buildroot}}/usr/share/doc/dleapp
install -m 644 "{copyright}" %{{buildroot}}/usr/share/doc/dleapp/copyright
mkdir -p %{{buildroot}}/usr/share/man/man1
gzip -n -c "{man}" > %{{buildroot}}/usr/share/man/man1/dleapp.1.gz
chmod 644 %{{buildroot}}/usr/share/man/man1/dleapp.1.gz

%files
/opt/dleapp/
/usr/bin/dleapp
/usr/share/applications/dleapp.desktop
/usr/share/icons/hicolor/256x256/apps/dleapp.png
/usr/share/pixmaps/dleapp.png
/usr/share/doc/dleapp/copyright
/usr/share/man/man1/dleapp.1.gz

%changelog
* Thu Nov 05 2026 DLEAPP Contributors <noreply@github.com> - {rpm_version}-{rpm_release}
- Wrap the frozen PyInstaller build as an RPM (see packaging/linux/).
