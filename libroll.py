import os
import subprocess
import sys
from threading import Thread

####################################################################################################

debug_mode = os.getenv("DEBUG") is not None


####################################################################################################

def run(descr: str, command: str | list[str], **kwargs) -> str | subprocess.Popen | None:
    """
    Runs a command using the :py:module:`subprocess` module. Keyword arguments are forwarded to
    the :py:class:`subprocess.Popen` constructor directly and can be used to override the defaults
    used. Be careful, as some overrides will be incompatible with the processing done by this
    function, read the rest to know more.

    For defaults, we use `text=True` (read write text instead of bytes), `shell=True` (passing the
    command to shell — beware injections!).

    The output is handled according to the value of the `forward` keyword argument:
    - "capture": the output is captured and returned as a string.
    - "self": the output is forwarded to the current process' terminal.
      Note that this will not honour overrides of `sys.stdout` and `sys.stderr` as the original
      file descriptor will be used instead — use "stream" instead.
    - "stream": the output is forwarded to the stream given in the `stream` option, an object that
      implements the `write(self, text)` and `flush(self)` methods.
    - "discard": the output is discarded.
    - "fd" (for "file descriptor"): the output is redirected to the provided `stdout` and `stderr`.
      If those aren't provided, this will behave similarly to "self".

    The default is "stream" if the `stream` option is specified, "self" if `wait=False` and
    "capture" otherwise.

    You can only specify `stdout` and `stderr` when using `forward='fd'` (the other modes will set
    it explicitly according to their purpose).

    Examples of possible values for `stream` options are :py:class:`libroll.Tee`. and
    :py:class:`term.FixedTermSizeStream`.

    The `wait` option (defaulting to `True`) determines whether the function waits for the process
    to complete. `wait=False` is incompatible with `forward='capture'` and `check=True`. When
    `wait=False`, the :py:class:`subprocess.Popen` object is returned.

    We also introduce keyword arg `check` which is `True` by default (unless `wait=False`) and will
    throw an exception if the process doesn't complete successfully (non-zero return code). This is
    analogous to the same option is :py:func:`subprocess.run`.
    """
    if kwargs.get("shell") is not False and type(command) is list:
        command = " ".join(command)

    try:
        wait = kwargs.pop("wait", True)
        check = kwargs.pop("check", True if wait else False)
        stream = kwargs.pop("stream", None)
        forward_default = "stream" if stream is not None else "capture" if wait else "self"
        forward = kwargs.pop("forward", forward_default)

        if forward == "self":
            stdout = None
            stderr = None
        elif forward in ("capture", "stream"):
            stdout = subprocess.PIPE
            stderr = subprocess.STDOUT
        elif forward == "discard":
            stdout = subprocess.DEVNULL
            stderr = subprocess.DEVNULL
        elif forward == "fd":
            stdout = kwargs.pop("stdout", None)
            stderr = kwargs.pop("stderr", None)
        else:
            raise AssertionError(f"Invalid run_mode: {forward}")

        if not isinstance(check, bool):
            raise AssertionError("`check` option must be a boolean")
        if not isinstance(wait, bool):
            raise AssertionError("`wait` option must be a boolean")

        if stream is not None and forward != "stream":
            raise AssertionError(
                "`forward` option must be 'stream' or omitted when using the `stream` option.")
        if stream is None and forward == "stream":
            raise AssertionError(
                "Must specify `stream` option when using the `forward='stream'` option.")

        missing = object()
        if kwargs.get("stdout", missing) is not missing:
            raise AssertionError("Cannot only specify `stdout` option when using `forward='fd'`")
        if kwargs.get("stderr", missing) is not missing:
            raise AssertionError("Cannot only specify `stderr` option when using `forward='fd'`")

        if forward == "capture" and not wait:
            raise AssertionError("Cannot use `forward='capture'` with `wait=False`")
        if check and not wait:
            raise AssertionError("Cannot use `check=True` with `wait=False`")

        keywords = {
            "stdout": stdout,
            "stderr": stderr,
            "text": True,
            "shell": True,
            **kwargs,
        }

        process = subprocess.Popen(command, **keywords)

        thread = None
        if stream is not None:
            thread = Thread(target=forward_output, args=(process.stdout, stream))
            thread.daemon = True  # kill thread when main thread exits
            thread.start()

        if not wait:
            return process

        returncode = process.wait()

        # NOTE: I believe this isn't required (given we daemonized the thread), but including it
        # from abundance of caution. Including this prevented errors in the buggy scenario where it
        # was allowed to capture both the output and forward it to the terminal (leading to
        # contention on the stdout pipe).
        if thread is not None:
            thread.join()

        output = "".join(line for line in process.stdout) if forward == "capture" else None

        if check and returncode != 0:
            raise subprocess.CalledProcessError(returncode, command)
        elif forward == "capture":
            return output
        else:
            return None

    except subprocess.CalledProcessError as err:
        raise Exception(f"Failed to {descr}: {err}") from err


