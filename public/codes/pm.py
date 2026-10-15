from machine import Pin, UART
import time
import utime
import dht
from time import sleep
import network
from umqtt.simple import MQTTClient
import urequests  # 用於 HTTP 請求
import struct

# Initialize sensor and LED
dSensor = dht.DHT22(Pin(28))
led_onboard = machine.Pin("LED", machine.Pin.OUT)

# PMS5003 UART 初始化 (使用 UART1, GPIO 4=TX, GPIO 5=RX)
uart = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))

# Network Initialization
ssid = "Pixel4"
password = "12345678"

# Global variables for sensor readings
temp = 0
temp_f = 0
hum = 0
pm1 = 0
pm25 = 0
pm10 = 0

# ThingSpeak Configuration
THINGSPEAK_API_KEY = "YOUR_WRITE_API_KEY_HERE"  # 請替換為你的 Write API Key
THINGSPEAK_URL = "http://api.thingspeak.com/update"


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


def readPMS5003():
    """讀取 PMS5003 感測器數據"""
    global pm1, pm25, pm10

    try:
        # 清空 UART 緩衝區
        while uart.any():
            uart.read()

        # 等待數據
        time.sleep(1)

        # 尋找數據包開始標誌 0x42 0x4d
        attempts = 0
        while attempts < 10:
            if uart.any() >= 2:
                data = uart.read(2)
                if data == b"\x42\x4d":
                    break
            time.sleep(0.1)
            attempts += 1
        else:
            print("PMS5003: Start bytes not found")
            return False

        # 讀取剩餘的 30 字節數據
        if uart.any() < 30:
            time.sleep(0.5)  # 等待更多數據

        if uart.any() < 30:
            print("PMS5003: Insufficient data")
            return False

        remaining_data = uart.read(30)
        full_data = b"\x42\x4d" + remaining_data

        # 驗證數據長度和校驗和
        if len(full_data) != 32:
            print(f"PMS5003: Invalid data length: {len(full_data)}")
            return False

        # 檢查校驗和
        checksum = sum(full_data[:-2])
        received_checksum = struct.unpack(">H", full_data[-2:])[0]

        if checksum != received_checksum:
            print(
                f"PMS5003: Checksum error. Calculated: {checksum}, Received: {received_checksum}"
            )
            return False

        # 解析數據 (使用大端序)
        # 字節 4-5: PM1.0 (CF=1)
        # 字節 6-7: PM2.5 (CF=1)
        # 字節 8-9: PM10 (CF=1)
        pm1 = struct.unpack(">H", full_data[4:6])[0]
        pm25 = struct.unpack(">H", full_data[6:8])[0]
        pm10 = struct.unpack(">H", full_data[8:10])[0]

        # 數據合理性檢查
        if pm1 > 500 or pm25 > 500 or pm10 > 500:
            print(
                f"PMS5003: Unreasonable values - PM1.0: {pm1}, PM2.5: {pm25}, PM10: {pm10}"
            )
            return False

        print(f"PM1.0: {pm1} μg/m³, PM2.5: {pm25} μg/m³, PM10: {pm10} μg/m³")
        return True

    except Exception as e:
        print(f"PMS5003 reading error: {e}")
        return False


def send_to_thingspeak(temperature, humidity, pm1_val, pm25_val, pm10_val):
    """發送資料到 ThingSpeak"""
    try:
        # 建立 URL 參數 (使用 5 個欄位)
        url = f"{THINGSPEAK_URL}?api_key={THINGSPEAK_API_KEY}&field1={temperature:.1f}&field2={humidity:.1f}&field3={pm1_val}&field4={pm25_val}&field5={pm10_val}"

        # 發送 HTTP GET 請求
        response = urequests.get(url)

        if response.status_code == 200:
            entry_id = response.text.strip()
            if entry_id != "0":  # ThingSpeak 成功時會回傳 entry ID
                print(f"ThingSpeak upload successful! Entry ID: {entry_id}")
                return True
            else:
                print("ThingSpeak upload failed - API returned 0")
                return False
        else:
            print(f"ThingSpeak HTTP error: {response.status_code}")
            return False

    except Exception as e:
        print(f"ThingSpeak upload error: {e}")
        return False
    finally:
        try:
            response.close()  # 釋放連線資源
        except:
            pass


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
mqtt_publish_topic = "yisong/temp"  # 溫度
mqtt_publish_topic2 = "yisong/hum"  # 濕度
mqtt_publish_topic3 = "yisong/pm1"  # PM1.0
mqtt_publish_topic4 = "yisong/pm25"  # PM2.5
mqtt_publish_topic5 = "yisong/pm10"  # PM10
mqtt_client_id = "somethingreallyrandomandunique123"


