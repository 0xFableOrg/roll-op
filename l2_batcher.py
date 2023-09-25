import subprocess
import sys

from config import Config
from processes import PROCESS_MGR

import libroll as lib


####################################################################################################

def start(config: Config):
    """
    Starts the OP batcher, which submits transaction batches.
    """

    lib.ensure_port_unoccupied(
        "L2 batcher", config.batcher_rpc_listen_addr, config.batcher_rpc_listen_port)

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
