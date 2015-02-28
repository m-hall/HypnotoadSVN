import sublime, sublime_plugin

SETTINGS_FILE = "HypnotoadSVN.sublime-settings"
GLOBAL_PREFERENCES = "Preferences.sublime-settings"
LISTENER_PREFIX = 'HypnotoadSVN-'

class Settings:
    """Interface for communicating with settings"""
    plugin = None
    def load():
        """Loads the settings for the plugin"""
        Settings.plugin = sublime.load_settings(SETTINGS_FILE)

    def get(name, type=None, default=None):
        """Gets a value from the plugin settings"""
        if not Settings.plugin:
            Settings.load()
        if type is not None:
            return Settings.plugin.get(type, {}).get(name, default)
        return Settings.plugin.get(name, default)

def get(name, svn_type=None, default=None):
    """Gets a value from settings"""
    return Settings.get(name, svn_type, default)

def get_native(name, default=None):
    """Gets a value from the native section of settings"""
    return Settings.get(name, 'nativeSVN', default)

def get_tortoise(name, default=None):
    """Gets a value from the tortoise section of settings"""
    return Settings.get(name, 'tortoiseSVN', default)

def get_tortoise_path():
    """Gets the path to TortoiseProc"""
    return Settings.get("tortoiseproc_path", "tortoiseSVN", "C:\\Program Files\\TortoiseSVN\\bin\\TortoiseProc.exe")