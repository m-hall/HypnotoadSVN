import sublime
import sublime_plugin
import os
import os.path
import re
import time
import subprocess
from .lib import util, thread, settings

LOG_PARSE = r'-{72}\nr(\d+) \| ([^|]+) \| ([^|]+) \| [^\n]+\n\n(.+)'
STATUS_PARSE = r'(^[A-Z\?\!\ >]{3,6}) (.*)'
INFO_PARSE_REVISION = r"Revision: (\d+)"
INFO_PARSE_LAST_CHANGE = r"Last Changed Rev: (\d+)"

class SvnViewMessageCommand(sublime_plugin.TextCommand):
    def run(self, edit, message=""):
        self.view.set_read_only(False)
        self.view.insert(edit, self.view.size(), message + '\n')
        self.view.set_read_only(True)

class SvnKillProcessesCommand(sublime_plugin.WindowCommand):
    def run(self):
        thread.terminate_all()

class SvnCommand(sublime_plugin.WindowCommand):
    recent_files = []

    def nothing(nothing1=None, nothing2=None, nothing3=None, **args):
        return

    def run_command(self, cmd, files=None, log=True, async=True):
        return thread.Process(self.name, 'svn ' + cmd, files, log, async)

    def run_tortoise(self, cmd, files):
        if not util.use_tortoise():
            error_message('Tortoise command can not be run: ' + cmd)
            return
        command = '"' + settings.get_tortoise('tortoiseproc_path') + '" /command:'+ cmd + ' /path:"%s"' % util.tortoise_path(files)
        return subprocess.Popen(command, stdout=subprocess.PIPE)

    def test_versionned(self, result):
        return 'not a working copy' not in result

    def is_versionned(self, files):
        if len(files) == 0:
            return False
        p = self.run_command('info', files, False, False)
        return self.test_versionned(p.output() + p.error())

    def is_changed(self, files):
        p = self.run_command('status', files, False, False)
        return bool(p.output())

    def is_unchanged(self, files):
        return not self.is_changed(files)

    def is_single(self, files):
        if len(files) == 1:
            return True
        return False

    def is_file(self, files):
        if self.is_single(files) and os.path.isfile(files[0]):
            return True
        return False

    def is_folder(self, files):
        if self.is_single(files) and not os.path.isfile(files[0]):
            return True
        return False

    def test_all(self, files):
        uid = "*".join(files)
        for tests in SvnCommand.recent_files:
            if time.time() - tests['timestamp'] > 1:
                SvnCommand.recent_files.remove(tests)
                continue
            if uid == tests['uid']:
                return tests
        tests = {
            'uid': uid,
            'timestamp': time.time(),
            'versionned': self.is_versionned(files),
            'changed': self.is_changed(files),
            'file': self.is_file(files),
            'folder': self.is_folder(files),
            'single': self.is_single(files)
        }
        SvnCommand.recent_files.append(tests)
        return tests

    def run(self, cmd="", paths=None, group=-1, index=-1):
        if cmd is "":
            return
        files = util.get_files(paths, group, index)
        self.name = cmd.upper()
        self.run_command(cmd, files)

    def is_visible(self, paths=None, group=-1, index=-1):
        return util.enabled()

class SvnCommitCommand(SvnCommand):
    def commit(self):
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
        thread.Process('Log', 'svn status', self.files, False, True, self.on_changes_available)
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        self.name = "Commit"
        if util.prefer_tortoise():
            self.run_tortoise('commit', files)
            return
        if not util.use_native():
            return
        self.files = files
        self.get_changes()
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned']

class SvnUpdateRevisionCommand(SvnCommand):
    def on_done_input(self, value):
        self.name = "Update to revision (%s)" % value
        self.run_command('update -r %s' % value, self.files)
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
        self.parse_logs(output)
        sublime.active_window().show_quick_panel(self.logs, self.on_select)
    def get_revisions(self, revisions):
        thread.Process('Log', 'svn log -r HEAD:1 -l ' + str(revisions), self.files, False, True, self.on_logs_available)
    def run(self, paths=None, group=-1, index=-1):
        if not util.use_native():
            return
        files = util.get_files(paths, group, index)
        self.files = files
        show_history = settings.get_native("updateToRevisionHistory")
        if (show_history):
            self.number = settings.get_native('updateToRevisionHistorySize')
            self.get_revisions(self.number)
        else:
            sublime.active_window().show_input_panel('Which revision', '', self.on_done_input, self.nothing, self.nothing)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and util.use_native()

