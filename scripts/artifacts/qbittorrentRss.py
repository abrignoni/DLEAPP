"""qBittorrent RSS feeds, stored articles and auto-download rules, for DLEAPP.

Author: @AlexisBrignoni, Claude.

qBittorrent keeps its feed tree in rss/feeds.json and its rules in rss/download_rules.json under the config folder, and
one JSON file of articles per feed in rss/articles under the data folder. Keys come from qBittorrent release-5.3.0.
"""

__artifacts_v2__ = {
    "qbittorrentRssFeeds": {
        "name": "qBittorrent RSS Feeds",
        "description": "RSS feeds set up in qBittorrent, with the folder, URL, identifier and the number of articles "
                       "stored for each.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-21",
        "last_update_date": "2026-11-21",
        "requirements": "none",
        "category": "qBittorrent",
        "platforms": ("Windows", "macOS", "Linux"),
        "notes": "One row per feed in rss/feeds.json. Key names come from qBittorrent at commit "
                 "9213075dd5f7b352208361c6a84c1c115efc898e (release-5.3.0, src/base/rss/rss_feed.cpp, "
                 "rss_folder.cpp and rss_session.cpp). Tested on known data "
                 "(windows11_arm_qbittorrent_rss_known_20261121: qBittorrent 5.3.0 on Windows 11 with two "
                 "feeds served from the same computer). Other versions, macOS and Linux were not tested. Feed "
                 "is the name in the tree and Folder the folders above it. Stored Articles counts the entries "
                 "in the file named after the feed's UID. It is blank when that file is not in the extraction "
                 "or cannot be read. The feed's title and last build date are not in these files. Refresh "
                 "Interval is the refreshInterval key in seconds, which qBittorrent writes only when the feed "
                 "has its own interval, and had no value on any row of the known data. User is the folder "
                 "after Users, Documents and Settings or home in the path. User had no value on the known "
                 "data, whose profile folder is not under one.",
        "paths": ('*/qBittorrent/rss/feeds.json', '*/qBittorrent/config/rss/feeds.json',
                  '*/qBittorrent/rss/articles/*.json', '*/qBittorrent/data/rss/articles/*.json'),
        "output_types": ["html", "tsv", "lava"],
        "artifact_icon": "rss",
        "sample_data": {
            "windows11_arm_qbittorrent_rss_known_20261121": "Windows 11 build 26200 (ARM64), qBittorrent 5.3.0 | 2 rows",
            "windows11_arm_qbittorrent_known_20261107": "Windows 11 build 26200 (ARM64), qBittorrent 5.3.0 | 0 rows (no feeds set up)",
        },
    },
    "qbittorrentRssArticles": {
        "name": "qBittorrent RSS Articles",
        "description": "Articles qBittorrent stored from its RSS feeds, with the date, title, author, links and "
                       "whether each is marked read.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-21",
        "last_update_date": "2026-11-21",
        "requirements": "none",
        "category": "qBittorrent",
        "platforms": ("Windows", "macOS", "Linux"),
        "notes": "One row per article in rss/articles/<feed UID>.json. Key names come from qBittorrent at "
                 "commit 9213075dd5f7b352208361c6a84c1c115efc898e (release-5.3.0, src/base/rss/rss_article.cpp "
                 "and feed_serializer.cpp). Tested on known data "
                 "(windows11_arm_qbittorrent_rss_known_20261121: qBittorrent 5.3.0 on Windows 11, four "
                 "articles from feeds served on the same computer). Other versions, macOS and Linux were not "
                 "tested. Article Date is the date key. qBittorrent fills it from the date the feed gave the "
                 "article. When the feed gave none, or one it could not read, qBittorrent stores the time it "
                 "updated the feed (rss_parser.cpp and rss_feed.cpp at the same commit). It is not when anyone "
                 "saw the article. On the known data all four equal the pubDate served. It is blank when the "
                 "stored text does not parse or carries no UTC offset. Feed and Feed URL are joined from "
                 "feeds.json by the UID in the file name, and are blank when no feed has that UID. Feed is the "
                 "feed's folders and name joined with a slash. Is Read is the isRead key, and an article "
                 "without the key reads as No, the default in rss_article.cpp. Is Read does not prove a person "
                 "read the article: on the known data the article the auto-download rule matched was set read "
                 "with no read action. Author held one value on all four rows of the known data, because the "
                 "test feeds gave every article the same author. Torrent URL is the torrentURL key. On the "
                 "three known data articles with no enclosure it held the same value as Link, so a value there "
                 "is not proof the article offered a torrent. User is the folder after Users, Documents and "
                 "Settings or home in the path. User had no value on the known data, whose profile folder is "
                 "not under one.",
        "paths": ('*/qBittorrent/rss/feeds.json', '*/qBittorrent/config/rss/feeds.json',
                  '*/qBittorrent/rss/articles/*.json', '*/qBittorrent/data/rss/articles/*.json'),
        "output_types": ["standard"],
        "artifact_icon": "rss",
        "sample_data": {
            "windows11_arm_qbittorrent_rss_known_20261121": "Windows 11 build 26200 (ARM64), qBittorrent 5.3.0 | 4 rows",
            "windows11_arm_qbittorrent_known_20261107": "Windows 11 build 26200 (ARM64), qBittorrent 5.3.0 | 0 rows (no feeds set up)",
        },
    },
    "qbittorrentRssRules": {
        "name": "qBittorrent RSS Download Rules",
        "description": "Auto-download rules in qBittorrent, with the text each must and must not contain, the feeds "
                       "it applies to, the save path and the stored last match value.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-21",
        "last_update_date": "2026-11-21",
        "requirements": "none",
        "category": "qBittorrent",
        "platforms": ("Windows", "macOS", "Linux"),
        "notes": "One row per rule in rss/download_rules.json. Key names come from qBittorrent at commit "
                 "9213075dd5f7b352208361c6a84c1c115efc898e (release-5.3.0, "
                 "src/base/rss/rss_autodownloadrule.cpp). Tested on known data "
                 "(windows11_arm_qbittorrent_rss_known_20261121: qBittorrent 5.3.0 on Windows 11, one rule set "
                 "through the Web API). Other versions, macOS and Linux were not tested. Last Match is the "
                 "lastMatch key. On the known data it held the matched article's date, about five hours before "
                 "the rule fired, so it is not the time the rule ran. Save Path is the savePath key and Add "
                 "Stopped the addPaused key. The source marks both as deprecated and prefers the stored "
                 "torrent parameters when it loads a rule. They agreed on the known data. Other Values holds "
                 "these values when set, as name=value: category, episode filter, regular expression and smart "
                 "filter use, ignore days, a priority other than 0, content layout and previously matched "
                 "episodes. Other Values had no value on the one row of the known data. The stored torrent "
                 "parameters are not reported. User is the folder after Users, Documents and Settings or home "
                 "in the path. User had no value on the known data, whose profile folder is not under one.",
        "paths": ('*/qBittorrent/rss/download_rules.json', '*/qBittorrent/config/rss/download_rules.json'),
        "output_types": ["standard"],
        "artifact_icon": "filter",
        "sample_data": {
            "windows11_arm_qbittorrent_rss_known_20261121": "Windows 11 build 26200 (ARM64), qBittorrent 5.3.0 | 1 row",
            "windows11_arm_qbittorrent_known_20261107": "Windows 11 build 26200 (ARM64), qBittorrent 5.3.0 | 0 rows (no rules file)",
        },
    },
}

