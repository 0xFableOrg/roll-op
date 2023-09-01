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
    "devnet",
    help="spins up a local devnet, comprising an L1 node and all L2 components")

subparsers.add_parser(
    "clean",
    help="cleans up build outputs and databases")

subparsers.add_parser(
    "l1",
    help="spins up a local L1 node with the rollup contracts deployed on it")

subparsers.add_parser(
    "l2-engine",
    help="spins up a local l2 execution engine (op-geth) node")

subparsers.add_parser(
    "l2-sequencer",
    help="spins up a local l2 node (op-node) in sequencer mode")

subparsers.add_parser(
    "l2-batcher",
    help="spins up a local l2 transaction batcher")

subparsers.add_parser(
    "l2-proposer",
    help="spins up a local l2 outpur roots proposer")

subparsers.add_parser(
    "clean-l1",
    help="cleans up deployment outputs & databases for L1")

subparsers.add_parser(
    "clean-l2",
    help="cleans up deployment outputs & databases for L2")

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

        from paths import OPPaths
        paths = OPPaths("optimism")
        from config import devnet_config
        config = devnet_config(paths)

        if lib.args.command == "devnet":
            deps.check_or_install_geth()
            deps.check_or_install_foundry()

            import l1
            import l2
            l1.deploy_devnet_l1(paths)
            l2.deploy(paths)

            from processes import PROCESS_MGR
            PROCESS_MGR.wait_all()

        if lib.args.command == "clean":
            import l1
            import l2
            l1.clean(paths)
            l2.clean(paths)

        if lib.args.command == "l1":
            deps.check_or_install_foundry()
            deps.check_or_install_geth()
            import l1
            l1.deploy_devnet_l1(paths)
            from processes import PROCESS_MGR
            PROCESS_MGR.wait_all()

        if lib.args.command == "l2":
            deps.check_or_install_foundry()

            import l2
            l2.deploy(paths)

            from processes import PROCESS_MGR
            PROCESS_MGR.wait_all()

        if lib.args.command == "l2-engine":
            import l2_engine
            l2_engine.start(config, paths)

            from processes import PROCESS_MGR
            PROCESS_MGR.wait_all()

        if lib.args.command == "l2-sequencer":
            import l2_node
            l2_node.start_l2_node(config(paths), paths, sequencer=True)

            from processes import PROCESS_MGR
            PROCESS_MGR.wait_all()

        if lib.args.command == "l2-batcher":
            import l2_batcher
            l2_batcher.start(config)

            from processes import PROCESS_MGR
            PROCESS_MGR.wait_all()

        if lib.args.command == "l2-proposer":
            import l2_proposer
            deployments = lib.read_json_file(paths.addresses_json_path)
            l2_proposer.start(config, deployments)

            from processes import PROCESS_MGR
            PROCESS_MGR.wait_all()

        if lib.args.command == "clean-l1":
            import l1
            l1.clean(paths)

        if lib.args.command == "clean-l2":
            import l2
            l2.clean(paths)

        print("Done.")
    except KeyboardInterrupt:
        # Usually not triggered because we will exit via the exit hook handler.
        print("Interrupted by user.")
    except Exception as e:
        if lib.args.show_stack_trace:
            raise e
        else:
            print(f"Aborted with error: {e}")

####################################################################################################
