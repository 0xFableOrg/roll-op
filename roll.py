#!/usr/bin/env python3

import argparse
import os

import libroll as lib
import deps


####################################################################################################
# SETUP

def setup():
    deps.check_go()
    deps.check_or_install_jq()
    deps.check_or_install_node()
    deps.check_or_install_yarn()
    deps.check_or_install_foundry()
    setup_optimism_repo()


# --------------------------------------------------------------------------------------------------

def setup_optimism_repo():
    github_url = "https://github.com/ethereum-optimism/optimism.git"
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
        command=deps.cmd_with_node("make build"),
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

subparsers.add_parser(
    "clean",
    help="cleans up build outputs")

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
    lib.args = parser.parse_args()
    try:
        if lib.args.command is None:
            parser.print_help()
            exit()

        deps.basic_setup()
        deps.check_basic_prerequisites()

        if lib.args.command == "setup":
            setup()

        print("Done.")
    except KeyboardInterrupt:
        print("Interrupted by user.")
    except Exception as e:
        if lib.args.show_stack_trace:
            raise e
        else:
            print(f"Aborted with error: {e}")

####################################################################################################
