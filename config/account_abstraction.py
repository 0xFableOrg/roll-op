class AccountAbstractionConfig:
    """
    Configuration options related to account abstraction (4337 bundler and paymaster).
    """

    # ==============================================================================================

    def __init__(self):
        super().__init__()

        self.paymaster_initial_deposit = 3
        """
        Initial deposit amount (in Ether) for the paymaster contract.
        """

        self.paymaster_validity = 300
        """
        Time validity (in seconds) for the sponsored transaction that is signed by paymaster.
        """

        self.deploy_aa_log_file_name = "deploy_aa_contracts.log"
        """
        File name for the log file that will be created when deploying the AA contracts.
        
        It's recommended not to mess with this, it's only in the config because it's written and
        read in different locations, so it helps to maintain a single source of truth.
        """

    # ==============================================================================================

    # Also needed to run the bundler and paymster:
    # :py:attr:`aa_deployer_key` in :py:class:`config.AccountAbstractionConfig`
    # :py:attr:`bundler_key` in :py:class:`config.AccountAbstractionConfig`
    # :py:attr:`paymaster_key` in :py:class:`config.AccountAbstractionConfig`

    # ==============================================================================================
