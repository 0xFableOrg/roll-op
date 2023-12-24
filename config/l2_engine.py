class L2EngineConfig:
    """
    Configuration options related to the L2 execution engine.
    """

    # ==============================================================================================

    def __init__(self):
        super().__init__()

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

    # ==============================================================================================

    # See also:
    # :py:attribute:`l2_chain_id` in :py:class:`config.network.NetworkConfig`
    # :py:attribute:`l2_engine_data_dir` in :py:class:`config.paths.PathConfig`
    # :py:attribute:`jwt_secret_path` in :py:class:`config.paths.PathConfig`

    # ==============================================================================================
