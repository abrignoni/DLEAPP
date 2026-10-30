"""Windows Prefetch parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange Windows.Forensics.Prefetch artifact.

A Windows 10 and 11 prefetch file (.pf) is a MAM/Xpress-Huffman compressed container
around the SCCA prefetch structure; earlier versions store the SCCA structure as it is. The decompressor below is an original
implementation of the LZ77+Huffman (Xpress Huffman) algorithm from the public
[MS-XCA] specification (Microsoft grants the right to implement it); it uses only
the standard library. The SCCA structure is then parsed with the field offsets
from the libyal libscca format documentation: version 17 (Windows XP and 2003),
23 (Vista and 7), 26 (8.0 and 8.1), 30, which Windows 10 and 11 write, and 31,
which newer Windows 11 builds write with the layout of version 30's second
variant. All are cited in the notes.
"""

import os
import struct
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc

_MAM_SIGNATURE = b"MAM\x04"       # Xpress Huffman, no checksum
_SCCA_SIGNATURE = b"SCCA"
# Version 30 (Windows 10 and 11) and version 31 (Windows 11), which libscca describes as similar to
# version 30 variant 2 in each structure this module reads; see the notes for what was measured.
# Versions 17, 23 and 26 are uncompressed: per libscca's file information tables, version 17 keeps
# one run time at file offset 120 and the run count at 144, version 23 one run time at 128 and the
# run count at 152, and version 26 eight run times from 128 and the run count at 208 (each offset is
# the table's, which counts from the end of the 84-byte file header, plus 84). A volume information
# entry is 40 bytes in version 17, 104 in 23 and 26 and 96 in 30 and 31.
_SUPPORTED_VERSIONS = (17, 23, 26, 30, 31)
_FIXED_LAYOUT = {17: (120, 1, 144), 23: (128, 1, 152), 26: (128, 8, 208)}
_VOLUME_ENTRY_SIZE = {17: 40, 23: 104, 26: 104, 30: 96, 31: 96}
# Version 30 comes in two variants of the file information that follows the 84-byte
# file header, told apart by the file metrics array offset stored first in it: 304 in
# variant 1, which keeps the run count at file offset 208, and 296 in variant 2, which
# keeps it at 200 (libscca, "File information - version 30 - variant 1/2").
_RUN_COUNT_OFFSET = {304: 208, 296: 200}
_MAX_BITS = 15
_CHUNK = 65536

