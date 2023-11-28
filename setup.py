"""
Exposes function to set up the project, in particular clone the Optimism monorepo and build it.
"""

import os
import shutil
import sys

import deps
import libroll as lib
import platform

from config import Config


####################################################################################################

def setup(config: Config):
    deps.check_or_install_go()
    deps.go_path_setup()
    deps.check_or_install_jq()
    deps.check_or_install_node()
    deps.check_or_install_yarn()
    deps.check_or_install_foundry()
    setup_optimism_repo()
    setup_op_geth_repo()
    setup_blockscout_repo()

    os.makedirs(config.paths.gen_dir, exist_ok=True)


####################################################################################################

def setup_optimism_repo():
    github_url = "https://github.com/ethereum-optimism/optimism.git"

    git_tag = "op-node/v1.3.0"
    git_fix1_tag = "2e57472890f9fea39cde72537935393b068d3e0f"
    git_fix2_tag = "5252c82f607af81f6cb741a370425eaf26280892"

    if os.path.isfile("optimism"):
        raise Exception("Error: 'optimism' exists as a file and not a directory.")
    elif not os.path.exists("optimism"):
        print("Cloning the optimism repository. This may take a while...")
        lib.clone_repo(github_url, "clone the optimism repository")

    lib.run("checkout stable version", f"git checkout --detach {git_tag}",
            cwd="optimism")

    lib.run("install devnet fix", f"git cherry-pick {git_fix1_tag}", cwd="optimism")
    lib.run("install submodules fix", f"git cherry-pick {git_fix2_tag}", cwd="optimism")

    log_file = "logs/build_optimism.log"
    print(
        f"Starting to build the optimism repository. Logging to {log_file}\n"
        "This may take a while...")

    lib.run_roll_log(
        descr="build optimism",
        command=deps.cmd_with_node("make build"),
        cwd="optimism",
        log_file=log_file)

    shutil.copyfile("optimism/op-proposer/bin/op-proposer", "bin/op-proposer")
    lib.chmodx("bin/op-proposer")

    shutil.copyfile("optimism/op-batcher/bin/op-batcher", "bin/op-batcher")
    lib.chmodx("bin/op-batcher")

    shutil.copyfile("optimism/op-node/bin/op-node", "bin/op-node")
    lib.chmodx("bin/op-node")

    print("Building the Cannon pre-state")
    lib.run("building the Cannon pre-state", "make cannon-prestate", cwd="optimism")

    print("Successfully built the optimism repository.")


####################################################################################################

def setup_op_geth_repo():
    """
    Clone the op-geth repository and build it.
    """
    github_url = "https://github.com/ethereum-optimism/op-geth.git"
    git_tag = "v1.101106.0"

    if os.path.isfile("op-geth"):
        raise Exception("Error: 'op-geth' exists as a file and not a directory.")
    elif not os.path.exists("op-geth"):
        print("Cloning the op-geth repository. This may take a while...")
        lib.clone_repo(github_url, "clone the op-geth repository")

    lib.run("checkout stable version", f"git checkout --detach {git_tag}",
            cwd="op-geth")

    print("Starting to build the op-geth repository. Logging to logs/build_op_geth.log\n"
          "This may take a while...")

    lib.run_roll_log(
        descr="build op-geth",
        command=deps.cmd_with_node("make geth"),
        cwd="op-geth",
        log_file="logs/build_op_geth.log")

    shutil.copyfile("op-geth/build/bin/geth", "bin/op-geth")
    lib.chmodx("bin/op-geth")

    print("Successfully built the op-geth repository.")


####################################################################################################

def setup_blockscout_repo():
    github_url = "https://github.com/blockscout/blockscout.git"
    git_tag = "49eee16ee1078a975a060b1564e6ea5b1ad70f39"

    if os.path.isfile("blockscout"):
        raise Exception("Error: 'blockscout' exists as a file and not a directory.")
    elif not os.path.exists("blockscout"):
        print("Cloning the blockscout repository. This may take a while...")
        lib.clone_repo(github_url, "clone the blockscout repository")

        lib.run("checkout stable version", f"git checkout --detach {git_tag}",
                cwd="blockscout")

        # TODO make this not replace multiple times if run multiple times
        if sys.platform == "darwin" and platform.processor() == "arm":
            anchor_line = "image: blockscout/blockscout:${DOCKER_TAG:-latest}"
            lib.replace_in_file(
                "blockscout/docker-compose/docker-compose-no-build-hardhat-network.yml",
                {anchor_line: f"{anchor_line}\nplatform: linux/arm64"})


####################################################################################################

def clean_build():
    """
    Clean the build outputs (from the Optimism monorepo and the op-geth repo).
    """
    lib.run(
        descr="clean optimism repo",
        # This encompases `make clean` and `make clean-node-modules` and avoids erroring on `make
        # nuke` because Docker is not running.
        command="git clean -Xdf",
        cwd="optimism",
        forward="self")

    lib.run(
        descr="clean op-geth repo",
        command="make clean",
        cwd="op-geth",
        forward="self")

    # NOTE: Need to cleanup blockscout when properly integrated.


####################################################################################################
