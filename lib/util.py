import sublime, sublime_plugin
import re
import os
from . import settings

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
    """Get a list of files based on command input"""
    files = []
    if isinstance(paths, list):
        files = files+paths
    if group >=0 and index >= 0:
        view = sublime.active_window().views_in_group(group)[index]
        files.append(view.file_name())
    if len(files) == 0:
        view = sublime.active_window().active_view()
        file_name = view.file_name()
        if file_name is not None and os.path.exists(file_name):
            files.append(file_name)
    return files

def enabled():
    """Check if the plugin is enabled"""
    return use_native() or use_tortoise()

def use_native():
    """Check if native SVN support is enabled"""
    if settings.get_native('disable') is not True:
        return True
    return False

if os.name == 'nt':
    def use_tortoise():
        """In Widnows, Check if TortoiseSVN support is enabled"""
        if settings.get_tortoise('disable') is not True:
            tortoise_path = settings.get_tortoise('tortoiseproc_path');
            if os.path.isfile(tortoise_path):
                return True
        return False
else:
    def use_tortoise():
        """Not in Windows, TortoiseSVN is not available"""
        return False


def prefer_tortoise(command="Default"):
    """Check if TortoiseSVN is preferred over native SVN"""
    if not use_native():
        return use_tortoise()
    prefers = settings.get('prefer')
    if isinstance(prefers, str):
        return use_tortoise and prefers == 'tortoiseSVN'
    if command not in prefers.keys():
        command = "Default"
    return use_tortoise() and prefers.get(command) == 'tortoiseSVN'

def tortoise_path(paths):
    """Join paths for a TortoiseProc command"""
    return "*".join(paths)

def debug(message):
    """Send output to console if debugging is enabled"""
    if (settings.get("debug", default=False)):
        print('HypnotoadSVN: ' + message)
