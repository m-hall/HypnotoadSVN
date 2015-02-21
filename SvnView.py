import sublime
import sublime_plugin
import re

class SvnMessageCommand(sublime_plugin.TextCommand):
    def run(self, edit, message=""):
        self.view.insert(edit, self.view.size(), message)

class SvnView(sublime_plugin.EventListener):
    view=None
    @staticmethod
    def get():
        if not SvnView.view:
            SvnView.view = sublime.active_window().new_file()
            SvnView.view.set_scratch(True)
            SvnView.view.set_name('SVN Output')
            SvnView.view.set_read_only(True)
            SvnView.view.set_syntax_file('Packages/Hypnotoad/SVNOutput.tmLanguage')
        return SvnView.view

    @staticmethod
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

    @staticmethod
    def add_command(name, args=None):
        view = SvnView.get()
        point = view.text_to_layout(view.size() - 1)
        SvnView.add_message("Command: " + name + "\n")
        if args is not None:
            for arg in args:
                SvnView.add_message("    " + arg + "\n")
        SvnView.get().set_viewport_position(point, True)

    @staticmethod
    def add_result(result):
        if result:
            SvnView.add_message("Output:\n    " + re.sub(r'\n', '\n    ', result) + "\n")

    @staticmethod
    def add_error(err):
        if err:
            SvnView.add_message("Error:\n    " + re.sub(r'\n', '\n    ', err) + "\n")

    @staticmethod
    def end_command():
        SvnView.add_message("\n")

    def on_close(self, view):
        if view == SvnView.view:
            SvnView.view = None