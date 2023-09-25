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
from config import Config
from paths import OPPaths
from processes import PROCESS_MGR


####################################################################################################

DEVNET_L1_DATA_DIR = "db/devnetL1"
"""Directory to store the devnet L1 blockchain data."""


####################################################################################################

def deploy_devnet_l1(config: Config):
    """
    Spin the devnet L1 node, doing whatever tasks are necessary, including installing geth,
    generating the genesis file and config files, and deploying the L1 contracts.
    """
    os.makedirs(config.paths.gen_dir, exist_ok=True)

    generate_devnet_l1_genesis(config)
    start_devnet_l1_node(config)
    print("Devnet L1 deployment is complete! L1 node is running.")


####################################################################################################

GENESIS_TMPL = {}


def generate_devnet_l1_genesis(config: Config):
    """
    Generate the L1 genesis file (simply copies the template).
    """
    if os.path.exists(config.paths.l1_genesis_path):
        print("L1 genesis already generated.")
    else:
        print("Generating L1 genesis.")
        try:
            global GENESIS_TMPL  # overriden by exec below
            with open("optimism/bedrock-devnet/devnet/genesis.py") as f:
                exec(f.read(), globals(), globals())
            GENESIS_TMPL["config"]["chainId"] = config.l1_chain_id
            lib.write_json_file(config.paths.l1_genesis_path, GENESIS_TMPL)
        except Exception as err:
            raise lib.extend_exception(err, prefix="Failed to generate L1 genesis: ")


####################################################################################################

def start_devnet_l1_node(config: Config):
    """
    Spin the devnet L1 node (currently: via `docker compose`), then wait for it to be ready.
    """

    # Make sure the port isn't occupied yet.
    # Necessary on MacOS that easily allows two processes to bind to the same port.
    running = True
    try:
        lib.wait("127.0.0.1", config.l1_rpc_port, retries=1)
    except Exception:
        running = False
    if running:
        raise Exception(
            f"Couldn't start L1 node: server already running at localhost:{config.l1_rpc_port}")

    # Create geth db if it doesn't exist.
    os.makedirs(DEVNET_L1_DATA_DIR, exist_ok=True)

    if not os.path.exists(config.l1_keystore_dir):
        # Initial account setup
        print(f"Directory '{config.l1_keystore_dir}' missing, running account import.")
        with open(config.l1_password_path, "w") as f:
            f.write(config.l1_password)
        with open(config.l1_tmp_signer_key_path, "w") as f:
            f.write(config.l1_signer_private_key.replace("0x", ""))
        lib.run(
            "importing signing keys",
            ["geth", "account", "import",
             f"--datadir={config.l1_data_dir}",
             f"--password={config.l1_password_path}",
             config.l1_tmp_signer_key_path])
        os.remove(f"{config.l1_data_dir}/block-signer-key")

    if not os.path.exists(config.l1_chaindata_dir):
        log_file = "logs/init_l1_genesis.log"
        print(f"Directory {config.l1_chaindata_dir} missing, importing genesis in L1 node."
              f"Logging to {log_file}")
        lib.run(
            "initializing genesis",
            ["geth",
             f"--verbosity={config.l1_verbosity}",
             "init",
             f"--datadir={config.l1_data_dir}",
             config.paths.l1_genesis_path])

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

            f"--datadir={config.l1_data_dir}",
            f"--verbosity={config.l1_verbosity}",

            f"--networkid={config.l1_chain_id}",
            "--syncmode=full",  # doesn't matter, it's only us
            "--gcmode=archive",
            "--rpc.allow-unprotected-txs",  # allow legacy transactions for deterministic deployment

            # p2p network config
            f"--port={config.l1_p2p_port}",

            # No peers: the blockchain is only this node
            "--nodiscover",
            "--maxpeers=1",

            # HTTP JSON-RPC server config
            "--http",
            "--http.corsdomain=*",
            "--http.vhosts=*",
            f"--http.addr={config.l1_rpc_listen_addr}",
            f"--http.port={config.l1_rpc_port}",
            "--http.api=web3,debug,eth,txpool,net,engine",

            # WebSocket JSON-RPC server config
            "--ws",
            f"--ws.addr={config.l1_rpc_ws_listen_addr}",
            f"--ws.port={config.l1_rpc_ws_port}",
            "--ws.origins=*",
            "--ws.api=debug,eth,txpool,net,engine",

            # Configuration for clique signing, clique itself is enabled via the genesis file
            f"--unlock={config.l1_signer_account}",
            "--mine",
            f"--miner.etherbase={config.l1_signer_account}",
            f"--password={config.l1_password_path}",
            "--allow-insecure-unlock",

            # Authenticated RPC config
            f"--authrpc.addr={config.l1_authrpc_listen_addr}",
            f"--authrpc.port={config.l1_authrpc_port}",
            # NOTE: The Optimism monorepo accepts connections from any host, and specifies the JWT
            # secret to be the same used on L2. We don't see any reason to do that (we never use
            # authenticated RPC), so we restrict access to localhost only (authrpc can't be turned
            # off), and don't specify the JWT secret (`--authrpc.jwtsecret=jwt_secret_path`) which
            # causes a random secret to be created in `config.l1_data_dir/geth/jwtsecret`.
            "--authrpc.vhosts=127.0.0.1",

            # Configuration for the metrics server (we currently don't use this)
            "--metrics",
            "--metrics.addr=0.0.0.0",
            "--metrics.port=6060"
        ], forward="fd", stdout=log_file, stderr=subprocess.STDOUT)

    lib.wait_for_rpc_server("127.0.0.1", config.l1_rpc_port)


####################################################################################################

def clean(paths: OPPaths):
    """
    Cleans up build outputs, such that trying to deploy the devnet L1 node will proceed as though it
    was the first invocation.
    """
    if os.path.exists(paths.gen_dir):
        path = os.path.join(paths.gen_dir, "genesis-l1.json")
        pathlib.Path(path).unlink(missing_ok=True)

    if os.path.exists(DEVNET_L1_DATA_DIR):
        print(f"Cleaning up {DEVNET_L1_DATA_DIR}")
        shutil.rmtree(DEVNET_L1_DATA_DIR, ignore_errors=True)

####################################################################################################
