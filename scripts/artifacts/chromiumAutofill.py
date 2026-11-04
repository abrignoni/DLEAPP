__artifacts_v2__ = {
    "chromiumAutofill": {
        "name": "Chromium Autofill Entries",
        "description": "Rows of the autofill table from the Web Data databases of Google Chrome, "
                       "Microsoft Edge, Brave, Vivaldi, Opera and Chromium profiles: form field name, "
                       "stored value, stored count and the created and last used times.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-09-23",
        "last_update_date": "2026-11-03",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the autofill table of each Web Data database in a Chromium-based browser profile: "
                 "one row per stored form field name and value, with its count and dates. An "
                 "autofill table missing either date_created or date_last_used is logged and not "
                 "read; none of the tested "
                 "databases lacked them. Browser, Profile and User come from the path: the browser from "
                 "the user data folder, the profile from the folder inside it, and the user from the home "
                 "folder that holds it; Source File names the file each row came from, since "
                 "Browser, Profile and User do not separate two copies of one profile, which a "
                 "logical extraction can hold under Users/ and System/Volumes/Data/Users/. A "
                 "profile under User Data/Snapshots/<version>/ is "
                 "reported with that path as its Profile, so a snapshot copy is not merged with the live "
                 "profile; no registered image carries one, and that branch was exercised on a constructed "
                 "tree only. Created and Last Used are date_created and date_last_used, seconds since "
                 "1970-01-01 UTC: Chromium writes them with base::Time::ToTimeT "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/autofill/core/browser/webdata/autocomplete/autocomplete_table.cc#L441-L442), "
                 "as the Chrome 65 release did "
                 "(https://github.com/chromium/chromium/blob/abb5172872b726072a64dfabaf45894c6ecf7369/components/autofill/core/browser/webdata/autofill_table.cc#L816-L817). "
                 "On the tested rows Last Used was never earlier than Created. Count is the stored count: "
                 "Chromium adds one to it and sets date_last_used each time it records the value for the "
                 "field again "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/autofill/core/browser/webdata/autocomplete/autocomplete_table.cc#L411-L413), "
                 "and an entry written through its insert path gets 1 or 2 depending on whether its two "
                 "dates differ "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/autofill/core/browser/webdata/autocomplete/autocomplete_table.cc#L443-L447). "
                 "It ran from 1 to 2 on pc_mus_001_win11 and from 1 to 66 on lonewolf_win10. Field Name "
                 "and Value are the autofill name and value columns as stored. Browser held one value, "
                 "Google Chrome, on every row of pc_mus_001_win11, whose Microsoft Edge Web Data held no "
                 "autofill rows. A database left with a rollback journal that SQLite treats as hot cannot "
                 "be opened read only, because replaying the journal writes to the database; such a "
                 "database is read as found, with the journal ignored, and the run log says so. No "
                 "database read by this artifact on the tested images had one. Browser, Profile and User "
                 "each held one value on every row of lonewolf_win10, which carries one Chrome profile in "
                 "one home folder, and User held one value on every row of pc_mus_001_win11, whose Chrome "
                 "and Edge profiles sit in one home folder. Tested: Chrome 108.0.5359.125 (21 rows from "
                 "profiles Default and Profile 2) and Microsoft Edge 108.0.1462.54 (0 rows) on "
                 "pc_mus_001_win11, and Chrome 65.0.3325.181 on lonewolf_win10. The address tables of Web Data "
                 "are read by Chromium Autofill Addresses; its credit card and IBAN tables are not read. No "
                 "member of af_case2_win10, szechuan_win10 or "
                 "dleapp_macos_bigsur matched any of the declared paths. The user data folders read are "
                 "those of Google Chrome, Chromium, Microsoft Edge, Brave, Vivaldi and Opera on Windows, "
                 "macOS and Linux, and a store directly inside an Opera user data folder is "
                 "reported with that folder as its Profile. Only the Windows Google Chrome and "
                 "Microsoft Edge folders and the Linux Chromium snap and Flatpak folders were exercised by a "
                 "registered image, the last two by ubuntu2604_arm64_chromium; a constructed tree exercised the "
                 "Brave macOS, Vivaldi "
                 "Linux and Opera Windows folders, the last with its profile kept directly in the user "
                 "data folder, and the remaining folders were exercised by neither. "
                 "When a logical extraction holds a profile under Users/ and under "
                 "System/Volumes/Data/Users/, a store whose second copy is byte-identical, "
                 "with any -journal or -wal beside it, is read once and counted in the run "
                 "log, and copies that differ are both read. The macOS Google Chrome "
                 "folder was also exercised, on the public MacBook Pro logical extraction "
                 "(macOS 15.4, corpus key mvs2026_macbookpro_macos15), where each store was "
                 "byte-identical under the two paths. "
                 "Not read: other Chrome "
                 "channels (Beta, Dev, Canary), extension storage partitions under a profile's Storage "
                 "folder, and WebView2 or Electron app profiles such as EBWebView folders, which share the "
                 "layout but sit in other applications' folders. Chromium source is cited at commit "
                 "33f34ef179f55596f6c2fc8a55878b7ccf6276e4 and, for the Chrome 65 release, at "
                 "abb5172872b726072a64dfabaf45894c6ecf7369, the 65.0.3325.181 tag."
                 " Chromium installed as a snap keeps its user data folder in snap/chromium/common/chromium in the "
                 "home folder, because Chromium keeps it in a chromium folder inside CHROME_CONFIG_HOME, else "
                 "XDG_CONFIG_HOME, else .config "
                 "(Reference: Chromium, 'chrome_paths_linux.cc', "
                 "https://github.com/chromium/chromium/blob/73934a44f61e6b3878d1943064c141a5a820f5f7/chrome/common/chrome_paths_linux.cc#L62-L101) "
                 "and the snap's snap.yaml sets CHROME_CONFIG_HOME to the snap's common folder (measured on "
                 "revision 3535); installed as a Flatpak from Flathub it keeps it in "
                 ".var/app/org.chromium.Chromium/config/chromium, because Flatpak sets XDG_CONFIG_HOME to the "
                 "config folder in the app's folder (Reference: flatpak 1.16.6, 'flatpak-context.c', "
                 "https://github.com/flatpak/flatpak/blob/e761a8885453c217a931281092a641ebbdd0a0c6/common/flatpak-context.c#L3168-L3175). "
                 "Both are read as Chromium, measured on ubuntu2604_arm64_chromium, whose snap (Chromium "
                 "153.0.8010.47) and Flatpak (Chromium 154.0.8037.57) each kept a Default profile there. Other "
                 "browsers' Flatpaks are not read. A profile in a .config folder that is not directly in a home "
                 "folder, such as a snap's snap/<name>/<revision>/.config, is matched by the .config paths and "
                 "read with User blank."
                 " The folder webbrowser/chrome, which an LG webOS TV keeps on the volume it mounts at"
                 " /mnt/lg/cmn_data, is read as the user data folder of a browser named webOS webbrowser (field"
                 " mapped from a private sample); which app writes it is not established, and User is blank for it,"
                 " since it sits in no home folder.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/Web Data*',
            '*/Library/Application Support/Google/Chrome/*/Web Data*',
            '*/.config/google-chrome/*/Web Data*',
            '*/AppData/Local/Chromium/User Data/*/Web Data*',
            '*/Library/Application Support/Chromium/*/Web Data*',
            '*/.config/chromium/*/Web Data*',
            '*/snap/chromium/common/chromium/*/Web Data*',
            '*/.var/app/org.chromium.Chromium/config/chromium/*/Web Data*',
            '*/webbrowser/chrome/*/Web Data*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Web Data*',
            '*/Library/Application Support/Microsoft Edge/*/Web Data*',
            '*/.config/microsoft-edge/*/Web Data*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Web Data*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Web Data*',
            '*/.config/BraveSoftware/Brave-Browser/*/Web Data*',
            '*/AppData/Local/Vivaldi/User Data/*/Web Data*',
            '*/Library/Application Support/Vivaldi/*/Web Data*',
            '*/.config/vivaldi/*/Web Data*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Web Data*',
            '*/Library/Application Support/com.operasoftware.Opera/*/Web Data*',
            '*/.config/opera/*/Web Data*',
            '*/AppData/Roaming/Opera Software/Opera Stable/Web Data*',
            '*/Library/Application Support/com.operasoftware.Opera/Web Data*',
            '*/.config/opera/Web Data*',
        ),
        "output_types": "standard",
        "artifact_icon": "edit",
        "sample_data": {
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 21 rows",
            "lonewolf_win10": "Windows 10 Education build 16299 | 401 rows",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64, Chromium 153.0.8010.47 (snap) and 154.0.8037.57 (Flatpak) | 0 rows (the matched files held nothing this artifact reports)",
        },
    },
    "chromiumAutofillAddresses": {
        "name": "Chromium Autofill Addresses",
        "description": "Addresses and contact details saved for autofill in the Web Data databases of "
                       "Google Chrome, Microsoft Edge, Brave, Vivaldi, Opera and Chromium profiles: name, "
                       "organization, street, city, state, postal code, country, email and phone, with "
                       "the last used and modified times and the use count.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-03",
        "last_update_date": "2026-11-04",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "Reads the saved autofill addresses of each Web Data database in a Chromium-based browser "
                 "profile, one row per address, from whichever of three table layouts the database holds. Up "
                 "to schema version 112 an address is a row of autofill_profiles, with its names, emails and "
                 "phones in autofill_profile_names, autofill_profile_emails and autofill_profile_phones under "
                 "the same guid. Version 113 moved addresses saved on the device to local_addresses and "
                 "version 114 dropped the autofill_profiles tables; account addresses sat in contact_info from "
                 "version 107 "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/autofill/core/browser/webdata/addresses/address_autofill_table.cc#L975, "
                 "https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/autofill/core/browser/webdata/addresses/address_autofill_table.cc#L1009-L1050). "
                 "In both, the values are rows of a type token table (local_addresses_type_tokens, "
                 "contact_info_type_tokens) holding a field type and a value. Version 134 merged the two into "
                 "addresses and address_type_tokens, with a record_type column "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/autofill/core/browser/webdata/addresses/address_autofill_table.cc#L1094-L1105). "
                 "A layout is read when its tables exist, whatever the version number says. Last Used and "
                 "Modified are use_date and date_modified, seconds since 1970-01-01 UTC: Chromium writes them "
                 "with base::Time::ToTimeT "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/autofill/core/browser/webdata/addresses/address_autofill_table.cc#L379-L396) "
                 "and read the autofill_profiles columns with FromTimeT "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/autofill/core/browser/webdata/addresses/address_autofill_table.cc#L166-L181). "
                 "A zero is shown blank. Use Count is use_count as stored. On "
                 "windows11_arm_chromium_autofill_known_20261103 Last Used and Modified were equal on every "
                 "row and fell 1 to 4 seconds before the time logged after each save, and Use Count held 1 on "
                 "all 7 rows. No saved address was filled into a form there, so a fill was not exercised. Full "
                 "Name, Organization, Street Address, City, State, Postal Code, Country, Email and Phone are "
                 "the values of field types NAME_FULL (7), COMPANY_NAME (60), ADDRESS_HOME_STREET_ADDRESS "
                 "(77), ADDRESS_HOME_CITY (33), ADDRESS_HOME_STATE (34), ADDRESS_HOME_ZIP (35), "
                 "ADDRESS_HOME_COUNTRY (36), EMAIL_ADDRESS (9) and PHONE_HOME_WHOLE_NUMBER (14), as numbered "
                 "in Chromium's field_types.h "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/autofill/core/browser/field_types.h#L141-L231). "
                 "field_types.h says the list is not modified except in step with the Autofill server "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/autofill/core/browser/field_types.h#L22-L26) "
                 "and lists retired numbers as deprecated "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/autofill/core/browser/field_types.h#L159-L161), "
                 "so one map reads every schema version. Country is the stored country code "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/autofill/core/browser/field_types.h#L171-L175). "
                 "autofill_profiles keeps the same values in named columns, mapped to the same field types as "
                 "Chromium reads them "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/autofill/core/browser/webdata/addresses/address_autofill_table.cc#L166-L181, "
                 "https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/autofill/core/browser/webdata/addresses/address_autofill_table.cc#L190-L206, "
                 "https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/autofill/core/browser/webdata/addresses/address_autofill_table.cc#L304-L307, "
                 "https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/autofill/core/browser/webdata/addresses/address_autofill_table.cc#L321-L324); "
                 "honorific_prefix and full_name_with_honorific_prefix are named NAME_HONORIFIC_PREFIX and "
                 "NAME_FULL_WITH_HONORIFIC_PREFIX from their column names, the second shown as "
                 "'NAME_FULL_WITH_HONORIFIC_PREFIX (deprecated)', since the current source no longer reads "
                 "them. Other Values lists every other non-empty stored value with its "
                 "field type name, or 'type <n>' for a number this artifact does not name, so every stored "
                 "value is reported; on the known data it held the name parts Chromium split from the full "
                 "name, field type 117 on the 2 Chromium 110 and 2 Chromium 120 rows, which field_types.h "
                 "marks deprecated "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/autofill/core/browser/field_types.h#L327), "
                 "and the street name, house number and street location on one Chromium 120 row. "
                 "Where an autofill_profiles side table holds more than one row for a guid, the values are "
                 "joined with '; ' in rowid order; that case was exercised on a constructed database only. A "
                 "value stored as a BLOB is reported by its length and not decoded; the Microsoft Edge 86 "
                 "snapshot database on ou_ransomware_server2022 (schema 88) declares these columns BLOB, and "
                 "no tested row held one. Record Type is record_type of the addresses table, named from "
                 "AutofillProfile::RecordType "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/autofill/core/browser/data_model/addresses/autofill_profile.h#L57-L100); "
                 "for local_addresses it is kLocalOrSyncable (0) and for contact_info one of the account "
                 "types, the tables Chromium keeps those record types in "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/autofill/core/browser/webdata/addresses/address_autofill_table.cc#L340-L352); "
                 "autofill_profiles has no record type, and Record Type is blank for its rows. Record Type "
                 "held kLocalOrSyncable (0) on every tested addresses and local_addresses row; no tested image "
                 "held an account address (kAccount needs a signed-in browser, "
                 "https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/autofill/core/browser/data_model/addresses/autofill_profile.h#L66-L70), "
                 "and the contact_info branch was exercised on a constructed database only. Label is label as "
                 "stored and held no value on any tested row. Table names the table the row came from. Tested: "
                 "windows11_arm_chromium_autofill_known_20261103, fictional addresses saved through each "
                 "browser's settings on Windows 11 build 26200 (ARM64), 7 rows: 2 from Chromium 110.0.5481.0 "
                 "(autofill_profiles, schema 108), 2 from Chromium 120.0.6099.0 (local_addresses, schema 120), "
                 "2 from Google Chrome 157.0.8103.39 (addresses, schema 160) and 1 from Microsoft Edge "
                 "156.0.4314.58 (addresses, schema 158); every saved field type was reported in its column; "
                 "the per-save logs in the zip record field types, and the README beside it describes the "
                 "values. Edge kept one of the two addresses saved in it; the one without a street address is "
                 "absent, and why is not established. On hexordia_mvs2025_win11 (Microsoft Edge, schema 135) 3 "
                 "rows held Country on all 3, Email on 2 and Phone on 1; Full Name, Organization, Street "
                 "Address, City, State, Postal Code and Other Values had no value on any of them, and Country "
                 "held one value on all 3. The Web Data databases of cfreds_leakage_win7, lonewolf_win10, "
                 "ou_ransomware_server2022, pc_mus_001_win11, ubuntu2604_arm64_chromium and "
                 "mvs2026_macbookpro_macos15 (schema versions 60 to 154) were read without error and held no "
                 "address. Not read: server_addresses and server_address_metadata, server address tables that "
                 "version 121 dropped "
                 "(https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/autofill/core/browser/webdata/addresses/address_autofill_table.cc#L1072-L1077), "
                 "which held no rows on any tested image; autofill_profile_addresses, which holds structured "
                 "street parts of autofill_profiles addresses; autofill_profile_birthdates; the "
                 "verification_status and observations columns of the type token tables; language_code, which "
                 "held no value on any tested row; initial_creator_id, which held a value on every tested "
                 "addresses and local_addresses row; the use_date2 and use_date3 columns that version 132 "
                 "added and version 145 dropped, which held no value on any tested row; Microsoft Edge's own "
                 "tables (autofill_profile_edge_extended and the other autofill_edge_ tables), for which no "
                 "published schema was found, autofill_edge_field_values being read by Microsoft Edge Form "
                 "Field Values; the autofill_ai_, plus_addresses and loyalty_cards tables, empty "
                 "in every tested database that has them; and the payment card, IBAN and bank account tables. "
                 "The user data folders read are the same as for Chromium Autofill Entries, and WebView2 or "
                 "Electron app profiles are not read.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/Web Data*',
            '*/Library/Application Support/Google/Chrome/*/Web Data*',
            '*/.config/google-chrome/*/Web Data*',
            '*/AppData/Local/Chromium/User Data/*/Web Data*',
            '*/Library/Application Support/Chromium/*/Web Data*',
            '*/.config/chromium/*/Web Data*',
            '*/snap/chromium/common/chromium/*/Web Data*',
            '*/.var/app/org.chromium.Chromium/config/chromium/*/Web Data*',
            '*/webbrowser/chrome/*/Web Data*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Web Data*',
            '*/Library/Application Support/Microsoft Edge/*/Web Data*',
            '*/.config/microsoft-edge/*/Web Data*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Web Data*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Web Data*',
            '*/.config/BraveSoftware/Brave-Browser/*/Web Data*',
            '*/AppData/Local/Vivaldi/User Data/*/Web Data*',
            '*/Library/Application Support/Vivaldi/*/Web Data*',
            '*/.config/vivaldi/*/Web Data*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Web Data*',
            '*/Library/Application Support/com.operasoftware.Opera/*/Web Data*',
            '*/.config/opera/*/Web Data*',
            '*/AppData/Roaming/Opera Software/Opera Stable/Web Data*',
            '*/Library/Application Support/com.operasoftware.Opera/Web Data*',
            '*/.config/opera/Web Data*',
        ),
        "output_types": "standard",
        "artifact_icon": "map-pin",
        "sample_data": {
            "windows11_arm_chromium_autofill_known_20261103": "Windows 11 build 26200 (ARM64), Chrome 157.0.8103.39, Edge 156.0.4314.58, Chromium 110.0.5481.0 and 120.0.6099.0 | 7 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 3 rows",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (the matched files held nothing this artifact reports)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (the matched files held nothing this artifact reports)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (the matched files held nothing this artifact reports)",
            "ou_ransomware_server2022": "Windows Server 2022 build 20348 | 0 rows (the matched files held nothing this artifact reports)",
            "af_case2_win10": "Windows 10 1809 build 17763 | 0 rows (no member matches the declared paths)",
            "szechuan_win10": "Windows 10 2004 build 19041 | 0 rows (no member matches the declared paths)",
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows (the matched files held nothing this artifact reports)",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64, Chromium 153.0.8010.47 (snap) and 154.0.8037.57 (Flatpak) | 0 rows (the matched files held nothing this artifact reports)",
        },
    },
    "chromiumSavedPaymentCards": {
        "name": "Chromium Saved Payment Cards",
        "description": "Payment cards saved on the device for autofill in the Web Data databases of "
                       "Google Chrome, Microsoft Edge, Brave, Vivaldi, Opera, Chromium and webOS webbrowser profiles: name on "
                       "card, expiry, nickname, use count and the last used and modified times. The card "
                       "number is not read.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-04",
        "last_update_date": "2026-11-04",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "One row per card in the credit_cards table of each Web Data database in a Chromium-based "
                 "browser profile: the cards saved on the device. The column names and the statement that "
                 "saves a card are in Chromium's payments table code (https://github.com/chromium/chromium/blob/51bc117ffe992d07bbc5a28892b8e8e0e9f832fe/components/autofill/core/browser/webdata/payments/payments_autofill_table.cc#L64-L75, #L779-L782). Name "
                 "on Card, Expiry Month, Expiry Year and Nickname are the name_on_card, expiration_month, "
                 "expiration_year and nickname columns as stored, text decoded as UTF-8. Last Used and Modified are use_date and "
                 "date_modified, which Chromium writes as seconds since 1 January 1970 UTC (ToTimeT, #L256-L257); "
                 "a 0 is shown blank, as is a database with no use_date or use_count column (schema 60, on "
                 "cfreds_leakage_win7, has neither). Use Count is use_count as stored. A card starts with a use count of 1 "
                 "(https://github.com/chromium/chromium/blob/8a6c17bdde4f7c73bbe1cdf5147a06d7e9948e4c/components/autofill/core/browser/data_model/usage_history_information.h#L74), so 1 does not show the card was used: on the known data (corpus key "
                 "windows11_arm_chromium_cards_known_20261104, a test card typed into the settings page of "
                 "Chrome 157 and of Edge 156 in new profiles) each card read 1 right after it was saved, with "
                 "Last Used and Modified equal to the second of the save. User Confirmed is Yes when "
                 "is_user_confirmed is 1, which Chromium documents as the user having saved the card in "
                 "settings (https://github.com/chromium/chromium/blob/36258236c6b8a818509adfc1df25387063b4b820/components/autofill/core/browser/data_model/payments/credit_card.h#L138-L141), and No when it is 0; both test cards, saved in settings, "
                 "read 1, and a card saved another way, which would read 0, was not tested. A database from "
                 "before is_user_confirmed existed stores an origin column instead; for it User Confirmed is "
                 "Yes when origin is 'Chrome settings' and No otherwise, as Chromium's migration sets the "
                 "column (#L2215-L2240); no tested row came from such a database, because the Web Data files "
                 "with an origin column (seven keys, schema 60 to 145) held no card. The card number is stored "
                 "encrypted (card_number_encrypted) and is not read, decrypted or reported, nor are its last "
                 "digits. The billing address id, a reference to a saved address, is not shown; it was empty "
                 "on both test cards. Cards stored by the payments server (masked_credit_cards and related "
                 "tables), saved security codes (local_stored_cvc) and saved IBANs are not read; on the known "
                 "data each held 0 rows. Edge also has a table of its own, credit_cards_edge_extended, which held "
                 "one row for the one card and is not read because no source for its columns was found. Edge's "
                 "row stored no nickname, although one was typed into Edge's form; it was found in no table of "
                 "Web Data and in no file of the profile folder, so Edge 156 did not keep it. Browser, Profile and User are as in Chromium Autofill Addresses. A saved card "
                 "records that a card was saved in that profile, not who saved or used it.",
        "paths": (
            '*/AppData/Local/Google/Chrome/User Data/*/Web Data*',
            '*/Library/Application Support/Google/Chrome/*/Web Data*',
            '*/.config/google-chrome/*/Web Data*',
            '*/AppData/Local/Chromium/User Data/*/Web Data*',
            '*/Library/Application Support/Chromium/*/Web Data*',
            '*/.config/chromium/*/Web Data*',
            '*/snap/chromium/common/chromium/*/Web Data*',
            '*/.var/app/org.chromium.Chromium/config/chromium/*/Web Data*',
            '*/webbrowser/chrome/*/Web Data*',
            '*/AppData/Local/Microsoft/Edge/User Data/*/Web Data*',
            '*/Library/Application Support/Microsoft Edge/*/Web Data*',
            '*/.config/microsoft-edge/*/Web Data*',
            '*/AppData/Local/BraveSoftware/Brave-Browser/User Data/*/Web Data*',
            '*/Library/Application Support/BraveSoftware/Brave-Browser/*/Web Data*',
            '*/.config/BraveSoftware/Brave-Browser/*/Web Data*',
            '*/AppData/Local/Vivaldi/User Data/*/Web Data*',
            '*/Library/Application Support/Vivaldi/*/Web Data*',
            '*/.config/vivaldi/*/Web Data*',
            '*/AppData/Roaming/Opera Software/Opera Stable/*/Web Data*',
            '*/Library/Application Support/com.operasoftware.Opera/*/Web Data*',
            '*/.config/opera/*/Web Data*',
            '*/AppData/Roaming/Opera Software/Opera Stable/Web Data*',
            '*/Library/Application Support/com.operasoftware.Opera/Web Data*',
            '*/.config/opera/Web Data*',
        ),
        "output_types": "standard",
        "artifact_icon": "credit-card",
        "sample_data": {
            "windows11_arm_chromium_cards_known_20261104": "Windows 11 build 26200 (ARM64), Chrome 157, Edge 156.0.4314.58 | 2 rows",
            "windows11_arm_chromium_autofill_known_20261103": "Windows 11 build 26200 (ARM64), Chrome 157.0.8103.39, Edge 156.0.4314.58, Chromium 110.0.5481.0 and 120.0.6099.0 | 0 rows (credit_cards present and empty)",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 0 rows (credit_cards present and empty)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621 | 0 rows (credit_cards present and empty)",
            "lonewolf_win10": "Windows 10 Education build 16299 | 0 rows (credit_cards present and empty)",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1 build 7601 | 0 rows (credit_cards present and empty)",
            "ou_ransomware_server2022": "Windows Server 2022 build 20348 | 0 rows (credit_cards present and empty)",
            "mvs2026_macbookpro_macos15": "macOS 15.4 | 0 rows (credit_cards present and empty)",
            "ubuntu2604_arm64_chromium": "Ubuntu 26.04 LTS aarch64, Chromium 153.0.8010.47 (snap) and 154.0.8037.57 (Flatpak) | 0 rows (credit_cards present and empty)",
        },
    },
    "edgeFormFieldValues": {
        "name": "Microsoft Edge Form Field Values",
        "description": "Values entered into web form fields and kept by Microsoft Edge in its own "
                       "autofill_edge_field_values table of Web Data, with the site's host name, the field's "
                       "label, the count and the first and last times.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-04",
        "last_update_date": "2026-11-04",
        "requirements": "none",
        "category": "Chromium Browsers",
        "notes": "One row per row of autofill_edge_field_values, a table Microsoft Edge adds to Web Data "
                 "beside Chromium's autofill table. Edge is closed source and no published schema was found, "
                 "so every column below is described from known data: corpus key "
                 "windows11_arm_edge_field_values_known_20261104, made-up values typed into local test forms "
                 "in a new Edge 156.0.4314.58 profile on Windows 11, with no account signed in, over seven "
                 "steps (a repeat, a second host, an empty field, a fetch submit, an iframe removal, slow "
                 "typing); the README beside the zip lists them. Site and Field Label come from the "
                 "autofill_edge_field_client_info row whose field_id matches: field_id is that row's "
                 "domain_signature, form_signature_v2 and field_signature_v2 joined by $, on all 6 rows of the "
                 "known data and all 37 of hexordia_mvs2025_win11, where every field_values row had a "
                 "client_info row. Site is domain_value, the page's full host name without the port: the same "
                 "form served from a host and from its parent domain was stored under two different Site "
                 "values, one per host. Field Label is label, the "
                 "text of the field's label element; the field's name, id, placeholder and aria-label were each "
                 "different and none was stored; it was empty on 1 row of hexordia_mvs2025_win11. Value is the "
                 "value as stored; a BLOB value would be reported by its length, and every tested value was "
                 "text. On the known data Edge stored a field left empty as edge_default_dummy_empty_value, "
                 "and this artifact shows that value blank: 12 of the 38 "
                 "rows on hexordia_mvs2025_win11 held it. Created and Last Used are date_created and "
                 "date_last_used, seconds since 1970-01-01 UTC. On the known data both were the second in "
                 "which typing into the form began, the same second for every field of the form, and not the "
                 "submit time: with 20 seconds between page load, each field and the submit click, both "
                 "fields carried the second the first field was clicked and typed. Chromium's autofill table "
                 "(Chromium Autofill Entries) kept the same values in rows of its own, dated at the submit, 1 "
                 "to 42 seconds later on the known data, and with no row for an empty field, so the two "
                 "tables do not hold the same rows: 11 here against 7 there after the last step. Count is "
                 "count as stored: it went from 1 to 2 when the same value was submitted again in the same "
                 "field of the same form on the same host, and that repeat moved Last Used and not Created. "
                 "Submission Source is submission_source as stored: 6 after a click on the form's submit "
                 "button, 2 after a fetch POST that then removed the form, and 3 after the iframe holding the "
                 "form was removed; a repeat overwrites it with the latest submission's value. 6 is not "
                 "Chromium's value for a normal form submission, 5 in "
                 "https://github.com/chromium/chromium/blob/33f34ef179f55596f6c2fc8a55878b7ccf6276e4/components/autofill/core/common/mojom/autofill_types.mojom#L153-L176, "
                 "so Chromium's names are not used. hexordia_mvs2025_win11 also held 101, which the known data "
                 "did not produce, and its meaning is not established. Not shown: is_masked, which held 1 on 4 "
                 "rows of hexordia_mvs2025_win11 and 0 on every known-data row, so what sets it is not "
                 "established; the client_info signatures and its date_created, which on the known data was "
                 "the first time its field got a value and did not move for a later value; and "
                 "autofill_edge_fieldid_cid_mapping, autofill_edge_extended and the other autofill_edge_, "
                 "credit_cards_edge_ and edge_ tables, which held no rows on the known data except edge_meta's "
                 "one version row; the known data had no account signed in. The table was absent from the tested databases "
                 "of schema 88 (an Edge 86 snapshot on ou_ransomware_server2022) and 104 (Edge 108 on "
                 "pc_mus_001_win11), and present in those of schema 117, 120, 135 and 158; the 117 and 120 "
                 "ones lack is_masked. Profile, User and Source File are as in Chromium Autofill Entries; "
                 "Browser is left out because the paths read are Edge's, so it would hold one value. Profile held one value, Default, "
                 "and User held one value on every row of hexordia_mvs2025_win11 and of the known data, each "
                 "of which has one Edge profile with rows. Only the Windows Edge folder was exercised; the "
                 "macOS and Linux Edge folders were not. A row records that a value was entered into a form "
                 "field of that site and the form was submitted or removed, in that profile; it does not "
                 "record who entered it.",
        "paths": (
            '*/AppData/Local/Microsoft/Edge/User Data/*/Web Data*',
            '*/Library/Application Support/Microsoft Edge/*/Web Data*',
            '*/.config/microsoft-edge/*/Web Data*',
        ),
        "output_types": "standard",
        "artifact_icon": "edit",
        "sample_data": {
            "windows11_arm_edge_field_values_known_20261104": "Windows 11 build 26200 (ARM64), Edge 156.0.4314.58 | 11 rows",
            "hexordia_mvs2025_win11": "Windows 11 24H2 build 26100 | 38 rows",
            "windows11_arm_chromium_cards_known_20261104": "Windows 11 build 26200 (ARM64), Edge 156.0.4314.58 | 0 rows (autofill_edge_field_values present and empty)",
            "windows11_arm_chromium_autofill_known_20261103": "Windows 11 build 26200 (ARM64), Edge 156.0.4314.58 | 0 rows (autofill_edge_field_values present and empty)",
            "ou_ransomware_server2022": "Windows Server 2022 build 20348 | 0 rows (autofill_edge_field_values present and empty in two profiles; absent from an Edge 86 snapshot)",
            "pc_mus_001_win11": "Windows 11 22H2 build 22621, Edge 108.0.1462.54 | 0 rows (no autofill_edge_field_values table)",
        },
    },
}

