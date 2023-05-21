
from flask import Flask, render_template,jsonify, request
import serial
import threading

import mysql.connector
import pytz
import datetime
import json
import requests
from pyowm import OWM
import time
import paho.mqtt.client as paho
from paho import mqtt
from decimal import Decimal


# Create a Flask app
app = Flask(__name__)

# Set up the serial port
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=None)

# Set up the MySQL database
mydb = mysql.connector.connect(
    host="localhost",
    user="pi",
    password="pi",
    database="water_db2"
)

cursor = mydb.cursor()
cursor.execute("UPDATE thresLog SET thres = '26.7'")
mydb.commit()
cursor.close()

# Set the timezone to UTC+8
timezone = pytz.timezone("Asia/Kuala_Lumpur")

# Define a function to read data from the serial port
def read_from_port():
    try:
        while True:
            while (ser.in_waiting == 0):
                pass   
            line = ser.readline()
            if not line:
                x=1
                #pass
            else:
                y = ""
                try:
                    y = line.decode("utf-8").strip()
                    #print(y)
                except UnicodeDecodeError as e:
                    print("Error decoding UTF-8:", e)
                # Get the current timestamp in UTC
                timestamp = time.time()

                # Convert the UTC timestamp to the Malaysia timezone
                malaysia_timezone = pytz.timezone('Asia/Kuala_Lumpur')
                utc_datetime = datetime.datetime.utcfromtimestamp(timestamp)
                malaysia_datetime = pytz.utc.localize(utc_datetime).astimezone(malaysia_timezone)

                # Format the Malaysia datetime as a string
                formatted_date = malaysia_datetime.strftime("%Y-%m-%d %H:%M:%S")
                if y != "":     
                    print(y)
                    if y.startswith("Moisture 1: "):
                        substring = "Moisture 1: "
                        y = y.replace(substring, "")
                        cursor = mydb.cursor()
                        cursor.execute("INSERT INTO moistureLog1 VALUES (%s, %s)", (y, formatted_date,))
                        mydb.commit()
                        cursor.close()
                    elif y.startswith("Moisture 2: "):
                        substring = "Moisture 2: "
                        y = y.replace(substring, "")
                        cursor = mydb.cursor()
                        cursor.execute("INSERT INTO moistureLog2 VALUES (%s, %s)", (y, formatted_date,))
                        mydb.commit()
                        cursor.close()
                    elif y.startswith("Moisture 3: "):
                        substring = "Moisture 3: "
                        y = y.replace(substring, "")
                        cursor = mydb.cursor()
                        cursor.execute("INSERT INTO moistureLog3 VALUES (%s, %s)", (y, formatted_date,))
                        mydb.commit()
                        cursor.close()
                    elif y == "Pump 1 Activated":
                        cursor = mydb.cursor()
                        cursor.execute("INSERT INTO pumpLog1 VALUES (%s)", (formatted_date,))
                        mydb.commit()
                        cursor.close()
                    elif y == "Pump 2 Activated":
                        cursor = mydb.cursor()
                        cursor.execute("INSERT INTO pumpLog2 VALUES (%s)", (formatted_date,))
                        mydb.commit()
                        cursor.close()
                    elif y == "Pump 3 Activated":
                        cursor = mydb.cursor()
                        cursor.execute("INSERT INTO pumpLog3 VALUES (%s)", (formatted_date,))
                        mydb.commit()
                        cursor.close()
                    elif y.startswith("Latitude: "):
                        substring = "Latitude: "
                        y = y.replace(substring, "")
                        y  = float(y)
                        cursor = mydb.cursor()
                        cursor.execute("UPDATE coorLog SET latitude = (%s)", (y,))
                        mydb.commit()
                        cursor.close()
                    elif y.startswith("Longitude: "):
                        substring = "Longitude: "
                        y = y.replace(substring, "")
                        y  = float(y)
                        cursor = mydb.cursor()
                        cursor.execute("UPDATE coorLog SET longitude = (%s)", (y,))
                        mydb.commit()
                        cursor.close()
                                          
                   

                    
                    '''
                    elif y == "Alarm Activated":
                        cursor = mydb.cursor()
                        cursor.execute("INSERT INTO alarmLog (timestamp) VALUES (%s)", (formatted_date,))
                        mydb.commit()
                        cursor.close()
                    elif y == "Button Pressed":
                        pass  
                    else:
                        if (timestamp - last_save_timestamp >= 3):
                            cursor = mydb.cursor()
                            cursor.execute("INSERT INTO moistureLog VALUES (%s, %s)", (y, formatted_date,))
                            mydb.commit()
                            cursor.close()
                            last_save_timestamp = timestamp
                            '''
    except Exception as e:
        print("Error:")
        print(e)
        pass
