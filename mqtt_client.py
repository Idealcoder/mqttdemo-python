#!/usr/bin/env python3

import sys
import getopt
import psutil
import json
import paho.mqtt.client as mqtt
import time
import subprocess
import platform
from datetime import datetime

topic_status  = "mqttdemo/status"  #For sending status updates
topic_command = "mqttdemo/command" #For receiving commands
topic_result  = "mqttdemo/result"  #For sending back result of commands

def on_connect(client, userdata, flags, rc):
    print("Connected with code "+str(rc))
    client.subscribe(topic_command)

#Called when message is recieved
def on_message(client, userdata, msg):
    command=json.loads(msg.payload.decode('ascii')) #Convert to ascii then json
    print("Received message : "+command+" on topic : "+str(msg.topic))
    
    #Check command and respond accordingly
    if command == 'ifconfig':
      bashCommand = "ifconfig"
      process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
      output = process.communicate()[0]
      message = "{\"Message\":\""+str(output)+"\"}"
      client.publish(topic_result, message)
      print("Sent ls")
    elif command == 'ls':
      bashCommand = "ls"
      process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
      output = process.communicate()[0]
      message = "{\"Message\":\""+str(output)+"\"}"
      client.publish(topic_result, message)
      print("Sent cd")
    elif command == 'bootTime':
      date = datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M')
      message = json.dumps({"Message":"Booted at "+date})
      client.publish(topic_result, message)
    elif command == 'exit':
        sys.exit(1)
    else:
      message = "{\"Message\":\"I received an unknown command\"}"
      client.publish(topic_result, message)
      print("Sent unknown")

#Called when message succesfully sent
def on_publish(mosq, obj, mid):
    print("Publishing successful")

#Help message to display if arguments are incorrect
def print_usage():
    print("mqtt_example [-h hostname] [-p port] [-v]")

def main(argv):
    host="localhost"
    port=1883
    verbose = False
    clientid = "POHA/"+str(int(time.time()))

    #Process command line arguments
    try:
        opts, args = getopt.getopt(argv, "h:p:v", ["host","port","verbose"])
    except getopt.GetoptError as s:
        print_usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--host"):
            host = arg
        elif opt in ("-p", "--port"):
            port = int(arg)
        elif opt in ("-v", "--verbose"):
            verbose = True

    #Connect to broker
    print("Connecting to "+host+" on port "+str(port));
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish
    client.will_set(topic_command, payload=None, qos=0, retain=False)
    client.username_pw_set("guest", "guest")
    client.connect(host,port,60)
    client.loop()

    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    while client.loop() == 0:
        #Get OS info from psutils
        message = json.dumps({
            "id"      : clientid,
            "hostname": platform.uname()[1],
            "cpu":str(psutil.cpu_percent(interval=1)),
            "memory":psutil.virtual_memory().percent,
            "disk": psutil.disk_usage('/').percent,
            "network":{
                 "sent": psutil.net_io_counters().bytes_sent,
                 "recv": psutil.net_io_counters().bytes_recv},
        },indent=4)

        if verbose:
            print("Sending message :"+str(message))	
       
        #Send message to broker 
        client.publish(topic_status, message)
        time.sleep(0.5)

if __name__ == "__main__":
    main(sys.argv[1:])
