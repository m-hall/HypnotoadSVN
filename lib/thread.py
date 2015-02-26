import sublime
import re
from subprocess import Popen, PIPE
from threading import Thread, Timer
from . import output

TIME_INTERVAL = 0.05
LOADING_SIZE = 7

class Process:
    active_processes = []
    def __init__(self, name, cmd, paths=None, log=True, async=False, on_complete=None):
        self.name = name
        self.cmd = cmd
        self.paths = paths
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
        self.process = Popen(self.command, stdout=PIPE, stderr=PIPE, shell=True, universal_newlines=True)
        if async:
            Process.active_processes.append(self)
            self.check_status()
        else:
            self.finish()

    def get_path(self, paths):
        path = None
        if paths:
            path = '"' + '" "'.join(paths) + '"'
        else:
            view = sublime.active_window().active_view()
            path = view.file_name() if view else None
        return path

    def finish(self):
        out, error = self.process.communicate()
        self.outputText = out
        self.errorText = error
        self.done = True
        if self.log:
            output.add_result(self.output())
            output.add_error(self.error(), self.process.returncode)
            output.end_command()

    def check_status(self):
        if self not in Process.active_processes:
            return
        if self.process.stdout:
            line = self.process.stdout.readline().strip('\r\n')
            self.lines.append(line)
            if self.log and line:
                output.add_result_message(line)
        if self.is_done():
            last = self.process.stdout.read().strip('\r\n')
            self.outputText = "\n".join(self.lines) + "\n" + last
            Process.active_processes.remove(self)
            sublime.status_message("Complete: " + self.name)
            if self.on_complete is not None:
                self.on_complete(self)
            if self.log:
                output.add_result_message(last)
                output.add_error(self.error(), self.process.returncode)
                output.end_command()
        else:
            if LOADING_SIZE > 0:
                n = abs(self.loading - LOADING_SIZE)
                sublime.status_message("Running: " + self.name + "  [" + " " * (LOADING_SIZE - n) + "=" + " " * n + "]")
                self.loading = (self.loading + 1) % (LOADING_SIZE * 2)

            self.timer = Timer(TIME_INTERVAL, self.check_status)
            self.timer.start()

    def output(self):
        if self.outputText is not None:
            return self.outputText
        if not self.is_done():
            return self.process.stdout.read()
        out = self.process.stdout.read()
        if out is not None:
            self.outputText = out
            return self.outputText
        return None

    def error(self):
        if self.errorText is not None:
            return self.errorText
        if not self.is_done():
            return self.process.stderr.read()
        error = self.process.stderr.read()
        if error is not None:
            self.errorText = error
            return self.errorText
        return None

    def is_done(self):
        if not self.done:
            self.done = self.process.poll() is not None
        return self.done

    def terminate(self):
        if not self.is_done():
            self.process.terminate()
        Process.active_processes.remove(self)

def terminate_all():
    for proc in Process.active_processes:
        proc.terminate()