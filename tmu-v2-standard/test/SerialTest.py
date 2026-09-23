#!/usr/bin/env python3
from pymodbus.client import ModbusSerialClient
from time import sleep

client = ModbusSerialClient(method='rtu', port='/dev/ttyACM0', baudrate=9600)
loop = False

def testBatch():
    getModbus = client.read_holding_registers(0, 10, slave = 2)
    try:
        print("Read Power Meter 1")
        print(getModbus.registers) 
    except:
        print("Read Failed")
        print(getModbus) 
    print("~~~")

if loop:
    while True:
        testBatch()
        sleep(2)
else:   
    testBatch()