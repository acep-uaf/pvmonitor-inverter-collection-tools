'''
MIT License

Copyright (c) [year] [fullname]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import ACEP_AuroraVision
from requests import post
from datetime import datetime
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--username", help="The username for access to the website")
parser.add_argument("-p", "--password", help="the password to access the website")

args = parser.parse_args()

current_site_list = ["Ruby Health Clinic"]

post_urls = ["https://psi.alaska.edu/pvmonitor/readingdb/reading/RubyHealthClinic/store/"]

username = args.username
password = args.password


for item, url in zip(current_site_list, post_urls):
    grabber = ACEP_AuroraVision.Aurora_Vision_Sites(username, password, item)
    watts = grabber.run()
    print(watts)
    r = post(url,
             data={
                 'storeKey': 'PutStorageKeyHere',
                 'val': str(watts / 1000),
                 'ts': datetime.utcnow()
             })