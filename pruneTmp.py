#!/usr/bin/python3

# Prune /tmp entries created by the 
# web scraper.
##
#$ ls -l --full-time
#total 176
#-rwxrw-r-- 1 psi psi  6573 2020-04-21 17:51:26.535689075 +0000 APsystems.py
#-rwxrw-r-- 1 psi psi  5588 2020-04-22 00:44:24.559436092 +0000 AuroraVision.py
#-rwxrw-r-- 1 psi psi  2264 2020-04-21 17:50:23.078680821 +0000 CloudModuleTemplate.py

import os, sys
import shutil
import dateutil.parser, datetime, pytz
import subprocess

os.chdir("/tmp")
cdir = os.getcwd()
if cdir != "/tmp":
    sys.exit()

subProcData = subprocess.run(['ls', '-l', '--full-time'], stdout=subprocess.PIPE).stdout.decode('utf-8')
# drwx------  2 psi  psi  4096 2020-04-15 18:23:06.499162111 +0000 tmpzscu9kj7
directories = subProcData.split("\n")
tm = datetime.datetime.now()
tm = pytz.timezone('UTC').localize(tm)
for ln in directories:
    dataStr = ln.strip()
    dataTmp = dataStr.split(" ")
    data = []
    for r in dataTmp:
        if r != '':
            data.append(r)
    if len(data) > 7:
        rDir = data[-1]
        if data[2] == 'psi':
            if os.path.isdir(rDir):
                dtStr = "%s %s %s" % (data[5],data[6],data[7])
                dt = dateutil.parser.parse(dtStr)
                delta = tm-dt
                # Convert to days
                ##
                delta = delta.total_seconds() / (24.0 * 60.0 * 60.0)

                #print(rDir,delta)
                if delta > 1.0:
                    shutil.rmtree(rDir)
