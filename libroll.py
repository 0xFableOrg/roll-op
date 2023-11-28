import http.client
import os
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from threading import Thread

####################################################################################################
# GLOBALS

args = object()
"""Container for parsed program arguments (cf. roll.py)"""

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
      If those aren't provided, this will behave similarly to "self". If only `stdout` is provided,
      `stderr` is redirected to it.

    The default is "stream" if the `stream` option is specified, "self" if `wait=False` and
    "capture" otherwise.

    You can only specify `stdout` and `stderr` when using `forward='fd'` (the other modes will set
    them explicitly according to their purpose).

    Examples of possible values for `stream` options are :py:class:`libroll.Tee`. and
    :py:class:`term.FixedTermSizeStream`.

    The `wait` option (defaulting to `True`) determines whether the function waits for the process
    to complete. `wait=False` is incompatible with `forward='capture'` and `check=True`. When
    `wait=False`, the :py:class:`subprocess.Popen` object is returned.

    We also introduce keyword arg `check` which is `True` by default (unless `wait=False`) and will
    throw an exception if the process doesn't complete successfully (non-zero return code). This is
    analogous to the same option is :py:func:`subprocess.run`.
    """
    if kwargs.get("shell") is not False and isinstance(command, list):
        command = " ".join(command)

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
        stderr = kwargs.pop("stderr", stdout)
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

    try:
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
            raise extend_exception(
                subprocess.CalledProcessError(returncode, command),
                prefix=f"Failed to {descr}: ",
                suffix=f"\nProcess output:\n> {output}" if output is not None else "") from None

        return output

    except OSError as e:
        raise extend_exception(e, prefix=f"Failed to {descr}: ") from None


####################################################################################################

def run_roll_log(descr: str, command: str | list[str], log_file: str | None, **kwargs):
    """
    A wrapper for :py:func:`run` that uses `forward="stream"` with a stream that combines
    :py:class:`Tee` with :py:class:`term.FixedTermSizeStream` to both forward the output to
    the file `log_file` and to the terminal, where it will not take up more than a fixed number
    of lines and be cleared at the end.

    If you do not need logging to a file (only the rolling functionality), you can specify None
    for the `log_file` argument.

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
    # noinspection PyUnresolvedReferences
    use_ansi_esc = kwargs.pop("use_ansi_esc", args.use_ansi_esc)

    if kwargs.get("forward", None) is not None or kwargs.get("stream", None) is not None:
        raise AssertionError("Cannot specify `forward` or `stream`")

    stream = sys.stdout
    if use_ansi_esc:
        stream = term.FixedTermSizeStream(stream, max_lines=max_lines, prefix=prefix)
    if log_file is not None:
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
        sys.stdout.flush()
        line = input_stream.readline()
        if line == "":  # EOF
            sys.stdout.flush()
            break
        output_stream.write(line)
        output_stream.flush()


####################################################################################################

def ask_yes_no(question: str) -> bool:
    """
    Prompts the user with a yes/no question and returns the results as a boolean.
    """
    # noinspection PyUnresolvedReferences
    if hasattr(args, "always_yes") and args.always_yes:
        return True
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
    with open(file_path, "w") as file:
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
        filedata = filedata.replace(key, value)

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

class ExtendedException(Exception):
    """
    A wrapper exception class that extends its inner exception with a prefix and a suffix to the
    message.
    """

    def __init__(self, e: Exception, prefix: str, suffix: str = ""):
        self.prefix = prefix
        self.suffix = suffix
        self.e = e

    def __getattr__(self, item: str):
        # forward all unknonw attributes & functions to the inner exception
        return getattr(self.e, item)

    def __str__(self):
        return f"(wrapping {type(self.e).__name__}):\n" \
            f"> {self.prefix}{self.e.__str__()}{self.suffix}"


####################################################################################################

def extend_exception(e: Exception, prefix: str, suffix: str = ""):
    """
    Extends the given exception with the given prefix and suffix added to the message, by wrapping
    it into a instance of :py:class:`ExtendedException`. These exceptions are not meant to be caught
    but to bubble up to the top level, where they will be printed.

    Note that to avoid "During handling of the above exception, another exception occurred" messages
    and double stack printing, you should use `raise lib.extend_exception(...) from None` to raise
    (the `from None` part suppresses the original exception).
    """
    return ExtendedException(e, prefix, suffix)


####################################################################################################

def chmodx(file_path: str):
    """
    Makes the given file executable.
    """
    os.chmod(file_path, os.stat(file_path).st_mode | 0o111)


