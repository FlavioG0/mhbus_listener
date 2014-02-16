import xively

# S T A R T  C L A S S  'xively'
class xivelyapi:

    DEBUG = 1

    def __init__(self,xivapikey,xivfeedid):
        self._xivapikey = xivapikey
        self._xivfeedid = xivfeedid
        self._xivapi = xively.XivelyAPIClient(self._xivapikey)
        self._xivfeed = xively.XivelyAPIClient(self._xivapikey).feeds.get(self._xivfeedid)

    def send_value(self,dsid,value):
        self._xivfeed.datastreams = [xively.Datastream(id = dsid, current_value = value)]
        # Upload the data into the Xively feed
        self._xivfeed.update()
        # Wait 30 seconds to avoid flooding the Xively feed.
        #time.sleep(30)
