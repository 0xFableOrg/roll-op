class NetworkConfig:
    """
    Configuration options related to the global L2 network setup.

    This includes chain IDs, contract deployment addresses on the L1, as well as the network
    addresses at which services (L2 node, L2 engine, etc...) can reach the other services.

    This is not to be confused with the configuration of each individual service, which must specify
    on which port/address they listen.

    For instance, the L2 engine might listen on 0.0.0.0:9545 (listen on the port 9545 on all network
    interfaces), but the L2 node might need to reach it at 127.0.0.42:8545 (local address of the
    machine + port remapping).
    """

    # ==============================================================================================

    def __init__(self):
        super().__init__()

        self.l1_chain_id = 1201101711
        """
        Chain ID of the L1 to use. If spinning an L1 devnet, it will use this chain ID.
        Defaults to 1201101711 — 'rollop L1' in 1337 speak.
        """

        self.l2_chain_id = 1201101712
        """Chain ID of the local L2 (default: 1201101712 — 'rollop L2' in 1337 speak)."""

        self.own_address = "127.0.0.1"
        """
        Remote address of the local machine. This is used to determine if multiple components are
        running on the same machine, so they might reach each other via 127.0.0.1 instead of going
        out to the internet and then back into them machine.
        (Defaults to "127.0.0.1" — assuming a local-only setup.)
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

        self.batch_inbox_address = "0xff00000000000000000000000000000000000000"
        """
        Address of the batch inbox contract on L1. (0xff00000000000000000000000000000000000000 by
        default).
        """

        self.deployments = None
        """
        Dictionary containing a mapping from rollup contract names to the address at which they're
        deployed on L1. None before initialization.
        """

    # ==============================================================================================