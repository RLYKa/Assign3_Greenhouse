from flask import Flask, render_template, request, jsonify, make_response
import paho.mqtt.client as mqtt
import paho.mqtt.client as paho
import json
import mysql.connector
import pytz
from datetime import datetime

import subprocess
import time
import threading


def read_water_node_json(message):
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
                #print(f"Inserting row: {row}")  # Debug print statement
                # For moistureLog tables, insert a new row
                query = f"INSERT IGNORE INTO {table_names[table_name]} (moisture_level, timestamp) VALUES (%s, %s)"
                cursor.execute(query, (row[0], row[1]))
            elif table_name == "thresLog":
                # For thresLog  tables, update the values
                query = f"UPDATE {table_names[table_name]} SET thres = %s WHERE thres_num = %s"
                cursor.execute(query, (row[1], row[0]))
            elif table_name == "weatherLog":
                # For  weatherLog tables, update the values
                query = f"UPDATE {table_names[table_name]} SET temperature = %s, humidity = %s, status = %s"
                cursor.execute(query, (row[0], row[1], row[2]))
  
  # Commit the changes and close the cursor
  mydb.commit()
  cursor.close()

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
topic = "nodes/#"

client = paho.Client(client_id="")
mqtt_client = mqtt.Client(client_id="")
mqtt_client.username_pw_set(username, password)
mqtt_client.tls_set(tls_version=paho.ssl.PROTOCOL_TLSv1_2)

mqtt_client.connect(broker, port)

TOPIC_LED_CONTROL = "nodes/ledControl"
TOPIC_THRESHOLD = "nodes/threshold"
TOPIC_STATUS = "nodes/status"
TOPIC_LDR = "nodes/ldr"
TOPIC_HOUR = "nodes/hour"
TOPIC_REQUEST_STATUS = "nodes/requestStatus"
TOPIC_REQUEST_LDR= "nodes/requestLDR"
TOPIC_REQUEST_HOUR= "nodes/requestHour"


# Callback functions
def on_connect(client, userdata, flags, rc, properties=None):
    mqtt_client.subscribe(topic,qos=1)
    print("CONNACK received with code %s." % rc)

    #Gordon part
    mqtt_client.subscribe("nodes/th")
    #until here


def on_publish(client, userdata, mid, properties=None):
    print("mid: " + str(mid))


def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))


def on_message(client, userdata, msg):
    # Gordon Part
    payload = msg.payload.decode("utf-8")
    topic = msg.topic

    if topic == "nodes/th":
        data = json.loads(payload)
        print(data)
        cursor = mydb.cursor()
        tableName = 'tempA'
        if data['plot'] == 'A':  
            tableName = 'tempA'
        elif data['plot'] == 'B': 
            tableName = 'tempB'
        elif data['plot'] == 'C': 
            tableName = 'tempC'  

        print(tableName)
        sql = "INSERT INTO " + tableName + " (temperature, humidity) VALUES (%s, %s)"
        val = (data['temp'], data['humd'])
        #val = json.dumps(val)
        cursor.execute(sql, val)
        print("Sql value: " + json.dumps(val))  
        mydb.commit()
    
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    message = str(msg.payload.decode("utf-8"))
    receiving_topic = str(msg.topic)
    
    if receiving_topic == "nodes/water" and message.startswith('{"thresLog":'):
        read_water_node_json(message)

    elif receiving_topic == TOPIC_STATUS:
        # Handle status message
        # Extract the data from the MQTT message
        status_data = message.split(',')
        led1_status = status_data[0]
        ldr1_threshold = status_data[1]
        led2_status = status_data[2]
        ldr2_threshold = status_data[3]
        led3_status = status_data[4]
        ldr3_threshold = status_data[5]

        # Get the current UTC timestamp
        utc_now = datetime.now(pytz.utc)

        # Convert UTC timestamp to GMT+8
        gmt8_now = utc_now.astimezone(pytz.timezone('Asia/Singapore'))

        # Insert data into node_status table
        query = "INSERT INTO node_status (timestamp, led1_status, ldr1_threshold, led2_status, ldr2_threshold, led3_status, ldr3_threshold) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        values = (gmt8_now, led1_status, ldr1_threshold, led2_status, ldr2_threshold, led3_status, ldr3_threshold)
        cursor = mydb.cursor()
        cursor.execute(query, values)
        mydb.commit()

    elif receiving_topic == TOPIC_HOUR:
        # Handle hour message
        # Extract the data from the MQTT message
        hour_data = message.split(',')
        led1_hour = hour_data[0]
        led2_hour = hour_data[1]
        led3_hour = hour_data[2]

        # Get the current UTC timestamp
        utc_now = datetime.now(pytz.utc)

        # Convert UTC timestamp to GMT+8
        gmt8_now = utc_now.astimezone(pytz.timezone('Asia/Singapore'))

        # Insert data into node_hour table
        query = "INSERT INTO node_hour (timestamp, led1_hour, led2_hour, led3_hour) VALUES (%s, %s, %s, %s)"
        values = (gmt8_now, led1_hour, led2_hour, led3_hour)
        cursor = mydb.cursor()
        cursor.execute(query, values)
        mydb.commit()     

