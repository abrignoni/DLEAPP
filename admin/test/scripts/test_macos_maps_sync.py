"""Pin how the Apple Maps MapsSync artifacts read queries, places, routes and guides.

The place query cases are ported from iLEAPP's test_mapssync_place_queries.py
(abrignoni/iLEAPP#2735), adapted to DLEAPP's field-path reader.
"""
import base64
import inspect
import pathlib
import sqlite3
import sys
import tempfile
import unittest
from types import SimpleNamespace

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from scripts.artifacts import macosMapsSync
# pylint: enable=wrong-import-position


def _varint(value):
    out = b''
    while True:
        part = value & 0x7F
        value >>= 7
        out += bytes([part | (0x80 if value else 0)])
        if not value:
            return out


def _field(number, value):
    return _varint(number << 3 | 2) + _varint(len(value)) + value


def place_request_payload(sent=None, raw=None):
    """A request with field 8.1.3 = sent text and field 8.1.7.10000 = raw text."""
    inner = b''
    if sent is not None:
        inner += _field(3, sent.encode() if isinstance(sent, str) else sent)
    if raw is not None:
        inner += _field(7, _field(10000, raw.encode() if isinstance(raw, str) else raw))
    return _field(8, _field(1, inner))


def request_string(payload, url=False):
    text = b'placeRequest=' + base64.b64encode(payload)
    return b'https://gsp.apple.com/path?' + text + b'&other=1' if url else text


def map_item(name=None, address_lines=(), requests=()):
    """A map item message: 1.4.8.30.1 name, 1.4.8.31.1.101.2.11 address lines, 1.4.11.2 requests."""
    entry = b''
    if name is not None:
        entry += _field(8, _field(30, _field(1, name.encode())))
    if address_lines:
        lines = b''.join(_field(11, line.encode()) for line in address_lines)
        entry += _field(8, _field(31, _field(1, _field(101, _field(2, lines)))))
    for request in requests:
        entry += _field(11, _field(2, request))
    return _field(1, _field(4, entry))


def route(*waypoints):
    """A route request: one map item message per waypoint at 1.n.2."""
    return b''.join(_field(1, _field(2, waypoint)) for waypoint in waypoints)


def make_store(path, history_rows=(), mixin_rows=(), with_lat1=True, entities=None):
    connection = sqlite3.connect(path)
    second = 'ZLATITUDE1, ZLONGITUDE1, ' if with_lat1 else ''
    connection.execute('CREATE TABLE ZHISTORYITEM (Z_PK, Z_ENT, ZCREATETIME, ZMODIFICATIONTIME, ZQUERY, '
                       'ZLOCATIONDISPLAY, ZLATITUDE, ZLONGITUDE, ' + second + 'ZMAPITEM, ZROUTEREQUESTSTORAGE)')
    connection.execute('CREATE TABLE ZMIXINMAPITEM (Z_PK, ZMAPITEMSTORAGE, ZLATITUDE, ZLONGITUDE)')
    connection.execute('CREATE TABLE Z_PRIMARYKEY (Z_ENT, Z_NAME)')
    for ent, name in (entities or {21: 'HistoryPlaceItem', 17: 'HistoryDirectionsItem'}).items():
        connection.execute('INSERT INTO Z_PRIMARYKEY VALUES (?, ?)', (ent, name))
    for row in mixin_rows:
        connection.execute('INSERT INTO ZMIXINMAPITEM VALUES (?, ?, ?, ?)', row)
    for row in history_rows:
        if not with_lat1:
            row = row[:8] + row[10:]
        connection.execute(f'INSERT INTO ZHISTORYITEM VALUES ({", ".join("?" * len(row))})', row)
    connection.commit()
    return connection


def run(function, *paths):
    context = SimpleNamespace(get_files_found=lambda: [str(p) for p in paths],
                              get_relative_path=lambda p: 'Users/lab/Library/Containers/com.apple.Maps/Data/Maps/'
                                                          + pathlib.Path(p).name)
    return inspect.unwrap(function)(context)


