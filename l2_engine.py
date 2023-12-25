import os
import shutil
import sys

import l2
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

    l2.generate_jwt_secret(config)

    # Create geth db if it doesn't exist.
    os.makedirs(config.l2_engine_data_dir, exist_ok=True)

    if not os.path.exists(config.l2_engine_chaindata_dir):
        log_file = f"{config.logs_dir}/init_l2_genesis.log"
        print(f"Directory {config.l2_engine_chaindata_dir} missing, "
              "importing genesis in op-geth node."
              f"Logging to {log_file}")
        lib.run(
            "initializing genesis",
            ["op-geth",
             f"--verbosity={config.l2_engine_verbosity}",
             "init",
             f"--datadir={config.l2_engine_data_dir}",
             config.l2_genesis_path])

    log_file_path = f"{config.logs_dir}/l2_engine.log"
    print(f"Starting op-geth node. Logging to {log_file_path}")
    sys.stdout.flush()

    log_file = open(log_file_path, "w")

    command = [
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
        f"--txlookuplimit={config.l2_engine_history_transactions}"
    ]

    config.log_run_config("\n".join(command))

    PROCESS_MGR.start(
        "starting op-geth",
        command,
        forward="fd",
        stdout=log_file)

    lib.wait_for_rpc_server("127.0.0.1", config.l2_engine_rpc_listen_port)


####################################################################################################

def clean(config: Config):
    """
    Cleans up L2 execution engine's databases.
    """
    if os.path.exists(config.l2_engine_data_dir):
        lib.debug(f"Removing {config.l2_engine_data_dir}")
        shutil.rmtree(config.l2_engine_data_dir, ignore_errors=True)

####################################################################################################
