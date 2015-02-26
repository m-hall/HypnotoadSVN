import sublime, sublime_plugin

SETTINGS_FILE = "HypnotoadSVN.sublime-settings"
GLOBAL_PREFERENCES = "Preferences.sublime-settings"
LISTENER_PREFIX = 'HypnotoadSVN-'

class Settings:
    plugin = None
    preferences = None
    def load():
        Settings.plugin = sublime.load_settings(SETTINGS_FILE)
        Settings.preferences = sublime.load_settings(GLOBAL_PREFERENCES)

    def get(name, type=None, default=None):
        if not Settings.plugin or not Settings.preferences:
            Settings.load()
        if type is not None:
            return Settings.plugin.get(type, {}).get(name, default)
        return Settings.plugin.get(name, default)

    def listen_changes(name, observer):
        if not Settings.plugin or not Settings.preferences:
            Settings.load()
        Settings.unlisten_changes(name)
        Settings.preferences.add_on_change(LISTENER_PREFIX + name, observer)
        Settings.plugin.add_on_change(LISTENER_PREFIX + name, observer)

    def unlisten_changes(name):
        if not Settings.plugin or not Settings.preferences:
            Settings.load()
        Settings.preferences.clear_on_change(LISTENER_PREFIX + name)
        Settings.plugin.clear_on_change(LISTENER_PREFIX + name)

def listen_to_changes(name, observer):
    Settings.listen_changes(name, observer)

def unlisten_to_changes(name):
    Settings.unlisten_changes(name)

def get(name, svn_type=None, default=None):
    return Settings.get(name, svn_type, default)

def get_native(name, default=None):
    return Settings.get(name, 'nativeSVN', default)

def get_tortoise(name, default=None):
    return Settings.get(name, 'tortoiseSVN', default)

def get_tortoise_path():
    return Settings.get("tortoiseproc_path", "tortoiseSVN", "C:\\Program Files\\TortoiseSVN\\bin\\TortoiseProc.exe")