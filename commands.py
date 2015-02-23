import sublime
import sublime_plugin
import os
import os.path
import re
from . import util
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

    def is_versionned(self, paths):
        if len(paths) == 0:
            return False
        p = self.run_command('info', paths, False, False)
        return self.test_versionned(p.output() + p.error())

    def is_single(self, paths=None):
        if paths == None:
            return False
        if len(paths) == 1:
            return True
        return False

    def is_file(self, paths):
        if paths == None:
            return False
        file = self.get_path(paths)
        if os.path.isfile(file):
            return False
        return True

    def is_folder(self, paths):
        if paths == None:
            return False
        file = self.get_path(paths)
        if not os.path.isfile(file):
            return False
        return True

    def run(self, cmd="", paths=None, group=-1, index=-1):
        if cmd is "":
            return
        files = util.get_paths(paths, group, index)
        self.name = cmd.upper()
        self.run_command(cmd, files)

class SvnCommitCommand(SvnCommand):
    def commit(self):
        self.name = "SVN Commit"
        self.run_command('commit', self.files)
    def verify(self):
        files = []
        for index, include in enumerate(self.includes):
            if include is True:
                files.append(self.items[index])
        if sublime.ok_dialog(self.message+'\n\nFiles:\n'+'\n'.join(files)):
            self.files = files
            self.commit()
    def on_done_input(self, value):
        self.message = value
        verify()
    def on_change_input(self, value):
        return
    def on_cancel_input(self):
        return
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
        SvnProcess.Process('Log', 'svn status', self.files, False, True, self.on_changes_available)
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_paths(paths, group, index)
        self.files = files
        self.get_changes()
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_paths(paths, group, index)
        return self.is_versionned(files)

class SvnUpdateRevisionCommand(SvnCommand):
    def on_done_input(self, value):
        self.name = "Update to revision (%s)" % value
        self.run_command('update -r %s' % value, self.files)
    def on_change_input(self, value):
        return
    def on_cancel_input(self):
        return
    def on_select(self, index):
        if index < 0:
            return
        if index >= len(self.revisions):
            self.number = self.number * 2
            self.get_revisions(self.number)
        revision = self.revisions[index]
        self.name = "Update to revision (%s)" % revision
        self.run_command('update -r %s' % revision, self.files)
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
        SvnProcess.Process('Log', 'svn log -r HEAD:1 -l ' + str(revisions), self.files, False, True, self.on_logs_available)
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_paths(paths, group, index)
        self.files = files
        show_history = self.get_setting("updateToRevisionHistory")
        if (show_history):
            self.number = self.get_setting('updateToRevisionHistorySize')
            self.get_revisions(self.number)
        else:
            sublime.active_window().show_input_panel('Which revision', '', self.on_done_input, self.on_change_input, self.on_cancel_input)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_paths(paths, group, index)
        return self.is_versionned(files)

class SvnUpdateCommand(SvnCommand):
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_paths(paths, group, index)
        self.name = "Update"
        self.run_command('update', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_paths(paths, group, index)
        return self.is_versionned(files)

class SvnLogCommand(SvnCommand):
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_paths(paths, group, index)
        self.name = "Log"
        revisions = self.get_setting('logHistorySize')
        if isinstance(revisions, int) and revisions > 0:
            self.run_command('log -v -l %s' % revision, files)
        else:
            self.run_command('log -v', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_paths(paths, group, index)
        return self.is_versionned(files)

class SvnStatusCommand(SvnCommand):
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_paths(paths, group, index)
        self.name = "Check for Modifications"
        self.run_command('status -v', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_paths(paths, group, index)
        return self.is_versionned(files)

class SvnAddCommand(SvnCommand):
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_paths(paths, group, index)
        self.name = "Add"
        self.run_command('add', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_paths(paths, group, index)
        return self.is_versionned(files)

class SvnDeleteCommand(SvnCommand):
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_paths(paths, group, index)
        self.name = "Delete"
        self.run_command('delete', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_paths(paths, group, index)
        return self.is_versionned(files)

class SvnRevertCommand(SvnCommand):
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_paths(paths, group, index)
        self.name = "Revert"
        self.run_command('revert -R', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_paths(paths, group, index)
        return self.is_versionned(files)

class SvnCleanupCommand(SvnCommand):
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_paths(paths, group, index)
        self.name = "Cleanup"
        self.run_command('cleanup -R', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_paths(paths, group, index)
        return self.is_versionned(files)

class SvnLockCommand(SvnCommand):
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_paths(paths, group, index)
        self.name = "Lock"
        self.run_command('lock', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_paths(paths, group, index)
        return self.is_versionned(files)

class SvnStealLockCommand(SvnCommand):
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_paths(paths, group, index)
        self.name = "Steal Lock"
        self.run_command('lock --force', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_paths(paths, group, index)
        return self.is_versionned(files)

class SvnUnlockCommand(SvnCommand):
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_paths(paths, group, index)
        self.name = "Unlock"
        self.run_command('unlock', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_paths(paths, group, index)
        return self.is_versionned(files)