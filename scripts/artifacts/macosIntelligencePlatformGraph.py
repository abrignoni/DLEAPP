__artifacts_v2__ = {
    "macosIntelligencePlatformEntities": {
        "name": "Intelligence Platform Knowledge Graph - Entities (macOS)",
        "description": "Entities held in each user's Library/IntelligencePlatform/graph.db: people, "
                       "organizations and software, with names, aliases, contact details and app identifiers, "
                       "and predicate and class labels from the ontology.db beside it.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-30",
        "last_update_date": "2026-10-30",
        "requirements": "none",
        "category": "Intelligence Platform (macOS)",
        "notes": "Ported from iLEAPP's Intelligence Platform Knowledge Graph artifacts. The parsing "
                 "helpers are copied unchanged; the entry points were rewritten to read one store per "
                 "user and add the User and Source File columns. Each user's "
                 "Library/IntelligencePlatform/graph.db is read with the ontology.db in the same folder. "
                 "User is the folder after Users in the path, root under private/var/root, otherwise "
                 "blank. When a logical extraction holds the same file under Users/ and under "
                 "System/Volumes/Data/Users/ or System/Volumes/Update/mnt1/Users/, a byte-identical copy "
                 "is not read again and the run log counts it. Of the registered macOS images staged as "
                 "file trees for the gap-finder run (10 of 23), only mvs2026_macbookpro_macos15 (macOS "
                 "15.4) held graph.db; the raw-input disk images were not searched. On it this artifact's "
                 "rows equalled, field for field on the columns the two share, those of the iLEAPP "
                 "artifact run on a copy of the same graph.db and ontology.db; User and Source File are "
                 "added here. graph.db holds a reified triple store: a row with relationshipId 0 carries "
                 "a base fact about an entity (its type, name, first and family name, external "
                 "reference), and rows sharing a nonzero relationshipId carry the parts of one compound "
                 "attribute (a contact method, an external identifier, an alias with its provenance, a "
                 "postal address, a coordinate). The predicate and class codes are resolved to labels "
                 "from that folder's ontology.db, and the columns are filled by matching those labels by "
                 "name; if ontology.db is missing or a label is worded differently, the row is still "
                 "listed with those columns blank, and the run log says when ontology.db is missing or "
                 "gives no predicate labels. One row is emitted per entity. Text values are reported as "
                 "stored, except that class codes are replaced by their ontology labels, a value repeated "
                 "within one cell is listed once, several values in one cell are comma-joined, and "
                 "timestamps are converted from Cocoa (2001-epoch) seconds. Confidence is the highest "
                 "confidence value among the entity's rows, rounded to four places, and Latest Timestamp "
                 "the newest timestamp among them; neither is a measurement made here. How the system "
                 "produces an entity is not established here, so an entity is not evidence the user "
                 "created or confirmed it. Columns are a union across entity types. Rows of the "
                 "expired_stable_graph table are read alongside stable_graph and marked Yes in the "
                 "Expired column; what moves an entry into that table is not established. On the tested "
                 "image all 341 rows came from stable_graph; expired_stable_graph was present and empty. "
                 "The IntelligencePlatform graph databases and the ontology-code resolution were "
                 "described by 0x11 Forensics and Consulting, 'That is one smart Apple', "
                 "https://0x11forensicssc.com/f/that-is-one-smart-apple, 2026-07-21.",
        "paths": ('*/Library/IntelligencePlatform/graph.db*',
                  '*/Library/IntelligencePlatform/ontology.db*'),
        "output_types": "standard",
        "sample_data": {
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 341 rows",
        },
        "artifact_icon": "users",
    },
    "macosIntelligencePlatformEvents": {
        "name": "Intelligence Platform Knowledge Graph - Events (macOS)",
        "description": "Events held in each user's Library/IntelligencePlatform/graph.db with their imputed "
                       "start and end times and, where an event carries a location reference, the place it "
                       "resolves to.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-30",
        "last_update_date": "2026-10-30",
        "requirements": "none",
        "category": "Intelligence Platform (macOS)",
        "notes": "Ported from iLEAPP's Intelligence Platform Knowledge Graph artifacts. The parsing "
                 "helpers are copied unchanged; the entry points were rewritten to read one store per "
                 "user and add the User and Source File columns. Each user's "
                 "Library/IntelligencePlatform/graph.db is read with the ontology.db in the same folder. "
                 "User is the folder after Users in the path, root under private/var/root, otherwise "
                 "blank. When a logical extraction holds the same file under Users/ and under "
                 "System/Volumes/Data/Users/ or System/Volumes/Update/mnt1/Users/, a byte-identical copy "
                 "is not read again and the run log counts it. Of the registered macOS images staged as "
                 "file trees for the gap-finder run (10 of 23), only mvs2026_macbookpro_macos15 (macOS "
                 "15.4) held graph.db; the raw-input disk images were not searched. On it this artifact's "
                 "rows equalled, field for field on the columns the two share, those of the iLEAPP "
                 "artifact run on a copy of the same graph.db and ontology.db; User and Source File are "
                 "added here. Each event is a reified group of triples sharing a subject: its type, name, "
                 "a compound date carrying imputed start and end times, and, where present, a location "
                 "reference. Imputed Start Time is the earliest of the event's imputed start time and "
                 "imputed occurrence date values and Imputed End Time the latest imputed end time, each "
                 "read as Cocoa (2001-epoch) seconds; the raw start-time and end-time objects are stored "
                 "in a serialized form and are not reported. How the system produces an event is not "
                 "established here, so an event is not evidence the user was present or confirmed it. The "
                 "location reference, when present, is reported as stored. On the iOS images the iLEAPP "
                 "artifact was built against it was an 'md:' prefix followed by a number that matched a "
                 "place node's subject id; no vendor source for that form is cited, and the tested macOS "
                 "image held none. It is resolved to that place's name, composed address, latitude and "
                 "longitude by reading the referenced node from stable_graph, then expired_stable_graph. "
                 "Confidence is the highest confidence value among the event's rows, rounded to four "
                 "places, not a measurement made here. Rows of the expired_event_graph table are read "
                 "alongside event_graph and marked Yes in the Expired column; what moves an event into "
                 "that table is not established. On the tested image all 6 rows came from event_graph, "
                 "expired_event_graph was present and empty, and no event carried a location reference. "
                 "The IntelligencePlatform graph databases and the ontology-code resolution were "
                 "described by 0x11 Forensics and Consulting, 'That is one smart Apple', "
                 "https://0x11forensicssc.com/f/that-is-one-smart-apple, 2026-07-21.",
        "paths": ('*/Library/IntelligencePlatform/graph.db*',
                  '*/Library/IntelligencePlatform/ontology.db*'),
        "output_types": "standard",
        "sample_data": {
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 6 rows",
        },
        "artifact_icon": "calendar",
    },
}

