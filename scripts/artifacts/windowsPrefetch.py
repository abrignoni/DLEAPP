"""Windows Prefetch parser for DLEAPP.

Author: @AlexisBrignoni, Claude.
Inspired by the Velociraptor exchange Windows.Forensics.Prefetch artifact.

A Windows 8+ prefetch file (.pf) is a MAM/Xpress-Huffman compressed container
around the SCCA prefetch structure. The decompressor below is an original
implementation of the LZ77+Huffman (Xpress Huffman) algorithm from the public
[MS-XCA] specification (Microsoft grants the right to implement it); it uses only
the standard library. The SCCA version 30 structure that Windows 10 and 11 write
is then parsed with the field offsets from the libyal libscca format
documentation. Both are cited in the notes.
"""

import os
import struct
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc

_MAM_SIGNATURE = b"MAM\x04"       # Xpress Huffman, no checksum
_SCCA_SIGNATURE = b"SCCA"
_SUPPORTED_VERSION = 30           # Windows 10 and 11
_MAX_BITS = 15
_CHUNK = 65536

__artifacts_v2__ = {
    "prefetch": {
        "name": "Prefetch",
        "description": "Programs Windows prepared to run, from the .pf prefetch "
                       "files: the executable, run count, up to eight run times, and "
                       "the source volume.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-16",
        "last_update_date": "2026-09-16",
        "requirements": "none",
        "category": "Windows",
        "notes": "One row per prefetch file. Executable is the name stored in the "
                 "file's header. Run Count is the total number of times the program "
                 "was prepared to run. Last Run (UTC) is the most recent of the "
                 "recorded run times and Run Times (UTC) lists all of them, newest "
                 "first (Windows keeps up to eight). Files Loaded is the number of "
                 "files the run referenced. Volume Device Path, Volume Serial and "
                 "Volume Created (UTC) describe the first volume the file records; a "
                 "prefetch file can reference more than one volume, and only the "
                 "first is shown on this row. Prefetch File is the .pf file name. A "
                 "prefetch file records that Windows prepared an executable to run, "
                 "with up to eight of the most recent run times (newest first) and a "
                 "total run count. It is evidence that the program ran, not who ran "
                 "it. The .pf file is MAM Xpress-Huffman compressed; it is "
                 "decompressed in memory with an original implementation of the "
                 "MS-XCA LZ77+Huffman algorithm and the SCCA version 30 structure "
                 "that Windows 10 and 11 write is then parsed. A .pf whose format is "
                 "not MAM Xpress-Huffman or whose SCCA version is not 30 is skipped "
                 "with a note in the run log. Times are Windows FILETIMEs shown in "
                 "UTC; a 0 or out-of-range value is blank. Format: original MS-XCA "
                 "implementation, https://learn.microsoft.com/en-us/openspecs/"
                 "windows_protocols/ms-xca/a8b7cb0a-92a6-4187-a23b-5e14273b96f8; "
                 "SCCA fields from libyal libscca, https://github.com/libyal/libscca/"
                 "blob/main/documentation/Windows%20Prefetch%20File%20(PF)%20format."
                 "asciidoc; and Velocidex, Windows.Forensics.Prefetch.",
        "paths": ("*/Windows/Prefetch/*.pf",),
        "output_types": ["standard"],
        "artifact_icon": "activity",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 527 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 184 rows",
        },
    },
    "prefetchFilesLoaded": {
        "name": "Prefetch Files Loaded",
        "description": "Files each prefetched program referenced when it ran, from "
                       "the .pf prefetch files: one row per referenced file.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-16",
        "last_update_date": "2026-09-16",
        "requirements": "none",
        "category": "Windows",
        "notes": "One row per file referenced by a prefetch file, so an executable "
                 "with many loaded files produces many rows. Executable is the name "
                 "from the prefetch header and Loaded File is the referenced path as "
                 "stored, usually in \\VOLUME{...}\\ form naming the volume by its "
                 "GUID and serial. Prefetch File is the .pf file name. The list is "
                 "what the program referenced when it was prepared to run, which "
                 "includes its own image, its DLLs and data files it opened. A "
                 "prefetch file records that Windows prepared an executable to run. "
                 "It is evidence that the program ran, not who ran it. The .pf file "
                 "is MAM Xpress-Huffman compressed; it is decompressed in memory "
                 "with an original implementation of the MS-XCA LZ77+Huffman "
                 "algorithm and the SCCA version 30 structure that Windows 10 and 11 "
                 "write is then parsed. A .pf whose format is not MAM Xpress-Huffman "
                 "or whose SCCA version is not 30 is skipped with a note in the run "
                 "log. Format: original MS-XCA implementation, https://"
                 "learn.microsoft.com/en-us/openspecs/windows_protocols/ms-xca/"
                 "a8b7cb0a-92a6-4187-a23b-5e14273b96f8; SCCA fields from libyal "
                 "libscca, https://github.com/libyal/libscca/blob/main/documentation/"
                 "Windows%20Prefetch%20File%20(PF)%20format.asciidoc; and Velocidex, "
                 "Windows.Forensics.Prefetch.",
        "paths": ("*/Windows/Prefetch/*.pf",),
        "output_types": ["standard"],
        "artifact_icon": "file-text",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 55454 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 14460 rows",
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
        return datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=value / 10)
    except (OverflowError, ValueError, OSError):
        return ""


def _utf16(data, start, length):
    return data[start:start + length].decode("utf-16-le", "replace").split("\x00")[0]


def _parse_scca_v30(data):
    """Parse a decompressed SCCA version 30 prefetch image into a dict."""
    executable = _utf16(data, 16, 60)
    prefetch_hash = struct.unpack_from("<I", data, 76)[0]
    run_times = []
    for i in range(8):
        stamp = _filetime(struct.unpack_from("<Q", data, 128 + 8 * i)[0])
        if stamp:
            run_times.append(stamp)
    run_count = struct.unpack_from("<I", data, 208)[0]
    filenames_offset, filenames_size = struct.unpack_from("<II", data, 100)
    volumes_offset, volumes_count, _volumes_size = struct.unpack_from("<III", data, 108)

    files = [name for name in
             data[filenames_offset:filenames_offset + filenames_size]
             .decode("utf-16-le", "replace").split("\x00") if name]

    volumes = []
    for i in range(volumes_count):
        entry = volumes_offset + i * 96
        device_offset, device_length = struct.unpack_from("<II", data, entry)
        created = _filetime(struct.unpack_from("<Q", data, entry + 8)[0])
        serial = struct.unpack_from("<I", data, entry + 16)[0]
        device_path = ""
        if device_offset:
            device_path = _utf16(data, entry + device_offset, device_length * 2)
        volumes.append((device_path, "%08X" % serial, created))

    return {
        "executable": executable,
        "prefetch_hash": "%08X" % prefetch_hash,
        "run_times": run_times,
        "run_count": run_count,
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
            if raw[:4] != _MAM_SIGNATURE:
                logfunc(f"{label}: {relative_source} is not MAM Xpress-Huffman, skipped")
                continue
            uncompressed_size = struct.unpack_from("<I", raw, 4)[0]
            data = _decompress_xpress_huffman(raw[8:], uncompressed_size)
            if data[4:8] != _SCCA_SIGNATURE:
                logfunc(f"{label}: {relative_source} has no SCCA signature, skipped")
                continue
            version = struct.unpack_from("<I", data, 0)[0]
            if version != _SUPPORTED_VERSION:
                logfunc(f"{label}: {relative_source} SCCA version {version} not supported, skipped")
                continue
            yield relative_source, os.path.basename(source), _parse_scca_v30(data)
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
