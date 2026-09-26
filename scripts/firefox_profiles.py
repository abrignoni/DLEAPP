"""Firefox profile bookkeeping readers. Author: @AlexisBrignoni, Claude.

profiles.ini and installs.ini are written by toolkit/profile/nsToolkitProfileService.cpp,
and each profile's times.json by toolkit/modules/ProfileAge.sys.mjs, both at
mozilla-firefox/firefox c32abda0190531351e22da36334f18f9e994d474. The artifact notes cite
the lines.
"""

import configparser
import json
from pathlib import PurePosixPath

from scripts.firefox import timestamp
from scripts.ilapfuncs import logfunc
from scripts.macos_plists import unique_sources, user_from_path

_PROFILE_KEYS = ('Name', 'Path', 'IsRelative', 'Default', 'Locked', 'StoreID', 'ShowSelector')


def _user(relative):
    parts = str(relative).replace('\\', '/').split('/')
    user = user_from_path(relative)
    if not user and 'home' in parts and parts.index('home') + 1 < len(parts):
        user = parts[parts.index('home') + 1]
    return parts, user


def ini_rows(text):
    """One row of values per section of a profiles.ini or installs.ini."""
    parser = configparser.RawConfigParser(strict=False, interpolation=None)
    parser.optionxform = str
    parser.read_string(text)
    for section in parser.sections():
        values = dict(parser.items(section))
        other = '; '.join(f'{k}={v}' for k, v in values.items() if k not in _PROFILE_KEYS)
        yield (section,) + tuple(values.get(key, '') for key in _PROFILE_KEYS) + (other,)


def read_profile_list(context, label):
    found = [str(p) for p in context.get_files_found()
             if PurePosixPath(str(p).replace('\\', '/')).name in ('profiles.ini', 'installs.ini')]
    paths, _ = unique_sources(context, found, label=label)
    output, sources = [], []
    for path in paths:
        relative = context.get_relative_path(path)
        parts, user = _user(relative)
        try:
            with open(path, 'r', encoding='utf-8-sig', errors='replace') as handle:
                rows = list(ini_rows(handle.read()))
        except (OSError, configparser.Error) as exc:
            logfunc(f'{label}: {relative} was not read ({exc})')
            continue
        output.extend(row + (parts[-1], user) for row in rows)
        sources.append(path)
    return output, '\n'.join(sources)


def times_row(times):
    """Row values from a parsed times.json."""
    ms = 1000
    return (timestamp(times.get('created'), ms), timestamp(times.get('firstUse'), ms),
            timestamp(times.get('reset'), ms), timestamp(times.get('recoveredFromBackup'), ms),
            '' if times.get('source') is None else str(times.get('source')))


def read_profile_times(context, label):
    found = [str(p) for p in context.get_files_found()
             if PurePosixPath(str(p).replace('\\', '/')).name == 'times.json']
    paths, _ = unique_sources(context, found, label=label)
    output, sources = [], []
    for path in paths:
        relative = context.get_relative_path(path)
        parts, user = _user(relative)
        try:
            with open(path, 'r', encoding='utf-8') as handle:
                times = json.load(handle)
            if not isinstance(times, dict):
                raise ValueError('not a JSON object')
        except (OSError, ValueError, UnicodeDecodeError) as exc:
            logfunc(f'{label}: {relative} was not read ({exc})')
            continue
        profile = parts[-2] if len(parts) >= 2 else ''
        output.append(times_row(times) + (profile, user))
        sources.append(path)
    return output, '\n'.join(sources)


def container_rows(data):
    """One row per identity in a parsed containers.json."""
    identities = data.get('identities') if isinstance(data, dict) else None
    version = '' if not isinstance(data, dict) or data.get('version') is None else str(data.get('version'))
    for identity in identities if isinstance(identities, list) else []:
        if not isinstance(identity, dict):
            continue
        yield tuple('' if identity.get(key) is None else str(identity.get(key))
                    for key in ('userContextId', 'name', 'l10nId', 'public', 'icon', 'color',
                                'policyId')) + (version,)


def read_containers(context, label):
    found = [str(p) for p in context.get_files_found()
             if PurePosixPath(str(p).replace('\\', '/')).name == 'containers.json']
    paths, _ = unique_sources(context, found, label=label)
    output, sources = [], []
    for path in paths:
        relative = context.get_relative_path(path)
        parts, user = _user(relative)
        try:
            with open(path, 'r', encoding='utf-8') as handle:
                rows = list(container_rows(json.load(handle)))
        except (OSError, ValueError, UnicodeDecodeError) as exc:
            logfunc(f'{label}: {relative} was not read ({exc})')
            continue
        profile = parts[-2] if len(parts) >= 2 else ''
        output.extend(row + (profile, user) for row in rows)
        sources.append(path)
    return output, '\n'.join(sources)
