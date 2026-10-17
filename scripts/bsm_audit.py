"""A reader for BSM audit trails, the files macOS's auditd writes to /var/audit.

Author: @AlexisBrignoni, Claude.

The format is OpenBSM's. Every token layout here follows the reader praudit(1) is built
on, libbsm's bsm_io.c, at openbsm/openbsm commit 6230904e8b0c8d73339682ebe9173dd853436047:
the record framing in au_read_rec, the dispatch in au_fetch_tok and one fetch_*_tok
function per token type. Integers are big-endian (be16dec, be32dec, be64dec there);
addresses and ports are copied as stored, which is network byte order. The one token
OpenBSM does not read is Apple's identity token (0xed), whose layout is the writer's,
au_to_identity in xnu's bsd/security/audit/audit_bsm_token.c at
apple-oss-distributions/xnu commit f6217f891ac0bb64f3d375211650a4c1ff8ca1ea.

A trail is a run of records, each starting with a header token whose second field is the
record's byte count, plus file tokens standing alone between records. Reading stops, as
au_read_rec does, at the first byte that starts neither, or at a record that runs past
the end of the file; what is left is counted, never read. Inside a record a token is read
only within the record's byte count. A token of a type this reader does not know is
skipped to where the trailer would start, as fetch_invalid_tok does, and counted; a token
that runs past the record ends the record's tokens, as praudit does, and is counted.

Nothing here opens a file. Callers hand in bytes.
"""

import re
import socket
import struct
from collections import Counter

# Token identifiers, audit_record.h (openbsm sys/bsm/audit_record.h lines 44-136).
AUT_OTHER_FILE32 = 0x11
AUT_TRAILER = 0x13
AUT_HEADER32 = 0x14
AUT_HEADER32_EX = 0x15
AUT_HEADER64 = 0x74
AUT_HEADER64_EX = 0x79
AUT_IDENTITY = 0xed
AUT_TRAILER_MAGIC = 0xb105
AUDIT_TRAILER_SIZE = 7
AU_IPV4 = 4
AU_IPV6 = 16
HEADERS = (AUT_HEADER32, AUT_HEADER32_EX, AUT_HEADER64, AUT_HEADER64_EX)

TOKEN_NAMES = {
    0x11: 'file', 0x13: 'trailer', 0x14: 'header', 0x15: 'header_ex', 0x21: 'data', 0x22: 'IPC',
    0x23: 'path', 0x24: 'subject', 0x26: 'process', 0x27: 'return', 0x28: 'text', 0x29: 'opaque',
    0x2a: 'ip addr', 0x2b: 'ip', 0x2c: 'ip port', 0x2d: 'argument', 0x2e: 'socket', 0x2f: 'sequence',
    0x32: 'IPC perm', 0x34: 'group', 0x38: 'priv', 0x39: 'use of privilege',
    0x3b: 'group', 0x3c: 'exec arg', 0x3d: 'exec env', 0x3e: 'attribute', 0x52: 'exit',
    0x60: 'zone', 0x71: 'argument', 0x72: 'return', 0x73: 'attribute', 0x74: 'header',
    0x75: 'subject', 0x77: 'process', 0x79: 'header_ex', 0x7a: 'subject_ex', 0x7b: 'process_ex',
    0x7c: 'subject_ex', 0x7d: 'process_ex', 0x7e: 'ip addr ex', 0x7f: 'socket', 0x80: 'socket-inet',
    0x81: 'socket-inet6', 0x82: 'socket-unix', 0x84: 'argument', 0x85: 'return', 0xed: 'identity',
}

# A record that could not be read past a token, and why: the counters the caller logs.
SHORT_TOKEN = 'tokens that ran past the end of their record (the rest of that record not read)'
UNKNOWN_TOKEN = 'tokens of a type not read here (skipped to the trailer)'
TRAILING = 'bytes after the last whole record, not read'
BAD_TRAILER = 'records whose trailer magic or byte count disagrees with the header'
NO_TRAILER = 'records with no trailer token'


class _Short(Exception):
    """A field ran past the end of its token's record."""


class _Cursor:
    def __init__(self, data, start, end):
        self.data = data
        self.pos = start
        self.end = end

    def take(self, size):
        if size < 0 or self.pos + size > self.end:
            raise _Short()
        chunk = self.data[self.pos:self.pos + size]
        self.pos += size
        return chunk

    def u8(self):
        return self.take(1)[0]

    def u16(self):
        return struct.unpack('>H', self.take(2))[0]

    def u32(self):
        return struct.unpack('>I', self.take(4))[0]

    def u64(self):
        return struct.unpack('>Q', self.take(8))[0]

    def cstring_until_nul(self):
        """Bytes up to and including the next NUL, bounded by the record (fetch_execarg_tok)."""
        nul = self.data.find(b'\x00', self.pos, self.end)
        if nul < 0:
            raise _Short()
        return self.take(nul + 1 - self.pos)


def text(raw):
    """A stored string as praudit prints it (print_string skips NUL bytes), decoded as UTF-8
    with any byte that is not shown as a backslash escape."""
    return raw.replace(b'\x00', b'').decode('utf-8', errors='backslashreplace')


def ipv4(raw):
    return '.'.join(str(b) for b in raw)


def ip_ex(kind, raw):
    if kind == AU_IPV4:
        return ipv4(raw[:4])
    if kind == AU_IPV6:
        return socket.inet_ntop(socket.AF_INET6, raw[:16])
    return ''


def signed32(value):
    return value - (1 << 32) if value & 0x80000000 else value


def _tid_ex(cur, wide):
    port = cur.u64() if wide else cur.u32()
    kind = cur.u32()
    if kind == AU_IPV4:
        addr = cur.take(4)
    elif kind == AU_IPV6:
        addr = cur.take(16)
    else:
        raise _Short()
    return port, ip_ex(kind, addr)


def _subject(cur, wide=False, ex=False):
    fields = {'auid': signed32(cur.u32()), 'euid': signed32(cur.u32()), 'egid': signed32(cur.u32()),
              'ruid': signed32(cur.u32()), 'rgid': signed32(cur.u32()), 'pid': cur.u32(), 'sid': cur.u32()}
    if ex:
        fields['port'], fields['addr'] = _tid_ex(cur, wide)
    else:
        fields['port'] = cur.u64() if wide else cur.u32()
        fields['addr'] = ipv4(cur.take(4))
    return fields


def _header(cur, tid):
    fields = {'size': cur.u32(), 'version': cur.u8(), 'event': cur.u16(), 'modifier': cur.u16()}
    if tid in (AUT_HEADER32_EX, AUT_HEADER64_EX):
        kind = cur.u32()
        # fetch_header32_ex_tok reads an address only for AU_IPv4 and AU_IPv6
        fields['host'] = ip_ex(kind, cur.take(4 if kind == AU_IPV4 else 16 if kind == AU_IPV6 else 0))
    wide = tid in (AUT_HEADER64, AUT_HEADER64_EX)
    fields['seconds'] = cur.u64() if wide else cur.u32()
    fields['msec'] = cur.u64() if wide else cur.u32()
    return fields


def _counted(cur):
    return text(cur.take(cur.u16()))


def _arg(cur, wide):
    number = cur.u8()
    value = cur.u64() if wide else cur.u32()
    return {'number': number, 'value': value, 'desc': _counted(cur)}


def _strings(cur):
    count = cur.u32()
    return {'strings': [text(cur.cstring_until_nul()) for _ in range(count)]}


def _attr(cur, wide):
    fields = {'mode': cur.u32(), 'uid': signed32(cur.u32()), 'gid': signed32(cur.u32()), 'fsid': cur.u32(),
              'nid': cur.u64()}
    fields['dev'] = cur.u64() if wide else cur.u32()
    return fields