__artifacts_v2__ = {
    "prefetch": {
        "name": "Prefetch",
        "description": "Programs Windows prepared to run, from the .pf prefetch "
                       "files: the executable, run count, up to eight run times, and "
                       "the first volume the file records.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-16",
        "last_update_date": "2026-10-29",
        "requirements": "none",
        "category": "Windows",
        "notes": "One row per prefetch file. Executable is the name stored in the "
                 "file's header. Run Count is the run count the file stores, read "
                 "where each version 30 variant keeps it: the file information that "
                 "follows the 84-byte file header "
                 "(https://github.com/libyal/libscca/blob/d9ea0ceac5a971fa2856caf4fc6745f3b36cd9d9/documentation/Windows%20Prefetch%20File%20(PF)%20format.asciidoc?plain=1#L218-L220) "
                 "first stores the file metrics array offset, 304 in variant 1, which "
                 "keeps the run count at file offset 208 "
                 "(https://github.com/libyal/libscca/blob/d9ea0ceac5a971fa2856caf4fc6745f3b36cd9d9/documentation/Windows%20Prefetch%20File%20(PF)%20format.asciidoc?plain=1#L366-L391), "
                 "and 296 in variant 2, which keeps it at 200 "
                 "(https://github.com/libyal/libscca/blob/d9ea0ceac5a971fa2856caf4fc6745f3b36cd9d9/documentation/Windows%20Prefetch%20File%20(PF)%20format.asciidoc?plain=1#L402-L427); "
                 "a version 30 or 31 file with any other value there gets a blank Run Count and a note in the run log. Versions 17, 23 and 26, which libscca gives as written by Windows XP and 2003, Vista and 7, and 8.0 and 8.1 (https://github.com/libyal/libscca/blob/d9ea0ceac5a971fa2856caf4fc6745f3b36cd9d9/documentation/Windows%20Prefetch%20File%20(PF)%20format.asciidoc?plain=1#L249-L259), store the run count at file offsets 144, 152 and 208 and one, one and eight run times, read where libscca's file information tables place them (https://github.com/libyal/libscca/blob/d9ea0ceac5a971fa2856caf4fc6745f3b36cd9d9/documentation/Windows%20Prefetch%20File%20(PF)%20format.asciidoc?plain=1#L268-L357) plus the 84 bytes of the file header those tables count from. Version 31, which Windows 11 build 26200 writes, is read with the layout of "
                 "version 30 variant 2: libscca says 'The file information - version 31 appears to be similar to the file information version 30 - variant 2.' "
                 "(https://github.com/libyal/libscca/blob/d9ea0ceac5a971fa2856caf4fc6745f3b36cd9d9/documentation/Windows%20Prefetch%20File%20(PF)%20format.asciidoc?plain=1#L442-L443) "
                 "and describes version 31's volume information the same way against version 30 "
                 "(https://github.com/libyal/libscca/blob/d9ea0ceac5a971fa2856caf4fc6745f3b36cd9d9/documentation/Windows%20Prefetch%20File%20(PF)%20format.asciidoc?plain=1#L723-L724). "
                 "Every prefetch file read on af_case2_win10 and "
                 "lonewolf_win10 is variant 1 and every one on pc_mus_001_win11 and "
                 "szechuan_win10 is variant 2, and on every row whose Run Count is 8 "
                 "or less it equals the number of run times stored (134, 102, 398 and 177 rows). On windows11_arm_winlogon_known_20261004, a capture of a Windows 11 build 26200 "
                 "machine, all 371 files are version 31 and store 296 there, and Run Count equals the number of run times stored on the 285 rows where it is 8 or less. That capture's "
                 "Security log records process creation (event 4688), and each of the 385 run times that fall inside the log's span has a 4688 record within 0.4 seconds whose process "
                 "file name, cut to the 29 characters the prefetch header keeps, is the Executable. Last Run (UTC) is the first of the recorded run times and "
                 "Run Times (UTC) lists all of them in the order stored (versions 26, 30 and 31 keep up to eight, versions 17 and 23 one); that order was not newest first on 5 of the 184 "
                 "af_case2_win10 rows, 6 of the 160 lonewolf_win10 rows, 20 of the 527 "
                 "pc_mus_001_win11 rows and 8 of the 196 szechuan_win10 rows, and on 2, 2, 7 and 4 of those the first time was not the latest. On alihadi_challenge3_win81 it was not newest first on 4 of the 71 rows, and on all 4 the first time was not the latest. On the capture it was not newest first on"
                 " 13 of the 371 rows, and on 7 of those the first time was not the latest. Files "
                 "Loaded is the number of "
                 "files the run referenced. Volume Device Path, Volume Serial and "
                 "Volume Created (UTC) describe the first volume the file records; a "
                 "prefetch file can reference more than one volume, and only the "
                 "first is shown on this row. Prefetch File is the .pf file name. A "
                 "prefetch file records that Windows prepared an executable to run, "
                 "with up to eight of the most recent run times and a total run count. "
                 "It is evidence that the program ran, not who ran it. A version 30 or 31 .pf file is MAM Xpress-Huffman compressed; it is decompressed in memory with an original implementation of the MS-XCA LZ77+Huffman algorithm and the SCCA structure is then parsed. A version 17, 23 or 26 file holds the SCCA structure as it is and is parsed directly. A .pf that is neither MAM Xpress-Huffman nor SCCA, or whose SCCA version is none of 17, 23, 26, 30 and 31, is skipped with a note in the run log. On the version 17, 23 and 26 test files of Eric Zimmerman's Prefetch library (EricZimmerman/Prefetch at commit 841212266356a9121a1c34ee538cbce2bb2b9cf3, MIT, https://github.com/EricZimmerman/Prefetch/tree/841212266356a9121a1c34ee538cbce2bb2b9cf3/Prefetch.Test), the executable, run count, first run time, first volume's device path, serial and creation time, loaded-file count and named loaded file matched the 80 values its TestVersion17, TestVersion23 and TestVersion26 tests assert for those fields, and the 26 values its TestVersion30 test asserts for them matched as well; the tests' other assertions (header hash, file size, file references, directory names, second volumes) cover fields this artifact does not report. All 95 files on cfreds_leakage_win7 are version 23 and all 71 on alihadi_challenge3_win81 are version 26, and PECmd 2026.10.3 gave the same executable, run count, run times in order, first volume's device path, serial and creation time, and loaded files in order for every one of them, to the whole second PECmd writes. On alihadi_challenge3_win81 Run Count equals the number of run times stored on all 68 rows where it is 8 or less. Times are Windows FILETIMEs shown in UTC, cut to whole microseconds; a 0 or out-of-range value is blank. Format: original MS-XCA "
                 "implementation, https://learn.microsoft.com/en-us/openspecs/"
                 "windows_protocols/ms-xca/a8b7cb0a-92a6-4187-a23b-5e14273b96f8; "
                 "SCCA fields from libyal libscca, "
                 "https://github.com/libyal/libscca/blob/d9ea0ceac5a971fa2856caf4fc6745f3b36cd9d9/documentation/Windows%20Prefetch%20File%20(PF)%20format.asciidoc; "
                 "and Velocidex, Windows.Forensics.Prefetch.",
        "paths": ("*/Windows/Prefetch/*.pf",),
        "output_types": ["standard"],
        "artifact_icon": "activity",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 527 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 184 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 160 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 196 rows",
            "windows11_arm_winlogon_known_20261004": "Windows 11 build 26200 | 371 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 95 rows",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 71 rows",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 0 rows (no file matches the declared paths)",
        },
    },
    "prefetchFilesLoaded": {
        "name": "Prefetch Files Loaded",
        "description": "Files each prefetched program referenced when it ran, from "
                       "the .pf prefetch files: one row per referenced file.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-16",
        "last_update_date": "2026-10-29",
        "requirements": "none",
        "category": "Windows",
        "notes": "One row per file referenced by a prefetch file, so an executable "
                 "with many loaded files produces many rows. Executable is the name "
                 "from the prefetch header and Loaded File is the referenced path as "
                 "stored: in version 30 and 31 files usually in \\VOLUME{...}\\ form naming the volume by its GUID and serial, and in the version 23 and 26 files read beginning \\DEVICE\\HARDDISKVOLUME: on alihadi_challenge3_win81 all 3,648 in \\DEVICE\\HARDDISKVOLUMEn\\ form, on cfreds_leakage_win7 11,369 of 11,655 in that form and 286 in \\DEVICE\\HARDDISKVOLUMESHADOWCOPYn\\ form. "
                 "Version 31 files, which Windows 11 build 26200 writes, are read the same way as "
                 "version 30: on windows11_arm_winlogon_known_20261004 all 371 files are version "
                 "31 and every loaded file name in them begins \\VOLUME{. "
                 "Prefetch File is the .pf file name. Prefetch File does not separate two copies "
                 "of one prefetch file, and the declared path also matches a Prefetch folder under"
                 " Windows.old, so Source File names the file each row came from."
                 " The list is "
                 "what the program referenced when it was prepared to run, which "
                 "includes its own image, its DLLs and data files it opened. A "
                 "prefetch file records that Windows prepared an executable to run. "
                 "It is evidence that the program ran, not who ran it. A version 30 or 31 .pf file is MAM Xpress-Huffman compressed; it is decompressed in memory with an original implementation of the MS-XCA LZ77+Huffman algorithm and the SCCA structure is then parsed; a version 17, 23 or 26 file holds the SCCA structure as it is. A .pf that is neither MAM Xpress-Huffman nor SCCA, or whose SCCA version is none of 17, 23, 26, 30 and 31, is skipped with a note in the run log. On cfreds_leakage_win7 (version 23) and alihadi_challenge3_win81 (version 26) the loaded files of every prefetch file equal PECmd 2026.10.3's, in order. Format: original MS-XCA implementation, https://"
                 "learn.microsoft.com/en-us/openspecs/windows_protocols/ms-xca/"
                 "a8b7cb0a-92a6-4187-a23b-5e14273b96f8; SCCA fields from libyal libscca, "
                 "https://github.com/libyal/libscca/blob/d9ea0ceac5a971fa2856caf4fc6745f3b36cd9d9/documentation/Windows%20Prefetch%20File%20(PF)%20format.asciidoc; "
                 "and Velocidex, "
                 "Windows.Forensics.Prefetch.",
        "paths": ("*/Windows/Prefetch/*.pf",),
        "output_types": ["standard"],
        "artifact_icon": "file-text",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 55454 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 14460 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 19582 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 18,921 rows",
            "windows11_arm_winlogon_known_20261004": "Windows 11 build 26200 | 52128 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 11655 rows",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 3648 rows",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 0 rows (no file matches the declared paths)",
        },
    },
}


