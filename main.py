from time import sleep
from machine import Pin, SPI
import network
import socket
import machine

from sx127x import SX127x
import sx127x

PIN_CS = 18
PIN_MOSI = 27
PIN_MISO = 19
PIN_SCK = 5
PIN_RST = 14
PIN_DIO0 = 23 #26
PIN_LED = 25 

def udp_print(sock, msg, end='\n'):
    sock.sendto(msg.encode()+end, ('10.2.2.134', 5001))

class PayloadPkt(object):
    def __init__(self, data):
        self.data = data

    def serialize(self):
        return self.data

    def __len__(self):
        return len(self.data)


class LoRaModule(SX127x):
    def __init__(self, spi=None, rst=None, cs=None,
            dio=(None, None, None)):
        self.spi = spi
        self.rst_pin = rst
        self.cs_pin = cs
        self.dio_pins = dio

        self.dio_pins[0].irq(trigger=Pin.IRQ_RISING, handler=self.rx_callback)
        
        self.cs_pin.value(1)
        self.spi.init()
    
        super().__init__()
        

    def _transfer(self, addr, val = 0x00):
        response = bytearray(1)
        

        self.cs_pin.value(0)
        spi.write(bytes([addr]))
        spi.write_readinto(bytes([val]), response)
        self.cs_pin.value(1)
        
        print("DEBUG: addr: {}, val: {}, resp: {}".format(hex(addr), hex(val), response))

        return response

    def rx_callback(self):
        length = self.read_register(REG_PAYLOAD_LENGTH)
        ddd
        udp_print(sock, 'got packet {}'.format(length))
        print("RX CALLBACK {}".format(length))

if __name__ == '__main__':
    # connect wifi
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect('honigtopf-guest', 'helloworld')

    while not sta_if.isconnected():
        sleep(1)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    udp_print(sock, 'Startup...')

    led = Pin(PIN_LED, Pin.OUT)

    spi = SPI(2, baudrate = 10000000, polarity=0, phase= 0, bits=8, firstbit=SPI.MSB,
            sck = Pin(PIN_SCK, Pin.OUT, Pin.PULL_DOWN),
            mosi = Pin(PIN_MOSI, Pin.OUT, Pin.PULL_UP),
            miso = Pin(PIN_MISO, Pin.IN, Pin.PULL_UP))

    lora_module = LoRaModule(
            spi=spi, 
            rst=Pin(PIN_RST, Pin.OUT), 
            cs=Pin(PIN_CS, Pin.OUT),
            dio=(
                Pin(PIN_DIO0, Pin.IN) 
                ,None, None))

    version = lora_module.read_register(sx127x.REG_VERSION)
    
    if version == 0x12:
        print("Version {} OK".format(version))
    
    #for i in range(15):
    #    lora_module.transmit(PayloadPkt(b'HHello World!1!!'))
    #    print("sent!")
    #    sleep(0.2)
    
    lora_module.rx_mode()
    
    led.value(0)

    while True:
        irq_flags = lora_module.get_irq_flags()
        if (irq_flags & 0x40) == 0x40:
            led.value(1)
            
            rx_buf = lora_module.read_packet()
            rssi = lora_module.get_rssi()
            snr = lora_module.get_snr()

            udp_print(sock, 'IRQ: {} RSSI: {} SNR: {} RX: {}'.format(hex(irq_flags), rssi, snr, rx_buf))
            
        led.value(0)

    lora_module.close()
