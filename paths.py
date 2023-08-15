import os.path
from os.path import join as pjoin


####################################################################################################

class OPPaths:
    """
    A class whose fields are paths to various directories and files within the OP monorepo.
    """

    def __init__(self, monorepo_dir):
        # === Source Directories ===

        self.monorepo_dir = os.path.abspath(monorepo_dir)
        """The root directory of the monorepo."""

        self.contracts_dir = pjoin(self.monorepo_dir, "packages", "contracts-bedrock")
        """OP stack contracts source directory."""

        self.op_node_dir = pjoin(self.monorepo_dir, "op-node")
        """OP node source directory."""

        self.ops_bedrock_dir = pjoin(self.monorepo_dir, "ops-bedrock")
        """ops-bedrock directory, used for docker files & config."""

        # === Existing Configuration ===

        self.devnet_config_template_path = pjoin(
            self.contracts_dir, "deploy-config", "devnetL1.json.tmpl")
        """Template for devnet L1 configuration file."""
        # Note: this was added compared to the original Optimism logic, which edited the
        # devnetL1.json file in place. Instead, we create this template from the original the first
        # time we run the script (when it does not exist), and then use it a source to be modified
        # ever after.

        # === Generated Files — L1 Devnet ===

        self.l1_devnet_config_path = pjoin(self.contracts_dir, "deploy-config", "devnetL1.json")
        """Configuration file for devnet L1 within the deploy config dir."""

        self.l1_devnet_dir = pjoin(self.monorepo_dir, ".devnet")
        """Output directory for generated configuration files for the L1 devnet."""

        self.l1_genesis_path = pjoin(self.l1_devnet_dir, "genesis-l1.json")
        """L1 devnet genesis file path."""

        self.l1_devnet_deployment_dir = pjoin(self.contracts_dir, "deployments", "devnetL1")
        """Directory to store L1 devnet deployment artifacts (addresses, etc.)."""

        # === Generated Files — L1 ===

        self.addresses_json_path = pjoin(self.l1_devnet_dir, "addresses.json")
        """File mapping L1 contracts to their deployed addresses."""

        self.sdk_addresses_json_path = pjoin(self.l1_devnet_dir, "sdk-addresses.json")
        """L1 contract addresses for use in the Optimism SDK."""

####################################################################################################
