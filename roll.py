#!/usr/bin/env python3

import argparse
import os
import shutil

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
# ARGUMENT PARSING

# Store the parsed arguments here.
global args

parser = argparse.ArgumentParser(
    description="Helps you spin up an op-stack rollup.")

subparsers = parser.add_subparsers(
    title="commands",
    dest="command",
    metavar="<command>")

subparsers.add_parser(
    "setup",
    help="installs prerequisites and builds the optimism repository")

parser.add_argument(
    "--no-ansi-esc",
    help="disable ANSI escape codes for terminal manipulation",
    default=True,
    dest="use_ansi_esc",
    action="store_false")


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
    troubles.
    """

    os.makedirs("logs", exist_ok=True)

    if shutil.which("make") is None:
        raise Exception(
            "Make is not installed. Please install it from your package manager." +
            "e.g. `brew install make` or `sudo apt install build-essentials`")

    if shutil.which("git") is None:
        raise Exception(
            "git is not installed. Please install it from your package manager." +
            "e.g. `brew install gi` or `sudo apt install git`")

    if shutil.which("go") is None:
        raise Exception(
            f"go is not installed. Please install Go **version {GO_VERSION}** or higher.")
    elif lib.run("get go version", "go version") < GO_VERSION:
        raise Exception(
            f"Go version is too low. Please update to Go **version {GO_VERSION}** or higher."
            + "Go is backwards compatible, so your old project will continue to build.")

    if args.use_ansi_esc and not term.is_well_known_term():
        print(
            "\nWARNING: Your terminal is weird."
            + "This may cause it to not handle ANSI escape codes well."
            + "You can disable them with TODO\n")


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
    git_tag = "op-node/v1.1.1"

    if os.path.isfile("optimism"):
        raise Exception("Error: 'optimism' exists as a file and not a directory.")
    elif not os.path.exists("optimism"):
        print("Cloning the optimism repository. This may take a while...")
        descr = "clone the optimism repository"
        lib.run(descr, f"git clone {github_url}")
        print(f"Succeeded: {descr}")

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
    except Exception as e:
        print(f"Aborted with error: {e}")

####################################################################################################
