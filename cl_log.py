# ***********************************************************
# ** FUNZIONE DI SCRITTURA LOG MENSILE SU FILE             **
# ***********************************************************
import time

class log:

    DEBUG = 1

    def __init__(self,pathfilelog):
        self._pathfilelog = pathfilelog


    def write(self,description):
        # Write the OPEN message to log monthly.
        bOK = True
        try:
            # Monthly log
            logTime = time.localtime(time.time())
            month = str(time.strftime('%m', logTime))
            year = str(time.strftime('%Y', logTime))
            sfile = filename + '_' + month + year[2:] + '.txt'
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
