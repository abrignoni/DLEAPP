# Public BitLocker validation corpus

The added coverage is **15 additional public inputs**: 13 Dissect FVE volumes,
one dfVFS To Go image and one GTekSD CTF disk. Together with the earlier Dissect
AES-XTS-256 fixture this is 16 distinct public inputs. Negative/unsupported
controls are included in that number; it is not a count of 16 decoded volumes.
No private evidence is included in any fixture or public report.

## Observed coverage

| Input | Observed result |
| --- | --- |
| Dissect `aes-xts_128` | XTS-128, password protector, 3 valid copies |
| Dissect `aes_128`, `aes_256` | CBC-128 / CBC-256, password protector, 3 valid copies each |
| Dissect `aes_128_diffuser`, `aes_256_diffuser` | CBC with Elephant diffuser, 3 valid copies each |
| Dissect `recovery_key`, `startup_key` | External-key and password protectors, 3 valid copies each |
| Dissect `recovery_password` | Recovery-password and password protectors, 3 valid copies |
| Dissect `suspended` | Clear-key protector, 3 valid copies; no key material is printed |
| Dissect `eow_partial` | Encrypt-on-Write header, conversion state and 3 valid copies |
| Dissect `decrypted` | Method 0 (`None`), decrypted states, no protector, 3 valid copies |
| Dissect `win7_partial` | 1 valid copy, external/recovery/clear protectors; 2 invalid headers |
| Dissect `vista` | Header identified; version 1 metadata remains unsupported |
| dfVFS `bdetogo.raw` | To Go header identified; all 3 stored CRCs differ from computed CRCs |
| GTekSD BitLocker Breaker | CBC-128, password/recovery/external protectors, 3 valid copies |

None of the valid metadata copies in these added public inputs has a TPM datum.
**Zero public PCR rows is therefore the checked result, not validation of another
TPM/PCR profile.** PCR 7/11 is still covered only by synthetic metadata in this
package; the two private original-image prefixes previously checked have 0/2/11.
No live PCR hash, TPM bank, Secure Boot state or recovery-product eligibility is
inferred from these public volumes.

## Independent checks

