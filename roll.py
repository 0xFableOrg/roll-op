#!/usr/bin/env python3

"""
This is the entry point for roll-op system, responsible for parsing command line arguments and
invoking the appropriate commands.
"""

import argparse
import os

import ansible
import argparsext
import block_explorer
import account_abstraction
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
import setup

####################################################################################################

parser = argparse.ArgumentParser(
    prog="rollop",
    description="R|Helps you spin up an op-stack rollup.\n"
                "Use `rollop <command> --help` to get more detailed help for a command.",
    formatter_class=argparsext.SmartFormatter)

subparsers = parser.add_subparsers(
    title="commands",
    dest="command",
    metavar="<command>")


def command(*args, **kwargs):
    return argparsext.add_subparser(subparsers, *args, **kwargs)


def delimiter(*args, **kwargs):
    return argparsext.add_subparser_delimiter(subparsers, *args, **kwargs)


# --------------------------------------------------------------------------------------------------
delimiter("MAIN COMMANDS")

command(
    "help",
    help="show this help message and exit")

cmd_setup = command(
    "setup",
    help="installs prerequisites and builds the optimism repository")

cmd_devnet = command(
    "devnet",
    help="starts a local devnet, comprising an L1 node and all L2 components")

command(
    "clean",
    help="cleans up deployment outputs and databases")

cmd_l2 = command(
    "l2",
    help="deploys and starts a local L2 blockchain")

command(
    "aa",
    help="starts an ERC-4337 bundler and a paymaster signer service")

# --------------------------------------------------------------------------------------------------
delimiter("GRANULAR COMMANDS")

command(
    "l1",
    help="starts a local L1 node",
    description="Starts a local L1 node, initializing it if needed.")

command(
    "deploy-l2",
    help="deploys but does not start an L2 chain",
    description="Deploys but does not start an L2 chain: "
                "creates the genesis and deploys the contracts to L1.")

command(
    "start-l2",
    help="start all components of the rollup system (see below)")

command(
    "l2-engine",
    help="starts a local L2 execution engine (op-geth) node",
    description="Starts a local L2 execution engine (op-geth) node, initializing it if needed.")

command(
    "l2-sequencer",
    help="starts a local L2 node (op-node) in sequencer mode")

command(
    "l2-batcher",
    help="starts a local L2 transaction batcher")

command(
    "l2-proposer",
    help="starts a local L2 output roots proposer")

# --------------------------------------------------------------------------------------------------
delimiter("CLEANUP")

command(
    "clean-build",
    help="cleans up build outputs (but not deployment outputs or databases)",
    description="Cleans up build outputs — leaves deployment outputs and databases intact, "
         "as well as anything that was downloaded. "
         "Mostly used to get the Optimism monorepo to rebuild.")

command(
    "clean-aa",
    help="cleans up deployment outputs for account abstraction",
)

command(
    "clean-l1",
    help="cleans up deployment outputs & databases for L1")

command(
    "clean-l2",
    help="cleans up deployment outputs & databases for L2")

command(
    "remote",
    help="deploy to remote hosts using ansible"
)

# --------------------------------------------------------------------------------------------------
# Global Flags

parser.add_argument(
    "--name",
    help="name of the rollup deployment",
    default=None,
    dest="name")

parser.add_argument(
    "--preset",
    help="use a preset rollup configuration",
    choices=["dev", "prod"],
    default=None,
    dest="preset")

parser.add_argument(
    "--config",
    help="path to the config file",
    default=None,
    dest="config_path")

parser.add_argument(
    "--clean",
    help="run the 'clean' command before running the specified command",
    default=False,
    dest="clean_first",
    action="store_true")

parser.add_argument(
    "--stack-trace",
    help="display exception stack trace in case of failure",
    default=False,
    dest="show_stack_trace",
    action="store_true")

parser.add_argument(
    "--no-ansi-esc",
    help="disable ANSI escape codes for terminal manipulation",
    default=True,
    dest="use_ansi_esc",
    action="store_false")

# --------------------------------------------------------------------------------------------------
# Command-Specific Flags

cmd_setup.add_argument(
    "--yes",
    help="answer yes to all prompts (install all requested dependencies)",
    default=False,
    dest="always_yes",
    action="store_true")

