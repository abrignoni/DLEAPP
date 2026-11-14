#!/usr/bin/env bash
# DLEAPP one-line installer: native package when there is one, AppImage otherwise.
#
#   curl -fsSL https://raw.githubusercontent.com/abrignoni/DLEAPP/main/install.sh | bash
#
# Pins nothing: it asks the GitHub API for the latest release, verifies the
# download against that release's SHA256SUMS.txt, and installs it, so a fresh
# run always installs the latest version. Re-running it upgrades.
#
# What it installs, by platform:
#   Debian/Ubuntu and derivatives -> the release .deb (dpkg)
#   Fedora/RHEL/Rocky/Alma/openSUSE -> the release .rpm
#   Arch/CachyOS/EndeavourOS       -> dleapp-bin from the AUR (needs an AUR helper)
#   anything else with Linux       -> the release AppImage into ~/.local/bin
#   macOS                          -> the release .dmg (download + hdiutil, no App Store)
#
# Options (as VAR=val environment, since it is piped into bash):
#   TAG=v2026.4.5      install that release instead of the latest
#   METHOD=deb|rpm|appimage|aur|dmg
#                      force one method (default: detected)
#   PREFIX=~/.local/bin
#                      where the AppImage and its symlink go (default)
#   NO_SUDO=1          never call sudo (fails if root is needed instead)
#
set -euo pipefail

REPO="abrignoni/DLEAPP"
PROG="dleapp"
: "${PREFIX:=$HOME/.local/bin}"

die() { echo "install.sh: $*" >&2; exit 1; }
say() { echo "install.sh: $*"; }
have() { command -v "$1" >/dev/null 2>&1; }

SUDO=""
if [ "$(id -u)" -ne 0 ] && [ "${NO_SUDO:-0}" != "1" ]; then
  have sudo || die "need root and sudo is not installed; re-run as root"
  SUDO="sudo"
fi

TAG="${TAG:-}"
if [ -z "$TAG" ]; then
  say "finding the latest release of $REPO ..."
  API="$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest")" \
    || die "could not reach the GitHub API (network? rate limit?)"
  TAG="$(printf '%s' "$API" | grep -m1 '"tag_name"' | sed -E 's/.*"tag_name": *"([^"]+)".*/\1/')"
  [ -n "$TAG" ] || die "could not read tag_name from the GitHub API response"
fi
VER="${TAG#v}"
say "release: $TAG"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cd "$TMP"

say "fetching SHA256SUMS.txt ..."
curl -fsSL -o SHA256SUMS.txt "https://github.com/$REPO/releases/download/$TAG/SHA256SUMS.txt"

check() { # check <file>: verify against SHA256SUMS.txt
  grep -F "  $1" SHA256SUMS.txt | sha256sum -c - \
    || die "checksum mismatch for $1 (aborting; see SHA256SUMS.txt)"
}

ARCH="$(uname -m)"
case "$ARCH" in
  x86_64|amd64) FARCH="x64"; DEBARCH="amd64"; RPMARCH="x86_64" ;;
  aarch64|arm64) FARCH="arm64"; DEBARCH="arm64"; RPMARCH="aarch64" ;;
  *) die "unsupported architecture: $ARCH" ;;
esac

# --- method detection ---------------------------------------------------------
METHOD="${METHOD:-}"
if [ -z "$METHOD" ]; then
  if [ -f /etc/os-release ]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    case "${ID:-} ${ID_LIKE:-}" in
      *arch*|*cachyos*|*endeavouros*|*manjaro*) METHOD="aur" ;;
      *debian*|*ubuntu*|*linuxmint*|*pop*|*kali*|*raspbian*) METHOD="deb" ;;
      *fedora*|*rhel*|*centos*|*rocky*|*alma*|*suse*|*opensuse*) METHOD="rpm" ;;
      *) METHOD="appimage" ;;
    esac
  elif [ "$(uname -s)" = "Darwin" ]; then
    METHOD="dmg"
  else
    METHOD="appimage"
  fi
fi
say "method: $METHOD"
case "$METHOD" in
  deb|rpm|aur|appimage|dmg) ;;
  *) die "unknown METHOD=$METHOD (want deb|rpm|aur|appimage|dmg)" ;;
esac

