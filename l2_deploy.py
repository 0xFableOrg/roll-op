import json
import os
import shutil

import deploy_config
from config import Config

import libroll as lib


####################################################################################################

def deploy(config: Config):
    """
    Deploy the rollup by deploying the contracts to L1 then generating the L2 genesis file, but does
    not start the software components.
    """
    os.makedirs(config.paths.gen_dir, exist_ok=True)

    if not os.path.exists(config.deploy_config_path):
        deploy_config.generate_deploy_config(config)

    if not config.deploy_devnet_l1 or not os.path.exists(config.paths.l1_genesis_path):
        # Deploy contracts, but not on the devnet L1 which has them in the genesis state.
        deploy_contracts_on_l1(config)

    _generate_l2_genesis(config)
    config.deployments = lib.read_json_file(config.paths.addresses_json_path)

    if config.deployments.get("L2OutputOracleProxy") is None:
        raise Exception(
            "L2OutputOracleProxy address not found in addresses.json. "
            "Try redeploying the L1 contracts.")


####################################################################################################

def deploy_contracts_on_l1(config: Config, tmp_l1=False):
    """
    Deploy the L2 contracts to an L1. If `tmp_l1` is true, indicates we're deploying to a temporary
    node with the goal of dumping the contracts for inclusion in devnet L1 genesis.
    """

    if not tmp_l1 and os.path.exists(config.paths.addresses_json_path):
        print("L1 contracts already deployed.")
        return

    if tmp_l1:
        l1_address = "127.0.0.1"
        l1_rpc_port = config.temp_l1_rpc_listen_port
        l1_rpc_url = f"http://{l1_address}:{l1_rpc_port}"
    else:
        l1_address = config.l1_rpc_host
        l1_rpc_port = config.l1_rpc_port
        l1_rpc_url = config.l1_rpc_url

    # wait for l1
    lib.wait_for_port(l1_address, l1_rpc_port)
    lib.wait_for_rpc_server(l1_address, l1_rpc_port)

    if tmp_l1:
        # The temporary allow does not fund dev addresses, instead it has "owned" accounts that
        # are randomly generated. We need to use those.
        url = f"{l1_address}:{l1_rpc_port}"  # can't have "http:// in here
        print(f"Fetch eth_accounts from {url}")
        res = lib.send_json_rpc_request(url, 2, "eth_accounts", [])
        response = json.loads(res)
        deployer_account = response["result"][0]
        private_key_arg = ""
    else:
        deployer_account = config.contract_deployer_account
        private_key_arg = f"--private-key {config.contract_deployer_key}"

    if tmp_l1 or config.deploy_create2_deployer:
        lib.run("send some ether to the create2 deployer account", [
            "cast send",
            f"--from {deployer_account}",
            private_key_arg,
            f"--rpc-url {l1_rpc_url}",
            "--unlocked",
            "--value 1ether",
            "0x3fAB184622Dc19b6109349B94811493BF2a45362"  # create2 deployer account
        ], cwd=config.paths.contracts_dir)

        create2_deployer_deploy_tx \
            = "0xf8a58085174876e800830186a08080b853604580600e600039806000f350fe7" \
            + "fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" \
            + "e03601600081602082378035828234f58015156039578182fd5b8082525050506014600cf31ba0" \
            + "2222222222222222222222222222222222222222222222222222222222222222" \
            + "a02222222222222222222222222222222222222222222222222222222222222222"

        lib.run("deploy the create2 deployer", [
            "cast publish",
            f"--rpc-url {l1_rpc_url}",
            create2_deployer_deploy_tx
        ], cwd=config.paths.contracts_dir)

    deploy_script = "scripts/Deploy.s.sol:Deploy"

    log_file = "logs/deploy_l1_contracts.log"
    print(f"Deploying contracts to L1 with {deployer_account}. Logging to {log_file}")

    env = {**os.environ,
           "DEPLOYMENT_CONTEXT": config.deployment_name,
           "ETH_RPC_URL": l1_rpc_url}

    slow_arg = "--slow" if config.deploy_slowly else ""

    lib.run_roll_log("deploy the L2 contracts on L1", [
            f"forge script",
            deploy_script,
            "--sender", deployer_account,
            private_key_arg,
            f"--gas-estimate-multiplier {config.l1_deployment_gas_multiplier} "
            f"--rpc-url {l1_rpc_url}",
            "--broadcast",
            slow_arg,
            "--unlocked"
        ],
        cwd=config.paths.contracts_dir,
        env=env,
        log_file=log_file)

    shutil.copy(os.path.join(config.deployments_dir, ".deploy"), config.paths.addresses_json_path)

    log_file = "logs/create_l1_artifacts.log"
    print(f"Creating L1 deployment artifacts. Logging to {log_file}")
    lib.run_roll_log("create L1 deployment artifacts", [
            "forge script",
            deploy_script,
            "--sig 'sync()'",
            f"--rpc-url {l1_rpc_url}",
        ],
        cwd=config.paths.contracts_dir,
        env=env,
        log_file=log_file)


####################################################################################################

def _generate_l2_genesis(config: Config):
    """
    Generate the L2 genesis file and rollup configs.
    """
    if os.path.exists(config.paths.l2_genesis_path):
        print("L2 genesis and rollup configs already generated.")
    else:
        print("Generating L2 genesis and rollup configs.")
        try:
            lib.run("generate L2 genesis and rollup configs", [
                "go run cmd/main.go genesis l2",
                f"--l1-rpc={config.l1_rpc_url}",
                f"--deploy-config={config.deploy_config_path}",
                f"--deployment-dir={config.deployments_dir}",
                f"--outfile.l2={config.paths.l2_genesis_path}",
                f"--outfile.rollup={config.paths.rollup_config_path}"],
                cwd=config.paths.op_node_dir)
        except Exception as err:
            raise lib.extend_exception(
                err, prefix="Failed to generate L2 genesis and rollup configs: ") from None


####################################################################################################
