import sublime
import sublime_plugin
import os
import json

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

        plugin = Settings.plugin
        project = sublime.active_window().project_data() or {}
        project = project.get('HypnotoadSVN', {})
        if type is not None:
            project_value = project.get(type, {}).get(name, None)
            if project_value is not None:
                return project_value
            return plugin.get(type, {}).get(name, default)
        project_value = project.get(name, None)
        if project_value is not None:
            return project_value
        return plugin.get(name, default)


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