import sqlite3

from scripts.chromium.browser_profiles import (enum_label, open_store, profile_stores,
                                               row_tail, select_list, table_columns,
                                               unix_time)
from scripts.ilapfuncs import artifact_processor, logfunc


@artifact_processor
def chromiumAutofill(context):
    data_list = []
    sources = []
    for store in profile_stores(context, {'Web Data'}, 'Chromium Autofill Entries'):
        db = open_store(store, 'Chromium Autofill Entries')
        if db is None:
            continue
        try:
            present = table_columns(db, 'autofill')
            if not {'date_created', 'date_last_used'} <= present:
                if present:
                    logfunc(f'Chromium Autofill Entries: {store.relative} has an autofill '
                            f'table without date_created and date_last_used; not read')
                continue
            rows = db.execute('''
                SELECT date_created, date_last_used, name, value, count
                FROM autofill ORDER BY date_created, name, value''').fetchall()
        except sqlite3.Error as ex:
            logfunc(f'Chromium Autofill Entries: could not read {store.relative}: {ex}')
            continue
        finally:
            db.close()
        sources.append(store.path)
        for created, last_used, field, value, count in rows:
            data_list.append((unix_time(created), unix_time(last_used), field, value, count)
                             + row_tail(store))
    data_headers = (('Created', 'datetime'), ('Last Used', 'datetime'), 'Field Name', 'Value',
                    'Count', 'Browser', 'Profile', 'User', 'Source File')
    return data_headers, data_list, '\n'.join(sources)


