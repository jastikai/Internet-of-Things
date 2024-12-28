from machine import Pin, I2C
import network
import utime
from umqtt.simple import MQTTClient
import bme280  # Library supports both BME280 and BMP280 sensors

# Configuration for Wi-Fi and MQTT
WIFI_SSID = "ssid"
WIFI_PASSWORD = "password"

MQTT_BROKER = "192.168.1.69" 
MQTT_PORT = 8883 
MQTT_CLIENT_ID = "pico_w_weather_station"
MQTT_USER = "user"  # Set your MQTT broker username
MQTT_PASSWORD = "password"  # Set your MQTT broker password
MQTT_TOPIC_TEMP = "sensors/temperature"
MQTT_TOPIC_PRESS = "sensors/pressure"
# MQTT_TOPIC_HUM = "sensors/humidity"  # Uncomment if using a BME280 sensor

def connect_to_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.config(pm=0xa11140)  # Disable powersave mode
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    
    print("Connecting to Wi-Fi...")
    for attempt in range(10):
        if wlan.isconnected():
            break
        utime.sleep(1)
        print(f"Attempt {attempt + 1}...")
    
    if wlan.isconnected():
        print("Wi-Fi connected. IP address:", wlan.ifconfig()[0])
    else:
        raise RuntimeError("Wi-Fi connection failed. Check your credentials or network.")

def connect_to_mqtt():
    print("Connecting to MQTT broker...")
    client = MQTTClient(
        client_id=MQTT_CLIENT_ID,
        server=MQTT_BROKER,
        port=MQTT_PORT,
        user=MQTT_USER,
        password=MQTT_PASSWORD,
        keepalive=60,
        ssl=True,
        ssl_params={"server_hostname": MQTT_BROKER}  # Required for verifying broker's certificate
    )
    client.connect()
    client.set_callback(on_message)
    client.subscribe(b"picow/control")
    print("MQTT connected.")
    return client
    
# Warning LED
led_pin = Pin(16, Pin.OUT)

def on_message(topic, msg):
    print(f"Received message: {msg} on topic: {topic}")
    if msg == b"ON":
        led_pin.on()  # Turn on the LED
        print("LED ON")
    elif msg == b"OFF":
        led_pin.off()  # Turn off the LED
        print("LED OFF")

def main():
    try:
        # Connect to Wi-Fi
        connect_to_wifi()

        # Initialize I2C communication for the sensor
        i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=100000)  # Adjust pins if necessary
        sensor = bme280.BME280(i2c=i2c)  # BME280 will automatically ignore humidity if BMP280 is used
        
        # Connect to the MQTT broker
        mqtt_client = connect_to_mqtt()

        # Continuously read data and publish it
        while True:
            # Read sensor data
            temperature = sensor.values[0]  # Temperature in °C
            pressure = sensor.values[1]  # Pressure in hPa
            # humidity = sensor.values[2]  # Uncomment if using BME280

            # Display readings (useful for debugging)
            print(f"Temperature: {temperature} °C")
            print(f"Pressure: {pressure} hPa")
            # print(f"Humidity: {humidity} %")  # Uncomment if using BME280

            # Publish data to MQTT topics
            mqtt_client.publish(MQTT_TOPIC_TEMP, temperature)
            mqtt_client.publish(MQTT_TOPIC_PRESS, pressure)
            # mqtt_client.publish(MQTT_TOPIC_HUM, humidity)  # Uncomment if using BME280
            
            # Pause for a while before the next reading
            utime.sleep(10)
    except Exception as e:
        print("An error occurred:", e)
        raise

# Run the main program
if __name__ == "__main__":
    main()