class TestPlaceQueries(unittest.TestCase):
    def check(self, blob, expected):
        sent, raw, _ = macosMapsSync.place_queries(blob)
        self.assertEqual((sent, raw), expected)

    def test_sent_and_raw(self):
        self.check(map_item(requests=[request_string(place_request_payload('Sample Diner', 'Samp'))]),
                   ('Sample Diner', 'Samp'))

    def test_sent_only_when_raw_field_absent(self):
        self.check(map_item(requests=[request_string(place_request_payload('example town'))]), ('example town', ''))

    def test_request_inside_a_url_parameter(self):
        self.check(map_item(requests=[request_string(place_request_payload('test cafes', 'test'), url=True)]),
                   ('test cafes', 'test'))

    def test_plus_in_base64_is_kept(self):
        payload = place_request_payload('~~~>>>', 'x')
        encoded = base64.b64encode(payload)
        self.assertIn(b'+', encoded)
        self.check(map_item(requests=[b'placeRequest=' + encoded]), ('~~~>>>', 'x'))

    def test_no_request_yields_empty(self):
        self.check(map_item(name='Somewhere'), ('', ''))

    def test_not_a_message_yields_empty(self):
        self.check(b'blob without any request', ('', ''))

    def test_undecodable_request_is_counted(self):
        sent, raw, skipped = macosMapsSync.place_queries(map_item(requests=[b'placeRequest=!!!']))
        self.assertEqual((sent, raw, skipped), ('', '', 1))

    def test_first_request_without_query_then_one_with(self):
        earlier = _field(8, _field(1, _field(2, b'other')))
        self.check(map_item(requests=[request_string(earlier), request_string(place_request_payload('test cafes', 'test'))]),
                   ('test cafes', 'test'))

    def test_non_utf8_query_decodes_without_crash(self):
        self.check(map_item(requests=[request_string(place_request_payload(b'\xff\xfe bad'))]), ('�� bad', ''))

    def test_text_that_parses_as_a_message_is_kept_as_text(self):
        # 'h1h2h3' is also a valid protobuf message (field 13, three varints).
        self.check(map_item(requests=[request_string(place_request_payload('Springfield, ZZ', 'h1h2h3'))]),
                   ('Springfield, ZZ', 'h1h2h3'))

    def test_eight_byte_text_is_kept_as_text(self):
        self.check(map_item(requests=[request_string(place_request_payload('Hoover X', 'hoover x'))]),
                   ('Hoover X', 'hoover x'))

    def test_distinct_queries_from_every_request_are_joined(self):
        first = map_item(requests=[request_string(place_request_payload('Springfield, ZZ', 'Spr'))])
        second = map_item(requests=[request_string(place_request_payload('test cafes', 'test')),
                                    request_string(place_request_payload('Springfield, ZZ', 'Spr'))])
        sent, raw, _ = macosMapsSync.place_queries(first, second)
        self.assertEqual((sent, raw), ('Springfield, ZZ; test cafes', 'Spr; test'))


class TestPlaces(unittest.TestCase):
    def test_map_item_name_and_address(self):
        blob = map_item('Sample Tower', ('1 Example St', 'Testville, ZZ 00000', 'Testland'))
        self.assertEqual(macosMapsSync.map_item_place(blob), ('Sample Tower', '1 Example St, Testville, ZZ 00000, Testland'))

    def test_route_waypoints_in_stored_order(self):
        blob = route(map_item('Start Town', ('Start Town, ZZ',)), map_item('End Dam', ('Dam Rd', 'End City, ZZ')))
        self.assertEqual(macosMapsSync.route_places(blob),
                         ('Start Town -> End Dam', 'Start Town, ZZ -> Dam Rd, End City, ZZ'))

    def test_route_without_places_is_empty(self):
        self.assertEqual(macosMapsSync.route_places(b'\x08\x01'), ('', ''))


class TestHistory(unittest.TestCase):
    def rows(self, **kwargs):
        with tempfile.TemporaryDirectory() as directory:
            store = pathlib.Path(directory) / 'MapsSync_0.0.1'
            make_store(store, **kwargs).close()
            headers, rows, source = run(macosMapsSync.macosMapsSync, store)
        return headers, rows, source

    def test_place_row(self):
        item = map_item('Sample Tower', ('1 Example St',), [request_string(place_request_payload('Sample Tower', 'samp'))])
        headers, rows, source = self.rows(mixin_rows=[(1, item, None, None)],
                                          history_rows=[(1, 21, 700000000, 700000001, None, None, None, None,
                                                         40.5, -74.5, 1, None)])
        self.assertEqual(len(rows), 1)
        row = dict(zip([h[0] if isinstance(h, tuple) else h for h in headers], rows[0]))
        self.assertEqual(row['Entity (Z_PRIMARYKEY Name)'], 'HistoryPlaceItem')
        self.assertEqual((row['Place Name'], row['Address']), ('Sample Tower', '1 Example St'))
        self.assertEqual((row['Query (Sent)'], row['Query (Raw)']), ('Sample Tower', 'samp'))
        self.assertEqual((row['Latitude'], row['Longitude']), (40.5, -74.5))
        self.assertEqual(row['User'], 'lab')
        self.assertTrue(source.endswith('MapsSync_0.0.1'))

    def test_directions_row_reads_the_route(self):
        start = map_item('Start Town', ('Start Town, ZZ',), [request_string(place_request_payload('Start Town', 'sta'))])
        end = map_item('End Dam', ('Dam Rd',), [request_string(place_request_payload('End Dam', 'end d'))])
        _, rows, _ = self.rows(history_rows=[(9, 17, 700000000, 700000000, None, None, None, None, None, None,
                                              None, route(start, end))])
        self.assertEqual(rows[0][6:10], ('Start Town -> End Dam', 'Start Town, ZZ -> Dam Rd',
                                         'Start Town; End Dam', 'sta; end d'))

    def test_store_without_latitude1(self):
        _, rows, _ = self.rows(with_lat1=False,
                               history_rows=[(1, 21, 700000000, 700000000, 'cafes', 'Testville', 1.5, 2.5,
                                              None, None, None, None)])
        self.assertEqual(rows[0][4:6], ('cafes', 'Testville'))
        self.assertEqual(rows[0][10:12], (1.5, 2.5))

    def test_unknown_entity_number_is_blank(self):
        _, rows, _ = self.rows(history_rows=[(1, 99, 700000000, 700000000, None, None, None, None,
                                              None, None, None, None)])
        self.assertEqual(rows[0][2:4], ('', 99))

    def test_store_without_history_table(self):
        with tempfile.TemporaryDirectory() as directory:
            store = pathlib.Path(directory) / 'MapsSync_0.0.1'
            sqlite3.connect(store).execute('CREATE TABLE Z_PRIMARYKEY (Z_ENT, Z_NAME)')
            _, rows, source = run(macosMapsSync.macosMapsSync, store)
        self.assertEqual((rows, source), ([], ''))


