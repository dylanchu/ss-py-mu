#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2015 mengskysama
# Copyright 2016 Howard Liu
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import gc
import sys
import os
import logging
import time
from shadowsocks import config
try:
    import thread
except ImportError:
    import _thread as thread

logger = logging.getLogger()
logger.setLevel(config.LOG_LEVEL)
consoleHandler = logging.StreamHandler(stream=sys.stdout)
consoleHandler.setFormatter(logging.Formatter(config.LOG_FORMAT, datefmt=config.LOG_DATE_FORMAT))
consoleHandler.setLevel(config.LOG_LEVEL)

from sys import platform
if platform == 'linux' or platform == 'linux2':
    with open('/proc/1/cgroup', 'rt') as ifh:
        if 'docker' in ifh.read():
            print('[INFO] Running inside a docker.')
            print('[INFO] Log file config will be ignored & log will not be printed to stdout.')
            config.LOG_FILE = 'shadowsocks.log'
        else:
            logger.addHandler(consoleHandler)

if config.LOG_ALSO_TO_FILE:
    # If enabled logging to file, add a fileHandler as well
    if sys.version_info >= (2, 6) and platform != 'win32':
        # If python version is >= 2.6 and it is not running on Windows, use WatchedFileHandler
        import logging.handlers
        fileHandler = logging.handlers.WatchedFileHandler(config.LOG_FILE)
    else:
        fileHandler = logging.FileHandler(config.LOG_FILE)
    fileHandler.setFormatter(logging.Formatter(config.LOG_FORMAT, datefmt=config.LOG_DATE_FORMAT))
    fileHandler.setLevel(config.LOG_LEVEL)
    logger.addHandler(fileHandler)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

from shadowsocks import manager, dbtransfer
from shadowsocks.constant import Constant
import traceback

if os.path.isdir('../.git') and not os.path.exists('../.nogit'):
    import subprocess
    if "check_output" not in dir(subprocess):
        # Compatible with Python < 2.7
        VERSION = subprocess.Popen(["git", "describe", "--tags", "--always"], stdout=subprocess.PIPE).communicate()[0]
    else:
        VERSION = subprocess.check_output(["git", "describe", "--tags", "--always"]).decode()
    # Remove EOL characters in git's output
    VERSION = VERSION.rstrip()
else:
    VERSION = '3.4.0-dev'


def subprocess_callback(stack, exception):
    logging.info('Exception thrown in %s: %s' % (stack, exception))
    if config.SS_VERBOSE:
        traceback.print_exc()


def main():
    firewall_ports = config.SS_FIREWALL_PORTS if config.SS_FIREWALL_ENABLED else None
    config_passed = {
        'server': config.SS_BIND_IP,
        'local_port': 1081,
        'port_password': {},
        'method': config.SS_DEFAULT_METHOD,
        'manager_address': '%s:%s' % (config.MANAGE_BIND_IP, config.MANAGE_PORT),
        'timeout': config.SS_TIMEOUT,
        'fast_open': config.SS_FASTOPEN,
        'verbose': config.SS_VERBOSE,
        'forbidden_ip': config.SS_FORBIDDEN_IP,
        'firewall_mode': config.SS_FIREWALL_MODE,
        'firewall_trusted': config.SS_FIREWALL_TRUSTED_USERS,
        'firewall_ports': firewall_ports,
        'aead_enforcement': config.SS_ENFORCE_AEAD
    }
    logging.info('-----------------------------------------')
    logging.info('Multi-User Shadowsocks Server Starting...')
    logging.info('Current Server Version: %s' % VERSION)
    if config.INTERFACE == Constant.WebApi:
        logging.info('Now using MultiUser API as the user interface')
    elif config.INTERFACE == Constant.Database:
        logging.info('Now using MySQL Database as the user interface')
    logging.info('Now starting manager thread...')
    thread.start_new_thread(manager.run, (config_passed, subprocess_callback,))
    time.sleep(5)
    logging.info('Now starting user pulling thread...')
    thread.start_new_thread(dbtransfer.thread_pull, ())
    time.sleep(5)
    logging.info('Now starting user pushing thread...')
    thread.start_new_thread(dbtransfer.thread_push, ())

    while True:
        time.sleep(100)
        gc.collect()


if __name__ == '__main__':
    main()
