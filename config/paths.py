from abc import ABC, abstractmethod
import os

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

        # ------------------------------------------------------------------------------------------
        # Deployments Parent Directory

        self.deployments_parent_dir = os.path.abspath("deployments")
        """
        Parent directory under which to place all deployment-related outputs: deployment artifacts
        (such a list of L1 addresses, genesis files, generated private keys, ...), logs, databases,
        ...
        
        The paths for the L1 and L2 engine databases can be overriden by setting the
        :py:attr:`l1_data_dir` and :py:attr:`l2_engine_data_dir` attributes.
        """

        # ------------------------------------------------------------------------------------------
        # Optimism Monorepo

        self.op_monorepo_dir = os.path.abspath("optimism")
        """The root directory of the Optimism monorepo."""

        # ------------------------------------------------------------------------------------------
        # Databases

        self.l1_data_dir = os.path.join(self.databases_dir, "devnet_l1")
        """
        Geth data directory for devnet L1 node, if deployed.
        """

        self.l2_engine_data_dir = os.path.join(self.databases_dir, "l2_engine")
        """
        Geth data directory for the L2 engine, if deployed.
        """

        # ------------------------------------------------------------------------------------------
        # Other Generated Files

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

        # ------------------------------------------------------------------------------------------
        # Logs

        self.log_l2_commands_file = os.path.join(self.logs_dir, "l2_commands.log")
        """
        Files in which the L2 components commands being run are logged.
        `{self.logs_dir}/run_config.log` by default.
    
        Use :py:method:`log_command` to write to this file.
        """

        self.logrotate_config_file = os.path.join(self.logs_dir, "logrotate.conf")
        """
        The logrotate configuration file.
        """

        self.logrotate_status_file = os.path.join(self.logs_dir, "logrotate.status")
        """
        The logrotate status file (must be specified, otherwise logrotate will use the global status
        file).
        """

        self.logrotate_tmp_file = os.path.join(self.logs_dir, "logrotate.tmp")
        """
        File used to avoid data loss when rotating logs when :py:attr:`prevent_log_data_loss` is
        true.
        """

        self.logrotate_pid_file = os.path.join(self.logs_dir, "logrotate.pid")
        """
        File used to store the PID of a temporary process when :py:attr:`prevent_log_data_loss` is
        true.
        """

    # ==============================================================================================
    # Optimism Monorepo Paths

    @property
    def op_contracts_dir(self):
        """OP stack contracts source directory."""
        return os.path.join(self.op_monorepo_dir, "packages", "contracts-bedrock")

    @property
    def op_node_dir(self):
        """op-node source directory."""
        return os.path.join(self.op_monorepo_dir, "op-node")

    @property
    def op_deploy_config_path(self):
        """
        Path (within the Optimism monrepo) at which the OP stack deployment script will look for
        the deploy configuration file. This file is also used to generated the L2 genesis, the
        devnet L1 genesis if required, and the rollup config passed to the L2 node.
        """
        return os.path.join(self.op_contracts_dir, "deploy-config", f"{self.deployment_name}.json")

    @property
    def op_deployment_artifacts_dir(self):
        """
        Returns the directory where the deployment script will place the deployment artifacts
        (list of contract addresses, ABIs & chain ID) for the L1 rollup contracts.
        """
        return os.path.join(self.op_contracts_dir, "deployments", self.deployment_name)

    @property
    def op_rollup_l1_contracts_addresses_path(self):
        """
        Returns the path to the file containing the addresses of the L1 rollup contracts.
        This file is temporary in nature: it is created by the first deployment script run (which
        deploys the contracts), and deleted by the second run (which creates the contract ABI
        files).
        """
        return os.path.join(self.op_deployment_artifacts_dir, ".deploy")

    # ==============================================================================================
    # Deployment Outputs Directories

    @property
    def deployment_dir(self):
        """
        The directory under which to place all deployment-related outputs for this deployment.
        (See :py:attr:`deployments_parent_dir` for more details.)

        This is a directory with the same name as the deployment name
        (:py:attr:`deployment_name`), placed under
        :py:attr:`deployments_parent_dir`.
        """
        return os.path.join(self.deployments_parent_dir, self.deployment_name)

    @property
    def artifacts_dir(self):
        """Directory where the deployment artifacts are stored"""
        return os.path.join(self.deployment_dir, "artifacts")

    @property
    def databases_dir(self):
        """
        Default path in which to store the various databases generated by the components (p2p
        database for the L2 node, and node database for L1 and the L2 engine).

        The paths for the L1 and L2 engine databases can be overriden by setting the
        :py:attr:`l1_data_dir` and :py:attr:`l2_engine_data_dir` attributes. The location
        of the L2 node's p2p database dir cannot be overriden.
        """
        return os.path.join(self.deployment_dir, "databases")

    @property
    def logs_dir(self):
        """Default path in which to store the various logs generated by the components."""
        return os.path.join(self.deployment_dir, "logs")

    # ==============================================================================================
    # L1 Artifacts Paths

    @property
    def l1_genesis_path(self):
        """Path to use for the devnet L1 genesis file path."""
        return os.path.join(self.artifacts_dir, "genesis-l1.json")

    @property
    def l1_allocs_path(self):
        """
        Path to use for the devnet L1 account pre-allocations filepath. This includes ETH
        pre-allocation to test accounts, and possibly the pre-deployed L2 contracts if
        :py:attribute`contracts_in_l1_genesis` is true.
        """
        return os.path.join(self.artifacts_dir, "allocs-l1.json")

    # ==============================================================================================
    # L2 Artifacts Paths

    @property
    def addresses_path(self):
        """File mapping L1 contracts to their deployed addresses."""
        return os.path.join(self.artifacts_dir, "addresses.json")

    @property
    def l2_genesis_path(self):
        """L2 genesis file path."""
        return os.path.join(self.artifacts_dir, "genesis-l2.json")

    @property
    def rollup_config_path(self):
        """L2 rollup config file path."""
        return os.path.join(self.artifacts_dir, "rollup-config.json")

    @property
    def deploy_config_path(self):
        """
        Location where the deploy config is stored.

        The file will need to be copied at :py:attr:`op_deploy_config_path` for the rollup
        contract deployment script to use it.
        """
        return os.path.join(self.artifacts_dir, "deploy-config.json")

    @property
    def abi_dir(self):
        """
        Directory where the rollup contracts ABIs are stored for stored, after
        moving them there from :py:attr:`op_deployment_artifacts_dir`.
        """
        return os.path.join(self.artifacts_dir, "abi")

    # ==============================================================================================
    # Derived Database Paths

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

    @property
    def l2_engine_chaindata_dir(self):
        """Directory storing chain data for the L2 engine."""
        return os.path.join(self.l2_engine_data_dir, "geth", "chaindata")

    # ==============================================================================================

    def log_l2_command(self, command: str):
        """
        Append the command to :py:attr:`log_l2_commands_file`, prefixing it with a separator.
        """
        lib.append_to_file(
            self.log_l2_commands_file,
            "\n################################################################################\n"
            + command)

    # ==============================================================================================

    # See also:
    # :py:attr:`log_files` in :py:class:`config.logs.LogsConfig`
    # `*_log_file` in :py:class:`config.logs.LogsConfig`

    # ==============================================================================================