def connect_mqtt():
    """連接到 MQTT broker，包含重試機制"""
    global mqtt_client
    max_retries = 3

    for attempt in range(max_retries):
        try:
            print(f"MQTT connection attempt {attempt + 1}/{max_retries}")
            mqtt_client = MQTTClient(
                client_id=mqtt_client_id,
                server=mqtt_host,
                user=mqtt_username,
                password=mqtt_password,
                keepalive=60,
            )  # 設定心跳包間隔
            mqtt_client.connect()
            print("Connected to MQTT broker")
            return True
        except Exception as e:
            print(f"MQTT connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print("Retrying in 5 seconds...")
                time.sleep(5)

    print("All MQTT connection attempts failed")
    return False


def publish_mqtt_data(topic, payload):
    """發布 MQTT 資料，包含重連機制"""
    global mqtt_client
    max_retries = 2

    for attempt in range(max_retries):
        try:
            mqtt_client.publish(topic, payload)
            return True
        except Exception as e:
            print(f"MQTT publish attempt {attempt + 1} failed: {e}")

            # 如果是連線錯誤，嘗試重新連接
            if "ECONNABORTED" in str(e) or "ENOTCONN" in str(e) or attempt == 0:
                print("Attempting to reconnect to MQTT...")
                try:
                    mqtt_client.disconnect()
                except:
                    pass

                if connect_mqtt():
                    continue  # 重連成功，重試發布
                else:
                    break  # 重連失敗，退出
            else:
                break

    return False


# Initialize MQTT Client
mqtt_client = None
if not connect_mqtt():
    print("Initial MQTT connection failed, continuing without MQTT...")
    mqtt_client = None

# Main loop
print("Starting sensor readings...")
# 初次讀取前等待感測器啟動
time.sleep(2)

try:
    while True:
        print("--- Reading sensors ---")

        # 讀取 DHT22 溫濕度
        dht_success = readDHT()

        # 讀取 PMS5003 PM 數值
        pms_success = readPMS5003()

        if dht_success or pms_success:  # 至少一個感測器讀取成功
            # 準備 MQTT payload
            temp_payload = f"{temp:.1f}" if dht_success else "N/A"
            hum_payload = f"{hum:.1f}" if dht_success else "N/A"
            pm1_payload = f"{pm1}" if pms_success else "N/A"
            pm25_payload = f"{pm25}" if pms_success else "N/A"
            pm10_payload = f"{pm10}" if pms_success else "N/A"

            # 發送到 MQTT (使用重連機制)
            mqtt_success = False
            if mqtt_client is not None:
                mqtt_results = []
                if dht_success:
                    mqtt_results.append(
                        publish_mqtt_data(mqtt_publish_topic, temp_payload)
                    )
                    mqtt_results.append(
                        publish_mqtt_data(mqtt_publish_topic2, hum_payload)
                    )
                if pms_success:
                    mqtt_results.append(
                        publish_mqtt_data(mqtt_publish_topic3, pm1_payload)
                    )
                    mqtt_results.append(
                        publish_mqtt_data(mqtt_publish_topic4, pm25_payload)
                    )
                    mqtt_results.append(
                        publish_mqtt_data(mqtt_publish_topic5, pm10_payload)
                    )

                if mqtt_results and all(mqtt_results):
                    print("All MQTT data published successfully")
                    mqtt_success = True
                elif any(mqtt_results):
                    print("Partial MQTT publish success")
                    mqtt_success = False
                else:
                    print("MQTT publish failed")
                    mqtt_success = False
            else:
                print("MQTT client not available")

            # 發送到 ThingSpeak (只有當兩個感測器都讀取成功時才發送)
            thingspeak_success = False
            if dht_success and pms_success:
                thingspeak_success = send_to_thingspeak(temp, hum, pm1, pm25, pm10)
            elif dht_success:
                # 只有溫濕度數據時，PM 值設為 0
                thingspeak_success = send_to_thingspeak(temp, hum, 0, 0, 0)
            elif pms_success:
                # 只有 PM 數據時，溫濕度設為 0
                thingspeak_success = send_to_thingspeak(0, 0, pm1, pm25, pm10)

            # LED 指示：根據發送結果顯示不同模式
            if mqtt_success and thingspeak_success:
                # 兩個都成功：單次長閃爍
                led_onboard.value(1)
                time.sleep(0.5)
                led_onboard.value(0)
                print("All data sent successfully!")
            elif mqtt_success or thingspeak_success:
                # 部分成功：兩次短閃爍
                for _ in range(2):
                    led_onboard.value(1)
                    time.sleep(0.1)
                    led_onboard.value(0)
                    time.sleep(0.1)
                print("Partial data transmission success")
            else:
                # 全部失敗：三次快閃爍
                for _ in range(3):
                    led_onboard.value(1)
                    time.sleep(0.05)
                    led_onboard.value(0)
                    time.sleep(0.05)
                print("Data transmission failed")

        else:
            print("All sensors reading failed, skipping data transmission")

        # Wait before next reading
        # ThingSpeak 免費版有 15 秒間隔限制，所以這裡設定為 20 秒比較安全
        print("Waiting 20 seconds before next reading...")
        time.sleep(20)

except KeyboardInterrupt:
    print("Program interrupted by user")
except Exception as e:
    print(f"Unexpected error: {e}")
finally:
    try:
        if mqtt_client is not None:
            mqtt_client.disconnect()
            print("Disconnected from MQTT broker")
    except:
        pass
