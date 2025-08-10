from datetime import datetime
import json
import time
from pprint import pprint
import random
import logging
import os

import paho.mqtt.client as mqtt
import requests

logging.basicConfig(filename="app.log", \
                    level=logging.DEBUG, \
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', \
                    force=True)
logging.info('-----------')
logging.info("App Started")

current_dir = os.path.dirname(os.path.realpath(__file__))
logging.debug(f"Working DIR: {current_dir}")

mqtt_configured = os.environ.get("MQTT", False)
lube_configured = os.environ.get('LUBELOGGER', False)

if mqtt_configured != False:
    # Define the MQTT broker details
    broker_address = os.environ.get('MQTT_SERV')
    broker_port = int(os.environ.get('MQTT_PORT'))
    broker_user = os.environ.get('MQTT_USER')
    broker_pass = os.environ.get('MQTT_PASS')
    broker_client_id = str(random.random())
    topic = os.environ.get('MQTT_BASE')

else:
    logging.critical("No MQTT configured, exiting")
    exit()

# Lubelogger Details
if lube_configured != False :
    lubelogger_base_url = os.environ.get('LUBELOGGER_ADDRESS')
    lubelogger_port = os.environ.get('LUBELOGGER_PORT')
else:
    logging.critical("No LubeLogger Configured, Exiting")
    exit()

if lubelogger_port != '':
    lubelogger_url = 'http://'+ str(lubelogger_base_url) + ':' + str(lubelogger_port)
else:
    lubelogger_url = lubelogger_base_url

logging.debug(f"Lubelogger address = {lubelogger_url}")

def get_all_cars():
    logging.debug("In the get_all_cars() Function")
    api_address = '/api/vehicles'
    x = requests.get(lubelogger_url + api_address)
    data = x.text
    data = json.loads(data)
    return data

def find_car(topic, cars_json):
    logging.debug("In the find_car() function")
    logging.debug(f"    Topic : {topic} | cars_json : {cars_json}")
    # First strip the MQTT base topic off
    car_topic = topic.split('/')
    car_make_model = car_topic[1].split('-')
    car_make = car_make_model[0]
    car_model = car_make_model[1]
    
    # Loop though the cars, and if make & model match, return the id
    for car in cars_json:
        if car['make'].lower() == car_make.lower() and car['model'].lower() == car_model.lower():
            logging.debug(car)
            id = car['id']
    
    return id

def get_last_odo(car_id):
    logging.debug("In the get_last_odo() Function")
    api_address = f"/api/vehicle/odometerrecords/latest?vehicleId={car_id}"

    x = requests.get(f"{lubelogger_url}{api_address}")
    data = x.text
    data = json.loads(data)
    logging.info(f"Last Odo was {data}")
    return data

def compare_odo(last_odo, new_odo):
    logging.debug("In the compare_odo() Function")
    if int(float(new_odo)) > int(float(last_odo)):
        diff = int(float(new_odo)) - int(float(last_odo))
        logging.debug(f"Odos are different by {str(diff)} miles")
        return True
    else:
        logging.debug("Odo is no different, has it moved?")
        return False

def update_odo(new_odo, car_id):
    logging.debug("In the update_odo() Function")
    api_address = f"/api/vehicle/odometerrecords/add?vehicleId={car_id}"
    now = datetime.strftime(datetime.now(), "%Y-%m-%d")
    new_odo = int(float(new_odo))
    body = {'date': now, 'odometer':int(new_odo)}
    x = requests.post(f"{lubelogger_url}{api_address}", json = body)
    data = x.text
    data = json.loads(data)
    logging.debug(data)
    return data



# Callback when the client connects to the broker
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logging.info(f"Connected with result code {rc}")
        # Subscribe to the topic when connected
        client.subscribe(topic)
    else:
        logging.error(f"Reconnection failed. Error: {rc}")

# Callback when a message is received from the subscribed topic
def on_message(client, userdata, msg):
    payload = msg.payload.decode('utf-8')  # Decode the byte string
    topic = msg.topic
    logging.debug(f"Received message on topic {msg.topic}: {payload}")

    try:
        # Parse the payload assuming it is in JSON format
        data = json.loads(payload)
        logging.debug(f"Parsed JSON data: {data}")
        
        # Now you can access specific fields in 'data'
        # For example:
        # value = data["key"]
        # print("Value:", value)

    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON. Error: {e}")

    all_cars = get_all_cars()
    car_id = find_car(topic, all_cars)
    last_odo = get_last_odo(car_id)
    odo_different = compare_odo(last_odo, data['odometer'])
    if odo_different:
        updated = update_odo(data['odometer'], car_id)

        logging.debug(updated)


# Callback when the client disconnects from the broker
def on_disconnect(client, userdata, flags, rc, properties=None):
    logging.debug(f"Disconnected with result code {rc}")
    # Attempt to reconnect every 5 seconds
    while not client.is_connected():
        try:
            client.reconnect()
        except Exception as e:
            logging.error(f"Reconnection failed. Error: {e}")
            time.sleep(5)

# Create an MQTT client instance
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=broker_client_id)

# Set up the callback function
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

client.username_pw_set(broker_user, broker_pass)

# Connect to the MQTT broker
client.connect(broker_address, int(broker_port))

# Run the client loop to start listening for messages
client.loop_forever()
