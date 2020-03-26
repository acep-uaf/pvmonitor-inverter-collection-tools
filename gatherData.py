#!/usr/bin/python3

import os, sys
import sqlite_api
import pydoc

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

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
        return

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
        return

    def close(self):
        self.logFN.close()
        return

class WebScraper:
    def __init__(self,log=None):
        self.credentials = {}
        self.debug = False
        self.driver = None
        self.driverOpen = False
        self.errorFlag = False
        self.errorMsg = None
        self.log = log
        self.meter = {}
        self.webMod = None
        return

    def saveScreen(self, saveFile):
        if self.driverOpen:
            baseSaveDir = '/var/www/html/acepCollect'
            if 'siteCode' in self.meter:
                meterDir = os.path.join(baseSaveDir,self.meter['siteCode'])
                if not(os.path.isdir(meterDir)):
                    os.mkdir(meterDir)
                fullSaveFile = os.path.join(meterDir,saveFile)
                print(self.meter)
                self.driver.save_screenshot(fullSaveFile)

        return

    def setMeter(self,meter,cred):
        self.meter = meter
        self.credentials = cred
        if meter['siteEnabled'] == 9:
            self.debug = True
        else:
            self.debug = False
        return

    def startDriver(self):
        if self.driverOpen:
            return
        options = Options()
        options.add_argument('-headless')
        cap = DesiredCapabilities.FIREFOX
        cap = self.webMod.setCapabilities(cap)
        pro = webdriver.FirefoxProfile()
        pro = self.webMod.setProfile(pro)
        #pro.set_preference("security.tls.version.min",1)
        #pro.set_preference("security.tls.version.max",4)
        #pro.accept_untrusted_certs = True
        #pro.set_preference("security.tls.version.enable-depricated",True)
        #print(dir(pro))
        #print(pro.default_preferences)
        self.driver = webdriver.Firefox(firefox_profile=pro,options=options,capabilities=cap)
        self.driverOpen = True
        return

    def stopDriver(self):
        if self.driverOpen:
            self.driver.close()
            self.driverOpen = False
        return

    def login(self):
        #print(self.meter)
        #print(self.credentials)
        meterClass = self.credentials['meterClass']
        # Do not reload the class if the module is already
        # loaded.
        ##
        if not(self.webMod) or self.webMod.__name__ != meterClass:
            dynObj = pydoc.locate(meterClass)
            if not(meterClass) in dir(dynObj):
                self.webMod = None
                self.errorFlag = True
                self.errorMsg = "Unable to load meter class"
                return
            dynAttr = getattr(dynObj,meterClass)
            dynClass = dynAttr()
            self.webMod = dynClass

        # Using the meter class, proceed to login to the
        # website.
        ##
        self.startDriver()
        try:
            self.driver.get(self.webMod.url)
        except:
            self.errorFlag = True
            self.errorMsg = "URL connection error"
        if self.debug:
            self.saveScreen("debug.png")
        self.stopDriver()
        return

    def logout(self):
        pass

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
            ws.setMeter(i,meters.meters[cc])
            ws.login()
    #ws.logout()

    # Stop the web scraper
    ##
    ws.close()
    break

logger.close()
