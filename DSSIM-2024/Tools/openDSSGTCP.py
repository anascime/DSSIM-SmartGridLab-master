# -*- coding: utf-8 -*-
"""
Created on Fri Sep 21 2018
Updated on Mon Oct 01 2018

@author: AC Melhorn

This module is to help with the TCP interface of OpenDSS-G.  It provides a
class with a variety of functions to interact with OpenDSS-G and several 
functions to parse through the resultant data.

The user current needs to run the following code in their main python 
file/function:
    import openDSSGTCP as dssTCP
    
    TCP_IP = '127.0.0.1'
    TCP_PORT = 6345
    BUFFER_SIZE = 20000
    
    # creates an object of the class
    ODGTCP = dssTCP.OpenDSSGTCP(TCP_IP, TCP_PORT, BUFFER_SIZE)
    # starts the TCP connection
    ODGTCP.startTCPConnection()
    
Now the user can run anyother class function or function built into the module.
Notes/comments are included with all the functions below.

Future work:
    - Add additonal funcationality as needed.
    - Allow the user to start OpenDSS-G and start a simulation from the script
    itself, instead of requiring the user to do a setup
"""


import socket


"""
Variables  and dictionaries for TCP commands and for 'yes' and 'no' answers
"""
# OpenDSS-G dictionary, makes it easier to know what the TCP commands are
COMMANDS = {
    'seconds': '01;',
    'Close': '&Q;',
    'days': '02;',
    'Vpu': '03;',
    'V': '04;',
    'CapC': '05;',
    'CapV': '06;',
    'CapL': '07;',
    'CapP': '08;',
    'XfrtC': '09;',
    'XfrtV': '10;',
    'XfrtL': '11;',
    'XfrtP': '12;',
    'LoadC': '13;',
    'LoadP': '14;',
    'LineC': '15;',
    'LineP': '16;',
    'LineL': '17;',
    'SwitchC': '18;',
    'Switch': '19;',
    #'FixPower': '1A;',
    #'FixElement': '1B;',
    'EnergyM': '1C;',
    'Inc_Mat': '1D;',
    'EVStorage_List': '1E;',
    'EVStorage_Status': '1F;',
    'SW_Currents': '20;',
    'SW_Losses': '21;',
    'SW_Powers': '22;',
    'Step_in': '23;',
    'End_Sim': '24;',
    'Command': '25;',
    'Monitors': '26;',
    #'Mon_data': '27;',
    'SetLineList': '28;',
    'SetLineColors': '29;',
    'SetColorMode': '30;',
    'RefreshGUI': '31;',
    'LineNames': '33;',
    'ShowOvLoads': '36;',
    'ShowVolt': '37;',
    'ShowPower': '38;',
    'ClearCtrlQueue': '3F;',
    'GetCtrlQueue': '40;',
    'ShowIsolated': '41;',
    'BusNames': '42;',
    'NodeNames': '43;',
    'LoadNames': '44;',
    'XfrtNames': '45;',
    'CapNames': '46;',
    'StorageNames': '47;'
}
# dictionary for turning things on and off
ONOFF = {
    'on': '1',
    'off': '0'
}


