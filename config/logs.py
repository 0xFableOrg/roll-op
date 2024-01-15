import os


# noinspection PyUnresolvedReferences
class LogsConfig:
    """
    Configuration options related to log files.
    """

    # ==============================================================================================

    def __init__(self):
        super().__init__()

        # ------------------------------------------------------------------------------------------
        # File Names

        self.l1_node_log_filename = "l1_node.log"
        """
        Filename (not path!) for the log file of the L1 node.
        """

        self.l2_node_log_filename = "l2_node.log"
        """
        Filename (not path!) for the log file of the L2 node.
        """

        self.l2_engine_log_filename = "l2_engine.log"
        """
        Filename (not path!) for the log file of the L2 engine.
        """

        self.l2_batcher_log_filename = "l2_batcher.log"
        """
        Filename (not path!) for the log file of the L2 batcher.
        """

        self.l2_proposer_log_filename = "l2_proposer.log"
        """
        Filename (not path!) for the log file of the L2 proposer.
        """

        self.blockscout_log_filename = "launch_blockscout.log"
        """
        Filename (not path!) for the global log file for the blockscout services.
        """

        self.paymaster_log_filename = "paymaster.log"
        """
        Filename (not path!) for the log file of the paymaster.
        """

        self.stackup_bundler_log_filename = "stackup_bundler.log"
        """
        Filename (not path!) for the log file of the stackup bundler.
        """

        # ------------------------------------------------------------------------------------------
        # Logrotate

        self.logrotate_period = 10
        """
        Time in seconds between logrotate runs. 10 by default.
        """

        self.logrotate_max_size = "3M"
        """
        Maximum size of a log file before it is rotated, as a string with units (k/M/G).
        3M by default.
        """

        self.logrotate_count = 300
        """
        Maximum number of times to rotate the log file before deleting old log files.
        The max filesize usage for a log file is approximately this number times
        :py:attr:`logrotate_max_size`. 300 by default.
        """

        self.logrotate_max_days = 14
        """
        Maximum number of days to keep old log files arounds, even if the maximum number of
        rotations hasn't been reached. 14 by default.
        """

    # ==============================================================================================

    @property
    def l1_node_log_file(self):
        return os.path.join(self.logs_dir, self.l1_node_log_filename)

    @property
    def l2_node_log_file(self):
        return os.path.join(self.logs_dir, self.l2_node_log_filename)

    @property
    def l2_engine_log_file(self):
        return os.path.join(self.logs_dir, self.l2_engine_log_filename)

    @property
    def l2_batcher_log_file(self):
        return os.path.join(self.logs_dir, self.l2_batcher_log_filename)

    @property
    def l2_proposer_log_file(self):
        return os.path.join(self.logs_dir, self.l2_proposer_log_filename)

    @property
    def blockscout_log_file(self):
        return os.path.join(self.logs_dir, self.blockscout_log_filename)

    @property
    def paymaster_log_file(self):
        return os.path.join(self.logs_dir, self.paymaster_log_filename)

    @property
    def stackup_bundler_log_file(self):
        return os.path.join(self.logs_dir, self.stackup_bundler_log_filename)

    @property
    def rotating_log_files(self):
        """
        List of all the log files that should be rotated
        (these should be all log files of long-running services).
        """
        return [
            self.l1_node_log_file,
            self.l2_node_log_file,
            self.l2_engine_log_file,
            self.l2_batcher_log_file,
            self.l2_proposer_log_file,
            self.blockscout_log_file,
            self.paymaster_log_file,
            self.stackup_bundler_log_file,
        ]

    # ----------------------------------------------------------------------------------------------

    @property
    def logrotate_old_dir(self):
        """
        The directory where rotated log files are moved to.
        """
        return os.path.join(self.logs_dir, "old")

    # ==============================================================================================

    # See also:
    # :py:attr:`logrotate_config_file` in :py:class:`config.paths.PathsConfig`
    # :py:attr:`logrotate_tmp_file` in :py:class:`config.paths.PathsConfig`
    # :py:attr:`logrotate_pid_file` in :py:class:`config.paths.PathsConfig`

    # ==============================================================================================
