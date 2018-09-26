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
import os.path


'''
This class is used to grab the web data for solar inverters for apsystemsema inverters
username is the entered username for the login account
password is the entered password for the login account
chromedriverPath is the path name to access the chromedriver for the headless chrome webscrapper
    Both having the correct path and the driver itself on the machine that is running the script is required
        for the script to actually run.
apsystesema_Login is the url to the apsystesema login web page
driver is the headless chrome driver

pass in username and password as strings only
'''
class ACEP_apsys:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.chromedriverPath = "/usr/bin/chromedriver"
        self.apsystesema_Login = "https://apsystemsema.com/ema/index.action"
        self.error_email_from_addr = "reminderforerrors@gmail.com"
        self.email_to_address = "nwcrockett@alaska.edu"
        self.email_cc_addr = "erin.whitney@alaska.edu, cpike6@alaska.edu"
        self.email_login = "reminderforerrors@gmail.com"
        self.email_password = "Iyuaabaygkag87@#"
        self.email_subject = "error in Apsystemsema " + self.username + " cron job"
        self.login_errors = 0
        self.grab_html_errors = 0
        self.parse_html_errors = 0
        self.failure_number = 0
        self.successful_uploads = 0

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920x1080")

        self.driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=self.chromedriverPath)

    def input_error_rates(self):
        with open(self.username + ".txt", "r") as f:
            content = f.readlines()

        content = [x.strip("\n") for x in content]
        self.login_errors = int(content[0])
        self.grab_html_errors = int(content[1])
        self.parse_html_errors = int(content[2])
        self.failure_number = int(content[3])
        self.successful_uploads = int(content[4])
        f.close()

    def write_error_rates(self):
        with open(self.username + ".txt", "w") as f:
            f.write(str(self.login_errors) + "\n")
            f.write(str(self.grab_html_errors) + "\n")
            f.write(str(self.parse_html_errors) + "\n")
            f.write(str(self.failure_number) + "\n")
            f.write(str(self.successful_uploads) + "\n")

        f.close()

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
    This function sends out an email using a google email account that is provided.
    It is mainly used for error reporting in event of a cron job failure
    '''
    def send_error_email(from_addr, to_addr_list, cc_addr_list,
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
        #print("quit driver")
        server.quit()
        return problems

    '''
    Takes in the result of the parsed html then looks for the span elements in it
    It will then parse those elements to get the wattage of the current values
    '''
    def parse_solar_array(self, html):
        soup = BeautifulSoup(html.get_attribute("innerHTML"), "html.parser")

        spans = soup.find_all('span')
        watts = 0
        for item in spans:
            span = str(item)
            if "position: absolute" in span:
                temp = span.split(">")
                part2 = temp[1].split("<")
                watts += int(part2[0])

        time.sleep(5)
        self.driver.quit()
        return watts / 1000

    '''
    This function does the actual functionality of grabbing the web data.
    It enters in the website login details then pulls up the webpage with the 
    current inverter data. Then returns that data.
    The try catch blocks in this code are for reporting via email that an error has
    occurred in the code. They do not actually handle the error. This is due to the massive
    amount of possible errors that can possibly exist as a result of website changes on apsystesema's
    side of things. 
    The only differentiation in the different parts of the try catch setup are indicators in what part of
    the whole process has failed
    '''
    def ACEP_get_inverter_data(self):
        if not os.path.isfile(self.username+ ".txt"):
            self.write_error_rates()
        self.input_error_rates()
        try:
            self.driver.get(self.apsystesema_Login)
            time.sleep(5)

            uname = self.driver.find_element_by_name("username")
            uname.send_keys(self.username)

            pword = self.driver.find_element_by_name("password")
            pword.send_keys(self.password)
            self.driver.find_element_by_id("Login").click()
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
        try:
            self.driver.find_element_by_id("module_head").click()
            time.sleep(10)
            array = self.driver.find_element_by_class_name("ArrayView")

        except:
            time.sleep(2)
            self.driver.quit()
            self.grab_html_errors += 1
            self.failure_number += 1
            self.write_error_rates()
            if self.failure_number > 100:
                self.error_report()
            quit()
        try:

            return self.parse_solar_array(array)
        except:
            time.sleep(2)
            self.driver.quit()
            self.parse_html_errors += 1
            self.failure_number += 1
            self.write_error_rates()
            if self.failure_number > 100:
                self.error_report()
            quit()

        self.successful_uploads += 1
        if self.successful_uploads > 5:
            self.login_errors = 0
            self.grab_html_errors = 0
            self.parse_html_errors = 0
            self.failure_number = 0
            self.successful_uploads = 0

        self.write_error_rates()

        time.sleep(3)
        #print("quit driver")
        self.driver.quit()
