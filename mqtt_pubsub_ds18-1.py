#!/usr/bin/python3
import os
import glob
import signal
import logging
import threading
import time
from datetime import datetime
from datetime import timedelta
from queue import Queue, Empty
import paho.mqtt.client as mqttClient

# Global variables
Exiting = False # to force exit from the dequeue Thread
mqConnected = False # global variable for the state of the broker connection
broker_address= "mosquitto.hive.com"  # Broker address
user = "xxxxxxxxx" # Connection username
password = "xxxxxxxx" # Connection password
clientid = "raspberry3" # identificator for the MQTT client
announcementTopic = "announcement/clientid" #
dataTopic1 = "it/xxxxxx/out/sens/tempdallas1"
dataTopic2 = "it/xxxxxx/out/sens/tempdallas2"
cmdTopic =   "it/xxxxxx/cmds/reading"
sigTopic =   "it/xxxxxx/out/reading"
mpipeline = Queue(maxsize=100) # max queue elements
timeLap = timedelta(minutes=10,seconds=0) # days,seconds,microseconds,milliseconds,minutes,hours,week
lastRead = datetime.now()
base_dir = '/sys/bus/w1/devices/'
# End of Global Variables


def main():
  global mqConnected
  global Exiting
  global lastRead
  global timeLap
  global client
  
  formatstr = "%(asctime)s: %(message)s"
  signal.signal(signal.SIGTERM, receiveSignal)
  logging.basicConfig(format=formatstr, level=logging.INFO,
                      datefmt="%H:%M:%S")
  client = mqttClient.Client(clientid) #create new instance
  client.username_pw_set(user, password) #set username and password
  client.on_connect= on_connect #attach function to callback
  client.on_message= on_message #attach function to callback
  client.connect(broker_address) #connect to broker
  client.loop_start()        #start the loop
  
  logging.debug("Connecting")
  while mqConnected != True:    #Wait for connection
    logging.debug("Still connecting")
    time.sleep(0.1)
  dQt = threading.Thread(target=dequeueMessage)
  dQt.start()
  
  try:
    while True:
      if (((datetime.now() - lastRead)) > timeLap):
        # inserire qui la richiesta nella coda
        ## print("Ci siamo")
        logging.debug("Diff: " + str(datetime.now() - lastRead))
        lastRead = datetime.now()
        mpipeline.put("READNOW")
      time.sleep(0.2)
  except KeyboardInterrupt:
  #Exit point
    logging.info ("exiting")
    Exiting = True
    client.disconnect()
    client.loop_stop()
    ## DBdisconnect()
# end of main()


def receiveSignal(signalNumber, frame):
  logging.info('Received:' + str(signalNumber))
  raise KeyboardInterrupt # to use the same handler
  return
# receiveSignal


def on_connect(client, userdata, flags, rc):
  global mqConnected #Use global variable
  global topics
  
  if rc == 0:
    logging.info("Connected to broker")
    client.publish(announcementTopic, "Hello here " + clientid)
    logging.info("Subscribing " + cmdTopic)
    client.subscribe(cmdTopic)
    mqConnected = True   #Signal connection         
  else:
    logging.error("Connection failed")
# end of on_connect()


def on_message(client, userdata, message):
  logging.debug("Received message")
  mMt = threading.Thread(target=enqueueMessage, args=(userdata, message,))
  mMt.start()
  # queueMessage(userdata, message)
# end of on_message()
 

def enqueueMessage(userdata, message):
  global mpipeline
  
  try:
    logging.debug("In enqueueMessage")
    if ((message.topic == cmdTopic) and
        (str(message.payload, "utf-8") == "READNOW")):
      logging.debug ("*d*Topic     : " + str(message.topic))
      logging.debug ("*d*  Message : " + str(message.payload, "utf-8"))
      lastRead = datetime.now()
      mpipeline.put("READNOW")
  except Exception as e:
    logging.error(e)  
# end of enqueueMessage()


def dequeueMessage():
  global Exiting
  global mpipeline
  
  logging.debug("In dequeueMessage")
  while ((not Exiting) or (mpipeline.qsize()>0)):
    # Pausa 
    time.sleep(1)
    logging.debug("Waiting for message")
    try:
      tte = mpipeline.get(timeout=1) # after 1 sec raises an Empty exception
      logging.debug("Got q element")
      logging.debug(tte)
      readTemp()
    except Empty:
      pass
    except Exception as e:
      logging.error(e)
# end of dequeueMessage()


def readTemp():
  global client
  
  logging.debug("Reading temp")
  client.publish(sigTopic, "READINGON")
  client.publish(dataTopic1,"{0:.1f}".format(read_temp(0)));
  client.publish(dataTopic2,"{0:.1f}".format(read_temp(1)));
  client.publish(sigTopic, "READINGOFF")
# end of readTemp()


def read_temp_raw(devicenum):
  device_folder = glob.glob(base_dir + '28*')[devicenum]
  device_file = device_folder + '/w1_slave'
  f = open(device_file, 'r')
  lines = f.readlines()
  f.close()
  return lines
# end of read_temp_raw


def read_temp(devicenum):
  os.system('modprobe w1-gpio')
  os.system('modprobe w1-therm')
 
  lines = read_temp_raw(devicenum)
  while lines[0].strip()[-3:] != 'YES':
    #print("ciclo1")
    time.sleep(0.2)
    lines = read_temp_raw(devicenum)
  equals_pos = lines[1].find('t=')
  if equals_pos != -1:
    temp_string = lines[1][equals_pos+2:]
    temp_c = float(temp_string) / 1000.0
    # temp_f = temp_c * 9.0 / 5.0 + 32.0
    return temp_c #, temp_f
# end of read_temp


if __name__ == "__main__":
  main()
