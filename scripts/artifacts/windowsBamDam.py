"""Windows Background/Desktop Activity Moderator (BAM/DAM) parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange Windows.Forensics.Bam artifact; this reads
the SYSTEM hive's on-disk structure directly with python-registry.

The Background Activity Moderator (bam) and Desktop Activity Moderator (dam)
services record, per user SID, the last time each executable ran. Each value is
named for the executable and its data begins with an 8-byte little-endian Windows
FILETIME of the last run, matching the winfiletime handling in the Velociraptor
artifact.
"""

import struct
from datetime import datetime, timedelta, timezone

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc

# BAM/DAM live under each control set. A raw SYSTEM hive has no CurrentControlSet
# runtime link, so the real control sets (ControlSet001, ControlSet002, ...) are
# read directly. Windows 10 1809 moved the per-SID keys under a State subkey, so
# both layouts are read.
_SERVICES = ("bam", "dam")
_SUBPATHS = ("State\\UserSettings", "UserSettings")

__artifacts_v2__ = {
    "backgroundActivityModerator": {
        "name": "Background and Desktop Activity Moderator",
        "description": "Last run time per executable per user recorded by the "
                       "Windows Background and Desktop Activity Moderator services, "
                       "from the SYSTEM hive.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-16",
        "last_update_date": "2026-09-16",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Read from the SYSTEM hive, named in the report's located-at line. Each row is one "
                 "executable entry under a control set's Services\\bam or "
                 "Services\\dam, State\\UserSettings\\<SID> on Windows 10 1809 and "
                 "later or UserSettings\\<SID> before it. Every ControlSet00N in the "
                 "hive is read. Executable is the entry's value name as stored, "
                 "usually a path in \\Device\\HarddiskVolume<n>\\... form or a "
                 "packaged-app moniker. Last Execution (UTC) is the first eight "
                 "bytes of the entry's value read as a little-endian Windows "
                 "FILETIME, which is the last time that service recorded the "
                 "executable running for that user; an entry whose time is 0 or out "
                 "of range is shown blank. User SID is the account the entry is "
                 "stored under. Service is the source service, bam or dam; on the "
                 "tested images every row is bam because the dam key was not "
                 "present. An entry records that the executable ran for the user, "
                 "not who was at the keyboard, and the \\Device\\HarddiskVolume<n> "
                 "prefix is not resolved to a drive letter here. Reading the hive "
                 "needs the python-registry package; its .LOG1/.LOG2 transaction "
                 "logs are not replayed. Field meanings: Velocidex, "
                 "Windows.Forensics.Bam, https://github.com/Velocidex/velociraptor/"
                 "blob/master/artifacts/definitions/Windows/Forensics/Bam.yaml",
        "paths": ("*/Windows/System32/config/SYSTEM",),
        "output_types": ["standard"],
        "artifact_icon": "activity",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 53 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 33 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 28 rows",
        },
    },
}


def _filetime_datetime(blob):
    """First 8 bytes of a BAM/DAM value: a little-endian Windows FILETIME."""
    if not blob or len(blob) < 8:
        return ""
    value = struct.unpack("<Q", blob[:8])[0]
    if not value:
        return ""
    try:
        return datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=value / 10)
    except (OverflowError, ValueError, OSError):
        return ""


def _control_sets(reg):
    try:
        root = reg.root()
    except Exception:  # pylint: disable=broad-exception-caught
        return []
    return [k.name() for k in root.subkeys()
            if k.name().lower().startswith("controlset")]


def _iter_entries(reg):
    """Yield (executable, last_run_blob, sid, service) for every BAM/DAM entry."""
    for control_set in _control_sets(reg):
        for service in _SERVICES:
            for subpath in _SUBPATHS:
                path = "%s\\Services\\%s\\%s" % (control_set, service, subpath)
                try:
                    key = reg.open(path)
                except Registry.RegistryKeyNotFoundException:
                    continue
                for sid_key in key.subkeys():
                    for value in sid_key.values():
                        if value.value_type() != Registry.RegBin:
                            continue
                        yield value.name(), value.value(), sid_key.name(), service


@artifact_processor
def backgroundActivityModerator(context):
    data_headers = (('Last Execution (UTC)', 'datetime'), 'Executable', 'User SID',
                    'Service')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('BAM/DAM: the python-registry package is not installed')
        return data_headers, data_list, ''

    for source in [str(f) for f in context.get_files_found()
                   if str(f).lower().endswith('system')]:
        relative_source = context.get_relative_path(source)
        rows_here = 0
        try:
            reg = Registry.Registry(source)
            for executable, blob, sid, service in _iter_entries(reg):
                data_list.append((_filetime_datetime(blob), executable, sid,
                                  service))
                rows_here += 1
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'BAM/DAM: could not read {relative_source}: {exc}')
            continue
        if rows_here:
            sources.append(source)

    return data_headers, data_list, "\n".join(sources)
