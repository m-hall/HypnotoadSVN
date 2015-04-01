import sublime
import sublime_plugin
import os
import re
from functools import partial
from . import svn_commands
from .lib import util, thread, settings, output, panels

CHERRYPICK_FORMAT = r'^(\-?\d+,?)+$'
REVISIONS_FORMAT = r'^(HEAD|BASE|COMMITTED|PREV|\d+):?(HEAD|BASE|COMMITTED|PREV|\d+)?$'


def nothing(nothing1=None, nothing2=None, nothing3=None, **args):
    """Does nothing, just a placeholder for things I don't handle"""
    return


def get_branches():
    """Get the branches listed in the project"""
    data = sublime.active_window().project_data()
    if not data:
        return []
    return list(data.get('HypnotoadSVN', {}).get('branches', []))


def add_branch(branch):
    """Adds a branch to the project"""
    if branch is None or not util.is_url(branch):
        sublime.status_message('Invalid URL')
        return False
    data = sublime.active_window().project_data()
    if data is None:
        data = {
            'HypnotoadSVN': {
                'branches': [branch]
            }
        }
    else:
        hypno = data.get('HypnotoadSVN')
        if hypno is None:
            data['HypnotoadSVN'] = {
                'branches': [branch]
            }
        else:
            branches = hypno.get('branches')
            if branches is None:
                branches = [branch]
            else:
                if branch in branches:
                    branches.remove(branch)
                branches.insert(0, branch)
            hypno['branches'] = branches
    sublime.active_window().set_project_data(data)
    return True


def picked_branch(on_complete, branch):
    """Moves a branch to the top of the list after being picked"""
    if not add_branch(branch):
        sublime.error_message('Branch is not a valid URL')
        return
    on_complete(branch)


def pick_branch(current, on_complete):
    """Picks a branch from the project"""
    add_branch(current)
    branches = get_branches()
    branches.remove(current)
    picked = partial(picked_branch, on_complete)
    if len(branches) > 0:
        panels.SelectOrAdd(branches, picked, add_base=current, input_name='Branch...')
    else:
        sublime.active_window().show_input_panel('Branch...', current, picked, nothing, nothing)


class HypnoSvnMergeCommand(svn_commands.HypnoSvnCommand):
    """Merges changes from the repo to the working copy"""

    def __init__(self, window):
        """Initialize the command object"""
        super().__init__(window)
        self.svn_name = 'Merge'
        self.tests = {
            'versionned': True,
            'enabled': True,
            'single': True
        }
        self.files = None
        self.url = None
        self.branch = None

    def on_revisions_picked(self, value):
        """Verifies that the revisions are valid format then runs the merge"""
        args = value.split(' ')
        argserr = []
        params = []
        for a in args:
            if re.match(CHERRYPICK_FORMAT, a):
                params.append('-c ' + a)
            elif re.match(REVISIONS_FORMAT, a):
                params.append('-r ' + a)
            elif (a != ''):
                argserr.append(a)
        if len(argserr) != 0:
            sublime.error_message('These revisions argument are not in a valid format:\n ' + '\n '.join(argserr))
            return
        self.run_command('merge ' + ' '.join(params), [self.branch, self.files[0]])

    def pick_revisions(self):
        """Prompts the user for revision numbers"""
        sublime.active_window().show_input_panel('Revisions...', '', self.on_revisions_picked, self.nothing, self.nothing)

    def on_branch_picked(self, value):
        """Handles picking the branch"""
        self.branch = value
        self.pick_revisions()

    def verify_changes(self, files):
        """If the files are changed, checks with the user to confirm that they really want to merge."""
        if self.is_changed(files):
            message = 'There are changed files, are you sure you want to merge to this location?'
            if self.is_file(files):
                message = 'This file has been modified, are you sure you want to merge to this file?'
            if not sublime.ok_cancel_dialog(message):
                return False
        return True

    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug(self.svn_name)
        files = util.get_files(paths, group, index)
        if util.prefer_tortoise('merge'):
            self.run_tortoise('merge', files)
            return
        if not util.use_native():
            return
        if not self.verify_changes(files):
            sublime.status_message('Merge cancelled by user.')
            return
        self.files = files
        self.url = self.get_url(files[0])
        pick_branch(self.url, self.on_branch_picked)


