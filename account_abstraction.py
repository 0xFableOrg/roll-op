#!/usr/bin/env python3

import os
import shutil

import libroll as lib
import deps
from processes import PROCESS_MGR
from config import Config


####################################################################################################

def is_setup():
    """
    Checks if the account abstraction setup has been run.
    """
    return os.path.isdir("account-abstraction") \
        and shutil.which("stackup-bundler") is not None

    # TODO check contracts have been built
    # TODO check paymaster dependencies have been built


# --------------------------------------------------------------------------------------------------

def setup(config: Config):
    """
    Sets up all components necessary to run the account abstraction setup (cloning directories,
    building & installing sfotware).
    """

    # === clone account-abstraction repo ===

    github_url = "https://github.com/0xFableOrg/account-abstraction.git"

    if os.path.isfile("account-abstraction"):
        raise Exception("Error: 'account-abstraction' exists as a file and not a directory.")
    elif not os.path.exists("account-abstraction"):
        print("Cloning the account-abstraction repository. This may take a while...")
        lib.clone_repo(github_url, "clone the account-abstraction repository")

    # === build account abstraction contracts ===

    deps.check_or_install_node()
    deps.check_or_install_yarn()

    log_file = f"{config.logs_dir}/build_aa_contracts.log"
    print(f"Building account abstraction contracts. Logging to {log_file}")

    lib.run_roll_log(
        "build account abstraction contracts",
        command=deps.cmd_with_node("yarn install"),
        cwd="account-abstraction",
        log_file=log_file)

    # === clone stackup-bundler repo ===

    github_url = "https://github.com/stackup-wallet/stackup-bundler.git"

    if os.path.isfile("stackup-bundler"):
        raise Exception("Error: 'stackup-bundler' exists as a file and not a directory.")
    elif not os.path.exists("stackup-bundler"):
        print("Cloning the stackup-bundler repository. This may take a while...")
        lib.clone_repo(github_url, "clone the stackup-bundler repository")

    # === install stackup bundler ===

    version = "v0.6.44"

    log_file = f"{config.logs_dir}/install_bundler.log"
    print(f"Installing stackup bundler. Logging to {log_file}")

    env = {**os.environ, "GOBIN": os.path.abspath("bin")}

    lib.run_roll_log(
        "install stackup bundler",
        f"git checkout {version} && go build -o ./tmp/stackup-bundler main.go",
        env=env,
        cwd="stackup-bundler",
        log_file=log_file)

    # === build paymaster dependencies ===

    log_file = f"{config.logs_dir}/build_paymaster.log"
    print(f"Building paymaster dependencies. {log_file}")
    lib.run_roll_log(
        "build paymaster dependencies",
        command=deps.cmd_with_node("pnpm install"),
        cwd="paymaster",
        log_file=log_file)


####################################################################################################

def deploy(config: Config):
    """
    Deploy the account abstraction contracts.
    """

    env = {**os.environ,
           "PRIVATE_KEY": config.aa_deployer_key,
           "PAYMASTER_PRIVATE_KEY": config.paymaster_key,
           "RPC_URL": config.l2_engine_rpc_url}

    log_file = str(os.path.join(config.logs_dir, config.deploy_aa_log_file_name))
    print(f"Deploying account abstraction contracts. Logging to {log_file}")

    lib.run_roll_log(
        "deploy contracts",
        command=deps.cmd_with_node("yarn deploy --network opstack"),
        cwd="account-abstraction",
        env=env,
        log_file=log_file)

    print("Account abstraction contracts successfully deployed.")

    # NOTE: Deployment state can be checked at "account-abstraction/deployments/opstack"


####################################################################################################

def start(config: Config):
    start_bundler(config)
    start_paymaster(config)


# --------------------------------------------------------------------------------------------------

def start_bundler(config: Config):
    """
    Start the stackup bundler.
    """

    bundler_key = config.bundler_key
    if bundler_key.startswith("0x"):
        bundler_key = bundler_key[2:]

    env = {**os.environ,
           "ERC4337_BUNDLER_ETH_CLIENT_URL": config.l2_engine_rpc_url,
           "ERC4337_BUNDLER_PRIVATE_KEY": bundler_key}

    log_file = config.stackup_bundler_log_file
    print(f"Starting the stackup bundler. Logging to {log_file}.")

    def on_exit():
        print(f"AA bundler exited. Check {log_file} for details.\n"
              "You can re-run with `./rollop aa` in another terminal\n"
              "(!! Make sure to specify the same config file and flags!)")

    PROCESS_MGR.start(
        "start bundler",
        "stackup-bundler start --mode private",
        env=env,
        file=log_file,
        on_exit=on_exit)


# --------------------------------------------------------------------------------------------------


def start_paymaster(config: Config):
    """
    Starts the paymaster signer service.
    """

    entrypoint_address = lib.read_json_file(
        "account-abstraction/deployments/opstack/EntryPoint.json"
    )["address"]

    simple_account_factory_address = lib.read_json_file(
        "account-abstraction/deployments/opstack/SimpleAccountFactory.json"
    )["address"]

    paymaster_address = lib.run(
        "parsing paymaster address",
        f"grep '==VerifyingPaymaster addr=' {config.logs_dir}/{config.deploy_aa_log_file_name}"
    ).strip().split(' ')[-1]

    env = {**os.environ,
           "RPC_URL": config.l2_engine_rpc_url,
           "PAYMASTER_RPC_URL": "http://localhost:3000",
           "ENTRYPOINT_ADDRESS": entrypoint_address,
           "SIMPLE_ACCOUNT_FACTORY_ADDRESS": simple_account_factory_address,
           "PAYMASTER_ADDRESS": paymaster_address,
           "TIME_VALIDITY": str(config.paymaster_validity),
           "INITIAL_DEPOSIT": str(config.paymaster_initial_deposit),
           "PRIVATE_KEY": config.paymaster_key}

    lib.run(
        "deposit initial funds for paymaster",
        command=deps.cmd_with_node("pnpm run deposit"),
        cwd="paymaster",
        env=env)

    # start paymaster signer service
    log_file = config.paymaster_log_file
    print(f"Starting paymaster signer service. Logging to {log_file}")

    def on_exit():
        print(f"AA paymaster exited. Check {log_file} for details.\n"
              "You can re-run with `./rollop aa` in another terminal\n"
              "(!! Make sure to specify the same config file and flags!)")

    PROCESS_MGR.start(
        "start paymaster signer service",
        "pnpm run start",
        cwd="paymaster",
        env=env,
        file=log_file,
        on_exit=on_exit)


####################################################################################################

def clean(config: Config):
    """
    Deletes the account abstraction deployment outputs and build logs.
    """
    lib.remove_paths(config, [
        os.path.join(config.logs_dir, "build_aa_contracts.log"),
        os.path.join(config.logs_dir, "install_bundler.log"),
        os.path.join(config.logs_dir, "build_paymaster.log"),
        os.path.join(config.logs_dir, config.deploy_aa_log_file_name),
        config.stackup_bundler_log_file,
        config.paymaster_log_file,
        # dirs
        "account-abstraction/deployments/opstack",
    ])


####################################################################################################
