"""Command, search and input history, registers, file marks and per-file marks in Vim's viminfo file, for DLEAPP.

Author: @AlexisBrignoni, Claude.
"""

__artifacts_v2__ = {
    "vimHistory": {
        "name": "Vim History",
        "description": "Command-line, search, expression and input lines saved in Vim's viminfo file, with the time "
                       "the file stores for each.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-04",
        "last_update_date": "2026-10-04",
        "requirements": "none",
        "category": "Command Line (Vim)",
        "notes": "Reads Vim's viminfo file where Vim keeps it by default: .viminfo in the home folder on Linux and "
                 "macOS and _viminfo on Windows "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/os_unix.h#L299, "
                 "https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/os_mac.h#L158 and "
                 "https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/os_dos.h#L66-L69, all "
                 "at Vim's v9.1.2141 tag); a file named with Vim's -i option or its 'viminfo' option is read only if "
                 "it has one of those names. No Windows file was tested. A file with neither an *encoding= line nor a"
                 " version line is not read and is counted in the run log; the comment lines, which Vim writes in the"
                 " language of its messages "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L3009-L3013),"
                 " are not used. Vim writes each item twice: a line in its older form, and below it a line starting "
                 "with | (a bar line) that also stores a time; a version line, |1 and a number, says which kinds have"
                 " bar lines, from 2 for history, 3 for registers and 4 for file marks "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/vim.h#L1241-L1249), "
                 "and when Vim reads a file back it passes over the older lines of a kind whose bar lines the version"
                 " announces "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L2902-L2934)."
                 " The artifact reads the file the same way: every bar line, and the older lines, which give a blank "
                 "time, only for a kind the version line does not cover. A value too long for a line is continued on "
                 "lines starting with |<, with its length counted in bytes "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L1050-L1055),"
                 " or, in the older lines, put on a following line starting with < "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L147-L149);"
                 " both are read, and text is decoded with the encoding the file's *encoding= line names "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L2887), "
                 "latin-1 when there is none, with bytes that do not decode shown as backslash escapes. Times are "
                 "whole seconds since 1970 as the writing machine's clock gave them, shown in UTC; a stored 0 is "
                 "shown blank. A history bar line is |2, the kind of history, the time, the separator and the text "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L936-L942);"
                 " History is the kind, 0 to 4 in Vim's order: Command line, Search, Expression, Input line and Debug"
                 " line "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/vim.h#L1233-L1237). "
                 "In the older lines input and debug lines share one mark, so such a row reads 'Input or debug line'."
                 " Vim sets the time when it adds an entry to its history "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/cmdhist.c#L363) and "
                 "again when an entry already there is used once more, which moves it to the newest place instead of "
                 "adding a second one "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/cmdhist.c#L273). The "
                 "known sessions agree: in the fourth session of ubuntu2604_arm64_viminfo, whose commands were spaced"
                 " with :sleep, the entries 'set ruler', 'sleep 3', 'sleep 2' and 'q' are timed 0, 3, 6 and 8 seconds"
                 " after the session's start; ':sleep 3' was typed twice there and ':q' in two sessions, and each has"
                 " one row, with the later time. So a time is when the entry was last used, to the second, by the "
                 "machine's clock, and an earlier use of the same text leaves no row. Search Separator is the "
                 "character stored with a search entry, as stored: / on the 3 forward searches and ? on the backward "
                 "search of that capture, and blank on the pattern that the :s command of the first session added to "
                 "the search history. Entry is the text without the leading : or search character. The capture's 19 "
                 "rows are 12 command lines, 5 searches, the expression 6*7 entered through the expression register "
                 "and the answer typed to an input() prompt; the answer is under Input line and the :call that asked "
                 "for it under Command line. vim_viminfo_known_macos gave 9 rows, 6 command lines and 3 searches. "
                 "Within each kind the file's order, which the rows keep, was newest first on both captures. The line"
                 " the first session of ubuntu2604_arm64_viminfo typed in insert mode and wrote to the edited file is"
                 " nowhere in the viminfo file, in any of the copies taken after the four sessions. A row shows that "
                 "the text was entered in a Vim run under the account whose home holds the file; it does not show who"
                 " typed it. Vim writes a limited number of entries of each kind, the smaller of its 'history' option"
                 " and any limit in its 'viminfo' option "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L859-L863),"
                 " so an entry's absence is not evidence that it was never typed. Tested on two known captures. "
                 "ubuntu2604_arm64_viminfo is the .viminfo of a virtual machine running Vim 9.1 (patches 1-948, "
                 "950-2141) after four sessions driven by key scripts, and vim_viminfo_known_macos is the viminfo "
                 "file of two such sessions run with the Vim 9.1 (patches 1-1752) that ships with macOS 27.0.1 under "
                 "a scratch home folder. On both, every row's time falls inside the session that made it by the "
                 "recorded start and end of each session, and no time was blank. The virtual machine's clock was "
                 "11,853 seconds behind real time, and the stored times are that clock's. The reading was also "
                 "compared with Vim's own writer: 40 viminfo files that Vim 9.1 on the virtual machine wrote from "
                 "3,200 generated history entries and 320 generated registers (3,737 lines), with quotes, "
                 "backslashes, control characters, multi-byte text and values up to 1,500 characters, which made "
                 "lines as long as 1,683 bytes. The artifact read back every one of the 3,200 entries, each with a "
                 "time, and 317 of the registers as given; the other 3 were empty blockwise registers, which Vim "
                 "wrote with a width of -1 that its own bar-line reader, which takes only digits as a number, does "
                 "not read "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L1106-L1109)."
                 " With the bar lines and version line taken out of the same 40 files, the older lines gave the same "
                 "3,200 entries and all 320 registers, with no time; no file written by a Vim that old was tested. No"
                 " member of ubuntu2604_arm64_triage, honeynet_fc7_debian5, dleapp_macos_bigsur, "
                 "evidencelocker_macos14 or magnet2021_macos_bigsur matches the declared paths. Not read: the last "
                 "search and substitute patterns, the buffer list and global variables a viminfo file can also hold, "
                 "and the files the marks name. Line is the line of the viminfo file a row comes from, and Source "
                 "File the file; the report's located-at line names the files that held a row.",
        "paths": ("*/.viminfo", "*/_viminfo"),
        "output_types": "standard",
        "artifact_icon": "terminal",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "evidencelocker_macos14": "macOS 14.6.1 build 23G93 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "magnet2021_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_viminfo": "Ubuntu 26.04 LTS aarch64, Vim 9.1.2141 | 19 rows",
            "vim_viminfo_known_macos": "macOS 27.0.1 build 26A434, Vim 9.1.1752 | 9 rows",
        },
    },
    "vimRegisters": {
        "name": "Vim Registers",
        "description": "Text held in Vim's registers as saved in its viminfo file, with the time the file stores for "
                       "each register.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-04",
        "last_update_date": "2026-10-04",
        "requirements": "none",
        "category": "Command Line (Vim)",
        "notes": "Reads Vim's viminfo file where Vim keeps it by default: .viminfo in the home folder on Linux and "
                 "macOS and _viminfo on Windows "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/os_unix.h#L299, "
                 "https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/os_mac.h#L158 and "
                 "https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/os_dos.h#L66-L69, all "
                 "at Vim's v9.1.2141 tag); a file named with Vim's -i option or its 'viminfo' option is read only if "
                 "it has one of those names. No Windows file was tested. A file with neither an *encoding= line nor a"
                 " version line is not read and is counted in the run log; the comment lines, which Vim writes in the"
                 " language of its messages "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L3009-L3013),"
                 " are not used. Vim writes each item twice: a line in its older form, and below it a line starting "
                 "with | (a bar line) that also stores a time; a version line, |1 and a number, says which kinds have"
                 " bar lines, from 2 for history, 3 for registers and 4 for file marks "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/vim.h#L1241-L1249), "
                 "and when Vim reads a file back it passes over the older lines of a kind whose bar lines the version"
                 " announces "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L2902-L2934)."
                 " The artifact reads the file the same way: every bar line, and the older lines, which give a blank "
                 "time, only for a kind the version line does not cover. A value too long for a line is continued on "
                 "lines starting with |<, with its length counted in bytes "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L1050-L1055),"
                 " or, in the older lines, put on a following line starting with < "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L147-L149);"
                 " both are read, and text is decoded with the encoding the file's *encoding= line names "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L2887), "
                 "latin-1 when there is none, with bytes that do not decode shown as backslash escapes. Times are "
                 "whole seconds since 1970 as the writing machine's clock gave them, shown in UTC; a stored 0 is "
                 "shown blank. A register bar line is |3, flags, the register, its type, the number of lines, the "
                 "block width, the time and the lines "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L1986-L1990)."
                 " Register is the register's character as Vim names it from the stored number: 0 to 9, a to z from "
                 "10 and - for 36 "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/register.c#L2397-L2418);"
                 " another number is shown as '(register N)'. Vim does not write the clipboard registers "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L1911-L1913)."
                 " Type is CHAR, LINE or BLOCK for the stored 0, 1 or 2 "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/vim.h#L1681-L1683), "
                 "Text the stored lines joined by line breaks, Lines their count and Block Width the stored width. "
                 "Unnamed Register is Yes when flag 1 is set, which marks the register the unnamed register points "
                 "at, and Last Executed is Yes when flag 2 is set, the register last run with @. Vim sets a "
                 "register's time when text is yanked or deleted into it "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/register.c#L1273). On"
                 " ubuntu2604_arm64_viminfo the 5 rows are 0, 1, a, b and d: register 1 holds the line deleted in the"
                 " second session and has that session's time; register 0 held the line yanked in the first session "
                 "through the first three copies of the file and, after the fourth session yanked another line, holds"
                 " that line with the fourth session's time, so the earlier text is gone; register d, yanked into "
                 "last, is the one marked Unnamed Register, as a, b and b were in the copies taken after sessions one"
                 " to three. vim_viminfo_known_macos gave 4 rows. Last Executed was blank on every row of both "
                 "captures; no session ran a register. On both captures Lines held 1 and Block Width held 0 on every "
                 "row: each register held one line and none was blockwise. A register holds text that was yanked or "
                 "deleted in Vim, so a row can hold text of a file that has since changed or gone. Vim limits what it"
                 " saves: with its built-in 'viminfo' value, '100,<50,s10,h "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/optiondefs.h#L2879), "
                 "a register of more than 50 lines is written with its first 50 and one of more than 10 KiB is left "
                 "out "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L1941-L1975),"
                 " so the text may be the start of what the register held; a system or user configuration can set "
                 "another value, and the captures' values were not read. Tested on two known captures. "
                 "ubuntu2604_arm64_viminfo is the .viminfo of a virtual machine running Vim 9.1 (patches 1-948, "
                 "950-2141) after four sessions driven by key scripts, and vim_viminfo_known_macos is the viminfo "
                 "file of two such sessions run with the Vim 9.1 (patches 1-1752) that ships with macOS 27.0.1 under "
                 "a scratch home folder. On both, every row's time falls inside the session that made it by the "
                 "recorded start and end of each session, and no time was blank. The virtual machine's clock was "
                 "11,853 seconds behind real time, and the stored times are that clock's. The reading was also "
                 "compared with Vim's own writer: 40 viminfo files that Vim 9.1 on the virtual machine wrote from "
                 "3,200 generated history entries and 320 generated registers (3,737 lines), with quotes, "
                 "backslashes, control characters, multi-byte text and values up to 1,500 characters, which made "
                 "lines as long as 1,683 bytes. The artifact read back every one of the 3,200 entries, each with a "
                 "time, and 317 of the registers as given; the other 3 were empty blockwise registers, which Vim "
                 "wrote with a width of -1 that its own bar-line reader, which takes only digits as a number, does "
                 "not read "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L1106-L1109)."
                 " With the bar lines and version line taken out of the same 40 files, the older lines gave the same "
                 "3,200 entries and all 320 registers, with no time; no file written by a Vim that old was tested. No"
                 " member of ubuntu2604_arm64_triage, honeynet_fc7_debian5, dleapp_macos_bigsur, "
                 "evidencelocker_macos14 or magnet2021_macos_bigsur matches the declared paths. Not read: the last "
                 "search and substitute patterns, the buffer list and global variables a viminfo file can also hold, "
                 "and the files the marks name. Line is the line of the viminfo file a row comes from, and Source "
                 "File the file; the report's located-at line names the files that held a row.",
        "paths": ("*/.viminfo", "*/_viminfo"),
        "output_types": "standard",
        "artifact_icon": "clipboard",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "evidencelocker_macos14": "macOS 14.6.1 build 23G93 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "magnet2021_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_viminfo": "Ubuntu 26.04 LTS aarch64, Vim 9.1.2141 | 5 rows",
            "vim_viminfo_known_macos": "macOS 27.0.1 build 26A434, Vim 9.1.1752 | 4 rows",
        },
    },
    "vimFileMarks": {
        "name": "Vim File Marks and Jumps",
        "description": "File marks and jump list positions saved in Vim's viminfo file: the file each names, the line "
                       "and column, and the time the file stores for each.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-04",
        "last_update_date": "2026-10-04",
        "requirements": "none",
        "category": "Command Line (Vim)",
        "notes": "Reads Vim's viminfo file where Vim keeps it by default: .viminfo in the home folder on Linux and "
                 "macOS and _viminfo on Windows "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/os_unix.h#L299, "
                 "https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/os_mac.h#L158 and "
                 "https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/os_dos.h#L66-L69, all "
                 "at Vim's v9.1.2141 tag); a file named with Vim's -i option or its 'viminfo' option is read only if "
                 "it has one of those names. No Windows file was tested. A file with neither an *encoding= line nor a"
                 " version line is not read and is counted in the run log; the comment lines, which Vim writes in the"
                 " language of its messages "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L3009-L3013),"
                 " are not used. Vim writes each item twice: a line in its older form, and below it a line starting "
                 "with | (a bar line) that also stores a time; a version line, |1 and a number, says which kinds have"
                 " bar lines, from 2 for history, 3 for registers and 4 for file marks "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/vim.h#L1241-L1249), "
                 "and when Vim reads a file back it passes over the older lines of a kind whose bar lines the version"
                 " announces "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L2902-L2934)."
                 " The artifact reads the file the same way: every bar line, and the older lines, which give a blank "
                 "time, only for a kind the version line does not cover. A value too long for a line is continued on "
                 "lines starting with |<, with its length counted in bytes "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L1050-L1055),"
                 " or, in the older lines, put on a following line starting with < "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L147-L149);"
                 " both are read, and text is decoded with the encoding the file's *encoding= line names "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L2887), "
                 "latin-1 when there is none, with bytes that do not decode shown as backslash escapes. Times are "
                 "whole seconds since 1970 as the writing machine's clock gave them, shown in UTC; a stored 0 is "
                 "shown blank. A mark bar line is |4, the mark's character code, the line number, the column, the "
                 "time and the file name "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L2139-L2143)."
                 " Mark is 'A to 'Z for a file mark set with m and a capital letter, '0 to '9 for the numbered marks,"
                 " and Jump for an entry of the jump list, which the file stores under the code of the ' character. "
                 "When Vim writes the file on exit it puts the cursor's position in '0 and moves the earlier numbered"
                 " marks down "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L2179-L2182),"
                 " so '0 is where the cursor was when the last Vim to write the file exited; it also adds the cursor "
                 "position to the jump list "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L2235-L2237)."
                 " Vim sets a lettered mark's time when the mark is set "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/mark.c#L125) and a "
                 "jump's time when the position is recorded "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/mark.c#L206). On "
                 "ubuntu2604_arm64_viminfo the 45 rows are 3 lettered marks, 6 numbered marks and 36 jumps. 'B, 'C "
                 "and 'G are the marks the first, second and fourth sessions set, each with its session's time; 'G "
                 "was set after two 3-second pauses and is timed 6 seconds after that session's start. '0 is the "
                 "position and time at which the fourth session quit, '1 the third session's, '2 and '3 both the "
                 "second session's and '4 and '5 both the first session's. The 36 jump rows hold 11 different "
                 "combinations of file, position and time; the same jump is stored more than once. "
                 "vim_viminfo_known_macos gave 14 rows, 11 of them jumps with 7 different combinations. File is the "
                 "name as stored; on both captures every name began with ~/, the home folder of the account that ran "
                 "Vim. Line Number counts from 1 and Column from 0, as stored. The rows are in the file's order. A "
                 "row shows that the file was open in Vim at that position at that time by the machine's clock; it "
                 "does not show that the file still exists or what it held. Tested on two known captures. "
                 "ubuntu2604_arm64_viminfo is the .viminfo of a virtual machine running Vim 9.1 (patches 1-948, "
                 "950-2141) after four sessions driven by key scripts, and vim_viminfo_known_macos is the viminfo "
                 "file of two such sessions run with the Vim 9.1 (patches 1-1752) that ships with macOS 27.0.1 under "
                 "a scratch home folder. On both, every row's time falls inside the session that made it by the "
                 "recorded start and end of each session, and no time was blank. The virtual machine's clock was "
                 "11,853 seconds behind real time, and the stored times are that clock's. The reading was also "
                 "compared with Vim's own writer: 40 viminfo files that Vim 9.1 on the virtual machine wrote from "
                 "3,200 generated history entries and 320 generated registers (3,737 lines), with quotes, "
                 "backslashes, control characters, multi-byte text and values up to 1,500 characters, which made "
                 "lines as long as 1,683 bytes. The artifact read back every one of the 3,200 entries, each with a "
                 "time, and 317 of the registers as given; the other 3 were empty blockwise registers, which Vim "
                 "wrote with a width of -1 that its own bar-line reader, which takes only digits as a number, does "
                 "not read "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L1106-L1109)."
                 " With the bar lines and version line taken out of the same 40 files, the older lines gave the same "
                 "3,200 entries and all 320 registers, with no time; no file written by a Vim that old was tested. No"
                 " member of ubuntu2604_arm64_triage, honeynet_fc7_debian5, dleapp_macos_bigsur, "
                 "evidencelocker_macos14 or magnet2021_macos_bigsur matches the declared paths. Not read: the last "
                 "search and substitute patterns, the buffer list and global variables a viminfo file can also hold, "
                 "and the files the marks name. Line is the line of the viminfo file a row comes from, and Source "
                 "File the file; the report's located-at line names the files that held a row.",
        "paths": ("*/.viminfo", "*/_viminfo"),
        "output_types": "standard",
        "artifact_icon": "bookmark",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "evidencelocker_macos14": "macOS 14.6.1 build 23G93 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "magnet2021_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_viminfo": "Ubuntu 26.04 LTS aarch64, Vim 9.1.2141 | 45 rows",
            "vim_viminfo_known_macos": "macOS 27.0.1 build 26A434, Vim 9.1.1752 | 14 rows",
        },
    },
    "vimFileHistory": {
        "name": "Vim Marks Within Files",
        "description": "Files for which Vim's viminfo file keeps marks, one row per file: the last-used time the file "
                       "stores and the cursor, insert, change and named mark positions.",
        "author": "@AlexisBrignoni, Claude",
        "creation_date": "2026-10-04",
        "last_update_date": "2026-10-04",
        "requirements": "none",
        "category": "Command Line (Vim)",
        "notes": "Reads Vim's viminfo file where Vim keeps it by default: .viminfo in the home folder on Linux and "
                 "macOS and _viminfo on Windows "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/os_unix.h#L299, "
                 "https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/os_mac.h#L158 and "
                 "https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/os_dos.h#L66-L69, all "
                 "at Vim's v9.1.2141 tag); a file named with Vim's -i option or its 'viminfo' option is read only if "
                 "it has one of those names. No Windows file was tested. A file with neither an *encoding= line nor a"
                 " version line is not read and is counted in the run log; the comment lines, which Vim writes in the"
                 " language of its messages "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L3009-L3013),"
                 " are not used. Vim writes each item twice: a line in its older form, and below it a line starting "
                 "with | (a bar line) that also stores a time; a version line, |1 and a number, says which kinds have"
                 " bar lines, from 2 for history, 3 for registers and 4 for file marks "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/vim.h#L1241-L1249), "
                 "and when Vim reads a file back it passes over the older lines of a kind whose bar lines the version"
                 " announces "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L2902-L2934)."
                 " The artifact reads the file the same way: every bar line, and the older lines, which give a blank "
                 "time, only for a kind the version line does not cover. A value too long for a line is continued on "
                 "lines starting with |<, with its length counted in bytes "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L1050-L1055),"
                 " or, in the older lines, put on a following line starting with < "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L147-L149);"
                 " both are read, and text is decoded with the encoding the file's *encoding= line names "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L2887), "
                 "latin-1 when there is none, with bytes that do not decode shown as backslash escapes. Times are "
                 "whole seconds since 1970 as the writing machine's clock gave them, shown in UTC; a stored 0 is "
                 "shown blank. After its other sections a viminfo file lists files with the marks Vim keeps inside "
                 "each: a line starting with > and the file name, then one line per mark with its character, line "
                 "number and column "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L2037-L2055)."
                 " The artifact gives one row per file. Last Used (UTC) is the number Vim writes as the line number "
                 "of a mark named *, which is the time it last made the file the current buffer "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/buffer.c#L2070); a "
                 "file whose list has no such line gets a blank time. Cursor is the \" mark, the cursor position when "
                 "the file was last left; Last Insert the ^ mark and Last Change the . mark; Change List the + lines,"
                 " oldest first; and Named Marks the marks a to z. Each position is line:column, the line counted "
                 "from 1 and the column from 0, as stored; where a mark is listed more than once the last is shown. "
                 "On ubuntu2604_arm64_viminfo the 2 rows are the two files the sessions edited: beta.txt with the "
                 "time the fourth session quit and the cursor position that capture's '0 mark also holds, and "
                 "alpha.txt with the third session's time, the mark a the first session set at 3:0 and the insert and"
                 " change positions of the line that session appended. vim_viminfo_known_macos gave 2 rows. On both "
                 "captures Last Change and Change List were identical on every row, each file having one change "
                 "position. File is the name as stored; on both captures it began with ~/. The list holds a limited "
                 "number of files, 100 with Vim's built-in 'viminfo' value "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/optiondefs.h#L2879), "
                 "under the file's own heading 'History of marks within files (newest to oldest)', so a file's "
                 "absence is not evidence that it was never opened. A row shows that the file was open in Vim under "
                 "that account and when Vim last made it current by the machine's clock; it does not show that the "
                 "file was changed, that it still exists or what it held. Tested on two known captures. "
                 "ubuntu2604_arm64_viminfo is the .viminfo of a virtual machine running Vim 9.1 (patches 1-948, "
                 "950-2141) after four sessions driven by key scripts, and vim_viminfo_known_macos is the viminfo "
                 "file of two such sessions run with the Vim 9.1 (patches 1-1752) that ships with macOS 27.0.1 under "
                 "a scratch home folder. On both, every row's time falls inside the session that made it by the "
                 "recorded start and end of each session, and no time was blank. The virtual machine's clock was "
                 "11,853 seconds behind real time, and the stored times are that clock's. The reading was also "
                 "compared with Vim's own writer: 40 viminfo files that Vim 9.1 on the virtual machine wrote from "
                 "3,200 generated history entries and 320 generated registers (3,737 lines), with quotes, "
                 "backslashes, control characters, multi-byte text and values up to 1,500 characters, which made "
                 "lines as long as 1,683 bytes. The artifact read back every one of the 3,200 entries, each with a "
                 "time, and 317 of the registers as given; the other 3 were empty blockwise registers, which Vim "
                 "wrote with a width of -1 that its own bar-line reader, which takes only digits as a number, does "
                 "not read "
                 "(https://github.com/vim/vim/blob/60e93b5de7b2ebdf39a84f6d19873ac4d4686a57/src/viminfo.c#L1106-L1109)."
                 " With the bar lines and version line taken out of the same 40 files, the older lines gave the same "
                 "3,200 entries and all 320 registers, with no time; no file written by a Vim that old was tested. No"
                 " member of ubuntu2604_arm64_triage, honeynet_fc7_debian5, dleapp_macos_bigsur, "
                 "evidencelocker_macos14 or magnet2021_macos_bigsur matches the declared paths. Not read: the last "
                 "search and substitute patterns, the buffer list and global variables a viminfo file can also hold, "
                 "and the files the marks name. Line is the line of the viminfo file a row comes from, and Source "
                 "File the file; the report's located-at line names the files that held a row.",
        "paths": ("*/.viminfo", "*/_viminfo"),
        "output_types": "standard",
        "artifact_icon": "file-text",
        "sample_data": {
            "dleapp_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "evidencelocker_macos14": "macOS 14.6.1 build 23G93 | 0 rows (no member matches the declared paths)",
            "honeynet_fc7_debian5": "Debian 5.0.7 i386 | 0 rows (no member matches the declared paths)",
            "magnet2021_macos_bigsur": "macOS 11.2.1 build 20D74 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_triage": "Ubuntu 26.04 LTS aarch64 | 0 rows (no member matches the declared paths)",
            "ubuntu2604_arm64_viminfo": "Ubuntu 26.04 LTS aarch64, Vim 9.1.2141 | 2 rows",
            "vim_viminfo_known_macos": "macOS 27.0.1 build 26A434, Vim 9.1.1752 | 2 rows",
        },
    },
}

