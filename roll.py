#!/usr/bin/env python3

"""
This is the entry point for roll-op system, responsible for parsing command line arguments and
invoking the appropriate commands.
"""

import argparse

import deps
import libroll as lib
from setup import setup


####################################################################################################

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
    "l2",
    help="spins up a local op-geth node")

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

        if lib.args.command == "l1":
            deps.check_or_install_foundry()
            deps.check_or_install_geth()
            import l1
            import paths
            l1.deploy_l1_devnet(paths.OPPaths("optimism"))

        if lib.args.command == "l2":
            deps.check_or_install_op_geth()
            import l2
            import paths
            l2.deploy_l2_devnet(paths.OPPaths("optimism"))

        if lib.args.command == "clean":
            import l1
            import l2
            import paths
            l1.clean(paths.OPPaths("optimism"))
            l2.clean(paths.OPPaths("optimism"))

        print("Done.")
    except KeyboardInterrupt:
        print("Interrupted by user.")
    except Exception as e:
        if lib.args.show_stack_trace:
            raise e
        else:
            print(f"Aborted with error: {e}")

####################################################################################################
