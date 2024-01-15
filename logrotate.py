import os.path
from threading import Thread
import time

import libroll as lib
from config import Config

####################################################################################################

logrotate_setup = False
"""
Whether logrotate has already been setup (config file generated) for this rollop invocation.
"""


####################################################################################################

def start_thread(config: Config):
    """
    Starts a threads that periodically runs logrotate to rotate the log files.
    """
    def logrotate_thread_loop():
        while True:
            _rotate_logs(config)
            time.sleep(config.logrotate_period)

    thread = Thread(target=logrotate_thread_loop)
    thread.daemon = True  # kill thread when main thread exits
    thread.start()


# --------------------------------------------------------------------------------------------------

def _rotate_logs(config: Config):
    global logrotate_setup
    if not logrotate_setup:
        _generate_logrotate_config(config)
        logrotate_setup = True

    olddir = os.path.join(config.logs_dir, "old")
    os.makedirs(olddir, exist_ok=True)
    lib.run("rotate logs", [
        "logrotate",
        f"--state {config.logrotate_status_file}",
        config.logrotate_config_file])


# --------------------------------------------------------------------------------------------------

def _generate_logrotate_config(config: Config):
    """
    Generate the logrotate configuration file from the rollop config.
    """
    with open(config.logrotate_config_file, "w") as f:
        f.write(_generate_logrorate_config_prelude(config))
        f.write("\n\n")
        for file in config.rotating_log_files:
            f.write(_generate_logrotate_config_for_file(file, config))
            f.write("\n\n")


# --------------------------------------------------------------------------------------------------

def _generate_logrorate_config_prelude(config: Config) -> str:
    return "\n".join([
        f"rotate {config.logrotate_count}",
        f"size {config.logrotate_max_size}",
        f"olddir {config.logrotate_old_dir}",
        "missingok",     # don't complain if the log file is missing
        f"maxage {config.logrotate_max_days}",
        "compress",      # gzip the logs
        "dateext",       # add the rotation date (end date) to the end of the file name
        "dateformat -%Y-%m-%d-%H-%M-%S",  # format date down to the second
    ])


# --------------------------------------------------------------------------------------------------

def _generate_logrotate_config_for_file(file: str, config: Config) -> str:
    return "\n".join([
        f'"{file}" {{',
        # TODO add support for per-file logrotate settings
        "}"
    ])


####################################################################################################
