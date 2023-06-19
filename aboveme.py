#!/usr/bin/env python3
import json
import requests
import time
import paho.mqtt.client as mqtt
from datetime import datetime
import sys
import configparser
import traceback

# Set Up Config
config = configparser.ConfigParser()
configFile = '/app/config/config.cfg'
config.read(configFile)

QUERY_URL_PART1 = config['default'].get('QUERY_URL_PART1')
QUERY_URL_PART2 = config['default'].get('QUERY_URL_PART2')
BOUNDS = config['default'].get('BOUNDS')
EXTRA_DATA_URL = config['default'].get('EXTRA_DATA_URL')
USER_AGENT = config['default'].get('USER_AGENT')
BROKER_ADDRESS = config['default'].get('BROKER_ADDRESS')
BROKER_PORT = config['default'].get('BROKER_PORT')
BROKER_USERNAME = config['default'].get('BROKER_USERNAME')
BROKER_PASSWORD = config['default'].get('BROKER_PASSWORD')
MQTT_TOPIC = config['default'].get('MQTT_TOPIC')
SLEEP = config['default'].get('SLEEP')


if any(value == '' for value in [QUERY_URL_PART1, QUERY_URL_PART2, BOUNDS, EXTRA_DATA_URL, USER_AGENT, BROKER_ADDRESS, BROKER_PORT, BROKER_USERNAME, BROKER_PASSWORD, MQTT_TOPIC, SLEEP]):
    print("Error: Configuration file is missing required values.")
    sys.exit(1)
# Dictionary to store recently seen planes  and their timestamps, so i don't double notify if they are traveling slow
recent_planes = {}
url = QUERY_URL_PART1+BOUNDS+QUERY_URL_PART2
headers = {
    "User-Agent": USER_AGENT
}
# MQTT broker details
broker_address = BROKER_ADDRESS
broker_port = BROKER_PORT
username = BROKER_USERNAME
password = BROKER_PASSWORD
topic = MQTT_TOPIC


# Callback function when connection is established
def on_connect(client, userdata, flags, rc, protocol): # added protocol to help with TLS connection
    print("Connected to MQTT broker with result code " + str(rc))


def setup_mqtt():
    # Create an MQTT client instance 
    client = mqtt.Client(client_id="", userdata=None, protocol=mqtt.MQTTv5) # specified a few args in the client creation for TLS
    
    # enable TLS for secure connection - Test if using the standard MQTT TLS port 8883 and set the TLS version to use
    if broker_port == 8883:
        client.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS)

    # Set username and password if required by your broker
    client.username_pw_set(username, password)

    # Assign the on_connect function
    client.on_connect = on_connect

    # Connect to the MQTT broker
    client.connect(broker_address, int(broker_port))

    # Start the MQTT loop (it will handle reconnecting automatically)
    client.loop_start()
    return client


def extract_flight_information(flight_icao):
    return_data = {}
    try:    
        response = requests.get(EXTRA_DATA_URL + flight_icao, headers=headers)
        json_data = response.json()
       
    # Extract the desired information
        if json_data['identification']['number'] is not None:
            flight_number = json_data['identification']['number'].get(
                'default', 'No Data Available')
            return_data.update({"Flight Number": flight_number})
        if json_data['airport']['origin'] is not None:
            departure_airport = json_data['airport']['origin'].get(
                'name', 'No Data Available')
            if json_data['airport']['origin']['code'] is not None:
                departure_iata_code = json_data['airport']['origin']['code'].get(
                    'iata', 'No Data Available')
                return_data.update(
                    {"Departure Airport": f"{departure_airport} ({departure_iata_code})"})
        if json_data['airport']['destination'] is not None:
            arrival_airport = json_data['airport']['destination'].get(
                'name', 'No Data Available')
            if json_data['airport']['destination']['code'] is not None:
                arrival_iata_code = json_data['airport']['destination']['code'].get(
                    'iata', 'No Data Available')
                return_data.update(
                    {"Arrival Airport": f"{arrival_airport} ({arrival_iata_code})"})
        if json_data['aircraft']['images']['thumbnails'][0] is not None:
                image_url = json_data['aircraft']['images']['thumbnails'][0].get(
                    'src', 'No Data Available')
                return_data.update({"ent_pic": str(image_url)})    

        # The following are not always available, so i don't actually use them - but they're below in case you ever want to use:
        # if json_data['airport']['destination']['info'] is not None:
        #     arrival_gate = json_data['airport']['destination']['info'].get('gate', 'No Data Available')
        # if json_data['time']['scheduled'] is not None:
        #     scheduled_departure_time = json_data['time']['scheduled'].get('departure', 'No Data Available')
        # if json_data['time']['scheduled'] is not None:
        #     scheduled_arrival_time = json_data['time']['scheduled'].get('arrival', 'No Data Available')
        # if json_data['time']['real'] is not None:
        #     actual_departure_time = json_data['time']['real'].get('departure', 'No Data Available')
        # if json_data['time']['estimated'] is not None:
        #     estimated_arrival_time = json_data['time']['estimated'].get('arrival', 'No Data Available')

        # Return the extracted information as a dictionary
        return return_data
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        # try again after the normal sleep period
        time.sleep(int(SLEEP))
        return return_data


