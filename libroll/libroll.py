import glob
import http.client
import os
import shutil
import socket
import time
import re
from dataclasses import dataclass
from typing import Callable

import state
from .cmd import run_roll_log


####################################################################################################

def ask_yes_no(question: str) -> bool:
    """
    Prompts the user with a yes/no question and returns the results as a boolean.
    """
    # noinspection PyUnresolvedReferences
    if hasattr(state.args, "always_yes") and state.args.always_yes:
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

def replace_in_file(file_path: str, replacements: dict, regex: bool = False):
    """
    Replaces all occurrences of the keys in `replacements` with the corresponding values inside the
    given file.
    """
    with open(file_path, "r") as file:
        filedata = file.read()

    if regex:
        import re
        for key, value in replacements.items():
            filedata = re.sub(key, value, filedata, flags=re.MULTILINE)
    else:
        for key, value in replacements.items():
            filedata = filedata.replace(key, value)

    with open(file_path, "w") as file:
        file.write(filedata)


####################################################################################################

def debug(string: str):
    """
    Prints the given string to stdout if `libroll.debug_mode` is `True`.
    """
    if state.debug_mode:
        print(f"[DEBUG] {string}")


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
        retries: int = 10,
        wait_secs=5):
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
    body = body.replace("'", '"')  # JSON requires double quotes
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

def select_columns(string: str, column_index: int) -> list[str]:
    """
    Select the column at the given index from each line of the given string.
    This is somewhat equivalent to `echo $string | awk '{print $column_index}'` but is strict: it
    will throw an exception if the column is missing in at least one line.
    """
    try:
        return [line.strip().split()[column_index] for line in string.splitlines()]
    except IndexError:
        raise Exception(
            f"Column {column_index} missing in at least one line of:\n{string}") from None


####################################################################################################

def edit_yaml_file(file_path: str, edit: Callable[[dict], None]):
    """
    Edits the given YAML file by loading it, passing the resulting dictionary to the given `edit`
    function, and writing the resulting dictionary back to the file.
    """
    import deps
    deps.install_pyyaml()
    import yaml
    with open(file_path, "r") as file:
        data = yaml.safe_load(file)
    edit(data)
    with open(file_path, "w") as file:
        yaml.dump(data, file, default_flow_style=False, sort_keys=False)


####################################################################################################

def append_to_file(file_path: str, text: str):
    """
    Appends the given text to the given file.
    """
    with open(file_path, "a") as file:
        file.write(text)


####################################################################################################

def remove_paths(config, paths: list[str]):
    """
    Removes the given paths, if they exist, as well as archived logs if one of the passed path is
    a logfile.
    """
    for path in paths:
        if os.path.isfile(path):
            debug(f"Removing {path}")
            os.remove(path)
            if path.startswith(config.logs_dir):
                basename = os.path.basename(path)
                debug(f"Removing archived logs for {basename}")
                archived_logs = glob.glob(os.path.join(config.logrotate_old_dir, basename) + "*")
                for log in archived_logs:
                    os.remove(log)
        elif os.path.isdir(path):
            debug(f"Removing {path}")
            shutil.rmtree(path, ignore_errors=True)

####################################################################################################


def parse_amount(amount_str):
    """
    Parses an amount string and returns something a cast command understands.
    """
    pattern = re.compile(r'^(\d+(\.\d+)?)(\s?(ether|gwei|wei))?$')
    match = pattern.match(amount_str.lower())
    if match:
        amount = match.group(1)
        unit = match.group(4) or 'ether'
        return f"{amount}{unit}"
    else:
        raise ValueError("Invalid amount format.")


####################################################################################################
