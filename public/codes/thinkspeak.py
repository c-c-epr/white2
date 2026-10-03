from machine import Pin
import time
import utime
import dht
from time import sleep
import network
import urequests as requests
import ujson

# Initialize sensor and LED
dSensor = dht.DHT22(Pin(28))
led_onboard = machine.Pin("LED", machine.Pin.OUT)

# Network Initialization
ssid = "Pixel4"
password = "123456789"

# ThingSpeak Configuration
THINGSPEAK_WRITE_API_KEY = "YOUR_WRITE_API_KEY"  # 請替換為你的 Write API Key
THINGSPEAK_URL = "https://api.thingspeak.com/update"

# Global variables for sensor readings
temp = 0
temp_f = 0
hum = 0


def ConnectWiFi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    print("Connecting to WiFi...")
    timeout = 10  # 10 秒超時
    while wlan.isconnected() == False and timeout > 0:
        print("Waiting for connection...")
        sleep(1)
        timeout -= 1

    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print(f"Connected on {ip}")
        return ip
    else:
        raise Exception("WiFi connection timeout")


def readDHT():
    global temp, temp_f, hum
    try:
        dSensor.measure()
        time.sleep(0.2)  # 等待感測器穩定

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

        print("Temperature= {:.1f}°C, {:.1f}°F".format(temp, temp_f))
        print("Humidity= {:.1f}%".format(hum))
        return True

    except OSError as e:
        print("Failed to read sensor:", e)
        # LED 錯誤指示
        for _ in range(3):
            led_onboard.value(1)
            utime.sleep(0.1)
            led_onboard.value(0)
            utime.sleep(0.1)
        return False


def send_to_thingspeak(temperature, humidity):
    """發送資料到 ThingSpeak"""
    try:
        print(
            f"Sending to ThingSpeak: Temp={temperature:.1f}°C, Humidity={humidity:.1f}%"
        )

        # 方法1: 使用 URL 參數 (推薦)
        url_with_params = f"{THINGSPEAK_URL}?api_key={THINGSPEAK_WRITE_API_KEY}&field1={temperature:.1f}&field2={humidity:.1f}"
        print(f"Request URL: {url_with_params}")

        response = requests.get(url_with_params)

        # 方法2: 如果要使用 POST，改用這個格式
        # headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        # payload = f"api_key={THINGSPEAK_WRITE_API_KEY}&field1={temperature:.1f}&field2={humidity:.1f}"
        # response = requests.post(THINGSPEAK_URL, data=payload.encode('utf-8'), headers=headers)

        if response.status_code == 200:
            entry_id = response.text.strip()
            if entry_id != "0":
                print(f"✓ ThingSpeak upload successful! Entry ID: {entry_id}")
                # 成功指示燈
                led_onboard.value(1)
                time.sleep(0.5)
                led_onboard.value(0)
                return True
            else:
                print("✗ ThingSpeak returned 0 (upload failed - check API key)")
                return False
        else:
            print(f"✗ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"✗ ThingSpeak upload error: {e}")
        return False
    finally:
        # 確保關閉 response
        try:
            response.close()
        except:
            pass


# WiFi 連線
print("=== Starting DHT22 + ThingSpeak Monitor ===")
try:
    ip = ConnectWiFi()
except Exception as e:
    print(f"WiFi connection failed: {e}")
    print("Please check your WiFi credentials and try again")
    # WiFi 錯誤指示燈
    while True:
        led_onboard.value(1)
        sleep(0.1)
        led_onboard.value(0)
        sleep(0.1)

# 檢查 API Key 設定
if THINGSPEAK_WRITE_API_KEY == "YOUR_WRITE_API_KEY":
    print("⚠️  Please update THINGSPEAK_WRITE_API_KEY with your actual API key!")
    while True:
        led_onboard.value(1)
        sleep(2)
        led_onboard.value(0)
        sleep(0.5)

print(f"ThingSpeak API Key: {THINGSPEAK_WRITE_API_KEY}")
print("Starting sensor monitoring...")

# 等待感測器初始化
time.sleep(2)

# 主迴圈
consecutive_failures = 0
max_failures = 5

try:
    while True:
        print("\n--- Reading DHT22 Sensor ---")

        # 讀取感測器
        if readDHT():
            consecutive_failures = 0  # 重置失敗計數

            # 發送到 ThingSpeak
            success = send_to_thingspeak(temp, hum)

            if not success:
                print("Failed to upload to ThingSpeak, will retry next cycle")
                # 上傳失敗指示燈
                for _ in range(2):
                    led_onboard.value(1)
                    time.sleep(0.2)
                    led_onboard.value(0)
                    time.sleep(0.2)
        else:
            consecutive_failures += 1
            print(f"Sensor read failed ({consecutive_failures}/{max_failures})")

            if consecutive_failures >= max_failures:
                print("Too many consecutive sensor failures, restarting...")
                machine.reset()

        # ThingSpeak 免費版限制每 15 秒一次上傳
        print("Waiting 20 seconds before next reading...")
        for i in range(20, 0, -1):
            if i % 5 == 0:
                print(f"Next reading in {i} seconds...")
            time.sleep(1)

except KeyboardInterrupt:
    print("\n=== Program stopped by user ===")
except Exception as e:
    print(f"\n=== Unexpected error: {e} ===")
    print("Restarting system...")
    time.sleep(5)
    machine.reset()
finally:
    print("Cleaning up...")
    led_onboard.value(0)
