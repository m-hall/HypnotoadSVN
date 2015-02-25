import sublime
import sublime_plugin
import re
from . import util

VIEW_NAME = 'SVN Output'
PANEL_ID = 'svn-output'
SYNTAX = 'Packages/HypnotoadSVN/languages/SVN Output.tmLanguage'

class SvnView(sublime_plugin.EventListener):
    buffer = ""
    view = None
    panel = None
    def get():
        output = util.get_setting("outputTo")
        if output == "dialog":
            return None
        if output == "tab":
            if SvnView.view is None or SvnView.view.window() is None:
                view = sublime.active_window().new_file()
                view.set_scratch(True)
                view.set_name(VIEW_NAME)
                view.set_syntax_file(SYNTAX)
                view.set_read_only(True)
                SvnView.view = view
            return SvnView.view
        if SvnView.panel is None:
            panel = sublime.active_window().create_output_panel(PANEL_ID)
            panel.set_syntax_file(SYNTAX)
            SvnView.panel = panel
            sublime.active_window().run_command(
                'show_panel',
                {
                    'panel': 'output.'+PANEL_ID
                }
            )
            return SvnView.panel
    def message(message):
        output = util.get_setting("outputTo")
        if output == "dialog":
            SvnView.buffer = SvnView.buffer + message + "\n"
            return
        view = SvnView.get()
        if view is None:
            return
        view.run_command(
            'svn_view_message',
            {
                "message": message
            }
        );
    def end():
        output = util.get_setting("outputTo")
        if output == "dialog":
            sublime.message_dialog(SvnView.buffer)
        SvnView.buffer = ""
    def focus():
        view = SvnView.get()
        if view is None:
            return
        view.window().focus_view(view)
    def scroll_to_bottom():
        view = SvnView.get()
        if view is None:
            return
        point = view.text_to_layout(view.size())
        view.set_viewport_position(point, True)
    def on_close(self, view):
        if view == SvnView.view:
            SvnView.view = None
        if view == SvnPanel:
            SvnView.panel = None


def indent(text="", spaces=4):
    return " " * spaces + re.sub(r'\n', '\n' + " " * spaces, text)

def add_message(message):
    SvnView.message(message)

def add_command(name):
    SvnView.focus()
    SvnView.scroll_to_bottom()
    add_message("Command: " + name)

def add_files(paths=None):
    if paths is None:
        return
    s = paths
    if isinstance(paths, list):
        s = "\n".join(paths)
    add_message("Files:\n" + indent(s))

def add_result(result):
    if result:
        add_message("Output:\n" + indent(result))

def add_error(err):
    if err:
        add_message("Error:\n" + indent(err))

def end_command():
    SvnView.end()