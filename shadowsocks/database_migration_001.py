#!/usr/bin/env python3
# coding: utf-8
#
# Created by dylanchu on 2019/6/12
from collections import namedtuple

import cymysql

SOURCE_MYSQL_HOST = 'xxx.com'
SOURCE_MYSQL_PORT = 3306
SOURCE_MYSQL_USER = 'aaa'
SOURCE_MYSQL_PASS = 'bbb'
SOURCE_MYSQL_DB = 'ccc'
SOURCE_MYSQL_USER_TABLE = 'user'  # USUALLY no need to change

DEST_MYSQL_HOST = 'localhost'
DEST_MYSQL_PORT = 3306
DEST_MYSQL_USER = 'ddd'
DEST_MYSQL_PASS = 'eee'
DEST_MYSQL_DB = 'fff'
DEST_MYSQL_USER_TABLE = 'user'  # USUALLY no need to change


def migrate():
    print('Please check through the script to make sure the database structures are correct.')
    temp = input('press <Enter> to continue...')
    print('wait...')
    if temp != '':
        return

    #              0      1        2      3      4       5       6
    fields1 = 'remark, user_name, email, port, passwd, enable, method, ' \
              'u, d, transfer_enable, plan_type, plan_end_time, ' \
              'reg_date, reg_ip, ref_by, invite_num, is_email_verify'
    #          7  8         9            10           11
    #            12         13     14        15             16

    User1 = namedtuple('User1', fields1)

    conn = cymysql.connect(host=SOURCE_MYSQL_HOST, port=SOURCE_MYSQL_PORT, user=SOURCE_MYSQL_USER,
                           passwd=SOURCE_MYSQL_PASS, db=SOURCE_MYSQL_DB, charset='utf8')
    cur = conn.cursor()
    sql_dict = {'fields': fields1, 'table': SOURCE_MYSQL_USER_TABLE, 'conditions': ''}
    # noinspection SqlResolve
    cur.execute("SELECT {fields} FROM {table} {conditions} ORDER BY `id` ASC".format(**sql_dict))
    rows = cur.fetchall()
    # Release resources
    cur.close()
    conn.close()

    # insert to destiny
    conn2 = cymysql.connect(host=DEST_MYSQL_HOST, port=DEST_MYSQL_PORT, user=DEST_MYSQL_USER,
                           passwd=DEST_MYSQL_PASS, db=DEST_MYSQL_DB, charset='utf8')
    cur2 = conn2.cursor()

    for user in map(User1._make, rows):
        # noinspection SqlResolve
        values = "'%s','%s',%d,'%s','%s',%d,'%s','%s','%s'" % (user.remark, user.user_name, 0, user.email, 'password', user.port, user.passwd, user.enable, user.method)
        values = "%s,%d,%d,%d,'%s','%s','%s',%d" % (values, user.u, user.d, user.transfer_enable, '1999-01-01 08:00:00', user.plan_type, str(user.plan_end_time), 0)
        values = "%s,'%s','%s','%s','%s','%s'" % (values, '1999-01-01 08:00:00','1999-01-01 08:00:00','1999-01-01 08:00:00',str(user.reg_date),str(user.reg_ip))
        values = "%s,'%d','%s','%s'" % (values, user.ref_by, user.invite_num, user.is_email_verify)
        cur2.execute("INSERT INTO `{table}` (`note`,`name`,`level`,`email`,`password`,`ss_port`,`ss_pwd`,`ss_enabled`,`ss_method`,"
                    "`traffic_up`,`traffic_down`,`traffic_quota`,`last_use_time`,`plan_type`,`plan_end_time`,`total_paid`,"
                    "`last_gift_time`,`last_check_in_time`,`last_reset_pwd_time`,`reg_time`,`reg_ip`,`referee`,"
                    "`invite_num`,`email_verified`) VALUES ({values})".format(table=DEST_MYSQL_USER_TABLE,values=values))
        # print("INSERT INTO `{table}` (`note`,`name`,`level`,`email`,`password`,`ss_port`,`ss_pwd`,`ss_enabled`,`ss_method`,"
        #       "`traffic_up`,`traffic_down`,`traffic_quota`,`last_use_time`,`plan_type`,`plan_end_time`,`total_paid`,"
        #       "`last_gift_time`,`last_check_in_time`,`last_reset_pwd_time`,`reg_time`,`reg_ip`,`referee`,"
        #       "`invite_num`,`email_verified`) VALUES ({values})".format(table=DEST_MYSQL_USER_TABLE,values=values))
        conn2.commit()
        print('#', end='')

    # Release resources
    cur2.close()
    # conn2.commit()
    conn2.commit()
    conn2.close()


if __name__ == '__main__':
    migrate()
