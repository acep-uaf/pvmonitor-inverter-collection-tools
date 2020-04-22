import os, time, dateutil.parser, datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# DEBUG
# import pdb; pdb.set_trace()
##

# APsystems
# Web page communications module
# Required class functions
#   setCapabilities()
#   setProfile()
##

class APsystems:
    def __init__(self):
        self.urlLogin = "https://apsystemsema.com/ema/index.action"
        self.ws = None
        self.testing = False
        self.lastElement = None

    def doLogin(self,credentials):
        #print(credentials)
        loginUsername = credentials["meterUsername"]
        loginPassword = credentials["meterPassword"]

        formUsername = self.ws.driver.find_element_by_name("username")
        formPassword = self.ws.driver.find_element_by_name("password")

        formUsername.send_keys(loginUsername)
        formPassword.send_keys(loginPassword)
        
        self.ws.driver.find_element_by_id("Login").click()
        self.waitFor("idClick","datetime_val",10)

        if self.ws.debug:
            print(self.urlLogin)
            print(loginUsername,loginPassword)

        return

    def doLogout(self):
        linkSignout = self.ws.driver.find_element_by_link_text("Sign out")
        linkSignout.click()
        self.waitFor("idClick","Login",10)
        return

    # Once we are at the main data page, we have to cycle through
    # all available ECUs.
    ##
    def getDataRecords(self):
        dataRecs = {}
        # Get list of ECUs available and match them up
        # with our internal unitNames.
        ##
        ecuUnits = []
        ecuUnitObj = self.ws.driver.find_elements_by_xpath("//div[@id='uniform-ecuid']//option")

        # Currently selected ECU
        ##
        try:
            currentECUText = self.ws.driver.find_element_by_id('ecuidspan').text
        except:
            self.ws.saveScreen("error.png")
            self.ws.dumpLog("error.log")
            pass
        currentECU = ""

        for ecu in ecuUnitObj:
            ecuValue = ecu.get_attribute('value')
            ecuText = ecu.text
            if ecuText == currentECUText:
                currentECU = ecuValue
            ecuUnits.append(ecuValue)

        # For each ECU collect solar data
        ##
        while ecuUnits:
            #self.saveScreen(currentECU+".png")
            # This adequately changes the date, but individual times are not accessible
            # Data is available every 5 minutes.  We may not need to actively click,
            # data may be scrapable right from the chart by day.
            #cmd = "document.getElementById('queryDate').value = '2020-04-11';"
            #res = self.ws.driver.execute_script(cmd)
            #print(res)
            #cmd = "$.getDataByLevel();"
            #res = self.ws.driver.execute_script(cmd)
            #self.waitFor("idNotPresent","loadingDialog",10)
            # Obtaining back data
            # (1) select date
            # (2) refresh
            # (3) var charName = "#ArrayViewforHightChart";
            # (4) var chart = $(charName).highcharts();
            # (5) var xData = chart.series[0].points;
            # (6) Time(timestamp): xData[0].series.xData
            # (7) Solar(Watts)   : xData[0].series.yData
            ##
            self.ws.saveScreen(currentECU+".png")
            self.ws.dumpLog(currentECU+".log")
            # Collect data for ECU that do not show
            # "No Data".
            ##
            tobObj = self.ws.driver.find_element_by_class_name('selectedTime')
            tob = tobObj.text
            # Get the current date via javascript
            ##
            dob = self.ws.driver.execute_script("return $('#queryDate').val();")
            if tob != "No data":
                dataObjs = self.ws.driver.find_elements_by_xpath("//div[@class='Module layout num']")
                totalWatts = 0
                for rec in dataObjs:
                    totalWatts = totalWatts + int(rec.text)
                tm = "%s %s" % (dob,tob)
                dataRecs[currentECU] = {
                        'ob': tm,
                        'power': totalWatts
                        }
            ecuUnits.remove(currentECU)
            if ecuUnits:
                currentECU = ecuUnits[0]
                # Switch to this ECU
                ##
                fopt = "//div[@id='uniform-ecuid']//option[@value='%s']" % (currentECU)
                sopt = self.ws.driver.find_element_by_xpath(fopt)
                sopt.click()
                self.waitFor("idNotPresent","loadingDialog",10)

        return dataRecs

    # This always takes us to the main data page
    ##
    def gotoDataPage(self):
        if self.ws.driver == None:
            return

        self.ws.driver.find_element_by_id("module_head").click()
        # wait for id='powerSlider' to exist
        # wait for id='navigator0' to exist
        # wait for class='highcharts-axis-labels'
        ##
        #self.waitFor("class","highcharts-axis-labels",10)
        self.waitFor("idNotPresent","loadingDialog",10)
        return

    def gotoLoginPage(self):
        if self.ws.driver == None:
            return

        self.ws.driver.get(self.urlLogin)
        self.waitFor("idClick","Login",10)
        return

    def setCapabilities(self,cap):
        return cap

    # APsystems website does not use latest TLS 1.2 protocol
    ##
    def setProfile(self,pro):
        pro.set_preference("security.tls.version.min",1)
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
