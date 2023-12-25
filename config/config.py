import os.path

from .account_abstraction import AccountAbstractionConfig
from .accounts_keys import AccountsKeysConfig
from .devnet_l1 import DevnetL1Config
from .explorer import ExplorerConfig
from .governance import GovernanceConfig
from .l1_contracts_deploy import L1ContractsDeployConfig
from .l2_batcher import L2BatcherConfig
from .l2_engine import L2EngineConfig
from .l2_node import L2NodeConfig
from .l2_proposer import L2ProposerConfig
from .network import NetworkConfig
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
#
# We do not enable the pprof server in any config, but it listens on the 6060 port by default.
#
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
    GovernanceConfig,
    DevnetL1Config,
    L1ContractsDeployConfig,
    NetworkConfig,
    L2NodeConfig,
    L2EngineConfig,
    L2ProposerConfig,
    L2BatcherConfig,
    ExplorerConfig,
    AccountAbstractionConfig
):

    # ==========================================================================================
    # Ensure abstract properties are "implemented".

    deployment_name = None

    # ==========================================================================================

    def __init__(self, deployment_name: str = "rollup"):

        self.deployment_name = deployment_name
        """
        Name for the rollup deployment, this will be set as the `DEPLOYMENT_CONTEXT` environment
        variable during contract deployment to L1, to determine the directory where the deploy
        script will put the deployment artifacts.
        """
        # NOTE: setting this variable is not required for chains "known" by the optimism repo deploy
        # script, but required for other chains to put the deployment artifacts in their own
        # directory.

        super().__init__()

    # ==============================================================================================

    def validate(self):
        """
        Check the validity of the configuration. This raises an error if the config is invalid or
        inconsistent.
        """
        if not isinstance(self.deployment_name, str) or self.deployment_name == "":
            raise ValueError("deployment_name must be a non-empty string")

        # In the future, verify that if we deploy services to the same target, they listen on
        # different ports.

        # In the future, verify that the supplied keys match the supplied accounts.

####################################################################################################
