"""WMI event subscriptions read from the WMI CIM repository, for DLEAPP.

Author: @AlexisBrignoni, Claude.

A permanent WMI event subscription is three objects in the repository Windows keeps in
Windows\\System32\\wbem\\Repository: an __EventFilter (the event query), an instance of an
__EventConsumer subclass (what runs: a command line, a script, a log line) and an
__FilterToConsumerBinding joining the two. The repository is read with the vendored
cimreader (scripts/vendor/cimreader.py), which walks the active page mapping and the index
and decodes each instance against its class definition; the file is never scanned for
strings. Only the live view is read: objects that a deletion or a later write left in free
pages are not reported.
"""

import os
import re
from collections import OrderedDict

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.vendor import cimreader

_NAMESPACES = ('root\\subscription', 'root\\default')

# Consumer properties shown in their own columns. Every other property an instance holds,
# apart from Name and CreatorSID, goes to Other Properties, so nothing is dropped.
_CONSUMER_COLUMNS = ('CommandLineTemplate', 'ExecutablePath', 'WorkingDirectory',
                     'ScriptingEngine', 'ScriptFileName', 'ScriptText', 'Filename', 'Text')
_FILTER_COLUMNS = ('Name', 'QueryLanguage', 'Query', 'EventNamespace', 'CreatorSID')
_BINDING_COLUMNS = ('Filter', 'Consumer', 'CreatorSID')

_REF = re.compile(r'^(?:\\\\[^\\:]*\\(?P<ns>[^:]*):)?(?P<cls>[^.:]+)\.(?P<keys>.*)$')
_REF_KEY = re.compile(r'\s*(\w+)\s*=\s*("(?:[^"\\]|\\.)*"|[^,]*)\s*(?:,|$)')


def _sid(value):
    """A SID held as a uint8 array, as S-1-...: a revision byte, a sub-authority count, a
    48-bit big-endian identifier authority, then 32-bit little-endian sub-authorities
    ([MS-DTYP] 2.4.2.2). Bytes that do not hold one are shown as stored."""
    if not isinstance(value, list):
        return '' if value is None else str(value)
    data = bytes(value)
    if len(data) < 8 or data[0] != 1 or len(data) != 8 + 4 * data[1]:
        return ' '.join(f'{b:02x}' for b in data)
    authority = int.from_bytes(data[2:8], 'big')
    subs = [int.from_bytes(data[8 + 4 * i:12 + 4 * i], 'little') for i in range(data[1])]
    return 'S-1-' + '-'.join(str(v) for v in [authority] + subs)


def _text(value):
    if value is None:
        return ''
    if isinstance(value, bool):
        return 'True' if value else 'False'
    if isinstance(value, list):
        return '\n'.join(_text(v) for v in value)
    return str(value)


def _parse_ref(ref, default_ns):
    """(namespace, class, {key: value}) from an object path such as
    \\\\.\\ROOT\\subscription:__EventFilter.Name="x" or __EventFilter.Name="x"."""
    match = _REF.match(ref or '')
    if not match:
        return None
    keys = {}
    for name, value in _REF_KEY.findall(match.group('keys')):
        if value.startswith('"') and value.endswith('"'):
            value = re.sub(r'\\(.)', r'\1', value[1:-1])
        keys[name.lower()] = value
    return (match.group('ns') or default_ns), match.group('cls'), keys


