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
from config import Config
from deploy_config import PRODUCTION_CONFIG, DEVNET_CONFIG
from paths import OPPaths


####################################################################################################

def deploy_and_start(config: Config):
    """
    Deploys the rollup contracts to L1, create the L2 genesis then runs all components of the L2
    system (the L2 engine, the L2 node, the L2 batcher, and the L2 proposer).
    """

    deploy(config)
    start(config)


####################################################################################################

def deploy(config: Config):
    """
    Deploy the rollup by deploying the contracts to L1 then generating the genesis file, but do not
    start the software components.
    """
    patch(config.paths)
    os.makedirs(config.paths.gen_dir, exist_ok=True)
    generate_deploy_config(config)
    deploy_l1_contracts(config)
    generate_l2_genesis(config)
    config.deployments = lib.read_json_file(config.paths.addresses_json_path)

    if config.deployments.get("L2OutputOracleProxy") is None:
        raise Exception(
            "L2OutputOracleProxy address not found in addresses.json. "
            "Try redeploying the L1 contracts.")

    generate_jwt_secret(config)


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

def generate_deploy_config(config: Config):
    """
    Generate the network configuration file. This records information about the L1 and the L2.
    """
    print("Generating network config.")

    # Get base config, default is the devnet config, but can overriden to production config via
    # the --preset flag.

    if lib.args.preset == "prod":
        deploy_config = PRODUCTION_CONFIG.copy()
    else:
        deploy_config = DEVNET_CONFIG.copy()

    # We need to know the earliest L1 block that might contain rollup-related information
    # ("l1StartingBlockTag"). This accepts either a blockhash, or a "block tag".

    # Because it's pretty hard to find the documentation on these tags, here is the information I've
    # been able to gather. The possibile values are: earliest, finalized, safe, latest or pending.
    #
    # "Earliest" is block 0. On Ethereum, "safe" is a block that has received 2/3 attestations but
    # isn't finalized yet, "finalized" is a block that has been finalized, "latest" is the latest
    # proposed block, with no guarantee of attestations. "Pending" is an image of a block that could
    # theoretically be proposed, but probably won't be (because the node isn't the proposer).
    #
    # On L2s, these things are probably slighty different. I'm just wildly guessing here.
    # "Finalized" might be for blocks whose batch has been posted to a finalized L1 block, "safe"
    # might be for blocks whose batch has been posted to L1, and "latest" might be for blocks that
    # have been sent by the sequencer but not posted yet. (NOT SURE, JUST GUESSES)
    #
    # op-geth doesn't compute pending blocks by default (option `--rollup.computependingblock`).

    # Anyhow, we use "earliest" on a local devnet (we have a genesis file for L1), because fetching
    # the latest block somehow does not work against the local L1. But since we're usually spinning
    # the L1 right before the L2, using "earliest" works just as well.
    #
    # Otherwise, we use cast to get the "latest" block from the configured RPC endpoint and use its
    # hash.

    # TODO: why can't we do the same cast manipulation for the local L1?
    # TODO: l2OutputOracleStartingTimestamp ???

    if os.path.isfile(config.paths.l1_genesis_path):
        deploy_config["l1StartingBlockTag"] = "earliest"
        l1_genesis = lib.read_json_file(config.paths.l1_genesis_path)
        deploy_config["l1GenesisBlockTimestamp"] = l1_genesis["timestamp"]

    else:
        try:
            out = lib.run(
                "get latest block",
                f"cast block latest --rpc-url {config.l1_rpc} "
                "| grep -E '(hash|number|timestamp)' "
                "| awk '{print $2}'",
                forward="capture")
            [blockhash, number, timestamp, *_rest] = out.split("\n")
            deploy_config["l1StartingBlockTag"] = blockhash
            deploy_config["l2OutputOracleStartingTimestamp"] = int(timestamp)
            lib.debug(f"L1 starting block is {number} ({blockhash} at time {timestamp})")
        except Exception as e:
            raise lib.extend_exception(e, "Failed to get latest block")

    deploy_config["l1ChainID"] = config.l1_chain_id
    deploy_config["l2ChainID"] = config.l2_chain_id

    deploy_config["enableGovernance"] = config.enable_governance
    deploy_config["governanceTokenSymbol"] = config.governance_token_symbol
    deploy_config["governanceTokenName"] = config.governance_token_name
    deploy_config["governanceTokenOwner"] = config.admin_account

    deploy_config["p2pSequencerAddress"] = config.p2p_sequencer_account
    deploy_config["batchSenderAddress"] = config.batcher_account
    deploy_config["l2OutputOracleProposer"] = config.proposer_account
    deploy_config["l2OutputOracleChallenger"] = config.admin_account
    deploy_config["proxyAdminOwner"] = config.admin_account
    deploy_config["baseFeeVaultRecipient"] = config.admin_account
    deploy_config["l1FeeVaultRecipient"] = config.admin_account
    deploy_config["sequencerFeeVaultRecipient"] = config.admin_account
    deploy_config["finalSystemOwner"] = config.admin_account
    deploy_config["portalGuardian"] = config.admin_account
    deploy_config["controller"] = config.admin_account

    deploy_config["batchInboxAddress"] = config.batch_inbox_address

    # NOTE: temporarily make it faster because right now it's too slow to see if it works
    # TODO: undo this
    deploy_config["l2OutputOracleSubmissionInterval"] = 20

    # NOTE: devnet account config
    # proxyAdminOwner, finalSystemOwner, portalGuardian, baseFeeVaultRecipient,
    #    and governanceTokenOwner is 0xBcd4042DE499D14e55001CcbB24a551F3b954096
    # controller is 0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266 (0th test junk account)
    # challenger is 0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65
    # l1FeeVaultRecipient is 0x71bE63f3384f5fb98995898A86B02Fb2426c5788
    # sequencerFeeVaultRecipient is 0xfabb0ac9d68b0b445fb7357272ff202c5651694a
    #
    # These seems to be the standard hardhat dev accounts, different from the "test junk" mnemonic
    # accounts used by Anvil by default. List here:
    # https://github.com/ethereum-optimism/optimism/blob/develop/op-chain-ops/genesis/helpers.go#L34

    try:
        lib.write_json_file(config.deploy_config_path, deploy_config)
    except Exception as err:
        raise lib.extend_exception(err, prefix="Failed to generate devnet L1 config: ")


