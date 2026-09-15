"""Windows CapabilityAccessManager ConsentStore parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange artifact that reads the same store; the
implementation reads the store's on-disk structure directly and is not ported
from that artifact.
"""

import os
from datetime import datetime, timedelta, timezone

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc

# Windows records which app was allowed, denied or prompted for a protected
# capability (microphone, webcam, location, contacts, and so on) in the
# CapabilityAccessManager ConsentStore. The machine-wide grants live in the
# SOFTWARE hive and the per-user grants in each NTUSER.DAT. Each app key also
# carries LastUsedTimeStart / LastUsedTimeStop, the last time the app started
# and stopped using the capability. This is the Windows counterpart of the
# macOS TCC store.

_UNIX_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_FILETIME_EPOCH_TICKS = 116444736000000000
_TICKS_PER_SECOND = 10_000_000
_SOFTWARE_PATH = r"Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore"
_NTUSER_PATH = r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore"

__artifacts_v2__ = {
    "capabilityAccessManager": {
        "name": "Capability Access Manager",
        "description": "App permission decisions from the Windows "
                       "CapabilityAccessManager ConsentStore: the capability, "
                       "the app, whether it was set to allow, deny or prompt, "
                       "and the last start and stop time recorded for the "
                       "app's use of the capability.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-15",
        "last_update_date": "2026-09-15",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "The machine-wide store is read from the SOFTWARE hive and the "
                 "per-user store from each NTUSER.DAT, named in Source File so "
                 "the two are distinguishable. Capability is the sensor or "
                 "resource key name as stored (for example microphone, webcam, "
                 "location, contacts). App is a package family name for a "
                 "packaged app, or the executable path for a non-packaged app; "
                 "the store keeps that path with # in place of the path "
                 "separator and it is shown here with the separator restored, "
                 "and App Type records which of the two an entry is. Access is "
                 "read from the Value entry as stored and is not interpreted. "
                 "Last Used Start (UTC) and Last Used Stop (UTC) are decoded "
                 "from the Windows FILETIME LastUsedTimeStart and "
                 "LastUsedTimeStop values; both are blank when the store "
                 "recorded no such time, which is common, so many rows carry "
                 "only the consent setting. Presence of a consent entry does "
                 "not establish that the app used the capability, and a blank "
                 "time does not establish that it did not. Reading the hives "
                 "requires the python-registry package. The parser reads "
                 "offline hives and does not replay their transaction logs "
                 "(.LOG1/.LOG2).",
        "paths": (
            '*/Windows/System32/config/SOFTWARE',
            '*/Users/*/NTUSER.DAT',
        ),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "shield",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 125 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 107 rows",
        },
    },
}


def _utc_from_filetime(value):
    if value in (None, "", 0):
        return ""
    try:
        seconds = (int(value) - _FILETIME_EPOCH_TICKS) / _TICKS_PER_SECOND
        return _UNIX_EPOCH + timedelta(seconds=seconds)
    except (OverflowError, TypeError, ValueError):
        return ""


def _value(key, name):
    try:
        return key.value(name).value()
    except Registry.RegistryValueNotFoundException:
        return None


def _consent_store(hive_path):
    reg = Registry.Registry(hive_path)
    is_software = os.path.basename(hive_path).upper() == "SOFTWARE"
    base = _SOFTWARE_PATH if is_software else _NTUSER_PATH
    try:
        return reg.open(base)
    except Registry.RegistryKeyNotFoundException:
        return None


def _app_entries(capability):
    """Yield (app id, app type, key) for every app under one capability."""
    for app in capability.subkeys():
        if app.name() == 'NonPackaged':
            for sub in app.subkeys():
                yield sub.name().replace('#', '\\'), 'NonPackaged', sub
        else:
            yield app.name(), 'Packaged', app


@artifact_processor
def capabilityAccessManager(context):
    data_headers = ('Capability', 'App', 'App Type', 'Access',
                    ('Last Used Start (UTC)', 'datetime'),
                    ('Last Used Stop (UTC)', 'datetime'), 'Source File')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('CapabilityAccessManager: the python-registry package is not installed')
        return data_headers, data_list, ''

    for source in [str(f) for f in context.get_files_found()
                   if os.path.basename(str(f)).upper() in ('SOFTWARE', 'NTUSER.DAT')]:
        relative_source = context.get_relative_path(source)
        rows_here = 0
        try:
            store = _consent_store(source)
            if store is None:
                continue
            for capability in store.subkeys():
                cap_name = capability.name()
                for app_id, app_type, key in _app_entries(capability):
                    data_list.append((
                        cap_name, app_id, app_type,
                        _value(key, 'Value') or '',
                        _utc_from_filetime(_value(key, 'LastUsedTimeStart')),
                        _utc_from_filetime(_value(key, 'LastUsedTimeStop')),
                        relative_source))
                    rows_here += 1
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'CapabilityAccessManager: could not read {relative_source}: {exc}')
        if rows_here:
            sources.append(source)

    return data_headers, data_list, "\n".join(sources)
