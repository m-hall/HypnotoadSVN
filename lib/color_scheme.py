import sublime, sublime_plugin
import re
import os
from xml.etree import ElementTree
from . import util

LISTENER_NAME='color-scheme'
LANGUAGE = 'svn-output'
GREEN = '#A6E22E'
BLUE = '#66D9EF'
PURPLE = '#AE81FF'
RED = '#F92672'
ORANGE = '#FD971F'
YELLOW = '#FFE792'
WHITE = '#F8F8F0'
STYLE = '''
            <key>{key}</key>
            <string>{value}</string>
'''
COLOR_SCHEME = '''
    <dict>
        <key>name</key>
        <string>Hypnotoad {name}</string>
        <key>scope</key>
        <string>{selector}.{language}</string>
        <key>settings</key>
        <dict>
{styles}
        </dict>
    </dict>
'''
THEME_XML_DEFINITION = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
'''
SCHEMES = [
    ("Scopes", "keyword.control", [("foreground", RED)]),
    ("Command Name", "string.meta.command", []),
    ("Status", "keyword.status", [("foreground", GREEN)]),
    ("Add", "keyword.status.add", [("foreground", GREEN)]),
    ("Delete", "keyword.status.delete", [("foreground", PURPLE)]),
    ("Merge", "keyword.status.merge", [("foreground", BLUE)]),
    ("Update", "keyword.status.update", [("foreground", BLUE)]),
    ("Unversionned", "keyword.status.unversionned", []),
    ("Missing", "keyword.status.missing", [("foreground", ORANGE)]),
    ("Conflicted", "keyword.status.conflicted", [("background", RED), ("foreground", WHITE)]),
    ("Path", "string.path", []),
    ("Error Path", "string.error.path", [("foreground", RED)])
]

def generate():
    #settings.unlisten_to_changes(LISTENER_NAME)
    sublime.set_timeout_async(generate_async, 0)
    #settings.listen_to_changes(LISTENER_NAME, generate)

def generate_async():
    """
    Generate a modified copy of the current color scheme that contains SublimeLinter color entries.
    The current color scheme is checked for SublimeLinter color entries. If any are missing,
    the scheme is copied, the entries are added, and the color scheme is rewritten to Packages/User/SublimeLinter.
    """

    # First make sure the user prefs are valid. If not, bail.
    path = os.path.join(sublime.packages_path(), 'User', 'Preferences.sublime-settings')

    if (os.path.isfile(path)):
        try:
            with open(path, mode='r', encoding='utf-8') as f:
                json = f.read()

            sublime.decode_value(json)
        except:
            error_message('Could not modify color scheme, User Preferences is missing or invalid')
            return

    prefs = sublime.load_settings('Preferences.sublime-settings')
    scheme = prefs.get('color_scheme')

    if scheme is None:
        return

    scheme_text = sublime.load_resource(scheme)

    if 'hypnotoad' in scheme_text:
        return

    # Append style dicts with our styles to the style array
    plist = ElementTree.XML(scheme_text)
    styles = plist.find('./dict/array')
    base_scheme = COLOR_SCHEME.replace('{language}', LANGUAGE)
    for name, selector, schemes in SCHEMES:
        if len(schemes) < 1:
            continue
        style = ''
        for key, value in schemes:
            style = style + STYLE.replace('{key}', key).replace('{value}', value)
        definition = base_scheme
        definition = definition.replace('{name}', name)
        definition = definition.replace('{selector}', selector)
        definition = definition.replace('{styles}', style)
        styles.append(ElementTree.XML(definition))

    if not os.path.exists(os.path.join(sublime.packages_path(), 'User', 'HypnotoadSVN')):
        os.makedirs(os.path.join(sublime.packages_path(), 'User', 'HypnotoadSVN'))

    # Write the amended color scheme to Packages/User/HypnotoadSVN
    original_name = os.path.splitext(os.path.basename(scheme))[0]
    name = original_name
    scheme_path = os.path.join(sublime.packages_path(), 'User', 'HypnotoadSVN', name + '.tmTheme')

    with open(scheme_path, 'w', encoding='utf8') as f:
        f.write(THEME_XML_DEFINITION)
        f.write(ElementTree.tostring(plist, encoding='unicode'))

    # Set the amended color scheme to the current color scheme
    path = os.path.join('User', 'HypnotoadSVN', os.path.basename(scheme_path))
    components = util.get_path_components(path)
    if components and components[0] != 'Packages':
        components.insert(0, 'Packages')
    path = '/'.join(components)
    prefs.set('color_scheme', path)
    sublime.save_settings('Preferences.sublime-settings')