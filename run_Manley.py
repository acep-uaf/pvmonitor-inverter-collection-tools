import ACEP_AuroraVision
from requests import post
from datetime import datetime
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--username", help="The username for access to the website")
parser.add_argument("-p", "--password", help="the password to access the website")

args = parser.parse_args()

current_site_list = ["Manley Tribal Council"]

post_urls = ["https://psi.alaska.edu/pvmonitor/readingdb/reading/ManleyTribalCouncil/store/"]

username = args.username
password = args.password

for item, url in zip(current_site_list, post_urls):
    grabber = ACEP_AuroraVision.Aurora_Vision_Sites(username, password, item)
    watts = grabber.run()
    if watts == None:
        watts = 0
    print(watts)
    r = post(url,
             data={
                 'storeKey': 'PutStorageKeyHere',
                 'val': str(watts / 1000),
                 'ts': datetime.utcnow()
             })
