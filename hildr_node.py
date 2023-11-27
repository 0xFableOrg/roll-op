import sys
import os

from config import Config
from processes import PROCESS_MGR

import libroll as lib


####################################################################################################

def start(config: Config):
    """
    Starts the OP hildr node, which derives the L2 chain from the L1 chain & optionally creates new L2
    blocks, then waits for it to be reasy.
    """

    lib.ensure_port_unoccupied(
        "L2 hidlr node", config.l2_hildr_node_rpc_listen_addr, config.l2_hildr_node_rpc_listen_port)

    log_file_path = "logs/l2_hildr_node.log"
    print(f"Starting Hildr L2 node. Logging to {log_file_path}")
    log_file = open(log_file_path, "w")
    sys.stdout.flush()

    PROCESS_MGR.start(
        "Starting L2 hildr node",
        [
            # Hildr-node options
            # https://github.com/optimism-java/hildr/blob/main/hildr-node/src/main/java/io/optimism/cli/Cli.java
            "java",
            f"--enable-preview",
            f"-cp bin/hildr-node.jar",
            "io.optimism.Hildr",
            f"--network {config.paths.rollup_config_path}",
            f"--jwt-file {os.path.join('..', config.jwt_secret_path)}",
            f"--l1-rpc-url {config.l1_rpc}",
            f"--l1-ws-rpc-url {config.l1_rpc_for_node}",
            f"--l2-rpc-url {config.l2_hildr_engine_rpc}",
            f"--l2-engine-url {config.l2_hildr_engine_authrpc}",
            f"--rpc-port {config.l2_hildr_node_rpc_listen_port}",
            f"--sync-mode full",
            f"--devnet",
            *([] if not config.l2_hildr_node_metrics else [
                "--metrics-enabled",
                f"--metrics-port={config.l2_hildr_node_metrics_listen_port}"]),
        ],
        forward="fd", stdout=log_file)

####################################################################################################