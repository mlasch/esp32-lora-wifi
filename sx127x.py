from time import sleep
import gc

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
REG_PKT_SNR_VALUE = 0x1b
REG_HOP_CHANNEL = 0x1c
REG_MODEM_CONFIG_1 = 0x1d
REG_MODEM_CONFIG_2 = 0x1e
REG_PREAMBLE_MSB = 0x20
REG_PREAMBLE_LSB = 0x21
REG_PAYLOAD_LENGTH = 0x22
REG_HOP_PERIOD = 0x24
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

FIFO_RX_BASE_ADDR = 0x00
FIFO_TX_BASE_ADDR = 0x80

IRQ_FHSS_CHANGE_CHANNEL = 0x01
IRQ_TX_DONE_MASK = 0x08
IRQ_PAYLOAD_CRC_ERROR_MASK = 0x20
IRQ_RX_DONE_MASK = 0x40
IRQ_RX_TIME_OUT_MASK = 0x80

class SX127x(object):
    def __init__(self):
        self.recv_flag = False
        self.setup()

    def setup(self, freq=868.1e6, bw=125e3, cr=7, impl=0, sf=7):
        self.impl = impl
        

        self.reset_chip()
        
        sleep(0.1)
        self.set_sleep()
        
        self.set_frequency(freq)
        self.set_config_1(bw, cr, impl) # 4/7, implicit header
        self.set_config_2(sf)

        # enable AGC
        self.write_register(REG_MODEM_CONFIG_3, 0x04)

        # set output pin and tx power 
        #self.write_register(REG_PA_CONFIG, 0x70 | 14)
        self.write_register(REG_PA_CONFIG, 0x8f)

        self.write_register(REG_LNA, 0x23)  # LNA Gain -> G1 max
                                            # LNA Boost RF 150%

        # configure fifo addresses
        # default setting: TX 0x80
        #                RX: 0x00
   
    def handle_rx(self, arg):
        # set FIFO address to current rx address
        self.write_register(REG_FIFO_ADDR_PTR,
                self.read_register(REG_FIFO_RX_CURRENT_ADDR))

        pkt_length = self.read_register(REG_RX_NB_BYTES)

        self.recv_packet = bytearray()

        for _ in range(pkt_length):
            self.recv_packet.append(self.read_register(REG_FIFO))
        
        self.recv_flag = True

    def transmit(self, payload):
        self.set_standby()

        # set data pointer
        self.write_register(REG_FIFO_ADDR_PTR, FIFO_TX_BASE_ADDR)
        #current = self.read_register(REG_PAYLOAD_LENGTH)
        #print("Current register: ", current)

        # write packet into fifo buffer
        for byte in bytes(payload):
            self.write_register(REG_FIFO, byte)

        # set packet length
        self.write_register(REG_PAYLOAD_LENGTH, len(payload))
       
        self.write_register(REG_OP_MODE,
                MODE_LONG_RANGE | MODE_TX)
        

        while (self.read_register(REG_IRQ_FLAGS) & IRQ_TX_DONE_MASK) == 0:
            sleep(1)

        print("TX DONE")

        gc.collect()

    def reset_chip(self):
        self.rst_pin.value(0)
        sleep(0.012)         
        self.rst_pin.value(1)

    def set_config_2(self, sp_factor):
        cur_reg = self.read_register(REG_MODEM_CONFIG_2)

        self.write_register(REG_MODEM_CONFIG_2, (cur_reg & 0x0f) | \
                (sp_factor<<4))
        

    def set_config_1(self, bw, rate, impl_header=0):
        #cur_reg = self.read_register(REG_MODEM_CONFIG_1)

        # bandith
        bins = (7.8e3, 10.4e3, 15.6e3, 20.8e3, 31.25e3,
                41.7e3, 62.5e3, 125e3, 250e3, 500e3)

        for bw_idx in range(len(bins)):
            if bw <= bins[bw_idx]:
                break
        bw_idx = bw_idx<<4
       
        # coding rate
        crate = int(rate-4)<<1

        self.write_register(REG_MODEM_CONFIG_1,
                (bw_idx | crate | impl_header))

    def set_frequency(self, freq):
        self.frequency = freq

        # f_rf = f_step * FRF_*(23:0)
        fxosc = 32e6
        f_step = fxosc/2**19

        reg_val = freq/f_step

        self.write_register(REG_FRF_MSB,int(reg_val/2**16))
        self.write_register(REG_FRF_MID,int(reg_val/3**8) & 0xff)
        self.write_register(REG_FRF_LSB,int(reg_val) & 0xff)

    def get_irq_flags(self):
        irq_flags = self.read_register(REG_IRQ_FLAGS)

        # clear flags
        self.write_register(REG_IRQ_FLAGS, irq_flags)

        return irq_flags

    def get_random(self, n):
        """
        Read n true random bytes from RegRssiWideband
        """
        reg_op_mode = self.read_register(REG_OP_MODE)
        reg_modem_config1 = self.read_register(REG_MODEM_CONFIG_1)
        reg_modem_config2 = self.read_register(REG_MODEM_CONFIG_2)
        
        # recommended settings from AN1200.24
        self.write_register(REG_OP_MODE, 0x8d)
        self.write_register(REG_MODEM_CONFIG_1, 0x72)
        self.write_register(REG_MODEM_CONFIG_2, 0x70)
        
        buf = b''
        for i in range(n):
            b = 0
            for j in range(8):
                b |= (self.read_register(REG_RSSI_WIDEBAND) & 0x01) << j
            buf += bytes([b]) 
        self.write_register(REG_OP_MODE, reg_op_mode)
        self.write_register(REG_MODEM_CONFIG_1, reg_modem_config1)
        self.write_register(REG_MODEM_CONFIG_2, reg_modem_config2)

        gc.collect()

        return buf
         

    def get_rssi(self):
        return (self.read_register(REG_PKT_RSSI_VALUE) - (164 if self.frequency < 868e6 else 157))

    def get_snr(self):
        return (self.read_register(REG_PKT_SNR_VALUE)) * 0.25


    def rx_mode(self):
        self.set_continuous_rx()
        
        if self.impl == 1:
            self.write_register(REG_PAYLOAD_LENGTH, 15)

    def read_packet(self):
        # set FIFP address to current rx address
        self.write_register(REG_FIFO_ADDR_PTR, 
                self.read_register(REG_FIFO_RX_CURRENT_ADDR))
    
        pkt_length = self.read_register(REG_RX_NB_BYTES)

        buf = bytearray()

        for _ in range(pkt_length):
            buf.append(self.read_register(REG_FIFO))

        gc.collect()

        return buf

    def wait_for_join_accept(self):
        while True:
            pass

    def set_continuous_rx(self):
        self.write_register(REG_OP_MODE,
                MODE_LONG_RANGE | MODE_RX_CONTINUOUS)

    def set_sleep(self):
        self.write_register(REG_OP_MODE,
                MODE_LONG_RANGE | MODE_SLEEP)

    def set_standby(self):
        self.write_register(REG_OP_MODE,
                MODE_LONG_RANGE | MODE_STDBY)

    def read_register(self, addr):
        return int.from_bytes(self._transfer(addr & 0x7f), 'big')

    def write_register(self, addr, val):
        self._transfer(addr | 0x80, val)

    def close(self):
        self.spi.deinit()
