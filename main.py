from datetime import datetime
import sched, time
import requests
from paho.mqtt import client as mqtt_client
import os

s = sched.scheduler(time.time, time.sleep)

start_time = datetime.today().replace(hour=1, minute=0, second=0, microsecond=0)
end_time = datetime.today().replace(hour=23, minute=55, second=0, microsecond=0)

target = str(os.getenv('URL'))
delay = int(os.getenv(key='DELAY', default=60))
authToken = str(os.getenv('APIKEY'))
work_load = float(os.getenv("WORK_LOAD"))

urlTemplate = target + "/timetagger/api/v2/records?timerange={}-{}"

url = urlTemplate.format(int(start_time.timestamp()),int(end_time.timestamp()))

time = 0
def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if(rc == 0):
            print("Connected to MQTT Broker")
        else:
            print("Failed to connect, return code %d\n", rc)
    client = mqtt_client.Client("TimeTaggerConnection")
    client.on_connect = on_connect
    client.will_set("timetagger/status", payload="offline")
    client.connect("192.168.2.2", 1883)
    return client

mqtt_client_connection = connect_mqtt()
mqtt_client_connection.publish("timetagger/status", "online")

def callAPI(sc):
    response = requests.get(url=url, headers={"authtoken":authToken})
    data = response.json()
    time = 0
    for record in data['records']:
        if record['t1'] != record['t2']:
            duration = record['t2'] - record['t1']
            time += duration / 60 / 60
        else:
            duration = datetime.now().timestamp() - record['t1']
            time += duration / 60 / 60
    print("Todays time: " + str(time))
    mqtt_client_connection.publish("timetagger/total", time)
    
    mqtt_client_connection.publish("timetagger/percent", round(100 / 5.5 * time, 2))
    s.enter(delay, 1, callAPI, (sc,))


s.enter(delay, 1, callAPI, (s,))
s.run()