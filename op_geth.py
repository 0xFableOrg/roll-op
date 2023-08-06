#!/usr/bin/env python3

import os
import shutil

import libroll as lib
from genesis import GENESIS_TMPL

####################################################################################################

DEPLOYMENT_DIR = os.path.join(os.getcwd(), "deployment")
OP_GETH_DIR = os.path.join(DEPLOYMENT_DIR, "op-geth")
OP_GETH_ARTIFACTS_DIR = os.path.join(OP_GETH_DIR, "artifacts")
OP_GETH_CONFIG_DIR = os.path.join(OP_GETH_DIR, "config")
# OP_GETH_DATA_DIR=$OP_GETH_DIR/data
OP_GETH_BIN_DIR = os.path.join(OP_GETH_DIR, "bin")
OP_GETH_REPO_DIR = os.path.join(os.getcwd(), "op-geth")
OPTIMISM_REPO_DIR = os.path.join(os.getcwd(), "optimism")


####################################################################################################


def init_op_geth():
    """
    Initialize the op-geth deployment directory.
    """
    # Create the deployment directory.
    os.makedirs(DEPLOYMENT_DIR, exist_ok=True)

    # Create the op-geth directory.
    os.makedirs(OP_GETH_DIR, exist_ok=True)

    # Create the op-geth artifacts directory.
    os.makedirs(OP_GETH_ARTIFACTS_DIR, exist_ok=True)

    # Create the op-geth config directory.
    os.makedirs(OP_GETH_CONFIG_DIR, exist_ok=True)

    # Create the op-geth bin directory.
    os.makedirs(OP_GETH_BIN_DIR, exist_ok=True)

    # Create the op-geth data directory.
    # os.makedirs(OP_GETH_DATA_DIR, exist_ok=True)

    # Copy the devnet genesis file.
    shutil.copyfile(
        os.path.join(OPTIMISM_REPO_DIR, "packages", "contracts-bedrock", "deploy-config", "devnetL1.json"),
        os.path.join(OP_GETH_CONFIG_DIR, "genesis.json"))

    devnet_cfg_orig = os.path.join(OP_GETH_CONFIG_DIR, "genesis.json")
    deploy_config = lib.read_json_file(devnet_cfg_orig)
    deploy_config['l1GenesisBlockTimestamp'] = GENESIS_TMPL['timestamp']
    deploy_config['l1StartingBlockTag'] = 'earliest'
    lib.write_json_file(devnet_cfg_orig, deploy_config)

####################################################################################################
