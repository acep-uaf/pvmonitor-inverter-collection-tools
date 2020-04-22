#!/usr/bin/python3

import argparse, glob, os, sys, shutil
import datetime, dateutil.parser, pytz, time
import pydoc
import requests, json
import sqlite_api

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import NoSuchElementException

# DEBUG
# import pdb; pdb.set_trace()
##

# CLASSES
## 
class Installations:
    def __init__(self):
        self.db = None
        self.dataLocations = None
        self.installationData = None
        self.meters = None
        self.options = {}
        self.tzTarget = "US/Alaska"
        self.tzObj = pytz.timezone(self.tzTarget)
        self.tzUTC = pytz.timezone("UTC")

    def hasUnits(self, installationName):
        result = False

        s = "SELECT * FROM installUnits WHERE siteName=\"%s\"" % (installationName)
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
            if i['siteEnabled'] > 0:
                act['sites'].append(i)
                cc = i['credCode']
                if not(cc in act['credentials']):
                    act['credentials'].append(cc)
                act['credentials'].sort()
        return act

    def getOption(self, opt):
        '''Get an option'''
        if opt in self.options.keys():
            return self.options[opt]
        return None

    def getUnits(self, installationName):

        s = "SELECT * FROM installUnits WHERE siteName=\"%s\"" % (installationName)
        self.db.query(s)

        unitNames = {}
        for r in self.db.data:
            unitNames[r['unitName']] = r['siteUnit']

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

            self.db.query("SELECT * FROM dataLocations")
            dataLocs = {}
            for rec in self.db.data:
                if not(rec['urlCode'] in dataLocs.keys()):
                    dataLocs[rec['urlCode']] = {}
                dataLocs[rec['urlCode']][rec['dataMode']] = rec['urlTemplate']
            self.dataLocations = dataLocs

        return

    def setOption(self, opt, val):
        '''Set an option'''
        self.options[opt] = val
        return

    def setTimezone(self, tzStr):
        self.tzTarget = tzStr
        self.tzObj = pytz.timezone(self.tzTarget)
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
    def __init__(self,log=None,ins=None):
        self.credentials = {}
        self.debug = False
        self.driver = None
        self.driverLogFile = "geckodriver.log"
        self.driverOpen = False
        self.errorFlag = False
        self.errorMsg = None
        self.meter = {}
        self.webMod = None
        # Bring objects forward, will figure out
        # inheritance later.
        ##
        self.log = log
        self.ins = ins
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
        if self.driver == None:
            return

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
        if self.debug:
            print("WS:",dataRecords)

        return dataRecords

    def logError(self,errorMessage):
        self.errorFlag = True
        self.errorMsg = errorMessage.strip()
        self.log.msg(self.errorMsg)
        return

    def postData(self, dataRecords):
        # Determine if we are posting multiple records
        # for a single site or a single record.
        # Data structure
        #   Units within a site and data
        # { '204000001190': [{'ob': '2020-04-21 16:54:44', 'power': 2350}, {}] }
        # or
        #   SiteID and data
        # { 'AmblerWTP': [{'ob': '2020-04-21 16:54:44', 'power': 2350}, {}] }
        # NOTE: FOR NOW WILL ONLY SUPPORT ONE DAYS WORTH OF DATA AT ONE TIME
        ##
        site = self.meter['siteCode']
        if self.ins.hasUnits(site):
            units = self.ins.getUnits(site)
        else:
            units = {}
        urlTemplateStore = self.ins.dataLocations[self.meter['urlCode']]['store']
        urlTemplateRead = self.ins.dataLocations[self.meter['urlCode']]['read']
        fullURLStoreMany = self.ins.dataLocations[self.meter['urlCode']]['storeMany']
        for rec in dataRecords.keys():
            if rec in units.keys():
                site = units[rec]
            fullURLStore = (urlTemplateStore % (site))
            fullURLRead = (urlTemplateRead % (site))
            tmUTCmin = None
            tmUTCmax = None
            ct = 0
            #import pdb; pdb.set_trace()
            for r in dataRecords[rec]:
                kwValue = r['power'] / 1000.0
                tmParse = dateutil.parser.parse(r['ob'])
                tmLOC = self.ins.tzObj.localize(tmParse)
                tmUTC = tmLOC.astimezone(pytz.timezone('UTC')).strftime("%Y-%m-%d %H:%M:%S")
                # Replace ob date/time with UTC value
                ##
                r['ob'] = tmUTC
                r['power'] = kwValue
                ct = ct + 1
                if ct == 1:
                    tmUTCmin = tmUTC
                    tmUTCmax = tmUTC
                else:
                    if tmUTC > tmUTCmax:
                        tmUTCmax = tmUTC
                    if tmUTC < tmUTCmin:
                        tmUTCmin = tmUTC
            # Try to read data to see if it already exists
            ##
            tmExists = []
            payload = {
                'timezone': 'UTC',
                'start_ts': tmUTCmin,
                'end_ts': tmUTCmax
            }
            readResult = requests.get(fullURLRead,params=payload)
            bmonData = json.loads(readResult.text)
            if bmonData['status'] != 'success':
                msg = "Unable to read from bmon server, not performing updates."
                self.log.msg(msg)
                return

            for bmonRec in bmonData['data']['readings']:
                tmStr = bmonRec[0]
                tmExists.append(tmStr)

            dataFlag = "write"
            if tmUTC in tmExists:
                dataFlag = "skip"

            # Convert localized timezone to UTC before transmitting
            ##
            if self.debug:
                print(dataFlag,dataRecords[rec])
            if dataFlag == "write":
                if len(dataRecords[rec]) > 1:
                    # This format is form multiple readings
                    # [timestamp, siteID, value]
                    ##
                    #{"storeKey": "123abc",
                    #    "readings": [
                    #        [1432327040, "AmblerWTP", 71.788],
                    #        [1432327042, "test_cpu_temp", 45.527],
                    #        [1432327040, "28.FF1A2D021400", 65.859]
                    #    ]
                    #}
                    # Process into a bmon payload
                    ##
                    data = { 'storeKey': self.meter['dataStoreKey'],
                            'readings': [
                                ]
                            }
                    for r in dataRecords[rec]:
                        obStr = r['ob']
                        t = dateutil.parser.parse(obStr)
                        t = self.ins.tzUTC.localize(t)
                        obDt = t.timestamp()
                        obVal = r['power']
                        drec = [obDt, site, obVal]
                        data['readings'].append(drec)

                    data = json.dumps(data)
                    headers = {'Accept' : 'application/json', 'Content-Type' : 'application/json'}
                    resp = requests.post(fullURLStoreMany,data=data,headers=headers)
                    msg = "*> Multi value write: %s (%s)" % (site,resp.text)
                    self.log.msg(msg)
                else:
                    # This stores one reading
                    ##
                    kwValue = dataRecords[rec][0]['power']
                    tmUTC = dataRecords[rec][0]['ob']
                    data = {
                        'storeKey': self.meter['dataStoreKey'],
                        'val': str(kwValue),
                        'ts': tmUTC
                    }
                    # Do not convert data to json before requests.post call
                    ##
                    resp = requests.post(fullURLStore,data=data)
                    msg = "*> %s %s %s %s" % (site,tmUTC,str(kwValue),dataFlag)
                    self.log.msg(msg)
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

    def setMeter(self,meter,cred):
        self.meter = meter
        self.credentials = cred
        if meter['siteEnabled'] == 9:
            self.debug = True
        else:
            self.debug = False
        if self.ins.getOption('debug'):
            self.debug = True
        return

    def startDriver(self):
        if self.driverOpen:
            return

        # Create tmp directory (if requested)
        ##
        try:
            if not(os.path.isdir(self.tmpDir)):
                os.mkdir(self.tmpDir,0o755)
            if not(os.path.isdir(self.tmpDir)):
                msg = "Unable to make temporary directory: %s" % (self.tmpDir)
                self.logError(msg)
                sys.exit()
        except:
            pass

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
            self.driver.quit()
            self.driverOpen = False
            # Delete temporary directory
            # if utilized
            ##
            try:
                if self.webMod.tmpDir != None:
                    if os.path.isdir(self.webMod.tmpDir):
                        shutil.rmtree(self.webMod.tmpDir)
            except:
                pass
        return

    def login(self):
        #if self.debug:
        #    print(self.meter)
        #    print(self.credentials)
        meterClass = self.credentials['meterClass']
        # Do not reload the class if the module is already
        # loaded.
        ##
        if not(self.webMod) or self.webMod.__name__ != meterClass:
            dynObj = pydoc.locate(meterClass)
            if not(meterClass) in dir(dynObj):
                self.webMod = None
                self.logError("Unable to load meter class: %s" % (meterClass))
                return
            dynAttr = getattr(dynObj,meterClass)
            dynClass = dynAttr()
            self.webMod = dynClass
            # Start the driver if we are not testing
            ##
            if self.webMod.testing == False:
                self.startDriver()
                self.log.msg("* Driver started")
            else:
                # Start the driver from the testing application only
                ##
                if os.path.basename(sys.argv[0]) == 'gatherDataBeta.py':
                    self.startDriver()
                self.log.msg("* Driver testing: %s" % (meterClass))
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

        #import pdb; pdb.set_trace()

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
if os.path.basename(sys.argv[0]) != 'gatherDataBeta.py':
    logFile = 'dataGather.log'
