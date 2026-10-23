"""Writes the public fixture for the TeleGuard Windows module: an authored store.

Every id, name, text and time here is written for the fixture; no part of it
comes from a real client. Two profiles carry the same stored ids on purpose, so
the fixture shows that a conversation stays apart per source file.

Run it, then hand the archive to the repo's case-data tool:

    python admin/test/scripts/make_teleguard_desktop_fixture.py \
        --archive teleguard_synthetic.zip
    python admin/test/scripts/make_case_data.py teleguardDesktop \
        --case 1 --input teleguard_synthetic.zip

The archive holds a tree of the layout the Windows client writes: two
`teleguard_desktop` folders, each with the store, valid image, PDF and unreferenced image files, an
empty log, a `-wal` sidecar and the client's own `teleguard_temp.db`.
"""

import base64
import json
import os
import pathlib
import sqlite3
import zipfile
import argparse

# 2024-01-05 09:15 UTC; the fixture's messages run from this minute on.
FIXTURE_TIME = 1704446100000

# Valid independently generated tiny images and a one-page PDF.
JPEG = base64.b64decode(
    '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAACAAIDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwDjaKKK8c/VD//Z')
JPEG_SECOND = base64.b64decode(
    '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAACAAIDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwDzOiiiv1Q8Q//Z')
PNG = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAFklEQVR4nGMUWWXEwMDAxMDAwMDAAAALTAD02i3WoAAAAABJRU5ErkJggg==')
PNG_SECOND = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAFklEQVR4nGM8sU+EgYGBiYGBgYGBAQAUFgGeRgTp0QAAAABJRU5ErkJggg==')
PDF = base64.b64decode(
    'JVBERi0xLjMKJeLjz9MKMSAwIG9iago8PAovUHJvZHVjZXIgKHB5cGRmKQo+PgplbmRvYmoKMiAwIG9iago8PAovVHlwZSAvUGFnZXMKL0NvdW50IDEKL0tpZHMgWyA0IDAgUiBdCj4+CmVuZG9iagozIDAgb2JqCjw8Ci9UeXBlIC9DYXRhbG9nCi9QYWdlcyAyIDAgUgo+PgplbmRvYmoKNCAwIG9iago8PAovVHlwZSAvUGFnZQovUmVzb3VyY2VzIDw8Cj4+Ci9NZWRpYUJveCBbIDAuMCAwLjAgNzIgNzIgXQovUGFyZW50IDIgMCBSCj4+CmVuZG9iagp4cmVmCjAgNQowMDAwMDAwMDAwIDY1NTM1IGYgCjAwMDAwMDAwMTUgMDAwMDAgbiAKMDAwMDAwMDA1NCAwMDAwMCBuIAowMDAwMDAwMTEzIDAwMDAwIG4gCjAwMDAwMDAxNjIgMDAwMDAgbiAKdHJhaWxlcgo8PAovU2l6ZSA1Ci9Sb290IDMgMCBSCi9JbmZvIDEgMCBSCj4+CnN0YXJ0eHJlZgoyNTQKJSVFT0YK')

# id, chatId, sender, parentId, receiver, content, createDate, type,
# userTime, status, isEdited, metadata
MESSAGES = (
    ('a1', '10', 'aa', None, 'bb', 'Erste line', FIXTURE_TIME,
     'TEXT', FIXTURE_TIME + 300, 'READ', 0,
     '{"client-version":"4.0.1"}'),
    ('a2', '10', 'bb', None, 'aa', 'Zweite line', FIXTURE_TIME + 90000,
     'TEXT', FIXTURE_TIME + 90100, 'READ', 1,
     '{"client-version":"4.0.1","isContentExpired":1}'),
    ('a3', '10', 'aa', None, 'cc', 'Dritte line', FIXTURE_TIME + 180000,
     'TEXT', None, 'SENT', 0,
     '{"client-version":"4.0.2","isLocalized":1}'),
    ('a4', '11', 'aa', None, 'dd',
     json.dumps({'de': 'Viola', 'en': 'Violet', 'ru': 'Violeta'}),
     FIXTURE_TIME + 240000, 'TEXT', FIXTURE_TIME + 240100, 'READ', 0,
     '{"isLocalized":1,"client-version":"4.0.3"}'),
    ('a5', '11', 'dd', None, 'aa', 'Foto?', FIXTURE_TIME + 300000,
     'MEDIA', FIXTURE_TIME + 300001, 'READ', 0,
     '{"mediaFiles":[{"id":"m-1","name":"example_photo.jpeg",'
     '"mediaType":"IMAGE","order":0,"duration":null,"aspectRatio":1.5,'
     '"blurHash":"Qz","cacheName":"example_photo.jpeg",'
     '"thumbnailCacheName":"example_photo.jpeg"}],'
     '"mediaType":"IMAGE","client-version":"4.0.3"}'),
    ('a6', '11', 'aa', 'a5', 'dd', 'Re: Foto?', FIXTURE_TIME + 360000,
     'QUOTE', FIXTURE_TIME + 360001, 'READ', 0,
     '{"quote":"Foto?","messageId":"a5","author":"dd",'
     '"quotedMessageType":"MEDIA","replyType":"DIRECT",'
     '"client-version":"4.0.4"}'),
    ('a7', '10', 'aa', None, 'bb', 'Anhang', FIXTURE_TIME + 420000,
     'FILE', FIXTURE_TIME + 420001, 'READ', 0,
     '{"files":{"f-1":"example_document.pdf"},"mediaType":"FILE",'
     '"client-version":"4.0.4"}'),
    ('a8', '10', 'aa', 'a7', 'bb', 'Forwarded note', FIXTURE_TIME + 480000,
     'FORWARD', FIXTURE_TIME + 480001, 'READ', 0,
     '{"forward":{"from":"10","originDate":1704359700000},'
     '"client-version":"4.0.5"}'),
    ('a9', '10', None, None, 'aa', 'System banner', FIXTURE_TIME + 540000,
     'SERVICE', None, 'STATIC', 0,
     '{"isLocalized":1,"content":{"de":"System"}}'),
    ('a10', '10', 'bb', None, 'aa', 'Anruf', FIXTURE_TIME + 600000,
     'CALL', FIXTURE_TIME + 600001, 'READ', 0,
     '{"callType":"voice","isSuccessfull":1,"membersText":"Bob",'
     '"client-version":"4.0.6"}'),
    ('a11', '10', 'zz', None, 'aa', 'Unknown kind', FIXTURE_TIME + 660000,
     'WIDGET', FIXTURE_TIME + 660001, 'RECEIVED', 0,
     '{"client-version":"4.0.7"}'),
    ('a12', '10', 'aa', None, 'bb', 'Not JSON', FIXTURE_TIME + 720000,
     'TEXT', FIXTURE_TIME + 720001, 'READ', 0,
     'plain text, not JSON'),
)

