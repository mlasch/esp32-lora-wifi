from machine import Pin, SPI

from sx127x import SX127x
import sx127x

PIN_CS = 18
PIN_MOSI = 27
PIN_MISO = 19
PIN_SCK = 5
PIN_RST = 14
PIN_DIO0 = 26

class LoRaModule(SX127x):
    def __init__(self, spi=None, rst=None, cs=None,
            dio=(None, None, None)):
        self.spi = spi
        self.rst_pin = rst
        self.cs_pin = cs
        self.dio_pins = dio
        
        self.cs_pin.value(1)
        self.spi.init()
    
        super().__init__()
        

    def _transfer(self, addr, val = 0x00):
        response = bytearray(1)
        
        print("DEBUG: trans", hex(addr), val)

        self.cs_pin.value(0)
        spi.write(bytes([addr]))
        spi.write_readinto(bytes([val]), response)
        self.cs_pin.value(1)

        return response


if __name__ == '__main__':

    spi = SPI(2, baudrate = 10000000, polarity=0, phase= 0, bits=8, firstbit=SPI.MSB,
            sck = Pin(PIN_SCK, Pin.OUT, Pin.PULL_DOWN),
            mosi = Pin(PIN_MOSI, Pin.OUT, Pin.PULL_UP),
            miso = Pin(PIN_MISO, Pin.IN, Pin.PULL_UP))


    lora_module = LoRaModule(
            spi=spi, 
            rst=Pin(PIN_RST, Pin.OUT), 
            cs=Pin(PIN_CS, Pin.OUT))

    version = bytes(lora_module.read_register(sx127x.REG_VERSION))
    
    if bytes(version) == b'\x12':
        print("Version {} OK".format(version))
   
    lora_module.close()
