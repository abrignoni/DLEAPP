"""VLC 3 media player for Windows and Linux: the Qt interface settings file (Recent Media, the Open Network Stream
list, the last file dialog path) and the vlcrc options that decide what it records, for DLEAPP.

The settings file is written by Qt's QSettings. The reader below follows the QSettings INI rules of Qt 5.6.3
(qtbase e6f8b072d2bf15f8b82bede48ff29ce8ac8dbd9a, src/corelib/io/qsettings.cpp): readIniLine (1586-1647),
readIniFile (1654-1726), readIniSection (1728-1783), iniUnescapedKey (572-626), iniUnescapedStringList
(740-907), stringToVariant (488-541) and stringListToVariantList (368-388). A @Variant value is a QDataStream at
version Qt_4_0 (qsettings.cpp 456-476): a big-endian quint32 type id, and for QUrl (type 17) a QByteArray holding
the encoded URL (src/corelib/io/qurl.cpp 3908-3930, src/corelib/tools/qbytearray.cpp 2926-2949).

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "vlcRecentMedia": {
        "name": "VLC Recent Media",
        "description": "VLC 3 Recent Media list on Windows and Linux, one row per item of the Qt settings file in its "
                       "stored order, last started first, with the stored resume time; the file holds no clock time or "
                       "date for any item.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-18",
        "last_update_date": "2026-10-18",
        "requirements": "none",
        "category": "VLC",
        "notes": "VLC 3 keeps its Qt interface settings on Windows in %APPDATA%\\vlc\\vlc-qt-interface.ini, or in "
                 "<VLC folder>\\portable\\vlc\\vlc-qt-interface.ini when a portable folder sits beside vlc.exe, and on "
                 "Linux in ~/.config/vlc/vlc-qt-interface.conf, Qt's INI text under another name "
                 "(https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/modules/gui/qt/qt.cpp#L582-L598, "
                 "https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/src/win32/dirs.c#L257-L288, "
                 "https://github.com/qt/qtbase/blob/e6f8b072d2bf15f8b82bede48ff29ce8ac8dbd9a/src/corelib/io/qsettings.cpp#L938-L940 "
                 "and "
                 "https://github.com/qt/qtbase/blob/e6f8b072d2bf15f8b82bede48ff29ce8ac8dbd9a/src/corelib/io/qsettings.cpp#L1082-L1094). "
                 "The paths match either file name in any folder named vlc. The %APPDATA% and ~/.config layouts are "
                 "exercised on known data; the portable layout is source-verified only, and Snap and Flatpak "
                 "layouts were not checked. One row per item of [RecentsMRL] list. Rank 1 is the first item. When "
                 "playback of a top-level playlist item starts and VLC types the item as a file, which it does for "
                 "file, ftp, http, https, nfs, sftp, smb and upnp URIs, VLC puts it first, moving it there if it is "
                 "already listed, and keeps at most 30 "
                 "(https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/modules/gui/qt/input_manager.cpp#L118-L139, "
                 "https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/src/input/item.c#L1154-L1239, "
                 "https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/modules/gui/qt/recents.cpp#L101-L116, "
                 "https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/modules/gui/qt/recents.hpp#L36); "
                 "Open Folder adds the folder it is given, as a directory MRL, or as a dvd or bluray MRL when the "
                 "folder is VIDEO_TS or BDMV "
                 "(https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/modules/gui/qt/dialogs_provider.cpp#L596-L613). "
                 "Items VLC types otherwise, such as rtsp, rtp, rtmp, udp and mms streams, discs and capture "
                 "devices, are not added when they play, so their absence says nothing about whether they were "
                 "played. The file holds no time for any item, so a row shows the order items were last started, "
                 "not when, how often or for how long any was played. File Modified is the settings file's modified "
                 "time as the extraction recorded it, the same on every row of a file and not a time for any item; "
                 "on each known-data key it fell in the minute the recorded session ended with Media > Quit. Media "
                 "is the MRL decoded as VLC decodes its label in Open Recent Media: every %XX decoded and read as "
                 "UTF-8, and file:/// (Windows, .ini) or file:// (Linux, .conf) removed from the front "
                 "(https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/modules/gui/qt/menus.cpp#L1600-L1614); "
                 "a % not followed by two hex digits is left as stored. The menu's doubling of & and its limit of "
                 "ten entries are not applied here: every item is reported. MRL is the list item as Qt reads it "
                 "back: the quotes and backslash escapes QSettings adds when it writes are removed and nothing else "
                 "is changed "
                 "(https://github.com/qt/qtbase/blob/e6f8b072d2bf15f8b82bede48ff29ce8ac8dbd9a/src/corelib/io/qsettings.cpp#L628-L709 "
                 "and "
                 "https://github.com/qt/qtbase/blob/e6f8b072d2bf15f8b82bede48ff29ce8ac8dbd9a/src/corelib/io/qsettings.cpp#L740-L907). "
                 "The reader follows that Qt 5.6.3 code, the Qt the Windows builds of VLC 3.0.24 use "
                 "(https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/contrib/src/qt/rules.mak#L3); "
                 "the four Ubuntu files, written by the distribution's Qt 5, read correctly with the same rules. On "
                 "the known data the file name holding a comma and a semicolon was stored as a quoted item, which a "
                 "split on the comma breaks. Stored Time (ms) is the [RecentsMRL] times value at the same position, "
                 "as stored. When playback of an item ends, VLC takes the time reached if the position is between "
                 "5% and 95% and the media at least 60 s long, else -1 "
                 "(https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/modules/gui/qt/input_manager.cpp#L161-L171), "
                 "and stores it divided by 1000 in integer arithmetic "
                 "(https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/modules/gui/qt/recents.cpp#L176-L181), "
                 "so a time is in milliseconds and the -1 becomes 0. Resume Position is a time above 0 as H:MM:SS, "
                 "with .mmm added when it is not a whole second. VLC offers to resume a file item from such a time, "
                 "or resumes it, depending on its qt-continue option "
                 "(https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/modules/gui/qt/input_manager.cpp#L118-L129 "
                 "and "
                 "https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/modules/gui/qt/main_interface.cpp#L400-L414). "
                 "On the known data the files stopped at known points stored 128000 (Ubuntu) or 120000 (Windows), "
                 "60000 and 90000, the times each was taken to, and a file played to its end, a 30 s file and a "
                 "network stream that stopped stored 0. A 0 therefore does not tell those cases apart. -1, which "
                 "VLC writes when it adds an item "
                 "(https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/modules/gui/qt/recents.cpp#L108-L111), "
                 "and a missing times value, which VLC reads as -1 "
                 "(https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/modules/gui/qt/recents.cpp#L144-L150), "
                 "did not occur on the known data. Media > Open Recent Media > Clear empties list and times "
                 "(https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/modules/gui/qt/menus.cpp#L1627 "
                 "and "
                 "https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/modules/gui/qt/recents.cpp#L121-L130): "
                 "on the step2 keys the file held only the item played after the Clear. With Save recently played "
                 "items (qt-recentplay) off, VLC empties the list when it starts and adds nothing "
                 "(https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/modules/gui/qt/recents.cpp#L73-L87): "
                 "on the step3a_prefoff keys, saved just after it was turned off, the list still held its item; on "
                 "the step3 keys, after VLC was started again and a file played, list and times were @Invalid(), "
                 "Qt's form of an empty list "
                 "(https://github.com/qt/qtbase/blob/e6f8b072d2bf15f8b82bede48ff29ce8ac8dbd9a/src/corelib/io/qsettings.cpp#L719-L738), "
                 "and that file was not recorded. qt-recentplay-filter drops MRLs matching it when they are added "
                 "and when the list is loaded "
                 "(https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/modules/gui/qt/recents.cpp#L65-L71 "
                 "and "
                 "https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/modules/gui/qt/recents.cpp#L143-L150); "
                 "this is source-verified only. Both options are reported in VLC Recording Settings. A play VLC did "
                 "not record leaves no row, so an empty table is not evidence VLC was not used. On Windows VLC also "
                 "hands each file: item it adds (a local or UNC path) to the Windows SHAddToRecentDocs call "
                 "(https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/modules/gui/qt/recents.cpp#L89-L98) "
                 "for the Windows recent documents list; that was not checked on the known data. Stores in the same "
                 "folder: vlc-qt-interface is read here and in VLC Recording Settings, and its window geometry and "
                 "interface state keys and updatedate, the date of the last update check "
                 "(https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/modules/gui/qt/qt.cpp#L610-L624), "
                 "which no known data holds, are not reported; vlcrc gives two options to VLC Recording Settings; "
                 "ml.xspf is the Media Library playlist, not play history, and held no track on the Windows known "
                 "data, so it is not read; the crashdump folder was empty on the Windows known data and is not "
                 "read. VLC for macOS keeps recent items in org.videolan.vlc.plist, which this artifact does not "
                 "read, because no macOS known data exists yet; the VLC 4 media library is not read either. Known "
                 "data made 2026-10-18 with VLC 3.0.23 on Ubuntu 26.04 and VLC 3.0.24 on Windows 11 arm "
                 "(ubuntu2604_arm64_vlc_known_20261018_* and windows11_arm_vlc_known_20261018_*): every row on the "
                 "step1, step2 and step3a_prefoff keys equals the item and time the recorded steps give, and the "
                 "step3 keys give none. File Modified held one value on all rows of each key, which holds one "
                 "settings file. Prior research: Gabriele Zambelli, Forense nella Nebbia, 2019-01-27, documented "
                 "these keys and the millisecond times on VLC 3.0.5 and 3.0.6 "
                 "(https://forensenellanebbia.blogspot.com/2019/01/using-small-details-to-add-additional.html).",
        "paths": ('*/vlc/vlc-qt-interface.ini', '*/vlc/vlc-qt-interface.conf'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "movie",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_vlc_known_20261018_step1": "Ubuntu 26.04 LTS aarch64, VLC 3.0.23 | 6 rows",
            "ubuntu2604_arm64_vlc_known_20261018_step2": "Ubuntu 26.04 LTS aarch64, VLC 3.0.23 | 1 row",
            "ubuntu2604_arm64_vlc_known_20261018_step3": "Ubuntu 26.04 LTS aarch64, VLC 3.0.23 | 0 rows (list and times stored as @Invalid() after recent play was turned off)",
            "ubuntu2604_arm64_vlc_known_20261018_step3a_prefoff": "Ubuntu 26.04 LTS aarch64, VLC 3.0.23 | 1 row",
            "windows11_arm_known_20261001": "Windows 11 build 26200 ARM64 | 0 rows (no member matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step1": "Windows 11 build 26200 ARM64, VLC 3.0.24 | 6 rows",
            "windows11_arm_vlc_known_20261018_step2": "Windows 11 build 26200 ARM64, VLC 3.0.24 | 1 row",
            "windows11_arm_vlc_known_20261018_step3": "Windows 11 build 26200 ARM64, VLC 3.0.24 | 0 rows (list and times stored as @Invalid() after recent play was turned off)",
            "windows11_arm_vlc_known_20261018_step3a_prefoff": "Windows 11 build 26200 ARM64, VLC 3.0.24 | 1 row",
        },
    },
    "vlcSettings": {
        "name": "VLC Recording Settings",
        "description": "VLC 3 Open Network Stream URLs, last file dialog path and Recent Media item count from the "
                       "Qt settings file, and the vlcrc options that turn recent play off or filter it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-18",
        "last_update_date": "2026-10-18",
        "requirements": "none",
        "category": "VLC",
        "notes": "Rows from the VLC 3 Qt settings file (see VLC Recent Media for where it is) and from the vlcrc in "
                 "the same profile folder, %APPDATA%\\vlc\\vlcrc or <VLC folder>\\portable\\vlcrc on Windows and "
                 "~/.config/vlc/vlcrc on Linux "
                 "(https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/src/config/file.c#L59-L72, "
                 "https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/src/config/configuration.h#L59 "
                 "and "
                 "https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/src/win32/dirs.c#L257-L288). "
                 "The portable layout is source-verified only. RecentsMRL/list gives the number of Recent Media "
                 "items, with Stored As holding @Invalid() when the list is empty, so an emptied list still shows. "
                 "OpenDialog/netMRL gives one row per URL in the Open Network Stream list, Item being its position "
                 "as stored. VLC loads and saves that list only while qt-recentplay is on, de-duplicated and capped "
                 "at 10 by the box that shows it "
                 "(https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/modules/gui/qt/components/open_panels.cpp#L647-L654 "
                 "and "
                 "https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/modules/gui/qt/components/open_panels.cpp#L668-L684), "
                 "and Clear in Open Recent Media does not touch it: on the known data the URL typed in step 1 was "
                 "still there after the Clear and with recent play off. filedialog-path, in [General], is the last "
                 "path used in a VLC file dialog "
                 "(https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/modules/gui/qt/qt.hpp#L88), "
                 "a file or a folder "
                 "(https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/modules/gui/qt/dialogs_provider.cpp#L418, "
                 "https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/modules/gui/qt/dialogs_provider.cpp#L513 "
                 "and "
                 "https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/modules/gui/qt/dialogs_provider.cpp#L594). "
                 "VLC writes it when it exits with qt-recentplay on and removes it when it exits with it off "
                 "(https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/modules/gui/qt/qt.cpp#L720-L724): "
                 "on the known data it held the last file opened on the step1 and step2 keys and was absent on the "
                 "step3a_prefoff and step3 keys. It is stored as a Qt data stream "
                 "(https://github.com/qt/qtbase/blob/e6f8b072d2bf15f8b82bede48ff29ce8ac8dbd9a/src/corelib/io/qsettings.cpp#L456-L476): "
                 "Value is the URL it holds (type 17, a byte array: "
                 "https://github.com/qt/qtbase/blob/e6f8b072d2bf15f8b82bede48ff29ce8ac8dbd9a/src/corelib/io/qurl.cpp#L3908-L3930 "
                 "and "
                 "https://github.com/qt/qtbase/blob/e6f8b072d2bf15f8b82bede48ff29ce8ac8dbd9a/src/corelib/tools/qbytearray.cpp#L2926-L2949), "
                 "Decoded Path that URL decoded as VLC Recent Media decodes Media, and Stored As the text as the "
                 "file holds it. Decoded Path is blank on every other row, and held no value on any row of the "
                 "step3a_prefoff and step3 keys. vlcrc qt-recentplay (Save recently played items) and "
                 "qt-recentplay-filter decide what the settings file records "
                 "(https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/modules/gui/qt/recents.cpp#L65-L87). "
                 "VLC writes the saveable options of every loaded module to vlcrc and comments out one equal to its "
                 "default "
                 "(https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/src/config/file.c#L302-L313 "
                 "and "
                 "https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/src/config/file.c#L440-L476), "
                 "and skips commented lines when it reads the file "
                 "(https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/src/config/file.c#L191-L243); "
                 "the defaults are 1 and empty "
                 "(https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/modules/gui/qt/qt.cpp#L257-L260). "
                 "Value is the value in effect from this file: the stored value when set, the default when "
                 "commented out; Stored As is the line. Options given on the command line override vlcrc "
                 "(https://github.com/videolan/vlc/blob/6de05adcbaf2e8b85fe86aad4169393098628119/src/libvlc.c#L150-L162) "
                 "and leave no trace here. A missing vlcrc gives no rows; VLC then uses the defaults. Other vlcrc "
                 "options and the settings file's geometry, interface state and updatedate keys are not reported. "
                 "File Modified is each file's modified time as the extraction recorded it, not a time for any "
                 "value; on the step1 keys the settings file and vlcrc shared one, so File Modified held one value "
                 "on all 5 rows. Known data made 2026-10-18 with VLC 3.0.23 on Ubuntu 26.04 and VLC 3.0.24 on "
                 "Windows 11 arm: every row on the eight keys equals the recorded steps, qt-recentplay commented "
                 "out (default 1) on the step1 and step2 keys and 0 on the step3a_prefoff and step3 keys, "
                 "qt-recentplay-filter commented out on all eight.",
        "paths": ('*/vlc/vlc-qt-interface.ini', '*/vlc/vlc-qt-interface.conf', '*/vlc/vlcrc',
                  '*/portable/vlcrc'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "settings",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_vlc_known_20261018_step1": "Ubuntu 26.04 LTS aarch64, VLC 3.0.23 | 5 rows",
            "ubuntu2604_arm64_vlc_known_20261018_step2": "Ubuntu 26.04 LTS aarch64, VLC 3.0.23 | 5 rows",
            "ubuntu2604_arm64_vlc_known_20261018_step3": "Ubuntu 26.04 LTS aarch64, VLC 3.0.23 | 4 rows",
            "ubuntu2604_arm64_vlc_known_20261018_step3a_prefoff": "Ubuntu 26.04 LTS aarch64, VLC 3.0.23 | 4 rows",
            "windows11_arm_known_20261001": "Windows 11 build 26200 ARM64 | 0 rows (no member matches the declared paths)",
            "windows11_arm_vlc_known_20261018_step1": "Windows 11 build 26200 ARM64, VLC 3.0.24 | 5 rows",
            "windows11_arm_vlc_known_20261018_step2": "Windows 11 build 26200 ARM64, VLC 3.0.24 | 5 rows",
            "windows11_arm_vlc_known_20261018_step3": "Windows 11 build 26200 ARM64, VLC 3.0.24 | 4 rows",
            "windows11_arm_vlc_known_20261018_step3a_prefoff": "Windows 11 build 26200 ARM64, VLC 3.0.24 | 4 rows",
        },
    },
}

import os
import re
import struct

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.linux_links import recorded_time, seeker_of

_SPECIAL = frozenset(b'\n\r";=\\')
_SPACE = frozenset(b' \t\n\r')
_ESCAPES = {ord('a'): '\a', ord('b'): '\b', ord('f'): '\f', ord('n'): '\n', ord('r'): '\r', ord('t'): '\t',
            ord('v'): '\v', ord('"'): '"', ord('?'): '?', ord("'"): "'", ord('\\'): '\\'}
_HEX = frozenset(b'0123456789abcdefABCDEF')
_QURL = 17


def _ini_lines(data, pos):
    """(start, length, equals) for each logical line, as QConfFileSettingsPrivate::readIniLine splits them: a
    comment line starting with ';' is joined to nothing, a ';' or line end outside quotes ends a line, and a
    backslash escapes the next byte (so a backslash before a line end continues the line)."""
    end = len(data)
    while True:
        start = pos
        while start < end and data[start] in _SPACE:
            start += 1
        i, in_quotes, equals = start, False, -1
        while i < end:
            if data[i] not in _SPECIAL:
                i += 1
                continue
            ch = data[i]
            i += 1
            if ch == 0x3d:  # '='
                if not in_quotes and equals == -1:
                    equals = i - 1
            elif ch in (0x0a, 0x0d):
                if i == start + 1:
                    start += 1
                elif not in_quotes:
                    i -= 1
                    break
            elif ch == 0x5c:  # backslash
                if i < end:
                    first = data[i]
                    i += 1
                    if i < end and ((first == 0x0a and data[i] == 0x0d) or (first == 0x0d and data[i] == 0x0a)):
                        i += 1
            elif ch == 0x22:  # '"'
                in_quotes = not in_quotes
            else:  # ';'
                if i == start + 1:
                    while i < end and data[i] not in (0x0a, 0x0d):
                        i += 1
                    start = i
                elif not in_quotes:
                    i -= 1
                    break
        pos = i
        if i - start <= 0:
            return
        yield start, i - start, equals


def _unescape_key(raw):
    """QSettingsPrivate::iniUnescapedKey: a backslash is '/', %XX and %UXXXX are characters."""
    out, i, end = [], 0, len(raw)
    while i < end:
        ch = raw[i]
        if ch == 0x5c:
            out.append('/')
            i += 1
            continue
        if ch != 0x25 or i == end - 1:
            out.append(chr(ch))
            i += 1
            continue
        first, digits = i + 1, 2
        if raw[i + 1] == ord('U'):
            first, digits = i + 2, 4
        text = raw[first:first + digits]
        if first + digits > end or not all(c in _HEX for c in text):
            out.append('%')
            i += 1
            continue
        out.append(chr(int(text, 16)))
        i = first + digits
    return ''.join(out)


def _text(units):
    """A string from QChar values, joining UTF-16 surrogate pairs as Qt's QString does."""
    return ''.join(units).encode('utf-16-le', 'surrogatepass').decode('utf-16-le', 'replace')


