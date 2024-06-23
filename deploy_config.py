import time

import state
from config import Config
from deploy_config_templates import PRODUCTION_CONFIG, DEVNET_CONFIG
import libroll as lib


####################################################################################################

def generate_deploy_config(config: Config, pre_l1_genesis=False):
    """
    Generate the deploy configuration file. This is passed to the deploy script, and also used to
    generated the L2 genesis, the devnet L1 genesis if required, and the rollup config passed to the
    L2 node.

    The `pre_l1_genesis` flag is used to indicate that the L1 genesis has not been generated yet
    and so this should set the L1 genesis timestamp to the current time.
    """
    print("Generating deploy config.")

    # Get base config, default is the devnet config, but can overriden to production config via
    # the --preset flag.

    if state.args.preset == "prod":
        deploy_config = PRODUCTION_CONFIG.copy()
    else:
        deploy_config = DEVNET_CONFIG.copy()

    # We need to know the earliest L1 block that might contain rollup-related information
    # ("l1StartingBlockTag"). This accepts either a blockhash, or a "block tag".

    # Because it's pretty hard to find the documentation on these tags, here is the information I've
    # been able to gather. The possibile values are: earliest, finalized, safe, latest or pending.
    #
    # "Earliest" is block 0. On Ethereum, "safe" is a block that has received 2/3 attestations but
    # isn't finalized yet, "finalized" is a block that has been finalized, "latest" is the latest
    # proposed block, with no guarantee of attestations. "Pending" is an image of a block that could
    # theoretically be proposed, but probably won't be (because the node isn't the proposer).
    #
    # On L2s, these things are probably slighty different. I'm just wildly guessing here.
    # "Finalized" might be for blocks whose batch has been posted to a finalized L1 block, "safe"
    # might be for blocks whose batch has been posted to L1, and "latest" might be for blocks that
    # have been sent by the sequencer but not posted yet. (NOT SURE, JUST GUESSES)
    # Obviously, this will vary across L2s...
    #
    # (The only reason I'm bringing up L2s here is that they may serve as "L1" for a roll-op L2!)
    #
    # op-geth doesn't compute pending blocks by default (option `--rollup.computependingblock`).

    # Anyhow, we use "earliest" on a local devnet (we have a genesis file for L1), because fetching
    # the latest block somehow does not work against the local L1. But since we're usually spinning
    # the L1 right before the L2, using "earliest" works just as well.
    #
    # Otherwise, we use cast to get the "latest" block from the configured RPC endpoint and use its
    # hash.

    # If we're deploying a devnet L1, we need this.
    # Otherwise, it also needs to be set to a value that can be parsed, but will be ignored.
    deploy_config["l1GenesisBlockTimestamp"] = '{:#x}'.format(int(time.time()))

    if pre_l1_genesis:
        deploy_config["l1StartingBlockTag"] = "earliest"
    else:
        out = lib.run(
            "get latest block",
            f"cast block latest --rpc-url {config.l1_rpc_url} "
            "| grep -E '(hash|number|timestamp)'",
            forward="capture")
        try:
            # NOTE: We used to use awk here, but it swallows the pipeline error.
            [blockhash, number, timestamp, *_rest] = lib.select_columns(out, 1)
            deploy_config["l1StartingBlockTag"] = blockhash
            lib.debug(f"L1 starting block is {number} ({blockhash} at time {timestamp})")
        except Exception as e:
            raise lib.extend_exception(e, "Failed to get latest block") from None

    deploy_config["l1ChainID"] = config.l1_chain_id
    deploy_config["l2ChainID"] = config.l2_chain_id

    deploy_config["p2pSequencerAddress"] = config.p2p_sequencer_account
    deploy_config["batchInboxAddress"] = config.batch_inbox_address
    deploy_config["batchSenderAddress"] = config.batcher_account

    deploy_config["l2OutputOracleProposer"] = config.proposer_account
    deploy_config["l2OutputOracleChallenger"] = config.admin_account

    deploy_config["proxyAdminOwner"] = config.admin_account
    deploy_config["finalSystemOwner"] = config.admin_account
    deploy_config["superchainConfigGuardian"] = config.admin_account

    deploy_config["baseFeeVaultRecipient"] = config.admin_account
    deploy_config["l1FeeVaultRecipient"] = config.admin_account
    deploy_config["sequencerFeeVaultRecipient"] = config.admin_account

    deploy_config["enableGovernance"] = config.enable_governance
    deploy_config["governanceTokenSymbol"] = config.governance_token_symbol
    deploy_config["governanceTokenName"] = config.governance_token_name
    deploy_config["governanceTokenOwner"] = config.admin_account

    # See deploy_config.py to see the values the Optimism monorepo gives the various addresses
    # in the devnet. These are all standard "test junk" mnemonic accounts.

    try:
        lib.write_json_file(config.deploy_config_path, deploy_config)
    except Exception as err:
        raise lib.extend_exception(err, prefix="Failed to generate deploy config: ") from None

####################################################################################################
