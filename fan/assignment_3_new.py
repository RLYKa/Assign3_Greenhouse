from flask import Flask, render_template, jsonify, request
import serial
import mysql.connector
import schedule
import time
import json
import paho.mqtt.client as mqtt
import traceback
import threading

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

mqtt_client = mqtt.Client(client_id="")


mqtt_client.username_pw_set(username, password)
mqtt_client.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLSv1_2)

mqtt_client.connect(mqtt_broker, mqtt_port)


def on_connect(client, userdata, flags, rc):
    print("Conntected to MQTT broker")
    client.subscribe("nodes/th")
    client.subscribe("nodes/humidity")
    client.subscribe("nodes/th/get")
    client.subscribe("nodes/th/set")
    client.subscribe("nodes/th/set2")
    client.subscribe("nodes/th/set3")
    client.subscribe("nodes/control")
    client.subscribe("nodes/control2")
    client.subscribe("nodes/control3")

def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8")
    topic = msg.topic

    if topic == "nodes/th":
        data = json.loads(payload)
        print(data)
        cursor = mydb.cursor()
        sql = "INSERT INTO tempA (temperature, humidity) VALUES (%s, %s)"
        val = (data['temp'], data['humd'])
        #print (val)
        #val = json.dumps(val)
        # cursor.execute(sql, val)
        # mydb.commit()
        

    if topic == "nodes/th/get":
        try:
            tableName = 'tempA'
            plot = 'A'
            if payload == '1':
                tableName = 'tempA'
                plot = 'A'
            elif payload == '2':
                tableName = 'tempB'
                plot = 'B'
            elif payload == '3':
                tableName = 'tempC'
                plot = 'C'
                
            cursor = mydb.cursor()
            #Fetch the latest data from the database
            cursor.execute("SELECT temperature, humidity FROM " + tableName + " ORDER BY date_created DESC LIMIT 1")
            tempA = cursor.fetchall()
            th = {
                "plot": plot,
                "temp": float(tempA[0][0]),
                "humd": float(tempA[0][1]),
            }
            mqtt_client.publish("nodes/th", json.dumps(th))
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            
    if topic == 'nodes/th/set':
        try:
            data = json.loads(payload)
            print(data)
            ser.write(bytes("<{}{}".format(data['status'], data['speed']), 'utf-8'));
            print("Sent to arduino, plot1 air cond setting has been changed")
        except Exception as e:
            print(traceback.format_exc())
            
    if topic == 'nodes/th/set2':
        try:
            data = json.loads(payload)
            print(data)
            ser.write(bytes(">{}{}".format(data['status'], data['speed']), 'utf-8'));
            print("Sent to arduino, plot2 air cond setting has been changed")
        except Exception as e:
            print(traceback.format_exc())

    if topic == 'nodes/th/set3':
        try:
            data = json.loads(payload)
            print(data)
            ser.write(bytes("?{}{}".format(data['status'], data['speed']), 'utf-8'));
            print("Sent to arduino, plot3 air cond setting has been changed")
        except Exception as e:
            print(traceback.format_exc())
            
    if topic == 'nodes/control':
        try:
            data = json.loads(payload)
            print(data)
            if (data > 50):
                ser.write(bytes("<{}{}".format(1, 3), 'utf-8'));
                print("sent to arduino checklist changed")
            elif (data > 27):
                ser.write(bytes("<{}{}".format(1, 2), 'utf-8'));
                print("sent to arduino checklist changed")
            elif (data < 27):
                ser.write(bytes("<{}{}".format(1, 1), 'utf-8'));
                print("sent to arduino checklist changed")
            elif (data < 23):
                ser.write(bytes("<{}{}".format(1, 0), 'utf-8'));
                print("the temperature below 23, it's safe");
            else:
                ser.write(bytes("<{}{}".format(1, 0), 'utf-8'));
                print("Didn't change the checklist");
        except Exception as e:
            print(traceback.format_exc())
            
            
    if topic == 'nodes/control2':
        try:
            data = json.loads(payload)
            print(data)
            if (data > 50):
                ser.write(bytes(">{}{}".format(1, 3), 'utf-8'));
                print("sent to arduino checklist changed")
            elif (data > 27):
                ser.write(bytes(">{}{}".format(1, 2), 'utf-8'));
                print("sent to arduino checklist changed")
            elif (data < 27):
                ser.write(bytes(">{}{}".format(1, 1), 'utf-8'));
                print("sent to arduino checklist changed")
            elif (data < 23):
                ser.write(bytes(">{}{}".format(1, 0), 'utf-8'));
                print("the temperature below 23, it's safe");
            else:
                ser.write(bytes(">{}{}".format(1, 0), 'utf-8'));
                print("Didn't change the checklist");
        except Exception as e:
            print(traceback.format_exc())
            
    if topic == 'nodes/control3':
        try:
            data = json.loads(payload)
            print(data)
            if (data > 50):
                ser.write(bytes("?{}{}".format(1, 3), 'utf-8'));
                print("sent to arduino checklist changed")
            elif (data > 27):
                ser.write(bytes("?{}{}".format(1, 2), 'utf-8'));
                print("sent to arduino checklist changed")
            elif (data < 27):
                ser.write(bytes("?{}{}".format(1, 1), 'utf-8'));
                print("sent to arduino checklist changed")
            elif (data < 23):
                ser.write(bytes("?{}{}".format(1, 0), 'utf-8'));
                print("the temperature below 23, it's safe");
            else:
                ser.write(bytes("?{}{}".format(1, 0), 'utf-8'));
                print("Didn't change the checklist");
        except Exception as e:
            print(traceback.format_exc())            
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.loop_start()
    

