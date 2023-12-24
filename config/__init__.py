import os.path

from .accounts_keys import AccountsKeysConfig
from .devnet_l1 import DevnetL1Config
from .explorer import ExplorerConfig
from .governance import GovernanceConfig
from .l1_contracts_deploy import L1ContractsDeployConfig
from .l2_engine import L2EngineConfig
from .l2_node import L2NodeConfig
from .l2_proposer import L2ProposerConfig
from .network import NetworkConfig
from .paths import PathsConfig


####################################################################################################
# Summary on default port mapping:
#
# The default port mapping uses the same port as the devnet configuration in the Optimism monorepo,
# whenever possible.
#
# - L1 http RPC: 8545
# - L1 WebSocket RPC: 8546
# - L1 authRPC: 8551 (authenticated APIs)
# - L1 p2p: 30303 (block & tx gossip — geth default, not configured in devnet)
# - L1 metrics: 7060
# - L2 engine http RPC: 9545 (like L1 http RPC but for L2)
# - L2 engine Websocket RPC: 9546 (like L1 Websocket RPC but for L2)
# - L2 engine authRPC: 9551 (like L1 authRPC but for L2 — op-node <> engine communication)
# - L2 engine p2p: 30313 (like L1 p2p but for L2 — not configured in devnet)
# - L2 engine metrics: 8060
# - L2 node RPC: 7545 (optimism_ and admin_ namespaces)
# - L2 node metrics: 7300
# - L2 proposer RPC: 5545 (no namespaces)
# - L2 proposer metrics: 7302
# - L2 batcher RPC: 6545 (admin_ namespace)
# - L2 batcher metrics: 7301

# When following the OP stack "Getting Started" guide, the following ports are used:
# (The L1 and L2 engine ports are inverted, and the other components are numbered differently.)
# https://stack.optimism.io/docs/build/getting-started
#
# - L1 http RPC: 9545
# - L1 WebSocket RPC: 9546
# - L1 authRPC: 9551 (authenticated APIs)
# - L1 p2p: 30313 (block & tx gossip)
# - L2 engine http RPC: 8545
# - L2 engine Websocket RPC: 8546 (like L1 Websocket RPC but for L2)
# - L2 engine authRPC: 8551
# - L2 engine p2p: 9003
# - L2 node RPC: 8547
# - L2 proposer RPC: 8560 (no namespaces)
# - L2 batcher RPC: 8548 (admin_ namespace)
#
# The guide does not configure metrics, so the defaults from above are used.
####################################################################################################
# NOTE
#
# The default config is a DEVNET config, which makes it suitable for testing, but not production.
# It is based on the config from the Optimism monorepo devnet as far as the tuning parameters and
# the port mappings are concerned.
#
# We provide various ways to customize it via the following methods:
# - `use_production_config()` — a configurable more suitable for production environment
# - `use_devnet_config()` — same config as the Optimism monorepo devnet
#   (in practice, just changes some paths)
# - `use_doc_config()` — same config as the OP Stack "Getting Started" guide
#
# The `production` config is inspired by the `doc` config for the performance parameters, but uses
# the port mappings, paths, etc... from the default config.
#
# The `production` config is automatically enabled when using the `--preset=prod` flag, otherwise
# the default config is used.
#
####################################################################################################

