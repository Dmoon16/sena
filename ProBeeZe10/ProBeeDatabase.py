'''
Created on 30.01.2012
@author: Adrian Rosian
'''
import sqlite3

class ProbeeDatabase:
    '''
    Represents the database object used to store the device info
    '''
    
    def __init__(self, fileName, flushLimit = None):
        if not isinstance(fileName, str):
            raise IOError('Database file name must be a string')
        self.connection = sqlite3.connect(fileName)
        self.cursor = self.connection.cursor()
        if isinstance(flushLimit, int):
            self.bufferFlushCount = 0
            self.flushLimit = flushLimit
    
    def createDeviceTables(self):
        if not isinstance(self.connection, sqlite3.Connection):
            raise IOError('Connection not yet created')
        if not isinstance(self.cursor, sqlite3.Cursor):
            raise IOError('Cursor not yet obtained')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS "device" (
                "id" INTEGER PRIMARY KEY  NOT NULL ,
                "name" VARCHAR NOT NULL,
                "long_addr" VARCHAR NOT NULL ,
                "short_addr" VARCHAR NOT NULL ,
                "is_controller" BOOL NOT NULL  DEFAULT (0) 
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS "device_data" (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
                "device_id" INTEGER(10),
                "recv_time" INTEGER,
                "analog" VARCHAR(30),
                "digital" VARCHAR(30)
            )
        ''')
        self.connection.commit()
                       
    def insertDataSample(self, sample):
        self.cursor.execute('''
            INSERT INTO device_data (device_id, recv_time, analog, digital)
            SELECT id, ?, ?, ? FROM device WHERE long_addr=?''', sample)
        if not self.flushLimit:
            self.connection.commit()
        else:
            self.bufferFlushCount = self.bufferFlushCount + 1
            if self.bufferFlushCount >= self.flushLimit:
                self.connection.commit()
                self.bufferFlushCount = 0
            if self.connection.in_transaction:
                self.connection.commit()
    
    def __del__(self):
        if isinstance(self.connection, sqlite3.Connection):
            self.connection.close()