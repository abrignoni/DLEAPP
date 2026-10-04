"""Items in a user's CoreSpotlight store on macOS, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "macosCoreSpotlightItems": {
        "name": "CoreSpotlight Items",
        "description": "Items in a user's CoreSpotlight store, with the app each is stored under, the dates "
                       'stored for it, its title, snippet, authors, recipients and their addresses, and any link '
                       'stored with it.',
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-27",
        "last_update_date": "2026-09-27",
        "requirements": "none",
        "category": "Spotlight (macOS)",
        "notes": (
            'Reads each CoreSpotlight store, a folder under a Library/Metadata/CoreSpotlight '
            'folder holding store.db, .store.db and the dbStr-N.map files (index.spotlightV3, in '
            "the one user's Library, on both tested images), with the Spotlight store reader "
            'Spotlight Store Files uses, whose notes give the store layout, its source and the '
            'rules measured where that source is silent. Neither store.db nor .store.db names a '
            'page for the attribute tables on either tested image, so the dbStr files hold them. '
            'On these stores the reader was compared with spotlight_parser 1.0.4 '
            '(https://github.com/ydkhatri/spotlight_parser/tree/82e80705b172489180f1a2b8c8681033a0e9c0b1), '
            'run on the four store files of dleapp_macos_bigsur and the public MacBook Pro '
            'logical extraction (macOS 15.4, corpus key mvs2026_macbookpro_macos15): it gives the same '
            'records, 56 in store.db and 58 in .store.db on dleapp_macos_bigsur and 11,783 in '
            'each copy on the MacBook Pro, with the same identifier, parent, flags and update '
            'time on every one, and the same value for every attribute reported here, 188,523 '
            'values in all, a localized string compared as its first version that is not empty. '
            'Each row is an item of the store, and App is the bundle identifier the item is '
            "stored under, _kMDItemBundleID. Two kinds of record give no row, and each copy's "
            'count of them is in the run log: those whose App is com.apple.helpviewer (none on '
            'dleapp_macos_bigsur, 11,254 in each copy on the MacBook Pro), which each hold '
            '_kMDItemHelpIdentifier, _kMDItemHelpPath, _kMDItemHelpSummary, _kMDItemHelpTags and '
            '_kMDItemHelpTitle and none of the dates reported here other than Expiration (UTC) '
            'and Record Updated (UTC), and the one record in each copy with no App, identifier 1, '
            'which holds only kMDStoreUUID, kMDStoreProperties, kMDStoreAccumulatedSizes and '
            '_kStoreMetadataVersion. Both copies are read: an item the two copies hold with the '
            'same values is one row whose Source File lists both, and an item they hold '
            'differently gives a row for each copy, so 26 of the 86 rows on dleapp_macos_bigsur '
            'and 497 of the 559 on the MacBook Pro come from both copies. Every item the copies '
            'hold differently (29 on dleapp_macos_bigsur and 31 on the MacBook Pro) was updated '
            'later in .store.db. On dleapp_macos_bigsur all 29 differ in Record Updated (UTC), 15 '
            'also in Recipients, 10 in Authors and 1 in each of Interesting Date (UTC), Last Used '
            '(UTC) and Use Count (as stored), and .store.db holds 2 items store.db does not; on '
            'the MacBook Pro all 31 are Mail items that differ only in Record Updated (UTC) and '
            'Expiration (UTC), which store.db holds as 4001-01-01 00:00:00 and .store.db does not '
            'hold. A store file under System/Volumes/Data with the same bytes as the file at the '
            "same path outside it is not read again, as the MacBook Pro's 2 copies there are. "
            'Interesting Date (UTC) is _kMDItemInterestingDate, which MDItem.h does not describe, '
            'and the rows are in its order, those without one last (15 on dleapp_macos_bigsur and '
            '110 on the MacBook Pro). On all but 2 rows holding it, a Notes row and a Reminders '
            'row on the MacBook Pro, it repeats a date the row holds in another column: on '
            'dleapp_macos_bigsur it equals Content Created (UTC) on 57 of the 71 rows holding it '
            'and Last Used (UTC) on 15, and on the MacBook Pro Start (UTC) on 214 of the 449, '
            'Mail Received (UTC) on 119, Content Created (UTC) on 80, Content Modified (UTC) on '
            '56 and Last Used (UTC) on 26 (a row can match two). Content Created (UTC), Content '
            'Modified (UTC) and Last Used (UTC) are kMDItemContentCreationDate, '
            'kMDItemContentModificationDate and kMDItemLastUsedDate, and Start (UTC), End (UTC), '
            'Mail Received (UTC) and Expiration (UTC) are kMDItemStartDate, kMDItemEndDate, '
            'com_apple_mail_dateReceived and _kMDItemExpirationDate. These and Interesting Date '
            '(UTC) are read as the Cocoa timestamps the store layout documentation describes for '
            'date values '
            '(https://github.com/libyal/dtformats/blob/308ce8c38df2eb95a71b6e832b3f9803f0c4b169/documentation/Apple%20Spotlight%20store%20database%20file%20format.asciidoc), '
            'seconds since 1 January 2001, and shown in UTC, which the Mail and Messages '
            'comparisons below bear out. MDItem.h describes the two content dates as having an '
            'application specific semantic and the last used date as updated by LaunchServices '
            'every time a file is opened by double clicking or by asking LaunchServices to open '
            'it, a description of files; what sets it on these items is not established '
            '(Reference: Apple, MDItem.h, the Metadata framework header of the macOS SDK, '
            'System/Library/Frameworks/CoreServices.framework/Frameworks/Metadata.framework/Headers/MDItem.h '
            'in MacOSX26.5.sdk). MDItem.h describes neither kMDItemStartDate nor kMDItemEndDate, '
            'and on the MacBook Pro the 214 rows holding them are com.apple.CalendarUI items. Nor '
            'does MDItem.h describe _kMDItemExpirationDate, and what that date marks is not '
            'established: the latest on both images is 4001-01-01 00:00:00, held by 63 of the 75 '
            'rows holding one on dleapp_macos_bigsur and 250 of the 284 on the MacBook Pro. Used '
            'Dates (UTC) lists kMDItemUsedDates one per line, and every one falls exactly on an '
            'hour, 05:00 or 08:00 UTC on both images, so the time of day of a use is not '
            'established from them. Use Count (as stored) is kMDItemUseCount, and it equals the '
            'number of used dates on 4 of the 15 rows holding both on dleapp_macos_bigsur and 13 '
            'of 45 on the MacBook Pro. MDItem.h describes neither of those two. Record Updated '
            "(UTC) is the record's last update time, read as in Spotlight Store Files "
            '(microseconds since 1 January 1970, which the documentation assumes to be UTC); a '
            'value too large for a date is left blank, which no tested store holds. Title, '
            'Display Name, Subject, Description, Authors, Author Addresses, Author Email '
            'Addresses, Recipients and Recipient Addresses are kMDItemTitle, kMDItemDisplayName, '
            'kMDItemSubject, kMDItemDescription, kMDItemAuthors, kMDItemAuthorAddresses, '
            'kMDItemAuthorEmailAddresses, kMDItemRecipients and kMDItemRecipientAddresses, which '
            'MDItem.h describes; Primary Recipient Email Addresses, Account Handles and Content '
            'URL are kMDItemPrimaryRecipientEmailAddresses, kMDItemAccountHandles and '
            'kMDItemContentURL, which it does not, and Snippet is _kMDItemSnippet. Lists show one '
            'entry per line, leaving out empty entries. On the MacBook Pro each copy holds 120 '
            'Mail items (com.apple.mail), 97 of them with a received date, and the Mail Received '
            '(UTC) of each of those 97 equals the date_received of exactly one message of the '
            'Envelope Index (Mail/V10/MailData), the message whose ROWID its External ID (as '
            'stored) holds. Against that message, on all 97, Content Created (UTC) is date_sent, '
            'Subject is the subject the Envelope Index stores, without the prefix it keeps apart '
            '(4 of the 97 have one), and Primary Recipient Email Addresses are the addresses its '
            "recipients table lists with type 0; Author Email Addresses are the sender's address "
            'on 89 and on all 97 ignoring case, and Authors the comment its addresses table '
            "stores with the sender's address on 96. 1 of the 98 messages of the Envelope Index "
            'has no item. Messages items (com.apple.MobileSMS) were compared with chat.db, and '
            'From Me (as stored) is com_apple_mobilesms_fromMe, which MDItem.h does not describe. '
            'On the MacBook Pro each of the 5 messages in chat.db has an item in each copy whose '
            "External ID (as stored) is the message's guid, with From Me (as stored) equal to "
            'is_from_me, Content Created (UTC) within one second of the message date and Snippet '
            'equal to its text, and the other 5 items each carry the chat_identifier of one of '
            "chat.db's 5 chats as External ID. On dleapp_macos_bigsur the 25 messages in chat.db "
            'each have such an item in .store.db (24 in store.db), with From Me and Content '
            'Created agreeing the same way on all of them, and Snippet equal to the text on 15, '
            'equal once runs of white space are collapsed on 5, and absent on the other 5, whose '
            'text is only the object replacement character U+FFFC. 5 more items (4 in store.db) '
            'carry an External ID made of at_0_ and the guid of one of those 5 messages, each of '
            'which holds one attachment in chat.db. Of the other 2 items in each copy, one '
            "carries the chat_identifier of chat.db's only chat and the other an identifier that "
            'matches no value in any table of chat.db. Also on dleapp_macos_bigsur, each copy '
            "holds 17 Safari items: Content URL is a URL in Safari's History.db on 13, 10 of "
            'which hold a Last Used (UTC), and a URL found only in Bookmarks.plist on the other '
            '4, none of which holds one. Domain Identifier (as stored) and External ID (as '
            'stored) are _kMDItemDomainIdentifier and _kMDItemExternalID, reported as stored; '
            'what External ID holds depends on the app, as those comparisons show. User is the '
            'folder under Users in the path the store was read from, and it holds one value on '
            "each tested image, as each holds one user's store. Content Modified (UTC), Start "
            '(UTC), End (UTC), Mail Received (UTC), Subject, Author Email Addresses and Primary '
            'Recipient Email Addresses are empty on every row of dleapp_macos_bigsur and hold '
            'values on the MacBook Pro; on dleapp_macos_bigsur the 2 items in each copy holding '
            'kMDItemSubject hold an empty one. Neither tested store has a record page that cannot '
            'be read or a record whose values cannot all be decoded; those cases and a file that '
            'is not a Spotlight store were tested on constructed files, and each is written to '
            "the run log. The other attributes of an item, the store's full-text index files and "
            'its Cache folder are not reported, and neither are files under CoreSpotlight with '
            "other names, among them those of the MacBook Pro's SpotlightKnowledge folder, which "
            'holds a SQLite database named kg, and the skg_store.db and .skg_store.db files in '
            'two folders of its SpotlightKnowledgeEvents folder, each of which spotlight_parser '
            'reads as one record with no _kMDItemBundleID. No member of the four registered '
            'Windows disk images or windows11_arm_parallels matches the declared paths.'
        ),
        "paths": ('*/Library/Metadata/CoreSpotlight/*/store.db', '*/Library/Metadata/CoreSpotlight/*/.store.db',
                  '*/Library/Metadata/CoreSpotlight/*/dbStr-*.map.*'),
        "output_types": ["html", "tsv", "timeline", "lava"],
        "artifact_icon": "search",
        "sample_data": {
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 86 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (no member matches the declared paths)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
        },
    },
}

import os

from scripts.artifacts.macosSpotlightStore import _cocoa, _cocoa_text, _text, _unix_micro
from scripts.ilapfuncs import artifact_processor, logfunc
from scripts.macos_plists import unique_sources, user_from_path
from scripts.macos_powerlog import merge_sources
from scripts.macos_spotlight import Store, StoreError

_STORES = ('store.db', '.store.db')
_HELP = 'com.apple.helpviewer'


@artifact_processor
def macosCoreSpotlightItems(context):
    data_headers = (('Interesting Date (UTC)', 'datetime'), ('Content Created (UTC)', 'datetime'),
                    ('Content Modified (UTC)', 'datetime'), ('Last Used (UTC)', 'datetime'), 'Used Dates (UTC)',
                    'Use Count (as stored)', ('Start (UTC)', 'datetime'), ('End (UTC)', 'datetime'),
                    ('Mail Received (UTC)', 'datetime'), 'App', 'Title', 'Display Name', 'Subject', 'Snippet',
                    'Authors', 'Author Addresses', 'Author Email Addresses', 'Recipients', 'Recipient Addresses',
                    'Primary Recipient Email Addresses', 'Account Handles', 'From Me (as stored)', 'Content URL',
                    'Description', 'Domain Identifier (as stored)', 'External ID (as stored)',
                    ('Expiration (UTC)', 'datetime'), ('Record Updated (UTC)', 'datetime'), 'User', 'Source File')
    files = [str(path) for path in context.get_files_found()
             if os.path.basename(str(path)) in _STORES and os.path.isfile(str(path))]
    paths, _skipped = unique_sources(context, files, label='CoreSpotlight Items')
    records, read = [], []
    for path in paths:
        relative = context.get_relative_path(path)
        try:
            store = Store(path)
        except (OSError, StoreError) as error:
            logfunc(f'CoreSpotlight Items: {relative} not read: {error}')
            continue
        items = list(store.items())
        if store.unreadable_pages or store.incomplete:
            logfunc(f'CoreSpotlight Items: {relative}: {store.unreadable_pages} record page(s) not read, '
                    f'{store.incomplete} record(s) not fully decoded')
        user = user_from_path(relative)
        help_topics = no_app = 0
        for item in items:
            attributes = item.attributes
            app = attributes.get('_kMDItemBundleID')
            if not isinstance(app, str) or not app:
                no_app += 1
                continue
            if app == _HELP:
                help_topics += 1
                continue
            records.append(((
                _cocoa(attributes.get('_kMDItemInterestingDate')),
                _cocoa(attributes.get('kMDItemContentCreationDate')),
                _cocoa(attributes.get('kMDItemContentModificationDate')),
                _cocoa(attributes.get('kMDItemLastUsedDate')),
                _cocoa_text(attributes.get('kMDItemUsedDates')),
                _text(attributes.get('kMDItemUseCount')),
                _cocoa(attributes.get('kMDItemStartDate')),
                _cocoa(attributes.get('kMDItemEndDate')),
                _cocoa(attributes.get('com_apple_mail_dateReceived')),
                app,
                _text(attributes.get('kMDItemTitle')),
                _text(attributes.get('kMDItemDisplayName')),
                _text(attributes.get('kMDItemSubject')),
                _text(attributes.get('_kMDItemSnippet')),
                _text(attributes.get('kMDItemAuthors')),
                _text(attributes.get('kMDItemAuthorAddresses')),
                _text(attributes.get('kMDItemAuthorEmailAddresses')),
                _text(attributes.get('kMDItemRecipients')),
                _text(attributes.get('kMDItemRecipientAddresses')),
                _text(attributes.get('kMDItemPrimaryRecipientEmailAddresses')),
                _text(attributes.get('kMDItemAccountHandles')),
                _text(attributes.get('com_apple_mobilesms_fromMe')),
                _text(attributes.get('kMDItemContentURL')),
                _text(attributes.get('kMDItemDescription')),
                _text(attributes.get('_kMDItemDomainIdentifier')),
                _text(attributes.get('_kMDItemExternalID')),
                _cocoa(attributes.get('_kMDItemExpirationDate')),
                _unix_micro(item.updated),
                user), relative))
        read.append(path)
        if help_topics or no_app:
            logfunc(f'CoreSpotlight Items: {relative}: {help_topics} Help Viewer record(s) and {no_app} record(s) '
                    f'with no app not reported')
    merged = merge_sources(records)
    merged.sort(key=lambda entry: (entry[0][0] == '', str(entry[0][0]), entry[0][9], str(entry[0][27])))
    data_list = [values + ('\n'.join(sources),) for values, sources in merged]
    return data_headers, data_list, '\n'.join(read)
