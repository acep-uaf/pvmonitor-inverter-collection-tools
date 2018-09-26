#!/opt/local.acep/bin/python2.7
# Currently being run somewhere else so I have not updated along with the rest of the scripts
# Same reason for why there is no posting addition to this script

import ACEPenlighten

#this currently returns a list of three elements. Please alter the return as needed.

username = "Sminnema@irha.org"
password = "steveiscool777"

sites = ["ARTIC VILLAGE", "Koyukuk", "ruby"]

grabber = ACEPenlighten.Enlighten_Sites(username, password, sites)

print(grabber.run())