def _identity(cur):
    # au_to_identity: signer type, then counted signing id (count includes its NUL) and a
    # truncated flag, the same for the team id, then a counted cdhash
    fields = {'signer_type': cur.u32(), 'signing_id': _counted(cur), 'signing_id_truncated': cur.u8()}
    fields['team_id'] = _counted(cur)
    fields['team_id_truncated'] = cur.u8()
    fields['cdhash'] = cur.take(cur.u16()).hex()
    return fields


def _arbitrary(cur):
    how, unit, count = cur.u8(), cur.u8(), cur.u8()
    size = {0: 1, 1: 2, 2: 4, 3: 8}.get(unit)
    if size is None:
        raise _Short()
    return {'print_as': how, 'unit': unit, 'count': count, 'data': cur.take(size * count).hex()}


def _socket_ex(cur):
    fields = {'domain': cur.u16(), 'type': cur.u16()}
    kind = cur.u16()
    if kind not in (AU_IPV4, AU_IPV6):
        raise _Short()
    width = 4 if kind == AU_IPV4 else 16
    fields['local_port'] = struct.unpack('>H', cur.take(2))[0]
    fields['local_addr'] = ip_ex(kind, cur.take(width))
    fields['remote_port'] = struct.unpack('>H', cur.take(2))[0]
    fields['remote_addr'] = ip_ex(kind, cur.take(width))
    return fields


def _sock_unix(cur):
    family = cur.u16()
    # fetch_sock_unix_tok: the path up to and including a NUL, at most AU_UNIX_PATH_MAX (108) bytes
    end = min(cur.end, cur.pos + 108)
    nul = cur.data.find(b'\x00', cur.pos, end)
    return {'family': family, 'path': text(cur.take((nul + 1 if nul >= 0 else end) - cur.pos))}


def _process(cur, wide=False, ex=False):
    return _subject(cur, wide, ex)


def _in_addr_ex(cur):
    kind = cur.u32()
    if kind not in (AU_IPV4, AU_IPV6):
        raise _Short()
    return {'addr': ip_ex(kind, cur.take(4 if kind == AU_IPV4 else 16))}


_READERS = {
    0x11: lambda c: {'seconds': c.u32(), 'msec': c.u32(), 'name': _counted(c)},
    0x13: lambda c: {'magic': c.u16(), 'count': c.u32()},
    0x21: _arbitrary,
    0x22: lambda c: {'type': c.u8(), 'id': c.u32()},
    0x23: lambda c: {'path': _counted(c)},
    0x24: _subject,
    0x26: _process,
    0x27: lambda c: {'status': c.u8(), 'value': c.u32()},
    0x28: lambda c: {'text': _counted(c)},
    0x29: lambda c: {'data': c.take(c.u16()).hex()},
    0x2a: lambda c: {'addr': ipv4(c.take(4))},
    0x2b: lambda c: {'header': c.take(20).hex()},
    0x2c: lambda c: {'port': struct.unpack('>H', c.take(2))[0]},
    0x2d: lambda c: _arg(c, False),
    0x2e: lambda c: {'type': c.u16(), 'local_port': struct.unpack('>H', c.take(2))[0],
                     'local_addr': ipv4(c.take(4)), 'remote_port': struct.unpack('>H', c.take(2))[0],
                     'remote_addr': ipv4(c.take(4))},
    0x2f: lambda c: {'sequence': c.u32()},
    0x32: lambda c: {'uid': c.u32(), 'gid': c.u32(), 'puid': c.u32(), 'pgid': c.u32(), 'mode': c.u32(),
                     'seq': c.u32(), 'key': c.u32()},
    0x38: lambda c: {'set_type': _counted(c), 'set': _counted(c)},
    0x39: lambda c: {'success': c.u8(), 'privilege': _counted(c)},
    0x3b: lambda c: {'groups': [c.u32() for _ in range(c.u16())]},
    0x3c: _strings,
    0x3d: _strings,
    0x3e: lambda c: _attr(c, False),
    0x52: lambda c: {'status': c.u32(), 'value': c.u32()},
    0x60: lambda c: {'zone': _counted(c)},
    0x71: lambda c: _arg(c, True),
    0x72: lambda c: {'status': c.u8(), 'value': c.u64()},
    0x73: lambda c: _attr(c, True),
    0x75: lambda c: _subject(c, wide=True),
    0x77: lambda c: _process(c, wide=True),
    0x7a: lambda c: _subject(c, ex=True),
    0x7b: lambda c: _process(c, ex=True),
    0x7c: lambda c: _subject(c, wide=True, ex=True),
    0x7d: lambda c: _process(c, wide=True, ex=True),
    0x7e: _in_addr_ex,
    0x7f: _socket_ex,
    0x80: lambda c: {'family': c.u16(), 'port': struct.unpack('>H', c.take(2))[0], 'addr': ipv4(c.take(4))},
    0x81: lambda c: {'family': c.u16(), 'port': struct.unpack('>H', c.take(2))[0],
                     'addr': ip_ex(AU_IPV6, c.take(16))},
    0x82: _sock_unix,
    0x84: lambda c: {'number': c.u8(), 'uuid': c.take(16).hex(), 'desc': _counted(c)},
    0x85: lambda c: {'number': c.u8(), 'uuid': c.take(16).hex(), 'desc': _counted(c)},
    0xed: _identity,
}


def _tokens(data, start, end, counts):
    """The tokens of one record, data[start:end], as (id, fields) pairs."""
    out = []
    pos = start
    while pos < end:
        tid = data[pos]
        cur = _Cursor(data, pos + 1, end)
        if tid in HEADERS:
            reader = lambda c, t=tid: _header(c, t)
        else:
            reader = _READERS.get(tid)
        if reader is None:
            # fetch_invalid_tok: everything up to where the trailer would start
            skip = end - (pos + 1 + AUDIT_TRAILER_SIZE)
            if skip <= 0:
                counts[SHORT_TOKEN] += 1
                break
            counts[UNKNOWN_TOKEN] += 1
            out.append((tid, {'skipped_bytes': skip}))
            pos = pos + 1 + skip
            continue
        try:
            fields = reader(cur)
        except _Short:
            counts[SHORT_TOKEN] += 1
            break
        out.append((tid, fields))
        pos = cur.pos
    return out


def read_trail(data, counts=None):
    """Every record and stand-alone file token in one trail, in file order.

    Returns a list of dicts: 'offset' (of the record in the file), 'size' (bytes) and
    'tokens', a list of (token id, fields). ``counts`` (a Counter) gathers what was not
    read and why.
    """
    counts = Counter() if counts is None else counts
    records = []
    pos = 0
    size = len(data)
    while pos < size:
        tid = data[pos]
        if tid in HEADERS:
            if pos + 5 > size:
                break
            length = struct.unpack('>I', data[pos + 1:pos + 5])[0]
            if length < 5 or pos + length > size:
                break
        elif tid == AUT_OTHER_FILE32:
            if pos + 11 > size:
                break
            length = 11 + struct.unpack('>H', data[pos + 9:pos + 11])[0]
            if pos + length > size:
                break
        else:
            break
        tokens = _tokens(data, pos, pos + length, counts)
        if tid in HEADERS:
            trailers = [fields for token, fields in tokens if token == AUT_TRAILER]
            if not trailers:
                counts[NO_TRAILER] += 1
            elif trailers[-1]['magic'] != AUT_TRAILER_MAGIC or trailers[-1]['count'] != length:
                counts[BAD_TRAILER] += 1
        records.append({'offset': pos, 'size': length, 'tokens': tokens})
        pos += length
    if pos < size:
        counts[TRAILING] += size - pos
    return records


