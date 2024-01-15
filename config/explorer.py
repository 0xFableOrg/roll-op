from abc import ABC, abstractmethod


class ExplorerConfig(ABC):
    """
    Configuration options related to the block explorer.
    """

    # ==============================================================================================
    # Required Properties

    @property
    @abstractmethod
    def deployment_name(self):
        pass

    # ==============================================================================================

    def __init__(self):
        super().__init__()

        self.chain_name = f"roll-op <{self.deployment_name}>"
        """
        Name of the chain, notably used in the block explorer. Defaults to "roll-op
        <{deployment_name}>".
        """

        self.chain_short_name = "roll-op"
        """
        Short version of :py:attr:`chain_name`, used in the block explorer.
        Defaults to "roll-op".
        """

    # ==============================================================================================
