#!/usr/bin/python
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

import logging
import time
import socket
from collections import namedtuple
from datetime import datetime

from shadowsocks import config
import json
# from urllib.parse import urlencode
# from urllib.request import urlopen, Request
from shadowsocks.constant import Constant

if config.INTERFACE == Constant.Database:
    import cymysql


class SsCommander(object):
    instance = None

    @staticmethod
    def send_command(cmd) -> str:
        if isinstance(cmd, str):
            cmd = cmd.encode()
        data = ''
        try:
            cli = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            cli.settimeout(2)
            cli.sendto(cmd, ('%s' % config.MANAGE_BIND_IP, config.MANAGE_PORT))
            data, addr = cli.recvfrom(1500)
            cli.close()
            data = data.decode()  # bytes -> str
            # TODO: bad way solve timed out
            time.sleep(0.05)
        except Exception as e:
            if config.SS_VERBOSE:
                import traceback
                traceback.print_exc()
            logging.warning('Exception thrown when sending command: %s' % e)
        return data

    @staticmethod
    def get_servers_transfer():
        dt_transfer = {}
        cli = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        cli.settimeout(2)
        cli.sendto(b'transfer: {}', (config.MANAGE_BIND_IP, config.MANAGE_PORT))
        while True:
            data, addr = cli.recvfrom(1500)
            if data == b'e':
                break
            data = json.loads(data.decode())
            # print data
            dt_transfer.update(data)
        cli.close()
        return dt_transfer


class Database(object):
    user_select_fields = 'ss_port, ss_pwd, ss_enabled, ss_method, traffic_up, traffic_down, traffic_quota, ' \
                         'level, email, plan_type, plan_end_time'

    @staticmethod
    def pull_enabled_users():
        conditions = ''
        if config.SS_VERBOSE:
            logging.info('pull db, skip ports: %s' % config.SS_SKIP_PORTS)
        for i, port in enumerate(config.SS_SKIP_PORTS):
            if i == 0:
                conditions = 'WHERE `ss_enabled`=1 AND `ss_port`<>%d' % port
            else:
                conditions = '%s AND `ss_port`<>%d' % (conditions, port)
        conn = cymysql.connect(host=config.MYSQL_HOST, port=config.MYSQL_PORT, user=config.MYSQL_USER,
                               passwd=config.MYSQL_PASS, db=config.MYSQL_DB, charset='utf8')
        cur = conn.cursor()
        sql_dict = {'fields': Database.user_select_fields, 'table': config.MYSQL_USER_TABLE, 'conditions': conditions}
        # noinspection SqlResolve
        cur.execute("SELECT {fields} FROM {table} {conditions} ORDER BY `ss_port` ASC".format(**sql_dict))
        rows = cur.fetchall()
        # Release resources
        cur.close()
        conn.close()
        if config.SS_VERBOSE:
            logging.info('db downloaded')
        return rows  # [(),(),...], return [] if empty

    @staticmethod
    def push_traffic_usage(dt_transfer):
        case1 = ''
        case2 = ''
        query_set = None
        last_time = datetime.utcnow()
        for port in dt_transfer.keys():
            # case1 += ' WHEN %s THEN `traffic_up`+%s' % (port, 0)  # all in traffic_down
            case2 += ' WHEN %s THEN `traffic_down`+%s' % (port, dt_transfer[port])
            if query_set is not None:
                query_set += ',%s' % port
            else:
                query_set = '%s' % port
        if case2 == '':  # since case1 is never changed
            return
        sql_dict = {'table': config.MYSQL_USER_TABLE, 'case1': case1, 'case2': case2,
                    'last_time': str(last_time), 'query_set': query_set}
        # query_sql = "UPDATE {table} SET `traffic_up`=CASE ss_port {case1} END," \
        query_sql = "UPDATE {table} SET " \
                    "`traffic_down`=CASE ss_port {case2} END," \
                    "`last_use_time`='{last_time}'" \
                    " WHERE ss_port IN ({query_set})".format(**sql_dict)
        conn = cymysql.connect(host=config.MYSQL_HOST, port=config.MYSQL_PORT, user=config.MYSQL_USER,
                               passwd=config.MYSQL_PASS, db=config.MYSQL_DB, charset='utf8')
        cur = conn.cursor()
        cur.execute(query_sql)
        cur.close()
        conn.commit()
        conn.close()
        if config.SS_VERBOSE:
            logging.info('db uploaded')

    @staticmethod
    def push_other_information(dt_transfer):
        # info like online users, online nodes
        pass


