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
        Process.active_processes.append(self)
        if log:
            output.add_command(self.name)
            output.add_message(output.indent(cmd + ' ' + self.get_path(paths)))
            output.add_files(self.paths)
            output.add_result_section()
        self.process = Popen(cmd + ' ' + self.get_path(paths), stdout=PIPE, stderr=PIPE, shell=True, bufsize=20)
        if async:
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
        self.outputText = out.decode('UTF-8')
        self.errorText = error.decode('UTF-8')
        self.done = True
        Process.active_processes.remove(self)
        if self.log:
            output.add_result(self.output())
            output.add_error(self.error(), self.process.returncode)
            output.end_command()

    def check_status(self):
        if self.log and self.process.stdout.raw:
            line = self.process.stdout.raw.readline().decode("UTF-8").strip()
            if line:
                output.add_result_message(line)
        if self.is_done():
            Process.active_processes.remove(self)
            sublime.status_message("Complete: " + self.name)
            if self.on_complete is not None:
                self.on_complete(self)
            if self.log:
                output.add_result_message(self.process.stdout.raw.read().decode("UTF-8").strip())
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
            self.outputText = out.decode('UTF-8')
            return self.outputText
        return None

    def error(self):
        if self.errorText is not None:
            return self.errorText
        if not self.is_done():
            return self.process.stderr.read()
        error = self.process.stderr.read()
        if error is not None:
            self.errorText = error.decode('UTF-8')
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