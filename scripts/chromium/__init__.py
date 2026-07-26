"""Readers for the on-disk formats used by Chromium-based desktop apps.

Electron applications (Discord, Slack, Signal Desktop, Wire, ...) store their
web-layer data in the same formats a Chrome profile uses. The modules here
parse those container formats so that per-application artifacts only have to
deal with the application's own data.
"""
