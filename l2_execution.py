"""
This module defines functions related to spinning an op-geth node.
"""

import os
import shutil
import subprocess
import sys

import libroll as lib
from config import L2Config
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

    log_file_path = "logs/l2_engine.log"
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
# New Stuff
####################################################################################################

def deploy_l2(paths: OPPaths):
    """
    Deploys all components of the L2 system: the
    Spin the devnet op-geth node, doing whatever tasks are necessary, including installing op-geth,
    generating the genesis file and config files.
    """
    generate_l2_execution_genesis(paths)

    config = L2Config()
    config.use_devnet_config(paths)
    rollup_config_dict = lib.read_json_file(paths.rollup_config_path)
    config.load_rollup_config(rollup_config_dict)

    deployments = lib.read_json_file(paths.addresses_json_path)

    if deployments.get("L2OutputOracleProxy") is None:
        raise Exception(
            "L2OutputOracleProxy address not found in addresses.json. "
            "Try redeploying the L1 contracts.")

    start_l2_execution_node(paths)
    start_l2_node(config, paths, sequencer=True)
    start_l2_proposer(config, deployments)
    start_l2_batcher(config)

    print("Devnet L2 deployment is complete! L2 node is running.")


####################################################################################################

def start_l2_proposer(config: L2Config, deployment: dict):
    """
    Starts the OP proposer, which proposes L2 output roots.
    """

    log_file_path = "logs/l2_proposer.log"
    print(f"Starting L2 proposer. Logging to {log_file_path}")
    log_file = open(log_file_path, "w")
    sys.stdout.flush()

    PROCESS_MGR.start(
        "starting L2 proposer",
        [
            "op-proposer",

            # Proposer-Specific Options
            # https://github.com/ethereum-optimism/optimism/blob/develop/op-proposer/flags/flags.go

            f"--l1-eth-rpc='{config.l1_rpc}'",
            f"--rollup-rpc='{config.l2_node_rpc}'",
            f"--poll-interval={config.proposer_poll_interval}s",
            f"--l2oo-address={deployment['L2OutputOracleProxy']}",
            *(["--allow-non-finalized"] if config.allow_non_finalized else []),

            # RPC Options
            # https://github.com/ethereum-optimism/optimism/blob/develop/op-service/rpc/cli.go

            f"--rpc.addr={config.proposer_rpc_listen_addr}",
            f"--rpc.port={config.proposer_rpc_listen_port}",

            # Tx Manager Options
            # https://github.com/ethereum-optimism/optimism/blob/develop/op-service/txmgr/cli.go

            f"--num-confirmations={config.proposer_num_confirmations}",
            *([f"--private-key={config.proposer_key}"] if config.proposer_key else [
                f"--mnemonic='{config.proposer_mnemonic}'",
                f"--hd-path=\"{config.proposer_hd_path}\""]),

            # Metrics Options
            # https://github.com/ethereum-optimism/optimism/blob/develop/op-service/metrics/cli.go

            *([] if not config.proposer_metrics else [
                "--metrics.enabled",
                f"--metrics.port={config.proposer_metrics_listen_port}",
                f"--metrics.addr={config.proposer_metrics_listen_addr}"])
        ],
        forward="fd", stdout=log_file, stderr=subprocess.STDOUT)


####################################################################################################

