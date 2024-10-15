"""
This module exposes functions to check the presence, and sometimes install op-stack dependencies.
"""

import importlib.util
import os
import platform
import re
import shutil
import sys

import libroll as lib
import state
import term
from config import Config


####################################################################################################

def basic_setup():
    """
    Does some basic setup (creating directories, modifying path), performing basic checks.
    """
    os.makedirs("bin", exist_ok=True)

    lib.prepend_to_path("bin")

    if state.args.use_ansi_esc and not term.is_well_known_term():
        print(
            "\nWARNING: Your terminal is weird.\n"
            "This may cause it to not handle ANSI escape codes well.\n"
            "You can disable them with --no-ansi-esc\n")

    _check_basic_prerequisites()
    _setup_python_deps()


####################################################################################################

def create_paths(config: Config):
    """
    Make sure some basic config-dependent paths do exist.
    """
    os.makedirs(config.artifacts_dir, exist_ok=True)
    os.makedirs(config.databases_dir, exist_ok=True)
    os.makedirs(config.logs_dir, exist_ok=True)

    if os.path.exists(config.log_l2_commands_file):
        os.remove(config.log_l2_commands_file)


####################################################################################################

def post_setup():
    """
    Does some setup, but is dependent on the dependencies installed by :py:func:`setup.setup`, so
    cannot be rolled into :py:func:`basic_setup`.
    """
    go_path_setup()


####################################################################################################

def _setup_python_deps():
    """
    Install required Python dependencies.
    """
    # Used for the main config file
    if importlib.util.find_spec("tomli") is None:
        if lib.ask_yes_no("The Tomli python library is required. Install?\n"
                          "This will install globally if not running in a venv (see README.md)."):
            lib.run("install Tomli",
                    [sys.executable, "-m", "pip", "install", "tomli"])


####################################################################################################

def install_pyyaml():
    # Used for editing blockscout config files.
    if importlib.util.find_spec("yaml") is None:
        if lib.ask_yes_no("The PyYAML python library is required. Install?\n"
                          "This will install globally if not running in a venv (see README.md)."):
            lib.run("install PyYAML",
                    [sys.executable, "-m", "pip", "install", "pyyaml"])


####################################################################################################

def _check_basic_prerequisites():
    """
    check basic prerequisites that we won't offer to install.
    """

    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 10):
        raise Exception(
            "Python 3.10+ is required. Please install it from your package manager.\n"
            "e.g. `brew install python` or `sudo apt install python3-pip`")

    if importlib.util.find_spec("pip") is None:
        raise Exception(
            "pip is not installed. Please make sure it is installed.\n"
            "e.g. `brew install python` or `sudo apt install python3-pip`")

    if shutil.which("make") is None:
        raise Exception(
            "Make is not installed. Please install it from your package manager.\n"
            "e.g. `brew install make` or `sudo apt install build-essential`")

    if shutil.which("git") is None:
        raise Exception(
            "git is not installed. Please install it from your package manager.\n"
            "e.g. `brew install git` or `sudo apt install git`")

    if shutil.which("curl") is None:
        raise Exception(
            "curl is not installed. Please install it from your package manager.\n"
            "e.g. `sudo apt install curl`")

    if shutil.which("tar") is None:
        raise Exception(
            "tar is not installed. Please install it from your package manager.\n"
            "e.g. `sudo apt install tar`")

    if shutil.which("awk") is None:
        raise Exception(
            "awk is not installed. Please install it from your package manager.\n"
            "e.g. `sudo apt install awk`")

    if shutil.which("grep") is None:
        raise Exception(
            "grep is not installed. Please install it from your package manager.\n"
            "e.g. `sudo apt install grep`")

    if shutil.which("logrotate") is None:
        raise Exception(
            "logrotate is not installed. Please install it from your package manager.\n"
            "e.g. `brew install logrotate` or `sudo apt install logrotate`")

    if shutil.which("just") is None:
        raise Exception(
            "just is not installed. Please install it from your package manager.\n"
            "e.g. `brew install just` or see https://github.com/casey/just for more installation options")


####################################################################################################

def get_arch() -> str:
    """
    Returns the architecture of the current machine.
    """
    machine = platform.machine().lower()
    machine = "arm64" if machine == "aarch64" else machine
    machine = "amd64" if machine == "x86_64" else machine
    return machine


# --------------------------------------------------------------------------------------------------

