import sublime
import os
import re
from . import settings

URL_TEST = r"https?:\/\/.*"

def get_files(paths=None, group=-1, index=-1, base=None):
    """Get a list of files based on command input"""
    if base is None:
        base = settings.get('commandBaseFiles', default='project')
    files = []
    if isinstance(paths, list):
        files = files+paths
    if group >= 0 and index >= 0:
        view = sublime.active_window().views_in_group(group)[index]
        files.append(view.file_name())
    if len(files) == 0:
        if base == 'current':
            view = sublime.active_window().active_view()
            file_name = view.file_name()
            if file_name is not None and os.path.exists(file_name):
                files.append(file_name)
        elif base == 'project':
            folders = sublime.active_window().folders()
            return folders
        elif isinstance(base, list):
            for b in base:
                b = os.path.expanduser(b)
                if os.path.exists(b):
                    files.append(b)
        elif os.path.exists(os.path.expanduser(base)):
            files.append(os.path.expanduser(base))
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
        """In Windows, Check if TortoiseSVN support is enabled"""
        if settings.get_tortoise('disable') is not True:
            proc_path = settings.get_tortoise('tortoiseproc_path')
            if os.path.isfile(proc_path):
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
        command = "default"
    return use_tortoise() and prefers.get(command) == 'tortoiseSVN'

def tortoise_path(paths):
    """Join paths for a TortoiseProc command"""
    return "*".join(paths)

def debug(message):
    """Send output to console if debugging is enabled"""
    if settings.get("debug", default=False):
        print('HypnotoadSVN: ' + str(message))


def is_url(url):
    return re.match(URL_TEST, url) is not None