mqtt_client.on_connect = on_connect
mqtt_client.on_subscribe = on_subscribe
mqtt_client.on_message = on_message
mqtt_client.on_publish = on_publish


@app.route('/')
def index():
    #Retrieve the current temperature, humidity, and weather status from the database
    cursor = mydb.cursor()
    query = "SELECT temperature, humidity, status FROM weather_log LIMIT 1"
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()

    if result:
        temperature, humidity, status = result
        # Format the temperature, humidity, and status as desired for the message
        message = f"Current Temperature: {temperature}°C, Humidity: {humidity}, Weather Status: {status}"
        # Check if the same message has been shown today
        # You can use a variable or database to store the last shown message date and compare it with the current date

        # Render the template with the message variable
        return render_template('index.html', weather=message)
    return render_template('index.html')

# Route to fetch the past 5 days of data from node_hour table
@app.route('/get_hour_data')
def get_hour_data():
    # Prepare the SQL query to fetch the data for the past 5 days
    query = "SELECT timestamp, led1_hour, led2_hour, led3_hour FROM node_hour WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 5 DAY)"

    cursor = mydb.cursor()
    cursor.execute(query)

    # Fetch all the data rows
    rows = cursor.fetchall()

    # Prepare the data for the chart
    labels = []
    values1 = []
    values2 = []
    values3 = []

    for row in rows:
        timestamp = row[0]
        led1_hour = row[1]
        led2_hour = row[2]
        led3_hour = row[3]

        # Extract the date from the timestamp and format it as desired
        date = timestamp.strftime("%Y-%m-%d")

        # Append the date to the labels
        labels.append(date)

        # Append the values to their respective lists
        values1.append(led1_hour)
        values2.append(led2_hour)
        values3.append(led3_hour)

    # Prepare the chart data as a dictionary
    chart_data = {
        'labels': labels,
        'values1': values1,
        'values2': values2,
        'values3': values3
    }

    # Convert the chart data to JSON and return as the response
    return jsonify(chart_data)


import os
import sys
import time

def restart_script():
    try:
        python = sys.executable
        os.execl(python, python, *sys.argv)
    except Exception as e:
        print("An error occurred while restarting the script:", str(e))
import subprocess

def restart_service():
    try:
        subprocess.run(['sudo', 'systemctl', 'restart', 'assign3.service'])
        print("Service restarted successfully.")
    except subprocess.CalledProcessError as e:
        print("An error occurred while restarting the service:", str(e))