# FieldType values as Chromium stores them in the type column of addresses,
# local_addresses_type_tokens and contact_info_type_tokens: components/autofill/core/
# browser/field_types.h, chromium 33f34ef179f55596f6c2fc8a55878b7ccf6276e4. Retired
# values are marked deprecated there and not given to another field (lines 159-161,
# 177-178, 192-194), so one map reads every schema version; 117 is one, which older
# releases still wrote (line 327). Only the values an address can hold are named; any
# other value is reported as "type <n>".
_FIELD_TYPES = {
    3: 'NAME_FIRST', 4: 'NAME_MIDDLE', 5: 'NAME_LAST', 6: 'NAME_MIDDLE_INITIAL',
    7: 'NAME_FULL', 8: 'NAME_SUFFIX', 9: 'EMAIL_ADDRESS', 10: 'PHONE_HOME_NUMBER',
    11: 'PHONE_HOME_CITY_CODE', 12: 'PHONE_HOME_COUNTRY_CODE',
    13: 'PHONE_HOME_CITY_AND_NUMBER', 14: 'PHONE_HOME_WHOLE_NUMBER',
    30: 'ADDRESS_HOME_LINE1', 31: 'ADDRESS_HOME_LINE2', 32: 'ADDRESS_HOME_APT_NUM',
    33: 'ADDRESS_HOME_CITY', 34: 'ADDRESS_HOME_STATE', 35: 'ADDRESS_HOME_ZIP',
    36: 'ADDRESS_HOME_COUNTRY', 60: 'COMPANY_NAME', 77: 'ADDRESS_HOME_STREET_ADDRESS',
    79: 'ADDRESS_HOME_SORTING_CODE', 81: 'ADDRESS_HOME_DEPENDENT_LOCALITY',
    83: 'ADDRESS_HOME_LINE3', 103: 'ADDRESS_HOME_STREET_NAME',
    104: 'ADDRESS_HOME_HOUSE_NUMBER', 105: 'ADDRESS_HOME_SUBPREMISE',
    106: 'ADDRESS_HOME_OTHER_SUBUNIT', 107: 'NAME_LAST_FIRST', 108: 'NAME_LAST_CONJUNCTION',
    109: 'NAME_LAST_SECOND', 110: 'NAME_HONORIFIC_PREFIX', 114: 'ADDRESS_HOME_ADDRESS',
    115: 'ADDRESS_HOME_ADDRESS_WITH_NAME', 116: 'ADDRESS_HOME_FLOOR',
    117: 'NAME_FULL_WITH_HONORIFIC_PREFIX (deprecated)',
    121: 'PHONE_HOME_CITY_CODE_WITH_TRUNK_PREFIX',
    122: 'PHONE_HOME_CITY_AND_NUMBER_WITHOUT_TRUNK_PREFIX', 123: 'PHONE_HOME_NUMBER_PREFIX',
    124: 'PHONE_HOME_NUMBER_SUFFIX', 133: 'DELIVERY_INSTRUCTIONS', 135: 'ADDRESS_HOME_OVERFLOW',
    136: 'ADDRESS_HOME_LANDMARK', 140: 'ADDRESS_HOME_OVERFLOW_AND_LANDMARK',
    141: 'ADDRESS_HOME_ADMIN_LEVEL2', 142: 'ADDRESS_HOME_STREET_LOCATION',
    143: 'ADDRESS_HOME_BETWEEN_STREETS', 144: 'ADDRESS_HOME_BETWEEN_STREETS_OR_LANDMARK',
    145: 'ADDRESS_HOME_STREET_LOCATION_AND_LOCALITY',
    146: 'ADDRESS_HOME_STREET_LOCATION_AND_LANDMARK',
    150: 'ADDRESS_HOME_DEPENDENT_LOCALITY_AND_LANDMARK', 151: 'ADDRESS_HOME_BETWEEN_STREETS_1',
    152: 'ADDRESS_HOME_BETWEEN_STREETS_2', 153: 'ADDRESS_HOME_HOUSE_NUMBER_AND_APT',
    156: 'ADDRESS_HOME_APT', 157: 'ADDRESS_HOME_APT_TYPE', 163: 'ALTERNATIVE_FULL_NAME',
    164: 'ALTERNATIVE_GIVEN_NAME', 165: 'ALTERNATIVE_FAMILY_NAME', 201: 'ADDRESS_HOME_ZIP_PREFIX',
    202: 'ADDRESS_HOME_ZIP_SUFFIX', 207: 'ADDRESS_HOME_ZIP_AND_CITY',
}

