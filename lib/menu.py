import sublime
import os

DEFAULT_SIDE_BAR_FILE = "Packages/HypnotoadSVN/menus/Default Side Bar.sublime-menu"
USER_SIDE_BAR_FILE = "/User/HypnotoadSVN/Side Bar.sublime-menu"


def create_user_side_bar():
    """Create the sidebar config in the user directory"""
    if os.path.exists(USER_SIDE_BAR_FILE):
        return
    if not os.path.exists(os.path.join(sublime.packages_path(), 'User', 'HypnotoadSVN')):
        os.makedirs(os.path.join(sublime.packages_path(), 'User', 'HypnotoadSVN'))

    side_bar_contents = sublime.load_resource(DEFAULT_SIDE_BAR_FILE)

    with open(sublime.packages_path() + USER_SIDE_BAR_FILE, 'w', encoding='utf8') as f:
        f.write(side_bar_contents)


def remove_user_side_bar():
    """Remove the sidebar config in the user directory"""
    if os.path.exists(os.path.join(sublime.packages_path(), 'User', 'HypnotoadSVN')):
        os.remove(sublime.packages_path() + USER_SIDE_BAR_FILE)
        os.rmdir(os.path.join(sublime.packages_path(), 'User', 'HypnotoadSVN'))
