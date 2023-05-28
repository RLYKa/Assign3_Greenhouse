import paho.mqtt.client as mqtt
import serial
import time
import ssl
import mysql.connector
import threading
import os
import subprocess

from picamera import PiCamera
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# MQTT
BROKER = "30879eac8d1b42ea9dd2feaf91890eb6.s2.eu.hivemq.cloud"
username = "user1"
password = "Password123"
TOPIC_LED_CONTROL = "nodes/ledControl"
TOPIC_THRESHOLD = "nodes/threshold"
TOPIC_STATUS = "nodes/status"
TOPIC_LDR = "nodes/ldr"
TOPIC_HOUR = "nodes/hour"
TOPIC_REQUEST_STATUS = "nodes/requestStatus"
TOPIC_REQUEST_LDR= "nodes/requestLDR"
TOPIC_REQUEST_HOUR= "nodes/requestHour"
TOPIC_STREAM= "nodes/streamControl"

camera = PiCamera(resolution=(1280, 720), framerate=24)

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
    client.subscribe(TOPIC_HOUR)
    client.subscribe(TOPIC_REQUEST_STATUS)
    client.subscribe(TOPIC_REQUEST_LDR)
    client.subscribe(TOPIC_REQUEST_HOUR)
    client.subscribe(TOPIC_STREAM)
    print("CONNACK received with code %s." % rc)

# MQTT Callbacks
def on_message(client, userdata, msg):
    global send_status
    print(msg.topic, msg.payload)
    if msg.topic == TOPIC_LED_CONTROL:
        # Handle LED control commands
        payload = msg.payload.decode()
        if payload.startswith("led_off"):
            led_num, duration = extract_led_num_and_duration(payload)
            turn_off_led(led_num, duration)
        elif payload.startswith("led_on"):
            led_num, duration = extract_led_num_and_duration(payload)
            turn_on_led_for_duration(led_num, duration)
    elif msg.topic == TOPIC_THRESHOLD:
        # Handle threshold updates
        payload = msg.payload.decode()
        parts = payload.split("_")
        if len(parts) == 2 and parts[0] == "setThreshold":
            ldr_index = int(parts[1])
            new_threshold = int(parts[2])
            set_threshold(ldr_index, new_threshold)
    elif msg.topic == TOPIC_REQUEST_STATUS:
        # Handle status requests
        if msg.payload.decode() == "getStatus":
            send_status = True
            get_status_from_arduino()
    elif msg.topic == TOPIC_REQUEST_LDR:
        # Handle LDR requests
        if msg.payload.decode() == "getLDR":
            send_ldr = True
            get_ldr_from_arduino()
    elif msg.topic == TOPIC_REQUEST_HOUR:
        # Handle hour requests
        if msg.payload.decode() == "getHour":
            query = """
                SELECT led_num, 
                    TIMESTAMPDIFF(HOUR, MIN_EVENTDATE, MAX_EVENTDATE) AS total_hours
                FROM (
                    SELECT led_num, 
                        MIN(eventDate) AS MIN_EVENTDATE, 
                        MAX(eventDate) AS MAX_EVENTDATE
                    FROM lightLog
                    WHERE eventType = 'on' AND DATE(eventDate) = CURDATE()
                    GROUP BY led_num
                ) AS subquery
            """
            cursor.execute(query)

            # Fetch the results
            hours = []
            results = cursor.fetchall()
            for row in results:
                total_hours = row[1]
                hours.append(str(total_hours))

            # Close the cursor and connection
            message = ','.join(hours)
            mqtt_client.publish(TOPIC_HOUR, message)
    elif msg.topic == TOPIC_STREAM:
        # Handle streaming control commands
        if msg.payload.decode() == "start_streaming":
            start_streaming()
            start_ffmpeg_stream()
        elif msg.payload.decode() == "stop_streaming":
            stop_streaming()


# Function to set the LDR threshold
def set_threshold(ldr_index, new_threshold):
    arduino_command = f"setThreshold_{ldr_index}_{new_threshold}\n"
    ser.write(arduino_command.encode())

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
    time.sleep(0.5)  # add delay
    ser.write(b"getStatus\n")

def get_ldr_from_arduino():
    ser.write(b"getLDR\n")

# Function for reading data from Arduino
def read_from_arduino():
    global send_status
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('latin-1').strip()
            elements = line.split(',')
            if 3 < len(elements) < 6 and send_ldr:  # this is a status update
                mqtt_client.publish(TOPIC_LDR, line)
                send_status = False
            elif len(elements) == 6:
                if send_status:  # this is a status response from Arduino
                    mqtt_client.publish(TOPIC_STATUS, line)
                    send_status = False
            time.sleep(1)

# Function to set the LDR threshold
def set_threshold(ldr_index, new_threshold):
    arduino_command = f"setThreshold_{ldr_index}_{new_threshold}\n"
    ser.write(arduino_command.encode())
    time.sleep(0.5)  # add delay


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

def extract_led_num_and_duration(payload):
    parts = payload.split("_")
    led_num = int(parts[2])
    duration = int(parts[3])
    return led_num, duration

def turn_off_led(led_num, duration):
    arduino_command = f"led_off_{led_num}_{duration}\n"
    ser.write(arduino_command.encode())
    time.sleep(1)

def turn_on_led_for_duration(led_num, duration):
    arduino_command = f"led_on_{led_num}_{duration}\n"
    ser.write(arduino_command.encode())
    time.sleep(1)

# Function to execute LED state insertion and event creation every 10 seconds
def execute_led_state_insertion():
    ser.write(b"getStatus\n")  # Request LED status from the serial
    line = ser.readline().decode('latin-1').strip()
    elements = line.split(',')
    if len(elements) == 6:
        event_date = time.strftime('%Y-%m-%d %H:%M:%S')
        for led_num, state in enumerate(elements[::2], start=1):
            event_type = "on" if state == '1' else "off"
            insert_led_event(led_num, event_type, event_date)
    threading.Timer(10, execute_led_state_insertion).start()

def start_streaming():
    camera.start_recording('my_stream.h264', format='h264')

def stop_streaming():
    camera.stop_recording()

def start_ffmpeg_stream():
    command = [
        'ffmpeg',
        '-re', 
        '-i', 
        'my_stream.h264', 
        '-vcodec', 
        'copy', 
        '-acodec', 
        'aac', 
        '-ab', 
        '128k', 
        '-g', 
        '50', 
        '-strict', 
        'experimental', 
        '-f', 
        'flv', 
        'rtmp://a.rtmp.youtube.com/live2/44bd-u5hu-qhar-jxc2-1mbp'
    ]
    process = subprocess.Popen(command)
    process.wait()  # Wait for the process to finish
    os.remove('my_stream.h264')  # Delete the file after streaming


# Start executing LED state insertion every 10 seconds
execute_led_state_insertion()

# Start the Arduino reading thread
arduino_thread = threading.Thread(target=read_from_arduino)
arduino_thread.start()

# Start the MQTT loop in the main thread
mqtt_client.loop_forever()