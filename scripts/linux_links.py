"""What an extraction recorded about a staged Linux file, for DLEAPP artifacts that report a symbolic link rather
than follow it.

The seekers stage bytes. The tar seeker writes a symbolic link as an empty file, the zip seeker writes the target a
stored link holds as the file's content, the folder seeker copies the file a link inside the input folder points to
and returns, without staging anything, a link that resolves outside it, and the raw image seeker lists no links. So
an artifact that must not follow a link asks the seeker, or the input folder, what the source holds.
"""

import os
from datetime import datetime, timezone


def seeker_of(context):
    """The seeker the run uses, or None where the context has none."""
    try:
        return context.get_seeker()
    except ValueError:
        return None


def recorded_link(seeker, path):
    """The target of a symbolic link, as the input folder holds it or the tar or zip holding it recorded it, for a
    path the seeker returned; None when the file is not a link or where it came from cannot say."""
    if getattr(seeker, 'directory', None):
        full = in_folder(seeker, path)
        return os.readlink(full) if os.path.islink(full) else None
    info = getattr(seeker, 'file_infos', {}).get(path)
    source = getattr(info, 'source_path', None)
    if not source:
        return None
    archive = getattr(seeker, 'tar_file', None)
    if archive is not None:
        member = archive.getmember(source)
        return member.linkname if member.issym() else None
    archive = getattr(seeker, 'zip_file', None)
    if archive is not None:
        member = archive.getinfo(source)
        if (member.external_attr >> 16) & 0o170000 != 0o120000:
            return None
        with open(path, 'rb') as handle:
            return handle.read().decode('utf-8', errors='replace')
    return None


def in_folder(seeker, path):
    """The path in the input folder that a path the folder seeker returned stands for. The seeker returns a path,
    without staging anything there, for a folder and for a link that resolves outside the input or to something that
    is not a file, and the path it returns keeps a backslash in a file name that its recorded source path turns into
    /; the recorded path covers a file it staged under another name to keep two sources apart."""
    staged = os.path.join(seeker.directory, os.path.relpath(path, seeker.data_folder))
    info = seeker.file_infos.get(path)
    if os.path.lexists(staged) or info is None:
        return staged
    return os.path.join(seeker.directory, info.source_path)


def recorded_time(seeker, path, link):
    """The modified time the seeker recorded for a path it returned, for a link in an input folder the link's own,
    or ''."""
    info = getattr(seeker, 'file_infos', {}).get(path)
    value = getattr(info, 'modification_date', None)
    if link is not None and getattr(seeker, 'directory', None):
        value = os.lstat(in_folder(seeker, path)).st_mtime
    if isinstance(value, (int, float)) and value > 0:
        try:
            return datetime.fromtimestamp(value, timezone.utc)
        except (OverflowError, OSError, ValueError):
            return ''
    return ''