class OpenDSSGTCP:
    def __init__(self, TCP_IP, TCP_PORT, BUFFER_SIZE):
        self.TCP_IP = TCP_IP
        self.TCP_PORT = TCP_PORT
        self.BUFFER_SIZE = BUFFER_SIZE
        
    # start the TCP connection with OpenDSS-G
    def startTCPConnection(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.TCP_IP, self.TCP_PORT))
        
    # close the TCP connection with OpenDSS-G
    def closeTCPConnection(self):
        self.s.close()

    # request the time in seconds of the simulation
    def getTimeSeconds(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['seconds'])
        # return data
        return data
    
    # closes the TCP connection with OpenDSS-G
    def close(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['Close'])
        # return data
        return data
    
    # request the time in seconds of the simulation
    def getTimeDays(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['days'])
        # return data
        return data
    
    # request the system voltage magnitudes in per unit
    def getVoltsPU(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['Vpu'])
        # return data
        return data
    
    # request the system voltages (active and reactive values)
    def getVolts(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['V'])
        # return data
        return data
    
    # request the currents of the capacitors in the system
    def getCapsCurrents(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['CapC'])
        # return data
        return data
    
    # request the voltages of the capacitors in the system
    def getCapsVolts(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['CapV'])
        # return data
        return data
    
    # request the losses of the capacitors in the system
    def getCapsLosses(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['CapL'])
        # return data
        return data
    
    # request the power flows of the capacitors in the system
    def getCapsPowers(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['CapP'])
        # return data
        return data
    
    # request the currents of the transformers in the system
    def getXfrmsCurrents(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['XfrtC'])
        # return data
        return data
    
    # request the voltages of the transformers in the system
    def getXfrmsVolts(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['XfrtV'])
        # return data
        return data
    
    # request the losses of the transformers in the system
    def getXfrmsLosses(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['XfrtL'])
        # return data
        return data
    
    # request the power flows of the transformers in the system
    def getXfrmsPowers(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['XfrtP'])
        # return data
        return data
    
    # request the currents of the loads in the system
    def getLoadsCurrents(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['LoadC'])
        # return data
        return data
    
    # request the powers of the loads in the system
    def getLoadsPowers(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['LoadP'])
        # return data
        return data
    
    # request the currents of the lines in the system
    def getLinesCurrents(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['LineC'])
        # return data
        return data
    
    # request the powers of the loads in the system
    def getLinesPowers(self):
        # call the function to send TCP command and get the return data
        data =self. sendTCP(COMMANDS['LineP'])
        # return data
        return data
    
    # request the powers of the loads in the system
    def getLinesLosses(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['LineL'])
        # return data
        return data
    
    # set the switch to on or off
    def setSwitchControl(self, switchName, onORoff):
        # call the function to format the full TCP command
        message = formatTCPMessage(COMMANDS['SwitchC'], 
                                   switchName + '=' + ONOFF[onORoff])
        # call the function to send TCP command and get the return data
        data = self.sendTCP(message)
        # return data
        return data
    
    # request the statuses of the switches in the system
    def getSwitchesStatus(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['Switch'])
        # return data
        return data
    
    # request the information from the energy meters
    def getEnergyMeterData(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['EnergyM'])
        # return data
        return data
    
    # request the branc-node incidence matrix
    def getBranchNodeIncMatrix(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['Inc_Mat'])
        # return data
        return data
    
    # request the names of all EV and storage elements in the system
    def getEVStorageNames(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['EVStorage_List'])
        # return data
        return data
    
    # request the status of all EV and storage elements in the system
    def getEVStorageStatus(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['EVStorage_Status'])
        # return data
        return data
    
    # request the currents of all switches in the system
    def getSwitchesCurrents(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['SW_Currents'])
        # return data
        return data
    
    # request the losses of all switches in the system
    def getSwitchesLosses(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['SW_Losses'])
        # return data
        return data
    
    # request the powers of all switches in the system
    def getSwitchesPowers(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['SW_Powers'])
        # return data
        return data
    
    # Send the order to step in the simulation in DSSim-PC (only works in 
    # remote controlled mode)
    def stepIn(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['Step_in'])
        # return data
        return data
    
    # Finish the simulation in DSSim-PC (only works in remote controlled mode)
    def endSimulation(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['End_Sim'])
        # return data
        return data
    
    # function to send a command to OpenDSS-G using TCP
    def sendCommand(self, command):
        # call the function to format the full TCP command
        message = formatTCPMessage(COMMANDS['Command'], command) 
        # call the function to send TCP command and get the return data
        data = self.sendTCP(message)
        # format the data again since it was a direct command
        #data = formatCommandDataList(data)
        # return data
        return data
    
    # request the list of all monitors in the simulation
    def getMonitorsList(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['Monitors'])
        # return data
        return data
    
    # refreshes GUI to show the overloaded infrastructure
    def showOverLoads(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['ShowOvLoads'])
        # return data
        return data
    
    # refreshes GUI to show the voltage profile coloring each elements
    def showVoltages(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['ShowVolt'])
        # return data
        return data
    
    # refreshes GUI to show the power profile coloring each element
    def showPower(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['ShowPower'])
        # return data
        return data
    
    # clears the control queue??
    def clearControlQueue(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['ClearCtrlQueue'])
        # return data
        return data
    
    # requests the control queue??
    def getControlQueue(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['GetCtrlQueue'])
        # return data
        return data
    
    # refreshes the GUI to show the isolated zones in the system
    def showIsolated(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['ClearCtrlQueue'])
        # return data
        return data
    
    # requests all of the bus names in the simulation
    def getBusNames(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['BusNames'])
        # return data
        return data
    
    # requests all of the node names in the simulation
    def getNodeNames(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['NodeNames'])
        # return data
        return data
    
    # requests all of the load names in the simulation
    def getLoadNames(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['LoadNames'])
        # return data
        return data
    
    # requests all of the transformer names in the simulation
    def getXfrmNames(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['XfrtNames'])
        # return data
        return data
    
    # requests all of the capacitor names in the simulation
    def getCapNames(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['CapNames'])
        # return data
        return data
    
    # requests all of the storage device names in the simulation
    def getStorageNames(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['StorageNames'])
        # return data
        return data
    
    # requests all of the storage device names in the simulation
    def getLineNames(self):
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['LineNames'])
        # return data
        return data    
    
    # Sets the colors for the lines within the line list at OpenDSS-G
    def setLineColors(self, Colors):
        # call the function to send TCP command and get the return data
        myCmdStr = COMMANDS['SetLineColors'] + '0008'
        MsgSize = hex((len(Colors) * 4) + 4)[2:]
        MsgFill = ''
        if len(MsgSize) < 8:
            for i in range(8 -len(MsgSize)):
                MsgFill = MsgFill + '0'

        myMsg = (myCmdStr + MsgFill + MsgSize).encode('utf-8') + (int(len(Colors)).to_bytes(4, 'big'))
        # Now extracts the colors into a byte array
        for myColor in Colors:
            myMsg = myMsg + (int(myColor).to_bytes(4, 'big'))
        # adds the last semicolon
        myMsg = myMsg +  (int(59).to_bytes(1, 'big'))
        data = self.sendTCP(myMsg, True)
        # return data
        return data 
    
    # Sets the color mode at OpenDSS-G
    def setColorMode(self, Mode):    
        myCmdStr = COMMANDS['SetColorMode'] + '0005'    
        MsgSize = hex(Mode)[2:]
        MsgFill = ''
        if len(MsgSize) < 5:
            for i in range(5 -len(MsgSize)):
                MsgFill = MsgFill + '0'
        myCmdStr = myCmdStr + MsgFill + MsgSize + ';'
        data = self.sendTCP(myCmdStr)
        # return data
        return data 
    
    # Updates the GUI in OpenDSS-G to show the latests changes
    def RefreshGUI(self):     
        # call the function to send TCP command and get the return data
        data = self.sendTCP(COMMANDS['RefreshGUI'])
        # return data
        return data  
    
    # Forces OpenDSS-G for considering only the given list for updating colors
    def SetLineList(self, data):
        myCmdStr = COMMANDS['SetLineList']    
        MsgSize = hex(len(data))[2:]
        MsgFill = ''
        if len(MsgSize) < 5:
            for i in range(5 -len(MsgSize)):
                MsgFill = MsgFill + '0'
        myCmdStr = myCmdStr + MsgFill + MsgSize
        for Obj in data:
            myCmdStr = myCmdStr + Obj + '\t'
        myCmdStr = myCmdStr[0:(len(myCmdStr) - 1)]
        myCmdStr = myCmdStr + '\n'
        print(myCmdStr)
        # call the function to send TCP command and get the return data
        data = self.sendTCP(myCmdStr)

        return data        
    
    """
    This section os for specific send command functions, this will hopefully make
    it easier to send specific commands
    """
    
    # function to get voltage at a specific element
    # will return voltage as magnitude and angle (its how OpenDSS works)
    def getElementVoltage(self, elementName, elementTerminal):
        # format the command to follow for OpenDSS
        message = "select " + elementName + ' ' + str(elementTerminal)
        # send the command to OpenDSS-G through the command interface
        confirmation = self.sendCommand(message)
        
        if confirmation[0].lower() == 'ok':
            message = 'Voltages'
            data = self.sendCommand(message)
            return data
        else:
            error_message = "There was an error with the following command:  "
            print(error_message + message)
            return error_message + message
    
    # function to get the powers running through all terminals of the element
    # will return powers as active and reactive (its how OpenDSS works)
    def getElementPowers(self, elementName):
        # format the command to follow for OpenDSS
        message = "select " + elementName
        # send the command to OpenDSS-G through the command interface
        confirmation = self.sendCommand(message)
        
        if confirmation[0].lower() == 'ok':
            message = 'Powers'
            data = self.sendCommand(message)
            return data
        else:
            error_message = "There was an error with the following command:  "
            print(error_message + message)
            return error_message + message
    
    # function to get the currents running through all terminals of the element
    # will return current as magnitude and angle (its how OpenDSS works)
    def getElementCurrents(self, elementName):
        # format the command to follow for OpenDSS
        message = "select " + elementName
        # send the command to OpenDSS-G through the command interface
        confirmation = self.sendCommand(message)
        
        if confirmation[0].lower() == 'ok':
            message = 'Currents'
            data = self.sendCommand(message)
            return data
        else:
            error_message = "There was an error with the following command:  "
            print(error_message + message)
            return error_message + message
    
    
    """
    This section is the start of helper functions used in other functions
    """
    
    # function to send message and receive response with OpenDSS-G using the socket
    def sendTCP(self, message, isByte = False):
        # send the command via tcp
        if isByte:
            self.s.send(message)    
        else:
            self.s.send(message.encode('utf-8'))
        # receive the response to the command
        temp = self.s.recv(self.BUFFER_SIZE)
        # clean the data
        cleanedData = cleanData(temp)
        # format the data
        data = formatDataList(cleanedData)
        # return the result of the command cleaned up
        return data

