#!/usr/bin/env python3
# coding: utf-8
#
# Created by dylanchu on 2019/7/5

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

import sys
import codecs
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())


class MyMailer(object):
    def __init__(self, config: dict):
        """ config['bcc'] should be a list """
        self.Host = config['host']
        self.Port = config['port']
        self.Email = config['email']
        self.Password = config['password']
        self.From = config['from']
        self.using_ssl = config['using_ssl']
        self.Bcc = config['bcc']
        if not isinstance(self.Bcc, list):
            raise Exception('passed in "bcc" should be a list')

    def send_mail(self, recipient, subject, content):
        if recipient == '' or subject == '' or content == '':
            raise Exception('recipient/subject/content should not be empty!!')

        # Create message container - the correct MIME type is multipart/alternative.
        msg = MIMEMultipart('alternative')
        msg["Accept-Language"] = "zh-CN"
        msg["Accept-Charset"] = "ISO-8859-1,utf-8"
        msg['From'] = formataddr([self.From, self.Email])
        msg['To'] = recipient
        msg['Subject'] = subject

        # msg format should be 'plain' or 'html'
        body = MIMEText(content, 'html', 'utf-8')
        msg.attach(body)
        if self.Bcc and '@' in self.Bcc[0]:
            msg['Bcc'] = ','.join(self.Bcc)
            recipient = [recipient] + self.Bcc
        try:
            if self.using_ssl:
                smtp = smtplib.SMTP_SSL(self.Host, self.Port, timeout=30)
            else:
                smtp = smtplib.SMTP(self.Host, self.Port, timeout=30)
            # smtp.set_debuglevel(1)
            smtp.login(self.Email, self.Password)
            smtp.sendmail(self.Email, recipient, msg.as_string())
            smtp.quit()
            print("email sent successfully")
        except Exception as e:
            print("email sent failed with error: %s" % e)
