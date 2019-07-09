from __future__ import division
# SensorStation Screen Controller
# Copyright 2007-2019, Cellular Tracking Technologies, LLC, All Rights Reserved
# Version 1.1

# pip library requirements: inky

# Python library imports

import datetime
import bme680
import os
import RPi.GPIO as GPIO
import time
import math
from PIL import Image, ImageFont, ImageDraw
import inky_fast
import argparse

# configure screen
# a missing screen apparently has no effect on the execution of screen rendering 
# the HAT eeprom also does not appear

inky_display = inky_fast.InkyPHATFast("red")

img = Image.new("P", (212, 104))
draw = ImageDraw.Draw(img)

# remove GPIO warnings

GPIO.setwarnings(False)

# Configure I2C accessories
# This section will try to import I2C libraries. smcbus will throw an I/O exception if it is not found.

_sensor_environment = 0


# Check for environmental sensor (altimeter + humidity + temperatuare + VOC)

try: 
  sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
  _sensor_environment = 1
except:
  _sensor_environment = 0

#configure bme680 if it was found

if _sensor_environment == 1:
  sensor.set_humidity_oversample(bme680.OS_2X)
  sensor.set_pressure_oversample(bme680.OS_4X)
  sensor.set_temperature_oversample(bme680.OS_8X)
  sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
  sensor.set_gas_heater_temperature(320)
  sensor.set_gas_heater_duration(150)
  sensor.select_gas_heater_profile(0)

# Configure ADC

_TLC_CS =19
_TLC_ADDR =21
_TLC_CLK =18
_TLC_DOUT =20
_TLC_EOC = 16

_ADC_BATTERY = 0
_ADC_SOLAR = 1
_ADC_RTC = 2
_ADC_TEMPERATURE = 3
_ADC_LIGHT = 4
_ADC_AUX_1 = 5
_ADC_AUX_2 = 6
_ADC_AUX_3 = 7
_ADC_AUX_4 = 8
_ADC_AUX_5 = 9
_ADC_AUX_6 = 10
_ADC_CAL_1 = 11
_ADC_CAL_2 = 12
_ADC_CAL_3 = 13
_ADC_VREF = 4.972


# Configure GPIOs

_BUTTON_UP = 4
_BUTTON_DN = 5
_BUTTON_BACK = 7
_BUTTON_SELECT = 6
_DIAG_A = 39
_DIAG_B = 40
_TLC_CS =19
_TLC_ADDR =21
_TLC_CLK =18
_TLC_DOUT =20
_TLC_EOC = 16


GPIO.setmode(GPIO.BCM)
GPIO.setup(_BUTTON_UP,GPIO.IN)
GPIO.setup(_BUTTON_DN,GPIO.IN)
GPIO.setup(_BUTTON_BACK,GPIO.IN)
GPIO.setup(_BUTTON_SELECT,GPIO.IN)
GPIO.setup(_DIAG_A,GPIO.OUT)
GPIO.setup(_DIAG_B,GPIO.OUT)
GPIO.setup(_TLC_CLK,GPIO.OUT)
GPIO.setup(_TLC_ADDR,GPIO.OUT)
GPIO.setup(_TLC_DOUT,GPIO.IN)
GPIO.setup(_TLC_CS,GPIO.OUT)
GPIO.setup(_TLC_EOC,GPIO.IN)

GPIO.output(_DIAG_A,1)

# ADC function 


def ADC_Read(channel):
    GPIO.output(_TLC_CS, 0)
    value = 0
    for i in range(0,4):
        if((channel >> (3-i)) & 0x01):
            GPIO.output(_TLC_ADDR, 1)
        else:
            GPIO.output(_TLC_ADDR, 0)
        GPIO.output(_TLC_CLK, 1)
        GPIO.output(_TLC_CLK, 0)
    for i in range(0, 6):
        GPIO.output(_TLC_CLK, 1)
        GPIO.output(_TLC_CLK, 0)
    GPIO.output(_TLC_CS, 1)
    time.sleep(0.001)
    GPIO.output(_TLC_CS, 0)
    for i in range(0, 10):
        GPIO.output(_TLC_CLK, 1)
        value <<= 1
        if (GPIO.input(_TLC_DOUT)):
            value |= 0x01
        GPIO.output(_TLC_CLK, 0)
    GPIO.output(_TLC_CS, 1)

    return value


def getVoltage():
    reading = ADC_Read(_ADC_BATTERY)
    voltage = (reading * 4.972) / 1024
    vs = voltage  / (100000/599000)
    return vs + 0.5

def getSolarVoltage():
    reading = ADC_Read(_ADC_SOLAR)
    voltage = (reading * 4.972) / 1024
    voltage = voltage / (100000/599000)
    return voltage

def getRTCBatteryVoltage():
    reading = ADC_Read(_ADC_RTC)
    voltage = 4.972 / 1024 * reading
    return voltage