'''
Start of functions in the module not the class
'''


# function to format the message for TCP 
def formatTCPMessage(command, data):
    message = command + '{0:04X}'.format(len(data)) + data + ';'
    return message
    
    
"""
This is section is the start of auxiliary functions used to help clean data
for easier use and reporting
"""

# function to remove header, semicolon, and any end of line characters from data
def cleanData(data):
    # remove the hex header and semicolon
    temp = data[8:-1]
    # remove end line charaters if there are any
    cleaned_data = temp.rstrip()
    return cleaned_data

# function that formats data from built in TCP commands which are tab delimited
def formatDataList(data):
    # split the list by tab delimiter
    return data.split()

# function that formats data from OpenDSS command prompt, which are not 
# preprocessed and are space and comma delimited
def formatCommandDataList(data):
    # split the list by comma
    temp = data[0].split()
    data = []
    for t in temp:
        if t != '':
            data.append(t.split()[0])
    return data

# returns single values in three-phase format with the first column being the name of the bus
# the code depends on the buses, nodes, and values all being in the same order
def formatDataThreePhase(busNames, nodeNames, data):
    # number of buses
    num_buses = len(busNames)
    # initialize numpy array
    formatedData = [[None for ii in xrange(4)] for ii in xrange(num_buses)]
    # index for nodes
    jj = 0
    # traverse through the list of busses
    for ii in range(0, num_buses):
        # set the first column equal to bus name
        formatedData[ii][0] = busNames[ii]
        # set flag
        check = 1
        # run loop till flag or end of index is reached
        while (check == 1) and (jj < len(nodeNames)):
            # check if the busname is in the node name
            if busNames[ii] in nodeNames[jj]:
                # if yes, then check which phase (this assumes normal three phase)
                # assign the value to the correct column and advance the index
                if busNames[ii] + '.1' in nodeNames[jj]:
                    formatedData[ii][1] = data[jj]
                    jj += 1
                elif busNames[ii] + '.2' in nodeNames[jj]:
                    formatedData[ii][2] = data[jj]
                    jj += 1
                elif busNames[ii] + '.3' in nodeNames[jj]:
                    formatedData[ii][3] = data[jj]
                    jj += 1
            # if not, then the node must be part of the next bus so it should exit the loop
            else:
                check = 0
    return formatedData

