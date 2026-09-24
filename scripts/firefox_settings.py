"""Firefox permission and extension inventory readers.

Author: @AlexisBrignoni, Codex. Public tests use independently authored data only.
"""

import json
from pathlib import PurePosixPath

from scripts.firefox import columns, optional, timestamp
from scripts.ilapfuncs import logfunc
from scripts.macos_plists import unique_sources, user_from_path


def permissions(db):
    """Prefer the current store, even if empty, over a leftover migration table."""
    if columns(db, 'moz_perms'):
        table, origin = 'moz_perms', 'origin'
    elif columns(db, 'moz_hosts'):
        table, origin = 'moz_hosts', 'host'
    else:
        return
    names = ('modificationTime', 'expireTime', 'id', origin, 'type', 'permission', 'expireType')
    for row in db.execute(f'SELECT {optional(db, table, names)} FROM {table} ORDER BY id'):
        yield (timestamp(row['modificationTime'], 1000), timestamp(row['expireTime'], 1000),
               row['id'], row[origin], row['type'], row['permission'], row['expireType'], table)


def _json(value):
    return '' if value is None else json.dumps(value, ensure_ascii=False, sort_keys=True)


def extensions(document):
    """Only extension records; do not infer execution or a manual installation."""
    if not isinstance(document, dict) or not isinstance(document.get('addons'), list):
        raise ValueError('Expected an addons array')
    for addon in document['addons']:
        if not isinstance(addon, dict) or addon.get('type') != 'extension':
            continue
        locale = addon.get('defaultLocale')
        locale = locale if isinstance(locale, dict) else {}
        yield (timestamp(addon.get('installDate'), 1000), timestamp(addon.get('updateDate'), 1000),
               addon.get('id'), locale.get('name'), addon.get('version'), addon.get('location'),
               addon.get('active'), addon.get('userDisabled'), addon.get('appDisabled'),
               addon.get('sourceURI'), addon.get('path'),
               _json(addon.get('userPermissions')), _json(addon.get('optionalPermissions')))


def read_extensions(context):
    candidates = [str(p) for p in context.get_files_found()
                  if PurePosixPath(str(p).replace('\\', '/')).name == 'extensions.json']
    paths, _ = unique_sources(context, candidates, label='Firefox Extensions')
    result, sources = [], []
    for path in paths:
        relative = context.get_relative_path(path)
        normalized = str(relative).replace('\\', '/')
        profile = PurePosixPath(normalized).parent.name
        user = user_from_path(relative)
        if not user:
            parts = normalized.split('/')
            if 'home' in parts and parts.index('home') + 1 < len(parts):
                user = parts[parts.index('home') + 1]
        try:
            with open(path, encoding='utf-8') as handle:
                rows = list(extensions(json.load(handle)))
        except (OSError, ValueError, TypeError, UnicodeError):
            logfunc('Firefox Extensions: could not read a profile extension inventory')
            continue
        result.extend(row + (profile, user, relative) for row in rows)
        sources.append(path)
    return result, '\n'.join(sources)
