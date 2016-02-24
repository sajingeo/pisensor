#!/usr/bin/env python
""" 
Sensory.py this is a drivative of Fauxmo.py, example-minimal.py
This emulates a weemo device on the network and also pushes sensor data to Adafruit IO.
The weemo device name can be set in the script and the can be found by an amazon echo.
"""

import fauxmo
import logging
import time
import RPi.GPIO as GPIO
import random
import sys
import time
import Adafruit_DHT
import RPi.GPIO as GPIO
from twilio.rest import TwilioRestClient
from debounce_handler import debounce_handler

GPIO.cleanup()
GPIO.setmode(GPIO.BCM)
GPIO.setup(10, GPIO.IN)
GPIO.setup(9,GPIO.OUT)
runOnce = 0
securityEnable = 'OFF'

# Import Adafruit IO MQTT client.
from Adafruit_IO import MQTTClient
from Adafruit_IO import Client

# Set to your Adafruit IO key & username below.
ADAFRUIT_IO_KEY      = 'XXXXXXXXXXXXXXXXXXXXXXXXXX'
ADAFRUIT_IO_USERNAME = 'sXXXXXXo'  # See https://accounts.adafruit.com
account_sid = "XXXXXXXXXXXXXXXXX"
auth_token  = "XXXXXXXXXXXXXXXXXXX"
# to find your username.

GPIO.output(9, GPIO.LOW) #make sure you dont start the car

def presenseHandle(channel):
    # print 'presense detected!!'
    client.publish('Presense',100)
    securityEnable = restClient.receive('Security')
    if (securityEnable.value == 'ON'):
        #print 'Send Alarm' ## you can add your notification here TWILLIO/ GMAIL etc
        SMSclient = TwilioRestClient(account_sid, auth_token)
        message = SMSclient.messages.create(body="Motion Detected!!!",to="+15857667935",from_="+19783194030")

# Define callback functions which will be called when certain events happen.
def connected(client):
    # Connected function will be called when the client is connected to Adafruit IO.
    # This is a good place to subscribe to feed changes.  The client parameter
    # passed to this function is the Adafruit IO MQTT client so you can make
    # calls against it easily.
    print 'Connected to Adafruit IO!  Listening for DemoFeed changes...'
    # Subscribe to changes on a feed named DemoFeed.
    # client.subscribe('Security')

def disconnected(client):
    # Disconnected function will be called when the client disconnects.
    print 'Disconnected from Adafruit IO!'
    sys.exit(1)

def message(client, feed_id, payload):
    # Message function will be called when a subscribed feed has a new value.
    # The feed_id parameter identifies the feed, and the payload parameter has
    # the new value.
    print 'Feed {0} received new value: {1}'.format(feed_id, payload)

logging.basicConfig(level=logging.CRITICAL)

class device_handler(debounce_handler):
    """Publishes the on/off state requested,
       and the IP address of the Echo making the request.
    """
    TRIGGERS = {"My Car": 52000}

    def act(self, client_address, state):
        print "State", state, "from client @", client_address
        if(state):
            print "turning car ON"
            GPIO.output(9,GPIO.HIGH)
            time.sleep(4)
            
        GPIO.output(9,GPIO.LOW)
        return True

if __name__ == "__main__":
    # Startup the fauxmo server
    fauxmo.DEBUG = True
    timeout = 0
    p = fauxmo.poller()
    u = fauxmo.upnp_broadcast_responder()
    u.init_socket()
    p.add(u)

    # Register the device callback as a fauxmo handler
    d = device_handler()
    for trig, port in d.TRIGGERS.items():
        fauxmo.fauxmo(trig, u, p, None, port, d)

    # Loop and poll for incoming Echo requests
    logging.debug("Entering fauxmo polling loop")
    client=MQTTClient(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)
    restClient = Client(ADAFRUIT_IO_KEY)

    # Setup the callback functions defined above.
    client.on_connect=connected
    client.on_disconnect=disconnected
    client.on_message=message

    # Connect to the Adafruit IO server.
    client.connect()

    while True:
        try:
            # Allow time for a ctrl-c to stop the process
            p.poll(100)
            if(runOnce == 0):
                runOnce = 1
                GPIO.add_event_detect(10, GPIO.RISING, callback=presenseHandle,bouncetime=10000)
            timeout = timeout + 1
            if (timeout >= 100):
                timeout = 0
                humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11,4)
                if humidity is not None and temperature is not None:
                    # print 'Humi:'+str(humidity)+'Tmp:'+str(temperature)
                    client.publish('Temp', temperature)
                    client.publish('Humidity', humidity)
                    client.publish('Presense',0)
            time.sleep(0.1)
        except Exception, e:
            logging.critical("Critical exception: " + str(e))
            break
