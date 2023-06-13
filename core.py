#from ulab import numpy as np, scipy
import machine
from machine import I2C
from lcd_api import LcdApi
from i2c_lcd import I2cLcd
#from time import sleep, time as tim
import time
from machine import ADC, Pin

 

I2C_ADDR = 0x27
totalRows = 2
totalColumns = 16

 

#setup the Pulse Sensor reading pin
analog_pulse=machine.ADC(28)
led = Pin(25, Pin.OUT)

 

i2c = I2C(0, sda=machine.Pin(0), scl=machine.Pin(1), freq=400000)
lcd = I2cLcd(i2c, I2C_ADDR, totalRows, totalColumns) 
pump = Pin(20, Pin.OUT)
pump(0)

 

def CollectData(startTime, stopTime):
    while time.ticks_ms() < stopTime:
        voltage_value = analog_pulse.read_u16() * (3.3 / 65535)
        if voltage_value > 0:
            rawData.append([((time.ticks_ms())-startTime)/1000, voltage_value])
                    
        lcd.move_to(0,1)
        lcd.putstr("volts: " + str(round(voltage_value, 3)))
        

 

def CalcBPM(data, timeDelta, window, subgrouping, threshold):

 

    m = [[y[0][i-subgrouping:i+subgrouping], y[1][i-subgrouping:i+subgrouping]]  
         for i, y in enumerate(data) if y[1][i-subgrouping:i+6]]     

 

    maxList = [[x[0][x[1].index(max(x[1]))], max(x[1])] for x in m]

 


    #final = set({tuple(i) for i in maxList})
    
    
    a = [[x[0], x[1]] for x in list(set({tuple(i) for i in maxList}))]
    final = [x for x in a if x[0] > (max([x[0] for x in a]) - window)]
    print(final)
    
    lcd.move_to(0,0)
    if not [x for x in final if x[1] > threshold]:
        lcd.putstr("BPM: Not Detected")
        return 'Not Detected'
    
    bpm = round((len(final) / window) * 60, 0)
    lcd.putstr(f"BPM: " + str(bpm))
    
    return bpm

 

def ProcessData():
    time, voltage = [], []
    for i, x in enumerate(rawData):
      time.append(rawData[i][0])
      voltage.append(rawData[i][1])
  
    return [[time, voltage] for x in voltage]

 

if __name__ == '__main__':
    
    window = 15 # last x seconds of data in list
    threshold = 2.4 # voltage gate
    subgrouping = 3 # subgroups to check for local max
    
    rawData = []
    
    startTime = time.ticks_ms()
    stopTime = startTime + (window*1000) #time change original 60*1000 (60 secs)
    timeDelta = (stopTime - startTime)/1000

 

    while True:
        stopTime = time.ticks_ms() + (10*1000)
        timeDelta = (stopTime - startTime)/1000
        rawData = [x for x in rawData if x[0] > (max([x[0] for x in rawData]) - (2*window))]
        
        print(f'While loop breaks after {window} seconds')
        
        CollectData(startTime, stopTime)
        bpm = CalcBPM(ProcessData(), timeDelta, window, subgrouping, threshold)
        
        if bpm != 'Not Detected':
            if bpm > 50 and bpm < 80:
                pump(1)
            else:
                pump(0)
        else:
            pump(0)