#thread = threading.Thread(target=read_from_port)
#thread.start()



def get_weather_data():
     # Create a cursor object
     
    cursor = mydb.cursor()

    # Execute the query to fetch latitude and longitude
    query = "SELECT latitude, longitude FROM coorLog LIMIT 1"
    cursor.execute(query)

    # Fetch the result
    result = cursor.fetchone()

    # Check if a row is returned
    if result:
        latitude, longitude = result
    else:
        print("No data found in the table.")

    # Close the cursor and database connection
    cursor.close()

    # Initialize the OpenWeatherMap API client
    owm = OWM('b4f5848cd7b82ea9d9105cbca8d54baf')



    # Create a weather manager object
    mgr = owm.weather_manager()

    # Get the weather at the specified location
    observation = mgr.weather_at_coords(latitude, longitude)

    # Extract the weather details
    weather = observation.weather
    temperature = weather.temperature('celsius')

    # Print the weather information
    #print("Temperature:", temperature['temp'], "°C")
    #print("Humidity:", weather.humidity, "%")
    #print("Status:", weather.status)
    temp = str(temperature['temp'])
    humid = str(weather.humidity) + "%"
    status = weather.status

    cursor = mydb.cursor()
    cursor.execute("UPDATE weatherLog SET temperature = %s, humidity = %s, status = %s", (temp, humid, status))
    mydb.commit()

    cursor.close()


def publish_data():
    get_weather_data()
    # Custom JSON encoder to handle Decimal and datetime objects
    class CustomJSONEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, datetime.datetime):
                return obj.isoformat()
            return super().default(obj)

    # Define the tables and their corresponding criteria
    tables = {
        'thresLog': {'type': 'single_row'},
        'weatherLog': {'type': 'single_row'},
        'pumpLog1': {'type': 'date_range', 'column': 'timestamp'},
        'pumpLog2': {'type': 'date_range', 'column': 'timestamp'},
        'pumpLog3': {'type': 'date_range', 'column': 'timestamp'},
        'moistureLog1': {'type': 'limit', 'limit': 5},
        'moistureLog2': {'type': 'limit', 'limit': 5},
        'moistureLog3': {'type': 'limit', 'limit': 5},
        # Add more tables with their criteria here
    }

    # Initialize an empty dictionary to store the data
    data = {}

    # Iterate over the tables dictionary
    for table, criteria in tables.items():
    
        cursor = mydb.cursor()
        # Retrieve data based on the criteria type
        if criteria['type'] == 'single_row':
            # Query the table for the only row of data
            query = f"SELECT * FROM {table}"
            cursor.execute(query)
            table_data = cursor.fetchall()
            mydb.commit()
            cursor.close()

        elif criteria['type'] == 'date_range':
            # Calculate the datetime five days ago
            five_days_ago = datetime.datetime.now() - datetime.timedelta(days=5)
            formatted_date = five_days_ago.strftime('%Y-%m-%d')

            # Query the table to get the total number of triggers per 5-day range
            query = f"SELECT DATE({criteria['column']}) AS day, COUNT(*) AS trigger_count FROM {table} WHERE {criteria['column']} >= %s GROUP BY day"
            cursor.execute(query, (formatted_date,))
            results = cursor.fetchall()
            mydb.commit()
            cursor.close()
            table_data = {}
            for row in results:
                day = row[0].strftime('%Y-%m-%d')
                trigger_count = row[1]
                table_data[day] = trigger_count

        elif criteria['type'] == 'limit':
            # Query the table for the first N rows
            query = f"SELECT * FROM {table} LIMIT {criteria['limit']}"
            cursor.execute(query)
            table_data = cursor.fetchall()
            mydb.commit()
            cursor.close()
        if not table_data:
            table_data = []
        # Store the data in the dictionary
        data[table] = table_data

    # Convert the data dictionary to JSON
    json_data = json.dumps(data, cls=CustomJSONEncoder)
    print(json_data)
    # Publish the JSON message via MQTT
    client.publish("nodes/water", json_data, qos=1)





