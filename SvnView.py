import sublime
import sublime_plugin
import re

class SvnView:
    view = None
    def get():
        if not SvnView.view:
            view = sublime.active_window().new_file()
            view.set_scratch(True)
            view.set_name('SVN Output')
            view.set_read_only(True)
            view.set_syntax_file('Packages/Hypnotoad/SVNOutput.tmLanguage')
            SvnView.view = view
        return SvnView.view

class SvnMessageCommand(sublime_plugin.TextCommand):
    def run(self, edit, message=""):
        self.view.insert(edit, self.view.size(), message)

class SvnViewEvents(sublime_plugin.EventListener):
    def on_close(self, view):
        if view == view:
            view = None



def add_message(message):
    view = SvnView.get()
    view.set_read_only(False)
    view.run_command(
        'svn_message',
        {
            "message": message
        }
    );
    view.set_read_only(True)

def add_command(name, args=None):
    view = SvnView.get()
    view.window().focus_view(view)
    point = view.text_to_layout(view.size() - 1)
    add_message("Command: " + name + "\n")
    if args is not None:
        for arg in args:
            add_message("    " + arg + "\n")
    view.set_viewport_position(point, True)

def add_result(result):
    if result:
        add_message("Output:\n    " + re.sub(r'\n', '\n    ', result) + "\n")

def add_error(err):
    if err:
        add_message("Error:\n    " + re.sub(r'\n', '\n    ', err) + "\n")

def end_command():
    add_message("\n")