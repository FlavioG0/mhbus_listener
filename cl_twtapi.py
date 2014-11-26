#! /usr/bin/python

import sys
import twitter

DEBUG = 0

# S T A R T  C L A S S twtapi

class TwitterApi:

    def __init__(self,ckey,csec,atkey,atsec):
        self.ckey = ckey
        self.csec = csec
        self.atkey = atkey
        self.atsec = atsec
        self.twt = twitter.Api(consumer_key = self.ckey,
                        consumer_secret = self.csec,
                        access_token_key = self.atkey,
                        access_token_secret = self.atsec)


    def send_public_twt(self,msg):
        # Send a tweet on the public timeline
        bOK = True
        try:
            # Send public tweet
            status = self.twt.PostUpdate(msg)
            if DEBUG == 1:
                print status
        except Exception, err:
            bOK = False
            if DEBUG == 1:
                print 'Errore in f.send_public_twt! [' + str(err) + ']'
        finally:
            return bOK


    def send_private_twt(self,dest,msg):
        # Send a private message to another user.
        bOK = True
        try:
            # Send private tweet
            status = self.twt.PostDirectMessage(msg,None,dest)
            if DEBUG == 1:
                print msg + ' to ' + dest
                print status
        except Exception, err:
            bOK = False
            if DEBUG == 1:
                print 'Errore in f.send_private_twt! [' + str(err) + ']'
        finally:
            return bOK
