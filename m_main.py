#! /usr/bin/python

# -------------------------------------------------------------------------------
# Name:        mhbus_listener
# Purpose:     Home automation system with bticino MyHome(R)
#
# Author:      Flavio Giovannangeli
# e-mail:      flavio.giovannangeli@gmail.com
#
# Created:     15/10/2013
# Updated:     08/05/2017
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

import m_eventsman as evman
import xml.etree.ElementTree as ET
from cl_log import Log
from cl_btbus import MyHome

__version__ = '1.71'

# Tunable parameters
DEBUG = 1                     # Debug
ACK = '*#*1##'                # Acknowledge (OPEN message OK)
NACK = '*#*0##'               # Not-Acknowledge (OPEN message KO)
MONITOR = '*99*1##'           # Monitor session
COMMANDS = '*99*0##'          # Commands session
CFGFILENAME = 'mhblconf.xml'  # Configuration file name


# F U N C T I O N S #

def main():
    # MAIN
    # ***********************************************************
    # ** LETTURA PARAMETRI NECESSARI DA FILE DI CONFIGURAZIONE **
    # ***********************************************************
    # Lettura percorso e nome del file di log
    flog = ET.parse(CFGFILENAME).find("log[@file]").attrib['file']
    # Lettura del tipo file di log (D per giornaliero, M per mensile)
    logtype = ET.parse(CFGFILENAME).find("log[@type]").attrib['type']
    # Istanzia log
    logobj = Log(flog, logtype)
    # Lettura indirizzo IP e porta del gateway ethernet con priorita' 1 (deve essere sempre configurato)
    mhgateway_ip = ET.parse(CFGFILENAME).find("gateways/gateway[@priority='1']").attrib['address']
    mhgateway_port = ET.parse(CFGFILENAME).find("gateways/gateway[@priority='1']").attrib['port']
    mhgateway_priority = 1
    # Lettura dei 'CHI' da filtrare.
    iwhofilter = map(int, ET.parse(CFGFILENAME).find("log[@file]").attrib['who_filter'].split(','))
    # ***********************************************************
    # ** CONNESSIONE AL GATEWAY                                **
    # ***********************************************************
    logobj.write('mhbus_listener v.' + __version__ + ' started.')
    # Controllo presenza parametri necessari
    if mhgateway_ip and mhgateway_port and flog:
        # Instanziamento classe MyHome
        mhobj = MyHome(mhgateway_ip, mhgateway_port)
        # Connessione all'impianto MyHome...
        smon = mhobj.mh_connect()
        if smon:
            # Controllo risposta del gateway
            if mhobj.mh_receive_data(smon) == ACK:
                logobj.write('bticino gateway ' + mhgateway_ip + ' connected.')
                # OK, attivazione modalita' 'MONITOR'
                mhobj.mh_send_data(smon, MONITOR)
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
                            if frames.startswith('*') and frames.endswith('##'):
                                # OK, controllo se si tratta di ACK o NACK, che vengono ignorati.
                                if not (frames == ACK or frames == NACK):
                                    # Separazione frame (nel caso ne arrivino piu' di uno)
                                    frames = frames.split('##')
                                    for frame in frames:
                                        if frame:
                                            # Viene reinserito il terminatore open
                                            msgopen = frame + '##'
                                            if DEBUG == 1:
                                                print 'Frame open in transito:' + msgopen
                                            # Extract WHO and write log
                                            who = mhobj.mh_get_who(msgopen)
                                            if DEBUG == 1:
                                                print 'CHI rilevato:' + str(who)
                                            # Se il 'CHI' non e' tra quelli da filtrare, scrivi il log
                                            # e gestisci eventuale azione da compiere.
                                            if who not in iwhofilter:
                                                # Scrivi log
                                                logobj.write(msgopen)
                                                # Gestione voci antifurto
                                                if who == 5 and msgopen != '*5*3*##':
                                                    if msgopen not in afframes:
                                                        afframes.append(msgopen)
                                                    else:
                                                        continue
                                                    if msgopen == '*5*5*##' or msgopen == '*5*4*##':
                                                        # Reset lista af
                                                        afframes = []
                                                # Controllo eventi...
                                                evman.ctrl_eventi(msgopen)
                            else:
                                # Frame non riconosciuta!
                                logobj.write(frames + ' [STRINGA OPENWEBNET NON RICONOSCIUTA!]')
                else:
                    # KO, non e' stato possibile attivare la modalita' MONITOR, impossibile proseguire.
                    logobj.write('IL GATEWAY ' + mhgateway_ip + \
                                 ' CON PRIORITA'' ' + str(mhgateway_priority) + \
                                 ' HA RIFIUTATO LA MODALITA'' MONITOR. ARRIVEDERCI!')
                    # Chiudi connessione
                    smon.close
                    logobj.write('DISCONNESSO DAL GATEWAY. ARRIVEDERCI!')
            else:
                # KO, il gateway non ha risposto nel tempo previsto, impossibile proseguire.
                logobj.write('IL GATEWAY ' + mhgateway_ip + \
                             ' NON HA RISPOSTO NEL TEMPO PREVISTO. ARRIVEDERCI!')
                smon.close
                logobj.write('DISCONNESSO DAL GATEWAY. ARRIVEDERCI!')
        else:
            # KO, il gateway non e' stato trovato, impossibile proseguire.
            logobj.write('NESSUN GATEWAY BTICINO TROVATO ALL''INDIRIZZO ' + mhgateway_ip + \
                         '! ARRIVEDERCI!')
            smon.close
            logobj.write('DISCONNESSO DAL GATEWAY. ARRIVEDERCI!')
    else:
        # KO, errore nella lettura di parametri indispensabili, impossibile proseguire.
        logobj.write('ERRORE NELLA LETTURA DI PARAMETRI INDISPENSABILI. ARRIVEDERCI!')

if __name__ == '__main__':
    main()
