#!/bin/bash

# Temporary data collection script
##

# This does not use chromedriver
# as a webscraper.
##
echo "LincolnCreek.py"
python3 LincolnCreek.py

# New main routine for
# other solar systems
##
./gatherData.py
killall -q firefox

# Run specific debug items
##
#./gatherDataBeta.py -g AP1 -d

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

echo "run_AuroraVision.py"
python run_AuroraVision.py
killall -9 chromedriver
sleep 2

echo "run_apsystemsema.py"
python run_apsystemsema.py
killall -9 chromedriver
sleep 2

