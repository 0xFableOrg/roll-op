import os.path

from paths import OPPaths

# Summary on default port mapping:
#
# - L1 http RPC: 8545
# - L1 WebSocket RPC: 8546
# - L1 authRPC: 8551 (authenticated APIs)
# - L1 p2p: 30303 (block & tx gossip)
# - L2 engine http RPC: 9545 (like L1 http RPC but for L2)
# - L2 engine Websocket RPC: 9546 (like L1 Websocket RPC but for L2)
# - L2 engine authRPC: 9551 (like L1 authRPC but for L2 — op-node <> engine communication)
# - L2 engine p2p: 30313 (like L1 p2p but for L2)
# - L2 node RPC: 7545 (optimism_ and admin_ namespaces)
# - L2 proposer RPC: 5545 (no namespaces)
# - L2 batcher RPC: 6545 (admin_ namespace)

# When following the OP stack "Getting Started" document, the following ports are used:
# (The L1 and L2 engine ports are inverted, and the other components are numbered differently.)
#
# - L1 http RPC: 9545
# - L1 WebSocket RPC: 9546
# - L1 authRPC: 9551 (authenticated APIs)
# - L1 p2p: 30313 (block & tx gossip)
# - L2 engine http RPC: 8545
# - L2 engine Websocket RPC: 8546 (like L1 Websocket RPC but for L2)
# - L2 engine authRPC: 8551
# - L2 engine p2p: 30303 (geth default)
# - L2 node RPC: 8547
# - L2 proposer RPC: 8560 (no namespaces)
# - L2 batcher RPC: 8548 (admin_ namespace)


