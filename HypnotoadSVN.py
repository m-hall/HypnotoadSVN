import sublime
import sublime_plugin
import os
import os.path
import re
from . import SvnProcess

LOG_PARSE = r'-{10,}\nr(\d+) \| ([^|]+) \| ([^|]+) \| [^\n]+\n\n(.+)'
STATUS_PARSE = r'(^[A-Z\?\!\ >]{3,6}) (.*)'

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

class SvnCommitCommand(SvnCommand):
    def commit(self):
        self.name = "SVN Commit"
        self.run_command('commit', self.paths)
    def verify(self):
        files = []
        for index, include in enumerate(self.includes):
            if include is True:
                files.append(self.items[index])
        if sublime.ok_dialog(self.message+'\n\nFiles:\n'+'\n'.join(files)):
            self.paths = files
            self.commit()
    def on_done_input(self, value):
        self.message = value
        verify()
    def on_change_input(self, value):
        return
    def on_cancel_input(self):
        return
    def is_visible(self, paths=None):
        return super(SvnCommitCommand, self).is_visible(paths=paths, versionned=True)
    def show_message_panel(self):
        sublime.active_window().show_input_panel('Commit message', '', self.on_done_input, self.on_change_input, self.on_cancel_input)
    def show_changes_panel(self):
        sublime.active_window().show_quick_panel(self.items, self.on_select, sublime.MONOSPACE_FONT)
    def on_select(self, index):
        if index < 0:
            return
        if index == 0:
            self.show_message_panel()
        if self.includes[index]:
            self.items[index] = re.sub(r'^\[X\]', '[ ]', self.items[index])
        else:
            self.items[index] = re.sub(r'^\[ \]', '[X]', self.items[index])
        self.includes[index] = not self.includes[index]
        sublime.set_timeout(self.show_changes_panel, 50)
    def parse_changes(self, raw):
        matches = re.findall(STATUS_PARSE, raw, re.M)
        if len(matches) < 1:
            sublime.status_message('No changes to commit')
            return False
        files = []
        items = []
        includes = []
        files.append(None)
        items.append('Done')
        includes.append(None)
        for change, path in matches:
            files.append(path)
            items.append('[ ]' + change + ": " + path)
            includes.append(False)
        self.files = files
        self.items = items
        self.includes = includes
        return True
    def on_changes_available(self, process):
        output = process.output()
        if self.parse_changes(output) == False:
            return
        self.show_changes_panel()
    def get_changes(self):
        SvnProcess.Process('Log', 'svn status', self.paths, False, True, self.on_changes_available)
    def run(self, paths=None):
        if paths is None:
            return
        self.paths = paths
        self.get_changes()

class SvnUpdateRevisionCommand(SvnCommand):
    def on_done_input(self, value):
        self.name = "SVN Update to revision (%s)" % value
        self.run_command('update -r %s' % value, self.paths)
    def on_change_input(self, value):
        return
    def on_cancel_input(self):
        return
    def is_visible(self, paths=None):
        return super(SvnUpdateRevisionCommand, self).is_visible(paths=paths, versionned=True)
    def on_select(self, index):
        if index < 0:
            return
        if index >= len(self.revisions):
            self.number = self.number * 2
            self.get_revisions(self.number)
        revision = self.revisions[index]
        self.name = "SVN Update to revision (%s)" % revision
        self.run_command('update -r %s' % revision, self.paths)
    def parse_logs(self, raw):
        matches = re.findall(LOG_PARSE, raw, re.M)
        revisions = []
        logs = []
        show_more = len(matches) >= self.number
        for revision, author, date, message in matches:
            revisions.append(revision)
            logs.append(revision + ": " + message)
            if int(revision) is 1:
                show_more = False
        if (show_more):
            logs.append('More revisions...')
        self.revisions = revisions
        self.logs = logs
    def on_logs_available(self, process):
        output = process.output()
        print(output)
        self.parse_logs(output)
        sublime.active_window().show_quick_panel(self.logs, self.on_select)
    def get_revisions(self, revisions):
        SvnProcess.Process('Log', 'svn log -r HEAD:1 -l ' + str(revisions), self.paths, False, True, self.on_logs_available)
    def run(self, paths=None):
        if paths is None:
            return
        self.paths = paths
        show_history = self.get_setting("updateToRevisionHistory")
        if (show_history):
            self.number = self.get_setting('updateToRevisionHistorySize')
            self.get_revisions(self.number)
        else:
            sublime.active_window().show_input_panel('Which revision', '', self.on_done_input, self.on_change_input, self.on_cancel_input)