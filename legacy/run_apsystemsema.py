#!/opt/local.acep/bin/python2.7
import apsystemsema_Acep
from requests import post
from datetime import datetime
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--username", help="The username for access to the website")
parser.add_argument("-p", "--password", help="the password to access the website")
parser.add_argument("-s", "--posting_url", help="url to post the data to")

args = parser.parse_args()

# I took out Noorvik since it is working somewhere else with another script
# Noorvik username "AKVEC"
# Noorvik password "akvecadmin"
# Noorvik post strings "https://psi.alaska.edu/pvmonitor/readingdb/reading/Noorvik/store/"
# Just add these to the lists below to get Noorvik

username = args.username
password = args.password
post_url = args.posting_url


driver = apsystemsema_Acep.ACEP_apsys(username, password)
kwatts = driver.ACEP_get_inverter_data()
print(kwatts)
kwatts = float(kwatts)
if type(kwatts) != float or type(kwatts) != int:
    print("failure")
    

r = post(post_url,
                data={
                      'storeKey': 'PutStorageKeyHere',
                      'val': str(kwatts),
                      'ts': datetime.utcnow()
                  })
print(kwatts.ACEP_get_inverter_data())