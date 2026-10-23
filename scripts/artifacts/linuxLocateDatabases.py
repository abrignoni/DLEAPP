"""Locate databases (plocate, mlocate, GNU findutils locate), for DLEAPP.

Author: @AlexisBrignoni, Claude.

The reading is in scripts/linux_locate.py; the sources for each format are in the notes.
"""

__artifacts_v2__ = {
    "locateDatabasePaths": {
        "name": "Locate Database Paths",
        "description": "Paths listed in plocate, mlocate and GNU locate databases, one row per path, with the "
                       "entry type and the directory times the database stores.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-23",
        "last_update_date": "2026-10-23",
        "requirements": "plocate databases need zstd: Python 3.14 or later, or the backports.zstd or zstandard "
                        "package on an earlier Python",
        "category": "Locate Databases (Linux)",
        "notes": "Read from plocate.db in var/lib/plocate, and in var/lib/mlocate, where plocate-build's help says to put "
                 "it (plocate plocate-build.cpp lines 188-189 "
                 "(https://git.sesse.net/?p=plocate;a=blob;f=plocate-build.cpp;hb=cc0423b00042f51b648d0fb7cdadffc62c0b0daf#l188));"
                 " mlocate.db in var/lib/mlocate; and a GNU findutils locatedb in var/cache/locate, where Debian's "
                 "findutils build puts it "
                 "(https://salsa.debian.org/debian/findutils/-/blob/dd1f195249237ac011442188db9c49ff3184c290/debian/rules#L20),"
                 " or in usr/local/var, findutils' default when built with no prefix (findutils locate/Makefile.am line 20"
                 " "
                 "(https://cgit.git.savannah.gnu.org/cgit/findutils.git/tree/locate/Makefile.am?id=c67264238d9487d5313a131674cd7a01ca299927#n20)"
                 " names $(localstatedir)/locatedb). A database written elsewhere with updatedb -o or --output is not "
                 "found. The format is told by the magic at the start of the file, not by its name. Sources: plocate "
                 "1.1.25 (commit cc0423b0, GPL-2.0-or-later), whose header layout is the same from 1.1.0; mlocate 0.26 "
                 "(Debian 0.26-5, GPL-2.0, db.h without restriction); findutils 4.10.0 (commit c6726423, "
                 "GPL-3.0-or-later). The readers in scripts/linux_locate.py were written from these sources; no code was "
                 "taken from them. One row per path the database lists, in stored order. A row shows a path that existed "
                 "when updatedb last ran. It is not when the file was created, changed or deleted: the path can be gone "
                 "since, and a path missing from the list may have been made after that run or skipped by updatedb (the "
                 "pruned file system types, names and paths and the bind mount setting shown by the Locate Databases "
                 "artifact, and directories updatedb could not open). plocate: the header (plocate db.h lines 6-30 "
                 "(https://git.sesse.net/?p=plocate;a=blob;f=db.h;hb=cc0423b00042f51b648d0fb7cdadffc62c0b0daf#l6)), the "
                 "zstd-compressed blocks of NUL-separated paths (plocate database-builder.cpp lines 241-251 "
                 "(https://git.sesse.net/?p=plocate;a=blob;f=database-builder.cpp;hb=cc0423b00042f51b648d0fb7cdadffc62c0b0daf#l241),"
                 " plocate database-builder.cpp lines 339-346 "
                 "(https://git.sesse.net/?p=plocate;a=blob;f=database-builder.cpp;hb=cc0423b00042f51b648d0fb7cdadffc62c0b0daf#l339))"
                 " found through the block index (plocate database-builder.cpp lines 576-585 "
                 "(https://git.sesse.net/?p=plocate;a=blob;f=database-builder.cpp;hb=cc0423b00042f51b648d0fb7cdadffc62c0b0daf#l576)),"
                 " and the directory data, for each path one byte 0 when it is not a directory, or 1 followed by a 64-bit "
                 "seconds and a 32-bit nanoseconds field when it is (plocate database-builder.cpp lines 252-260 "
                 "(https://git.sesse.net/?p=plocate;a=blob;f=database-builder.cpp;hb=cc0423b00042f51b648d0fb7cdadffc62c0b0daf#l252),"
                 " plocate database-builder.cpp lines 657-666 "
                 "(https://git.sesse.net/?p=plocate;a=blob;f=database-builder.cpp;hb=cc0423b00042f51b648d0fb7cdadffc62c0b0daf#l657))."
                 " A path counts as a directory when the directory entry's type says so, so a symbolic link to a directory"
                 " is not a directory (plocate updatedb.cpp lines 627-638 "
                 "(https://git.sesse.net/?p=plocate;a=blob;f=updatedb.cpp;hb=cc0423b00042f51b648d0fb7cdadffc62c0b0daf#l627))."
                 " plocate-build output (plocate plocate-build.cpp line 171 "
                 "(https://git.sesse.net/?p=plocate;a=blob;f=plocate-build.cpp;hb=cc0423b00042f51b648d0fb7cdadffc62c0b0daf#l171))"
                 " and databases with max_version below 2 hold no directory data; Entry Type is then 'not recorded'. "
                 "mlocate: mlocate.db(5) (mlocate doc/mlocate.db.5 lines 25-123 "
                 "(https://sources.debian.org/src/mlocate/0.26-5/doc/mlocate.db.5/#L25-L123)): a directory record with the"
                 " directory's time and path, then the names in it, each marked as a directory or not. The database root "
                 "named in the header is a row of its own, 'directory (database root)'. A directory updatedb did not read,"
                 " because it was pruned, on an excluded file system or unreadable (mlocate src/updatedb.c lines 739-770 "
                 "(https://sources.debian.org/src/mlocate/0.26-5/src/updatedb.c/#L739-L770), mlocate src/db.h lines 41-42 "
                 "(https://sources.debian.org/src/mlocate/0.26-5/src/db.h/#L41-L42)), is listed in its parent with no "
                 "record of its own: 'directory, no directory time stored'. GNU locate: the LOCATE02 format (findutils "
                 "doc/find.texi lines 3162-3231 "
                 "(https://cgit.git.savannah.gnu.org/cgit/findutils.git/tree/doc/find.texi?id=c67264238d9487d5313a131674cd7a01ca299927#n3162),"
                 " read as findutils locate/locate.c lines 529-553 "
                 "(https://cgit.git.savannah.gnu.org/cgit/findutils.git/tree/locate/locate.c?id=c67264238d9487d5313a131674cd7a01ca299927#n529)"
                 " reads it): front-coded paths after a dummy LOCATE02 entry. It stores no entry type and no time, so "
                 "Entry Type is 'not recorded' and both time columns are blank. slocate databases and the pre-4.0 "
                 "findutils format are not read. Directory Time is the time stored for a directory row; Containing "
                 "Directory Time is the one stored for the directory the path is listed in. Both are the later of the "
                 "directory's st_ctime and st_mtime when updatedb read it (mlocate doc/mlocate.db.5 lines 85-90 "
                 "(https://sources.debian.org/src/mlocate/0.26-5/doc/mlocate.db.5/#L85-L90); plocate updatedb.cpp lines "
                 "198-213 "
                 "(https://git.sesse.net/?p=plocate;a=blob;f=updatedb.cpp;hb=cc0423b00042f51b648d0fb7cdadffc62c0b0daf#l198)),"
                 " shown in UTC to the microsecond (stored to the nanosecond). It is a time of the directory, not of the "
                 "listed file. updatedb stores 0 in place of a directory time less than 3 seconds before its own clock, or"
                 " later (plocate updatedb.cpp lines 115-148 "
                 "(https://git.sesse.net/?p=plocate;a=blob;f=updatedb.cpp;hb=cc0423b00042f51b648d0fb7cdadffc62c0b0daf#l115);"
                 " mlocate src/updatedb.c lines 134-166 "
                 "(https://sources.debian.org/src/mlocate/0.26-5/src/updatedb.c/#L134-L166), mlocate src/updatedb.c lines "
                 "798-806 (https://sources.debian.org/src/mlocate/0.26-5/src/updatedb.c/#L798-L806)), and plocate also "
                 "stores 0 for a directory skipped by name, one on an excluded file system and one it could not open "
                 "(plocate updatedb.cpp lines 680-685 "
                 "(https://git.sesse.net/?p=plocate;a=blob;f=updatedb.cpp;hb=cc0423b00042f51b648d0fb7cdadffc62c0b0daf#l680),"
                 " plocate updatedb.cpp lines 687-703 "
                 "(https://git.sesse.net/?p=plocate;a=blob;f=updatedb.cpp;hb=cc0423b00042f51b648d0fb7cdadffc62c0b0daf#l687),"
                 " plocate updatedb.cpp lines 715-731 "
                 "(https://git.sesse.net/?p=plocate;a=blob;f=updatedb.cpp;hb=cc0423b00042f51b648d0fb7cdadffc62c0b0daf#l715))."
                 " Such rows read 'directory, directory time stored as 0' and the time is blank. plocate lists a directory"
                 " under a pruned path with its time and nothing in it (plocate updatedb.cpp lines 525-531 "
                 "(https://git.sesse.net/?p=plocate;a=blob;f=updatedb.cpp;hb=cc0423b00042f51b648d0fb7cdadffc62c0b0daf#l525))."
                 " plocate does not list the root it scans (plocate updatedb.cpp lines 737-741 "
                 "(https://git.sesse.net/?p=plocate;a=blob;f=updatedb.cpp;hb=cc0423b00042f51b648d0fb7cdadffc62c0b0daf#l737),"
                 " plocate updatedb.cpp line 820 "
                 "(https://git.sesse.net/?p=plocate;a=blob;f=updatedb.cpp;hb=cc0423b00042f51b648d0fb7cdadffc62c0b0daf#l820)),"
                 " so paths directly under it have no Containing Directory Time. Paths are shown as UTF-8, other bytes as "
                 "backslash escapes. plocate and mlocate can be set to hide from a user the paths that user cannot reach; "
                 "this artifact lists each stored path whatever that setting is. Tested: packt_dfc_linux_mint_usb (Linux "
                 "Mint 22; the plocate version is not recorded in the image, which holds no dpkg status file) gives "
                 "509,291 rows from its plocate.db: 23,024 directories, 486,267 not directories, 3 directories stored with"
                 " time 0, and 24 paths under the scan root with no Containing Directory Time. Its 23,021 non-zero "
                 "directory times fall between 2024-07-21 12:45:50 and 12:54:22 UTC. 47,049 of the listed paths are files "
                 "or folders of the FAT32 volume the image holds. Cross-check: an independent reader written from "
                 "plocate's db.h and database-builder.cpp, run on an Ubuntu 26.04 virtual machine on a copy of the "
                 "database, gave the same 509,291 paths in the same order, with the same entry types and times, and for "
                 "each of the 56,002 trigrams in the database's hash table the number of blocks it stores equals the "
                 "number of decoded blocks holding that trigram. plocate is not installed on that machine, so plocate "
                 "itself was not run. Database Format held plocate on all 509,291 rows there, as one database matched the "
                 "declared paths. dissect_testdata_b43db37 (plocate, mlocate and GNU locate test databases) and "
                 "plaso_testdata_f951fc6 (an mlocate test database) keep their files at repository paths, which the paths "
                 "do not match, so they give 0 rows as registered; copies placed at the system paths, not registered, gave"
                 " 3,594 plocate, 3,318 mlocate and 3,575 GNU locate rows, and 10 mlocate rows. On those copies Database "
                 "Format and Source File separate the same rows; Source File stays because two databases of one format, as"
                 " in a chroot or a copied system, would not be told apart by format. The zstd backends (compression.zstd "
                 "on Python 3.14, backports.zstd and zstandard on Python 3.10) gave the same rows from both plocate "
                 "databases. Tested only with constructed databases: a big-endian plocate database, plocate version 0 and "
                 "max_version 1, a plocate database with no directory data as plocate-build writes it, and damaged "
                 "databases. Not exercised: a plocate.db in var/lib/mlocate (only the path pattern is tested), and a "
                 "locatedb whose origin is known (the source of the dissect_testdata file does not say how it was made). A"
                 " damaged database keeps the paths read before the damage, and the problem is logged and shown in Locate "
                 "Databases.",
        "paths": ('*/var/lib/plocate/plocate.db', '*/var/lib/mlocate/plocate.db', '*/var/lib/mlocate/mlocate.db',
                  '*/var/cache/locate/locatedb', '*/usr/local/var/locatedb'),
        "output_types": "standard",
        "artifact_icon": "search",
        "sample_data": {
            "dissect_testdata_b43db37": "plocate, mlocate and GNU locate test databases, OS and versions not established | 0 rows (its three databases are kept at repository paths, which the paths do not match)",
            "fedora44_arm64_dnf_known": "Fedora Linux 44 Server aarch64 | 0 rows (no member matches the declared paths)",
            "fedora44_arm64_firewalld_known": "Fedora Linux 44 Server aarch64 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386, dpkg info files for mlocate present | 0 rows (var/lib/mlocate holds no file)",
            "ou_defaced_webserver_ubuntu22": "Ubuntu 22.04.3 (per the publisher, not read from the image) | 0 rows (no member matches the declared paths; its root logical volume is read)",
            "packt_dfc_linux_mint_usb": "Linux Mint 22, plocate version not recorded in the image | 509,291 rows",
            "plaso_testdata_f951fc6": "mlocate test database, OS and version not established | 0 rows (its mlocate.db is kept at a repository path, which the paths do not match)",
            "rocky98_arm64_known": "Rocky Linux 9.8 aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_apport": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_apport_root": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_appstate": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_autostart": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_btmp": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_crontab": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cups": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_dconf": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_dpkgbackups": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_eds": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_gtkbookmarks": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_gtkbookmarks_chooser": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_gtkbookmarks_gui": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_gvfsmeta": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_launchers": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_lesshst": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_monitors": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_nautilusstars": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_nm_a": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_nm_b": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_nm_etcwifi": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_packages": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_pyhistory": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_screentime": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sqlitehist": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sshconfig": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sshkeys": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_thumbnails": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_tracker": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_units": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_upower": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usb": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usbstorage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_viminfo": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_vlc_known_20261018_step1": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_vlc_known_20261018_step2": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_vlc_known_20261018_step3": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_vlc_known_20261018_step3a_prefoff": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_wgethsts": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
    "locateDatabases": {
        "name": "Locate Databases",
        "description": "One row per plocate, mlocate or GNU locate database, with its format, the settings its "
                       "header and configuration block store, its path counts and its latest stored directory "
                       "time.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-23",
        "last_update_date": "2026-10-23",
        "requirements": "plocate path counts need zstd: Python 3.14 or later, or the backports.zstd or zstandard "
                        "package on an earlier Python",
        "category": "Locate Databases (Linux)",
        "notes": "Read from plocate.db in var/lib/plocate, and in var/lib/mlocate, where plocate-build's help says to put "
                 "it (plocate plocate-build.cpp lines 188-189 "
                 "(https://git.sesse.net/?p=plocate;a=blob;f=plocate-build.cpp;hb=cc0423b00042f51b648d0fb7cdadffc62c0b0daf#l188));"
                 " mlocate.db in var/lib/mlocate; and a GNU findutils locatedb in var/cache/locate, where Debian's "
                 "findutils build puts it "
                 "(https://salsa.debian.org/debian/findutils/-/blob/dd1f195249237ac011442188db9c49ff3184c290/debian/rules#L20),"
                 " or in usr/local/var, findutils' default when built with no prefix (findutils locate/Makefile.am line 20"
                 " "
                 "(https://cgit.git.savannah.gnu.org/cgit/findutils.git/tree/locate/Makefile.am?id=c67264238d9487d5313a131674cd7a01ca299927#n20)"
                 " names $(localstatedir)/locatedb). A database written elsewhere with updatedb -o or --output is not "
                 "found. The format is told by the magic at the start of the file, not by its name. Sources: plocate "
                 "1.1.25 (commit cc0423b0, GPL-2.0-or-later), whose header layout is the same from 1.1.0; mlocate 0.26 "
                 "(Debian 0.26-5, GPL-2.0, db.h without restriction); findutils 4.10.0 (commit c6726423, "
                 "GPL-3.0-or-later). The readers in scripts/linux_locate.py were written from these sources; no code was "
                 "taken from them. One row per database. Latest Directory Time is the latest directory time the database "
                 "stores. None of the three formats stores when updatedb ran; because updatedb stores 0 in place of a "
                 "directory time less than 3 seconds before its own clock, or later (plocate updatedb.cpp lines 115-148 "
                 "(https://git.sesse.net/?p=plocate;a=blob;f=updatedb.cpp;hb=cc0423b00042f51b648d0fb7cdadffc62c0b0daf#l115),"
                 " plocate updatedb.cpp lines 198-213 "
                 "(https://git.sesse.net/?p=plocate;a=blob;f=updatedb.cpp;hb=cc0423b00042f51b648d0fb7cdadffc62c0b0daf#l198);"
                 " mlocate src/updatedb.c lines 134-166 "
                 "(https://sources.debian.org/src/mlocate/0.26-5/src/updatedb.c/#L134-L166), mlocate src/updatedb.c lines "
                 "798-806 (https://sources.debian.org/src/mlocate/0.26-5/src/updatedb.c/#L798-L806)), updatedb read that "
                 "directory more than 3 seconds after its stored time, by the clock of the machine it ran on, so the run "
                 "took place after Latest Directory Time. It is blank for GNU locate, which stores no time. Format Version"
                 " is plocate's version and max_version (plocate db.h lines 8-16 "
                 "(https://git.sesse.net/?p=plocate;a=blob;f=db.h;hb=cc0423b00042f51b648d0fb7cdadffc62c0b0daf#l8); "
                 "updatedb writes max_version 2 and version 1, plocate database-builder.cpp line 531 "
                 "(https://git.sesse.net/?p=plocate;a=blob;f=database-builder.cpp;hb=cc0423b00042f51b648d0fb7cdadffc62c0b0daf#l531),"
                 " plocate database-builder.cpp line 683 "
                 "(https://git.sesse.net/?p=plocate;a=blob;f=database-builder.cpp;hb=cc0423b00042f51b648d0fb7cdadffc62c0b0daf#l683)),"
                 " or mlocate's version byte, or LOCATE02. Database Root is the root path mlocate stores in its header; "
                 "plocate and GNU locate store none, so it is blank for them (Database Root held no value on the one "
                 "plocate database of packt_dfc_linux_mint_usb). Visibility Check (as stored) is plocate's "
                 "check_visibility or mlocate's require visibility flag: 1 asks locate to show a user only the paths that "
                 "user can reach, a check locate makes only when the database file is owned by the locate group (plocate "
                 "or mlocate) and not readable by others (plocate plocate.1 lines 52-58 "
                 "(https://git.sesse.net/?p=plocate;a=blob;f=plocate.1;hb=cc0423b00042f51b648d0fb7cdadffc62c0b0daf#l52); "
                 "plocate updatedb.8.in lines 124-161, "
                 "https://git.sesse.net/?p=plocate;a=blob;f=updatedb.8.in;hb=cc0423b00042f51b648d0fb7cdadffc62c0b0daf#l124)."
                 " plocate reads a database whose max_version is below 2 as asking for the check (plocate plocate.cpp "
                 "lines 115-118 "
                 "(https://git.sesse.net/?p=plocate;a=blob;f=plocate.cpp;hb=cc0423b00042f51b648d0fb7cdadffc62c0b0daf#l115));"
                 " the column is blank there, as no flag is stored. Prune Bind Mounts, Pruned File System Types, Pruned "
                 "Names and Pruned Paths are the configuration block's values, one per line, as updatedb wrote them from "
                 "updatedb.conf and its options (plocate conf.cpp lines 650-670 "
                 "(https://git.sesse.net/?p=plocate;a=blob;f=conf.cpp;hb=cc0423b00042f51b648d0fb7cdadffc62c0b0daf#l650); "
                 "mlocate doc/mlocate.db.5 lines 35-66 "
                 "(https://sources.debian.org/src/mlocate/0.26-5/doc/mlocate.db.5/#L35-L66)); file system types are stored"
                 " in upper case (plocate conf.cpp lines 679-683 "
                 "(https://git.sesse.net/?p=plocate;a=blob;f=conf.cpp;hb=cc0423b00042f51b648d0fb7cdadffc62c0b0daf#l679)). "
                 "They are what updatedb was set to skip, so paths in pruned places are missing from the list for that "
                 "reason. GNU locate stores none of them. Paths is the number of paths read, Directories and Not "
                 "Directories split it where the format records the type (blank otherwise), and Directories With Time 0 "
                 "counts the directories stored with time 0. The database root of mlocate counts as a directory. Reading "
                 "Problems lists what stopped or limited the reading, such as a Python with no zstd decoder (Paths is then"
                 " blank, not 0) or damage. Tested: packt_dfc_linux_mint_usb, 1 row: plocate version 1, max_version 2, "
                 "little-endian, Latest Directory Time 2024-07-21 12:54:22 UTC, Visibility Check 1, Prune Bind Mounts 1, "
                 "51 file system types, 7 pruned paths, no pruned names, 509,291 paths. The independent reader described "
                 "in Locate Database Paths gave the same counts. Pruned Names was empty on that database and on the three "
                 "dissect_testdata copies and the plaso_testdata copy described there, and Reading Problems was empty on "
                 "all of them; Visibility Check (as stored) and Prune Bind Mounts (as stored) both held 1 on every plocate"
                 " and mlocate row and were blank on the GNU locate row, so the two columns were identical there. Under "
                 "Python 3.10 with no zstd package the plocate row keeps its header and configuration values, Paths is "
                 "blank and Reading Problems says why. Not exercised on real data: a database with pruned names, a "
                 "visibility flag of 0, and the cases listed in Locate Database Paths.",
        "paths": ('*/var/lib/plocate/plocate.db', '*/var/lib/mlocate/plocate.db', '*/var/lib/mlocate/mlocate.db',
                  '*/var/cache/locate/locatedb', '*/usr/local/var/locatedb'),
        "output_types": "standard",
        "artifact_icon": "database",
        "sample_data": {
            "dissect_testdata_b43db37": "plocate, mlocate and GNU locate test databases, OS and versions not established | 0 rows (its three databases are kept at repository paths, which the paths do not match)",
            "fedora44_arm64_dnf_known": "Fedora Linux 44 Server aarch64 | 0 rows (no member matches the declared paths)",
            "fedora44_arm64_firewalld_known": "Fedora Linux 44 Server aarch64 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386, dpkg info files for mlocate present | 0 rows (var/lib/mlocate holds no file)",
            "ou_defaced_webserver_ubuntu22": "Ubuntu 22.04.3 (per the publisher, not read from the image) | 0 rows (no member matches the declared paths; its root logical volume is read)",
            "packt_dfc_linux_mint_usb": "Linux Mint 22, plocate version not recorded in the image | 1 row",
            "plaso_testdata_f951fc6": "mlocate test database, OS and version not established | 0 rows (its mlocate.db is kept at a repository path, which the paths do not match)",
            "rocky98_arm64_known": "Rocky Linux 9.8 aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_apport": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_apport_root": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_appstate": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_authlog": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_autostart": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_btmp": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cron": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_crontab": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_cups": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_dconf": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_dpkgbackups": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_eds": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_gtkbookmarks": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_gtkbookmarks_chooser": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_gtkbookmarks_gui": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_gvfsmeta": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_journal": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_launchers": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_lesshst": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_logins": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_monitors": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_nautilusstars": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_nm_a": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_nm_b": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_nm_etcwifi": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_packages": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_pyhistory": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_recent": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_screentime": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_shutdown": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sqlitehist": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sshconfig": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sshkeys": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_sysinfo": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_thumbnails": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_tracker": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_trash": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_units": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_upower": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usb": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_usbstorage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_viminfo": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_vlc_known_20261018_step1": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_vlc_known_20261018_step2": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_vlc_known_20261018_step3": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_vlc_known_20261018_step3a_prefoff": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_wgethsts": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os

from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.linux_locate import TYPE_UNRECORDED, directory_time, read

_LABEL = 'Locate Databases'


def _databases(context):
    """(staged path, LocateDatabase) for each file that holds a database of a known format, in path order."""
    found = []
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError as exc:
            logfunc(f'{_LABEL}: {context.get_relative_path(path)} could not be read ({exc.strerror})')
            continue
        try:
            database = read(data)
        except ValueError as exc:
            logfunc(f'{_LABEL}: {context.get_relative_path(path)} was not read: {exc}')
            continue
        for problem in database.problems:
            logfunc(f'{_LABEL}: {context.get_relative_path(path)}: {problem}')
        found.append((path, database))
    return found


def _stamp(stored):
    return directory_time(*stored) if stored else ''


@artifact_processor
def locateDatabasePaths(context):
    data_headers = (('Containing Directory Time', 'datetime'), ('Directory Time', 'datetime'), 'Path',
                    'Entry Type', 'Database Format', 'Source File')
    data_list, read_from = [], []
    for path, database in _databases(context):
        relative = context.get_relative_path(path)
        read_from.append(path)
        for entry in database.entries:
            kind = entry.kind
            if kind.startswith('directory'):
                if entry.time is None:
                    kind += ', no directory time stored'
                elif entry.time == (0, 0):
                    kind += ', directory time stored as 0'
            data_list.append((_stamp(entry.container_time), _stamp(entry.time), entry.path, kind,
                              database.format, relative))
    return data_headers, data_list, '\n'.join(read_from)


def _values(configuration, name):
    if name not in configuration:
        return ''
    return '\n'.join(configuration[name])


@artifact_processor
def locateDatabases(context):
    data_headers = (('Latest Directory Time', 'datetime'), 'Database Format', 'Format Version', 'Database Root',
                    'Visibility Check (as stored)', 'Prune Bind Mounts (as stored)', 'Pruned File System Types',
                    'Pruned Names', 'Pruned Paths', 'Paths', 'Directories', 'Not Directories',
                    'Directories With Time 0', 'Reading Problems', 'Source File')
    data_list, read_from = [], []
    for path, database in _databases(context):
        read_from.append(path)
        total, directories, others, zero = database.counts()
        typed = any(entry.kind != TYPE_UNRECORDED for entry in database.entries)
        visibility = '' if database.visibility is None else str(database.visibility)
        data_list.append((
            _stamp(database.latest_directory_time()), database.format, database.version,
            database.root or '', visibility, _values(database.configuration, 'prune_bind_mounts'),
            _values(database.configuration, 'prunefs'), _values(database.configuration, 'prunenames'),
            _values(database.configuration, 'prunepaths'), total if database.paths_read else '',
            directories if typed else '', others if typed else '', zero if typed else '',
            '\n'.join(database.problems), context.get_relative_path(path)))
    return data_headers, data_list, '\n'.join(read_from)