import os

from scripts.ilapfuncs import artifact_processor, get_file_path, logfunc, \
    open_sqlite_db_readonly, convert_cocoa_core_data_ts_to_utc, does_table_exist_in_db
from scripts.macos_plists import fold_view_rows, unique_sources, user_from_path


def _load_ontology(files_found):
    """Return dicts mapping predicate id -> label and class id -> label from the
    ontology.db shipped beside graph.db. Empty dicts if it is missing."""
    predicates = {}
    classes = {}
    onto_path = get_file_path(files_found, "ontology.db")
    if not onto_path:
        logfunc('Intelligence Platform: ontology.db not found; predicate and class '
                'codes are not resolved and label-matched columns are blank')
        return predicates, classes
    db = open_sqlite_db_readonly(onto_path)
    if db is None:
        logfunc('Intelligence Platform: ontology.db could not be opened; predicate and '
                'class codes are not resolved and label-matched columns are blank')
        return predicates, classes
    cur = db.cursor()
    if does_table_exist_in_db(onto_path, "predicate"):
        for pid, label in cur.execute("select id, label from predicate"):
            predicates[pid] = label
    if does_table_exist_in_db(onto_path, "class"):
        for cid, label in cur.execute("select id, label from class"):
            classes[cid] = label
    db.close()
    if not predicates:
        logfunc('Intelligence Platform: ontology.db gave no predicate labels; '
                'label-matched columns are blank')
    return predicates, classes


def _read_triples(files_found, table_name):
    """Return (rows, graph_path) for the named table, or ([], '') if unavailable."""
    graph_path = get_file_path(files_found, "graph.db")
    if not graph_path or not does_table_exist_in_db(graph_path, table_name):
        return [], ''
    db = open_sqlite_db_readonly(graph_path)
    if db is None:
        return [], ''
    cur = db.cursor()
    rows = cur.execute(
        f'select subject, predicate, relationshipId, relationshipPredicate, '
        f'object, confidence, timestamp from "{table_name}"').fetchall()
    db.close()
    return rows, graph_path


