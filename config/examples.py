"""
Functions in this file alter a Config object (that must be default-initiatilized!) so that it
matches some well-known configuration example.
"""

import os

from config import Config


####################################################################################################

def use_devnet_config(config: Config):
    """
    Overrides the configuration values with those from the Optimism monorepo devnet.

    The default config is already based on the devnet, so this only overrides some paths.

    We also don't enable metric servers, pprof servers, and admin APIs, neither here or in the
    default config.

    The source of truth for these values can be found here:
    https://github.com/ethereum-optimism/optimism/blob/op-node/v1.3.1/ops-bedrock/docker-compose.yml
    Or in Go defaults, e.g.
    https://github.com/ethereum-optimism/optimism/blob/op-node/v1.3.1/op-service/txmgr/cli.go
    """

    # === Network ===

    config.jwt_secret_path = os.path.join(config.paths.ops_bedrock_dir, "test-jwt-secret.txt")

    # === Node ===

    config.p2p_peer_key_path = os.path.join(config.paths.ops_bedrock_dir, "p2p-node-key.txt")


####################################################################################################

# noinspection PyAttributeOutsideInit
def use_op_doc_config(config: Config):
    """
    Overrides the configuration values with the values specified in the OP stack "Getting
    Started" guide (https://stack.optimism.io/docs/build/getting-started), wherever they
    differ from the default values.

    One difference is that we don't enable admin APIs.

    Note that the guide also uses deploy config values equivalent to the "prod" preset in
    roll-op (see `PRODUCTION_CONFIG` in `deploy_config_templates.py`).

    The guide also uses a batch inbox address of 0xff00000000000000000000000000000000042069,
    but roll-op automatically overrides this to 0xff69000000000000000000000000000000042069
    (based on the chain ID) unless configured explicitly in the `config.toml` file.
    """

    # === Network ===

    config.l1_chain_id = 11155111
    config.l2_chain_id = 42069

    # We need to do this because the documentation assigns 8545 to the L2 engine RPC.
    config.l1_rpc_url = "http://127.0.0.1:9545"
    config.l1_rpc_for_node_url = "ws://127.0.0.1:9546"

    config.l2_engine_rpc_http_url = "http://127.0.0.1:8545"
    config.l2_engine_rpc_ws_url = "ws://127.0.0.1:8546"
    config.l2_engine_rpc_url = config.l2_engine_rpc_http_url
    config.l2_engine_authrpc_url = "http://127.0.0.1:8551"
    config.l2_node_rpc_url = "http://127.0.0.1:8547"

    config.jwt_secret_path = "jwt.txt"

    # === Devnet L1 ===

    config.l1_rpc_listen_port = 9545
    config.l1_rpc_ws_listen_port = 9546
    config.l1_authrpc_listen_port = 9551

    # === Engine ===

    config.l2_engine_rpc_listen_port = 8545
    config.l2_engine_rpc_ws_listen_port = 8546
    config.l2_engine_authrpc_listen_port = 8551
    config.l2_engine_p2p_port = 9003

    # === Node ===

    config.l2_node_sequencer_l1_confs = 3
    config.l2_node_verifier_l1_confs = 3
    config.l2_node_rpc_listen_port = 8547

    # === Proposer ===

    config.proposer_poll_interval = 12
    config.proposer_num_confirmations = 10
    # Must be true if using the devnet L1 or any L1 that doesn't mark blocks as finalized!
    config.allow_non_finalized = False
    config.proposer_rpc_listen_port = 8560

    # === Batcher ===

    config.batcher_num_confirmations = 10
    config.sub_safety_margin = 6
    config.batcher_rpc_listen_port = 8548


####################################################################################################

def use_production_config(config: Config):
    """
    Use a configuration suitable for production, inspired from the OP stack "Getting
    Started" guide (https://stack.optimism.io/docs/build/getting-started), but not identical
    (e.g. we don't follow their port scheme). If you want an identical configuration, use
    :py:meth:`use_op_doc_config`.
    """

    # === Node ===

    config.l2_node_sequencer_l1_confs = 5
    config.l2_node_verifier_l1_confs = 4

    # === Proposer ===

    config.proposer_poll_interval = 12
    config.proposer_num_confirmations = 10
    # Must be true if using the devnet L1 or any L1 that doesn't mark blocks as finalized!
    config.allow_non_finalized = False

    # === Batcher ===

    config.batcher_num_confirmations = 10
    config.sub_safety_margin = 6


####################################################################################################

def use_upnode_config(config: Config):
    """
    Config from https://github.com/upnodedev/op-stack-basic-deployment
    """

    # === Node ===

    config.l2_node_sequencer_l1_confs = 4

    # === Proposer ===

    config.proposer_poll_interval = 6
    config.proposer_num_confirmations = 10
    # Must be true if using the devnet L1 or any L1 that doesn't mark blocks as finalized!
    config.allow_non_finalized = False

    #  === Batcher ===

    config.batcher_num_confirmations = 10
    config.sub_safety_margin = 10

####################################################################################################