class _Repository:
    """The subscription objects of one repository folder."""

    def __init__(self, context, folder, label):
        self.folder = folder
        self.where = context.get_relative_path(folder)
        self.rows = {ns: [] for ns in _NAMESPACES}
        self.error = None
        try:
            with cimreader.open_repository(folder) as repo:
                result = cimreader.subscriptions(repo, _NAMESPACES)
                self.layout = repo.layout
        except (cimreader.CimError, OSError) as exc:
            self.error = str(exc)
            logfunc(f'{label}: could not read the WMI repository in {self.where}: {exc}')
            return
        for message in result['errors']:
            logfunc(f'{label}: {self.where}: {message}')
        for ns, rows in result['namespaces'].items():
            self.rows[ns] = rows
            for row in rows:
                for message in row['errors']:
                    logfunc(f'{label}: {self.where}: {ns}:{row["class"]}: {message}')

    def of_kind(self, kind):
        for ns in _NAMESPACES:
            for row in self.rows[ns]:
                if row['kind'] == kind:
                    yield ns, row

    def find(self, ns, cls, keys):
        """Instances of class cls in ns whose key properties equal keys."""
        hits = []
        kind = '__EventFilter' if cls.lower() == '__eventfilter' else '__EventConsumer'
        for row_ns, row in self.of_kind(kind):
            if row_ns.lower() != ns.lower() or row['class'].lower() != cls.lower():
                continue
            props = {k.lower(): v for k, v in row['properties'].items()}
            if all(str(props.get(k)) == v for k, v in keys.items()):
                hits.append(row)
        return hits

    def bindings_naming(self, row, side):
        """The bindings whose Filter or Consumer reference resolves to this instance."""
        out = []
        for binding_ns, binding in self.of_kind('__FilterToConsumerBinding'):
            parsed = _parse_ref(binding['properties'].get(side), binding_ns)
            if parsed and row in self.find(*parsed):
                other = binding['properties'].get('Consumer' if side == 'Filter' else 'Filter')
                out.append(_text(other))
        return out


def _repositories(context, label):
    folders = OrderedDict()
    for path in sorted({str(f) for f in context.get_files_found()}):
        if os.path.isfile(path) and os.path.basename(path).upper() == 'OBJECTS.DATA':
            folders[os.path.dirname(path)] = None
    return [_Repository(context, folder, label) for folder in folders]


def _sources(context):
    return '\n'.join(sorted(str(f) for f in context.get_files_found() if os.path.isfile(str(f))))


def _common(repo, row):
    location = row.get('location')
    return ('\n'.join(row['errors']), repo.where, location['file_offset'] if location else '')


