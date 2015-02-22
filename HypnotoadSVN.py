import sublime
import sublime_plugin
import os
import os.path
from subprocess import Popen, PIPE
from threading import Thread, Timer
from queue import Queue, Empty
import re
from . import SvnProcess

class HypnoCommand(sublime_plugin.WindowCommand):
    def get_path(self, paths):
        path = None
        if paths:
            path = '"' + '" "'.join(paths) + '"'
        else:
            view = sublime.active_window().active_view()
            path = view.file_name() if view else None
        return path

class OpenReadOnlyCommand(sublime_plugin.WindowCommand):
    def run(self, file):
        path = file.replace("${packages}", sublime.packages_path())
        view = sublime.active_window().open_file(path)
        view.set_read_only(True)

class SvnCommand(HypnoCommand):
    def run_command(self, cmd, args="", log=True, thread=True):
        command = 'svn ' + cmd + ' ' + args
        return SvnProcess.Process(self.name, command, log, thread)

    def run_path_command(self, cmd, paths, log=True, thread=True):
        dir = self.get_path(paths)
        if not dir:
            return
        return self.run_command(cmd, dir, log, thread)

    def test_versionned(self, result):
        return 'not a working copy' not in result

    def is_versionned(self, paths=None):
        p = self.run_path_command('info', paths, False, False)
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

    def run(self, cmd="", paths=None):
        if cmd is "":
            return
        self.name = "SVN " + cmd.upper()
        self.run_path_command(cmd, paths)

class SvnUpdateCommand(SvnCommand):
    def run(self, paths=None):
        self.name = "SVN Update"
        self.run_path_command('update', paths, True, True)

    def is_visible(self, paths=None):
        return True #super(SvnCommand, self).is_visible('update', paths, True)

class SvnUpdateRevisionCommand(SvnCommand):
    def run(self, paths=None):
        self.name = "SVN Update to revision (%s)" % 2
        self.run_path_command('update -r 2', paths, True, False)

    def is_visible(self, paths=None):
        return True #super(SvnCommand, self).is_visible('update', paths, True)