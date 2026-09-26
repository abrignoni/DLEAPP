"""Pin the TaskCache value readers in scripts/artifacts/windowsTaskCache.py.

DynamicInfo values follow the 36-byte layout in winreg-kb's Task Scheduler notes. Actions
values follow the layout measured against task XML definitions: a 16-bit version, the
context, then per action a 16-bit type and its ID, with an Exec action's command,
arguments and working directory or a COM handler's 16-byte class ID and data, each
string in UTF-16LE after its 32-bit byte length. Expected values are written out.
"""
import os
import pathlib
import struct
import sys
import tempfile
import unittest
import uuid

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import windowsTaskCache as taskcache  # pylint: disable=wrong-import-position


def lstr(text):
    raw = text.encode('utf-16-le')
    return struct.pack('<i', len(raw)) + raw


def exec_actions(command, arguments, working_directory, action_id='', context='Author'):
    return (struct.pack('<H', 3) + lstr(context) + struct.pack('<H', 0x6666) + lstr(action_id)
            + lstr(command) + lstr(arguments) + lstr(working_directory) + b'\x00\x00')


CLSID = uuid.UUID('A6BA00FE-40E8-477C-B713-C64A14F18ADB')


def com_actions(data, action_id=''):
    return (struct.pack('<H', 3) + lstr('LocalSystem') + struct.pack('<H', 0x7777) + lstr(action_id)
            + CLSID.bytes_le + lstr(data))


class DynamicInfoTest(unittest.TestCase):
    def test_fields(self):
        raw = struct.pack('<IQQIIQ', 3, 132139579870000000, 132139580000000000, 0, 0x800710E0,
                          132139581000000000)
        self.assertEqual(taskcache.dynamic_info(raw),
                         {'registered': 132139579870000000, 'last_start': 132139580000000000,
                          'last_result': 0x800710E0, 'last_stop': 132139581000000000})

    def test_short_values(self):
        self.assertIsNone(taskcache.dynamic_info(b'\x03\x00\x00\x00'))
        seven = struct.pack('<IQQII', 3, 1, 2, 0, 0)
        self.assertEqual(taskcache.dynamic_info(seven)['last_stop'], 0)


class ActionsTest(unittest.TestCase):
    def test_exec(self):
        action = taskcache.first_action(exec_actions('%windir%\\system32\\sc.exe', 'start w32time', ''))
        self.assertEqual((action['context'], action['type'], action['command'], action['arguments'],
                          action['working_directory']),
                         ('Author', 'Exec', '%windir%\\system32\\sc.exe', 'start w32time', ''))

    def test_exec_with_an_action_id(self):
        action = taskcache.first_action(exec_actions('cmd.exe', '/c x', 'C:\\', action_id='StartAction'))
        self.assertEqual((action['command'], action['arguments'], action['working_directory']),
                         ('cmd.exe', '/c x', 'C:\\'))

    def test_com_handler(self):
        action = taskcache.first_action(com_actions('<Data>1</Data>'))
        self.assertEqual((action['type'], action['class_id'], action['data'], action['command']),
                         ('COM handler', '{A6BA00FE-40E8-477C-B713-C64A14F18ADB}', '<Data>1</Data>', ''))

    def test_other_types_are_named_not_decoded(self):
        raw = struct.pack('<H', 3) + lstr('Author') + struct.pack('<H', 0x8888) + b'\x00' * 8
        self.assertEqual(taskcache.first_action(raw)['type'], '0x8888 (not decoded)')

    def test_lengths_past_the_value_are_refused(self):
        raw = exec_actions('cmd.exe', '', '')
        with self.assertRaises(ValueError):
            taskcache.first_action(raw[:20])
        # A context whose stated length (1000 bytes) is longer than what follows it.
        overlong = struct.pack('<H', 3) + struct.pack('<i', 1000) + 'Author'.encode('utf-16-le') + b'\x00' * 8
        with self.assertRaises(ValueError):
            taskcache.first_action(overlong)
        # The last string of an action is followed by nothing that would catch an overrun.
        raw = exec_actions('cmd.exe', '/c x', 'C:\\')
        at = raw.rindex('C:\\'.encode('utf-16-le')) - 4
        truncated_dir = raw[:at] + struct.pack('<i', 1000) + raw[at + 4:]
        with self.assertRaises(ValueError):
            taskcache.first_action(truncated_dir)


class _Context:
    def __init__(self, root, files):
        self.root, self.files = root, files

    def get_files_found(self):
        return self.files

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root)


class DefinitionFilesTest(unittest.TestCase):
    def test_only_files_of_the_same_volume(self):
        with tempfile.TemporaryDirectory() as root:
            files = []
            for volume, name in (('p3', 'Task One'), ('p4', 'Task Two')):
                path = os.path.join(root, volume, 'Windows', 'System32', 'Tasks', 'Microsoft', name)
                os.makedirs(os.path.dirname(path))
                with open(path, 'w', encoding='utf-8') as handle:
                    handle.write('<Task/>')
                files.append(path)
            found = taskcache.definition_files(_Context(root, files), '/p3')
        self.assertEqual(found, {'\\microsoft\\task one'})


if __name__ == '__main__':
    unittest.main()
