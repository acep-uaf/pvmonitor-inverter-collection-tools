import ACEP_AuroraVision
from requests import post
from datetime import datetime
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--username", help="The username for access to the website")
parser.add_argument("-p", "--password", help="the password to access the website")

args = parser.parse_args()

# I removed deering from this list since it was already on pvmoniter
# to add back just add "Deering WP" to the current site list
# same with Kobuk: "Kobuk WP" and Noatak: "Noatak WP" and Noorvik: "Noorvik"

current_site_list = ["Ambler WTP", "Buckland WTP", "Kiana WTP", "Kivalina WTP",
                     "Kotzebue Bailing", "Kotzebue WTP",
                     "Selawik WTP", "Shungnak WTP"]

post_urls = ["https://psi.alaska.edu/pvmonitor/readingdb/reading/AmblerWTP/store/",
             "https://psi.alaska.edu/pvmonitor/readingdb/reading/BucklandWTP/store/",
             "https://psi.alaska.edu/pvmonitor/readingdb/reading/KianaWTP/store/",
             "https://psi.alaska.edu/pvmonitor/readingdb/reading/KivalinaWTP/store/",
             "https://psi.alaska.edu/pvmonitor/readingdb/reading/KotzebueBailing/store/",
             "https://psi.alaska.edu/pvmonitor/readingdb/reading/KotzebueWTP/",
             "https://psi.alaska.edu/pvmonitor/readingdb/reading/SelawikWTP/store/",
             "https://psi.alaska.edu/pvmonitor/readingdb/reading/ShungankWTP/store/"]

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