def get_valid_arch(program: str) -> str:
    """
    Returns the architecture of the current machine if supported, or raises an exception otherwise
    that mention the program we were trying to install.
    """
    arch = get_arch()
    if arch not in ("amd64", "arm64"):
        raise Exception(
            f"Unsupported architecture for automatic {program} installation: {arch}.\n"
            f"Please install {program} manually, make sure it is executable "
            "and in $PATH or in ./bin/")
    return arch


# --------------------------------------------------------------------------------------------------

def get_valid_os(program: str) -> str:
    """
    Returns the OS of the current machine if supported, or raises an exception otherwise.
    """
    if sys.platform not in ("linux", "darwin"):
        raise Exception(
            f"Unsupported OS for automatic {program} installation: {sys.platform}.\n"
            f"Please install {program} manually, make sure it is executable "
            "and in $PATH or in ./bin/")
    return sys.platform


####################################################################################################

GO_MIN_VERSION = "1.21"
"""Minimum Go version required by the Optimism repository."""

GO_MAX_VERSION = "1.21.4"
"""Maximum Go version found to work."""

GO_INSTALL_VERSION = "1.21.4"
"""Version of Go to install if not found."""


# --------------------------------------------------------------------------------------------------

def check_or_install_go():
    if shutil.which("go") is None:
        if not install_go():
            raise Exception(
                f"go is not installed. Please install Go version {GO_MIN_VERSION} or higher.")
    else:
        version = lib.run("get go version", "go version")
        version = re.search(r"go version go(\d+\.\d+(\.\d+)?)", version)
        version = "0" if version is None else version.group(1)
        if (version < GO_MIN_VERSION or version > GO_MAX_VERSION) and not install_go():
            raise Exception(
                f"Invalid go version: {version}\n"
                f"Please upgrade Go a version >= {GO_MIN_VERSION} and <= {GO_MAX_VERSION}.\n"
                "(Or let us install a local Go that won't conflict with existing installations!)")


# --------------------------------------------------------------------------------------------------

def install_go() -> bool:
    """
    Installs Go in ./bin.
    """

    if not lib.ask_yes_no(
            f"Go >= {GO_MIN_VERSION} is required. "
            f"Install Go {GO_INSTALL_VERSION} in ./bin?\n"
            "This won't conflict with your existing Go installations."):
        return False

    os.makedirs("bin", exist_ok=True)
    osys = get_valid_os("go")
    arch = get_valid_arch("go")

    try:
        # Remove old installation if present.
        shutil.rmtree("bin/go_install", ignore_errors=True)

        print(f"Downloading go {GO_INSTALL_VERSION} ...")
        os.makedirs("bin/go_install", exist_ok=True)
        descr = "install go"
        url = f"https://go.dev/dl/go{GO_INSTALL_VERSION}.{osys}-{arch}.tar.gz"
        lib.run(descr, f"curl -L {url} | tar xz -C bin/go_install --strip-components=1")
        lib.run("symlink go to bin/go", "ln -sf go_install/bin/go bin/go")
        lib.chmodx("bin/go")
    except Exception as err:
        shutil.rmtree("bin/go_install", ignore_errors=True)
        raise lib.extend_exception(err, prefix="Failed to install go: ") from None

    print(f"Successfully installed go {GO_INSTALL_VERSION} as ./bin/go")
    return True


# --------------------------------------------------------------------------------------------------

def go_path_setup():
    """
    Updates path to work with Go, including with the local Go installation if we have one.
    """

    # If bin/go exists (and is thus used), set correct GOROOT
    if os.path.isfile("bin/go"):
        os.environ["GOROOT"] = os.path.abspath("bin/go_install")


####################################################################################################

def check_or_install_jq():
    """
    Checks if jq is installed (either globally or in ./bin), and if not, installs it in ./bin.
    """

    if shutil.which("jq") is not None:
        # This includes ./bin/jq, as basic_setup() adds ./bin to the path.
        return

    descr = "install jq"
    os.makedirs("bin", exist_ok=True)
    osys = get_valid_os("jq")
    arch = get_valid_arch("jq")

    try:
        print("Installing jq in bin/jq")
        url = f"https://github.com/jqlang/jq/releases/download/jq-1.7/jq-{osys}-{arch}"
        lib.run(descr, f"curl -L {url} -o bin/jq")
        lib.chmodx("bin/jq")
    except Exception as err:
        raise lib.extend_exception(err, prefix="Failed to install jq: ") from None

    print("Successfully installed jq as ./bin/jq")


####################################################################################################

# Whether we must instruct to use the proper Node version via NVM or not.
must_nvm_use = False
"""Whether we must instruct to use the proper Node version via `nvm use` or not."""


