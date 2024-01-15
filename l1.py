"""
This module defines functions related to spinning a devnet L1 node, and deploying L1 contracts
on an L1 blockchain (for now only devnet, but in the future, any kind of L1).
"""

import json
import os
from subprocess import Popen

import l2_deploy
import libroll as lib
import state
from config import Config
import deploy_config
from processes import PROCESS_MGR


####################################################################################################

def deploy_devnet_l1(config: Config):
    """
    Starts a devnet L1 node, generating the L1 genesis file if necessary.
    """
    os.makedirs(config.artifacts_dir, exist_ok=True)
    _generate_devnet_l1_genesis(config)
    _start_devnet_l1_node(config)
    print("Devnet L1 deployment is complete! L1 node is running.")


####################################################################################################

def _generate_devnet_l1_genesis(config: Config):
    """
    Generates the L1 genesis file. The genesis file will include the L2 pre-deployed contracts, so
    it's not necessary to redeploy them to the devnet L1 later.
    """
    if os.path.exists(config.l1_genesis_path):
        print("L1 genesis already generated.")
        return

    print("Generating L1 genesis.")

    deploy_config.generate_deploy_config(config, pre_l1_genesis=True)

    if os.path.exists(config.l1_allocs_path):
        # This shouldn't happen in normal operation, but be safe.
        os.remove(config.l1_allocs_path)

    _create_devnet_l1_genesis_allocs(config)

    lib.run(
        "generate l1 genesis", [
            "go run cmd/main.go genesis l1",
            f"--deploy-config {config.deploy_config_path}",
            f"--l1-allocs {config.l1_allocs_path}",
            f"--l1-deployments {config.addresses_path}",
            f"--outfile.l1 {config.l1_genesis_path}"
        ],
        cwd=config.op_node_dir)


####################################################################################################

def _create_devnet_l1_genesis_allocs(config: Config):
    """
    Create the "allocs" for the L1 genesis, i.e. the pre-existing state, in this case the
    pre-deployed L2 contracts, as well as a file containing the addresses of the L2 contracts.
    """

    geth = _start_temporary_geth_node(config)
    try:
        l2_deploy.deploy_contracts_on_l1(config, tmp_l1=True)

        # dump latest block to get the allocs
        host = f"127.0.0.1:{config.temp_l1_rpc_listen_port}"
        print(f"Fetch debug_dumpBlock from {host}")
        res = lib.send_json_rpc_request(host, 3, "debug_dumpBlock", ["latest"])
        response = json.loads(res)
        allocs = response['result']
        lib.write_json_file(config.l1_allocs_path, allocs)
    finally:
        PROCESS_MGR.kill(geth, ensure=True)


####################################################################################################

def _start_temporary_geth_node(config: Config) -> Popen:
    """
    Spin a temporary geth node, which will used to deploy the L2 contracts then dump them
    so they can be included in the devnet L1 genesis file.
    """

    lib.ensure_port_unoccupied("temporary geth", "127.0.0.1", config.temp_l1_rpc_listen_port)

    log_file = f"{config.logs_dir}/temp_geth.log"
    print(f"Starting temporary geth node. Logging to {log_file}")

    def early_exit_handler():
        print(f"Temporary geth node exited early. Check {log_file} for details.")
        # noinspection PyUnresolvedReferences,PyProtectedMember
        os._exit(1)  # we have to use this one to exit from a thread

    popen = PROCESS_MGR.start(
        "run temporary geth instance", [
            "geth",
            "--dev",
            "--http",
            "--http.api eth,debug",
            f"--http.port={config.temp_l1_rpc_listen_port}",
            "--verbosity 4",
            "--gcmode archive",
            "--dev.gaslimit 30000000",
            # Mine a block every second — without this the L2 contracts deployment can hang because
            # the basefees climbed too high and geth doesn't mine any blocks so it never goes down.
            "--dev.period 1",
            "--rpc.allow-unprotected-txs"
        ],
        file=log_file,
        on_exit=early_exit_handler)

    lib.wait_for_rpc_server("127.0.0.1", config.temp_l1_rpc_listen_port)

    return popen


####################################################################################################

