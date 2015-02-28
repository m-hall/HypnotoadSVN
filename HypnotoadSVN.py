import sublime
import sublime_plugin
import os
from .lib import menu

def plugin_loaded():
    """Handles the plugin loaded event"""
    menu.create_user_side_bar()
