#!/usr/bin/env python3

"""
This is the entry point for roll-op system, responsible for parsing command line arguments and
invoking the appropriate commands.
"""

import argparse
import os

import deps
import l1
import l2
import l2_batcher
import l2_engine
import l2_node
import l2_proposer
import libroll as lib
from config import devnet_config
from paths import OPPaths
from processes import PROCESS_MGR
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
    help="spins up a local L1 node")

subparsers.add_parser(
    "l2",
    help="deploys and starts local L2 blockchain")

subparsers.add_parser(
    "deploy-l2",
    help="deploys an L2 blockchain (creates the genesis and deploys the contracts to L1)")

subparsers.add_parser(
    "start-l2",
    help="start all components of the rollup system "
         "(L2 engine, L2 node, L2 batcher, and L2 proposer)")

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

        # paths = OPPaths()
        # config = devnet_config(paths)
        # config.validate()

        # === Config for Hackaton ===

        paths = OPPaths(gen_dir=".linea")
        config = devnet_config(paths)

        config.deploy_devnet_l1 = False
        config.l1_rpc = os.environ["L1_RPC"]
        config.l1_chain_id = 59140
        config.contract_deployer_key = os.environ["CONTRACT_DEPLOYER_KEY"]
        config.deployment_name = "linea"

        config.validate()
        os.makedirs(paths.gen_dir, exist_ok=True)

        # === End Config for Hackaton ===

        if lib.args.command == "devnet":
            deps.check_or_install_geth()
            deps.check_or_install_foundry()

            if config.deploy_devnet_l1:
                l1.deploy_devnet_l1(config, paths)
            l2.deploy_and_start(config, paths)
            PROCESS_MGR.wait_all()

        if lib.args.command == "clean":
            l1.clean(paths)
            l2.clean(config, paths)

        if lib.args.command == "l1":
            deps.check_or_install_foundry()
            deps.check_or_install_geth()

            l1.deploy_devnet_l1(config, paths)
            PROCESS_MGR.wait_all()

        if lib.args.command == "l2":
            deps.check_or_install_foundry()

            l2.deploy_and_start(config, paths)
            PROCESS_MGR.wait_all()

        if lib.args.command == "deploy-l2":
            deps.check_or_install_foundry()

            l2.deploy(config, paths)

        if lib.args.command == "start-l2":
            config.deployments = lib.read_json_file(paths.addresses_json_path)
            l2.start(config, paths)
            PROCESS_MGR.wait_all()

        if lib.args.command == "l2-engine":

            l2_engine.start(config, paths)
            PROCESS_MGR.wait_all()

        if lib.args.command == "l2-sequencer":
            l2_node.start(config(paths), paths, sequencer=True)
            PROCESS_MGR.wait_all()

        if lib.args.command == "l2-batcher":
            l2_batcher.start(config)
            PROCESS_MGR.wait_all()

        if lib.args.command == "l2-proposer":
            config.deployments = lib.read_json_file(paths.addresses_json_path)
            l2_proposer.start(config)
            PROCESS_MGR.wait_all()

        if lib.args.command == "clean-l1":
            l1.clean(paths)

        if lib.args.command == "clean-l2":
            l2.clean(config, paths)

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
