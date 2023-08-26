#!/usr/bin/env python3

import subprocess
import argparse
import os
import libroll as lib
import deps
from processes import PROCESS_MGR

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
    "start",
    help="start an ERC4337 bundler")

parser.add_argument(
    "--no-ansi-esc",
    help="disable ANSI escape codes for terminal manipulation",
    default=True,
    dest="use_ansi_esc",
    action="store_false")

####################################################################################################
# SETUP

def start():
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
        lib.run("install account abstraction dependencies", command=deps.cmd_with_node("yarn install"), cwd="account-abstraction")
        # we need to configure the network to point to local network
        # we also need to set private key for deployment
        priv_key = input(f"Enter private key that you would like to deploy contracts with: ")
        lib.run("set private key", f"echo PRIVATE_KEY={priv_key} > account-abstraction/.env")
        lib.run("deploy contracts", command=deps.cmd_with_node("yarn deploy --network opstack"), cwd="account-abstraction")
        print(f"Account abstraction contracts successfully deployed.")
    else:
        print(f"Account abstraction contracts already deployed.")

def setup_stackup_bundler():
    github_url = "github.com/stackup-wallet/stackup-bundler"
    version = "latest"

    lib.run("installing stackup bundler", f"go install {github_url}@{version}")
    print("Installation successful")

    # set environment variables for bundler
    lib.run("set full node RPC", f"echo ERC4337_BUNDLER_ETH_CLIENT_URL=http://localhost:8545 > .env")
    priv_key = input(f"Enter private key for bundler: ")
    lib.run("set private key", f"echo ERC4337_BUNDLER_PRIVATE_KEY={priv_key} >> .env")

    # make sure that GOPATH is set in PATH
    current_path = os.environ.get("PATH", "")
    gopath = subprocess.check_output(["go", "env", "GOPATH"]).decode().strip()
    # append the bin directory of GOPATH to PATH
    new_path = f"{gopath}/bin:{current_path}"
    os.environ["PATH"] = new_path

    # start bundler as a persistent process
    PROCESS_MGR.start("start bundler", f"stackup-bundler start --mode private")
    print("Bundler is running!")
    PROCESS_MGR.wait_all()

####################################################################################################

if __name__ == "__main__":
    args = parser.parse_args()
    try:
        if args.command is None:
            parser.print_help()
            exit()

        deps.check_basic_prerequisites()
        deps.check_go()
        if args.command == "start":
            start()

        print("Done.")
    except Exception as e:
        print(f"Aborted with error: {e}")

####################################################################################################
