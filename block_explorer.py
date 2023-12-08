"""
This module defines functions related to spinning a block explorer.
"""
import os
import shutil
import subprocess

import deps
from config import Config
from processes import PROCESS_MGR
import libroll as lib

####################################################################################################
# Constants

# URL of the Blockscout github repo
_GITHUB_URL = "https://github.com/blockscout/blockscout.git"

# Docker image tag for the latest tested Optimism-compatible "backend" component of blockscout
_DOCKER_TAG = "5.3.3-postrelease-d53f5a75"

# Commit corresponding to the Docker image
_GIT_HASH = "d53f5a7575a6af892bad69d80e8e23a5e54e8eea"

# Project name for docker compose
_COMPOSE_PROJECT_NAME = "blockscout"


####################################################################################################

def launch_blockscout(config: Config):
    """
    Launch the blockscout block explorer, setting up the repo if necessary.
    """
    setup_blockscout_repo()

    log_file_name = "logs/launch_blockscout.log"
    log_file = open(log_file_name, "w")
    print(f"Launching the blockscout block explorer. Logging to {log_file_name}\n"
          "Explorer available at http://localhost/ in a little bit.")

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

    lib.replace_in_file("blockscout/docker-compose/envs/common-blockscout.env",{
        r"^ETHEREUM_JSONRPC_HTTP_URL=.*": f"ETHEREUM_JSONRPC_HTTP_URL={http_url}",
        r"^ETHEREUM_JSONRPC_TRACE_URL=.*": f"ETHEREUM_JSONRPC_TRACE_URL={http_url}",
        r"^ETHEREUM_JSONRPC_WS_URL=.*": f"ETHEREUM_JSONRPC_WS_URL={ws_url}",
        # because this line is commented by default!
        r"^# ETHEREUM_JSONRPC_WS_URL=.*": f"ETHEREUM_JSONRPC_WS_URL={ws_url}",
    }, regex=True)

    env = {**os.environ,
           "COMPOSE_PROJECT_NAME": _COMPOSE_PROJECT_NAME,
           "DOCKER_REPO": "blockscout-optimism",
           "DOCKER_TAG": _DOCKER_TAG,
           # https://hub.docker.com/r/blockscout/blockscout-optimism/tags
           "FRONTEND_DOCKER_TAG": "v1.19.0",
           # ghcr.io/blockscout/frontend
           "SIG_PROVIDER_DOCKER_TAG": "v1.0.0",
           # ghcr.io/blockscout/sig-provider
           "SMART_CONTRACT_VERIFIER_DOCKER_TAG": "v1.6.0",
           # ghcr.io/blockscout/smart-contract-verifier
           "STATS_DOCKER_TAG": "v1.5.0",
           #  ghcr.io/blockscout/stats
           "VISUALIZER_DOCKER_TAG": "v0.2.0"
           # ghcr.io/blockscout/visualizer
           }

    # This will keep running, and the explorer will be shut down when it is killed.
    PROCESS_MGR.start(
        "spin up block explorer",
        "docker compose -f geth.yml up",
        cwd="blockscout/docker-compose",
        forward="fd", stdout=log_file, stderr=subprocess.STDOUT, env=env)


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
        lib.run(
            "checkout blockscout version",
            f"git checkout --detach {_GIT_HASH}",
            cwd="blockscout")

        def edit_backend_config(backend_config: dict):
            backend_config["services"]["backend"]["platform"] = "linux/arm64"

        lib.edit_yaml_file("blockscout/docker-compose/docker-compose.yml", edit_backend_config)


####################################################################################################

def clean():
    """
    Deletes the block explorer databases, logs, and containers.
    """
    print("Cleaning up block explorer databases, logs, and containers...")
    shutil.rmtree(
        "blockscout/docker-compose/services/blockscout-db-data", ignore_errors=True)
    shutil.rmtree(
        "blockscout/docker-compose/services/logs", ignore_errors=True)
    shutil.rmtree(
        "blockscout/docker-compose/services/redis-data", ignore_errors=True)
    shutil.rmtree(
        "blockscout/docker-compose/services/stats-db-data", ignore_errors=True)

    lib.run("remove blockscout containers",
            f"docker compose --project-name {_COMPOSE_PROJECT_NAME} rm --stop --force")


####################################################################################################
