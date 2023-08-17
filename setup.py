"""
Exposes function to set up the project, in particular clone the Optimism monorepo and build it.
"""

import os

import deps
import libroll as lib


####################################################################################################

def setup():
    deps.check_go()
    deps.check_or_install_jq()
    deps.check_or_install_node()
    deps.check_or_install_yarn()
    deps.check_or_install_foundry()
    setup_optimism_repo()


####################################################################################################

def setup_optimism_repo():
    github_url = "https://github.com/ethereum-optimism/optimism.git"
    # This is the earliest commit with functional devnet scripts
    # on top of "op-node/v1.1.1" tag release.
    git_tag = "7168db67c5b421975fef2a090aa6e6ee4e3ff298"

    if os.path.isfile("optimism"):
        raise Exception("Error: 'optimism' exists as a file and not a directory.")
    elif not os.path.exists("optimism"):
        print("Cloning the optimism repository. This may take a while...")
        descr = "clone the optimism repository"
        lib.run(descr, f"git clone {github_url}")
        print("Successfully cloned the optimism repository.")

    lib.run("checkout stable version", f"git checkout --detach {git_tag}", cwd="optimism")

    print("Starting to build the optimism repository. Logging to logs/build_optimism.log\n"
          "This may take a while...")

    lib.run_roll_log(
        descr="build optimism",
        command=deps.cmd_with_node("make build"),
        cwd="optimism",
        log_file="logs/build_optimism.log")

    print("Successfully built the optimism repository.")

####################################################################################################
