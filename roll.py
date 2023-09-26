#!/usr/bin/env python3

"""
This is the entry point for roll-op system, responsible for parsing command line arguments and
invoking the appropriate commands.
"""

import argparse
import os

import block_explorer
import deps
import l1
import l2
import l2_batcher
import l2_engine
import l2_node
import l2_proposer
import libroll as lib
from config import devnet_config, production_config, Config
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

# Devnet parser
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

parser.add_argument(
    "--preset",
    help="use a preset rollup configuration",
    default=None,
    dest="preset")

parser.add_argument(
    "--name",
    help="name of the rollup deployment",
    default=None,
    dest="name")

# Devnet arguments
parser.add_argument(
    "--config",
    help="path to the config file",
    default=None,
    dest="config_path")

parser.add_argument(
    "--explorer",
    help="deploy a blockscout explorer for the L2 chain",
    default=False,
    dest="explorer",
    action="store_true")


####################################################################################################

def load_config() -> Config:
    """
    Uses the program arguments (found at `lib.args`) to create and populate a :py:class:`Config`
    object.
    """

    deployment_name = lib.args.name
    deployment_name = deployment_name if deployment_name else lib.args.preset
    deployment_name = deployment_name if deployment_name else "rollup"

    paths = OPPaths(gen_dir=os.path.join("deployments", f"{deployment_name}"))

    # Define config preset
    if lib.args.preset is None or lib.args.preset == "devnet":
        config = devnet_config(paths)
    elif lib.args.preset == "production":
        config = production_config(paths)
    else:
        raise Exception(f"Unknown preset: '{lib.args.preset}'. Valid: 'devnet', 'production'.")

    config.deployment_name = deployment_name

    # Parse config file if specified
    if lib.args.config_path:
        try:
            import tomli
        except Exception:
            raise Exception(
                "Missing dependencies. Try running python roll.py setup first.")
        if os.path.exists(lib.args.config_path):
            with open(lib.args.config_path, mode="rb") as f:
                devnet_config_file = tomli.load(f)
        else:
            raise Exception(f"Cannot find config file at {lib.args.config_path}")

        try:
            for key, value in devnet_config_file.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            if devnet_config_file.get("batching_inbox_address") is None:
                # Derive a unique batch inbox address from the chain id.
                addr = "0xff69000000000000000000000000000000000000"
                str_id = str(config.l2_chain_id)
                config.batching_inbox_address = addr[:-len(str_id)] + str_id

            recommended_options = [
                "l1_chain_id",
                "l2_chain_id",
                "l1_rpc",
                "contract_deployer_key",
                "batcher_account",
                "batcher_key",
                "proposer_account",
                "proposer_key",
                "admin_account",
                "admin_key",
                "p2p_sequencer_account",
                "p2p_sequencer_key",
            ]

            for option in recommended_options:
                if devnet_config_file.get(option) is None:
                    print(f"Warning: config file does not specify `{option}`.\n"
                          "It is highly recommended to specify this option, "
                          "especially for non-local deployments.")

        except KeyError as e:
            raise Exception(f"Missing config file value: {e}")

    if lib.args.explorer:
        # Invert defaults, because it was hard to make blockscout work if the L2 engine wasn't
        # on the 8545 port.
        if config.l1_rpc == "http://127.0.0.1:8545":
            config.l1_rpc = "http://127.0.0.1:9545"
            config.l1_rpc_listen_port = 9545
        config.l2_engine_rpc = "http://127.0.0.1:8545"
        config.l2_engine_rpc_listen_port = 8545

    config.validate()

    return config


####################################################################################################

def main():
    lib.args = parser.parse_args()
    try:
        if lib.args.command is None:
            parser.print_help()
            exit()

        deps.basic_setup()
        config = load_config()

        if lib.args.command == "setup":
            setup(config)
            return

        deps.post_setup()

        if lib.args.command == "devnet":
            deps.check_or_install_geth()
            deps.check_or_install_foundry()

            if config.deploy_devnet_l1:
                l1.deploy_devnet_l1(config)
            l2.deploy_and_start(config)
            if lib.args.explorer:
                block_explorer.launch_blockscout()
            PROCESS_MGR.wait_all()

        elif lib.args.command == "clean":
            l1.clean(config)
            l2.clean(config)

        elif lib.args.command == "l1":
            deps.check_or_install_geth()
            deps.check_or_install_foundry()

            l1.deploy_devnet_l1(config)
            PROCESS_MGR.wait_all()

        elif lib.args.command == "l2":
            deps.check_or_install_foundry()

            l2.deploy_and_start(config)
            if lib.args.explorer:
                block_explorer.launch_blockscout()
            PROCESS_MGR.wait_all()

        elif lib.args.command == "deploy-l2":
            deps.check_or_install_foundry()

            l2.deploy(config)

        elif lib.args.command == "start-l2":
            config.deployments = lib.read_json_file(config.paths.addresses_json_path)
            l2.start(config)
            if lib.args.explorer:
                block_explorer.launch_blockscout()
            PROCESS_MGR.wait_all()

        elif lib.args.command == "l2-engine":
            l2_engine.start(config)
            if lib.args.explorer:
                block_explorer.launch_blockscout()
            PROCESS_MGR.wait_all()

        elif lib.args.command == "l2-sequencer":
            l2_node.start(config, sequencer=True)
            PROCESS_MGR.wait_all()

        elif lib.args.command == "l2-batcher":
            l2_batcher.start(config)
            PROCESS_MGR.wait_all()

        elif lib.args.command == "l2-proposer":
            config.deployments = lib.read_json_file(config.paths.addresses_json_path)
            l2_proposer.start(config)
            PROCESS_MGR.wait_all()

        elif lib.args.command == "clean-l1":
            l1.clean(config)

        elif lib.args.command == "clean-l2":
            l2.clean(config)

        print("Done.")
    except KeyboardInterrupt:
        # Usually not triggered because we will exit via the exit hook handler.
        print("Interrupted by user.")
    except Exception as e:
        if lib.args.show_stack_trace:
            raise e
        else:
            print(f"Aborted with error: {e}")
            exit(1)


####################################################################################################

if __name__ == "__main__":
    main()


####################################################################################################
