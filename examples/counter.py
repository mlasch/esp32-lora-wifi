"""
Increment packet counter for LoRaWAN. 
Shows the counter value on the OLED display
"""
#import sys
#sys.path.append('/LoRaWAN')
#sys.path.append('/LoRaWAN/LoRaWAN')
import micropython as mc
import ubinascii as binascii

import onewire
import ds18x20
import ssd1306
from machine import Pin, I2C, SPI, reset
from time import sleep
from random import randrange

from sx127x import SX127x
import sx127x
#from PhyPayload import PhyPayload
import LoRaWAN
from LoRaWAN.MHDR import MHDR
import secret_priv as secret

PIN_CS = 18
PIN_MOSI = 27
PIN_MISO = 19
PIN_SCK = 5
PIN_RST = 14
PIN_DIO0 = 26
PIN_LED = 25 

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

        self.dio_pins[0].irq(trigger=Pin.IRQ_RISING, \
                handler=lambda pin: mc.schedule(self.handle_rx, pin))

    def _transfer(self, addr, val = 0x00):
        response = bytearray(1)
        

        self.cs_pin.value(0)
        self.spi.write(bytes([addr]))
        self.spi.write_readinto(bytes([val]), response)
        self.cs_pin.value(1)
        
        #print("DEBUG: addr: {}, val: {}, resp: {}".format(hex(addr), hex(val), response))

        return response


def main_loop():
    # Pin 16 is connected to OLED_RST and should be kept high
    oled_rst = Pin(16, Pin.OUT)
    oled_rst.value(1)

    i2c = I2C(scl=Pin(15), sda=Pin(4))
    
    oled = ssd1306.SSD1306_I2C(128, 64, i2c)

    dat = Pin(13, Pin.IN)
    ds = ds18x20.DS18X20(onewire.OneWire(dat))
    roms = ds.scan()
    
    led = Pin(PIN_LED, Pin.OUT)
    try:
        spi = SPI(2, baudrate = 10000000, polarity=0, phase= 0, bits=8, firstbit=SPI.MSB,
                sck = Pin(PIN_SCK, Pin.OUT, Pin.PULL_DOWN),
                mosi = Pin(PIN_MOSI, Pin.OUT, Pin.PULL_UP),
                miso = Pin(PIN_MISO, Pin.IN, Pin.PULL_UP))
    except OSError:
        reset()

    lora_module = LoRaModule(
            spi=spi, 
            rst=Pin(PIN_RST, Pin.OUT), 
            cs=Pin(PIN_CS, Pin.OUT),
            dio=(
                Pin(PIN_DIO0, Pin.IN, Pin.PULL_UP) 
                ,None, None))
    
    #devnonce = list(lora_module.get_random(2))  # read random value from wideband rssi
    #join_request = LoRaWAN.new(appkey)
    #join_request.create(MHDR.JOIN_REQUEST, \
    #        {'deveui': deveui, 'appeui': appeui, 'devnonce': devnonce})
    #lora_module.transmit(join_request.to_raw())
    #
    #lora_module.rx_mode()

    ## block until join accept was received
    #while not lora_module.recv_flag:
    #    continue
    #
    #join_accept = LoRaWAN.new([], appkey)
    #join_accept.read(list(lora_module.recv_packet))

    #print(join_accept.get_payload())
    #print(join_accept.get_mhdr().get_mversion())

    #if join_accept.get_mhdr().get_mtype() == MHDR.JOIN_ACCEPT:
    #    print(join_accept.valid_mic())
    #    print(join_accept.get_devaddr())
    #    print(join_accept.derive_nwskey(devnonce))
    #    print(join_accept.derive_appskey(devnonce))

    #print("Received packet: {}", lora_module.recv_packet)

    #led.value(1)
 
    #print("Initialized system. Starting main loop")
    #while True:
    #    continue
    lora_module.set_sleep()
    temp = ds.convert_temp()
    print(roms[0])
    cnt = 0
    while True:
        ds.convert_temp()
        sleep(0.1)
        if len(roms) != 2:
            temp = -99.0
            temp2 = -99.0
        else:
            temp = ds.read_temp(b'(\x8c\xc3!\x02\x00\x00U')
            temp2 = ds.read_temp(b'(\xef\xb1\x87\x02\x00\x00\x81')
        
        lorawan = LoRaWAN.new(secret.nwkskey, secret.appskey)
        lorawan.create(MHDR.UNCONF_DATA_UP, {'devaddr': secret.devaddr,
            'fcnt': cnt, 'data': list(map(ord, 'Hello World! {:2.1f}'.format(temp)))})

        lora_module.transmit(lorawan.to_raw())
        lora_module.set_sleep()
        oled.fill(0)
        oled.text('FCnt: {}'.format(cnt), 0,0)
        oled.text('{:2.1f}'.format(temp), 0,20)
        oled.text('{:2.1f}'.format(temp2), 0,30)
        oled.show()
        
        cnt += 1
        sleep(10-0.1)
