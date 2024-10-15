import os

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
              "importing genesis in op-geth node.\n"
              f"Logging to {log_file}")
        lib.run(
            "initializing genesis",
            [
                "op-geth",
                f"--verbosity={config.l2_engine_verbosity}",
                "init",
                f"--datadir={config.l2_engine_data_dir}",
                "--state.scheme=hash",
                config.l2_genesis_path
            ],
            file=log_file)

    log_file = config.l2_engine_log_file
    print(f"Starting op-geth node. Logging to {log_file}")

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
        f"--history.transactions={config.l2_engine_history_transactions}",
        "--state.scheme=hash"  # TODO: investigate why state.scheme=path is not working
    ]

    config.log_l2_command("\n".join(command))

    def on_exit():
        print(f"L2 engine exited. Check {log_file} for details.\n"
              "You can re-run with `./rollop l2-engine` in another terminal\n"
              "(!! Make sure to specify the same config file and flags!)")

    PROCESS_MGR.start(
        "starting op-geth",
        command,
        file=log_file,
        on_exit=on_exit)

    lib.wait_for_rpc_server("127.0.0.1", config.l2_engine_rpc_listen_port)


####################################################################################################

def clean(config: Config):
    """
    Cleans up L2 execution engine's databases.
    """
    lib.remove_paths(config, [config.l2_engine_data_dir])

####################################################################################################
