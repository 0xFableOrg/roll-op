"""
This module defines functions related to spinning a devnet L1 node, and deploying L1 contracts
on an L1 blockchain (for now only devnet, but in the future, any kind of L1).
"""

import os
import pathlib
import shutil
import subprocess
import sys

import libroll as lib
from config import L2Config
from paths import OPPaths
from processes import PROCESS_MGR


####################################################################################################

DEVNET_L1_DATA_DIR = "db/devnetL1"
"""Directory to store the devnet L1 blockchain data."""


####################################################################################################

def deploy_devnet_l1(config: L2Config, paths: OPPaths):
    """
    Spin the devnet L1 node, doing whatever tasks are necessary, including installing geth,
    generating the genesis file and config files, and deploying the L1 contracts.
    """
    os.makedirs(paths.devnet_gen_dir, exist_ok=True)

    generate_devnet_l1_genesis(config, paths)
    start_devnet_l1_node(config, paths)
    print("Devnet L1 deployment is complete! L1 node is running.")


####################################################################################################

GENESIS_TMPL = {}


def generate_devnet_l1_genesis(config: L2Config, paths: OPPaths):
    """
    Generate the L1 genesis file (simply copies the template).
    """
    if os.path.exists(paths.l1_genesis_path):
        print("L1 genesis already generated.")
    else:
        print("Generating L1 genesis.")
        try:
            global GENESIS_TMPL  # overriden by exec below
            with open("optimism/bedrock-devnet/devnet/genesis.py") as f:
                exec(f.read(), globals(), globals())
            GENESIS_TMPL["config"]["chainId"] = config.l1_chain_id
            lib.write_json_file(paths.l1_genesis_path, GENESIS_TMPL)
        except Exception as err:
            raise lib.extend_exception(err, prefix="Failed to generate L1 genesis: ")


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

def start_devnet_l1_node(config: L2Config, paths: OPPaths):
    """
    Spin the devnet L1 node (currently: via `docker compose`), then wait for it to be ready.
    """

    cfg = DevnetL1Config(DEVNET_L1_DATA_DIR, paths)

    # Make sure the port isn't occupied yet.
    # Necessary on MacOS that easily allows two processes to bind to the same port.
    running = True
    try:
        lib.wait("127.0.0.1", cfg.rpc_port, retries=1)
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
    log_file = open(log_file_path, "w")

    # NOTE: The devnet L1 node must be an archive node, otherwise pruning happens within minutes of
    # starting the node. This could be an issue if the op-node is brought down or restarted later,
    # or if the sequencing window is larger than the time-to-prune.

    PROCESS_MGR.start(
        "starting geth",
        [
            "geth",

            f"--datadir={cfg.data_dir}",
            f"--verbosity={cfg.verbosity}",

            f"--networkid={config.l1_chain_id}",
            "--syncmode=full",  # doesn't matter, it's only us
            "--gcmode=archive",
            "--rpc.allow-unprotected-txs", # allow legacy transactions for deterministic deployment

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

    lib.wait_for_rpc_server("127.0.0.1", cfg.rpc_port)


####################################################################################################

def clean(paths: OPPaths):
    """
    Cleans up build outputs, such that trying to deploy the devnet L1 node will proceed as though it
    was the first invocation.
    """
    if os.path.exists(paths.devnet_gen_dir):
        path = os.path.join(paths.devnet_gen_dir, "genesis-l1.json")
        pathlib.Path(path).unlink(missing_ok=True)

    if os.path.exists(DEVNET_L1_DATA_DIR):
        print(f"Cleaning up {DEVNET_L1_DATA_DIR}")
        shutil.rmtree(DEVNET_L1_DATA_DIR, ignore_errors=True)

####################################################################################################
