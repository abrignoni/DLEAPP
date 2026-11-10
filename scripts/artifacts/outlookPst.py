"""Items in Outlook PST and OST files: mail, contacts, appointments, tasks, notes, journal
entries and their attachments, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "outlookPstEmails": {
        "name": "Outlook Emails",
        "description": "Mail and other message items in Outlook PST and OST files, with their "
                       "delivery and submit times, sender, recipients, subject, body and attachments.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-10",
        "last_update_date": "2026-11-10",
        "requirements": "none",
        "category": "Outlook",
        "notes": (
            "Reads every file named .pst or .ost, in any case, read-only, with the vendored pstprobe "
            "0.1.0 (scripts/vendor/pstprobe.py), written from Microsoft [MS-PST]; the 4 KB-page layout "
            "of newer OST files is not in [MS-PST] and follows Joachim Metz's PFF format notes. Items "
            "are those listed in the contents table of a folder, walking the folder tree from the root "
            "folder, so Deleted Items and, in an OST, folders such as Sync Issues are read too, and "
            "Folder names the folder. Search folder results, which are items of other folders, and "
            "folder-associated items get no rows. Items that were removed from Deleted Items are not "
            "recovered: the mail deleted that way in windows11_arm_outlook_pst_known_20261109 "
            "(kd_mail_8 in its fill log) is not reported. Items are routed to the Outlook artifacts by "
            "the prefix of PidTagMessageClass, matched without regard to case ([MS-OXCMSG] 2.2.1.3): "
            "IPM.Contact and IPM.DistList to Contacts, IPM.Appointment to Appointments, IPM.Task to "
            "Tasks, IPM.StickyNote to Notes, IPM.Activity to Journals, "
            "IPM.Microsoft.ScheduleData.FreeBusy, IPM.AbchPerson and IPM.Network to none, and every "
            "other class to Emails; an item with no message class is reported under Emails. Message "
            "Class is PidTagMessageClass as the folder's contents table holds it, else as the item "
            "holds it, and Item ID is the item's node ID in the file. Property IDs and names are those "
            "of [MS-OXPROPS]; meanings and enumerated values are from the Exchange protocol documents "
            "named below, release v20250520 ([MS-OXOCAL] v20250819). Datetime columns are the stored "
            "PtypTime values, which those documents give in UTC unless a column's notes say otherwise. "
            "A byte-identical second copy of a file is read once, the Users/ copy before one under "
            "System/Volumes/Data/, and an identical file in another user's folder is reported from the "
            "first path in sort order; a file that is not a PST or OST is logged and skipped; a file "
            "shorter than its header records is logged, since what is past the cut is missing, not "
            "empty; and values, items and attachments that cannot be read are counted in the run log. "
            "One row per item. Delivery Time is PidTagMessageDeliveryTime, which [MS-OXOMSG] 2.2.3.9 "
            "says the server sets when it receives a message, and Submit Time is "
            "PidTagClientSubmitTime, set when the message is submitted (2.2.3.11). On the corpus inputs "
            "in sample_data and two files of enron_edrm_v2_pst_hf_20261109 (zl_south-s_000.pst, "
            "zl_pereira-s_000.pst), 2,528 rows, Delivery Time was set on every row, unsent items "
            "included: on the nine drafts of windows11_arm_outlook_pst_known_20261109, which hold no "
            "sent or received mail, it fell within 70 ms before the save time in the kit's fill log. "
            "Four rows of zl_pereira-s_000.pst hold 1980-01-01 00:00:00 in both Delivery Time and "
            "Submit Time; what wrote that value was not established. Submit Time was blank on all 1,219 "
            "unsent items and on 24 items in the Aspose-written PSTs of pst_public_fixtures_20261109. "
            "Modified is PidTagLastModificationTime. From is PidTagSenderName. From Address is "
            "PidTagSenderSmtpAddress when stored, else PidTagSenderEmailAddress, which on 11 of the "
            "2,528 rows, in six files, is an Exchange address (/o=...), and on 736 rows of the three "
            "Enron-derived files text of 5 to 22 characters that is neither an SMTP nor an Exchange "
            "address. Sent On Behalf Of is PidTagSentRepresentingName when it differs from "
            "PidTagSenderName. To, Cc and Bcc list the recipient table rows whose PidTagRecipientType "
            "is 1, 2 and 3 ([MS-OXOMSG] 2.2.3.1), each as PidTagDisplayName and PidTagSmtpAddress, else "
            "PidTagEmailAddress; a row of another type is counted in the run log, and none was seen on "
            "these inputs. Subject is PidTagSubject without the two characters that mark a stored "
            "prefix ([MS-PST] 2.5.3.1.1.1). Body is PidTagBody when it holds text, else the text the "
            "compressed RTF body holds or encapsulates, else the visible text of PidTagBodyHtml, "
            "decoded with PidTagInternetCodepage when its bytes decode in that code page and as UTF-8 "
            "otherwise; Body Source names which: PidTagBody on 2,486 of the 2,528 rows. Attachments "
            "holds the file attachments of the item and of items attached to it, as media. Attachment "
            "Names lists the item's own attachments, one per line, by stored file name; an attached "
            "item is shown as [attached item] and its subject, and attachments inside an attached item "
            "are not listed there. Read and Unsent are the mfRead and mfUnsent bits of "
            "PidTagMessageFlags ([MS-OXCMSG] 2.2.1.6). Internet Message ID is PidTagInternetMessageId. "
            "Meeting requests and responses (IPM.Schedule.Meeting) are reported here. The transport "
            "headers (PidTagTransportMessageHeaders) are not reported."
        ),
        "sample_data": {
            "windows11_arm_outlook_pst_known_20261109": "Windows 11 build 26200 (ARM64), Outlook LTSC 2024 16.0.17932.21056 | 9 rows",
            "windows11_arm_outlook_pst_stress_known_20261109": "Windows 11 build 26200 (ARM64), Outlook LTSC 2024 16.0.17932.21056 | 1210 rows",
            "pst_public_fixtures_20261109": "PST and OST test files from public library repositories | 279 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1, Outlook OST | 14 rows",
        },
        "paths": ('*.[pP][sS][tT]', '*.[oO][sS][tT]'),
        "output_types": "standard",
        "artifact_icon": "mail",
    },
    "outlookPstContacts": {
        "name": "Outlook Contacts",
        "description": "Contacts and distribution lists in Outlook PST and OST files, with their "
                       "names, email addresses, phone numbers and the times the items were created "
                       "and last changed.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-10",
        "last_update_date": "2026-11-10",
        "requirements": "none",
        "category": "Outlook",
        "notes": (
            "Reads every file named .pst or .ost, in any case, read-only, with the vendored pstprobe "
            "0.1.0 (scripts/vendor/pstprobe.py), written from Microsoft [MS-PST]; the 4 KB-page layout "
            "of newer OST files is not in [MS-PST] and follows Joachim Metz's PFF format notes. Items "
            "are those listed in the contents table of a folder, walking the folder tree from the root "
            "folder, so Deleted Items and, in an OST, folders such as Sync Issues are read too, and "
            "Folder names the folder. Search folder results, which are items of other folders, and "
            "folder-associated items get no rows. Items that were removed from Deleted Items are not "
            "recovered: the mail deleted that way in windows11_arm_outlook_pst_known_20261109 "
            "(kd_mail_8 in its fill log) is not reported. Items are routed to the Outlook artifacts by "
            "the prefix of PidTagMessageClass, matched without regard to case ([MS-OXCMSG] 2.2.1.3): "
            "IPM.Contact and IPM.DistList to Contacts, IPM.Appointment to Appointments, IPM.Task to "
            "Tasks, IPM.StickyNote to Notes, IPM.Activity to Journals, "
            "IPM.Microsoft.ScheduleData.FreeBusy, IPM.AbchPerson and IPM.Network to none, and every "
            "other class to Emails; an item with no message class is reported under Emails. Message "
            "Class is PidTagMessageClass as the folder's contents table holds it, else as the item "
            "holds it, and Item ID is the item's node ID in the file. Property IDs and names are those "
            "of [MS-OXPROPS]; meanings and enumerated values are from the Exchange protocol documents "
            "named below, release v20250520 ([MS-OXOCAL] v20250819). Datetime columns are the stored "
            "PtypTime values, which those documents give in UTC unless a column's notes say otherwise. "
            "A byte-identical second copy of a file is read once, the Users/ copy before one under "
            "System/Volumes/Data/, and an identical file in another user's folder is reported from the "
            "first path in sort order; a file that is not a PST or OST is logged and skipped; a file "
            "shorter than its header records is logged, since what is past the cut is missing, not "
            "empty; and values, items and attachments that cannot be read are counted in the run log. "
            "One row per item. Modified and Created are PidTagLastModificationTime and "
            "PidTagCreationTime. Display Name, Given Name and Surname are PidTagDisplayName, "
            "PidTagGivenName and PidTagSurname; File As is PidLidFileUnder; Email 1 to Email 3 are "
            "PidLidEmail1EmailAddress to PidLidEmail3EmailAddress; Business Phone, Home Phone and "
            "Mobile Phone are PidTagBusinessTelephoneNumber, PidTagHomeTelephoneNumber and "
            "PidTagMobileTelephoneNumber; Company and Job Title are PidTagCompanyName and PidTagTitle; "
            "Work Address and Home Address are PidLidWorkAddress and PidLidHomeAddress; Birthday is the "
            "date of PidTagBirthday, which [MS-OXOCNTC] 2.2.1.5.1 stores at 11:59 UTC; Notes is the "
            "item's body, read as for Outlook Emails. Attachments holds the file attachments of the "
            "item and of items attached to it, as media. On the corpus inputs in sample_data, 39 rows, "
            "Email 2, Email 3, Birthday and Home Address had no value on any row, and Modified was "
            "blank on 16. A distribution list (IPM.DistList, 3 rows) is reported by its name; its "
            "members ([MS-OXOCNTC] 2.2.2.2) are not decoded. In one of the three outlook.com OSTs of "
            "pst_public_fixtures_20261109, 11 contacts are in a Contacts subfolder named Recipient "
            "Cache and 1 in a folder named MeContact; what puts them there was not established."
        ),
        "sample_data": {
            "windows11_arm_outlook_pst_known_20261109": "Windows 11 build 26200 (ARM64), Outlook LTSC 2024 16.0.17932.21056 | 4 rows",
            "windows11_arm_outlook_pst_stress_known_20261109": "Windows 11 build 26200 (ARM64), Outlook LTSC 2024 16.0.17932.21056 | 3 rows",
            "pst_public_fixtures_20261109": "PST and OST test files from public library repositories | 32 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1, Outlook OST | 0 rows",
        },
        "paths": ('*.[pP][sS][tT]', '*.[oO][sS][tT]'),
        "output_types": "standard",
        "artifact_icon": "users",
    },
    "outlookPstAppointments": {
        "name": "Outlook Appointments",
        "description": "Calendar items in Outlook PST and OST files, with their start and end, "
                       "location, attendees, recurrence description and busy status.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-10",
        "last_update_date": "2026-11-10",
        "requirements": "none",
        "category": "Outlook",
        "notes": (
            "Reads every file named .pst or .ost, in any case, read-only, with the vendored pstprobe "
            "0.1.0 (scripts/vendor/pstprobe.py), written from Microsoft [MS-PST]; the 4 KB-page layout "
            "of newer OST files is not in [MS-PST] and follows Joachim Metz's PFF format notes. Items "
            "are those listed in the contents table of a folder, walking the folder tree from the root "
            "folder, so Deleted Items and, in an OST, folders such as Sync Issues are read too, and "
            "Folder names the folder. Search folder results, which are items of other folders, and "
            "folder-associated items get no rows. Items that were removed from Deleted Items are not "
            "recovered: the mail deleted that way in windows11_arm_outlook_pst_known_20261109 "
            "(kd_mail_8 in its fill log) is not reported. Items are routed to the Outlook artifacts by "
            "the prefix of PidTagMessageClass, matched without regard to case ([MS-OXCMSG] 2.2.1.3): "
            "IPM.Contact and IPM.DistList to Contacts, IPM.Appointment to Appointments, IPM.Task to "
            "Tasks, IPM.StickyNote to Notes, IPM.Activity to Journals, "
            "IPM.Microsoft.ScheduleData.FreeBusy, IPM.AbchPerson and IPM.Network to none, and every "
            "other class to Emails; an item with no message class is reported under Emails. Message "
            "Class is PidTagMessageClass as the folder's contents table holds it, else as the item "
            "holds it, and Item ID is the item's node ID in the file. Property IDs and names are those "
            "of [MS-OXPROPS]; meanings and enumerated values are from the Exchange protocol documents "
            "named below, release v20250520 ([MS-OXOCAL] v20250819). Datetime columns are the stored "
            "PtypTime values, which those documents give in UTC unless a column's notes say otherwise. "
            "A byte-identical second copy of a file is read once, the Users/ copy before one under "
            "System/Volumes/Data/, and an identical file in another user's folder is reported from the "
            "first path in sort order; a file that is not a PST or OST is logged and skipped; a file "
            "shorter than its header records is logged, since what is past the cut is missing, not "
            "empty; and values, items and attachments that cannot be read are counted in the run log. "
            "One row per item. Start and End are PidLidAppointmentStartWhole and "
            "PidLidAppointmentEndWhole ([MS-OXOCAL] 2.2.1.5, 2.2.1.6), for a recurring series those of "
            "its first instance; Modified is PidTagLastModificationTime. Subject is PidTagSubject; "
            "Location is PidLidLocation; All Day is PidLidAppointmentSubType (2.2.1.9); Recurring is "
            "PidLidRecurring (2.2.1.12); Recurrence Pattern is PidLidRecurrencePattern, the stored "
            "description of the recurrence (2.2.1.46); Busy Status is PidLidBusyStatus by its "
            "documented name (2.2.1.2); Required Attendees and Optional Attendees are "
            "PidLidToAttendeesString and PidLidCcAttendeesString; Body is the item's body, read as for "
            "Outlook Emails. The recurrence itself (PidLidAppointmentRecur) and exceptions to a series "
            "are not decoded. [MS-OXOCAL] 3.1.5.5.1 says the times of an all-day appointment that is "
            "not a meeting are converted to the time zone stored with it, not read as plain UTC: Start "
            "of the all-day appointment in windows11_arm_outlook_pst_known_20261109, made on a client "
            "at UTC-5 for 25 November 2026, is 2026-11-25 05:00, the local midnight, and the three "
            "Start values there are the times its fill log records, converted to UTC. Attachments holds "
            "the file attachments of the item and of items attached to it, as media. On the corpus "
            "inputs in sample_data, 518 rows, Optional Attendees had no value on any row; 488 rows are "
            "in folders named United States holidays in the three outlook.com OSTs of "
            "pst_public_fixtures_20261109; Modified was blank on 499; Recurring was Yes on 43 and "
            "Recurrence Pattern set on 7. Message Class held IPM.Appointment on all 518 rows; it is "
            "kept because a class that continues IPM.Appointment is reported here too."
        ),
        "sample_data": {
            "windows11_arm_outlook_pst_known_20261109": "Windows 11 build 26200 (ARM64), Outlook LTSC 2024 16.0.17932.21056 | 3 rows",
            "windows11_arm_outlook_pst_stress_known_20261109": "Windows 11 build 26200 (ARM64), Outlook LTSC 2024 16.0.17932.21056 | 3 rows",
            "pst_public_fixtures_20261109": "PST and OST test files from public library repositories | 512 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1, Outlook OST | 0 rows",
        },
        "paths": ('*.[pP][sS][tT]', '*.[oO][sS][tT]'),
        "output_types": "standard",
        "artifact_icon": "calendar",
    },
    "outlookPstTasks": {
        "name": "Outlook Tasks",
        "description": "Tasks in Outlook PST and OST files, with their start and due dates, status, "
                       "progress percentage and completion date as stored.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-10",
        "last_update_date": "2026-11-10",
        "requirements": "none",
        "category": "Outlook",
        "notes": (
            "Reads every file named .pst or .ost, in any case, read-only, with the vendored pstprobe "
            "0.1.0 (scripts/vendor/pstprobe.py), written from Microsoft [MS-PST]; the 4 KB-page layout "
            "of newer OST files is not in [MS-PST] and follows Joachim Metz's PFF format notes. Items "
            "are those listed in the contents table of a folder, walking the folder tree from the root "
            "folder, so Deleted Items and, in an OST, folders such as Sync Issues are read too, and "
            "Folder names the folder. Search folder results, which are items of other folders, and "
            "folder-associated items get no rows. Items that were removed from Deleted Items are not "
            "recovered: the mail deleted that way in windows11_arm_outlook_pst_known_20261109 "
            "(kd_mail_8 in its fill log) is not reported. Items are routed to the Outlook artifacts by "
            "the prefix of PidTagMessageClass, matched without regard to case ([MS-OXCMSG] 2.2.1.3): "
            "IPM.Contact and IPM.DistList to Contacts, IPM.Appointment to Appointments, IPM.Task to "
            "Tasks, IPM.StickyNote to Notes, IPM.Activity to Journals, "
            "IPM.Microsoft.ScheduleData.FreeBusy, IPM.AbchPerson and IPM.Network to none, and every "
            "other class to Emails; an item with no message class is reported under Emails. Message "
            "Class is PidTagMessageClass as the folder's contents table holds it, else as the item "
            "holds it, and Item ID is the item's node ID in the file. Property IDs and names are those "
            "of [MS-OXPROPS]; meanings and enumerated values are from the Exchange protocol documents "
            "named below, release v20250520 ([MS-OXOCAL] v20250819). Datetime columns are the stored "
            "PtypTime values, which those documents give in UTC unless a column's notes say otherwise. "
            "A byte-identical second copy of a file is read once, the Users/ copy before one under "
            "System/Volumes/Data/, and an identical file in another user's folder is reported from the "
            "first path in sort order; a file that is not a PST or OST is logged and skipped; a file "
            "shorter than its header records is logged, since what is past the cut is missing, not "
            "empty; and values, items and attachments that cannot be read are counted in the run log. "
            "One row per item. Due Date and Start Date are PidLidTaskDueDate and PidLidTaskStartDate, "
            "which [MS-OXOTASK] 2.2.2.2.5 and 2.2.2.2.4 define as dates in the user's local time zone, "
            "so they are reported as dates. A value in the year 4501, where the no-date value those "
            "sections give (0x5AE980E0 minutes) falls, is left blank in Due Date, Start Date and Date "
            "Completed and counted in the run log; none was seen on the corpus inputs. Date Completed "
            "is PidLidTaskDateCompleted, midnight in the local time zone converted to UTC (2.2.2.2.9): "
            "in windows11_arm_outlook_pst_known_20261109, made at UTC-5, the task marked complete on 9 "
            "November 2026 holds 2026-11-09 05:00. Modified is PidTagLastModificationTime. Status is "
            "PidLidTaskStatus, shown by a short label for the meaning 2.2.2.2.2 gives each value; "
            "Percent Complete is PidLidPercentComplete, a fraction from 0 to 1 (2.2.2.2.3), shown as a "
            "percentage; Complete is PidLidTaskComplete; Owner is PidLidTaskOwner; Body is the item's "
            "body, read as for Outlook Emails. Attachments holds the file attachments of the item and "
            "of items attached to it, as media. Task requests (IPM.TaskRequest) are messages and are "
            "reported under Outlook Emails. In windows11_arm_outlook_pst_known_20261109 the open task's "
            "Due Date is 2026-11-30, the due date its fill log records. Message Class held IPM.Task on "
            "all 6 rows of the corpus inputs in sample_data and the two Enron files named under Outlook "
            "Emails; it is kept because a class that continues IPM.Task is reported here too."
        ),
        "sample_data": {
            "windows11_arm_outlook_pst_known_20261109": "Windows 11 build 26200 (ARM64), Outlook LTSC 2024 16.0.17932.21056 | 2 rows",
            "windows11_arm_outlook_pst_stress_known_20261109": "Windows 11 build 26200 (ARM64), Outlook LTSC 2024 16.0.17932.21056 | 2 rows",
            "pst_public_fixtures_20261109": "PST and OST test files from public library repositories | 2 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1, Outlook OST | 0 rows",
        },
        "paths": ('*.[pP][sS][tT]', '*.[oO][sS][tT]'),
        "output_types": "standard",
        "artifact_icon": "check-square",
    },
    "outlookPstNotes": {
        "name": "Outlook Notes",
        "description": "Notes in Outlook PST and OST files, with their text, colour and the times "
                       "they were created and last changed.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-10",
        "last_update_date": "2026-11-10",
        "requirements": "none",
        "category": "Outlook",
        "notes": (
            "Reads every file named .pst or .ost, in any case, read-only, with the vendored pstprobe "
            "0.1.0 (scripts/vendor/pstprobe.py), written from Microsoft [MS-PST]; the 4 KB-page layout "
            "of newer OST files is not in [MS-PST] and follows Joachim Metz's PFF format notes. Items "
            "are those listed in the contents table of a folder, walking the folder tree from the root "
            "folder, so Deleted Items and, in an OST, folders such as Sync Issues are read too, and "
            "Folder names the folder. Search folder results, which are items of other folders, and "
            "folder-associated items get no rows. Items that were removed from Deleted Items are not "
            "recovered: the mail deleted that way in windows11_arm_outlook_pst_known_20261109 "
            "(kd_mail_8 in its fill log) is not reported. Items are routed to the Outlook artifacts by "
            "the prefix of PidTagMessageClass, matched without regard to case ([MS-OXCMSG] 2.2.1.3): "
            "IPM.Contact and IPM.DistList to Contacts, IPM.Appointment to Appointments, IPM.Task to "
            "Tasks, IPM.StickyNote to Notes, IPM.Activity to Journals, "
            "IPM.Microsoft.ScheduleData.FreeBusy, IPM.AbchPerson and IPM.Network to none, and every "
            "other class to Emails; an item with no message class is reported under Emails. Message "
            "Class is PidTagMessageClass as the folder's contents table holds it, else as the item "
            "holds it, and Item ID is the item's node ID in the file. Property IDs and names are those "
            "of [MS-OXPROPS]; meanings and enumerated values are from the Exchange protocol documents "
            "named below, release v20250520 ([MS-OXOCAL] v20250819). Datetime columns are the stored "
            "PtypTime values, which those documents give in UTC unless a column's notes say otherwise. "
            "A byte-identical second copy of a file is read once, the Users/ copy before one under "
            "System/Volumes/Data/, and an identical file in another user's folder is reported from the "
            "first path in sort order; a file that is not a PST or OST is logged and skipped; a file "
            "shorter than its header records is logged, since what is past the cut is missing, not "
            "empty; and values, items and attachments that cannot be read are counted in the run log. "
            "One row per item. Modified and Created are PidTagLastModificationTime and "
            "PidTagCreationTime; Subject is PidTagSubject; Body is the item's body, read as for Outlook "
            "Emails; Color is PidLidNoteColor by its documented name ([MS-OXONOTE] 2.2.1.1). "
            "Attachments holds the file attachments of the item and of items attached to it, as media. "
            "On the corpus inputs in sample_data, Color held Yellow on all 5 rows. Attachments had no "
            "value on any of those rows, and Modified was blank on 1. Message Class held IPM.StickyNote "
            "on all 5 rows; it is kept because a class that continues IPM.StickyNote is reported here "
            "too."
        ),
        "sample_data": {
            "windows11_arm_outlook_pst_known_20261109": "Windows 11 build 26200 (ARM64), Outlook LTSC 2024 16.0.17932.21056 | 2 rows",
            "windows11_arm_outlook_pst_stress_known_20261109": "Windows 11 build 26200 (ARM64), Outlook LTSC 2024 16.0.17932.21056 | 2 rows",
            "pst_public_fixtures_20261109": "PST and OST test files from public library repositories | 1 row",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1, Outlook OST | 0 rows",
        },
        "paths": ('*.[pP][sS][tT]', '*.[oO][sS][tT]'),
        "output_types": "standard",
        "artifact_icon": "file-text",
    },
    "outlookPstJournals": {
        "name": "Outlook Journals",
        "description": "Journal entries in Outlook PST and OST files, with the activity type, its "
                       "start, end and duration, and the entry's text.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-10",
        "last_update_date": "2026-11-10",
        "requirements": "none",
        "category": "Outlook",
        "notes": (
            "Reads every file named .pst or .ost, in any case, read-only, with the vendored pstprobe "
            "0.1.0 (scripts/vendor/pstprobe.py), written from Microsoft [MS-PST]; the 4 KB-page layout "
            "of newer OST files is not in [MS-PST] and follows Joachim Metz's PFF format notes. Items "
            "are those listed in the contents table of a folder, walking the folder tree from the root "
            "folder, so Deleted Items and, in an OST, folders such as Sync Issues are read too, and "
            "Folder names the folder. Search folder results, which are items of other folders, and "
            "folder-associated items get no rows. Items that were removed from Deleted Items are not "
            "recovered: the mail deleted that way in windows11_arm_outlook_pst_known_20261109 "
            "(kd_mail_8 in its fill log) is not reported. Items are routed to the Outlook artifacts by "
            "the prefix of PidTagMessageClass, matched without regard to case ([MS-OXCMSG] 2.2.1.3): "
            "IPM.Contact and IPM.DistList to Contacts, IPM.Appointment to Appointments, IPM.Task to "
            "Tasks, IPM.StickyNote to Notes, IPM.Activity to Journals, "
            "IPM.Microsoft.ScheduleData.FreeBusy, IPM.AbchPerson and IPM.Network to none, and every "
            "other class to Emails; an item with no message class is reported under Emails. Message "
            "Class is PidTagMessageClass as the folder's contents table holds it, else as the item "
            "holds it, and Item ID is the item's node ID in the file. Property IDs and names are those "
            "of [MS-OXPROPS]; meanings and enumerated values are from the Exchange protocol documents "
            "named below, release v20250520 ([MS-OXOCAL] v20250819). Datetime columns are the stored "
            "PtypTime values, which those documents give in UTC unless a column's notes say otherwise. "
            "A byte-identical second copy of a file is read once, the Users/ copy before one under "
            "System/Volumes/Data/, and an identical file in another user's folder is reported from the "
            "first path in sort order; a file that is not a PST or OST is logged and skipped; a file "
            "shorter than its header records is logged, since what is past the cut is missing, not "
            "empty; and values, items and attachments that cannot be read are counted in the run log. "
            "One row per item. Start and End are PidLidLogStart and PidLidLogEnd ([MS-OXOJRNL] 2.2.1.3, "
            "2.2.1.4); Modified is PidTagLastModificationTime; Type and Type Description are "
            "PidLidLogType and PidLidLogTypeDesc as stored; Duration (minutes) is PidLidLogDuration; "
            "Subject is PidTagSubject; Body is the item's body, read as for Outlook Emails. In "
            "windows11_arm_outlook_pst_known_20261109 both entries' Start, End and Duration match the "
            "local times and lengths its fill log records, converted to UTC. Attachments holds the file "
            "attachments of the item and of items attached to it, as media. On the corpus inputs in "
            "sample_data, 5 rows, Attachments had no value on any row. Message Class held IPM.Activity "
            "on all 5 rows; it is kept because a class that continues IPM.Activity is reported here "
            "too."
        ),
        "sample_data": {
            "windows11_arm_outlook_pst_known_20261109": "Windows 11 build 26200 (ARM64), Outlook LTSC 2024 16.0.17932.21056 | 2 rows",
            "windows11_arm_outlook_pst_stress_known_20261109": "Windows 11 build 26200 (ARM64), Outlook LTSC 2024 16.0.17932.21056 | 2 rows",
            "pst_public_fixtures_20261109": "PST and OST test files from public library repositories | 1 row",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1, Outlook OST | 0 rows",
        },
        "paths": ('*.[pP][sS][tT]', '*.[oO][sS][tT]'),
        "output_types": "standard",
        "artifact_icon": "book",
    },
    "outlookPstAttachments": {
        "name": "Outlook Attachments",
        "description": "File attachments of the items in Outlook PST and OST files, with the "
                       "attachment itself, its name and size, and the item it belongs to.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-11-10",
        "last_update_date": "2026-11-10",
        "requirements": "none",
        "category": "Outlook",
        "notes": (
            "Reads every file named .pst or .ost, in any case, read-only, with the vendored pstprobe "
            "0.1.0 (scripts/vendor/pstprobe.py), written from Microsoft [MS-PST]; the 4 KB-page layout "
            "of newer OST files is not in [MS-PST] and follows Joachim Metz's PFF format notes. Items "
            "are those listed in the contents table of a folder, walking the folder tree from the root "
            "folder, so Deleted Items and, in an OST, folders such as Sync Issues are read too, and "
            "Folder names the folder. Search folder results, which are items of other folders, and "
            "folder-associated items get no rows. Items that were removed from Deleted Items are not "
            "recovered: the mail deleted that way in windows11_arm_outlook_pst_known_20261109 "
            "(kd_mail_8 in its fill log) is not reported. Items are routed to the Outlook artifacts by "
            "the prefix of PidTagMessageClass, matched without regard to case ([MS-OXCMSG] 2.2.1.3): "
            "IPM.Contact and IPM.DistList to Contacts, IPM.Appointment to Appointments, IPM.Task to "
            "Tasks, IPM.StickyNote to Notes, IPM.Activity to Journals, "
            "IPM.Microsoft.ScheduleData.FreeBusy, IPM.AbchPerson and IPM.Network to none, and every "
            "other class to Emails; an item with no message class is reported under Emails. Message "
            "Class is PidTagMessageClass as the folder's contents table holds it, else as the item "
            "holds it, and Item ID is the item's node ID in the file. Property IDs and names are those "
            "of [MS-OXPROPS]; meanings and enumerated values are from the Exchange protocol documents "
            "named below, release v20250520 ([MS-OXOCAL] v20250819). Datetime columns are the stored "
            "PtypTime values, which those documents give in UTC unless a column's notes say otherwise. "
            "A byte-identical second copy of a file is read once, the Users/ copy before one under "
            "System/Volumes/Data/, and an identical file in another user's folder is reported from the "
            "first path in sort order; a file that is not a PST or OST is logged and skipped; a file "
            "shorter than its header records is logged, since what is past the cut is missing, not "
            "empty; and values, items and attachments that cannot be read are counted in the run log. "
            "One row per file attachment of an item reported by the other Outlook artifacts, including "
            "the attachments of items attached to it, whose subjects Within Attached Item gives. Item "
            "Delivery Time and Item Modified are the item's PidTagMessageDeliveryTime and "
            "PidTagLastModificationTime, read as for Outlook Emails. Attachment is the attachment's "
            "data (PidTagAttachDataBinary) as media; File Name is PidTagAttachLongFilename, else "
            "PidTagAttachFilename; Size is the number of bytes of that data; MIME Type is "
            "PidTagAttachMimeTag, blank on 403 of the 810 rows of the corpus inputs in sample_data and "
            "the two Enron files named under Outlook Emails. Item Subject, Message Class, Item ID and "
            "Folder are the item's. The attachment's own creation and modification times are not "
            "reported: in windows11_arm_outlook_pst_known_20261109 they are earlier than the first "
            "entry of its fill log, and their meaning was not established. Attached items themselves "
            "are listed by subject in Outlook Emails' Attachment Names. An attachment that "
            "PidTagAttachMethod ([MS-OXCMSG] 2.2.2.9) marks as stored by path or web reference (2, 4, "
            "7) or in an application-specific format (afStorage, 6) holds no data here, so it is listed "
            "with no Attachment media, and the afStorage ones are counted in the run log; only methods "
            "1 (by value) and 5 (attached item) occur on the corpus inputs, so those branches are "
            "unexercised."
        ),
        "sample_data": {
            "windows11_arm_outlook_pst_known_20261109": "Windows 11 build 26200 (ARM64), Outlook LTSC 2024 16.0.17932.21056 | 2 rows",
            "windows11_arm_outlook_pst_stress_known_20261109": "Windows 11 build 26200 (ARM64), Outlook LTSC 2024 16.0.17932.21056 | 352 rows",
            "pst_public_fixtures_20261109": "PST and OST test files from public library repositories | 294 rows",
            "cfreds_leakage_win7": "Windows 7 Ultimate SP1, Outlook OST | 0 rows",
        },
        "paths": ('*.[pP][sS][tT]', '*.[oO][sS][tT]'),
        "output_types": "standard",
        "artifact_icon": "paperclip",
    },
}

from scripts.ilapfuncs import artifact_processor
from scripts import outlook_pst as O

# [MS-OXOCAL] 2.2.1.2 PidLidBusyStatus
_BUSY = {0: 'Free', 1: 'Tentative', 2: 'Busy', 3: 'Out of Office', 4: 'Working Elsewhere'}
# [MS-OXOTASK] 2.2.2.2.2 PidLidTaskStatus
_TASK_STATUS = {0: 'Not Started', 1: 'In Progress', 2: 'Complete', 3: 'Waiting on Someone Else',
                4: 'Deferred'}
# [MS-OXONOTE] 2.2.1.1 PidLidNoteColor
_NOTE_COLOR = {0: 'Blue', 1: 'Green', 2: 'Pink', 3: 'Yellow', 4: 'White'}


def _enum(value, names):
    """The documented name of an enumerated value, else the value as stored."""
    if value is None:
        return ''
    return names.get(value, f'{value} (as stored)')


def _tail(message, message_class, relative):
    return (message_class, f'0x{message.nid:x}', relative)


@artifact_processor
def outlookPstEmails(context):
    data_headers = (('Delivery Time', 'datetime'), ('Submit Time', 'datetime'), ('Modified', 'datetime'),
                    'Folder', 'From', 'From Address', 'Sent On Behalf Of', 'To', 'Cc', 'Bcc', 'Subject',
                    'Body', 'Body Source', ('Attachments', 'media'), 'Attachment Names', 'Read', 'Unsent',
                    'Internet Message ID', 'Message Class', 'Item ID', 'Source File')

    def row(m, folder, message_class, source, relative, r):
        pc = m.pc
        flags = r.get(pc, O.TAG_MESSAGE_FLAGS)
        flags = flags if isinstance(flags, int) else None
        people = O.recipients(m, r)
        body, body_source = O.body_text(m, r)
        sender = r.text(r.get(pc, O.TAG_SENDER_NAME))
        behalf = r.text(r.get(pc, O.TAG_SENT_REPRESENTING_NAME))
        return (r.time(r.get(pc, O.TAG_DELIVERY_TIME)), r.time(r.get(pc, O.TAG_CLIENT_SUBMIT_TIME)),
                r.time(r.get(pc, O.TAG_MODIFIED_TIME)), folder, sender,
                r.text(r.get(pc, O.TAG_SENDER_SMTP)) or r.text(r.get(pc, O.TAG_SENDER_EMAIL)),
                behalf if behalf != sender else '',
                '; '.join(people['To']), '; '.join(people['Cc']), '; '.join(people['Bcc']),
                r.text(m.subject), body, body_source, O.attachment_media(source, m, r),
                O.attachment_names(m, r),
                '' if flags is None else r.flag(flags & O.MF_READ),
                '' if flags is None else r.flag(flags & O.MF_UNSENT),
                r.text(r.get(pc, O.TAG_INTERNET_MESSAGE_ID))) + _tail(m, message_class, relative)

    rows, read = O.read_items(context, ('email',), 'Outlook Emails', row)
    return data_headers, rows, read


@artifact_processor
def outlookPstContacts(context):
    data_headers = (('Modified', 'datetime'), ('Created', 'datetime'), 'Folder', 'Display Name',
                    'Given Name', 'Surname', 'File As', 'Email 1', 'Email 2', 'Email 3', 'Business Phone',
                    'Home Phone', 'Mobile Phone', 'Company', 'Job Title', ('Birthday', 'date'),
                    'Work Address', 'Home Address', 'Notes', ('Attachments', 'media'),
                    'Message Class', 'Item ID', 'Source File')

    def row(m, folder, message_class, source, relative, r):
        pc = m.pc
        birthday = r.time(r.get(pc, O.TAG_BIRTHDAY))
        return (r.time(r.get(pc, O.TAG_MODIFIED_TIME)), r.time(r.get(pc, O.TAG_CREATION_TIME)), folder,
                r.text(r.get(pc, O.TAG_DISPLAY_NAME)), r.text(r.get(pc, O.TAG_GIVEN_NAME)),
                r.text(r.get(pc, O.TAG_SURNAME)), r.text(r.named(m, O.PSETID_ADDRESS, 0x8005)),
                r.text(r.named(m, O.PSETID_ADDRESS, 0x8083)), r.text(r.named(m, O.PSETID_ADDRESS, 0x8093)),
                r.text(r.named(m, O.PSETID_ADDRESS, 0x80A3)), r.text(r.get(pc, O.TAG_BUSINESS_PHONE)),
                r.text(r.get(pc, O.TAG_HOME_PHONE)), r.text(r.get(pc, O.TAG_MOBILE_PHONE)),
                r.text(r.get(pc, O.TAG_COMPANY)), r.text(r.get(pc, O.TAG_TITLE)),
                birthday.date().isoformat() if birthday else '',
                r.text(r.named(m, O.PSETID_ADDRESS, 0x801B)), r.text(r.named(m, O.PSETID_ADDRESS, 0x801A)),
                O.body_text(m, r)[0], O.attachment_media(source, m, r)) + _tail(m, message_class, relative)

    rows, read = O.read_items(context, ('contact',), 'Outlook Contacts', row)
    return data_headers, rows, read


@artifact_processor
def outlookPstAppointments(context):
    data_headers = (('Start', 'datetime'), ('End', 'datetime'), ('Modified', 'datetime'), 'Folder',
                    'Subject', 'Location', 'All Day', 'Recurring', 'Recurrence Pattern', 'Busy Status',
                    'Required Attendees', 'Optional Attendees', 'Body', ('Attachments', 'media'),
                    'Message Class', 'Item ID', 'Source File')

    def row(m, folder, message_class, source, relative, r):
        a = O.PSETID_APPOINTMENT
        busy = r.named(m, a, 0x8205)
        return (r.time(r.named(m, a, 0x820D)), r.time(r.named(m, a, 0x820E)),
                r.time(r.get(m.pc, O.TAG_MODIFIED_TIME)), folder, r.text(m.subject),
                r.text(r.named(m, a, 0x8208)), r.flag(r.named(m, a, 0x8215)), r.flag(r.named(m, a, 0x8223)),
                r.text(r.named(m, a, 0x8232)), _enum(busy if isinstance(busy, int) else None, _BUSY),
                r.text(r.named(m, a, 0x823B)), r.text(r.named(m, a, 0x823C)), O.body_text(m, r)[0],
                O.attachment_media(source, m, r)) + _tail(m, message_class, relative)

    rows, read = O.read_items(context, ('appointment',), 'Outlook Appointments', row)
    return data_headers, rows, read


@artifact_processor
def outlookPstTasks(context):
    data_headers = (('Due Date', 'date'), ('Start Date', 'date'), ('Date Completed', 'datetime'),
                    ('Modified', 'datetime'), 'Folder', 'Subject', 'Status', 'Percent Complete', 'Complete',
                    'Owner', 'Body', ('Attachments', 'media'), 'Message Class', 'Item ID', 'Source File')

    def row(m, folder, message_class, source, relative, r):
        t = O.PSETID_TASK
        due = r.time(r.named(m, t, 0x8105), no_date_sentinel=True)
        start = r.time(r.named(m, t, 0x8104), no_date_sentinel=True)
        status = r.named(m, t, 0x8101)
        percent = r.named(m, t, 0x8102)
        return (due.date().isoformat() if due else '', start.date().isoformat() if start else '',
                r.time(r.named(m, t, 0x810F), no_date_sentinel=True), r.time(r.get(m.pc, O.TAG_MODIFIED_TIME)),
                folder, r.text(m.subject), _enum(status if isinstance(status, int) else None, _TASK_STATUS),
                f'{percent * 100:g}%' if isinstance(percent, float) else '', r.flag(r.named(m, t, 0x811C)),
                r.text(r.named(m, t, 0x811F)), O.body_text(m, r)[0],
                O.attachment_media(source, m, r)) + _tail(m, message_class, relative)

    rows, read = O.read_items(context, ('task',), 'Outlook Tasks', row)
    return data_headers, rows, read


@artifact_processor
def outlookPstNotes(context):
    data_headers = (('Modified', 'datetime'), ('Created', 'datetime'), 'Folder', 'Subject', 'Body', 'Color',
                    ('Attachments', 'media'), 'Message Class', 'Item ID', 'Source File')

    def row(m, folder, message_class, source, relative, r):
        color = r.named(m, O.PSETID_NOTE, 0x8B00)
        return (r.time(r.get(m.pc, O.TAG_MODIFIED_TIME)), r.time(r.get(m.pc, O.TAG_CREATION_TIME)), folder,
                r.text(m.subject), O.body_text(m, r)[0],
                _enum(color if isinstance(color, int) else None, _NOTE_COLOR),
                O.attachment_media(source, m, r)) + _tail(m, message_class, relative)

    rows, read = O.read_items(context, ('note',), 'Outlook Notes', row)
    return data_headers, rows, read


@artifact_processor
def outlookPstJournals(context):
    data_headers = (('Start', 'datetime'), ('End', 'datetime'), ('Modified', 'datetime'), 'Folder', 'Type',
                    'Type Description', ('Duration (minutes)', 'number'), 'Subject', 'Body', ('Attachments', 'media'),
                    'Message Class', 'Item ID', 'Source File')

    def row(m, folder, message_class, source, relative, r):
        g = O.PSETID_LOG
        duration = r.named(m, g, 0x8707)
        return (r.time(r.named(m, g, 0x8706)), r.time(r.named(m, g, 0x8708)),
                r.time(r.get(m.pc, O.TAG_MODIFIED_TIME)), folder, r.text(r.named(m, g, 0x8700)),
                r.text(r.named(m, g, 0x8712)), duration if isinstance(duration, int) else '',
                r.text(m.subject), O.body_text(m, r)[0],
                O.attachment_media(source, m, r)) + _tail(m, message_class, relative)

    rows, read = O.read_items(context, ('journal',), 'Outlook Journals', row)
    return data_headers, rows, read


@artifact_processor
def outlookPstAttachments(context):
    data_headers = (('Item Delivery Time', 'datetime'), ('Item Modified', 'datetime'), ('Attachment', 'media'),
                    'File Name', ('Size', 'number'), 'MIME Type', 'Folder', 'Item Subject', 'Within Attached Item',
                    'Message Class', 'Item ID', 'Source File')

    def row(m, folder, message_class, source, relative, r):
        out = []
        for within, a in O.file_attachments(m, r):
            size = None
            try:
                size = a.data_size()
            except O.P.DAMAGE_ERRORS:
                r.counts['attachment sizes that could not be read'] += 1
            out.append((r.time(r.get(m.pc, O.TAG_DELIVERY_TIME)), r.time(r.get(m.pc, O.TAG_MODIFIED_TIME)),
                        O.check_in_attachment(source, a, r),
                        r.text(a.filename), size if size is not None else '',
                        r.text(r.get(a.pc, O.TAG_ATTACH_MIME)), folder, r.text(m.subject), within)
                       + _tail(m, message_class, relative))
        return out

    groups, read = O.read_items(context, ('email', 'contact', 'appointment', 'task', 'note', 'journal'),
                                'Outlook Attachments', row)
    return data_headers, [r for group in groups for r in group], read
