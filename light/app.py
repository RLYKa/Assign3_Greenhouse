from flask import Flask, render_template, request, jsonify
import paho.mqtt.client as mqtt

app = Flask(__name__)
broker = "30879eac8d1b42ea9dd2feaf91890eb6.s2.eu.hivemq.cloud"
port = 8883
username = "user1"
password = "Password123"

mqtt_client = mqtt.Client(client_id="")
mqtt_client.username_pw_set(username, password)
mqtt_client.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLSv1_2)

mqtt_client.connect(broker, port)

TOPIC_STATUS = 'nodes/status'
TOPIC_THRESHOLD = 'nodes/threshold'
TOPIC_LED = 'nodes/ledControl'
TOPIC_REQUEST_STATUS = "nodes/requestStatus"



def on_connect(client, userdata, flags, rc):
    mqtt_client.subscribe(TOPIC_STATUS)
    mqtt_client.subscribe(TOPIC_REQUEST_STATUS)
    mqtt_client.subscribe(TOPIC_LED)
    mqtt_client.subscribe(TOPIC_THRESHOLD)


def on_message(client, userdata, message):
    print(message.payload.decode())  # Print received message payload


mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message


@app.route('/')
def index():
    return render_template('index2.html')


@app.route('/get_status', methods=['GET'])
def get_status():
    mqtt_client.publish(TOPIC_REQUEST_STATUS, "getStatus")
    return 'OK', 200


@app.route('/change_threshold', methods=['POST'])
def change_threshold():
    index = request.form.get('index')
    new_threshold = request.form.get('new_threshold')
    mqtt_client.publish(TOPIC_THRESHOLD, f"{index}:{new_threshold}")
    return 'OK', 200


@app.route('/control_led', methods=['POST'])
def control_led():
    index = request.form.get('index')
    duration = request.form.get('duration')
    mqtt_client.publish(TOPIC_LED, f"{index}:{duration}")
    return 'OK', 200


if __name__ == '__main__':
    mqtt_client.loop_start()  # Start the MQTT loop in a separate thread
    app.run(host='0.0.0.0', port=8080)