def _chop(units, limit):
    while len(units) > limit and units[-1] in (' ', '\t'):
        units.pop()


def _unescape_value(data, start, end, utf8):
    """QSettingsPrivate::iniUnescapedStringList: (True, [items]) for a comma-separated list, else (False, text).
    Quotes group a value, backslash escapes are C-style with \\x taking every hex digit that follows, and bytes
    are Latin-1 unless the file starts with a UTF-8 byte order mark."""
    units, items, in_quotes, quoted, chop_final = [], None, False, False, True
    i = start
    while i < end and data[i] in (0x20, 0x09):
        i += 1
    chop = 0
    while i < end:
        ch = data[i]
        if ch == 0x5c:
            i += 1
            if i >= end:
                chop_final = False
                break
            code = data[i]
            i += 1
            if code in _ESCAPES:
                units.append(_ESCAPES[code])
                chop = len(units)
                continue
            if code == ord('x'):
                if i >= end:
                    chop_final = False
                    break
                if data[i] in _HEX:
                    value = 0
                    while i < end and data[i] in _HEX:
                        value = (value << 4) + int(chr(data[i]), 16)
                        i += 1
                    units.append(chr(value & 0xffff))
                    if i >= end:
                        chop_final = False
                        break
                    chop = len(units)
                    continue
            elif ord('0') <= code <= ord('7'):
                value = code - ord('0')
                while i < end and ord('0') <= data[i] <= ord('7'):
                    value = (value << 3) + data[i] - ord('0')
                    i += 1
                units.append(chr(value & 0xffff))
                if i >= end:
                    chop_final = False
                    break
                chop = len(units)
                continue
            elif code in (0x0a, 0x0d):
                if i < end and data[i] in (0x0a, 0x0d) and data[i] != code:
                    i += 1
            chop = len(units)
            continue
        if ch == 0x22:
            i += 1
            quoted = True
            in_quotes = not in_quotes
            if not in_quotes:
                while i < end and data[i] in (0x20, 0x09):
                    i += 1
                chop = len(units)
            continue
        if ch == 0x2c and not in_quotes:
            if not quoted:
                _chop(units, chop)
            if items is None:
                items = []
            items.append(_text(units))
            units, quoted = [], False
            i += 1
            while i < end and data[i] in (0x20, 0x09):
                i += 1
            chop = 0
            continue
        j = i + 1
        while j < end and data[j] not in (0x5c, 0x22, 0x2c):
            j += 1
        chunk = data[i:j]
        units.extend(chunk.decode('utf-8', 'replace') if utf8 else chunk.decode('latin-1'))
        i = j
    if chop_final and not quoted:
        _chop(units, chop)
    if items is not None:
        items.append(_text(units))
        return True, items
    return False, _text(units)


