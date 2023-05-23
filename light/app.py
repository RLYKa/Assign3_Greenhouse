from flask import Flask, render_template, request, jsonify
from flask_mqtt import Mqtt

app = Flask(__name__)
app.config['MQTT_BROKER_URL'] = '30879eac8d1b42ea9dd2feaf91890eb6.s2.eu.hivemq.cloud'
app.config['MQTT_BROKER_PORT'] = 8883
app.config['MQTT_USERNAME'] = 'user1'
app.config['MQTT_PASSWORD'] = 'Password123'
app.config['MQTT_TLS_ENABLED'] = True

mqtt = Mqtt(app)

latest_status = {
    "LED 1": {"state": 0, "threshold": 0},
    "LED 2": {"state": 0, "threshold": 0},
    "LED 3": {"state": 0, "threshold": 0},
}

TOPIC_STATUS = 'status'
TOPIC_THRESHOLD = 'threshold'
TOPIC_LED = 'ledControl'

@app.route('/')
def index():
    return render_template('index2.html')

@app.route('/get_status', methods=['GET'])
def get_status():
    mqtt.publish(TOPIC_STATUS, "getStatus")
    return jsonify(latest_status)

# MQTT Callbacks
@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe(TOPIC_STATUS)

@mqtt.on_message()
def handle_message(client, userdata, message):
    global latest_status
    status = message.payload.decode().split(',')
    latest_status = {
        "LED 1": {"state": int(status[0]), "threshold": int(status[1])},
        "LED 2": {"state": int(status[2]), "threshold": int(status[3])},
        "LED 3": {"state": int(status[4]), "threshold": int(status[5])},
    }

@app.route('/change_threshold', methods=['POST'])
def change_threshold():
    index = request.form.get('index')
    new_threshold = request.form.get('new_threshold')
    mqtt.publish(TOPIC_THRESHOLD, f"{index}:{new_threshold}")
    return 'OK', 200

@app.route('/control_led', methods=['POST'])
def control_led():
    index = request.form.get('index')
    duration = request.form.get('duration')
    mqtt.publish(TOPIC_LED, f"{index}:{duration}")
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
