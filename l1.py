"""
This module defines functions related to spinning a devnet L1 node, and deploying L1 contracts
on an L1 blockchain (for now only devnet, but in the future, any kind of L1).
"""

import http.client
import os
import shutil
import socket
import subprocess
import sys
import time
from os.path import join as pjoin

import libroll as lib
# from l1_genesis import GENESIS_TMPL
from paths import OPPaths
from processes import PROCESS_MGR

sys.path.append("optimism/bedrock-devnet/devnet")
# noinspection PyUnresolvedReferences
from genesis import GENESIS_TMPL


####################################################################################################

DEVNET_L1_DATA_DIR = "db/devnetL1"
"""Directory to store the devnet L1 blockchain data."""


####################################################################################################

def deploy_l1_devnet(paths: OPPaths):
    """
    Spin the devnet L1 node, doing whatever tasks are necessary, including installing geth,
    generating the genesis file and config files, and deploying the L1 contracts.
    """
    os.makedirs(paths.devnet_l1_gen_dir, exist_ok=True)

    patch(paths)
    generate_devnet_l1_genesis(paths)
    generate_network_config(paths)
    start_devnet_l1_node(paths)
    deploy_l1_contracts(paths)
    print("Devnet L1 deployment is complete! L1 node is running.")
    PROCESS_MGR.wait_all()


####################################################################################################

def patch(paths: OPPaths):
    """
    Apply modifications to the optimism repo necessary for our scripts to work.
    """

    # The original optimism repo edits the devnet configuration in place. Instead, we copy the
    # original over once, then use that as a template to be modified going forward.
    if not os.path.exists(paths.network_config_template_path):
        shutil.copy(paths.network_config_path, paths.network_config_template_path)

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

def generate_network_config(paths: OPPaths):
    """
    Generate the network configuration file. This records information about the L1 and the L2.
    Notaly, it is not read when spinning the L1 node.
    """
    print("Generating network config.")

    try:
        # Copy the template, and modify it with timestamp and starting block tag.

        # Note that we pick the timestamp at the time this file is generated. This doesn't matter
        # much: if we start the L1 node later, it will simply have two consecutive blocks with a
        # large timestamp difference, but no other consequences. The same logic applies if we shut
        # down the node and restart it later.

        deploy_config = lib.read_json_file(paths.network_config_template_path)
        deploy_config["l1GenesisBlockTimestamp"] = GENESIS_TMPL["timestamp"]
        deploy_config["l1StartingBlockTag"] = "earliest"
    except Exception as err:
        raise lib.extend_exception(err, prefix="Failed to generate devnet L1 config: ")


####################################################################################################

class DevnetL1Config:
    def __init__(self, geth_data_dir: str, paths: OPPaths):
        self.data_dir = geth_data_dir
        """Geth data directory for devnet L1 node."""

        self.keystore_dir = f"{self.data_dir}/keystore"
        """Keystore directory for devnet L1 node (each file stores an encrypted signer key)."""

        self.chaindata_dir = f"{self.data_dir}/geth/chaindata"
        """Directory storing chain data."""

        self.password_path = f"{self.data_dir}/password"
        """Path to file storing the password for the signer key."""

        self.password = "l1_devnet_password"
        """Password to use to secure the signer key."""

        self.tmp_signer_key_path = f"{self.data_dir}/block-signer-key"
        """Path to file storing the signer key during the initial import."""

        self.signer_address = "0xca062b0fd91172d89bcd4bb084ac4e21972cc467"
        """Address of the block signer."""

        self.signer_private_key = "3e4bde571b86929bf08e2aaad9a6a1882664cd5e65b96fff7d03e1c4e6dfa15c"
        """Private key of the block signer."""

        genesis = lib.read_json_file(paths.l1_genesis_path)
        self.chain_id = genesis["config"]["chainId"]

        self.jwt_secret_path = paths.ops_bedrock_dir + "/test-jwt-secret.txt"
        """Path for Jason Web Token secret, probably useless for devnet L1."""

        # For the following values, allow environment override for now, to follow the original.
        # In due time, remove that as we provide our own way to customize.

        self.verbosity = os.environ.get("GETH_VERBOSITY", 3)
        """Geth verbosity level (from 0 to 5, see geth --help)."""

        self.rpc_port = os.environ.get("RPC_PORT", 8545)
        """Port to use for the http-based JSON-RPC server."""

        self.ws_port = os.environ.get("WS_PORT", 8546)
        """Port to use for the WebSocket-based JSON_RPC server."""


####################################################################################################

