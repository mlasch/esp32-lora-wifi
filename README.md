The Wifi Lora 32 board features an ESP32 microcontroller, a SX1276 LoRa tranceiver and a SSD1306 comaptible oled display.

# Notes
  * How to install: https://www.instructables.com/id/MicroPython-on-an-ESP32-Board-With-Integrated-SSD1/
  * Hardware https://www.hackerspace-ffm.de/wiki/index.php?title=Heltec_Wifi_LoRa_32

# Install
```
pip3 install esptool
```

## Micropython
The serial interface defaults to ```/dev/ttyUSB0```

```
$ esptool.py erase_flash
```

Download matching binary from https://micropython.org/download#esp32

```
esptool.py write_flash -z 0x1000 esp32-20180721-v1.9.4-403-g81e320aec.bin
```

Access the Python console
```
$ screen /dev/ttyUSB0 115200
```

## Libraries
Ampy is a tool to interact with the Micropython serial console. We use it to copy files to the esp32 filesystem.

``` 
pip3 install adafruit-ampy
```

```
ampy --port /dev/ttyUSB0 --baud 115200 put micropython-adafruit-ssd1306/ssd1306.py
```

# LCD Demo

```
>>> import machine, ssd1306
```
OLED_RST is connected to pin 16 and must kept high.
```
>>> pin16 = machine.Pin(16, machine.Pin.OUT)
>>> pin16.value(1)
```


```
>>> i2c = machine.I2C(scl=machine.Pin(15), sda=machine.Pin(4))
>>> oled = ssd1306.SSD1306_I2C(128, 64, i2c)
>>> oled.fill(0)
>>> oled.text('Hello World!', 0,0)
>>> oled.show()
```

# LED Demo
Control the white led.
```
>>> led = machine.Pin(25, machine.Pin.OUT)
>>> led.value(1) #on
>>> led.value(0) #off
```

# OneWire Demo
Read a Dallas 18B20 temperature sensor, connected to `GPIO12`

http://docs.micropython.org/en/v1.9.3/esp8266/esp8266/tutorial/onewire.html

```
>>> dat = machine.Pin(12, machine.Pin.IN, machine.Pin.PULL_UP)
>>> ds = ds18x20.DS18X20(onewire.OneWire(dat))
>>> ds.scan()
[bytearray(b'(\x8c\xc3!\x02\x00\x00U')]
>>> roms = ds.scan()
>>> ds.convert_temp()
>>> ds.read_temp(roms[0])
31.5625
```

# Hardware
Pinout

| `GPIO`         | Description    |
| -------------------: | :------------- |
| `GPIO15`          | OLED_SCL |
| `GPIO4`            | OLED_SDA |
| `GPIO16`          | OLED_RST  |
| `GPIO25`          | white LED  |
| `GPIO5`            | **SCK** (SX1276) |
| `GPIO19`          | **MISO** (SX1276) |
| `GPIO27`          | **MOSI** (SX1276) |
| `GPIO18`          | **CS** (SX1276) |
| `GPIO14`          | **RESET** |
| `GPIO26`          | **DIO1** IRQ (8) |
| `GPIO33`          | **DIO2** 32k_XN (9)  |
| `GPIO32`          | **DIO3** 32k_XP (10) |
