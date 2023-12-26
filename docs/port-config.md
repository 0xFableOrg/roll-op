# Port Configuration

Each service must listen to some ports. This is configured in roll-op's config in two ways:

- Listen ports for each service (in its own `Config` superclass, e.g. [`L2NodeConfig`])
- Public port a which a service can reach another one, in the [`NetworkConfig`] superclass, e.g.
  `l2_node_rpc_port`.

[`L2NodeConfig`]: ../config/l2_node.py
[`NetworkConfig`]: ../config/network.py

If you do not use port mapping, then the listen port will always match the public port.

TODO: You can signal this by setting the `allow_port_mapping` option to `False` in the config, which
is the default. In this case, roll-op will check that the listen and public ports match. It will
also do so if a service is reachable at "127.0.0.1" (localhost).

This document summarizes the default port assignments, as well as the port assignments used in
additional [example configs].

[example configs]: ../config/examples.py

## Default Port Assigment

The default port mapping uses the same port as the devnet configuration in the Optimism monorepo,
whenever possible.

- L1 http RPC: 8545
- L1 WebSocket RPC: 8546
- L1 authRPC: 8551 (authenticated APIs)
- L1 p2p: 30303 (block & tx gossip — geth default, not configured in devnet)
- L1 metrics: 7060
- L2 engine http RPC: 9545 (like L1 http RPC but for L2)
- L2 engine Websocket RPC: 9546 (like L1 Websocket RPC but for L2)
- L2 engine authRPC: 9551 (like L1 authRPC but for L2 — op-node <> engine communication)
- L2 engine p2p: 30313 (like L1 p2p but for L2 — not configured in devnet)
- L2 engine metrics: 8060
- L2 node RPC: 7545 (optimism_ and admin_ namespaces)
- L2 node metrics: 7300
- L2 proposer RPC: 5545 (no namespaces)
- L2 proposer metrics: 7302
- L2 batcher RPC: 6545 (admin_ namespace)
- L2 batcher metrics: 7301

We do not enable the pprof server in any config, but it listens on the 6060 port by default.

# OP Doc Port Assigment

When following [the OP stack "Getting Started" guide][getting-started], the following ports are used:
(The L1 and L2 engine ports are inverted, and the other components are numbered differently.)

[getting-started]: https://stack.optimism.io/docs/build/getting-started

- L1 http RPC: 9545
- L1 WebSocket RPC: 9546
- L1 authRPC: 9551 (authenticated APIs)
- L1 p2p: 30313 (block & tx gossip)
- L2 engine http RPC: 8545
- L2 engine Websocket RPC: 8546 (like L1 Websocket RPC but for L2)
- L2 engine authRPC: 8551
- L2 engine p2p: 9003
- L2 node RPC: 8547
- L2 proposer RPC: 8560 (no namespaces)
- L2 batcher RPC: 8548 (admin_ namespace)

The guide does not configure metrics, so the defaults from the previous section are used.