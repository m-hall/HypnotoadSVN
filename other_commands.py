import sublime
import sublime_plugin
from .lib import thread


class HypnoKillProcessesCommand(sublime_plugin.WindowCommand):
    """A command that kills all of the running nativeSVN processes"""

    def run(self):
        """Runs the command"""
        thread.terminate_all()
