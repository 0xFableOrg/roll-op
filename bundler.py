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

subparsers.add_parser(
    "clean",
    help="cleanup bundler processes")

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
    setup_paymaster()

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
        log_file = "logs/build_4337_contracts.log"
        lib.run_roll_log(
            "install account abstraction dependencies", 
            command=deps.cmd_with_node("yarn install"), 
            cwd="account-abstraction",
            log_file=log_file
        )
        # we need to configure the network to point to local network
        # we also need to set private key for deployment
        priv_key = input("Enter private key that you would like to deploy contracts with: ")
        lib.run("set private key", f"echo PRIVATE_KEY={priv_key} > account-abstraction/.env")
        log_file = "logs/deploy_4337_contracts.log"
        lib.run_roll_log(
            "deploy contracts", 
            command=deps.cmd_with_node("yarn deploy --network opstack"), 
            cwd="account-abstraction",
            log_file=log_file
        )
        print("Account abstraction contracts successfully deployed.")
    else:
        print("Account abstraction contracts already deployed.")

def setup_stackup_bundler():
    github_url = "github.com/stackup-wallet/stackup-bundler"
    version = "latest"

    lib.run("installing stackup bundler", f"go install {github_url}@{version}")
    print("Installation successful")

    # set environment variables for bundler
    lib.run("set full node RPC", "echo ERC4337_BUNDLER_ETH_CLIENT_URL=http://localhost:8545 > .env")
    priv_key = input("Enter private key for bundler: ")
    lib.run("set private key", f"echo ERC4337_BUNDLER_PRIVATE_KEY={priv_key} >> .env")

    # make sure that GOPATH is set in PATH
    current_path = os.environ.get("PATH", "")
    gopath = subprocess.check_output(["go", "env", "GOPATH"]).decode().strip()
    # append the bin directory of GOPATH to PATH
    new_path = f"{gopath}/bin:{current_path}"
    os.environ["PATH"] = new_path

    # start bundler as a persistent process
    print("Starting bundler...")
    log_file_path = "logs/stackup_bundler.log"
    log_file = open(log_file_path, "w")
    PROCESS_MGR.start(
        "start bundler", 
        "stackup-bundler start --mode private",
        forward="fd", 
        stdout=log_file, 
        stderr=subprocess.STDOUT
    )
    print("Bundler is running!")
    # PROCESS_MGR.wait_all()

def setup_paymaster():
    # install paymaster dependencies
    lib.run_roll_log(
        "install paymaster dependencies", 
        command=deps.cmd_with_node("npm install"), 
        cwd="paymaster",
        log_file="logs/install_paymaster_dependencies.log"
    )

    # set environment variables for paymaster (deterministic deployments can be hardcoded)
    lib.run("set node RPC", "echo RPC_URL=http://localhost:8545 > paymaster/.env")
    lib.run("set paymaster RPC", "echo PAYMASTER_RPC_URL=http://localhost:3000 >> paymaster/.env")
    lib.run(
        "set entrypoint", 
        "echo ENTRYPOINT_ADDRESS=0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789 >> paymaster/.env"
    )
    lib.run(
        "set factory", 
        "echo SIMPLE_ACCOUNT_FACTORY_ADDRESS=0x9406Cc6185a346906296840746125a0E44976454 >> paymaster/.env"
    )
    paymaster_address = subprocess.check_output(
        ["grep", '==VerifyingPaymaster addr=', "logs/deploy_4337_contracts.log"]
    ).decode().strip().split(' ')[-1]
    lib.run("set paymaster", f"echo PAYMASTER_ADDRESS={paymaster_address} >> paymaster/.env")
    priv_key = input("Enter private key for paymaster signer: ")
    lib.run("set private key", f"echo PRIVATE_KEY={priv_key} >> paymaster/.env")

    # start paymaster signer service
    print("Starting paymaster signer service...")
    log_file_path = "logs/paymaster_signer.log"
    log_file = open(log_file_path, "w")
    PROCESS_MGR.start(
        "start paymaster", 
        "npm run start",
        cwd="paymaster",
        forward="fd", 
        stdout=log_file, 
        stderr=subprocess.STDOUT
    )
    print("Paymaster service is running!")

    # allow background processes to continue running
    PROCESS_MGR.wait_all()

####################################################################################################
# CLEANUP

def clean():
    lib.run("cleanup account abstraction directory", "rm -rf account-abstraction")
    lib.run("cleanup environment variable", "rm .env")
    print("Cleanup successful!")

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
        elif args.command == "clean":
            clean()

        print("Done.")
    except Exception as e:
        print(f"Aborted with error: {e}")

####################################################################################################
