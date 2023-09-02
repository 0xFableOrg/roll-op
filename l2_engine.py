import os
import shutil
import subprocess
import sys

from config import L2Config, L2_EXECUTION_DATA_DIR
from paths import OPPaths
from processes import PROCESS_MGR

import libroll as lib


####################################################################################################

def start(config: L2Config, paths: OPPaths):
    """
    Spin the L2 execution engine (op-geth), then wait for it to be ready.
    """

    # Make sure the port isn't occupied yet.
    # Necessary on MacOS that easily allows two processes to bind to the same port.
    running = True
    try:
        lib.wait("127.0.0.1", config.l2_engine_rpc_port, retries=1)
    except Exception:
        running = False
    if running:
        raise Exception(
            "Couldn't start op-geth node: server already running at localhost:9545")

    # Create geth db if it doesn't exist.
    os.makedirs(config.l2_engine_data_dir, exist_ok=True)

    if not os.path.exists(config.l2_engine_chaindata_dir):
        log_file = "logs/init_l2_genesis.log"
        print(f"Directory {config.l2_engine_chaindata_dir} missing, "
              "importing genesis in op-geth node."
              f"Logging to {log_file}")
        lib.run(
            "initializing genesis",
            ["op-geth",
             f"--verbosity={config.l2_engine_verbosity}",
             "init",
             f"--datadir={config.l2_engine_data_dir}",
             paths.l2_genesis_path])

    log_file_path = "logs/l2_engine.log"
    print(f"Starting op-geth node. Logging to {log_file_path}")
    sys.stdout.flush()

    log_file = open(log_file_path, "w")

    PROCESS_MGR.start(
        "starting op-geth",
        [
            "op-geth",

            f"--datadir={config.l2_engine_data_dir}",
            f"--verbosity={config.l2_engine_verbosity}",

            f"--networkid={config.l2_chain_id}",
            "--syncmode=full",  # doesn't matter, it's only us
            "--gcmode=archive",

            # No peers: the blockchain is only this node
            "--nodiscover",
            "--maxpeers=0",

            # p2p network config, avoid conflicts with L1 geth nodes
            f"--port={config.l2_engine_p2p_port}",

            "--rpc.allow-unprotected-txs",

            # HTTP JSON-RPC server config
            "--http",
            "--http.corsdomain=*",
            "--http.vhosts=*",
            f"--http.addr={config.l2_engine_rpc_listen_addr}",
            f"--http.port={config.l2_engine_rpc_port}",
            "--http.api=web3,debug,eth,txpool,net,engine",

            # WebSocket JSON-RPC server config
            "--ws",
            f"--ws.addr={config.l2_engine_rpc_ws_listen_addr}",
            f"--ws.port={config.l2_engine_rpc_ws_port}",
            "--ws.origins=*",
            "--ws.api=debug,eth,txpool,net,engine",

            # Authenticated RPC config
            f"--authrpc.addr={config.l2_engine_authrpc_listen_addr}",
            f"--authrpc.port={config.l2_engine_authrpc_port}",
            "--authrpc.vhosts=*",
            f"--authrpc.jwtsecret={config.jwt_secret_path}",

            # Configuration for the metrics server (we currently don't use this)
            "--metrics",
            "--metrics.addr=0.0.0.0",
            "--metrics.port=9060",

            # Configuration for the rollup engine
            "--rollup.disabletxpoolgossip=true",
        ], forward="fd", stdout=log_file, stderr=subprocess.STDOUT)

    lib.wait_for_rpc_server("127.0.0.1", config.l2_engine_rpc_port)


####################################################################################################

def clean(paths: OPPaths):
    """
    Cleans up build outputs, such that trying to deploy the L2 execution engine (op-geth) will
    proceed as though it was the first invocation.
    """
    if os.path.exists(L2_EXECUTION_DATA_DIR):
        print(f"Cleaning up {L2_EXECUTION_DATA_DIR}")
        shutil.rmtree(L2_EXECUTION_DATA_DIR, ignore_errors=True)

####################################################################################################
