# BitLocker protector fixtures

One small ZIP per case feeds the single `bitlockerKeyProtectors` artifact. The
compact report collapses matching copy observations within each volume and keeps
partial/differing metadata as Status text. Six current baselines cover:

* `casesynthetic_profiles`: two fake volumes, PCR 0/2/11 and 7/11, 4 rows.
* `casesynthetic_partial`: CRC failure, a partial valid copy, missing third copy
  and an unknown datum; 2 rows.
* `casesynthetic_protectors`: eight known codes including TPM+PIN/startup-key
  combinations, plus unknown 0x1234; 9 rows. Fake TPM/key payloads only.
* `casepublic_dissect_xts256`: exact public Dissect XTS-256 ranges; 1 row.
* `casepublic_reference_matrix`: 13 more Dissect inputs plus dfVFS To Go;
  19 rows including diagnostics for Vista, failed CRCs and no recorded protector.
* `casepublic_ctf_gteksd`: exact ranges from the GTekSD CTF partition; 3 rows.

No private data is included. The synthetic generator is
`admin/test/scripts/bitlocker_fixture.py`. Public source URLs, compressed-file
hashes, independent field observations and sizes are recorded in
`public_reference_matrix.json` and `public_ctf_gteksd.json`. These JSON files are
fixture documentation, not evidence files fed to the artifact.

Dissect source commit: `0b3caf20c1e95136cb2eb4494303604e7629616b`.
The earlier XTS-256 gzip SHA256 is
`908e7ca610ac9c777cf35d069ef9d457b1734f2bedb4f6a797b9e28a83517b42`.
Its expanded size is 51,032,064 bytes. Only the 512-byte header and three 64 KiB
metadata ranges are included. GNU AGPL v3 is preserved in
`LICENSE-Dissect-FVE-test-data.txt`; dfVFS Apache-2.0 in
`LICENSE-dfvfs-test-data.txt`; GTekSD MIT in `LICENSE-GTekSD-CTF.txt`.
The independently implemented parser uses the repository's MIT licence.

Original-image provenance, limits and independent checks are described in
`admin/docs/bitlocker_public_validation.md`. No public TPM profile is established
by the password/recovery/external-key inputs. The combination fixture only
validates structural decoding and labels, not key derivation or unsealing.

```console
TZ=UTC python admin/test/scripts/test_module.py bitlockerMetadata -a all -c all --allow-empty
TZ=UTC python admin/test/scripts/run_test_cases.py --module bitlockerMetadata
```
