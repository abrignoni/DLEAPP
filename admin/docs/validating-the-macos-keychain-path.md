# Validating the offline macOS keychain path

`scripts/macos_keychain.py` recovers a generic-password item from a
`login.keychain-db` given **the keychain's password**. That is the dead-box
route to an Electron app's `safeStorage` credential, and for Signal it is what
`scripts/signal_desktop.py` uses when the examiner supplies that password
instead of the credential itself.

Read "the keychain's password", not "the account's login password". They are the
same on older macOS, and the interface invites you to assume they always are.
On current macOS they frequently are not — see the finding below, which is the
single most important thing on this page.

## Finding: on macOS 26 the login password does not open the login keychain

Established 2026-07-27 against three independent `0x200` login keychains on a
macOS 26 host. None of them is unlocked by its account's login password, and one
case is airtight:

- A throwaway local account was created fresh and its password never changed.
- `dscl . -authonly <user> <password>` returns 0 — proof the string really is
  that account's current login password.
- macOS itself rejects that same password on the account's `login.keychain-db`
  (`SecKeychainUnlock` → `-25293`, "the passphrase you entered is not correct"),
  tested against a copy that the logged-in session does not auto-unlock.
- `Keychain Access → Reset Default Keychains`, which recreates the login
  keychain, produced another `0x200` file that also rejects the login password.

So the keychain is encrypted with something other than the login password from
creation onward, not only after a password reset. The most likely mechanism —
macOS keys the login keychain with a system-managed secret and releases it
through the SecureToken/login chain, so the login password unlocks the *stash*
rather than the keychain — is **a hypothesis, not confirmed from source**. The
divergence itself is proven; the reason is not.

**Consequence for the tool.** The reader is correct: it agrees with macOS on
every keychain tried, matches Apple's documented derivation, and parses the
`0x200` structure. What it cannot do is turn a modern login *password* into a
modern login *keychain* key, because on these systems the two are unrelated.
Supplying the actual keychain password still works; supplying the login password
often will not. This is not specific to DLEAPP — every tool built on the
"login password == keychain password" assumption meets the same ceiling on
current macOS.

**Status of the `0x200` decrypt path: still unverified end to end**, for the
plain reason that this host cannot produce a `0x200` keychain whose password is
known. The derivation is confirmed from Apple's source, the table walk, key
unwrap and item decrypt are tested against `security create-keychain` keychains
(`0x100`, `admin/test/scripts/test_macos_keychain.py`), the reader parses real
`0x200` structure, and its key-unwrap never branches on blob version. The one
untested combination is "correct keychain password applied to a `0x200` file".
The rest of this document is how to close that gap on a host where the login and
keychain passwords are still in sync — an older macOS, or a fresh VM where they
have not yet diverged.

## Why a normal test keychain is not enough

Every keychain that `security create-keychain` or `SecKeychainCreate` produces
carries `blobVersion` `0x00000100`. Every keychain macOS created for itself —
the login keychain, `metadata.keychain-db` — carries `0x00000200`
(`version_partition`, from OS X 10.11). The two cannot be told apart by the
tests we have, because nothing available to a test can produce the second kind.

The version gates which *verification* algorithm the blob decode uses, not the
key derivation, so it very likely does not matter here. "Very likely" is the
reason this document exists.

A convenient property: it is the *keychain file* that carries the version, not
the item. Adding an item to an existing login keychain leaves it `0x200`, so a
test item planted in a real login keychain exercises the real format.

## Verifying a candidate password without fooling yourself

You cannot trust a test case until you have confirmed the password actually
opens the keychain, and there are two independent traps in doing so.

**Trap 1: the logged-in session auto-unlocks its own keychain.** `security
unlock-keychain -p`, `set-keychain-password -o` and friends return success for
*any* password against a copy of the *current* user's login keychain, because
securityd auto-unlocks it from the session. An earlier investigation built its
whole diagnosis on this and chased a bug that did not exist. A keychain from a
*different* account, copied out and tested from your own session, is not
auto-unlocked, so there `security` is a valid oracle — with the next caveat.