# The field types given a column of their own, in column order.
_SHOWN_TYPES = (7, 60, 77, 33, 34, 35, 36, 9, 14)

# AutofillProfile::RecordType, components/autofill/core/browser/data_model/addresses/
# autofill_profile.h lines 57-100, chromium 33f34ef179f55596f6c2fc8a55878b7ccf6276e4.
_RECORD_TYPES = {0: 'kLocalOrSyncable', 1: 'kAccount', 2: 'kAccountHome', 3: 'kAccountWork',
                 4: 'kAccountNameEmail'}

# The tables of each address layout: metadata table, type token table, and the record
# type its rows have. local_addresses holds kLocalOrSyncable profiles and contact_info
# the account ones (GetLegacyProfileMetadataTable, address_autofill_table.cc lines
# 340-352, same commit); addresses carries the record type in a column of its own.
_TOKEN_LAYOUTS = (
    ('addresses', 'address_type_tokens', None),
    ('local_addresses', 'local_addresses_type_tokens', 'kLocalOrSyncable (0)'),
    ('contact_info', 'contact_info_type_tokens', 'kAccount or kAccountHome or kAccountWork'),
)

# The legacy autofill_profiles layout: profile column and the field type it holds
# (AddLegacyAutofillProfileDetailsFromStatement, address_autofill_table.cc lines
# 166-181), and the side tables read by guid with their columns and field types.
_LEGACY_PROFILE_COLUMNS = (
    ('company_name', 60), ('street_address', 77), ('dependent_locality', 81), ('city', 33),
    ('state', 34), ('zipcode', 35), ('sorting_code', 79), ('country_code', 36),
)
_LEGACY_SIDE_TABLES = (
    ('autofill_profile_names', (('full_name', 7), ('first_name', 3), ('middle_name', 4),
                                ('last_name', 5), ('honorific_prefix', 110),
                                ('first_last_name', 107), ('conjunction_last_name', 108),
                                ('second_last_name', 109),
                                ('full_name_with_honorific_prefix', 117))),
    ('autofill_profile_emails', (('email', 9),)),
    ('autofill_profile_phones', (('number', 14),)),
)


