from flask import Flask, render_template, jsonify, request
import serial
import mysql.connector

import schedule
import time

app = Flask(__name__)

# Connect to database 
mydb = mysql.connector.connect(
  host="localhost",
  user="pi",
  password="glds2010",
  database="mydb2"
)

# Open serial port
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
#ser = serial.Serial('/dev/ttyUSB1', 9600, timeout=1, encoding='latin-1')
ser.flush()

def insert_data_at_interval():
    try:
        temperature = float(ser.readline().strip().decode('utf-8'))
        humidity = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
    except UnicodeDecodeError as e:
        print(f"Error decoding data: {e}")
        return
    
    cursor = mydb.cursor()
    sql = "INSERT INTO devices (temperature, humidity) VALUES (%s, %s)"
    val = (temperature, humidity)
    cursor.execute(sql, val)
    mydb.commit()
    
    #Fetch the latest data from the database
    cursor.execute("SELECT * FROM devices ORDER BY date_created DESC LIMIT 10")
    devices = cursor.fetchall()
    
    #Render the template with the lastest data     
    return render_template('index6.html', devices=devices)

# Schedule the function to run every 1 minute
schedule.every(20).minutes.do(insert_data_at_interval)

@app.route('/redirect-page')
def redirect_page():
    try:
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        livingroom = float(ser.readline().strip().decode('utf-8'))
        bedroom = float(ser.readline().strip().decode('utf-8'))
        diningroom = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
    except UnicodeDecodeError as e:
        print(f"Error decoding data: {e}")
        return jsonify({'status': 'error', 'message': 'Error decoding data'})
    
    return render_template('lightcontrol.html', livingroom=livingroom, bedroom=bedroom, diningroom=diningroom)

@app.route('/AirControl')
def airControl_page():
    try:
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        motorStatus = float(ser.readline().strip().decode('utf-8'))
        motorSpeed = float(ser.readline().strip().decode('utf-8'))
    except UnicodeDecodeError as e:
        print(f"Error decoding data: {e}")
        return jsonify({'status': 'error', 'message': 'Error decoding data'})    
        
    return render_template('AirmotorControl.html', motorStatus=motorStatus, motorSpeed=motorSpeed)


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
    except UnicodeDecodeError as e:
        print(f"Error decoding data: {e}")
        return jsonify({'status': 'error', 'message': 'Error decoding data'})

    return render_template('data_visual.html', temperature=temperature, humidity=humidity)

@app.route('/LigtingDV')
def LightingDV():
    try:
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        livingroom = float(ser.readline().strip().decode('utf-8'))
        bedroom = float(ser.readline().strip().decode('utf-8'))
        diningroom = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))        
    except UnicodeDecodeError as e:
        print(f"Error decoding data: {e}")
        return jsonify({'status': 'error', 'message': 'Error decoding data'})
    
    return render_template('data_visual2.html', livingroom=livingroom, bedroom=bedroom, diningroom=diningroom)

@app.route('/AirControlDV')
def AirControlDV():
    try:
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        _ = float(ser.readline().strip().decode('utf-8'))
        motorStatus = float(ser.readline().strip().decode('utf-8'))
        motorSpeed = float(ser.readline().strip().decode('utf-8'))        
    except UnicodeDecodeError as e:
        print(f"Error decoding data: {e}")
        return jsonify({'status': 'error', 'message': 'Error decoding data'})
    
    return render_template('data_visual3.html', motorStatus=motorStatus, motorSpeed=motorSpeed)
    

@app.route('/lightcontrol', methods=['GET', 'POST'])
def lightcontrol():
    global ser
    if request.method == 'POST':
        livingroom = request.form['livingroom']
        bedroom = request.form['bedroom']
        diningroom = request.form['diningroom']
        
        mycursor = mydb.cursor()
        sql = "INSERT INTO lightingdb (livingroom, bedroom, diningroom) VALUES (%s, %s, %s)"
        val = (livingroom, bedroom, diningroom)
        mycursor.execute(sql, val)
        mydb.commit()
        
        ser.write(bytes("{}{}{}".format(livingroom, bedroom, diningroom), 'utf-8'));
        
        return render_template('lightcontrol.html', livingroom=livingroom, bedroom=bedroom, diningroom=diningroom, updated=True)
    
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
    
        return render_template('AirmotorControl.html', state=state, level=level, updated=True)

@app.route('/get-data')
def get_data():
    try:
        cursor = mydb.cursor(dictionary=True)
        cursor.execute("SELECT * FROM devices ORDER BY date_created DESC LIMIT 10")
        devices = cursor.fetchall()
    except my.sql.connector.Error as error:
        print("Failed to retrieve data from MySQL: {}".format(error))
        devices = []

    # Check temperature and humidity for warning message
    warning = False
    for device in devices:
        if device['temperature'] > 40 or device['humidity'] > 90:
            warning = True
            break

    # Return the latest data and warning flag as a JSON object
    return jsonify({'devices': devices, 'warning': warning})

@app.route('/get-data2')
def get_data2():
    try:
        cursor = mydb.cursor(dictionary=True)
        cursor.execute("SELECT * FROM lightingdb ORDER BY date_created DESC LIMIT 10")
        lighting = cursor.fetchall()
    except my.sql.connector.Error as error:
        print("Failed to retrieve data from MySQL: {}".format(error))
        lighting = []
    # Return the latest data and warning flag as a JSON object
    return jsonify({'lightingdb': lighting})

@app.route('/get-data3')
def get_data3():
    try:
        cursor = mydb.cursor(dictionary=True)
        cursor.execute("SELECT * FROM AirControlDB ORDER BY data_created DESC LIMIT 10")
        aircontrol = cursor.fetchall()
    except mysql.connector.Error as error:
        print("Failed to retrieve data from MySQL: {}".format(error))
        aircontrol = []
    # Return the latest data and warning flag as a JSON object
    return jsonify({'AirControlDB': aircontrol})

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
    except UnicodeDecodeError as e:
        print(f"Error decoding data: {e}")
        return jsonify({'status': 'error', 'message': 'Error decoding data'})
    
    cursor = mydb.cursor(dictionary=True)
    sql = "INSERT INTO devices (temperature, humidity) VALUES (%s, %s)"
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
    
    #cursor.execute("SELECT * FROM devices WHERE id = %s", (cursor.lastrowid,))
    #device = cursor.fetchone()
    #return jsonify({'status': 'success', 'device': device})
    cursor.execute("SELECT * FROM devices ORDER BY date_created DESC LIMIT 10")
    devices = cursor.fetchall()
    # return render_template('index6.html', devices=devices, warming=warming)
    return jsonify({'status': 'success', 'message': ''});

# Display data on web page
@app.route('/')
def show_data():
    try:
        cursor = mydb.cursor(dictionary=True)
        cursor.execute("SELECT * FROM devices ORDER BY date_created DESC LIMIT 10")
        devices = cursor.fetchall()
    except my.sql.connector.Error as error:
        print("Failed to retrieve data from MySQL: {}".format(error))
        devices = []
              
    #Check temperature and huminity
    warning = False
    for device in devices:
        if device['temperature'] > 40 or device['humidity'] > 90:
            warning = True
            break
        
    return render_template('index6.html', devices=devices, warning=warning)


if __name__ == '__main__':
    app.run(host='172.17.160.25',port=8080,debug=True)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

