#! /usr/bin/python

# -------------------------------------------------------------------------------
# Name:        mhbus_listener
# Version:     1.7
# Purpose:     Home automation system with bticino MyHome(R)
#
# Author:      Flavio Giovannangeli
# e-mail:      flavio.giovannangeli@gmail.com
#
# Created:     15/10/2013
# Updated:     25/11/2014
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

import re
import time
import os, sys
import m_eventsman as EvMan
import xml.etree.ElementTree as ET
from cl_log import Log
from cl_btbus import MyHome


#   C O N S T A N T S  #

DEBUG = 1
# Program version
VER = '1.7'
# Acknowledge (OPEN message OK)
ACK = '*#*1##'
# Not-Acknowledge (OPEN message KO)
NACK = '*#*0##'
# Monitor session
MONITOR = '*99*1##'
# Commands session
COMMANDS = '*99*0##'
# Configuration file name
CFGFILENAME = 'mhblconf.xml'


# F U N C T I O N S #

def main():
    ############
    ### MAIN ###
    ############
    try:
        # ***********************************************************
        # ** LETTURA PARAMETRI NECESSARI DA FILE DI CONFIGURAZIONE **
        # ***********************************************************
        # Lettura indirizzo IP e porta del gateway ethernet con priorita' 1
        mhgateway_ip = ET.parse(CFGFILENAME).find("gateways/gateway[@priority='1']").attrib['address']
        mhgateway_port = ET.parse(CFGFILENAME).find("gateways/gateway[@priority='1']").attrib['port']
        # Lettura percorso e nome del file di log
        flog = ET.parse(CFGFILENAME).find("log[@file]").attrib['file']
        # Lettura del tipo file di log (D per giornaliero, M per mensile)
        logtype = ET.parse(CFGFILENAME).find("log[@type]").attrib['type']
        # Istanzia log
        logobj = Log(flog,logtype)
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
        logobj.write('mhbus_listener v.' + VER + ' started.')
        # Controllo presenza parametri necessari
        if mhgateway_ip and mhgateway_port and flog:
            # Instanziamento classe MyHome
            mhobj = MyHome(mhgateway_ip,mhgateway_port)
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
                                                        logobj.write(msgOpen + ';' + mhobj.mh_get_who_descr(who,strawholang))
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
                                                    EvMan.ControlloEventi(msgOpen)
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


if __name__ == '__main__':
    main()