def _value(value):
    """A stored value as text. A BLOB is reported by its length, not decoded."""
    if value is None:
        return ''
    if isinstance(value, bytes):
        return f'[{len(value)} bytes, not decoded]' if value else ''
    return str(value)


def _field_name(field_type):
    return _FIELD_TYPES.get(field_type, f'type {field_type}')


def _address_row(store, use_date, modified, use_count, record_type, label, fields, table):
    """One report row from a profile's field values, {field type: [values]}.

    Values of a field type given no column of its own go to Other Values, so every
    stored value is reported somewhere.
    """
    shown = tuple('; '.join(fields.get(field_type, [])) for field_type in _SHOWN_TYPES)
    other = '; '.join(f'{_field_name(field_type)}: {value}'
                      for field_type in sorted(fields) if field_type not in _SHOWN_TYPES
                      for value in fields[field_type])
    return ((unix_time(use_date), unix_time(modified), use_count) + shown
            + (other, record_type, _value(label), table) + row_tail(store))


def _token_addresses(db, store, meta_table, token_table, record_type):
    present = table_columns(db, meta_table)
    if not present or not table_columns(db, token_table):
        return []
    tokens = {}
    for guid, field_type, value in db.execute(
            f'SELECT guid, type, value FROM "{token_table}" ORDER BY guid, type'):
        text = _value(value)
        if text:
            tokens.setdefault(guid, {}).setdefault(field_type, []).append(text)
    columns = select_list(present, ('guid', 'use_date', 'date_modified', 'use_count',
                                    'record_type', 'label'))
    rows = []
    for guid, use_date, modified, use_count, stored_type, label in db.execute(
            f'SELECT {columns} FROM "{meta_table}" ORDER BY use_date, guid'):
        kind = record_type if record_type is not None else enum_label(_RECORD_TYPES, stored_type)
        rows.append(_address_row(store, use_date, modified, use_count, kind, label,
                                 tokens.get(guid, {}), meta_table))
    return rows


