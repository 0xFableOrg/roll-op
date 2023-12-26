from .config import Config
from .examples import use_devnet_config, use_op_doc_config, use_production_config, use_upnode_config

####################################################################################################
# NOTE
#
# The default config is a DEVNET config, which makes it suitable for testing, but not production.
# It is based on the config from the Optimism monorepo devnet as far as the tuning parameters and
# the port mappings are concerned.
#
# We provide various ways to customize it via the following methods:
# - `use_production_config()` — a configurable more suitable for production environment
# - `use_devnet_config()` — same config as the Optimism monorepo devnet
#   (in practice, just changes some paths)
# - `use_doc_config()` — same config as the OP Stack "Getting Started" guide
#
# The `production` config is inspired by the `doc` config for the performance parameters, but uses
# the port mappings, paths, etc... from the default config.
#
# The `production` config is automatically enabled when using the `--preset=prod` flag, otherwise
# the default config is used.
#
####################################################################################################

__all__ = [
    "Config",
    "use_devnet_config",
    "use_op_doc_config",
    "use_production_config",
    "use_upnode_config"
]
