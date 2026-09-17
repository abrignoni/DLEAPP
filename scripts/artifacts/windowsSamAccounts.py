"""Windows SAM local user account parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange Windows.Forensics.SAM artifact and the
RegRipper samparse plugin; this reads the SAM hive's on-disk structure directly
with python-registry.

Each local account lives under SAM\\Domains\\Account\\Users\\<RID> in the SAM
hive. Two binary values describe it: F (a fixed struct of account-control flags,
the RID, and the last-login, last-password-change, account-expires and
last-incorrect-password FILETIMEs, plus the logon and failed-logon counts) and V
(a header table of offset/length pairs pointing at the username, full name and
comment strings). The F and V field offsets below are taken verbatim from two
independent implementations that agree on them, cited in the notes; no offset is
guessed.

The SAM F record carries no account-creation timestamp, so none is reported.
"""

import struct
from datetime import datetime, timedelta, timezone

try:
    from Registry import Registry
except ImportError:
    Registry = None

from scripts.ilapfuncs import artifact_processor, logfunc

# The local accounts sit under this path from the SAM hive root.
_USERS_PATH = "SAM\\Domains\\Account\\Users"

# Account-control (ACB) bit meanings, from RegRipper samparse's %acb_flags map.
# Reported as stored (the raw value in hex) alongside these sourced labels; any
# bit outside this map is appended as raw hex rather than dropped or named.
_ACB_FLAGS = (
    (0x0001, "Account Disabled"),
    (0x0002, "Home directory required"),
    (0x0004, "Password not required"),
    (0x0008, "Temporary duplicate account"),
    (0x0010, "Normal user account"),
    (0x0020, "MNS logon user account"),
    (0x0040, "Interdomain trust account"),
    (0x0080, "Workstation trust account"),
    (0x0100, "Server trust account"),
    (0x0200, "Password does not expire"),
    (0x0400, "Account auto locked"),
)
_ACB_KNOWN = 0x07FF  # OR of every mapped bit above

__artifacts_v2__ = {
    "samLocalAccounts": {
        "name": "SAM Local User Accounts",
        "description": "Local user accounts enumerated from the SAM registry "
                       "hive, with each account's last logon, last password "
                       "change and account-control flags as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-17",
        "last_update_date": "2026-09-17",
        "requirements": "python-registry",
        "category": "Windows",
        "notes": "Read from the SAM hive, named in the report's located-at line. One row per "
                 "local account under SAM\\Domains\\Account\\Users. RID is the "
                 "account's relative identifier, taken from its registry subkey "
                 "name (hexadecimal) as a decimal number; the built-in accounts "
                 "are Administrator 500, Guest 501, DefaultAccount 503 and "
                 "WDAGUtilityAccount 504, and locally created users start at "
                 "1000. Username, Full Name and User Comment are decoded from "
                 "the account's V value (a header of offset and length pairs "
                 "into a UTF-16 string area); Full Name and User Comment are "
                 "blank on accounts that set neither, which is common for the "
                 "built-in accounts other than their shipped descriptions. "
                 "Account Flags is the account-control value from the F value "
                 "shown as stored in hexadecimal with the flag names that are "
                 "set; a disabled account carries Account Disabled and a normal "
                 "enabled account carries Normal user account. Last Login (UTC), "
                 "Last Password Change (UTC), Last Incorrect Password (UTC) and "
                 "Account Expires (UTC) are Windows FILETIMEs from the F value; "
                 "each is shown blank when the stored value is zero or a "
                 "never-expires sentinel, so a blank Last Login means the SAM "
                 "hive recorded no last-logon time for that account and a "
                 "blank Account Expires means the account is set never to "
                 "expire. Login Count and Failed Login Count are the logon and "
                 "failed-logon counters stored in the account's F record; a "
                 "non-zero Login Count is the count the SAM hive stored, not "
                 "proof of who was at the keyboard. The SAM logon count and "
                 "last-logon time are not updated for every sign-in, so a zero "
                 "Login Count or a blank Last Login is not evidence the account "
                 "was never used; on one tested image an active account carried "
                 "a zero Login Count and no last-logon time. Only local "
                 "accounts are in the SAM hive; domain and Microsoft-account "
                 "sign-ins are not. The SAM F record carries "
                 "no account-creation timestamp, so none is reported. Reading "
                 "the hive needs the python-registry package; its .LOG1/.LOG2 "
                 "transaction logs are not replayed. Field offsets: Velocidex, "
                 "Windows.Forensics.SAM, https://github.com/Velocidex/velocirap"
                 "tor/blob/master/artifacts/definitions/Windows/Forensics/SAM."
                 "yaml ; and RegRipper samparse, https://github.com/keydet89/"
                 "RegRipper3.0/blob/master/plugins/samparse.pl (the two agree "
                 "on the F and V layouts and the account-control flag names).",
        "paths": ("*/Windows/System32/config/[Ss][Aa][Mm]",),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "users",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 6 rows: "
                              "Administrator 500, Guest 501, DefaultAccount 503, "
                              "WDAGUtilityAccount 504, IEUser 1000, sshd 1002",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 5 rows: built-in "
                                "500/501/503/504 and user borch 1001",
            "lonewolf_win10": "Windows 10 Education build 16299 | 5 rows: built-in "
                              "500/501/503/504 and user jcloudy 1001",
        },
    },
}