def read_qsettings(data):
    """{key: (stored text, value)} for a QSettings INI file, keys as Qt names them ('RecentsMRL/list', and
    'filedialog-path' for a key of [General]); a key stored twice keeps its last value, as Qt's map does.
    value is a list of strings for a list, None for @Invalid(), bytes for @ByteArray(), ('variant', bytes) or
    ('datetime', bytes) for a QDataStream value, and the string otherwise."""
    utf8 = data[:3] == b'\xef\xbb\xbf'
    pos = 3 if utf8 else 0
    section, settings = '', {}
    for start, length, equals in _ini_lines(data, pos):
        line_end = start + length
        if data[start] == 0x5b:  # '['
            close = data.find(b']', start)
            raw = data[start + 1:line_end] if close == -1 or close >= line_end else data[start + 1:close]
            raw = raw.strip()
            lowered = raw.lower()
            if lowered == b'general':
                section = ''
            elif lowered == b'%general':
                section = raw[1:].decode('latin-1') + '/'
            else:
                section = _unescape_key(raw) + '/'
            continue
        if equals == -1:
            continue
        key_end = equals
        while key_end > start and data[key_end - 1] in (0x20, 0x09):
            key_end -= 1
        key = section + _unescape_key(data[start:key_end])
        is_list, value = _unescape_value(data, equals + 1, line_end, utf8)
        stored = data[equals + 1:line_end].strip(b' \t').decode('utf-8' if utf8 else 'latin-1', 'replace')
        settings[key] = (stored, _list_value(value) if is_list else _variant(value))
    return settings


