"""Web server logs for DLEAPP: Apache HTTP Server and nginx access and error logs, IIS W3C extended
access logs, and HTTP.sys error logs, with per-client, per-hour and per-status summaries of the access
entries.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "webServerAccessLogEntries": {
        "name": "Web Server Access Log Entries",
        "description": 'The lines of the Apache HTTP Server, nginx and IIS access logs, one row per line with text, imported into the LAVA database: the request time converted to UTC, and the client, user, request, status, response size, referer and user agent as written (decoded as UTF-8), with lines that do not parse kept whole.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Web Server Logs",
        "notes": 'Imports every line with text of the access logs into the LAVA database only, one row per line, because a busy server\'s logs are too large for the HTML, TSV and timeline outputs: on ou_defaced_webserver_ubuntu22 the 17 access log files hold 26,668,145 lines, about 20 GB uncompressed, reading and importing them took 860 seconds on the test machine, and the LAVA database, which also held the 13,978,005 error log rows of Web Server Error Log Entries, came to 34.4 GB. Web Server Access by Client, by Hour and by Status count these rows for the HTML report, and the log files themselves are in the report\'s data folder. Read: files whose name contains \'access\' under var/log/apache2, var/log/httpd and var/log/nginx, rotated ones included (a gzip file is found by its first two bytes, not its name), and the .log files under inetpub/logs/LogFiles/W3SVC* (IIS\'s default folder, https://learn.microsoft.com/en-us/iis/configuration/system.applicationhost/sites/site/logfile/) and Windows/System32/LogFiles/W3SVC*. Log Kind is Apache HTTP Server, nginx or IIS from the folder the file sits in. A file whose first line is a W3C directive (#Software, #Version or #Fields) is read as a W3C extended log, each line by the #Fields directive above it; IIS writes those times in UTC (https://learn.microsoft.com/en-us/iis/configuration/system.applicationhost/sites/site/logfile/, logFormat W3C, and https://learn.microsoft.com/en-us/windows/win32/http/w3c-logging). Any other file is read line by line as one of Apache\'s documented forms, common \'%h %l %u %t "%r" %>s %b\' and combined, the same with \' "%{Referer}i" "%{User-agent}i"\' after it (https://httpd.apache.org/docs/2.4/mod/mod_log_config.html, Examples), or vhost_combined, combined after \'%v:%p\' as the apache2.conf on ou_defaced_webserver_ubuntu22 defines it; nginx\'s predefined combined format writes the same shape (https://nginx.org/en/docs/http/ngx_http_log_module.html#log_format). A line written with another LogFormat or log_format is split only when it begins in one of these forms, and any line in no form is kept whole in Unparsed Line with Line Format \'not parsed\'; no line with text is dropped, and empty lines are not reported and are counted in the run log. Time (UTC) is %t, the time the request was received with its offset (https://httpd.apache.org/docs/2.4/mod/mod_log_config.html, %t), converted to UTC, and Time as Recorded the stamp as written. Client is %h (the client address unless HostnameLookups is on), Remote Log Name %l, User %u, Request Line %r as written, with the server\'s escapes (a backslash before a quote or backslash, C-style \\n and \\t for whitespace, \\xhh for other bytes) left in place, Method its first word when %r splits into three words, Status %>s, Response Bytes the size field as written, and Referer and User Agent the two quoted fields. Which size the server wrote is set by its LogFormat: %b is the response size without headers and %O, from mod_logio, the bytes sent including headers (https://httpd.apache.org/docs/2.4/mod/mod_log_config.html); ou_defaced_webserver_ubuntu22\'s own apache2.conf defines combined with %O and both files in its sites-available log access.log in combined. For IIS rows Client is c-ip, User cs-username, Method cs-method, Status sc-status, Response Bytes sc-bytes, Referer cs(Referer), User Agent cs(User-Agent) and Virtual Host cs-host, Request Line is cs-method, cs-uri-stem, cs-uri-query and cs-version put together, and the other fields go to Other Fields as name=value pairs. Fields after the user agent on an Apache or nginx line go to Other Fields. Line is the line number in the file and Source File the file. On ou_defaced_webserver_ubuntu22 (Apache) 26,668,143 lines were combined, one was not parsed (the last line of access.log, 25 characters with no line feed) and one was the last line of access.log.1.gz-2024043018.backup, whose gzip data ends early, kept whole with Line Format \'cut short by damaged gzip data\'; every line that could be decompressed from that file was read. other_vhosts_access.log was empty. As a second reading, on access.log and access.log.9.gz, splitting each of the 2,433,276 lines that hold no backslash at its quotes gave the same request, status, size, referer, user agent and client as the parser on every line. No IIS log, nginx log, vhost_combined line or common line was present on any tested image, so those paths are tested on synthetic files and unit-test lines only. A row records what the server wrote; the client address can be a proxy or a forged source, and a request does not show that its content ran.',
        "paths": ('*/var/log/apache2/*access*', '*/var/log/httpd/*access*', '*/var/log/nginx/*access*',
                  '*/inetpub/logs/LogFiles/W3SVC*/*.log', '*/Windows/System32/LogFiles/W3SVC*/*.log'),
        "output_types": "lava_only",
        "artifact_icon": "globe",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (no member matches the declared paths)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 0 rows (no member matches the declared paths)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (the private/var/log/apache2 folder holds no files)",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (the private/var/log/apache2 folder holds no files)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "ou_defaced_webserver_ubuntu22": "Ubuntu 22.04.3 | 26668145 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
    "webServerAccessByClient": {
        "name": "Web Server Access by Client",
        "description": "The access log entries imported by Web Server Access Log Entries, counted per client: "
                       "the first and last request time, the number of requests by status class, the "
                       "response bytes and the number of distinct user agents.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "The Web Server Access Log Entries artifact (webServerAccessLogEntries) must run in the "
                        "same session",
        "category": "Web Server Logs",
        "notes": "Counts the rows that Web Server Access Log Entries imported into the LAVA database in the same run, so it reports nothing when that artifact did not run; rows whose Line Format is 'not parsed' or 'cut short by damaged gzip data' are not counted. One row per Client value. First Request (UTC) and Last Request (UTC) are the earliest and latest Time (UTC); Requests is the number of rows; 2xx to 5xx count the rows whose Status is three characters starting with that digit and Other Status the rest (a '-' or other value); Response Bytes is the sum of Response Bytes over the rows where it starts with a digit, whatever size the server logged (see Web Server Access Log Entries); Distinct User Agents counts distinct User Agent values; Log Kinds lists the Log Kind values. On ou_defaced_webserver_ubuntu22 there were 15,871 clients; Other Status held 0 on every row and Log Kinds held one value on every row, Apache HTTP Server. A count is of log lines, so one client behind several addresses, or several behind one proxy address, is not separated.",
        "paths": None,
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "users",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no access log entries imported)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (no access log entries imported)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 0 rows (no access log entries imported)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no access log entries imported)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no access log entries imported)",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no access log entries imported)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (no access log entries imported)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no access log entries imported)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no access log entries imported)",
            "ou_defaced_webserver_ubuntu22": "Ubuntu 22.04.3 | 15871 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows (no access log entries imported)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no access log entries imported)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 0 rows (no access log entries imported)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no access log entries imported)",
        },
    },
    "webServerAccessByHour": {
        "name": "Web Server Access by Hour",
        "description": "The access log entries imported by Web Server Access Log Entries, counted per UTC hour: "
                       "the number of requests by status class and the number of distinct clients.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "The Web Server Access Log Entries artifact (webServerAccessLogEntries) must run in the "
                        "same session",
        "category": "Web Server Logs",
        "notes": 'Counts the rows that Web Server Access Log Entries imported into the LAVA database in the same run, so it reports nothing when that artifact did not run; rows that were not parsed, cut short or have no Time (UTC) are not counted. One row per UTC hour that has at least one request. Requests is the number of rows, Distinct Clients the number of distinct Client values, and 2xx to 5xx and Other Status count the rows by Status as Web Server Access by Client does. On ou_defaced_webserver_ubuntu22 347 hours had requests, between 2024-04-27 and 2024-06-06 UTC, and Other Status held 0 on every row. An hour with no row had no request in the logs read, which does not establish that the server was idle: rotated logs that were removed are not counted.',
        "paths": None,
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "clock",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no access log entries imported)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (no access log entries imported)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 0 rows (no access log entries imported)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no access log entries imported)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no access log entries imported)",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no access log entries imported)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (no access log entries imported)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no access log entries imported)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no access log entries imported)",
            "ou_defaced_webserver_ubuntu22": "Ubuntu 22.04.3 | 347 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows (no access log entries imported)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no access log entries imported)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 0 rows (no access log entries imported)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no access log entries imported)",
        },
    },
    "webServerAccessByStatus": {
        "name": "Web Server Access by Status",
        "description": "The access log entries imported by Web Server Access Log Entries, counted per status "
                       "code: the first and last request time, the number of requests and of distinct "
                       "clients.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "The Web Server Access Log Entries artifact (webServerAccessLogEntries) must run in the "
                        "same session",
        "category": "Web Server Logs",
        "notes": 'Counts the rows that Web Server Access Log Entries imported into the LAVA database in the same run, so it reports nothing when that artifact did not run; rows that were not parsed or cut short are not counted. One row per Status value as written. First Request (UTC) and Last Request (UTC) are the earliest and latest Time (UTC) of the rows with that status, Requests their number and Distinct Clients the number of distinct Client values among them. On ou_defaced_webserver_ubuntu22 there were 13 status values.',
        "paths": None,
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "bar-chart-2",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no access log entries imported)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (no access log entries imported)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 0 rows (no access log entries imported)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no access log entries imported)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no access log entries imported)",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no access log entries imported)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (no access log entries imported)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no access log entries imported)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no access log entries imported)",
            "ou_defaced_webserver_ubuntu22": "Ubuntu 22.04.3 | 13 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows (no access log entries imported)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no access log entries imported)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 0 rows (no access log entries imported)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no access log entries imported)",
        },
    },
    "webServerErrorLogEntries": {
        "name": "Web Server Error Log Entries",
        "description": 'The lines of the Apache HTTP Server and nginx error logs, one row per line with text, imported into the LAVA database: the time as written, module, level, process and thread, client and message, with lines that do not parse kept whole.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Web Server Logs",
        "notes": "Imports every line with text of the error logs into the LAVA database only, one row per line, for the same reason as Web Server Access Log Entries: on ou_defaced_webserver_ubuntu22 the 15 error log files hold 13,978,005 lines, about 3.3 GB uncompressed. Read: files whose name contains 'error' under var/log/apache2, var/log/httpd and var/log/nginx, gzip ones by content. A line is read in Apache's default error form for threaded MPMs, '[%{u}t] [%-m:%l] [pid %P:tid %T] ... [client %a] %M' (https://httpd.apache.org/docs/2.4/mod/core.html#errorlogformat), with the module, pid, tid and client parts optional so the older '[%t] [%l] [client %a] %M' form also reads, or in nginx's form, 'yyyy/mm/dd hh:mm:ss [level] pid#tid: message' (https://github.com/nginx/nginx/blob/release-1.26.0/src/core/ngx_log.c, ngx_log_error_core), whose client is taken from ', client: ' in the message. Any other line is kept whole in Message with Line Format 'not parsed'. Line Format says which form the line was read in and Log Kind which server's folder the file sits in. Time as Recorded is the time as written, and Local Time (no zone recorded) the same time as ISO 8601 text: neither form writes a UTC offset, so the zone is not recorded and no UTC time is given. Module, Level, Process ID, Thread ID, Client and Message are the parts as written. On ou_defaced_webserver_ubuntu22 13,977,988 lines were in the Apache form and 17 were not parsed: 15 'AH00558' lines that apache2 writes without a time at start up, and 2 beginning with NUL bytes. A message is the server's own diagnostic text, and a client address in it can be a proxy or forged.",
        "paths": ('*/var/log/apache2/*error*', '*/var/log/httpd/*error*', '*/var/log/nginx/*error*'),
        "output_types": "lava_only",
        "artifact_icon": "alert-triangle",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (no member matches the declared paths)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 0 rows (no member matches the declared paths)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (the private/var/log/apache2 folder holds no files)",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (the private/var/log/apache2 folder holds no files)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "ou_defaced_webserver_ubuntu22": "Ubuntu 22.04.3 | 13978005 rows",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
    "httpSysErrorLog": {
        "name": "HTTP.sys Error Log",
        "description": "The entries of the Windows HTTP Server API (HTTP.sys) error logs, read by each file's "
                       "#Fields directive: the time, client and server address and port, protocol version, "
                       "method, URL, status and the reason phrase as written.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-17",
        "last_update_date": "2026-10-17",
        "requirements": "none",
        "category": "Web Server Logs",
        "notes": 'Reads the .log files under Windows/System32/LogFiles/HTTPERR, the error logs of the Windows HTTP Server API (HTTP.sys), one row per data line, each line read by the #Fields directive above it; on every tested file the directive named date time c-ip c-port s-ip s-port cs-version cs-method cs-uri streamid streamid_ex sc-status s-siteid s-reason s-queuename transport fault-code, or, on szechuan_dc01_server2012r2, the same without streamid, streamid_ex, transport and fault-code. Microsoft documents the fields: the date and time are in UTC, a hyphen marks an empty field, and the reason phrase names the kind of error (https://learn.microsoft.com/en-us/windows/win32/http/format-of-the-http-server-api-error-logs). Time (UTC) is date and time, Time as Recorded the two as written, and Client IP, Client Port, Server IP, Server Port, Protocol Version, Method, URL, Status, Site ID, Reason and Queue Name are c-ip, c-port, s-ip, s-port, cs-version, cs-method, cs-uri, sc-status, s-siteid, s-reason and s-queuename as written; any other field goes to Other Fields as name=value pairs. A line that does not match its directive is kept whole in Unparsed Line. On pc_mus_001_win11 Client IP, Server IP, Server Port, Status, Site ID, Queue Name and Other Fields held one value on every row of the 3,491 data lines its three files held, and Unparsed Line held no value on any row: both addresses were the IPv6 loopback address with a zone index, the port one value, the status, site ID and queue name a hyphen, and the other fields streamid, streamid_ex, transport and fault-code, with the values -, -, TCP and -. On szechuan_dc01_server2012r2 one file held 2 data lines, and Other Fields held no value on either row there. A row records one error HTTP.sys logged. Site ID and Queue Name are the only fields that point to the site or application behind the port, and on both tested images they held a hyphen.',
        "paths": ('*/Windows/System32/LogFiles/HTTPERR/*.log',),
        "output_types": ["standard"],
        "artifact_icon": "alert-octagon",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "alihadi_challenge3_win81": "Windows 8.1 Enterprise build 9600 | 0 rows (no member matches the declared paths)",
            "alihadi_threatsim_server2019": "Windows Server 2019 Standard build 17763 | 0 rows (no member matches the declared paths)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "evidencelocker_macos14": "macOS 14.6.1 | 0 rows (no member matches the declared paths)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "ou_defaced_webserver_ubuntu22": "Ubuntu 22.04.3 | 0 rows (no member matches the declared paths)",
            "ou_ransomware_server2022": "Windows Server 2022 Standard build 20348 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 3491 rows",
            "szechuan_dc01_server2012r2": "Windows Server 2012 R2 Standard Evaluation build 9600 | 2 rows",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os
from collections import Counter

from scripts import web_server_logs as wsl
from scripts.ilapfuncs import artifact_processor, get_file_path, get_sqlite_db_records, logfunc

ACCESS_HEADERS = (('Time (UTC)', 'datetime'), 'Time as Recorded', 'Log Kind', 'Client', 'Remote Log Name', 'User',
                  'Method', 'Status', 'Response Bytes', 'Referer', 'User Agent',
                  'Virtual Host', 'Other Fields', 'Request Line', 'Line Format', 'Unparsed Line', 'Line',
                  'Source File')
ACCESS_TABLE = 'webserveraccesslogentries'
CUT = 'cut short by damaged gzip data'


def log_kind(path):
    """Which server's log a file is, from the folder it sits in."""
    lowered = path.replace('\\', '/').lower()
    if '/nginx/' in lowered:
        return 'nginx'
    if '/apache2/' in lowered or '/httpd/' in lowered:
        return 'Apache HTTP Server'
    if '/w3svc' in lowered:
        return 'IIS'
    return ''