@app.route('/get_status', methods=['GET'])
def get_status():
    cursor = mydb.cursor()

    mqtt_client.publish(TOPIC_REQUEST_STATUS, "getStatus")
    mqtt_client.publish(TOPIC_REQUEST_HOUR, "getHour")
    mqtt_client.publish('nodes/water', "refresh")

    # Fetch the latest data from node_status table
    query_status = "SELECT * FROM node_status ORDER BY id DESC LIMIT 1"
    cursor.execute(query_status)
    status_data = cursor.fetchone()

    # Fetch the latest data from node_hour table
    query_hour = "SELECT * FROM node_hour ORDER BY id DESC LIMIT 1"
    cursor.execute(query_hour)
    hour_data = cursor.fetchone()

    # Fetch the latest data from moisture_log1 table
    query_moisture1 = "SELECT moisture_level FROM moisture_log1 ORDER BY timestamp DESC LIMIT 1"
    cursor.execute(query_moisture1)
    moisture1_data = cursor.fetchone()

    # Fetch the latest data from moisture_log2 table
    query_moisture2 = "SELECT moisture_level FROM moisture_log2 ORDER BY timestamp DESC LIMIT 1"
    cursor.execute(query_moisture2)
    moisture2_data = cursor.fetchone()

    # Fetch the latest data from moisture_log3 table
    query_moisture3 = "SELECT moisture_level FROM moisture_log3 ORDER BY timestamp DESC LIMIT 1"
    cursor.execute(query_moisture3)
    moisture3_data = cursor.fetchone()

    # Prepare the response data
    if status_data and hour_data:
        response_data = f"{status_data[1]},{status_data[2]},{status_data[3]},{status_data[4]},{status_data[5]},{status_data[6]},{status_data[7]},{hour_data[1]},{hour_data[2]},{hour_data[3]}, {hour_data[4]}"
        response_data += f",{moisture1_data[0] if moisture1_data else 'N/A'},{moisture2_data[0] if moisture2_data else 'N/A'},{moisture3_data[0] if moisture3_data else 'N/A'}"
    else:
        # If no data found, send empty values
        response_data = "No data available"

    # Create the Flask response
    response = make_response(response_data, 200)

    # Set cache-control headers to prevent caching
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    time.sleep(3)
    restart_service()

    return response



@app.route('/set_threshold', methods=['POST'])
def set_threshold():
    data = request.json
    ldr_index = data['ldr_index']
    new_threshold = data['new_threshold']

    # Prepare the MQTT message
    command = f"T{ldr_index}_{new_threshold}"
    try:
        mqtt_client.publish(TOPIC_LDR, payload=command)
        return "Threshold message sent successfully"
    except Exception as e:
        return f"Failed to send threshold message: {str(e)}", 500


@app.route('/led', methods=['POST'])
def control_led():
    data = request.json
    led_num = data['led_num']
    duration = data['duration']
    if data['action'] == 'on':
        payload = f"led_on_{led_num}_{duration}"
    elif data['action'] == 'off':
        payload = f"led_off_{led_num}_{duration}"
    else:
        return "Invalid action", 400

    try:
        mqtt_client.publish(TOPIC_LED_CONTROL, payload)
        return "LED control message sent successfully"
    except Exception as e:
        return f"Failed to send LED control message: {str(e)}", 500

@app.route('/LightDataVisualization')
def LightDataVisualization():
    return render_template('data_light.html')


# Endpoint for fetching plot 1 moisture data
@app.route('/plot1_moisture_data')
def plot1_moisture_data():
    
    cursor = mydb.cursor()

    # Fetch data for plot 1 from moisture_log1 table
    query = "SELECT moisture_level, timestamp FROM moisture_log1 ORDER BY timestamp DESC LIMIT 5"
    cursor.execute(query)
    moisture_data = cursor.fetchall()

    # Fetch threshold value from thres_log table
    query = "SELECT thres FROM water_thres_log WHERE thres_num = '1'"
    cursor.execute(query)
    threshold = cursor.fetchone()[0]
    # Calculate moisture level as a percentage
    percentage_data = []
    for data in moisture_data:
        moisture_level = data[0]
        percentage = round(((moisture_level - 1024)/-1024),2) * 100
        percentage_data.append(percentage)
    # Close the database connection
    cursor.close()

    # Prepare the chart data
    chart_data = {
        'labels': [data[1] for data in reversed(moisture_data)],
        'datasets': [
            {'label': 'Threshold', 'data': [threshold] * len(moisture_data)},
            {'label': 'Moisture Level', 'data': percentage_data}
        ]
    }

    return jsonify(chart_data)

# Endpoint for fetching plot 2 moisture data
@app.route('/plot2_moisture_data')
def plot2_moisture_data():
    cursor = mydb.cursor()

    # Fetch data for plot 2 from moisture_log2 table
    query = "SELECT moisture_level, timestamp FROM moisture_log2 ORDER BY timestamp DESC LIMIT 5"
    cursor.execute(query)
    moisture_data = cursor.fetchall()

    # Fetch threshold value from thres_log table
    query = "SELECT thres FROM water_thres_log WHERE thres_num = '2'"
    cursor.execute(query)
    threshold = cursor.fetchone()[0]
 # Calculate moisture level as a percentage
    percentage_data = []
    for data in moisture_data:
        moisture_level = data[0]
        percentage = round(((moisture_level - 1024)/-1024),2) * 100
        percentage_data.append(percentage)
    # Close the database connection
    cursor.close()

    # Prepare the chart data
    chart_data = {
        'labels': [data[1] for data in reversed(moisture_data)],
        'datasets': [
            {'label': 'Threshold', 'data': [threshold] * len(moisture_data)},
            {'label': 'Moisture Level', 'data': percentage_data}
        ]
    }

    return jsonify(chart_data)


