from flask import Flask, render_template, request
import paho.mqtt.client as mqtt
import paho.mqtt.client as paho
import json
import mysql.connector

# Assuming you have established a MySQL connection and have a cursor object
# mydb = mysql.connector.connect(...)
# cursor = mydb.cursor()

mydb = mysql.connector.connect(
    host="localhost",
    user="pi",
    password="pi",
    database="greenhouse_db"
)




app = Flask(__name__)

# MQTT broker credentials
broker = "30879eac8d1b42ea9dd2feaf91890eb6.s2.eu.hivemq.cloud"
port = 8883
username = "user1"
password = "Password123"
topic = "nodes/"

client = paho.Client(client_id="")
mqtt_client = mqtt.Client(client_id="")
mqtt_client.username_pw_set(username, password)
mqtt_client.tls_set(tls_version=paho.ssl.PROTOCOL_TLSv1_2)

mqtt_client.connect(broker, port)


# Callback functions
def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)


def on_publish(client, userdata, mid, properties=None):
    print("mid: " + str(mid))


def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))


def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    message = str(msg.payload.decode("utf-8"))
    receiving_topic = str(msg.topic)
    if receiving_topic == "nodes/water":
        
        # Load JSON data
        data = json.loads(message)
        
        # Define table names
        table_names = {
            "thresLog": "water_thres_log",
            "weatherLog": "weather_log",
            "pumpLog1": "pump_log1",
            "pumpLog2": "pump_log2",
            "pumpLog3": "pump_log3",
            "moistureLog1": "moisture_log1",
            "moistureLog2": "moisture_log2",
            "moistureLog3": "moisture_log3"
        }
        
        cursor = mydb.cursor()
        
        # Iterate over each key-value pair in the JSON data
        for table_name, table_data in data.items():
            if isinstance(table_data, dict):
                # For tables with dictionary data (pumpLog1, pumpLog2, pumpLog3)
                for date, value in table_data.items():
                    # Check if the date already exists in the table
                    query = f"SELECT COUNT(*) FROM {table_names[table_name]} WHERE date = %s"
                    cursor.execute(query, (date,))
                    count = cursor.fetchone()[0]
        
                    if count > 0:
                        # Date exists, update the value
                        query = f"UPDATE {table_names[table_name]} SET daily_ml = %s WHERE date = %s"
                        cursor.execute(query, (int(value)*4*20, date))
                    else:
                        # Date doesn't exist, insert a new row
                        query = f"INSERT INTO {table_names[table_name]} (daily_ml, date) VALUES (%s, %s)"
                        cursor.execute(query, (int(value)*4*20, date))
        
            elif isinstance(table_data, list):
                # For tables with list data (thresLog, weatherLog, moistureLog1, moistureLog2, moistureLog3)
                for row in table_data:
                    if table_name.startswith("moistureLog"):
                        # For moistureLog tables, insert a new row
                        query = f"INSERT INTO {table_names[table_name]} (moisture_level, timestamp) VALUES (%s, %s)"
                        cursor.execute(query, (row[0], row[1]))
                    elif table_name == "thresLog":
                        # For thresLog and weatherLog tables, update the values
                        query = f"UPDATE {table_names[table_name]} SET thres = %s WHERE thres_num = %s"
                        cursor.execute(query, (row[1], row[0]))
                    elif table_name == "weatherLog":
                        # For thresLog and weatherLog tables, update the values
                        query = f"UPDATE {table_names[table_name]} SET temperature = %s, humidity = %s, status = %s"
                        cursor.execute(query, (row[0], row[1], row[2]))
        
        # Commit the changes and close the cursor
        mydb.commit()
        cursor.close()


mqtt_client.on_connect = on_connect
mqtt_client.on_subscribe = on_subscribe
mqtt_client.on_message = on_message
mqtt_client.on_publish = on_publish


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/publish', methods=['POST'])
def publish_message():
    message = request.form['message']

    # Publish the message to the MQTT topic
    mqtt_client.publish(topic, payload=message)

    return "Message sent successfully!"


# def publish_data():
#     # Define your data publishing logic here
#     # For example:
#     # mqtt_client.publish(topic, payload="Data to be published")
#     pass


# Start the MQTT client loop in a separate thread
mqtt_client.loop_start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