def _variant(text):
    """QSettingsPrivate::stringToVariant for the forms this module reads."""
    if text.startswith('@') and text.endswith(')'):
        if text.startswith('@ByteArray('):
            return text[11:-1].encode('latin-1', 'replace')
        if text.startswith('@String('):
            return text[8:-1]
        if text.startswith('@Variant('):
            return ('variant', text[9:-1].encode('latin-1', 'replace'))
        if text.startswith('@DateTime('):
            return ('datetime', text[10:-1].encode('latin-1', 'replace'))
        if text == '@Invalid()':
            return None
    if text.startswith('@@'):
        return text[1:]
    return text


def _list_value(items):
    """QSettingsPrivate::stringListToVariantList: '@@' loses one '@'; an item that is another '@' form makes
    every item go through stringToVariant."""
    if any(item.startswith('@') and not item.startswith('@@') for item in items):
        return [_variant(item) for item in items]
    return [item[1:] if item.startswith('@@') else item for item in items]


def string_list(value):
    """QVariant::toStringList for a value read_qsettings returned: a list keeps its string items, @Invalid() is an
    empty list and a single string is a list of one."""
    if value is None:
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    if isinstance(value, str):
        return [value]
    return []


def qurl_text(value):
    """The URL a @Variant(QUrl) value holds, or None when the value is not one."""
    if not (isinstance(value, tuple) and value[0] == 'variant'):
        return None
    raw = value[1]
    if len(raw) < 8 or struct.unpack_from('>I', raw, 0)[0] != _QURL:
        return None
    size = struct.unpack_from('>I', raw, 4)[0]
    if size == 0xffffffff:
        return ''
    return raw[8:8 + size].decode('latin-1')


