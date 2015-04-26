from multiprocessing import Process, Lock, Manager, freeze_support
from http import server
from serverhandlers import DataServerHandler, CommandServerHandler 
import argparse
#import json

def readProcess(l, data, command, databaseName):
    from ProBeeZe10 import ProBeeZe10
    from ProBeeZe10 import ProBeeDatabase
    from time import time
    
    try:
        device = ProBeeZe10.ProBeeZe10('COM5')
        database = ProBeeDatabase.ProbeeDatabase(databaseName.value, 500)
        #database.createDeviceTables
        '''
        # AT+REMOTE=0001950000000280,AT+DIO=1111111111111
        '''
        device.setRegister(11, 1)
        database.createDeviceTables()
        while True:
            if (command._callmethod('__len__') and 
                    command[len(command) - 1] == 'exit'):
                l.acquire()
                print('Read process exiting..')
                l.release()
                break
            line = device.getLine()
            if not line:
                continue
            address, digital, analog = line.split('|')
            address = address.lstrip('+')           
            samplingTime = int(time())
            t = samplingTime, analog, digital, address
            database.insertDataSample(t)
            digital = [int(i) if i.isalnum() else None for i in digital]
            analog = [device.getVoltage(int(i, 16)) if i.isalnum() else None for i in analog.split(',')]
            data.append({'nodeId': address, 'time': samplingTime, 
                         'analogValue': analog, 'digitalValue': digital})        
    except Exception as e:
        l.acquire()
        print('\nAn error has occured: ', type(e), e, 
              '\nRead process exiting..')
        l.release()           

def serverProcess(l, data, command):  
    Handler = DataServerHandler    
    httpd = server.HTTPServer(("", 5000), Handler) 
    httpd.timeout = 10
      
    while True: 
        if (command._callmethod('__len__') and 
                command[len(command) - 1] == 'exit'):     
            break       
        if data._callmethod('__len__'):
            while data._callmethod('__len__'):
                Handler.data.append(data.pop())
        httpd.handle_request()
        Handler.data = []       
    
if __name__ == '__main__':  
    freeze_support()  
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Data server and controller' 
                                     + 'for the Sena ProBee ZE10 module')
    parser.add_argument('database', metavar='DbName', type=str,
                   help='SQlite3 database absolute location')
    parser.add_argument('--key', '-key', metavar='accessKey', type=str,
                   help='Security token to grant access to device commands')
    args = parser.parse_args()
    
    # Set the lock and the manager for the shared memory
    lock = Lock()
    manager = Manager()
    
    # Define shared memory
    sensorData = manager.list()
    command = manager.list()
    databaseName = manager.Value('u', args.database)
    
    # Start processes
    readProc = Process(target=readProcess, args=(lock, sensorData, command, 
                                                 databaseName))
    readProc.start()
    serverProc = Process(target=serverProcess, args=(lock, sensorData, command))
    serverProc.start()
    
    # Handle received commands
    allowedCommands = ['exit'] 
    commandHandler = CommandServerHandler    
    listener = server.HTTPServer(("", 5001), commandHandler) 
    listener.timeout = 10
      
    while True: 
        if (command._callmethod('__len__') and 
                command[len(command) - 1] == 'exit'):
            break
        listener.handle_request()
        if hasattr(listener, 'lastCommand') and listener.lastCommand:
            print('Command received: ', listener.lastCommand)
            if listener.lastCommand in allowedCommands:
                command.append(listener.lastCommand)
    readProc.join()
    serverProc.join()
    
    print('Upon exit, the data list had a size of: ', 
          sensorData._callmethod('__len__'))
    print('Main process exiting..')