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
import os, sys
import platform
import ConfigParser
import httplib, urllib
import cPickle as pickle
import json as simplejson
import xml.etree.ElementTree as ET
from cl_log import Log
from cl_btbus import MyHome
from cl_email import EmailSender
# Optionl module for GSM function.
try:
    from cl_gsmat import GsmDevice
    gsm_module_available = True
except ImportError:
    gsm_module_available = False
# Optional module for Twitter function.
try:
    from cl_twtapi import TwitterApi
    twt_module_available = True
except ImportError:
    twt_module_available = False


# Tunable parameters
DEBUG = 1                     # Debug
CFGFILENAME = 'mhblconf.xml'  # Configuration file name


########################
### CONTROLLO EVENTI ###
########################

def ControlloEventi(msgOpen):
    # GESTIONE EVENTI E AZIONI #
    trigger = msgOpen
    try:
        # Lettura percorso e nome del file di log.
        flog = ET.parse(CFGFILENAME).find("log[@file]").attrib['file']
        logtype = ET.parse(CFGFILENAME).find("log[@file]").attrib['type']
        logobj = Log(flog,logtype)
        # Se CHI=4 estrazione dati di temperatura.
        if trigger.startswith('*#4*'):
            ####################################################################
            # Recupero precedenti valori di temperatura memorizzati.
            # Se non disponibili e' prima volta. L'informazione della
            # temperatura viene inviata dalle sonde sul bus ogni 15 minuti.
            # L'ultimo valore di temp. viene storicizzato e confrontato con
            # la successiva lettura, questo perche' il trigger deve scattare
            # una sola volta finche' la condizione rimane VERA.
            ####################################################################
            try:
                tempdict = pickle.load(open("tempdata", "rb"))
                lastvalue = True
            except Exception:
                lastvalue = False
                 # Inizializza dizionario temperature x zona
                tempdict = {}
                # Zone interne
                tempdict['Z1'] = 0
                tempdict['Z2'] = 0
                tempdict['Z3'] = 0
                tempdict['Z4'] = 0
                tempdict['Z5'] = 0
                tempdict['Z6'] = 0
                tempdict['Z7'] = 0
                tempdict['Z8'] = 0
                tempdict['Z9'] = 0
                tempdict['Z10'] = 0
                # Sonde esterne radio
                tempdict['SE1'] = 0
                tempdict['SE2'] = 0
                tempdict['SE3'] = 0
            finally:
                # Lettura sonde
                if trigger.split('*')[3] == '15':
                    #################
                    # Sonda esterna #
                    #################
                    # Numero sonda
                    nso = int(trigger.split('*')[2][0:1])
                    # Lettura temperatura
                    vt = fixtemp(trigger.split('*')[5][0:4])
                    # Lettura ultimi dati registrati
                    if lastvalue:
                        # Presenza di valore precedente
                        if vt == tempdict['SE'+str(nso)]:
                            # Valori invariati dalla precedente lettura, no trigger!
                            exit
                        else:
                            # Valori variati dalla precedente lettura, scrivi quelli appena letti e OK trigger.
                            tempdict['SE'+str(nso)] = vt
                            pickle.dump(tempdict,open("tempdata", "wb"))
                            trigger = 'TSE' + str(nso)
                    else:
                        # Assenza valore precedente, scrivi quello appena letto e OK trigger.
                        tempdict['SE'+str(nso)] = vt
                        pickle.dump(tempdict,open("tempdata", "wb"))
                        trigger = 'TSE' + str(nso)
                elif trigger.split('*')[3] == '0':
                    #################
                    # Sonda interna #
                    #################
                    # Numero zona
                    nzo = int(trigger.split('*')[2][0:1])
                    # Lettura temperatura
                    vt = fixtemp(trigger.split('*')[4][0:4])
                     # Lettura ultimi dati registrati
                    if lastvalue:
                        # Presenza di valore precedente
                        if vt == tempdict['Z'+str(nzo)]:
                            # Valori invariati dalla precedente lettura, no trigger!
                            exit
                        else:
                            # Valori variati dalla precedente lettura, scrivi quelli appena letti e OK trigger.
                            tempdict['Z'+str(nzo)] = vt
                            pickle.dump(tempdict,open("tempdata", "wb"))
                            trigger = 'TSZ' + str(nzo)
                    else:
                        # Assenza valore precedente, scrivi quello appena letto e OK trigger.
                        tempdict['Z'+str(nzo)] = vt
                        pickle.dump(tempdict,open("tempdata", "wb"))
                        trigger = 'TSZ' + str(nzo)
        # Cerca trigger evento legato alla frame open ricevuta.
        for elem in ET.parse(CFGFILENAME).iterfind("alerts/alert[@trigger='" + trigger + "']"):
            # Estrai canale
            channel = elem.attrib['channel']
            # Se trigger di temperatura estrai parametri e verificali
            if trigger.startswith('TS'):
                tempdta = elem.attrib['data'].split('|')
                tempopt = tempdta[2]
                tempval = float(tempdta[3])
                if tempopt == 'EQ':
                    # EQUAL
                    if not vt == tempval:
                        break
                elif tempopt == 'LS':
                    # LESS THAN
                    if not vt < tempval:
                        break
                elif tempopt == 'LE':
                    # LESS OR EQUAL
                    if not vt <= tempval:
                        break
                elif tempopt == 'GR':
                    # GREATER THAN
                    if not vt > tempval:
                        break
                elif tempopt == 'GE':
                    # GREATER OR EQUAL
                    if not vt >= tempval:
                        break
                # Lettura canale
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
                    if pushover_service(povdata[1]) == True:
                        logobj.write('Inviato messaggio pushover a seguito di evento ' + trigger)
                    else:
                        logobj.write('Errore invio messaggio pushover a seguito di evento ' + trigger)
                elif channel == 'SMS':
                    # ***********************************************************
                    # ** SMS channel (a GSM phone is required on RS-232)       **
                    # ***********************************************************
                    smsdata = data.split('|')
                    if sms_service(smsdata[0],smsdata[1]) == True:
                        logobj.write('Inviato/i SMS a ' + smsdata[0] + ' a seguito di evento ' + trigger)
                    else:
                        logobj.write('Errore invio SMS a seguito di evento ' + trigger)
                elif channel == 'TWT':
                    # ***********************************************************
                    # ** Twitter channel                                       **
                    # ***********************************************************
                    twtdata = data.split('|')
                    if twitter_service(twtdata[0],twtdata[1]) == True:
                        logobj.write('Inviato tweet a ' + twtdata[0] + ' a seguito di evento ' + trigger)
                    else:
                        logobj.write('Errore invio tweet a seguito di evento ' + trigger)
                elif channel == 'EML':
                    # ***********************************************************
                    # ** e-mail channel                                        **
                    # ***********************************************************
                    emldata = data.split('|')
                    if email_service(emldata[0],'mhbus_listener alert',emldata[1]) == True:
                        logobj.write('Inviata/e e-mail a ' + emldata[0] + ' a seguito di evento ' + trigger)
                    else:
                        logobj.write('Errore invio e-mail a seguito di evento ' + trigger)
                elif channel == 'BUS':
                    # ***********************************************************
                    # ** SCS-BUS channel                                       **
                    # ***********************************************************
                    busdata = data.split('|')
                    if opencmd_service(busdata[0]) == True:
                        logobj.write('Eseguito/i comando/i OPEN preimpostato/i a seguito di evento ' + trigger)
                    else:
                        logobj.write('Errore esecuzione comando/i OPEN preimpostato/i a seguito di evento ' + trigger)
                elif channel == 'OSE':
                    # ***********************************************************
                    # ** Open.sen.se channel                                   **
                    # ***********************************************************
                    osedata = data.split('|')
                    osefeedid = osedata[0]
                    osevalue = osedata[1]
                    if send_to_opensense(osefeedid,osevalue) == True:
                        logobj.write('Inviato dato a piattaforma Open.Sen.Se (feed id:' + osefeedid + ', valore:' + osevalue + ') a seguito di evento ' + trigger)
                    else:
                        logobj.write('Errore invio dato a piattaforma Open.Sen.Se (feed id:' + osefeedid + ', valore:' + osevalue + ') a seguito di evento ' + trigger)
                elif channel == 'BAT':
                    # ***********************************************************
                    # ** Batch channel                                         **
                    # ***********************************************************
                    busdata = data.split('|')
                    if batch_service(busdata[0]) == True:
                        logobj.write('Eseguito batch a seguito di evento ' + trigger)
                    else:
                        logobj.write('Errore esecuzione batch a seguito di evento ' + trigger)
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


