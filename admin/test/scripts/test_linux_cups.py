"""Pin the CUPS Print Jobs and CUPS Printers artifacts (scripts/artifacts/linuxCups.py).

The job control file is built for the test in the IPP encoding (RFC 8010) with the attributes CUPS 2.4.16 wrote on
ubuntu2604_arm64_cups; PRINTERS has the layout of that capture's printers.conf. The values are made up.
"""
import os
import pathlib
import struct
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import linuxCups as cups
# pylint: enable=wrong-import-position

T1 = 1791317872


def attribute(tag, name, value):
    name = name.encode()
    return bytes([tag]) + struct.pack('>H', len(name)) + name + struct.pack('>H', len(value)) + value


def integer(name, value, tag=0x21):
    return attribute(tag, name, struct.pack('>i', value))


def text(name, value, tag=0x42):
    return attribute(tag, name, value.encode())


def message(*attributes, end=b'\x03'):
    return (b'\x02\x00\x00\x05\x00\x00\x00\x04\x01' + text('attributes-charset', 'utf-8', 0x47) + b'\x02'
            + b''.join(attributes) + end)


JOB = message(
    text('job-originating-user-name', 'made-up user'), text('job-name', 'made-up title'), integer('copies', 2),
    text('job-sheets', 'none'), text('', 'none'), text('job-uuid', 'urn:uuid:00000000-0000-3000-8000-000000000001', 0x45),
    text('job-originating-host-name', 'localhost'), attribute(0x31, 'date-time-at-creation', b'\x07\xea\n\x06\x14\x11\x34\x00+\x00\x00'),
    integer('time-at-completed', T1 + 5), integer('time-at-creation', T1), attribute(0x13, 'time-at-processing', b''),
    integer('job-id', 7), integer('job-state', 7, 0x23), text('job-state-reasons', 'job-canceled-by-user', 0x44),
    text('', 'second-reason', 0x44), integer('job-media-sheets-completed', 0),
    text('job-printer-uri', 'ipp://host.example/printers/PDF', 0x45), integer('job-k-octets', 3),
    text('document-format', 'text/plain', 0x49), text('document-name-supplied', 'made-up.txt'),
    attribute(0x22, 'made-up-boolean', b'\x01'))
ROW = (datetime.fromtimestamp(T1, timezone.utc), '', datetime.fromtimestamp(T1 + 5, timezone.utc), 7, 'canceled',
       'job-canceled-by-user | second-reason', 'made-up title', 'made-up user', 'localhost',
       'ipp://host.example/printers/PDF', 'made-up.txt', 'text/plain', 3, 2, 0,
       'urn:uuid:00000000-0000-3000-8000-000000000001',
       'attributes-charset, date-time-at-creation, job-sheets, made-up-boolean')
PRINTERS = (b'# Printer configuration file for CUPS v2.4.16\n# Written by cupsd\nNextPrinterId 3\n<DefaultPrinter PDF>\n'
            b'PrinterId 2\nUUID urn:uuid:4583fe54-0000-3000-8000-000000000002\nInfo PDF\n'
            b'MakeModel Generic CUPS-PDF Printer (w/ options)\nDeviceURI cups-pdf:/\nState Idle\nStateTime 1791317872\n'
            b'ConfigTime 1791317859\nAccepting Yes\nShared No\nOption pdftops-renderer pdftocairo\n</DefaultPrinter>\n'
            b'<Printer Office Laser>\ninfo Second floor\nLOCATION Room 2\nDeviceURI socket://192.0.2.20:9100\n'
            b'DeviceURI ignored://second\nState Stopped\nStateTime soon\nAccepting No\n</Printer>\n'
            b'Info outside a section\n<Printer Unfinished>\nInfo never closed\n')


class FakeContext:
    def __init__(self, paths, root):
        self.paths, self.root = paths, root

    def get_files_found(self):
        return self.paths

    def get_relative_path(self, path):
        return os.path.relpath(path, self.root)


class Ipp(unittest.TestCase):
    def test_a_job(self):
        attributes = cups.ipp_attributes(JOB)
        self.assertEqual(attributes['job-sheets'], ['none', 'none'])
        self.assertEqual(attributes['time-at-processing'], [''])
        self.assertIs(attributes['made-up-boolean'][0], True)
        self.assertEqual(attributes['job-state'], [7])
        self.assertEqual(cups.job_row(attributes), ROW)

    def test_a_collection_is_one_value(self):
        inner = (attribute(0x34, 'media-col', b'') + attribute(0x4a, '', b'media-size') + attribute(0x34, '', b'')
                 + attribute(0x4a, '', b'x-dimension') + integer('', 21000) + attribute(0x37, '', b'')
                 + attribute(0x37, '', b''))
        attributes = cups.ipp_attributes(message(integer('job-id', 1), inner, integer('copies', 4)))
        self.assertEqual(attributes, {'attributes-charset': ['utf-8'], 'job-id': [1], 'media-col': ['<collection>'],
                                      'copies': [4]})

    def test_an_unknown_state_and_missing_attributes(self):
        row = cups.job_row(cups.ipp_attributes(message(integer('job-state', 12, 0x23), integer('time-at-creation', -5))))
        self.assertEqual(row[:5], ('', '', '', '', 12))
        self.assertEqual(row[5:16], ('',) * 11)

    def test_incomplete_messages(self):
        for data in (b'', JOB[:8], JOB[:-1], JOB[:40], message(integer('job-id', 1), end=b''),
                     message(integer('job-id', 1), end=b'\x21\x00\x05ab')):
            self.assertIsNone(cups.ipp_attributes(data), data[-12:])

    def test_a_value_before_any_name_is_passed_over(self):
        self.assertEqual(cups.ipp_attributes(b'\x02\x00\x00\x05\x00\x00\x00\x04\x02' + integer('', 5) + b'\x03'), {})

    def test_group_boundaries_and_repeated_names(self):
        head = b'\x02\x00\x00\x05\x00\x00\x00\x04'
        self.assertEqual(cups.ipp_attributes(head + b'\x03'), {})
        data = head + b'\x02' + integer('job-id', 1) + b'\x04' + integer('', 5) + integer('job-id', 2) + b'\x03'
        self.assertEqual(cups.ipp_attributes(data), {'job-id': [1, 2]})

    def test_times(self):
        self.assertEqual(cups.utc(0), '')
        self.assertEqual(cups.utc(True), '')
        self.assertEqual(cups.utc('5'), '')
        self.assertEqual(cups.utc(10 ** 15), '')
        self.assertEqual(cups.utc(1), datetime(1970, 1, 1, 0, 0, 1, tzinfo=timezone.utc))


