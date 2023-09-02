PRODUCTION_CONFIG = {
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

DEVNET_CONFIG = {
    # Copied directly from patched devnetL1.json
    # TODO test this works
    # TODO reformat to look like production config
    "l1ChainID": 900,
    "l2ChainID": 42069,
    "l2BlockTime": 2,
    "maxSequencerDrift": 300,
    "sequencerWindowSize": 200,
    "channelTimeout": 120,
    "p2pSequencerAddress": "0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc",
    "batchInboxAddress": "0xff00000000000000000000000000000000000000",
    "batchSenderAddress": "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
    "l2OutputOracleSubmissionInterval": 20,
    "l2OutputOracleStartingTimestamp": -1,
    "l2OutputOracleStartingBlockNumber": 0,
    "l2OutputOracleProposer": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
    "l2OutputOracleChallenger": "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65",
    "l2GenesisBlockGasLimit": "0x1c9c380",
    "l1BlockTime": 3,
    "cliqueSignerAddress": "0xca062b0fd91172d89bcd4bb084ac4e21972cc467",
    "baseFeeVaultRecipient": "0xBcd4042DE499D14e55001CcbB24a551F3b954096",
    "l1FeeVaultRecipient": "0x71bE63f3384f5fb98995898A86B02Fb2426c5788",
    "sequencerFeeVaultRecipient": "0xfabb0ac9d68b0b445fb7357272ff202c5651694a",
    "baseFeeVaultMinimumWithdrawalAmount": "0x8ac7230489e80000",
    "l1FeeVaultMinimumWithdrawalAmount": "0x8ac7230489e80000",
    "sequencerFeeVaultMinimumWithdrawalAmount": "0x8ac7230489e80000",
    "baseFeeVaultWithdrawalNetwork": 0,
    "l1FeeVaultWithdrawalNetwork": 0,
    "sequencerFeeVaultWithdrawalNetwork": 0,
    "proxyAdminOwner": "0xBcd4042DE499D14e55001CcbB24a551F3b954096",
    "finalSystemOwner": "0xBcd4042DE499D14e55001CcbB24a551F3b954096",
    "portalGuardian": "0xBcd4042DE499D14e55001CcbB24a551F3b954096",
    "controller": "0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266",
    "finalizationPeriodSeconds": 2,
    "deploymentWaitConfirmations": 1,
    "fundDevAccounts": True,
    "l2GenesisBlockBaseFeePerGas": "0x3B9ACA00",
    "gasPriceOracleOverhead": 2100,
    "gasPriceOracleScalar": 1000000,
    "enableGovernance": True,
    "governanceTokenSymbol": "OP",
    "governanceTokenName": "Optimism",
    "governanceTokenOwner": "0xBcd4042DE499D14e55001CcbB24a551F3b954096",
    "eip1559Denominator": 8,
    "eip1559Elasticity": 2,
    "l1GenesisBlockTimestamp": "0x64f3b814",
    "l1StartingBlockTag": "earliest",
    "l2GenesisRegolithTimeOffset": "0x0"
}
