import uuid

import state


class L2DeployConfig:
    """
    Configuration options related to the deployment of the L2 contracts on the L1 chain.
    """

    # ==============================================================================================

    def __init__(self):
        super().__init__()

        self.l1_deployment_gas_multiplier = 130
        """
        Percent-based multiplier to gas estimations during contract deployment on L1 (130 by
        default, which is the Foundry default).
        """

        self.deploy_slowly = \
            state.args.preset == "prod" and getattr(self, "l1_rpc_host") != "127.0.0.1"
        """
        Whether to deploy contracts "slowly", i.e. wait for each transaction to succeed before
        submitting the next one. This is recommended for production deployments, since RPC nodes
        can be capricious and don't react kindly to getting 30+ transactions at once.
        
        Defaults to True when the `--preset=prod` is passed and the L1 is not running locally, False
        otherwise.
        """

        self.deploy_create2_deployer = False
        """
        Whether to deploy the CREATE2 deployer contract on the L1 before deploying the L2 contracts.
        (False by default).
        """

        self.deploy_salt = uuid.uuid4()
        """
        A salt used for deterministic contract deployment addresses. Ideally, this would enable us
        to skip redeploying contracts that are already deployed (though they need to have been
        deployed by us, otherwise they would have the wrong owner and parameters). Unfortunately,
        this is not how the deploy script works at the moment, meaning partial deployments are not
        possible and this needs to be rotated ever time.
    
        Default to a random UUID, but the value can be any string.
        """

    # ==============================================================================================

    # Also needed to configure and run the deployment:
    # :py:attribute:`contract_deployer_account` in :py:class:`config.AccountsKeysConfig`
    # :py:attribute:`contract_deployer_key` in :py:class:`config.AccountsKeysConfig`
    # :py:attribute:`l1_rpc_url` in :py:class:`config.NetworkConfig`
    # :py:attribute:`deployment_name` in :py:class:`config.Config`
    # :py:attribute:`deployment_artifacts_gen_dir` in :py:class:`config.PathConfig`

    # TODO
    # config.paths.addresses_json_path
    # config.paths.contracts_dir

    # ==============================================================================================