def cmd_with_node(command: str) -> str:
    """
    If required, prepends the command with an ``nvm use`` statement.

    WARNING: The command will be double-quoted and passed to bash, so it must not itself include
    double quotes (single quotes are fine).
    """
    if must_nvm_use:
        return f"bash -c \". ~/.nvm/nvm.sh; nvm use {NODE_VERSION}; {command}\""
    else:
        return command


####################################################################################################

NODE_VERSION = "v20.9.0"
"""Full node of the node version required by the optimism repository."""

NVM_VERSION = "v0.39.7"
"""A recent NVM version to install if needed."""


def check_or_install_node():
    """
    Check if Node.js is installed and is the correct version, otherwise prompts the user to install
    it via NVM.
    """

    # Check if Node is installed and is the correct version.
    if shutil.which("node") is not None:
        if lib.run("get node version", "node --version") == NVM_VERSION:
            return

    # Either Node is not installed, or the current version is not v16.
    # global must_nvm_use
    global must_nvm_use
    must_nvm_use = True

    def nvm_install_node():
        lib.run(f"install Node {NODE_VERSION}",
                f"bash -c '. ~/.nvm/nvm.sh; nvm install {NODE_VERSION}'")
        print(f"Successfully installed Node {NODE_VERSION}")

    if os.path.isfile(os.path.expanduser("~/.nvm/nvm.sh")):
        # We have NVM, try using required version or installing it.
        try:
            lib.run(f"use node {NODE_VERSION}",
                    f"bash -c '. ~/.nvm/nvm.sh; nvm use {NODE_VERSION}'")
        except Exception:
            if lib.ask_yes_no(f"Node {NODE_VERSION} is required. NVM is installed. "
                              f"Install with NVM?"):
                nvm_install_node()
            else:
                raise Exception(f"Node {NODE_VERSION} is required.")
    else:
        # Install NVM + Node.
        nvm_url = f"https://raw.githubusercontent.com/nvm-sh/nvm/{NVM_VERSION}/install.sh"
        if lib.ask_yes_no(f"Node {NODE_VERSION} is required. Install NVM + Node?"):
            lib.run("install nvm", f"curl -o- {nvm_url} | bash")
            nvm_install_node()
        else:
            raise Exception(f"Node {NODE_VERSION} is required.")


####################################################################################################

def check_or_install_yarn():
    """
    Check if Yarn is installed on the current Node and is the correct version, otherwise prompts
    the user to install it. This call should always be preceded by a call to
    :py:func:`check_or_install_node`.
    """
    try:
        # can't use `shutil.which`, we need to use proper Node version!
        lib.run("get yarn version", cmd_with_node("yarn --version"))
        return
    except Exception:
        pass

    if lib.ask_yes_no("Yarn is required. Install?"):
        lib.run("install Yarn", cmd_with_node("npm install -g yarn"))
        print("Successfully installed Yarn.")
    else:
        raise Exception("Yarn is required.")


####################################################################################################

def check_or_install_pnpm():
    """
    Check if pnpm is installed on the current Node and is the correct version, otherwise prompts
    the user to install it. This call should always be preceded by a call to
    :py:func:`check_or_install_node`.
    """
    try:
        # can't use `shutil.which`, we need to use proper Node version!
        lib.run("get pnpm version", cmd_with_node("pnpm --version"))
        return
    except Exception:
        pass

    if lib.ask_yes_no("PNPM is required. Install?"):
        lib.run("install PNPM", cmd_with_node("npm install -g pnpm"))
        print("Successfully installed PNPM.")
    else:
        raise Exception("PNPM is required.")


####################################################################################################

def get_foundry_version():
    """
    Returns the Foundry version (actually the date of release, which is updated a lot more often).
    It's possible to have multiple releases on the same day, but these are commit-tagged, so we
    can't compare them.
    """
    try:
        version_blob = lib.run("get forge version", "forge --version")
    except Exception as e:
        print(e)
        version_blob = ""
    match = re.search(r"^forge \d+\.\d+\.\d+ \([0-9a-fA-F]+ (\d{4}-\d\d-\d\d)", version_blob)
    return None if match is None else match.group(1)


####################################################################################################

FOUNDRY_VERSION = "2024-06-02"
"""
Required version of forge. We're locking down foundry to a specific version, as new versions can
introduce serious regressions, and have done so in the past.
"""

FOUNDRY_INSTALL_TAG = "nightly-5ac78a9cd4b94dc53d1fe5e0f42372b28b5a7559"
"""
The tag of the foundry release to install if needed.
"""


