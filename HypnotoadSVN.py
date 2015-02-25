import sublime
import sublime_plugin
import os
from .lib import color_scheme

def plugin_loaded():
    color_scheme.generate()
    color_scheme.add_listener()
