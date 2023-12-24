import uuid

import libroll as lib


class L1ContractsDeployConfig:
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

        self.deploy_slowly = lib.args.preset == "prod"
        """
        Whether to deploy contracts "slowly", i.e. wait for each transaction to succeed before
        submitting the next one. This is recommended for production deployments, since RPC nodes
        can be capricious and don't react kindly to getting 30+ transactions at once.
        
        Defaults to True when the `--preset=prod` is passed, False otherwise.
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