import json
import os
from datetime import timezone
from email.utils import parsedate_to_datetime

from scripts.ilapfuncs import artifact_processor, logfunc


def _user(relative):
    parts = relative.replace('\\', '/').split('/')
    for index, part in enumerate(parts[:-1]):
        if part.lower() in ('users', 'documents and settings', 'home'):
            return parts[index + 1]
    return ''


def _json(path, label):
    try:
        with open(path, encoding='utf-8', errors='replace') as handle:
            return json.load(handle)
    except (OSError, ValueError) as exc:
        logfunc(f'{label}: could not read {os.path.basename(path)}: {type(exc).__name__}')
        return None


def _when(value):
    if not isinstance(value, str) or not value.strip():
        return ''
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        return ''
    return parsed.astimezone(timezone.utc) if parsed.tzinfo else ''


def _uid_key(value):
    return str(value or '').strip('{}').replace('-', '').lower()


def _walk(tree, folder=()):
    for name, value in tree.items():
        if isinstance(value, str):
            yield name, folder, {'url': value or name}
        elif isinstance(value, dict) and 'url' in value:
            yield name, folder, value
        elif isinstance(value, dict):
            yield from _walk(value, folder + (name,))


def _files(context, name):
    return sorted(str(p) for p in context.get_files_found()
                  if os.path.isfile(str(p)) and os.path.basename(str(p)).lower() == name)