def _build_decode_table(lengths):
    """Canonical Huffman decode table over 512 symbols; index by the top 15 bits.

    Each entry packs (symbol << 4) | code_length; 0 means the prefix is unused.
    """
    bl_count = [0] * (_MAX_BITS + 1)
    for length in lengths:
        if length:
            bl_count[length] += 1
    code = 0
    next_code = [0] * (_MAX_BITS + 1)
    for bits in range(1, _MAX_BITS + 1):
        code = (code + bl_count[bits - 1]) << 1
        next_code[bits] = code
    table = [0] * (1 << _MAX_BITS)
    for symbol, length in enumerate(lengths):
        if length == 0:
            continue
        value = next_code[length]
        next_code[length] += 1
        start = value << (_MAX_BITS - length)
        end = (value + 1) << (_MAX_BITS - length)
        packed = (symbol << 4) | length
        for i in range(start, end):
            table[i] = packed
    return table


def _decompress_xpress_huffman(data, out_size):
    """Decompress an MS-XCA LZ77+Huffman stream to exactly out_size bytes."""
    out = bytearray()
    pos = 0
    size = len(data)

    def word_at(offset):
        if offset + 1 < size:
            return data[offset] | (data[offset + 1] << 8)
        if offset < size:
            return data[offset]
        return 0

    while len(out) < out_size:
        if pos + 256 > size:
            break
        lengths = [0] * 512
        for j in range(256):
            byte = data[pos + j]
            lengths[2 * j] = byte & 0x0F
            lengths[2 * j + 1] = byte >> 4
        pos += 256
        table = _build_decode_table(lengths)

        next_bits = word_at(pos) << 16
        pos += 2
        next_bits |= word_at(pos)
        pos += 2
        shift = 16

        block_end = min(out_size, len(out) + _CHUNK)
        while len(out) < block_end:
            packed = table[(next_bits >> 17) & 0x7FFF]
            if packed == 0:
                raise ValueError("no Huffman symbol for the current bits")
            symbol = packed >> 4
            code_length = packed & 15
            next_bits = (next_bits << code_length) & 0xFFFFFFFF
            shift -= code_length
            if shift < 0:
                next_bits = (next_bits + (word_at(pos) << (-shift))) & 0xFFFFFFFF
                pos += 2
                shift += 16
            value = symbol - 256
            if value < 0:
                out.append(symbol)
                continue
            offset_bits = value >> 4
            match_length = value & 15
            if match_length == 15:
                match_length = data[pos]
                pos += 1
                if match_length == 255:
                    match_length = data[pos] | (data[pos + 1] << 8)
                    pos += 2
                    if match_length == 0:
                        match_length = struct.unpack_from("<I", data, pos)[0]
                        pos += 4
                    match_length -= 15
                match_length += 15
            match_length += 3
            if offset_bits:
                match_offset = (next_bits >> (32 - offset_bits)) + (1 << offset_bits)
            else:
                match_offset = 1
            next_bits = (next_bits << offset_bits) & 0xFFFFFFFF
            shift -= offset_bits
            if shift < 0:
                next_bits = (next_bits + (word_at(pos) << (-shift))) & 0xFFFFFFFF
                pos += 2
                shift += 16
            src = len(out) - match_offset
            if src < 0:
                raise ValueError("match offset points before the output")
            for _ in range(match_length):
                out.append(out[src])
                src += 1
    return bytes(out)


