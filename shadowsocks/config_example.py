# !!! Please rename config_example.py as config.py BEFORE editing it !!!

import logging
from shadowsocks.constant import Constant
# You'll need to copy config_example.py as config.py and update configures
# if they have different DEV_VERSION.
DEV_VERSION = '20190611-1'


# MultiUser Interface Settings
# ---------------------------
# Currently just use Constant.Database, there is no known app supports API yet.
INTERFACE = Constant.Database  # Constant.Database or Constant.WebApi

# Database Config
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_USER = 'your_username'
MYSQL_PASS = 'your_password'
MYSQL_DB = 'your_db_name'
MYSQL_USER_TABLE = 'user'  # USUALLY this dont need to be changed
MYSQL_TIMEOUT = 30  # Also the timeout of connecting to WebApi

# Shadowsocks MultiUser API Settings  # todo: not implemented, to remove
# ----------------
API_URL = 'https://yoursite.com/mu'
# API Key (you can find this in the .env file if you are using SS-Panel V3)
API_PASS = 'aaa-bbb-ccc'
NODE_ID = '1'


# Manager Settings
# ----------------
# USUALLY you can just keep this section unchanged
MANAGE_PASS = 'passwd'  # no need to change if ss-manager only listen on 127.0.0.1
MANAGE_BIND_IP = '127.0.0.1'  # change it only if ss-manager is on other server
MANAGE_PORT = 65000  # make sure this port is idle

# Data Sync Settings
# ----------------
PULL_INTERVAL = 30  # interval between 2 pulls from db or api
PUSH_INTERVAL = 120  # interval between 2 pushes to db or api


# Server Settings
# ---------------
# Address binding settings
# if you want to bind ipv4 and ipv6 please use '::'
# if you want to bind only all of ipv4 please use '0.0.0.0'
# if you want to bind a specific IP you may use something like '4.4.4.4'
SS_BIND_IP = '::'
# default method will be replaced by database/api query result if applicable when SS_USE_CUSTOM_METHOD is True
SS_DEFAULT_METHOD = 'aes-128-cfb'
SS_USE_CUSTOM_METHOD = True
# Enforce the use of AEAD ciphers
# When enabled, all requests of creating server with non-AEAD cipher will be omitted
# Check shadowsocks/crypto/aead.py for the list of ciphers
SS_ENFORCE_AEAD = False
# Skip listening these ports
SS_SKIP_PORTS = [80]
# TCP Fastopen (Some OS may not support this, Eg.: Windows)
SS_FASTOPEN = False
# Shadowsocks Time Out
# It should > 180s as some protocol has keep-alive packet of 3 min, Eg.: bt
SS_TIMEOUT = 185


# Firewall Settings
# -----------------
# Prevent user from abusing your service
SS_FIREWALL_ENABLED = True
SS_FIREWALL_MODE = 'blacklist'  # 'whitelist' or 'blacklist'
# Member ports should be INTEGERS
# (SS_FIREWALL_PORTS are configured for tcp/udp relay, remote ports, not ss ports)
SS_FIREWALL_PORTS = [23, 25]  # 'only ban' for blacklist, or 'only allow' for whitelist
# Trusted users (all target ports will be not be blocked for these users)
SS_FIREWALL_TRUSTED_USERS = [443]
# Banned Target IP List
SS_FORBIDDEN_IP = []


# Logging and Debugging Settings
# --------------------------
LOG_ENABLE = True
SS_VERBOSE = False
# Available Log Level: logging.NOTSET|DEBUG|INFO|WARNING|ERROR|CRITICAL
LOG_LEVEL = logging.INFO
# chud - (wocao, zhushi zhong de zhongwen biaodian ye baocuo, bianma wenti)
LOG_ALSO_TO_FILE = False  # set to False if you use supervisor to manage logs
LOG_FILE = 'shadowsocks.log'
# The following format is the one suggested for debugging
# LOG_FORMAT = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'
LOG_FORMAT = '%(asctime)s %(levelname)s %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
