'''
Created on 25.12.2011
@author: Adrian Rosian
'''
import serial
from serial.serialutil import SerialException
from collections import deque

class ProBeeZe10:
    '''
    Represents a Sena ProBeeZe10 device
    '''
    
    def __init__(self, port):
        '''
        Class constructor
        
        @param port: The serial port number to connect to
        '''
        if not isinstance(port, str):
            raise TypeError
        try:
            self.serial = serial.Serial(port)
            self.serial.setTimeout(1)
        except SerialException:
            raise IOError('Could not connect to serial port')
        
        # Node type definitions
        self.NODE_TYPE_COORDINATOR = 1
        self.NODE_TYPE_ROUTER = 2
        self.NODE_TYPE_END_DEVICE = 3
        self.NODE_TYPE_SLEEPY_END_DEVICE = 4 
        
        # Function map. The dictionary consists of the function name as key
        # and a list contianing the AT command and the number of params to receive
        # as value
        self._functionMap = {}
        self._functionMap['getAnalogInput'] = ["AT+AI?\n", 0]
        self._functionMap['getDigitalInput'] = ["AT+DIO?\n", 0]
        self._functionMap['setDigitalInput'] = ["AT+DIO={0:b}\n", 1]
        self._functionMap['setRemoteDigitalInput'] = ["AT+REMOTE={!s},AT+DIO={!s}\n", 2]
        self._functionMap['getGpioDigitalInput'] = ["AT+DIO{0:d}?\n", 1]
        self._functionMap['getExtendedAddress'] = ["AT+LA?\n", 0]
        self._functionMap['getNodeType'] = ["AT+NT?\n", 0]
        self._functionMap['setNodeType'] = ["AT+NT={0:d}\n", 1]
        self._functionMap['getChannelMask'] = ["AT+CHMASK?\n", 0]
        self._functionMap['setChannelMask'] = ["AT+CHMASK={0:x}\n", 1]
        self._functionMap['getPanId'] = ["AT+PANID?\n", 0]
        self._functionMap['setPanId'] = ["AT+PANID={0:x}\n", 1]
        self._functionMap['getExtendedPanId'] = ["AT+EPID?\n", 0]
        self._functionMap['setExtendedPanId'] = ["AT+EPID={0:x}\n", 1]
        self._functionMap['resetDevice'] = ["ATZ\n", 0]
        self._functionMap['setPermitJoining'] = ["AT+PJ={0:d}\n", 1]
        self._functionMap['getRegister'] = ["ATS{0:d}?\n", 1]
        self._functionMap['setRegister'] = ["ATS{0:d}={1:d}\n", 2]
    
    def getCommandResponse(self, command):
        '''
        Returns the device response to a given command
        
        @param command: The command to transmit
        @return: mixed
        '''
        if not self.serial:
            raise IOError('Serial device not connected')
        if not isinstance(command, str):
            raise IOError('Command is not a string')
        self.serial.write(command.encode(encoding='ascii'))
        response = []
        for line in self.serial:
            response.append(line)
        response = deque(response)
        numLines = len(response)        
        if numLines < 1:
            return None
        # Pop the first line, representing the repeated command
        if numLines > 1:
            response.popleft()
        if numLines > 3:
            response.pop()
            return response
        result = response.popleft().rstrip().decode('ascii')
        return result  
    
    def getLine(self):
        '''
        Returns the device response to a given command
        
        @param command: The command to transmit
        @return: mixed
        '''
        if not self.serial:
            raise IOError('Serial device not connected')

        response = self.serial.readline()     
        if not response:
            return None        
        return response.decode('ascii').strip(" \t\r\n\0")  
    
    def __getattr__(self, name):
        '''
        Defines a function for each action requiering a command to the device
        
        @param name: The name of the function
        @return: function The function to execute
        '''
        if name in self._functionMap:
            def callbackFunction(*args, commandList=self._functionMap[name]):
                if len(args) != commandList[1]:
                    return None
                command = commandList[0].format(*args)
                return self.getCommandResponse(command)
            return callbackFunction
        raise AttributeError('Function or attributte do not exist')
    
    def getVoltage(self, analogInput):
        if analogInput > 0 and analogInput < int('0x2EE0', 16):
            return round(analogInput * 0.1, 2)
        elif analogInput > int('0xD120', 16) and analogInput < int('0x2EE0', 16):
            return round((analogInput - 65536) * 0.1, 2)
#    
#    def getLightIntensity(self, precision):
#        '''
#        Return the light intensity as read by the light sensor
#        
#        @param precision: The number of decimals of the light intensity (integer)
#        @return: float
#        '''
#        if not isinstance(precision, int):
#            raise TypeError('Light intensity precision must be an integer')
#        
#        rawLight = voltLight = light = 0        
#        rawLight = self.getAnalogInput()
#        if not rawLight:
#            return
#        rawLight = int(rawLight[10:14], 16)
#        voltLight = rawLight
#        if rawLight > 0 and rawLight < int('0x2EE0', 16):
#            voltLight = rawLight * 0.1
#        elif rawLight > int('0xD120', 16) and rawLight < int('0x2EE0', 16):
#            voltLight = (rawLight - 65536) * 0.1
#        
#        light = voltLight * 0.25
#        
#        return round(light, precision) 