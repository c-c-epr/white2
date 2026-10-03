from machine import Pin
import time
import utime
import dht

from time import sleep
import network

dSensor = dht.DHT22(Pin(28))

led_onboard = machine.Pin("LED", machine.Pin.OUT)

# Network Initialization
ssid = "TUNG"
password = "ipadipad@tung"


def ConnectWiFi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while wlan.isconnected() == False:
        print("Waiting for connection...")
        sleep(1)
    ip = wlan.ifconfig()[0]
    print(f"Connected on {ip}")
    return ip


def readDHT():
    try:
        dSensor.measure()
        temp = dSensor.temperature()
        temp_f = (temp * (9 / 5)) + 32.0
        hum = dSensor.humidity()

        print("Temperature= {} C, {} F".format(temp, temp_f))
        print("Humidity= {} ".format(hum))
    except OSError as e:
        print("Failed to read data from DHT sensor")
        led_onboard.value(1)
        utime.sleep(0.3)
        led_onboard.value(0)
        utime.sleep(0.3)


# Connect to Network
ip = ConnectWiFi()

while True:
    readDHT()
    time.sleep(1)
