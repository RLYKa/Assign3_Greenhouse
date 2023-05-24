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

# Flag to control status publishing
send_status = False
send_ldr = False

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
    client.subscribe(TOPIC_LED_CONTROL)
    client.subscribe(TOPIC_THRESHOLD)
    client.subscribe(TOPIC_STATUS)
    client.subscribe(TOPIC_LDR)
    client.subscribe(TOPIC_REQUEST_STATUS)
    client.subscribe(TOPIC_REQUEST_LDR)
    print("CONNACK received with code %s." % rc)

def on_message(client, userdata, msg):
    global send_status
    print(msg.topic, msg.payload)
    if msg.topic == TOPIC_LED_CONTROL:
        ser.write(msg.payload)
    elif msg.topic == TOPIC_THRESHOLD:
        ser.write(msg.payload)
    elif msg.topic == TOPIC_REQUEST_STATUS:
        if msg.payload.decode() == "getStatus":
            send_status = True
            get_status_from_arduino()
    elif msg.topic == TOPIC_REQUEST_LDR:
        if msg.payload.decode() == "getLDR":
            send_ldr = True
            get_ldr_from_arduino()

# MQTT Setup
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(username, password)
mqtt_client.tls_set(ca_certs=None, certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED,
                            tls_version=ssl.PROTOCOL_TLS, ciphers=None)
mqtt_client.tls_insecure_set(False)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(BROKER, 8883, 60)

def get_status_from_arduino():
    ser.write(b"getStatus\n")

def get_ldr_from_arduino():
    ser.write(b"getLDR\n")

# Function for reading data from Arduino
def read_from_arduino():
    global send_status
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            elements = line.split(',')
            if 3 < len(elements) < 6 and send_ldr:  # this is a status update
                mqtt_client.publish(TOPIC_LDR, line)
                send_status = False
            elif len(elements) == 6:
                if send_status:  # this is a status response from Arduino
                    mqtt_client.publish(TOPIC_STATUS, line)
                    send_status = False
                else:
                    led_states = [int(elements[0]), int(elements[2]), int(elements[4])]
                    event_date = time.strftime('%Y-%m-%d %H:%M:%S')
                    for led_num, state in enumerate(led_states, start=1):
                        event_type = "on" if state == 1 else "off"
                        insert_led_event(led_num, event_type, event_date)
            time.sleep(1)

# Function to insert LED event into the lightLog table
def insert_led_event(led_num, event_type, event_date):
    try:
        query = "INSERT INTO lightLog (led_num, eventType, eventDate) VALUES (%s, %s, %s)"
        values = (led_num, event_type, event_date)
        cursor.execute(query, values)
        db_connection.commit()
        print("LED event inserted into the lightLog table.")
    except mysql.connector.Error as e:
        print(f"Error inserting LED event: {e}")

# Function to execute LED state insertion and event creation every 10 seconds
def execute_led_state_insertion():
    ser.write(b"getStatus\n")  # Request LED status from the serial
    line = ser.readline().decode('utf-8').strip()
    elements = line.split(',')
    if len(elements) == 6:
        event_date = time.strftime('%Y-%m-%d %H:%M:%S')
        for led_num, state in enumerate(elements[::2], start=1):
            event_type = "on" if state == '1' else "off"
            insert_led_event(led_num, event_type, event_date)
    threading.Timer(10, execute_led_state_insertion).start()


# Start executing LED state insertion every 10 seconds
execute_led_state_insertion()

# Start the Arduino reading thread
arduino_thread = threading.Thread(target=read_from_arduino)
arduino_thread.start()

# Start the MQTT loop in the main thread
mqtt_client.loop_forever()