def _group_by_subject(rows, predicates):
    """Group triples per subject. Base facts (relationshipId 0) are keyed by their
    resolved predicate label. Compound attributes (nonzero relationshipId) are grouped
    and tagged with their resolved parent predicate label and resolved part labels."""
    entities = {}
    for subject, predicate, rel_id, rel_pred, obj, confidence, timestamp in rows:
        ent = entities.setdefault(
            subject, {'base': {}, 'groups': {}, 'confidence': 0.0, 'timestamp': 0.0})
        if confidence and confidence > ent['confidence']:
            ent['confidence'] = confidence
        if timestamp and timestamp > ent['timestamp']:
            ent['timestamp'] = timestamp
        if rel_id in (0, None):
            ent['base'].setdefault(predicates.get(predicate, predicate), []).append(obj)
        else:
            grp = ent['groups'].setdefault(
                rel_id, {'parent': predicates.get(predicate, predicate), 'parts': {}})
            grp['parts'].setdefault(
                predicates.get(rel_pred, rel_pred), []).append(obj)
    return entities


def _base(ent, label):
    return ent['base'].get(label, [])


def _part(ent, parent_label, part_label):
    """Collect the values of one part across every compound group whose parent
    predicate matches."""
    out = []
    for grp in ent['groups'].values():
        if grp['parent'] == parent_label:
            out.extend(grp['parts'].get(part_label, []))
    return out


def _coords(ent):
    """Return the (latitude, longitude) of the first coordinate group, or ('', '')."""
    for grp in ent['groups'].values():
        if grp['parent'] == 'has latitude/longitude':
            lats = grp['parts'].get('latitude', [])
            lons = grp['parts'].get('longitude', [])
            if lats and lons:
                return str(lats[0]), str(lons[0])
    return '', ''


def _join(values):
    """De-duplicate preserving order and join with a comma for a report cell."""
    seen = []
    for value in values:
        text = '' if value is None else str(value)
        if text and text not in seen:
            seen.append(text)
    return ', '.join(seen)


def _cocoa(value):
    """Convert a stored Cocoa (2001-epoch) numeric string to UTC, else return None."""
    try:
        return convert_cocoa_core_data_ts_to_utc(float(value))
    except (TypeError, ValueError):
        return None


def _first(values):
    """Return the first non-empty value as text, else ''."""
    for value in values:
        text = '' if value is None else str(value)
        if text:
            return text
    return ''


def _place_lookup(files_found, predicates):
    """Map each modeled node's subject id to its resolved (name, composed address,
    latitude, longitude), gathered from the live and expired entity tables. An event
    references its location by node id (object 'md:<id>'), so this turns that pointer
    into the place the graph modeled. The live stable_graph wins over the expired
    table when a node is in both."""
    lookup = {}
    for table_name in ("stable_graph", "expired_stable_graph"):
        rows, _ = _read_triples(files_found, table_name)
        for subject, ent in _group_by_subject(rows, predicates).items():
            number = _first(_part(ent, 'has address', 'sub thoroughfare'))
            street = _first(_part(ent, 'has address', 'full street address'))
            city = _first(_part(ent, 'has address', 'city'))
            region = _first(_part(ent, 'has address', 'administrative district'))
            postal = _first(_part(ent, 'has address', 'postal code'))
            name = _first(_part(ent, 'has address', 'name'))
            lat, lon = _coords(ent)
            line1 = ' '.join(p for p in (number, street) if p)
            region_zip = ' '.join(p for p in (region, postal) if p)
            address = ', '.join(p for p in (line1, city, region_zip) if p)
            if subject not in lookup and (name or address or lat or lon):
                lookup[subject] = (name, address, lat, lon)
    return lookup


def _resolve_location(ent, places):
    """Resolve an event's location reference ('md:<id>') to the modeled place's
    (name, address, latitude, longitude). Returns blanks when the event has no
    location or the reference does not resolve to a modeled node."""
    for ref in _part(ent, 'has location relationship', 'has location'):
        if isinstance(ref, str) and ref.startswith('md:'):
            try:
                node = int(ref[3:])
            except ValueError:
                continue
            if node in places:
                return places[node]
    return '', '', '', ''


_LABEL = 'Intelligence Platform'


def _stores(context):
    """(graph.db path, [graph.db, ontology.db beside it]) for each user's graph.db, read once per
    byte-identical copy under another volume view."""
    graphs = [str(p) for p in context.get_files_found() if os.path.basename(str(p)) == 'graph.db']
    paths, _skipped = unique_sources(context, graphs, sidecars=('-wal',), label=_LABEL)
    for path in paths:
        files = [path]
        ontology = os.path.join(os.path.dirname(path), 'ontology.db')
        if os.path.isfile(ontology):
            files.append(ontology)
        yield path, files