# returns single values in three-phase format with the first column being the name of the bus
# the code depends on the buses, nodes, and values all being in the same order
def formatComplexDataThreePhase(busNames, nodeNames, data):
    # number of buses
    num_buses = len(busNames)
    # initialize numpy array
    formatedData = [[None for ii in xrange(7)] for ii in xrange(num_buses)]
    # index for node names
    jj = 0
    # index for complex values
    kk = 0
    # traverse through the list of busses
    for ii in range(0, num_buses):
        # set the first column equal to bus name
        formatedData[ii][0] = busNames[ii]
        # set flag
        check = 1
        # run loop till flag or end of index is reached
        while (check == 1) and (jj < len(nodeNames)):
            # check if the busname is in the node name
            if busNames[ii] in nodeNames[jj]:
                # if yes, then check which phase (this assumes normal three phase)
                # assign the value to the correct column and advance the index
                if busNames[ii] + '.1' in nodeNames[jj]:
                    formatedData[ii][1] = data[kk]
                    formatedData[ii][2] = data[kk + 1]
                    jj += 1
                    kk += 2
                elif busNames[ii] + '.2' in nodeNames[jj]:
                    formatedData[ii][3] = data[kk]
                    formatedData[ii][4] = data[kk + 1]
                    jj += 1
                    kk += 2
                elif busNames[ii] + '.3' in nodeNames[jj]:
                    formatedData[ii][5] = data[kk]
                    formatedData[ii][6] = data[kk + 1]
                    jj += 1
                    kk += 2
            # if not, then the node must be part of the next bus so it should exit the loop
            else:
                check = 0
    return formatedData
    