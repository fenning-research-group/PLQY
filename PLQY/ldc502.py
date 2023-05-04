from pymeasure.instruments import Instrument
import numpy as np
import time

# Control code for the LDC500 series laser driver by Stanford Research Systems
# Modeled after the control code from pymeasure for the SR830 lock-in amplifier

class LDC502(Instrument):

    def __init__(self, resourceName, **kwargs):
        super(LDC502, self).__init__(
            resourceName,
            "Stanford Research Systems LDC502 Series Laser Diode Driver",
            **kwargs
        )

    POLLINGDELAY = 0.02

    def get_laser_voltage(self):
        v = self.ask("RVLD?")
        time.sleep(self.POLLINGDELAY)
        return float(v[:2])

    def get_laser_current(self):
        I = self.ask("RILD?")
        time.sleep(self.POLLINGDELAY)
        return float(I[:-2])

    def get_laser_temp(self):
        T = self.ask("TEMP?")
        time.sleep(self.POLLINGDELAY)
        return float(T[:-2])

    def set_Vmax(self, Vmax):
        self.write("SVLM %f" %Vmax)
        time.sleep(self.POLLINGDELAY)

    def set_Imax(self, Imax):
        self.write("SILM %f" %Imax)
        time.sleep(self.POLLINGDELAY)

    def set_laserOn(self):
        self.write("LDON ON")
        time.sleep(3) # there is a 3s safety delay before the laser turns on

    def set_laserOff(self):
        self.write("LDON OFF")
        time.sleep(self.POLLINGDELAY)

    def set_laserCurrent(self, I):
        self.write("SILD %f" %I)
        time.sleep(self.POLLINGDELAY)

    def set_tecTemp(self, T):
        self.write("TEMP %f" %T)
        time.sleep(self.POLLINGDELAY)

    def set_tecOn(self):
        self.write("TEON ON")
        time.sleep(self.POLLINGDELAY)

    def set_tecOff(self):
        self.write("TEON OFF")
        time.sleep(self.POLLINGDELAY)

    def set_laserRange(self, state):
        """ 
        Can be set to LOW or HIGH.
        For the LDC502, LOW == 1A and HIGH == 2A
        """
        self.write("RNGE %d" %state)
        time.sleep(self.POLLINGDELAY)

    def set_modulationOn(self):
        self.write("MODU ON")
        time.sleep(self.POLLINGDELAY)

    def set_modulationOff(self):
        self.write("MODU OFF")
        time.sleep(self.POLLINGDELAY)

    def set_laserControlMode(self, state):
        """
        For setting the laser to either:
        1) constant current (state="CC") or 
        2) constant power (state="CP")
        """
        self.write("SMOD %d" %state)
        time.sleep(self.POLLINGDELAY)

    def set_laserModulationBandwidth(self, state):
        """
        For setting the modulation bandwidth to either:
        1) low bandwidth (10kHz in CC mode) (state="LOW") or 
        2) high bandwidth (1.2MHz in CC mode) (state="HIGH")
        """
        self.write("SIBW %d" %state)
        time.sleep(self.POLLINGDELAY)




 #    def set_blank(self):
 #        self.write("CMND")
 #        time.sleep(self.POLLINGDELAY)

 #    def set_blank(self):
 #        self.write("CMND")
 #        time.sleep(self.POLLINGDELAY)
 # 