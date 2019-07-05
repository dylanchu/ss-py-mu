#!/usr/bin/env python3
# coding: utf-8
#
# Created by dylanchu on 2019/7/5

import datetime
import os
import shutil

import cymysql
from shadowsocks.reminder_mail_utils import MyMailer
from shadowsocks import config

template_customer = ''
template_myself = ''

mail_html = config._user_config_dir + '/reminder_mail_to_customer.html'

if not os.path.isfile(mail_html):
    os.makedirs(config._user_config_dir, exist_ok=True)
    mail_template = os.path.join(config._current_dir, 'reminder_mail_to_customer.html')
    # the config_template is a simplified default_config_file, to reduce users' work
    shutil.copyfile(mail_template, mail_html)
    print('It maybe the first time you run ss-py-mu-reminder-mail, '
          'you can edit the template file in:\n  %s' % mail_html)

with open(mail_html, 'r') as f:
    template_customer = f.read()


def main():
    if not config.MAIL_ENABLE_REMINDER_MAIL:
        print('reminder mail not enabled in config file, now quit\n')
        return

    configs = {
        'host': config.MAIL_HOST,
        'port': config.MAIL_PORT,
        'email': config.MAIL_EMAIL,
        'password': config.MAIL_PASSWORD,
        'from': config.MAIL_FROM,
        'using_ssl': config.MAIL_SSL,
        'bcc': config.MAIL_BCC
    }
    mailer = MyMailer(configs)

    # only check paid users and only send emails exactly 2 days before plan end time
    var_nowf = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    var_today = datetime.date.today()
    print('===================================================  now:', var_nowf)

    db_conn = cymysql.connect(host=config.MYSQL_HOST,
                              port=config.MYSQL_PORT,
                              user=config.MYSQL_USER,
                              passwd=config.MYSQL_PASS,
                              db=config.MYSQL_DB,
                              charset='utf8')
    db_cur = db_conn.cursor()
    db_cur.execute('select name, email, plan_type, plan_end_time from %s' % config.MYSQL_USER_TABLE)
    for user_name, user_email, plan_type, plan_end_time in db_cur.fetchall():
        if not plan_type == 'free':
            diff = plan_end_time.date() - var_today
            diff_days = diff.total_seconds() / 86400
            if diff_days == 2:
                print('\n2天后到期 (用户: %s)' % user_name)
                if template_customer != '':
                    print('    将发送提醒邮件到 %s ...' % user_email)
                    content = template_customer.format(user=user_name,
                                                       plan_type=plan_type,
                                                       end_time=plan_end_time.strftime('%Y-%m-%d %H:%M'),
                                                       now=var_nowf)
                    # send e-mail
                    mailer.send_mail(user_email, '到期提醒', content)
                print('\n')
            else:
                print(diff_days, 'days  (user_name: %s)' % user_name)
    db_cur.close()
    db_conn.close()


if __name__ == '__main__':
    main()
