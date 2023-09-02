import os.path
from os.path import join as pjoin


####################################################################################################

class OPPaths:
    """
    A class whose fields are paths to various directories and files within the OP monorepo.
    """

    def __init__(self, monorepo_dir="optimism", gen_dir=pjoin("optimism", ".devnet")):
        # === Source Directories ===

        self.monorepo_dir = os.path.abspath(monorepo_dir)
        """The root directory of the monorepo."""

        self.contracts_dir = pjoin(self.monorepo_dir, "packages", "contracts-bedrock")
        """OP stack contracts source directory."""

        self.op_node_dir = pjoin(self.monorepo_dir, "op-node")
        """OP node source directory."""

        self.ops_bedrock_dir = pjoin(self.monorepo_dir, "ops-bedrock")
        """ops-bedrock directory, used for docker files & config."""

        # === Existing Files ===

        self.network_config_template_path = pjoin(
            self.contracts_dir, "deploy-config", "devnetL1.json.tmpl")
        """Template for the network configuration file."""
        # Note: this was added compared to the original Optimism logic, which edited the
        # devnetL1.json file in place. Instead, we create this template from the original the first
        # time we run the script (when it does not exist), and then use it a source to be modified
        # ever after.

        self.network_config_template_path_source = pjoin(
            self.contracts_dir, "deploy-config", "devnetL1.json")
        """
        The source to create the network config template path from if it doesn't exist yet.
        """

        self.p2p_key_path = pjoin(self.ops_bedrock_dir, "p2p-node-key.txt")
        """
        Paths to a file containing a private key used for the peer identity for the L2 node.
        The origin of this key is unclear (it's not one of the ten "test junk" keys).FF
        """

        self.jwt_test_secret_path = pjoin(self.ops_bedrock_dir, "test-jwt-secret.txt")
        """
        Path to a file containing a TEST Jason Web Token secret used for the l2 node to communicate
        with the execution engine. Not secure in production.
        """

        # === Generated Files ===

        self.gen_dir = os.path.abspath(gen_dir)
        """Output directory for generated files."""

        self.network_config_dir = pjoin(self.contracts_dir, "deploy-config")
        """Directory that will contain the network configuration files, whose name will be the
        `deployment_name` provided in the config (+ .json).
        """

        # === Generated Files — L1 Devnet ===

        self.l1_genesis_path = pjoin(self.gen_dir, "genesis-l1.json")
        """Devnet L1 genesis file path."""

        # === Generated Files — L2 ===

        self.deployments_dir = pjoin(self.contracts_dir, "deployments")
        """
        Directory where the deployment script will place the deployment artifacts (contract
        addresses etc) for the L1 rollup contracts. If a `deployment_name` is provided in the
        L2Config, it will be appended as a new path component.
        """

        # self.deployment_dir = pjoin(self.contracts_dir, "deployments", "devnetL1")
        # """Directory to move the L1 rollup contracts deployment artifacts (contract addresses etc)
        # to, for safe keeping."""

        self.addresses_json_path = pjoin(self.gen_dir, "addresses.json")
        """File mapping L1 contracts to their deployed addresses."""

        self.sdk_addresses_json_path = pjoin(self.gen_dir, "sdk-addresses.json")
        """L1 contract addresses for use in the Optimism SDK."""

        self.l2_genesis_path = pjoin(self.gen_dir, "genesis-l2.json")
        """L2 genesis file path."""

        self.rollup_config_path = pjoin(self.gen_dir, "rollup.json")
        """L2 rollup config file path."""

####################################################################################################