install_deb() {
  local deb="DLEAPP-${VER}-linux-${FARCH}.deb"
  say "downloading $deb ..."
  curl -fsSL -o "$deb" "https://github.com/$REPO/releases/download/$TAG/$deb" \
    || die "no .deb in release $TAG (older release? set TAG=... or METHOD=appimage)"
  check "$deb"
  say "installing with dpkg (apt fixes dependencies) ..."
  # shellcheck disable=SC2086
  if ! $SUDO dpkg -i "$deb"; then
    $SUDO apt-get install -y -f || die "dpkg failed even after apt-get install -f"
  fi
}

install_rpm() {
  local rpm="DLEAPP-${VER}-linux-${FARCH}.rpm"
  say "downloading $rpm ..."
  curl -fsSL -o "$rpm" "https://github.com/$REPO/releases/download/$TAG/$rpm" \
    || die "no .rpm in release $TAG (older release? set TAG=... or METHOD=appimage)"
  check "$rpm"
  say "installing ..."
  if have dnf; then
    # shellcheck disable=SC2086
    $SUDO dnf install -y "./$rpm"
  elif have zypper; then
    # shellcheck disable=SC2086
    $SUDO zypper --no-confirm install "./$rpm"
  else
    # shellcheck disable=SC2086
    $SUDO rpm -U --force "./$rpm"
  fi
}

install_aur() {
  local helper=""
  for h in paru yay trizen pikaur; do
    if have "$h"; then helper="$h"; break; fi
  done
  [ -n "$helper" ] || die "no AUR helper found (install paru or yay first), or METHOD=appimage for a manual install"
  say "installing dleapp-bin with $helper (always the latest release) ..."
  # shellcheck disable=SC2086
  $helper -S --needed dleapp-bin
  say "tip: 'dleapp-git' tracks the latest commit instead (rebuilds on --devel upgrades)"
}

install_appimage() {
  local img="DLEAPP-${VER}-linux-${FARCH}.AppImage"
  say "downloading $img ..."
  curl -fsSL -o "$img" "https://github.com/$REPO/releases/download/$TAG/$img"
  check "$img"
  chmod +x "$img"
  mkdir -p "$PREFIX"
  cp "$img" "$PREFIX/$img"
  ln -sf "$img" "$PREFIX/$PROG"
  say "installed to $PREFIX/$img (symlinked as $PREFIX/$PROG)"
  case ":$PATH:" in
    *":$PREFIX:"*) ;;
    *) say "note: $PREFIX is not on your PATH; add: export PATH=\"\$PREFIX:\$PATH\"" ;;
  esac
}

install_dmg() {
  local dmg
  case "$ARCH" in
    x86_64|amd64) dmg="DLEAPP-${VER}-macos-x64.dmg" ;;
    *) dmg="DLEAPP-${VER}-macos-arm64.dmg" ;;
  esac
  say "downloading $dmg ..."
  curl -fsSL -o "$dmg" "https://github.com/$REPO/releases/download/$TAG/$dmg"
  check "$dmg"
  say "installing DLEAPP.app to /Applications (needs sudo) ..."
  # shellcheck disable=SC2086
  $SUDO hdiutil attach -nobrowse -mountpoint /tmp/dleapp-mnt "$dmg"
  trap '$SUDO hdiutil detach /tmp/dleapp-mnt 2>/dev/null; rm -rf "$TMP"' EXIT
  $SUDO cp -R /tmp/dleapp-mnt/DLEAPP.app /Applications/
  $SUDO hdiutil detach /tmp/dleapp-mnt
  trap 'rm -rf "$TMP"' EXIT
  say "installed. CLI: /Applications/DLEAPP.app/Contents/MacOS/dleapp --help"
}

case "$METHOD" in
  deb) install_deb ;;
  rpm) install_rpm ;;
  aur) install_aur ;;
  appimage) install_appimage ;;
  dmg) install_dmg ;;
  *) die "unknown METHOD=$METHOD (want deb|rpm|aur|appimage|dmg)" ;;
esac

if [ "$METHOD" != "aur" ] && [ "$METHOD" != "dmg" ]; then
  if have "$PROG"; then
    say "installed: $("$PROG" --version 2>/dev/null || echo "$PROG on PATH")"
  else
    say "installed, but $PROG is not on PATH yet (open a new shell)"
  fi
fi
say "done."