import codecs
import os
from collections import Counter
from datetime import datetime, timedelta, timezone

from scripts.ilapfuncs import artifact_processor, logfunc

CTRL_V = b'\x16'
DIGITS = b'0123456789'
HISTORY_KINDS = ('Command line', 'Search', 'Expression', 'Input line', 'Debug line')
OLD_HISTORY = {b':': 'Command line', b'?': 'Search', b'=': 'Expression', b'@': 'Input or debug line'}
REGISTER_TYPES = ('CHAR', 'LINE', 'BLOCK')
JUMP = 39       # the ' character, the name a jump list entry is stored under
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
TIME_MAX = 253402300799     # the last second of year 9999


def utc(seconds):
    """A datetime in UTC for a stored time in seconds, or '' for 0 (no time recorded) or a value out of range."""
    if not seconds or seconds > TIME_MAX:
        return ''
    return EPOCH + timedelta(seconds=seconds)


def register_name(index):
    """The register's character for the number a register bar line stores, as Vim's get_register_name gives it."""
    if 0 <= index < 10:
        return str(index)
    if 10 <= index < 36:
        return chr(ord('a') + index - 10)
    if index == 36:
        return '-'
    return f'(register {index})'


def _digits(text, at):
    """(value, index after it) for the decimal digits at text[at:]; no digits read as 0, as Vim's getdigits does."""
    end = at
    while end < len(text) and text[end:end + 1] in DIGITS:
        end += 1
    return (int(text[at:end]) if end > at else 0), end


