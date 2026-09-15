"""Windows Program Compatibility Assistant (PCA) parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange PCA artifact; the implementation reads the
files' on-disk structure directly and is not ported from that artifact.

Field layout and the UTC timezone of PcaAppLaunchDic.txt are sourced from public
PCA research (see the artifact notes); the PcaGeneralDb Run Time timezone is
established here by comparison with the documented-UTC PcaAppLaunchDic times.
"""

import os
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc

# Windows 11 records program execution in the Program Compatibility Assistant
# logs under %SystemRoot%\appcompat\pca. PcaAppLaunchDic.txt keeps one line per
# executable with its most recent run time. PcaGeneralDb0.txt / PcaGeneralDb1.txt
# keep a richer per-event log (run time, a status code, the executable, its
# version-resource strings, a ProgramId, and an exit-code message). The logs are
# a Windows 11 feature and are absent on earlier Windows.

__artifacts_v2__ = {
    "pcaAppLaunch": {
        "name": "PCA App Launch Dictionary",
        "description": "Program Compatibility Assistant last-run times: for each "
                       "executable, the full path and the most recent time it was "
                       "run, from PcaAppLaunchDic.txt (Windows 11).",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-15",
        "last_update_date": "2026-09-15",
        "requirements": "none",
        "category": "Windows",
        "notes": "PcaAppLaunchDic.txt keeps one pipe-separated line per executable: "
                 "the full path and the most recent run time. The time is recorded "
                 "in UTC and is rendered here as UTC. The Program Compatibility "
                 "Assistant launch log is a Windows 11 feature and the file is "
                 "absent on earlier Windows, so an empty result is expected there. "
                 "Presence of an entry records that the executable was run at least "
                 "once; the file keeps the most recent run time only, not a full "
                 "history. Reference: Psmths, 'windows-forensic-artifacts', "
                 "https://github.com/Psmths/windows-forensic-artifacts/blob/main/"
                 "execution/program-compatibility-assistant.md",
        "paths": ("*/Windows/appcompat/pca/PcaAppLaunchDic.txt",),
        "output_types": ["standard"],
        "artifact_icon": "play",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 24 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (PCA is a Windows 11 feature; file absent)",
        },
    },
    "pcaGeneralDb": {
        "name": "PCA General Db",
        "description": "Program Compatibility Assistant event log from "
                       "PcaGeneralDb0.txt and PcaGeneralDb1.txt (Windows 11): run "
                       "time, run status as stored, executable path, its "
                       "description, vendor and file version, ProgramId, and the "
                       "exit-code message.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-15",
        "last_update_date": "2026-09-15",
        "requirements": "none",
        "category": "Windows",
        "notes": "PcaGeneralDb0.txt (and the alternate PcaGeneralDb1.txt) keep one "
                 "pipe-separated line per event with eight fields: run time, a run "
                 "status code, the executable path, the file description, the "
                 "vendor, the file version, a ProgramId, and an exit-code message. "
                 "The file is UTF-16. Description, Vendor and File Version are the "
                 "executable's own version-resource strings as stored, and the path "
                 "is kept as stored (it may use %variable% forms). Run Status is an "
                 "undocumented code reported as stored, not interpreted. Exit Code / "
                 "Message is the event text as stored. The vendor does not document "
                 "the Run Time timezone; on the tested Windows 11 image the Run Time "
                 "values matched the UTC PcaAppLaunchDic times for the same "
                 "executable to within the same hour with no fixed offset, so Run "
                 "Time is rendered as UTC. The log is a Windows 11 feature and is "
                 "absent on earlier Windows. Field layout: Sygnia, 'Diving into the "
                 "Windows 11 Forensics PCA Artifact', "
                 "https://www.sygnia.co/blog/new-windows-11-pca-artifact/",
        "paths": ("*/Windows/appcompat/pca/PcaGeneralDb0.txt",
                  "*/Windows/appcompat/pca/PcaGeneralDb1.txt"),
        "output_types": ["standard"],
        "artifact_icon": "play",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 123 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (PCA is a Windows 11 feature; files absent)",
        },
    },
}


def _read_text(path):
    """Decode a PCA log, which is UTF-8 in one file and UTF-16 in the other."""
    with open(path, 'rb') as handle:
        raw = handle.read()
    if raw[:2] in (b'\xff\xfe', b'\xfe\xff'):
        return raw.decode('utf-16', errors='replace')
    if b'\x00' in raw[:32]:  # UTF-16-LE with no byte-order mark
        return raw.decode('utf-16-le', errors='replace')
    return raw.decode('utf-8-sig', errors='replace')


def _lines(path):
    for line in _read_text(path).splitlines():
        line = line.strip().lstrip('﻿')
        if line:
            yield line


def _utc_from_pca(value):
    value = (value or '').strip()
    if not value:
        return ''
    try:
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f').replace(tzinfo=timezone.utc)
    except ValueError:
        pass
    try:
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    except ValueError:
        return ''


@artifact_processor
def pcaAppLaunch(context):
    data_headers = (('Last Executed (UTC)', 'datetime'), 'Executable Path', 'Source File')
    data_list = []
    sources = []
    for source in [str(f) for f in context.get_files_found()
                   if os.path.basename(str(f)).lower() == 'pcaapplaunchdic.txt']:
        relative_source = context.get_relative_path(source)
        rows_here = 0
        try:
            for line in _lines(source):
                parts = line.split('|')
                if len(parts) != 2:
                    continue
                path, ts = parts
                data_list.append((_utc_from_pca(ts), path.strip(), relative_source))
                rows_here += 1
        except OSError as exc:
            logfunc(f'PCA App Launch: could not read {relative_source}: {exc}')
        if rows_here:
            sources.append(source)
    return data_headers, data_list, "\n".join(sources)


@artifact_processor
def pcaGeneralDb(context):
    data_headers = (('Run Time (UTC)', 'datetime'), 'Run Status', 'Executable Path',
                    'Description', 'Vendor', 'File Version', 'Program ID',
                    'Exit Code / Message', 'Source File')
    data_list = []
    sources = []
    for source in [str(f) for f in context.get_files_found()
                   if os.path.basename(str(f)).lower().startswith('pcageneraldb')]:
        relative_source = context.get_relative_path(source)
        rows_here = 0
        try:
            for line in _lines(source):
                parts = line.split('|')
                if len(parts) != 8:
                    continue
                run_time, status, path, desc, vendor, version, program_id, message = parts
                data_list.append((
                    _utc_from_pca(run_time), status.strip(), path.strip(),
                    desc.strip(), vendor.strip(), version.strip(),
                    program_id.strip(), message.strip(), relative_source))
                rows_here += 1
        except OSError as exc:
            logfunc(f'PCA General Db: could not read {relative_source}: {exc}')
        if rows_here:
            sources.append(source)
    return data_headers, data_list, "\n".join(sources)