else:
    logFile = 'dataGather2.log'

logger = DebugOutput(logDir,logFile)
meters = Installations()
meters.openDB(dbConfig)
activeMeters = meters.getActiveMeters()

# Command line parsing
##
parser = argparse.ArgumentParser()
parser.add_argument("-d", help="turn on script debugging", action="store_true")
parser.add_argument("-g", help="site group to collect", action="append")
parser.add_argument("-s", help="site to collect", action="append")
args = parser.parse_args()
# Turn on debugging script wide
# disregard meter options
##
meters.setOption('debug',False)
if args.d:
    meters.setOption('debug',True)

meters.setOption('siteSelection',args.s)
siteGroups = args.g

# Work through all the active meters by credential
# so that we do not unnecessarily hammer a website
# with login requests.
#
# Check command line arguments to see if we only should
# process certain sites.
##
for m in activeMeters['credentials']:
    if siteGroups:
        if not(m in siteGroups):
            continue
    if meters.options['debug']:
        print(">%s" % (m))
    # Start a web scraper
    ##
    ws = WebScraper(log=logger,ins=meters)
    ws.log.msg("** Site Group %s" % (m))
    ct = 0
    for siteRec in activeMeters['sites']:
        cc = siteRec['credCode']
        if cc != m:
            continue
        siteCode = siteRec['siteCode']
        if meters.options['siteSelection']:
            if not(siteCode in meters.options['siteSelection']):
                continue
        if meters.options['debug']:
            print(">>%s" % (siteCode))
        ct = ct + 1
        ws.setMeter(siteRec,meters.meters[cc])
        if ct == 1:
            ws.clearLogs()
            ws.log.msg("* Login %s (start)" % (cc))
            ws.login()
            ws.log.msg("* Login %s (end)" % (cc))

        if ws.errorFlag == False:
            ws.log.msg("* Collect (start)")
            dataRecords = ws.collectData()
        if ws.errorFlag == False:
            ws.log.msg("* Collect (end)")
            ws.postData(dataRecords)

    if ws.errorFlag == False:
        ws.log.msg("* Logout (start)")
        ws.logout()
        ws.log.msg("* Logout (end)")

    # Stop the web scraper
    ##
    ws.close()
logger.close()