class SvnUpdateCommand(SvnCommand):
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        self.name = "Update"
        if util.prefer_tortoise():
            self.run_tortoise('update', files)
            return
        if not util.use_native():
            return
        self.run_command('update', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and util.enabled()

class SvnLogCommand(SvnCommand):
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        self.name = "Log"
        if util.prefer_tortoise():
            self.run_tortoise('log', files)
            return
        if not util.use_native():
            return
        revisions = settings.get_native('logHistorySize')
        if isinstance(revisions, int) and revisions > 0:
            self.run_command('log -v -l %s' % revisions, files)
        else:
            self.run_command('log -v', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and util.enabled()

class SvnStatusCommand(SvnCommand):
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        self.name = "Check for Modifications"
        if util.prefer_tortoise():
            self.run_tortoise('repostatus', files)
            return
        if not util.use_native():
            return
        self.run_command('status', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and util.enabled()

class SvnAddCommand(SvnCommand):
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        self.name = "Add"
        if util.prefer_tortoise():
            self.run_tortoise('add', files)
            return
        if not util.use_native():
            return
        self.run_command('add', files)

class SvnDeleteCommand(SvnCommand):
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        self.name = "Delete"
        if util.prefer_tortoise():
            self.run_tortoise('remove', files)
            return
        if not util.use_native():
            return
        self.run_command('delete', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and util.enabled()

class SvnRevertCommand(SvnCommand):
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        self.name = "Revert"
        if util.prefer_tortoise():
            self.run_tortoise('revert', files)
            return
        if not util.use_native():
            return
        self.run_command('revert -R', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and util.enabled()

class SvnCleanupCommand(SvnCommand):
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        self.name = "Cleanup"
        if util.prefer_tortoise():
            self.run_tortoise('cleanup', files)
            return
        if not util.use_native():
            return
        self.run_command('cleanup', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and util.enabled()

class SvnLockCommand(SvnCommand):
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        self.name = "Lock"
        if util.prefer_tortoise():
            self.run_tortoise('lock', files)
            return
        if not util.use_native():
            return
        self.run_command('lock', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and util.enabled()

class SvnStealLockCommand(SvnCommand):
    def run(self, paths=None, group=-1, index=-1):
        if not util.use_native():
            return
        files = util.get_files(paths, group, index)
        self.name = "Steal Lock"
        self.run_command('lock --force', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and util.use_native()

class SvnUnlockCommand(SvnCommand):
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        self.name = "Unlock"
        if util.prefer_tortoise():
            self.run_tortoise('unlock', files)
            return
        if not util.use_native():
            return
        self.run_command('unlock', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and util.enabled()

class SvnMergeCommand(SvnCommand):
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        self.name = "Merge"
        if util.use_tortoise():
            self.run_tortoise("merge", files)
            return
        if not util.use_native():
            return
        self.run_command('merge', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['single']
    def is_enabled(self, paths=None, group=-1, index=-1):
        return util.use_tortoise()

class SvnDiffCommand(SvnCommand):
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        self.name = "Diff"
        if util.prefer_tortoise():
            self.run_tortoise("diff", files)
            return
        if not util.use_native():
            return
        self.run_command('diff', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['file'] and tests['versionned'] and tests['changed'] and util.enabled()

class SvnDiffPreviousCommand(SvnCommand):
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        self.name = "Diff With Previous"
        p = self.run_command('info', files, False, False)
        output = p.output()
        current = re.search(INFO_PARSE_REVISION, output).group(1)
        last = str(int(re.search(INFO_PARSE_LAST_CHANGE, output).group(1)) - 1)
        if util.prefer_tortoise():
            self.run_tortoise("diff /startrev:" + last + " /endrev:" + current, files)
            return
        if not util.use_native():
            return
        self.run_command('diff -r ' + last + ":" + current, files)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['file'] and tests['versionned'] and not tests['changed'] and util.enabled()

class SvnRenameCommand(SvnCommand):
    def on_done_input(self, value):
        self.name = "Rename"
        self.run_command('rename --parents' + self.current_path + self.current_name + ' ' + self.current_path + value)
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        self.name = "Rename"
        if util.use_tortoise():
            self.run_tortoise("rename", files)
            return
        if not util.use_native():
            return
        path = util.get_path_components(files[0])
        self.current_name = path[-1]
        path.remove(path[-1])
        self.current_path = "/".join(path) + "/"
        sublime.active_window().show_input_panel('Rename...', self.current_name, self.on_done_input, self.nothing, self.nothing)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['single'] and util.enabled()

class SvnBlameCommand(SvnCommand):
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        self.name = "Blame"
        if util.use_tortoise():
            self.run_tortoise("blame", files)
            return
        self.run_command('blame', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and util.enabled()

class SvnConflictEditorCommand(SvnCommand):
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        self.run_tortoise('conflicteditor', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return util.use_tortoise() and tests['versionned']

class SvnResolveCommand(SvnCommand):
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        self.name = "Resolve"
        if util.use_tortoise():
            self.run_tortoise("resolve", files)
            return
        #self.run_command('resolve', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and util.use_tortoise()

class SvnSwitchCommand(SvnCommand):
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        self.name = "Switch"
        if util.use_tortoise():
            self.run_tortoise("switch", files)
            return
        #self.run_command('switch', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['single'] and util.use_tortoise()

class SvnBranchCommand(SvnCommand):
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        self.name = "Branch"
        if util.use_tortoise():
            self.run_tortoise("branch", files)
            return
        #self.run_command('copy', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['single'] and util.use_tortoise()

class SvnCheckoutCommand(SvnCommand):
    def on_done_input(self, value):
        self.name = "Rename"
        self.run_command('checkout', self.files)
    def run(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        self.name = "Checkout"
        if util.use_tortoise():
            self.run_tortoise("checkout", files)
            return
        if not util.use_native():
            return
        self.files = files
        sublime.active_window().show_input_panel('Checkout from...', 'http://', self.on_done_input, self.nothing, self.nothing)
    def is_visible(self, paths=None, group=-1, index=-1):
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return not tests['versionned'] and tests['folder'] and util.enabled()
