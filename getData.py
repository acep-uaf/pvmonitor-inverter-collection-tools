#!/usr/bin/python3

# GET data example for BMON
##
#/bin/bash
#curl -s "http://localhost/pvmonitor/api/v1/readings/Anchorage1B/?timezone=UTC&start_ts=2020-04-15%2018:19:48&end_ts=2020-04-15%2018:19:48" | json_pp

import os, sys, requests, json

url = 'http://localhost/pvmonitor/api/v1/readings/Anchorage1B/'

payload = {
    'timezone': 'UTC',
    'start_ts': '2020-04-15 18:19:48',
    'end_ts': '2020-04-15 18:19:48'
}

r = requests.get(url, params=payload)
j = json.loads(r.text)

for rec in j['data']['readings']:
    print(rec)
