import datetime as dt
import sqlite3 as db
from os import path

import adafruit_bme280
import busio
import smbus
# Start measurement at 4lx resolution. Time typically 16ms.
from microcontroller import pin

CONTINUOUS_LOW_RES_MODE = 0x13
# Start measurement at 1lx resolution. Time typically 120ms
CONTINUOUS_HIGH_RES_MODE_1 = 0x10
# Start measurement at 0.5lx resolution. Time typically 120ms
CONTINUOUS_HIGH_RES_MODE_2 = 0x11
# Start measurement at 1lx resolution. Time typically 120ms
# Device is automatically set to Power Down after measurement.
ONE_TIME_HIGH_RES_MODE_1 = 0x20
# Start measurement at 0.5lx resolution. Time typically 120ms
# Device is automatically set to Power Down after measurement.
ONE_TIME_HIGH_RES_MODE_2 = 0x21
# Start measurement at 1lx resolution. Time typically 120ms
# Device is automatically set to Power Down after measurement.
ONE_TIME_LOW_RES_MODE = 0x23
# Define some constants from the datasheet
DEVICE = 0x23  # Default device I2C address

POWER_DOWN = 0x00  # No active state
POWER_ON = 0x01  # Power on
RESET = 0x07  # Reset data register value

# bus = smbus.SMBus(0) # Rev 1 Pi uses 0
bus = smbus.SMBus(1)  # Rev 2 Pi uses 1


def _aktuelleTemperatur(folder='28-02148107cbff'):
    # 1-wire Slave Datei lesen
    folder = '/sys/bus/w1/devices/' + folder
    rueckgabewert = 0
    if path.exists(folder):
        complFolder = folder + '/w1_slave'
        if path.exists(complFolder):
            file = open(complFolder)
            filecontent = file.read()
            file.close()

            # Temperaturwerte auslesen und konvertieren
            stringvalue = filecontent.split("\n")[1].split(" ")[9]
            temperature = float(stringvalue[2:]) / 1000

            # Temperatur ausgeben
            rueckgabewert = '%6.2f' % temperature
    return rueckgabewert


def _getClimate():
    i2c = busio.I2C(pin.i2cPorts[1][1], pin.i2cPorts[1][2])
    bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
    return bme280.temperature, bme280.humidity, bme280.pressure


if __name__ == '__main__':
    connection = db.connect('/etc/birdshome/birdshome_base.db')
    cursor = connection.cursor()
    # temp, hum, pres = _getClimate()
    currTime = dt.datetime.now().isoformat()
    temp_nest = float(_aktuelleTemperatur(folder='28-0317252964ff'))
    temp_out = float(_aktuelleTemperatur(folder='28-02148107cbff'))
    _vals = (currTime, str(round(temp_out, 1)), str(round(0, 0)), str(round(0, 0)), str(round(0, 2)),
             str(round(temp_nest, 1)))
    sql = 'INSERT INTO climate (id, temperature, humidity, pressure, density, temp_nest) values' + str(
        _vals) + ";"
    values = []
    cursor.execute(sql, values)
    connection.commit()
    connection.close()
