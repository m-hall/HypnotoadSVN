import sublime
import sublime_plugin
import os
import re
from . import svn_commands
from .lib import util, thread, settings, output, panels

CHERRYPICK_FORMAT = r"[\d:,\-\s]+"
REVISIONS_FORMAT = r"(HEAD|BASE|COMMITTED|PREV|\d+):?(HEAD|BASE|COMMITTED|PREV|\d+)?"

def get_branches():
    """Get the branches listed in the project"""
    data = sublime.active_window().project_data()
    if not data:
        return []
    return list(data.get('HypnotoadSVN', {}).get('branches', []))

def add_branch(branch):
    """Adds a branch to the project"""
    if branch is None or not util.is_url(branch):
        sublime.status_message("Invalid URL")
        return False
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
            data["HypnotoadSVN"] = {
                "branches": [branch]
            }
        else:
            branches = hypno.get("branches")
            if branches is None:
                branches = [branch]
            else:
                if branch in branches:
                    return True
                branches.append(branch)
            hypno['branches'] = branches
    sublime.active_window().set_project_data(data)
    return True

def nothing(nothing1=None, nothing2=None, nothing3=None, **args):
    """Does nothing, just a placeholder for things I don't handle"""
    return

def pick_branch(current, on_complete):
    """Picks a branch from the project"""
    add_branch(current)
    branches = get_branches()
    branches.remove(current)
    if len(branches) > 0:
        panels.SelectOrAdd(branches, on_complete, add_base=current, input_name='Branch...')
    else:
        sublime.active_window().show_input_panel('Branch...', current, on_complete, nothing, nothing)


class HypnoSvnMergeCommand(svn_commands.HypnoSvnCommand):
    """Merges changes from the repo to the working copy"""
    def on_revisions_picked(self, value):
        cherrypick = value.replace(' ', '')
        if re.match(CHERRYPICK_FORMAT, cherrypick):
            param = '-c ' + cherrypick
        elif re.match(REVISIONS_FORMAT, value):
            param = '-r ' + value
        else:
            sublime.error_message('Revisions are not in a valid format')
            return
        self.run_command('merge '+ param, [self.branch, self.files[0]])
    def pick_revisions(self):
        sublime.active_window().show_input_panel('Revisions...', '', self.on_revisions_picked, self.nothing, self.nothing)
    def on_branch_picked(self, value):
        if not add_branch(value):
            sublime.error_message('Branch is not a valid URL')
            return
        self.branch = value
        self.pick_revisions()
    def verify_changes(self, files):
        if self.is_changed(files):
            message = 'There are changed files, are you sure you want to merge to this location?'
            if self.is_file(files):
                message = 'This file has been modified, are you sure you want to merge to this file?'
            if not sublime.ok_cancel_dialog(message):
                return False
        return True
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
        if not self.verify_changes(files):
            sublime.status_message('Merge cancelled by user.')
            return

        self.files = files
        self.url = self.get_url(files[0])

        pick_branch(self.url, self.on_branch_picked)
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the command should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['single'] and tests['enabled']

class HypnoSvnSwitchCommand(svn_commands.HypnoSvnCommand):
    """Switches the working copy to a different branch"""
    def on_branch_picked(self, value):
        """Handles selecting a value"""
        add_branch(value)
        self.run_command('switch', [value, self.files[0]])
    def run(self, paths=None, group=-1, index=-1):
        """Runs the command"""
        util.debug('Switch')
        files = util.get_files(paths, group, index)
        self.name = "Switch"
        if util.use_tortoise():
            self.run_tortoise("switch", files)
            return
        self.files = files
        self.url = self.get_url(files[0])
        pick_branch(self.url, self.on_branch_picked)
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the command should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['single'] and tests['enabled']

class HypnoSvnBranchCommand(svn_commands.HypnoSvnCommand):
    """Creates a new branch"""
    def on_complete(self, proc):
        """If the branch was successfully created, add it to the list of project branches"""
        if proc.returncode != 0:
            sublime.error_message('Branch creation failed')
            return
        add_branch(self.branch)
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
        add_branch(self.url)
        sublime.active_window().show_input_panel('Branch to...', self.url, self.on_done_input, self.nothing, self.nothing)
    def is_visible(self, paths=None, group=-1, index=-1):
        """Checks if the command should be visible"""
        files = util.get_files(paths, group, index)
        tests = self.test_all(files)
        return tests['versionned'] and tests['single'] and tests['enabled']