class _Lines:
    """The lines of a viminfo file with a cursor, each as bytes without its line end. Vim counts and cuts lines in
    bytes, so a value is put together in bytes and decoded afterwards, in the encoding the file names."""

    def __init__(self, data):
        encoding = 'latin-1'
        self.lines = [raw[:-1] if raw.endswith(b'\r') else raw for raw in data.split(b'\n')]
        for raw in self.lines:
            if raw.startswith(b'*encoding='):
                name = raw[10:].strip().decode('ascii', errors='replace')
                try:
                    codecs.lookup(name)
                    encoding = name
                except LookupError:
                    pass
                break
        self.encoding = encoding
        self.at = 0

    def more(self):
        return self.at < len(self.lines)

    def line(self):
        return self.lines[self.at]

    def text(self, raw):
        return raw.decode(self.encoding, errors='backslashreplace')

    def read_string(self, off):
        """The string that starts at byte `off` of the current line, as viminfo_readstring reads it: a CTRL-V and
        a length mean the text is on the next line after a '<', and CTRL-V n is a line break."""
        raw = self.lines[self.at]
        if raw[off:off + 1] == CTRL_V and raw[off + 1:off + 2] in DIGITS and raw[off + 1:off + 2]:
            self.at += 1
            raw = self.lines[self.at][1:] if self.at < len(self.lines) else b''
        else:
            raw = raw[off:]
        out, i = bytearray(), 0
        while i < len(raw):
            if raw[i:i + 1] == CTRL_V and i + 1 < len(raw):
                out += b'\n' if raw[i + 1:i + 2] == b'n' else CTRL_V
                i += 2
            else:
                out.append(raw[i])
                i += 1
        return self.text(bytes(out))


