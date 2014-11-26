#-------------------------------------------------------------------------------
# Name:        mEmail
# Purpose:     Invio notifiche via e-mail
#
# Author:      Flavio Giovannangeli
#
# Created:     09/02/2013
# Updated:     08/10/2013
# Copyright:   (c) Flavio Giovannangeli 2013
# Licence:     GPLv3
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import time
import Queue
import smtplib
import ConfigParser
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import Encoders


# S T A R T  C L A S S  'emailsender'

class EmailSender:

    DEBUG = 0

    def __init__(self,smtpsrv,smtpport,smtpauth,smtpuser,smtppsw,smtptls,sender):
        self._smtpsrv = smtpsrv
        self._smtpport = smtpport
        self._smtpauth = smtpauth
        self._smtpuser = smtpuser
        self._smtppsw = smtppsw
        self._smtptls = smtptls
        self._sender = sender


    def send_email(self,email_to,email_obj,email_msg):
        # Invia una e-mail
        bOK = True
        send_date = time.strftime("%d %b %Y %H:%M:%S", time.localtime(time.time()))
        send_msg = "From: %s\r\nTo: %s\r\nDate:%s\r\nSubject:%s\r\n\r\n%s"  % (self._sender, email_to, send_date, email_obj, email_msg)
        # Check recipient(s)
        mailTo = []
        #mailTo = ReadFields(email_to,";")
        mailTo = email_to.split(";")
        # Controllo parametri...
        if not (self._smtpsrv or self._smtpport or email_to):
            bOK = False
        else:
            try:
                mailServer = smtplib.SMTP(self._smtpsrv, int(self._smtpport))
            except Exception, error:
                # SMTP server error
                bOK = False
                if DEBUG == 1:
                   print 'SMTP server error! Details:[' + str(error) + ']'
            else:
                # Check if security is required.
                if self._smtptls == 'Y':
                    # Set encrypted comunication (TLS)
                    try:
                       mailServer.ehlo_or_helo_if_needed
                       mailServer.starttls()
                       mailServer.ehlo_or_helo_if_needed
                    except smtplib.SMTPException, error:
                        bOK = False
                        if DEBUG == 1:
                            print 'TLS security error! Details:[' + str(error) + ']'
                # Check if authentication is required.
                if self._smtpauth == 'Y':
                    # SMTP server requires authentication
                    try:
                        mailServer.ehlo_or_helo_if_needed
                        mailServer.login(str(self._smtpuser),str(self._smtppsw))
                    except smtplib.SMTPException, error:
                        bOK = False
                        if DEBUG == 1:
                            print 'E-mail authentication error! Details:[' + str(error) + ']'
                # Send e-mail...
                try:
                    if bOK==True:
                        for address in mailTo:
                            if address:
                                mailServer.sendmail(self._sender, address, send_msg)
                except smtplib.SMTPException, error:
                    bOK = False
                    if DEBUG == 1:
                        print 'E-mail error! Details:[' + str(error) + ']'
                mailServer.quit()
        return bOK
