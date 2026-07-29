"""Windows-specific presentations of Roblox's cross-platform artifacts.

The parser implementations remain shared with the macOS artifacts, while these
Windows-only entry points give DLEAPP accurate platform categories and paths.

Author: @AlexisBrignoni, Codex
"""

from scripts.artifacts.robloxAccount import robloxAccount as _roblox_account
from scripts.artifacts.robloxActivity import (
    robloxNotifications as _roblox_notifications,
    robloxPresence as _roblox_presence,
)
from scripts.artifacts.robloxLogs import (
    robloxGameJoins as _roblox_game_joins,
)
from scripts.ilapfuncs import artifact_processor


def _windows_artifact(parser, paths, sample_description):
    original = parser.__wrapped__
    source = original.__globals__["__artifacts_v2__"][original.__name__]
    metadata = dict(source)
    metadata["name"] = source["name"].replace("Roblox ", "Roblox Windows ", 1)
    metadata["category"] = "Roblox (Windows)"
    metadata["paths"] = paths
    metadata["sample_data"] = {"roblox_windows": sample_description}
    return metadata


_LOCAL_ROBLOX = "*/AppData/Local/Roblox/"
_WEBVIEW2 = _LOCAL_ROBLOX + "UniversalApp/WebView2/EBWebView/Default/"

__artifacts_v2__ = {
    "robloxWindowsPresence": _windows_artifact(
        _roblox_presence,
        (_WEBVIEW2 + "Local Storage/leveldb/*",),
        "Roblox 0.732.23.7321040 Windows | 5 rows",
    ),
    "robloxWindowsNotifications": _windows_artifact(
        _roblox_notifications,
        (_WEBVIEW2 + "Local Storage/leveldb/*",),
        "Roblox 0.732.23.7321040 Windows | 1 row",
    ),
    "robloxWindowsGameJoins": _windows_artifact(
        _roblox_game_joins,
        (_LOCAL_ROBLOX + "logs/*_Player_*.log",),
        "Roblox 0.732.23.7321040 Windows | 2 rows",
    ),
    "robloxWindowsAccount": _windows_artifact(
        _roblox_account,
        (
            _LOCAL_ROBLOX + "LocalStorage/appStorage.json",
            _LOCAL_ROBLOX + "AnalysticsSettings.xml",
        ),
        "Roblox 0.732.23.7321040 Windows | 22 rows",
    ),
}


@artifact_processor
def robloxWindowsPresence(context):
    return _roblox_presence.__wrapped__(context)


@artifact_processor
def robloxWindowsNotifications(context):
    return _roblox_notifications.__wrapped__(context)


@artifact_processor
def robloxWindowsGameJoins(context):
    return _roblox_game_joins.__wrapped__(context)


@artifact_processor
def robloxWindowsAccount(context):
    return _roblox_account.__wrapped__(context)
