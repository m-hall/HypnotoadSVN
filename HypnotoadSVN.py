import sublime
import sublime_plugin
import os
from .lib import color_scheme, menu

def plugin_loaded():
    """Handles the plugin loaded event"""
    color_scheme.generate()
    color_scheme.add_listener()
    menu.create_user_side_bar()