def parse_event_table(raw):
    """{event number: description} from an audit_event file's bytes, read the way libbsm's
    getauevnum_r reads it (bsm_event.c): fields split on ':' with empty fields skipped
    (strtok_r), the number taken as atoi takes it, and the first line for a number kept."""
    table = {}
    for line in raw.decode('utf-8', errors='backslashreplace').split('\n'):
        parts = [part for part in line.split(':') if part]
        if len(parts) < 2:
            continue
        match = re.match(r'\s*[+-]?\d+', parts[0])
        if not match:
            continue
        table.setdefault(int(match.group()) & 0xFFFF, parts[2] if len(parts) > 2 else '')
    return table


# Event descriptions from etc/audit_event in apple-oss-distributions/OpenBSM at commit
# bb0681420e99d447f466ba70d38589213bb69fea (tag OpenBSM-21), read with parse_event_table.
_EVENT_TABLE_TEXT = """\
0:AUE_NULL:indir system call
1:AUE_EXIT:exit(2)
2:AUE_FORK:fork(2)
3:AUE_OPEN:open(2) - attr only
4:AUE_CREAT:creat(2)
5:AUE_LINK:link(2)
6:AUE_UNLINK:unlink(2)
7:AUE_EXEC:exec(2)
8:AUE_CHDIR:chdir(2)
9:AUE_MKNOD:mknod(2)
10:AUE_CHMOD:chmod(2)
11:AUE_CHOWN:chown(2)
12:AUE_UMOUNT:umount(2) - old version
13:AUE_JUNK:junk
14:AUE_ACCESS:access(2)
15:AUE_KILL:kill(2)
16:AUE_STAT:stat(2)
17:AUE_LSTAT:lstat(2)
18:AUE_ACCT:acct(2)
19:AUE_MCTL:mctl(2)
20:AUE_REBOOT:reboot(2)
21:AUE_SYMLINK:symlink(2)
22:AUE_READLINK:readlink(2)
23:AUE_EXECVE:execve(2)
24:AUE_CHROOT:chroot(2)
25:AUE_VFORK:vfork(2)
26:AUE_SETGROUPS:setgroups(2)
27:AUE_SETPGRP:setpgrp(2)
28:AUE_SWAPON:swapon(2)
29:AUE_SETHOSTNAME:sethostname(2)
30:AUE_FCNTL:fcntl(2)
31:AUE_SETPRIORITY:setpriority(2)
32:AUE_CONNECT:connect(2)
33:AUE_ACCEPT:accept(2)
34:AUE_BIND:bind(2)
35:AUE_SETSOCKOPT:setsockopt(2)
36:AUE_VTRACE:vtrace(2)
37:AUE_SETTIMEOFDAY:settimeofday(2)
38:AUE_FCHOWN:fchown(2)
39:AUE_FCHMOD:fchmod(2)
40:AUE_SETREUID:setreuid(2)
41:AUE_SETREGID:setregid(2)
42:AUE_RENAME:rename(2)
43:AUE_TRUNCATE:truncate(2)
44:AUE_FTRUNCATE:ftruncate(2)
45:AUE_FLOCK:flock(2)
46:AUE_SHUTDOWN:shutdown(2)
47:AUE_MKDIR:mkdir(2)
48:AUE_RMDIR:rmdir(2)
49:AUE_UTIMES:utimes(2)
50:AUE_ADJTIME:adjtime(2)
51:AUE_SETRLIMIT:setrlimit(2)
52:AUE_KILLPG:killpg(2)
53:AUE_NFS_SVC:nfs_svc(2)
54:AUE_STATFS:statfs(2)
55:AUE_FSTATFS:fstatfs(2)
56:AUE_UNMOUNT:unmount(2)
57:AUE_ASYNC_DAEMON:async_daemon(2)
58:AUE_NFS_GETFH:nfs_getfh(2)
59:AUE_SETDOMAINNAME:setdomainname(2)
60:AUE_QUOTACTL:quotactl(2)
61:AUE_EXPORTFS:exportfs(2)
62:AUE_MOUNT:mount(2)
63:AUE_SEMSYS:semsys(2)
64:AUE_MSGSYS:msgsys(2)
65:AUE_SHMSYS:shmsys(2)
66:AUE_BSMSYS:bsmsys(2)
67:AUE_RFSSYS:rfssys(2)
68:AUE_FCHDIR:fchdir(2)
69:AUE_FCHROOT:fchroot(2)
70:AUE_VPIXSYS:vpixsys(2)
71:AUE_PATHCONF:pathconf(2)
72:AUE_OPEN_R:open(2) - read
73:AUE_OPEN_RC:open(2) - read,creat
74:AUE_OPEN_RT:open(2) - read,trunc
75:AUE_OPEN_RTC:open(2) - read,creat,trunc
76:AUE_OPEN_W:open(2) - write
77:AUE_OPEN_WC:open(2) - write,creat
78:AUE_OPEN_WT:open(2) - write,trunc
79:AUE_OPEN_WTC:open(2) - write,creat,trunc
80:AUE_OPEN_RW:open(2) - read,write
81:AUE_OPEN_RWC:open(2) - read,write,creat
82:AUE_OPEN_RWT:open(2) - read,write,trunc
83:AUE_OPEN_RWTC:open(2) - read,write,creat,trunc
84:AUE_MSGCTL:msgctl(2) - illegal command
85:AUE_MSGCTL_RMID:msgctl(2) - IPC_RMID command
86:AUE_MSGCTL_SET:msgctl(2) - IPC_SET command
87:AUE_MSGCTL_STAT:msgctl(2) - IPC_STAT command
88:AUE_MSGGET:msgget(2)
89:AUE_MSGRCV:msgrcv(2)
90:AUE_MSGSND:msgsnd(2)
91:AUE_SHMCTL:shmctl(2) - illegal command
92:AUE_SHMCTL_RMID:shmctl(2) - IPC_RMID command
93:AUE_SHMCTL_SET:shmctl(2) - IPC_SET command
94:AUE_SHMCTL_STAT:shmctl(2) - IPC_STAT command
95:AUE_SHMGET:shmget(2)
96:AUE_SHMAT:shmat(2)
97:AUE_SHMDT:shmdt(2)
98:AUE_SEMCTL:semctl(2) - illegal command
99:AUE_SEMCTL_RMID:semctl(2) - IPC_RMID command
100:AUE_SEMCTL_SET:semctl(2) - IPC_SET command
101:AUE_SEMCTL_STAT:semctl(2) - IPC_STAT command
102:AUE_SEMCTL_GETNCNT:semctl(2) - GETNCNT command
103:AUE_SEMCTL_GETPID:semctl(2) - GETPID command
104:AUE_SEMCTL_GETVAL:semctl(2) - GETVAL command
105:AUE_SEMCTL_GETALL:semctl(2) - GETALL command
106:AUE_SEMCTL_GETZCNT:semctl(2) - GETZCNT command
107:AUE_SEMCTL_SETVAL:semctl(2) - SETVAL command
108:AUE_SEMCTL_SETALL:semctl(2) - SETALL command
109:AUE_SEMGET:semget(2)
110:AUE_SEMOP:semop(2)
111:AUE_CORE:process dumped core
112:AUE_CLOSE:close(2)
113:AUE_SYSTEMBOOT:system booted
114:AUE_ASYNC_DAEMON_EXIT:async_daemon(2) exited
115:AUE_NFSSVC_EXIT:nfssvc(2) exited
128:AUE_WRITEL:writel(2)
129:AUE_WRITEVL:writevl(2)
130:AUE_GETAUID:getauid(2)
131:AUE_SETAUID:setauid(2)
132:AUE_GETAUDIT:getaudit(2)
133:AUE_SETAUDIT:setaudit(2)
134:AUE_GETUSERAUDIT:getuseraudit(2)
135:AUE_SETUSERAUDIT:setuseraudit(2)
136:AUE_AUDITSVC:auditsvc(2)
137:AUE_AUDITUSER:audituser(2)
138:AUE_AUDITON:auditon(2)
139:AUE_AUDITON_GTERMID:auditon(2) - GETTERMID command
140:AUE_AUDITON_STERMID:auditon(2) - SETTERMID command
141:AUE_AUDITON_GPOLICY:auditon(2) - GPOLICY command
142:AUE_AUDITON_SPOLICY:auditon(2) - SPOLICY command
143:AUE_AUDITON_GESTATE:auditon(2) - GESTATE command
144:AUE_AUDITON_SESTATE:auditon(2) - SESTATE command
145:AUE_AUDITON_GQCTRL:auditon(2) - GQCTRL command
146:AUE_AUDITON_SQCTRL:auditon(2) - SQCTRL command
147:AUE_GETKERNSTATE:getkernstate(2)
148:AUE_SETKERNSTATE:setkernstate(2)
149:AUE_GETPORTAUDIT:getportaudit(2)
150:AUE_AUDITSTAT:auditstat(2)
151:AUE_REVOKE:revoke(2)
152:AUE_MAC:Solaris AUE_MAC
153:AUE_ENTERPROM:enter prom
154:AUE_EXITPROM:exit prom
155:AUE_IFLOAT:Solaris AUE_IFLOAT
156:AUE_PFLOAT:Solaris AUE_PFLOAT
157:AUE_UPRIV:Solaris AUE_UPRIV
158:AUE_IOCTL:ioctl(2)
173:AUE_ONESIDE:one-sided session record
174:AUE_MSGGETL:msggetl(2)
175:AUE_MSGRCVL:msgrcvl(2)
176:AUE_MSGSNDL:msgsndl(2)
177:AUE_SEMGETL:semgetl(2)
178:AUE_SHMGETL:shmgetl(2)
183:AUE_SOCKET:socket(2)
184:AUE_SENDTO:sendto(2)
185:AUE_PIPE:pipe(2)
186:AUE_SOCKETPAIR:socketpair(2)
187:AUE_SEND:send(2)
188:AUE_SENDMSG:sendmsg(2)
189:AUE_RECV:recv(2)
190:AUE_RECVMSG:recvmsg(2)
191:AUE_RECVFROM:recvfrom(2)
192:AUE_READ:read(2)
193:AUE_GETDENTS:getdents(2)
194:AUE_LSEEK:lseek(2)
195:AUE_WRITE:write(2)
196:AUE_WRITEV:writev(2)
197:AUE_NFS:nfs server
198:AUE_READV:readv(2)
199:AUE_OSTAT:Solaris old stat(2)
200:AUE_SETUID:setuid(2)
201:AUE_STIME:old stime(2)
202:AUE_UTIME:old utime(2)
203:AUE_NICE:old nice(2)
204:AUE_OSETPGRP:Solaris old setpgrp(2)
205:AUE_SETGID:setgid(2)
206:AUE_READL:readl(2)
207:AUE_READVL:readvl(2)
208:AUE_FSTAT:fstat(2)
209:AUE_DUP2:dup2(2)
210:AUE_MMAP:mmap(2)
211:AUE_AUDIT:audit(2)
212:AUE_PRIOCNTLSYS:Solaris priocntlsys(2)
213:AUE_MUNMAP:munmap(2)
214:AUE_SETEGID:setegid(2)
215:AUE_SETEUID:seteuid(2)
216:AUE_PUTMSG:putmsg(2)
217:AUE_GETMSG:getmsg(2)
218:AUE_PUTPMSG:putpmsg(2)
219:AUE_GETPMSG:getpmsg(2)
220:AUE_AUDITSYS:audit system calls place holder
221:AUE_AUDITON_GETKMASK:auditon(2) - get kernel mask
222:AUE_AUDITON_SETKMASK:auditon(2) - set kernel mask
223:AUE_AUDITON_GETCWD:auditon(2) - get cwd
224:AUE_AUDITON_GETCAR:auditon(2) - get car
225:AUE_AUDITON_GETSTAT:auditon(2) - get audit statistics
226:AUE_AUDITON_SETSTAT:auditon(2) - reset audit statistics
227:AUE_AUDITON_SETUMASK:auditon(2) - set mask per uid
228:AUE_AUDITON_SETSMASK:auditon(2) - set mask per session ID
229:AUE_AUDITON_GETCOND:auditon(2) - get audit state
230:AUE_AUDITON_SETCOND:auditon(2) - set audit state
231:AUE_AUDITON_GETCLASS:auditon(2) - get event class
232:AUE_AUDITON_SETCLASS:auditon(2) - set event class
233:AUE_UTSSYS:utssys(2) - fusers
234:AUE_STATVFS:statvfs(2)
235:AUE_XSTAT:xstat(2)
236:AUE_LXSTAT:lxstat(2)
237:AUE_LCHOWN:lchown(2)
238:AUE_MEMCNTL:memcntl(2)
239:AUE_SYSINFO:sysinfo(2)
240:AUE_XMKNOD:xmknod(2)
241:AUE_FORK1:fork1(2)
242:AUE_MODCTL:modctl(2) system call place holder
243:AUE_MODLOAD:modctl(2) - load module
244:AUE_MODUNLOAD:modctl(2) - unload module
245:AUE_MODCONFIG:modctl(2) - configure module
246:AUE_MODADDMAJ:modctl(2) - bind module
247:AUE_SOCKACCEPT:getmsg-accept
248:AUE_SOCKCONNECT:putmsg-connect
249:AUE_SOCKSEND:putmsg-send
250:AUE_SOCKRECEIVE:getmsg-receive
251:AUE_ACLSET:acl(2) - SETACL comand
252:AUE_FACLSET:facl(2) - SETACL command
253:AUE_DOORFS:doorfs(2) - system call place holder
254:AUE_DOORFS_DOOR_CALL:doorfs(2) - DOOR_CALL
255:AUE_DOORFS_DOOR_RETURN:doorfs(2) - DOOR_RETURN
256:AUE_DOORFS_DOOR_CREATE:doorfs(2) - DOOR_CREATE
257:AUE_DOORFS_DOOR_REVOKE:doorfs(2) - DOOR_REVOKE
258:AUE_DOORFS_DOOR_INFO:doorfs(2) - DOOR_INFO
259:AUE_DOORFS_DOOR_CRED:doorfs(2) - DOOR_CRED
260:AUE_DOORFS_DOOR_BIND:doorfs(2) - DOOR_BIND
261:AUE_DOORFS_DOOR_UNBIND:doorfs(2) - DOOR_UNBIND
262:AUE_P_ONLINE:p_online(2)
263:AUE_PROCESSOR_BIND:processor_bind(2)
264:AUE_INST_SYNC:inst_sync(2)
265:AUE_SOCKCONFIG:configure socket
266:AUE_SETAUDIT_ADDR:setaudit_addr(2)
267:AUE_GETAUDIT_ADDR:getaudit_addr(2)
268:AUE_UMOUNT2:Solaris umount(2)
269:AUE_FSAT:fsat(2) - place holder
270:AUE_OPENAT_R:openat(2) - read
271:AUE_OPENAT_RC:openat(2) - read,creat
272:AUE_OPENAT_RT:openat(2) - read,trunc
273:AUE_OPENAT_RTC:openat(2) - read,creat,trunc
274:AUE_OPENAT_W:openat(2) - write
275:AUE_OPENAT_WC:openat(2) - write,creat
276:AUE_OPENAT_WT:openat(2) - write,trunc
277:AUE_OPENAT_WTC:openat(2) - write,creat,trunc
278:AUE_OPENAT_RW:openat(2) - read,write
279:AUE_OPENAT_RWC:openat(2) - read,write,create
280:AUE_OPENAT_RWTC:openat(2) - read,write,creat,trunc
282:AUE_RENAMEAT:renameat(2)
283:AUE_FSTATAT:fstatat(2)
284:AUE_FCHOWNAT:fchownat(2)
285:AUE_FUTIMESAT:futimesat(2)
286:AUE_UNLINKAT:unlinkat(2)
287:AUE_CLOCK_SETTIME:clock_settime(2)
288:AUE_NTP_ADJTIME:ntp_adjtime(2)
289:AUE_SETPPRIV:setppriv(2)
290:AUE_MODDEVPLCY:modctl(2) - configure device policy
291:AUE_MODADDPRIV:modctl(2) - configure additional privilege
292:AUE_CRYPTOADM:kernel cryptographic framework
293:AUE_CONFIGKSSL:configure kernel SSL
294:AUE_BRANDSYS:brandsys(2)
295:AUE_PF_POLICY_ADDRULE:Add IPsec policy rule
296:AUE_PF_POLICY_DELRULE:Delete IPsec policy rule
297:AUE_PF_POLICY_CLONE:Clone IPsec policy
298:AUE_PF_POLICY_FLIP:Flip IPsec policy
299:AUE_PF_POLICY_FLUSH:Flush IPsec policy rules
300:AUE_PF_POLICY_ALGS:Update IPsec algorithms
301:AUE_PORTFS:portfs
302:AUE_DARWIN_PTRACE:ptrace(2)
303:AUE_DARWIN_CHFLAGS:chflags(2)
304:AUE_DARWIN_FCHFLAGS:fchflags(2)
305:AUE_DARWIN_PROFILE:profil(2)
306:AUE_DARWIN_KTRACE:ktrace(2)
307:AUE_DARWIN_SETLOGIN:setlogin(2)
308:AUE_DARWIN_REBOOT:reboot(2)
309:AUE_DARWIN_REVOKE:revoke(2)
310:AUE_DARWIN_UMASK:umask(2)
311:AUE_DARWIN_MPROTECT:mprotect(2)
312:AUE_DARWIN_SETPRIORITY:setpriority(2)
313:AUE_DARWIN_SETTIMEOFDAY:settimeofday(2)
314:AUE_DARWIN_FLOCK:flock(2)
315:AUE_DARWIN_MKFIFO:mkfifo(2)
316:AUE_DARWIN_POLL:poll(2)
317:AUE_DARWIN_SOCKETPAIR:socketpair(2)
318:AUE_DARWIN_FUTIMES:futimes(2)
319:AUE_DARWIN_SETSID:setsid(2)
320:AUE_DARWIN_SETPRIVEXEC:setprivexec(2)
321:AUE_DARWIN_NFSSVC:nfssvc(2)
322:AUE_DARWIN_GETFH:getfh(2)
323:AUE_DARWIN_QUOTACTL:quotactl(2)
324:AUE_DARWIN_ADDPROFILE:add_profil()
325:AUE_DARWIN_KDEBUGTRACE:kdebug_trace()
326:AUE_DARWIN_FSTAT:fstat(2)
327:AUE_DARWIN_FPATHCONF:fpathconf(2)
328:AUE_DARWIN_GETDIRENTRIES:getdirentries(2)
329:AUE_DARWIN_TRUNCATE:truncate(2)
330:AUE_DARWIN_FTRUNCATE:ftruncate(2)
331:AUE_DARWIN_SYSCTL:sysctl(3)
332:AUE_DARWIN_MLOCK:mlock(2)
333:AUE_DARWIN_MUNLOCK:munlock(2)
334:AUE_DARWIN_UNDELETE:undelete(2)
335:AUE_DARWIN_GETATTRLIST:getattrlist()
336:AUE_DARWIN_SETATTRLIST:setattrlist()
337:AUE_DARWIN_GETDIRENTRIESATTR:getdirentriesattr()
338:AUE_DARWIN_EXCHANGEDATA:exchangedata()
339:AUE_DARWIN_SEARCHFS:searchfs()
340:AUE_DARWIN_MINHERIT:minherit(2)
341:AUE_DARWIN_SEMCONFIG:semconfig()
342:AUE_DARWIN_SEMOPEN:sem_open(2)
343:AUE_DARWIN_SEMCLOSE:sem_close(2)
344:AUE_DARWIN_SEMUNLINK:sem_unlink(2)
345:AUE_DARWIN_SHMOPEN:shm_open(2)
346:AUE_DARWIN_SHMUNLINK:shm_unlink(2)
347:AUE_DARWIN_LOADSHFILE:load_shared_file()
348:AUE_DARWIN_RESETSHFILE:reset_shared_file()
349:AUE_DARWIN_NEWSYSTEMSHREG:new_system_share_regions()
350:AUE_DARWIN_PTHREADKILL:pthread_kill(2)
351:AUE_DARWIN_PTHREADSIGMASK:pthread_sigmask(2)
352:AUE_DARWIN_AUDITCTL:auditctl(2)
353:AUE_DARWIN_RFORK:rfork(2)
354:AUE_DARWIN_LCHMOD:lchmod(2)
355:AUE_DARWIN_SWAPOFF:swapoff(2)
356:AUE_DARWIN_INITPROCESS:init_process()
357:AUE_DARWIN_MAPFD:map_fd()
358:AUE_DARWIN_TASKFORPID:task_for_pid()
359:AUE_DARWIN_PIDFORTASK:pid_for_task()
360:AUE_DARWIN_SYSCTL_NONADMIN:sysctl() - non-admin
361:AUE_DARWIN_COPYFILE:copyfile()
6144:AUE_at_create:at-create atjob
6145:AUE_at_delete:at-delete atjob (at or atrm)
6146:AUE_at_perm:at-permission
6147:AUE_cron_invoke:cron-invoke
6148:AUE_crontab_create:crontab-crontab created
6149:AUE_crontab_delete:crontab-crontab deleted
6150:AUE_crontab_perm:crontab-permission
6151:AUE_inetd_connect:inetd connection
6152:AUE_login:login - local
6153:AUE_logout:logout - local
6154:AUE_telnet:login - telnet
6155:AUE_rlogin:login - rlogin
6156:AUE_mountd_mount:mount
6157:AUE_mountd_umount:unmount
6158:AUE_rshd:rsh access
6159:AUE_su:su(1)
6160:AUE_halt:system halt
6161:AUE_reboot:system reboot
6162:AUE_rexecd:rexecd
6163:AUE_passwd:passwd
6164:AUE_rexd:rexd
6165:AUE_ftpd:ftp access
6166:AUE_init:init
6167:AUE_uadmin:uadmin
6168:AUE_shutdown:system shutdown
6170:AUE_crontab_mod:crontab-modify
6171:AUE_ftpd_logout:ftp logout
6172:AUE_ssh:login - ssh
6173:AUE_role_login:role login
6180:AUE_prof_cmd: profile command
6181:AUE_filesystem_add:add filesystem
6182:AUE_filesystem_delete:delete filesystem
6183:AUE_filesystem_modify:modify filesystem
6200:AUE_allocate_succ:allocate-device success
6201:AUE_allocate_fail:allocate-device failure
6202:AUE_deallocate_succ:deallocate-device success
6203:AUE_deallocate_fail:deallocate-device failure
6204:AUE_listdevice_succ:allocate-list devices success
6205:AUE_listdevice_fail:allocate-list devices failure
6207:AUE_create_user:create user
6208:AUE_modify_user:modify user
6209:AUE_delete_user:delete user
6210:AUE_disable_user:disable user
6211:AUE_enable_user:enable users
6212:AUE_newgrp_login:newgrp login
6213:AUE_admin_authenticate:admin login
6214:AUE_kadmind_auth:authenticated kadmind request
6215:AUE_kadmind_unauth:unauthenticated kadmind req
6216:AUE_krb5kdc_as_req:kdc authentication svc request
6217:AUE_krb5kdc_tgs_req:kdc tkt-grant svc request
6218:AUE_krb5kdc_tgs_req_2ndtktmm:kdc tgs 2ndtkt mismtch
6219:AUE_krb5kdc_tgs_req_alt_tgt:kdc tgs issue alt tgt
6300:AUE_DARWIN_sudo:sudo(1)
6501:AUE_DARWIN_modify_password:modify password
6511:AUE_DARWIN_create_group:create group
6512:AUE_DARWIN_delete_group:delete group
6513:AUE_DARWIN_modify_group:modify group
6514:AUE_DARWIN_add_to_group:add to group
6515:AUE_DARWIN_remove_from_group:remove from group
6521:AUE_DARWIN_revoke_obj:revoke object priv
6600:AUE_DARWIN_lw_login:loginwindow login
6601:AUE_DARWIN_lw_logout:loginwindow logout
7000:AUE_DARWIN_auth_user:user authentication
7001:AUE_DARWIN_ssconn:SecSrvr connection setup
7002:AUE_DARWIN_ssauthorize:SecSrvr AuthEngine
7003:AUE_DARWIN_ssauthint:SecSrvr authinternal mech
32800:AUE_openssh:OpenSSH login
43001:AUE_GETFSSTAT:getfsstat(2)
43002:AUE_PTRACE:ptrace(2)
43003:AUE_CHFLAGS:chflags(2)
43004:AUE_FCHFLAGS:fchflags(2)
43005:AUE_PROFILE:profil(2)
43006:AUE_KTRACE:ktrace(2)
43007:AUE_SETLOGIN:setlogin(2)
43008:AUE_OPENBSM_REVOKE:revoke(2)
43009:AUE_UMASK:umask(2)
43010:AUE_MPROTECT:mprotect(2)
43011:AUE_MKFIFO:mkfifo(2)
43012:AUE_POLL:poll(2)
43013:AUE_FUTIMES:futimes(2)
43014:AUE_SETSID:setsid(2)
43015:AUE_SETPRIVEXEC:setprivexec(2)
43016:AUE_ADDPROFILE:add_profil()
43017:AUE_KDEBUGTRACE:kdebug_trace()
43018:AUE_OPENBSM_FSTAT:fstat(2)
43019:AUE_FPATHCONF:fpathconf(2)
43020:AUE_GETDIRENTRIES:getdirentries(2)
43021:AUE_SYSCTL:sysctl(3)
43022:AUE_MLOCK:mlock(2)
43023:AUE_MUNLOCK:munlock(2)
43024:AUE_UNDELETE:undelete(2)
43025:AUE_GETATTRLIST:getattrlist()
43026:AUE_SETATTRLIST:setattrlist()
43027:AUE_GETDIRENTRIESATTR:getdirentriesattr()
43028:AUE_EXCHANGEDATA:exchangedata()
43029:AUE_SEARCHFS:searchfs()
43030:AUE_MINHERIT:minherit(2)
43031:AUE_SEMCONFIG:semconfig()
43032:AUE_SEMOPEN:sem_open(2)
43033:AUE_SEMCLOSE:sem_close(2)
43034:AUE_SEMUNLINK:sem_unlink(2)
43035:AUE_SHMOPEN:shm_open(2)
43036:AUE_SHMUNLINK:shm_unlink(2)
43037:AUE_LOADSHFILE:load_shared_file()
43038:AUE_RESETSHFILE:reset_shared_file()
43039:AUE_NEWSYSTEMSHREG:new_system_share_regions()
43040:AUE_PTHREADKILL:pthread_kill(2)
43041:AUE_PTHREADSIGMASK:pthread_sigmask(2)
43042:AUE_AUDITCTL:auditctl(2)
43043:AUE_RFORK:rfork(2)
43044:AUE_LCHMOD:lchmod(2)
43045:AUE_SWAPOFF:swapoff(2)
43046:AUE_INITPROCESS:init_process()
43047:AUE_MAPFD:map_fd()
43048:AUE_TASKFORPID:task_for_pid()
43049:AUE_PIDFORTASK:pid_for_task()
43050:AUE_SYSCTL_NONADMIN:sysctl() - non-admin
43051:AUE_COPYFILE:copyfile(2)
43052:AUE_LUTIMES:lutimes(2)
43053:AUE_LCHFLAGS:lchflags(2)
43054:AUE_SENDFILE:sendfile(2)
43055:AUE_USELIB:uselib(2)
43056:AUE_GETRESUID:getresuid(2)
43057:AUE_SETRESUID:setresuid(2)
43058:AUE_GETRESGID:getresgid(2)
43059:AUE_SETRESGID:setresgid(2)
43060:AUE_WAIT4:wait4(2)
43061:AUE_LGETFH:lgetfh(2)
43062:AUE_FHSTATFS:fhstatfs(2)
43063:AUE_FHOPEN:fhopen(2)
43064:AUE_FHSTAT:fhstat(2)
43065:AUE_JAIL:jail(2)
43066:AUE_EACCESS:eaccess(2)
43067:AUE_KQUEUE:kqueue(2)
43068:AUE_KEVENT:kevent(2)
43069:AUE_FSYNC:fsync(2)
43070:AUE_NMOUNT:nmount(2)
43071:AUE_BDFLUSH:bdflush(2)
43072:AUE_SETFSUID:setfsuid(2)
43073:AUE_SETFSGID:setfsgid(2)
43074:AUE_PERSONALITY:personality(2)
43075:AUE_SCHED_GETSCHEDULER:getscheduler(2)
43076:AUE_SCHED_SETSCHEDULER:setscheduler(2)
43077:AUE_PRCTL:prctl(2)
43078:AUE_GETCWD:getcwd(2)
43079:AUE_CAPGET:capget(2)
43080:AUE_CAPSET:capset(2)
43081:AUE_PIVOT_ROOT:pivot_root(2)
43082:AUE_RTPRIO:rtprio(2)
43083:AUE_SCHED_GETPARAM:sched_getparam(2)
43084:AUE_SCHED_SETPARAM:sched_setparam(2)
43085:AUE_SCHED_GET_PRIORITY_MAX:sched_get_priority_max(2)
43086:AUE_SCHED_GET_PRIORITY_MIN:sched_get_priority_min(2)
43087:AUE_SCHED_RR_GET_INTERVAL:sched_rr_get_interval(2)
43088:AUE_ACL_GET_FILE:acl_get_file(2)
43089:AUE_ACL_SET_FILE:acl_set_file(2)
43090:AUE_ACL_GET_FD:acl_get_fd(2)
43091:AUE_ACL_SET_FD:acl_set_fd(2)
43092:AUE_ACL_DELETE_FILE:acl_delete_file(2)
43093:AUE_ACL_DELETE_FD:acl_delete_fd(2)
43094:AUE_ACL_CHECK_FILE:acl_aclcheck_file(2)
43095:AUE_ACL_CHECK_FD:acl_aclcheck_fd(2)
43096:AUE_ACL_GET_LINK:acl_get_link(2)
43097:AUE_ACL_SET_LINK:acl_set_link(2)
43098:AUE_ACL_DELETE_LINK:acl_delete_link(2)
43099:AUE_ACL_CHECK_LINK:acl_aclcheck_link(2)
43100:AUE_SYSARCH:sysarch(2)
43101:AUE_EXTATTRCTL:extattrctl(2)
43102:AUE_EXTATTR_GET_FILE:extattr_get_file(2)
43103:AUE_EXTATTR_SET_FILE:extattr_set_file(2)
43104:AUE_EXTATTR_LIST_FILE:extattr_list_file(2)
43105:AUE_EXTATTR_DELETE_FILE:extattr_delete_file(2)
43106:AUE_EXTATTR_GET_FD:extattr_get_fd(2)
43107:AUE_EXTATTR_SET_FD:extattr_set_fd(2)
43108:AUE_EXTATTR_LIST_FD:extattr_list_fd(2)
43109:AUE_EXTATTR_DELETE_FD:extattr_delete_fd(2)
43110:AUE_EXTATTR_GET_LINK:extattr_get_link(2)
43111:AUE_EXTATTR_SET_LINK:extattr_set_link(2)
43112:AUE_EXTATTR_LIST_LINK:extattr_list_link(2)
43113:AUE_EXTATTR_DELETE_LINK:extattr_delete_link(2)
43114:AUE_KENV:kenv(8)
43115:AUE_JAIL_ATTACH:jail_attach(2)
43116:AUE_SYSCTL_WRITE:sysctl(3)
43117:AUE_IOPERM:linux ioperm
43118:AUE_READDIR:readdir(3)
43119:AUE_IOPL:linux iopl
43120:AUE_VM86:linux vm86
43121:AUE_MAC_GET_PROC:mac_get_proc(2)
43122:AUE_MAC_SET_PROC:mac_set_proc(2)
43123:AUE_MAC_GET_FD:mac_get_fd(2)
43124:AUE_MAC_GET_FILE:mac_get_file(2)
43125:AUE_MAC_SET_FD:mac_set_fd(2)
43126:AUE_MAC_SET_FILE:mac_set_file(2)
43127:AUE_MAC_SYSCALL:mac_syscall(2)
43128:AUE_MAC_GET_PID:mac_get_pid(2)
43129:AUE_MAC_GET_LINK:mac_get_link(2)
43130:AUE_MAC_SET_LINK:mac_set_link(2)
43131:AUE_MAC_EXECVE:mac_execve(2)
43132:AUE_GETPATH_FROMFD:getpath_fromfd(2)
43133:AUE_GETPATH_FROMADDR:getpath_fromaddr(2)
43134:AUE_MQ_OPEN:mq_open(2)
43135:AUE_MQ_SETATTR:mq_setattr(2)
43136:AUE_MQ_TIMEDRECEIVE:mq_timedreceive(2)
43137:AUE_MQ_TIMEDSEND:mq_timedsend(2)
43138:AUE_MQ_NOTIFY:mq_notify(2)
43139:AUE_MQ_UNLINK:mq_unlink(2)
43140:AUE_LISTEN:listen(2)
43141:AUE_MLOCKALL:mlockall(2)
43142:AUE_MUNLOCKALL:munlockall(2)
43143:AUE_CLOSEFROM:closefrom(2)
43144:AUE_FEXECVE:fexecve(2)
43145:AUE_FACCESSAT:faccessat(2)
43146:AUE_FCHMODAT:fchmodat(2)
43147:AUE_LINKAT:linkat(2)
43148:AUE_MKDIRAT:mkdirat(2)
43149:AUE_MKFIFOAT:mkfifoat(2)
43150:AUE_MKNODAT:mknodat(2)
43151:AUE_READLINKAT:readlinkat(2)
43152:AUE_SYMLINKAT:symlinkat(2)
43153:AUE_MAC_GETFSSTAT:mac_getfsstat(2)
43154:AUE_MAC_GET_MOUNT:mac_get_mount(2)
43155:AUE_MAC_GET_LCID:mac_get_lcid(2)
43156:AUE_MAC_GET_LCTX:mac_get_lctx(2)
43157:AUE_MAC_SET_LCTX:mac_set_lctx(2)
43158:AUE_MAC_MOUNT:mac_mount(2)
43159:AUE_GETLCID:getlcid(2)
43160:AUE_SETLCID:setlcid(2)
43161:AUE_TASKNAMEFORPID:taskname_for_pid()
43162:AUE_ACCESS_EXTENDED:access_extended(2)
43163:AUE_CHMOD_EXTENDED:chmod_extended(2)
43164:AUE_FCHMOD_EXTENDED:fchmod_extended(2)
43165:AUE_FSTAT_EXTENDED:fstat_extended(2)
43166:AUE_LSTAT_EXTENDED:lstat_extended(2)
43167:AUE_MKDIR_EXTENDED:mkdir_extended(2)
43168:AUE_MKFIFO_EXTENDED:mkfifo_extended(2)
43169:AUE_OPEN_EXTENDED:open_extended(2) - attr only
43170:AUE_OPEN_EXTENDED_R:open_extended(2) - read
43171:AUE_OPEN_EXTENDED_RC:open_extended(2) - read,creat
43172:AUE_OPEN_EXTENDED_RT:open_extended(2) - read,trunc
43173:AUE_OPEN_EXTENDED_RTC:open_extended(2) - read,creat,trunc
43174:AUE_OPEN_EXTENDED_W:open_extended(2) - write
43175:AUE_OPEN_EXTENDED_WC:open_extended(2) - write,creat
43176:AUE_OPEN_EXTENDED_WT:open_extended(2) - write,trunc
43177:AUE_OPEN_EXTENDED_WTC:open_extended(2) - write,creat,trunc
43178:AUE_OPEN_EXTENDED_RW:open_extended(2) - read,write
43179:AUE_OPEN_EXTENDED_RWC:open_extended(2) - read,write,creat
43180:AUE_OPEN_EXTENDED_RWT:open_extended(2) - read,write,trunc
43181:AUE_OPEN_EXTENDED_RWTC:open_extended(2) - read,write,creat,trunc
43182:AUE_STAT_EXTENDED:stat_extended(2)
43183:AUE_UMASK_EXTENDED:umask_extended(2)
43184:AUE_OPENAT:openat(2) - attr only
43185:AUE_POSIX_OPENPT:posix_openpt(2)
43186:AUE_CAP_NEW:cap_new(2)
43187:AUE_CAP_GETRIGHTS:cap_getrights(2)
43188:AUE_CAP_ENTER:cap_enter(2)
43189:AUE_CAP_GETMODE:cap_getmode(2)
43190:AUE_POSIX_SPAWN:posix_spawn(2)
43191:AUE_FSGETPATH:fsgetpath(2)
43192:AUE_PREAD:pread(2)
43193:AUE_PWRITE:pwrite(2)
43194:AUE_FSCTL:fsctl()
43195:AUE_FFSCTL:ffsctl()
45000:AUE_audit_startup:audit startup
45001:AUE_audit_shutdown:audit shutdown
45014:AUE_modify_password:modify password
45015:AUE_create_group:create group
45016:AUE_delete_group:delete group
45017:AUE_modify_group:modify group
45018:AUE_add_to_group:add to group
45019:AUE_remove_from_group:remove from group
45020:AUE_revoke_obj:revoke object priv
45021:AUE_lw_login:loginwindow login
45022:AUE_lw_logout:loginwindow logout
45023:AUE_auth_user:user authentication
45024:AUE_ssconn:SecSrvr connection setup
45025:AUE_ssauthorize:SecSrvr AuthEngine
45026:AUE_ssauthint:SecSrvr authinternal mech
45027:AUE_calife:Calife
45028:AUE_sudo:sudo(1)
45029:AUE_audit_recovery:audit crash recovery
45030:AUE_ssauthmech:SecSrvr AuthMechanism
"""

