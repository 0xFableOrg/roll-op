"""
This module defines functions related to spinning an op-geth node.
"""

import os
import pathlib
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
    patch(paths)
    os.makedirs(paths.gen_dir, exist_ok=True)
    generate_network_config(config, paths)
    deploy_l1_contracts(config, paths)
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

def patch(paths: OPPaths):
    """
    Apply modifications to the optimism repo necessary for our scripts to work.
    """

    # The original optimism repo edits the devnet configuration in place. Instead, we copy the
    # original over once, then use that as a template to be modified going forward.
    if not os.path.exists(paths.deploy_config_template_path):
        shutil.copy(paths.deploy_config_template_path_source, paths.deploy_config_template_path)

    # /usr/bin/bash does not always exist on MacOS (and potentially other Unixes)
    # This was fixed upstream, but isn't fixed in the commit we're using
    try:
        scripts = os.path.join(paths.contracts_dir, "scripts")
        deployer_path = os.path.join(scripts, "Deployer.sol")
        deploy_config_path = os.path.join(scripts, "DeployConfig.s.sol")
        lib.replace_in_file(deployer_path, {"/usr/bin/bash": "bash"})
        lib.replace_in_file(deploy_config_path, {"/usr/bin/bash": "bash"})
    except Exception as err:
        raise lib.extend_exception(err, prefix="Failed to patch Solidity scripts: ")


####################################################################################################

def generate_network_config(config: L2Config, paths: OPPaths):
    """
    Generate the network configuration file. This records information about the L1 and the L2.
    """
    print("Generating network config.")

    try:
        # Copy the template, and modify it with timestamp and starting block tag.

        # Note that we pick the timestamp at the time this file is generated. This doesn't matter
        # much: if we start the L1 node later, it will simply have two consecutive blocks with a
        # large timestamp difference, but no other consequences. The same logic applies if we shut
        # down the node and restart it later.

        deploy_config = lib.read_json_file(paths.deploy_config_template_path)

        if os.path.isfile(paths.l1_genesis_path):
            # If we have a genesis file for L1 (devnet L1)
            l1_genesis = lib.read_json_file(paths.l1_genesis_path)
            deploy_config["l1GenesisBlockTimestamp"] = l1_genesis["timestamp"]
        else:
            # NOTE: The l1 genesis block timestamp is never used, but it needs to be set anyway.
            # This value is only used for generating a devnet L1 genesis file, but that logic is
            # also unused.
            deploy_config["l1GenesisBlockTimestamp"] = "0x0"

        deploy_config["l1StartingBlockTag"] = "earliest"
        deploy_config["l1ChainID"] = config.l1_chain_id
        deploy_config["l2ChainID"] = config.l2_chain_id


        lib.write_json_file(config.deploy_config_path, deploy_config)
    except Exception as err:
        raise lib.extend_exception(err, prefix="Failed to generate devnet L1 config: ")


####################################################################################################

def deploy_l1_contracts(config: L2Config, paths: OPPaths):
    """
    Deploy the L1 contracts to an L1.
    Currently assumes the L1 is a local devnet L1.
    """

    if os.path.exists(paths.addresses_json_path):
        print("L1 contracts already deployed.")
        return

    deploy_script = "scripts/Deploy.s.sol:Deploy"

    env = {**os.environ,
           "DEPLOYMENT_CONTEXT": config.deployment_name,
           "ETH_RPC_URL": config.l1_rpc}

    log_file = "logs/deploy_l1_contracts.log"
    print(f"Deploying contracts to L1. Logging to {log_file}")
    lib.run_roll_log(
        "deploy contracts",
        f"forge script {deploy_script} --private-key {config.contract_deployer_key} "
        f"--rpc-url {config.l1_rpc} --broadcast",
        cwd=paths.contracts_dir,
        env=env,
        log_file=log_file)

    log_file = "logs/create_l1_artifacts.log"
    print(f"Creating L1 deployment artifacts. Logging to {log_file}")
    lib.run_roll_log(
        "create L1 deployment artifacts",
        f"forge script {deploy_script} --private-key {config.contract_deployer_key} "
        f"--sig 'sync()' --rpc-url {config.l1_rpc} --broadcast",
        cwd=paths.contracts_dir,
        env=env,
        log_file=log_file)

    try:
        # Read the addresses in the L1 deployment artifacts and store them in json files
        contracts = os.listdir(config.deployments_dir)
        addresses = {}

        for c in contracts:
            if not c.endswith(".json"):
                continue
            data = lib.read_json_file(os.path.join(config.deployments_dir, c))
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
                 f"--l1-rpc={config.l1_rpc}",
                 f"--deploy-config={config.deploy_config_path}",
                 f"--deployment-dir={config.deployments_dir}",
                 f"--outfile.l2={paths.l2_genesis_path}",
                 f"--outfile.rollup={paths.rollup_config_path}"],
                cwd=paths.op_node_dir)
        except Exception as err:
            raise lib.extend_exception(
                err, prefix="Failed to generate L2 genesis and rollup configs: ")

    genesis = lib.read_json_file(paths.l2_genesis_path)
    config.l2_chain_id = genesis["config"]["chainId"]

    rollup_config_dict = lib.read_json_file(paths.rollup_config_path)
    config.batch_inbox_address = rollup_config_dict["batch_inbox_address"]


####################################################################################################

def clean(config: L2Config, paths: OPPaths):
    """
    Cleans up build outputs, such that trying to deploy the L2 blockchain will proceed as though it
    was the first invocation.
    """
    if os.path.exists(paths.gen_dir):
        lib.debug(f"Cleaning up {paths.gen_dir}")

    for file_path in pathlib.Path(paths.gen_dir).iterdir():
        if file_path.is_file() and file_path.name != "genesis-l1.json":
            os.remove(file_path)

    l2_engine.clean(paths)

    lib.debug(f"Cleaning up {config.deployments_dir}")
    shutil.rmtree(config.deployments_dir, ignore_errors=True)

    shutil.rmtree("opnode_discovery_db", ignore_errors=True)
    shutil.rmtree("opnode_peerstore_db", ignore_errors=True)

####################################################################################################
