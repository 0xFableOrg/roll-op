class AccountAbstractionConfig:
    """
    Configuration options related to account abstraction (4337 bundler and paymaster).
    """

    # ==============================================================================================

    def __init__(self):
        super().__init__()

        self.aa_deployer_key = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
        """
        Private key to use for deploying 4337 contracts.
        Uses the 0th "test junk" mnemonnic key by default.
        """

        self.bundler_key = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
        """
        Private key to use for submitting bundled transactions.
        Uses the 0th "test junk" mnemonnic key by default.
        """

        self.paymaster_key = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
        """
        Private key to use as paymaster signer.
        Uses the 0th "test junk" mnemonnic key by default.
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