# Endpoint for fetching plot 3 moisture data
@app.route('/plot3_moisture_data')
def plot3_moisture_data():
    cursor = mydb.cursor()

    # Fetch data for plot 3 from moisture_log3 table
    query = "SELECT moisture_level, timestamp FROM moisture_log3 ORDER BY timestamp DESC LIMIT 5"
    cursor.execute(query)
    moisture_data = cursor.fetchall()

    # Fetch threshold value from thres_log table
    query = "SELECT thres FROM water_thres_log WHERE thres_num = '3'"
    cursor.execute(query)
    threshold = cursor.fetchone()[0]
 # Calculate moisture level as a percentage
    percentage_data = []
    for data in moisture_data:
        moisture_level = data[0]
        percentage = round(((moisture_level - 1024)/-1024),2) * 100
        percentage_data.append(percentage)
    # Close the database connection
    cursor.close()

    # Prepare the chart data
    chart_data = {
        'labels': [data[1] for data in reversed(moisture_data)],
        'datasets': [
            {'label': 'Threshold', 'data': [threshold] * len(moisture_data)},
            {'label': 'Moisture Level', 'data': percentage_data}
        ]
    }

    return jsonify(chart_data)


@app.route('/plot1_pump_data')
def plot1_pump_data():
    cursor = mydb.cursor()
    query = "SELECT date, daily_ml FROM pump_log1 ORDER BY date DESC LIMIT 5"
    cursor.execute(query)
    rows = cursor.fetchall()

    data = {
        'labels': [],
        'datasets': [{
            'label': 'Daily ML',
            'data': [],
            'backgroundColor': 'rgba(75, 192, 192, 0.6)'
        }]
    }

    for row in reversed(rows):
        date, daily_ml = row
        data['labels'].append(date)
        data['datasets'][0]['data'].append(daily_ml)

    return jsonify(data)


@app.route('/plot2_pump_data')
def plot2_pump_data():
    cursor = mydb.cursor()
    query = "SELECT date, daily_ml FROM pump_log2 ORDER BY date DESC LIMIT 5"
    cursor.execute(query)
    rows = cursor.fetchall()

    data = {
        'labels': [],
        'datasets': [{
            'label': 'Daily ML',
            'data': [],
            'backgroundColor': 'rgba(75, 192, 192, 0.6)'
        }]
    }

    for row in reversed(rows):
        date, daily_ml = row
        data['labels'].append(date)
        data['datasets'][0]['data'].append(daily_ml)

    return jsonify(data)


@app.route('/plot3_pump_data')
def plot3_pump_data():
    cursor = mydb.cursor()
    query = "SELECT date, daily_ml FROM pump_log3 ORDER BY date DESC LIMIT 5"
    cursor.execute(query)
    rows = cursor.fetchall()

    data = {
        'labels': [],
        'datasets': [{
            'label': 'Daily ML',
            'data': [],
            'backgroundColor': 'rgba(75, 192, 192, 0.6)'
        }]
    }

    for row in reversed(rows):
        date, daily_ml = row
        data['labels'].append(date)
        data['datasets'][0]['data'].append(daily_ml)

    return jsonify(data)

@app.route('/WaterDataVisualization')
def WaterDataVisualization():
    return render_template('data_water.html')


#Gordon Part
@app.route('/TempDataVisualization')
def gay():
  return render_template('data_temp.html')
    
# Plot 1 data visualization
@app.route('/temp_data1')
def getTemp_Data():
    try:
        cursor = mydb.cursor()
        query = "SELECT * FROM tempA ORDER BY date_created DESC LIMIT 10"
        cursor.execute(query)
        tempA = cursor.fetchall()
    except mysql.connector.Error as error:
        print("Failed to retrieve data from MySQL: {}".format(error))
        tempA = []
    return jsonify({'tempA' : tempA})

# Plot 2 data visualization
@app.route('/temp_data2')
def getTemp_Data2():
    try:
        cursor = mydb.cursor()
        query = "SELECT * FROM tempB ORDER BY date_created DESC LIMIT 10"
        cursor.execute(query)
        tempB = cursor.fetchall()
    except mysql.connector.Error as error:
        print("Failed to retrieve data from MySQL: {}".format(error))
        tempB = []
    return jsonify({'tempB' : tempB})