def _filetime(value):
    if not value:
        return ""
    try:
        # Whole 100-nanosecond intervals cut to microseconds; dividing as a float can put the time one microsecond off either way
        # on FILETIMEs of this century, which are larger than a float holds exactly.
        return datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=value // 10)
    except (OverflowError, ValueError, OSError):
        return ""


def _utf16(data, start, length):
    return data[start:start + length].decode("utf-16-le", "replace").split("\x00")[0]


def _parse_scca(data, version):
    """Parse an uncompressed SCCA prefetch image of a supported version into a dict."""
    executable = _utf16(data, 16, 60)
    prefetch_hash = struct.unpack_from("<I", data, 76)[0]
    metrics_offset = struct.unpack_from("<I", data, 84)[0]
    if version in _FIXED_LAYOUT:
        times_at, times, run_count_at = _FIXED_LAYOUT[version]
    else:
        times_at, times, run_count_at = 128, 8, _RUN_COUNT_OFFSET.get(metrics_offset)
    run_times = []
    for i in range(times):
        stamp = _filetime(struct.unpack_from("<Q", data, times_at + 8 * i)[0])
        if stamp:
            run_times.append(stamp)
    run_count = struct.unpack_from("<I", data, run_count_at)[0] if run_count_at else ""
    filenames_offset, filenames_size = struct.unpack_from("<II", data, 100)
    volumes_offset, volumes_count, _volumes_size = struct.unpack_from("<III", data, 108)

    files = [name for name in
             data[filenames_offset:filenames_offset + filenames_size]
             .decode("utf-16-le", "replace").split("\x00") if name]

    volumes = []
    for i in range(volumes_count):
        entry = volumes_offset + i * _VOLUME_ENTRY_SIZE[version]
        device_offset, device_length = struct.unpack_from("<II", data, entry)
        created = _filetime(struct.unpack_from("<Q", data, entry + 8)[0])
        serial = struct.unpack_from("<I", data, entry + 16)[0]
        device_path = ""
        if device_offset:
            # libscca: the offset is relative to the start of the volume information.
            device_path = _utf16(data, volumes_offset + device_offset, device_length * 2)
        volumes.append((device_path, "%08X" % serial, created))

    return {
        "executable": executable,
        "prefetch_hash": "%08X" % prefetch_hash,
        "run_times": run_times,
        "run_count": run_count,
        "metrics_offset": metrics_offset,
        "version": version,
        "files": files,
        "volumes": volumes,
    }