def _log_files(context):
    return sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p))


def _w3c_access_row(record, number, unparsed, kind, relative):
    """One IIS W3C record as an access row; fields not shown in their own column go to Other Fields."""
    if not record:
        return ('', '', kind, '', '', '', '', '', '', '', '', '', '', '', 'W3C, ' + wsl.NOT_PARSED,
                unparsed, number, relative)
    shown = {'date', 'time', 'c-ip', 'cs-username', 'cs-method', 'cs-uri-stem', 'cs-uri-query', 'cs-version',
             'sc-status', 'sc-bytes', 'cs(Referer)', 'cs(Referrer)', 'cs(User-Agent)', 'cs-host'}
    other = '; '.join(f'{name}={value}' for name, value in record.items() if name not in shown)
    recorded = ' '.join(v for v in (record.get('date', ''), record.get('time', '')) if v)
    return (wsl.w3c_time(record), recorded, kind, record.get('c-ip', ''), '', record.get('cs-username', ''),
            record.get('cs-method', ''), record.get('sc-status', ''), record.get('sc-bytes', ''),
            record.get('cs(Referer)', record.get('cs(Referrer)', '')), record.get('cs(User-Agent)', ''),
            record.get('cs-host', ''), other, w3c_request(record), 'W3C', '', number, relative)


