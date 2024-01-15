"""
This module defines functions related to spinning a block explorer.
"""
import os
import shutil

import deps
from config import Config
from processes import PROCESS_MGR
import libroll as lib

####################################################################################################
# Constants

# URL of the Blockscout github repo
_GITHUB_URL = "https://github.com/blockscout/blockscout.git"

# Docker image tag for the latest tested Optimism-compatible "backend" component of blockscout
# https://hub.docker.com/r/blockscout/blockscout-optimism/tags
_DOCKER_TAG = "5.4.0-postrelease-63747320"

# Commit corresponding to the Docker image
_GIT_HASH = "6374732056677a557f2b9b1e0b94e92b299bfbed"

# https://ghcr.io/blockscout/frontend
# See here for frontend/backend compatibility:
#   https://docs.blockscout.com/for-developers/information-and-settings/requirements/back-front-compatibility-matrix
_FRONTEND_DOCKER_TAG = "v1.20.0"

# https://ghcr.io/blockscout/sig-provider
_SIG_PROVIDER_DOCKER_TAG = "v1.0.0"

# https://ghcr.io/blockscout/smart-contract-verifier
_SMART_CONTRACT_VERIFIER_DOCKER_TAG = "v1.6.0"

# https://ghcr.io/blockscout/stats
_STATS_DOCKER_TAG = "v1.5.0"

# https://ghcr.io/blockscout/visualizer
_VISUALIZER_DOCKER_TAG = "v0.2.0"

_COMPOSE_PROJECT_NAME = "blockscout"


####################################################################################################

def launch_blockscout(config: Config):
    """
    Launch the blockscout block explorer, setting up the repo if necessary.
    """
    deps.check_docker()
    setup_blockscout_repo()

    log_file = config.blockscout_log_file
    print(f"Launching the blockscout block explorer. Logging to {log_file}\n"
          "Explorer available at http://localhost:80 in a little bit.")

    http_url = config.l2_engine_rpc_http_url.replace("127.0.0.1", "host.docker.internal")
    ws_url = config.l2_engine_rpc_ws_url.replace("127.0.0.1", "host.docker.internal")

    def edit_docker_compose_config(dc_config: dict):
        dc_env = dc_config["services"]["backend"]["environment"]
        dc_env["ETHEREUM_JSONRPC_HTTP_URL"] = http_url
        dc_env["ETHEREUM_JSONRPC_TRACE_URL"] = http_url
        dc_env["ETHEREUM_JSONRPC_WS_URL"] = ws_url

    lib.edit_yaml_file(
        "blockscout/docker-compose/docker-compose.yml",
        edit_docker_compose_config)

    lib.replace_in_file("blockscout/docker-compose/envs/common-blockscout.env", {
        r"^ETHEREUM_JSONRPC_HTTP_URL=.*": f"ETHEREUM_JSONRPC_HTTP_URL={http_url}",
        r"^ETHEREUM_JSONRPC_TRACE_URL=.*": f"ETHEREUM_JSONRPC_TRACE_URL={http_url}",
        r"^ETHEREUM_JSONRPC_WS_URL=.*": f"ETHEREUM_JSONRPC_WS_URL={ws_url}",
        # because these lines are commented by default!
        r"^# ETHEREUM_JSONRPC_WS_URL=.*": f"ETHEREUM_JSONRPC_WS_URL={ws_url}",
        r"^# TRACE_FIRST_BLOCK=.*": "TRACE_FIRST_BLOCK=1",  # avoids "genesis is not traceable"
    }, regex=True)

    lib.replace_in_file("blockscout/docker-compose/envs/common-frontend.env", {
        r"^NEXT_PUBLIC_NETWORK_NAME=.*":
            f"NEXT_PUBLIC_NETWORK_NAME={config.chain_name}",
        r"^NEXT_PUBLIC_NETWORK_SHORT_NAME=.*":
            f"NEXT_PUBLIC_NETWORK_SHORT_NAME={config.chain_short_name}",
        r"^NEXT_PUBLIC_NETWORK_ID=.*":
            f"NEXT_PUBLIC_NETWORK_ID={config.l2_chain_id}"
    }, regex=True)

    env = {**os.environ,
           "COMPOSE_PROJECT_NAME": _COMPOSE_PROJECT_NAME,
           "NEXT_PUBLIC_NETWORK_NAME": config.chain_name,
           "NEXT_PUBLIC_NETWORK_ID": str(config.l2_chain_id),
           "DOCKER_REPO": "blockscout-optimism",
           "DOCKER_TAG": _DOCKER_TAG,
           "FRONTEND_DOCKER_TAG": _FRONTEND_DOCKER_TAG,
           "SIG_PROVIDER_DOCKER_TAG": _SIG_PROVIDER_DOCKER_TAG,
           "SMART_CONTRACT_VERIFIER_DOCKER_TAG": _SMART_CONTRACT_VERIFIER_DOCKER_TAG,
           "STATS_DOCKER_TAG": _STATS_DOCKER_TAG,
           "VISUALIZER_DOCKER_TAG": _VISUALIZER_DOCKER_TAG
           }

    if config.enable_governance:
        env["NEXT_PUBLIC_NETWORK_GOVERNANCE_TOKEN_SYMBOL"] = config.governance_token_symbol

    # This will keep running, and the explorer will be shut down when it is killed.
    PROCESS_MGR.start(
        "spin up block explorer",
        "docker compose -f geth.yml up",
        cwd="blockscout/docker-compose",
        file=log_file,
        env=env)


####################################################################################################

def setup_blockscout_repo():
    """
    Clones the Blockscout github repo and sets it up so that it will work with the
    Optimism-compatible
    docker images.
    """
    if os.path.isfile("blockscout"):
        raise Exception("Error: 'blockscout' exists as a file and not a directory.")
    elif not os.path.exists("blockscout"):
        print("Cloning the blockscout repository. This may take a while...")
        lib.clone_repo(_GITHUB_URL, "clone the blockscout repository")

    head_hash = lib.run(
        "get head commit",
        "git show-ref --hash HEAD",
        cwd="blockscout")

    if head_hash != _GIT_HASH:
        lib.run("discard changes in repo", "git reset --hard", cwd="blockscout")
        lib.run("fetch blockscout repo", "git fetch", cwd="blockscout")
        lib.run(
            "checkout blockscout version",
            f"git checkout --detach {_GIT_HASH}",
            cwd="blockscout")

        def edit_backend_config(backend_config: dict):
            backend_config["services"]["backend"]["platform"] = "linux/arm64"

        lib.edit_yaml_file("blockscout/docker-compose/docker-compose.yml", edit_backend_config)


####################################################################################################

def clean(config: Config):
    """
    Deletes the block explorer databases, logs, and containers.
    """

    dir_paths = [
        "blockscout/docker-compose/services/blockscout-db-data",
        "blockscout/docker-compose/services/logs",
        "blockscout/docker-compose/services/redis-data",
        "blockscout/docker-compose/services/stats-db-data",
    ]

    for path in dir_paths:
        lib.debug(f"Removing {path}")
        shutil.rmtree(path, ignore_errors=True)

    path = config.blockscout_log_file
    if os.path.exists(path):
        lib.debug(f"Removing {path}")
        os.remove(path)

    lib.run("remove blockscout containers",
            f"docker compose --project-name {_COMPOSE_PROJECT_NAME} rm --stop --force")


####################################################################################################
