import sys

from config import Config
from processes import PROCESS_MGR

import libroll as lib


####################################################################################################

def start(config: Config):
    """
    Starts the OP proposer, which proposes L2 output roots.
    """

    if config.deployments is None:
        raise Exception("Deployments not set!")

    lib.ensure_port_unoccupied(
        "L2 proposer", config.proposer_rpc_listen_addr, config.proposer_rpc_listen_port)

    log_file_path = f"{config.logs_dir}/l2_proposer.log"
    print(f"Starting L2 proposer. Logging to {log_file_path}")
    log_file = open(log_file_path, "w")

    command = [
        "op-proposer",

        # Proposer-Specific Options
        # https://github.com/ethereum-optimism/optimism/blob/develop/op-proposer/flags/flags.go

        # TODO check on deployment not being None

        f"--l1-eth-rpc='{config.l1_rpc_url}'",
        f"--rollup-rpc='{config.l2_node_rpc_url}'",
        f"--poll-interval={config.proposer_poll_interval}s",
        f"--l2oo-address={config.deployments['L2OutputOracleProxy']}",
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
    ]

    config.log_run_config("\n".join(command))

    PROCESS_MGR.start(
        "starting L2 proposer",
        command,
        forward="fd",
        stdout=log_file)


####################################################################################################
