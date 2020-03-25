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
import re
import smtplib
import os.path

'''
This class will grab the current inverter data for any site that exist for the user password combination
it will then return the current wattage values for that site. This code is dependent on the site name provided
matching the exact hyperlink. If the username password combination and site name does not exist it will not work.

username: the username for access the inverter
password: the password for accessing the inverter
site_name: The hyperlink site name for the site wanted
login url: url to the login
system url: url to the page where the current wattage is found
email_(name): All of the values are for the error emails that are set if something goes wrong with the cron job
driver: the headless chrome driver
(name)_errors: Contains the number of errors that is stored in a text file
'''
class Sunny_Portal_Sites:
    def __init__(self, username, password, site_name):
        self.username = username
        self.password = password
        self.site_name = site_name
        self.chrome_driver_path = "/usr/bin/chromedriver"
        self.login_url = "https://www.sunnyportal.com/Templates/Start.aspx?ReturnUrl=%2fTemplates%2fNoticePage.aspx"
        self.error_email_from_addr = "reminderforerrors@gmail.com"
        self.email_to_address = "nwcrockett@alaska.edu"
        self.email_cc_addr = "erin.whitney@alaska.edu, cpike6@alaska.edu"
        self.email_login =  "reminderforerrors@gmail.com"
        self.email_password =  "Iyuaabaygkag87@#"
        self.email_subject = "error in sunny portal " + self.site_name + " cron job"
        self.login_errors = 0
        self.grab_html_errors = 0
        self.parse_html_errors = 0
        self.failure_number = 0
        self.successful_uploads = 0

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920x1080")

        self.driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=self.chrome_driver_path)

    '''
    Inputs the error type and number from a text file that has the name of the site.
    '''
    def input_error_rates(self):
        with open(self.site_name + ".txt", "r") as f:
            content = f.readlines()

        content = [x.strip("\n") for x in content]
        self.login_errors = int(content[0])
        self.grab_html_errors = int(content[1])
        self.parse_html_errors = int(content[2])
        self.failure_number = int(content[3])
        self.successful_uploads = int(content[4])
        f.close()

    def write_error_rates(self):
        with open(self.site_name + ".txt", "w") as f:
            f.write(str(self.login_errors) + "\n")
            f.write(str(self.grab_html_errors) + "\n")
            f.write(str(self.parse_html_errors) + "\n")
            f.write(str(self.failure_number) + "\n")
            f.write(str(self.successful_uploads) + "\n")

        f.close()

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
    If the point is hit where enough errors have occurred to require an error message this function sends it
    '''
    def error_report(self):
        error = "login errors " + str(self.login_errors) + "\n" + \
        "grab html errors " + str(self.grab_html_errors) + "\n" + \
        "parse html errors " + str(self.parse_html_errors) + "\n" + \
        "failure total " + str(self.failure_number) + "\n" + \
        "successful upload in row " + str(self.successful_uploads) + "\n"
        self.send_error_email(self.error_email_from_addr, self.email_to_address,
                              self.email_cc_addr, self.email_subject,
                              error, self.email_login, self.email_password)


    '''
    Runs the login process for accessing the website. This has to be the first function used in getting the data
    '''
    def login(self):
        try:
            self.driver.get(self.login_url)
            time.sleep(5)

            uname = self.driver.find_element_by_id("txtUserName")
            uname.send_keys(self.username)

            pword = self.driver.find_element_by_id("txtPassword")
            pword.send_keys(self.password)

            self.driver.find_element_by_name("ctl00$ContentPlaceHolder1$Logincontrol1$LoginBtn").click()
            time.sleep(5)

        except:
            time.sleep(2)
            self.driver.quit()
            self.login_errors += 1
            self.failure_number += 1
            self.write_error_rates()
            if self.failure_number > 100:
                self.error_report()
            quit()



    '''
    Grabs the actual html where the current wattage exists at the site name provided
    Loading for this site takes forever which is why the long load time is included
    '''
    def get_html(self):
        try:
            self.driver.find_element_by_link_text(self.site_name).click()
            time.sleep(20)

            html = self.driver.page_source

            soup = BeautifulSoup(html, "html.parser")

            latest_power = soup.find_all("span", attrs={"class": "mainValueAmount"})
            return latest_power

        except:
            time.sleep(2)
            self.driver.quit()
            self.grab_html_errors += 1
            self.failure_number += 1
            self.write_error_rates()
            if self.failure_number > 100:
                self.error_report()
            quit()



    '''
    This parses the html that we got to pull out the actual wattage data that we need.  
    '''
    def parse_html_get_data(self, html):
        try:
            time.sleep(2)
            wattage = 0
            for item in html:
                if "data-peak" in str(item):
                    temp = re.split('<|>', str(item))
                    if temp[2] != "-":
                        wattage = int(float(temp[2]))

            time.sleep(2)
            self.driver.quit()
            self.successful_uploads += 1
            if self.successful_uploads > 5:
                self.login_errors = 0
                self.grab_html_errors = 0
                self.parse_html_errors = 0
                self.failure_number = 0
                self.successful_uploads = 0

            self.write_error_rates()
            if wattage == None:
                wattage = 1

            return wattage
        except:
            time.sleep(2)
            self.driver.quit()
            self.parse_html_errors += 1
            self.failure_number += 1
            self.write_error_rates()
            if self.failure_number > 100:
                self.error_report()
            quit()

    '''
    Runs the script to grab the data
    '''

    def run(self):
        if not os.path.isfile(self.site_name + ".txt"):
            self.write_error_rates()
        self.input_error_rates()
        self.login()
        return self.parse_html_get_data(self.get_html())
