class GovernanceConfig:
    """
    Configuration options related to governance.
    """

    # ==============================================================================================

    def __init__(self):
        super().__init__()

        self.enable_governance = False
        """
        Whether to deploy a governance token (False by default).
        """

        self.governance_token_symbol = "STONK"
        """
        If :py:attribute:`enable_governance` is True, the symbol of the governance token to deploy.
        """

        self.governance_token_name = "Simple Token Op-chain Network Koin"
        """
        If :py:attribute:`enable_governance` is True, the name of the governance token to deploy.
        """

    # ==============================================================================================
