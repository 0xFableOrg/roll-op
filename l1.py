import http.client
import os
import shutil
import socket
import sys
import time
from os.path import join as pjoin

import libroll as lib
# from l1_genesis import GENESIS_TMPL
from paths import OPPaths

sys.path.append("optimism/bedrock-devnet/devnet")
# noinspection PyUnresolvedReferences
from genesis import GENESIS_TMPL


####################################################################################################

def deploy_l1_devnet(paths: OPPaths):
    """
    Spin the devnet L1 node, doing whatever tasks are necessary, including installing geth,
    generating the genesis file and config files, and deploying the L1 contracts.
    """
    os.makedirs(paths.l1_devnet_dir, exist_ok=True)

    patch(paths)
    generate_devnet_l1_genesis(paths)
    start_devnet_l1_node(paths)
    generate_devnet_l1_config(paths)
    deploy_l1_contracts(paths)


####################################################################################################

def patch(paths: OPPaths):
    """
    Apply modifications to the optimism repo necessary for our scripts to work.
    """

    # The original optimism repo edits the devnet configuration in place. Instead, we copy the
    # original over once, then use that as a template to be modified going forward.
    if not os.path.exists(paths.devnet_config_template_path):
        shutil.copy(paths.l1_devnet_config_path, paths.devnet_config_template_path)

    # /usr/bin/bash does not always exist on MacOS (and potentially other Unixes)
    # This was fixed upstream, but isn't fixed in the commit we're using
    try:
        scripts = pjoin(paths.contracts_dir, "scripts")
        deployer_path = pjoin(scripts, "Deployer.sol")
        deploy_config_path = pjoin(scripts, "DeployConfig.s.sol")
        lib.replace_in_file(deployer_path, {"/usr/bin/bash": "bash"})
        lib.replace_in_file(deploy_config_path, {"/usr/bin/bash": "bash"})
    except Exception as err:
        raise lib.extend_exception(err, prefix="Failed to patch Solidity scripts: ")


####################################################################################################

def generate_devnet_l1_genesis(paths: OPPaths):
    """
    Generate the L1 genesis file (simply copies the template).
    """
    if os.path.exists(paths.l1_genesis_path):
        print("L1 genesis already generated.")
    else:
        print("Generating L1 genesis.")
        try:
            lib.write_json_file(paths.l1_genesis_path, GENESIS_TMPL)
        except Exception as err:
            raise lib.extend_exception(err, prefix="Failed to generate L1 genesis: ")


####################################################################################################

def start_devnet_l1_node(paths: OPPaths):
    """
    Spin the devnet L1 node (currently: via `docker compose`), then wait for it to be ready.
    """

    # Make sure the port isn't occupied yet.
    # Necessary on MacOS that easily allows two processes to bind to the same port.
    running = True
    try:
        wait("127.0.0.1", 8545, retries=3)
    except Exception:
        running = False
    if running:
        raise Exception("Couldn't start L1 node: server already running at localhost:8545")

    log_file = "logs/start_l1_node.log"
    print(f"Starting L1 node. Logging to {log_file}")

    lib.run_roll_log(
        "start devnet L1 node",
        "docker compose up -d l1",
        cwd=paths.ops_bedrock_dir,
        env={**os.environ, "PWD": paths.ops_bedrock_dir},
        log_file=log_file)
    print("L1 node successfully started.")

    wait_for_rpc_server("127.0.0.1", 8545)

####################################################################################################

def wait(address: str, port: int, retries: int = 10, wait_secs: int = 1):
    """
    Waits for `address:port` to be reachable. Will try up to `retries` times, waiting `wait_secs`
    in between each attempt.
    """
    for i in range(0, retries):
        lib.debug(f"Trying {address}:{port}")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Note: this has no internal timeout, fails immediately if unreachable.
            s.connect((address, int(port)))
            s.shutdown(socket.SHUT_RDWR)
            lib.debug(f"Connected to {address}:{port}")
            return True
        except Exception:
            print("Waiting for {address}:{port}")
            if i < retries - 1:
                time.sleep(wait_secs)

    raise Exception(f"Timed out waiting for {address}:{port}.")


####################################################################################################

def wait_for_rpc_server(address: str, port: int, retries: int = 5, wait_secs=3):
    """
    Waits for a JSON-RPC server to be available at `url` (ascertained by asking for the chain ID).
    Retries until the server responds with a successful status code, waiting `wait_secs` in between
    tries, with at most `retries` attempts.
    """
    url = f"{address}:{port}"
    print(f"Waiting for RPC server at {url}...")

    conn = http.client.HTTPConnection(url)
    headers = {"Content-type": "application/json"}
    body = '{"id":1, "jsonrpc":"2.0", "method": "eth_chainId", "params":[]}'

    for i in range(0, retries):
        try:
            conn.request("POST", "/", body, headers)
            response = conn.getresponse()
            conn.close()
            if response.status < 300:
                lib.debug(f"RPC server at {url} ready")
                return
        except Exception:
            time.sleep(wait_secs)


####################################################################################################

def generate_devnet_l1_config(paths: OPPaths):
    """
    Generate the devnet L1 config file.
    """
    print("Generating network config.")

    try:
        # copy the template, and modify it with timestamp and starting block tag
        deploy_config = lib.read_json_file(paths.devnet_config_template_path)
        deploy_config["l1GenesisBlockTimestamp"] = GENESIS_TMPL["timestamp"]
        deploy_config["l1StartingBlockTag"] = "earliest"
        lib.write_json_file(paths.l1_devnet_config_path, deploy_config)
    except Exception as err:
        raise lib.extend_exception(err, prefix="Failed to generate devnet L1 config: ")


####################################################################################################

def deploy_l1_contracts(paths):
    """
    Deploy the L1 contracts to an L1.
    Currently assumes the L1 is a local L1 devnet.
    """

    if os.path.exists(paths.addresses_json_path):
        print("Contracts already deployed.")
        return

    deploy_script = "scripts/Deploy.s.sol:Deploy"

    # Private key of first dev Hardhat/Anvil account
    private_key = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

    log_file = "logs/deploy_l1_contracts.log"
    print(f"Deploying contracts to L1. Logging to {log_file}")
    lib.run_roll_log(
        "deploy contracts",
        f"forge script {deploy_script} --private-key {private_key} "
        + "--rpc-url http://127.0.0.1:8545 --broadcast",
        cwd=paths.contracts_dir,
        log_file=log_file)

    log_file = "logs/create_l1_artifacts.log"
    print(f"Creating L1 deployment artifacts. Logging to {log_file}")
    lib.run_roll_log(
        "create L1 deployment artifacts",
        f"forge script {deploy_script} --private-key {private_key} --sig 'sync()' "
        + "--rpc-url http://127.0.0.1:8545 --broadcast",
        cwd=paths.contracts_dir,
        log_file=log_file)

    try:
        # Read the addresses in the L1 deployment artifacts and store them in json files
        contracts = os.listdir(paths.l1_devnet_deployment_dir)
        addresses = {}

        for c in contracts:
            if not c.endswith(".json"):
                continue
            data = lib.read_json_file(pjoin(paths.l1_devnet_deployment_dir, c))
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

def clean(paths: OPPaths):
    """
    Cleans up build outputs, such that trying to deploy the L1 devnet will proceed as though it was
    the first invocation.
    """
    if os.path.exists(paths.l1_devnet_dir):
        print(f"Cleaning up {paths.l1_devnet_dir}")
        shutil.rmtree(paths.l1_devnet_dir)

####################################################################################################
