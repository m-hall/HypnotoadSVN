import sublime
import sublime_plugin
import os
import re
from . import svn_commands
from .lib import util, thread, settings, output, panels

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
    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug('Branch')
        files = util.get_files(paths, group, index)
        self.name = "Branch"
        if util.use_tortoise():
            self.run_tortoise("branch", files)
            return
        self.run_command('copy', files)
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the command should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['single'] and tests['enabled']