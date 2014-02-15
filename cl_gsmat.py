#! /usr/bin/python

# << AT Class >>

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

import serial
from cl_pdu import PDU
import sys
import time

#   C O N S T A N T S   #

##PSERIAL_PORT = ''
##PSERIAL_BAUD = 9600
PSERIAL_TIMEOUT = None


# S T A R T  C L A S S  A T

class gsmdevice:

    def __init__(self,serport,serspeed):
        self.pserial_port = serport
        self.pserial_baud = serspeed

    def send_sms(self,numdest,msgtext):
        # Send an sms over COM serial port
        bOK = True
        try:
            # Encode SMS in PDU format
            pduobj = PDU()
            pdustring = pduobj.encodeSMS(numdest,msgtext)
            #print 'numdest:' + numdest
            #print 'msgtext:' + msgtext
            #print pdustring
            # Count ottets pdu string
            nocts = str((len(pdustring)/2)-1)
            # Open serial port.
            ser = serial.Serial(self.pserial_port,self.pserial_baud,timeout=PSERIAL_TIMEOUT)
            #print ser
            # Enable PDU mode.
            atcmd = 'AT+CMGF=0\r\n'
            ser.write(atcmd)
            time.sleep(1)
            phans = ser.read(ser.inWaiting())
            #print atcmd
            #print phans
            if 'OK' or atcmd in phans:
                # Assign the total octets number to AT command CMGS.
                atcmd = 'AT+CMGS=' + nocts + '\r\n'
                ser.write(atcmd)
                time.sleep(1)
                phans = ser.read(ser.inWaiting())
                #print phans
                if '>' in phans:
                    # Send the SMS in PDU format.
                    atcmd = pdustring + '\x1A\r\n'
                    #print atcmd
                    ser.write(atcmd)
                    time.sleep(3)
                    phans = ser.read(ser.inWaiting())
                    #print phans
                    if not pdustring in phans:
                        bOK = False
                else:
                    bOK = False
            else:
                bOK = False
            # Close serial port
            ser.close()
        except serial.SerialException, error:
            bOK = False
        finally:
            return bOK

    def receive_sms(auth_senders):
        bOK = True
        sms = ''
        try:
            # Read new SMS stored in the phone
            # Open serial port.
            ser = serial.Serial(self.pserial_port,self.pserial_baud,timeout=PSERIAL_TIMEOUT)
            # Set the memory storage to use (ME=Mobile Equipment=phone)
            # and reading the number of messages presents and maximum message can be stored.
            atcmd = 'AT+CPMS="ME","ME"\r\n'
            ser.write(atcmd)
            time.sleep(1)
            phans = ser.read(ser.inWaiting())
            #print phans
            idstr = string.find(phans,':')+1
            # Read number of SMS stored
            numsms = phans[idstr:].split(',')
            #print int(numsms[0].strip())
            if int(numsms[0]) > 0:
                # Enable PDU mode.
                ser.write('AT+CMGF=0\r\n')
                time.sleep(1)
                # Read the first SMS
                ser.write('AT+CMGR=1\r\n')
                time.sleep(2)
                phans = ser.read(ser.inWaiting())
                #print phans
                if 'OK' in phans:
                    # Delete sms after read it
                    ser.write('AT+CMGD=1\r\n')
                    time.sleep(1)
                    smsinfo = phans.split('\r\n')
                    recpdustring = smsinfo[4]
                    # Decode SMS
                    pduobj = pdu.PDU()
                    pduobj.decodeSMS(recpdustring)
                    #print pduobj.SMS
                    smsrec = pduobj.SMS
                    #print smsrec
                    sms = smsrec['message']
                    #print sms
                    smssender = smsrec['sender']
                    #print smssender
                    # Check sender
                    if not smssender in auth_senders:
                        sms = ''
        except serial.SerialException, error:
            bOK = False
        finally:
            return sms
