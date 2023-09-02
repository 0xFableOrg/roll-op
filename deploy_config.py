DEPLOY_CONFIG = {
    "l1ChainID": "REPLACE THIS",
    "l2ChainID": "REPLACE THIS",

    "p2pSequencerAddress": "REPLACE THIS (SEQUENCER)",
    "batchInboxAddress": "REPLACE_THIS (BATCHER)",
    "batchSenderAddress": "REPLACE_THIS (PROPOSER)",

    "l2OutputOracleProposer": "REPLACE THIS (PROPOSER)",
    "l2OutputOracleChallenger": "REPLACE THIS (ADMIN)",

    "proxyAdminOwner": "REPLACE THIS (ADMIN)",
    "baseFeeVaultRecipient": "REPLACE THIS (ADMIN)",
    "l1FeeVaultRecipient": "REPLACE THIS (ADMIN)",
    "sequencerFeeVaultRecipient": "REPLACE THIS (ADMIN)",
    "finalSystemOwner": "REPLACE_THIS (ADMIN)",
    "portalGuardian": "REPLACE_THIS (ADMIN)",
    "controller": "REPLACE_THIS (ADMIN)",

    "l2BlockTime": 2,
    "maxSequencerDrift": 600,
    "sequencerWindowSize": 3600,
    "channelTimeout": 300,
    "finalizationPeriodSeconds": 12,

    "l2OutputOracleSubmissionInterval": 120,
    "l2OutputOracleStartingBlockNumber": 0,

    "l1StartingBlockTag": "REPLACE THIS (BLOCKHASH or TAG)",

    # Setting this to negative value causes the deploy script to use l1StartingBlockTag's timestamp.
    "l2OutputOracleStartingTimestamp": -1,

    "l2GenesisBlockGasLimit": "0x1c9c380",
    "l2GenesisBlockBaseFeePerGas": "0x3b9aca00",
    "l2GenesisRegolithTimeOffset": "0x0",

    "baseFeeVaultMinimumWithdrawalAmount": "0x8ac7230489e80000",
    "l1FeeVaultMinimumWithdrawalAmount": "0x8ac7230489e80000",
    "sequencerFeeVaultMinimumWithdrawalAmount": "0x8ac7230489e80000",
    "baseFeeVaultWithdrawalNetwork": 0,
    "l1FeeVaultWithdrawalNetwork": 0,
    "sequencerFeeVaultWithdrawalNetwork": 0,

    "gasPriceOracleOverhead": 2100,
    "gasPriceOracleScalar": 1000000,

    "enableGovernance": True,
    "governanceTokenSymbol": "REPLACE THIS",
    "governanceTokenName": "REPLACE THIS",
    "governanceTokenOwner": "REPLACE THIS (ADMIN)",

    "eip1559Denominator": 50,
    "eip1559Elasticity": 10,

    # NOTE: The devnetL1.json deploy config includes additional fields, which are relevant for
    #       deploying a devnet L1 chain. However, these are not even used by the Optimism repo
    #       at the commit we're using (not sure about later). Here is the list

    # "l1BlockTime": 3,
    # "cliqueSignerAddress": "0xca062b0fd91172d89bcd4bb084ac4e21972cc467",
    # "fundDevAccounts": True,
    # "l1GenesisBlockTimestamp": "0x64f34f83"
}
