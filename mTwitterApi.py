#! /usr/bin/python

# Test di invio di un tweet diretto con Python!
import twitter
import sys

DEBUG = 0

# S T A R T  C L A S S twtapi

class twtapi:

    def __init__(self,ckey,csec,atkey,atsec):
        self.ckey = ckey
        self.csec = csec
        self.atkey = atkey
        self.atsec = atsec


    def send_private_msg(dest,msg):
        # Instanzia API. Codici generati preventivamente su 'Twitter Developers'
        # https://dev.twitter.com/
        bOK = True
        try:
            # Instanzia canale
            api = twitter.Api(consumer_key = self.ckey,
                              consumer_secret = self.csec,
                              access_token_key = self.atkey,
                              access_token_secret = self.atsec)
            # Invia messaggio diretto
            dirmsg = api.PostDirectMessage(msg,dest)
            if DEBUG == 1:
                print dirmsg
        except:
            bOK = False
            if DEBUG == 1:
                print 'Errore in f.SendPrivateTweet! [' + str(sys.exc_info()[0]) + ']'
        finally:
            return bOK
