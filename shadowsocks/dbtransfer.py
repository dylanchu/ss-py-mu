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
    user_select_fields = 'port, u, d, transfer_enable, passwd, switch, enable, method, email, plan_type, plan_end_time'

    @staticmethod
    def pull_db_all_user():
        string = ''
        if config.SS_VERBOSE:
            logging.info('pull db, skip ports: %s' % config.SS_SKIP_PORTS)
        for i, port in enumerate(config.SS_SKIP_PORTS):
            if i == 0:
                string = ' WHERE `port`<>%d' % port
            else:
                string = '%s AND `port`<>%d' % (string, port)
        conn = cymysql.connect(host=config.MYSQL_HOST, port=config.MYSQL_PORT, user=config.MYSQL_USER,
                               passwd=config.MYSQL_PASS, db=config.MYSQL_DB, charset='utf8')
        cur = conn.cursor()
        sql_dict = {'fields': Database.user_select_fields, 'table': config.MYSQL_USER_TABLE, 'conditions': string}
        # noinspection SqlResolve
        cur.execute("SELECT {fields} FROM {table} {conditions} ORDER BY `port` ASC".format(**sql_dict))
        rows = cur.fetchall()
        # Release resources
        cur.close()
        conn.close()
        if config.SS_VERBOSE:
            logging.info('db downloaded')
        return rows  # [(),(),...], return [] if empty

    @staticmethod
    def push_traffic_usage(dt_transfer):
        query_head = 'UPDATE `user`'
        query_sub_when = ''
        query_sub_when2 = ''
        query_sub_in = None
        last_time = time.time()
        for port in dt_transfer.keys():
            query_sub_when += ' WHEN %s THEN `u`+%s' % (port, 0)  # all in d
            query_sub_when2 += ' WHEN %s THEN `d`+%s' % (
                port, dt_transfer[port])
            if query_sub_in is not None:
                query_sub_in += ',%s' % port
            else:
                query_sub_in = '%s' % port
        if query_sub_when == '':
            return
        query_sql = query_head + ' SET u = CASE port' + query_sub_when + \
                    ' END, d = CASE port' + query_sub_when2 + \
                    ' END, t = ' + str(int(last_time)) + \
                    ' WHERE port IN (%s)' % query_sub_in
        # print query_sql
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
    for user in map(user._make, rows):
        # 'port, u, d, transfer_enable, passwd, switch, enable, method, email, plan_type, plan_end_time'
        #    0   1  2          3           4       5       6       7       8       9           10
        server = json.loads(SsCommander.send_command('stat: {"server_port":%s}' % user.port))
        if server['stat'] != 'ko':
            if user.switch == 0 or user.enable == 0:
                # stop disabled or switched-off user
                logging.info('U[%d] Server has been stopped: user is disabled' % user.port)
                SsCommander.send_command('remove: {"server_port":%d}' % user.port)
            elif user.u + user.d >= user.transfer_enable:
                # stop user that exceeds bandwidth limit
                logging.info('U[%d] Server has been stopped: bandwith exceeded' % user.port)
                SsCommander.send_command('remove: {"server_port":%d}' % user.port)
            elif user.plan_end_time < time_now:
                # stop user that exceeds plan_end_time
                logging.info('U[%d] Server has been stopped: plan_end_time exceeded' % user.port)
                SsCommander.send_command('remove: {"server_port":%d}' % user.port)
            elif server['password'] != user.passwd:
                # password changed
                logging.info('U[%d] Server is restarting: password is changed' % user.port)
                SsCommander.send_command('remove: {"server_port":%d}' % user.port)
            else:
                user_method = user.method if config.SS_USE_CUSTOM_METHOD else config.SS_DEFAULT_METHOD
                if server['method'] != user_method:
                    # encryption method changed
                    logging.info('U[%d] Server is restarting: encryption method is changed' % user.port)
                    SsCommander.send_command('remove: {"server_port":%d}' % user.port)
        else:
            if (user.switch == 1 or user.switch == "1") and user.enable == 1 and user.u + user.d < \
                    user.transfer_enable and user.plan_end_time > time_now:
                user_method = user.method if config.SS_USE_CUSTOM_METHOD else config.SS_DEFAULT_METHOD
                SsCommander.send_command(
                    'add: {"server_port": %d, "password":"%s", "method":"%s", "email":"%s"}' % (
                        user.port, user.passwd, user_method, user.email))
                if config.MANAGE_BIND_IP != '127.0.0.1':
                    logging.info('U[%s] Server Started with password [%s] and method [%s]' %
                                 (user.port, user.passwd, user_method))


def thread_pull():
    socket.setdefaulttimeout(config.MYSQL_TIMEOUT)
    while True:
        try:
            if config.INTERFACE == Constant.WebApi:
                rows = WebApi.pull_api_user()
            else:  # config.INTERFACE == Constant.Database
                rows = Database.pull_db_all_user()
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