def getTemperature():
    base_ohms = 100000
    divider_ohms = 100000
    c1 = 1.009249522e-03
    c2 = 2.378405444e-04
    c3 = 2.019202697e-07
    source_voltage = 3.3
    reading = ADC_Read(_ADC_BATTERY)
    print "reading: "+str(reading)
    voltage = (reading * 5) / 1024
    print "voltage: "+str(voltage)
    logR2 = math.log(divider_ohms);
    temperature = (1.0 / (c1 + c2*logR2 + c3*logR2*logR2*logR2))
    temperature = temperature - 273.15
    return temperature

file = 0
if file == 1:
  if GPIO.input(_BUTTON_UP) == 0:
     print "Up"
     GPIO.output(_DIAG_A,1)
  if GPIO.input(_BUTTON_DN) == 0:
     print "Down"
     GPIO.output(_DIAG_B,1)
  if GPIO.input(_BUTTON_BACK) == 0:
     print "Back"
     GPIO.output(_DIAG_A,1)
  if GPIO.input(_BUTTON_SELECT) == 0:
     print "Select"
     GPIO.output(_DIAG_B_1)


def getPressure():
 while 1:
   if sensor.get_sensor_data():
          return sensor.data.pressure

def getTemperature():
 while 1:
  if sensor.get_sensor_data():
          return sensor.data.temperature

def getHumidity():
 while 1:
   if sensor.get_sensor_data():
         return sensor.data.humidity

def getGas():
 while 1:
       if sensor.get_sensor_data() and sensor.data.heat_stable:
            return sensor.data.gas_resistance
	
def batteryMonitor():
   try:
     while 1:
        time.sleep(30)
        voltage = getVolts(_ADC_BATTERY)
        if voltage < 11.5:
             low_battery_light = 1

   except KeyboardInterrupt:
       GPIO.cleanup()

def getIPAddress():
   print "getting IP address"
   result = os.popen("ifconfig | grep eth0").read()
   if result == "":
        print "Couldn't find eth0"
        return "No Ethernet"
   print "Found eth0..getting IP"
   result = os.popen("ifconfig eth0 | grep inet").read()
   try:
     ip = result.split("inet")[1].split(" ")[1]
     print "my IP address is: "+str(ip)
   except:
     print "didn't find an IP"
     return "No Cable"
   return ip

def displayWelcome():
   ctt_font_large = ImageFont.truetype("/home/pi/ctt_font.ttf",26)
   ctt_font_mega = ImageFont.truetype("/home/pi/ctt_font.ttf",32)
   ctt_font_small  = ImageFont.truetype("/home/pi/ctt_font.ttf",14)
   bauhaus = ImageFont.truetype("/home/pi/bauhaus.ttf",14)
   draw.text((20,1), "Welcome To", 1, font=ctt_font_large)
   draw.text((4,26), "SensorStation", 2, font=ctt_font_mega)
   draw.text((1,70), "Version 1.00, Copyright 2019", 1)
   draw.text((1,90), "Cellular Tracking Technologies", 1)
   inky_display.set_image(img)
   inky_display.show()


