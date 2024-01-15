class L2BatcherConfig:
    """
    Configuration options related to the L2 batcher.
    """

    # ==============================================================================================

    def __init__(self):
        super().__init__()

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
        Ignored if :py:attr:`batcher_metrics` is False.
        """

        self.batcher_metrics_listen_addr = "0.0.0.0"
        """
        Address the batcher metrics server should bind to ("0.0.0.0" by default).
        Ignored if :py:attr:`batcher_metrics` is False.
        """

    # ==============================================================================================

    # Also needed to configure the L2 batcher:
    # :py:attr:`l1_rpc_url` in :py:class:`config.NetworkConfig`
    # :py:attr:`l2_engine_rpc_url` in :py:class:`config.NetworkConfig`
    # :py:attr:`l2_node_rpc_url` in :py:class:`config.NetworkConfig`

    # ==============================================================================================
