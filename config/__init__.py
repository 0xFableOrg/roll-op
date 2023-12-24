import os.path
import uuid

import libroll as lib
from .accounts_keys import AccountsKeysConfig
from .governance import GovernanceConfig
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
    GovernanceConfig
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
        # Deployment

        self.l1_deployment_gas_multiplier = 130
        """
        Percent-based multiplier to gas estimations during contract deployment on L1 (130 by
        default, which is the Foundry default).
        """

        self.deploy_slowly = lib.args.preset == "prod"
        """
        Whether to deploy contracts "slowly", i.e. wait for each transaction to succeed before
        submitting the next one. This is recommended for production deployments, since RPC nodes
        can be capricious and don't react kindly to getting 30+ transactions at once.
        
        Defaults to True when the `--preset=prod` is passed, False otherwise.
        """

        # ==========================================================================================
        #  Network Configuration

        # NOTE: All URL configured in this section are used to instruct various services/nodes on
        # how to reach the other services. This configuration mirrors the configuration of each of
        # the individual services, which must specify on which port/address they listen.
        #
        # The reasons the configuration is not unique is that:
        # - The actual software deployment might involve port mapping.
        # - Binding to 0.0.0.0 (always the default) means listening to every single network
        #   interface connected to the server.
        #
        # Anyhow, changing a port often involves changing a configuration in this section AND
        # changing a configuration option in the service-specific section.

        self.chain_name = f"roll-op <{self.deployment_name}>"
        """
        Name of the chain, notably used in the block explorer. Defaults to "roll-op
        <{deployment_name}>".
        """

        self.chain_short_name = "roll-op"
        """
        Short version of :py:attribute:`chain_name`, used in the block explorer.
        Defaults to "roll-op".
        """

        self.l1_chain_id = 1201101711
        """
        Chain ID of the L1 to use. If spinning an L1 devnet, it will use this chain ID.
        Defaults to 1201101711 — 'rollop L1' in 1337 speak.
        """

        self.own_address = "127.0.0.1"
        """
        Remote address of the local machine. This is used to determine if multiple components are
        running on the same machine, so they might reach each other via 127.0.0.1 instead of going
        out to the internet and then back into them machine.
        (Defaults to "127.0.0.1" — assuming a local-only setup.)
        """

        self.deploy_salt = uuid.uuid4()
        """
        A salt used for deterministic contract deployment addresses. Ideally, this would enable us
        to skip redeploying contracts that are already deployed (though they need to have been
        deployed by us, otherwise they would have the wrong owner and parameters). Unfortunately,
        this is not how the deploy script works at the moment, meaning partial deployments are not
        possible and this needs to be rotated ever time.

        Default to a random UUID, but the value can be any string.
        """

        # I'm not going to document all of these individually, but refer to their respective
        # properties which string them together in a usable URL.
        #
        # These properties also have setters that allow setting the URL as a whole, which will
        # then be split and assign the protocol, host and port parts.
        #
        # The L1 RPCs have a path part, to allow for JSON-RPC provider URLs. We assume you don't
        # need those for the other components, so we eschew the path part.

        # See :py:attribute:`l1_rpc_url` for more details.
        self.l1_rpc_protocol = "http"
        self.l1_rpc_host = "127.0.0.1"
        self.l1_rpc_path = ""
        self.l1_rpc_port = 8545

        # See :py:attribute:`l1_rpc_for_node_url` for more details.
        self.l1_rpc_for_node_protocol = "ws"
        self.l1_rpc_for_node_host = "127.0.0.1"
        self.l1_rpc_for_node_path = ""
        self.l1_rpc_for_node_port = 8546

        # See :py:attribute:`l2_engine_rpc_http_url` for more details.
        self.l2_engine_rpc_http_host = "127.0.0.1"
        self.l2_engine_rpc_http_port = 9545

        # See :py:attribute:`l2_engine_rpc_ws_url` for more details.
        self.l2_engine_rpc_ws_host = "127.0.0.1"
        self.l2_engine_rpc_ws_port = 9546

        # See :py:attribute:`l2_engine_rpc_url` for more details.
        self.l2_engine_rpc_protocol = "http"
        self.l2_engine_rpc_host = self.l2_engine_rpc_http_host
        self.l2_engine_rpc_port = self.l2_engine_rpc_http_port

        # See :py:attribute:`l2_engine_authrpc_url` for more details.
        self.l2_engine_authrpc_protocol = "http"
        self.l2_engine_authrpc_host = "127.0.0.1"
        self.l2_engine_authrpc_port = 9551

        # See :py:attribute:`l2_node_rpc_url` for more details.
        self.l2_node_rpc_protocol = "http"
        self.l2_node_rpc_host = "127.0.0.1"
        self.l2_node_rpc_port = 7545

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

        self.deploy_create2_deployer = False
        """
        Whether to deploy the CREATE2 deployer contract on the L1 before deploying the L2 contracts.
        (False by default).
        """

        # ==========================================================================================
        # Devnet L1 Configuration

        self.deploy_devnet_l1 = True
        """
        When using the "devnet" command, whether to deploy a local L1 devnet (True by default).
        If false, it means deploying on an existing L1 blockchain, specified by
        :py:attribute:`l1_rpc`.
        
        Note that you can/should stil set :py:attribute:`l1_rpc` when this is True, if you want to
        deploy the the devnet L1 on another IP or port.
        """

        # Any attribute defined in this section are only meaningful (used) if
        # :py:attribute:`deploy_devnet_l1` is True!

        # See also the properties starting with `l1` below which are paths derived from
        # :py:attribute:`l1_data_dir`.

        self.l1_verbosity = 3
        """Geth verbosity level (from 0 to 5, see geth --help)."""

        self.l1_p2p_port = 30303
        """Port to use for the p2p server of the devnet L1. (default: 30303 — geth default)"""

        self.l1_rpc_listen_addr = "0.0.0.0"
        """Address the devnet L1 http RPC server should bind to ("0.0.0.0" by default)."""

        self.l1_rpc_listen_port = 8545
        """Port to use for the devnet L1 http RPC server (9545 by default)."""

        self.l1_rpc_ws_listen_addr = "0.0.0.0"
        """Address the devnet L1 WebSocket RPC server should bind to ("0.0.0.0" by default)."""

        self.l1_rpc_ws_listen_port = 8546
        """Port to use for the WebSocket JSON_RPC server (8546 by default)."""

        self.l1_authrpc_listen_addr = "0.0.0.0"
        """Address the devnet L1 authRPC server should bind to ("0.0.0.0" by default)."""

        self.l1_authrpc_listen_port = 8551
        """Port to use for the devnet L1 authRPC server (8551 by default)."""

        self.l1_password = "l1_devnet_password"
        """Password to use to secure the signer key."""

        self.temp_l1_rpc_listen_port = 8545
        """
        Port for the temporary L1 RPC server, which is used to deploy then dump the L2 contracts,
        to be included in the devnet L1 genesis. (8545 by default)
        """

        # === Metrics ===

        self.l1_metrics = False
        """
        Whether to record metrics in the L1 node (False by default).
        """

        self.l1_metrics_listen_port = 7060
        """
        Port to the L1 node metrics server should bind to (7060 by default).
        Ignored if :py:attribute:`node_metrics` is False.
        """

        self.l1_metrics_listen_addr = "0.0.0.0"
        """
        Address the L1 node metrics server should bind to ("0.0.0.0" by default).
        Ignored if :py:attribute:`node_metrics` is False.
        """

        # ==========================================================================================
        # L2 Execution Engine Configuration

        # See also the properties starting with `l2_engine` below which are paths derived from
        # :py:attribute:`l2_engine_data_dir`.

        self.l2_chain_id = 1201101712
        """Chain ID of the local L2 (default: 1201101712 — 'rollop L2' in 1337 speak)."""

        self.l2_engine_verbosity = 3
        """Geth verbosity level (from 0 to 5, see op-geth --help)."""

        self.l2_engine_p2p_port = 30313
        """Port to use for the p2p server of the L2 engine (30313 by default)."""

        self.l2_engine_rpc_listen_addr = "0.0.0.0"
        """Address the L2 engine http RPC server should bind to ("0.0.0.0" by default)."""

        self.l2_engine_rpc_listen_port = 9545
        """Port to use for the L2 engine http JSON-RPC server."""

        self.l2_engine_rpc_ws_listen_addr = "0.0.0.0"
        """Address the L2 engine WebSocket RPC server should bind to ("0.0.0.0" by default)."""

        self.l2_engine_rpc_ws_listen_port = 9546
        """Port to use for the WebSocket JSON_RPC server."""

        self.l2_engine_authrpc_listen_addr = "0.0.0.0"
        """Address the L2 engine authRPC server should bind to ("0.0.0.0" by default)."""

        self.l2_engine_authrpc_listen_port = 9551
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

        # === Metrics ===

        self.l2_engine_metrics = False
        """
        Whether to record metrics in the L2 engine (False by default).
        """

        self.l2_engine_metrics_listen_port = 8060
        """
        Port to the L2 engine metrics server should bind to (8060 by default).
        Ignored if :py:attribute:`node_metrics` is False.
        """

        self.l2_engine_metrics_listen_addr = "0.0.0.0"
        """
        Address the L2 engine metrics server should bind to ("0.0.0.0" by default).
        Ignored if :py:attribute:`node_metrics` is False.
        """

        # ==========================================================================================
        # Node Configuration

        self.l2_node_sequencer_l1_confs = 0
        """
        Minimum number of L1 blocks that the L1 origin of L2 block must be behind the L1 head (0 by
        default).
        """

        self.l2_node_verifier_l1_confs = 0
        """
        Don't attempt to derive L2 blocks from L1 blocks that are less than this number of L1 blocks
        before the L1 head. (While L1 reorgs are supported, they are slow to perform.)
        """

        self.l2_node_l1_rpc_kind = "basic"
        """
        The kind of RPC provider for L1 access, used to inform optimal transactions receipts
        fetching, and thus reduce costs. Valid options: alchemy, quicknode, infura, parity,
        nethermind, debug_geth, erigon, basic, any. Default: basic.
        
        "Basic" only tries basic methods, while "any" tries any available method.
        """

        # === RPC ===

        self.l2_node_enable_admin = False
        """
        Whether the "admin" namespace node API is enabled (False by default). This API allows
        starting, stopping, and querying the status of the sequencer (cf.
        https://github.com/ethereum-optimism/optimism/blob/develop/op-node/sources/rollupclient.go).
        """

        self.l2_node_rpc_listen_addr = "0.0.0.0"
        """
        Address the node RPC server should bind to ("0.0.0.0" by default).
        
        Used for the "optimism" namespace API
        (https://community.optimism.io/docs/developers/build/json-rpc/) and the "admin" namespace
        (cf. :py:attribute:`node_enable_admin`).
        """

        self.l2_node_rpc_listen_port = 7545
        """
        Port the node RPC server should bind to (7545 by default).
        
        Used for the "optimism" namespace API
        (https://community.optimism.io/docs/developers/build/json-rpc/) and the "admin" namespace
        (cf. :py:attribute:`node_enable_admin`).
        """

        # === P2P Options ===

        self.l2_node_p2p_enabled = False
        """
        Whether to enable P2P (peer discovery + block gossip — False by default).
        """

        self.l2_node_p2p_listen_addr = "0.0.0.0"
        """
        IP to bind LibP2P and Discv5 to.
        """

        self.l2_node_p2p_tcp_listen_port = 9222
        """
        TCP port to bind LibP2P to. Any available system port if set to 0.
        """

        self.l2_node_p2p_udp_listen_port = 0
        """
        UDP port to bind Discv5 to. Same as TCP port if left 0.
        """

        # === Metrics ===

        self.l2_node_metrics = False
        """
        Whether to record metrics in the L2 node (False by default).
        """

        self.l2_node_metrics_listen_port = 7300
        """
        Port to the l2 node metrics server should bind to (7300 by default).
        Ignored if :py:attribute:`node_metrics` is False.
        """

        self.l2_node_metrics_listen_addr = "0.0.0.0"
        """
        Address the L2 node metrics server should bind to ("0.0.0.0" by default).
        Ignored if :py:attribute:`node_metrics` is False.
        """

        # ==========================================================================================
        # Proposer Configuration

        self.proposer_poll_interval = 1
        """
        Interval in seconds at which the proposer polls the op-node for new blocks.
        (Default: 1s)
        """

        self.proposer_num_confirmations = 1
        """
        Number of confirmations to wait after submitting a proposal to the L1, to consider the
        submission successful (1 by default).
        """

        self.allow_non_finalized = True
        """
        Allows the proposer to submit proposals for L2 blocks derived from non-finalized L1 blocks
        (True by default).

        Note that if your L1 does not mark blocks as finalized, this *needs* to be True, or the
        proposer will never propose anything. This is the case for the devnet L1!
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

    # These are the URLs that other components use to reach the specified components, which are
    # distinct form the addresses / ports that the components bind to.
    # Refer to the "Network Configuration" section for more details.

    def _maybe_local_url(
            self,
            protocol: str,
            host: str,
            port: int,
            path: str = "",
            own_address: str = None):
        """
        Returns a URL made from protocol, host and port, but substitute 127.0.0.1 to the host
        if the host is the same as `own_address`.
        """
        if own_address is None:
            own_address = self.own_address
        if own_address and own_address == host:
            host = "127.0.0.1"
        return f"{protocol}://{host}:{port}{path}"

    def _set_url_components(self, url: str, prefix: str, allow_path: bool = False):
        """
        Parses an URL and assigns its components to the corresponding attributes of this object
        based on the prefix. The URL is only allowed to have a path after the hostname if
        `allow_path` is True, or an exception is raised.
        """
        parsed = lib.parse_rpc_url(url)
        if not allow_path and parsed.path:
            raise ValueError(f"URL {url} (for {prefix} contains a path part, which is not allowed")
        setattr(self, prefix + "_protocol", parsed.protocol)
        setattr(self, prefix + "_host", parsed.address)
        setattr(self, prefix + "_port", parsed.port)
        if allow_path:
            setattr(self, prefix + "_path", parsed.path)

    @property
    def l1_rpc_url(self, own_address: str = None):
        """
        Protocol + address + port to use to connect to the L1 RPC server
        ("http://127.0.0.1:8545" by default).
        Host is substituted by 127.0.0.1 if it matches `own_address`.

        The L2 node will use :py:attribute:`l1_rpc_for_node` instead!
        """
        return self._maybe_local_url(
            self.l1_rpc_protocol,
            self.l1_rpc_host,
            self.l1_rpc_port,
            self.l1_rpc_path,
            own_address=own_address)

    @l1_rpc_url.setter
    def l1_rpc_url(self, url: str):
        self._set_url_components(url, "l1_rpc", allow_path=True)

    @property
    def l1_rpc_for_node_url(self, own_address: str = None):
        """
        Protocol + address + port for use *by the L2 node* to connect to the L1 RPC server
        ("ws://127.0.0.1:8546" by default).

        The reason for this override is to enable the L2 node to use a more performant RPC, or a
        WebSocket connection to get L1 data.

        If the config file doesn't set this but set :py:attribute:`l1_rpc_url` instead, roll-op
        will automatically copy the value of :py:attribute:`l1_rpc_url` to this property.
        """
        return self._maybe_local_url(
            self.l1_rpc_for_node_protocol,
            self.l1_rpc_for_node_host,
            self.l1_rpc_for_node_port,
            self.l1_rpc_for_node_path,
            own_address=own_address)

    @l1_rpc_for_node_url.setter
    def l1_rpc_for_node_url(self, url: str):
        self._set_url_components(url, "l1_rpc_for_node", allow_path=True)

    @property
    def l2_engine_rpc_url(self, own_address: str = None):
        """
        Protocol + address + port to use to connect to the L2 RPC server attached to the execution
        engine ("http://127.0.0.1:9545" by default).
        This is the default URL to be used whenever protocol choice is allowed.
        Host is substituted by 127.0.0.1 if it matches `own_address`.
        """
        return self._maybe_local_url(
            self.l2_engine_rpc_protocol,
            self.l2_engine_rpc_host,
            self.l2_engine_rpc_port,
            own_address=own_address)

    @l2_engine_rpc_url.setter
    def l2_engine_rpc_url(self, url: str):
        self._set_url_components(url, "l2_engine_rpc")

    @property
    def l2_engine_rpc_http_url(self, own_address: str = None):
        """
        Protocol + address + port to use to connect to the L2 *HTTP* RPC server attached to the
        execution engine ("http://127.0.0.1:9545" by default).
        Host is substituted by 127.0.0.1 if it matches `own_address`.
        """
        return self._maybe_local_url(
            "http",
            self.l2_engine_rpc_http_host,
            self.l2_engine_rpc_http_port,
            own_address=own_address)

    @l2_engine_rpc_http_url.setter
    def l2_engine_rpc_http_url(self, url: str):
        self._set_url_components(url, "l2_engine_rpc_http")

    @property
    def l2_engine_rpc_ws_url(self, own_address: str = None):
        """
        Protocol + address + port to use to connect to the L2 *WebSocket* RPC server attached to the
        execution engine ("ws://127.0.0.1:9546" by default).
        Host is substituted by 127.0.0.1 if it matches `own_address`.
        """
        return self._maybe_local_url(
            "ws",
            self.l2_engine_rpc_ws_host,
            self.l2_engine_rpc_ws_port,
            own_address=own_address)

    @l2_engine_rpc_ws_url.setter
    def l2_engine_rpc_ws_url(self, url: str):
        self._set_url_components(url, "l2_engine_rpc_ws")

    @property
    def l2_engine_authrpc_url(self, own_address: str = None):
        """
        Protocol + address + port to use to connect to the authenticated RPC (authrpc) server
        attached to the execution engine, which serves the engine API ("http://127.0.0.1:9551" by
        default). Host is substituted by 127.0.0.1 if it matches `own_address`.
        """
        return self._maybe_local_url(
            self.l2_engine_authrpc_protocol,
            self.l2_engine_authrpc_host,
            self.l2_engine_authrpc_port,
            own_address=own_address)

    @l2_engine_authrpc_url.setter
    def l2_engine_authrpc_url(self, url: str):
        self._set_url_components(url, "l2_engine_authrpc")

    @property
    def l2_node_rpc_url(self, own_address: str = None):
        """
        Address to use to connect to the op-node RPC server ("http://127.0.0.1:7545" by default).
        Host is substituted by 127.0.0.1 if it matches `own_address`.
        """
        return self._maybe_local_url(
            self.l2_node_rpc_protocol,
            self.l2_node_rpc_host,
            self.l2_node_rpc_port,
            own_address=own_address)

    @l2_node_rpc_url.setter
    def l2_node_rpc_url(self, url: str):
        self._set_url_components(url, "l2_node_rpc")

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