def w3c_request(record):
    """The request of a W3C record put together as 'method stem?query version', from the fields present."""
    target = record.get('cs-uri-stem', '')
    query = record.get('cs-uri-query', '')
    if query and query != '-':
        target += '?' + query
    return ' '.join(part for part in (record.get('cs-method', ''), target, record.get('cs-version', '')) if part)


def _is_w3c(path):
    """Whether a file begins with a W3C extended log directive."""
    for _number, text, _cut in wsl.open_lines(path, Counter()):
        if text.strip():
            return text.startswith('#Software:') or text.startswith('#Version:') or text.startswith('#Fields:')
    return False


def access_rows(path, relative, counts):
    """Yield the access rows of one log file."""
    kind = log_kind(path)
    if _is_w3c(path):
        lines = wsl.open_lines(path, counts)
        for number, record, unparsed in wsl.w3c_records(lines, counts):
            counts['W3C lines read'] += 1
            yield _w3c_access_row(record, number, unparsed, kind, relative)
        return
    cache = {}
    for number, text, cut in wsl.open_lines(path, counts):
        if not text:
            counts['empty lines, not reported'] += 1
            continue
        counts['lines read'] += 1
        if cut:
            counts['lines cut short by damaged gzip data, kept whole'] += 1
            yield ('', '', kind, '', '', '', '', '', '', '', '', '', '', '', CUT, text, number, relative)
            continue
        line = wsl.parse_access_line(text, cache)
        counts[line.form] += 1
        if line.form != wsl.NOT_PARSED and line.time == '':
            counts['times that are not a calendar time, Time (UTC) left blank'] += 1
        method = wsl.split_request(line.request)[0]
        yield (line.time, line.recorded, kind, line.client, line.logname, line.user, method, line.status, line.size, line.referer, line.agent, line.virtual_host, line.other,
               line.request, line.form, line.raw, number, relative)


