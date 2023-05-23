from flask import Flask, render_template, request
import paho.mqtt.client as mqtt
import paho.mqtt.client as paho
import json
import mysql.connector

mydb = mysql.connector.connect(
    host="localhost",
    user="pi",
    password="pi",
    database="greenhouse_db"
)



app = Flask(__name__)

