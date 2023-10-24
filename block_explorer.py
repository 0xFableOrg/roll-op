"""
This module defines functions related to spinning a block explorer.
"""

import shutil
import subprocess

from processes import PROCESS_MGR


####################################################################################################

def launch_blockscout():
    """
    Launch the blockscout block explorer.
    """
    # Remove old volumes
    shutil.rmtree(
        "blockscout/docker-compose/services/blockscout-db-data", ignore_errors=True)
    shutil.rmtree(
        "blockscout/docker-compose/services/redis-data", ignore_errors=True)

    log_file_name = "logs/launch_blockscout.log"
    log_file = open(log_file_name, "w")
    print(f"Launching the blockscout block explorer. Logging to {log_file_name}\n"
          "Explorer available at localhost:4000 in a little bit.")

    PROCESS_MGR.start(
        "spin up block explorer",
        "DOCKER_TAG=5.1.0 FRONTEND_DOCKER_TAG=v1.15.0 docker compose -f "
        "docker-compose-no-build-geth.yml up",
        cwd="blockscout/docker-compose",
        forward="fd", stdout=log_file, stderr=subprocess.STDOUT)


####################################################################################################

def clean():
    pass  # TODO

####################################################################################################
