import atexit
import signal
from typing import Callable


####################################################################################################

class ExitHooksManager:
    """
    Enables registering exit hooks that are called on exit (both successful exit and exit due to
    signals). Does support all signals that normally cause termination of the program (SIGTERM,
    SIGINT and SIGQUIT) but not SIGKILL that cannot be caught by design.
    """

    def __init__(self):
        self.hooks = []
        """List of functions to call when exiting."""

        atexit.register(self._run_hooks)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGQUIT, self._signal_handler)

    def _run_hooks(self):
        for hook in self.hooks:
            hook(0)

    def _signal_handler(self, signum, frame):
        for hook in self.hooks:
            hook(signum)

    def register(self, hook: Callable[[int], None]):
        """
        Registers a hook to be called on exit (both successful exit and exit due to signal).
        The hook is passed 0 on successful exit, and the signal number on exit due to signal.
        """
        self.hooks.append(hook)


####################################################################################################

EXIT_HOOKS_MGR = ExitHooksManager()
"""Singleton instance of :py:class:`ExitHooksManager`."""

####################################################################################################