def start_l2_batcher(config: L2Config):
    """
    Starts the OP batcher, which submits transaction batches.
    """

    log_file_path = "logs/l2_batcher.log"
    print(f"Starting L2 batcher. Logging to {log_file_path}")
    log_file = open(log_file_path, "w")
    sys.stdout.flush()

    PROCESS_MGR.start(
        "starting L2 batcher",
        [
            "op-batcher",

            # Batcher-Specific Options
            # https://github.com/ethereum-optimism/optimism/blob/develop/op-batcher/flags/flags.go

            f"--l1-eth-rpc='{config.l1_rpc}'",
            f"--l2-eth-rpc='{config.l2_engine_rpc}'",
            f"--rollup-rpc='{config.l2_node_rpc}'",
            f"--poll-interval={config.batcher_poll_interval}s",
            f"--sub-safety-margin={config.sub_safety_margin}",
            f"--max-channel-duration={config.max_channel_duration}",

            # Tx Manager Options
            # https://github.com/ethereum-optimism/optimism/blob/develop/op-service/txmgr/cli.go

            f"--num-confirmations={config.batcher_num_confirmations}",
            *([f"--private-key={config.batcher_key}"] if config.batcher_key else [
                f"--mnemonic='{config.batcher_mnemonic}'",
                f"--hd-path=\"{config.batcher_hd_path}\""]),

            # Metrics Options
            # https://github.com/ethereum-optimism/optimism/blob/develop/op-service/metrics/cli.go

            *([] if not config.proposer_metrics else [
                "--metrics.enabled",
                f"--metrics.port={config.batcher_metrics_listen_port}",
                f"--metrics.addr={config.batcher_metrics_listen_addr}"]),

            # RPC Options
            # https://github.com/ethereum-optimism/optimism/blob/develop/op-batcher/rpc/config.go
            # https://github.com/ethereum-optimism/optimism/blob/develop/op-service/rpc/cli.go

            *([] if not config.batcher_enable_admin else ["--rpc.enable-admin"]),
            f"--rpc.addr={config.batcher_rpc_listen_addr}",
            f"--rpc.port={config.batcher_rpc_listen_port}"
        ],
        forward="fd", stdout=log_file, stderr=subprocess.STDOUT)


####################################################################################################

def start_l2_node(config: L2Config, paths: OPPaths, sequencer: bool = True):
    """
    Starts the OP node, which derives the L2 chain from the L1 chain & optionally creates new L2
    blocks, then waits for it to be reasy.
    """

    log_file_path = "logs/l2_node.log"
    print(f"Starting L2 node. Logging to {log_file_path}")
    log_file = open(log_file_path, "w")
    sys.stdout.flush()

    PROCESS_MGR.start(
        "starting L2 node",
        [
            "op-node",

            # Node-Specific Options
            # https://github.com/ethereum-optimism/optimism/blob/develop/op-node/flags/flags.go

            f"--l1={config.l1_rpc_for_node}",
            f"--l2={config.l2_engine_authrpc}",
            f"--l2.jwt-secret={config.jwt_secret_path}",
            f"--verifier.l1-confs={config.verifier_l1_confs}",
            f"--rollup.config={paths.rollup_config_path}",

            # Sequencer Options

            *([] if not sequencer else [
                "--sequencer.enabled",
                f"--sequencer.l1-confs={config.sequencer_l1_confs}",
            ]),

            # RPC Options
            # https://github.com/ethereum-optimism/optimism/blob/develop/op-service/rpc/cli.go

            f"--rpc.addr={config.node_rpc_listen_addr}",
            f"--rpc.port={config.node_rpc_listen_port}",

            # P2P Flags
            # https://github.com/ethereum-optimism/optimism/blob/develop/op-node/flags/p2p_flags.go

            *(["--p2p.disable"] if not config.p2p_enabled else [
                f"--p2p.listen.ip={config.p2p_listen_addr}",
                f"--p2p.listen.tcp={config.p2p_tcp_listen_port}",
                f"--p2p.listen.udp={config.p2p_udp_listen_port}",
                f"--p2p.priv.path={config.p2p_peer_key_path}",
                *([] if config.p2p_sequencer_key is None else [
                    f"--p2p.sequencer.key={config.p2p_sequencer_key}"
                ])
            ]),

            # Metrics Options
            # https://github.com/ethereum-optimism/optimism/blob/develop/op-service/metrics/cli.go

            *([] if not config.proposer_metrics else [
                "--metrics.enabled",
                f"--metrics.port={config.node_metrics_listen_port}",
                f"--metrics.addr={config.node_metrics_listen_addr}"]),
        ],
        forward="fd", stdout=log_file, stderr=subprocess.STDOUT)

    lib.wait_for_rpc_server("127.0.0.1", config.node_rpc_listen_port)

####################################################################################################
