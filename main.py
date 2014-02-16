#! /usr/bin/python

# -------------------------------------------------------------------------------
# Name:        mhbus_listener
# Version:     1.5
# Purpose:     Home automation system with bticino MyHome(R)
#
# Author:      Flavio Giovannangeli
# e-mail:      flavio.giovannangeli@gmail.com
#
# Created:     15/10/2013
# Updated:     13/02/2014
# Licence:     GPLv3
# -------------------------------------------------------------------------------

# Copyright (C) 2013 Flavio Giovannangeli

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Thanks to MyOpen Community (http://www.myopen-legrandgroup.com/) for support.


#   M O D U L E S  & L I B R A R I E S #

import xml.etree.ElementTree as ET
import sys
import time
import ConfigParser
import httplib, urllib
import json as simplejson
import re
import os
from cl_log import log
from cl_btbus import myhome
from cl_gsmat import gsmdevice
from cl_email import emailsender
from cl_xively import xivelyapi
from m_twitterapi import twtapi


#   V A R I A B L E S   #

DEBUG = 1
# Acknowledge (OPEN message OK)
ACK = '*#*1##'
# Not-Acknowledge (OPEN message wrong)
NACK = '*#*0##'
# Monitor session
MONITOR = '*99*1##'
# Commands session
COMMANDS = '*99*0##'
# Configuration file name
CFGFILENAME = 'mhblconf.xml'


# F U N C T I O N S #

def main():
    # ****************************************************************************************************************
    # *** S T A R T ...                                                                                          ***
    # ****************************************************************************************************************
    try:
        # ***********************************************************
        # ** LETTURA PARAMETRI NECESSARI DA FILE DI CONFIGURAZIONE **
        # ***********************************************************
        # Lettura indirizzo IP e porta del gateway ethernet con priorita' 1
        mhgateway_ip = ET.parse(CFGFILENAME).find("gateways/gateway[@priority='1']").attrib['address']
        mhgateway_port = ET.parse(CFGFILENAME).find("gateways/gateway[@priority='1']").attrib['port']
        # Lettura percorso e nome del file di log.
        flog = ET.parse(CFGFILENAME).find("log[@file]").attrib['file']
        logobj = log(flog)
        # Lettura dei 'CHI' da filtrare.
        iwhofilter = map(int, ET.parse(CFGFILENAME).find("log[@file]").attrib['who_filter'].split(','))
        # Lettura parametri di traduzione del 'CHI'.
        strawho = 'N' # 'NO' default
        strawho = ET.parse(CFGFILENAME).find("log[@file]").attrib['who_translate']
        strawholang = 'ITA' # 'ITA' default
        strawholang = ET.parse(CFGFILENAME).find("log[@file]").attrib['who_lang']
        # ***********************************************************
        # ** CONNESSIONE AL GATEWAY                                **
        # ***********************************************************
        logobj.write('mhbus_listener v1.5 started.')
        # Controllo presenza parametri necessari
        if mhgateway_ip and mhgateway_port and flog:
            # Instanziamento classe MyHome
            mhobj = myhome(mhgateway_ip,mhgateway_port)
            # Connessione all'impianto MyHome...
            smon = mhobj.mh_connect()
            if smon:
                # Controllo risposta del gateway
                if mhobj.mh_receive_data(smon) == ACK:
                    logobj.write('bticino gateway ' + mhgateway_ip + ' connected.')
                    # OK, attivazione modalita' 'MONITOR'
                    mhobj.mh_send_data(smon,MONITOR)
                    # Controllo risposta del gateway
                    if mhobj.mh_receive_data(smon) == ACK:
                        # Modalita' MONITOR attivata.
                        logobj.write('OK, Ready!')
                        # ***********************************************************
                        # ** ASCOLTO BUS...                                        **
                        # ***********************************************************
                        afframes = []
                        while smon:
                            # Lettura dati in arrivo dal bus
                            frames = mhobj.mh_receive_data(smon)
                            if frames != '':
                                # Controllo prima di tutto che la frame open sia nel formato corretto (*...##)
                                if (frames.startswith('*') and frames.endswith('##')):
                                    # OK, controllo se si tratta di ACK o NACK, che vengono ignorati.
                                    if not (frames == ACK or frames == NACK):
                                        # Separazione frame (nel caso ne arrivino piu' di uno)
                                        frames = frames.split('##')
                                        for frame in frames:
                                            if frame:
                                                # Viene reinserito il terminatore open
                                                msgOpen = frame + '##'
                                                if DEBUG == 1:
                                                    print 'Frame open in transito:' + msgOpen
                                                # Extract WHO and write log
                                                who = mhobj.mh_get_who(msgOpen)
                                                if DEBUG == 1:
                                                    print 'CHI rilevato:' + str(who)
                                                # Se il 'CHI' non e' tra quelli da filtrare, scrivi il log
                                                # e gestisci eventuale azione da compiere.
                                                if who not in iwhofilter:
                                                    # Controlla se e' richiesta la traduzione del 'CHI'
                                                    if strawho == 'Y':
                                                        logobj.write(msgOpen + ' [' + mhobj.mh_get_who_descr(who,strawholang) + ']')
                                                    else:
                                                        logobj.write(msgOpen)
                                                    # Gestione voci antifurto
                                                    if who == 5 and msgOpen != '*5*3*##':
                                                        if msgOpen not in afframes:
                                                            afframes.append(msgOpen)
                                                        else:
                                                            continue
                                                        if msgOpen == '*5*5*##' or msgOpen == '*5*4*##':
                                                            # Reset lista af
                                                            afframes = []
                                                    # Controllo eventi...
                                                    ControlloEventi(msgOpen)
                                else:
                                    # Frame non riconosciuta!
                                    logobj.write(msgOpen + ' [STRINGA OPENWEBNET NON RICONOSCIUTA!]')
                    else:
                        # KO, non e' stato possibile attivare la modalita' MONITOR, impossibile proseguire.
                        logobj.write('IL GATEWAY ' + mhgateway_ip + ' HA RIFIUTATO LA MODALITA'' MONITOR. ARRIVEDERCI!')
                        ExitApp()
                else:
                    # KO, il gateway non ha risposto nel tempo previsto, impossibile proseguire.
                    logobj.write('IL GATEWAY ' + mhgateway_ip + ' NON HA RISPOSTO NEL TEMPO PREVISTO. ARRIVEDERCI!')
                    ExitApp()
            else:
                # KO, il gateway non e' stato trovato, impossibile proseguire.
                #print 'NESSUN GATEWAY BTICINO TROVATO ALL''INDIRIZZO ' + mhgateway_ip + '! ARRIVEDERCI!'
                logobj.write('NESSUN GATEWAY BTICINO TROVATO ALL''INDIRIZZO ' + mhgateway_ip + '! ARRIVEDERCI!')
                ExitApp()
        else:
            # KO, errore nella lettura di parametri indispensabili, impossibile proseguire.
            logobj.write('ERRORE NELLA LETTURA DI PARAMETRI INDISPENSABILI. ARRIVEDERCI!')
            ExitApp()
    except Exception, err:
        if DEBUG == 1:
            print 'Errore in f.main! [' + str(sys.stderr.write('ERROR: %s\n' % str(err))) + ']'
        logobj.write('Errore in f.main! [' + str(sys.stderr.write('ERROR: %s\n' % str(err))) + ']')


def ControlloEventi(msgOpen):
    # GESTIONE EVENTI E AZIONI #
    try:
        # Lettura percorso e nome del file di log.
        flog = ET.parse(CFGFILENAME).find("log[@file]").attrib['file']
        logobj = log(flog)
        # Cerca trigger evento legato alla frame open ricevuta.
        for elem in ET.parse(CFGFILENAME).iterfind("alerts/alert[@trigger='" + msgOpen + "']"):
            channel = elem.attrib['channel']
            # Controlla stato del canale
            status = ET.parse(CFGFILENAME).find("channels/channel[@type='" + channel + "']").attrib['enabled']
            if status == "Y":
                data = elem.attrib['data']
                # Trovato evento, verifica come reagire.
                if channel == 'POV':
                    # ***********************************************************
                    # ** INVIO ALERT TRAMITE PUSHOVER                          **
                    # ***********************************************************
                    povdata = data.split('|')
                    if pushover_service(povdata[1]) == True:
                        logobj.write('Inviato messaggio pushover a seguito di evento ' + msgOpen)
                    else:
                        logobj.write('Errore invio messaggio pushover a seguito di evento ' + msgOpen)
                elif channel == 'SMS':
                    # ***********************************************************
                    # ** INVIO ALERT TRAMITE SMS (necessario mod.GSM su RS-232)**
                    # ***********************************************************
                    smsdata = data.split('|')
                    if sms_service(smsdata[0],smsdata[1]) == True:
                        logobj.write('Inviato/i SMS a ' + smsdata[0] + ' a seguito di evento ' + msgOpen)
                    else:
                        logobj.write('Errore invio SMS a seguito di evento ' + msgOpen)
                elif channel == 'TWT':
                    # ***********************************************************
                    # ** INVIO ALERT TRAMITE TWEET PRIVATO                     **
                    # ***********************************************************
                    import mTwitterApi
                    twtdata = data.split('|')
                    if twitter_service(twtdata[0],twtdata[1]) == True:
                        logobj.write('Inviato tweet privato a ' + twtdata[0] + ' a seguito di evento ' + msgOpen)
                    else:
                        logobj.write('Errore invio tweet privato a seguito di evento ' + msgOpen)
                elif channel == 'EML':
                    # ***********************************************************
                    # ** INVIO ALERT TRAMITE E-MAIL                            **
                    # ***********************************************************
                    emldata = data.split('|')
                    if email_service(emldata[0],'mhbus_listener alert',emldata[1]) == True:
                        logobj.write('Inviata/e e-mail a ' + emldata[0] + ' a seguito di evento ' + msgOpen)
                    else:
                        logobj.write('Errore invio e-mail a seguito di evento ' + msgOpen)
                elif channel == 'BUS':
                    # ***********************************************************
                    # ** INVIO COMANDO/I OPEN SUL BUS                          **
                    # ***********************************************************
                    busdata = data.split('|')
                    if opencmd_service(busdata[0]) == True:
                        logobj.write('Eseguito/i comando/i OPEN preimpostato/i a seguito di evento ' + msgOpen)
                    else:
                        logobj.write('Errore esecuzione comando/i OPEN preimpostato/i a seguito di evento ' + msgOpen)
                elif channel == 'OSE':
                    # ***********************************************************
                    # ** INVIO DATO A PIATTAFORMA WEB OPEN.SES.SE              **
                    # ** https://sen.se/                                       **
                    # ***********************************************************
                    osedata = data.split('|')
                    osefeedid = osedata[0]
                    osevalue = osedata[1]
                    if send_to_opensense(osefeedid,osevalue) == True:
                        logobj.write('Inviato dato a piattaforma Open.Sen.Se (feed id:' + osefeedid + ', valore:' + osevalue + ') a seguito di evento ' + msgOpen)
                    else:
                        logobj.write('Errore invio dato a piattaforma Open.Sen.Se (feed id:' + osefeedid + ', valore:' + osevalue + ') a seguito di evento ' + msgOpen)
                elif channel == 'XIV':
                    # ***********************************************************
                    # ** INVIO DATO A PIATTAFORMA XIVELY                       **
                    # ** https://xively.com                                    **
                    # ***********************************************************
                    xivdata = data.split('|')
                    xivdsid = xivdata[0]
                    xivvalue = xivdata[1]
                    if xively_service(xivdsid,xivvalue) == True:
                        logobj.write('Inviato dato a piattaforma Xively (Data stream ID:' + xivdsid + ', valore:' + xivvalue + ') a seguito di evento ' + msgOpen)
                    else:
                        logobj.write('Errore invio dato a piattaforma Xively (Data stream ID:' + xivdsid + ', valore:' + xivvalue + ') a seguito di evento ' + msgOpen)
                else:
                    # Error
                    logobj.write('Canale di notifica non riconosciuto! [' + action + ']')
            else:
                logobj.write('Alert non gestito causa canale <' + channel + '> non abilitato!')
    except Exception, err:
        if DEBUG == 1:
            print 'Errore in f.ControlloEventi! [' + str(sys.exc_info()[0]) + ']'
        logobj.write('Errore in f.ControlloEventi! [' + str(sys.exc_info()[0]) + ']')


def pushover_service(pomsg):
    bOK = True
    try:
        # Lettura parametri Pushover da file di configurazione
        poat = ET.parse(CFGFILENAME).find("channels/channel[@type='POV']").attrib['api_token']
        pouk = ET.parse(CFGFILENAME).find("channels/channel[@type='POV']").attrib['user_key']
        poaddr = ET.parse(CFGFILENAME).find("channels/channel[@type='POV']").attrib['address']
        conn = httplib.HTTPSConnection(poaddr)
        conn.request("POST", "/1/messages.json",
          urllib.urlencode({
            "token": poat,
            "user": pouk,
            "message": pomsg,
          }), { "Content-type": "application/x-www-form-urlencoded" })
        conn.getresponse()
    except:
        bOK = False
    finally:
        return bOK


def sms_service(nums,smstext):
    bOK = True
    try:
        serport = ET.parse(CFGFILENAME).find("channels/channel[@type='SMS']").attrib['serport']
        serspeed = ET.parse(CFGFILENAME).find("channels/channel[@type='SMS']").attrib['serspeed']
        gsmobj = gsmdevice(serport,serspeed)
        numdest = nums.split(';')
        i = 0
        while i < len(numdest):
            if numdest[i]:
                if not gsmobj.send_sms(numdest[i],smstext) == True:
                    bOK = False
                i = i + 1
            else:
                break
    except Exception, err:
        bOK = False
        if DEBUG == 1:
            print sys.stderr.write('ERROR: %s\n' % str(err))
    finally:
        return bOK


def twitter_service(twtdest,twttext):
    bOK = True
    try:
        # Lettura parametri Pushover da file di configurazione
        ckey = ET.parse(CFGFILENAME).find("channels/channel[@type='TWT']").attrib['ckey']
        cset = ET.parse(CFGFILENAME).find("channels/channel[@type='TWT']").attrib['csecret']
        atkey = ET.parse(CFGFILENAME).find("channels/channel[@type='TWT']").attrib['atkey']
        atsec = ET.parse(CFGFILENAME).find("channels/channel[@type='TWT']").attrib['atsecret']
        twdest = twtdest.split(';')
        if DEBUG == 1:
            print twdest
        # Instanziamento classe twtapi
        twtobj = twtapi(ckey,cset,atkey,atsec)
        i = 0
        while i < len(twdest):
            if twdest[i]:
                if DEBUG == 1:
                    print twdest[i],twttext
                if not twtobj.send_private_msg(twdest[i],twttext) == True:
                    bOK = False
                time.sleep(2)
                i = i + 1
            else:
                break
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
        mailobj = emailsender(smtpsrv,smtpport,smtpauth,smtpuser,smtppsw,smtptls,sender)
        if not mailobj.send_email(emldest,emlobj,emltext) == True:
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
        mhobj = myhome(mhgateway_ip,mhgateway_port)
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
                        if not mhobj.mh_send_data(scmd,mhcmd[i]) == True:
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

def xively_service(xivdsid,xivvalue):
    bOK = True
    try:
        # Lettura parametri xively da file di configurazione
        xivapikey = ET.parse(CFGFILENAME).find("channels/channel[@type='XIV']").attrib['api_token']
        xivfeedid = ET.parse(CFGFILENAME).find("channels/channel[@type='XIV']").attrib['feed_id']
        xivobj = xivelyapi(xivapikey,xivfeedid)
        if not xivobj.send_value(xivdsid,xivvalue) == True:
            bOK = False
    except Exception, err:
        bOK = False
    finally:
        return bOK

def send_to_opensense(feedId,value):
    bOK = True
    try:
        # Send data to Open.Sen.Se platform
        sat = ET.parse(CFGFILENAME).find("channels/channel[@type='OSE']").attrib['api_token']
        datalist = [{"feed_id" : feedId, "value" : value},]
        headers = {"sense_key": sat,"content-type": "application/json"}
        conn = httplib.HTTPConnection("api.sen.se")
        # format a POST request with JSON content
        conn.request("POST", "/events/", simplejson.dumps(datalist), headers)
        response = conn.getresponse()
        if not response.reason == 'OK':
            bOK = False
        if DEBUG == 1:
            print response.status, response.reason
            print response.read()
    except:
        bOK = False
    finally:
        conn.close()
        return bOK


def getConfigs(fileconfig,section,key):
    try:
        config = ConfigParser.RawConfigParser()
        config.read(fileconfig)
        keyvalue = config.get(section, key)
    except:
        keyvalue = ''
    return keyvalue


def ExitApp():
    try:
        # Lettura percorso e nome del file di log.
        flog = ET.parse(CFGFILENAME).find("log[@file]").attrib['file']
        # Close socket.
        smon.close
    except:
        # Exit
        if not logobj.write('DISCONNESSO DAL GATEWAY. ARRIVEDERCI!'):
            print 'DISCONNESSO DAL GATEWAY. ARRIVEDERCI!'
        pushover_service('mhbus_listener v1.5 closed!')
        sys.exit()


if __name__ == '__main__':
    main()
