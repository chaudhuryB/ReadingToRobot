"""
Communication manager using the MQTT protocol.

[Requires Python 2.7 compatibility]
"""

import logging
import time
from builtins import range

import paho.mqtt.client as mqtt


class MQTTManager:
    """Manager for MQTT communication between processes of the application."""

    def __init__(self, name, stop_function, process_text_function=None, timeout=20, server_ip=None):
        """Initialize MQTT Manager.

        :param name: Identifier for this MQTT client.
        :type name: str
        :param stop_function: Method to be executed when the 'stop' command is received.
        :type stop_function: Callable
        :param process_text_function: Method to be executed when the 'speech/cmd' command is received.
        :type process_text_function: Optional[Callable]
        :param timeout: MQTT connection timeout.
        :type timeout: int
        :param server_ip: Ip of the MQTT server. When not specified, localhost is used.
        :type server_ip: Optional[str]
        """
        self._process_text = process_text_function or (lambda _: None)
        self._stop = stop_function
        self._name = name
        self._logger = logging.getLogger(name=__name__)

        # Connection to command server
        self._client = mqtt.Client(self._name)
        self._client.message_callback_add("{}/stop".format(self._name), self._stop_callback)
        self._client.message_callback_add("speech/cmd", self._process_text_callback)
        self._client.on_connect = self._on_connect
        self._client.connect(server_ip or "localhost")
        self._client.subscribe("{}/stop".format(self._name), 0)
        self._client.subscribe("speech/cmd", 0)
        self._mqtt_timeout = timeout
        self._connected_flag = False

    def start(self):
        """Wait for connection to MQTT server."""
        self._client.loop_start()
        try:
            for _ in range(self._mqtt_timeout):
                if self._connected_flag:
                    break
                time.sleep(1)
        except TimeoutError:
            self._logger.error("MQTT connection timed out, exiting.")
            raise

    def publish(self, *args, **kwargs):
        """Publish message on mqtt topic."""
        self._client.publish(*args, **kwargs)

    def _on_connect(self, client, userdata, flags, rc):
        """Detect connection to MQTT server.

        See documentation in the Paho MQTT package for 'Client.on_connect'.

        :param client: Unused.
        :param userdata: Unused.
        :Param flags: Unused.
        :param rc: The connection result.
        :type rc: int
        """
        # Delete unaccessed variables.
        del client, userdata, flags
        if rc == 0:
            self._connected_flag = True
            self._logger.info("Connected to MQTT broker.")
            self._client.publish("{}/started".format(self._name), 1)
        else:
            self._logger.error("Bad connection to mqtt, returned code: {}".format(rc))
            self._client.publish("{}/started".format(self._name), 0)

    def _stop_callback(self, cli, obj, msg):
        """Run stop function and send success response when finished.

        :param cli: Unused.
        :param obj: Unused.
        :param msg: Message recieved in topic.
        :type msg: Dict|Tuple
        """
        # Delete unaccessed variables.
        del cli, obj
        self._logger.info("Stop message recieved: {}".format(msg.topic))
        self._stop()
        # Add mqtt response saying we finished.
        self._logger.info("Sending response.")
        self._client.publish("nao/stopped_clean", "0")
        time.sleep(1)
        self._client.loop_stop()

    def _process_text_callback(self, cli, obj, msg):
        """Run process text function on msg recieved.

        :param cli: Unused.
        :param obj: Unused.
        :param msg: Message recieved in topic.
        :type msg: Dict|Tuple
        """
        # Delete unaccessed variables
        del cli, obj
        self._process_text(msg.payload.decode("ascii"))