class Config(
    PathsConfig,
    AccountsKeysConfig,
    GovernanceConfig,
    DevnetL1Config,
    L1ContractsDeployConfig,
    NetworkConfig,
    L2NodeConfig,
    L2EngineConfig,
    L2ProposerConfig,
    ExplorerConfig
):

    # ==========================================================================================
    # Ensure abstract properties are "implemented".

    deployment_name = None

    # ==========================================================================================

    def __init__(self, deployment_name: str = "rollup"):

        # ==========================================================================================
        # Deployment Name

        self.deployment_name = deployment_name
        """
        Name for the rollup deployment, this will be set as the `DEPLOYMENT_CONTEXT` environment
        variable during contract deployment to L1, to determine the directory where the deploy
        script will put the deployment artifacts.
        """
        # NOTE: setting this variable is not required for chains "known" by the optimism repo deploy
        # script, but required for other chains to put the deployment artifacts in their own
        # directory.

        # ==========================================================================================
        # Mixin Constructors

        super().__init__()

        # ==========================================================================================
        # Batcher Configuration

        self.batcher_poll_interval = 1
        """
        Interval in seconds at which the batcher polls the execution engine for new blocks.
        """

        # NOTE(norswap): Comment in monorepo devnet says "SWS is 15, ChannelTimeout is 40"
        self.sub_safety_margin = 4
        """
        The batcher tx submission safety margin (in number of L1-blocks) to subtract from a
        channel's timeout and sequencing window, to guarantee safe inclusion of a channel on
        L1 (4 by default).
        """

        self.batcher_num_confirmations = 1
        """
        Number of confirmations to wait after submitting a batch to the L1, to consider the
        submission successful (1 by default).
        """

        self.max_channel_duration = 1
        """
        The maximum duration of L1-blocks to keep a channel open. (Default: 1)
        When set to 0, this enables channels to stay open until they are big enough.
        """

        self.batcher_resubmission_timeout = 30
        """
        The time after which a batcher will resubmit an L1 transaction that has not been included
        on-chain.
        """

        # === RPC ===

        self.batcher_enable_admin = False
        """
        Whether the "admin" namespace batcher API is enabled (False by default). This API allows
        starting and stopping the batcher (cf.
        https://github.com/ethereum-optimism/optimism/blob/develop/op-batcher/rpc/api.go).
        
        This is the only API exposed by the batcher, though the batcher will always spin the server
        even if this is disabled.
        """

        self.batcher_rpc_listen_addr = "127.0.0.1"
        """
        Address the batcher RPC server should bind to ("127.0.0.1" by default).
        
        Because only the admin API is exposed by the RPC server, this should not be exposed to the
        outside world.
        """

        self.batcher_rpc_listen_port = 6545
        """
        Port the batcher RPC server should bind to (6545 by default).
        """

        # === Metrics ===

        self.batcher_metrics = False
        """
        Whether to record metrics in the proposer (False by default).
        """

        self.batcher_metrics_listen_port = 7301
        """
        Port to the batcher metrics server should bind to (7301 by default).
        Ignored if :py:attribute:`batcher_metrics` is False.
        """

        self.batcher_metrics_listen_addr = "0.0.0.0"
        """
        Address the batcher metrics server should bind to ("0.0.0.0" by default).
        Ignored if :py:attribute:`batcher_metrics` is False.
        """

        # NOTE(norswap): The pprof server listens on port 6060 by default.

        # ==========================================================================================
        # Account Abstraction Configuration

        self.aa_deployer_key = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
        """
        Private key to use for deploying 4337 contracts.
        Uses the 0th "test junk" mnemonnic key by default.
        """

        self.bundler_key = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
        """
        Private key to use for submitting bundled transactions.
        Uses the 0th "test junk" mnemonnic key by default.
        """

        self.paymaster_key = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
        """
        Private key to use as paymaster signer.
        Uses the 0th "test junk" mnemonnic key by default.
        """

        self.paymaster_validity = 300
        """
        Time validity (in seconds) for the sponsored transaction that is signed by paymaster.
        """

        self.deploy_aa_log_file_name = "deploy_aa_contracts.log"
        """
        File name for the log file that will be created when deploying the AA contracts.
        
        It's recommended not to mess with this, it's only in the config because it's written and
        read in different locations, so it helps to maintain a single source of truth.
        """

    # ==============================================================================================

    def validate(self):
        """
        Check the validity of the configuration. This raises an error if the config is invalid or
        inconsistent.
        """
        if not isinstance(self.deployment_name, str) or self.deployment_name == "":
            raise ValueError("deployment_name must be a non-empty string")

    # ==============================================================================================
    # Updating / Altering the Configuration

    # ----------------------------------------------------------------------------------------------

    def use_devnet_config(self):
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

        self.jwt_secret_path = os.path.join(self.paths.ops_bedrock_dir, "test-jwt-secret.txt")

        # === Node ===

        self.p2p_peer_key_path = os.path.join(self.paths.ops_bedrock_dir, "p2p-node-key.txt")

    # ----------------------------------------------------------------------------------------------

    # noinspection PyAttributeOutsideInit
    def use_op_doc_config(self):
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

        self.l1_chain_id = 11155111
        self.l2_chain_id = 42069

        # We need to do this because the documentation assigns 8545 to the L2 engine RPC.
        self.l1_rpc_url = "http://127.0.0.1:9545"
        self.l1_rpc_for_node_url = "ws://127.0.0.1:9546"

        self.l2_engine_rpc_http_url = "http://127.0.0.1:8545"
        self.l2_engine_rpc_ws_url = "ws://127.0.0.1:8546"
        self.l2_engine_rpc_url = self.l2_engine_rpc_http_url
        self.l2_engine_authrpc_url = "http://127.0.0.1:8551"
        self.l2_node_rpc_url = "http://127.0.0.1:8547"

        self.jwt_secret_path = "jwt.txt"

        # === Devnet L1 ===

        self.l1_rpc_listen_port = 9545
        self.l1_rpc_ws_listen_port = 9546
        self.l1_authrpc_listen_port = 9551

        # === Engine ===

        self.l2_engine_rpc_listen_port = 8545
        self.l2_engine_rpc_ws_listen_port = 8546
        self.l2_engine_authrpc_listen_port = 8551
        self.l2_engine_p2p_port = 9003

        # === Node ===

        self.l2_node_sequencer_l1_confs = 3
        self.l2_node_verifier_l1_confs = 3
        self.l2_node_rpc_listen_port = 8547

        # === Proposer ===

        self.proposer_poll_interval = 12
        self.proposer_num_confirmations = 10
        # Must be true if using the devnet L1 or any L1 that doesn't mark blocks as finalized!
        self.allow_non_finalized = False
        self.proposer_rpc_listen_port = 8560

        # === Batcher ===

        self.batcher_num_confirmations = 10
        self.sub_safety_margin = 6
        self.batcher_rpc_listen_port = 8548

    # ----------------------------------------------------------------------------------------------

    def use_production_config(self):
        """
        Use a configuration suitable for production, inspired from the OP stack "Getting
        Started" guide (https://stack.optimism.io/docs/build/getting-started), but not identical
        (e.g. we don't follow their port scheme). If you want an identical configuration, use
        :py:meth:`use_op_doc_config`.
        """

        # === Node ===

        self.l2_node_sequencer_l1_confs = 5
        self.l2_node_verifier_l1_confs = 4

        # === Proposer ===

        self.proposer_poll_interval = 12
        self.proposer_num_confirmations = 10
        # Must be true if using the devnet L1 or any L1 that doesn't mark blocks as finalized!
        self.allow_non_finalized = False

        # === Batcher ===

        self.batcher_num_confirmations = 10
        self.sub_safety_margin = 6

    # ----------------------------------------------------------------------------------------------

    def use_upnode_config(self):
        """
        Config from https://github.com/upnodedev/op-stack-basic-deployment
        """

        # === Node ===

        self.l2_node_sequencer_l1_confs = 4

        # === Proposer ===

        self.proposer_poll_interval = 6
        self.proposer_num_confirmations = 10
        # Must be true if using the devnet L1 or any L1 that doesn't mark blocks as finalized!
        self.allow_non_finalized = False

        #  === Batcher ===

        self.batcher_num_confirmations = 10
        self.sub_safety_margin = 10

####################################################################################################
