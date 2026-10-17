"""Compact BitLocker protector inventory with stored PCR explanations."""

__artifacts_v2__ = {
    "bitlockerKeyProtectors": {
        "name": "BitLocker Key Protectors",
        "description": "BitLocker key-protector types and identifiers with stored PCR selections and short PC/UEFI explanations.",
        "author": "@ForensikITGmbH",
        "creation_date": "2026-10-17", "last_update_date": "2026-10-17",
        "requirements": "none", "category": "BitLocker",
        "paths": ("*/$BitLocker/*",),
        "output_types": ["html", "tsv", "lava"], "artifact_icon": "key",
        "notes": "Reads generated, byte-preserving $BitLocker range views, including locked volumes. "
                 "Image / Volume identifies the input; identical protector GUID, protection code and "
                 "decoded policy fields in multiple validated copies become one row per volume. "
                 "Different policy fields remain separate rows; Status names partial, differing or "
                 "unusable metadata. This is an inventory, not authentication of a wrapped key. "
                 "Copies require a valid CRC32 and bounded v2 structure. CRC32 is not authentication; "
                 "the encrypted integrity check is not verified. A diagnostic row is retained when "
                 "there is no usable metadata copy or no VMK protector in validated copies. "
                 "Protector ID is the VMK GUID, not a recovery password or secret. Unknown codes stay "
                 "hexadecimal. Multiple TPM properties stay separately labelled within a row. "
                 "An inner/outer PCR disagreement produces no decoded indices for that property. "
                 "An unsupported inner layout is qualified as outer-bitmap-only in Status. "
                 "PCRs are stored selected indices, not live TPM hashes. PCR Meaning uses the Windows "
                 "PC/UEFI convention and does not establish firmware state, the active TPM bank, "
                 "DBX/SVN or recovery-product eligibility. PCR 7 absent does not establish Secure Boot off. "
                 "PCRs and PCR Meaning are blank for protectors without a TPM datum; they are empty "
                 "throughout the public password/recovery/external-key samples for that reason. "
                 "Image / Volume may be constant in a single-volume input. Status is constant at "
                 "Validated when all three copies agree. Source manifests are retained by the normal "
                 "report provenance. No timestamp is reported, so this inventory emits no timeline events. "
                 "VMK layout: https://github.com/libyal/libbde/blob/"
                 "dd48d476e3da4a19d7bf1c4d16d14b3b6efeddf0/documentation/"
                 "BitLocker%20Drive%20Encryption%20%28BDE%29%20format.asciidoc#L868-L930. "
                 "TPM selection: https://github.com/fox-it/dissect.fve/blob/"
                 "0b3caf20c1e95136cb2eb4494303604e7629616b/dissect/fve/bde/c_tpm.py#L44-L57. "
                 "PCR convention: https://learn.microsoft.com/en-us/windows/security/operating-system-security/"
                 "data-protection/bitlocker/configure#configure-tpm-platform-validation-profile-for-native-uefi-firmware-configurations. "
                 "TPM+PIN and TPM/startup-key combinations are source-verified and synthetically tested, not validated with Windows-written images of every combination. Public-key, TPM-certificate and SID-specific layouts are not classified; unknown on-disk codes remain visible. The public reference matrix includes unsupported Vista and CRC-negative controls; "
                 "the additional public inputs contain no TPM datum. See admin/docs/bitlocker_metadata.md.",
        "sample_data": {
            "bitlocker_synthetic_profiles": "Two synthetic volumes with PCR 0/2/11 and 7/11 | 4 rows",
            "bitlocker_synthetic_partial": "Synthetic partial ranges with CRC fallback | 2 rows",
            "dissect_fve_xts256_metadata": "Public Dissect AES-XTS-256 password-only ranges | 1 rows",
            "bitlocker_public_reference_matrix": "Additional public ranges including unsupported/CRC-negative controls | 19 rows",
            "bitlocker_synthetic_protectors": "Synthetic standard protector codes and one unknown code | 9 rows",
            "bitlocker_public_ctf_gteksd": "GTekSD BitLocker Breaker CTF ranges, no TPM | 3 rows"
        },
    },
}

import json
import os

from scripts.bitlocker_metadata import (BLOCK_LIMIT, CAPTURE_MANIFEST, PCR_MEANINGS,
                                       PROTECTORS, analyze_capture)
from scripts.ilapfuncs import artifact_processor, logfunc


