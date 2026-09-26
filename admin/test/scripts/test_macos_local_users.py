"""Pin the macOS local account readers in scripts/artifacts/macosLocalUsers.py.

The records below follow the shapes on dleapp_macos_bigsur: account values are arrays,
accountPolicyData holds a binary property list as data, and LinkedIdentity holds an XML
property list as text. The expected values are written out, never read back from the code.
"""
import pathlib
import plistlib
import sys
import unittest
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.artifacts import macosLocalUsers as users  # pylint: disable=wrong-import-position

POLICY = plistlib.dumps({'creationTime': 1606921618.318532, 'failedLoginCount': 0,
                         'failedLoginTimestamp': 0, 'passwordLastSetTime': 1606921620.698925},
                        fmt=plistlib.PlistFormat.FMT_BINARY)
LINKED = plistlib.dumps({'appleid.apple.com': {
    'allows password reset': True,
    'linked identities': [{'full name': 'someone@example.com',
                           'timestamp': datetime(2021, 1, 17, 20, 6, 25)}]}}).decode('utf-8')
RECORD = {'name': ['someone'], 'uid': ['501'], 'shell': ['/bin/zsh'],
          'accountPolicyData': [POLICY], 'LinkedIdentity': [LINKED]}


class NestedTest(unittest.TestCase):
    def test_policy_stored_as_data(self):
        self.assertEqual(users.nested_plist(RECORD, 'accountPolicyData')['failedLoginCount'], 0)

    def test_linked_identity_stored_as_text(self):
        self.assertEqual(users.linked_apple_ids(RECORD),
                         (['someone@example.com'],
                          [datetime(2021, 1, 17, 20, 6, 25, tzinfo=timezone.utc)]))

    def test_missing_or_unreadable_values(self):
        self.assertEqual(users.nested_plist({}, 'accountPolicyData'), {})
        self.assertEqual(users.nested_plist({'x': [b'not a plist']}, 'x'), {})
        self.assertEqual(users.linked_apple_ids({}), ([], []))


class TimeTest(unittest.TestCase):
    def test_unix_seconds(self):
        # 1606921618.318532 is 2020-12-02 15:06:58.318532 UTC.
        self.assertEqual(users.unix_utc(1606921618.318532),
                         datetime(2020, 12, 2, 15, 6, 58, 318532, tzinfo=timezone.utc))
        self.assertEqual(users.unix_utc(0), '')
        self.assertEqual(users.unix_utc(True), '')
        self.assertEqual(users.unix_utc('1606921618'), '')


class NodeTest(unittest.TestCase):
    def test_users_and_groups_of_one_node_match(self):
        node = 'p2/Macintosh HD - Data/private'
        self.assertEqual(users.node_of(node + '/var/db/dslocal/nodes/Default/users/a.plist'), '/' + node)
        self.assertEqual(users.node_of(node + '/var/db/dslocal/nodes/Default/groups/admin.plist'),
                         '/' + node)

    def test_firmlink_prefix_is_removed(self):
        self.assertEqual(
            users.node_of('System/Volumes/Data/private/var/db/dslocal/nodes/Default/users/a.plist'),
            '/private')

    def test_node_at_the_extraction_root(self):
        # A logical extraction can be rooted at private/, leaving var/ as the first segment.
        self.assertEqual(users.node_of('var/db/dslocal/nodes/Default/users/a.plist'), '')


class AnchorTest(unittest.TestCase):
    def test_template_tree_at_the_extraction_root_is_recognised(self):
        # A logical extraction rooted at the volume starts its template tree with System/.
        rel = 'System/Library/Templates/Data/private/var/db/dslocal/nodes/Default/users/root.plist'
        self.assertIn('/System/Library/Templates/Data/', users.anchored(rel))

    def test_windows_separators_and_leading_slash(self):
        self.assertEqual(users.anchored('private\\var\\db'), '/private/var/db')
        self.assertEqual(users.anchored('/private/var'), '/private/var')

    def test_first(self):
        self.assertEqual(users.first({'a': ['x', 'y']}, 'a'), 'x')
        self.assertEqual(users.first({'a': []}, 'a'), '')
        self.assertEqual(users.first({}, 'a'), '')


if __name__ == '__main__':
    unittest.main()