class Config:

    def __init__(self, paths: OPPaths = None):

        self.paths = paths
        """
        This object is a registry of paths into the optimism directory that we need to build &
        deploy op-stack rollups.
        """

        # ==========================================================================================
        # Private Keys

        self.contract_deployer_key = (
            "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80")
        """
        Private key used to deploy contracts to L1.
        Use the 0th "test junk" mnemonnic key by default.
        """

        self.batcher_account = "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"
        """
        Account used to submit batches.
        By default, use the 2nd (0-based!) "test junk" mnemonic account.
        """

        self.batcher_key = None
        """
        Private key used to submit batches.
        Will be used if set, otherwise a mnemonic + HD derivation path will be used.
        """

        self.batcher_mnemonic = "test test test test test test test test test test test junk"
        """
        Mnemonic to use to derive the batcher key (Anvil "test junk" account mnemonic by default).
        Ignored if :py:attribute:`batcher_key` is set.
        """

        self.batcher_hd_path = "m/44'/60'/0'/0/2"
        """
        HD derivation path to use to derive the batcher key.
        Use the 2nd (0-based!) "test junk" mnemonnic key by default.
        Ignored if :py:attribute:`proposer_key` is set.
        """

        self.proposer_account = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
        """
        Account used to propose output roots
        By default, use the 0th "test junk" mnemonic account.
        """

        self.proposer_key = None
        """
        Private key used to propose output roots.
        Will be used if set, otherwise a mnemonic + HD derivation path will be used.
        """

        self.proposer_mnemonic = "test test test test test test test test test test test junk"
        """
        Mnemonic to use to derive the proposer key (Anvil "test junk" account mnemonic by default).
        Ignored if :py:attribute:`proposer_key` is set.
        """

        self.proposer_hd_path = "m/44'/60'/0'/0/1"
        """
        HD derivation path to use to derive the proposer key.
        Use the 1th (0-based!) "test junk" mnemonnic key by default.
        Ignored if :py:attribute:`proposer_key` is set.
        """

        self.p2p_sequencer_account = "0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc"
        """
        If provided, account used by the sequencer to sign blocks gossiped over p2p.
        Use the 5th (0-based!) "test junk" mnemonic account by default.
        """

        self.p2p_sequencer_key = "8b3a350cf5c34c9194ca85829a2df0ec3153be0318b5e2d3348e872092edffba"
        """
        If provided, private key used by the sequencer to sign blocks gossiped over p2p.
        Uses the 5th (0-based!) "test junk" mnemonic key by default.
        Do not prefix the key with 0x.
        """

        self.admin_account = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
        """
        Account used for various roles in the rollup system:
        - It owns all the contracts that have an owner.
        - It takes on all the privileged roles in the system.
            - challenger for the (yet to be implemented) fault proof
            - final system owner, portal guardian, and controller
                - TODO: figure out what these do
        - It is the recipient for all fees (basefees, l1 fees, sequencer fees).
        
        By default, use the 0th "test junk" account.
        
        Later, we should split this to granular roles.
        """

        self.admin_key = "ac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
        """
        Private key corresponding to :py:attribute:`admin_account`, see its documentation for
        more details.
        By default, use the 0th "test junk" account key.
        Do not prefix the key with 0x.
        """

        self.p2p_peer_key_path = os.path.join(paths.gen_dir, "opnode_p2p_priv.txt")
        """
        Path to the hex-encoded 32-byte private key for the peer ID. Will be created if it does not
        already exist.

        It's important to persist to keep the same network identity after restarting, maintaining
        the previous advertised identity.
        
        This is different than the sequencer key (which is only used by the sequencer).
        Uses `{paths.gen_dir}/opnode_p2p_priv.txt` by default.
        """

        self.l1_signer_account = "0xca062b0fd91172d89bcd4bb084ac4e21972cc467"
        """Address of the devnet L1 block signer."""

        self.l1_signer_private_key = \
            "3e4bde571b86929bf08e2aaad9a6a1882664cd5e65b96fff7d03e1c4e6dfa15c"
        """Private key of the devnet L1 block signer."""

        # ==========================================================================================
        # Deployment

        self.l1_deployment_gas_multiplier = 130
        """
        Percent-based multiplier to gas estimations during contract deployment on L1 (130 by
        default, which is the Foundry default).
        """

        # ==========================================================================================
        # Governance

        self.enable_governance = False
        """
        Whether to deploy a governance token (False by default).
        """

        self.governance_token_symbol = "STONK"
        """
        If :py:attribute:`enable_governance` is True, the symbol of the governance token to deploy.
        """

        self.governance_token_name = "Simple Token Op-chain Network Koin"
        """
        If :py:attribute:`enable_governance` is True, the name of the governance token to deploy.
        """

        # ==========================================================================================
        #  Network Configuration

        # NOTE: All URLs in this section are used to instruct various services/nodes on how to
        # reach the other services. This configuration mirrors the configuration of each of the
        # individual services, which must specify on which port/address they listen.
        #
        # The reasons the configuration is not unique is that:
        # - The actual software deployment might involve port mapping.
        # - Binding to 0.0.0.0 (always the default) means listening to every single network
        #   interface connected to the server.
        #
        # Anyhow, changing a port often involves changing a configuration in this section AND
        # changing a configuration option in the service-specific section.

        self.deployment_name = "devnetL1"
        """
        Name for the rollup deployment, this will be set as the `DEPLOYMENT_CONTEXT` environment
        variable during contract deployment to L1, to determine the directory where the deploy
        script will put the deployment artifacts.
        """
        # NOTE: setting this variable is not required for chains "known" by the optimism repo deploy
        # script, but required for other chains to put the deployment artifacts in their own
        # directory.

        self.l1_chain_id = 900
        """
        Chain ID of the L1 to use. If spinning an L1 devnet, it will use this chain ID.
        """

        self.l1_rpc = "http://127.0.0.1:8545"
        """
        Protocol + address + port to use to connect to the L1 RPC server
        ("http://127.0.0.1:8545" by default).
        
        The L2 node will use :py:attribute:`l1_rpc_for_node` instead!
        """

        self.l1_rpc_for_node = "ws://127.0.0.1:8546"
        """
        Protocol + address + port for use *by the L2 node* to connect to the L1 RPC server
        ("ws://127.0.0.1:8546" by default).
        
        The reason for this override is to enable the L2 node to use a more performant RPC, or a
        WebSocket connection to get L1 data.
        """

        self.l2_engine_rpc = "http://127.0.0.1:9545"
        """
        Protocol + address + port to use to connect to the L2 RPC server attached to the execution
        engine ("http://127.0.0.1:9545" by default).
        """

        self.l2_engine_authrpc = "http://127.0.0.1:9551"
        """
        Protocol + address + port to use to connect to the authenticated RPC (authrpc) server
        attached to the execution engine, which serves the engine API ("http://127.0.0.1:9551" by
        default).
        """

        self.l2_node_rpc = "http://127.0.0.1:7545"
        """
        Address to use to connect to the op-node RPC server ("http://127.0.0.1:7545" by default).
        """

        self.jwt_secret_path = os.path.join(paths.gen_dir, "jwt-secret.txt")
        """
        Path to the Jason Web Token secret file, which enable the l2 node to communicate with the
        execution engine. Will be generated if it does not already exist.
        
        Uses `{paths.gen_dir}/jwt-secret.txt` by default.
        
        This is also passed to the devnet L1 (if started) currently, but unclear if it's needed.
        """

        self.deployments = None
        """
        Dictionary containing a mapping from rollup contract names to the address at which they're
        deployed on L1. None before initialization.
        """

        self.batch_inbox_address = "0xff00000000000000000000000000000000000000"
        """
        Address of the batch inbox contract on L1. (0xff00000000000000000000000000000000000000 by
        default).
        """

        # ==========================================================================================
        # Devnet L1 Configuration

        self.deploy_devnet_l1 = True
        """
        Whether to deploy a local L1 devnet (True by default).
        If false, it means deploying on an existing L1 blockchain, specified by
        :py:attribute:`l1_rpc`.
        """

        # Any attribute defined in this section are only meaningful (used) if
        # :py:attribute:`deploy_devnet_l1` is True!

        self.l1_data_dir = "db/devnetL1"
        """Geth data directory for devnet L1 node."""

        # See also the properties starting with `l1` below which are paths derived from
        # :py:attribute:`l1_data_dir`.

        self.l1_verbosity = 3
        """Geth verbosity level (from 0 to 5, see geth --help)."""

        self.l1_p2p_port = 30303
        """Port to use for the p2p server of the devnet L1. (default: 30303 — geth default)"""

        self.l1_rpc_listen_addr = "0.0.0.0"
        """Address the devnet L1 http RPC server should bind to ("0.0.0.0" by default)."""

        self.l1_rpc_port = 8545
        """Port to use for the devnet L1 http RPC server (9545 by default)."""

        self.l1_rpc_ws_listen_addr = "0.0.0.0"
        """Address the devnet L1 WebSocket RPC server should bind to ("0.0.0.0" by default)."""

        self.l1_rpc_ws_port = 8546
        """Port to use for the WebSocket JSON_RPC server (8546 by default)."""

        self.l1_authrpc_listen_addr = "0.0.0.0"
        """Address the devnet L1 authRPC server should bind to ("0.0.0.0" by default)."""

        self.l1_authrpc_port = 8551
        """Port to use for the devnet L1 authRPC server (8551 by default)."""

        self.l1_password = "l1_devnet_password"
        """Password to use to secure the signer key."""

        # ==========================================================================================
        # L2 Execution Engine Configuration

        self.l2_engine_data_dir = "db/L2-execution"
        """Geth data directory for the L2 engine."""

        # See also the properties starting with `l2_engine` below which are paths derived from
        # :py:attribute:`l2_engine_data_dir`.

        self.l2_chain_id = 42069
        """Chain ID of the local L2."""

        self.l2_engine_verbosity = 3
        """Geth verbosity level (from 0 to 5, see op-geth --help)."""

        self.l2_engine_p2p_port = 30313
        """Port to use for the p2p server of the L2 engine (30313 by default)."""

        self.l2_engine_rpc_listen_addr = "0.0.0.0"
        """Address the L2 engine http RPC server should bind to ("0.0.0.0" by default)."""

        self.l2_engine_rpc_port = 9545
        """Port to use for the L2 engine http JSON-RPC server."""

        self.l2_engine_rpc_ws_listen_addr = "0.0.0.0"
        """Address the L2 engine WebSocket RPC server should bind to ("0.0.0.0" by default)."""

        self.l2_engine_rpc_ws_port = 9546
        """Port to use for the WebSocket JSON_RPC server."""

        self.l2_engine_authrpc_listen_addr = "0.0.0.0"
        """Address the L2 engine authRPC server should bind to ("0.0.0.0" by default)."""

        self.l2_engine_authrpc_port = 9551
        """Port to use for the L2 engine authRPC server (9551 by default)."""

        self.l2_engine_history_transactions = 2350000
        """
        Number of recent blocks to maintain transactions index for (default = about one
        year (geth default), 0 = entire chain)
        
        This is the `--txlookuplimit` option in geth <= 1.12 and `--history.transactions` in geth >=
        1.13.
        """

        self.l2_engine_disable_tx_gossip = True
        """
        Whether to disable transaction pool gossiping (True by default).
        
        In a system with a single sequencer, publicizing the mempool holds very little advantage:
        it can cause spam by MEV searchers trying to frontrun or backrun transactions.
        On the flip side, if the node crashes, gossiping can help refill the sequencer's mempool.
        
        I believe it's possible to set this to False (enable gossip) but restrict the peers in
        another way, such that "centralized redundancy" (multiple nodes ran by the same entity)
        can be achieved.
        
        This is currently pretty irrelevant, because we hardcode the --maxpeers=0 and --nodiscover
        flags.
        """

        # ==========================================================================================
        # Node Configuration

        self.sequencer_l1_confs = 4
        """
        Minimum number of L1 blocks that the L1 origin of L2 block must be behind the L1 head.
        """

        self.verifier_l1_confs = 0
        """
        Don't attempt to derive L2 blocks from L1 blocks that are less than this number of L1 blocks
        before the L1 head. (While L1 reorgs are supported, they are slow to perform.)
        """

        # === RPC ===

        self.node_enable_admin = False
        """
        Whether the "admin" namespace node API is enabled (False by default). This API allows
        starting, stopping, and querying the status of the sequencer (cf.
        https://github.com/ethereum-optimism/optimism/blob/develop/op-node/sources/rollupclient.go).
        """

        self.node_rpc_listen_addr = "0.0.0.0"
        """
        Address the node RPC server should bind to ("0.0.0.0" by default).
        
        Used for the "optimism" namespace API
        (https://community.optimism.io/docs/developers/build/json-rpc/) and the "admin" namespace
        (cf. :py:attribute:`node_enable_admin`).
        """

        self.node_rpc_listen_port = 7545
        """
        Port the node RPC server should bind to (7545 by default).
        
        Used for the "optimism" namespace API
        (https://community.optimism.io/docs/developers/build/json-rpc/) and the "admin" namespace
        (cf. :py:attribute:`node_enable_admin`).
        """

        # === P2P Options ===

        self.p2p_enabled = True
        """
        Whether to enable P2P (peer discovery + block gossip — True by default).
        """

        self.p2p_listen_addr = "0.0.0.0"
        """
        IP to bind LibP2P and Discv5 to.
        """

        self.p2p_tcp_listen_port = 9222
        """
        TCP port to bind LibP2P to. Any available system port if set to 0.
        """

        self.p2p_udp_listen_port = 0
        """
        UDP port to bind Discv5 to. Same as TCP port if left 0.
        """

        # === Metrics ===

        self.node_metrics = False
        """
        Whether to record metrics in the proposer (False by default).
        """

        self.node_metrics_listen_port = 7302
        """
        Port to the node metrics server should bind to (7302 by default).
        Ignored if :py:attribute:`node_metrics` is False.
        """

        self.node_metrics_listen_addr = "0.0.0.0"
        """
        Address the node metrics server should bind to ("0.0.0.0" by default).
        Ignored if :py:attribute:`node_metrics` is False.
        """

        # ==========================================================================================
        # Proposer Configuration

        self.proposer_poll_interval = 6
        """
        Interval in seconds at which the proposer polls the op-node for new blocks.
        NOTE: devnet config is 1s.
        """

        self.proposer_num_confirmations = 10
        """
        Number of confirmations to wait for before submitting a block to the L1. Defaults to 10.
        """

        self.allow_non_finalized = False
        """
        Allows the proposer to submit proposals for L2 blocks derived from non-finalized L1 blocks.
        False by default.
        """

        # === RPC ===

        self.proposer_rpc_listen_addr = "127.0.0.1"
        """
        Address the proposer RPC server should bind to ("127.0.0.1" by default).
        
        While the proposer always spins an RPC server, it does not currently handle ANY API calls,
        as a result, this should always be bound to localhost.
        """

        self.proposer_rpc_listen_port = 5545
        """
        Port the proposer RPC server should bind to (5545 by default).
        """

        # === Metrics ===

        self.proposer_metrics = False
        """
        Whether to record metrics in the proposer (False by default).
        """

        self.proposer_metrics_listen_port = 7302
        """
        Port to the proposer metrics server should bind to (7302 by default).
        Ignored if :py:attribute:`proposer_metrics` is False.
        """

        self.proposer_metrics_listen_addr = "0.0.0.0"
        """
        Address the proposer metrics server should bind to ("0.0.0.0" by default).
        Ignored if :py:attribute:`proposer_metrics` is False.
        """

        # ==========================================================================================
        # Batcher Configuration

        self.batcher_poll_interval = 6
        """
        Interval in seconds at which the proposer polls the execution engine for new blocks.
        """

        self.sub_safety_margin = 10
        """
        The batcher tx submission safety margin (in number of L1-blocks) to subtract from a
        channel's timeout and sequencing window, to guarantee safe inclusion of a channel on
        L1.
        """

        self.batcher_num_confirmations = 10
        """
        Number of confirmations to wait for before submitting a block to the L1. Defaults to 10.
        """

        self.max_channel_duration = 0
        """
        The maximum duration of L1-blocks to keep a channel open. 0 (default) to disable.
        """

        self.batcher_resubmission_timeout = 48
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

        # === Private Key ===

        self.deployer_key = None
        """
        Private key to use for deploying 4337 contracts and paymaster signature (None by default).
        Will be used if set, otherwise will prompt users to enter private key.
        """

        self.bundler_key = None
        """
        Private key to use for submitting bundled transactions (None by default).
        Will be used if set, otherwise will prompt users to enter private key.
        """

        self.paymaster_validity = 300
        """
        Time validity (in seconds) for the sponsored transaction that is signed by paymaster.
        """

    # ==============================================================================================

    @property
    def deploy_config_path(self):
        """
        Returns the path to the deploy configuration file.
        """
        return os.path.join(self.paths.deploy_config_dir, f"{self.deployment_name}.json")

    # ----------------------------------------------------------------------------------------------

    @property
    def deployments_dir(self):
        """
        Returns the directory where the deployment script will place the deployment artifacts
        (contract addresses etc) for the L1 rollup contracts.
        """
        return os.path.join(self.paths.deployments_parent_dir, self.deployment_name)

    # ----------------------------------------------------------------------------------------------

    @property
    def l1_keystore_dir(self):
        """Keystore directory for devnet L1 node (each file stores an encrypted signer key)."""
        return f"{self.l1_data_dir}/keystore"

    @property
    def l1_chaindata_dir(self):
        """Directory storing chain data."""
        return f"{self.l1_data_dir}/geth/chaindata"

    @property
    def l1_password_path(self):
        """Path to file storing the password for the signer key."""
        return f"{self.l1_data_dir}/password"

    @property
    def l1_tmp_signer_key_path(self):
        """Path to file storing the signer key during the initial import."""
        return f"{self.l1_data_dir}/block-signer-key"

    # ----------------------------------------------------------------------------------------------

    @property
    def l2_engine_chaindata_dir(self):
        """Directory storing chain data for the L2 engine."""
        return f"{self.l2_engine_data_dir}/geth/chaindata"

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

    def use_devnet_config(self, paths: OPPaths):
        """
        Overrides the configuration values with the defaults for a local devnet deployment (only
        sets the values that are different from the standard defaults).

        Currently, all values are similar to that used for the monorepo devnet, except that
        we don't enable metric servers, pprof servers, and admin APIs.
        """

        # === Network ===

        self.jwt_secret_path = paths.jwt_test_secret_path

        # === Node ===

        self.sequencer_l1_confs = 0
        self.p2p_peer_key_path = paths.p2p_key_path

        # === Proposer ===

        self.proposer_poll_interval = 1
        self.proposer_num_confirmations = 1
        self.allow_non_finalized = True

        #  === Batcher ===

        self.batcher_num_confirmations = 1
        self.batcher_poll_interval = 1
        self.max_channel_duration = 1

        # NOTE(norswap): Comment in monorepo devnet says "SWS is 15, ChannelTimeout is 40"
        self.sub_safety_margin = 4

    # ----------------------------------------------------------------------------------------------

    def use_op_doc_config(self):
        """
        Overrides the configuration values with the values specified in the OP stack "Getting
        Started" document (https://stack.optimism.io/docs/build/getting-started), wherever they
        differ from the default values.

        One difference is that we don't enable admin APIs.
        """

        # === Network ===

        # We need to do this because the documentation assigns 8545 to the L2 engine RPC.
        self.l1_rpc = "http://127.0.0.1:9545"
        self.l1_rpc_for_node = "ws://127.0.0.1:9546"

        self.l2_engine_rpc = "http://127.0.0.1:8545"
        self.l2_engine_authrpc = "http://127.0.0.1:8551"
        self.l2_node_rpc = "http://127.0.0.1:8547"

        self.jwt_secret_path = "jwt.txt"

        # === Devnet L1 ===

        self.l1_rpc_port = 9545
        self.l1_rpc_ws_port = 9546
        self.l1_authrpc_port = 9551
        self.l1_p2p_port = 30313

        # === Engine ===

        self.l2_engine_rpc_port = 8545
        self.l2_engine_rpc_ws_port = 8546
        self.l2_engine_authrpc_port = 8551
        self.l2_engine_p2p_port = 30303

        # === Node ===

        self.sequencer_l1_confs = 3
        self.verifier_l1_confs = 3
        self.node_rpc_listen_port = 8547

        # === Proposer ===

        self.proposer_poll_interval = 12
        self.proposer_rpc_listen_port = 8560

        # === Batcher ===

        self.sub_safety_margin = 6
        self.batcher_poll_interval = 1
        self.batcher_resubmission_timeout = 30
        self.max_channel_duration = 1
        self.batcher_rpc_listen_port = 8548

    # ----------------------------------------------------------------------------------------------

    def use_production_config(self):
        """
        Use a configuration suitable for production, inspired from the OP stack "Getting
        Started" document (https://stack.optimism.io/docs/build/getting-started), but not identical
        (e.g. we don't follow their port scheme). If you want an identical configuration, use
        :py:meth:`use_op_doc_config`.
        """

        # TODO parameterize
        self.allow_non_finalized = True

        # === Node ===

        self.sequencer_l1_confs = 3
        self.verifier_l1_confs = 3

        # === Proposer ===

        self.proposer_poll_interval = 12

        # === Batcher ===

        self.sub_safety_margin = 6
        self.batcher_poll_interval = 1
        self.batcher_resubmission_timeout = 30
        self.max_channel_duration = 1


####################################################################################################

def devnet_config(paths: OPPaths):
    """
    Get a full devnet configuration.
    """
    config = Config(paths)
    config.use_devnet_config(paths)
    return config


# -------------------------------------------------------------------------------------------------

def op_doc_config(paths: OPPaths):
    """
    Get a full devnet configuration.
    """
    config = Config(paths)
    config.use_op_doc_config()
    return config


# -------------------------------------------------------------------------------------------------

def production_config(paths: OPPaths):
    """
    Get a full production configuration.
    """
    config = Config(paths)
    config.use_production_config()
    return config


####################################################################################################
