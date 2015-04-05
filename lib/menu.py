import sublime
import os

DEFAULT_SIDE_BAR_RESOURCE = "Packages/HypnotoadSVN/menus/Default Side Bar.sublime-menu"
USER_SIDE_BAR_FILE = "Side Bar.sublime-menu"


def create_user_side_bar():
    """Create the sidebar config in the user directory"""
    user_folder = os.path.join(sublime.packages_path(), 'User', 'HypnotoadSVN')
    user_file = os.path.join(user_folder, USER_SIDE_BAR_FILE)
    if os.path.exists(user_file):
        return
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    side_bar_contents = sublime.load_resource(DEFAULT_SIDE_BAR_RESOURCE)
    with open(user_file, 'w', encoding='utf8') as f:
        f.write(side_bar_contents)


def remove_user_side_bar():
    """Remove the sidebar config in the user directory"""
    user_folder = os.path.join(sublime.packages_path(), 'User', 'HypnotoadSVN')
    if os.path.exists(user_folder):
        os.remove(os.path.join(user_folder, USER_SIDE_BAR_FILE))
    if not os.listdir(user_folder): # folder is empty
        os.rmdir(user_folder)
