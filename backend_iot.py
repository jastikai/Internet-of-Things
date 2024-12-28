import paho.mqtt.client as mqtt
import requests
import json
import time

# Configuration
BROKER = "ip"
MQTT_PORT = 8883
MQTT_USER = "user"
MQTT_PASSWORD = "password"
MQTT_CERT = "path"

INFLUXDB_URL = "url"
INFLUXDB_TOKEN = "token"
INFLUXDB_ORG = "org"
INFLUXDB_BUCKET = "sensordata"

TOPIC_TEMP = "sensors/temperature"
TOPIC_PRESS = "sensors/pressure"
TOPIC_HUM = "sensors/humidity"  # Optional
TOPIC_CONTROL = "picow/control"     # Pico subscribes to control messages (e.g., LED ON/OFF)

# Global dictionary to store sensor data
sensor_data = {}
DEBUG = True  # Set to False to disable debug logs

# MQTT callback for handling messages
def on_message(client, userdata, msg):
    try:
        # Parse JSON payload
        payload = json.loads(msg.payload.decode().strip())
        
        # Extract values
        temperature = payload.get("temperature")
        pressure = payload.get("pressure")

        # Log received data
        print(f"Received data - Temperature: {temperature} °C, Pressure: {pressure} hPa")

        # Condition: If temperature > 25°C, send LED ON command
        if temperature is not None and temperature > 25.0:
            print("[INFO] Temperature exceeded 25°C. Sending 'LED ON' to Pico...")
            client.publish("picow/control", "LED ON")
        elif temperature is not None:
            print("[INFO] Temperature is safe. Sending 'LED OFF' to Pico...")
            client.publish("picow/control", "LED OFF")

        # Send data to InfluxDB
        if temperature is not None and pressure is not None:
            send_to_influxdb({"temperature": temperature, "pressure": pressure})
    
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse JSON payload: {msg.payload.decode()}, Error: {e}")
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
    

# Function to send data to InfluxDB
def send_to_influxdb(data):
    try:
        # Create the InfluxDB payload
        timestamp = int(time.time())
        influx_payload = f"weather,host=pico temperature={data['temperature']},pressure={data['pressure']} {timestamp}"

        headers = {
            "Authorization": f"Token {INFLUXDB_TOKEN}",
            "Content-Type": "text/plain; charset=utf-8",
        }
        response = requests.post(
            f"{INFLUXDB_URL}/api/v2/write?org={INFLUXDB_ORG}&bucket={INFLUXDB_BUCKET}&precision=s",
            data=influx_payload,
            headers=headers,
        )

        if response.status_code == 204:
            if DEBUG:
                print("[DEBUG] Data successfully written to InfluxDB.")
        else:
            print(f"[ERROR] Failed to write to InfluxDB: {response.text}")

    except Exception as e:
        print(f"[ERROR] Error sending data to InfluxDB: {e}")

# MQTT connection callback
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[INFO] Connected to MQTT Broker!")
        client.subscribe([(TOPIC_TEMP, 0), (TOPIC_PRESS, 0)])
        client.subscribe("sensors/data", 0);
    else:
        print(f"[ERROR] Failed to connect, return code {rc}")

# MQTT disconnect callback
def on_disconnect(client, userdata, rc):
    print(f"[WARNING] Disconnected from MQTT Broker, return code {rc}. Reconnecting...")
    time.sleep(5)
    client.reconnect()

# Connect to MQTT broker
def connect_to_mqtt():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.tls_set(ca_certs=MQTT_CERT)

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    try:
        client.connect(BROKER, MQTT_PORT)
    except Exception as e:
        print(f"[ERROR] Could not connect to MQTT broker: {e}")
        exit(1)

    return client

# Main execution
if __name__ == "__main__":
    mqtt_client = connect_to_mqtt()
    print("[INFO] Starting MQTT loop...")
    mqtt_client.loop_forever()