def _filetime_datetime(value):
    """A little-endian Windows FILETIME integer to a tz-aware UTC datetime.

    Zero (never set) and the never-expires sentinel (which overflows) return
    an empty string, so those cells are blank rather than a false 1601 or a
    year past the epoch.
    """
    if not value:
        return ""
    try:
        return datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=value / 10)
    except (OverflowError, ValueError, OSError):
        return ""


def _decode_acb(flags):
    """Account-control value as stored (hex) plus the sourced flag names set."""
    if flags is None:
        return ""
    labels = [label for bit, label in _ACB_FLAGS if flags & bit]
    extra = flags & ~_ACB_KNOWN
    if extra:
        labels.append("0x%04X" % extra)
    detail = ", ".join(labels) if labels else "none set"
    return "0x%04X (%s)" % (flags, detail)


def _f_fields(blob):
    """Decode the F value. Returns a dict, or None when the value is too short.

    Offsets (both cited implementations agree): last login 8, password last set
    24, account expires 32, last incorrect password 40, RID 48, account-control
    flags 56, failed logon count 64, logon count 66.
    """
    if not blob or len(blob) < 68:
        return None
    return {
        "last_login": struct.unpack_from("<Q", blob, 8)[0],
        "pwd_last_set": struct.unpack_from("<Q", blob, 24)[0],
        "acct_expires": struct.unpack_from("<Q", blob, 32)[0],
        "pwd_fail": struct.unpack_from("<Q", blob, 40)[0],
        "rid": struct.unpack_from("<I", blob, 48)[0],
        "acb": struct.unpack_from("<H", blob, 56)[0],
        "failed_count": struct.unpack_from("<H", blob, 64)[0],
        "login_count": struct.unpack_from("<H", blob, 66)[0],
    }


def _v_string(blob, off_pos, len_pos):
    """One UTF-16 string from the V value: offset at off_pos, length at len_pos.

    The header offsets are relative to 0xCC, the start of the V value's string
    area (both cited implementations use this base).
    """
    try:
        off = struct.unpack_from("<I", blob, off_pos)[0]
        length = struct.unpack_from("<I", blob, len_pos)[0]
    except struct.error:
        return ""
    start = 0xCC + off
    end = start + length
    if length <= 0 or start < 0 or end > len(blob):
        return ""
    return blob[start:end].decode("utf-16-le", "replace").rstrip("\x00")


def _v_strings(blob):
    """(username, full name, comment) from the V value, blanks when absent."""
    if not blob or len(blob) < 44:
        return "", "", ""
    return (_v_string(blob, 12, 16),   # username offset @12, length @16
            _v_string(blob, 24, 28),   # full name offset @24, length @28
            _v_string(blob, 36, 40))   # comment offset @36, length @40


def _read_value(key, name):
    """The raw bytes of a named value, or None when it is absent."""
    try:
        return key.value(name).value()
    except (Registry.RegistryValueNotFoundException, AttributeError):
        return None


def _iter_accounts(reg):
    """Yield (rid, username, fullname, comment, f_fields) per local account."""
    try:
        users = reg.open(_USERS_PATH)
    except Registry.RegistryKeyNotFoundException:
        return
    for rid_key in users.subkeys():
        name = rid_key.name()
        try:
            rid = int(name, 16)          # skips the Names subkey (not hex)
        except ValueError:
            continue
        username, fullname, comment = _v_strings(_read_value(rid_key, "V"))
        f_fields = _f_fields(_read_value(rid_key, "F"))
        yield rid, username, fullname, comment, f_fields


@artifact_processor
def samLocalAccounts(context):
    data_headers = ('Username', 'RID', 'Full Name', 'User Comment', 'Account Flags',
                    ('Last Login (UTC)', 'datetime'),
                    ('Last Password Change (UTC)', 'datetime'),
                    ('Last Incorrect Password (UTC)', 'datetime'),
                    ('Account Expires (UTC)', 'datetime'),
                    'Login Count', 'Failed Login Count')
    data_list = []
    sources = []
    if Registry is None:
        logfunc('SAM local accounts: the python-registry package is not installed')
        return data_headers, data_list, ''

    for source in [str(f) for f in context.get_files_found()
                   if str(f).lower().endswith('sam')]:
        relative_source = context.get_relative_path(source)
        rows_here = 0
        try:
            reg = Registry.Registry(source)
            for rid, username, fullname, comment, ff in _iter_accounts(reg):
                if ff is None:
                    data_list.append((username, rid, fullname, comment, '',
                                      '', '', '', '', '', ''))
                else:
                    data_list.append((
                        username, rid, fullname, comment, _decode_acb(ff['acb']),
                        _filetime_datetime(ff['last_login']),
                        _filetime_datetime(ff['pwd_last_set']),
                        _filetime_datetime(ff['pwd_fail']),
                        _filetime_datetime(ff['acct_expires']),
                        ff['login_count'], ff['failed_count']))
                rows_here += 1
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'SAM local accounts: could not read {relative_source}: {exc}')
            continue
        if rows_here:
            sources.append(source)

    return data_headers, data_list, "\n".join(sources)