####################################################################################################

def deploy_l1_contracts(config: Config):
    """
    Deploy the L1 contracts to an L1.
    Currently assumes the L1 is a local devnet L1.
    """

    if os.path.exists(config.paths.addresses_json_path):
        print("L1 contracts already deployed.")
        return

    deploy_script = "scripts/Deploy.s.sol:Deploy"

    env = {**os.environ,
           "DEPLOYMENT_CONTEXT": config.deployment_name,
           "ETH_RPC_URL": config.l1_rpc}

    log_file = "logs/deploy_l1_contracts.log"
    print(f"Deploying contracts to L1. Logging to {log_file}")
    slow = "--slow" if config.deploy_slowly else ""
    lib.run_roll_log(
        "deploy contracts",
        f"forge script {deploy_script} --private-key {config.contract_deployer_key} "
        f"--gas-estimate-multiplier {config.l1_deployment_gas_multiplier} "
        f"--rpc-url {config.l1_rpc} --broadcast {slow}",
        cwd=config.paths.contracts_dir,
        env=env,
        log_file=log_file)

    log_file = "logs/create_l1_artifacts.log"
    print(f"Creating L1 deployment artifacts. Logging to {log_file}")
    lib.run_roll_log(
        "create L1 deployment artifacts",
        f"forge script {deploy_script} --private-key {config.contract_deployer_key} "
        # Note: this is probably not required since we do not actually deploy anything here,
        # but I figure it doesn't hurt?
        f"--gas-estimate-multiplier {config.l1_deployment_gas_multiplier} "
        f"--sig 'sync()' --rpc-url {config.l1_rpc}",
        cwd=config.paths.contracts_dir,
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

        lib.write_json_file(config.paths.addresses_json_path, addresses)
        lib.write_json_file(config.paths.sdk_addresses_json_path, sdk_addresses)
        print(f"Wrote L1 contract addresses to {config.paths.addresses_json_path}")

    except Exception as err:
        raise lib.extend_exception(
            err, prefix="Failed to extract addresses from L1 deployment artifacts: ")


####################################################################################################

def generate_l2_genesis(config: Config):
    """
    Generate the L2 genesis file and rollup configs.
    """
    if os.path.exists(config.paths.l2_genesis_path):
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
                 f"--outfile.l2={config.paths.l2_genesis_path}",
                 f"--outfile.rollup={config.paths.rollup_config_path}"],
                cwd=config.paths.op_node_dir)
        except Exception as err:
            raise lib.extend_exception(
                err, prefix="Failed to generate L2 genesis and rollup configs: ")


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
    Cleans up deployment outputs and databases, such that trying to deploy the L2 blockchain will
    proceed as though the chain hadn't been deployed previously.
    """
    if os.path.exists(config.paths.gen_dir):
        lib.debug(f"Cleaning up {config.paths.gen_dir}")
        for file_path in pathlib.Path(config.paths.gen_dir).iterdir():
            if file_path.is_file() and file_path.name != "genesis-l1.json":
                os.remove(file_path)

    l2_engine.clean(config)
    l2_node.clean()

    lib.debug(f"Cleaning up {config.deployments_dir}")
    shutil.rmtree(config.deployments_dir, ignore_errors=True)


####################################################################################################