The public Dissect corpus is pinned at
[`0b3caf20c1e95136cb2eb4494303604e7629616b`](https://github.com/fox-it/dissect.fve/tree/0b3caf20c1e95136cb2eb4494303604e7629616b/tests/_data/bde).
Dissect's `Information` reader was run on the **original input**, separately from
this parser. Checks cover each referenced block's CRC validity; for valid copies,
volume UUID, method, current/next states, dataset creation FILETIME, VMK GUIDs,
protection codes and modification FILETIMEs agreed. Invalid-header exceptions
and CRC failures remain explicit negative observations. Vista's unsupported
semantics were not silently asserted against v2 expectations.

`public_reference_matrix.json` records pinned source URLs, compressed-source
SHA256s, expanded sizes and the independent reader's field values.
`public_ctf_gteksd.json` records all five original archive-part SHA256s, VHDX
identity, logical-image identity, partition offset and independent fields.
The normal unittest suite compares the byte-preserving fixture ranges against
those observations. It requires no independent-reader runtime dependency.

The dfVFS image is pinned at
[`917cefc9426d6ded2687d2b55164ded25b44fcb7`](https://github.com/log2timeline/dfvfs/blob/917cefc9426d6ded2687d2b55164ded25b44fcb7/test_data/bdetogo.raw).
Its three stored CRC32 values are `0x62bc388a`; their computed values are
`0xc66b05c5`. Dissect's information reader agrees with that failure. libbde
20260916 can open the image and report method/UUID/protectors despite those
checksums. This module deliberately keeps its CRC guard: no semantic findings
from those blocks. The fixture does **not** establish successful raw-reader
To Go discovery or semantic decoding of a checksum-valid To Go image.

## CTF extraction and complete report

Original author and data:
[GTekSD/BitLocker-CTF at db6caa8f7ddd6d659c2fd33417c64ee6b6c26ee1](https://github.com/GTekSD/BitLocker-CTF/tree/db6caa8f7ddd6d659c2fd33417c64ee6b6c26ee1).
The repository licenses the challenge under MIT; its licence is preserved with
the fixture subset. Five renamed `.partNN.rar` files were extracted with 7-Zip
26.04, with successful archive verification. `secret_data.vhdx` was read through
Dissect Hypervisor 3.21 as a 72,351,744-byte logical disk. This conversion reads
the allocated VHDX mapping, not an arbitrary concatenation or signature carve.
The BitLocker partition begins at byte 65,536 and spans 69,206,016 bytes.

| Object | SHA256 |
| --- | --- |
| Extracted VHDX, 71,303,168 bytes | `3ac487aaff4566a6840df95def57f60d1af30c3b8f4328028e41496b69850a4b` |
| Logical raw disk, 72,351,744 bytes | `94fecf4a2bd78eebe6780e4c0cb3bbdfa7fd94d5da0b045a0b615a8d3d239e86` |

The **complete raw disk**, with its MBR and partition offset, was passed to the
real DLEAPP CLI without a BitLocker key. The input SHA256 remained unchanged.
The compact HTML table, TSV column alignment and LAVA manifest/database counts
were checked again after reducing the output to one artifact. There is no event
timestamp and no timeline output. The source parser's independent field checks
above remain unchanged; their internal fields are no longer separate report tables.

| Input | Compact Key Protectors rows |
| --- | ---: |
| Reference matrix (14 volumes) | 19, including 3 diagnostic/no-protector rows |
| GTekSD CTF | 3 |
| Earlier Dissect XTS-256 | 1 |
| Synthetic profiles (2 volumes) | 4 |
| Synthetic partial capture | 2 |
| Synthetic protector combinations | 9 |

The additional synthetic case exercises eight standard protector codes, including
TPM+PIN and both startup-key combinations, and one unknown code. It uses fake
opaque key material and is not a Windows-produced example of every combination.

## Reproduce fixture checks

Install the repository's ordinary requirements. No downloads occur during tests:

```console
TZ=UTC PYTHONPATH=. python -m unittest admin.test.scripts.test_bitlocker_public_corpus -v
TZ=UTC python admin/test/scripts/run_test_cases.py --module bitlockerMetadata
```

The fixture README describes range creation and baseline recording. Public
fixture licences are separate from the independently implemented parser's MIT
licence. No complete CTF disk, VHDX or original archive is committed.

## Located but not executed

* **picoCTF 2025 Bitlocker-1 and Bitlocker-2:** official challenge-file URLs were
  located, but repeated full/range requests returned HTTP 502 in this environment.
  No bytes were available and neither case is counted as tested. Original links:
  [Bitlocker-1](https://challenge-files.picoctf.net/c_verbal_sleep/9e934e4d78276b12e27224dac16e50e6bbeae810367732eee4d5e38e6b2bb868/bitlocker-1.dd),
  [Bitlocker-2](https://challenge-files.picoctf.net/c_verbal_sleep/b22e1ca13c0b82bb85afe5ae162f6ecbdf5b651e364e6a2b57c9ad44ae0b3bfd/bitlocker-2.dd).
* **BelkaCTF 6 Bogus Bill:** the organizer provides a large supplementary archive
  containing a laptop E01 and an embedded BitLocker VHDX. The source and intended
  extraction are documented in the
  [official write-up](https://belkasoft.com/belkactf6-writeup) and
  [download page](https://belkasoft.com/belkactf6/info). It was not downloaded or
  tested in this run. No redistribution permission is inferred.
* **Arsenal Recon TechHive / NIST CFReDS:** a Windows-on-Arm image with BitLocker
  is listed by its creator and the [CFReDS portal](https://cfreds.nist.gov/).
  The full large dataset was not downloaded or tested in this run.
