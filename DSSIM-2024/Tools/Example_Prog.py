
# coding: utf-8

# In[125]:


from scipy import stats
import time
import struct
import numpy as np
# this part adds the path to the Python library so it can be used later
import sys, os
from os import system, name
# sys.path.insert(0,r'C:\DSSim-PC\V-06_64\Python_Lib')
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

for x in range(0,NumHours):
    data = ODGTCP.stepIn()
    time.sleep(0.2)           # A time delay to see what's going on
    ODGTCP.sendCommand('select PVSystem.pv_3')
    PVkW=abs(float(ODGTCP.sendCommand('powers').pop(0).decode("utf-8").replace(',','')))
    SOC_2 = float(ODGTCP.sendCommand('? Storage.sto_2.%stored').pop(0).decode('utf-8').replace(',',''))
    if PVkW >= 485:
        if SOC_2 > 25 and rechargeflag == 0:
            ODGTCP.sendCommand('SwtControl.sw_2.Action=Open')
            ODGTCP.sendCommand('SwtControl.sw_mg_sp_2.Action=Close')
            ODGTCP.sendCommand('Storage.sto_2.state=DISCHARGING')
        else:
            ODGTCP.sendCommand('SwtControl.sw_mg_sp_2.Action=Open')
            ODGTCP.sendCommand('SwtControl.sw_2.Action=Close')
            ODGTCP.sendCommand('Storage.sto_2.state=CHARGING')
    else:
        if SOC_2 > 25 and rechargeflag == 0:
            ODGTCP.sendCommand('SwtControl.sw_2.Action=Open')
            ODGTCP.sendCommand('SwtControl.sw_mg_sp_2.Action=Close')
            ODGTCP.sendCommand('Storage.sto_2.state=DISCHARGING')
        else:
            if rechargeflag == 1:
                if SOC_2 >= rechargelimit:
                    rechargeflag = 0
                print('Verifying the battery charge')
            else:
                print('Charging the battery using the grid')
                ODGTCP.sendCommand('SwtControl.sw_mg_sp_2.Action=Open')
                ODGTCP.sendCommand('SwtControl.sw_2.Action=Close')
                ODGTCP.sendCommand('Storage.sto_2.state=CHARGING')
                rechargeflag = 1

    system('cls')
    print('Power delivered by PV_3 (kW per phase): ' + str(PVkW))
    print('Battery SoC: ' + str(SOC_2))


ODGTCP.closeTCPConnection()