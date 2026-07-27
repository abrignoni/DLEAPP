# Why DLEAPP does not recover a Signal key from a login keychain

A Signal Desktop profile on a current build stores its database key as
`encryptedKey` in `config.json`, wrapped by the OS credential store. On macOS
that store is the login keychain, and the item is a generic password under the
service `Signal Safe Storage`.

The obvious dead-box move is to read that item straight out of a
`login.keychain-db` given the account's login password. DLEAPP briefly did this
and the code was removed. This note records why, so it is not re-added on the
reasonable-sounding assumption that a login password unlocks a login keychain.

## On current macOS it does not

Tested on a macOS 26 host against three independent `login.keychain-db` files
(`blobVersion 0x200`), none of which is opened by its account's login password:

- A throwaway local account, created fresh, its password never changed.
  `dscl . -authonly <user> <password>` returns 0 — the string really is that
  account's current login password.
- macOS itself rejects that same password on the account's `login.keychain-db`:
  `SecKeychainUnlock` returns `-25293`, "the passphrase you entered is not
  correct", tested against a copy the logged-in session does not auto-unlock.
- `Keychain Access → Reset Default Keychains`, which recreates the login
  keychain, produced another `0x200` file that also rejects the login password.

So on current macOS the login keychain is encrypted with something other than
the account login password from creation onward — not only after a password
reset. The likely mechanism, that macOS keys the keychain with a system-managed
secret released through the SecureToken/login chain so the login password
unlocks a *stash* rather than the keychain, is a hypothesis; the divergence
itself is proven. The key-derivation parameters are not the issue: Apple's
`DatabaseCryptoCore::deriveDbMasterKey` uses PBKDF2-HMAC-SHA1, 1000 iterations,
a 24-byte key, unconditionally, and a clean-room reader matching that opened
every keychain built with `security create-keychain` (`0x100`). `0x200` gates
only the blob's verification algorithm, not derivation.

The path therefore failed on exactly the systems that use `encryptedKey`, and
its failure was easy to misread as a wrong password. Offering it invited an
examiner to spend effort on an input that cannot work.

## Two traps for anyone re-investigating this

Both were hit during the original work and produced confident wrong conclusions.

1. **No `security` subcommand validates a keychain password against the current
   session's own keychain.** `unlock-keychain -p`, `set-keychain-password -o`
   and friends succeed for *any* password against a copy, because securityd
   auto-unlocks it from the session. A *foreign* account's keychain is not
   auto-unlocked, so it can be tested there — except that `unlock-keychain -p ''`
   (empty) still succeeds even on a real-passworded keychain, so only non-empty
   wrong passwords are a valid check.

2. **PKCS#7 padding validation is not proof of a correct key.** A wrong 3DES key
   yields valid padding about 1 time in 256, deterministically for a fixed salt
   and password, so a false positive reproduces on every run. The sound oracle
   is how many of the keychain's symmetric keys the candidate database key
   unwraps — essentially all, or none.

## What DLEAPP does instead

The three key paths that work dead-box are kept:

- the plaintext `key` an older `config.json` carries — no credential at all;
- a 64-character database key supplied directly;
- the `Signal Safe Storage` credential supplied directly (`--signal-key`, the
  GUI's Signal key dialog, or a `signal_safe_storage.txt` file beside the
  extraction), captured from the running host.

Recovering a modern login keychain offline is not impossible — it requires the
actual keychain secret, reachable through the FileVault/SecureToken key chain an
examiner already unlocks to read the disk — but that is the domain of a
full-disk forensic suite, not a lightweight profile reader.
