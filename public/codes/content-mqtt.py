from machine import Pin
import time
import utime
import dht
from time import sleep
import network
from umqtt.simple import MQTTClient

# Initialize sensor and LED
dSensor = dht.DHT22(Pin(28))
led_onboard = machine.Pin("LED", machine.Pin.OUT)

# Network Initialization
ssid = "Pixel4"
password = "123456789"

# Global variables for sensor readings
temp = 0
temp_f = 0
hum = 0


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
    global temp, temp_f, hum  # Add global declaration
    try:
        dSensor.measure()
        # 等待感測器穩定
        time.sleep(0.2)

        temp = dSensor.temperature()
        hum = dSensor.humidity()

        # 檢查讀取值是否有效
        if temp is None or hum is None:
            print("Sensor returned None values")
            return False

        # 檢查數值是否在合理範圍內
        if temp < -40 or temp > 80 or hum < 0 or hum > 100:
            print(f"Invalid sensor readings: temp={temp}, hum={hum}")
            return False

        temp_f = (temp * (9 / 5)) + 32.0

        print("Temperature= {:.1f} C, {:.1f} F".format(temp, temp_f))
        print("Humidity= {:.1f} %".format(hum))
        return True  # Return success status
    except OSError as e:
        print("Failed to read data from DHT sensor:", e)
        # Blink LED to indicate error
        led_onboard.value(1)
        utime.sleep(0.3)
        led_onboard.value(0)
        utime.sleep(0.3)
        return False  # Return failure status


# Connect to Network
try:
    ip = ConnectWiFi()
except Exception as e:
    print(f"WiFi connection failed: {e}")
    # Handle WiFi connection failure gracefully
    while True:
        led_onboard.value(1)
        sleep(0.1)
        led_onboard.value(0)
        sleep(0.1)

# MQTT Configuration
mqtt_host = "broker.mqttgo.io"  # Fixed case sensitivity
mqtt_username = ""  # Your MQTTGO.io username
mqtt_password = ""  # MQTTGO.io key
mqtt_publish_topic = "yisong/temp"  # The MQTT topic for your feed溫度
mqtt_publish_topic2 = "yisong/hum"  # 濕度
mqtt_client_id = "somethingreallyrandomandunique123"

# Initialize MQTT Client
try:
    mqtt_client = MQTTClient(
        client_id=mqtt_client_id,
        server=mqtt_host,
        user=mqtt_username,
        password=mqtt_password,
    )
    mqtt_client.connect()
    print("Connected to MQTT broker")
except Exception as e:
    print(f"MQTT connection failed: {e}")
    # Handle MQTT connection failure
    while True:
        led_onboard.value(1)
        sleep(0.5)
        led_onboard.value(0)
        sleep(0.5)

# Main loop
print("Starting sensor readings...")
# 初次讀取前等待感測器啟動
time.sleep(2)

try:
    while True:
        print("--- Reading sensor ---")
        success = readDHT()

        if success:  # Only publish if sensor reading was successful
            # Send temperature in Celsius as simple string
            payload = f"{temp:.1f}"
            payload2 = f"{hum:.1f}"

            try:
                mqtt_client.publish(mqtt_publish_topic, payload)
                print(f"Published temperature: {payload}°C")
                mqtt_client.publish(mqtt_publish_topic2, payload2)
                print(f"Published humidity: {payload2}")

                # Brief LED flash to indicate successful publish
                led_onboard.value(1)
                time.sleep(0.1)
                led_onboard.value(0)

            except Exception as e:
                print(f"Failed to publish message: {e}")
        else:
            print("Sensor reading failed, skipping MQTT publish")

        # Wait before next reading (DHT22 needs at least 2 seconds between readings)
        print("Waiting 5 seconds before next reading...")
        time.sleep(5)

except KeyboardInterrupt:
    print("Program interrupted by user")
except Exception as e:
    print(f"Unexpected error: {e}")
finally:
    try:
        mqtt_client.disconnect()
        print("Disconnected from MQTT broker")
    except:
        pass
