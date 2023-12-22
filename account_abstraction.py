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

    # === install stackup bundler ===

    github_url = "github.com/stackup-wallet/stackup-bundler"
    version = "v0.6.21"

    log_file = f"{config.logs_dir}/install_bundler.log"
    print(f"Installing stackup bundler. Logging to {log_file}")

    env = {**os.environ, "GOBIN": os.path.abspath("bin")}

    lib.run_roll_log(
        "install stackup bundler",
        f"go install {github_url}@{version}",
        env=env,
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

    log_file = os.path.join(config.logs_dir, config.deploy_aa_log_file_name)
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

    log_file_path = f"{config.logs_dir}/stackup_bundler.log"
    log_file = open(log_file_path, "w")
    print(f"Starting the stackup bundler. Logging to {log_file_path}.")

    PROCESS_MGR.start(
        "start bundler",
        "stackup-bundler start --mode private",
        env=env,
        forward="fd",
        stdout=log_file)


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
           "PRIVATE_KEY": config.paymaster_key}

    # start paymaster signer service
    log_file_path = f"{config.logs_dir}/paymaster_signer.log"
    log_file = open(log_file_path, "w")
    print(f"Starting paymaster signer service. Logging to {log_file_path}")

    PROCESS_MGR.start(
        "start paymaster signer service",
        "pnpm run start",
        cwd="paymaster",
        env=env,
        forward="fd",
        stdout=log_file)


####################################################################################################

def clean(config: Config):
    """
    Deletes the account abstraction deployment outputs and build logs.
    """
    paths = [
        os.path.join(config.logs_dir, "build_aa_contracts.log"),
        os.path.join(config.logs_dir, "stackup_bundler.log"),
        os.path.join(config.logs_dir, "install_bundler.log"),
        os.path.join(config.logs_dir, "build_paymaster.log"),
        os.path.join(config.logs_dir, config.deploy_aa_log_file_name),
        os.path.join(config.logs_dir, "paymaster_signer.log")
    ]

    for path in paths:
        if os.path.exists(path):
            lib.debug(f"Removing {path}")
            os.remove(path)

    path = "account-abstraction/deployments/opstack"
    lib.debug(f"Removing {path}")
    shutil.rmtree(path, ignore_errors=True)


####################################################################################################
