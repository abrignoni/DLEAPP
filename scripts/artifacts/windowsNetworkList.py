"""Windows Network List (network profiles) parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange and RegRipper artifacts that read the same
NetworkList keys; the implementation reads the SOFTWARE hive keys directly and
is not ported from those artifacts.
"""

import struct

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc

# Windows records each network it has connected to under NetworkList in the
# SOFTWARE hive. A profile (keyed by a GUID) holds the network name and the
# times it was first created and last connected; a signature holds the network's
# default gateway MAC address and DNS suffix and points back to the profile GUID.
# Joining the two gives, per network, its name, connection times, category and
# gateway MAC.
_NETWORKLIST = r"Microsoft\Windows NT\CurrentVersion\NetworkList"

# NLM_NETWORK_CATEGORY values.
_CATEGORY = {0: "Public", 1: "Private", 2: "Domain"}

__artifacts_v2__ = {
    "networkList": {
        "name": "Network Profiles",
        "description": "Networks this computer has connected to, from the "
                       "Windows NetworkList: each network's name, category, the "
                       "times it was created and last connected, its default "
                       "gateway MAC address and DNS suffix.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-17",
        "last_update_date": "2026-09-17",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Rows from the NetworkList keys in the SOFTWARE hive, named in "
                 "Source File, one row per network profile. Network Name is the "
                 "profile's ProfileName. Category is the profile's Category value "
                 "mapped through the NLM_NETWORK_CATEGORY vocabulary (0 Public, 1 "
                 "Private, 2 Domain) and shown with the stored number; a value "
                 "outside that set is shown as stored. Date Created and Date Last "
                 "Connected are decoded from the profile's DateCreated and "
                 "DateLastConnected SYSTEMTIME values and reported as stored: a "
                 "SYSTEMTIME carries no time zone, and on the tested images these "
                 "were local time (about seven hours from a Windows FILETIME on "
                 "the same machine), so they are not converted and not labelled "
                 "UTC. Default Gateway MAC and DNS Suffix come from the network's "
                 "signature under Signatures (Managed or Unmanaged), joined to "
                 "the profile by the signature's ProfileGuid; Default Gateway MAC "
                 "is the DefaultGatewayMac bytes formatted as a MAC address and "
                 "is blank when the signature stored none. Managed records which "
                 "signature list the network was found in. A gateway MAC address "
                 "can place a network at a physical location through public "
                 "geolocation data; a profile records that the computer connected "
                 "to the network, not who was using it. Reading the hive requires "
                 "python-registry. Category vocabulary: Microsoft "
                 "NLM_NETWORK_CATEGORY, https://learn.microsoft.com/en-us/windows/"
                 "win32/api/netlistmgr/ne-netlistmgr-nlm_network_category",
        "paths": ('*/Windows/System32/config/SOFTWARE',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "wifi",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 1 row",
            "af_case2_win10": "Windows 10 1809 build 17763 | 1 row",
            "lonewolf_win10": "Windows 10 Education build 16299 | 1 row",
        },
    },
}


def _value(key, name):
    try:
        return key.value(name).value()
    except Registry.RegistryValueNotFoundException:
        return None


def _systemtime(raw):
    """A 16-byte SYSTEMTIME, reported as stored text (no zone). Blank if invalid."""
    if not raw or len(raw) < 16:
        return ''
    year, month, _dow, day, hour, minute, second, _ms = struct.unpack('<8H', raw[:16])
    if not (1601 <= year <= 9999 and 1 <= month <= 12 and 1 <= day <= 31
            and hour < 24 and minute < 60 and second < 60):
        return ''
    return f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"


def _mac(raw):
    if not isinstance(raw, bytes) or len(raw) < 6:
        return ''
    return ':'.join(f'{byte:02x}' for byte in raw[:6])


def _category(value):
    if value is None:
        return ''
    return f"{_CATEGORY[value]} ({value})" if value in _CATEGORY else f"({value})"


def _signatures(reg):
    """profile GUID -> (gateway MAC, DNS suffix, managed/unmanaged)."""
    by_profile = {}
    for managed in ('Managed', 'Unmanaged'):
        try:
            root = reg.open(_NETWORKLIST + '\\Signatures\\' + managed)
        except Registry.RegistryKeyNotFoundException:
            continue
        for signature in root.subkeys():
            guid = _value(signature, 'ProfileGuid')
            if guid:
                by_profile[guid] = (_mac(_value(signature, 'DefaultGatewayMac')),
                                    _value(signature, 'DnsSuffix') or '', managed)
    return by_profile


@artifact_processor
def networkList(context):
    data_headers = ('Network Name', 'Category', 'Date Created', 'Date Last Connected',
                    'Default Gateway MAC', 'DNS Suffix', 'Managed', 'Source File')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('Network Profiles: the python-registry package is not installed')
        return data_headers, data_list, ''

    for source in [str(f) for f in context.get_files_found()]:
        relative_source = context.get_relative_path(source)
        try:
            reg = Registry.Registry(source)
            profiles = reg.open(_NETWORKLIST + '\\Profiles')
        except Registry.RegistryKeyNotFoundException:
            continue
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Network Profiles: could not read {relative_source}: {exc}')
            continue
        signatures = _signatures(reg)
        rows_here = 0
        for profile in profiles.subkeys():
            mac, dns, managed = signatures.get(profile.name(), ('', '', ''))
            data_list.append((
                _value(profile, 'ProfileName') or '',
                _category(_value(profile, 'Category')),
                _systemtime(_value_bytes(profile, 'DateCreated')),
                _systemtime(_value_bytes(profile, 'DateLastConnected')),
                mac, dns, managed, relative_source))
            rows_here += 1
        if rows_here:
            sources.append(source)

    return data_headers, data_list, "\n".join(sources)


def _value_bytes(key, name):
    try:
        return key.value(name).value()
    except Registry.RegistryValueNotFoundException:
        return None
