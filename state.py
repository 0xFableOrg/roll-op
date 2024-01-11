"""
This module contains application global state.
"""

####################################################################################################

import os

####################################################################################################

args = object()
"""Container for parsed program arguments (cf. roll.py)"""

debug_mode = os.getenv("DEBUG") is not None
"""
Whether debug mode is enabled, printing extra information.
"""

####################################################################################################