**Trap 2: an empty password argument is not a test.** `unlock-keychain -p ''`
returns success even on a keychain keyed with a real, non-empty password —
`-p ''` falls back to a stashed/interactive unlock rather than trying the empty
string. Only **non-empty wrong passwords** exercise the check; those correctly
return `-25293`. When in doubt, use the reader itself as the tie-breaker:
`_database_key` feeds the password through PBKDF2 for real and refuses the empty
string, where the CLI accepts it.

**The strongest oracle is structural: how many of the keychain's symmetric keys
the recovered database key unwraps.** A correct key opens essentially all of
them, a wrong one opens none. Padding validation alone is not enough — a wrong
3DES key produces valid PKCS#7 padding about 1 time in 256, and because the salt
and password are fixed, that false positive reproduces on every run and reads
convincingly like a finding. This is what mislabelled SHA-256/10000 as the
answer once; do not repeat it.

So the test case has to be a login keychain whose password is **confirmed to
open it**, not merely believed to. On current macOS that is the hard part: see
the finding at the top of this page. Confirm with `dscl . -authonly` that the
string is the account password, then confirm *separately* that the same string
opens the keychain. If the first passes and the second fails, you have
reproduced the finding, not built a test case.

### Never create a test keychain named `login.keychain-db`

```bash
security create-keychain -p 'known-password' /tmp/scratch/login.keychain-db
```

That produces a keychain the supplied password does **not** open. Give the same
sequence any other basename and it opens immediately. The file is otherwise
identical — same size, same `blobVersion`, same record counts — so the symptom
is a key derivation that simply fails, which looks exactly like the bug this
document exists to rule out. `security` treats that basename as the user's login
keychain and does not key the new file with `-p`.

The reader itself does not care about the name: a byte-for-byte copy of a
working keychain renamed to `login.keychain-db` opens normally. The trap is only
in *creating* one, so it never affects a genuine login keychain copied out of an
image or a VM. It will bite anyone trying to fake a test case, which is why it is
written down here.

## Option A — a second local user account (fast, but verify before trusting)

About five minutes, and it produces a genuine system-created login keychain.
Needs an administrator password, so run it yourself rather than delegating it.

**On macOS 26 this was tried and the login keychain did not open with the
account password** — the fresh account's keychain diverged from creation, per
the finding above. Do not assume the account password will work; step 5 is
therefore not optional. If it fails, either the host is new enough to have this
behaviour (use an older macOS or a VM at an older version), or fall back to a
host where login and keychain passwords are still in sync.

1. System Settings, Users & Groups, add a user. Give it a password you choose
   and record it. Do not reset that password afterwards.
2. Log in as that user once. The login keychain is not created until first
   login.
3. Plant a known item, logged in as that user:

   ```bash
   security add-generic-password -s 'Signal Safe Storage' -a 'Signal' \
       -w 'test-credential-not-a-real-secret' ~/Library/Keychains/login.keychain-db
   ```

4. Copy `~/Library/Keychains/login.keychain-db` somewhere both accounts can
   reach, then log back into your own account.
5. Run the validation below.
6. Delete the account when finished.

Limitation: this validates the keychain reader, not Signal end to end, because
the account has no Signal profile. That is usually the right trade — the
keychain reader is the untested part, and the Signal artifacts are already
covered by the existing corpora.

## Option B — a macOS virtual machine (durable)

Slower, but it yields a reusable corpus containing no personal data, which can
be registered in `samples.json` and kept, and it can host a full Signal install.

### Getting macOS

Apple's licence permits running up to two additional copies of macOS in virtual
machines on a single Apple-branded computer, so a test VM on a Mac is within the
terms. Three ways to obtain the OS, in order of convenience:

1. **Let the hypervisor fetch it.** Parallels Desktop and UTM both offer to
   create a macOS VM by downloading Apple's official restore image for you. On
   Apple Silicon this pulls a `UniversalMac_*.ipsw` straight from Apple. Nothing
   to source manually, and it is the recommended route.
