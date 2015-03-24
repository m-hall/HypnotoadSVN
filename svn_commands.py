import sublime
import sublime_plugin
import os
import os.path
import re
import subprocess
import time
from .lib import util, thread, settings, output, panels

LOG_PARSE = r'-{72}[\r\n]+r(\d+) \| ([^|]+) \| ([^|]+) \| [^\n\r]+[\n\r]+(.+)'
STATUS_PARSE = r'(^[A-Z\?\!\ >]+?) +(\+ +)?(.*)'
INFO_PARSE_REVISION = r'Revision: (\d+)'
INFO_PARSE_LAST_CHANGE = r'Last Changed Rev: (\d+)'
INFO_PARSE_URL = r'URL: ([^\n]*)'


class HypnoSvnCommand(sublime_plugin.WindowCommand):
    """Base command for svn commands"""
    recent_files = []

    def __init__(self, window):
        """Initializes the HypnoSvnCommand object"""
        super().__init__(window)
        self.svn_name = 'SVN Command'
        self.tests = {
            'enabled': True
        }

    def nothing(self, nothing1=None, nothing2=None, nothing3=None, **args):
        """Does nothing, just a placeholder for things I don't handle"""
        return

    def run_command(self, cmd, files=None, log=True, async=True, on_complete=None):
        """Starts a process for a native command"""
        return thread.Process(self.svn_name, 'svn ' + cmd, files, log, async, on_complete)

    def run_tortoise(self, cmd, files):
        """Starts a process for a TortoiseSVN command"""
        if not util.use_tortoise():
            sublime.error_message('Tortoise command can not be run: ' + cmd)
            return
        command = '"' + settings.get_tortoise_path() + '" /command:' + cmd + ' /path:"%s"' % util.tortoise_path(files)
        util.debug(command)
        return subprocess.Popen(command, stdout=subprocess.PIPE)

    def test_versionned(self, result):
        """Tests output to verify if a file is versionned"""
        return re.search(INFO_PARSE_REVISION, result, re.M) is not None

    def is_versionned(self, files):
        """Runs a native command to verify if a file is versionned"""
        if len(files) == 0:
            return False

        for f in files:
            p = self.run_command('info', [f], False, False)
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
            'versionned': self.is_versionned(files),
            'changed': self.is_changed(files),
            'file': self.is_file(files),
            'folder': self.is_folder(files),
            'single': self.is_single(files),
            'native': util.use_native(),
            'tortoise': util.use_tortoise()
        }
        tests['enabled'] = tests['native'] or tests['tortoise']
        tests['timestamp'] = time.time()
        HypnoSvnCommand.recent_files.append(tests)
        return tests

    def on_complete_select(self, values):
        """Handles completion of the MultiSelect"""
        self.files = values

    def parse_changes(self, raw):
        """Parses the output of a status command for use in a MultiSelect"""
        matches = re.findall(STATUS_PARSE, raw, re.M)
        if len(matches) < 1:
            sublime.status_message('No changes')
            return False
        items = []
        for change, modifier, path in matches:
            inSVN = self.is_versionned([path])
            item = {
                'label': path,
                'value': path,
                'selected': inSVN
            }
            items.append(item)
        self.items = items
        return True

    def on_changes_available(self, process):
        """Shows the list of changes to the user"""
        output = process.output()
        if not self.parse_changes(output):
            return
        panels.MultiSelect(self.items, self.on_complete_select, show_select_all=True)

    def select_changes(self):
        """Gets the committable changes"""
        thread.Process('Log', 'svn status', self.files, False, True, self.on_changes_available)

    def get_url(self, file):
        """Gets the svn url for a file"""
        p = self.run_command('info', [file], False, False)
        m = re.search(INFO_PARSE_URL, p.output(), re.M)
        return m.group(1)

    def run(self, cmd="", paths=None, group=-1, index=-1):
        """Runs the command"""
        if cmd is "":
            return
        files = util.get_files(paths, group, index)
        self.svn_name = cmd.upper()
        self.run_command(cmd, files)

    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the command should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        for key in self.tests:
            if tests[key] != self.tests[key]:
                util.debug(self.svn_name + " is not visible because a test failed (%s)" % str(key))
                return False
        return True


