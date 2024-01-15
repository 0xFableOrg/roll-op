"""
This module defines functions related to spinning an op-geth node.
"""

import os
import shutil

import l2_batcher
import l2_deploy
import l2_engine
import l2_node
import l2_proposer
import libroll as lib
from config import Config


####################################################################################################

def deploy_and_start(config: Config):
    """
    Deploys the rollup contracts to L1, create the L2 genesis then runs all components of the L2
    system (the L2 engine, the L2 node, the L2 batcher, and the L2 proposer).
    """
    l2_deploy.deploy(config)
    start(config)


####################################################################################################

def start(config: Config):
    """
    Starts all components of the the L2 system: the L2 engine, the L2 node, the L2 batcher, and the
    L2 proposer. This assumes the L2 contracts have already been deployed to L1 and that the L2
    genesis has already been generated.
    """
    l2_engine.start(config)
    l2_node.start(config, sequencer=True)
    l2_proposer.start(config)
    l2_batcher.start(config)
    print("All L2 components are running.")


####################################################################################################

def generate_jwt_secret(config: Config):
    """
    Generate the JWT secret if it doesn't already exist. This enables secure communication
    between the L2 node and the L2 execution engine.

    This is called both by the L2 node and the L2 engine when they start. If deploying them on
    separate machines, it is necessary to generate this in advance and transmit them to both
    machines.
    """
    if os.path.isfile(config.jwt_secret_path) and os.path.getsize(config.jwt_secret_path) >= 64:
        return

    import secrets
    random_bytes = secrets.token_bytes(32)
    random_hex = random_bytes.hex()
    try:
        with open(config.jwt_secret_path, "w") as file:
            file.write(random_hex)
    except Exception as e:
        raise lib.extend_exception(e, "Failed to write JWT secret to file") from None


####################################################################################################

def clean(config: Config):
    """
    Cleans up L2 deployment outputs.
    """
    lib.remove_paths(config, [
        config.addresses_path,
        config.l2_genesis_path,
        config.rollup_config_path,
        config.deploy_config_path,
        config.jwt_secret_path,
        config.log_l2_commands_file,
        config.op_deploy_config_path,
        os.path.join(config.logs_dir, "deploy_l1_contracts.log"),
        os.path.join(config.logs_dir, "create_l1_artifacts.log"),
        os.path.join(config.logs_dir, "init_l2_genesis.log"),
        config.l2_batcher_log_file,
        config.l2_engine_log_file,
        config.l2_node_log_file,
        config.l2_proposer_log_file,
        # dirs
        config.op_deployment_artifacts_dir,
        config.abi_dir,
    ])

    l2_engine.clean(config)
    l2_node.clean(config)


####################################################################################################
