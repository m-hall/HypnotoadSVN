import sublime
import sublime_plugin
import os
import os.path
import subprocess
import re
from . import SvnView

SVNView = SvnView.SvnView

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

class NativeSvnCommand(HypnoCommand):
    def run_command(self, cmd):
        command = 'svn ' + cmd
        print(command)
        proce = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        return proce.communicate()
    def run_path_command(self, cmd, paths):
        dir = self.get_path(paths)
        if not dir:
            return
        command = cmd + ' %s' % dir
        return self.run_command(command)
    def test_versionned(self, result):
        return 'not a working copy' not in result
    def is_versionned(self, paths=None):
        result, error = self.run_path_command('info', paths)
        return self.test_versionned(result) and self.test_versionned(error)
    def is_visible(self, cmd="", paths=None, versionned=None, fileType=None):
        visible = True
        if versionned == True:
            visible = visible and self.is_versionned()
        elif versionned == False:
            visible = visible and not self.is_versionned()
        
        if fileType != None:
            if paths == None:
                return False
            file = self.get_path(paths)
            if fileType == 'folder':
                visible = visible and not os.path.isfile(file)
            elif fileType == 'file':
                visible = visible and os.path.isfile(file)

        return visible
    def run(self, cmd="", paths=None):
        result, error = self.run_path_command(cmd, paths)

        if error:
            if not self.test_versionned(error):
                sublime.error_message('File is not versionned.')
            else:
                sublime.error_message(error.decode('UTF-8'))
            return

        sublime.status_message('Command successfully completed')

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

        if os.name == 'nt':
            proce = subprocess.Popen('svn status "%s"' % dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, creationflags=0x08000000)
        else:
            proce = subprocess.Popen('svn status "%s"' % dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
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

# class SvnUpdateCommand(MutatingSvnCommand):
#     def run(self, paths=None):
#         settings = self.get_setting()
#         closeonend = ('3' if True == settings.get('autoCloseUpdateDialog')
#             else '0')
#         MutatingSvnCommand.run(self, 'update /closeonend:' + closeonend, 
#             paths)


class SvnCommitCommand(SvnCommand):
    def run(self, paths=None):
        settings = self.get_setting()
        closeonend = ('3' if True == settings.get('autoCloseCommitDialog')
            else '0')
        SvnCommand.run(self, 'commit /closeonend:' + closeonend, paths)


class SvnDiffCommand(SvnCommand):
    def run(self, paths=None):
        SvnCommand.run(self, 'diff', paths)

    def is_visible(self, paths=None):
        # if not super(SvnDiffCommand, self).is_visible(paths):
        #     return false
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

        if os.name == 'nt':
            proce = subprocess.Popen('svnversion "%s"' % dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, creationflags=0x08000000)
        else:
            proce = subprocess.Popen('svnversion "%s"' % dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = proce.communicate()
        return out.decode('UTF-8')

    def get_last (self, paths):
        dir = self.get_path(paths)

        if not dir:
            return

        if os.name == 'nt':
            proce = subprocess.Popen('svn info "%s"' % dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, creationflags=0x08000000)
        else:
            proce = subprocess.Popen('svn info "%s"' % dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = proce.communicate()
        p = re.compile(r"Last Changed Rev: (\d+)", re.MULTILINE)
        versionLine = p.search(out.decode('UTF-8'))
        return versionLine.group(1)

class SvnUpdateCommand(NativeSvnCommand):
    def run(self, paths=None):
        result, error = self.run_path_command('update', paths)
        SVNView.add_command('SVN Update')
        SVNView.add_result(result.decode('UTF-8'))
        SVNView.add_error(error.decode('UTF-8'))
        SVNView.end_command()

    def is_visible(self, paths=None):
        return True #super(SvnCommand, self).is_visible('update', paths, True)