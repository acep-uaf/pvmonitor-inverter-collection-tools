#Currently being run somewhere else so I have not updated along with the rest of the scripts

from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import smtplib



'''
This class will grab the current inverter data for any number of sites that exist for the user password combination
it will then return the wattage values for those sites in a list. This code is dependent on the sites list provided
matching the html that this script will encounter. This is to prevent data from being inputted into the wrong place

username: the username for access the inverter
password: the password for accessing the inverter
site_list: this is important. we need to know that the data we are getting is the correct data for the site that we have
    otherwise we will end up either having not enough data for the number of sites that we expect. The other possibility
    is that we grab data for the wrong site. So make sure this matches the sites shown on the user password combination
    and that we are inputting the data into the correct place
chrome_driver_path: path to the chrome driver executable
login url: url to the login
system url: url to the page where the current wattage is found
email stuff: All of the values are for the error emails that are set if something goes wrong with the cron job
driver: the headless chrome driver
'''
class Enlighten_Sites:
    def __init__(self, username, password, site_list):
        self.username = username
        self.password = password
        self.site_list = site_list
        self.chrome_driver_path = "/usr/bin/chromedriver"
        self.login_url = "https://enlighten.enphaseenergy.com/"
        self.system_url = "https://enlighten.enphaseenergy.com/systems?"
        self.error_email_from_addr = "reminderforerrors@gmail.com"
        self.email_to_address = "nwcrockett@alaska.edu"
        self.email_cc_addr = "erin.whitney@alaska.edu, cpike6@alaska.edu"
        self.email_login = "reminderforerrors@gmail.com"
        self.email_password = "Iyuaabaygkag87@#"
        self.email_subject = "error in enlighten cron job"

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920x1080")

        self.driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=self.chrome_driver_path)

    '''
    This function sends out an email using a google email account that is provided.
    It is mainly used for error reporting in event of a cron job failure
    '''
    def send_error_email(self, from_addr, to_addr_list, cc_addr_list,
                         subject, message,
                         login, password,
                         smtpserver='smtp.gmail.com:587'):
        header = 'From: %s\n' % from_addr
        header += 'To: %s\n' % ','.join(to_addr_list)
        header += 'Cc: %s\n' % ','.join(cc_addr_list)
        header += 'Subject: %s\n\n' % subject
        message = header + message

        server = smtplib.SMTP(smtpserver)
        server.starttls()
        server.login(login, password)
        problems = server.sendmail(from_addr, to_addr_list, message)
        server.quit()
        return problems

    '''
    Runs the login process for accessing the website. This has to be the first function used in getting the data
    '''
    def login(self):
        try:
            self.driver.get(self.login_url)
            time.sleep(5)

            uname = self.driver.find_element_by_name("user[email]")
            uname.send_keys(self.username)

            pword = self.driver.find_element_by_name("user[password]")
            pword.send_keys(self.password)

            self.driver.find_element_by_id("submit").click()
            time.sleep(5)
        except:
            time.sleep(2)
            self.driver.quit()
            error = "Login Process " + self.username + "  " + self.password
            self.send_error_email(self.error_email_from_addr, self.email_to_address,
                                  self.email_cc_addr, self.email_subject,
                                  error, self.email_login, self.email_password)


    '''
    grabs the actual html where the current wattage exists. Luckily it will also grab the site name of the inverters
    This allows for error checking since in this code we are grabbing wattage for multiple sites
    '''
    def get_html(self):
        try:
            self.driver.get(self.system_url)

            time.sleep(10)
            html_source = self.driver.page_source
            soup = BeautifulSoup(html_source, "html.parser")

            return soup.find_all("td", )
        except:
            time.sleep(2)
            self.driver.quit()
            error = "grabbing html " + self.username + "  " + self.password
            self.send_error_email(self.error_email_from_addr, self.email_to_address,
                                  self.email_cc_addr, self.email_subject,
                                  error, self.email_login, self.email_password)
    '''
    This parses the html that we got to pull out the actual wattage data that we need. It has an error checker inside of
    it that checks to make sure the sites list provided are in order with the sites shown on the html in the website.
    I'm not exactly happy with the current version of this error checker but it does work so I'm leaving it in for now.
    
    The wattage values will be returned in a list that corresponds with the order of the site list provided. 
    '''
    def parse_html_get_data(self, html):
        try:
            site_counter = 0

            correct_site = 1

            watts = []

            for item in html:

                if self.site_list[site_counter] in str(item):
                    site_counter += 1

                if "kWh" in str(item) and not ("MWh" in str(item)):
                    if site_counter == correct_site:
                        correct_site += 1
                        temp = str(item).split(">")
                        data = temp[2].split("<")
                        watts.append(int(float(data[0]) * 1000))
                    else:
                        time.sleep(2)
                        self.driver.quit()
                        error = "site list on website has changed from the provided list " + self.username + "  " + self.password
                        self.send_error_email(self.error_email_from_addr, self.email_to_address,
                                          self.email_cc_addr, self.email_subject,
                                          error, self.email_login, self.email_password)
                        print("site list is incorrect")
                        quit()
                elif "Wh" in str(item) and not ("MWh" in str(item)):
                    if site_counter == correct_site:
                        correct_site += 1
                        temp = str(item).split(">")
                        data = temp[2].split("<")
                        watts.append(int(data[0]))
                    else:
                        time.sleep(2)
                        self.driver.quit()
                        error = "site list on website has changed from the provided list " + self.username + "  " + self.password
                        self.send_error_email(self.error_email_from_addr, self.email_to_address,
                                              self.email_cc_addr, self.email_subject,
                                              error, self.email_login, self.email_password)
                        print("site list is incorrect")
                        quit()

                if site_counter == len(self.site_list):
                    # Gone over the total number of sites
                    site_counter = 0
                    correct_site = 0

            time.sleep(2)
            self.driver.quit()

            return watts
        except:
            time.sleep(2)
            self.driver.quit()
            error = "parsing html " + self.username + "  " + self.password
            self.send_error_email(self.error_email_from_addr, self.email_to_address,
                                  self.email_cc_addr, self.email_subject,
                                  error, self.email_login, self.email_password)

    '''
    Runs the script to grab the data
    '''
    def run(self):
        self.login()
        return self.parse_html_get_data(self.get_html())





