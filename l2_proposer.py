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
        "L2 proposer",
        config.l2_proposer_rpc_listen_addr,
        config.l2_proposer_rpc_listen_port)

    log_file = config.l2_proposer_log_file
    print(f"Starting L2 proposer. Logging to {log_file}")

    command = [
        "op-proposer",

        # Proposer-Specific Options
        # https://github.com/ethereum-optimism/optimism/blob/develop/op-proposer/flags/flags.go

        # TODO check on deployment not being None

        f"--l1-eth-rpc='{config.l1_rpc_url}'",
        f"--rollup-rpc='{config.l2_node_rpc_url}'",
        f"--poll-interval={config.l2_proposer_poll_interval}s",
        f"--l2oo-address={config.deployments['L2OutputOracleProxy']}",
        *(["--allow-non-finalized"] if config.l2_proposer_allow_non_finalized else []),

        # RPC Options
        # https://github.com/ethereum-optimism/optimism/blob/develop/op-service/rpc/cli.go

        f"--rpc.addr={config.l2_proposer_rpc_listen_addr}",
        f"--rpc.port={config.l2_proposer_rpc_listen_port}",

        # Tx Manager Options
        # https://github.com/ethereum-optimism/optimism/blob/develop/op-service/txmgr/cli.go

        f"--num-confirmations={config.l2_proposer_num_confirmations}",
        *([f"--private-key={config.proposer_key}"] if config.proposer_key else [
            f"--mnemonic='{config.proposer_mnemonic}'",
            f"--hd-path=\"{config.proposer_hd_path}\""]),

        # Metrics Options
        # https://github.com/ethereum-optimism/optimism/blob/develop/op-service/metrics/cli.go

        *([] if not config.l2_proposer_metrics else [
            "--metrics.enabled",
            f"--metrics.port={config.l2_proposer_metrics_listen_port}",
            f"--metrics.addr={config.l2_proposer_metrics_listen_addr}"])
    ]

    config.log_l2_command("\n".join(command))

    def on_exit():
        print(f"L2 proposer exited. Check {log_file} for details.\n"
              "You can re-run with `./rollop l2-proposer` in another terminal\n"
              "(!! Make sure to specify the same config file and flags!)")

    PROCESS_MGR.start(
        "starting L2 proposer",
        command,
        file=log_file,
        on_exit=on_exit)


####################################################################################################
