#!/usr/bin/python3

import os, time, dateutil.parser, datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# DEBUG
# import pdb; pdb.set_trace()
##

# CloudModuleTemplate
# Web page communications module
# Required class functions
#   setCapabilities()
#   setProfile()
##

class Enlighten:
    def __init__(self):
        self.urlLogin = "https://enlighten.enphaseenergy.com/"
        self.urlLogout = "https://enlighten.enphaseenergy.com/logout"
        self.urlHeadDataPage = ""
        self.urlDataPageExample = ""
        self.ws = None
        self.testing = True
        self.lastElement = None

    def doLogin(self,credentials):
        return

    def doLogout(self):
        return

    def getDataRecords(self):
        dataRecs = {}

        return dataRecs

    # This always takes us to the main data page
    ##
    def gotoDataPage(self):
        if self.ws.driver == None:
            return
        return

    def gotoLoginPage(self):
        if self.ws.driver == None:
            return

        self.ws.driver.get(self.urlLogin)
        self.waitFor("idClick","Login",10)
        return

    def setCapabilities(self,cap):
        return cap

    def setProfile(self,pro):
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

