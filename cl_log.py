# ***********************************************************
# ** FUNZIONE DI SCRITTURA LOG MENSILE SU FILE             **
# ***********************************************************
import time
def WriteLog(filename,msg):
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
        flog.write(frtlogTime + ';' + msg + '\n')
        flog.close()
    except IOError, error:
        bOK = False
        print ('LOG FILE ERROR! [' + str(error) + ']')
    finally:
        return bOK