def _legacy_addresses(db, store):
    present = table_columns(db, 'autofill_profiles')
    if not present:
        return []
    side = {}
    for table, columns in _LEGACY_SIDE_TABLES:
        side_present = table_columns(db, table)
        if not side_present:
            continue
        wanted = [(column, field_type) for column, field_type in columns
                  if column in side_present]
        if not wanted:
            continue
        query = (f'SELECT guid, {", ".join(column for column, _ in wanted)} '
                 f'FROM "{table}" ORDER BY rowid')
        for record in db.execute(query):
            fields = side.setdefault(record[0], {})
            for (_column, field_type), value in zip(wanted, record[1:]):
                text = _value(value)
                if text:
                    fields.setdefault(field_type, []).append(text)
    profile_columns = [column for column, _ in _LEGACY_PROFILE_COLUMNS]
    columns = select_list(present, ['guid', 'use_date', 'date_modified', 'use_count', 'label']
                          + profile_columns)
    rows = []
    for record in db.execute(f'SELECT {columns} FROM autofill_profiles ORDER BY use_date, guid'):
        guid, use_date, modified, use_count, label = record[:5]
        fields = {field_type: list(values) for field_type, values in side.get(guid, {}).items()}
        for (_column, field_type), value in zip(_LEGACY_PROFILE_COLUMNS, record[5:]):
            text = _value(value)
            if text:
                fields.setdefault(field_type, []).append(text)
        rows.append(_address_row(store, use_date, modified, use_count, '', label, fields,
                                 'autofill_profiles'))
    return rows


