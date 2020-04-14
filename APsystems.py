import os, time, dateutil.parser, datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

        #print(self.urlLogin)
        #print(loginUsername,loginPassword)
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
        self.ws.driver.find_element_by_id("module_head").click()
        # wait for id='powerSlider' to exist
        # wait for id='navigator0' to exist
        # wait for class='highcharts-axis-labels'
        ##
        #self.waitFor("class","highcharts-axis-labels",10)
        self.waitFor("idNotPresent","loadingDialog",10)

    def gotoLoginPage(self):
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

        wait = WebDriverWait(self.ws.driver,elementTimeout)
        try:
            if elementType == "idClick":
                element = wait.until(EC.element_to_be_clickable((By.ID,elementValue)))
            if elementType == "class":
                element = wait.until(EC.element_to_be_clickable((By.CLASS_NAME,elementValue)))
            if elementType == "idNotPresent":
                element = wait.until(EC.invisibility_of_element_located((By.ID,elementValue)))
        except:
            pass

        return
