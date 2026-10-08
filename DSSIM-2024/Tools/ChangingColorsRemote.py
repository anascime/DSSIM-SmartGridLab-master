
# coding: utf-8


from scipy import stats
import time
import struct
import numpy as np
# this part adds the path to the Python library so it can be used later
import sys, os
from os import system, name 
# Now you can import the library
import openDSSGTCP as dssTCP


# Connecting to OpenDSS-G
TCP_IP = '127.0.0.1'
TCP_PORT = 6345
BUFFER_SIZE = 20000

ODGTCP = dssTCP.OpenDSSGTCP(TCP_IP, TCP_PORT, BUFFER_SIZE)
ODGTCP.startTCPConnection()
# Configures OpenDSS-G remotely
ODGTCP.sendCommand('set time=(0,0) mode=time controlmode=time stepsize=1h number=1')
rechargelimit = 80   # sets that the storage needs to be charged at least to 80% to be operational
rechargeflag = 0     # is used to tell the system if the storage is charging
time.sleep(0.1)
NumHours = 240        # the number of hours to simulate

MyList = ODGTCP.getLineNames()

myColors = [0xFF0000,0x00FF00,0x0000FF]

for Color in myColors:
    Colors = []
    for Line in MyList:
        Colors.append(Color)
        
    ODGTCP.setColorMode(1)
    ODGTCP.setLineColors(Colors)
    ODGTCP.RefreshGUI()
    time.sleep(3)


ODGTCP.closeTCPConnection()