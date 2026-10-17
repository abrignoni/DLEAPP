# BitLocker Key Protectors

One compact artifact inventories VMK protectors and their stored PCR selections
without a BitLocker key. It works on the generated read-only metadata ranges of
locked raw/E01 volumes. The helper and raw-image integration must accompany the
artifact; no runtime dependency is added.

## Report

| Column | Purpose |
| --- | --- |
| Image / Volume | Keep findings attributed to their input and volume |
| Key Protector | TPM, TPM + PIN, recovery password, startup key, etc. |
| Protector ID | Stored VMK GUID, useful for matching the protector |
| PCRs | Stored selected indices, such as `0, 2, 11` or `7, 11` |
| PCR Meaning | Short Windows PC/UEFI explanation beside each selected index |
| Status | Validated, partial/differing metadata, unsupported data or a PCR conflict |

Matching protector ID, code and policy fields across metadata copies collapse
into one row **within that volume**. Different policy fields remain separate;
volumes are never merged by matching GUID. A TPM and recovery-password pair
therefore normally gives two rows, rather than six repeated observations.
Unusable metadata retains a diagnostic row; it does not become an empty report
claiming that no protector exists. Non-TPM protectors have blank PCR fields.

Output: one HTML table, one TSV and one LAVA artifact. This configuration
inventory reports no event timestamp and emits no timeline events. The source
manifests and binary ranges remain available as report provenance; there are no
separate header, offset, CRC, datum or timestamp report tables.

## Run

Prepared against DLEAPP `86255fb823e6de7b6f397dcde0d6e7d16b232049`.
Start `dleappGUI.py`, load `bitlocker-metadata.dlprofile`, choose raw-image input,
select the E01 and an output folder, and process. Leave a BitLocker-key prompt
empty to inventory the metadata while the volume remains locked.

```console
python dleapp.py -t raw -i disk.E01 -o output -m bitlocker-metadata.dlprofile --no-find-members
```

Create the output folder first. Keep all E01 segments together. An encrypted E01
container still needs its container password to access its disk bytes.

## Protector coverage

| Stored code | Label | Validation boundary |
| --- | --- | --- |
| `0x0000` | Clear key | Public Dissect data and synthetic tests |
| `0x0100` | TPM | Two private original-image prefixes and synthetic tests |
| `0x0200` | External key | Public Dissect/CTF data and synthetic tests |
| `0x0300` | TPM and external startup key | Source flags + synthetic structure/label test |
| `0x0500` | TPM and PIN | Source mapping + synthetic structure/label test |
| `0x0700` | TPM, PIN and external startup key | Source flags + synthetic structure/label test |
| `0x0800` | Recovery password | Public/private metadata and synthetic tests |
| `0x2000` | Password | Public Dissect/CTF data and synthetic tests |
| Other | `Unknown (0x....)` | Preserved, not guessed or dropped |

The synthetic combination case does not reproduce Windows key derivation or a
valid TPM sealed object. Not every TPM combination was tested on a real Windows
image. Public-key, TPM-certificate and SID-specific layouts are not classified;
this module does not claim every Windows protector scenario is decoded. WMI/API
type numbers are not on-disk FVE protection codes and must not be substituted.

PCR numbers are the stored selections, not live PCR hashes. The PC/UEFI meanings
do not establish boot mode, Secure Boot state, the active TPM bank, DBX/SVN or a
recovery product's eligibility. Unknown inner TPM layouts are explicitly
qualified as outer-bitmap-only. Conflicting inner/outer selections are not
decoded into apparently valid indices.

## Structural checks and limits

The existing bounded parser validates the range manifest, per-range SHA256,
header pointers, information CRC32 and datum boundaries. At most 512 header
bytes and three 64 KiB ranges are requested, bounded by the available logical
image and volume. Coordinates refer to disk/array bytes, not E01-container
positions. Manifest paths are never opened. CRC32 is not authentication; the
encrypted integrity check is not verified. Vista remains unsupported.

No key, password, recovery password or TPM secret is extracted. The module does
not inspect EFI signatures, BCD, WinRE or current firmware. Broader internal
fields are retained only for structural checks and reference tests, not exposed
as more artifact tables. See [public validation](bitlocker_public_validation.md)
for source identities, original-image comparisons and public coverage limits.

## Sources

* [libbde VMK format and protection codes](https://github.com/libyal/libbde/blob/dd48d476e3da4a19d7bf1c4d16d14b3b6efeddf0/documentation/BitLocker%20Drive%20Encryption%20%28BDE%29%20format.asciidoc#L868-L930).
* [Dissect protector flags](https://github.com/fox-it/dissect.fve/blob/0b3caf20c1e95136cb2eb4494303604e7629616b/dissect/fve/bde/c_bde.py#L87-L94),
  [information CRC](https://github.com/fox-it/dissect.fve/blob/0b3caf20c1e95136cb2eb4494303604e7629616b/dissect/fve/bde/information.py#L44-L105),
  [TPM selection](https://github.com/fox-it/dissect.fve/blob/0b3caf20c1e95136cb2eb4494303604e7629616b/dissect/fve/bde/c_tpm.py#L44-L57).
* [Microsoft native UEFI PCR convention](https://learn.microsoft.com/en-us/windows/security/operating-system-security/data-protection/bitlocker/configure#configure-tpm-platform-validation-profile-for-native-uefi-firmware-configurations).
* [Microsoft WMI protector types](https://learn.microsoft.com/en-us/windows/win32/secprov/getkeyprotectors-win32-encryptablevolume), a separate numbering scheme.