def displayMain():
   # define colors
   black = 1
   white = 0
   red = 2
 
   # build title bar with icons
   draw.rectangle(((0,0),(212,100)),fill=white)					# clear screen
   draw.rectangle(((0,0),(212,18)),fill=black)					# draw title bar
   #bauhaus = ImageFont.truetype("/home/pi/bauhaus.ttf",14)			# configure fancy font
   ip = getIPAddress()								# get IP address
   if ip.find(".") != -1: ip = "http://" + str(ip) + "/"
   draw.text((0,0),"SensorStation",white)   					# print product name
   draw.text((0,9),str(ip),white)

   # antenna symbol

   ant_x = 190
   ant_y = 1

   draw.line((ant_x,ant_y,ant_x+10,ant_y),fill=white)
   draw.line((ant_x,ant_y,ant_x+4,ant_y+4),fill=white)
   draw.line((ant_x+10,ant_y,ant_x+4,ant_y+4),fill=white)
   draw.line((ant_x+5,ant_y,ant_x+5,ant_y+17),fill=white)

   # signal bars

   bar_x = 200

   if signal == 0: draw.text((bar_x,ant_y+6),"X",white)
   if signal > 0: draw.rectangle(((bar_x,12),(bar_x+1,17)),fill=white)
   if signal > 1: draw.rectangle(((bar_x+3,8),(bar_x+1+3,17)),fill=white)
   if signal > 2: draw.rectangle(((bar_x+6,1),(bar_x+1+6,17)),fill=white)

   # GPS indicator

   gps_x = 170
   gps_y = 1

   draw.ellipse((gps_x,gps_y,gps_x+16,gps_y+16),fill=black,outline=white)

   if gps == 0: draw.text((gps_x+6,gps_y+6),"X",white)
   if gps == 1: draw.text((gps_x+6,gps_y+6),"T",white)
   if gps == 2: draw.text((gps_x+3,gps_y+3),"2D",white)
   if gps == 3: draw.text((gps_x+3,gps_y+3),"3D",white)


   batt = getVoltage()
   if batt < 11.3: color = 2
   else: color = 1
   draw.line((123,20,123,90),fill=black)
   draw.text((0,20),"Battery   | "+str(round(batt,1))+"V",color)
   solar = getSolarVoltage()
   if solar < 12: color = 2
   else: color = 1
   rtc_status = "Low Batt"
   if getRTCBatteryVoltage() > 2.7:
     rtc_status = "Ok"
   if getRTCBatteryVoltage() < 1.0:
     rtc_status = "No Batt"
   rtc_status = "Low Batt"
   draw.text((125,20),"RTC | "+str(rtc_status),black)
   draw.text((0,29),"Solar     | "+str(round(solar,1))+"V",color)
   draw.text((0,38),"Beeps     | "+str(beeps),1)
   draw.text((0,47),"Nodes     | "+str(nodes),1)
   result = os.popen("df -h | grep /dev/root").read()
   disk = result.split("%")[0].split("  ")[-1]
   draw.text((0,56),"Disk Used | "+str(disk)+"%",1)
   draw.line((0,90,212,90),fill=black)
   draw.text((20,92),str(datetime.datetime.utcnow()),1)

   if _sensor_environment == 1:
     draw.text((0,56),"Pres : "+str(getPressure())+"hPa",1)
     draw.text((100,56),"RH% : "+str(getHumidity())+"%",1)
     draw.text((0,65),"Temp : "+str(getTemperature())+"C",1)
     draw.text((100,65),"VOC : "+str(getGas())+"Ohms",1)

   inky_display.set_image(img)
   inky_display.show()

def displayCustom():
   draw.rectangle(((0,0),(212,100)),fill=0)
   bauhaus = ImageFont.truetype("/home/pi/bauhaus.ttf",16)
   draw.line((0,10,212,10),fill=1)
   draw.text((0,0),"SensorStation",1)
   if line0 != None: draw.text((0,12),str(line0),1)
   if line1 != None: draw.text((0,21),str(line1),1)
   if line2 != None: draw.text((0,30),str(line2),1)
   if line3 != None: draw.text((0,39),str(line3),1)
   if line4 != None: draw.text((0,48),str(line4),1)
   if line5 != None: draw.text((0,57),str(line5),1)
   if line6 != None: draw.text((0,66),str(line6),1)
   if line7 != None: draw.text((0,75),str(line7),1)
   if line8 != None: draw.text((0,84),str(line8),1)
   if line9 != None: draw.text((0,92),str(line9),1)
   inky_display.set_image(img)
   inky_display.show()





parser = argparse.ArgumentParser()
parser.add_argument('--beeps', '-b', type=int, required=False,help="Number of total beeps received since system boot")
parser.add_argument('--nodes', '-n', type=int, required=False,help="Number of nodes seen since system boot")
parser.add_argument('--signal', '-s', type=int, required=True,help="Signal strength of GSM signal. 0: No GSM, 1-5: number of bars")
parser.add_argument('--gps', '-g', type=int, required=True,help="GPS position. 0: No GPS, 1: Time, 2: 2D Fix, 3: 3D Fix")
parser.add_argument('--view', '-v', type=str, required=True,choices=["welcome","main","custom"], help="Select the view")
parser.add_argument('--line0','-0', type=str, required=False,help="Custom line 0 text")
parser.add_argument('--line1','-1', type=str, required=False,help="Custom line 1 text")
parser.add_argument('--line2','-2', type=str, required=False,help="Custom line 2 text")
parser.add_argument('--line3','-3', type=str, required=False,help="Custom line 3 text")
parser.add_argument('--line4','-4', type=str, required=False,help="Custom line 4 text")
parser.add_argument('--line5','-5', type=str, required=False,help="Custom line 5 text")
parser.add_argument('--line6','-6', type=str, required=False,help="Custom line 6 text")
parser.add_argument('--line7','-7', type=str, required=False,help="Custom line 7 text")
parser.add_argument('--line8','-8', type=str, required=False,help="Custom line 8 text")
parser.add_argument('--line9','-9', type=str, required=False,help="Custom line 9 text")

args = parser.parse_args()

beeps = args.beeps
nodes = args.nodes
signal = args.signal
gps = args.gps
view = args.view
line0 = args.line0
line1 = args.line1
line2 = args.line2
line3 = args.line3
line4 = args.line4
line5 = args.line5
line6 = args.line6
line7 = args.line7
line8 = args.line8
line9 = args.line9

GPIO.output(_DIAG_A,0)

if view == "welcome": displayWelcome()
if view == "main": displayMain()
if view == "custom": displayCustom()

