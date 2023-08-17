"""
This module enable starting, killing and waiting for background processes. See
:py:class:`BackgroundProcessManager` for details. Use this through the singleton
value :py:data:`PROCESS_MGR` (its singleton nature is not enforced).
"""

import time
from multiprocessing import Process
from subprocess import Popen
from threading import Thread
from typing import Callable

import libroll as lib
from exithooks import EXIT_HOOKS_MGR


####################################################################################################

class BackgroundProcessManager:
    """
    Enables starting, killing and waiting for background processes. It also registers an atexit
    handler to kill all background processes on process exit.
    """

    ################################################################################################

    def __init__(self):
        self.processes = []
        """List of background processes that might still be running."""
        EXIT_HOOKS_MGR.register(self._exit_hook)

    ################################################################################################

    def start_py(
            self,
            descr: str,
            target: Callable,
            args: tuple[...],
            on_exit: Callable = None) \
            -> Process:
        """
        Starts and returns a new python background process, running the target function and passing
        the given arguments to it. If `on_exit` is specified, it will be called when the process
        exits (which is monitored in a separate thread).
        """
        process = Process(
            target=target,
            args=args,
            name=f"roll_py_wrapper({descr})")
        self.processes.append(process)
        process.start()

        if on_exit is not None:
            monitor = Thread(target=self.monitor_process_exit, args=(process, on_exit))
            monitor.daemon = True  # kill thread when main thread exits
            process.monitor = monitor  # only attach to process after starting, or pickling error!
            monitor.start()

        return process

    ################################################################################################

    def start(
            self,
            descr: str,
            command: str | list[str],
            on_exit: Callable = None,
            **kwargs) \
            -> Popen:
        """
        Starts and returns a new background process, running the given command. The parameters
        `descr`, `command` and `kwargs` are passed to
        :py:func:`lib.run` which is used to start the process, additionally specifying the
        `wait=False` option.

        If `on_exit` is specified, it will be called when the process exits (which is monitored in a
        separate thread).
        """
        process: Popen = lib.run(descr, command, **kwargs, wait=False)
        process.name = f"subprocess({descr})"
        self.processes.append(process)

        if on_exit is not None:
            monitor = Thread(target=self.monitor_process_exit, args=(process, on_exit))
            monitor.daemon = True  # kill thread when main thread exits
            process.monitor = monitor  # only attach to process after starting, or pickling error!
            monitor.start()

        return process

    ################################################################################################

    @staticmethod
    def is_alive(process: Process | Popen) -> bool:
        """
        Returns true if the given process is still running.
        """
        if isinstance(process, Process):
            return process.is_alive()
        else:
            return process.poll() is None

    ################################################################################################

    def monitor_process_exit(self, process: Process, on_exit: Callable):
        """
        Monitors the given process and calls the given function when the process exits.
        """
        while True:
            self._wait(process)
            if not self.is_alive(process):
                break
        if process in self.processes:
            # if not, it was killed by us, no need to notify
            on_exit()
            self.processes.remove(process)

    ################################################################################################

    def kill(self, process: Process, ensure: bool = False):
        """
        Tries to terminate the given process. If ensure is True, it will wait one second for the
        process to terminate, then will try to kill (different more forceful signal on Linux) the
        process if it is still alive. It will wait another second and log an error if the process
        is still alive.

        The process is removed from the list of background processes no matter what.
        """
        try:
            # Terminate process if alive
            if not self.is_alive(process):
                return
            process.terminate()

            if not ensure:
                return

            # Only printing now because it causes waiting
            lib.debug(f"Terminating {process.name}...")

            # Sleep then kill process if still alive
            time.sleep(1)
            if not self.is_alive(process):
                return
            process.kill()
            time.sleep(1)

            # Log if process is still alive
            if self.is_alive(process):
                print(f"Failed to promptly terminate {process.name}")
        finally:
            self.processes.remove(process)

    ################################################################################################

    @staticmethod
    def _wait(process: Process | Popen, timeout: int | None = None):
        if isinstance(process, Process):
            process.join(timeout)
        else:
            process.wait(timeout)

    ################################################################################################

    def wait(self, process: Process | Popen, timeout: int | None = None):
        """
        Waits for the given process to complete. If `timeout` is not None, the
        implementation waits at most this many seconds. If the join fails, an error is logged.
        """
        try:
            self._wait(process, timeout)
            if self.is_alive(process):
                if timeout is None:
                    print(f"Failed to wait for {process.name} to complete")
                else:
                    print(f"Process {process.name} didn't complete within {timeout} seconds")
        finally:
            self.processes.remove(process)

    ################################################################################################

    def _exit_hook(self, _exitcode: int):
        self.kill_all()

    ################################################################################################

    def kill_all(self):
        """
        Try to terminate (then kill — uses a different more forceful signal on Linux) all background
        processes. Acts like `kill` with `ensure=True` for all background processes.

        Clears the list of background processes before returning.
        """
        print("Terminating background processes...")
        try:
            # Try terminating all processes
            alive_count = 0
            for process in self.processes:
                if self.is_alive(process):
                    alive_count += 1
                    lib.debug(f"Terminating {process.name}")
                    process.terminate()

            # There was no process to terminate
            if alive_count == 0:
                return

            # Give them a second to terminate, then try to kill processes that are left
            time.sleep(1)
            alive_count = 0
            for process in self.processes:
                if self.is_alive(process):
                    alive_count += 1
                    lib.debug(f"Killing {process.name}")
                    process.kill()

            # There was no process to kill
            if alive_count == 0:
                return

            # There killed processes a second to terminate, then log if they are still alive
            time.sleep(1)
            for process in self.processes:
                if self.is_alive(process):
                    print(f"Failed to prompty kill {process.name}")
        finally:
            self.processes.clear()

    ################################################################################################

    def wait_all(self, per_process_timeout: int | None = None):
        """
        Waits for all background processes to complete (by calling `join`).
        If `per_process_timeout` is not None, the implementation waits at most this many seconds for
        each process. If a join fails, an error is logged.

        The list of background processes is cleared before returning.
        """
        for process in self.processes:
            self.wait(process, per_process_timeout)


####################################################################################################

PROCESS_MGR = BackgroundProcessManager()
"""Singleton instance of :py:class:`BackgroundProcessManager`."""

####################################################################################################