def bar_values(lines, raw):
    """The values after the type number of a bar line, as barline_parse reads them: ('nr', int), ('str', text) or
    ('empty',). `raw` starts at the first comma. Continuation lines (|<) are taken from `lines`; the last one can
    hold more values after the string, which are read from it in turn."""
    values = []
    p = 0
    while raw[p:p + 1] == b',':
        p += 1
        if raw[p:p + 1] == b'>':
            if raw[p + 1:p + 2] and raw[p + 1:p + 2] in DIGITS:
                todo, _ = _digits(raw, p + 1)
                parts = []
                while todo > 0:
                    lines.at += 1
                    if not lines.more() or not lines.line().startswith(b'|<'):
                        lines.at -= 1
                        return values
                    piece = lines.line()[2:]
                    parts.append(piece)
                    todo -= len(piece)
                raw, p = b''.join(parts), 0
            else:
                lines.at += 1
                if not lines.more() or not lines.line().startswith(b'|<'):
                    lines.at -= 1
                    return values
                raw, p = lines.line()[2:], 0
        ch = raw[p:p + 1]
        if ch and ch in DIGITS:
            number, p = _digits(raw, p)
            values.append(('nr', number))
        elif ch == b'"':
            p += 1
            out = bytearray()
            while raw[p:p + 1] != b'"':
                if p >= len(raw):
                    return values
                if raw[p:p + 1] == b'\\':
                    p += 1
                    out += b'\n' if raw[p:p + 1] == b'n' else raw[p:p + 1]
                    p += 1
                else:
                    out.append(raw[p])
                    p += 1
            p += 1
            values.append(('str', lines.text(bytes(out))))
        elif ch == b',':
            values.append(('empty',))
        else:
            break
    return values