BUNDLED_EVENTS = parse_event_table(_EVENT_TABLE_TEXT.encode())

# Event numbers that table does not hold, with the constant xnu's bsd/bsm/audit_kevents.h
# (xnu commit f6217f891ac0bb64f3d375211650a4c1ff8ca1ea) or OpenBSM's bsm/audit_uevents.h
# (openbsm commit 6230904e8b0c8d73339682ebe9173dd853436047) defines for them.
EVENT_CONSTANTS = {
    281: 'AUE_OPENAT_RWTC',
    362: 'AUE_TRACKERACTION',
    6169: 'AUE_poweroff',
    6206: 'AUE_listdevice_fail',
    43196: 'AUE_LPATHCONF',
    43197: 'AUE_PDFORK',
    43198: 'AUE_PDKILL',
    43199: 'AUE_PDGETPID',
    43200: 'AUE_PDWAIT',
    43201: 'AUE_GETATTRLISTBULK',
    43202: 'AUE_GETATTRLISTAT',
    43203: 'AUE_OPENBYID',
    43204: 'AUE_OPENBYID_R',
    43205: 'AUE_OPENBYID_RT',
    43206: 'AUE_OPENBYID_W',
    43207: 'AUE_OPENBYID_WT',
    43208: 'AUE_OPENBYID_RW',
    43209: 'AUE_OPENBYID_RWT',
    43210: 'AUE_CLONEFILEAT',
    43211: 'AUE_FCLONEFILEAT',
    43212: 'AUE_SETATTRLISTAT',
    43213: 'AUE_FMOUNT',
    43214: 'AUE_FSGETPATH_EXTENDED',
    43215: 'AUE_DBGPORTFORPID',
    43216: 'AUE_PREADV',
    43217: 'AUE_PWRITEV',
    43218: 'AUE_FREADLINK',
    43219: 'AUE_FUNMOUNT',
    44901: 'AUE_SESSION_START',
    44902: 'AUE_SESSION_UPDATE',
    44903: 'AUE_SESSION_END',
    44904: 'AUE_SESSION_CLOSE',
}

