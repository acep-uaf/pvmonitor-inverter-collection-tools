import time
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
        self.driver = None

    def doLogin(self,credentials):
        #print(credentials)
        loginUsername = credentials["meterUsername"]
        loginPassword = credentials["meterPassword"]

        formUsername = self.driver.find_element_by_name("username")
        formPassword = self.driver.find_element_by_name("password")

        formUsername.send_keys(loginUsername)
        formPassword.send_keys(loginPassword)
        
        self.driver.find_element_by_id("Login").click()
        self.waitFor("idClick","datetime_val",10)

        print(self.urlLogin)
        print(loginUsername,loginPassword)
        return

    def doLogout(self):
        linkSignout = self.driver.find_element_by_link_text("Sign out")
        linkSignout.click()
        self.waitFor("idClick","Login",10)
        return

    def gotoDataPage(self):
        self.driver.find_element_by_id("module_head").click()
        # wait for id='powerSlider' to exist
        # wait for id='navigator0' to exist
        ##
        self.waitFor("idClick","ArrayViewforHightChart",10)

    def gotoLoginPage(self):
        self.driver.get(self.urlLogin)
        self.waitFor("idClick","Login",10)
        return

    def setDriver(self,driver):
        self.driver = driver
        return

    def setCapabilities(self,cap):
        return cap

    # APsystems website does not use latest TLS 1.2 protocol
    ##
    def setProfile(self,pro):
        pro.set_preference("security.tls.version.min",1)
        return pro

    # Wrapper for explicit waits
    # https://selenium-python.readthedocs.io/waits.html
    ##
    def waitFor(self,elementType,elementValue,elementTimeout):

        wait = WebDriverWait(self.driver,elementTimeout)
        try:
            if elementType == "idClick":
                element = wait.until(EC.element_to_be_clickable((By.ID,elementValue)))
        except:
            pass

        return