def _captures(context):
    """Read only the fixed, staged range filenames; never follow manifest paths."""
    groups = {}
    names = {'volume-header.bin', 'metadata-1.bin', 'metadata-2.bin', 'metadata-3.bin',
             CAPTURE_MANIFEST}
    for path in context.get_files_found():
        if os.path.basename(path) in names and not os.path.isdir(path):
            groups.setdefault(os.path.dirname(path), {})[os.path.basename(path)] = path
    for folder, paths in sorted(groups.items()):
        if CAPTURE_MANIFEST not in paths:
            continue
        try:
            with open(paths[CAPTURE_MANIFEST], 'rb') as handle:
                payload = handle.read(BLOCK_LIMIT + 1)
            if len(payload) > BLOCK_LIMIT:
                raise ValueError('range manifest exceeds the size limit')
            manifest = json.loads(payload)
            files = {}
            for name, path in paths.items():
                if name != CAPTURE_MANIFEST:
                    with open(path, 'rb') as handle:
                        files[name] = handle.read(BLOCK_LIMIT + 1)
                    if len(files[name]) > BLOCK_LIMIT:
                        raise ValueError('metadata range exceeds the size limit')
            capture = analyze_capture(manifest, files)
        except (OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
            logfunc(f'BitLocker metadata view {context.get_relative_path(folder)} not read: {exc}')
            continue
        source = context.get_relative_path(paths[CAPTURE_MANIFEST]).replace('\\', '/')
        capture['source'] = source
        yield capture



def _policy_fields(policies):
    profiles, meanings, warnings = [], [], []
    for number, policy in enumerate(policies, 1):
        prefix = f"Policy {number}: " if len(policies) > 1 else ''
        indices = policy['pcrs']
        profile = ', '.join(map(str, indices))
        if not profile:
            profile = ('None selected' if policy['bitmap'] == 0 and
                       policy['status'] == 'outer and inner PCR bitmaps agree' else 'Not decoded')
        profiles.append(prefix + profile)
        meanings.append(prefix + '; '.join(f"{n}: {PCR_MEANINGS.get(n, 'Unknown')}" for n in indices))
        if policy['status'] != 'outer and inner PCR bitmaps agree':
            warnings.append(prefix + policy['status'])
    return ' | '.join(profiles), ' | '.join(meanings), warnings


def _protector_groups(capture):
    groups = {}
    for block in capture['copies']:
        if not block['valid']:
            continue
        for protector in block['protectors']:
            policies = protector['policies']
            policy_key = tuple((p['bitmap'], tuple(p['pcrs']), p['digest'], p['status']) for p in policies)
            key = (protector['id'], protector['type'], policy_key)
            if key not in groups:
                groups[key] = (protector, set())
            groups[key][1].add(block['number'])
    return groups.values()


def _status(capture, copies):
    valid = sum(b['valid'] for b in capture['copies'])
    if valid == 3 and capture['copies_agree']:
        return 'Validated'
    observed = 'Copies ' + ', '.join(map(str, sorted(copies)))
    notes = [observed]
    if valid < 3:
        notes.append(f'partial metadata ({valid}/3 valid copies)')
    if not capture['copies_agree']:
        notes.append('metadata copies differ')
    return '; '.join(notes)


@artifact_processor
def bitlockerKeyProtectors(context):
    data_headers = ('Image / Volume', 'Key Protector', 'Protector ID', 'PCRs', 'PCR Meaning', 'Status')
    rows, captures = [], list(_captures(context))
    for capture in captures:
        meta = capture['manifest']
        identity = meta['source_image'] + ' / ' + meta['volume_name']
        groups = list(_protector_groups(capture))
        for protector, copies in groups:
            profiles, meanings, warnings = _policy_fields(protector['policies'])
            status = '; '.join([_status(capture, copies), *warnings])
            kind = PROTECTORS.get(protector['type'], f"Unknown (0x{protector['type']:04x})")
            rows.append((identity, kind, protector['id'], profiles, meanings, status))
        if not groups:
            if capture['selected'] is not None:
                valid = [b['number'] for b in capture['copies'] if b['valid']]
                status = _status(capture, valid) + '; no VMK protector recorded in validated copies'
                kind = 'None recorded'
            else:
                reason = '; '.join(dict.fromkeys(b['status'] for b in capture['copies']))
                status = ('Vista metadata is not decoded' if not capture['copies'] else
                          'No usable metadata copy: ' + reason)
                kind = 'Not assessed'
            rows.append((identity, kind, '', '', '', status))
    return data_headers, rows, '\n'.join(c['source'] for c in captures)