# setting callbacks for different events to see if it works, print the message etc.
def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)

# with this callback you can see if your publish was successful
def on_publish(client, userdata, mid, properties=None):
    print("mid: " + str(mid))

# print which topic was subscribed to
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

# print message, useful for checking if it was successful
def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    message = str(msg.payload.decode("utf-8"))
    topic = str(msg.topic.decode("utf-8"))
    if (message == "refresh" and topic == "nodes/water"):
        publish_data()
        

# using MQTT version 5 here, for 3.1.1: MQTTv311, 3.1: MQTTv31
# userdata is user defined data of any type, updated by user_data_set()
# client_id is the given name of the client
client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
client.on_connect = on_connect

# enable TLS for secure connection
client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
# set username and passwordnodes
client.username_pw_set("user1", "Password123")
# connect to HiveMQ Cloud on port 8883 (default for MQTT)
client.connect("30879eac8d1b42ea9dd2feaf91890eb6.s2.eu.hivemq.cloud", 8883)

# setting callbacks, use separate functions like above for better visibility
client.on_subscribe = on_subscribe
client.on_message = on_message
client.on_publish = on_publish

# subscribe to all topics of encyclopedia by using the wildcard "#"
client.subscribe("nodes/water", qos=1)
publish_data()

# loop_forever for simplicity, here you need to stop the loop manually
# you can also use loop_start and loop_stop
client.loop_forever()



# read_from_port()

