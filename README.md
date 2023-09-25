# simple-op-stack-rollup

Under development!

This work is support by an
[Optimism governance grant](https://app.charmverse.io/op-grants/proposals?id=a6e6bfb8-75bd-41bd-acb1-618c3c62e667).

simple-op-stack rollup is open-source package that makes it trivial for any
developer to spin up an OP stack rollup, both for development and production
use.

The package enables you to configure and run your own rollup infrastructure by
running only two or three commands. It uses a single well-documented
configuration file, and helps you fill it via a command line wizard.

Additionally, the package supports spinning EIP-4337 account abstraction
infrastructure (a bundler and a paymaster) and helps you configure them so that
you can automatically subsidize gas for transactions that match certain criteria
(e.g. transactions to specific whitelisted contracts).

## Versioning

The current version of simple-op-stack-rollup deploys software pinned to the following commit

- Optimism Monorepo: [`7168db67c5b421975fef2a090aa6e6ee4e3ff298`](https://github.com/ethereum-optimism/optimism/tree/7168db67c5b421975fef2a090aa6e6ee4e3ff298)
- op-geth: [`v1.101106.0`](https://github.com/ethereum-optimism/op-geth/tree/v1.101106.0)

## Prerequisites

- Python >= 3.10 (to run the `roll.py` script)

The following dependencies will be checked by `roll.py`:

- Some common command line utilities: `make`, `curl`, `tar`, `awk` and `grep`.
- Git
- Go 1.19

`roll.py` will check the following dependencies and install them for you if needed (the script will
always for your permission before installing anything outside the current directory):

- [Tomli Python Lib](https://pypi.org/project/tomli/)
    - Will be installed globally if you don't run the script in a venv.
    - You can install locally (in a venv within the roll-op directory) by running
      `source scripts/install.sh` before running `roll.py`.
- Node.js 16.x
- Yarn (`npm install -g yarn` — the old one, not yarn v3 aka yarn berry)
- Geth > 1.12.0 (but only if you want to run a devnet L1 node)
- The `jq` command line utility
- Foundry

## Running

```bash
./roll.py setup
./roll.py devnet # runs a local devnet
./roll.py clean # erase any effect of the previous command (except logs)
# equivalent with a different name
./roll.py --name=testing --preset=devnet --config=config.toml.example devnet
# clean needs the same flags to work properly!
./roll.py --name=testing --preset=devnet --config=config.toml.example clean
# to deploy & run on an existing L1 (after setting up a config.toml)
./roll.py --name=my-prod-rollup --preset=production --config=config.toml l2
./roll.py --name=my-prod-rollup --preset=production --config=config.toml clean
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