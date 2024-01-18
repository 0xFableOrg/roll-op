#!/usr/bin/env python3

import argparse
import json
import os
import sys
import tomli

import libroll as lib


def main():
    parser = argparse.ArgumentParser(description='Bridge eth from L1 to L2.')
    parser.add_argument('--private-key', type=str, default=None,
                        help='Private key for the transaction.')
    parser.add_argument('--account', type=str, default=None,
                        help='Account to send to.')
    parser.add_argument('--amount', type=str, default='1ether',
                        help='Amount of eth to bridge.')
    parser.add_argument('--name', type=str, default='rollup',
                        help='Name of the deployment.')
    parser.add_argument('--config', type=str, default='config.toml',
                        help='Path to the config file.')
    args = parser.parse_args()

    config = tomli.load(open(args.config, 'rb'))

    private_key = args.private_key or config["contract_deployer_key"]
    account = args.account or config["contract_deployer_account"]

    bridge_proxy = json.load(
        open(os.path.join('deployments', args.name, 'artifacts', 'addresses.json')))['L1StandardBridgeProxy']

    if not private_key or not account:
        sys.exit("Private key and account must be provided either via arguments or config.")

    try:
        print("Sending eth to L1StandardBridgeProxy contract.")
        cast_command = [
            "cast", "send",
            "--rpc-url", config["l1_rpc_url"],
            "--private-key", private_key,
            bridge_proxy,
            "--value", lib.parse_amount(args.amount),
            "'depositETHTo(address,uint32, bytes)'", account, "0", "0x"
        ]

        lib.run("sending eth to L1StandardBridgeProxy contract.", cast_command)
        print("Successfully sent transaction to L1StandardBridgeProxy.")

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
