from .account_abstraction import AccountAbstractionConfig
from .accounts_keys import AccountsKeysConfig
from .devnet_l1 import DevnetL1Config
from .explorer import ExplorerConfig
from .governance import GovernanceConfig
from .l2_deploy import L2DeployConfig
from .l2_batcher import L2BatcherConfig
from .l2_engine import L2EngineConfig
from .l2_node import L2NodeConfig
from .l2_proposer import L2ProposerConfig
from .network import NetworkConfig
from .paths import PathsConfig


class Config(
    PathsConfig,
    AccountsKeysConfig,
    GovernanceConfig,
    DevnetL1Config,
    L2DeployConfig,
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

        self._validate_devnet_l1()

        # In the future, verify that if we deploy services to the same target, they listen on
        # different ports.

        # In the future, verify that the supplied keys match the supplied accounts.

####################################################################################################
