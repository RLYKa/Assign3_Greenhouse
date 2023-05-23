from flask import Flask, render_template, request, jsonify
import paho.mqtt.client as mqtt
import paho.mqtt.client as paho
import json

import mysql.connector

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
    #Gordon Part
    payload = msg.payload.decode("utf-8")
    topic = msg.topic

    if topic == "topic/th":
        data = json.loads(payload)
        cursor = mydb.cursor()
        sql = "INSERT INTO tempA (temperature, humidity) VALUES (%s, %s)"
        val = (data.temp, data.humd)
        cursor.execute(sql, val)
        mydb.commit()
    #until here

    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    message = str(msg.payload.decode("utf-8"))
    receiving_topic = str(msg.topic)
    if receiving_topic == "nodes/water" and message.startswith('{"thresLog":'):
        read_water_node_json(message)

        

mqtt_client.on_connect = on_connect
mqtt_client.on_subscribe = on_subscribe
mqtt_client.on_message = on_message
mqtt_client.on_publish = on_publish


@app.route('/')
def index():
    return render_template('index.html')

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

@app.route('/TempDataVisualization')
def TempDataVisualization():
    try:
        cursor = mydb.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tempA ORDER BY date_created DESC LIMIT 10")
        tempAs = cursor.fetchall()
    except my.sql.connector.Error as error:
        print("Failed to retrieve data from MySQL: {}".format(error))
        tempAs = []
        return jsonify({'tempA' : tempAs})
    return render_template('data_temp.html')

@app.route('/plot1')
def plot1():
    return render_template('plot1.html')

@app.route('/plot2')
def plot2():
    return render_template('plot2.html')

@app.route('/plot3')
def plot3():
    return render_template('plot3.html')


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
    app.run(host='0.0.0.0', port=8080)
