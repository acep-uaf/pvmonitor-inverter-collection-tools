#!/usr/bin/python3

import os, datetime, glob
import sqlite_api
import pydoc

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import NoSuchElementException

# CLASSES
## 
class Installations:
    def __init__(self):
        self.db = None
        self.installationData = None
        self.meters = None

    def hasUnits(self, installationName):
        result = False

        s = "SELECT * FROM installUnits WHERE siteName=%" % (installationName)
        self.db.query(s)
        if len(self.db.data) > 0:
            result = True

        return result

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

    def getUnits(self, installationName):

        s = "SELECT * FROM installUnits WHERE siteName=%" % (installationName)
        self.db.query(s)

        unitNames = {}
        for r in self.db.data:
            unitNames[r['unitName']] = r['siteName']

        return unitNames

    def openDB(self, dbname):
        if os.path.isfile(dbname):
            self.db = sqlite_api.sql(dbConfig)

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

            # Update any installation records with meterID
            # based on credential code.  Detect mismatches.
            ##
            for i in self.installationData:
                if i['meterID'] == None:
                    mID = self.meters[i['credCode']]['meterID']
                    s = "UPDATE installations SET meterID=%s WHERE installID=%s" % (mID,i['installID'])
                    #print(s)
                    self.db.run(s)

            self.db.query("SELECT * FROM installations")
            self.installationData = self.db.data

        return

class DebugOutput:
    def __init__(self,logDIR,logFILE):
        self.logFN = None
        self.logDir = None
        self.logOpen = False
        if os.path.isdir(logDIR):
            self.logFN = open(logDIR + "/" + logFILE,"w")
            self.logDir = logDIR
            self.logOpen = True

    def msg(self,msg):
        if self.logOpen:
            ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S")
            self.logFN.write("%s %s\n" % (ts,msg))
        return

    def close(self):
        if self.logOpen:
            self.logFN.close()
            self.logOpen = False
        return

class WebScraper:
    def __init__(self,log=None):
        self.credentials = {}
        self.debug = False
        self.driver = None
        self.driverLogFile = "geckodriver.log"
        self.driverOpen = False
        self.errorFlag = False
        self.errorMsg = None
        self.log = log
        self.meter = {}
        self.webMod = None
        self.db = None
        return

    def clearLogs(self):
        '''Clears *.log files from specified directory'''
        baseDir = self.log.logDir
        if 'siteCode' in self.meter:
            meterDir = os.path.join(baseDir,self.meter['siteCode'])
            if os.path.isdir(meterDir):
                fileList = glob.glob(os.path.join(meterDir,"*.log"))
                if len(fileList) > 0:
                    for fileName in fileList:
                        os.unlink(fileName)

    def dumpLog(self, logFile):
        baseDir = self.log.logDir
        if 'siteCode' in self.meter:
            meterDir = os.path.join(baseDir,self.meter['siteCode'])
            if not(os.path.isdir(meterDir)):
                os.mkdir(meterDir)
            fullDumpFile = os.path.join(meterDir,logFile)
            fn = open(fullDumpFile,'w')
            fn.write("HTML:\n")
            fn.write(self.driver.page_source)
            fn.write("\n")
            #fn.write("Console:\n")
            #for entry in self.driver.get_log("browser"):
            #    fn.write(entry)
            #fn.write("\n")
            fn.close()

    def collectData(self):
        try:
            self.webMod.gotoDataPage()
        except Exception as err:
            msg = "Unhandled exception: %s" % str(err)
            self.logError(msg)
            self.saveScreen("error.png")
            self.dumpLog("error.log")

        if self.debug:
            self.saveScreen("dataPage.png")
            self.dumpLog("data.log")

        dataRecords = self.webMod.getDataRecords()

        return

    def logError(self,errorMessage):
        self.errorFlag = True
        self.errorMsg = errorMessage.strip()
        self.log.msg(self.errorMsg)
        return

    def saveScreen(self, saveFile):
        if self.driverOpen:
            baseSaveDir = '/var/www/html/acepCollect'
            if 'siteCode' in self.meter:
                meterDir = os.path.join(baseSaveDir,self.meter['siteCode'])
                if not(os.path.isdir(meterDir)):
                    os.mkdir(meterDir)
                fullSaveFile = os.path.join(meterDir,saveFile)
                self.driver.save_screenshot(fullSaveFile)
        return

    def setMeter(self,meter,cred,db):
        self.meter = meter
        self.credentials = cred
        self.db = db
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
        # Check for geckodriver.log file and erase
        # before starting a new driver
        ##
        if os.path.isfile(self.driverLogFile):
            os.unlink(self.driverLogFile)
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
                self.logError("Unable to load meter class")
                return
            dynAttr = getattr(dynObj,meterClass)
            dynClass = dynAttr()
            self.webMod = dynClass
            self.startDriver()
            self.log.msg("* Driver started")
            self.webMod.setWebScraper(self)

        # Using the meter class, proceed to login to the
        # website.
        ##
        try:
            self.webMod.gotoLoginPage()
        except Exception as err:
            msg = "Unhandled exception: %s" % str(err)
            self.logError(msg)
            self.saveScreen("error.png")
            self.dumpLog("error.log")
        if self.debug:
            self.saveScreen("login.png")

        if not(self.errorFlag):
            try:
                self.webMod.doLogin(self.credentials)
            except NoSuchElementException as err: 
                msg = "No such element found: %s" % str(err)
                self.logError(msg)
            except Exception as err:
                msg = "Unhandled exception: %s" % str(err)
                self.logError(msg)

        if not(self.errorFlag):
            self.dumpLog("trace.log")
            if self.debug:
                self.saveScreen("postLogin.png")

        return

    def logout(self):
        try:
            self.webMod.doLogout()
        except NoSuchElementException as err: 
            msg = "No such element found: %s" % str(err)
            self.logError(msg)
        except Exception as err:
            msg = "Unhandled exception: %s" % str(err)
            self.logError(msg)
        return

    def close(self):
        self.stopDriver()
        self.log.close()
        return

# MAIN PROGRAM
##

# Gather data based on items placed into a
# database configuration file: 
##
dbConfig = '/home/psi/etc/config.db'
logDir = '/home/psi/dataCollection/log'
# For remote debugging
##
logDir = '/var/www/html/acepCollect/log'
logFile = 'dataGather.log'

logger = DebugOutput(logDir,logFile)
meters = Installations()
meters.openDB(dbConfig)
activeMeters = meters.getActiveMeters()

# Work through all the active meters by credential
# so that we do not unnecessarily hammer a website
# with login requests.
##
for m in activeMeters['credentials']:
    # Start a web scraper
    ##
    ws = WebScraper(log=logger)
    ws.log.msg("** Site %s" % (m))
    ct = 0
    for i in activeMeters['sites']:
        cc = i['credCode']
        if cc != m:
            continue
        ct = ct + 1
        if ct == 1:
            ws.setMeter(i,meters.meters[cc],meters.db)
            ws.clearLogs()
            ws.log.msg("* Login %s (start)" % (i['siteName']))
            ws.login()
            ws.log.msg("* Login %s (end)" % (i['siteName']))
        ws.log.msg("* Collect (start)")
        ws.collectData()
        ws.log.msg("* Collect (end)")
        #ws.postData()

    ws.log.msg("* Logout (start)")
    ws.logout()
    ws.log.msg("* Logout (end)")

    # Stop the web scraper
    ##
    ws.close()
    break

