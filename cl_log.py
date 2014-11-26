# ***********************************************************
# ** FUNZIONE DI SCRITTURA LOG MENSILE SU FILE             **
# ***********************************************************
import time

class Log:

    DEBUG = 0

    def __init__(self,pathfilelog,timelog):
        self._pathfilelog = pathfilelog
        self._timelog = timelog


    def write(self,description):
        # Write the OPEN message to log monthly.
        bOK = True
        try:
            logTime = time.localtime(time.time())
            day = str(time.strftime('%d', logTime))
            month = str(time.strftime('%m', logTime))
            year = str(time.strftime('%Y', logTime))
            if self._timelog == 'd' or self._timelog == 'D':
                # Daily log
                sfile = self._pathfilelog + '_' + day + month + year[2:] + '.txt'
            else:
                # Monthly log
                sfile = self._pathfilelog + '_' + month + year[2:] + '.txt'
            flog = open(sfile,'a')
            frtlogTime = time.strftime('%d/%m/%Y %H:%M:%S', logTime)
            flog.write(frtlogTime + ';' + description + '\n')
            flog.close()
        except IOError, error:
            bOK = False
            if DEBUG == 1:
               print ('LOG FILE ERROR! [' + str(error) + ']')
        finally:
            return bOK
