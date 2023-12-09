# roll-op

Under development!

This work is support by an
[Optimism governance grant](https://app.charmverse.io/op-grants/proposals?id=a6e6bfb8-75bd-41bd-acb1-618c3c62e667).

roll-op (formerly simple-op-stack-rollup) is an open-source script that makes it trivial for any
developer to spin up an OP stack rollup, both for development and production use.

The script enables you to configure and run your own rollup infrastructure by running only two or
three commands. It uses a single well-documented configuration file, and helps you fill it via a
command line wizard.

Additionally, the package supports spinning EIP-4337 account abstraction infrastructure (a bundler
and a paymaster) and helps you configure them so that you can automatically subsidize gas for
transactions that match certain criteria (e.g. transactions to specific whitelisted contracts).

## Versioning

The current version of simple-op-stack-rollup deploys software pinned to the following commit

- Optimism Monorepo: [`7168db67c5b421975fef2a090aa6e6ee4e3ff298`](https://github.com/ethereum-optimism/optimism/tree/7168db67c5b421975fef2a090aa6e6ee4e3ff298)
- op-geth: [`v1.101106.0`](https://github.com/ethereum-optimism/op-geth/tree/v1.101106.0)

## Prerequisites

- Python >= 3.10 (to run the `roll.py` script) with pip
  - `sudo apt install python3-pip` on Debian-based systems
  - `brew install python` on macOS with Homebrew

The following dependencies will be checked by `roll.py`:

- Some common command line utilities: `make`, `curl`, `tar`, `awk` and `grep`.
- Git
- Docker (if you wish to run the Blockscout block explorer)

`roll.py` will check the following dependencies and install them for you if needed (the script will
always for your permission before installing anything outside the current directory):

- Python libraries
  - [Tomli](https://pypi.org/project/tomli/)
  - [PyYAML](https://pypi.org/project/PyYAML/) (for block explorer support)
  - These will be installed globally by default
  - install them locally instead (in a venv within the roll-op directory), you can run `source
    devenv.sh` before running `rollop`.
- Node.js 20.9.0
- pnpm (`pnpm install -g pnpm`)
- Yarn (for account abstraction support)
  (`npm install -g yarn` — the old one, not yarn v3 aka yarn berry)
- Geth >= 1.13.4 (but only if you want to run a devnet L1 node)
- The `jq` command line utility
- [Foundry](https://github.com/foundry-rs/foundry)
- Go >= 1.21

## Usage

```
usage: rollop [--name NAME] [--preset {dev,prod}] [--config CONFIG_PATH] [--clean] [--trace] [--no-ansi-esc] [--yes] <command> ...

Helps you spin up an op-stack rollup.
Use `rollop <command> --help` to get more detailed help for a command.

options:
  --name NAME           name of the rollup deployment
  --preset {dev,prod}   use a preset rollup configuration
  --config CONFIG_PATH  path to the config file
  --clean               clean command-related output before running the specified command
  --trace               display exception stack trace in case of failure
  --no-ansi-esc         disable ANSI escape codes for terminal manipulation
  --yes                 answer yes to all prompts (install all requested dependencies)

commands:
  <command>

    -- MAIN COMMANDS --

    help                show this help message and exit
    setup               installs prerequisites and builds the optimism repository
    devnet              starts a local devnet, comprising an L1 node and all L2 components
    clean               cleans up deployment outputs and databases
    l2                  deploys and starts a local L2 blockchain
    aa                  starts an ERC-4337 bundler and a paymaster signer service
    explorer            starts a block explorer
    
    -- GRANULAR COMMANDS --

    l1                  starts a local L1 node
    deploy-l2           deploys but does not start an L2 chain
    start-l2            start all components of the rollup system (see below)
    l2-engine           starts a local L2 execution engine (op-geth) node
    l2-sequencer        starts a local L2 node (op-node) in sequencer mode
    l2-batcher          starts a local L2 transaction batcher
    l2-proposer         starts a local L2 output roots proposer
    
    -- CLEANUP --

    clean-build         cleans up build outputs (but not deployment outputs or databases)
    clean-l1            cleans up deployment outputs & databases for L1, deploy config is preserved
    clean-l2            cleans up deployment outputs & databases for L2, deploy config is preserved
    clean-aa            cleans up deployment outputs for account abstraction
    clean-explorer      deletes the block explorer databases, logs, and containers
```

You can also use the `roll.py` script directly as `./roll.py` or `python3 roll.py`  as an
alternative. However `rollop` is recommended, as it will guarantee it is run from the rollop
repository and can be symlinked if required.

### Examples

```bash
./rollop setup
./rollop setup --yes # auto-install all dependencies
./rollop --clean devnet # default deployment name is "rollup"

# equivalent with a different deployment name
./rollop --clean --name=testing --preset=dev --config=config.toml.example devnet

# to deploy & run on an existing L1 (after setting up a config.toml)
./rollop --clean --name=my-prod-rollup --preset=prod --config=config.toml l2

# resume previously create rollup (e.g. after killing previous command)
./rollop --name=my-prod-rollup --preset=prod --config=config.toml start-l2

# deploy rollup on existing L1, then start it
./rollop --name=my-prod-rollup --preset=prod --config=config.toml deploy-l2
./rollop --name=my-prod-rollup --preset=prod --config=config.toml start-l2
```

## Contributing (for developers building simple-op-stack rollup)

```bash
# Enable dev environment and make sure dev dependencies are installed
source devenv.sh

# ... do stuff

# Run lint & format checks
make check

# Fix issues highlighted by make check if possible (some lint issues might need manual fixes)
make fix && make check


```

## Plans

- See [here](https://app.charmverse.io/op-grants/proposals?id=a6e6bfb8-75bd-41bd-acb1-618c3c62e667)
  for the initial description of the project including some milestones.
- See [this document](https://hackmd.io/@vitalizing/SJXw9Wbih) for a more thoughtful architecture breakdown.