"""
This module defines functions related to spinning an op-geth node.
"""

import os
import shutil
import subprocess
import sys

import libroll as lib
from paths import OPPaths
from processes import PROCESS_MGR


####################################################################################################

L2_EXECUTION_DATA_DIR = "db/L2-execution"
"""Directory to store the op-geth blockchain data."""


####################################################################################################

def deploy_l2_execution(paths: OPPaths):
    """
    Spin the l2 execution node, doing whatever tasks are necessary, including installing op-geth,
    generating the genesis file and config files.
    """
    generate_l2_execution_genesis(paths)
    start_l2_execution_node(paths)
    print("L2 execution deployment is complete! L2 execution node is running.")
    PROCESS_MGR.wait_all()


####################################################################################################

def generate_l2_execution_genesis(paths: OPPaths):
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
            raise lib.extend_exception(err, prefix="Failed to generate L2 genesis and rollup configs: ")


####################################################################################################


class L2ExecutionConfig:
    def __init__(self, geth_data_dir: str, paths: OPPaths):
        self.data_dir = geth_data_dir
        """Geth data directory for op-geth node."""

        self.chaindata_dir = f"{self.data_dir}/geth/chaindata"
        """Directory storing chain data."""

        genesis = lib.read_json_file(paths.l2_genesis_path)
        self.chain_id = genesis["config"]["chainId"]

        self.jwt_secret_path = paths.jwt_test_secret_path
        """Path for Jason Web Token secret, used for op-geth rpc auth."""

        # For the following values, allow environment override for now, to follow the original.
        # In due time, remove that as we provide our own way to customize.

        self.verbosity = os.environ.get("GETH_VERBOSITY", 3)
        """Geth verbosity level (from 0 to 5, see geth --help)."""

        self.rpc_port = os.environ.get("RPC_PORT", 9545)
        """Port to use for the http-based JSON-RPC server."""

        self.ws_port = os.environ.get("WS_PORT", 9546)
        """Port to use for the WebSocket-based JSON_RPC server."""


####################################################################################################

def start_l2_execution_node(paths: OPPaths):
    """
    Spin the op-geth node, then wait for it to be ready.
    """

    cfg = L2ExecutionConfig(L2_EXECUTION_DATA_DIR, paths)

    # Make sure the port isn't occupied yet.
    # Necessary on MacOS that easily allows two processes to bind to the same port.
    running = True
    try:
        lib.wait("127.0.0.1", cfg.rpc_port, retries=1)
    except Exception:
        running = False
    if running:
        raise Exception(
            "Couldn't start op-geth node: server already running at localhost:9545")

    # Create geth db if it doesn't exist.
    os.makedirs(L2_EXECUTION_DATA_DIR, exist_ok=True)

    if not os.path.exists(cfg.chaindata_dir):
        log_file = "logs/init_l2_genesis.log"
        print(f"Directory {cfg.chaindata_dir} missing, importing genesis in op-geth node."
              f"Logging to {log_file}")
        lib.run(
            "initializing genesis",
            ["op-geth",
             f"--verbosity={cfg.verbosity}",
             "init",
             f"--datadir={cfg.data_dir}",
             paths.l2_genesis_path])

    log_file_path = "logs/l2_node.log"
    print(f"Starting op-geth node. Logging to {log_file_path}")
    sys.stdout.flush()

    log_file = open(log_file_path, "w")

    PROCESS_MGR.start(
        "starting op-geth",
        [
            "op-geth",

            f"--datadir={cfg.data_dir}",
            f"--verbosity={cfg.verbosity}",

            f"--networkid={cfg.chain_id}",
            "--syncmode=full",  # doesn't matter, it's only us
            "--gcmode=archive",

            # No peers: the blockchain is only this node
            "--nodiscover",
            "--maxpeers=0",

            "--rpc.allow-unprotected-txs",

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

            # Network config, avoid conflicts with L1 geth nodes
            "--port=30313",

            # Authenticated RPC config
            "--authrpc.addr=0.0.0.0",
            "--authrpc.port=9551",
            "--authrpc.vhosts=*",
            f"--authrpc.jwtsecret={cfg.jwt_secret_path}",

            # Configuration for the metrics server (we currently don't use this)
            "--metrics",
            "--metrics.addr=0.0.0.0",
            "--metrics.port=9060",

            # Configuration for the rollup engine
            "--rollup.disabletxpoolgossip=true",
        ], forward="fd", stdout=log_file, stderr=subprocess.STDOUT)

    lib.wait_for_rpc_server("127.0.0.1", cfg.rpc_port)


####################################################################################################


def clean(paths: OPPaths):
    """
    Cleans up build outputs, such that trying to deploy the op-geth node will proceed as though it
    was the first invocation.
    """
    if os.path.exists(paths.devnet_gen_dir):
        lib.debug(f"Cleaning up {paths.devnet_gen_dir}")
        shutil.rmtree(paths.devnet_gen_dir, ignore_errors=True)

    if os.path.exists(L2_EXECUTION_DATA_DIR):
        print(f"Cleaning up {L2_EXECUTION_DATA_DIR}")
        shutil.rmtree(L2_EXECUTION_DATA_DIR, ignore_errors=True)

####################################################################################################