_PERCENT = re.compile(rb'%([0-9A-Fa-f]{2})')


def media_text(mrl, windows):
    """The MRL as VLC's Open Recent Media menu labels it (modules/gui/qt/menus.cpp 1602-1614 at VLC 3.0.24): every
    %XX decoded, read as UTF-8, and file:/// (Windows) or file:// (elsewhere) removed from the front. A % not
    followed by two hex digits is left as stored."""
    decoded = _PERCENT.sub(lambda m: bytes([int(m.group(1), 16)]), mrl.encode('utf-8', 'surrogatepass'))
    text = decoded.decode('utf-8', 'replace')
    scheme = 'file:///' if windows else 'file://'
    return text[len(scheme):] if text.startswith(scheme) else text


def resume_position(stored):
    """(H:MM:SS, note) for one stored [RecentsMRL] times value, in milliseconds."""
    if stored is None:
        return '', 'no value at this position in times; VLC reads a missing value as -1'
    value = stored.strip()
    if not re.fullmatch(r'-?\d+', value):
        return '', 'not a whole number; reported as stored'
    number = int(value)
    if number > 0:
        seconds, millis = divmod(number, 1000)
        hours, rest = divmod(seconds, 3600)
        text = f'{hours}:{rest // 60:02d}:{rest % 60:02d}' + (f'.{millis:03d}' if millis else '')
        return text, 'time saved when playback of the item ended'
    if number == 0:
        return '', 'no position saved: 0 is what VLC stores when playback ends with no position kept'
    if number == -1:
        return '', 'no time stored yet: VLC writes -1 when it adds an item'
    return '', 'negative value other than -1; reported as stored'


