import sublime
import sublime_plugin
from .lib import output

class HypnoViewMessageCommand(sublime_plugin.TextCommand):
    """A command that adds a message to the end of a view"""
    def run(self, edit, message=""):
        """Runs the command"""
        self.view.set_read_only(False)
        self.view.insert(edit, self.view.size(), message + '\n')
        self.view.set_read_only(True)

class HypnoViewClearCommand(sublime_plugin.TextCommand):
    """A command that clears all content from a view"""
    def run(self, edit):
        """Runs the command"""
        self.view.set_read_only(False)
        self.view.erase(edit, sublime.Region(0, self.view.size()))
        self.view.set_read_only(True)
    def is_visible(self, edit=None):
        """Checks if the view should be visible"""
        return output.SvnView.view == self.view

class HypnoOutputClearCommand(sublime_plugin.WindowCommand):
    """A command that clears the SVN Output view"""
    def run(self, group=-1, index=-1):
        """Runs the command"""
        output.clear()
    def is_visible(self, group=-1, index=-1):
        """Checks if the view should be visible"""
        if group >=0 and index >= 0:
            view = sublime.active_window().views_in_group(group)[index]
            return output.SvnView.view == view
        return True