__artifacts_v2__ = {
    "wmiRepositoryEventFilters": {
        "name": "WMI Repository Event Filters",
        "description": "__EventFilter instances in the root\\subscription and root\\default "
                       "namespaces of the WMI CIM repository: each filter's name, query and "
                       "creator SID, and the consumers that bindings join it to.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-31",
        "last_update_date": "2026-10-31",
        "requirements": "none",
        "category": "Windows",
        "notes": "Read from the WMI CIM repository: OBJECTS.DATA, INDEX.BTR and MAPPING1.MAP to MAPPING3.MAP under Windows\\System32\\wbem\\Repository, or OBJECTS.MAP and INDEX.MAP in its FS folder on an early Windows XP repository, all named in the report's located-at line. The files are read with the vendored cimreader 0.1.0 (scripts/vendor/cimreader.py, https://github.com/abrignoni/cimreader/blob/4ac4c85198ac59c8243eb3465be93dd00280bcfc/cimreader.py), a standard-library port of Mandiant's python-cim (flare-wmi commit b0a5a094ff9ca7d7a1c4fc711dc00c74dec4b6b1), which resolves the mapping file with the highest version, walks the index B-tree and decodes each instance against its class definition and the classes it derives from; the files are not scanned for strings. Only the live view is read: an object a deletion or a later write left in a free page or an older mapping generation is not reported, so the absence of a row is not evidence that an object never existed. Only the root\\subscription and root\\default namespaces are read; a subscription registered in another namespace is not reported. Validated on known data from a Windows 11 25H2 build 26200 ARM64 lab machine (corpus keys windows11_arm_wmi_subscription_known_20261031_baseline, _created, _modified and _removed): nine subscription objects were created there with New-CimInstance, one consumer's command line was then changed and all nine were removed, the repository was copied out of a VSS shadow copy at each step, and the live view was exported with Get-CimInstance. On those captures cimreader matched every property of every exported instance in the two namespaces (498 of 498 after creation, 416 of 416 before creation and after removal) except one SystemRestoreConfig instance in root\\default, which carries dynamic properties and is not a subscription object; each artifact here gave 1 row before creation, 4 after creation and after the change, and 1 after removal. Creator SID is the CreatorSID byte array rendered as a SID ([MS-DTYP] 2.4.2.2: a revision byte, a sub-authority count, a 48-bit big-endian authority, then 32-bit little-endian sub-authorities); on the known data it equals, for all nine created objects, the SID that whoami /user reported for the account that created them (recorded in the known data's known_session folder). Bytes that do not hold a SID are shown as hex. Text is decoded as the repository stores it: a leading byte 0 then one byte per character (decoded as Latin-1), or 1 then UTF-16LE, which the known data's non-ASCII filter name, command line and log text confirmed. Not reported: the two FILETIMEs at the head of each instance record. On the known data neither was the time the instance was created or changed: the second equalled its class definition's timestamp on all 28,254 instances measured across the known-data repository and eleven corpus repositories, and the first predated the creation by five days and moved by one 100 ns tick when the instance was changed. There is no event time column for that reason. Repository Folder is the folder holding OBJECTS.DATA, relative to the input; it holds one value on every row of an input with one repository, and it is kept because the paths can match more than one repository (a Windows.old tree, a second volume) and no other column separates them: a composite input holding two repositories gave the sum of their rows, and a copy of the same files outside a wbem folder added none. Record Offset (OBJECTS.DATA) is the byte offset of the record's first byte in that file (its physical page times 8,192 plus the offset its page's table of contents records); a record larger than its page continues on the following logical pages, which need not follow it in the file. Other Properties lists, one per line as name: value, every property the instance holds a value for that has no column of its own, including values the instance takes from its class default; a property the instance marks as not set is left out. Read Errors holds what cimreader could not decode on that instance (embedded object properties, char16 properties, dynamic properties); it was empty on every row of every registered sample, and no subscription class in any of their repositories declares an embedded object or char16 property. Exercised with no oracle on the repositories of eleven registered images, Windows XP to Windows 11 and Server 2012 R2 to 2022: every subscription object decoded with no error. Not covered: Windows Vista and 8.0 repositories have not been read, and python-cim's own XP layout with MAPPING files has been read only as a mapping file, never as a whole repository. A row records that the object is in the repository; it does not by itself establish who created it, when, or whether its consumer ever ran. Filter Name, Query Language, Query and Event Namespace are the instance's Name, QueryLanguage, Query and EventNamespace. Query Language held WQL on every row of every registered sample. Event Namespace held root\\cimv2 on every row except one filter on cfreds_hacking_case_winxp, which has an empty Event Namespace. Bound Consumers lists, as stored, the Consumer reference of every binding whose Filter reference resolves to this filter by namespace, class and key values; a filter no binding names has none. Other Properties was empty on every row of every registered sample.",
        "paths": ('*/[Ww][Bb][Ee][Mm]/[Rr][Ee][Pp][Oo][Ss][Ii][Tt][Oo][Rr][Yy]/*',),
        "output_types": ["standard"],
        "artifact_icon": "filter",
        "sample_data": {
                           "windows11_arm_wmi_subscription_known_20261031_baseline": "Windows 11 25H2 build 26200 | 1 row",
                           "windows11_arm_wmi_subscription_known_20261031_created": "Windows 11 25H2 build 26200 | 4 rows",
                           "windows11_arm_wmi_subscription_known_20261031_modified": "Windows 11 25H2 build 26200 | 4 rows",
                           "windows11_arm_wmi_subscription_known_20261031_removed": "Windows 11 25H2 build 26200 | 1 row",
                           "cfreds_hacking_case_winxp": "Windows XP build 2600 | 2 rows",
                           "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 2 rows",
                           "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 1 row",
                           "af_case2_win10": "Windows 10 1809 build 17763 | 1 row",
                           "lonewolf_win10": "Windows 10 Education build 16299 | 1 row",
                           "szechuan_win10": "Windows 10 2004 build 19041 | 1 row",
                           "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 1 row",
                           "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 1 row",
                           "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 1 row",
                           "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 1 row",
                           "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 1 row",
                       },
    },
    "wmiRepositoryEventConsumers": {
        "name": "WMI Repository Event Consumers",
        "description": "Instances of __EventConsumer and of the classes derived from it "
                       "(CommandLineEventConsumer, ActiveScriptEventConsumer and others) in "
                       "the root\\subscription and root\\default namespaces of the WMI CIM "
                       "repository: the command line, script or other action each holds, and "
                       "the filters that bindings join it to.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-31",
        "last_update_date": "2026-10-31",
        "requirements": "none",
        "category": "Windows",
        "notes": "Read from the WMI CIM repository: OBJECTS.DATA, INDEX.BTR and MAPPING1.MAP to MAPPING3.MAP under Windows\\System32\\wbem\\Repository, or OBJECTS.MAP and INDEX.MAP in its FS folder on an early Windows XP repository, all named in the report's located-at line. The files are read with the vendored cimreader 0.1.0 (scripts/vendor/cimreader.py, https://github.com/abrignoni/cimreader/blob/4ac4c85198ac59c8243eb3465be93dd00280bcfc/cimreader.py), a standard-library port of Mandiant's python-cim (flare-wmi commit b0a5a094ff9ca7d7a1c4fc711dc00c74dec4b6b1), which resolves the mapping file with the highest version, walks the index B-tree and decodes each instance against its class definition and the classes it derives from; the files are not scanned for strings. Only the live view is read: an object a deletion or a later write left in a free page or an older mapping generation is not reported, so the absence of a row is not evidence that an object never existed. Only the root\\subscription and root\\default namespaces are read; a subscription registered in another namespace is not reported. Validated on known data from a Windows 11 25H2 build 26200 ARM64 lab machine (corpus keys windows11_arm_wmi_subscription_known_20261031_baseline, _created, _modified and _removed): nine subscription objects were created there with New-CimInstance, one consumer's command line was then changed and all nine were removed, the repository was copied out of a VSS shadow copy at each step, and the live view was exported with Get-CimInstance. On those captures cimreader matched every property of every exported instance in the two namespaces (498 of 498 after creation, 416 of 416 before creation and after removal) except one SystemRestoreConfig instance in root\\default, which carries dynamic properties and is not a subscription object; each artifact here gave 1 row before creation, 4 after creation and after the change, and 1 after removal. Creator SID is the CreatorSID byte array rendered as a SID ([MS-DTYP] 2.4.2.2: a revision byte, a sub-authority count, a 48-bit big-endian authority, then 32-bit little-endian sub-authorities); on the known data it equals, for all nine created objects, the SID that whoami /user reported for the account that created them (recorded in the known data's known_session folder). Bytes that do not hold a SID are shown as hex. Text is decoded as the repository stores it: a leading byte 0 then one byte per character (decoded as Latin-1), or 1 then UTF-16LE, which the known data's non-ASCII filter name, command line and log text confirmed. Not reported: the two FILETIMEs at the head of each instance record. On the known data neither was the time the instance was created or changed: the second equalled its class definition's timestamp on all 28,254 instances measured across the known-data repository and eleven corpus repositories, and the first predated the creation by five days and moved by one 100 ns tick when the instance was changed. There is no event time column for that reason. Repository Folder is the folder holding OBJECTS.DATA, relative to the input; it holds one value on every row of an input with one repository, and it is kept because the paths can match more than one repository (a Windows.old tree, a second volume) and no other column separates them: a composite input holding two repositories gave the sum of their rows, and a copy of the same files outside a wbem folder added none. Record Offset (OBJECTS.DATA) is the byte offset of the record's first byte in that file (its physical page times 8,192 plus the offset its page's table of contents records); a record larger than its page continues on the following logical pages, which need not follow it in the file. Other Properties lists, one per line as name: value, every property the instance holds a value for that has no column of its own, including values the instance takes from its class default; a property the instance marks as not set is left out. Read Errors holds what cimreader could not decode on that instance (embedded object properties, char16 properties, dynamic properties); it was empty on every row of every registered sample, and no subscription class in any of their repositories declares an embedded object or char16 property. Exercised with no oracle on the repositories of eleven registered images, Windows XP to Windows 11 and Server 2012 R2 to 2022: every subscription object decoded with no error. Not covered: Windows Vista and 8.0 repositories have not been read, and python-cim's own XP layout with MAPPING files has been read only as a mapping file, never as a whole repository. A row records that the object is in the repository; it does not by itself establish who created it, when, or whether its consumer ever ran. Consumer Class is the instance's own class; Consumer Name is its Name. Command Line Template, Executable Path, Working Directory, Scripting Engine, Script File Name, Script Text, Log File Name and Log Text are the CommandLineTemplate, ExecutablePath, WorkingDirectory, ScriptingEngine, ScriptFileName, ScriptText, Filename and Text properties, empty for a class that does not declare them or an instance that does not set them: Executable Path and Script File Name were empty on every row of every registered sample, and on the images whose only consumer is the NTEventLogEventConsumer every one of those columns is empty and the consumer's properties are in Other Properties. Bound Filters lists, as stored, the Filter reference of every binding whose Consumer reference resolves to this consumer; a consumer no binding names has none.",
        "paths": ('*/[Ww][Bb][Ee][Mm]/[Rr][Ee][Pp][Oo][Ss][Ii][Tt][Oo][Rr][Yy]/*',),
        "output_types": ["standard"],
        "artifact_icon": "terminal",
        "sample_data": {
                           "windows11_arm_wmi_subscription_known_20261031_baseline": "Windows 11 25H2 build 26200 | 1 row",
                           "windows11_arm_wmi_subscription_known_20261031_created": "Windows 11 25H2 build 26200 | 4 rows",
                           "windows11_arm_wmi_subscription_known_20261031_modified": "Windows 11 25H2 build 26200 | 4 rows",
                           "windows11_arm_wmi_subscription_known_20261031_removed": "Windows 11 25H2 build 26200 | 1 row",
                           "cfreds_hacking_case_winxp": "Windows XP build 2600 | 2 rows",
                           "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 2 rows",
                           "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 1 row",
                           "af_case2_win10": "Windows 10 1809 build 17763 | 1 row",
                           "lonewolf_win10": "Windows 10 Education build 16299 | 1 row",
                           "szechuan_win10": "Windows 10 2004 build 19041 | 1 row",
                           "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 1 row",
                           "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 1 row",
                           "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 1 row",
                           "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 1 row",
                           "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 1 row",
                       },
    },
    "wmiRepositoryFilterToConsumerBindings": {
        "name": "WMI Repository Filter to Consumer Bindings",
        "description": "__FilterToConsumerBinding instances in the root\\subscription and "
                       "root\\default namespaces of the WMI CIM repository, each with the "
                       "query of the filter and the action of the consumer it names, looked "
                       "up through the binding's own references.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-31",
        "last_update_date": "2026-10-31",
        "requirements": "none",
        "category": "Windows",
        "notes": "Read from the WMI CIM repository: OBJECTS.DATA, INDEX.BTR and MAPPING1.MAP to MAPPING3.MAP under Windows\\System32\\wbem\\Repository, or OBJECTS.MAP and INDEX.MAP in its FS folder on an early Windows XP repository, all named in the report's located-at line. The files are read with the vendored cimreader 0.1.0 (scripts/vendor/cimreader.py, https://github.com/abrignoni/cimreader/blob/4ac4c85198ac59c8243eb3465be93dd00280bcfc/cimreader.py), a standard-library port of Mandiant's python-cim (flare-wmi commit b0a5a094ff9ca7d7a1c4fc711dc00c74dec4b6b1), which resolves the mapping file with the highest version, walks the index B-tree and decodes each instance against its class definition and the classes it derives from; the files are not scanned for strings. Only the live view is read: an object a deletion or a later write left in a free page or an older mapping generation is not reported, so the absence of a row is not evidence that an object never existed. Only the root\\subscription and root\\default namespaces are read; a subscription registered in another namespace is not reported. Validated on known data from a Windows 11 25H2 build 26200 ARM64 lab machine (corpus keys windows11_arm_wmi_subscription_known_20261031_baseline, _created, _modified and _removed): nine subscription objects were created there with New-CimInstance, one consumer's command line was then changed and all nine were removed, the repository was copied out of a VSS shadow copy at each step, and the live view was exported with Get-CimInstance. On those captures cimreader matched every property of every exported instance in the two namespaces (498 of 498 after creation, 416 of 416 before creation and after removal) except one SystemRestoreConfig instance in root\\default, which carries dynamic properties and is not a subscription object; each artifact here gave 1 row before creation, 4 after creation and after the change, and 1 after removal. Creator SID is the CreatorSID byte array rendered as a SID ([MS-DTYP] 2.4.2.2: a revision byte, a sub-authority count, a 48-bit big-endian authority, then 32-bit little-endian sub-authorities); on the known data it equals, for all nine created objects, the SID that whoami /user reported for the account that created them (recorded in the known data's known_session folder). Bytes that do not hold a SID are shown as hex. Text is decoded as the repository stores it: a leading byte 0 then one byte per character (decoded as Latin-1), or 1 then UTF-16LE, which the known data's non-ASCII filter name, command line and log text confirmed. Not reported: the two FILETIMEs at the head of each instance record. On the known data neither was the time the instance was created or changed: the second equalled its class definition's timestamp on all 28,254 instances measured across the known-data repository and eleven corpus repositories, and the first predated the creation by five days and moved by one 100 ns tick when the instance was changed. There is no event time column for that reason. Repository Folder is the folder holding OBJECTS.DATA, relative to the input; it holds one value on every row of an input with one repository, and it is kept because the paths can match more than one repository (a Windows.old tree, a second volume) and no other column separates them: a composite input holding two repositories gave the sum of their rows, and a copy of the same files outside a wbem folder added none. Record Offset (OBJECTS.DATA) is the byte offset of the record's first byte in that file (its physical page times 8,192 plus the offset its page's table of contents records); a record larger than its page continues on the following logical pages, which need not follow it in the file. Other Properties lists, one per line as name: value, every property the instance holds a value for that has no column of its own, including values the instance takes from its class default; a property the instance marks as not set is left out. Read Errors holds what cimreader could not decode on that instance (embedded object properties, char16 properties, dynamic properties); it was empty on every row of every registered sample, and no subscription class in any of their repositories declares an embedded object or char16 property. Exercised with no oracle on the repositories of eleven registered images, Windows XP to Windows 11 and Server 2012 R2 to 2022: every subscription object decoded with no error. Not covered: Windows Vista and 8.0 repositories have not been read, and python-cim's own XP layout with MAPPING files has been read only as a mapping file, never as a whole repository. A row records that the object is in the repository; it does not by itself establish who created it, when, or whether its consumer ever ran. Filter (as stored) and Consumer (as stored) are the binding's Filter and Consumer references. Filter Query, Consumer Class and Consumer Action come from the filter and consumer those references resolve to, found by the namespace the reference names (or the binding's own), the class it names and the key values it records; Filter Found and Consumer Found say whether such an instance is in the repository. Both were Yes on every row of every registered sample; the committed synthetic test case holds a binding whose consumer is absent. Consumer Action is the first of CommandLineTemplate, ExecutablePath, ScriptText, ScriptFileName and Filename the consumer holds, named, or for a consumer holding none of them every property it holds other than Name and CreatorSID. Other Properties held DeliverSynchronously, MaintainSecurityContext and SlowDownProviders on every row of every registered sample.",
        "paths": ('*/[Ww][Bb][Ee][Mm]/[Rr][Ee][Pp][Oo][Ss][Ii][Tt][Oo][Rr][Yy]/*',),
        "output_types": ["standard"],
        "artifact_icon": "link",
        "sample_data": {
                           "windows11_arm_wmi_subscription_known_20261031_baseline": "Windows 11 25H2 build 26200 | 1 row",
                           "windows11_arm_wmi_subscription_known_20261031_created": "Windows 11 25H2 build 26200 | 4 rows",
                           "windows11_arm_wmi_subscription_known_20261031_modified": "Windows 11 25H2 build 26200 | 4 rows",
                           "windows11_arm_wmi_subscription_known_20261031_removed": "Windows 11 25H2 build 26200 | 1 row",
                           "cfreds_hacking_case_winxp": "Windows XP build 2600 | 2 rows",
                           "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 2 rows",
                           "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 1 row",
                           "af_case2_win10": "Windows 10 1809 build 17763 | 1 row",
                           "lonewolf_win10": "Windows 10 Education build 16299 | 1 row",
                           "szechuan_win10": "Windows 10 2004 build 19041 | 1 row",
                           "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 1 row",
                           "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 1 row",
                           "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 1 row",
                           "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 1 row",
                           "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 1 row",
                       },
    },
}


