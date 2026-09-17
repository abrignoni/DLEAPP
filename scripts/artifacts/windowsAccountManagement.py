"""Windows account management event parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange event-log artifacts; the implementation
reads the .evtx records directly and is not ported from that artifact.

The Event ID titles are Microsoft's, from the account-management audit
documentation (see the artifact notes).
"""

from datetime import datetime, timezone
from xml.etree import ElementTree

try:
    import Evtx.Evtx as evtx
except ImportError:
    evtx = None

from scripts.ilapfuncs import artifact_processor, logfunc

# The Security event log records local account and group administration under
# the account-management audit subcategories: an account being created,
# enabled, disabled, changed, deleted, locked out or unlocked, a password
# change or reset, and members being added to or removed from a group.

# Event ID titles as Microsoft documents them (account-management auditing).
_ACCOUNT_EVENTS = {
    '4720': 'A user account was created',
    '4722': 'A user account was enabled',
    '4723': "An attempt was made to change an account's password",
    '4724': "An attempt was made to reset an account's password",
    '4725': 'A user account was disabled',
    '4726': 'A user account was deleted',
    '4738': 'A user account was changed',
    '4740': 'A user account was locked out',
    '4767': 'A user account was unlocked',
    '4728': 'A member was added to a security-enabled global group',
    '4729': 'A member was removed from a security-enabled global group',
    '4732': 'A member was added to a security-enabled local group',
    '4733': 'A member was removed from a security-enabled local group',
    '4756': 'A member was added to a security-enabled universal group',
    '4757': 'A member was removed from a security-enabled universal group',
}

__artifacts_v2__ = {
    "accountManagement": {
        "name": "Windows Account Management",
        "description": "Local account and group administration from the Security "
                       "event log: account creation, change, deletion, lockout "
                       "and password events, and group membership changes, with "
                       "the affected account, the member, and who performed it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-15",
        "last_update_date": "2026-09-15",
        "requirements": "python-evtx",
        "category": "Windows",
        "notes": "Read from Security.evtx, named in Source File. Reported are the "
                 "account-lifecycle events (creation, enabling, disabling, "
                 "change, deletion, lockout, unlock, and password change or "
                 "reset) and the security-group membership changes (a member "
                 "added to or removed from a global, local or universal group); "
                 "the Event column is Microsoft's title for the Event ID. Event "
                 "Time (UTC) is the record's TimeCreated SystemTime, stored in "
                 "UTC. Target Account is TargetUserName as stored, which is the "
                 "account for the lifecycle events and the group for the "
                 "membership events. Member is the MemberName, or the MemberSid "
                 "when the name is not recorded, and is populated for the group "
                 "membership events (the account added or removed). Performed By "
                 "is SubjectUserName, the account that carried out the change. "
                 "Computer is the machine that recorded the event. Across the "
                 "tested images the account creation (4720), enabling (4722), "
                 "disabling (4725), change (4738), deletion (4726) and "
                 "password-reset (4724) events and the global and local group "
                 "membership changes (4728, 4729, 4732, 4733) were present; the "
                 "password-change (4723), lockout (4740), unlock (4767) and "
                 "universal-group (4756, 4757) events are read and titled but "
                 "were not present on those images. "
                 "Reading needs the python-evtx package (pip install "
                 "python-evtx). Event IDs: Microsoft, 'Audit User Account "
                 "Management', https://learn.microsoft.com/windows/security/"
                 "threat-protection/auditing/audit-user-account-management",
        "paths": ("*/Windows/System32/winevt/Logs/Security.evtx",),
        "output_types": ["standard"],
        "artifact_icon": "user-check",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 84 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 53 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 50 rows",
        },
    },
}


def _utc_from_iso(value):
    """Parse an EVTX SystemTime (ISO 8601, UTC, variable fraction) to UTC."""
    if not value:
        return ''
    text = value.strip().rstrip('Z')
    fmt = "%Y-%m-%dT%H:%M:%S"
    if '.' in text:
        base, frac = text.split('.', 1)
        text = f"{base}.{(frac + '000000')[:6]}"
        fmt = "%Y-%m-%dT%H:%M:%S.%f"
    try:
        return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
    except ValueError:
        return ''


def _member(data):
    name = (data.get('MemberName') or '').strip()
    if name and name != '-':
        return name
    return (data.get('MemberSid') or '').strip()


def _account_row(xml_text, relative_source):
    root = ElementTree.fromstring(xml_text)
    system = root.find('{*}System')
    if system is None:
        return None
    event_id = system.find('{*}EventID')
    event_id = event_id.text.strip() if event_id is not None and event_id.text else ''
    if event_id not in _ACCOUNT_EVENTS:
        return None
    time_created = system.find('{*}TimeCreated')
    when = time_created.get('SystemTime') if time_created is not None else ''
    computer = system.find('{*}Computer')
    data = {}
    event_data = root.find('{*}EventData')
    if event_data is not None:
        for item in event_data.findall('{*}Data'):
            name = item.get('Name')
            if name:
                data[name] = item.text or ''
    return (
        _utc_from_iso(when), event_id, _ACCOUNT_EVENTS[event_id],
        data.get('TargetUserName', ''), data.get('TargetDomainName', ''),
        _member(data), data.get('SubjectUserName', ''),
        computer.text if computer is not None and computer.text else '',
        relative_source)


@artifact_processor
def accountManagement(context):
    data_headers = (('Event Time (UTC)', 'datetime'), 'Event ID', 'Event',
                    'Target Account', 'Target Domain', 'Member', 'Performed By',
                    'Computer', 'Source File')
    data_list = []
    sources = []
    if evtx is None:
        logfunc('Windows Account Management: python-evtx is not installed (pip install python-evtx)')
        return data_headers, data_list, ''

    for source in [str(f) for f in context.get_files_found()
                   if str(f).lower().endswith('security.evtx')]:
        relative_source = context.get_relative_path(source)
        rows_here = 0
        try:
            with evtx.Evtx(source) as log:
                for record in log.records():
                    try:
                        row = _account_row(record.xml(), relative_source)
                    except ElementTree.ParseError:
                        continue
                    if row is not None:
                        data_list.append(row)
                        rows_here += 1
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Windows Account Management: could not read {relative_source}: {exc}')
        if rows_here:
            sources.append(source)

    return data_headers, data_list, "\n".join(sources)
