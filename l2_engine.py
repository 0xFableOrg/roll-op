import os
import shutil
import sys

from config import Config
from processes import PROCESS_MGR

import libroll as lib


####################################################################################################

def start(config: Config):
    """
    Spin the L2 execution engine (op-geth), then wait for it to be ready.
    """

    lib.ensure_port_unoccupied(
        "op-geth", config.l2_engine_rpc_listen_addr, config.l2_engine_rpc_listen_port)

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
             config.paths.l2_genesis_path])

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

            "--rpc.allow-unprotected-txs",  # allow legacy transactions for deterministic deployment

            # HTTP JSON-RPC server config
            "--http",
            "--http.corsdomain=*",
            "--http.vhosts=*",
            f"--http.addr={config.l2_engine_rpc_listen_addr}",
            f"--http.port={config.l2_engine_rpc_listen_port}",
            "--http.api=web3,debug,eth,txpool,net,engine",

            # WebSocket JSON-RPC server config
            "--ws",
            f"--ws.addr={config.l2_engine_rpc_ws_listen_addr}",
            f"--ws.port={config.l2_engine_rpc_ws_listen_port}",
            "--ws.origins=*",
            "--ws.api=debug,eth,txpool,net,engine",

            # Authenticated RPC config
            f"--authrpc.addr={config.l2_engine_authrpc_listen_addr}",
            f"--authrpc.port={config.l2_engine_authrpc_listen_port}",
            "--authrpc.vhosts=*",
            f"--authrpc.jwtsecret={config.jwt_secret_path}",

            # Metrics Options
            *([] if not config.l2_engine_metrics else [
                "--metrics",
                f"--metrics.port={config.l2_engine_metrics_listen_port}",
                f"--metrics.addr={config.l2_engine_metrics_listen_addr}"]),

            # Configuration for the rollup engine
            f"--rollup.disabletxpoolgossip={config.l2_engine_disable_tx_gossip}",

            # Other geth options
            f"--txlookuplimit={config.l2_engine_history_transactions}",

        ], forward="fd", stdout=log_file)

    lib.wait_for_rpc_server("127.0.0.1", config.l2_engine_rpc_listen_port)


####################################################################################################

def clean(config: Config):
    """
    Cleans up L2 execution engine's databases, such that trying to start the L2 execution engine
    (op-geth) will proceed as though it had never been started before (this might cause problems
    if the rest of the system hasn't been similarly reset).
    """
    if os.path.exists(config.l2_engine_data_dir):
        print(f"Cleaning up {config.l2_engine_data_dir}")
        shutil.rmtree(config.l2_engine_data_dir, ignore_errors=True)

####################################################################################################