class WebApi(object):  # todo: not implemented, to remove
    @staticmethod
    def pull_api_user():
        pass
        return []

    @staticmethod
    def push_traffic_usage(dt_transfer):
        pass

    @staticmethod
    def push_other_information(dt_transfer):
        pass


user = namedtuple('user', Database.user_select_fields)


def validate_users_and_sync_ss(rows):
    time_now = datetime.utcnow()
    global user
    invalid_reasons = {-1: 'User Level < 0', -2: 'Bandwidth Exceeded', -3: 'Plan Expired',
                       -4: 'Update SS Password', -5: 'Update SS Method'}
    for user in map(user._make, rows):
        # 'ss_port, ss_pwd, ss_enabled, ss_method, traffic_up, traffic_down, traffic_quota, ' \
        #     0        1        2           3           4            5              6
        #                  'level, email, plan_type, plan_end_time'
        #                     7      8       9           10
        server = json.loads(SsCommander.send_command('stat: {"server_port":%s}' % user.ss_port))
        status = 1  # normal
        if user.level < 0:
            status = -1
        elif user.traffic_up + user.traffic_down >= user.traffic_quota:
            status = -2
        elif user.plan_end_time < time_now:
            status = -3

        # when server[stat] is 'ko', server has no other attributes
        if server['stat'] == 'ko':
            if status == 1:
                user_method = user.ss_method if config.SS_USE_CUSTOM_METHOD else config.SS_DEFAULT_METHOD
                SsCommander.send_command('add: {"server_port": %d, "password":"%s", "method":"%s", "email":"%s"}' %
                                         (user.ss_port, user.ss_pwd, user_method, user.email))
                if config.MANAGE_BIND_IP != '127.0.0.1':
                    logging.info('U[%s] with pwd[%s] and m[%s] will be started on Server %s' %
                                 (user.ss_port, user.ss_pwd, user_method, config.MANAGE_BIND_IP))
        else:
            if user.ss_pwd != server['password']:
                status = -4
            else:
                user_method = user.ss_method if config.SS_USE_CUSTOM_METHOD else config.SS_DEFAULT_METHOD
                if server['method'] != user_method:
                    status = -5
            if status < 0:
                logging.info('U[%d] will be removed: %s' % (user.ss_port, invalid_reasons[status]))
                SsCommander.send_command('remove: {"server_port":%d}' % user.ss_port)


def thread_pull():
    socket.setdefaulttimeout(config.MYSQL_TIMEOUT)
    while True:
        try:
            if config.INTERFACE == Constant.WebApi:
                rows = WebApi.pull_api_user()
            else:  # config.INTERFACE == Constant.Database
                rows = Database.pull_enabled_users()
            validate_users_and_sync_ss(rows)
        except Exception as e:
            if config.SS_VERBOSE:
                import traceback
                traceback.print_exc()
            logging.error('Except thrown: pull user data and sync ss:%s' % e)
        finally:
            time.sleep(config.PULL_INTERVAL)


def thread_push():  # push traffic information to db or web api
    socket.setdefaulttimeout(config.MYSQL_TIMEOUT)
    while True:
        try:
            dt_transfer = SsCommander.get_servers_transfer()
            if config.INTERFACE == Constant.WebApi:
                WebApi.push_traffic_usage(dt_transfer)
                WebApi.push_other_information(dt_transfer)
            else:  # config.INTERFACE == Constant.Database
                Database.push_traffic_usage(dt_transfer)
                Database.push_other_information(dt_transfer)
        except Exception as e:
            import traceback
            if config.SS_VERBOSE:
                traceback.print_exc()
            logging.error('Except thrown while pushing user data:%s' % e)
        finally:
            time.sleep(config.PUSH_INTERVAL)