def _start_devnet_l1_node(config: Config):
    """
    Spin the devnet L1 node, then wait for it to be ready.
    """

    lib.ensure_port_unoccupied(
        "L1 node", config.l1_rpc_listen_addr, config.l1_rpc_listen_port)

    # Create geth db if it doesn't exist.
    os.makedirs(config.l1_data_dir, exist_ok=True)

    if not os.path.exists(config.l1_keystore_dir):
        # Initial account setup
        print(f"Directory '{config.l1_keystore_dir}' missing, running account import.")
        with open(config.l1_password_path, "w") as f:
            f.write(config.l1_password)
        with open(config.l1_tmp_signer_key_path, "w") as f:
            f.write(config.l1_signer_private_key.replace("0x", ""))
        lib.run("importing signing keys", [
            "geth account import",
            f"--datadir={config.l1_data_dir}",
            f"--password={config.l1_password_path}",
            config.l1_tmp_signer_key_path
        ])
        os.remove(f"{config.l1_data_dir}/block-signer-key")

    if not os.path.exists(config.l1_chaindata_dir):
        log_file = f"{config.logs_dir}/init_l1_genesis.log"
        print(f"Directory {config.l1_chaindata_dir} missing, importing genesis in L1 node.\n"
              f"Logging to {log_file}")
        lib.run(
            "initializing genesis", [
                "geth",
                f"--verbosity={config.l1_verbosity}",
                "init",
                f"--datadir={config.l1_data_dir}",
                config.l1_genesis_path
            ],
            file=log_file)

    log_file = config.l1_node_log_file
    print(f"Starting L1 node. Logging to {log_file}")

    # NOTE: The devnet L1 node must be an archive node, otherwise pruning happens within minutes of
    # starting the node. This could be an issue if the op-node is brought down or restarted later,
    # or if the sequencing window is larger than the time-to-prune.

    command = [
        "geth",

        f"--datadir={config.l1_data_dir}",
        f"--verbosity={config.l1_verbosity}",

        f"--networkid={config.l1_chain_id}",
        "--syncmode=full",  # doesn't matter, it's only us
        "--gcmode=archive",
        "--rpc.allow-unprotected-txs",  # allow legacy transactions for deterministic deployment

        # p2p network config
        f"--port={config.l1_p2p_port}",

        # No peers: the blockchain is only this node
        "--nodiscover",
        "--maxpeers=1",

        # HTTP JSON-RPC server config
        "--http",
        "--http.corsdomain=*",
        "--http.vhosts=*",
        f"--http.addr={config.l1_rpc_listen_addr}",
        f"--http.port={config.l1_rpc_listen_port}",
        "--http.api=web3,debug,eth,txpool,net,engine",

        # WebSocket JSON-RPC server config
        "--ws",
        f"--ws.addr={config.l1_rpc_ws_listen_addr}",
        f"--ws.port={config.l1_rpc_ws_listen_port}",
        "--ws.origins=*",
        "--ws.api=debug,eth,txpool,net,engine",

        # Configuration for clique signing, clique itself is enabled via the genesis file
        f"--unlock={config.l1_signer_account}",
        "--mine",
        f"--miner.etherbase={config.l1_signer_account}",
        f"--password={config.l1_password_path}",
        "--allow-insecure-unlock",

        # Authenticated RPC config
        f"--authrpc.addr={config.l1_authrpc_listen_addr}",
        f"--authrpc.port={config.l1_authrpc_listen_port}",
        # NOTE: The Optimism monorepo accepts connections from any host, and specifies the JWT
        # secret to be the same used on L2. We don't see any reason to do that (we never use
        # authenticated RPC), so we restrict access to localhost only (authrpc can't be turned
        # off), and don't specify the JWT secret (`--authrpc.jwtsecret=jwt_secret_path`) which
        # causes a random secret to be created in `config.l1_data_dir/geth/jwtsecret`.
        "--authrpc.vhosts=127.0.0.1",

        # Metrics options
        *([] if not config.l1_metrics else [
            "--metrics",
            f"--metrics.port={config.l1_metrics_listen_port}",
            f"--metrics.addr={config.l1_metrics_listen_addr}"]),
    ]

    with open(os.path.join(config.logs_dir, "l1_command.log"), "w") as f:
        f.write("\n".join(command))

    def on_exit():
        print(f"L1 node exited. Check {log_file} for details.\n"
              "You can re-run with `./rollop l1` in another terminal\n"
              "(!! Make sure to specify the same config file and flags!)")

    PROCESS_MGR.start(
        "running geth",
        command,
        file=log_file,
        on_exit=on_exit)

    lib.wait_for_rpc_server("127.0.0.1", config.l1_rpc_listen_port)


####################################################################################################

def clean(config: Config):
    """
    Cleans up L1 deployment outputs.
    """
    lib.remove_paths(config, [
        config.l1_node_log_file,
        os.path.join(config.logs_dir, "temp_geth.log"),
        config.l1_genesis_path,
        config.l1_allocs_path,
        config.op_deploy_config_path,
        # dirs
        config.l1_data_dir,
        config.op_deployment_artifacts_dir,
    ])

    if config.l1_contracts_in_genesis and state.args.command != "clean":
        # When the comman is "clean", we do remove those files anyway.
        print(
            "The rollup contracts were baked into the L1 genesis.\n"
            "You may want to run the `clean-l2` roll-op command to remove the deployment outputs.\n"
            "These are not removed by default, as they could have been overriden "
            "by a later deployment.")


####################################################################################################
