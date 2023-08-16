#!/usr/bin/env python3

import argparse
import shutil
import libroll as lib

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
    setup_stackup_bundler()

# --------------------------------------------------------------------------------------------------

def setup_stackup_bundler():
    github_url = "github.com/stackup-wallet/stackup-bundler"
    version = "latest"

    lib.run("installing stackup bundler", f"go install {github_url}@{version}")
    print("Installation successful")

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
