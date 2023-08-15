"""
This module exposes functions to check the presence, and sometimes install op-stack dependencies.
"""

import os
import re
import shutil
import sys

import libroll as lib
import term


####################################################################################################

def basic_setup():
    """
    Does some basic setup (creating directories, modifying path), performing basic checks.
    """
    os.makedirs("logs", exist_ok=True)
    os.makedirs("bin", exist_ok=True)

    lib.append_to_path("bin")

    if lib.args.use_ansi_esc and not term.is_well_known_term():
        print(
            "\nWARNING: Your terminal is weird."
            + "This may cause it to not handle ANSI escape codes well."
            + "You can disable them with --no-ansi-esc\n")


####################################################################################################

def check_basic_prerequisites():
    """
    check basic prerequisites that we won't offer to install.
    """

    if shutil.which("make") is None:
        raise Exception(
            "Make is not installed. Please install it from your package manager." +
            "e.g. `brew install make` or `sudo apt install build-essential`")

    if shutil.which("git") is None:
        raise Exception(
            "git is not installed. Please install it from your package manager." +
            "e.g. `brew install git` or `sudo apt install git`")

    if shutil.which("curl") is None:
        raise Exception(
            "curl is not installed. Please install it from your package manager." +
            "e.g. `sudo apt install curl`")

    if shutil.which("tar") is None:
        raise Exception(
            "tar is not installed. Please install it from your package manager." +
            "e.g. `sudo apt install tar`")


####################################################################################################

GO_VERSION = "1.19"
"""Minimum Go version required by the Optimism repository."""


def check_go():
    if shutil.which("go") is None:
        raise Exception(
            f"go is not installed. Please install Go version {GO_VERSION} or higher.")
    elif lib.run("get go version", "go version") < GO_VERSION:
        raise Exception(
            f"Go version is too low. Please update to Go **version {GO_VERSION}** or higher."
            + "Go is backwards compatible, so your old project will continue to build.")


####################################################################################################

JQ_URL_LINUX = "https://github.com/jqlang/jq/releases/download/jq-1.6/jq-linux64"
"""Link to the jq binary for Linux."""

JQ_URL_MACOS = "https://github.com/jqlang/jq/releases/download/jq-1.6/jq-osx-amd64"
"""Link to the jq binary for macOS."""


def check_or_install_jq():
    """
    Checks if jq is installed (either globally or in ./bin), and if not, installs it in ./bin.
    """

    if shutil.which("jq") is not None:
        # This includes ./bin/jq, as basic_setup() adds ./bin to the path.
        return

    descr = "install jq"
    os.makedirs("bin", exist_ok=True)
    if sys.platform not in ("linux", "darwin"):
        raise Exception(
            f"Unsupported OS for automatic jq installation: {sys.platform}.\n"
            + "Please install jq manually, make sure it is executable and in $PATH or in ./bin/")

    print("Installing jq in bin/jq")

    try:
        if sys.platform == "linux":
            lib.run(descr, f"curl -L {JQ_URL_LINUX} -o bin/jq")
        elif sys.platform == "darwin":
            lib.run(descr, f"curl -L {JQ_URL_MACOS} -o bin/jq")
        lib.chmodx("bin/jq")
    except Exception as err:
        raise lib.extend_exception(err, prefix="Failed to install jq: ")

    print(f"Successfully installed jq as ./bin/jq")


####################################################################################################

# Whether we must instruct to use the proper Node version via NVM or not.
must_nvm_use = False
"""Whether we must instruct to use the proper Node version via `nvm use` or not."""


def cmd_with_node(command: str) -> str:
    """
    If required, prepends the command with an ``nvm use`` statement.
    """
    if must_nvm_use:
        return f". ~/.nvm/nvm.sh; nvm use {NODE_VERSION}; {command}"
    else:
        return command


####################################################################################################

NODE_VERSION = "v16.16.0"
"""Full node of the node version required by the optimism repository."""

NVM_VERSION = "v0.39.4"
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
        lib.run(f"install Node {NODE_VERSION}", f". ~/.nvm/nvm.sh; nvm install {NODE_VERSION}")
        print(f"Successfully installed Node {NODE_VERSION}")

    if os.path.isfile(os.path.expanduser("~/.nvm/nvm.sh")):
        # We have NVM, try using required version or installing it.
        try:
            lib.run(f"use node {NODE_VERSION}", f". ~/.nvm/nvm.sh; nvm use {NODE_VERSION}")
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
    Check if Node.js is installed on the current Node and is the correct version, otherwise prompts
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

