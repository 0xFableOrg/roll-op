"""
This module defines functions related to spinning an op-geth node.
"""

import os
import shutil

import l2_batcher
import l2_engine
import libroll as lib
from config import devnet_config
from l2_node import start_l2_node
from l2_proposer import start
from paths import OPPaths


####################################################################################################

def generate_l2_genesis(paths: OPPaths):
    """
    Generate the L2 genesis file and rollup configs.
    """
    if os.path.exists(paths.l2_genesis_path):
        print("L2 genesis and rollup configs already generated.")
    else:
        print("Generating L2 genesis and rollup configs.")
        try:
            lib.run(
                "generating L2 genesis and rollup configs",
                ["go", "run", "cmd/main.go", "genesis", "l2",
                 "--l1-rpc=http://localhost:8545",
                 f"--deploy-config={paths.network_config_path}",
                 f"--deployment-dir={paths.devnet_l1_deployment_dir}",
                 f"--outfile.l2={paths.l2_genesis_path}",
                 f"--outfile.rollup={paths.rollup_config_path}"],
                cwd=paths.op_node_dir)
        except Exception as err:
            raise lib.extend_exception(
                err, prefix="Failed to generate L2 genesis and rollup configs: ")


####################################################################################################

def deploy(paths: OPPaths):
    """
    Deploys all components of the L2 system: the
    Spin the devnet op-geth node, doing whatever tasks are necessary, including installing op-geth,
    generating the genesis file and config files.
    """
    generate_l2_genesis(paths)
    config = devnet_config(paths)
    deployments = lib.read_json_file(paths.addresses_json_path)

    if deployments.get("L2OutputOracleProxy") is None:
        raise Exception(
            "L2OutputOracleProxy address not found in addresses.json. "
            "Try redeploying the L1 contracts.")

    l2_engine.start(config, paths)
    start_l2_node(config, paths, sequencer=True)
    start(config, deployments)
    l2_batcher.start(config)

    print("Devnet L2 deployment is complete! L2 node is running.")


####################################################################################################

def clean(paths: OPPaths):
    """
    Cleans up build outputs, such that trying to deploy the L2 blockchain will proceed as though it
    was the first invocation.
    """
    l2_engine.clean(paths)
    shutil.rmtree("opnode_discovery_db")
    shutil.rmtree("opnode_peerstore_db")

####################################################################################################