def _is(values, index, kind):
    return index < len(values) and values[index][0] == kind


def viminfo_records(data, counts):
    """What a viminfo file holds, read as Vim reads it: {'history': [(seconds, kind, entry, separator, line)],
    'registers': [(seconds, name, type, width, lines, previous, executed, line)],
    'marks': [(seconds, mark, file, lnum, col, line)], 'files': [(file, {mark: [(lnum, col)]}, line)]}.
    Bar lines are read for every file. The older lines without a time are read only when the file's version
    line is below the version that moved that kind into bar lines, which is when Vim itself reads them. A line
    starting with '<' is the second line of a long value in the older form; like Vim, the loop passes over it."""
    lines = _Lines(data)
    out = {'history': [], 'registers': [], 'marks': [], 'files': [], 'version': 0, 'encoding': lines.encoding}
    version, got_encoding = 0, False
    while lines.more() and not lines.line().startswith(b'>'):
        raw, number = lines.line(), lines.at + 1
        first = raw[:1]
        if first == b'|':
            if raw[1:2] != b'<':
                bartype, end = _digits(raw, 1)
                values = bar_values(lines, raw[end:])
                if bartype == 1:
                    if not got_encoding and _is(values, 0, 'nr'):
                        version = values[0][1]
                elif bartype == 2:
                    _bar_history(values, number, out, counts)
                elif bartype == 3:
                    _bar_register(values, number, out, counts)
                elif bartype == 4:
                    _bar_mark(values, number, out, counts)
                else:
                    counts['bar lines of a type Vim 9.1 does not define, passed over'] += 1
        elif first == b'*':
            got_encoding = True
        elif first == b'"':
            if version < 3:
                _old_register(lines, number, out, counts)
            else:
                while lines.at + 1 < len(lines.lines) and lines.lines[lines.at + 1][:1] in (b'\t', b'<'):
                    lines.at += 1
        elif first in OLD_HISTORY:
            if version < 2:
                separator = ''
                if first == b'?' and len(raw) > 1:
                    # Vim writes the separator, or a space for none, before the pattern
                    separator = '' if raw[1:2] == b' ' else lines.text(raw[1:2])
                    entry = lines.read_string(2)
                else:
                    entry = lines.read_string(1)
                if entry:
                    out['history'].append((0, OLD_HISTORY[first], entry, separator, number))
        elif first in (b'-', b"'"):
            if version < 4:
                _old_mark(lines, number, out)
        lines.at += 1
    out['version'] = version
    while lines.more():
        raw, number = lines.line(), lines.at + 1
        if not raw.startswith(b'>'):
            lines.at += 1
            continue
        off = 1
        while raw[off:off + 1] in (b' ', b'\t') and raw[off:off + 1]:
            off += 1
        name = lines.read_string(off).rstrip()
        marks = {}
        lines.at += 1
        while lines.more() and lines.line().startswith(b'\t'):
            mark_line = lines.text(lines.line())
            if len(mark_line) > 1:
                rest = mark_line[2:].split()
                try:
                    lnum = int(rest[0]) if rest else 0
                    col = int(rest[1]) if len(rest) > 1 else 0
                    marks.setdefault(mark_line[1], []).append((lnum, col))
                except ValueError:
                    counts['mark lines within a file whose numbers do not read, passed over'] += 1
            lines.at += 1
        out['files'].append((name, marks, number))
    return out