class HypnoSvnCommitCommand(HypnoSvnCommand):
    """A command that handles committing to SVN"""

    def __init__(self, window):
        """Initialize the command object"""
        super().__init__(window)
        self.svn_name = 'Commit'
        self.tests = {
            'versionned': True,
            'enabled': True
        }
        self.files = None
        self.message = None

    def escape(self, message):
        """Escapes quotes in a commit message."""
        return message.replace('"', '\\"')

    def commit(self):
        """Runs the native commit command"""
        self.run_command('commit -m "' + self.escape(self.message) + '"', self.files)

    def verify(self):
        """Checks with the user if the commit is valid"""
        if sublime.ok_cancel_dialog(self.message + '\n\nFiles:\n' + '\n'.join(self.files)):
            self.commit()

    def on_done_input(self, value):
        """Handles completion of the input panel"""
        self.message = value
        minSize = settings.get_native('commitMessageSize', 0)
        if minSize > 0 and len(value) < minSize:
            sublime.status_message('Commit message too short')
            return
        if settings.get_native('commitConfirm', True):
            self.verify()
        else:
            self.commit()

    def show_message_panel(self):
        """Opens an input panel to get the commit message"""
        sublime.active_window().show_input_panel('Commit message', '', self.on_done_input, self.nothing, self.nothing)

    def on_complete(self, values):
        """Handles completion of the MultiSelect"""
        self.files = values
        self.show_message_panel()

    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug(self.svn_name)
        files = util.get_files(paths, group, index)
        if util.prefer_tortoise('commit'):
            self.run_tortoise('commit', files)
            return
        if not util.use_native():
            return
        self.files = files
        if self.is_file(files):
            self.show_message_panel()
        else:
            self.select_changes()
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the command should be visible"""
        print(self.svn_name)
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        for key in self.tests:
            if key not in tests:
                return false
            if tests[key] != self.tests[key]:
                print(self.svn_name + ": " + str(key))
                return false
        return True


class HypnoSvnUpdateRevisionCommand(HypnoSvnCommand):
    """A command that updates to a particular revision instead of HEAD"""

    def __init__(self, window):
        """Initialize the command object"""
        super().__init__(window)
        self.svn_name = 'Update to revision'
        self.tests = {
            'versionned': True,
            'enabled': True
        }
        self.files = None
        self.revisions = None
        self.logs = None

    def on_done_input(self, value):
        """Handles the result of the input panel"""
        self.svn_name = 'Update to revision (%s)' % value
        self.run_command('update -r %s' % value, self.files)

    def on_select(self, index):
        """Handles the result of the quickpanel"""
        if index < 0:
            return
        if index >= len(self.revisions):
            self.number = self.number * 2
            self.get_revisions(self.number)
        revision = self.revisions[index]
        self.svn_name = 'Update to revision (%s)' % revision
        self.run_command('update -r %s' % revision, self.files)

    def parse_logs(self, raw):
        """Parses the logs"""
        matches = re.findall(LOG_PARSE, raw, re.M)
        revisions = []
        logs = []
        show_more = len(matches) >= self.number
        for revision, author, date, message in matches:
            revisions.append(revision)
            logs.append([revision + ': ' + message, author, date])
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
        util.debug('found revisions:' + self.revisions[0] + '-' + self.revisions[-1])
        if len(self.logs) > 0:
            sublime.active_window().show_quick_panel(self.logs, self.on_select)

    def get_revisions(self, revisions):
        """Runs a process to get log output"""
        thread.Process('Log', 'svn log -r HEAD:1 -l ' + str(revisions), self.files, False, True, self.on_logs_available)

    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug(self.svn_name)
        if util.prefer_tortoise('update'):
            self.run_tortoise('update /rev', files)
            return
        if not util.use_native():
            return
        files = util.get_files(paths, group, index)
        self.files = files
        show_history = settings.get_native('updateToRevisionHistory', True)
        if (show_history):
            self.number = settings.get_native('updateToRevisionHistorySize', 20)
            self.get_revisions(self.number)
        else:
            sublime.active_window().show_input_panel('Which revision', '', self.on_done_input, self.nothing, self.nothing)


class HypnoSvnUpdateCommand(HypnoSvnCommand):
    """A command that updates to HEAD"""

    def __init__(self, window):
        """Initialize the command object"""
        super().__init__(window)
        self.svn_name = 'Update'
        self.tests = {
            'versionned': True,
            'enabled': True
        }

    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug(self.svn_name)
        files = util.get_files(paths, group, index)
        if util.prefer_tortoise('update'):
            self.run_tortoise('update', files)
            return
        if not util.use_native():
            return
        self.run_command('update', files)


class HypnoSvnLogCommand(HypnoSvnCommand):
    """A command the gets recent logs"""

    def __init__(self, window):
        """Initialize the command object"""
        super().__init__(window)
        self.svn_name = 'Log'
        self.tests = {
            'versionned': True,
            'native': True
        }

    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug(self.svn_name)
        files = util.get_files(paths, group, index)
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


class HypnoSvnLogNumberCommand(HypnoSvnCommand):
    """A command the gets a specific number of log entries"""

    def __init__(self, window):
        """Initialize the command object"""
        super().__init__(window)
        self.svn_name = 'Update to revision'
        self.tests = {
            'versionned': True,
            'native': True
        }
        self.files = None

    def on_done_input(self, value):
        """Handles completion of an input panel"""
        try:
            revisions = int(value)
        except:
            return
        if revisions < 1:
            return
        revisions = str(revisions)
        self.svn_name = 'Log (' + revisions + ')'
        self.run_command('log -v -l %s' % revisions, self.files)

    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        if not util.use_native():
            return
        util.debug(self.svn_name)
        self.files = util.get_files(paths, group, index)
        revisions = settings.get_native('logHistorySize', 20)

        sublime.active_window().show_input_panel('Number of logs...', str(revisions), self.on_done_input, self.nothing, self.nothing)

    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the command should be visible"""
        return not util.prefer_tortoise('log') and super().is_visible(paths, group, index)