def start_devnet_l1_node(paths: OPPaths):
    """
    Spin the devnet L1 node (currently: via `docker compose`), then wait for it to be ready.
    """

    cfg = DevnetL1Config(DEVNET_L1_DATA_DIR, paths)

    # Make sure the port isn't occupied yet.
    # Necessary on MacOS that easily allows two processes to bind to the same port.
    running = True
    try:
        wait("127.0.0.1", cfg.rpc_port, retries=1)
    except Exception:
        running = False
    if running:
        raise Exception("Couldn't start L1 node: server already running at localhost:8545")

    # Create geth db if it doesn't exist.
    os.makedirs(DEVNET_L1_DATA_DIR, exist_ok=True)

    if not os.path.exists(cfg.keystore_dir):
        # Initial account setup
        print(f"Directory '{cfg.keystore_dir}' missing, running account import.")
        with open(cfg.password_path, "w") as f:
            f.write(cfg.password)
        with open(cfg.tmp_signer_key_path, "w") as f:
            f.write(cfg.signer_private_key.replace("0x", ""))
        lib.run(
            "importing signing keys",
            ["geth", "account", "import",
             f"--datadir={cfg.data_dir}",
             f"--password={cfg.password_path}",
             cfg.tmp_signer_key_path])
        os.remove(f"{cfg.data_dir}/block-signer-key")

    if not os.path.exists(cfg.chaindata_dir):
        log_file = "logs/init_l1_genesis.log"
        print(f"Directory {cfg.chaindata_dir} missing, importing genesis in L1 node."
              f"Logging to {log_file}")
        lib.run(
            "initializing genesis",
            ["geth",
             f"--verbosity={cfg.verbosity}",
             "init",
             f"--datadir={cfg.data_dir}",
             paths.l1_genesis_path])

    log_file_path = "logs/l1_node.log"
    print(f"Starting L1 node. Logging to {log_file_path}")
    sys.stdout.flush()

    # NOTE: The devnet L1 node must be an archive node, otherwise pruning happens within minutes of
    # starting the node. This could be an issue if the op-node is brought down or restarted later,
    # or if the sequencing window is larger than the time-to-prune.

    log_file = open(log_file_path, "w")

    PROCESS_MGR.start(
        "starting geth",
        [
            "geth",

            f"--datadir={cfg.data_dir}",
            f"--verbosity={cfg.verbosity}",

            f"--networkid={cfg.chain_id}",
            "--syncmode=full",  # doesn't matter, it's only us
            "--gcmode=archive",

            # No peers: the blockchain is only this node
            "--nodiscover",
            "--maxpeers=1",

            # HTTP JSON-RPC server config
            "--http",
            "--http.corsdomain=*",
            "--http.vhosts=*",
            "--http.addr=0.0.0.0",
            f"--http.port={cfg.rpc_port}",
            "--http.api=web3,debug,eth,txpool,net,engine",

            # WebSocket JSON-RPC server config
            "--ws",
            "--ws.addr=0.0.0.0",
            f"--ws.port={cfg.ws_port}",
            "--ws.origins=*",
            "--ws.api=debug,eth,txpool,net,engine",

            # Configuration for clique signing, clique itself is enabled via the genesis file
            f"--unlock={cfg.signer_address}",
            "--mine",
            f"--miner.etherbase={cfg.signer_address}",
            f"--password={cfg.data_dir}/password",
            "--allow-insecure-unlock",

            # Authenticated RPC config
            # TODO Do we use or need this for the devnet?
            #      I think it's only for connection to a consensus client, or between op-node and
            #      the L2 execution engine.
            "--authrpc.addr=0.0.0.0",
            "--authrpc.port=8551",
            "--authrpc.vhosts=*",
            f"--authrpc.jwtsecret={cfg.jwt_secret_path}",

            # Configuration for the metrics server (we currently don't use this)
            "--metrics",
            "--metrics.addr=0.0.0.0",
            "--metrics.port=6060"
        ], forward="fd", stdout=log_file, stderr=subprocess.STDOUT)

    wait_for_rpc_server("127.0.0.1", cfg.rpc_port)


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
            if i < retries - 1:
                print(f"Waiting for {address}:{port}")
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

def deploy_l1_contracts(paths):
    """
    Deploy the L1 contracts to an L1.
    Currently assumes the L1 is a local devnet L1.
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
            data = lib.read_json_file(pjoin(paths.devnet_l1_deployment_dir, c))
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
    Cleans up build outputs, such that trying to deploy the devnet L1 node will proceed as though it
    was the first invocation.
    """
    if os.path.exists(paths.devnet_l1_gen_dir):
        print(f"Cleaning up {paths.devnet_l1_gen_dir}")
        shutil.rmtree(paths.devnet_l1_gen_dir, ignore_errors=True)
        shutil.rmtree(DEVNET_L1_DATA_DIR, ignore_errors=True)

####################################################################################################