# BSM error numbers, the BSM_ERRNO_ constants in OpenBSM's sys/bsm/audit_errno.h
# (openbsm commit 6230904e8b0c8d73339682ebe9173dd853436047), without the prefix.
BSM_ERRNO = {
    0: 'ESUCCESS',
    1: 'EPERM',
    2: 'ENOENT',
    3: 'ESRCH',
    4: 'EINTR',
    5: 'EIO',
    6: 'ENXIO',
    7: 'E2BIG',
    8: 'ENOEXEC',
    9: 'EBADF',
    10: 'ECHILD',
    11: 'EAGAIN',
    12: 'ENOMEM',
    13: 'EACCES',
    14: 'EFAULT',
    15: 'ENOTBLK',
    16: 'EBUSY',
    17: 'EEXIST',
    18: 'EXDEV',
    19: 'ENODEV',
    20: 'ENOTDIR',
    21: 'EISDIR',
    22: 'EINVAL',
    23: 'ENFILE',
    24: 'EMFILE',
    25: 'ENOTTY',
    26: 'ETXTBSY',
    27: 'EFBIG',
    28: 'ENOSPC',
    29: 'ESPIPE',
    30: 'EROFS',
    31: 'EMLINK',
    32: 'EPIPE',
    33: 'EDOM',
    34: 'ERANGE',
    35: 'ENOMSG',
    36: 'EIDRM',
    37: 'ECHRNG',
    38: 'EL2NSYNC',
    39: 'EL3HLT',
    40: 'EL3RST',
    41: 'ELNRNG',
    42: 'EUNATCH',
    43: 'ENOCSI',
    44: 'EL2HLT',
    45: 'EDEADLK',
    46: 'ENOLCK',
    47: 'ECANCELED',
    48: 'ENOTSUP',
    49: 'EDQUOT',
    50: 'EBADE',
    51: 'EBADR',
    52: 'EXFULL',
    53: 'ENOANO',
    54: 'EBADRQC',
    55: 'EBADSLT',
    56: 'EDEADLOCK',
    57: 'EBFONT',
    58: 'EOWNERDEAD',
    59: 'ENOTRECOVERABLE',
    60: 'ENOSTR',
    61: 'ENODATA',
    62: 'ETIME',
    63: 'ENOSR',
    64: 'ENONET',
    65: 'ENOPKG',
    66: 'EREMOTE',
    67: 'ENOLINK',
    68: 'EADV',
    69: 'ESRMNT',
    70: 'ECOMM',
    71: 'EPROTO',
    72: 'ELOCKUNMAPPED',
    73: 'ENOTACTIVE',
    74: 'EMULTIHOP',
    77: 'EBADMSG',
    78: 'ENAMETOOLONG',
    79: 'EOVERFLOW',
    80: 'ENOTUNIQ',
    81: 'EBADFD',
    82: 'EREMCHG',
    83: 'ELIBACC',
    84: 'ELIBBAD',
    85: 'ELIBSCN',
    86: 'ELIBMAX',
    87: 'ELIBEXEC',
    88: 'EILSEQ',
    89: 'ENOSYS',
    90: 'ELOOP',
    91: 'ERESTART',
    92: 'ESTRPIPE',
    93: 'ENOTEMPTY',
    94: 'EUSERS',
    95: 'ENOTSOCK',
    96: 'EDESTADDRREQ',
    97: 'EMSGSIZE',
    98: 'EPROTOTYPE',
    99: 'ENOPROTOOPT',
    120: 'EPROTONOSUPPORT',
    121: 'ESOCKTNOSUPPORT',
    122: 'EOPNOTSUPP',
    123: 'EPFNOSUPPORT',
    124: 'EAFNOSUPPORT',
    125: 'EADDRINUSE',
    126: 'EADDRNOTAVAIL',
    127: 'ENETDOWN',
    128: 'ENETUNREACH',
    129: 'ENETRESET',
    130: 'ECONNABORTED',
    131: 'ECONNRESET',
    132: 'ENOBUFS',
    133: 'EISCONN',
    134: 'ENOTCONN',
    143: 'ESHUTDOWN',
    144: 'ETOOMANYREFS',
    145: 'ETIMEDOUT',
    146: 'ECONNREFUSED',
    147: 'EHOSTDOWN',
    148: 'EHOSTUNREACH',
    149: 'EALREADY',
    150: 'EINPROGRESS',
    151: 'ESTALE',
    152: 'EQFULL',
    190: 'EPROCLIM',
    191: 'EBADRPC',
    192: 'ERPCMISMATCH',
    193: 'EPROGUNAVAIL',
    194: 'EPROGMISMATCH',
    195: 'EPROCUNAVAIL',
    196: 'EFTYPE',
    197: 'EAUTH',
    198: 'ENEEDAUTH',
    199: 'ENOATTR',
    200: 'EDOOFUS',
    201: 'EJUSTRETURN',
    202: 'ENOIOCTL',
    203: 'EDIRIOCTL',
    204: 'EPWROFF',
    205: 'EDEVERR',
    206: 'EBADEXEC',
    207: 'EBADARCH',
    208: 'ESHLIBVERS',
    209: 'EBADMACHO',
    210: 'EPOLICY',
    211: 'EDOTDOT',
    212: 'EUCLEAN',
    213: 'ENOTNAM',
    214: 'ENAVAIL',
    215: 'EISNAM',
    216: 'EREMOTEIO',
    217: 'ENOMEDIUM',
    218: 'EMEDIUMTYPE',
    219: 'ENOKEY',
    220: 'EKEYEXPIRED',
    221: 'EKEYREVOKED',
    222: 'EKEYREJECTED',
    223: 'ENOTCAPABLE',
    224: 'ECAPMODE',
    225: 'EINTEGRITY',
    250: 'UNKNOWN',
}
