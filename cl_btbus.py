#! /usr/bin/python

# << MyHome(r) Class >>

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

#   M O D U L E S  #
import socket


# S T A R T  C L A S S  M Y H O M E

class MyHome:

    DEBUG = 0

    def __init__(self,mhgwaddr,mhgwport):
        self.mh_gwaddr = mhgwaddr
        self.mh_gwport = mhgwport
        self.sck = None

    def mh_connect(self):
        # Connect to MyHome(r) gateway
        try:
            self.sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sck.connect((self.mh_gwaddr,int(self.mh_gwport)))
        except Exception, e:
            if DEBUG == 1:
                print e
            self.sck = None
        finally:
            return self.sck

    def mh_receive_data(self,conn):
        # Read BUS data
        try:
            return conn.recv(1024)
        except ValueError:
            return 'ERR_RECV'

    def mh_send_data(self,conn,cmdopen):
        # Send data to BUS
        bOK = True
        try:
            conn.send(cmdopen)
        except conn.error, msg:
            bOK = False
        finally:
            conn.close
        return bOK

    def mh_get_who(self,msgOpen):
        # Estrazione tag 'CHI'
        tags = msgOpen.split('*')
        # Il 'CHI' si trova nel primo tag. E' possibile che
        # il tag 'CHI' sia preceduto dal carattere '#'.
        tag = tags[1]
        # Estrazione tag 'CHI' ignorando il carattere '#', se presente.
        who = int(tag.replace('#',''))
        #print who
        return who

    def mh_get_who_descr(self,who, lang):
        # Ritorna la descrizione del 'CHI' passato
        if who == 0:
            if lang == 'ITA':
                descrwho = 'SCENARI'
            elif lang == 'ESP':
                descrwho = 'ESCENARIOS'
            else:
                descrwho = 'SCENARIOS'
        elif who == 1:
            if lang == 'ITA':
                descrwho = 'ILLUMINAZIONE'
            elif lang == 'ESP':
                descrwho = 'ILLUMINACION'
            else:
                descrwho = 'LIGHTNING'
        elif who == 2:
            if lang == 'ITA':
                descrwho = 'AUTOMAZIONE'
            elif lang == 'ENG':
                descrwho = 'AUTOMATION'
            else:
                descrwho = 'XYZ'
        elif who == 3:
            if lang == 'ITA':
                descrwho = 'CONTROLLO CARICHI'
            elif lang == 'ENG':
                descrwho = 'LOADS CONTROL'
            else:
                descrwho = 'XYZ'
        elif who == 4:
            if lang == 'ITA':
                descrwho = 'TERMOREGOLAZIONE'
            elif lang == 'ENG':
                descrwho = 'TEMPERATURE CONTROL'
            else:
                descrwho = 'XYZ'
        elif who == 5:
            if lang == 'ITA':
                descrwho = 'ANTIFURTO'
            elif lang == 'ENG':
                descrwho = 'ALARM'
            else:
                descrwho = 'XYZ'
        elif who == 6:
            if lang == 'ITA':
                descrwho = 'VIDEOCITOFONIA'
            elif lang == 'ENG':
                descrwho = 'VDES'
            else:
                descrwho = 'XYZ'
        elif who == 9:
            if lang == 'ITA':
                descrwho = 'CANALE AUSILIARIO'
            elif lang == 'ENG':
                descrwho = 'AUX'
            else:
                descrwho = 'XYZ'
        elif who == 13:
            if lang == 'ITA':
                descrwho = 'GATEWAY INFO'
            elif lang == 'ENG':
                descrwho = 'GATEWAY MANAGEMENT'
            else:
                descrwho = 'XYZ'
        elif who == 15:
            if lang == 'ITA':
                descrwho = 'COMANDI CEN'
            elif lang == 'ENG':
                descrwho = 'CEN COMMANDS'
            else:
                descrwho = 'XYZ'
        elif who == 16:
            if lang == 'ITA':
                descrwho = 'AUDIO DIFFUSIONE'
            elif lang == 'ENG':
                descrwho = 'SOUND DIFFUSION'
            else:
                descrwho = 'XYZ'
        elif who == 22:
            if lang == 'ITA':
                descrwho = 'AUDIO DIFFUSIONE'
            elif lang == 'ENG':
                descrwho = 'SOUND DIFFUSION'
            else:
                descrwho = 'XYZ'
        elif who == 17:
            if lang == 'ITA':
                descrwho = 'SCENARI MH200N'
            elif lang == 'ENG':
                descrwho = 'MH200N SCENARIOS'
            else:
                descrwho = 'XYZ'
        elif who == 18:
            if lang == 'ITA':
                descrwho = 'GESTIONE ENERGIA'
            elif lang == 'ENG':
                descrwho = 'ENERGY MANAGEMENT'
            else:
                descrwho = 'XYZ'
        elif who == 25:
            if lang == 'ITA':
                descrwho = 'CEN PLUS, SCENARI PLUS, CONTATTI'
            elif lang == 'ENG':
                descrwho = 'CEN PLUS, SCENARIOS PLUS, DRY CONTACTS'
            else:
                descrwho = 'XYZ'
        elif who == 1001:
            if lang == 'ITA':
                descrwho = 'DIAGNOSTICA ILLUMINAZIONE'
            elif lang == 'ENG':
                descrwho = 'AUTOMATION DIAGNOSTIC'
            else:
                descrwho = 'XYZ'
        elif who == 1004:
            if lang == 'ITA':
                descrwho = 'DIAGNOSTICA TERMOREGOLAZIONE'
            elif lang == 'ENG':
                descrwho = 'THERMOREGULATION DIAGNOSTIC'
            else:
                descrwho = 'XYZ'
        elif who == 1013:
            if lang == 'ITA':
                descrwho = 'DIAGNOSTICA DISPOSITIVI'
            elif lang == 'ENG':
                descrwho = 'DEVICE DIAGNOSTIC'
            else:
                descrwho = 'XYZ'
        else:
            if lang == 'ITA':
                descrwho = 'CHI SCONOSCIUTO'
            elif lang == 'ENG':
                descrwho = 'UNKNOWN WHO'
            else:
                descrwho = 'XYZ'
        return descrwho