def insert_data_at_interval():
    try:
        with app.app_context():
            temperature = float(ser.readline().strip().decode('utf-8'))
            humidity = float(ser.readline().strip().decode('utf-8'))
            tempB = float(ser.readline().strip().decode('utf-8'))
            humdB = float(ser.readline().strip().decode('utf-8'))
            tempC = float(ser.readline().strip().decode('utf-8'))
            humdC = float(ser.readline().strip().decode('utf-8'))
            motorStatusA = float(ser.readline().strip().decode('utf-8'))
            motorSpeedA = float(ser.readline().strip().decode('utf-8'))
            motorStatusB = float(ser.readline().strip().decode('utf-8'))
            motorSpeedB = float(ser.readline().strip().decode('utf-8'))
            motorStatusC = float(ser.readline().strip().decode('utf-8'))
            motorSpeedC = float(ser.readline().strip().decode('utf-8'))
            #Publish temperature and humidity values as MQTT messages
            th = {
                "temp": temperature,
                "humd": humidity,
                "tempB": tempB,
                "humdB": humdB,
                "tempC": tempC,
                "humdC": humdC,
                "mStatusA": motorStatusA,
                "mSpeedA": motorSpeedA,
                "mStatusB": motorStatusB,
                "mSpeedB": motorSpeedB,
                "mStatusC": motorStatusC,
                "mSpeedC": motorSpeedC
            }
            mqtt_client.publish("nodes/th", json.dumps(th))
            #mqtt_client.publish("topic/humidity", str(humidity))

            if (temperature >20):
                ser.write(bytes("<{}{}".format(1, 1), 'utf-8'));
                
            print("insert data at interval")
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
    # return render_template('index6.html', tempA=tempA)

# Schedule the function to run every 1 minute
# schedule.every(20).minutes.do(insert_data_at_interval)

def run_scheduler():
    schedule.every(10).minutes.do(insert_data_at_interval)
    while True:
        schedule.run_pending()
        time.sleep(1)

@app.route('/plot2')
def redirect_page():
    try:
        temperature = float(ser.readline().strip().decode('utf-8'))
        humidity = float(ser.readline().strip().decode('utf-8'))
        #Publish temperature and humidity values as MQTT messages
        th = {
            "temp": temperature,
            "humd": humidity
        }
        mqtt_client.publish("nodes/th", jsonify(th))
        #mqtt_client.publi sh("topic/humidity", str(humidity))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
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
    
    return render_template('plot2.html', temperature=temperature, humidity=humidity)

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

@app.route('/get-data2')
def get_data2():
    try:
        cursor = mydb.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tempB ORDER BY date_created DESC LIMIT 10")
        tempBs = cursor.fetchall()
    except my.sql.connector.Error as error:
        print("Failed to retrieve data from MySQL: {}".format(error))
        tempBs = []

    # Return the latest data and warning flag as a JSON object
    return jsonify({'tempB': tempBs})

@app.route('/get-data3')
def get_data3():
    try:
        cursor = mydb.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tempC ORDER BY date_created DESC LIMIT 10")
        tempCs = cursor.fetchall()
    except my.sql.connector.Error as error:
        print("Failed to retrieve data from MySQL: {}".format(error))
        tempCs = []

    # Return the latest data and warning flag as a JSON object
    return jsonify({'tempC': tempCs})


