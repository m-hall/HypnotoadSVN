from .lib import menu


def plugin_loaded():
    """Handles the plugin loaded event"""
    menu.create_user_side_bar()


def plugin_unloaded():
    """Handles the plugin unloaded event"""
    menu.remove_user_side_bar()
