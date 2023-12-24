class L2ProposerConfig:
    """
    Configuration options related to the L2 proposer.
    """

    # ==============================================================================================

    def __init__(self):
        super().__init__()

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

    # ==============================================================================================

    # See also:
    # :py:attribute:`deployments` in :py:class:`config.network.NetworkConfig`

    # ==============================================================================================