def _source(context, seeker, path):
    info = getattr(seeker, 'file_infos', {}).get(path)
    return info.source_path if info is not None else context.get_relative_path(path).replace(os.sep, '/')


def _files(context, names):
    for path in sorted(str(p) for p in context.get_files_found()):
        if os.path.basename(path) in names and os.path.isfile(path):
            yield path


def _read(path):
    try:
        with open(path, 'rb') as handle:
            return handle.read()
    except OSError:
        logfunc(f'VLC: could not read {os.path.basename(path)}')
        return None


@artifact_processor
def vlcRecentMedia(context):
    data_headers = (('File Modified', 'datetime'), 'Rank', 'Media', 'Resume Position', 'Stored Time (ms)',
                    'Resume Note', 'MRL', 'Source File')
    seeker = seeker_of(context)
    data_list, read = [], []
    for path in _files(context, ('vlc-qt-interface.ini', 'vlc-qt-interface.conf')):
        data = _read(path)
        if data is None:
            continue
        read.append(path)
        settings = read_qsettings(data)
        windows = path.endswith('.ini')
        when = recorded_time(seeker, path, None)
        source = _source(context, seeker, path)
        mrls = string_list(settings.get('RecentsMRL/list', ('', None))[1])
        times = string_list(settings.get('RecentsMRL/times', ('', None))[1])
        if len(times) != len(mrls):
            logfunc(f'VLC Recent Media: {len(mrls)} items and {len(times)} times in {source}')
        for rank, mrl in enumerate(mrls, 1):
            stored = times[rank - 1] if rank <= len(times) else None
            position, note = resume_position(stored)
            data_list.append((when, rank, media_text(mrl, windows), position, stored if stored is not None else '',
                              note, mrl, source))
    return data_headers, data_list, '\n'.join(read)


