from flask import Flask, render_template, request
import paho.mqtt.client as mqtt

app = Flask(__name__, template_folder='/templates')

# MQTT broker credentials
broker = "30879eac8d1b42ea9dd2feaf91890eb6.s2.eu.hivemq.cloud"
port = 8883
username = "user1"
password = "Password123"

# MQTT topic for LDR threshold updates
threshold_topic = "light"

# MQTT client setup
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(username, password)
mqtt_client.connect(broker, port)


@app.route('/')
def index():
    return render_template('assign2.html')


@app.route('/update-threshold', methods=['POST'])
def update_threshold():
    ldr1_threshold = int(request.form['ldr1_threshold'])
    ldr2_threshold = int(request.form['ldr2_threshold'])
    ldr3_threshold = int(request.form['ldr3_threshold'])

    # Publish the threshold values to the MQTT topic
    mqtt_client.publish(threshold_topic, payload=f"{ldr1_threshold},{ldr2_threshold},{ldr3_threshold}")

    return "Thresholds updated successfully!"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