# Read data from serial port and insert into database
@app.route('/insert-data')
def insert_data():
    try:
        temperature = float(ser.readline().strip().decode('utf-8'))
        humidity = float(ser.readline().strip().decode('utf-8'))
        #Publish temperature and humidity values as MQTT messages
        th = {
            "temp": temperature,
            "humd": humidity
        }
        mqtt_client.publish("nodes/th", json.dumps(th))
        #mqtt_client.publish("topic/temperature", str(temperature))
        #mqtt_client.publish("topic/humidity", str(humidity))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
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

@app.route('/insert-data2')
def insert_data2():
    try:
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        #Publish temperature and humidity values as MQTT messages

        #mqtt_client.publish("topic/temperature", str(temperature))
        #mqtt_client.publish("topic/humidity", str(humidity))
        temperature = float(ser.readline().strip().decode('utf-8'))
        humidity = float(ser.readline().strip().decode('utf-8'))
        th = {
            "temp": temperature,
            "humd": humidity
        }
        mqtt_client.publish("nodes/th", json.dumps(th))        
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
    sql = "INSERT INTO tempB (temperature, humidity) VALUES (%s, %s)"
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
    cursor.execute("SELECT * FROM tempB ORDER BY date_created DESC LIMIT 10")
    tempA = cursor.fetchall()
    # return render_template('index6.html', devices=devices, warming=warming)
    return jsonify({'status': 'success', 'message': ''});

@app.route('/insert-data3')
def insert_data3():
    try:
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        #Publish temperature and humidity values as MQTT messages
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        #mqtt_client.publish("topic/temperature", str(temperature))
        #mqtt_client.publish("topic/humidity", str(humidity))
        temperature = float(ser.readline().strip().decode('utf-8'))
        humidity = float(ser.readline().strip().decode('utf-8'))
        th = {
            "temp": temperature,
            "humd": humidity
        }
        mqtt_client.publish("nodes/th", json.dumps(th))        
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
    sql = "INSERT INTO tempC (temperature, humidity) VALUES (%s, %s)"
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
    cursor.execute("SELECT * FROM tempC ORDER BY date_created DESC LIMIT 10")
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
        
        cursor.execute("SELECT * FROM tempB ORDER BY date_created DESC LIMIT 10")
        tempB = cursor.fetchall()
        
        cursor.execute("SELECT * FROM tempC ORDER BY date_created DESC LIMIT 10")
        tempC = cursor.fetchall()        
    except my.sql.connector.Error as error:
        print("Failed to retrieve data from MySQL: {}".format(error))
        tempA = []
        tempB = []
        tempC = []      
    #Check temperature and huminity
    warning = False
    for tempA in tempA:
        if tempA['temperature'] > 40 or tempA['humidity'] > 90:
            warning = True
            break
        
    return render_template('index6.html', tempA=tempA, tempB=tempB, tempC=tempC, warning=warning)

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
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))        
    except UnicodeDecodeError as e:
        print(f"Error decoding data: {e}")
        return jsonify({'status': 'error', 'message': 'Error decoding data'})
    return render_template('data_visual.html', temperature=temperature, humidity=humidity)

@app.route('/plot2d')
def plot2d():
    try:
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))        
        temperature = float(ser.readline().strip().decode('utf-8'))
        humidity = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))        
    except UnicodeDecodeError as e:
        print(f"Error decoding data: {e}")
        return jsonify({'status': 'error', 'message': 'Error decoding data'})
    return render_template('data_visual4.html', temperature=temperature, humidity=humidity)

@app.route('/plot3d')
def plot3d():
    try:
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        temperature = float(ser.readline().strip().decode('utf-8'))
        humidity = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))        
    except UnicodeDecodeError as e:
        print(f"Error decoding data: {e}")
        return jsonify({'status': 'error', 'message': 'Error decoding data'})
    return render_template('data_visual5.html', temperature=temperature, humidity=humidity)

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
        sql = "INSERT INTO airCondA (State, Level) VALUES (%s, %s)"
        val = (state, level)
        mycursor.execute(sql, val)
        mydb.commit()
    
        ser.write(bytes("<{}{}".format(state, level), 'utf-8'));
    
        return render_template('index6.html', state=state, level=level, updated=True)

if __name__ == '__main__':
    #Start the schedular in a separate thread
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()
    
    app.run(host='192.168.185.168',port=8082,debug=True, use_reloader=False)
    #    app.run(host='192.168.0.193',port=8080,debug=True, use_reloader=False)
    #app.run(host='172.17.160.20',port=8080,debug=True)
    

 