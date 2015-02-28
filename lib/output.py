import sublime
import sublime_plugin
import re
from . import util, settings

VIEW_NAME = 'SVN Output'
PANEL_ID = 'svn-output'
SYNTAX = 'Packages/HypnotoadSVN/languages/SVN Output.tmLanguage'

class SvnView(sublime_plugin.EventListener):
    """Handles the SVN Output view/panel"""
    buffer = ""
    view = None
    panel = None
    def find_existing_view():
        """Finds a view that matches the signature of an SVN Output view"""
        if SvnView.view:
            return SvnView.view
        views = sublime.active_window().views()
        for view in views:
            if (
                view.name() == VIEW_NAME
                and view.is_read_only()
                and view.is_scratch()
            ):
                return view
        return None
    def get():
        """Gets a view or panel for output"""
        output = settings.get_native("outputTo", "panel")
        if output == "dialog":
            return None
        if output == "tab":
            if SvnView.view is None or SvnView.view.window() is None:
                view = SvnView.find_existing_view()
                if view is None:
                    view = sublime.active_window().new_file()
                    view.set_scratch(True)
                    view.set_name(VIEW_NAME)
                    view.set_read_only(True)
                view.set_syntax_file(SYNTAX)
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
        """Sends a message to the output"""
        output = settings.get_native("outputTo", "panel")
        if output == "dialog":
            SvnView.buffer = SvnView.buffer + message + "\n"
            return
        view = SvnView.get()
        if view is None:
            return
        msg = re.sub(r'\r\n?', '\n', message)
        view.run_command(
            'hypno_view_message',
            {
                "message": msg
            }
        );
    def clear():
        """Clears the output view"""
        view = SvnView.get()
        if view is None:
            return
        view.run_command('hypno_view_clear');

    def end():
        """Sends the end signal to the output"""
        output = settings.get_native("outputTo", "panel")
        if output == "dialog":
            sublime.message_dialog(SvnView.buffer)
        SvnView.buffer = ""
        SvnView.message("Completed\n")
    def focus():
        """Brings the output view into focus"""
        view = SvnView.get()
        if view is None:
            return
        view.window().focus_view(view)
    def scroll_to_bottom():
        """Scrolls the output view to the bottom of the view"""
        view = SvnView.get()
        if view is None:
            return
        point = view.text_to_layout(view.size())
        view.set_viewport_position(point, True)
    def on_close(self, view):
        """Stop using the view if it has been closed"""
        if view == SvnView.view:
            SvnView.view = None
        if view == SvnView.panel:
            SvnView.panel = None


def indent(text="", spaces=4):
    """Indents a message for output"""
    return " " * spaces + re.sub(r'\n', '\n' + " " * spaces, text)

def add_message(message):
    """Add a message to output"""
    SvnView.message(message)

def add_command(name):
    """Adds a named command to output"""
    SvnView.focus()
    SvnView.scroll_to_bottom()
    add_message("Command: " + name)

def add_files(paths=None):
    """Add a list of files to output"""
    if paths is None:
        return
    s = paths
    if isinstance(paths, list):
        s = "\n".join(paths)
    add_message("Files:\n" + indent(s))

def add_files_section():
    """Adds a files section to output"""
    add_message("Files:")

def add_result(result):
    """Adds results to output"""
    if result:
        add_message("Output:\n" + indent(result))

def add_result_section():
    """Opens a result section in output"""
    add_message("Output:")

def add_result_message(result):
    """Adds a result message to output"""
    add_message(indent(result))

def add_error(err, code=None):
    """Adds errors to output"""
    if err:
        add_message("Error: " + str(code if code is not None else "") + "\n" + indent(err))

def add_error_section(code = None):
    """Opens an error section in output"""
    add_message("Error: " + str(code if code is not None else ""))

def end_command():
    """Ends a command in output"""
    SvnView.end()

def clear():
    """Clears the output view"""
    SvnView.clear()