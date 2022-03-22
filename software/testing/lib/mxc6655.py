# mmxc6655.py
#
# circuitpython driver lib for mmc6655 accelerometer
#
# currently is just a set-it-and-forget-it dealio for the FP/mainboard usage
#
# C. Hillis 3/22

#change output to tuples!

from micropython import const
from adafruit_bus_device.i2c_device import I2CDevice
from adafruit_register.i2c_bits import ROBits, RWBits
from adafruit_register.i2c_bit import ROBit, RWBit
from adafruit_register.i2c_struct import UnaryStruct

# Register Map
INT_0 = const(0x00)
INT_1 = const(0x01)
STATUS = const(0x02)
XOUT_U = const(0x03)
XOUT_L = const(0x04)
YOUT_U = const(0x05)
YOUT_L = const(0x06)
ZOUT_U = const(0x07)
ZOUT_L = const(0x08)
TOUT = const(0x09)
INT_MASK0 = const(0x0A)
INT_MASK1 = const(0x0B)
DETECT = const(0x0C)
CONTROL = const(0x0D)
WHO_AM_I = const(0x0F)

class MXC6655:

    _sw_rst = RWBit(INT_1, 4)
    _drdy = RWBit(INT_1, 0)
    _ord = ROBit(STATUS, 4)
    _xout_u = UnaryStruct(XOUT_U, "<B")
    _xout_l = UnaryStruct(XOUT_L, "<B")
    _yout_u = UnaryStruct(YOUT_U, "<B")
    _yout_l = UnaryStruct(YOUT_L, "<B")
    _zout_u = UnaryStruct(ZOUT_U, "<B")
    _zout_l = UnaryStruct(ZOUT_L, "<B")
    _tout = UnaryStruct(TOUT, "<B")
    _pd = RWBit(CONTROL, "<B")
    _fsr = RWBits(2, CONTROL, 6)
    _drdye = RWBit(INT_MASK1, 0)
    _who_am_i = ROBit(WHO_AM_I, 0)

    def __init__(self, i2c_bus, addr):
        self.i2c_device = I2CDevice(i2c_bus, addr, probe=False)
        if not self._who_am_i:
            print("[ERROR][MXC6655][BAD WHO_AM_I VALUE]")
        self.ON()
    
    def OFF(self):
        self._pd = True

    def ON(self): #no power adjustment paramaters for this chip, just on or off.
        self.reset()
        self._fsr = 0 #1024 LSB/g
        self._drdye = True

    def reset(self):
        self._sw_rst = True

    # read function returns touple of floats if it got data, None type otherwise., maybe make this FFFFFF or exact 0? idk since it is gonna be a float
    def read(self): #device self refreshes @ 100Hz
        good_data_flag = False
        if(self._ord == True):#check ord bit
            if(self._drdy == True): #check drdy bit
                x_raw = (self._xout_u << 4) + (self._xout_l >> 4)
                y_raw = (self._yout_u << 4) + (self._yout_l >> 4)
                z_raw = (self._zout_u << 4) + (self._zout_l >> 4)
                out = [x_raw, y_raw, z_raw]
                #reset drdy
                self._drdy = False
                #make data flagged goog
                good_data_flag = True
        #adjust values to accel in g
        for meas in out: #12b 2's complememt form, -2048 to 2048, 
            if (out[meas]>>11 == 1): # if it is 2's convert it to int
                #flip all 12 bits and add 1
                out[meas] = ((out[meas] ^ 0x0FFF) + 1) * (-1)
            out[meas] = out[meas]/1024
        #assemble the output
        if(good_data_flag == True):
            return(out)
        else:
            return(None)
    
    def temp(self):
        temp = self._tout #8b value =0 @ 25degC, 0.568degC/LSB
        #do adjustment
        if(temp>>7 == 1): #if 2's comp
            temp = ((temp ^ 0xFF) + 1) * (-1)
        temp = temp * 0.568
        return(temp)