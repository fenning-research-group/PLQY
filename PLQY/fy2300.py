import time
import io
import serial
import sys


class fy2300:
    """This class is used to control the FeelTech FY2300 signal generator"""

    def __init__(self, port, baudrate=9600, timeout=0.5, bytesize=8):
        """
        Args:
            port (str): usually a COM port
            baudrate (int): Should usually be 9600
            timeout (float, optional): Serial timeout. Defaults to 0.5.
            bytesize (int, optional): How big the bytes are. Defaults to 8.
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.bytesize = bytesize

        self.connect()
        self.initiate_coms()
        self.channels = {1: "WM", 2: "WF"}
        self.waves = {"sine": 0, "square": 1}

    def connect(self):
        """Connect to the instument"""
        try:
            self.serial = serial.Serial(
                self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                bytesize=self.bytesize,
            )
        except:
            sys.stdout.write("Could not connect to FY2300, try again")

    def initiate_coms(self):
        self.sio = io.TextIOWrapper(
            io.BufferedRWPair(self.serial, self.serial, 1), newline=None
        )
        self.sio._CHUNK_SIZE = 1

    def write_and_read(self, message):
        self.sio.write(f"{message}\n")
        self.sio.flush()
        response = self.sio.readline()
        return response

    def get_device_name(self):
        id = self.write_and_read("UMO")
        return id.strip()

    def set_amplitude(self, channel, v):
        message = f"{self.channels[channel]}A{float(v)}"
        self.write_and_read(message)

    def set_output_on(self, channel):
        message = f"{self.channels[channel]}N1"
        self.write_and_read(message)

    def set_output_off(self, channel):
        message = f"{self.channels[channel]}N0"
        self.write_and_read(message)

    def set_waveform(self, channel, waveform, freq, duty=50):
        """Set up a waveform on the specified channel

        Args:
            channel (int): 1 or 2 for channel 1 or 2
            waveform (str): 'sine' or 'square' for example
            freq (float): frequency in Hz
            duty (int, optional): The duty cycle of the waveform. Defaults to 50.
        """

        message = f"{self.channels[channel]}W{self.waves[waveform]}"
        self.write_and_read(message)

        message = f"{self.channels[channel]}F{freq*1000000:0.0f}"
        self.write_and_read(message)

        message = f"{self.channels[channel]}D{duty:0.0f}"
        self.write_and_read(message)
