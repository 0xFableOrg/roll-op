import subprocess
import sys

from config import L2Config
import libroll as lib
from processes import PROCESS_MGR


####################################################################################################

def start(config: L2Config, sequencer: bool = True):
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

            # TODO: This should work, but somehow using the WebSocket RPC here causes the *proposer*
            #       to fail to submit output roots because the L1 blockhash it supplies is
            #       incorrect. This setup works in the devnet though, so we messed something up
            #       somewhere.
            # f"--l1={config.l1_rpc_for_node}",
            f"--l1={config.l1_rpc}",
            f"--l2={config.l2_engine_authrpc}",
            f"--l2.jwt-secret={config.jwt_secret_path}",
            f"--verifier.l1-confs={config.verifier_l1_confs}",
            f"--rollup.config={config.paths.rollup_config_path}",

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