# data table in plot 1
@app.route('/temp_data_plot1')
def getTemp_Data_plot1():
    try:
        cursor = mydb.cursor()
        query = "SELECT * FROM tempA ORDER BY date_created DESC LIMIT 5"
        cursor.execute(query)
        tempA = cursor.fetchall()
    except mysql.connector.Error as error:
        print("Failed to retrieve data from MySQL: {}".format(error))
        tempA = []
    return jsonify({'tempA' : tempA})

# data table in plot 2
@app.route('/temp_data_plot2')
def getTemp_Data_plot2():
    try:
        cursor = mydb.cursor()
        query = "SELECT * FROM tempB ORDER BY date_created DESC LIMIT 5"
        cursor.execute(query)
        tempB = cursor.fetchall()
    except mysql.connector.Error as error:
        print("Failed to retrieve data from MySQL: {}".format(error))
        tempB = []
    return jsonify({'tempB' : tempB})


# data table in plot 1
@app.route('/Aircontrol', methods=['POST'])
def Aircontrol():
    data = request.form
    mqtt_client.publish('nodes/th/set', payload=json.dumps({
        'status': data.get('direction'), 
        'speed': data.get('speed')
    }))
    time.sleep(1)
    return 'OK', 200

@app.route('/Aircontrol2', methods=['POST'])
def Aircontrol2():
    data = request.form
    mqtt_client.publish('nodes/th/set2', payload=json.dumps({
        'status': data.get('direction'), 
        'speed': data.get('speed')
    }))
    time.sleep(1)
    return 'OK', 200

# update the checklist in plot 1
@app.route('/update_checklist', methods=['POST'])
def update_checklist():
    new_value = float(request.form.get('new_value'))
    cursor = mydb.cursor()
    cursor.execute("UPDATE tempA SET checklist = %s", (new_value,))
    mydb.commit()
    cursor.close()
    message = "Checklist updated successfully"
    #return "Checklist updated successfully"
    return render_template('plot1.html', message=message)

# update the checklist in plot 2
@app.route('/update_checklist2', methods=['POST'])
def update_checklist2():
    new_value = float(request.form.get('new_value'))
    cursor = mydb.cursor()
    cursor.execute("UPDATE tempB SET checklist = %s", (new_value,))
    mydb.commit()
    cursor.close()
    message = "Checklist updated successfully"
    #return "Checklist updated successfully"
    return render_template('plot2.html', message=message)

# inset data in the plot 1
@app.route('/insert-data')
def insert_data():
    status = 'success'
    try:
        data = request.args['plot']
        mqtt_client.publish('nodes/th/get', payload=data)

        # cursor = mydb.cursor()
        # query = "INSERT INTO tempA (temperature, humidity) VALUES (%s, %s)"
        # cursor.execute(query)
        status = 'success'
    except mysql.connector.Error as error:
        print("Failed to retrieve data from MySQL: {}".format(error))
        status = 'error'

    return jsonify({'status' : status})

@app.route('/data-visualization')
def datavisualization():
    cursor = mydb.cursor()
    query = "SELECT temperature, humidity, date_created FROM tempA ORDER BY date_created DESC LIMIT 10"
    cursor.execute(query)
    tempAs = cursor.fetchall()

    data = {
        'labels': [],
        'datasets': [{
            'label': 'Temperature',
            'data': [],
            'backgroundColor': 'rgba(75, 192, 192, 0.6)',
        }, {
            'label': 'Humidity',
            'data': [],
            'backgroundColor': 'rgba(75, 192, 192, 0.6)',
        }]
    }

    for row in reversed(tempAs):
        temperature, humidity, date_created = row
        data['labels'].append(date_created)
        data['datasets'][0]['data'].append(temperature)
        data['datasets'][1]['data'].append(humidity)
    
    return jsonify(data)
#Gordon part until here



