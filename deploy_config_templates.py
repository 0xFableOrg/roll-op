PRODUCTION_CONFIG = {
    # Values copied from optimism/packages/contracts-bedrock/deploy-config/goerli.json
    # With some edit mades for values that encode specific Goerli blockhashes and timestamps.

    # These need to be overriden depending on the target L1:
    # - l1StartingBlockTag — earliest L1 block that may contain L2 data
    # - l2OutputOracleStartingTimestamp — timestamp of the first L2 block
    #   (this defaults to -1, causing it to use l1StartingBlockTag's timestamp)
    #
    # If you're deploying an L1 genesis, you also need to set the following, in order to generate
    # the L1 genesis (these values are not otherwise used):
    # - l1UseClique — whether to use clique (vs Ethereum PoS — roll-op only supports clique)
    # - cliqueSignerAddress — address of the clique signer
    # - l1GenesisBlockTimestamp — timestamp to use for the L1 genesis block
    # - l1BlockTime — time between two L1 blocks

    # The documentation for all values in this file can be found here:
    # https://github.com/ethereum-optimism/optimism/blob/op-node/v1.3.0/op-chain-ops/genesis/config.go

    # All fields between "start overriden" and "end overriden" are overriden by the global Config.
    # See l2_deploy.py::generate_deploy_config() for details on how the global Config overrides
    # these.

    # start overriden

    "l1ChainID": "REPLACE THIS",
    "l2ChainID": "REPLACE THIS",

    "p2pSequencerAddress": "REPLACE THIS (SEQUENCER)",
    "batchInboxAddress": "REPLACE_THIS (BATCHER)",
    "batchSenderAddress": "REPLACE_THIS (PROPOSER)",

    "l2OutputOracleProposer": "REPLACE THIS (PROPOSER)",
    "l2OutputOracleChallenger": "REPLACE THIS (ADMIN)",

    "proxyAdminOwner": "REPLACE THIS (ADMIN)",
    "finalSystemOwner": "REPLACE_THIS (ADMIN)",
    "portalGuardian": "REPLACE_THIS (ADMIN)",

    "baseFeeVaultRecipient": "REPLACE THIS (ADMIN)",
    "l1FeeVaultRecipient": "REPLACE THIS (ADMIN)",
    "sequencerFeeVaultRecipient": "REPLACE THIS (ADMIN)",

    "enableGovernance": True,
    "governanceTokenSymbol": "REPLACE THIS",
    "governanceTokenName": "REPLACE THIS",
    "governanceTokenOwner": "REPLACE THIS (ADMIN)",

    # end overriden

    "l2BlockTime": 2,
    "maxSequencerDrift": 600,
    "sequencerWindowSize": 3600,
    "channelTimeout": 300,
    "finalizationPeriodSeconds": 12,

    "l2OutputOracleSubmissionInterval": 120,
    "l2OutputOracleStartingBlockNumber": 0,
    "l2GenesisBlockGasLimit": "0x2faf080",

    "baseFeeVaultMinimumWithdrawalAmount": "0x8ac7230489e80000",
    "l1FeeVaultMinimumWithdrawalAmount": "0x8ac7230489e80000",
    "sequencerFeeVaultMinimumWithdrawalAmount": "0x8ac7230489e80000",
    "baseFeeVaultWithdrawalNetwork": 0,
    "l1FeeVaultWithdrawalNetwork": 0,
    "sequencerFeeVaultWithdrawalNetwork": 0,

    "fundDevAccounts": False,

    "l2GenesisBlockBaseFeePerGas": "0x3b9aca00",
    "gasPriceOracleOverhead": 2100,
    "gasPriceOracleScalar": 1000000,
    "eip1559Denominator": 50,
    "eip1559DenominatorCanyon": 250,
    "eip1559Elasticity": 10,

    "l2GenesisRegolithTimeOffset": "0x0",
    "l2GenesisSpanBatchTimeOffset": "0x0",
    "l2GenesisCanyonTimeOffset": "0x40",

    "faultGameAbsolutePrestate":
        "0x03c7ae758795765c6664a5d39bf63841c71ff191e9189522bad8ebff5d4eca98",
    "faultGameMaxDepth": 30,
    "faultGameMaxDuration": 1200,

    "systemConfigStartBlock": 0,
    "requiredProtocolVersion":
        "0x0000000000000000000000000000000000000000000000000000000000000000",
    "recommendedProtocolVersion":
        "0x0000000000000000000000000000000000000000000000000000000000000000",

    # Settings to get from L1
    "l1StartingBlockTag": "REPLACE THIS (BLOCKHASH or TAG)",

    # This is the timestamp of the first L2 block. Setting this to a negative value causes the
    # deploy script to use l1StartingBlockTag's timestamp.
    "l2OutputOracleStartingTimestamp": -1,

    # Devnet L1 Settings
    "l1UseClique": True,
    "cliqueSignerAddress": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    "l1GenesisBlockTimestamp": "REPLACE THIS OR UNUSED",
    "l1BlockTime": 12
}

