from .lib import menu
from package_control import events

HYPNOTOADSVN_PKGNAME = "HypnotoadSVN"


def plugin_loaded():
    """Handles the plugin loaded event"""
    menu.create_user_side_bar()


def plugin_unloaded():
    """Handles the plugin unloaded event"""
    if events.remove(HYPNOTOADSVN_PKGNAME) is not False:
        menu.remove_user_side_bar()