def check_or_install_foundry():
    """
    Verify that foundry is installed with the correct version.
    """

    version = get_foundry_version()
    if version == FOUNDRY_VERSION:
        return

    osys = get_valid_os("foundry")
    arch = get_valid_arch("foundry")

    if osys == "linux" and arch == "arm64":
        raise Exception(
            "Foundry binaries are not available for Linux/arm64.\n"
            "Try foundryup -v nightly-60ec00296f00754bc21ed68fd05ab6b54b50e024, "
            "or building foundry from sources.")

    url = f"https://github.com/foundry-rs/foundry/releases/download/{FOUNDRY_INSTALL_TAG}" \
          f"/foundry_nightly_{osys}_{arch}.tar.gz"

    print(f"Installing Foundry locally ({FOUNDRY_VERSION} release)...")
    # will overwrite old version if present
    lib.run("downloading foundry",
            f"curl -L {url} | tar xz -C bin")


####################################################################################################

MIN_GETH_VERSION = "1.13.4"
"""Minimum supported geth version."""

INSTALL_GETH_VERSION = "1.13.4"
"""Version of geth to install if not found."""

INSTALL_GETH_COMMIT_SLUG = "3f907d6a"
"""The commit prefix that must added to the version to download the correct geth version."""


# --------------------------------------------------------------------------------------------------

def check_or_install_geth():
    """
    Verify that geth is installed and has the correct version, or install it if not.
    """

    geth_path = shutil.which("geth")
    if geth_path is not None:
        # This includes ./bin/jq, as basic_setup() adds ./bin to the path.
        version_blob = lib.run("get geth version", "geth version")
        match = re.search(r"^Version: (\d+\.\d+\.\d+)", version_blob, flags=re.MULTILINE)
        if match is not None:
            version = match.group(1)
            abspath = os.path.abspath(geth_path)
            if version >= MIN_GETH_VERSION:
                print(f"Using {abspath} (version: {version})")
                return
            else:
                lib.debug(f"Found {abspath} (version: {version})")

    if lib.ask_yes_no(
            f"Geth >= {MIN_GETH_VERSION} is required. "
            f"Install Geth {INSTALL_GETH_VERSION} in ./bin?\n"
            "This will overwrite any version of geth that might be in that directory."):
        install_geth()
    else:
        raise Exception(f"Geth missing or wrong version (expected: > {MIN_GETH_VERSION}).")


# --------------------------------------------------------------------------------------------------

def install_geth():
    """
    Installs geth in ./bin (uses the GETH_URL_LINUX and GETH_URL_MACOS constants).
    """
    descr = "install geth"
    os.makedirs("bin", exist_ok=True)
    osys = get_valid_os("geth")
    arch = get_valid_arch("geth")
    if osys == "darwin" and arch == "arm64":
        arch = "amd64"  # only version available, and is compatible via Rosetta

    try:
        host = "https://gethstore.blob.core.windows.net"
        geth_id = f"geth-{osys}-{arch}-{INSTALL_GETH_VERSION}-{INSTALL_GETH_COMMIT_SLUG}"
        url = f"{host}/builds/{geth_id}.tar.gz"
        lib.run(descr, f"curl -L {url} | tar xz -C bin --strip-components=1")
    except Exception as err:
        raise lib.extend_exception(err, prefix="Failed to install geth: ") from None

    print(f"Successfully installed geth {INSTALL_GETH_VERSION} as ./bin/geth")


####################################################################################################

MIN_DOCKER_VERSION = "24"
"""
Minimum supported Docker version. This is somewhat arbitrary, simply the latest major version,
that we also tested with.
"""


def check_docker():
    if shutil.which("docker") is None:
        raise Exception(
            "Docker is not installed. Please install either Docker Engine or Docker Desktop\n"
            "by following the instructions at https://docs.docker.com/engine/install/.")

    version_blob = lib.run("get docker version", "docker --version")
    match = re.search(r"(\d+\.\d+\.\d+)", version_blob)
    if match is None:
        raise Exception("Failed to parse the Docker version, "
                        f"try updating Docker engine to v{MIN_DOCKER_VERSION} or higher.")
    elif match.group(1) < MIN_DOCKER_VERSION:
        raise Exception(f"Please update docker to {MIN_DOCKER_VERSION} or higher. "
                        "Refer to https://docs.docker.com/engine/install/")

    try:
        lib.run("try running docker compose", "docker compose version")
    except Exception:
        raise Exception("Docker Compose not available, please install the Compose plugin. "
                        "Refer to https://docs.docker.com/compose/install/")


####################################################################################################