class HypnoSvnMergeReintegrateCommand(HypnoSvnMergeCommand):
    """Merges reintegrate changes from branch to its origin"""

    def __init__(self, window):
        """Initialize the command object"""
        super().__init__(window)
        self.svn_name = 'Merge reintegrate'
        self.tests = {
            'versionned': True,
            'native': True,
            'single': True
        }
        self.native_only = 'merge'
        self.files = None
        self.url = None
        self.branch = None

    def on_revisions_picked(self, value):
        """Verifies that the revisions are valid format then runs the merge"""
        args = value.split(' ')
        argserr = []
        params = []
        for a in args:
            if re.match(CHERRYPICK_FORMAT, a):
                params.append('-c ' + a)
            elif re.match(REVISIONS_FORMAT, a):
                params.append('-r ' + a)
            elif (a != ''):
                argserr.append(a)
        if len(argserr) != 0:
            sublime.error_message('These revisions argument are not in a valid format:\n ' + '\n '.join(argserr))
            return
        self.run_command('merge --reintegrate ' + ' '.join(params), [self.branch, self.files[0]])
    
    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug(self.svn_name)
        files = util.get_files(paths, group, index)
        if not self.verify_changes(files):
            sublime.status_message('Merge cancelled by user.')
            return
        self.files = files
        self.url = self.get_url(files[0])
        pick_branch(self.url, self.on_branch_picked)


class HypnoSvnSwitchCommand(svn_commands.HypnoSvnCommand):
    """Switches the working copy to a different branch"""

    def __init__(self, window):
        """Initialize the command object"""
        super().__init__(window)
        self.svn_name = 'Switch'
        self.tests = {
            'versionned': True,
            'enabled': True,
            'single': True
        }
        self.files = None
        self.url = None

    def on_branch_picked(self, value):
        """Handles selecting a value"""
        self.run_command('switch', [value, self.files[0]])

    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug(self.svn_name)
        files = util.get_files(paths, group, index)
        if util.prefer_tortoise('switch'):
            self.run_tortoise('switch', files)
            return
        self.files = files
        self.url = self.get_url(files[0])
        pick_branch(self.url, self.on_branch_picked)


class HypnoSvnSwitchIgnoreAncestryCommand(svn_commands.HypnoSvnCommand):
    """Switches the working copy to a different branch"""

    def __init__(self, window):
        """Initialize the command object"""
        super().__init__(window)
        self.svn_name = 'Switch ignore ancestry'
        self.tests = {
            'versionned': True,
            'native': True,
            'single': True
        }
        self.native_only = 'switch'
        self.files = None
        self.url = None

    def on_branch_picked(self, value):
        """Handles selecting a value"""
        self.run_command('switch --ignore-ancestry ', [value, self.files[0]])


    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug(self.svn_name)
        files = util.get_files(paths, group, index)
        self.files = files
        self.url = self.get_url(files[0])
        pick_branch(self.url, self.on_branch_picked)


class HypnoSvnBranchCommand(svn_commands.HypnoSvnCommand):
    """Creates a new branch"""

    def __init__(self, window):
        """Initialize the command object"""
        super().__init__(window)
        self.svn_name = 'Branch'
        self.tests = {
            'versionned': True,
            'enabled': True,
            'single': True
        }
        self.url = None
        self.branch = None

    def escape(self, message):
        """Escapes quotes in a commit message."""
        return message.replace('"', '\\"')

    def on_complete(self, proc):
        """If the branch was successfully created, add it to the list of project branches"""
        if proc.returncode != 0:
            sublime.error_message('Branch creation failed')
            return
        add_branch(self.branch)

    def on_message_input(self, value):
        """Handles completion of an input panel"""
        self.message = value
        minSize = settings.get_native('commitMessageSize', 0)
        if minSize > 0 and len(value) < minSize:
            sublime.status_message('Commit message too short')
            return
        items = [self.url, self.branch]
        self.run_command('copy -m "' + self.escape(self.message) + '"', items, on_complete=self.on_complete)

    def on_done_input(self, value):
        """Handles completion of an input panel"""
        if value is None or not util.is_url(value):
            sublime.status_message('Invalid URL')
            return
        self.branch = value
        sublime.active_window().show_input_panel('Copy message', 'Create branch \'branches/name\'', self.on_message_input, self.nothing, self.nothing)

    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug(self.svn_name)
        files = util.get_files(paths, group, index)
        if util.prefer_tortoise('branch'):
            self.run_tortoise('branch', files)
            return
        self.url = self.get_url(files[0])
        add_branch(self.url)
        sublime.active_window().show_input_panel('Branch to...', self.url, self.on_done_input, self.nothing, self.nothing)
