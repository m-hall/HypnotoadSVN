import sublime
import sublime_plugin
import os
import re
from . import svn_commands
from .lib import util, thread, settings, output, panels

INFO_PARSE_URL = r"URL: ([^\n]*)"

def get_branches():
    data = sublime.active_window().project_data()
    if not data:
        return []
    return data.get('HypnotoadSVN', {}).get('branches', [])
def add_branch(branch):
    data = sublime.active_window().project_data()
    if data is None:
        data = {
            "HypnotoadSVN": {
                "branches": [branch]
            }
        }
    else:
        hypno = data.get("HypnotoadSVN")
        if hypno is None:
            data.set("HypnotoadSVN", {
                "branches": [branch]
            })
        else:
            branches = hypno.get("branches")
            if branches is None:
                branches = [branch]
            else:
                branches.append(branch)
            hypno['branches'] = branches
        data['HypnotoadSVN'] = hypno
    sublime.active_window().set_project_data(data)


class HypnoSvnMergeCommand(svn_commands.HypnoSvnCommand):
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
        """Checks if the command should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['single'] and tests['enabled']

class HypnoSvnSwitchCommand(svn_commands.HypnoSvnCommand):
    """Switches the working copy to a different branch"""
    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug('Switch')
        files = util.get_files(paths, group, index)
        self.name = "Switch"
        if util.use_tortoise():
            self.run_tortoise("switch", files)
            return
        self.run_command('switch', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the command should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['single'] and tests['enabled']

class HypnoSvnBranchCommand(svn_commands.HypnoSvnCommand):
    """Creates a new branch"""
    def on_complete(self, proc):
        if proc.returncode != 0:
            sublime.error_message('Branch creation failed')
            return
        add_branch(self.branch)
    def get_url(self, file):
        """Gets the svn url for a file"""
        p = self.run_command('info', [file], False, False)
        m = re.search(INFO_PARSE_URL, p.output(), re.M)
        return m.group(1)
    def on_done_input(self, value):
        """Handles completion of an input panel"""
        if value is None or not util.is_url(value):
            sublime.status_message("Invalid URL")
            return
        self.name = "Branch"
        items = [self.url, value]
        self.branch = value
        thread.Process(self.name, 'svn copy', items, True, True, self.on_complete)
    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug('Branch')
        files = util.get_files(paths, group, index)
        self.name = "Branch"
        if util.use_tortoise():
            self.run_tortoise("branch", files)
            return
        self.url = self.get_url(files[0])
        sublime.active_window().show_input_panel('Branch to...', self.url, self.on_done_input, self.nothing, self.nothing)
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the command should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['single'] and tests['enabled']