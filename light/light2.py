import paho.mqtt.client as mqtt
import serial
import time
import ssl

# MQTT
BROKER = "30879eac8d1b42ea9dd2feaf91890eb6.s2.eu.hivemq.cloud"
username = "user1"
password = "Password123"
TOPIC_LED_CONTROL = "ledControl"
TOPIC_LDR = "ldr"
TOPIC_THRESHOLD = "threshold"
TOPIC_STATUS = "status"

# Serial
ser = serial.Serial('/dev/ttyUSB0', 9600)

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    print(f"Connected: {rc}")
    client.subscribe(TOPIC_LED_CONTROL)
    client.subscribe(TOPIC_THRESHOLD)
    client.subscribe(TOPIC_STATUS)

def on_message(client, userdata, msg):
    print(msg.topic, msg.payload)
    if msg.topic == TOPIC_LED_CONTROL:
        ser.write(msg.payload)
    elif msg.topic == TOPIC_THRESHOLD:
        ser.write(msg.payload)
    elif msg.topic == TOPIC_STATUS:
        ser.write(b"getStatus\n")

# MQTT Setup
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(username, password)
mqtt_client.tls_set(ca_certs=None, certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED,
                            tls_version=ssl.PROTOCOL_TLS, ciphers=None)
mqtt_client.tls_insecure_set(False)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(BROKER, 8883, 60)

# Loop for reading LDR values and status
while True:
    if ser.in_waiting > 0:
        line = ser.readline().decode('utf-8').strip()
        if len(line.split(',')) > 3:  # this is a status update
            mqtt_client.publish(TOPIC_STATUS, line)
        else:  # this is an LDR update
            ldr_val = ','.join(line.split(','))
            mqtt_client.publish(TOPIC_LDR, ldr_val)
        time.sleep(1)

mqtt_client.loop_forever()
