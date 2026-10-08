
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
ODGTCP.setColorMode(1)

MyList = ODGTCP.getLineNames()

# Uses only the first 3 lines on the list
LineList = []
for idx in range(3):
    LineList.append(MyList[idx].decode('utf-8'))

ODGTCP.SetLineList(LineList)
myColors = [0xFF0000,0x00FF00,0x0000FF]


for Color in myColors:
    Colors = []
    for Line in LineList:
        Colors.append(Color)
        

    ODGTCP.setLineColors(Colors)
    ODGTCP.RefreshGUI()
    time.sleep(3)


ODGTCP.closeTCPConnection()