"""Replay of registry transaction logs onto a dirty hive, for DLEAPP.

The replay is the vendored regfprobe's (scripts/vendor/regfprobe.py, from
https://github.com/abrignoni/regfprobe; scripts/vendor/vendored.json records the commit).
This file was its source. regfprobe holds the same functions; two of them (xor32, base_block)
wrap a slice in bytes() so regfprobe can pass a memoryview, and recover's docstring is longer.
DLEAPP now uses that copy so there is one to maintain.

recover is what scripts/windows_registry.py calls; base_block, marvin32, recover and xor32 are
what the tests call.

recover(primary, logs) applies a dirty hive's .LOG1 and .LOG2 entries, in the format Windows 8.1
and later write (entries signed HvLE, checked with Marvin32) or, when none of those applies, the
older format (a dirty vector signed DIRT). It refuses a replay that would give a key an earlier
last-written time than the hive holds. The SYSTEM hive of pc_mus_001_win11 had logs like that:
applying them, as the specification's rules allow, set three keys, one of them a BAM key, back by
14 to 15 minutes and moved no key forward. See regfprobe's recover() docstring for the
description and regfprobe's module docstring for its sources.

Author: @AlexisBrignoni, Claude.
"""

from scripts.vendor.regfprobe import (  # noqa: F401  pylint: disable=unused-import
    base_block,
    marvin32,
    recover,
    xor32,
)