class HypnoSvnStatusCommand(HypnoSvnCommand):
    """A command that checks the status of the files"""

    def __init__(self, window):
        """Initialize the command object"""
        super().__init__(window)
        self.svn_name = 'Check for Modifications'
        self.tests = {
            'versionned': True,
            'enabled': True
        }

    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug(self.svn_name)
        files = util.get_files(paths, group, index)
        if util.prefer_tortoise('status'):
            self.run_tortoise('repostatus', files)
            return
        if not util.use_native():
            return
        self.run_command('status', files)


class HypnoSvnAddCommand(HypnoSvnCommand):
    """Adds unversionned files to the repo"""

    def __init__(self, window):
        """Initialize the command object"""
        super().__init__(window)
        self.svn_name = 'Add'
        self.tests = {
            'enabled': True
        }

    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug(self.svn_name)
        files = util.get_files(paths, group, index)
        if util.prefer_tortoise('add'):
            self.run_tortoise('add', files)
            return
        if not util.use_native():
            return
        self.run_command('add', files)


class HypnoSvnDeleteCommand(HypnoSvnCommand):
    """Deletes versionned files from the repo"""

    def __init__(self, window):
        """Initialize the command object"""
        super().__init__(window)
        self.svn_name = 'Delete'
        self.tests = {
            'versionned': True,
            'enabled': True
        }

    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug(self.svn_name)
        files = util.get_files(paths, group, index)
        if util.prefer_tortoise('delete'):
            self.run_tortoise('remove', files)
            return
        if not util.use_native():
            return
        self.run_command('delete', files)