@artifact_processor
def chromiumAutofillAddresses(context):
    data_list = []
    sources = []
    for store in profile_stores(context, {'Web Data'}, 'Chromium Autofill Addresses'):
        db = open_store(store, 'Chromium Autofill Addresses')
        if db is None:
            continue
        try:
            rows = _legacy_addresses(db, store)
            for meta_table, token_table, record_type in _TOKEN_LAYOUTS:
                rows.extend(_token_addresses(db, store, meta_table, token_table, record_type))
        except sqlite3.Error as ex:
            logfunc(f'Chromium Autofill Addresses: could not read {store.relative}: {ex}')
            continue
        finally:
            db.close()
        sources.append(store.path)
        data_list.extend(rows)
    data_headers = (('Last Used', 'datetime'), ('Modified', 'datetime'), 'Use Count', 'Full Name',
                    'Organization', 'Street Address', 'City', 'State', 'Postal Code', 'Country',
                    'Email', ('Phone', 'phonenumber'), 'Other Values', 'Record Type', 'Label',
                    'Table', 'Browser', 'Profile', 'User', 'Source File')
    return data_headers, data_list, '\n'.join(sources)


def _user_confirmed(confirmed, origin, present):
    """Yes or No from is_user_confirmed, or, on an older database, from origin as Chromium's migration reads it."""
    if 'is_user_confirmed' in present:
        return {1: 'Yes', 0: 'No'}.get(confirmed, _value(confirmed))
    if 'origin' in present:
        return 'Yes' if origin == 'Chrome settings' else 'No'
    return ''


