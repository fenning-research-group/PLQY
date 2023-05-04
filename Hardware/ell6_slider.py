import yaml
import os
import serial
import time

# https://github.com/cdbaird/TL-rotation-control/blob/759dc3fc58efd975c37c7ee954fa6152618cd58e/elliptec/rotation.py

class FilterSlider:
    def __init__(self, port='COM19'):
        # communication variables

        constants = {'device_identifiers': {'vid' : "0403", 'pid' : "6015"}}        

        self.port = port

        self.POLLINGDELAY = 0.02
            
        self.SLIDERRESPONSETIME = 1

        self.ADDRESS = "0"

        self.connect()

    def connect(self):
        self._handle = serial.Serial(self.port, timeout=3, baudrate=9600)

    def disconnect(self):
        self._handle.close()

    def write(self, address, request):
        command = address.encode("utf-8") + request.encode("utf-8")
        self._handle.write(command)
        response = self._handle.readline().decode("utf-8")

    def left(self):
        """Move top shutter to left position"""
        self.write(address=self.ADDRESS, request="fw")
        time.sleep(self.SLIDERRESPONSETIME)

    def right(self):
        """Move top shutter to right position"""
        self.write(address=self.ADDRESS, request="bw")
        time.sleep(self.SLIDERRESPONSETIME)