def _bar_history(values, number, out, counts):
    if (len(values) < 4 or not _is(values, 0, 'nr') or not _is(values, 1, 'nr')
            or values[2][0] not in ('nr', 'empty') or not _is(values, 3, 'str')
            or values[0][1] >= len(HISTORY_KINDS) or not values[3][1]):
        counts['history bar lines Vim would not accept, not reported'] += 1
        return
    kind = values[0][1]
    separator = chr(values[2][1]) if kind == 1 and values[2][0] == 'nr' and 0 < values[2][1] < 0x110000 else ''
    out['history'].append((values[1][1], HISTORY_KINDS[kind], values[3][1], separator, number))


def _bar_register(values, number, out, counts):
    if len(values) < 6 or not all(_is(values, i, 'nr') for i in range(6)):
        counts['register bar lines Vim would not accept, not reported'] += 1
        return
    flags, index, kind, count, width, seconds = (values[i][1] for i in range(6))
    if kind > 2 or len(values) < 6 + count or not all(_is(values, 6 + i, 'str') for i in range(count)):
        counts['register bar lines Vim would not accept, not reported'] += 1
        return
    text = [values[6 + i][1] for i in range(count)]
    out['registers'].append((seconds, register_name(index), REGISTER_TYPES[kind], width, text,
                             bool(flags & 1), bool(flags & 2), number))