'''             
# Start a new thread to read data from the serial port
thread = threading.Thread(target=read_from_port)
thread.start()

@app.route("/<action>", methods=['GET', 'POST']) 
def action(action):
    if request.method == 'GET':
        print(action)
        x = ''
        if action == 'PauseSprinkler' : 
            ser.write(b"PauseSprinkler = 1\n")
            x = "Sprinkler|Paused"
        if action == 'ResumeSprinkler' : 
            ser.write(b"PauseSprinkler = 0\n")
            x = "Sprinkler|Resume"
        if action == 'PauseAlarm' : 
            ser.write(b"PauseAlarm = 1\n")
            x = "Alarm|Paused"
        if action == 'ResumeAlarm' : 
            ser.write(b"PauseAlarm = 0\n")
            x = "Alarm|Resumed"
        if action == 'StartSprinkling' : 
            ser.write(b"StartSprinkling = 1\n")
            x = "Sprinkler|Started Manually"
        if action == 'BuzzerSet' : 
            ser.write(b"BuzzerSet = 1\n")
            x = "Alarm|Started Manually"
        if action.startswith('NewThres'):
            percentage = action.replace('NewThres=', '')
            
            cursor = mydb.cursor()
            cursor.execute("UPDATE thresLog SET thres = %s WHERE thres_type = 's_thres'", (percentage,))
            mydb.commit()
            cursor.close()
            
            percentage = int(percentage)
            new_thres = round((100.0 - percentage) / 100.0 * 1024.0)
            ser.write(('s_thres = ' + str(new_thres) + '\n').encode('utf-8'))
            
            x = "Threshold|Changed"
        time.sleep(2)
        ser.write(b"LCDData = " + x.encode())
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "message": "Invalid method"})

    
# Define a function to get the number of triggers and latest trigger timestamp for a given log type
def get_log_data(log_type):
    cursor = mydb.cursor()
    timestamp = time.time()
    datetime_obj = time.localtime(timestamp)
    today = time.strftime("%Y-%m-%d", datetime_obj)
    cursor.execute(f"SELECT COUNT(*) FROM {log_type} WHERE DATE(timestamp) = %s", (today,))
    data1 = cursor.fetchone()
    cursor.execute(f"SELECT MAX(timestamp) FROM {log_type}")
    data2 = cursor.fetchone()
    cursor.close()
    return (data1[0], data2[0])

def get_chart_2_data():
    cursor = mydb.cursor()
    cursor.execute(f"SELECT * FROM moistureLog ORDER BY timestamp DESC LIMIT 5")
    results = cursor.fetchall()
    cursor.close()
    cursor = mydb.cursor()
    cursor.execute(f"SELECT thres FROM thresLog WHERE thres_type='s_thres'")
    threshold = cursor.fetchone()[0]
    cursor.close()
    
    return results, threshold

@app.route('/', methods=['GET', 'POST'])
def index():
    timestamp = time.time()
    datetime_obj = time.localtime(timestamp)
    today = time.strftime("%Y-%m-%d", datetime_obj)
    sprinkler_triggers, sprinkler_latest = get_log_data("sprinklerLog")
    alarm_triggers, alarm_latest = get_log_data("alarmLog")
    
    sprinkler_daily = get_daily_triggers("sprinklerLog", 5)
    alarm_daily = get_daily_triggers("alarmLog", 5)
    
    results, threshold = get_chart_2_data()
    label_list = [dt[1].strftime("%Y-%m-%d %H:%M:%S") for dt in results]
    
    chart_2_data = {
        'labels': label_list,
        'datasets': [
            {
                'label': 'Moisture',
                'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                'borderColor': 'rgba(255, 99, 132, 1)',
                'data': [round((row[0]-1024) / -1024,2) * 100 for row in results],
                'fill': False
            },
            {
                'label': 'Threshold',
                'borderColor': 'rgba(54, 162, 235, 1)',
                'data': [threshold for i in range(len(results))],
                'fill': False
            }
        ]
    }
    return render_template('index.html',
                           today=today,
                           datetime=datetime,
                           timedelta=timedelta,
                           map=map,
                           str=str,
                           sprinkler_triggers=sprinkler_triggers,
                           sprinkler_latest=sprinkler_latest,
                           alarm_triggers=alarm_triggers,
                           alarm_latest=alarm_latest,
                           sprinkler_daily= sprinkler_daily,
                           alarm_daily=alarm_daily,
                           chart_2_data=json.dumps(chart_2_data))
    if request.method == "GET":
        timestamp = time.time()
        datetime_obj = time.localtime(timestamp)
        today = time.strftime("%Y-%m-%d", datetime_obj)
        sprinkler_triggers, sprinkler_latest = get_log_data("sprinklerLog")
        alarm_triggers, alarm_latest = get_log_data("alarmLog")
        
        sprinkler_daily = get_daily_triggers("sprinklerLog", 5)
        alarm_daily = get_daily_triggers("alarmLog", 5)
        
        results, threshold = get_chart_2_data()
        label_list = [dt[1].strftime("%Y-%m-%d %H:%M:%S") for dt in results]
        chart_2_data = {
            'labels': label_list,
            'datasets': [
                {
                    'label': 'Moisture',
                    'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                    'borderColor': 'rgba(255, 99, 132, 1)',
                    'data': [round((row[0]-1024) / -1024,2) * 100 for row in results],
                    'fill': False
                },
                {
                    'label': 'Threshold',
                    'borderColor': 'rgba(54, 162, 235, 1)',
                    'data': [threshold for i in range(len(results))],
                    'fill': False
                }
            ]
        }
        return render_template('index.html',
                           today=today,
                           datetime=datetime,
                           timedelta=timedelta,
                           map=map,
                           str=str,
                           sprinkler_triggers=sprinkler_triggers,
                           sprinkler_latest=sprinkler_latest,
                           alarm_triggers=alarm_triggers,
                           alarm_latest=alarm_latest,
                           sprinkler_daily= sprinkler_daily,
                           alarm_daily=alarm_daily,
                            chart_2_data=json.dumps(chart_2_data))


def get_daily_triggers(log_type, days):
    daily_triggers = []
    cursor = mydb.cursor()
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        cursor.execute(f"SELECT COUNT(*) FROM {log_type} WHERE DATE(timestamp) = %s", (date,))
        data = cursor.fetchone()
        daily_triggers.append(data[0])
    cursor.close()
    return daily_triggers[::-1]


   
@app.route('/moisture-level')
def moisture_level():
    try:
        cursor = mydb.cursor()
        cursor.execute("SELECT moisture_level, timestamp FROM moistureLog ORDER BY timestamp DESC LIMIT 1")
        data = cursor.fetchone()
        cursor.close()
        
        moisture_level = 0
        if data is not None:
            analog_value = int(data[0])
            moisture_level = round(((analog_value - 1024) / -1024.0) * 100, 2)
            #ser.write(b"LCDData = Moisture Level:|" + str(moisture_level).encode() + b"%") 

        return str(moisture_level)
    except Exception as e:
        print (e)
        return 'Loading...'

# Run the Flask app
if __name__ == "__main__":
    app.run(host="192.168.137.219", port=8080, debug=False)
    '''

