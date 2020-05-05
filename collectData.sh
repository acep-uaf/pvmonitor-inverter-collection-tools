#!/bin/bash

# Main data gathering
# script
##
./gatherData.py

# Run specific debug items
##
#./gatherDataBeta.py -g AP1 -d

killall -q firefox
exit

echo "run_sunny_portal.py"
python run_sunny_portal.py
killall -9 chromedriver
sleep 2

echo "run_Ruby.py"
python run_Ruby.py
killall -9 chromedriver
sleep 2

echo "run_Manley.py"
python run_Manley.py
killall -9 chromedriver
sleep 2