def _vlcrc_options(data):
    """{option: (value, stored line)} for qt-recentplay and qt-recentplay-filter in a vlcrc file. An uncommented
    line wins over a commented one, and a later line over an earlier one, as config_LoadConfigFile reads them."""
    found = {}
    text = data[3:] if data[:3] == b'\xef\xbb\xbf' else data
    for line in text.decode('utf-8', 'replace').split('\n'):
        line = line.rstrip('\r')
        commented = line.startswith('#')
        name, sep, value = (line[1:] if commented else line).partition('=')
        if not sep or name not in ('qt-recentplay', 'qt-recentplay-filter'):
            continue
        if commented and name in found and not found[name][2]:
            continue
        found[name] = (value, line, commented)
    return found


_DEFAULTS = {'qt-recentplay': '1', 'qt-recentplay-filter': ''}


def _vlcrc_rows(when, data, source):
    rows = []
    for name, (value, line, commented) in sorted(_vlcrc_options(data).items()):
        if commented:
            effective = _DEFAULTS[name]
            note = (f'commented out: VLC writes an option commented when it equals its default, so the default '
                    f'({effective or "empty"}) applies when VLC reads this file')
        elif name == 'qt-recentplay':
            effective = value
            note = ('set: recent play off, so VLC empties Recent Media at its next start and adds nothing'
                    if value.strip() == '0' else 'set')
        else:
            effective = value
            note = ('set: MRLs matching this regular expression, without regard to case, are not added and are '
                    'dropped when VLC loads the list' if value else 'set to empty: no filter')
        rows.append((when, f'vlcrc {name}', '', effective, '', line, note, source))
    return rows


