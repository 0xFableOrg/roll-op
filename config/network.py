import libroll as lib


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

        # See :py:attr:`l1_rpc_url` for more details.
        self.l1_rpc_protocol = "http"
        self.l1_rpc_host = "127.0.0.1"
        self.l1_rpc_path = ""
        self.l1_rpc_port = 8545

        # See :py:attr:`l1_rpc_for_node_url` for more details.
        self.l1_rpc_for_node_protocol = "ws"
        self.l1_rpc_for_node_host = "127.0.0.1"
        self.l1_rpc_for_node_path = ""
        self.l1_rpc_for_node_port = 8546

        # See :py:attr:`l2_engine_rpc_http_url` for more details.
        self.l2_engine_rpc_http_host = "127.0.0.1"
        self.l2_engine_rpc_http_port = 9545

        # See :py:attr:`l2_engine_rpc_ws_url` for more details.
        self.l2_engine_rpc_ws_host = "127.0.0.1"
        self.l2_engine_rpc_ws_port = 9546

        # See :py:attr:`l2_engine_rpc_url` for more details.
        self.l2_engine_rpc_protocol = "http"
        self.l2_engine_rpc_host = self.l2_engine_rpc_http_host
        self.l2_engine_rpc_port = self.l2_engine_rpc_http_port

        # See :py:attr:`l2_engine_authrpc_url` for more details.
        self.l2_engine_authrpc_protocol = "http"
        self.l2_engine_authrpc_host = "127.0.0.1"
        self.l2_engine_authrpc_port = 9551

        # See :py:attr:`l2_node_rpc_url` for more details.
        self.l2_node_rpc_protocol = "http"
        self.l2_node_rpc_host = "127.0.0.1"
        self.l2_node_rpc_port = 7545

        self.batch_inbox_address = "0xff69000000000000000000000000001201101712"
        """
        Address of the batch inbox contract on L1.
        
        By default, this is the result of taking the 0xff69000000000000000000000000000000000000
        address and replacing up to 10 of its last digits
        with the chain id. So the batch inbox address for
        the default chain id is 0xff69000000000000000000000000001201101712.
        
        (The logic that performs this computation in case the L2 chain id is overriden by the config
        file is in `load_config` in `roll.py`.)
        """

        self.deployments = None
        """
        Dictionary containing a mapping from rollup contract names to the address at which they're
        deployed on L1. None before initialization.
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

    # ----------------------------------------------------------------------------------------------

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

    # ==============================================================================================

    @property
    def l1_rpc_url(self, own_address: str = None):
        """
        Protocol + address + port to use to connect to the L1 RPC server
        ("http://127.0.0.1:8545" by default).
        Host is substituted by 127.0.0.1 if it matches `own_address`.

        The L2 node will use :py:attr:`l1_rpc_for_node` instead!
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

    # ----------------------------------------------------------------------------------------------

    @property
    def l1_rpc_for_node_url(self, own_address: str = None):
        """
        Protocol + address + port for use *by the L2 node* to connect to the L1 RPC server
        ("ws://127.0.0.1:8546" by default).

        The reason for this override is to enable the L2 node to use a more performant RPC, or a
        WebSocket connection to get L1 data.

        If the config file doesn't set this but set :py:attr:`l1_rpc_url` instead, roll-op
        will automatically copy the value of :py:attr:`l1_rpc_url` to this property.
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

    # ----------------------------------------------------------------------------------------------

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

    # ----------------------------------------------------------------------------------------------

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

    # ----------------------------------------------------------------------------------------------

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

    # ----------------------------------------------------------------------------------------------

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

    # ----------------------------------------------------------------------------------------------

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