def _parsed_prefetch(context, label):
    """Yield (relative_source, basename, parsed) for every readable .pf file."""
    for source in [str(f) for f in context.get_files_found()
                   if str(f).lower().endswith(".pf")]:
        relative_source = context.get_relative_path(source)
        try:
            with open(source, "rb") as handle:
                raw = handle.read()
            if raw[:4] == _MAM_SIGNATURE:
                uncompressed_size = struct.unpack_from("<I", raw, 4)[0]
                data = _decompress_xpress_huffman(raw[8:], uncompressed_size)
            elif raw[4:8] == _SCCA_SIGNATURE:
                data = raw
            else:
                logfunc(f"{label}: {relative_source} is neither MAM Xpress-Huffman nor SCCA, skipped")
                continue
            if data[4:8] != _SCCA_SIGNATURE:
                logfunc(f"{label}: {relative_source} has no SCCA signature, skipped")
                continue
            version = struct.unpack_from("<I", data, 0)[0]
            if version not in _SUPPORTED_VERSIONS:
                logfunc(f"{label}: {relative_source} SCCA version {version} not supported, skipped")
                continue
            yield relative_source, os.path.basename(source), _parse_scca(data, version)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f"{label}: could not read {relative_source}: {exc}")


@artifact_processor
def prefetch(context):
    data_headers = (('Last Run (UTC)', 'datetime'), 'Executable', 'Run Count',
                    'Run Times (UTC)', 'Files Loaded', 'Volume Device Path',
                    'Volume Serial', ('Volume Created (UTC)', 'datetime'),
                    'Prefetch File', 'Source File')
    data_list = []
    sources = []
    for relative_source, basename, info in _parsed_prefetch(context, "Prefetch"):
        if info["run_count"] == "" and info["version"] in (30, 31):
            logfunc(f"Prefetch: {relative_source} has file metrics offset {info['metrics_offset']}, "
                    "which is neither version 30 variant, so Run Count is blank")
        run_times = info["run_times"]
        last_run = run_times[0] if run_times else ""
        all_runs = "; ".join(str(t) for t in run_times)
        device_path, serial, created = info["volumes"][0] if info["volumes"] else ("", "", "")
        data_list.append((last_run, info["executable"], info["run_count"], all_runs,
                          len(info["files"]), device_path, serial, created,
                          basename, relative_source))
        if relative_source not in sources:
            sources.append(relative_source)
    return data_headers, data_list, "\n".join(sources)


@artifact_processor
def prefetchFilesLoaded(context):
    data_headers = ('Executable', 'Loaded File', 'Prefetch File', 'Source File')
    data_list = []
    sources = []
    for relative_source, basename, info in _parsed_prefetch(context, "Prefetch Files Loaded"):
        for loaded in info["files"]:
            data_list.append((info["executable"], loaded, basename, relative_source))
        if info["files"] and relative_source not in sources:
            sources.append(relative_source)
    return data_headers, data_list, "\n".join(sources)