# serverId, alias, type, color, avatar, lastActivityTime, options, info,
# lastVisitTime, personalId
CONTACTS = (
    ('aa', 'Alice', 'PERSON', None, JPEG, FIXTURE_TIME, '{"key":"k1"}',
     '{"avatarId":"av-1"}', FIXTURE_TIME + 1000, 'synthetic-person-aa'),
    ('bb', 'Bob', 'PERSON', None, None, FIXTURE_TIME + 2000, None, None,
     None, None),
    ('cc', 'Carolin', 'PERSON', None, PNG, None, None, None, None, None),
    ('dd', 'Dora', 'PERSON', None, None, FIXTURE_TIME + 4000, None, None,
     None, None),
    ('11', 'Example Group', 'GROUP', None, None, None, None, None, None,
     None),
    ('ee', 'Unused Contact', 'PERSON', None, None, None, None, None, None,
     None),
)


def write_store(directory, second=False):
    """Write one store of the tested layout into `directory`."""
    path = directory / 'teleguard_database.db'
    connection = sqlite3.connect(str(path))
    try:
        connection.execute(
            'CREATE TABLE messages(id TEXT, chatId TEXT, sender TEXT,'
            ' parentId TEXT, receiver TEXT, content TEXT, createDate INTEGER,'
            ' type TEXT, userTime INTEGER, status TEXT, isEdited INTEGER,'
            " metadata TEXT DEFAULT '{}')")
        connection.execute('CREATE TABLE service(id TEXT, data TEXT)')
        connection.execute(
            'CREATE TABLE contacts(serverId TEXT, alias TEXT, type TEXT,'
            ' color BLOB, avatar BLOB, lastActivityTime INTEGER,'
            ' options TEXT, info TEXT, lastVisitTime INTEGER,'
            ' personalId TEXT)')
        contacts = tuple(tuple((JPEG_SECOND if value == JPEG else PNG_SECOND)
                               if isinstance(value, bytes) and second else value
                               for value in row) for row in CONTACTS)
        for table, rows in (('messages', MESSAGES), ('contacts', contacts)):
            for row in rows:
                connection.execute(
                    f'INSERT INTO {table} VALUES ('
                    + ', '.join('?' * len(row)) + ')', row)
        connection.execute('INSERT INTO service VALUES (?, ?)',
                           ('user', json.dumps({'serverId': 'aa',
                                               'alias': 'Alice',
                                               'privateKey': 'private-value',
                                               'publicKey': 'public-value'})))
        connection.execute('INSERT INTO service VALUES (?, ?)',
                           ('settings', json.dumps({'theme': 'dark'})))
        for empty in ('channels', 'posts', 'sipcalls'):
            connection.execute(f'CREATE TABLE {empty}(id TEXT)')
    finally:
        connection.commit()
        connection.close()
    return path


def build(root):
    """Write the fixture tree: two profiles of the layout the client writes."""
    for profile in ('profile-one', 'profile-two'):
        app = root / 'AppData' / 'Roaming' / profile / 'teleguard_desktop'
        app.mkdir(parents=True)
        write_store(app, second=profile == 'profile-two')
        (app / 'example_photo.jpeg').write_bytes(
            JPEG_SECOND if profile == 'profile-two' else JPEG)
        (app / 'unreferenced_image.png').write_bytes(
            PNG_SECOND if profile == 'profile-two' else PNG)
        (app / 'example_document.pdf').write_bytes(PDF)
        (app / 'teleguard_app.log').write_bytes(b'')
        (app / 'teleguard_database.db-wal').write_bytes(b'')
        temp = sqlite3.connect(str(app / 'teleguard_temp.db'))
        try:
            temp.execute('CREATE TABLE draft(text TEXT)')
        finally:
            temp.commit()
            temp.close()
    return root


def pack(root, archive):
    """Zip the fixture tree, keeping the tree's own top folder."""
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as packed:
        for path in sorted(root.rglob('*')):
            if path.is_dir():
                continue
            info = zipfile.ZipInfo(path.relative_to(root.parent).as_posix(),
                                   date_time=(2025, 6, 2, 7, 0, 0))
            packed.writestr(info, path.read_bytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--tree', default='teleguard_fixture',
                       help='folder the fixture tree is written into')
    parser.add_argument('--archive', default='teleguard_synthetic.zip',
                       help='archive the tree is packed into')
    args = parser.parse_args()
    root = pathlib.Path(args.tree) / 'extraction'
    if root.exists():
        raise SystemExit(f'{root} exists, remove it first')
    build(root)
    pack(root, args.archive)
    print(args.archive, os.path.getsize(args.archive))


if __name__ == '__main__':
    main()