def _bar_mark(values, number, out, counts):
    if len(values) < 5 or not all(_is(values, i, 'nr') for i in range(4)) or not _is(values, 4, 'str'):
        counts['mark bar lines Vim would not accept, not reported'] += 1
        return
    name, lnum, col, seconds = (values[i][1] for i in range(4))
    letter = chr(name) if 0 < name < 128 else ''
    if not (name == JUMP or letter.isdigit() or ('A' <= letter <= 'Z')) or lnum <= 0:
        counts['mark bar lines Vim would not accept, not reported'] += 1
        return
    out['marks'].append((seconds, 'Jump' if name == JUMP else "'" + letter, values[4][1], lnum, col, number))


def _old_register(lines, number, out, counts):
    text = lines.text(lines.line())
    at = 1
    previous = text[at:at + 1] == '"'
    if previous:
        at += 1
    name = text[at:at + 1]
    if not (name.isascii() and (name.isalnum() or name == '-')):
        counts['register lines with a name Vim would not accept, not reported'] += 1
        name = ''
    at += 1
    executed = text[at:at + 1] == '@'
    fields = text[at + 1 if executed else at:].split()
    kind = ('CHAR' if fields and fields[0].startswith('CHAR')
            else 'BLOCK' if fields and fields[0].startswith('BLOCK') else 'LINE')
    width = _digits(fields[1].encode('ascii', errors='replace'), 0)[0] if len(fields) > 1 else 0
    content = []
    while lines.at + 1 < len(lines.lines) and lines.lines[lines.at + 1][:1] in (b'\t', b'<'):
        lines.at += 1
        if lines.line().startswith(b'\t'):
            content.append(lines.read_string(1))
    if name:
        out['registers'].append((0, name, kind, width, content, previous, executed, number))


