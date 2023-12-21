import os.path
from os.path import join as pjoin


####################################################################################################

class OPPaths:
    """
    A class whose fields are paths to various directories and files, both inside the Optimism
    monorepo and inside the generated files directory (which by default is `optimism/.devnet`).
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

        self.artifacts_dir = pjoin(self.gen_dir, "artifacts")
        """cf. :py:attr:`Config.artifacts_dir`."""

        self.deploy_config_dir = pjoin(self.contracts_dir, "deploy-config")
        """
        Directory that will contain the deploy configuration files, whose name will be the
        `deployment_name` provided in the config (+ .json).
        """

        # === Generated Files — L1 Devnet ===

        self.l1_genesis_path = pjoin(self.artifacts_dir, "genesis-l1.json")
        """Devnet L1 genesis file path."""

        self.l1_allocs_path = pjoin(self.artifacts_dir, "allocs-l1.json")
        """
        Devnet L1 account pre-allocations file path. This includes ETH pre-allocation to test
        accounts, and possibly the pre-deployed L2 contracts if
        :py:attr`Config.contracts_in_l1_genesis` is true.
        """

        # === Generated Files — L2 ===

        self.deployments_parent_dir = pjoin(self.contracts_dir, "deployments")
        """
        Directory where the deployment script will place the deployment artifacts (contract
        addresses etc) for the L1 rollup contracts. If a `deployment_name` is provided in the
        :py:class:Config, it will be appended as a new path component.
        """

        self.addresses_json_path = pjoin(self.artifacts_dir, "addresses.json")
        """File mapping L1 contracts to their deployed addresses."""

        self.sdk_addresses_json_path = pjoin(self.artifacts_dir, "sdk-addresses.json")
        """L1 contract addresses for use in the Optimism SDK."""

        self.l2_genesis_path = pjoin(self.artifacts_dir, "genesis-l2.json")
        """L2 genesis file path."""

        self.rollup_config_path = pjoin(self.artifacts_dir, "rollup.json")
        """L2 rollup config file path."""

####################################################################################################
