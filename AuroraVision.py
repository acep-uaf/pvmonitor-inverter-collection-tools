#!/usr/bin/python3

import os, time, dateutil.parser, datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# DEBUG
# import pdb; pdb.set_trace()
##

# AuroraVision
# Web page communications module
# Required class functions
#   setCapabilities()
#   setProfile()
##

class AuroraVision:
    def __init__(self):
        self.urlLogin = "https://www.auroravision.net/ums/v1/loginPage?redirectUrl=http:%2F%2Fwww.auroravision.net%2Fdash%2Fhome.jsf&cause=MISSING_TOKEN"
        self.urlLogout = "https://www.auroravision.net/ums/v1/logoutPage"
        self.urlHeadDataPage = "https://www.auroravision.net/dash/home.jsf"
        self.urlDataPageExample = "https://www.auroravision.net/dash/assets/summary.jsf#3466383"
        self.ws = None
        self.testing = True
        self.lastElement = None
        self.myPid = os.getpid()
        self.tmpDir = "/home/psi/dataCollection/tmp/%d" % (self.myPid)
        self.tmpFile = "%s/download.csv" % (self.tmpDir)

    def doLogin(self,credentials):
        loginUsername = credentials["meterUsername"]
        loginPassword = credentials["meterPassword"]

        formUsername = self.ws.driver.find_element_by_name("userId")
        formPassword = self.ws.driver.find_element_by_name("password")

        formUsername.send_keys(loginUsername)
        formPassword.send_keys(loginPassword)
        
        self.ws.driver.find_element_by_xpath("//button[@data-ng-click='doLogin()']").click()

        # Wait for page update beyond login
        ##
        # self.driver.find_elements_by_xpath("//div[@class='data-label cell' and text()='Last 30 Days']")
        xp = "//div[@class='data-label cell' and text()='Last 30 Days']"
        self.waitFor("xpath",xp,15)

        return

    def doLogout(self):
        return

    def getDataRecords(self):
        dataRecs = {}
        # Detect no data available
        # If no data is available, the CSV button is typically disabled
        # and we should just return no data.
        ##
        xp = "//div[@class='alert alert-info noChartData hideOnLoad']"
        elements = self.ws.driver.find_elements_by_xpath(xp)

        if elements[0].is_displayed():
            return dataRecs

        self.ws.dumpLog("trace2.log")
        self.ws.saveScreen("trace2.png")
        xp = "//div[@class='csvButton']"
        elements = self.ws.driver.find_elements_by_xpath(xp)
        # Make sure download.csv is not present
        # prior to download.
        ##
        if os.path.isfile(self.tmpFile):
            os.unlink(self.tmpFile)
        #import pdb; pdb.set_trace()
        elements[0].click()
        # expecting download.csv
        # wait for up to 15 seconds
        ##
        found = False
        ct = 0
        while found == False and ct < 15:
            ct = ct + 1
            if os.path.isfile(self.tmpFile):
                found = True
            if found == False:
                time.sleep(1)

        if found:
            dataRecs = {}
            fp = open(self.tmpFile,'r')
            hdr = fp.readline()
            hdr = fp.readline().strip()
            data = hdr.split(",")
            dataSite = data[1]
            # Verify dataSite is the site we want
            ##
            siteName = self.ws.meter['siteName']
            if dataSite == siteName:
                hdr = fp.readline()
                hdr = fp.readline()
                hdr = fp.readline()
                siteCode = self.ws.meter['siteCode']
                dataRecs = {siteCode: []}
                for f in fp:
                    ln = fp.readline().strip()
                    # Skip empty lines
                    ##
                    if ln == "":
                        continue
                    data = ln.split(',')
                    if data[1] != '--':
                        # Reformat data[0]
                        # 2020-04-22 6:45:00 -> 2020-04-22 06:45:00
                        ##
                        tmStr = data[0]
                        tmObj = dateutil.parser.parse(tmStr)
                        tmStr = tmObj.strftime("%Y-%m-%d %H:%M:%S")
                        rec = {'ob': tmStr, 'power': float(data[1])}
                        dataRecs[siteCode].append(rec)
                fp.close()
                os.unlink(self.tmpFile)

        return dataRecs

    # This always takes us to the main data page
    ##
    def gotoDataPage(self):
        if self.ws.driver == None:
            return

        # Return to data page
        ##
        # self.urlHeadDataPage
        if self.ws.driver.current_url != self.urlHeadDataPage:
            self.ws.log.msg("* Return to home page")
            self.ws.driver.find_element_by_xpath("//a[text()='Home']").click()
            xp = "//div[@class='data-label cell' and text()='Last 30 Days']"
            self.waitFor("xpath",xp,10)

        # Proceed to plant page
        ##
        siteName = self.ws.meter['siteName']
        xp = "//a[@class='dt-link' and text()='%s']" % (siteName)
        #import pdb; pdb.set_trace()
        siteElement = self.ws.driver.find_element_by_xpath(xp)
        siteElement.click()
        xp = "//div[@class='chartView hideWhileLoading']"
        self.waitFor("xpath",xp,10)


        # Make sure we are on AC Output
        ##

        # Select "1D" page
        # Wait for:
        # <div class="chartView hideWhileLoading" style="display: block;">
        # while page is reloading, style is "display: none;"
        ##
        # Make sure we are on the 1D view
        # There are more than one, it is always the
        # first one.
        # //li[@duration='1D']
        ##
        xp = "//li[@duration='1D']"
        elements = self.ws.driver.find_elements_by_xpath(xp)
        elements[0].click();
        xp = "//div[@class='chartView hideWhileLoading' and @style='display: block;']"
        self.waitFor("xpath",xp,10)

        return

    def gotoLoginPage(self):
        if self.ws.driver == None:
            return

        self.ws.driver.get(self.urlLogin)
        self.waitFor("idClick","userId",10)
        return

    def setCapabilities(self,cap):
        return cap

    def setProfile(self,pro):
        pro.set_preference('browser.download.folderList', 2) # custom location
        pro.set_preference('browser.download.manager.showWhenStarting', False)
        pro.set_preference('browser.download.dir', self.tmpDir)
        pro.set_preference('browser.helperApps.neverAsk.saveToDisk', 'text/csv')
        return pro

    def setWebScraper(self,ws):
        '''Pass web scraper class to this class'''
        self.ws = ws
        return

    # Wrapper for explicit waits
    # https://selenium-python.readthedocs.io/waits.html
    ##
    def waitFor(self,elementType,elementValue,elementTimeout):

        element = None
        wait = WebDriverWait(self.ws.driver,elementTimeout)
        try:
            if elementType == "idClick":
                element = wait.until(EC.element_to_be_clickable((By.ID,elementValue)))
            if elementType == "class":
                element = wait.until(EC.element_to_be_clickable((By.CLASS_NAME,elementValue)))
            if elementType == "idNotPresent":
                element = wait.until(EC.invisibility_of_element_located((By.ID,elementValue)))
            if elementType == "xpath":
                element = wait.until(EC.visibility_of_element_located((By.XPATH,elementValue)))
        except:
            pass

        self.lastElement = element
        return