@artifact_processor
def vlcSettings(context):
    data_headers = (('File Modified', 'datetime'), 'Setting', 'Item', 'Value', 'Decoded Path', 'Stored As', 'Note',
                    'Source File')
    seeker = seeker_of(context)
    data_list, read = [], []
    for path in _files(context, ('vlc-qt-interface.ini', 'vlc-qt-interface.conf', 'vlcrc')):
        data = _read(path)
        if data is None:
            continue
        read.append(path)
        when = recorded_time(seeker, path, None)
        source = _source(context, seeker, path)
        if os.path.basename(path) == 'vlcrc':
            data_list.extend(_vlcrc_rows(when, data, source))
            continue
        windows = path.endswith('.ini')
        settings = read_qsettings(data)
        if 'RecentsMRL/list' in settings:
            stored, value = settings['RecentsMRL/list']
            count = len(string_list(value))
            data_list.append((when, 'RecentsMRL/list', '', f'{count} item' + ('' if count == 1 else 's'), '',
                              stored if value is None else '', 'number of items in VLC Recent Media', source))
        if 'OpenDialog/netMRL' in settings:
            stored, value = settings['OpenDialog/netMRL']
            for number, url in enumerate(string_list(value), 1):
                data_list.append((when, 'OpenDialog/netMRL', number, url, '', stored,
                                  'URL in the Open Network Stream list', source))
        if 'filedialog-path' in settings:
            stored, value = settings['filedialog-path']
            url = qurl_text(value)
            if url is None:
                data_list.append((when, 'filedialog-path', '', '', '', stored,
                                  'not a QUrl value; reported as stored', source))
            else:
                data_list.append((when, 'filedialog-path', '', url, media_text(url, windows), stored,
                                  'last path used in a VLC file dialog', source))
    return data_headers, data_list, '\n'.join(read)
