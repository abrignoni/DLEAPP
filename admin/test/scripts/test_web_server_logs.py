"""Pin the web server log readers on synthetic lines: access forms, escapes, W3C directives, error logs
and damaged gzip files."""
import datetime
import gzip
import os
import pathlib
import sys
import tempfile
import unittest
from collections import Counter

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts import web_server_logs as wsl
from scripts.artifacts import webServerLogs as art
# pylint: enable=wrong-import-position

UTC = datetime.timezone.utc


class AccessLineTest(unittest.TestCase):
    def test_combined_with_escaped_quotes_and_offset(self):
        line = wsl.parse_access_line('192.0.2.1 - - [18/Sep/2011:19:18:28 -0400] "GET /a?b=\\"c\\" HTTP/1.1" '
                                     '200 512 "http://example.com/" "UA \\"x\\""')
        self.assertEqual(line.form, 'combined')
        self.assertEqual(line.time, datetime.datetime(2011, 9, 18, 23, 18, 28, tzinfo=UTC))
        self.assertEqual(line.recorded, '18/Sep/2011:19:18:28 -0400')
        self.assertEqual(line.request, 'GET /a?b=\\"c\\" HTTP/1.1')
        self.assertEqual((line.status, line.size, line.referer, line.agent),
                         ('200', '512', 'http://example.com/', 'UA \\"x\\"'))
        self.assertEqual(wsl.split_request(line.request), ('GET', '/a', 'b=\\"c\\"', 'HTTP/1.1'))

    def test_common_and_vhost_forms(self):
        common = wsl.parse_access_line('192.0.2.2 - alice [01/Jan/2024:00:00:00 +0000] "POST /x HTTP/1.0" 404 -')
        self.assertEqual((common.form, common.user, common.size), ('common', 'alice', '-'))
        vhost = wsl.parse_access_line('www.example.com:443 192.0.2.3 - - [01/Jan/2024:00:00:00 +0530] '
                                      '"GET / HTTP/2.0" 301 0 "-" "curl/8"')
        self.assertEqual((vhost.form, vhost.virtual_host, vhost.client), ('vhost_combined', 'www.example.com:443',
                                                                           '192.0.2.3'))
        self.assertEqual(vhost.time, datetime.datetime(2023, 12, 31, 18, 30, tzinfo=UTC))

    def test_trailing_fields_are_kept(self):
        line = wsl.parse_access_line('192.0.2.4 - - [01/Jan/2024:00:00:00 +0000] "GET / HTTP/1.1" 200 1 "-" '
                                     '"ua" 1234 extra')
        self.assertEqual(line.form, 'combined with trailing fields')
        self.assertEqual(line.other, '1234 extra')

    def test_a_line_in_no_form_is_kept_whole(self):
        for text in ('garbage', '192.0.2.1 - - [01/Jan/2024:00:00:00 +0000] "GET /'):
            line = wsl.parse_access_line(text)
            self.assertEqual(line.form, wsl.NOT_PARSED, text)
            self.assertEqual(line.raw, text)

    def test_a_stamp_that_is_not_a_calendar_time_leaves_the_time_blank(self):
        line = wsl.parse_access_line('192.0.2.1 - - [32/Foo/2024:00:00:00 +0000] "GET / HTTP/1.1" 200 1')
        self.assertEqual((line.form, line.time, line.recorded), ('common', '', '32/Foo/2024:00:00:00 +0000'))

    def test_a_request_line_that_does_not_split_in_three(self):
        self.assertEqual(wsl.split_request('\\x16\\x03\\x01'), ('', '', '', ''))
        self.assertEqual(wsl.split_request('-'), ('', '', '', ''))


class FileTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, name, data):
        path = os.path.join(self.tmp.name, name)
        with open(path, 'wb') as handle:
            handle.write(data)
        return path

    def test_gzip_is_found_by_content_and_a_cut_stream_keeps_its_start(self):
        whole = gzip.compress(b''.join(b'line %d\n' % n for n in range(2000)))
        path = self.write('access.log.1.backup', whole[:len(whole) // 2])
        counts = Counter()
        lines = list(wsl.open_lines(path, counts))
        self.assertGreater(len(lines), 10)
        self.assertEqual(lines[0], (1, 'line 0', False))
        self.assertTrue(all(not cut for _n, _t, cut in lines[:-1]))
        self.assertEqual(sum(counts.values()), 1)

    def test_line_feeds_only_split_lines(self):
        path = self.write('access.log', b'a\x0bb\r\nc\n')
        self.assertEqual(list(wsl.open_lines(path, Counter())), [(1, 'a\x0bb', False), (2, 'c', False)])

    def test_w3c_fields_directive_applies_until_the_next(self):
        lines = [(1, '#Software: Microsoft Internet Information Services 10.0', False),
                 (2, '#Fields: date time c-ip sc-status', False),
                 (3, '2024-01-01 00:00:01 192.0.2.9 200', False),
                 (4, 'short line', False),
                 (5, '#Fields: date time cs-method', False),
                 (6, '2024-01-01 00:00:02 GET', False)]
        counts = Counter()
        records = list(wsl.w3c_records(lines, counts))
        self.assertEqual(records[0], (3, {'date': '2024-01-01', 'time': '00:00:01', 'c-ip': '192.0.2.9',
                                          'sc-status': '200'}, ''))
        self.assertEqual(records[1], (4, {}, 'short line'))
        self.assertEqual(records[2][1], {'date': '2024-01-01', 'time': '00:00:02', 'cs-method': 'GET'})
        self.assertEqual(wsl.w3c_time(records[0][1]), datetime.datetime(2024, 1, 1, 0, 0, 1, tzinfo=UTC))

    def test_iis_rows_put_unshown_fields_in_other_fields(self):
        path = self.write('u_ex240101.log', b'#Software: Microsoft Internet Information Services 10.0\r\n'
                                            b'#Fields: date time c-ip cs-method cs-uri-stem sc-status time-taken\r\n'
                                            b'2024-01-01 00:00:01 192.0.2.9 GET /x 200 15\r\n')
        rows = list(art.access_rows(path, 'inetpub/logs/LogFiles/W3SVC1/u_ex240101.log', Counter()))
        self.assertEqual(len(rows), 1)
        row = dict(zip([h if isinstance(h, str) else h[0] for h in art.ACCESS_HEADERS], rows[0]))
        self.assertEqual((row['Client'], row['Method'], row['Request Line'], row['Status'], row['Other Fields']),
                         ('192.0.2.9', 'GET', 'GET /x', '200', 'time-taken=15'))
        self.assertEqual(len(rows[0]), len(art.ACCESS_HEADERS))

    def test_every_access_row_shape_matches_the_headers(self):
        path = self.write('access.log', b'192.0.2.1 - - [01/Jan/2024:00:00:00 +0000] "GET / HTTP/1.1" 200 1\nodd\n')
        w3c = self.write('u_ex1.log', b'#Fields: date time c-ip\r\n2024-01-01 00:00:00 192.0.2.1\r\nbad line here\r\n')
        cut = gzip.compress(b''.join(b'192.0.2.1 - - [01/Jan/2024:00:00:00 +0000] "GET / HTTP/1.1" 200 1\n'
                                     for _ in range(3000)))
        damaged = self.write('access.log.2.gz', cut[:len(cut) // 2])
        for source in (path, w3c, damaged):
            for row in art.access_rows(source, 'rel', Counter()):
                self.assertEqual(len(row), len(art.ACCESS_HEADERS))


class ErrorLineTest(unittest.TestCase):
    def test_apache_24_and_22_and_nginx(self):
        apache = wsl.parse_error_line('[Thu May 12 08:28:57.652118 2011] [core:error] [pid 8777:tid 4326490112] '
                                      '[client ::1:58619] AH00124: Request exceeded the limit')
        self.assertEqual(apache, ('Thu May 12 08:28:57.652118 2011', '2011-05-12 08:28:57.652118', 'core',
                                  'error', '8777', '4326490112', '::1:58619', 'AH00124: Request exceeded the limit',
                                  'Apache'))
        old = wsl.parse_error_line('[Wed Oct 11 14:32:52 2000] [error] [client 127.0.0.1] client denied')
        self.assertEqual(old[2:8], ('', 'error', '', '', '127.0.0.1', 'client denied'))
        nginx = wsl.parse_error_line('2024/06/06 12:00:00 [error] 12#34: *1 open() failed, client: 192.0.2.3, '
                                     'server: s')
        self.assertEqual(nginx[1:8], ('2024-06-06 12:00:00', '', 'error', '12', '34', '192.0.2.3',
                                      '*1 open() failed, client: 192.0.2.3, server: s'))
        self.assertEqual(wsl.parse_error_line('odd')[-1], wsl.NOT_PARSED)

    def test_log_kind_comes_from_the_folder(self):
        self.assertEqual(art.log_kind('/x/var/log/nginx/access.log'), 'nginx')
        self.assertEqual(art.log_kind('/x/var/log/httpd/ssl_access_log'), 'Apache HTTP Server')
        self.assertEqual(art.log_kind('/x/inetpub/logs/LogFiles/W3SVC2/u_ex1.log'), 'IIS')


if __name__ == '__main__':
    unittest.main()
