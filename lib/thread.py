import sublime
import re
from subprocess import Popen, PIPE
from threading import Thread, Timer
from . import output, util

TIME_INTERVAL = 0.05
LOADING_SIZE = 7

class Process(Thread):
    active_processes = []
    def __init__(self, name, cmd, paths=None, log=True, async=False, on_complete=None):
        Thread.__init__(self)
        self.name = name
        self.cmd = cmd
        self.paths = paths
        self.async = async
        self.done = False
        self.log = log
        self.lines = []
        self.outputText = None
        self.errorText = None
        self.loading = 0
        self.on_complete = on_complete
        if log:
            output.add_command(self.name)
            output.add_message(output.indent(cmd + ' ' + self.get_path(paths)))
            output.add_files(self.paths)
            output.add_result_section()
        if not paths:
            self.command = cmd
        else:
            self.command = cmd + ' ' + self.get_path(paths)
        util.debug(self.command)
        if self.async:
            self.start()
        else:
            self.run()

    def runSync(self):
        self.process = Popen(self.command, stdout=PIPE, stderr=PIPE, shell=True, universal_newlines=True)
        self.outputText, self.errorText = self.process.communicate()
        if self.log:
            output.add_result_message(self.outputText)
        self.complete()

    def run(self):
        self.process = Popen(self.command, stdout=PIPE, stderr=PIPE, shell=True, universal_newlines=True)
        Process.active_processes.append(self)
        for line in self.process.stdout:
            self.lines.append(line)
            if self.log:
                output.add_result_message(line.strip('\r\n'))
        self.outputText = "\n".join(self.lines)
        self.errorText = self.process.stderr.read()
        self.complete()

    def get_path(self, paths):
        path = None
        if paths:
            path = '"' + '" "'.join(paths) + '"'
        else:
            view = sublime.active_window().active_view()
            path = view.file_name() if view else None
        return path

    def complete(self):
        if self.done:
            return
        util.debug(self.command + " DONE")
        self.done = True
        if self in Process.active_processes:
            Process.active_processes.remove(self)
        if self.log:
            output.add_error(self.error(), self.process.returncode)
            output.end_command()
        if self.on_complete is not None:
            self.on_complete(self)

    def check_status(self):
        if self not in Process.active_processes:
            return
        if self.done:
            sublime.status_message("Complete: " + self.name)
        else:
            if LOADING_SIZE > 0:
                n = abs(self.loading - LOADING_SIZE)
                sublime.status_message("Running: " + self.name + "  [" + " " * (LOADING_SIZE - n) + "=" + " " * n + "]")
                self.loading = (self.loading + 1) % (LOADING_SIZE * 2)

            self.timer = Timer(TIME_INTERVAL, self.check_status)
            self.timer.start()

    def output(self):
        return self.outputText

    def error(self):
        return self.errorText

    def terminate(self):
        if not self.done:
            self.process.terminate()
        self.complete()

def terminate_all():
    for proc in Process.active_processes:
        proc.terminate()