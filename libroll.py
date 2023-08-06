import os
import subprocess
import sys


####################################################################################################

def run(descr: str, command: str | list[str], **kwargs) -> str:
    """
    Runs a command using the :py:module:`subprocess` module. Keyword arguments are forwarded to
    the :py:func:`subprocess.run` function directly and can be used to override the defaults used.

    In particular, we use ``shell=True`` (passing the command to shell), ``check=True`` (throwing an
    exception if the command fails) and ``stderr=subprocess.STDOUT`` (redirecting stderr to stdout).

    We also introduce a new keyword argument, ``forward_output``, which is a boolean that defaults
    to False. If True, the output of the command is forwarded to the terminal. Otherwise, the output
    is captured and returned.
    """
    if kwargs.get("shell") is not False and type(command) is list:
        command = " ".join(command)
    try:
        forward = kwargs.pop("forward_output", False)
        keywords = {
            'stdout': subprocess.PIPE if not forward else None,
            'stderr': subprocess.STDOUT,
            'text': True,
            'shell': True,
            'check': True,
            **kwargs,
        }
        # Seems to return str but I'm getting warnings about it being typed as bytes.
        output: str|bytes = subprocess.run(command, **keywords).stdout
        if type(output) is str:
            return output
        elif type(output) is bytes:
            return output.decode("utf-8")
    except subprocess.CalledProcessError as err:
        raise Exception(f"Failed to {descr}: {err}") from err


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

def term_save_cursor():
    """
    Uses an ANSI escape code to save the current cursor position.
    """
    sys.stdout.write("\033[s")
    sys.stdout.flush()


####################################################################################################

def term_restore_cursor():
    """
    Uses an ANSI escape code to restore the previously saved cursor position.
    """
    sys.stdout.write("\033[u")
    sys.stdout.flush()


####################################################################################################

def term_clear_to_end():
    """
    Uses an ANSI escape code to clear from the cursor to the end of the screen.
    """
    sys.stdout.write("\033[J")
    sys.stdout.flush()


####################################################################################################

def term_clear_from_saved():
    """
    Uses ANSI escape codes to clear from the previously saved cursor position to the end of the
    screen.
    """
    term_restore_cursor()
    term_clear_to_end()


####################################################################################################

def is_well_known_term():
    """
    Returns true if the current terminal is in a list of well-known terminal types that should
    handle ANSI escapes.
    """
    term = os.getenv('TERM')
    return term in ['xterm', 'linux', 'vt100', 'vt220', 'xterm-color', 'xterm-256color']


####################################################################################################


def read_json_file(file_path: str) -> dict:
    """
    Reads a JSON file and returns the parsed contents.
    """
    import json
    with open(file_path, 'r') as file:
        return json.load(file)


####################################################################################################


def write_json_file(file_path: str, data: dict):
    """
    Writes a JSON file with the given data.
    """
    import json
    with open(file_path, 'w+') as file:
        json.dump(data, file, indent=4)


####################################################################################################