@artifact_processor
def macosIntelligencePlatformEntities(context):
    data_list, read = [], []
    for path, files_found in _stores(context):
        relative = context.get_relative_path(path)
        predicates, classes = _load_ontology(files_found)
        user = user_from_path(relative)
        # Rows of stable_graph and expired_stable_graph share one schema and are reported
        # together, tagged. What moves an entry into the expired table is not established.
        for table_name, expired in (("stable_graph", "No"), ("expired_stable_graph", "Yes")):
            rows, graph_path = _read_triples(files_found, table_name)
            if graph_path and graph_path not in read:
                read.append(graph_path)
            for subject, ent in _group_by_subject(rows, predicates).items():
                identifiers = _join(
                    _part(ent, 'identifier', 'username')
                    + _part(ent, 'identifier', 'identifier id'))
                data_list.append((
                    convert_cocoa_core_data_ts_to_utc(ent['timestamp']) if ent['timestamp'] else '',
                    _join(classes.get(v, v) for v in _base(ent, 'is a')),
                    _join(_base(ent, 'name')),
                    _join(_base(ent, 'first name')),
                    _join(_base(ent, 'family name')),
                    _join(_part(ent, 'entity alias relationship', 'also known as')),
                    _join(_part(ent, 'has contact information', 'phone number')),
                    _join(_part(ent, 'has contact information', 'email address')),
                    _join(_part(ent, 'has contact information', 'contact label')),
                    identifiers,
                    _join(_part(ent, 'has address', 'full street address')),
                    *_coords(ent),
                    _join(_base(ent, 'bundle id') + _base(ent, 'application identifier')),
                    _join(_base(ent, 'same as')),
                    round(ent['confidence'], 4),
                    expired,
                    str(subject),
                    user,
                    relative))
    data_headers = (
        ('Latest Timestamp', 'datetime'), 'Entity Type', 'Name', 'First Name', 'Family Name', 'Also Known As',
        ('Phone Numbers', 'phonenumber'), 'Email Addresses', 'Contact Labels', 'Other Identifiers', 'Address',
        'Latitude', 'Longitude', 'App Bundle ID', 'Same As', 'Confidence', 'Expired', 'Entity ID', 'User',
        'Source File')
    return data_headers, fold_view_rows(data_list), '\n'.join(read)


@artifact_processor
def macosIntelligencePlatformEvents(context):
    data_list, read = [], []
    for path, files_found in _stores(context):
        relative = context.get_relative_path(path)
        predicates, classes = _load_ontology(files_found)
        places = _place_lookup(files_found, predicates)
        user = user_from_path(relative)
        # event_graph and expired_event_graph are both read and tagged; what moves an
        # event into the expired table is not established.
        for table_name, expired in (("event_graph", "No"), ("expired_event_graph", "Yes")):
            rows, graph_path = _read_triples(files_found, table_name)
            if graph_path and graph_path not in read:
                read.append(graph_path)
            for subject, ent in _group_by_subject(rows, predicates).items():
                starts = [_cocoa(v) for v in
                          _part(ent, 'has date', 'imputed start time')
                          + _part(ent, 'has date', 'imputed occurrence date')]
                ends = [_cocoa(v) for v in _part(ent, 'has date', 'imputed end time')]
                starts = [s for s in starts if s]
                ends = [e for e in ends if e]
                loc_name, loc_addr, loc_lat, loc_lon = _resolve_location(ent, places)
                data_list.append((
                    min(starts) if starts else '',
                    max(ends) if ends else '',
                    _join(classes.get(v, v) for v in _base(ent, 'is a')),
                    _join(_base(ent, 'name')),
                    _join(_part(ent, 'has location relationship', 'has location')),
                    loc_name, loc_addr, loc_lat, loc_lon,
                    round(ent['confidence'], 4),
                    expired,
                    str(subject),
                    user,
                    relative))
    data_headers = (
        ('Imputed Start Time', 'datetime'), ('Imputed End Time', 'datetime'), 'Event Type', 'Name',
        'Location (as stored)', 'Location Name', 'Location Address', 'Latitude', 'Longitude', 'Confidence',
        'Expired', 'Event ID', 'User', 'Source File')
    return data_headers, fold_view_rows(data_list), '\n'.join(read)