def get_foundry_version():
    """
    Returns the Foundry version (actually the date of release, which is updated a lot more often).
    It's possible to have multiple releases on the same day, but these are commit-tagged, so we
    can't compare them.
    """
    version_blob = lib.run("get forge version", "forge --version")
    match = re.search(r"^forge \d+\.\d+\.\d+ \([0-9a-fA-F]+ (\d{4}-\d\d-\d\d)", version_blob)
    return None if match is None else match.group(1)


####################################################################################################

# This is a pretty arbitrary cutoff, this was my old version that worked.
MIN_FORGE_VERSION = "2023-05-23"
"""Minimum supported forge version."""


def check_or_install_foundry():
    """
    Verify that foundry is installed and has the correct version, or install it if not.
    """

    def check_forge_version():
        version = get_foundry_version()
        if version is None:
            return False
        print(version)
        return version >= MIN_FORGE_VERSION

    # Doing this here, even if Foundry might already be in path, covers the edge case where we
    # installed Foundry in a previous run of the tool, but the user didn't restart their shell.
    lib.append_to_path(os.path.expanduser("~/.foundry/bin"))

    if shutil.which("forge") is not None:
        if check_forge_version():
            return
        if shutil.which("foundryup") is not None:
            if lib.ask_yes_no("Forge (Foundry) is outdated, run foundryup to update?"):
                lib.run("update foundry", "foundryup")
                if check_forge_version():
                    return
                if lib.ask_yes_no("Forge is still outdated, update foundryup?"):
                    install_foundry()
                    return
        else:
            if lib.ask_yes_no("Forge (Foundry) is outdated, install foundryup and update?"):
                install_foundry()
                return
        raise Exception(f"Forge (Foundry) is outdated (expected: > {MIN_FORGE_VERSION}).")
    else:
        if lib.ask_yes_no(f"Forge (Foundry) is required. Install globally?"):
            install_foundry()
        else:
            raise Exception("Forge is required.")


####################################################################################################

def install_foundry():
    """
    Installs foundry globally.
    """
    print("Installing Foundry")
    lib.run("install foundryup", "curl -L https://foundry.paradigm.xyz | bash")
    lib.run("install foundry", "foundryup")
    version = get_foundry_version()
    print(f"Successfully installed Foundry {version}")


####################################################################################################

MIN_GETH_VERSION = "1.12.0"
"""Minimum supported geth version."""

INSTALL_GETH_VERSION = "1.12.0"
"""Version of geth to install if not found."""

GETH_URL_LINUX = \
    "https://gethstore.blob.core.windows.net/builds/geth-linux-amd64-1.12.0-e501b3b0.tar.gz"
"""Link to geth binary for Linux."""

GETH_URL_MACOS = \
    "https://gethstore.blob.core.windows.net/builds/geth-darwin-amd64-1.12.0-e501b3b0.tar.gz"
"""Link to geth binary for MacOS."""


def check_or_install_geth():
    """
    Verify that geth is installed and has the correct version, or install it if not.
    """

    geth_path = shutil.which("geth")
    if geth_path is not None:
        # This includes ./bin/jq, as basic_setup() adds ./bin to the path.
        version_blob = lib.run(f"get geth version", f"geth version")
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
            f"Geth {MIN_GETH_VERSION} is required. Install in ./bin?\n"
            + "This will overwrite any version of geth that might be in that directory."):
        install_geth()
    else:
        raise Exception(f"Geth missing or wrong version (expected: > {MIN_GETH_VERSION}).")


####################################################################################################

def install_geth():
    """
    Installs geth in ./bin (uses the GETH_URL_LINUX and GETH_URL_MACOS constants).
    """
    descr = "install geth"
    os.makedirs("bin", exist_ok=True)
    if sys.platform not in ("linux", "darwin"):
        raise Exception(f"Unsupported OS for automatic geth installation: {sys.platform}.\n"
                        + "Please install geth manually and have it in $PATH or in ./bin/")

    try:
        if sys.platform == "linux":
            lib.run(descr, f"curl -L {GETH_URL_LINUX} | tar xz -C bin --strip-components=1")
        elif sys.platform == "darwin":
            lib.run(descr, f"curl -L {GETH_URL_MACOS} | tar xz -C bin --strip-components=1")
    except Exception as err:
        raise lib.extend_exception(err, prefix="Failed to install geth: ")

    print(f"Successfully installed geth {INSTALL_GETH_VERSION} as ./bin/geth")

####################################################################################################
