"""Installed RPM packages from the RPM database (RHEL-family), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxRpmPackages": {
        "name": "RPM Installed Packages",
        "description": "Packages installed on a Fedora or other RPM-family system, read from the RPM database "
                       "(rpmdb.sqlite): one row per package, with its install and build times, name, version, "
                       "architecture, vendor, size, licence, group and source package.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-13",
        "last_update_date": "2026-10-13",
        "requirements": "none",
        "category": "Installed Software (Linux)",
        "notes": "Reads the RPM database rpmdb.sqlite (RPM 4.16 added a SQLite backend for the package database and "
                 "Fedora uses it from Fedora 33; Fedora 36 and later keep the file at usr/lib/sysimage/rpm and "
                 "earlier Fedora kept it at var/lib/rpm, and the search pattern matches either) and reports one row "
                 "per installed package from the headers in its Packages table. Each Packages row holds one RPM "
                 "header blob, whose layout is eight bytes giving the index-entry count and the data-store size, then "
                 "that many sixteen-byte index entries (tag, type, data-store offset and count), then the data store "
                 "(RPM header format, Reference: rpm 6.0.2, 'lib/header.cc', "
                 "https://github.com/rpm-software-management/rpm/blob/rpm-6.0.2-release/lib/header.cc). "
                 "Install Time (UTC) is the INSTALLTIME tag read as Unix seconds (the time rpm recorded the package "
                 "as installed) and leads the row; Build Time (UTC) is BUILDTIME. Package is the NEVRA built from "
                 "the NAME, EPOCH (shown only when not zero), VERSION, RELEASE and ARCH tags (the trailing .arch is "
                 "omitted when a header carries no ARCH tag, as a gpg-pubkey key package does). Vendor, Size (bytes), "
                 "License, Group, Source RPM and Summary are the VENDOR, SIZE, LICENSE, GROUP, SOURCERPM and SUMMARY "
                 "tags; Size is taken from the newer LONGSIZE tag instead when a package records its size only there, "
                 "as a package built in the rpm v6 format does (tested with constructed input; every package in the "
                 "known data carries SIZE). A header that cannot be parsed, or that has no NAME tag, is skipped and "
                 "the count is written to the run log. A row records that the package is present in the database, "
                 "with the time rpm stored; it is not an application run. "
                 "Validated on fedora44_arm64_dnf_known (Fedora Linux 44 Server, rpm 6.0.2), where the database "
                 "holds 1639 installed packages, all with an install time on 12 August 2026 (the image build). "
                 "Vendor was Fedora Project on 1638 and blank on 1 (the gpg-pubkey key package, which carries no "
                 "vendor). This is the RPM-family counterpart of the Debian dpkg package artifacts. The DNF5 "
                 "transaction history is reported separately. Reading the database needs no extra package.",
        "paths": ("*/rpm/rpmdb.sqlite*",),
        "output_types": "standard",
        "artifact_icon": "package",
        "sample_data": {
            "fedora44_arm64_dnf_known": "Fedora Linux 44 Server (aarch64), rpm 6.0.2 | 1639 rows",
        },
    },
}

import os
import struct
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly

_LABEL = 'RPM Installed Packages'
# RPM header tags read here (rpmtag.h): the value types are string (6), string-array (8), i18n string (9),
# int16 (3), int32 (4) and int64 (5); an i18n or string-array value is taken as its first string. LONGSIZE is
# the int64 size a package built in the rpm v6 format records in place of the int32 SIZE.
_TAGS = {1000: 'NAME', 1001: 'VERSION', 1002: 'RELEASE', 1003: 'EPOCH', 1004: 'SUMMARY', 1006: 'BUILDTIME',
         1008: 'INSTALLTIME', 1009: 'SIZE', 1011: 'VENDOR', 1014: 'LICENSE', 1016: 'GROUP', 1022: 'ARCH',
         1044: 'SOURCERPM', 5009: 'LONGSIZE'}


def parse_header(blob):
    """The RPM tags of interest from one header blob, as a dict; {} when the blob is too short to parse."""
    if not isinstance(blob, (bytes, bytearray)) or len(blob) < 8:
        return {}
    blob = bytes(blob)
    nindex, hsize = struct.unpack('>II', blob[:8])
    index_end = 8 + nindex * 16
    store = blob[index_end:index_end + hsize]
    if len(blob) < index_end or len(store) < hsize:
        return {}
    out = {}
    for i in range(nindex):
        tag, vtype, offset, _count = struct.unpack('>IIII', blob[8 + i * 16:8 + i * 16 + 16])
        name = _TAGS.get(tag)
        if name is None or offset < 0 or offset > len(store):
            continue
        if vtype in (6, 8, 9):  # STRING, STRING_ARRAY, I18NSTRING: first null-terminated string
            end = store.find(b'\x00', offset)
            out[name] = store[offset:end if end >= 0 else len(store)].decode('utf-8', 'replace')
        elif vtype == 5 and offset + 8 <= len(store):  # INT64
            out[name] = struct.unpack('>Q', store[offset:offset + 8])[0]
        elif vtype == 4 and offset + 4 <= len(store):  # INT32
            out[name] = struct.unpack('>I', store[offset:offset + 4])[0]
        elif vtype == 3 and offset + 2 <= len(store):  # INT16
            out[name] = struct.unpack('>H', store[offset:offset + 2])[0]
    return out


def _unix_utc(seconds):
    """Unix seconds as an aware UTC datetime; '' for 0 or anything not a number."""
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or seconds == 0:
        return ''
    try:
        return datetime.fromtimestamp(seconds, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


def _nevra(h):
    name = h.get('NAME', '')
    epoch = h.get('EPOCH')
    epoch_part = f'{epoch}:' if isinstance(epoch, int) and epoch else ''
    arch = h.get('ARCH', '')
    arch_part = f'.{arch}' if arch else ''  # a gpg-pubkey header carries no ARCH
    return f"{name}-{epoch_part}{h.get('VERSION', '')}-{h.get('RELEASE', '')}{arch_part}"


@artifact_processor
def linuxRpmPackages(context):
    data_headers = (('Install Time (UTC)', 'datetime'), ('Build Time (UTC)', 'datetime'), 'Package', 'Vendor',
                    'Size (bytes)', 'License', 'Group', 'Source RPM', 'Summary', 'Source File')
    data_list = []
    read = []
    for path in [str(p) for p in context.get_files_found() if os.path.basename(str(p)) == 'rpmdb.sqlite']:
        relative = context.get_relative_path(path)
        database = open_sqlite_db_readonly(path)
        if database is None:
            logfunc(f'{_LABEL}: could not open {relative}')
            continue
        try:
            blobs = database.execute('SELECT blob FROM Packages').fetchall()
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'{_LABEL}: {relative} has no Packages table ({type(exc).__name__})')
            continue
        finally:
            database.close()
        read.append(path)
        skipped = 0
        rows = []
        for (blob,) in blobs:
            header = parse_header(blob)
            if not header.get('NAME'):
                skipped += 1
                continue
            size = header.get('LONGSIZE', header.get('SIZE'))  # LONGSIZE on rpm v6 packages, else SIZE
            rows.append((_unix_utc(header.get('INSTALLTIME')), _unix_utc(header.get('BUILDTIME')), _nevra(header),
                         header.get('VENDOR', ''), '' if size is None else str(size),
                         header.get('LICENSE', ''), header.get('GROUP', ''), header.get('SOURCERPM', ''),
                         header.get('SUMMARY', ''), relative))
        rows.sort(key=lambda r: (r[0] == '', r[0]))
        data_list.extend(rows)
        if skipped:
            logfunc(f'{_LABEL}: {skipped} header(s) skipped in {relative}')
    return data_headers, data_list, '\n'.join(read)
