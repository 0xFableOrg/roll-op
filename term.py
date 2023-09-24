"""
This module contains functions and classes to manipulate the terminal via ANSI escape codes.
"""

import os
import sys


####################################################################################################

def save_cursor(stream=sys.stdout):
    """
    Uses an ANSI escape code to save the current cursor position.
    """
    stream.write("\0337")  # using DEC escape code, SCO escape code is "\033[s"
    stream.flush()


####################################################################################################

def restore_cursor(stream=sys.stdout):
    """
    Uses an ANSI escape code to restore the previously saved cursor position.
    """
    stream.write("\0338")  # using DEC escape code, SCO escape code is "\033[u
    stream.flush()


####################################################################################################

def clear_to_end(stream=sys.stdout):
    """
    Uses an ANSI escape code to clear from the cursor to the end of the screen.
    """
    stream.write("\033[J")
    stream.flush()


####################################################################################################

def clear_from_saved(stream=sys.stdout):
    """
    Uses ANSI escape codes to clear from the previously saved cursor position to the end of the
    screen.
    """
    restore_cursor(stream)
    clear_to_end(stream)


####################################################################################################

def scroll_up(num_lines: int, stream=sys.stdout):
    """
    Uses ANSI escape codes to scroll up the screen by `num_lines`.
    """
    stream.write(f"\033[{num_lines}A")
    stream.flush()


####################################################################################################

def is_well_known_term():
    """
    Returns true if the current terminal is in a list of well-known terminal types that should
    handle ANSI escapes.
    """
    term = os.getenv("TERM")
    return term in ["xterm", "linux", "vt100", "vt220", "xterm-color", "xterm-256color", "tmux",
                    "tmux256-color", "screen", "screen-256color"]


####################################################################################################

def get_terminal_lines():
    """
    Returns the number of lines in the current terminal.
    """
    return os.get_terminal_size().lines


####################################################################################################

def get_terminal_columns():
    """
    Returns the number of columns in the current terminal.
    """
    return os.get_terminal_size().columns


####################################################################################################

class FixedTermSizeStream:
    """
    A stream that writes to an underlying terminal stream (usually `sys.stdout`) uses ANSI escape
    codes to clear the screen such that a given maximum number of lines of the screen are recycled
    for output (this is capped such that if the actual height of the terminal is lesser, only the
    height of the terminal is used).

    This class makes the important assumption that for the duration of the use of this stream,
    nobody is writing to the underlying stream directly.
    """

    def __init__(self, original_stream, max_lines: int, prefix: str = None):
        """
        See class description.
        :max_lines: if positive, the maximum number of lines to occupy on the screen. If negative or
            0, a number to remove form the maximum number of lines on the screen to obtain
            this quantity.
        :prefix: prepended to every line if not None.
        """

        self.original_stream = original_stream
        """The underlying stream to write to."""

        self.max_lines = max_lines
        """Maximum number of lines to occupy on the screen. The actual occupied space will be capped
        at the effective terminal height at any given time."""

        self.prefix = prefix
        """A prefix to prepend to every line."""

        self.lines = []
        """Buffer that holds the current lines to be displayed."""

        # This makes sure we have `max_lines` empty lines at the bottom of the screen, and we can
        # save the top position as one it's safe to go back to and erase from until end of screen.
        self.original_stream.write("\n" * self._get_max_lines())  # writes max lines
        scroll_up(self._get_max_lines(), original_stream)
        save_cursor(original_stream)

    def _get_max_lines(self):
        # It's important to cap `max_lines` at the current terminal size, some output will
        # escape out of our reach (out of the screen) and won't be erasable afterwards.
        # We also have to do this every time, because the terminal can be resized.
        if self.max_lines > 0:
            return max(self.max_lines, get_terminal_lines())
        else:
            return get_terminal_lines() + self.max_lines

    def write(self, data: str):
        if len(data) == 0:
            return

        max_lines = self._get_max_lines()
        width = get_terminal_columns()

        # Split input into lines of length `width` or less
        split = data.split("\n")
        lines = []
        for string in split:
            string = f"{self.prefix}{string}"
            while len(string) > width:
                lines.append(string[:width])
                string = string[width:]
            lines.append(string)
        if lines[-1] == self.prefix:
            # when writing text followed by a newline, don't apply prefix to final empty line
            lines[-1] = ""

        # Extend `self.lines` based on `lines`
        if len(self.lines) > 0:
            self.lines[-1] += lines[0]
        else:
            self.lines.append(lines[0])
        self.lines.extend(lines[1:])

        # Trim `self.lines` to `max_lines`
        if len(self.lines) > max_lines:
            self.lines = self.lines[-max_lines:]

        # Clear reserved screen space (`max_lines`) and write `lines_to_write`.
        clear_from_saved(self.original_stream)
        self.original_stream.write("\n".join(self.lines))
        self.original_stream.flush()

    def flush(self):
        self.original_stream.flush()

####################################################################################################
