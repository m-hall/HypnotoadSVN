import sublime
from subprocess import Popen, PIPE
from threading import Thread, Timer
from . import output, util

TIME_INTERVAL = 0.05
LOADING_SIZE = 7

class Process(Thread):
    """A threaded process"""
    active_processes = []
    def __init__(self, name, cmd, paths=None, log=True, async=False, on_complete=None):
        """Initializes a Process object"""
        Thread.__init__(self)
        self.name = name
        self.cmd = cmd
        self.paths = paths
        self.async = async
        self.done = False
        self.log = log
        self.lines = []
        self.output_text = None
        self.error_text = None
        self.timer = None
        self.loading = 0
        self.returncode = None
        self.on_complete = on_complete
        if not paths:
            self.command = cmd + ' --non-interactive'
        else:
            self.command = cmd + ' --non-interactive ' + self.get_path(paths)
        if log:
            output.add_command(self.name, self.command)
            output.add_files(self.paths)
            output.add_result_section()
        util.debug(self.command)
        if self.async:
            self.start()
        else:
            self.run()

    def run(self):
        """Runs the process"""
        self.process = Popen(self.command, stdout=PIPE, stderr=PIPE, shell=True, universal_newlines=True)
        Process.active_processes.append(self)
        for line in self.process.stdout:
            self.lines.append(line)
            if self.log:
                output.add_result_message(line.strip('\r\n'))
        self.output_text = "\n".join(self.lines)
        self.error_text = self.process.stderr.read()
        self.process.communicate()
        self.complete()

    def get_path(self, paths):
        """Gets path for command arguments"""
        path = None
        if paths:
            path = '"' + '" "'.join(paths) + '"'
        else:
            view = sublime.active_window().active_view()
            path = view.file_name() if view else None
        return path

    def complete(self):
        """Handles the complete signal from a process"""
        if self.done:
            return
        util.debug(self.command + " DONE")
        self.done = True
        self.returncode = self.process.returncode
        if self in Process.active_processes:
            Process.active_processes.remove(self)
        if self.log:
            output.add_error(self.error(), self.process.returncode)
            output.end_command()
        if self.on_complete is not None:
            self.on_complete(self)

    def check_status(self):
        """Checks the status of a running process"""
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
        """Get output from the process"""
        return self.output_text

    def error(self):
        """Get error text from the process"""
        return self.error_text

    def terminate(self):
        """Terminates the process"""
        if not self.done:
            self.process.terminate()
        self.complete()

def terminate_all():
    """Terminates all active processes"""
    for proc in Process.active_processes:
        proc.terminate()
