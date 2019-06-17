#!/usr/bin/env python3
# coding: utf-8
#
# Created by dylanchu on 2019/6/17

import configparser
import logging
import os
import shutil
import sys
from shadowsocks.constant import Constant

REQUIRED_DEV_VERSION = '20190611-1'

_user_config_dir = os.path.expanduser("~") + "/.config/ss-py-mu"
user_config_file = _user_config_dir + "/config.ini"
_current_dir = os.path.dirname(os.path.abspath(__file__))
default_config_file = os.path.join(_current_dir, 'config_default.ini')

if not os.path.isfile(user_config_file):
    os.makedirs(_user_config_dir, exist_ok=True)
    config_template = os.path.join(_current_dir, 'config_template.ini')
    # the config_template is a simplified default_config_file, to reduce users' work
    shutil.copyfile(config_template, user_config_file)
    print('It maybe the first time you run ss-py-mu, please first edit your config file in:\n  %s' % user_config_file)
    sys.exit(1)

config = configparser.ConfigParser(interpolation=None)
config.read(default_config_file)
config.read(user_config_file)


def parse_list(string: str) -> list:
    result = []
    string = string.strip().strip('[]')
    for data in string.split(','):
        data = data.strip()
        if data != '':
            result.append(data)
    return result


def parse_int_list(string: str) -> list:
    return [int(s) for s in parse_list(string)]


if config.get('base', 'config_type') == 'example':
    print('Please first edit your config file in:\n  %s' % user_config_file)
    print("And don't forget to change the 'config_type' of 'base' section to 'custom'")
    sys.exit(1)

DEV_VERSION = config.get('base', 'dev_version')
# Check whether the versions of config files match
if DEV_VERSION != REQUIRED_DEV_VERSION:
    print('Your config file is:\n  %s' % user_config_file)
    print('Your config file seems to be of the wrong version.')
    print('Required config file version is %s' % REQUIRED_DEV_VERSION)
    print('Please first edit your config file according to the file\n'
          '  `config_template.ini` provided with the package.')
    sys.exit(1)

_interface = config.get('base', 'interface')
if _interface != 'mysql':
    print('Currently ss-py-mu only support mysql as database backend, please check your config file.')
    sys.exit(1)
INTERFACE = Constant.Database

PULL_INTERVAL = config.getint('base', 'pull_interval')
PUSH_INTERVAL = config.getint('base', 'push_interval')
NODE_ID = config.getint('base', 'node_id')

# Database Config
MYSQL_HOST = config.get('mysql', 'host')
MYSQL_PORT = config.getint('mysql', 'port')
MYSQL_USER = config.get('mysql', 'user')
MYSQL_PASS = config.get('mysql', 'password')
MYSQL_DB = config.get('mysql', 'db')
MYSQL_USER_TABLE = config.get('mysql', 'user_table')
MYSQL_TIMEOUT = config.getint('mysql', 'timeout')

# WebApi interface, not implemented yet
API_URL = config.get('webapi', 'url')
API_PASS = config.get('webapi', 'key')

# Manager Settings
MANAGE_PASS = config.get('ss_manager', 'pass')
MANAGE_BIND_IP = config.get('ss_manager', 'bind_ip')
MANAGE_PORT = config.getint('ss_manager', 'port')

# SS
SS_BIND_IP = config.get('ss', 'bind_ip')
# default method will be replaced by database/api query result if applicable when SS_USE_CUSTOM_METHOD is True
SS_DEFAULT_METHOD = config.get('ss', 'default_method')
SS_USE_CUSTOM_METHOD = config.getboolean('ss', 'use_custom_method')
SS_ENFORCE_AEAD = config.getboolean('ss', 'enforce_aead')
SS_SKIP_PORTS = parse_int_list(config.get('ss', 'skip_ports'))
SS_FASTOPEN = config.getboolean('ss', 'fast_open')
SS_TIMEOUT = config.getint('ss', 'timeout')

# Firewall
SS_FIREWALL_ENABLED = config.getboolean('firewall', 'enabled')
SS_FIREWALL_MODE = config.get('firewall', 'mode')
SS_FIREWALL_PORTS = parse_int_list(config.get('firewall', 'ports'))
# Trusted users (all target ports will be not be blocked for these users)
SS_FIREWALL_TRUSTED_USERS = parse_int_list(config.get('firewall', 'trusted_users'))
# Banned Target IP List
SS_FORBIDDEN_IP = parse_list(config.get('firewall', 'forbidden_ip'))

# Logging
LOG_ENABLE = config.getboolean('logs', 'enabled')
SS_VERBOSE = config.getboolean('logs', 'verbose')
_log_levels = {'notset': logging.NOTSET, 'debug': logging.DEBUG,
               'info': logging.INFO, 'warning': logging.WARNING,
               'error': logging.ERROR, 'critical': logging.CRITICAL}
LOG_LEVEL = _log_levels[config.get('logs', 'log_level')]
LOG_ALSO_TO_FILE = config.getboolean('logs', 'also_to_file')
LOG_FILE = config.get('logs', 'file')
LOG_FORMAT = config.get('logs', 'format', raw=True)
LOG_DATE_FORMAT = config.get('logs', 'time_format', raw=True)
