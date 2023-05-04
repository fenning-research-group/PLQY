import serial
from time import sleep
import numpy as np
import pandas as pd
# import struct


class Stepper:

    def __init__(self, port):

        self.port = port
        self.POLLINGDELAY = 0.02
        self.HOMINGTIME = 5
        self.arduino = serial.Serial(port = self.port, baudrate = 9600)

    def gohome(self):

        self.arduino.close()
        sleep(2)
        sleep(self.HOMINGTIME)

    def moveto(self, position):

        self.arduino.write(str(position).encode())

        while self.arduino.in_waiting == 0:
            pass

        sleep(0.01)
        num = self.arduino.in_waiting
        string = self.arduino.read(num).decode('utf-8')
        print(f'Moved to {string}')