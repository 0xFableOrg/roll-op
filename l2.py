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
    paths = [
        os.path.join(config.artifacts_dir, "addresses.json"),
        os.path.join(config.artifacts_dir, "genesis-l2.json"),
        os.path.join(config.artifacts_dir, "rollup.json"),
        os.path.join(config.jwt_secret_path),
        os.path.join(config.log_run_config_file),
        os.path.join(config.logs_dir, "deploy_l1_contracts.log"),
        os.path.join(config.logs_dir, "create_l1_artifacts.log"),
        os.path.join(config.logs_dir, "l2_batcher.log"),
        os.path.join(config.logs_dir, "l2_engine.log"),
        os.path.join(config.logs_dir, "l2_node.log"),
        os.path.join(config.logs_dir, "l2_proposer.log"),
        config.op_deploy_config_path
    ]

    for path in paths:
        if os.path.exists(path):
            lib.debug(f"Removing {path}")
            os.remove(path)

    l2_engine.clean(config)
    l2_node.clean()

    lib.debug(f"Removing {config.deployment_artifacts_gen_dir}")
    shutil.rmtree(config.deployment_artifacts_gen_dir, ignore_errors=True)


####################################################################################################
