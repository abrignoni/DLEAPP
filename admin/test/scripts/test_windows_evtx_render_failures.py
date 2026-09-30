"""Pin that a record python-evtx cannot render is skipped and counted, and the records after it are read."""
import ast
import pathlib
import sys
import unittest
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import windowsAccountManagement
from scripts.artifacts import windowsRdpSessions
from scripts.artifacts import windowsSecurityLogons
from scripts.artifacts import windowsServiceInstalls
from scripts.artifacts import windowsSystemPowerEvents
# pylint: enable=wrong-import-position


class FakeRecord:
    def __init__(self, number, renders=True):
        self.number = number
        self.renders = renders

    def record_num(self):
        return self.number

    def xml(self):
        if not self.renders:
            # python-evtx 0.8.1 raises KeyError for a value type missing from its table (132 is a
            # byte array), as on the TPM event 27 records of windows11_arm_4688_known's System log.
            raise KeyError(132)
        return f'<Event><EventRecordID>{self.number}</EventRecordID></Event>'


class FakeEvtxModule:
    """Evtx(path) opens a log whose records are 1, 2 (does not render) and 3."""

    def Evtx(self, _path):  # pylint: disable=invalid-name
        class _Open:
            def __enter__(self):
                return 'log'

            def __exit__(self, *_exc):
                return False
        return _Open()


def fake_log_records(_log, _label, _relative):
    return iter([FakeRecord(1), FakeRecord(2, renders=False), FakeRecord(3)])


class FakeContext:
    def __init__(self, name):
        self.path = f'/case/data/vol/Windows/System32/winevt/Logs/{name}'

    def get_files_found(self):
        return [self.path]

    @staticmethod
    def get_relative_path(path):
        return path.split('/data/', 1)[1]


CASES = [
    (windowsAccountManagement, 'accountManagement', '_account_row', 'Security.evtx', 'Windows Account Management'),
    (windowsRdpSessions, 'rdpSessions', '_session_row',
     'Microsoft-Windows-TerminalServices-LocalSessionManager%4Operational.evtx', 'Windows Terminal Services Sessions'),
    (windowsSecurityLogons, 'securityLogons', '_event_rows', 'Security.evtx', 'Windows Security Logons'),
    (windowsServiceInstalls, 'serviceInstalls', '_service_row', 'System.evtx', 'Windows Service Installations'),
]


class RenderFailureTest(unittest.TestCase):
    @staticmethod
    def run_processor(module, processor, context, patches):
        lines = []
        with mock.patch.object(module, 'evtx', FakeEvtxModule()), \
                mock.patch.object(module, 'log_records', fake_log_records), \
                mock.patch.object(module, 'logfunc', lines.append), \
                mock.patch.multiple(module, **patches):
            _headers, rows, source = getattr(module, processor).__wrapped__(context)
        return rows, source, lines

    def test_a_record_that_does_not_render_is_skipped_and_the_next_is_read(self):
        for module, processor, row_function, log_name, label in CASES:
            with self.subTest(processor):
                context = FakeContext(log_name)
                rows, source, lines = self.run_processor(
                    module, processor, context, {row_function: lambda xml: ('row', xml)})
                self.assertEqual([r[1] for r in rows], ['<Event><EventRecordID>1</EventRecordID></Event>',
                                                        '<Event><EventRecordID>3</EventRecordID></Event>'])
                self.assertEqual(source, context.path)
                self.assertEqual(lines, [f'{label}: 1 record(s) in vol/Windows/System32/winevt/Logs/{log_name} '
                                         'could not be rendered by python-evtx and were skipped'])

    def test_power_events_skip_a_record_that_does_not_render_and_read_the_next(self):
        context = FakeContext('System.evtx')
        found = lambda xml: {'kind': 'other', 'fields': {}, 'record_id': xml, 'version': 0}
        rows, source, lines = self.run_processor(
            windowsSystemPowerEvents, 'systemPowerEvents', context,
            {'_power_record': found, '_power_row': lambda found, named: ('row', found['record_id'])})
        self.assertEqual([r[1] for r in rows], ['<Event><EventRecordID>1</EventRecordID></Event>',
                                                '<Event><EventRecordID>3</EventRecordID></Event>'])
        self.assertEqual(source, context.path)
        self.assertIn('Windows System Power Events: 1 record(s) in vol/Windows/System32/winevt/Logs/System.evtx '
                      'could not be rendered by python-evtx and were skipped', lines)


class NoRenderInsideTheParseTryTest(unittest.TestCase):
    def test_no_module_renders_a_record_as_an_argument(self):
        """record.xml() passed straight to a parser puts a render failure under the parser's except,
        which catches only ParseError, so the failure ends the whole log instead of one record."""
        offenders = []
        for path in sorted((REPO_ROOT / 'scripts').rglob('*.py')):
            tree = ast.parse(path.read_text(encoding='utf-8', errors='replace'))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    for arg in node.args:
                        if (isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute)
                                and arg.func.attr == 'xml' and not arg.args):
                            offenders.append(f'{path.relative_to(REPO_ROOT)}:{node.lineno}')
        self.assertEqual(offenders, [])


if __name__ == '__main__':
    unittest.main()