@artifact_processor
def wmiRepositoryEventFilters(context):
    data_headers = ('Namespace', 'Filter Name', 'Query Language', 'Query', 'Event Namespace',
                    'Creator SID', 'Bound Consumers', 'Other Properties', 'Read Errors',
                    'Repository Folder', 'Record Offset (OBJECTS.DATA)')
    data_list = []
    for repo in _repositories(context, 'WMI Repository Event Filters'):
        for ns, row in repo.of_kind('__EventFilter'):
            p = row['properties']
            other = [f'{k}: {_text(v)}' for k, v in p.items() if k not in _FILTER_COLUMNS and v is not None]
            data_list.append((
                ns, _text(p.get('Name')), _text(p.get('QueryLanguage')), _text(p.get('Query')),
                _text(p.get('EventNamespace')), _sid(p.get('CreatorSID')),
                '\n'.join(repo.bindings_naming(row, 'Filter')), '\n'.join(other)) + _common(repo, row))
    return data_headers, data_list, _sources(context)


@artifact_processor
def wmiRepositoryEventConsumers(context):
    data_headers = ('Namespace', 'Consumer Class', 'Consumer Name', 'Command Line Template',
                    'Executable Path', 'Working Directory', 'Scripting Engine', 'Script File Name',
                    'Script Text', 'Log File Name', 'Log Text', 'Creator SID', 'Bound Filters',
                    'Other Properties', 'Read Errors', 'Repository Folder',
                    'Record Offset (OBJECTS.DATA)')
    data_list = []
    for repo in _repositories(context, 'WMI Repository Event Consumers'):
        for ns, row in repo.of_kind('__EventConsumer'):
            p = row['properties']
            shown = set(_CONSUMER_COLUMNS) | {'Name', 'CreatorSID'}
            other = [f'{k}: {_text(v)}' for k, v in p.items() if k not in shown and v is not None]
            data_list.append((ns, row['class'], _text(p.get('Name'))) +
                             tuple(_text(p.get(c)) for c in _CONSUMER_COLUMNS) +
                             (_sid(p.get('CreatorSID')), '\n'.join(repo.bindings_naming(row, 'Consumer')),
                              '\n'.join(other)) + _common(repo, row))
    return data_headers, data_list, _sources(context)


