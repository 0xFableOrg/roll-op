from abc import ABC, abstractmethod
import os

from paths import OPPaths
import libroll as lib


class PathsConfig(ABC):
    """
    Configuration options related to filesystem paths.
    """

    # ==============================================================================================
    # Required Properties

    @property
    @abstractmethod
    def deployment_name(self):
        pass

    # ==============================================================================================

    def __init__(self):
        super().__init__()

        self.deployments_parent_dir = os.path.abspath("deployments")
        """
        Parent directory under which to place all deployment-related outputs: deployment artifacts
        (such a list of L1 addresses, genesis files, generated private keys, ...), logs, databases,
        ...
        
        The paths for the L1 and L2 engine databases can be overriden by setting the
        :py:attribute:`l1_data_dir` and :py:attribute:`l2_engine_data_dir` attributes.
        """

        self.paths = OPPaths(gen_dir=self.deployment_dir)
        """
        This object is a registry of paths into the optimism directory that we need to build &
        deploy op-stack rollups.
        """

        self.l1_data_dir = os.path.join(self.databases_dir, "devnet_l1")
        """
        Geth data directory for devnet L1 node, if deployed.
        """

        self.l2_engine_data_dir = os.path.join(self.databases_dir, "l2_engine")
        """
        Geth data directory for the L2 engine, if deployed.
        """

        self.log_run_config_file = os.path.join(self.artifacts_dir, "run_config.log")
        """
        Files in which the commands being run and generated config files are logged.
        `{self.artifacts_dir}/run_config.log` by default.
    
        Use :py:method:`log_run_config` to write to this file.
        """

        self.jwt_secret_path = os.path.join(self.artifacts_dir, "jwt-secret.txt")
        """
        Path to the Jason Web Token secret file, which enable the L2 node to communicate with the
        execution engine. Will be generated if it does not already exist.
        
        Uses `{self.artifacts_dir}/jwt-secret.txt` by default.
        
        This is also passed to the devnet L1 (if started) currently, but unclear if it's needed.
        """

        self.p2p_peer_key_path = os.path.join(self.artifacts_dir, "opnode_p2p_priv.txt")
        """
        Path to the hex-encoded 32-byte private key for the peer ID of the L2 node. Will be created
        if it does not already exist.
        
        It's important to persist to keep the same network identity after restarting, maintaining
        the previous advertised identity.
        
        This is different than the sequencer key (which is only used by the sequencer).
        
        Uses `{self.artifacts_dir}/opnode_p2p_priv.txt` by default.
        """

    # ==============================================================================================

    @property
    def deploy_config_path(self):
        """
        Returns the path to the deploy configuration file. This file to the deploy script, and also
        used to generated the L2 genesis, the devnet L1 genesis if required, and the rollup config
        passed to the L2 node.
        """
        return os.path.join(self.paths.deploy_config_dir, f"{self.deployment_name}.json")

    # ----------------------------------------------------------------------------------------------

    @property
    def deployment_artifacts_gen_dir(self):
        """
        Returns the directory where the deployment script will place the deployment artifacts
        (contract addresses etc) for the L1 rollup contracts.
        """
        return os.path.join(self.paths.deployments_parent_dir, self.deployment_name)

    # ----------------------------------------------------------------------------------------------

    @property
    def deployment_dir(self):
        """
        The directory under which to place all deployment-related outputs for this deployment.
        (See :py:attribute:`deployments_parent_dir` for more details.)

        This is a directory with the same name as the deployment name
        (:py:attribute:`deployment_name`), placed under
        :py:attribute:`deployments_parent_dir`.
        """
        return f"{self.deployments_parent_dir}/{self.deployment_name}"

    # ----------------------------------------------------------------------------------------------

    @property
    def artifacts_dir(self):
        """
        Directory where the deployment artifacts are stored
        """
        return os.path.join(self.deployment_dir, "artifacts")

    # ----------------------------------------------------------------------------------------------

    @property
    def databases_dir(self):
        """
        Default path in which to store the various databases generated by the components (p2p
        database for the L2 node, and node database for L1 and the L2 engine).

        The paths for the L1 and L2 engine databases can be overriden by setting the
        :py:attribute:`l1_data_dir` and :py:attribute:`l2_engine_data_dir` attributes. The location
        of the L2 node's p2p database dir cannot be overriden.
        """
        return os.path.join(self.deployment_dir, "databases")

    # ----------------------------------------------------------------------------------------------

    @property
    def logs_dir(self):
        """
        Default path in which to store the various logs generated by the components.
        """
        return os.path.join(self.deployment_dir, "logs")

    # ----------------------------------------------------------------------------------------------

    @property
    def l1_keystore_dir(self):
        """Keystore directory for devnet L1 node (each file stores an encrypted signer key)."""
        return os.path.join(self.l1_data_dir, "keystore")

    @property
    def l1_chaindata_dir(self):
        """Directory storing chain data."""
        return os.path.join(self.l1_data_dir, "geth", "chaindata")

    @property
    def l1_password_path(self):
        """Path to file storing the password for the signer key."""
        return os.path.join(self.l1_data_dir, "password")

    @property
    def l1_tmp_signer_key_path(self):
        """Path to file storing the signer key during the initial import."""
        return os.path.join(self.l1_data_dir, "block-signer-key")

    # ----------------------------------------------------------------------------------------------

    @property
    def l2_engine_chaindata_dir(self):
        """Directory storing chain data for the L2 engine."""
        return os.path.join(self.l2_engine_data_dir, "geth", "chaindata")

    # ==============================================================================================

    def log_run_config(self, text: str):
        """
        Append the text to :py:attribute:`log_run_config_file`, prefixing it with a separator.
        This should be used to log run commands and generated configuration files.
        """
        lib.append_to_file(
            self.log_run_config_file,
            "\n################################################################################\n"
            + text)

    # ==============================================================================================