"""The secrets that open what desktop apps keep encrypted, as the command line and the window
give them to the artifacts.

Both go through dleapp.set_app_secrets: a value is the secret, or the path of a file holding
it. The window runs several times in one process, so a secret left out of a run must not keep
the value an earlier run gave. The run log records each secret given.
"""
import argparse
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import dleapp  # noqa: E402  pylint: disable=wrong-import-position
from scripts.context import Context  # noqa: E402  pylint: disable=wrong-import-position


class TestSetAppSecrets(unittest.TestCase):
    """ dleapp.set_app_secrets, for the command line and the window. """

    def setUp(self):
        self.addCleanup(dleapp.set_app_secrets, {})

    def test_a_value_is_the_secret(self):
        """ Spaces around a value are not part of it, as on the command line. """
        dleapp.set_app_secrets({'signal': '  a1b2  '})
        self.assertEqual(Context.get_app_secret('signal'), 'a1b2')

    def test_a_path_stands_for_what_the_file_holds(self):
        """ A path typed in the window is read as the command line reads it. """
        with tempfile.TemporaryDirectory() as folder:
            path = pathlib.Path(folder, 'password.txt')
            path.write_text('correct horse\n', encoding='utf-8')
            dleapp.set_app_secrets({'exodus_password': str(path)})
        self.assertEqual(Context.get_app_secret('exodus_password'), 'correct horse')

    def test_a_secret_left_out_is_cleared(self):
        """ A second run without a secret does not keep the first run's. """
        dleapp.set_app_secrets({'signal': 'first', 'threema': 'key'})
        dleapp.set_app_secrets({'threema': 'key'})
        self.assertIsNone(Context.get_app_secret('signal'))
        self.assertEqual(Context.get_app_secret('threema'), 'key')
        dleapp.set_app_secrets({})
        self.assertIsNone(Context.get_app_secret('threema'))

    def test_an_empty_file_is_refused(self):
        """ As on the command line, an empty file stops the run before it starts. """
        with tempfile.TemporaryDirectory() as folder:
            path = pathlib.Path(folder, 'empty.txt')
            path.write_text('', encoding='utf-8')
            with self.assertRaises(argparse.ArgumentError):
                dleapp.set_app_secrets({'windows_user_password': str(path)})


class TestSeveralWindowsPasswords(unittest.TestCase):
    """ A computer can have several accounts: the Windows user password may be given more than
    once, and the artifacts get them all, in order, without repeats. """

    def setUp(self):
        self.addCleanup(dleapp.set_app_secrets, {})

    def test_one_password_is_a_tuple_of_one(self):
        """ A single value works as it did, spaces around it dropped. """
        dleapp.set_app_secrets({'windows_user_password': '  pass word  '})
        self.assertEqual(Context.get_app_secret('windows_user_password'), ('pass word',))

    def test_a_repeated_option_gives_each_password(self):
        """ The command line gives a list when the option is repeated. """
        dleapp.set_app_secrets({'windows_user_password': ['first', 'second', 'first']})
        self.assertEqual(Context.get_app_secret('windows_user_password'), ('first', 'second'))

    def test_a_file_gives_one_password_per_line(self):
        """ Lines end in LF or CRLF; empty lines are skipped. """
        with tempfile.TemporaryDirectory() as folder:
            path = pathlib.Path(folder, 'passwords.txt')
            path.write_bytes(b'first\r\n\r\nsecond word\r\n')
            dleapp.set_app_secrets({'windows_user_password': [str(path), 'third']})
        self.assertEqual(Context.get_app_secret('windows_user_password'),
                         ('first', 'second word', 'third'))

    def test_lines_from_the_window_are_several_passwords(self):
        """ The window's Load from file puts the file's lines in the field. """
        dleapp.set_app_secrets({'windows_user_password': 'first\nsecond'})
        self.assertEqual(Context.get_app_secret('windows_user_password'), ('first', 'second'))

    def test_only_line_feeds_split_passwords(self):
        """ A password may hold a form feed, vertical tab or Unicode line separator. """
        password = 'a\fb\vc\x1cd\x85e\u2028f\u2029g'
        dleapp.set_app_secrets({'windows_user_password': password})
        self.assertEqual(Context.get_app_secret('windows_user_password'), (password,))
        dleapp.set_app_secrets({'windows_user_password': f'{password}\r\nsecond'})
        self.assertEqual(Context.get_app_secret('windows_user_password'), (password, 'second'))

    def test_a_file_too_long_is_refused_not_cut(self):
        """ Cutting it could leave half a password. """
        with tempfile.TemporaryDirectory() as folder:
            path = pathlib.Path(folder, 'passwords.txt')
            path.write_text('p\n' * dleapp.MULTI_VALUE_READ_LIMIT, encoding='utf-8')
            with self.assertRaises(argparse.ArgumentError):
                dleapp.set_app_secrets({'windows_user_password': str(path)})

    def test_other_secrets_stay_one_string(self):
        """ A Signal key holds no list. """
        dleapp.set_app_secrets({'signal': 'a\nb'})
        self.assertEqual(Context.get_app_secret('signal'), 'a\nb')

    def test_each_password_is_logged_on_its_own_line(self):
        """ The log says how many were given. """
        dleapp.set_app_secrets({'windows_user_password': ['first', 'second']})
        with mock.patch.object(dleapp, 'logfunc') as logged:
            dleapp.log_supplied_secrets()
        self.assertEqual([call.args[0] for call in logged.call_args_list],
                         ['Windows user password 1 of 2: first',
                          'Windows user password 2 of 2: second'])


