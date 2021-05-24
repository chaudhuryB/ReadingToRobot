import logging
import time
import paho.mqtt.client as mqtt
from builtins import range


class MQTTManager:
    def __init__(self, name, stop_function, process_text_function, timeout, server_ip):
        self.process_text = process_text_function
        self.stop = stop_function
        self.name = name
        self.logger = logging.getLogger(name=__name__)

        # Connection to command server
        self.client = mqtt.Client(self.name)
        self.client.message_callback_add("{}/stop".format(self.name), self.stop_callback)
        self.client.message_callback_add("speech/cmd", self.process_text_callback)
        self.client.on_connect = self.on_connect
        self.client.connect(server_ip)
        self.client.subscribe("{}/stop".format(self.name), 0)
        self.client.subscribe("speech/cmd", 0)
        self.mqtt_timeout = timeout
        self.connected_flag = False

    def start(self):
        # Wait for connection
        try:
            for _ in range(self.mqtt_timeout):
                if self.connected_flag:
                    break
                time.sleep(1)
        except TimeoutError:
            self.logger.error("MQTT connection timed out, exiting.")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected_flag = True
            self.logger.info("Connected to MQTT broker.")
            self.client.publish("{}/started".format(self.name), 1)
        else:
            self.logger.error("Bad connection to mqtt, returned code: {}".format(rc))
            self.client.publish("{}/started".self.name, 0)

    def stop_callback(self, cli, obj, msg):
        self.logger.info("Stop message recieved: {}".format(msg.topic))
        self.stop()
        # Add mqtt response saying we finished.
        self.logger.info("Sending response.")
        self.mqtt_client.publish("nao/stopped_clean", "0")
        time.sleep(1)
        self.mqtt_client.loop_stop()

    def process_text_callback(self, cli, obj, msg):
        self.process_text(msg.payload)