_ACTIONS = ('CommandLineTemplate', 'ExecutablePath', 'ScriptText', 'ScriptFileName', 'Filename')


def _action(consumer):
    """The first of _ACTIONS the consumer holds, named; for a consumer holding none of them,
    every property it holds other than Name and CreatorSID."""
    p = consumer['properties']
    for name in _ACTIONS:
        if p.get(name) not in (None, ''):
            return f'{name}: {_text(p[name])}'
    return '\n'.join(f'{k}: {_text(v)}' for k, v in p.items()
                     if k not in ('Name', 'CreatorSID') and v is not None)


@artifact_processor
def wmiRepositoryFilterToConsumerBindings(context):
    data_headers = ('Namespace', 'Filter (as stored)', 'Consumer (as stored)', 'Filter Query',
                    'Consumer Class', 'Consumer Action', 'Filter Found', 'Consumer Found',
                    'Creator SID', 'Other Properties', 'Read Errors', 'Repository Folder',
                    'Record Offset (OBJECTS.DATA)')
    data_list = []
    for repo in _repositories(context, 'WMI Repository Filter to Consumer Bindings'):
        for ns, row in repo.of_kind('__FilterToConsumerBinding'):
            p = row['properties']
            filters, consumers = [], []
            parsed = _parse_ref(p.get('Filter'), ns)
            if parsed:
                filters = repo.find(*parsed)
            parsed = _parse_ref(p.get('Consumer'), ns)
            if parsed:
                consumers = repo.find(*parsed)
            other = [f'{k}: {_text(v)}' for k, v in p.items() if k not in _BINDING_COLUMNS and v is not None]
            data_list.append((
                ns, _text(p.get('Filter')), _text(p.get('Consumer')),
                '\n'.join(_text(f['properties'].get('Query')) for f in filters),
                '\n'.join(c['class'] for c in consumers), '\n'.join(_action(c) for c in consumers),
                'Yes' if filters else 'No', 'Yes' if consumers else 'No',
                _sid(p.get('CreatorSID')), '\n'.join(other)) + _common(repo, row))
    return data_headers, data_list, _sources(context)
