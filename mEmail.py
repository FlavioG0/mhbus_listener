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
import mLog
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import Encoders

# Configuration file name
CFGFILENAME = 'mh_bus_listener.cfg'

def SendMail(email_to,email_obj,email_msg):
    # Invia una e-mail
    bOK = True
    # Lettura percorso e nome del file di log.
    flog = getConfigs(CFGFILENAME,'LOG','LOG_FILE')
    # Lettura parametri SMTP da file di configurazione
    smtp_address = getConfigs(CFGFILENAME,"EMAIL","SMTP_ADDRESS")
    smtp_port = getConfigs(CFGFILENAME,"EMAIL","SMTP_PORT")
    smtp_auth = getConfigs(CFGFILENAME,"EMAIL","SMTP_AUTH")
    smtp_user = getConfigs(CFGFILENAME,"EMAIL","SMTP_USER")
    smtp_pwd = getConfigs(CFGFILENAME,"EMAIL","SMTP_PASSWORD")
    smtp_tls = getConfigs(CFGFILENAME,"EMAIL","SMTP_TLS_SEC")
    email_from = getConfigs(CFGFILENAME,"EMAIL","MAIL_FROM")
    # Preparazione all'invio
    send_date = time.strftime("%d %b %Y %H:%M:%S", time.localtime(time.time()))
    send_msg = "From: %s\r\nTo: %s\r\nDate:%s\r\nSubject:%s\r\n\r\n%s"  % (email_from, email_to, send_date, email_obj, email_msg)
    # Check recipient(s)
    mailTo = []
    mailTo = ReadFields(email_to,";")
    # Controllo parametri...
    if not (smtp_address or smtp_port or email_to):
        bOK = False
        mLog.WriteLog(flog,'Parametri per invio e-mail non corretti o mancanti! Verificare il file di configurazione.')
    else:
        try:
            mailServer = smtplib.SMTP(smtp_address, smtp_port)
        except Exception, error:
            # SMTP server error
            bOK = False
            print 'SMTP server error! Details:[' + str(error) + ']'
            # Write to log (if active)
            mLog.WriteLog(flog,'SMTP server error! Details:[' + str(error) + ']')
        else:
            # Check if security is required.
            if smtp_tls == 'Y':
                # Set encrypted comunication (TLS)
                try:
                   mailServer.ehlo_or_helo_if_needed
                   mailServer.starttls()
                   mailServer.ehlo_or_helo_if_needed
                except smtplib.SMTPException, error:
                    bOK = False
                    if DEBUG == 1:
                        print 'TLS security error! Details:[' + str(error) + ']'
                    mLog.WriteLog(flog,'TLS security error! Details:[' + str(error) + ']')
            # Check if authentication is required.
            if smtp_auth == 'Y':
                # SMTP server requires authentication
                try:
                    mailServer.ehlo_or_helo_if_needed
                    mailServer.login(str(smtp_user),str(smtp_pwd))
                except smtplib.SMTPException, error:
                    bOK = False
                    if DEBUG == 1:
                        print 'E-mail authentication error! Details:[' + str(error) + ']'
                    mLog.WriteLog(flog,'E-mail authentication error! Details:[' + str(error) + ']')
            # Send e-mail...
            try:
                if bOK==True:
                    for address in mailTo:
                        if address:
                            mailServer.sendmail(email_from, address, send_msg)
            except smtplib.SMTPException, error:
                bOK = False
                if DEBUG == 1:
                    print 'E-mail error! Details:[' + str(error) + ']'
                mLog.WriteLog(flog,'E-mail error! Details:[' + str(error) + ']')
            mailServer.quit()
    return bOK


def getConfigs(fileconfig,section,key):
    try:
        config = ConfigParser.RawConfigParser()
        config.read(fileconfig)
        keyvalue = config.get(section, key)
    except Exception, error:
        keyvalue = ''
    return keyvalue


def ReadFields(strInput, sep):
    listFields = []
    start = 0
    while 1:
        posep = strInput.find(sep, start)
        if posep>0:
            # Read fields.
            valfield = strInput[start:posep]
        else:
            # Read only last field.
            end = strInput.find("##")
            if end>0:
                valfield=strInput[start:end]
                listFields.append(valfield)
                break
            else:
                valfield=strInput[start:]
                listFields.append(valfield)
                break
        listFields.append(valfield)
        start = posep+1
    return listFields

