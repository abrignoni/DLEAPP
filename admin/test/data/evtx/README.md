# Event log fixtures for the reader tests

| file | what it holds | expected values written by |
| --- | --- | --- |
| `defender-1116-1117-no-templates.evtx.gz` | one 64 KiB chunk, 6 Microsoft-Windows-Windows Defender records (5 of event 1116, 1 of 1117) whose binary XML holds its elements directly, with no template instance; their event data includes `&` entity references, and the record headers number them 1 to 6 while the EventRecordID each stores runs 171 to 177 without 174 | evtx 0.13.1 (the Rust `evtx` crate's Python binding), which reads all 6 |
| `security-4688-template.evtx.gz` | one 64 KiB chunk, 1 Microsoft-Windows-Security-Auditing record of event 4688, version 2, read through a template instance as most records are | evtx 0.13.1 |

`defender-1116-1117-no-templates.evtx.gz` is `Antivirus/ID1116-1117-Defender threat detected.evtx` from
mdecrevoisier/EVTX-to-MITRE-Attack at commit 474856008f037ccd42753f02a631b42690195829, released under CC0 1.0
(https://github.com/mdecrevoisier/EVTX-to-MITRE-Attack/blob/474856008f037ccd42753f02a631b42690195829/LICENSE.md), compressed
with `gzip -9 -n`. SHA-256 of the uncompressed file: 6b1cce6cbb972596ec9361de93163fc6173c52e0e7c23c890bd99f9f42928862.

`security-4688-template.evtx.gz` is `TA0002-Execution/T1053.005-Scheduled Task/ID4688-Scheduled task creation.evtx` from the
same repository and commit, under the same licence, compressed the same way. SHA-256 of the uncompressed file:
640fed5b01787f10e8b38019de16b21845548cc6e01b5b34a31417af47852e28.
