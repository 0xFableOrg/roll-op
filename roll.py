#!/usr/bin/env python3

import argparse
import os
import shutil
import sys

import libroll as lib
import term

####################################################################################################
# VARIABLES

# Whether we must instruct to use the proper Node version via NVM or not.
must_nvm_use = False

####################################################################################################
# CONSTANTS

# Short name of the node version to use, for use in logs.
NODE_VNAME = "v16"

# Full node of the node version required by the optimism repository.
NODE_VERSION = "v16.16.0"

# Minimum Go version required by the optimism repository.
GO_VERSION = "1.19"

# Not a strict dependency, just a recent NVM version to install if needed.
NVM_VERSION = "0.39.4"

####################################################################################################
# GLOBALS

global args
"""Parsed program arguments."""

jq_path = "jq"
"""Path to the jq utility."""

JQ_URL_LINUX = "https://github.com/jqlang/jq/releases/download/jq-1.6/jq-linux64"
"""Link to the jq binary for Linux."""

JQ_URL_MACOS = "https://github.com/jqlang/jq/releases/download/jq-1.6/jq-osx-amd64"
"""Link to the jq binary for macOS."""


####################################################################################################
# UTILITY

def cmd_with_node(command: str) -> str:
    """
    If required, prepends the command with an ``nvm use`` statement.
    """
    if must_nvm_use:
        return f"source ~/.nvm/nvm.sh; nvm use {NODE_VERSION}; {command}"
    else:
        return command


####################################################################################################

def check_prerequisites():
    """
    Check basic prerequisites for running this script, and print warnings for potential source of
    troubles. Can also install some of the prerequisites, and does some basic setup (creating
    directories, modifying PATH).
    """

    os.makedirs("logs", exist_ok=True)
    os.makedirs("bin", exist_ok=True)

    # Append "bin" to the path
    os.environ['PATH'] = f"{os.environ['PATH']}:{os.path.abspath('bin')}"

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

    if shutil.which("go") is None:
        raise Exception(
            f"go is not installed. Please install Go version {GO_VERSION} or higher.")
    elif lib.run("get go version", "go version") < GO_VERSION:
        raise Exception(
            f"Go version is too low. Please update to Go **version {GO_VERSION}** or higher."
            + "Go is backwards compatible, so your old project will continue to build.")

    if shutil.which("jq") is None:
        global jq_path
        jq_path = "bin/jq"
        if not os.path.isfile("bin/jq"):
            install_jq()

    if args.use_ansi_esc and not term.is_well_known_term():
        print(
            "\nWARNING: Your terminal is weird."
            + "This may cause it to not handle ANSI escape codes well."
            + "You can disable them with --no-ansi-esc\n")


####################################################################################################

def install_jq():
    """
    Installs jq in ./bin (uses the JQ_URL_LINUX and JQ_URL_MACOS constants).
    """
    descr = "install jq"
    os.makedirs("bin", exist_ok=True)
    if sys.platform not in ("linux", "darwin"):
        raise Exception(f"Unsupported OS for automatic jq installation: {sys.platform}.\n"
                        + "Please install jq manually and have it in $PATH or in ./bin/")

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
# SETUP

def setup():
    install_correct_node()
    install_yarn()
    setup_optimism_repo()


# --------------------------------------------------------------------------------------------------

def install_correct_node():
    # Check if Node is installed and is the correct version.
    if shutil.which("node") is not None:
        if lib.run("get node version", "node --version") == NVM_VERSION:
            return

    # Either Node is not installed, or the current version is not v16.
    # global must_nvm_use
    global must_nvm_use
    must_nvm_use = True

    def nvm_install_node():
        lib.run(f"install node {NODE_VNAME}", f"source ~/.nvm/nvm.sh; nvm install {NODE_VERSION}")

    if os.path.isfile(os.path.expanduser("~/.nvm/nvm.sh")):
        # We have NVM, try using required version or installing it.
        try:
            lib.run(f"use node {NODE_VNAME}", f"source ~/.nvm/nvm.sh; nvm use {NODE_VERSION}")
        except Exception:
            if lib.ask_yes_no(f"Node {NODE_VNAME} ({NODE_VERSION}) is required. NVM is installed. "
                              f"Install with NVM?"):
                nvm_install_node()
            else:
                raise Exception(f"Node {NODE_VNAME} ({NODE_VERSION}) is required.")
    else:
        # Install NVM + Node.
        nvm_url = f"https://raw.githubusercontent.com/nvm-sh/nvm/{NVM_VERSION}/install.sh"
        if lib.ask_yes_no(f"Node {NODE_VNAME} ({NODE_VERSION}) is required. Install NVM + Node?"):
            lib.run("install nvm", f"curl -o- {nvm_url} | bash")
            nvm_install_node()
        else:
            raise Exception(f"Node {NODE_VNAME} ({NODE_VERSION}) is required.")


# --------------------------------------------------------------------------------------------------

def install_yarn():
    if shutil.which("yarn") is not None:
        return

    if lib.ask_yes_no("Yarn is required. Install?"):
        lib.run("install yarn", cmd_with_node("npm install -g yarn"))
    else:
        raise Exception("Yarn is required.")


# --------------------------------------------------------------------------------------------------

def setup_optimism_repo():
    github_url = "git@github.com:ethereum-optimism/optimism.git"
    # This is the earliest commit with functional devnet scripts
    # on top of "op-node/v1.1.1" tag release.
    git_tag = "7168db67c5b421975fef2a090aa6e6ee4e3ff298"

    if os.path.isfile("optimism"):
        raise Exception("Error: 'optimism' exists as a file and not a directory.")
    elif not os.path.exists("optimism"):
        print("Cloning the optimism repository. This may take a while...")
        descr = "clone the optimism repository"
        lib.run(descr, f"git clone {github_url}")
        print("Successfully cloned the optimism repository.")

    lib.run("checkout stable version", f"git checkout --detach {git_tag}", cwd="optimism")

    print("Starting to build the optimism repository. Logging to logs/build_optimism.log\n" +
          "This may take a while...")

    lib.run_roll_log(
        descr="build optimism",
        command=cmd_with_node("make build"),
        cwd="optimism",
        log_file="logs/build_optimism.log")

    print("Successfully built the optimism repository.")


####################################################################################################
# ARGUMENT PARSING

parser = argparse.ArgumentParser(
    description="Helps you spin up an op-stack rollup.")

subparsers = parser.add_subparsers(
    title="commands",
    dest="command",
    metavar="<command>")

subparsers.add_parser(
    "setup",
    help="installs prerequisites and builds the optimism repository")

subparsers.add_parser(
    "l1",
    help="spins up a local L1 node with the rollup contracts deployed on it")

parser.add_argument(
    "--no-ansi-esc",
    help="disable ANSI escape codes for terminal manipulation",
    default=True,
    dest="use_ansi_esc",
    action="store_false")

parser.add_argument(
    "--stack-trace",
    help="display exception stack trace in case of failure",
    default=False,
    dest="show_stack_trace",
    action="store_true")

####################################################################################################

if __name__ == "__main__":
    args = parser.parse_args()
    try:
        if args.command is None:
            parser.print_help()
            exit()

        check_prerequisites()
        if args.command == "setup":
            setup()

        print("Done.")
    except KeyboardInterrupt:
        print("Interrupted by user.")
    except Exception as e:
        if args.show_stack_trace:
            raise e
        else:
            print(f"Aborted with error: {e}")

####################################################################################################
