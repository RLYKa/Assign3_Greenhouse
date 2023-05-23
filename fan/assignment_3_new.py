from flask import Flask, render_template, jsonify, request
import serial
import mysql.connector
import schedule
import time

import paho.mqtt.client as mqtt

app = Flask(__name__)

# Connect to database 
mydb = mysql.connector.connect(
  host="localhost",
  user="pi",
  password="glds2010",
  database="mydb"
)

# Open serial port
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
#ser = serial.Serial('/dev/ttyUSB1', 9600, timeout=1, encoding='latin-1')
ser.flush()

# MQTT Configuration
mqtt_broker = "30879eac8d1b42ea9dd2feaf91890eb6.s2.eu.hivemq.cloud"
mqtt_port = 8883
username = "user1"
password = "Password123"
topic = "nodes/"

mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print("Conntected to MQTT broker")
    client.subscribe("topic/temperature")
    client.subscribe("topic/humidity")

def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8")
    topic = msg.topic

    if topic == "topic/temperature":
        temperature = float(payload)
        # Process temperature value
        #...

    if topic == "topic/humidity":
        humidity = float(payload)
        # Process temperature value
        #...  

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.connect(mqtt_broker, mqtt_port, username, password)
mqtt_client.loop_start()
    

def insert_data_at_interval():
    try:
        temperature = float(ser.readline().strip().decode('utf-8'))
        humidity = float(ser.readline().strip().decode('utf-8'))
        #Publish temperature and humidity values as MQTT messages
        mqtt_client.publish("topic/temperature", str(temperature))
        mqtt_client.publish("topic/humidity", str(humidity))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
    except UnicodeDecodeError as e:
        print(f"Error decoding data: {e}")
        return
    
    cursor = mydb.cursor()
    sql = "INSERT INTO tempA (temperature, humidity) VALUES (%s, %s)"
    val = (temperature, humidity)
    cursor.execute(sql, val)
    mydb.commit()
    
    #Fetch the latest data from the database
    cursor.execute("SELECT * FROM tempA ORDER BY date_created DESC LIMIT 10")
    tempA = cursor.fetchall()
    
    #Render the template with the lastest data     
    return render_template('index6.html', tempA=tempA)

# Schedule the function to run every 1 minute
schedule.every(20).minutes.do(insert_data_at_interval)


@app.route('/get-data')
def get_data():
    try:
        cursor = mydb.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tempA ORDER BY date_created DESC LIMIT 10")
        tempAs = cursor.fetchall()
    except my.sql.connector.Error as error:
        print("Failed to retrieve data from MySQL: {}".format(error))
        tempAs = []

    # Return the latest data and warning flag as a JSON object
    return jsonify({'tempA': tempAs})

# Read data from serial port and insert into database
@app.route('/insert-data')
def insert_data():
    try:
        temperature = float(ser.readline().strip().decode('utf-8'))
        humidity = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
    except UnicodeDecodeError as e:
        print(f"Error decoding data: {e}")
        return jsonify({'status': 'error', 'message': 'Error decoding data'})
    
    cursor = mydb.cursor(dictionary=True)
    sql = "INSERT INTO tempA (temperature, humidity) VALUES (%s, %s)"
    val = (temperature, humidity)
    cursor.execute(sql, val)
    mydb.commit()
    #return render_template('index6.html')

    # check the temperature and humidity
    if temperature > 40 or humidity > 60:
    # Perform an action or display a message
        warming = "Warning: Temperature is above 40'C or humidity is above 60."
    else:
        warming = ""
    #cursor.execute("SELECT * FROM s WHERE id = %s", (cursor.lastrowid,))
    #device = cursor.fetchone()
    #return jsonify({'status': 'success', 'device': device})
    cursor.execute("SELECT * FROM tempA ORDER BY date_created DESC LIMIT 10")
    tempA = cursor.fetchall()
    # return render_template('index6.html', devices=devices, warming=warming)
    return jsonify({'status': 'success', 'message': ''});

# Display data on web page
@app.route('/')
def show_data():
    try:
        cursor = mydb.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tempA ORDER BY date_created DESC LIMIT 10")
        tempA = cursor.fetchall()
    except my.sql.connector.Error as error:
        print("Failed to retrieve data from MySQL: {}".format(error))
        tempA = []
              
    #Check temperature and huminity
    warning = False
    for tempA in tempA:
        if tempA['temperature'] > 40 or tempA['humidity'] > 90:
            warning = True
            break
        
    return render_template('index6.html', tempA=tempA, warning=warning)

@app.route('/redirect-page2')
def redirect_page2():
    try:
        temperature = float(ser.readline().strip().decode('utf-8'))
        humidity = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
    except UnicodeDecodeError as e:
        print(f"Error decoding data: {e}")
        return jsonify({'status': 'error', 'message': 'Error decoding data'})
    return render_template('data_visual.html', temperature=temperature, humidity=humidity)

# update the checklist
@app.route('/update_checklist', methods=['POST'])
def update_checklist():
    new_value = float(request.form.get('new_value'))
    cursor = mydb.cursor()
    cursor.execute("UPDATE tempA SET checklist = %s", (new_value,))
    mydb.commit()
    cursor.close()
    message = "Checklist updated successfully"
    #return "Checklist updated successfully"
    return render_template('index6.html', message=message)

#AirCond
@app.route('/insertAirCond')
def airControl():
    try:
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        motorStatus = float(ser.readline().strip().decode('utf-8'))
        motorSpeed = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
    except UnicodeDecodeError as e:
        print(f"Error decoding data: {e}")
        return jsonify({'status': 'error', 'message': 'Error decoding data'})

    return render_template('index6.html', motorStatus=motorStatus, motorSpeed=motorSpeed)

@app.route('/Aircontrol', methods=['POST'])
def aircontrol():
    global ser
    if request.method == 'POST':
        state = request.form['direction']
        level = request.form['speed']

        # update database
        mycursor = mydb.cursor()
        sql = "INSERT INTO AirControlDB (State, Level) VALUES (%s, %s)"
        val = (state, level)
        mycursor.execute(sql, val)
        mydb.commit()
    
        ser.write(bytes("<{}{}".format(state, level), 'utf-8'));
    
        return render_template('index6.html', state=state, level=level, updated=True)












if __name__ == '__main__':
    #app.run(host='192.168.185.168',port=8080,debug=True)
    #app.run(host='192.168.0.193',port=8080,debug=True)
    app.run(host='172.17.160.20',port=8080,debug=True)
    
    while True:
        schedule.run_pending()
        time.sleep(1)