class TestEveryPasswordIsTriedOnEveryAccount(unittest.TestCase):
    """ The two DPAPI pools make candidates from each password for each account SID. """

    def test_both_pools(self):
        """ Two passwords and two SIDs give four password candidate calls in each pool. """
        from scripts.chromium import windows_oscrypt  # pylint: disable=import-outside-toplevel
        from scripts.artifacts import windowsUserVaultCredentials as vault  # pylint: disable=import-outside-toplevel
        for module in (windows_oscrypt, vault):
            with mock.patch.object(module.dpapiprobe, 'user_master_key_candidates',
                                   return_value=[]) as candidates:
                module._unlocked_pool({'S-1-5-21-1': [], 'S-1-5-21-2': []}, [],  # pylint: disable=protected-access
                                      ('first', 'second'))
            self.assertEqual(sorted((call.args[0], call.kwargs['password'])
                                    for call in candidates.call_args_list),
                             [('S-1-5-21-1', 'first'), ('S-1-5-21-1', 'second'),
                              ('S-1-5-21-2', 'first'), ('S-1-5-21-2', 'second')],
                             module.__name__)


class TestCheckSuppliedSecret(unittest.TestCase):
    """ The window's check: it refuses what the run would refuse, and never quotes the text. """

    def test_a_value_or_a_file_that_holds_one_passes(self):
        """ Nothing to say about a value, nor about a file that holds something. """
        dleapp.check_supplied_secret('a password')
        with tempfile.TemporaryDirectory() as folder:
            path = pathlib.Path(folder, 'key.txt')
            path.write_text('a' * 64, encoding='utf-8')
            dleapp.check_supplied_secret(str(path))

    def test_an_empty_file_is_named_without_its_path(self):
        """ The message says why, and does not repeat what was typed. """
        with tempfile.TemporaryDirectory() as folder:
            path = pathlib.Path(folder, 'empty.txt')
            path.write_text('', encoding='utf-8')
            with self.assertRaises(ValueError) as caught:
                dleapp.check_supplied_secret(str(path))
        self.assertNotIn(folder, str(caught.exception))


class TestLogSuppliedSecrets(unittest.TestCase):
    """ The run log records the secrets given, and nothing for those not given. """

    def setUp(self):
        self.addCleanup(dleapp.set_app_secrets, {})

    def test_each_secret_given_is_logged_once(self):
        """ One line for each secret given, under its command line name. """
        dleapp.set_app_secrets({'signal': 'sig', 'exodus_password': 'pass word'})
        with mock.patch.object(dleapp, 'logfunc') as logged:
            dleapp.log_supplied_secrets()
        self.assertEqual([call.args[0] for call in logged.call_args_list],
                         ['Signal key: sig', 'Exodus password: pass word'])


class TestWindowFields(unittest.TestCase):
    """ data/leapp_config.json names each secret field after the secret artifacts ask for. """

    def test_every_field_is_a_secret_artifacts_read(self):
        """ A field the run does not know would be typed for nothing. """
        config = json.loads((REPO_ROOT / 'data' / 'leapp_config.json').read_text(encoding='utf-8'))
        for field in config['secrets']['fields']:
            self.assertIn(field['name'], dleapp.APP_SECRETS, field['name'])
            self.assertEqual(field.get('kind'), 'text', field['name'])
            self.assertEqual(field.get('check'), 'dleapp:check_supplied_secret', field['name'])


if __name__ == '__main__':
    unittest.main()
