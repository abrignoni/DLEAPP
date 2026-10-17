"""BitLocker key protectors and the TPM PCRs they are sealed to, from raw disk images.

The vendored qnxprobe reads each BitLocker volume's FVE metadata when the image is
opened and keeps it on the volume it lists (``volumes()``, key ``bitlocker``), locked or
opened. This module reports that, so it needs no file to match and reads nothing from
the image itself. It reports nothing for inputs that are not disk images.
"""

__artifacts_v2__ = {
    "bitlockerKeyProtectors": {
        "name": "BitLocker Key Protectors",
        "description": "Key protectors of each BitLocker volume in a disk image, locked or opened, "
                       "with the PCRs each TPM protector is sealed to.",
        "author": "@ForensikITGmbH, @AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "BitLocker",
        "notes": "Read from each volume's FVE metadata, which is not encrypted, so a locked volume "
                 "is reported too. One row per protector, and one row for a BitLocker volume whose "
                 "protectors could not be read. Protector ID is the protector's GUID, the id Windows "
                 "shows; it is not a key. For a recovery password protector it is the recovery key ID "
                 "Microsoft's recovery process uses to find an escrowed recovery password. PCRs are "
                 "the stored selection a TPM protector's key is sealed to, not measurements from a TPM: "
                 "a change to what those PCRs measure makes Windows ask for the recovery key. PCR "
                 "Meaning (UEFI) is Microsoft's description for native UEFI firmware; with BIOS or a "
                 "CSM the PCRs mean other things. Per Microsoft, for native UEFI, Windows' default is "
                 "7, 11 with Secure Boot and 0, 2, 4, 11 without. No TPM key is unsealed. A volume is "
                 "decrypted only when the examiner gives a key that opens it, and Volume State then "
                 "says so. On the nine protectors checked, each added once, Protector Last Modified "
                 "followed the order they were added in, and for the one timed independently it "
                 "matched to the second. Volume, Volume Created, Volume Description, Encryption Method "
                 "and Volume State belong to the volume, so they repeat on each of its protectors and "
                 "are uniform when the input holds one BitLocker volume. Volume Description is the "
                 "text Windows stored: on the volumes checked, the computer name, then the drive "
                 "letter or the volume label, then a date. PCRs and PCR Meaning (UEFI) are empty for "
                 "protectors other than TPM ones, as for every password, recovery password and "
                 "startup key protector in the samples. Volumes in the Windows Vista layout get one "
                 "row with no protectors (not run on a Vista image here; the row comes from the code "
                 "and qnxprobe's own test). TPM layout and PCR reading contributed by @ForensikITGmbH "
                 "in DLEAPP #616, layout per dissect.fve.",
        "sample_data": {
            "bitlocker_tpm_win11_states": "Windows 11 build 26200 | 11 rows",
            "bitlocker_win11_ntfs_xts128": "Windows 11 Pro build 26200 | 3 rows",
        },
        "paths": None,
        "output_types": "standard",
        "artifact_icon": "key",
    },
}

from scripts.ilapfuncs import artifact_processor
from scripts.windows_ntfs import filetime

# Microsoft, "Configure BitLocker", the PCR list under "Configure TPM platform validation
# profile for native UEFI firmware configurations",
# https://learn.microsoft.com/en-us/windows/security/operating-system-security/data-protection/bitlocker/configure
# (the page names its source as MicrosoftDocs/windows-docs-pr at
# 561b0d37f70d363250e59ac15f35d659ab266a7c, windows/security/operating-system-security/
# data-protection/bitlocker/configure.md).
_PCR_UEFI = {
    0: "Core System Firmware executable code", 1: "Core System Firmware data",
    2: "Extended or pluggable executable code", 3: "Extended or pluggable firmware data",
    4: "Boot Manager", 5: "GPT/Partition Table", 6: "Resume from S4 and S5 Power State Events",
    7: "Secure Boot State", 8: "Initialized to 0 with no Extends (reserved for future use)",
    9: "Initialized to 0 with no Extends (reserved for future use)",
    10: "Initialized to 0 with no Extends (reserved for future use)",
    11: "BitLocker access control", 12: "Data events and highly volatile events",
    13: "Boot Module Details", 14: "Boot Authorities",
    **{n: "Reserved for future use" for n in range(15, 24)},
}
_NOT_LISTED = "not in Microsoft's table"


def _pcrs(protector):
    """(PCRs, PCR Meaning) for one protector."""
    if protector.get('pcrs_disagree'):
        return 'Not read: the two stored PCR lists disagree', ''
    if protector.get('tpm_unread'):
        return 'Not read: TPM entry in a layout not decoded', ''
    pcrs = protector.get('pcrs')
    if pcrs is None:
        return '', ''
    if not pcrs:
        return 'None', ''
    return (', '.join(map(str, pcrs)),
            '; '.join(f'{n}: {_PCR_UEFI.get(n, _NOT_LISTED)}' for n in pcrs))


def _state(facts):
    if facts.get('unlocked_by'):
        return f"Opened with its {facts['unlocked_by']}"
    return 'Locked' + (f": {facts['why']}" if facts.get('why') else '')


def protector_rows(volumes):
    """One row per key protector of every BitLocker volume among ``volumes`` (the
    seeker's, as qnxprobe's volumes() lists them); a volume with none gets one row."""
    rows = []
    for vol in volumes or ():
        facts = vol.get('bitlocker')
        if not facts:
            continue
        name = vol.get('name') or vol.get('label') or ''
        common = (filetime(facts.get('created') or 0), name)
        tail = (facts.get('description', ''), facts.get('method_name', ''), _state(facts))
        protectors = facts.get('protectors') or []
        for protector in protectors:
            pcrs, meaning = _pcrs(protector)
            rows.append((filetime(protector.get('modified') or 0),) + common
                        + (protector['kind'], protector['id'], pcrs, meaning) + tail)
        if not protectors:
            rows.append(('',) + common + ('', '', '', '') + tail)
    return rows


@artifact_processor
def bitlockerKeyProtectors(context):
    data_headers = (('Protector Last Modified', 'datetime'), ('Volume Created', 'datetime'),
                    'Volume', 'Key Protector', 'Protector ID', 'PCRs', 'PCR Meaning (UEFI)',
                    'Volume Description', 'Encryption Method', 'Volume State')
    seeker = context.get_seeker()
    rows = protector_rows(getattr(seeker, 'volumes', None))
    source = '\n'.join(getattr(seeker, 'image_paths', None) or ()) if rows else ''
    return data_headers, rows, source
