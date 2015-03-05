import sublime
import sublime_plugin
import os
import os.path
import re
import subprocess
import time
from .lib import util, thread, settings, output

LOG_PARSE = r'-{72}[\r\n]+r(\d+) \| ([^|]+) \| ([^|]+) \| [^\n\r]+[\n\r]+(.+)'
STATUS_PARSE = r'(^[A-Z\?\!\ >]+?) +(.*)'
INFO_PARSE_REVISION = r"Revision: (\d+)"
INFO_PARSE_LAST_CHANGE = r"Last Changed Rev: (\d+)"

class HypnoSvnCommand(sublime_plugin.WindowCommand):
    """Base command for svn commands"""
    recent_files = []

    def nothing(nothing1=None, nothing2=None, nothing3=None, **args):
        """Does nothing, just a placeholder for things I don't handle"""
        return

    def run_command(self, cmd, files=None, log=True, async=True):
        """Starts a process for a native command"""
        return thread.Process(self.name, 'svn ' + cmd, files, log, async)

    def run_tortoise(self, cmd, files):
        """Starts a process for a TortoiseSVN command"""
        if not util.use_tortoise():
            error_message('Tortoise command can not be run: ' + cmd)
            return
        command = '"' + settings.get_tortoise_path() + '" /command:'+ cmd + ' /path:"%s"' % util.tortoise_path(files)
        return subprocess.Popen(command, stdout=subprocess.PIPE)

    def test_versionned(self, result):
        """Tests output to verify if a file is versionned"""
        return re.search(INFO_PARSE_REVISION, result, re.M) is not None

    def is_versionned(self, files):
        """Runs a native command to verify if a file is versionned"""
        if len(files) == 0:
            return False

        versionned = False
        for f in files:
            p = self.run_command('info', [ f ], False, False)
            if self.test_versionned(p.output() + p.error()) is True:
                return True
        return False

    def is_changed(self, files):
        """Runs a status command to see if a file has been changed since last revision"""
        p = self.run_command('status', files, False, False)
        return bool(p.output())

    def is_unchanged(self, files):
        """Checks if a file is unchanged since last revision"""
        return not self.is_changed(files)

    def is_single(self, files):
        """Checks if the list of files contains only 1 file"""
        if len(files) == 1:
            return True
        return False

    def is_file(self, files):
        """Checks if a file is actually a file"""
        if self.is_single(files) and os.path.isfile(files[0]):
            return True
        return False

    def is_folder(self, files):
        """Checks if a file is actually a folder"""
        if self.is_single(files) and not os.path.isfile(files[0]):
            return True
        return False

    def test_all(self, files):
        """Gets the result of all of the tests"""
        uid = "*".join(files)
        for tests in HypnoSvnCommand.recent_files:
            if time.time() - tests['timestamp'] > 1:
                HypnoSvnCommand.recent_files.remove(tests)
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
            'single': self.is_single(files),
            'native': util.use_native(),
            'tortoise': util.use_tortoise()
        }
        tests['enabled'] = tests['native'] or tests['tortoise']
        HypnoSvnCommand.recent_files.append(tests)
        return tests

    def run(self, cmd="", paths=None, group=-1, index=-1):
        """Runs the command"""
        if cmd is "":
            return
        files = util.get_files(paths, group, index)
        self.name = cmd.upper()
        self.run_command(cmd, files)

    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the view should be visible"""
        return util.enabled()

class HypnoSvnCommitCommand(HypnoSvnCommand):
    """A command that handles committing to SVN"""
    def escape(self, message):
        """Escapes quotes in a commit message."""
        return message.replace('"', '\\"')
    def commit(self):
        """Runs the native commit command"""
        self.run_command('commit -m "' + self.escape(self.message) + '"', self.files)
    def verify(self):
        """Checks with the user if the commit is valid"""
        files = []
        for index, include in enumerate(self.includes):
            if include is True:
                files.append(self.files[index])
        if sublime.ok_cancel_dialog(self.message+'\n\nFiles:\n'+'\n'.join(files)):
            self.files = files
            self.commit()
    def on_done_input(self, value):
        """Handles completion of the input panel"""
        self.message = value
        self.verify()
    def show_message_panel(self):
        """Opens an input panel to get the commit message"""
        sublime.active_window().show_input_panel('Commit message', '', self.on_done_input, self.nothing, self.nothing)
    def show_changes_panel(self):
        """Opens a quick panel to select files for committing"""
        sublime.active_window().show_quick_panel(self.items, self.on_select, sublime.MONOSPACE_FONT)
    def on_select(self, index):
        """Toggles a file for committing"""
        if index < 0:
            return
        if index == 0:
            self.show_message_panel()
            return
        if self.includes[index]:
            self.items[index] = re.sub(r'^\[X\]', '[ ]', self.items[index])
        else:
            self.items[index] = re.sub(r'^\[ \]', '[X]', self.items[index])
        self.includes[index] = not self.includes[index]
        sublime.set_timeout(self.show_changes_panel, 50)
    def parse_changes(self, raw):
        """Parses the output of a status command"""
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
            inSVN = self.is_versionned([path])
            files.append(path.strip())
            if inSVN:
                items.append('[X]' + change + ": " + path)
                includes.append(True)
            else:
                items.append('[ ]' + change + ": " + path)
                includes.append(False)
        self.files = files
        self.items = items
        self.includes = includes
        return True
    def on_changes_available(self, process):
        """Shows the list of changes to the user"""
        output = process.output()
        if self.parse_changes(output) == False:
            return
        self.show_changes_panel()
    def get_changes(self):
        """Gets the committable changes"""
        thread.Process('Log', 'svn status', self.files, False, True, self.on_changes_available)
    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug('Commit')
        files = util.get_files(paths, group, index)
        self.name = "Commit"
        if util.prefer_tortoise("commit"):
            self.run_tortoise('commit', files)
            return
        if not util.use_native():
            return
        self.files = files
        self.get_changes()
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the view should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned']

class HypnoSvnUpdateRevisionCommand(HypnoSvnCommand):
    """A command that updates to a particular revision instead of HEAD"""
    def on_done_input(self, value):
        """Handles the result of the input panel"""
        self.name = "Update to revision (%s)" % value
        self.run_command('update -r %s' % value, self.files)
    def on_select(self, index):
        """Handles the result of the quickpanel"""
        if index < 0:
            return
        if index >= len(self.revisions):
            self.number = self.number * 2
            self.get_revisions(self.number)
        revision = self.revisions[index]
        self.name = "Update to revision (%s)" % revision
        self.run_command('update -r %s' % revision, self.files)
    def parse_logs(self, raw):
        """Parses the logs"""
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
        """Handles the logs being available"""
        output = process.output()
        self.parse_logs(output)
        util.debug(",".join(self.logs))
        if len(self.logs) > 0:
            sublime.active_window().show_quick_panel(self.logs, self.on_select)
    def get_revisions(self, revisions):
        """Runs a process to get log output"""
        thread.Process('Log', 'svn log -r HEAD:1 -l ' + str(revisions), self.files, False, True, self.on_logs_available)
    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug('Update to revision')
        if not util.use_native():
            return
        files = util.get_files(paths, group, index)
        self.files = files
        show_history = settings.get_native("updateToRevisionHistory", True)
        if (show_history):
            self.number = settings.get_native('updateToRevisionHistorySize', 20)
            self.get_revisions(self.number)
        else:
            sublime.active_window().show_input_panel('Which revision', '', self.on_done_input, self.nothing, self.nothing)
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the view should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['native']

class HypnoSvnUpdateCommand(HypnoSvnCommand):
    """A command that updates to HEAD"""
    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug('Update')
        files = util.get_files(paths, group, index)
        self.name = "Update"
        if util.prefer_tortoise('update'):
            self.run_tortoise('update', files)
            return
        if not util.use_native():
            return
        self.run_command('update', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the view should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['enabled']

class HypnoSvnLogCommand(HypnoSvnCommand):
    """A command the gets recent logs"""
    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug('Log')
        files = util.get_files(paths, group, index)
        self.name = "Log"
        if util.prefer_tortoise('log'):
            self.run_tortoise('log', files)
            return
        if not util.use_native():
            return
        revisions = settings.get_native('logHistorySize', 20)
        if isinstance(revisions, int) and revisions > 0:
            self.run_command('log -v -l %s' % revisions, files)
        else:
            self.run_command('log -v', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the view should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['enabled']

class HypnoSvnLogNumberCommand(HypnoSvnCommand):
    """A command the gets a specific number of log entries"""
    def on_done_input(self, value):
        """Handles completion of an input panel"""
        try:
            revisions = int(value)
        except:
            return
        if revisions < 1:
            return
        revisions = str(revisions)
        self.name = "Log (" + revisions + ")"
        self.run_command('log -v -l %s' % revisions, self.files)
    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        if not util.use_native():
            return
        util.debug('Log N')
        self.files = util.get_files(paths, group, index)
        self.name = "Log"
        revisions = settings.get_native('logHistorySize', 20)

        sublime.active_window().show_input_panel('Number of logs...', str(revisions), self.on_done_input, self.nothing, self.nothing)
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the view should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['native'] and not util.prefer_tortoise('log')

class HypnoSvnStatusCommand(HypnoSvnCommand):
    """A command that checks the status of the files"""
    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug('Check for Modifications')
        files = util.get_files(paths, group, index)
        self.name = "Check for Modifications"
        if util.prefer_tortoise('status'):
            self.run_tortoise('repostatus', files)
            return
        if not util.use_native():
            return
        self.run_command('status', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the view should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['enabled']

class HypnoSvnAddCommand(HypnoSvnCommand):
    """Adds unversionned files to the repo"""
    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug('Add')
        files = util.get_files(paths, group, index)
        self.name = "Add"
        if util.prefer_tortoise('add'):
            self.run_tortoise('add', files)
            return
        if not util.use_native():
            return
        self.run_command('add', files)

class HypnoSvnDeleteCommand(HypnoSvnCommand):
    """Deletes versionned files from the repo"""
    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug('Delete')
        files = util.get_files(paths, group, index)
        self.name = "Delete"
        if util.prefer_tortoise('delete'):
            self.run_tortoise('remove', files)
            return
        if not util.use_native():
            return
        self.run_command('delete', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the view should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['enabled']

class HypnoSvnRevertCommand(HypnoSvnCommand):
    """Reverts changes made to the working copy"""
    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug('Revert')
        files = util.get_files(paths, group, index)
        self.name = "Revert"
        if util.prefer_tortoise('revert'):
            self.run_tortoise('revert', files)
            return
        if not util.use_native():
            return
        self.run_command('revert -R', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the view should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['enabled']

class HypnoSvnCleanupCommand(HypnoSvnCommand):
    """Cleans up broken repos"""
    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug('Cleanup')
        files = util.get_files(paths, group, index)
        self.name = "Cleanup"
        if util.prefer_tortoise('cleanup'):
            self.run_tortoise('cleanup', files)
            return
        if not util.use_native():
            return
        self.run_command('cleanup', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the view should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['enabled']

class HypnoSvnLockCommand(HypnoSvnCommand):
    """Gets a lock on the selected files"""
    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug('Lock')
        files = util.get_files(paths, group, index)
        self.name = "Lock"
        if util.prefer_tortoise('lock'):
            self.run_tortoise('lock', files)
            return
        if not util.use_native():
            return
        self.run_command('lock', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the view should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['enabled']

class HypnoSvnStealLockCommand(HypnoSvnCommand):
    """Steals a lock from another user"""
    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug('Steal Lock')
        if not util.use_native():
            return
        files = util.get_files(paths, group, index)
        self.name = "Steal Lock"
        self.run_command('lock --force', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the view should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['native']

class HypnoSvnUnlockCommand(HypnoSvnCommand):
    """Unlocks the repo"""
    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug('Unlock')
        files = util.get_files(paths, group, index)
        self.name = "Unlock"
        if util.prefer_tortoise('unlock'):
            self.run_tortoise('unlock', files)
            return
        if not util.use_native():
            return
        self.run_command('unlock', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the view should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['enabled']

class HypnoSvnMergeCommand(HypnoSvnCommand):
    """Merges changes from the repo to the working copy"""
    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug('Merge')
        files = util.get_files(paths, group, index)
        self.name = "Merge"
        if util.use_tortoise():
            self.run_tortoise("merge", files)
            return
        if not util.use_native():
            return
        self.run_command('merge', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the view should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['single'] and tests['tortoise']

class HypnoSvnDiffCommand(HypnoSvnCommand):
    """Lists the changes to a working copy file"""
    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug('Diff')
        files = util.get_files(paths, group, index)
        self.name = "Diff"
        if util.prefer_tortoise('diff'):
            self.run_tortoise("diff", files)
            return
        if not util.use_native():
            return
        self.run_command('diff', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the view should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['file'] and tests['versionned'] and tests['changed'] and tests['enabled']

class HypnoSvnDiffPreviousCommand(HypnoSvnCommand):
    """Lists the changes between latest and previous revisions"""
    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug('Diff with previous')
        files = util.get_files(paths, group, index)
        self.name = "Diff With Previous"
        p = self.run_command('info', files, False, False)
        output = p.output()
        current = re.search(INFO_PARSE_REVISION, output).group(1)
        last = str(int(re.search(INFO_PARSE_LAST_CHANGE, output).group(1)) - 1)
        if util.prefer_tortoise('diff'):
            self.run_tortoise("diff /startrev:" + last + " /endrev:" + current, files)
            return
        if not util.use_native():
            return
        self.run_command('diff -r ' + last + ":" + current, files)
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the view should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['file'] and tests['versionned'] and not tests['changed'] and tests['enabled']

class HypnoSvnRenameCommand(HypnoSvnCommand):
    """Renames a file or folder in SVN"""
    def on_done_input(self, value):
        """Handles completion of an input panel"""
        self.name = "Rename"
        self.run_command('rename --parents' + os.path.join(self.current_path, self.current_name) + ' ' + os.path.join(self.current_path, value))
    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug('Rename')
        files = util.get_files(paths, group, index)
        self.name = "Rename"
        if util.prefer_tortoise('rename'):
            self.run_tortoise("rename", files)
            return
        if not util.use_native():
            return
        self.head, self.tail = os.path.split(files[0])
        sublime.active_window().show_input_panel('Rename...', self.current_name, self.on_done_input, self.nothing, self.nothing)
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the view should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['single'] and tests['enabled']

class HypnoSvnBlameCommand(HypnoSvnCommand):
    """Checks who has made the last changes to each line in a file"""
    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug('Blame')
        files = util.get_files(paths, group, index)
        self.name = "Blame"
        if util.prefer_tortoise('blame'):
            self.run_tortoise("blame", files)
            return
        self.run_command('blame', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the view should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['enabled']

class HypnoSvnConflictEditorCommand(HypnoSvnCommand):
    """Opens the TortoiseSVN conflict editor"""
    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug('Conflict Editor')
        files = util.get_files(paths, group, index)
        self.run_tortoise('conflicteditor', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the view should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['tortoise'] and tests['versionned']

class HypnoSvnResolveCommand(HypnoSvnCommand):
    """Resolves conflicts"""
    options = [
        'base',
        'working',
        'mine-conflict',
        'theirs-conflict',
        'mine-full',
        'theirs-full'
    ]
    def on_select(self, index):
        """Handles which option for resolution"""
        self.run_command('resolve -R --accept ' + HypnoSvnResolveCommand.options[index], self.files)
    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug('Resolve')
        files = util.get_files(paths, group, index)
        self.name = "Resolve"
        if util.use_tortoise():
            self.run_tortoise("resolve", files)
            return
        self.files = files
        sublime.active_window().show_quick_panel(HypnoSvnResolveCommand.options, self.on_select)
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the view should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['single'] and tests['enabled']

class HypnoSvnSwitchCommand(HypnoSvnCommand):
    """Switches the working copy to a different branch"""
    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug('Switch')
        files = util.get_files(paths, group, index)
        self.name = "Switch"
        if util.use_tortoise():
            self.run_tortoise("switch", files)
            return
        #self.run_command('switch', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the view should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['single'] and tests['tortoise']

class HypnoSvnBranchCommand(HypnoSvnCommand):
    """Creates a new branch"""
    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug('Branch')
        files = util.get_files(paths, group, index)
        self.name = "Branch"
        if util.use_tortoise():
            self.run_tortoise("branch", files)
            return
        #self.run_command('copy', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the view should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['single'] and tests['tortoise']

class HypnoSvnCheckoutCommand(HypnoSvnCommand):
    """Checks out a repo"""
    def on_done_input(self, value):
        """Handles completion of the input panel"""
        self.name = "Rename"
        self.run_command('checkout', self.files)
    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug('Checkout')
        files = util.get_files(paths, group, index)
        self.name = "Checkout"
        if util.prefer_tortoise('checkout'):
            self.run_tortoise("checkout", files)
            return
        if not util.use_native():
            return
        self.files = files
        sublime.active_window().show_input_panel('Checkout from...', 'http://', self.on_done_input, self.nothing, self.nothing)
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the view should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return not tests['versionned'] and tests['folder'] and tests['enabled']