def batch_service(batchdata):
    bOK = True
    try:
        import subprocess
        # Determina tip osistema operativo
        ostype = platform.system()
        if ostype == 'Windows':
            esito = subprocess.call([batchdata])
            if esito != 0:
                bOK = False
        else:
            esito = subprocess.call(['.' + batchdata])
            if esito != 0:
                bOK = False
    except:
        bOK = False
    finally:
        return bOK


def sms_service(nums,smstext):
    bOK = True
    try:
        serport = ET.parse(CFGFILENAME).find("channels/channel[@type='SMS']").attrib['serport']
        serspeed = ET.parse(CFGFILENAME).find("channels/channel[@type='SMS']").attrib['serspeed']
        gsmobj = GsmDevice(serport,serspeed)
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
        # Instanziamento classe TwitterApi
        twtobj = TwitterApi(ckey,cset,atkey,atsec)
        i = 0
        while i < len(twdest):
            if twdest[i]:
                if DEBUG == 1:
                    print twdest[i],twttext
                if twdest[i].startswith('@'):
                    # Send a private tweet
                    if not twtobj.send_private_twt(twdest[i],twttext) == True:
                        bOK = False
                else:
                    # Send a public tweet
                    if not twtobj.send_public_twt(twttext) == True:
                        bOK = False
                time.sleep(2)
                i = i + 1
            else:
                break
    except Exception, err:
        bOK = False
        if DEBUG == 1:
            print sys.stderr.write('ERROR: %s\n' % str(err))
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
        mailobj = EmailSender(smtpsrv,smtpport,smtpauth,smtpuser,smtppsw,smtptls,sender)
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


def fixtemp(vt):
    # Adatta il formato di temperatura
    # Controllo segno temperatura
    if vt[0:1] == '1':
        # Temp. negativa
        vt = float(vt[1:])*-1
    elif vt[0:1] == '0':
        # Temp. positiva
        vt = float(vt)
    else:
        # Errore!
        vt = 999
    # Mostra temperatura
    return vt/10