####################################################################################################

def prepend_to_path(path: str):
    """
    Adds an absolute version of `path` to the start of the `PATH` environment variable.
    """
    os.environ["PATH"] = f"{os.path.abspath(path)}{os.pathsep}{os.environ['PATH']}"


####################################################################################################

def clone_repo(url: str, descr: str):
    """
    Clone a git repository
    """
    run_roll_log(
        descr=descr,
        command=f"git clone --progress {url}",
        log_file=None,
        max_lines=2)


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

def wait_for_port(address: str, port: int, retries: int = 10, wait_secs: int = 1):
    """
    Waits for `address:port` to be reachable. Will try up to `retries` times, waiting `wait_secs`
    in between each attempt.
    """
    for i in range(0, retries):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Note: this has no internal timeout, fails immediately if unreachable.
            s.connect((address, int(port)))
            s.shutdown(socket.SHUT_RDWR)
            debug(f"Connected to {address}:{port}")
            return True
        except Exception:
            if i < retries - 1:
                print(f"Waiting for {address}:{port}")
                time.sleep(wait_secs)

    raise Exception(f"Timed out waiting for {address}:{port}.")


####################################################################################################

def ensure_port_unoccupied(service_name: str, addr: str, port: int):
    """
    Raises an exception if the given port is already bound on the given address.
    Necessary on MacOS that easily allows two processes to bind to the same port.
    """
    running = True
    try:
        wait_for_port(addr, port, retries=1)
    except Exception:
        running = False
    if running:
        raise Exception(
            f"Couldn't start {service_name}: server already running at {addr}:{port}")


####################################################################################################

def wait_for_rpc_server(
        host: str,
        port: int,
        path: str = "/",
        protocol: str = "http",
        retries: int = 5,
        wait_secs=3):
    """
    Waits for a JSON-RPC server to be available at `url` (ascertained by asking for the chain ID).
    Retries until the server responds with a successful status code, waiting `wait_secs` in between
    tries, with at most `retries` attempts.
    """
    print(f"Waiting for RPC server at {host} (port: {port})...")

    headers = {"Content-type": "application/json"}
    body = '{"id":1, "jsonrpc":"2.0", "method": "eth_chainId", "params":[]}'

    for i in range(0, retries):
        try:
            if protocol == "https":
                conn = http.client.HTTPSConnection(host, port)
            elif protocol == "http":
                conn = http.client.HTTPConnection(host, port)
            else:
                raise Exception(f"unsupported: waiting for RPC protocol '{protocol}'")
            conn.request("POST", path, body, headers)
            response = conn.getresponse()
            conn.close()
            if response.status < 300:
                debug(f"RPC server at {host} ready")
                return
            else:
                print(response)
                debug(f"RPC server not ready, status: {response.status}")
        except Exception:
            debug("RPC server not ready, connection attempt failed, retrying...")
            time.sleep(wait_secs)

    raise Exception(f"Timed out waiting for {host} (port: {port})")


####################################################################################################

def send_json_rpc_request(host: str, iden: int, method: str, params: list, path: str = "/"):
    """
    Sends a JSON-RPC request to the given JSON_RPC server (`host` can include a port number, e.g.
    "127.0.0.1:8454"), with the given nonce, method and params, returns the decoded JSON data from
    the response.
    """
    conn = http.client.HTTPConnection(host)
    headers = {"Content-type": "application/json"}
    body = f'{{"id":{iden}, "jsonrpc":"2.0", "method": "{method}", "params":{params}}}'
    body = body.replace("'", '"') # JSON requires double quotes
    conn.request("POST", path, body, headers)
    response = conn.getresponse()
    data = response.read().decode()
    conn.close()
    return data


####################################################################################################

@dataclass
class RPCParseResult:
    """
    Result of parsing an RPC URL via :py:func:`parse_rpc_url`.
    """
    protocol: str
    address: str
    port: int
    path: str


def parse_rpc_url(url: str) -> RPCParseResult:
    """
    Parses an RPC URL into its (protocol, address, port) components.

    If missing, the protocol defaults to "http" and the port to 8545 (433 for https).
    """
    import urllib.parse
    parsed = urllib.parse.urlparse(url)
    protocol = parsed.scheme or "http"
    address = parsed.hostname
    path = parsed.path if parsed.path else ""
    port = parsed.port or (443 if protocol == "https" else 8545)
    return RPCParseResult(protocol, address, port, path)

####################################################################################################