@artifact_processor
def webServerAccessLogEntries(context):
    files = _log_files(context)
    results = context.create_artifact_result(headers=ACCESS_HEADERS)
    if not files:
        return results
    results.set_source_path('\n'.join(files))
    counts = Counter()

    def rows():
        for path in files:
            yield from access_rows(path, context.get_relative_path(path), counts)
        logfunc('Web Server Access Log Entries: ' +
                ', '.join(f'{n:,} {kind}' for kind, n in sorted(counts.items())))

    return results.extend(rows())


def _status_columns(prefix=''):
    """SQL for the request counts per status class."""
    column = f'{prefix}status'
    return (f"SUM({column} LIKE '2__'), SUM({column} LIKE '3__'), SUM({column} LIKE '4__'), "
            f"SUM({column} LIKE '5__'), SUM({column} NOT LIKE '2__' AND {column} NOT LIKE '3__' AND "
            f"{column} NOT LIKE '4__' AND {column} NOT LIKE '5__')")


_TIME = "(CASE WHEN typeof(time_utc) IN ('integer', 'real') THEN time_utc END)"
_PARSED = "line_format NOT LIKE '%not parsed%' AND line_format != '" + CUT + "'"


def _imported(context, query, label):
    """Rows of a query over the imported access table, or (source, []) when it was not imported."""
    source = get_file_path(context.get_files_found(), '_lava_artifacts.db')
    present = get_sqlite_db_records(
        source, f"SELECT name FROM sqlite_master WHERE type = 'table' AND name = '{ACCESS_TABLE}'")
    if not present:
        logfunc(f'{label}: no imported access log entries in this run (Web Server Access Log Entries found no '
                f'access log, or did not run), so there is nothing to count')
        return source, []
    return source, get_sqlite_db_records(source, query)


