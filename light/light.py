from flask import Flask, render_template, request
import datetime
import paho.mqtt.client as mqtt
import mysql.connector

app = Flask(__name__)

# MQTT broker credentials
broker = "30879eac8d1b42ea9dd2feaf91890eb6.s2.eu.hivemq.cloud"
port = 8883
username = "user1"
password = "Password123"
topic_light = "nodes/light"
topic_threshold = "nodes/threshold"
topic_led = "nodes/led"

# Edge (Raspberry Pi) configuration
edge_host = "localhost"
edge_user = "pi1"
edge_password = "pi1"
edge_database = "light_db"

# Create MQTT client
mqtt_client = mqtt.Client(client_id="")
mqtt_client.username_pw_set(username, password)
mqtt_client.tls_set()

mqtt_client.connect(broker, port)


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


# Callback functions for MQTT
def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)
    mqtt_client.subscribe(topic_threshold + "/+")
    mqtt_client.subscribe(topic_led + "/+")

def on_publish(client, userdata, mid):
    print("mid: " + str(mid))

def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    message = str(msg.payload.decode("utf-8"))
    topic = str(msg.topic.decode("utf-8"))

    # Implement your logic based on the received MQTT messages
    if topic.startswith(topic_threshold):
        ldr_num = topic.split("/")[-1]
        handle_threshold(ldr_num, message)
    elif topic.startswith(topic_led):
        led_num = topic.split("/")[-1]
        action, duration = message.split(",")
        handle_led(led_num, action, duration)

def handle_threshold(ldr_num, threshold):
    # Update the threshold in the database
    try:
        cursor.execute("UPDATE ldrThreshold SET threshold = %s WHERE ldr_num = %s", (threshold, ldr_num))
        db_connection.commit()
        print("Threshold updated successfully.")
    except mysql.connector.Error as e:
        print(f"Error updating threshold: {e}")

def handle_ldr_event(led_num, event_type):
    # Store the event in the database
    try:
        cursor.execute("INSERT INTO lightLog (led_num, event_type, event_date) VALUES (?, ?, ?)",
                       (led_num, event_type, datetime.datetime.now()))
        db_connection.commit()
        print("Event logged successfully.")
    except mariadb.Error as e:
        print(f"Error logging event: {e}")

    # Publish the event to the MQTT topic
    mqtt_client.publish(topic, payload=f"Event: LED {led_num} {event_type}")

    # Convert event_type to the corresponding LED control action
    action = "off" if event_type == "OFF" else "on"
    duration = 5000  # Default duration of 5 seconds

    # Publish the LED control message to the MQTT topic
    payload = f"{action},{duration}"
    mqtt_client.publish(f"{topic_led}/{led_num}", payload=payload)


mqtt_client.on_connect = on_connect
mqtt_client.on_subscribe = on_subscribe
mqtt_client.on_message = on_message
mqtt_client.on_publish = on_publish


@app.route('/')
def index():
    return render_template('mqtt.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
