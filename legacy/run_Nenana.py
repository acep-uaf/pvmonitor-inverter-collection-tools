import Nenana_teen_center
from requests import post
from datetime import datetime
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--username", help="The username for access to the website")
parser.add_argument("-p", "--password", help="the password to access the website")

args = parser.parse_args()

username = args.username
password = args.password

grabber = Nenana_teen_center.NenanaEnlighten(username, password)

# the class returns watts must divide by 1000 to get KW

watts = grabber.run()
r = post('https://psi.alaska.edu/pvmonitor/readingdb/reading/NenanaTeenCenter/store/',
  data = {
    'storeKey':'PutStorageKeyHere',
    'val':str(watts / 1000),
    'ts':datetime.utcnow()
  })


print(watts)