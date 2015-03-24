import sublime
import sublime_plugin
import os
import re
from .lib import output

UNIX_PATH = r"/[^\n'\"]*"
NT_PATH = r"[A-Za-z]:\\[^\n'\"]*"


class HypnoViewMessageCommand(sublime_plugin.TextCommand):
    """A command that adds a message to the end of a view"""

    def run(self, edit, message=""):
        """Runs the command"""
        self.view.set_read_only(False)
        self.view.insert(edit, self.view.size(), message + '\n')
        self.view.set_read_only(True)
        output.highlight_conflicts()


class HypnoViewClearCommand(sublime_plugin.TextCommand):
    """A command that clears all content from a view"""

    def run(self, edit):
        """Runs the command"""
        self.view.set_read_only(False)
        self.view.erase(edit, sublime.Region(0, self.view.size()))
        self.view.set_read_only(True)

    def is_visible(self, edit=None):
        """Checks if the view should be visible"""
        return output.SvnView.get_existing() == self.view


class HypnoOutputClearCommand(sublime_plugin.WindowCommand):
    """A command that clears the SVN Output view"""

    def run(self, group=-1, index=-1):
        """Runs the command"""
        output.clear()

    def is_visible(self, group=-1, index=-1):
        """Checks if the view should be visible"""
        if group >= 0 and index >= 0:
            view = sublime.active_window().views_in_group(group)[index]
            return output.SvnView.get_existing() == view
        return True


class HypnoOutputOpenFileCommand(sublime_plugin.TextCommand):
    """A command that clears all content from a view"""

    def line_to_file(self, line):
        """Checks if there is a valid path in the line"""
        if os.name == 'nt':
            match = re.search(NT_PATH, line)
        else:
            match = re.search(UNIX_PATH, line)
        if not match:
            return None
        path = match.group(0)
        return path if os.path.exists(path) and os.path.isfile(path) else None

    def run(self, edit):
        """Runs the command"""
        win = sublime.active_window()
        regions = self.view.sel()
        for region in regions:
            lines = self.view.lines(region)
            for line in lines:
                path = self.line_to_file(self.view.substr(line))
                if path is not None:
                    win.open_file(path)

    def is_visible(self, edit=None):
        """Checks if the view should be visible"""
        if output.SvnView.get_existing() != self.view:
            return False
        regions = self.view.sel()
        for region in regions:
            lines = self.view.lines(region)
            for line in lines:
                path = self.line_to_file(self.view.substr(line))
                if path is not None:
                    return True
        return False