2. **Download the IPSW yourself.** Apple hosts the restore images; sites such as
   `ipsw.me` and `mrmacintosh.com` index the official Apple URLs. Verify you are
   downloading from an `apple.com` host. Point the hypervisor at the `.ipsw`.
3. **`softwareupdate`.** `softwareupdate --list-full-installers` and
   `--fetch-full-installer --full-installer-version <version>` retrieve the
   installer application from Apple. More useful on Intel hosts; Apple Silicon
   VM creation generally wants an IPSW.

Only Apple Silicon hosts can virtualise Apple Silicon macOS, and only Intel
hosts can virtualise Intel macOS. There is no cross-architecture option.

### Building the corpus

An Apple Silicon VM installs a *current* macOS, and current macOS is where the
login/keychain-password divergence was observed. Prefer a VM at an **older
macOS version** for this test — one old enough that the login keychain is still
keyed with the account password. If you must use a current version, treat step 2
as a gate: if the account password does not open the keychain there, this VM
cannot serve as a positive test case, only as another confirmation of the
finding.

1. Create the VM and complete Setup Assistant. **Set a local account password
   you choose and never change it, and skip Apple ID sign-in** — Apple ID
   sign-in and any later password reset both risk desynchronising the keychain.
2. Confirm the account password actually opens the keychain before trusting the
   VM. From your host, against a copy (so the guest session does not auto-unlock
   it), run the validation script below; `database key recovered` must be True.
   Do not skip this — a keychain the password does not open is not a test case.

3. Plant a known item, or install Signal Desktop and link it to a test account
   for a genuine `encryptedKey` profile:

   ```bash
   security add-generic-password -s 'Signal Safe Storage' -a 'Signal' \
       -w 'test-credential-not-a-real-secret' ~/Library/Keychains/login.keychain-db
   ```

4. Copy `~/Library/Keychains/login.keychain-db` out via a shared folder. If
   Signal was installed, take `~/Library/Application Support/Signal` too.
5. Record the account password with the corpus. A corpus whose password is lost
   is worth nothing — that is the whole point of this exercise.

## Running the validation

With the keychain file and its password:

```bash
python3 - <<'PY'
import struct, sys
sys.path.insert(0, '.')
from scripts import macos_keychain as mk

path = '/path/to/login.keychain-db'
password = 'the-password-you-set'

data = open(path, 'rb').read()
kc = mk._Keychain(data)
base = kc.db_blob()
common, = struct.unpack_from('> 8s', data, base)
print('blobVersion : 0x%08X' % struct.unpack('> I I', common)[1])

symkeys = len(list(kc.records(mk._RECORD_SYMMETRIC_KEY)))
db_key = mk._database_key(data, base, password)
print('database key recovered :', db_key is not None)
if db_key:
    print('keys unwrapped : %d / %d' % (len(mk._key_list(kc, db_key)), symkeys))
print('item recovered :',
      mk.find_generic_password(path, password, 'Signal Safe Storage'))
PY
```

Success looks like: `blobVersion : 0x00000200`, database key recovered, keys
unwrapped equal or nearly equal to the total, and the planted value returned.

**Anything less than "nearly all keys unwrapped" is a failure, even if a
database key came back.** That is the trap this whole document is about.

If it fails, the derivation is not the place to look — Apple's
`DatabaseCryptoCore::deriveDbMasterKey` is fixed at PBKDF2-HMAC-SHA1, 1000
rounds, 24 bytes, unconditional. Look at `_unwrap_key`, which is where the
`0x200` verification difference would surface.

## When it passes

- Add the keychain to `samples.json` with its password in the notes, and record
  the `blobVersion` so the coverage is visible.
- Extend `admin/test/scripts/test_macos_keychain.py` with a case that runs
  against the corpus when present and skips when it is not, in the manner of
  `TestLiveKeychainRoundTrip`.
- Drop the "Not covered" caveat from the Signal documentation.