# Route for rendering the plot1 page
"""
@app.route('/plot1')
def plot1():
    try:
        cursor = mydb.cursor()
        query = "SELECT moisture_level FROM moisture_log1 ORDER BY timestamp DESC LIMIT 1"
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            moisture_level = result[0]
        cursor.close()
    
        # Apply a formula to the moisture level
        moisture_level = (moisture_level - 1024) / -1024 * 100
        print(moisture_level)
    
        cursor = mydb.cursor()
        query = "SELECT thres FROM water_thres_log WHERE thres_num = '1' LIMIT 1"
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            moisture_threshold = result[0]
        cursor.close()
    
        moisture_threshold = (moisture_threshold - 1024) / -1024 * 100
        print(moisture_threshold)
    
    except Exception as e:
        print("An error occurred:", str(e))

    return render_template('plot1.html', moisture_level=moisture_level, moisture_threshold=moisture_threshold)
"""
# Route for rendering the plot1 page
@app.route('/plot1')
def plot1():
    try:
        cursor = mydb.cursor()
        query = "SELECT moisture_level FROM moisture_log1 ORDER BY timestamp DESC LIMIT 1"
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            moisture_level = result[0]
        cursor.close()
    
        # Apply a formula to the moisture level
        moisture_level = (moisture_level - 1024) / -1024 * 100
        print(moisture_level)
    
        cursor = mydb.cursor()
        query = "SELECT thres FROM water_thres_log WHERE thres_num = '1' LIMIT 1"
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            moisture_threshold = result[0]
        cursor.close()
    
        moisture_threshold = (moisture_threshold - 1024) / -1024 * 100
        print(moisture_threshold)
    
    except Exception as e:
        print("An error occurred:", str(e))

    return render_template('plot1.html', moisture_level=moisture_level, moisture_threshold=moisture_threshold)

# Route for fetching the latest data for plot1
@app.route('/get_latest_plot1_data', methods=['GET'])
def get_latest_plot1_data():
    try:
        cursor = mydb.cursor()
        query = "SELECT moisture_level FROM moisture_log1 ORDER BY timestamp DESC LIMIT 1"
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            moisture_level = result[0]
        cursor.close()

        # Apply a formula to the moisture level
        moisture_level = (moisture_level - 1024) / -1024 * 100

        cursor = mydb.cursor()
        query = "SELECT thres FROM water_thres_log WHERE thres_num = '1' LIMIT 1"
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            moisture_threshold = result[0]
        cursor.close()

        moisture_threshold = (moisture_threshold - 1024) / -1024 * 100

        return jsonify({'moisture_level': moisture_level, 'moisture_threshold': moisture_threshold})
    
    except Exception as e:
        print("An error occurred:", str(e))
        return jsonify({'error': 'An error occurred'})



    
@app.route("/<action>", methods=['GET', 'POST']) 
def action(action):
    if request.method == 'GET':
        print(action)
        if action == 'PumpTrigger = 1' : 
            mqtt_client.publish("nodes/water", payload=action)
          
        if action == 'Pump1_Pause = 1' : 
            mqtt_client.publish("nodes/water", payload=action)
           
        if action == 'Pump1_Pause = 0' : 
            mqtt_client.publish("nodes/water", payload=action)
          
        if action.startswith('thres1 = '):
            percentage = action.replace('thres1 =', '')
            percentage = int(percentage)
            new_thres = round((100.0 - percentage) / 100.0 * 1024.0)
            action = (('thres1 = ' + str(new_thres)))
            mqtt_client.publish("nodes/water", payload=action)

        if action == 'PumpTrigger = 2' : 
            mqtt_client.publish("nodes/water", payload=action)
          
        if action == 'Pump2_Pause = 1' : 
            mqtt_client.publish("nodes/water", payload=action)
           
        if action == 'Pump2_Pause = 0' : 
            mqtt_client.publish("nodes/water", payload=action)
          
        if action.startswith('thres2 = '):
            percentage = action.replace('thres2 =', '')
            percentage = int(percentage)
            new_thres = round((100.0 - percentage) / 100.0 * 1024.0)
            action = (('thres2 = ' + str(new_thres)))
            mqtt_client.publish("nodes/water", payload=action)

        if action == 'PumpTrigger = 3' : 
            mqtt_client.publish("nodes/water", payload=action)
          
        if action == 'Pump3_Pause = 1' : 
            mqtt_client.publish("nodes/water", payload=action)
           
        if action == 'Pump3_Pause = 0' : 
            mqtt_client.publish("nodes/water", payload=action)
          
        if action.startswith('thres3 = '):
            percentage = action.replace('thres3 =', '')
            percentage = int(percentage)
            new_thres = round((100.0 - percentage) / 100.0 * 1024.0)
            action = (('thres3 = ' + str(new_thres)))
            mqtt_client.publish("nodes/water", payload=action)
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "message": "Invalid method"})
"""
# Route for processing pump actions
@app.route('/pump_action', methods=['POST'])
def pump_action():
    action = request.form['action']
    # Perform necessary actions based on the received action parameter
    
    # Placeholder response, replace with actual response data
    response_data = {'status': 'success', 'message': 'Action successful'}
    
    return jsonify(response_data)

# Route for processing setting new pump threshold
@app.route('/set_threshold', methods=['POST'])
def set_threshold():
    new_threshold = request.form['new_threshold']
    # Perform necessary actions to set the new threshold
    
    # Placeholder response, replace with actual response data
    response_data = {'status': 'success', 'message': 'Threshold set successfully'}
    
    return jsonify(response_data) 
"""
@app.route('/plot2')
def plot2():
    try:
        cursor = mydb.cursor()
        query = "SELECT moisture_level FROM moisture_log2 ORDER BY timestamp DESC LIMIT 1"
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            moisture_level = result[0]
        cursor.close()
    
        # Apply a formula to the moisture level
        moisture_level = (moisture_level - 1024) / -1024 * 100
        print(moisture_level)
    
        cursor = mydb.cursor()
        query = "SELECT thres FROM water_thres_log WHERE thres_num = '2' LIMIT 1"
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            moisture_threshold = result[0]
        cursor.close()
    
        moisture_threshold = (moisture_threshold - 1024) / -1024 * 100
        print(moisture_threshold)
    
    except Exception as e:
        print("An error occurred:", str(e))

    return render_template('plot2.html', moisture_level=moisture_level, moisture_threshold=moisture_threshold)

