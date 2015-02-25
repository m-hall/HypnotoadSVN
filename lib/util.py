import sublime, sublime_plugin
import re
import os

SETTINGS_FILE = "HypnotoadSVN.sublime-settings"
GLOBAL_PREFERENCES = "Preferences.sublime-settings"
LISTENER_PREFIX = 'HypnotoadSVN-'

preferences = sublime.load_settings(GLOBAL_PREFERENCES)

def add_preferences_listener(name, observer):
    remove_preferences_listener(name)
    preferences.add_on_change(LISTENER_PREFIX + name, observer)

def remove_preferences_listener(name):
    preferences.clear_on_change(LISTENER_PREFIX + name)

def get_setting(name):
    settings = sublime.load_settings(SETTINGS_FILE)
    return settings.get(name)

def get_path_components(path):
    """Split a file path into its components and return the list of components."""
    components = []

    while path:
        head, tail = os.path.split(path)

        if tail:
            components.insert(0, tail)

        if head:
            if head == os.path.sep or head == os.path.altsep:
                components.insert(0, head)
                break

            path = head
        else:
            break

    return components

def get_files(paths=None, group=-1, index=-1):
    files = []
    if isinstance(paths, list):
        files = files+paths
    if group >=0 and index >= 0:
        view = sublime.active_window().views_in_group(group)[index]
        files.append(view.file_name())
    if len(files) == 0:
        view = sublime.active_window().active_view()
        if os.path.exists(view.file_name()):
            files.append(view.file_name())
    return files

def use_tortoise():
    if os.name == 'nt' and get_setting('useTortoise'):
        tortoise_path = get_setting('tortoiseproc_path');
        if os.path.isfile(tortoise_path):
            return True
    return False

def always_tortoise():
    return get_setting('always_tortoise') and use_tortoise()

def tortoise_path(paths):
    return "*".join(paths)