####################################################################################################

def run_roll_log(descr: str, command: str | list[str], log_file: str, **kwargs):
    """
    A wrapper for :py:func:`run` that uses `forward="stream"` with a stream that combines
    :py:class:`Tee` with :py:class:`term.FixedTermSizeStream` to both forward the output to
    the file `log_file` and to the terminal, where it will not take up more than a fixed number
    of lines and be cleared at the end.

    `kwargs` matches the arguments of :py:func:`run` except that you shouldn't specify `forward` and
    `stream`, and that the following options are added:

    - `max_lines`: max number of term lines to occupy (default to -3, occupying all lines except 3)
       See :py:class:`term.FixedTermSizeStream` for more details.
    - `prefix`: a prefix to display in front of every line on the terminal
    - `use_ansi_esc`: whether to use ANSI escape sequences to clear the terminal (default: `True`)
       If `False`, the output will simply appear whole on the terminal, without ever being cleared.
    """
    import term
    max_lines = kwargs.pop("max_lines", -3)
    prefix = kwargs.pop("prefix", "| ")
    use_ansi_esc = kwargs.pop("use_ansi_esc", True)

    if kwargs.get("forward", None) is not None or kwargs.get("stream", None) is not None:
        raise AssertionError("Cannot specify `forward` or `stream`")

    stream = sys.stdout
    if use_ansi_esc:
        stream = term.FixedTermSizeStream(stream, max_lines=max_lines, prefix=prefix)
    stream = Tee(stream, open(log_file, "w"))
    run(descr, command, **kwargs, stream=stream)
    if use_ansi_esc:
        term.clear_from_saved()


####################################################################################################

def forward_output(input_stream, output_stream):
    """
    Forwards the contents of the given input stream to the given output stream.
    Prefixes the given `prefix` string if given.
    """
    while True:
        line = input_stream.readline()
        if line == "":  # EOF
            break
        output_stream.write(line)
        output_stream.flush()


####################################################################################################

def ask_yes_no(question: str) -> bool:
    """
    Prompts the user with a yes/no question and returns the results as a boolean.
    """
    while True:
        response = input(f"{question} (yes/no): ").strip().lower()
        if response in ("yes", "y"):
            return True
        elif response in ("no", "n"):
            return False
        else:
            print("Invalid response. Please enter 'yes' or 'no'.")


####################################################################################################

def read_json_file(file_path: str) -> dict:
    """
    Reads a JSON file and returns the parsed contents.
    """
    import json
    with open(file_path, "r") as file:
        return json.load(file)


####################################################################################################

def write_json_file(file_path: str, data: dict):
    """
    Writes a JSON file with the given data.
    """
    import json
    with open(file_path, "w+") as file:
        json.dump(data, file, indent=4)


####################################################################################################

def replace_in_file(file_path: str, replacements: dict):
    """
    Replaces all occurrences of the keys in `replacements` with the corresponding values inside the
    given file.
    """
    with open(file_path, "r") as file:
        filedata = file.read()

    for key, value in replacements.items():
        filedata.replace(key, value)

    with open(file_path, "w") as file:
        file.write(filedata)


####################################################################################################

def debug(string: str):
    """
    Prints the given string to stdout if `debug_mode` is `True`.
    """
    global debug_mode
    if debug_mode:
        print(f"[DEBUG] {string}")


####################################################################################################

def extend_exception(e: Exception, prefix: str, suffix: str = ""):
    """
    If supported, extends the given exception with the given prefix and suffix added to the message.
    The stack trace is preserved.
    """
    if len(e.args) >= 1:
        e.args = (f"{prefix}{e.args[0]}{suffix}",) + e.args[1:]
    return e


####################################################################################################

class Tee:
    """
    A class that implements `write(text)` and `flush()` making it suitable to assignment to
    `sys.stdout`. It forwards all the writes to a list of files (one of which can be the original
    `sys.stdout`).
    """

    def __init__(self, *files):
        self.files = files

    def write(self, text):
        for file in self.files:
            file.write(text)

    def flush(self):
        for file in self.files:
            file.flush()


####################################################################################################
