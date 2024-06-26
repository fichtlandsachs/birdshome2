#!/usr/bin/python
# coding=utf-8
from os import path

from flask import current_app as app


def aktuelleTemperatur():
    # 1-wire Slave Datei lesen
    folder = app.config['WIREDATEI_TEMP']
    if path.exists('/sys/bus/w1/devices/' + folder):
        complFolder = '/sys/bus/w1/devices/' + folder + '/w1_slave'
        file = open(complFolder)
        filecontent = file.read()
        file.close()

        # Temperaturwerte auslesen und konvertieren
        stringvalue = filecontent.split("\n")[1].split(" ")[9]
        temperature = float(stringvalue[2:]) / 1000

        # Temperatur ausgeben
        rueckgabewert = '%6.2f' % temperature
        return (rueckgabewert)
    else:
        return 0
