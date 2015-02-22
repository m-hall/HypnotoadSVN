import sublime
import sublime_plugin
import os
import os.path
import re
from . import SvnProcess

class OpenReadOnlyCommand(sublime_plugin.WindowCommand):
    def run(self, file):
        path = file.replace("${packages}", sublime.packages_path())
        view = sublime.active_window().open_file(path)
        view.set_read_only(True)

class SvnCommand(sublime_plugin.WindowCommand):
    def get_setting(self, name):
        settings = sublime.load_settings("HypnotoadSVN.sublime-settings")
        return settings.get(name)

    def run_command(self, cmd, paths=None, log=True, thread=True):
        return SvnProcess.Process(self.name, 'svn ' + cmd, paths, log, thread)

    def test_versionned(self, result):
        return 'not a working copy' not in result

    def is_versionned(self, paths=None):
        p = self.run_command('info', paths, False, False)
        return self.test_versionned(p.output() + p.error())

    def is_visible(self, cmd="", paths=None, versionned=None, fileType=None):
        if versionned is not None:
            if versionned != self.is_versionned(paths):
                return False
        if fileType is not None:
            if paths == None:
                return False
            file = self.get_path(paths)
            if os.path.isfile(file) == (fileType == 'file'):
                return False
        return True

    def run(self, cmd="", paths=None, versionned=None, fileType=None):
        if cmd is "":
            return
        self.name = "SVN " + cmd.upper()
        self.run_command(cmd, paths)
