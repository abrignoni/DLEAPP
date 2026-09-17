"""Windows service and driver configuration parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange and RegRipper artifacts that read the same
Services keys; the implementation reads the SYSTEM hive keys directly and is not
ported from those artifacts.

The Start and Type value meanings, and the Services registry layout, are sourced
from Microsoft's CreateServiceW documentation (see the notes).
"""

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc

# Windows stores one key per service and driver under
# <current control set>\Services in the SYSTEM hive. Each key holds the values
# CreateService writes: DisplayName, Description, ImagePath, ObjectName, and the
# DWORDs Start (start mode) and Type (service type flags). This is the service
# configuration recorded in the registry, not a history.

# dwStartType values, Microsoft CreateServiceW (winsvc.h).
_START_TYPES = {
    0: 'Boot',       # SERVICE_BOOT_START
    1: 'System',     # SERVICE_SYSTEM_START
    2: 'Automatic',  # SERVICE_AUTO_START
    3: 'Manual',     # SERVICE_DEMAND_START
    4: 'Disabled',   # SERVICE_DISABLED
}

# dwServiceType flags, Microsoft CreateServiceW (winsvc.h). Only the documented
# flags are decoded; any other bit is reported as an unmapped hex remainder.
_SERVICE_TYPE_FLAGS = (
    (0x00000001, 'Kernel driver'),
    (0x00000002, 'File system driver'),
    (0x00000004, 'Adapter'),
    (0x00000008, 'Recognizer driver'),
    (0x00000010, 'Win32 own process'),
    (0x00000020, 'Win32 share process'),
    (0x00000100, 'Interactive process'),
)

__artifacts_v2__ = {
    "windowsServices": {
        "name": "Windows Services",
        "description": "Windows services and drivers configured in the SYSTEM "
                       "hive registry under the current control set's Services "
                       "key: each service's name, display name, description, "
                       "image path, start mode, service type and the account it "
                       "runs under.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-17",
        "last_update_date": "2026-09-17",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Rows are the direct subkeys of the current control set's "
                 "Services key in the SYSTEM hive, named in Source File, one row "
                 "per service or driver. The current control set is resolved from "
                 "Select\\Current (ControlSet00N), falling back to ControlSet001. "
                 "This is the service configuration recorded in the registry at "
                 "acquisition, not a history of when services were installed or "
                 "run; the Windows Service Installations artifact (Service "
                 "Control Manager event 7045 in System.evtx) covers install "
                 "events over time. Service is the subkey name. Display Name and "
                 "Description are the DisplayName and Description values as "
                 "stored; either can be blank or hold an indirect resource "
                 "reference such as @file.dll,-100 rather than plain text. Image "
                 "Path is the ImagePath value as stored and can hold %SystemRoot% "
                 "and other unexpanded variables; a driver or grouped service "
                 "that stores no ImagePath is normal, so Image Path is blank on "
                 "those rows. Start is the Start value mapped to Boot (0), System "
                 "(1), Automatic (2), Manual (3) or Disabled (4), shown as the "
                 "stored number and its label. Service Type is the Type value "
                 "shown as stored in hexadecimal with a decoded label for each "
                 "documented flag: 0x1 kernel driver, 0x2 file system driver, "
                 "0x4 adapter, 0x8 recognizer driver, 0x10 Win32 own process, "
                 "0x20 Win32 share process and 0x100 interactive process; any bit "
                 "outside that set is shown as an unmapped hex remainder rather "
                 "than a guessed name. Start and Service Type are blank when the "
                 "subkey stores no Start or Type value. Run As is the ObjectName "
                 "value, the "
                 "account the service is configured to run under (for example "
                 "LocalSystem, NT AUTHORITY\\LocalService or NT "
                 "AUTHORITY\\NetworkService), and is blank for drivers and any "
                 "service that stores none. A row shows how a service is "
                 "configured, not that it ran. Reading the hive needs the "
                 "python-registry package. Start and Type value meanings and the "
                 "Services registry layout: Microsoft, CreateServiceW "
                 "(winsvc.h), https://learn.microsoft.com/en-us/windows/win32/"
                 "api/winsvc/nf-winsvc-createservicew",
        "paths": ('*/Windows/System32/config/SYSTEM',),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "sliders",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 762 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 661 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 655 rows",
        },
    },
}


def _current_set(reg):
    try:
        current = reg.open('Select').value('Current').value()
        return f"ControlSet{current:03d}"
    except Exception:  # pylint: disable=broad-exception-caught
        return "ControlSet001"


def _value(key, name):
    """The data of a service value, or None when it is absent or unreadable."""
    try:
        return key.value(name).value()
    except Registry.RegistryValueNotFoundException:
        return None
    except Exception:  # pylint: disable=broad-exception-caught
        return None


def _text(value):
    if value is None or isinstance(value, (bytes, bytearray)):
        return ''
    return str(value)


def _start_type(value):
    if value is None:
        return ''
    try:
        number = int(value)
    except (TypeError, ValueError):
        return _text(value)
    label = _START_TYPES.get(number)
    return f"{number} ({label})" if label else f"{number}"


def _service_type(value):
    if value is None:
        return ''
    try:
        number = int(value)
    except (TypeError, ValueError):
        return _text(value)
    labels = []
    remainder = number
    for bit, label in _SERVICE_TYPE_FLAGS:
        if number & bit:
            labels.append(label)
            remainder &= ~bit
    if remainder:
        labels.append(f"unmapped 0x{remainder:x}")
    decoded = ' | '.join(labels) if labels else 'none'
    return f"0x{number:x} ({decoded})"


@artifact_processor
def windowsServices(context):
    data_headers = ('Service', 'Display Name', 'Description', 'Image Path',
                    'Start', 'Service Type', 'Run As', 'Source File')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('Windows Services: the python-registry package is not installed')
        return data_headers, data_list, ''

    for source in [str(f) for f in context.get_files_found()]:
        relative_source = context.get_relative_path(source)
        try:
            reg = Registry.Registry(source)
            services = reg.open(_current_set(reg) + r"\Services")
        except Registry.RegistryKeyNotFoundException:
            continue
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'Windows Services: could not read {relative_source}: {exc}')
            continue
        rows_here = 0
        for service in services.subkeys():
            data_list.append((
                service.name(),
                _text(_value(service, 'DisplayName')),
                _text(_value(service, 'Description')),
                _text(_value(service, 'ImagePath')),
                _start_type(_value(service, 'Start')),
                _service_type(_value(service, 'Type')),
                _text(_value(service, 'ObjectName')),
                relative_source))
            rows_here += 1
        if rows_here:
            sources.append(source)

    return data_headers, data_list, "\n".join(sources)
