import paho.mqtt.client as mqtt
import serial
import time
import ssl
import mysql.connector
import threading

# MQTT
BROKER = "30879eac8d1b42ea9dd2feaf91890eb6.s2.eu.hivemq.cloud"
username = "user1"
password = "Password123"
TOPIC = "nodes/ledControl, nodes/threshold, nodes/status, nodes/ldr, nodes/requestStatus, nodes/requestLDR"
TOPIC_LED_CONTROL = "nodes/ledControl"
TOPIC_THRESHOLD = "nodes/threshold"
TOPIC_STATUS = "nodes/status"
TOPIC_LDR = "nodes/ldr"
TOPIC_REQUEST_STATUS = "nodes/requestStatus"
TOPIC_REQUEST_LDR= "nodes/requestLDR"

# Edge (Raspberry Pi) configuration
edge_host = "localhost"
edge_user = "pi1"
edge_password = "pi1"
edge_database = "light_db"

# Create MariaDB connection
try:
    db_connection = mysql.connector.connect(
        user=edge_user,
        password=edge_password,
        host=edge_host,
        database=edge_database
    )
    cursor = db_connection.cursor()
except mysql.connector.Error as e:
    print(f"Error connecting to MariaDB: {e}")
    exit(1)

# Serial
ser = serial.Serial('/dev/ttyUSB0', 9600)

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    print(f"Connected: {rc}")
    client.subscribe(TOPIC)
    print("CONNACK received with code %s." % rc)

def on_message(client, userdata, msg):
    print(msg.topic, msg.payload)
    if msg.topic == TOPIC_LED_CONTROL:
        ser.write(msg.payload)
    elif msg.topic == TOPIC_THRESHOLD:
        ser.write(msg.payload)
    elif msg.topic == TOPIC_REQUEST_STATUS:
        if msg.payload.decode() == "getStatus":
            send_status_update()
    elif msg.topic == TOPIC_REQUEST_LDR:
        if msg.payload.decode() == "getLDR":
            send_LDR_update()

# MQTT Setup
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(username, password)
mqtt_client.tls_set(ca_certs=None, certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED,
                            tls_version=ssl.PROTOCOL_TLS, ciphers=None)
mqtt_client.tls_insecure_set(False)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(BROKER, 8883, 60)

# Flags to control status publishing
send_status = False
send_ldr = False
last_db_update = 0  # Track the time of the last database update

# Function to send status update
def send_status_update():
    global send_status
    send_status = True

def send_LDR_update():
    global send_ldr
    send_ldr = True

# Function for reading LDR values and status
def read_ldr_status():
    global send_status, send_ldr, last_db_update
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            elements = line.split(',')
            if len(elements) > 5:  # this is a Status update
                if send_status:
                    mqtt_client.publish(TOPIC_STATUS, line)
                    send_status = False
                elif time.time() - last_db_update > 5:  # Insert into the database every 5 seconds
                    for i in range(3):
                        state = elements[i]
                        query = "INSERT INTO light_db (led_num, eventType) VALUES (%s, %s)"
                        cursor.execute(query, (i, 'on' if state == '1' else 'off'))
                        db_connection.commit()
                    last_db_update = time.time()
            elif 3 < len(elements) < 5:  # this is a LDR Value update
                if send_ldr:
                    mqtt_client.publish(TOPIC_LDR, line)
                    send_ldr = False
        time.sleep(1)

# Start the LDR reading thread
ldr_thread = threading.Thread(target=read_ldr_status)
ldr_thread.start()

# Start the MQTT loop in the main thread
mqtt_client.loop_forever()
