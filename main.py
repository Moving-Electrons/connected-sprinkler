import network
import machine
import ujson
import sys
from umqtt.simple import MQTTClient
import ubinascii
import time

# Reading configuration file
try:
    with open("config.json") as file:
        print("Loading config.json...")
        config = ujson.loads(file.read())
        print("Done.")
except (OSError, ValueError):
    print("Couldn't load config.json")
    sys.exit(0)

# GPIO configuration:
relay_set = machine.Pin(13, machine.Pin.OUT, value=0)
relay_unset = machine.Pin(14, machine.Pin.OUT, value=0)


def wifi_connect():
    global config

    led_red = machine.Pin(0, machine.Pin.OUT, value=1)
    led_red.value(0) #turns on red LED.
    sta_if = network.WLAN(network.STA_IF)
    ap_if = network.WLAN(network.AP_IF)

	# disabling access point mode
    if ap_if.active():
        ap_if.active(False)

    if not sta_if.isconnected():
        print('connecting to network...')

        sta_if.active(True)
        sta_if.connect(config["ESSID"], config["PASSWD"])
        while not sta_if.isconnected():
            pass

    led_red.value(1)
    print('Network Configuration:', sta_if.ifconfig())

def mqtt_connect():
    global config
    print('Setting up MQTT client...')

    CLIENT_ID = b"Huzzah-"+ubinascii.hexlify(machine.unique_id())
    c = MQTTClient(CLIENT_ID, config["MQTT_Broker"])

    # Subscribed messages will be delivered to this callback
    c.set_callback(sub_callback)
    c.connect()
    c.subscribe(config["TOPIC"])
    print("Connected to {}, subscribed to {} topic.".format(config["MQTT_Broker"], config["TOPIC"]))

    while True:
    	c.wait_msg()
        #c.check_msg()

    c.disconnect()

def sub_callback(topic, msg):

    global config
    if msg == b"on":

        print("Message is on.\nActivating Sprinkler for {} seconds.".format(config["DURATION"]))
        #Sets relay through 20ms pulse.
        relay_set.value(1)
        time.sleep(0.2)
        relay_set.value(0)
        time.sleep(config["DURATION"])
        # Unsets relay through 20ms pulse.
        relay_unset.value(1)
        time.sleep(0.2)
        relay_unset.value(0)

    elif msg == b"off":
        print("message is off")
        # Unsetting relay (in case it wasn't unset at end of "on" state.)
        relay_unset.value(1)
        time.sleep(0.2)
        relay_unset.value(0)

if __name__ == '__main__':

    wifi_connect()
    mqtt_connect()
