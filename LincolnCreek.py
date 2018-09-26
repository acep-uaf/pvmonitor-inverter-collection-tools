#!/usr/bin/python

# pvmonitor key = PutStorageKeyHere

import os, sys, requests
import time
from calendar import timegm
from datetime import datetime

# PART 1: Data collection
##

# Get current PV value
# Scrape data from Rob's site
# This is a non-standard data source
##
r = requests.get('https://jupyter.lccllc.info:4443/power/pwr.php?MATE=3')

if r.status_code != 200:
  # Failed to get a good return code from the site
  ##
  sys.exit()
data = r.text.split("\n")

# Parse message looking for solar data
# (c) block: Outback FlexMax60 via MATE1 serial
# 2018-04-12T06:42:32Z,c,0140,0001,0000,11,00140,248,097,000,26,08,110
##
solar = {}
for ln in data:
  cs = ln.split(',')
  # Look for a lot of comma separated values
  ##
  if len(cs) > 10:
    # c block in position 1? and there are 13 values
    ##
    if cs[1] == "c" and len(cs) == 13:
      # GMT time is position 0
      # Solar data is shunt B or position 3 in amps (need to scale by 0.1)
      #   System is 24V so multiply by 24 to get watts and divide by 1000 to get kW
      #   System has transient voltage, floor it to zero if below 10W
      ##
      kw = (((int(cs[3]) / 10.0) * 24.0) / 1000.0)
      if kw < 0.01: kw = 0.00
      solar['kw'] = kw
      solar['tm'] = cs[0]

# Part 2
# Posting data to BMON server for a single sensor
##

# If we have data, try and post it.  
##
if 'kw' in solar.keys(): 

  # Convert time to an integer timestamp
  # The BMON server wants integer timestamps in GMT/UTC time
  # We have to do some shinanigans to get the timestamp in UTC
  ##
  iso_string = solar['tm']
  pv = solar['kw']

  # A single entry wants a GMT date string
  # Multiple entries wants a integer time stamp
  # http://bmon-documentation.readthedocs.io/en/latest/setting-up-sensors-to-post-to-bmon.html
  ##
  tm = timegm(time.strptime(iso_string.replace('Z', 'GMT'),'%Y-%m-%dT%H:%M:%S%Z')) 
  tm = datetime.utcfromtimestamp(tm).isoformat()

  # ACEP psi.alaska.edu
  # The storeKey is a GLOBAL key to upload/post data to the server.  The key is
  # unfortinately weak.  The key is used for all sensors.
  ##
  r = requests.post('https://psi.alaska.edu/pvmonitor/readingdb/reading/LincolnCreek/store/',
  data = {
    'storeKey':'PutStorageKeyHere',
    'val':str(pv),
    'ts':tm
  })

  #print r.status_code
  #print r.text
