"""DNF5 transaction history (RHEL-family package installs and removals), for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "linuxDnfHistory": {
        "name": "DNF5 Transaction History",
        "description": "Package installs, upgrades and removals DNF5 recorded in its transaction_history.sqlite "
                       "database on Fedora and other systems that use dnf5: one row per package action, with the "
                       "transaction's time, command and user, the package, the action and the reason, and the "
                       "repository recorded for the item (@System for removed and replaced packages).",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-13",
        "last_update_date": "2026-10-13",
        "requirements": "none",
        "category": "Installed Software (Linux)",
        "notes": "Reads the DNF5 history database (the libdnf5 transaction_history.sqlite that dnf5 writes on "
                 "Fedora and other systems that use dnf5) and reports one row per package action of each transaction, "
                 "joining the trans, trans_item, rpm, comps_group, comps_environment, repo and the action and reason "
                 "tables. Begin Time (UTC) and End Time (UTC) are the trans dt_begin and dt_end columns read as Unix "
                 "seconds. Transaction ID is trans.id and Command is the trans.description column: the dnf5 command "
                 "line writes itself there, and another libdnf5 client may leave it blank. User ID is "
                 "trans.user_id, the login UID libdnf5 records, so a command run through sudo keeps the invoking "
                 "user's id rather than 0. Action is the "
                 "trans_item_action name (Install, Upgrade, Downgrade, Reinstall, Remove, Replaced or Reason Change) "
                 "and Reason the trans_item_reason name (User, Dependency, Weak Dependency, Group, Clean, External "
                 "User or None); both names are read from the database's own enum tables, not assumed. Package is "
                 "the item: for an rpm item its NEVRA (name, epoch when not zero, version, release and arch), for a "
                 "comps item its group or environment id, and Item Type says which. Repository is the repo.repoid, "
                 "and Transaction State is the trans_state name (Ok, Started or Error). A row records that DNF5 "
                 "carried out an item of a transaction, and Transaction State is the state of the whole transaction "
                 "(the per-item state column is not reported); the reason distinguishes a package the user named "
                 "(User) from one pulled in as a dependency. Validated on fedora44_arm64_dnf_known (Fedora Linux 44 Server, dnf5 5.4.2.1), "
                 "where the database holds 11 transactions and 2386 package actions dated 12 August 2026: 1 "
                 "transaction recorded user 0 with a blank command and every item from the anaconda repository, and "
                 "10 recorded user 1000 with a dnf command line. Action was Install on 1727, Upgrade on 289, Replaced on 289 and Remove on 81; Reason was "
                 "Dependency on 1820, Group on 375, Clean on 69, Weak Dependency on 64 and User on 58. Item Type was "
                 "rpm on 2378, group on 7 and environment on 1, and Transaction State was Ok on every row. The older "
                 "DNF4 (libdnf) history database has a different schema and is not read. Reading the "
                 "database needs no extra package.",
        "paths": ("*/libdnf5/transaction_history.sqlite*",),
        "output_types": "standard",
        "artifact_icon": "package",
        "sample_data": {
            "fedora44_arm64_dnf_known": "Fedora Linux 44 Server (aarch64), dnf5 5.4.2.1 | 2386 rows",
        },
    },
}

import os
from datetime import datetime, timezone

from scripts.ilapfuncs import artifact_processor, logfunc, open_sqlite_db_readonly

_LABEL = 'DNF5 Transaction History'
_QUERY = """
SELECT t.dt_begin, t.dt_end, t.id, t.description, t.user_id, a.name,
    CASE WHEN rpm.item_id IS NOT NULL THEN 'rpm'
         WHEN cg.item_id IS NOT NULL THEN 'group'
         WHEN ce.item_id IS NOT NULL THEN 'environment' ELSE '' END,
    COALESCE(pn.name || '-' || CASE WHEN rpm.epoch > 0 THEN rpm.epoch || ':' ELSE '' END
                 || rpm.version || '-' || rpm.release || '.' || ar.name,
             cg.groupid, ce.environmentid, ''),
    r.name, rp.repoid, ts.name
FROM trans_item ti
JOIN trans t ON t.id = ti.trans_id
JOIN trans_item_action a ON a.id = ti.action_id
JOIN trans_item_reason r ON r.id = ti.reason_id
LEFT JOIN trans_state ts ON ts.id = t.state_id
LEFT JOIN repo rp ON rp.id = ti.repo_id
LEFT JOIN rpm ON rpm.item_id = ti.item_id
LEFT JOIN pkg_name pn ON pn.id = rpm.name_id
LEFT JOIN arch ar ON ar.id = rpm.arch_id
LEFT JOIN comps_group cg ON cg.item_id = ti.item_id
LEFT JOIN comps_environment ce ON ce.item_id = ti.item_id
ORDER BY t.dt_begin, ti.id
"""


def _unix_utc(seconds):
    """Unix seconds as an aware UTC datetime; '' for 0 or anything not a number."""
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or seconds == 0:
        return ''
    try:
        return datetime.fromtimestamp(seconds, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ''


def _text(value):
    return '' if value is None else str(value)


@artifact_processor
def linuxDnfHistory(context):
    data_headers = (('Begin Time (UTC)', 'datetime'), ('End Time (UTC)', 'datetime'), 'Transaction ID', 'Command',
                    'User ID', 'Action', 'Item Type', 'Package', 'Reason', 'Repository', 'Transaction State',
                    'Source File')
    data_list = []
    read = []
    for path in [str(p) for p in context.get_files_found()
                 if os.path.basename(str(p)) == 'transaction_history.sqlite']:
        relative = context.get_relative_path(path)
        database = open_sqlite_db_readonly(path)
        if database is None:
            logfunc(f'{_LABEL}: could not open {relative}')
            continue
        try:
            rows = database.execute(_QUERY).fetchall()
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logfunc(f'{_LABEL}: {relative} is not a DNF5 history database ({type(exc).__name__})')
            continue
        finally:
            database.close()
        read.append(path)
        for begin, end, tid, command, uid, action, itype, package, reason, repo, state in rows:
            data_list.append((_unix_utc(begin), _unix_utc(end), _text(tid), _text(command), _text(uid),
                              _text(action), _text(itype), _text(package), _text(reason), _text(repo),
                              _text(state), relative))
    return data_headers, data_list, '\n'.join(read)
