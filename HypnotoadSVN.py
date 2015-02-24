import sublime
import sublime_plugin
import os
from .lib import util

def plugin_loaded():
    util.generate_color_scheme()
