# Validating the offline macOS keychain path

`scripts/macos_keychain.py` recovers a generic-password item from a
`login.keychain-db` given the account's login password. That is the dead-box
route to an Electron app's `safeStorage` credential, and for Signal it is what
`scripts/signal_desktop.py` uses when the examiner supplies a login password
instead of the credential itself.

**Status: unverified against a system-created login keychain.** The derivation is
confirmed from Apple's source, and the table walk, key unwrap and item decrypt
are tested against keychains that `security create-keychain` writes
(`admin/test/scripts/test_macos_keychain.py`). What has never been exercised is a
keychain that macOS itself created at first login. This document is how to build
one and close that gap.

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

## Why the obvious test case does not work

The login keychain on the machine this was developed on is not opened by its
account password. That is not a fault: a login keychain keeps its **old**
password when the account password is reset through Apple ID or by an
administrator, and macOS goes on unlocking it from the stashed session key, so
nothing on a live host reveals the divergence.

This has a sharp corollary. **No `security` subcommand can validate a keychain
password on a live host.** `unlock-keychain -p`, `set-keychain-password -o` and
friends all return success for *any* password — empty string included — against
a copy of the login keychain, because securityd auto-unlocks it. Do not build a
check on one; an earlier investigation did, and spent a day chasing a bug that
did not exist.

The only trustworthy oracle is **how many of the keychain's symmetric keys the
recovered database key unwraps**. A correct key opens essentially all of them, a
wrong one opens none. Padding validation is not enough on its own: a wrong 3DES
key produces valid PKCS#7 padding about 1 time in 256, and because the salt and
password are fixed, that false positive reproduces on every run and reads
convincingly like a finding.

So the test case has to be a login keychain whose password is **known to work**,
which means one created fresh and never subjected to a password reset.

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

## Option A — a second local user account (fast)

About five minutes, and it produces a genuine system-created login keychain.
Needs an administrator password, so run it yourself rather than delegating it.

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

1. Create the VM and complete Setup Assistant. **Set a local account password
   you choose and never change it, and skip Apple ID sign-in** — an Apple ID
   password reset is exactly the event that desynchronises a login keychain.
2. Confirm the keychain exists and note its format:

   ```bash
   ls -l ~/Library/Keychains/login.keychain-db
   ```

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