class Printers(unittest.TestCase):
    def test_sections(self):
        self.assertEqual(cups.printer_rows(PRINTERS), [
            (datetime.fromtimestamp(1791317872, timezone.utc), datetime.fromtimestamp(1791317859, timezone.utc), 'PDF',
             'Yes', 'PDF', '', 'Generic CUPS-PDF Printer (w/ options)', 'cups-pdf:/', 'Idle', 'Yes', 'No',
             'urn:uuid:4583fe54-0000-3000-8000-000000000002'),
            ('', '', 'Office Laser', 'No', 'Second floor', 'Room 2', '', 'socket://192.0.2.20:9100', 'Stopped', 'No', '',
             '')])

    def test_a_directive_cannot_replace_the_name(self):
        rows = cups.printer_rows(b'<Printer Real>\nName Other\nDefault Yes\n</Printer>\n')
        self.assertEqual(rows[0][2:4], ('Real', 'No'))

    def test_a_second_closing_tag_adds_no_row(self):
        self.assertEqual(len(cups.printer_rows(b'<Printer One>\nInfo x\n</Printer>\nInfo y\n</Printer>\n')), 1)

    def test_nothing(self):
        self.assertEqual(cups.printer_rows(b''), [])
        self.assertEqual(cups.printer_rows(b'<Printer>\nInfo x\n</Printer>\n'), [])


class Processors(unittest.TestCase):
    def test_jobs(self):
        with tempfile.TemporaryDirectory() as root:
            spool = os.path.join(root, 'var', 'spool', 'cups')
            os.makedirs(spool)
            paths = []
            for name, data in (('c00007', JOB), ('c00008', JOB[:50]), ('c00009', b''), ('c00011', JOB[:8] + b'\x03')):
                paths.append(os.path.join(spool, name))
                with open(paths[-1], 'wb') as handle:
                    handle.write(data)
            paths += [os.path.join(spool, 'c00010'), spool]
            with mock.patch.object(cups, 'logfunc') as log:
                headers, data, located = cups.cupsJobs.__wrapped__(FakeContext(paths[::-1], root))
        self.assertEqual(len(headers), 18)
        self.assertEqual(headers[:3], (('Created (UTC)', 'datetime'), ('Processing (UTC)', 'datetime'),
                                       ('Completed (UTC)', 'datetime')))
        self.assertEqual(data, [ROW + (os.path.join('var', 'spool', 'cups', 'c00007'),)])
        self.assertEqual(located, paths[0])
        message_text = log.call_args[0][0]
        self.assertIn('1 files that could not be read', message_text)
        self.assertIn('3 files that are not a complete IPP message, not reported', message_text)

    def test_printers(self):
        with tempfile.TemporaryDirectory() as root:
            first = os.path.join(root, 'a', 'etc', 'cups', 'printers.conf')
            second = os.path.join(root, 'b', 'etc', 'cups', 'printers.conf')
            for path, data in ((first, PRINTERS), (second, b'# no printers\n')):
                os.makedirs(os.path.dirname(path))
                with open(path, 'wb') as handle:
                    handle.write(data)
            gone = os.path.join(root, 'c', 'etc', 'cups', 'printers.conf')
            with mock.patch.object(cups, 'logfunc') as log:
                headers, data, located = cups.cupsPrinters.__wrapped__(FakeContext([gone, second, first], root))
        self.assertEqual(len(headers), 13)
        self.assertEqual([row[2] for row in data], ['PDF', 'Office Laser'])
        self.assertEqual({row[-1] for row in data}, {os.path.join('a', 'etc', 'cups', 'printers.conf')})
        self.assertEqual(located, first)
        self.assertEqual(log.call_args[0][0], 'CUPS Printers: 1 files that could not be read')

    def test_nothing_found(self):
        with mock.patch.object(cups, 'logfunc') as log:
            self.assertEqual(cups.cupsJobs.__wrapped__(FakeContext([], '/'))[1:], ([], ''))
            self.assertEqual(cups.cupsPrinters.__wrapped__(FakeContext([], '/'))[1:], ([], ''))
        log.assert_not_called()


if __name__ == '__main__':
    unittest.main()