def _utc(value):
    return wsl.unix_utc(value)


@artifact_processor
def webServerAccessByClient(context):
    data_headers = (('First Request (UTC)', 'datetime'), ('Last Request (UTC)', 'datetime'), 'Client', 'Requests',
               '2xx', '3xx', '4xx', '5xx', 'Other Status', 'Response Bytes', 'Distinct User Agents', 'Log Kinds')
    query = (f"SELECT MIN({_TIME}), MAX({_TIME}), client, COUNT(*), {_status_columns()}, "
             f"SUM(CASE WHEN response_bytes GLOB '[0-9]*' THEN CAST(response_bytes AS INTEGER) ELSE 0 END), "
             f"COUNT(DISTINCT user_agent), GROUP_CONCAT(DISTINCT log_kind) FROM {ACCESS_TABLE} "
             f"WHERE {_PARSED} GROUP BY client ORDER BY COUNT(*) DESC, client")
    source, records = _imported(context, query, 'Web Server Access by Client')
    rows = [(_utc(r[0]), _utc(r[1])) + tuple(r[2:]) for r in records]
    return data_headers, rows, source


@artifact_processor
def webServerAccessByHour(context):
    data_headers = (('Hour (UTC)', 'datetime'), 'Requests', 'Distinct Clients', '2xx', '3xx', '4xx', '5xx',
               'Other Status')
    query = (f"SELECT CAST({_TIME} / 3600 AS INTEGER) * 3600 AS hour, COUNT(*), COUNT(DISTINCT client), "
             f"{_status_columns()} FROM {ACCESS_TABLE} WHERE {_PARSED} AND {_TIME} IS NOT NULL "
             f"GROUP BY hour ORDER BY hour")
    source, records = _imported(context, query, 'Web Server Access by Hour')
    rows = [(_utc(r[0]),) + tuple(r[1:]) for r in records]
    return data_headers, rows, source


