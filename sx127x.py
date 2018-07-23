from time import sleep

# Register addresses
REG_FIFO = 0x00
REG_OP_MODE = 0x01
REG_FRF_MSB = 0x06
REG_FRF_MID = 0x07
REG_FRF_LSB = 0x08
REG_PA_CONFIG = 0x09
REG_PA_RAMP = 0x0a
REG_OCP = 0x0b
REG_LNA = 0x0c
REG_FIFO_ADDR_PTR = 0x0d
REG_FIFO_TX_BASE_ADDR = 0x0e
REG_FIFO_RX_BASE_ADDR = 0x0f
REG_FIFO_RX_CURRENT_ADDR = 0x10
REG_IRQ_FLAGS_MASK = 0x11
REG_IRQ_FLAGS = 0x12
REG_RX_NB_BYTES = 0x13
REG_MODEM_STAT = 0x18
REG_PKT_RSSI_VALUE = 0x1a
REG_PKT_SNA_VALUE = 0x1b
REG_MODEM_CONFIG_1 = 0x1d
REG_MODEM_CONFIG_2 = 0x1e
REG_PREAMBLE_MSB = 0x20
REG_PREAMBLE_LSB = 0x21
REG_PAYLOAD_LENGTH = 0x22
REG_FIFO_RX_BYTE_ADDR = 0x25
REG_MODEM_CONFIG_3 = 0x26
REG_RSSI_WIDEBAND = 0x2c
REG_DETECTION_OPTIMIZE = 0x31
REG_DETECTION_THRESHOLD = 0x37
REG_SYNC_WORD = 0x39
REG_DIO_MAPPING_1 = 0x40
REG_VERSION = 0x42

MODE_LONG_RANGE = 0x80  # lora mode: bit 7
MODE_SLEEP = 0x00
MODE_STDBY = 0x01
MODE_TX = 0x03
MODE_RX_CONTINUOUS = 0x05
MODE_RX_SINGLE = 0x06

class SX127x(object):
    def __init__(self):
        
        
        self.setup()

    def setup(self):
        self.reset_chip()
        self.set_sleep()
        self.set_frequency(868e6)
        self.set_bandwith(125e3)

    def reset_chip(self):
        self.rst_pin.value(0)
        sleep(0.012)
        self.rst_pin.value(1)

    def set_bandwith(self, bw):
        pass

    def set_frequency(self, freq):
        self.frequency = freq

        # f_rf = f_step * FRF_*(23:0)
        fxosc = 32e6
        f_step = fxosc/2**19

        reg_val = freq/f_step

        self.write_register(REG_FRF_MSB,int(reg_val/2**16))
        self.write_register(REG_FRF_MID,int(reg_val/2**8) & 0xff)
        self.write_register(REG_FRF_LSB,int(reg_val) & 0xff)

    def set_sleep(self):
        self.write_register(REG_OP_MODE,
                MODE_LONG_RANGE | MODE_SLEEP)

    def set_standby(self):
        self.write_register(REG_OP_MODE,
                MODE_LONG_RANGE | MODE_STDBY)

    def read_register(self, addr):
        return self._transfer(addr & 0x7f)

    def write_register(self, addr, val):
        self._transfer(addr | 0x80, val)

    def close(self):
        self.spi.deinit()