class TestCollections(unittest.TestCase):
    def test_guides_found_through_the_join_table(self):
        with tempfile.TemporaryDirectory() as directory:
            store = pathlib.Path(directory) / 'MapsSync_0.0.1'
            connection = sqlite3.connect(store)
            connection.execute('CREATE TABLE Z_PRIMARYKEY (Z_ENT, Z_NAME)')
            connection.executemany('INSERT INTO Z_PRIMARYKEY VALUES (?, ?)',
                                   [(7, 'Collection'), (8, 'CollectionItem'), (9, 'CollectionPlaceItem')])
            connection.execute('CREATE TABLE ZCOLLECTION (Z_PK, ZTITLE)')
            connection.executemany('INSERT INTO ZCOLLECTION VALUES (?, ?)', [(1, 'Guide A'), (2, 'Guide B')])
            connection.execute('CREATE TABLE Z_7PLACES (Z_7COLLECTIONS INTEGER, Z_8PLACES INTEGER)')
            connection.executemany('INSERT INTO Z_7PLACES VALUES (?, ?)', [(1, 2), (2, 2)])
            connection.execute('CREATE TABLE ZCOLLECTIONITEM (Z_PK, Z_ENT, ZCREATETIME, ZMODIFICATIONTIME, '
                               'ZMAPITEMNAME, ZTYPE)')
            connection.executemany('INSERT INTO ZCOLLECTIONITEM VALUES (?, ?, ?, ?, ?, ?)',
                                   [(1, 9, 700000000, 700000000, 'One', 1), (2, 9, 700000001, 700000001, 'Two', 0)])
            connection.commit()
            connection.close()
            _, rows, _ = run(macosMapsSync.macosMapsCollectionItems, store)
        self.assertEqual([(r[4], r[8], r[9]) for r in rows], [('One', 1, ''), ('Two', 0, 'Guide A; Guide B')])
        self.assertEqual(rows[0][2], 'CollectionPlaceItem')


class TestFavorites(unittest.TestCase):
    def test_favorite_falls_back_to_the_map_item(self):
        with tempfile.TemporaryDirectory() as directory:
            store = pathlib.Path(directory) / 'MapsSync_0.0.1'
            connection = sqlite3.connect(store)
            connection.execute('CREATE TABLE ZFAVORITEITEM (Z_PK, ZCREATETIME, ZMODIFICATIONTIME, ZCUSTOMNAME, '
                               'ZTYPE, ZSOURCE, ZHIDDEN, ZLATITUDE, ZLONGITUDE, ZMAPITEM, ZORIGINATINGADDRESSSTRING)')
            connection.execute('CREATE TABLE ZMIXINMAPITEM (Z_PK, ZMAPITEMSTORAGE, ZLATITUDE, ZLONGITUDE)')
            item = map_item('Sample Tower', ('1 Example St',), [request_string(place_request_payload('Sample', 'sam'))])
            connection.execute('INSERT INTO ZMIXINMAPITEM VALUES (1, ?, 3.5, 4.5)', (item,))
            connection.execute("INSERT INTO ZFAVORITEITEM VALUES (1, 700000000, 700000000, NULL, 1, 0, 0, NULL, NULL, "
                               "1, 'fallback')")
            connection.commit()
            connection.close()
            _, rows, _ = run(macosMapsSync.macosMapsFavorites, store)
        self.assertEqual(rows[0][2:6], ('', 'Sample Tower', '1 Example St', ''))
        self.assertEqual(rows[0][9:13], ('Sample', 'sam', 3.5, 4.5))


if __name__ == '__main__':
    unittest.main()
