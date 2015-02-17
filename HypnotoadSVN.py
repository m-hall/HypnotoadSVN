import sublime
import sublime_plugin
import os
import os.path
import subprocess
import re

class HypnoCommand(sublime_plugin.WindowCommand):
    def get_path(self, paths):
        path = None
        if paths:
            path = '*'.join(paths)
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
    def run(self, cmd, paths=None, isHung=False):
        dir = self.get_path(paths)

        if not dir:
            return

        settings = self.get_setting()
        print(settings)
        tortoiseproc_path = settings.get('tortoiseproc_path')
        print(tortoiseproc_path)

        if not os.path.isfile(tortoiseproc_path):
            sublime.error_message('can\'t find TortoiseProc.exe,'
                ' please config setting file' '\n   --HypnotoadSVN')
            raise

        proce = subprocess.Popen('"' + tortoiseproc_path + '"' + 
            ' /command:' + cmd + ' /path:"%s"' % dir , stdout=subprocess.PIPE)

        # This is required, cause of ST must wait TortoiseSVN update then revert
        # the file. Otherwise the file reverting occur before SVN update, if the
        # file changed the file content in ST is older.
        #if isHung:
            #proce.communicate()

    def get_setting(self):
        return sublime.load_settings('HypnotoadSVN.sublime-settings')

    def get_status (self, paths):
        dir = self.get_path(paths)

        if not dir:
            return

        proce = subprocess.Popen('svn status "%s"' % dir, stdout=subprocess.PIPE, shell=False, creationflags=0x08000000)
        out, err = proce.communicate()
        return out

class MutatingSvnCommand(SvnCommand):
    def run(self, cmd, paths=None):
        SvnCommand.run(self, cmd, paths, True)

        #self.view = sublime.active_window().active_view()
        #row, col = self.view.rowcol(self.view.sel()[0].begin())
        #self.lastLine = str(row + 1);
        #sublime.set_timeout(self.revert, 100)

    def revert(self):
        self.view.run_command('revert')
        sublime.set_timeout(self.revertPoint, 600)

    def revertPoint(self):
        self.view.window().run_command('goto_line', {'line':self.lastLine})

class SvnFileCommand(SvnCommand):
    def is_visible(self, paths=None):
        return true

class SvnUpdateCommand(MutatingSvnCommand):
    def run(self, paths=None):
        settings = self.get_setting()
        closeonend = ('3' if True == settings.get('autoCloseUpdateDialog')
            else '0')
        MutatingSvnCommand.run(self, 'update /closeonend:' + closeonend, 
            paths)


class SvnCommitCommand(SvnCommand):
    def run(self, paths=None):
        settings = self.get_setting()
        closeonend = ('3' if True == settings.get('autoCloseCommitDialog')
            else '0')
        SvnCommand.run(self, 'commit /closeonend:' + closeonend, paths)


class SvnRevertCommand(MutatingSvnCommand):
    def run(self, paths=None):
        MutatingSvnCommand.run(self, 'revert', paths)


class SvnLogCommand(SvnCommand):
    def run(self, paths=None):
        SvnCommand.run(self, 'log', paths)


class SvnSwitchCommand(SvnCommand):
    def run(self, paths=None):
        SvnCommand.run(self, 'switch', paths)


class SvnDiffCommand(SvnCommand):
    def run(self, paths=None):
        SvnCommand.run(self, 'diff', paths)

    def is_visible(self, paths=None):
        file = self.get_path(paths)
        realFile = os.path.isfile(file)
        if not realFile:
            return False
        status = self.get_status(paths)
        return len(status) > 0

class SvnDiffPreviousCommand(SvnCommand):
    def run(self, paths=None):
        last = int(self.get_last(paths)) - 1
        current = self.get_current(paths)
        SvnCommand.run(self, 'diff /startrev:' + str(last) + ' /endrev:'+current, paths)

    def is_visible(self, paths=None):
        file = self.get_path(paths)
        realFile = os.path.isfile(file)
        if not realFile:
            return False
        status = self.get_status(paths)
        return len(status) == 0

    def get_current (self, paths):
        dir = self.get_path(paths)

        if not dir:
            return

        proce = subprocess.Popen('svnversion "%s"' % dir, stdout=subprocess.PIPE, shell=False, creationflags=0x08000000)
        out, err = proce.communicate()
        return out.decode('UTF-8')

    def get_last (self, paths):
        dir = self.get_path(paths)

        if not dir:
            return

        proce = subprocess.Popen('svn info "%s"' % dir, stdout=subprocess.PIPE, shell=False, creationflags=0x08000000)
        out, err = proce.communicate()
        p = re.compile(r"Last Changed Rev: (\d+)", re.MULTILINE)
        versionLine = p.search(out.decode('UTF-8'))
        return versionLine.group(1)


class SvnBlameCommand(SvnCommand):
    def run(self, paths=None):
        view = sublime.active_window().active_view()
        row = view.rowcol(view.sel()[0].begin())[0] + 1

        SvnCommand.run(self, 'blame /line:' + str(row), paths)

    def is_visible(self, paths=None):
        file = self.get_path(paths)
        return os.path.isfile(file) if file else False


class SvnAddCommand(SvnCommand):
    def run(self, paths=None):
        SvnCommand.run(self, 'add', paths)

class SvnDeleteCommand(SvnCommand):
    def run(self, paths=None):
        SvnCommand.run(self, 'remove', paths)

class SvnMergeCommand(SvnCommand):
    def run(self, paths=None):
        SvnCommand.run(self, 'merge', paths)

class SvnBranchCommand(SvnCommand):
    def run(self, paths=None):
        SvnCommand.run(self, 'copy', paths)

class SvnStatusCommand(SvnCommand):
    def run(self, paths=None):
        SvnCommand.run(self, 'repostatus', paths)

class SvnCleanupCommand(SvnCommand):
    def run(self, paths=None):
        SvnCommand.run(self, 'cleanup', paths)

class SvnRenameCommand(SvnCommand):
    def run(self, paths=None):
        SvnCommand.run(self, 'rename', paths)

class SvnResolveCommand(SvnCommand):
    def run(self, paths=None):
        SvnCommand.run(self, 'resolve', paths)

class SvnConflictEditorCommand(SvnCommand):
    def run(self, paths=None):
        SvnCommand.run(self, 'conflicteditor', paths)

class SvnBrowseCommand(SvnCommand):
    def run(self, paths=None):
        SvnCommand.run(self, 'repobrowser', paths)

class SvnLockCommand(SvnCommand):
    def run(self, paths=None):
        SvnCommand.run(self, 'lock', paths)

class SvnUnlockCommand(SvnCommand):
    def run(self, paths=None):
        SvnCommand.run(self, 'unlock', paths)

class SvnSettingsCommand(SvnCommand):
    def run(self, paths=None):
        SvnCommand.run(self, 'settings', paths)