@app.route('/plot3')
def plot3():
    try:
        cursor = mydb.cursor()
        query = "SELECT moisture_level FROM moisture_log3 ORDER BY timestamp DESC LIMIT 1"
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            moisture_level = result[0]
        cursor.close()
    
        # Apply a formula to the moisture level
        moisture_level = (moisture_level - 1024) / -1024 * 100
        print(moisture_level)
    
        cursor = mydb.cursor()
        query = "SELECT thres FROM water_thres_log WHERE thres_num = '3' LIMIT 1"
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            moisture_threshold = result[0]
        cursor.close()
    
        moisture_threshold = (moisture_threshold - 1024) / -1024 * 100
        print(moisture_threshold)
    
    except Exception as e:
        print("An error occurred:", str(e))

    return render_template('plot3.html', moisture_level=moisture_level, moisture_threshold=moisture_threshold)


@app.route('/publish', methods=['POST'])
def publish_message():
    message = request.form['message']

    # Publish the message to the MQTT topic
    mqtt_client.publish(topic, payload=message)

    return "Message sent successfully!"
#json_data = 
'''
{
    "thresLog": [["1", "26.7"], ["2", "26.7"], ["3", "26.7"]],
    "weatherLog": [["31.57", "71%", "Clouds"]],
    "pumpLog1": {"2023-05-19": 48, "2023-05-20": 33},
    "pumpLog2": {"2023-05-19": 2},
    "pumpLog3": {"2023-05-19": 1},
    "moistureLog1": [[1006, "2023-05-18T14:39:13"], [1009, "2023-05-18T14:39:19"], [1009, "2023-05-18T14:39:25"], [1009, "2023-05-18T14:39:55"], [1009, "2023-05-18T14:40:01"]],
    "moistureLog2": [[383, "2023-05-18T14:41:01"], [383, "2023-05-18T14:41:07"], [384, "2023-05-18T14:41:13"], [383, "2023-05-18T14:41:19"], [383, "2023-05-18T14:41:25"]],
    "moistureLog3": [[339, "2023-05-18T14:41:02"], [339, "2023-05-18T14:41:07"], [338, "2023-05-18T14:41:13"], [337, "2023-05-18T14:41:19"], [337, "2023-05-18T14:41:25"]]
}
'''


#read_water_node_json(json_data)

# def publish_data():
#     # Define your data publishing logic here
#     # For example:
#     # mqtt_client.publish(topic, payload="Data to be published")
#     pass


# Start the MQTT client loop in a separate thread


if __name__ == '__main__':
    mqtt_client.loop_forever()    
    app.run(host='0.0.0.0',debug=True, port=8080)
