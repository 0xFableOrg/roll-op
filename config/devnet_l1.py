class DevnetL1Config:
    """
    Configuration options related to the devnet L1 node.
    """

    # ==============================================================================================

    def __init__(self):
        super().__init__()

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

    # ==============================================================================================

    # See also:
    # :py:attribute:`l1_chain_id` in :py:class:`config.network.NetworkConfig`
    # :py:attribute:`l1_data_dir` in :py:class:`config.paths.PathConfig`

    # ==============================================================================================