DEVNET_CONFIG = {
    # Values copied from optimism/packages/contracts-bedrock/deploy-config/devnetL1-template.json

    # These need to be overriden depending on the target L1:
    # - l1StartingBlockTag — earliest L1 block that may contain L2 data
    # - l2OutputOracleStartingTimestamp — timestamp of the first L2 block
    #   (this defaults to -1, causing it to use l1StartingBlockTag's timestamp)
    #
    # If you're deploying an L1 genesis, you also need to set the following, in order to generate
    # the L1 genesis (these values are not otherwise used):
    # - l1UseClique — whether to use clique (vs Ethereum PoS — roll-op only supports clique)
    # - cliqueSignerAddress — address of the clique signer
    # - l1GenesisBlockTimestamp — timestamp to use for the L1 genesis block
    # - l1BlockTime — time between two L1 blocks

    # The documentation for all values in this file can be found here:
    # https://github.com/ethereum-optimism/optimism/blob/op-node/v1.3.0/op-chain-ops/genesis/config.go

    # All fields between "start overriden" and "end overriden" are overriden by the global Config.
    # See l2_deploy.py::generate_deploy_config() for details on how the global Config overrides
    # these.

    # start overriden

    "l1ChainID": 900,  # config default
    "l2ChainID": 901,  # config default

    "p2pSequencerAddress": "0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc",
    "batchInboxAddress": "0xff00000000000000000000000000000000000000",
    "batchSenderAddress": "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",

    "l2OutputOracleProposer": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
    "l2OutputOracleChallenger": "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65",

    "proxyAdminOwner": "0xa0Ee7A142d267C1f36714E4a8F75612F20a79720",
    "finalSystemOwner": "0xa0Ee7A142d267C1f36714E4a8F75612F20a79720",
    "portalGuardian": "0xa0Ee7A142d267C1f36714E4a8F75612F20a79720",

    "baseFeeVaultRecipient": "0x14dC79964da2C08b23698B3D3cc7Ca32193d9955",
    "l1FeeVaultRecipient": "0x23618e81E3f5cdF7f54C3d65f7FBc0aBf5B21E8f",
    "sequencerFeeVaultRecipient": "0xa0Ee7A142d267C1f36714E4a8F75612F20a79720",

    "enableGovernance": True,
    "governanceTokenSymbol": "OP",
    "governanceTokenName": "Optimism",
    "governanceTokenOwner": "0xBcd4042DE499D14e55001CcbB24a551F3b954096",

    # end overriden

    "l2BlockTime": 2,
    "maxSequencerDrift": 300,
    "sequencerWindowSize": 200,
    "channelTimeout": 120,
    "finalizationPeriodSeconds": 2,

    "l2OutputOracleSubmissionInterval": 10,
    "l2OutputOracleStartingBlockNumber": 0,
    "l2GenesisBlockGasLimit": "0x1c9c380",

    "baseFeeVaultMinimumWithdrawalAmount": "0x8ac7230489e80000",
    "l1FeeVaultMinimumWithdrawalAmount": "0x8ac7230489e80000",
    "sequencerFeeVaultMinimumWithdrawalAmount": "0x8ac7230489e80000",
    "baseFeeVaultWithdrawalNetwork": "remote",
    "l1FeeVaultWithdrawalNetwork": "remote",
    "sequencerFeeVaultWithdrawalNetwork": "remote",

    "fundDevAccounts": True,

    "l2GenesisBlockBaseFeePerGas": "0x1",
    "gasPriceOracleOverhead": 2100,
    "gasPriceOracleScalar": 1000000,
    "eip1559Denominator": 50,
    "eip1559DenominatorCanyon": 250,
    "eip1559Elasticity": 6,

    "l2GenesisRegolithTimeOffset": "0x0",
    "l2GenesisSpanBatchTimeOffset": "0x0",
    "l2GenesisCanyonTimeOffset": "0x40",

    "faultGameAbsolutePrestate":
        "0x03c7ae758795765c6664a5d39bf63841c71ff191e9189522bad8ebff5d4eca98",
    "faultGameMaxDepth": 30,
    "faultGameMaxDuration": 1200,

    "systemConfigStartBlock": 0,
    "requiredProtocolVersion":
        "0x0000000000000000000000000000000000000000000000000000000000000000",
    "recommendedProtocolVersion":
        "0x0000000000000000000000000000000000000000000000000000000000000000",

    # Settings to get from L1
    "l1StartingBlockTag": "REPLACE THIS (BLOCKHASH or TAG)",

    # This is the timestamp of the first L2 block. Setting this to a negative value causes the
    # deploy script to use l1StartingBlockTag's timestamp.
    "l2OutputOracleStartingTimestamp": -1,

    # Devnet L1 Settings
    "l1UseClique": True,
    "cliqueSignerAddress": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    "l1GenesisBlockTimestamp": "REPLACE THIS OR UNUSED",
    "l1BlockTime": 3
}
