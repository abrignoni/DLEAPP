"""Windows Setup answer files (unattend.xml) left on a Windows volume, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "windowsAnswerFiles": {
        "name": "Windows Setup Answer Files",
        "description": "Settings from the Windows Setup answer files (unattend.xml) cached in "
                       "Windows\\Panther and in the other Windows folders Setup searches, one row "
                       "per setting with its configuration pass and component.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-26",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "Windows",
        "notes": "Reads the Windows Setup answer files Windows\\Panther\\unattend.xml, "
                 "Windows\\Panther\\Unattend\\Unattend.xml or Autounattend.xml, and "
                 "Windows\\System32\\Sysprep\\unattend.xml, one row per setting. Microsoft's Windows "
                 "Setup Automation Overview lists these folders in Setup's implicit answer file "
                 "search order, says a copy of the answer file is cached to %WINDIR%\\Panther "
                 "because reboots are required during Setup, that Setup annotates the cached file "
                 "to show a configuration pass has been processed, and that it removes sensitive "
                 "data in the cached file at the end of each configuration pass (last updated "
                 "2021-10-01, "
                 "https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/windows-setup-automation-overview?view=windows-11). "
                 "The search order's other locations, a registry pointer, removable media and the "
                 "root of the system drive or of the Setup folder, are not read. A file that does "
                 "not parse as XML is logged and skipped. Pass and Pass Processed are the pass and "
                 "wasPassProcessed attributes of the settings element, Component is the "
                 "component's name, Setting is the path of element names from the component down "
                 "to an element with no child elements, with a 1-based position after a name "
                 "repeated among its siblings, as in SynchronousCommand[2], and Value is that "
                 "element's text as stored, trimmed. The offlineImage element's source attribute "
                 "is reported as a row of its own. Answer File names the file a row came from. "
                 "af_case2_win10 held Windows\\Panther\\unattend.xml, which gave 111 rows, the same "
                 "as an independent count of its elements with no child elements. Every pass in it "
                 "was marked processed, and its product key and all three password values held the "
                 "text *SENSITIVE*DATA*DELETED* instead of a value. lonewolf_win10, "
                 "pc_mus_001_win11 and szechuan_win10 hold none of the files.",
        "paths": (
            '*/Windows/[Pp]anther/[Uu]nattend.xml',
            '*/Windows/[Pp]anther/[Uu]nattend/[Uu]nattend.xml',
            '*/Windows/[Pp]anther/[Uu]nattend/[Aa]utounattend.xml',
            '*/Windows/System32/[Ss]ysprep/[Uu]nattend.xml',
        ),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "file-settings",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 111 rows",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
from xml.etree import ElementTree

from scripts.ilapfuncs import artifact_processor, logfunc


def _tag(element):
    return element.tag.split('}')[-1]


def _attribute(element, name):
    """An attribute by its local name, whatever namespace it carries."""
    for key, value in element.attrib.items():
        if key.split('}')[-1] == name:
            return value
    return ''


def leaves(element, prefix=''):
    """(setting path, value) for each element below `element` that has no child elements.

    The path joins element names with '/', and an element that shares its name with a sibling
    carries its 1-based position among them, as in SynchronousCommand[2].
    """
    children = list(element)
    counts = {}
    for child in children:
        counts[_tag(child)] = counts.get(_tag(child), 0) + 1
    seen = {}
    for child in children:
        name = _tag(child)
        seen[name] = seen.get(name, 0) + 1
        label = f'{name}[{seen[name]}]' if counts[name] > 1 else name
        path = f'{prefix}/{label}' if prefix else label
        if len(child):
            yield from leaves(child, path)
        else:
            yield path, (child.text or '').strip()


def answer_rows(root):
    """(pass, pass processed, component, setting, value) for each setting in an answer file."""
    rows = []
    for settings in root:
        if _tag(settings) == 'settings':
            for component in settings:
                for setting, value in leaves(component):
                    rows.append((settings.get('pass', ''), settings.get('wasPassProcessed', ''),
                                 component.get('name', ''), setting, value))
        elif _tag(settings) == 'offlineImage':
            rows.append(('', '', '', 'offlineImage source', _attribute(settings, 'source')))
    return rows


@artifact_processor
def windowsAnswerFiles(context):
    data_headers = ('Pass', 'Pass Processed', 'Component', 'Setting', 'Value', 'Answer File')
    data_list, sources = [], []
    for path in sorted({str(f) for f in context.get_files_found()}):
        if not os.path.isfile(path):
            continue
        relative = context.get_relative_path(path)
        try:
            root = ElementTree.parse(path).getroot()
        except (ElementTree.ParseError, OSError) as exc:
            logfunc(f'Windows Setup Answer Files: could not read {relative}: {exc}')
            continue
        data_list.extend(row + (relative,) for row in answer_rows(root))
        sources.append(path)
    return data_headers, data_list, '\n'.join(sources)
