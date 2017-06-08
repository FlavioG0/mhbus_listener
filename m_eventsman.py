#! /usr/bin/python

# << Events Manager Module for mhbus_lister >>

# Thanks to MyOpen Community (http://www.myopen-bticino.it/) for support.

# Copyright (C) 2012 Flavio Giovannangeli
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# e-mail:flavio.giovannangeli@gmail.com


import time
import httplib
import urllib
import xml.etree.ElementTree as ET
from cl_log import Log
from cl_btbus import MyHome
from cl_email import EmailSender

# Tunable parameters
DEBUG = 1                     # Debug
CFGFILENAME = 'mhblconf.xml'  # Configuration file name


# CONTROLLO EVENTI

def ctrl_eventi(trigger):
    # GESTIONE EVENTI E AZIONI #
    # Lettura percorso e nome del file di log.
    flog = ET.parse(CFGFILENAME).find("log[@file]").attrib['file']
    logtype = ET.parse(CFGFILENAME).find("log[@file]").attrib['type']
    logobj = Log(flog, logtype)
    # Cerca trigger evento legato alla frame open ricevuta.
    for elem in ET.parse(CFGFILENAME).iterfind("alerts/alert[@trigger='" + trigger + "']"):
        # Estrai canale
        channel = elem.attrib['channel']
        # Controlla stato del canale
        status = ET.parse(CFGFILENAME).find("channels/channel[@type='" + channel + "']").attrib['enabled']
        if status == "Y":
            data = elem.attrib['data']
            # Trovato evento, verifica come reagire.
            if channel == 'POV':
                # ***********************************************************
                # ** Pushover channel                                      **
                # ***********************************************************
                povdata = data.split('|')
                if pushover_service(povdata[1]) is True:
                    logobj.write('Inviato messaggio pushover a seguito di evento ' + trigger)
                else:
                    logobj.write('Errore invio messaggio pushover a seguito di evento ' + trigger)
            elif channel == 'EML':
                # ***********************************************************
                # ** e-mail channel                                        **
                # ***********************************************************
                emldata = data.split('|')
                if email_service(emldata[0], 'mhbus_listener alert', emldata[1]) is True:
                    logobj.write('Inviata/e e-mail a ' + emldata[0] + ' a seguito di evento ' + trigger)
                else:
                    logobj.write('Errore invio e-mail a seguito di evento ' + trigger)
            elif channel == 'BUS':
                # ***********************************************************
                # ** SCS-BUS channel                                       **
                # ***********************************************************
                busdata = data.split('|')
                if opencmd_service(busdata[0]) is True:
                    logobj.write('Eseguito/i comando/i OPEN preimpostato/i a seguito di evento ' + trigger)
                else:
                    logobj.write('Errore esecuzione comando/i OPEN preimpostato/i a seguito di evento ' + trigger)
            else:
                # Error
                logobj.write('Canale di notifica non riconosciuto! [' + channel + ']')
        else:
            logobj.write('Alert non gestito causa canale <' + channel + '> non abilitato!')



def pushover_service(pomsg):
    bOK = True
    try:
        # Lettura parametri Pushover da file di configurazione
        poat = ET.parse(CFGFILENAME).find("channels/channel[@type='POV']").attrib['api_token']
        pouk = ET.parse(CFGFILENAME).find("channels/channel[@type='POV']").attrib['user_key']
        poaddr = ET.parse(CFGFILENAME).find("channels/channel[@type='POV']").attrib['address']
        conn = httplib.HTTPSConnection(poaddr)
        conn.request("POST", "/1/messages.json", urllib.urlencode({"token": poat, "user": pouk, "message": pomsg,}), {"Content-type": "application/x-www-form-urlencoded"})
        conn.getresponse()
    except:
        bOK = False
    finally:
        return bOK


def email_service(emldest,emlobj,emltext):
    bOK = True
    try:
        # Lettura parametri e-mail da file di configurazione
        smtpsrv = ET.parse(CFGFILENAME).find("channels/channel[@type='EML']").attrib['smtp']
        smtpport = cset = ET.parse(CFGFILENAME).find("channels/channel[@type='EML']").attrib['smtp_port']
        smtpauth = ET.parse(CFGFILENAME).find("channels/channel[@type='EML']").attrib['smtp_auth']
        smtpuser = ET.parse(CFGFILENAME).find("channels/channel[@type='EML']").attrib['smtp_user']
        smtppsw = ET.parse(CFGFILENAME).find("channels/channel[@type='EML']").attrib['smtp_psw']
        smtptls = ET.parse(CFGFILENAME).find("channels/channel[@type='EML']").attrib['smtp_tls_sec']
        sender = ET.parse(CFGFILENAME).find("channels/channel[@type='EML']").attrib['sender']
        mailobj = EmailSender(smtpsrv, smtpport, smtpauth, smtpuser, smtppsw, smtptls, sender)
        if not mailobj.send_email(emldest,emlobj,emltext) is True:
            bOK = False
    except Exception, err:
        bOK = False
    finally:
        return bOK


def opencmd_service(opencmd):
    bOK = True
    try:
        # Lettura parametri Pushover da file di configurazione
        mhgateway_ip = ET.parse(CFGFILENAME).find("gateways/gateway[@priority='1']").attrib['address']
        mhgateway_port = ET.parse(CFGFILENAME).find("gateways/gateway[@priority='1']").attrib['port']
        # Instanziamento classe MyHome
        mhobj = MyHome(mhgateway_ip,mhgateway_port)
        # Connessione all'impianto MyHome...
        scmd = mhobj.mh_connect()
        mhcmd  = opencmd.split(';')
        if scmd != None:
            time.sleep(1)
            if mhobj.mh_receive_data(scmd) == ACK:
                # OK, apertura sessione comandi
                mhobj.mh_send_data(scmd, COMMANDS)
                time.sleep(1)
                i = 0
                while i < len(mhcmd):
                    if mhcmd[i]:
                        if not mhobj.mh_send_data(scmd,mhcmd[i]) is True:
                            bOK = False
                        i = i + 1
                    else:
                        break
                # Chiudi sessione comandi
                scmd.close()
            else:
                bOK = False
        else:
            bOK = False
    except:
        bOK = False
    finally:
        return bOK