def check_above_me(mqtt_client):
  
    try:
        # Fetch JSON data from the URL with the specified headers
        response = requests.get(url, headers=headers, timeout=30)
        json_data = response.json()

        # Extract statistics
        full_count = json_data["full_count"]
        total_stats = json_data["stats"]["total"]
        visible_stats = json_data["stats"]["visible"]

        # This is really just debug info, if there are no planes going overhead, how do we know if the query is working?
        print(f"Time: { str(datetime.now())}\nFull Count: {full_count}")
        # print(f"Total Stats: {total_stats}")
        # print(f"Visible Stats: {visible_stats}")
        # print("-----")

        # Extract flight data
        for flight_key, flight_data in json_data.items():
            if isinstance(flight_data, list):
                flight_icao = flight_key

                if not have_seen_recently(flight_icao):

                    if flight_data[7] is not None:
                        flight_callsign = flight_data[7]
                    if flight_data[1] is not None:
                        flight_latitude = flight_data[1]
                    if flight_data[2] is not None:
                        flight_longitude = flight_data[2]
                    if flight_data[3] is not None:
                        flight_altitude = flight_data[3]
                    if flight_data[4] is not None:
                        flight_speed = flight_data[4]

                    # again, more debug information
                    # print(f"Flight ICAO: {flight_icao}")
                    # print(f"Callsign: {flight_callsign}")
                    # print(f"Latitude: {flight_latitude}")
                    # print(f"Longitude: {flight_longitude}")
                    # print(f"Altitude: {flight_altitude}")
                    # print(f"Speed: {flight_speed}")
                    # print("-----")

                    # dict to begin building structure to convert to json and send via mqtt
                    data = {
                        "flight_icao": flight_icao,
                        "callsign": flight_callsign,
                        "latitude": flight_latitude,
                        "longitude": flight_longitude,
                        "altitude": flight_altitude,
                        "speed": flight_speed,
                        "time_seen":  str(datetime.now())
                    }

                    # Enriches with additional data about the plane
                    flight_information = extract_flight_information(
                        flight_icao)

                    # add the enriched data to the dict
                    data.update(flight_information)

                    if data['Flight Number'] is not None:

                        # convert to json
                        json_message = json.dumps(data)
                        # Publish the JSON message to the MQTT broker
                        mqtt_client.publish(topic, json_message)

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print(traceback.format_exc())
        # try again after the normal sleep period
        time.sleep(int(SLEEP))

# some very basic caching of planes seen in the past 60 seconds
# this is to manage a slower plane being notified multiple times as it passes over


def have_seen_recently(flight_icao):
    
    current_time = time.time()
    if flight_icao in recent_planes:
        last_seen_time = recent_planes[flight_icao]
        if current_time - last_seen_time < 60:
            print(f"Skipping Plane '{flight_icao}'")
            return True

    recent_planes[flight_icao] = current_time

    # Remove expired planes
    try:
        expired_ids = [key for key, value in recent_planes.items()
                       if current_time - value >= 60]
        for expired_id in expired_ids:
            del recent_planes[expired_id]
    except Exception as e:
        print(f"An error occurred: {str(e)}")

    return False


def main():
    mqtt_client = setup_mqtt()
    while True:
        try:

            check_above_me(mqtt_client)

            # Wait for x seconds before the next query
            time.sleep(int(SLEEP))

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            # try again after the normal sleep period
            time.sleep(int(SLEEP))


if __name__ == "__main__":
    main()
