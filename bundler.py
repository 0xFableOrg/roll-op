#!/usr/bin/env python3

import argparse
import os
import shutil
import libroll as lib

####################################################################################################
# VARIABLES

# Whether we must instruct to use the proper Node version via NVM or not.
must_nvm_use = False

####################################################################################################
# CONSTANTS

# Minimum Go version required by the Stackup bundler.
GO_VERSION = "1.19"

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
    help="setup an ERC4337 bundler")

parser.add_argument(
    "--no-ansi-esc",
    help="disable ANSI escape codes for terminal manipulation",
    default=True,
    dest="use_ansi_esc",
    action="store_false")

####################################################################################################
# UTILITY

def run_with_node(descr: str, command: str | list[str], **kwargs) -> str:
    """
    Just like :py:func:`run`, but prepends the command with an ``nvm use`` statement if necessary.
    """
    if must_nvm_use:
        return lib.run(descr, f"source ~/.nvm/nvm.sh; nvm use {NODE_VERSION}; {command}", **kwargs)
    else:
        return lib.run(descr, command, **kwargs)

####################################################################################################

def check_prerequisites():
    """
    Check basic prerequisites for running this script, and print warnings for potential source of
    troubles.
    """

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

    if args.use_ansi_esc and not lib.is_well_known_term():
        print(
            "\nWARNING: Your terminal is weird."
            + "This may cause it to not handle ANSI escape codes well."
            + "You can disable them with TODO\n")


####################################################################################################
# SETUP

def setup():
    setup_4337_contracts()
    setup_stackup_bundler()

# --------------------------------------------------------------------------------------------------

def setup_4337_contracts():
    github_url = "https://github.com/0xFableOrg/account-abstraction.git"

    if os.path.isfile("account-abstraction"):
        raise Exception("Error: 'account-abstraction' exists as a file and not a directory.")
    elif not os.path.exists("account-abstraction"):
        descr = "clone the account-abstraction repository"
        lib.run(descr, f"git clone {github_url}")
        print(f"Succeeded: {descr}")

    # If contracts have not been previously deployed
    if not os.path.exists("account-abstraction/deployments/opstack"):
        run_with_node("install account abstraction dependencies", "yarn install", cwd="account-abstraction", forward_output=True)
        # we need to configure the network to point to local network
        # we also need to set private key for deployment
        priv_key = input(f"Enter private key that you would like to deploy contracts with: ")
        lib.run("set private key", f"echo PRIVATE_KEY={priv_key} > account-abstraction/.env")
        run_with_node("deploy contracts", "yarn deploy --network opstack", cwd="account-abstraction", forward_output=True)
        print(f"Account abstraction contracts successfully deployed.")
    else:
        print(f"Account abstraction contracts already deployed.")

def setup_stackup_bundler():
    github_url = "github.com/stackup-wallet/stackup-bundler"
    version = "latest"

    # make sure that GOPATH is set in PATH
    lib.run("set go path", f"export PATH=$(go env GOPATH)/bin:$PATH")

    lib.run("installing stackup bundler", f"go install {github_url}@{version}")
    print("Installation successful")

    # start bundler
    lib.run("start bundler", f"stackup-bundler start --mode private")

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