class HypnoSvnRevertAllCommand(HypnoSvnCommand):
    """Reverts changes made to the working copy"""

    def __init__(self, window):
        """Initialize the command object"""
        super().__init__(window)
        self.svn_name = 'Revert All'
        self.tests = {
            'versionned': True,
            'enabled': True
        }

    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug(self.svn_name)
        files = util.get_files(paths, group, index)
        if util.prefer_tortoise('revert'):
            self.run_tortoise('revert', files)
            return
        if not util.use_native():
            return
        self.run_command('revert -R', files)

    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the command should be visible"""
        return not util.prefer_tortoise('revert') and super().is_visible(paths, group, index)


class HypnoSvnRevertCommand(HypnoSvnCommand):
    """Reverts changes made to the working copy"""

    def __init__(self, window):
        """Initialize the command object"""
        super().__init__(window)
        self.svn_name = 'Revert'
        self.tests = {
            'versionned': True,
            'enabled': True
        }
        self.files = None

    def revert(self):
        """Runs the revert command on the sepcified files."""
        self.run_command('revert', self.files)

    def on_complete(self, values):
        """Handles completion of the MultiSelect"""
        self.files = values
        self.revert()

    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug(self.svn_name)
        files = util.get_files(paths, group, index)
        if util.prefer_tortoise('revert'):
            self.run_tortoise('revert', files)
            return
        if not util.use_native():
            return
        self.files = files
        if self.is_file(files):
            self.revert()
        else:
            self.select_changes()


class HypnoSvnCleanupCommand(HypnoSvnCommand):
    """Cleans up broken repos"""

    def __init__(self, window):
        """Initialize the command object"""
        super().__init__(window)
        self.svn_name = 'Cleanup'
        self.tests = {
            'versionned': True,
            'enabled': True
        }

    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug(self.svn_name)
        files = util.get_files(paths, group, index)
        if util.prefer_tortoise('cleanup'):
            self.run_tortoise('cleanup', files)
            return
        if not util.use_native():
            return
        self.run_command('cleanup', files)


class HypnoSvnLockCommand(HypnoSvnCommand):
    """Gets a lock on the selected files"""

    def __init__(self, window):
        """Initialize the command object"""
        super().__init__(window)
        self.svn_name = 'Lock'
        self.tests = {
            'versionned': True,
            'enabled': True
        }

    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug(self.svn_name)
        files = util.get_files(paths, group, index)
        if util.prefer_tortoise('lock'):
            self.run_tortoise('lock', files)
            return
        if not util.use_native():
            return
        self.run_command('lock', files)


class HypnoSvnStealLockCommand(HypnoSvnCommand):
    """Steals a lock from another user"""

    def __init__(self, window):
        """Initialize the command object"""
        super().__init__(window)
        self.svn_name = 'Steal Lock'
        self.tests = {
            'versionned': True,
            'native': True
        }

    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug(self.svn_name)
        if not util.use_native():
            return
        files = util.get_files(paths, group, index)
        self.run_command('lock --force', files)


class HypnoSvnUnlockCommand(HypnoSvnCommand):
    """Unlocks the repo"""

    def __init__(self, window):
        """Initialize the command object"""
        super().__init__(window)
        self.svn_name = 'Unlock'
        self.tests = {
            'versionned': True,
            'enabled': True
        }

    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug(self.svn_name)
        files = util.get_files(paths, group, index)
        if util.prefer_tortoise('unlock'):
            self.run_tortoise('unlock', files)
            return
        if not util.use_native():
            return
        self.run_command('unlock', files)


class HypnoSvnDiffCommand(HypnoSvnCommand):
    """Lists the changes to a working copy file"""

    def __init__(self, window):
        """Initialize the command object"""
        super().__init__(window)
        self.svn_name = 'Diff'
        self.tests = {
            'versionned': True,
            'enabled': True,
            'file': True,
            'changed': True
        }

    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug(self.svn_name)
        files = util.get_files(paths, group, index)
        if util.prefer_tortoise('diff'):
            self.run_tortoise('diff', files)
            return
        if not util.use_native():
            return
        self.run_command('diff', files)


class HypnoSvnDiffPreviousCommand(HypnoSvnCommand):
    """Lists the changes between latest and previous revisions"""

    def __init__(self, window):
        """Initialize the command object"""
        super().__init__(window)
        self.svn_name = 'Diff With Previous'
        self.tests = {
            'versionned': True,
            'enabled': True,
            'file': True,
            'changed': False
        }

    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug(self.svn_name)
        files = util.get_files(paths, group, index)
        p = self.run_command('info', files, False, False)
        output = p.output()
        current = re.search(INFO_PARSE_REVISION, output).group(1)
        last = str(int(re.search(INFO_PARSE_LAST_CHANGE, output).group(1)) - 1)
        if util.prefer_tortoise('diff'):
            self.run_tortoise('diff /startrev:' + last + ' /endrev:' + current, files)
            return
        if not util.use_native():
            return
        self.run_command('diff -r ' + last + ':' + current, files)


class HypnoSvnRenameCommand(HypnoSvnCommand):
    """Renames a file or folder in SVN"""

    def __init__(self, window):
        """Initialize the command object"""
        super().__init__(window)
        self.svn_name = 'Rename'
        self.tests = {
            'versionned': True,
            'enabled': True,
            'single': True
        }

    def on_done_input(self, value):
        """Handles completion of an input panel"""
        src = os.path.join(self.head, self.tail)
        dest = os.path.join(self.head, value)
        self.run_command('rename --parents', [src, dest])

    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug(self.svn_name)
        files = util.get_files(paths, group, index)
        if util.prefer_tortoise('rename'):
            self.run_tortoise('rename', files)
            return
        if not util.use_native():
            return
        self.head, self.tail = os.path.split(files[0])
        sublime.active_window().show_input_panel('Rename...', self.tail, self.on_done_input, self.nothing, self.nothing)


class HypnoSvnBlameCommand(HypnoSvnCommand):
    """Checks who has made the last changes to each line in a file"""

    def __init__(self, window):
        """Initialize the command object"""
        super().__init__(window)
        self.svn_name = 'Blame'
        self.tests = {
            'versionned': True,
            'enabled': True
        }

    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug(self.svn_name)
        files = util.get_files(paths, group, index)
        if util.prefer_tortoise('blame'):
            self.run_tortoise('blame', files)
            return
        self.run_command('blame', files)

    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the command should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['enabled']


class HypnoSvnConflictEditorCommand(HypnoSvnCommand):
    """Opens the TortoiseSVN conflict editor"""

    def __init__(self, window):
        """Initialize the command object"""
        super().__init__(window)
        self.svn_name = 'Conflict Editor'
        self.tests = {
            'versionned': True,
            'tortoise': True
        }

    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug(self.svn_name)
        files = util.get_files(paths, group, index)
        self.run_tortoise('conflicteditor', files)


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

    def __init__(self, window):
        """Initialize the command object"""
        super().__init__(window)
        self.svn_name = 'Resolve'
        self.tests = {
            'versionned': True,
            'enabled': True,
            'single': True
        }

    def on_select(self, index):
        """Handles which option for resolution"""
        self.run_command('resolve -R --accept ' + HypnoSvnResolveCommand.options[index], self.files)

    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug(self.svn_name)
        files = util.get_files(paths, group, index)
        if util.use_tortoise():
            self.run_tortoise('resolve', files)
            return
        self.files = files
        sublime.active_window().show_quick_panel(HypnoSvnResolveCommand.options, self.on_select)


class HypnoSvnCheckoutCommand(HypnoSvnCommand):
    """Checks out a repo"""
    def __init__(self, window):
        """Initialize the command object"""
        super().__init__(window)
        self.svn_name = 'Checkout'
        self.tests = {
            'versionned': False,
            'enabled': True,
            'folder': True
        }

    def on_done_input(self, value):
        """Handles completion of the input panel"""
        self.run_command('checkout', self.files)

    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug(self.svn_name)
        files = util.get_files(paths, group, index)
        if util.prefer_tortoise('checkout'):
            self.run_tortoise('checkout', files)
            return
        if not util.use_native():
            return
        self.files = files
        sublime.active_window().show_input_panel('Checkout from...', 'http://', self.on_done_input, self.nothing, self.nothing)