@artifact_processor
def webServerAccessByStatus(context):
    data_headers = (('First Request (UTC)', 'datetime'), ('Last Request (UTC)', 'datetime'), 'Status', 'Requests',
               'Distinct Clients')
    query = (f"SELECT MIN({_TIME}), MAX({_TIME}), status, COUNT(*), COUNT(DISTINCT client) "
             f"FROM {ACCESS_TABLE} WHERE {_PARSED} GROUP BY status ORDER BY status")
    source, records = _imported(context, query, 'Web Server Access by Status')
    rows = [(_utc(r[0]), _utc(r[1])) + tuple(r[2:]) for r in records]
    return data_headers, rows, source


def error_rows(path, relative, counts):
    """Yield the error log rows of one file."""
    kind = log_kind(path)
    for number, text, cut in wsl.open_lines(path, counts):
        if not text:
            counts['empty lines, not reported'] += 1
            continue
        counts['lines read'] += 1
        if cut:
            counts['lines cut short by damaged gzip data, kept whole'] += 1
            yield ('', '', kind, '', '', '', '', '', text, CUT, number, relative)
            continue
        recorded, local, module, level, pid, tid, client, message, form = wsl.parse_error_line(text)
        counts[form] += 1
        yield (recorded, local, kind, module, level, pid, tid, client, message, form, number, relative)


