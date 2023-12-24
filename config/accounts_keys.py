class AccountsKeysConfig:
    """
    Configuration options related to account addresses and keys to use for various roles.
    """

    # ==============================================================================================

    def __init__(self):
        super().__init__()

        self.contract_deployer_account = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
        """
        Account used to deploy contracts to L1.
        """

        self.contract_deployer_key = \
            "ac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
        """
        Private key used to deploy contracts to L1.
        Uses the 0th "test junk" mnemonnic key by default.
        """

        self.batcher_account = "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"
        """
        Account used to submit batches.
        By default, uses the 2nd (0-based!) "test junk" mnemonic account.
        """

        self.batcher_key = None
        """
        Private key used to submit batches.
        Will be used if set, otherwise a mnemonic + HD derivation path will be used.
        """

        self.batcher_mnemonic = "test test test test test test test test test test test junk"
        """
        Mnemonic to use to derive the batcher key (Anvil "test junk" account mnemonic by default).
        Ignored if :py:attribute:`batcher_key` is set.
        """

        self.batcher_hd_path = "m/44'/60'/0'/0/2"
        """
        HD derivation path to use to derive the batcher key.
        Uses the 2nd (0-based!) "test junk" mnemonnic key by default.
        Ignored if :py:attribute:`proposer_key` is set.
        """

        self.proposer_account = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
        """
        Account used to propose output roots
        By default, uses the 0th "test junk" mnemonic account.
        """

        self.proposer_key = None
        """
        Private key used to propose output roots.
        Will be used if set, otherwise a mnemonic + HD derivation path will be used.
        """

        self.proposer_mnemonic = "test test test test test test test test test test test junk"
        """
        Mnemonic to use to derive the proposer key (Anvil "test junk" account mnemonic by default).
        Ignored if :py:attribute:`proposer_key` is set.
        """

        self.proposer_hd_path = "m/44'/60'/0'/0/1"
        """
        HD derivation path to use to derive the proposer key.
        Uses the 1th (0-based!) "test junk" mnemonnic key by default.
        Ignored if :py:attribute:`proposer_key` is set.
        """

        self.p2p_sequencer_account = "0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc"
        """
        If provided, account used by the sequencer to sign blocks gossiped over p2p.
        Uses the 5th (0-based!) "test junk" mnemonic account by default.
        """

        self.p2p_sequencer_key = "8b3a350cf5c34c9194ca85829a2df0ec3153be0318b5e2d3348e872092edffba"
        """
        If provided (not None), private key used by the sequencer to sign blocks gossiped over p2p.
        Uses the 5th (0-based!) "test junk" mnemonic key by default.
        Do not prefix the key with 0x.
        """

        self.admin_account = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
        """
        Account used for various roles in the rollup system:
        - It owns all the contracts that have an owner.
        - It takes on all the privileged roles in the system.
            - challenger for the (yet to be implemented) fault proof
            - final system owner, portal guardian, and controller
                - TODO: figure out what these do
        - It is the recipient for all fees (basefees, l1 fees, sequencer fees).
        
        By default, uses the 0th "test junk" account.
        
        Later, we should split this to granular roles.
        """

        self.admin_key = "ac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
        """
        Private key corresponding to :py:attribute:`admin_account`, see its documentation for
        more details.
        By default, uses the 0th "test junk" account key.
        Do not prefix the key with 0x.
        """

        self.l1_signer_account = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
        """Address of the devnet L1 block signer."""

        self.l1_signer_private_key = \
            "ac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
        """Private key of the devnet L1 block signer."""

    # ==============================================================================================