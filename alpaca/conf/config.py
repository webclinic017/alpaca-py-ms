#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Alpaca configuration module.

This module handles all configuration data in alpaca/conf.
"""

import os
import sys
import yaml
import time
import logging
import logging.config
from pathlib import Path

# Module pointer for module variable configuration
this = sys.modules[__name__]

# Module variables
this.ALPACA_MS_ROOT = None
this.LOG_DIRECTORY = None


# Configure root directory
def get_alpaca_ms_root() -> Path:
    """Get the root directory of package
    @TODO Needs update for package deployment
    @return: Path object of package root
    """
    dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
    while not (dir_path / 'alpaca').is_dir():
        dir_path = dir_path.parent
    # Set module variable and environment variable
    this.ALPACA_MS_ROOT = dir_path
    os.environ['ALPACA_MS_ROOT'] = str(dir_path)
    return dir_path


def configure_logging() -> Path:
    """Configure logging for Alpaca Microservice package.
        - Load logging configuration data from logging.yml file
        - Create logging directory for today, if not already created. Set ALPACA_MS_LOG_DIR
        - Direct all logs to the created folder

    :return: Path object to today's logging directory
    """

    # Don't configure logging if already done
    if this.LOG_DIRECTORY is not None:
        return this.LOG_DIRECTORY

    # Check for logging config, raise error if not present
    root_dir = get_alpaca_ms_root()
    logging_config_yml = root_dir / 'alpaca/conf/logging.yml'
    if logging_config_yml.is_file():
        with open(str(logging_config_yml), 'r') as fp:
            try:
                logging_conf = yaml.safe_load(fp)
            except yaml.YAMLError as e:
                logging_conf = None
                print("Error reading logging config YAML: {} | {}".format(logging_config_yml, e))
    else:
        print("****************************************************************************")
        print("Must provide a logging configuration file: {}".format(logging_config_yml))
        print("****************************************************************************")
        raise FileNotFoundError

    # Create log directory for today, set module variable
    logs_dir = root_dir / 'LOGS'
    todays_log_dir = logs_dir / time.strftime('%Y-%m-%d', time.localtime())
    todays_log_dir.mkdir(exist_ok=True)
    this.LOG_DIRECTORY = todays_log_dir

    # Create filepath with timestamp for all file handlers
    timestamp = time.strftime('%Y%m%dT%H%M%S', time.localtime())
    for hdl in logging_conf['handlers'].values():
        if 'filename' in hdl:
            log_file = todays_log_dir / "{}_{}.log".format(hdl['filename'], timestamp)
            hdl['filename'] = str(log_file)

    # Configure logging from dict
    logging.config.dictConfig(logging_conf)
    return todays_log_dir


class AlpacaMsConfiguration:
    def __init__(self):
        self.run_mode = None
        self.api_key = None
        self.secret_key = None
        self.base_url = None
        self._parse()

    def _parse(self):
        root_dir = get_alpaca_ms_root()
        alpaca_config_yml = root_dir / 'alpaca/conf/alpaca.yml'
        with open(str(alpaca_config_yml), 'r') as fp:
            config_data = yaml.load(fp, Loader=yaml.FullLoader)

        self.run_mode = config_data.get('mode', os.getenv('APCA_RUN_MODE', 'paper'))
        if self.run_mode not in ['paper', 'live']:
            # TODO Print exception here
            pass

        # Get keys based on run mode, fall back to use environmental variables if not present in YAML config file
        key_d = config_data.get(self.run_mode, {})
        self.api_key = key_d.get('api_key', os.getenv('APCA_API_KEY_ID', None))
        self.secret_key = key_d.get('secret_key', os.getenv('APCA_API_SECRET_KEY', None))
        self.base_url = key_d.get('base_url', os.getenv('APCA_API_BASE_URL', None))
