"""
This module defines functions related to spinning an op-geth node.
"""

import os
import shutil

import l2_batcher
import l2_engine
import l2_node
import l2_proposer
import libroll as lib
from config import L2Config
from paths import OPPaths


####################################################################################################

def deploy_and_start(config: L2Config, paths: OPPaths):
    """
    Deploys the rollup contracts to L1, create the L2 genesis then runs all components of the L2
    system (the L2 engine, the L2 node, the L2 batcher, and the L2 proposer).
    """

    deploy(config, paths)
    start(config, paths)


####################################################################################################

def deploy(config: L2Config, paths: OPPaths):
    """
    Deploy the rollup by deploying the contracts to L1 then generating the genesis file, but do not
    start the software components.
    """
    deploy_l1_contracts(paths)
    generate_l2_genesis(config, paths)
    config.deployments = lib.read_json_file(paths.addresses_json_path)

    if config.deployments.get("L2OutputOracleProxy") is None:
        raise Exception(
            "L2OutputOracleProxy address not found in addresses.json. "
            "Try redeploying the L1 contracts.")


####################################################################################################

def start(config: L2Config, paths: OPPaths):
    """
    Starts all components of the the L2 system: the L2 engine, the L2 node, the L2 batcher, and the
    L2 proposer. This assumes the L2 contracts have already been deployed to L1 and the L2 genesis
    has already been generated.
    """
    l2_engine.start(config, paths)
    l2_node.start(config, paths, sequencer=True)
    l2_proposer.start(config)
    l2_batcher.start(config)
    print("All L2 components are running.")


####################################################################################################

def deploy_l1_contracts(paths):
    """
    Deploy the L1 contracts to an L1.
    Currently assumes the L1 is a local devnet L1.
    """

    if os.path.exists(paths.addresses_json_path):
        print("L1 contracts already deployed.")
        return

    deploy_script = "scripts/Deploy.s.sol:Deploy"

    # Private key of first dev Hardhat/Anvil account
    private_key = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

    log_file = "logs/deploy_l1_contracts.log"
    print(f"Deploying contracts to L1. Logging to {log_file}")
    lib.run_roll_log(
        "deploy contracts",
        f"forge script {deploy_script} --private-key {private_key} "
        "--rpc-url http://127.0.0.1:8545 --broadcast",
        cwd=paths.contracts_dir,
        log_file=log_file)

    log_file = "logs/create_l1_artifacts.log"
    print(f"Creating L1 deployment artifacts. Logging to {log_file}")
    lib.run_roll_log(
        "create L1 deployment artifacts",
        f"forge script {deploy_script} --private-key {private_key} --sig 'sync()' "
        "--rpc-url http://127.0.0.1:8545 --broadcast",
        cwd=paths.contracts_dir,
        log_file=log_file)

    try:
        # Read the addresses in the L1 deployment artifacts and store them in json files
        contracts = os.listdir(paths.devnet_l1_deployment_dir)
        addresses = {}

        for c in contracts:
            if not c.endswith(".json"):
                continue
            data = lib.read_json_file(os.path.join(paths.devnet_l1_deployment_dir, c))
            addresses[c.replace(".json", "")] = data["address"]

        sdk_addresses = {
            # Addresses needed by the Optimism SDK
            # We don't use this right now, but it doesn't hurt to include.
            "AddressManager": "0x0000000000000000000000000000000000000000",
            "StateCommitmentChain": "0x0000000000000000000000000000000000000000",
            "CanonicalTransactionChain": "0x0000000000000000000000000000000000000000",
            "BondManager": "0x0000000000000000000000000000000000000000",
            "L1CrossDomainMessenger": addresses["L1CrossDomainMessengerProxy"],
            "L1StandardBridge": addresses["L1StandardBridgeProxy"],
            "OptimismPortal": addresses["OptimismPortalProxy"],
            "L2OutputOracle": addresses["L2OutputOracleProxy"]
        }

        lib.write_json_file(paths.addresses_json_path, addresses)
        lib.write_json_file(paths.sdk_addresses_json_path, sdk_addresses)
        print(f"Wrote L1 contract addresses to {paths.addresses_json_path}")

    except Exception as err:
        raise lib.extend_exception(
            err, prefix="Failed to extract addresses from L1 deployment artifacts: ")


####################################################################################################

def generate_l2_genesis(config: L2Config, paths: OPPaths):
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

    genesis = lib.read_json_file(paths.l2_genesis_path)
    config.chain_id = genesis["config"]["chainId"]

    rollup_config_dict = lib.read_json_file(paths.rollup_config_path)
    config.batch_inbox_address = rollup_config_dict["batch_inbox_address"]


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
