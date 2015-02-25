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

def use_native():
    if settings.get_native('disable') is not True:
        return True
    return False

def use_tortoise():
    if os.name == 'nt' and settings.get_tortoise('disable') is not True:
        tortoise_path = settings.get_tortoise('tortoiseproc_path');
        if os.path.isfile(tortoise_path):
            return True
    return False

def prefer_tortoise():
    return use_tortoise() and settings.get('prefer') == 'tortoiseSVN'

def tortoise_path(paths):
    return "*".join(paths)