@artifact_processor
def chromiumSavedPaymentCards(context):
    data_list = []
    sources = []
    label = 'Chromium Saved Payment Cards'
    for store in profile_stores(context, {'Web Data'}, label):
        db = open_store(store, label)
        if db is None:
            continue
        try:
            present = table_columns(db, 'credit_cards')
            rows = []
            if present:
                wanted = ('use_date', 'date_modified', 'name_on_card', 'expiration_month', 'expiration_year',
                          'nickname', 'use_count', 'is_user_confirmed', 'origin')
                columns = select_list(present, wanted)
                rows = db.execute(f'SELECT {columns} FROM credit_cards ORDER BY use_date, guid').fetchall()
        except sqlite3.Error as ex:
            logfunc(f'{label}: could not read {store.relative}: {ex}')
            continue
        finally:
            db.close()
        if rows:
            sources.append(store.path)
        for (use_date, modified, name, month, year, nickname, use_count, confirmed, origin) in rows:
            data_list.append((unix_time(use_date), unix_time(modified), _value(name), _value(month),
                              _value(year), _value(nickname), _value(use_count),
                              _user_confirmed(confirmed, origin, present)) + row_tail(store))
    data_headers = (('Last Used', 'datetime'), ('Modified', 'datetime'), 'Name on Card', 'Expiry Month',
                    'Expiry Year', 'Nickname', 'Use Count', 'User Confirmed', 'Browser', 'Profile', 'User',
                    'Source File')
    return data_headers, data_list, '\n'.join(sources)


# Edge's stored value for a form field submitted empty, measured on
# windows11_arm_edge_field_values_known_20261104 (README beside the zip).
_EDGE_EMPTY_VALUE = 'edge_default_dummy_empty_value'


@artifact_processor
def edgeFormFieldValues(context):
    data_list = []
    sources = []
    label = 'Microsoft Edge Form Field Values'
    for store in profile_stores(context, {'Web Data'}, label):
        db = open_store(store, label)
        if db is None:
            continue
        try:
            present = table_columns(db, 'autofill_edge_field_values')
            rows = []
            if present:
                values = select_list(present, ('date_created', 'date_last_used', 'value', 'count',
                                               'submission_source', 'field_id'), 'v.')
                info = table_columns(db, 'autofill_edge_field_client_info')
                if {'field_id', 'domain_value', 'label'} <= info:
                    query = (f'SELECT {values}, c.domain_value, c.label FROM autofill_edge_field_values v '
                             'LEFT JOIN autofill_edge_field_client_info c ON c.field_id = v.field_id')
                else:
                    query = f'SELECT {values}, NULL, NULL FROM autofill_edge_field_values v'
                rows = db.execute(query + ' ORDER BY v.date_created, v.field_id, v.value').fetchall()
        except sqlite3.Error as ex:
            logfunc(f'{label}: could not read {store.relative}: {ex}')
            continue
        finally:
            db.close()
        if present:
            sources.append(store.path)
        for created, last_used, value, count, source, _field_id, site, field_label in rows:
            shown = '' if value == _EDGE_EMPTY_VALUE else _value(value)
            data_list.append((unix_time(created), unix_time(last_used), _value(site), _value(field_label),
                              shown, _value(count), _value(source)) + row_tail(store)[1:])
    data_headers = (('Created', 'datetime'), ('Last Used', 'datetime'), 'Site', 'Field Label', 'Value',
                    'Count', 'Submission Source', 'Profile', 'User', 'Source File')
    return data_headers, data_list, '\n'.join(sources)