def _article_files(context):
    found = {}
    for path in sorted(str(p) for p in context.get_files_found()):
        if os.path.isfile(path) and path.lower().endswith('.json') and \
                os.path.basename(os.path.dirname(path)).lower() == 'articles':
            found.setdefault(os.path.splitext(os.path.basename(path))[0].lower(), []).append(path)
    return found


def _feeds(context, label):
    for path in _files(context, 'feeds.json'):
        tree = _json(path, label)
        if isinstance(tree, dict):
            yield path, list(_walk(tree))


@artifact_processor
def qbittorrentRssFeeds(context):
    data_headers = ('Feed', 'Folder', 'URL', 'UID', 'Refresh Interval (seconds)', 'Stored Articles', 'User')
    data_list, sources = [], []
    articles = _article_files(context)
    for path, feeds in _feeds(context, 'qBittorrent RSS Feeds'):
        user = _user(context.get_relative_path(path))
        for name, folder, feed in feeds:
            count = ''
            for candidate in articles.get(_uid_key(feed.get('uid')), ()):
                if _user(context.get_relative_path(candidate)) == user:
                    stored = _json(candidate, 'qBittorrent RSS Feeds')
                    if isinstance(stored, list):
                        count = len(stored)
                        break
            data_list.append((name, '/'.join(folder), feed.get('url', ''), feed.get('uid', ''),
                              feed.get('refreshInterval', ''), count, user))
        if feeds:
            sources.append(path)
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def qbittorrentRssArticles(context):
    data_headers = (('Article Date', 'datetime'), 'Title', 'Feed', 'Feed URL', 'Author', 'Link', 'Torrent URL',
                    'Is Read', 'Description', 'Article ID', 'User')
    data_list, sources = [], []
    names = {}
    for path, feeds in _feeds(context, 'qBittorrent RSS Articles'):
        user = _user(context.get_relative_path(path))
        for name, folder, feed in feeds:
            names[(user, _uid_key(feed.get('uid')))] = ('/'.join(folder + (name,)), feed.get('url', ''))
    for stem, paths in sorted(_article_files(context).items()):
        for path in paths:
            stored = _json(path, 'qBittorrent RSS Articles')
            if not isinstance(stored, list):
                continue
            user = _user(context.get_relative_path(path))
            feed, url = names.get((user, stem), ('', ''))
            rows = 0
            for entry in stored:
                if not isinstance(entry, dict):
                    continue
                data_list.append((_when(entry.get('date')), entry.get('title', ''), feed, url, entry.get('author', ''),
                                  entry.get('link', ''), entry.get('torrentURL', ''),
                                  'Yes' if entry.get('isRead') is True else 'No', entry.get('description', ''),
                                  entry.get('id', ''), user))
                rows += 1
            if rows:
                sources.append(path)
    data_list.sort(key=lambda row: (row[0] == '', str(row[0]), row[2], row[9]))
    return data_headers, data_list, '\n'.join(sources)


@artifact_processor
def qbittorrentRssRules(context):
    data_headers = (('Last Match', 'datetime'), 'Rule', 'Enabled', 'Must Contain', 'Must Not Contain', 'Affected Feeds',
                    'Save Path', 'Add Stopped', 'Other Values', 'User')
    data_list, sources = [], []
    for path in _files(context, 'download_rules.json'):
        rules = _json(path, 'qBittorrent RSS Download Rules')
        if not isinstance(rules, dict):
            continue
        user = _user(context.get_relative_path(path))
        for name, rule in rules.items():
            if not isinstance(rule, dict):
                continue
            other = []
            for key, shown in (('assignedCategory', 'category'), ('episodeFilter', 'episode_filter'),
                               ('useRegex', 'use_regex'), ('smartFilter', 'smart_filter'),
                               ('ignoreDays', 'ignore_days'), ('priority', 'priority'),
                               ('torrentContentLayout', 'content_layout'),
                               ('previouslyMatchedEpisodes', 'previously_matched')):
                value = rule.get(key)
                if value not in (None, '', False, 0, []):
                    other.append(f"{shown}={', '.join(value) if isinstance(value, list) else value}")
            flag = {True: 'Yes', False: 'No'}
            feeds = rule.get('affectedFeeds')
            data_list.append((_when(rule.get('lastMatch')), name, flag.get(rule.get('enabled'), ''),
                              rule.get('mustContain', ''), rule.get('mustNotContain', ''),
                              '\n'.join(feeds) if isinstance(feeds, list) else '', rule.get('savePath', ''),
                              flag.get(rule.get('addPaused'), ''), '; '.join(other), user))
        if rules:
            sources.append(path)
    return data_headers, data_list, '\n'.join(sources)