def _old_mark(lines, number, out):
    raw = lines.line()
    second = raw[1:2]
    if raw[:1] == b"'" and second and (second in DIGITS or b'A' <= second <= b'Z'):
        mark = "'" + second.decode('ascii')
    elif raw[:1] == b'-' and second == b"'":
        mark = 'Jump'
    else:
        return
    at = 2
    numbers = []
    for _ in range(2):
        while raw[at:at + 1] in (b' ', b'\t') and raw[at:at + 1]:
            at += 1
        value, at = _digits(raw, at)
        numbers.append(value)
    while raw[at:at + 1] in (b' ', b'\t') and raw[at:at + 1]:
        at += 1
    out['marks'].append((0, mark, lines.read_string(at), numbers[0], numbers[1], number))


def _read(context, name, problems):
    """[(path, records)] for each viminfo file found, in path order."""
    out = []
    for path in sorted(str(p) for p in context.get_files_found() if not os.path.isdir(p)):
        try:
            with open(path, 'rb') as handle:
                data = handle.read()
        except OSError:
            problems['files that could not be read'] += 1
            continue
        if not any(line.startswith((b'*encoding=', b'|1,')) for line in data.split(b'\n')):
            problems['files with neither an *encoding= line nor a version line, not read'] += 1
            continue
        out.append((path, viminfo_records(data, problems)))
    if problems:
        logfunc(f'{name}: ' + ', '.join(f'{count} {kind}' for kind, count in sorted(problems.items())))
    return out


@artifact_processor
def vimHistory(context):
    data_headers = (('Time (UTC)', 'datetime'), 'History', 'Entry', 'Search Separator', 'Line', 'Source File')
    data_list, read = [], []
    for path, records in _read(context, 'Vim History', Counter()):
        relative = context.get_relative_path(path)
        data_list.extend((utc(seconds), kind, entry, separator, number, relative)
                         for seconds, kind, entry, separator, number in records['history'])
        if records['history']:
            read.append(path)
    return data_headers, data_list, '\n'.join(read)


@artifact_processor
def vimRegisters(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Register', 'Type', 'Text', 'Lines', 'Block Width', 'Unnamed Register',
                    'Last Executed', 'Line', 'Source File')
    data_list, read = [], []
    for path, records in _read(context, 'Vim Registers', Counter()):
        relative = context.get_relative_path(path)
        data_list.extend((utc(seconds), name, kind, '\n'.join(text), len(text), width, 'Yes' if previous else '',
                          'Yes' if executed else '', number, relative)
                         for seconds, name, kind, width, text, previous, executed, number in records['registers'])
        if records['registers']:
            read.append(path)
    return data_headers, data_list, '\n'.join(read)


@artifact_processor
def vimFileMarks(context):
    data_headers = (('Time (UTC)', 'datetime'), 'Mark', 'File', 'Line Number', 'Column', 'Line', 'Source File')
    data_list, read = [], []
    for path, records in _read(context, 'Vim File Marks and Jumps', Counter()):
        relative = context.get_relative_path(path)
        data_list.extend((utc(seconds), mark, name, lnum, col, number, relative)
                         for seconds, mark, name, lnum, col, number in records['marks'])
        if records['marks']:
            read.append(path)
    return data_headers, data_list, '\n'.join(read)


def _position(marks, letter):
    found = marks.get(letter)
    return f'{found[-1][0]}:{found[-1][1]}' if found else ''


@artifact_processor
def vimFileHistory(context):
    data_headers = (('Last Used (UTC)', 'datetime'), 'File', 'Cursor', 'Last Insert', 'Last Change', 'Change List',
                    'Named Marks', 'Line', 'Source File')
    data_list, read = [], []
    for path, records in _read(context, 'Vim Marks Within Files', Counter()):
        relative = context.get_relative_path(path)
        for name, marks, number in records['files']:
            used = marks.get('*')
            named = '; '.join(f'{letter} {lnum}:{col}' for letter in sorted(marks) if 'a' <= letter <= 'z'
                              for lnum, col in marks[letter][-1:])
            changes = '; '.join(f'{lnum}:{col}' for lnum, col in marks.get('+', []))
            data_list.append((utc(used[-1][0]) if used else '', name, _position(marks, '"'), _position(marks, '^'),
                              _position(marks, '.'), changes, named, number, relative))
        if records['files']:
            read.append(path)
    return data_headers, data_list, '\n'.join(read)
