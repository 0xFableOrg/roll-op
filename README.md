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

## Prerequisites

- Python 3 (to run the `roll.py` script)

The following dependencies will be checked by `roll.py`:

- `make`
- Git
- Go 1.19

`roll.py` will check the following dependencies and install them for you if needed (the script will
always for your permission before installing anything outside the current directory):

- Node.js 16.x
- Yarn (`npm install -g yarn` — the old one, not yarn v3 aka yarn berry)

## Plans

- See [here](https://app.charmverse.io/op-grants/proposals?id=a6e6bfb8-75bd-41bd-acb1-618c3c62e667)
  for the initial description of the project including some milestones.
- See [this document](https://hackmd.io/@vitalizing/SJXw9Wbih) for a more thoughtful architecture breakdown.