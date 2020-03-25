#!/usr/bin/python3

import os, sys
import sqlite_api

# CLASSES
## 
class Installations:
    def __init__(self):
        self.db = None
        self.installationData = None
        self.meters = None

    def openDB(self, dbname):
        if os.path.isfile(dbname):
            self.db = sqlite_api.sql(dbConfig)

            self.db.query("SELECT * FROM installations")
            self.installationData = self.db.data

            # Update any installation records with meterID
            # based on credential code.  Detect mismatches.
            ##
            for i in self.installationData:
                if i['meterID'] == None:
                    mID = meters[i['credCode']]['meterID']
                    s = "UPDATE installations SET meterID=%s WHERE installID=%s" % (mID,i['installID'])
                    #print(s)
                    self.db.run(s)

            self.db.query("SELECT * FROM installations")
            self.installationData = self.db.data

            self.db.query("SELECT * FROM meters")
            meterData = self.db.data
            # Realign meters by credential code (credCode)
            ##
            self.meters = {}
            for m in meterData:
                c = m['credCode']
                self.meters[c] = m

    def getActiveMeters(self):
        # Get active installations
        ##
        act = {
                'sites': [],
                'credentials': []
        }
        for i in self.installationData:
            if i['siteEnabled']:
                act['sites'].append(i)
                cc = i['credCode']
                if not(cc in act['credentials']):
                    act['credentials'].append(cc)
                act['credentials'].sort()
        return act

class DebugOutput:
    def __init__(self,logDIR,logFILE):
        if os.path.isdir(logDIR):
            self.logFN = open(logDIR + "/" + logFILE,"w")

    def msg(self,msg):
        self.logFN.write("%s\n" % (msg))

    def close(self):
        self.logFN.close()

class WebScraper:
    def __init__(self,log=None):
        self.log = log

    def setMeter(self,meter):
        self.meter = meter
        print(meter)

    def login(self):

    def close(self):
        pass

# MAIN PROGRAM
##

# Gather data based on items placed into a
# database configuration file: 
##
dbConfig = '/home/psi/etc/config.db'
logDir = '/home/psi/dataCollection/log'
logFile = 'dataGather.log'

logger = DebugOutput(logDir,logFile)
meters = Installations()
meters.openDB(dbConfig)

activeMeters = meters.getActiveMeters()

# Work through all the active meters by credential
##
for m in activeMeters['credentials']:
    # Start a web scraper
    ##
    ws = WebScraper(log=logger)
    ct = 0
    for i in activeMeters['sites']:
        cc = i['credCode']
        if cc != m:
            continue
        ct = ct + 1
        if ct == 1:
            ws.setMeter(i)
            #ws.login()

    # Stop the web scraper
    ##
    ws.close()

logger.close()