@artifact_processor
def webServerErrorLogEntries(context):
    data_headers = ('Time as Recorded', 'Local Time (no zone recorded)', 'Log Kind', 'Module', 'Level', 'Process ID',
                    'Thread ID', 'Client', 'Message', 'Line Format', 'Line', 'Source File')
    files = _log_files(context)
    results = context.create_artifact_result(headers=data_headers)
    if not files:
        return results
    results.set_source_path('\n'.join(files))
    counts = Counter()

    def rows():
        for path in files:
            yield from error_rows(path, context.get_relative_path(path), counts)
        logfunc('Web Server Error Log Entries: ' +
                ', '.join(f'{n:,} {kind}' for kind, n in sorted(counts.items())))

    return results.extend(rows())


HTTPERR_SHOWN = ('c-ip', 'c-port', 's-ip', 's-port', 'cs-version', 'cs-method', 'cs-uri', 'sc-status', 's-siteid',
                 's-reason', 's-queuename')


def httperr_row(number, record, unparsed, relative):
    if not record:
        return ('', '') + ('',) * len(HTTPERR_SHOWN) + ('', unparsed, number, relative)
    other = '; '.join(f'{name}={value}' for name, value in record.items()
                      if name not in HTTPERR_SHOWN and name not in ('date', 'time'))
    recorded = ' '.join(v for v in (record.get('date', ''), record.get('time', '')) if v)
    return ((wsl.w3c_time(record), recorded) + tuple(record.get(name, '') for name in HTTPERR_SHOWN) +
            (other, '', number, relative))


@artifact_processor
def httpSysErrorLog(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Time as Recorded', 'Client IP', 'Client Port', 'Server IP',
               'Server Port', 'Protocol Version', 'Method', 'URL', 'Status', 'Site ID', 'Reason',
               'Queue Name', 'Other Fields', 'Unparsed Line', 'Line', 'Source File')
    files = _log_files(context)
    data_list = []
    counts = Counter()
    for path in files:
        relative = context.get_relative_path(path)
        for number, record, unparsed in wsl.w3c_records(wsl.open_lines(path, counts), counts):
            data_list.append(httperr_row(number, record, unparsed, relative))
    if counts:
        logfunc('HTTP.sys Error Log: ' + ', '.join(f'{n:,} {kind}' for kind, n in sorted(counts.items())))
    return data_headers, data_list, '\n'.join(files)
