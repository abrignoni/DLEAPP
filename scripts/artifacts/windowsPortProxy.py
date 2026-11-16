"""Windows netsh interface portproxy rules from the SYSTEM registry hive, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "windowsPortProxy": {
        "name": "Port Proxy Rules (netsh portproxy)",
        "description": "Port proxy rules in the SYSTEM hive under Services\\PortProxy of each control set: one row per "
                 "rule, with the listen and connect address and port as read from the value name and data, and the "
                 "last-written time of the key that holds the rule.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-15",
        "last_update_date": "2026-11-15",
        "requirements": "none (vendored regfprobe)",
        "category": "Windows Network",
        "notes": "Reads every ControlSetNNN\\Services\\PortProxy key of each SYSTEM hive. Each subkey of PortProxy "
                 "is a rule type (v4tov4, v4tov6, v6tov4 or v6tov6, the four rule types that netsh interface "
                 "portproxy add takes in the Microsoft netsh documentation, "
                 "https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/netsh-interface, "
                 "read on 15 November 2026, source at "
                 "https://github.com/MicrosoftDocs/windowsserverdocs/blob/c34e220f1302e3c586b0f01bf7c8a36d9fab79c6/WindowsServerDocs/administration/windows-commands/netsh-interface.md, "
                 "which says only tcp is supported), and each of its subkeys a protocol; every value under it is "
                 "one rule, its name the listen address and port and its data the connect address and port, each "
                 "joined with a slash. That layout is not in the documentation page; it was read off a Windows 11 "
                 "ARM64 lab VM after netsh interface portproxy add was run there three times for this artifact, "
                 "and the output of reg query and of netsh interface portproxy show all on the VM listed the same "
                 "three rules. Listen Address, Listen Port, Connect Address and Connect Port are the parts before "
                 "and after the last slash of the value name and data. Text is shown as read, and data that is not "
                 "text is shown as hex; all 3 values on the VM were REG_SZ text. On that VM netsh stored * as the "
                 "listen address of a rule added without one; the documentation page says an omitted listenaddress "
                 "defaults to 0.0.0.0. Key Last Written is the last-written time of the protocol key, UTC, so on a "
                 "key with several rules it is the time the key last changed, including when a rule was removed; "
                 "it is not the time each rule was added. Control Set names the control set read, and Current says "
                 "whether the Select key names it as current; when the Select key has no Current number, "
                 "ControlSet001 is treated as current. A row shows a stored rule. It does not show that the rule "
                 "was in effect or that traffic passed through it, in any control set. The documentation says "
                 "delete removes a rule and reset resets all rules; on the VM, reset left the empty v4tov4 and "
                 "v4tov6 keys behind, which give no row, and what delete leaves in the key was not tested. The "
                 "hives are read with the vendored regfprobe and a dirty hive is replayed from its .LOG1 and .LOG2 "
                 "files as Run and RunOnce Keys describes; the test hive was clean, so the replay did not run. "
                 "Evidence tier: data-proven on the SYSTEM hive of that VM, saved with reg save while the three "
                 "rules were in place (two v4tov4, one v4tov6) and removed with netsh interface portproxy reset "
                 "afterwards: 3 rows in ControlSet001, the only control set in the hive. The v6tov4 and v6tov6 "
                 "types are code-present and unexercised. That hive is not a corpus image and has no corpus key. "
                 "In that run Protocol held tcp, Control Set ControlSet001, Current Yes and Source File one path "
                 "on all 3 rows. On windows11_arm_known_20261001 the PortProxy key of ControlSet001 had no subkey, "
                 "so it gives no row.",
        "paths": ('*/Windows/System32/config/SYSTEM',
                  '*/Windows/System32/config/[Ss][Yy][Ss][Tt][Ee][Mm].[Ll][Oo][Gg][12]'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "shuffle",
        "sample_data": {
            "windows11_arm_known_20261001": "Windows 11 build 26200 | 0 rows (PortProxy key present, no rule)",
        },
    },
}

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.windows_registry import (Registry, current_control_set, found_hives, key_written_utc, open_hive,
                                      open_key)


def _split(text):
    """(address, port) split at the last slash; (text, '') when there is none."""
    address, slash, port = text.rpartition('/')
    return (address, port) if slash else (text, '')


def _text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).hex()
    return '' if value is None else str(value)


def portproxy_rows(reg):
    """One row tuple (without the source) per rule value in every control set."""
    current = current_control_set(reg)
    rows = []
    for control_set in sorted(k.name() for k in reg.root().subkeys() if k.name().lower().startswith('controlset')):
        proxy = open_key(reg, f'{control_set}\\Services\\PortProxy')
        if proxy is None:
            continue
        for rule_type in proxy.subkeys():
            for protocol in rule_type.subkeys():
                written = key_written_utc(protocol)
                for value in protocol.values():
                    listen_address, listen_port = _split(_text(value.name()))
                    connect_address, connect_port = _split(_text(value.value()))
                    rows.append((written, rule_type.name(), protocol.name(), listen_address, listen_port,
                                 connect_address, connect_port, control_set,
                                 'Yes' if control_set.lower() == current.lower() else 'No'))
    return rows


@artifact_processor
def windowsPortProxy(context):
    data_headers = (('Key Last Written (UTC)', 'datetime'), 'Type', 'Protocol', 'Listen Address', 'Listen Port',
                    'Connect Address', 'Connect Port', 'Control Set', 'Current', 'Source File')
    data_list, sources = [], []
    for source in found_hives(context, 'SYSTEM'):
        relative = context.get_relative_path(source)
        try:
            rows = portproxy_rows(open_hive(source, context))
        except (OSError, ValueError, Registry.RegistryException) as error:
            logfunc(f'Port Proxy Rules: could not read {relative}: {error}')
            continue
        data_list.extend(row + (relative,) for row in rows)
        sources.append(source)
    return data_headers, data_list, '\n'.join(sources)
