class DevnetL1Config:
    """
    Configuration options related to the devnet L1 node.
    """

    # ==============================================================================================

    def __init__(self):
        super().__init__()

        self.run_devnet_l1 = True
        """
        When using the "devnet" command, whether to run a local L1 chain (True by default).
        If false, it means deploying on an existing L1 blockchain, specified by
        :py:attr:`l1_rpc`.
        
        Note that you can/should stil set :py:attr:`l1_rpc` when this is True, if you want to
        deploy the the devnet L1 on another IP or port.
        """

        # Any attribute defined in this section are only meaningful (used) if
        # :py:attr:`deploy_devnet_l1` is True!

        self.l1_contracts_in_genesis = True
        """
        Whether to include the L2 contracts in the genesis state of the devnet L1 (True by default).
        
        (Currently, only True is supported, as the OP monorepo L1 genesis file creation script does
        not support this options. We will implement this on our own in the future.)
        
        This saves time when running multiple devnets in succession, as there is no need to redeploy
        the contracts every time. The Optimism monorepo does this to speed up testing.
        
        To create the genesis file, a temporary L1 node is started, the contracts are deployed to it,
        and then dumped to the genesis file.
        """

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
        Ignored if :py:attr:`l1_metrics` is False.
        """

        self.l1_metrics_listen_addr = "0.0.0.0"
        """
        Address the L1 node metrics server should bind to ("0.0.0.0" by default).
        Ignored if :py:attr:`l1_metrics` is False.
        """

    # ==============================================================================================

    # See also:
    # :py:attr:`l1_chain_id` in :py:class:`config.network.NetworkConfig`
    # :py:attr:`l1_data_dir` in :py:class:`config.paths.PathConfig`

    # ==============================================================================================

    def _validate_devnet_l1(self):
        if not self.l1_contracts_in_genesis:
            raise NotImplementedError("Only l1_contracts_in_genesis=True is currently supported.")

    # ==============================================================================================
