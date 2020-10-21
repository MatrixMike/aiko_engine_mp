# lib/aiko/oled.py: version: 2020-10-11 05:00
#
# Usage
# ~~~~~
# import aiko.oled
# aiko.oled.initialise()
# oled.title = "Title"
# oled.write_title()
# oled.log("Log message"))
#
# MQTT commands
# ~~~~~~~~~~~~~
# Topic: /in   (oled:clear)
#              (oled:log This is a test !)
#              (oled:pixel x y)
#              (oled:text x y This is a test !)
#              oled.bg=1; oled.fg=0
#
# Topic: /in   (oled:traits)
#        /out  (oled:traits ????)
#
# To Do
# ~~~~~
# - Only register MQTT on_oled_message() if MQTT is enabled
# - Only register MQTT on_oled_log_message() if MQTT is enabled
#
# Resources
# ~~~~~~~~~
# http://docs.micropython.org/en/latest/pyboard/library/framebuf.html

'''
ol = aiko.oled.oled
x = 0;  y = 32
bg = 1; fg = 0
ol.fill(bg)
ol.pixel(x, y, fg)
ol.text("text", x, y, fg)
ol.hline(x, y, w, fg)
ol.vline(x, y, h, fg)
ol.line(x1, y1, x2, y2, fg)
ol.rect(x, y, w, h, fg)
ol.fill_rect(x, y, w, h, fg)
ol.scroll(xs, ys)
ol.blit(frame_buffer, x, y, key)

ol.poweron()
ol.poweroff()
ol.invert(0|1)
ol.contrast(0 .. 255)
'''

import configuration.oled
import aiko.mqtt as mqtt

from machine import Pin
import machine, ssd1306

oleds = []
width = None
height = None
font_size = None
bottom_row = None
bg = 0
fg = 1

lock_title = False
title = "Aiko 0.1"

def initialise(settings=configuration.oled.settings):
  global lock_title, width, height, font_size, bottom_row
  parameter = configuration.main.parameter

  Pin(int(settings["enable_pin"]), Pin.OUT).value(1)
  addresses = settings["addresses"]
  scl_pin = int(settings["scl_pin"])
  sda_pin = int(settings["sda_pin"])

  lock_title = parameter("lock_title", settings)
  width = int(settings["width"])
  height = int(settings["height"])
  font_size = int(settings["font_size"])
  bottom_row = height - font_size

  i2c = machine.I2C(scl=Pin(scl_pin), sda=Pin(sda_pin))
# i2c.scan()
  for addr in addresses:
    oleds.append(ssd1306.SSD1306_I2C(width, height, i2c, addr=addr))
  oleds_clear(bg)

  mqtt.add_message_handler(on_oled_message, "$me/in")
  if parameter("logger_enabled"):
    mqtt.add_message_handler(on_oled_log_message, "$all/log")

def log(text):
  for oled in oleds:
    oled.scroll(0, -font_size)
    oled.fill_rect(0, bottom_row, width, font_size, bg)
    length = len(text) * font_size
    if length > width:
        snippet = text[0:int(width/font_size)]
        oled.text(snippet, 0, bottom_row,fg)
        oled.show()
        log(text[len(snippet):])
    else:
        oled.text(text, 0, bottom_row, fg)
        oled.show()

  if lock_title: write_title()

def oleds_clear(bg):
  for oled in oleds:
    oled.fill(bg)
    oled.show()
  if lock_title: write_title()

def oleds_show():
  for oled in oleds:
    oled.show()

def test(text="Line "):
  for oled in oleds:
    oled.fill(bg)
    for y in range(0, height, font_size):
      oled.text(text + str(y), 0, y, fg)
    oled.show()

def write_title():
  for oled in oleds:
    oled.fill_rect(0, 0, width, font_size, fg)
    oled.text(title, 0, 0, bg)
    oled.show()

def on_oled_message(topic, payload_in):
  if payload_in == "(oled:clear)":
    oleds_clear(bg)
    return True

  if payload_in.startswith("(oled:log "):
    log(payload_in[10:-1])
    return True

  if payload_in.startswith("(oled:pixel "):
    tokens = [int(token) for token in payload_in[12:-1].split()]
    for oled in oleds:
      oled.pixel(tokens[0], height - tokens[1] - 1, fg)
      oled.show()
    return True

  if payload_in.startswith("(oled:text "):
    tokens = payload_in[11:-1].split()
    text = " ".join(tokens[2:])
    for oled in oleds:
      oled.text(text, int(tokens[0]), height - font_size - int(tokens[1]), fg)
      oled.show()
    return True

  return False

def on_oled_log_message(topic, payload_in):
  log(payload_in)
  return True

'''
# cs   = Pin( 2, mode=Pin.OUT)
# rst  = Pin(15, mode=Pin.OUT)
# mosi = Pin(14, mode=Pin.OUT)
# miso = Pin(12, mode=Pin.IN)
# sck  = Pin(13, mode=Pin.OUT)
# spi  = machine.SPI(baudrate=100000, sck=sck, mosi=mosi, miso=miso)
# oled = ssd1306.SSD1306_SPI(128, 64, spi)

# sck  = machine.Pin(19, machine.Pin.OUT)
# mosi = machine.Pin(23, machine.Pin.IN)
# miso = machine.Pin(25, machine.Pin.OUT)
# pcs  = machine.Pin(26, machine.Pin.OUT)
# pdc  = machine.Pin(27, machine.Pin.OUT)
# prst = machine.Pin(18, machine.Pin.OUT)

# spi  = machine.SPI(1,baudrate=1000000, sck=sck, mosi=mosi, miso=miso)
# oled = ssd1306.SSD1306_SPI(128, 64, spi, pdc, prst, pcs)
'''