for cmd in [cmd_l2, cmd_devnet]:
    # NOTE: When functional, might want to add to other commands (e.g. `start-l2`).
    cmd.add_argument(
        "--explorer",
        help="deploys a blockscout explorer for the L2 chain (NOT FUNCTIONAL)",
        default=False,
        dest="explorer",
        action="store_true")

    cmd.add_argument(
        "--aa",
        help="starts an ERC4337 bundler and a paymaster signer service",
        default=False,
        dest="aa",
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
    if lib.args.preset is None or lib.args.preset == "dev":
        config = devnet_config(paths)
    elif lib.args.preset == "prod":
        config = production_config(paths)
    else:
        # Should never happen, as correct preset is validated by argparse.
        raise Exception(f"Unknown preset: '{lib.args.preset}'. Valid: 'dev', 'prod'.")

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
                config_file = tomli.load(f)
        else:
            raise Exception(f"Cannot find config file at {lib.args.config_path}")

        try:
            for key, value in config_file.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            if config_file.get("batching_inbox_address") is None:
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
                if config_file.get(option) is None:
                    print(f"Warning: config file does not specify `{option}`.\n"
                          "It is highly recommended to specify this option, "
                          "especially for non-local deployments.")

        except KeyError as e:
            raise Exception(f"Missing config file value: {e}")

    if hasattr(lib.args, "explorer") and lib.args.explorer:
        # Invert defaults, because it was hard to make blockscout work if the L2 engine wasn't
        # on the 8545 port.
        if config.l1_rpc == "http://127.0.0.1:8545":
            config.l1_rpc = "http://127.0.0.1:9545"
            config.l1_rpc_listen_port = 9545
        config.l2_engine_rpc = "http://127.0.0.1:8545"
        config.l2_engine_rpc_listen_port = 8545

    # Update endpoints if remote deployment
    if config.l1_node_remote_ip is not None:
        setattr(
            config,
            "l1_rpc",
            config.l1_rpc.replace("127.0.0.1", config.l1_node_remote_ip)
        )
        setattr(
            config,
            "l1_rpc_for_node",
            config.l1_rpc_for_node.replace("127.0.0.1", config.l1_node_remote_ip)
        )
    if config.l2_engine_remote_ip is not None:
        setattr(
            config,
            "l2_engine_rpc",
            config.l2_engine_rpc.replace("127.0.0.1", config.l2_engine_remote_ip)
        )
        setattr(
            config,
            "l2_engine_authrpc",
            config.l2_engine_authrpc.replace("127.0.0.1", config.l2_engine_remote_ip)
        )
    if config.l2_sequencer_remote_ip is not None:
        setattr(
            config,
            "l2_node_rpc",
            config.l2_node_rpc.replace("127.0.0.1", config.l2_sequencer_remote_ip)
        )

    config.validate()

    return config


####################################################################################################

def start_addons(config: Config):
    """
    Starts a block explorer and/or an ERC4337 bundler and paymaster, if configured to do so.
    """
    if hasattr(lib.args, "explorer") and lib.args.explorer:
        block_explorer.launch_blockscout()
    if hasattr(lib.args, "aa") and lib.args.aa:
        account_abstraction.setup()
        account_abstraction.deploy(config)
        account_abstraction.start(config)


####################################################################################################

def clean(config: Config):
    """
    Cleans up deployment outputs and databases.
    """
    l1.clean(config)
    l2.clean(config)


####################################################################################################

def main():
    lib.args = parser.parse_args()
    try:
        if lib.args.command is None or lib.args.command == "help":
            parser.print_help()
            exit()

        deps.basic_setup()
        config = load_config()

        if lib.args.clean_first:
            clean(config)

        if lib.args.command == "setup":
            setup.setup(config)
            return

        deps.post_setup()

        if lib.args.command == "devnet":
            deps.check_or_install_geth()
            deps.check_or_install_foundry()

            if config.deploy_devnet_l1:
                l1.deploy_devnet_l1(config)
            l2.deploy_and_start(config)
            start_addons(config)
            PROCESS_MGR.wait_all()

        elif lib.args.command == "clean":
            clean(config)

        elif lib.args.command == "l2":
            deps.check_or_install_foundry()

            l2.deploy_and_start(config)
            start_addons(config)
            PROCESS_MGR.wait_all()

        elif lib.args.command == "aa":
            account_abstraction.setup()
            account_abstraction.deploy(config)
            account_abstraction.start(config)
            PROCESS_MGR.wait_all()

        elif lib.args.command == "l1":
            deps.check_or_install_geth()
            deps.check_or_install_foundry()

            l1.deploy_devnet_l1(config)
            PROCESS_MGR.wait_all()

        elif lib.args.command == "deploy-l2":
            deps.check_or_install_foundry()

            l2.deploy(config)

        elif lib.args.command == "start-l2":
            config.deployments = lib.read_json_file(config.paths.addresses_json_path)
            l2.start(config)
            if hasattr(lib.args, "explorer") and lib.args.explorer:
                block_explorer.launch_blockscout()
            PROCESS_MGR.wait_all()

        elif lib.args.command == "l2-engine":
            l2_engine.start(config)
            if hasattr(lib.args, "explorer") and lib.args.explorer:
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

        elif lib.args.command == "clean-build":
            setup.clean_build()

        elif lib.args.command == "clean-l1":
            l1.clean(config)

        elif lib.args.command == "clean-l2":
            l2.clean(config)

        elif lib.args.command == "clean-aa":
            account_abstraction.clean()

        if lib.args.command == "remote":
            ansible.generate_inventory(config)
            log_file = open("logs/ansible.log", "w")
            ansible.run_playbook(
                config,
                "setup and start remote deployment",
                log_file=log_file,
                playbook="rollop.yml",
                tags=["setup", "l1", "l2", "restart"]
            )

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
