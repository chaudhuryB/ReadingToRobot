#!/usr/bin/python3
"""
    Server launching a Speech Recognition instance.
"""

import argparse
import logging
import socket
import time

import paho.mqtt.client as mqtt

from readingtorobot.common.continuous_speech import DEFAULT_SAMPLE_RATE
from readingtorobot.common.configuration_loader import load_config_file
from readingtorobot.common.voice_recognition import SpeechReco


class SpeechSender(SpeechReco):
    HOST = socket.gethostbyname(socket.gethostname())

    def __init__(self, config=None, interpreter=None, timeout=20):
        super().__init__(read_game=None, config=config, interpreter=interpreter)

        # Connection to command server
        self.mqtt_client = mqtt.Client("speech")
        self.mqtt_client.message_callback_add("speech/stop", self.stop_callback)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.connect(self.HOST)
        self.mqtt_client.subscribe("speech/stop", 0)
        self.mqtt_timeout = timeout
        self.connected_flag = False

    def start(self):
        self.mqtt_client.loop_start()
        # Wait for connection
        for _ in range(self.mqtt_timeout):
            if self.connected_flag:
                super().start()
                break
            time.sleep(1)
        else:
            self.logger.error("MQTT connection timed out, exiting.")
            self.stop()

    def stop_callback(self, cli, obj, msg):
        self.logger.info("Stop message recieved: {}".format(msg.topic))
        self.running = False

    def send_stopped(self):
        # Add mqtt response saying we finished.
        self.logger.info("Sending response.")
        self.mqtt_client.publish("speech/stopped_clean", "0")
        time.sleep(5)
        self.mqtt_client.loop_stop()
        self.done = True

    def process_text(self, text):
        op = self.book.evaluate_static_sentence_validity(text)
        if op is not None:
            self.mqtt_client.publish("speech/cmd", op)

    def on_connect(self, client, userdata, flags, rc):
        self.connected_flag = True
        self.logger.info("Connected to MQTT broker on host: {}".format(self.HOST))


def main():

    logging.basicConfig(format='%(asctime)s:SpeechService:%(levelname)s:\033[32m%(name)s\033[0m: %(message)s',
                        level=logging.DEBUG)

    parser = argparse.ArgumentParser(description="Stream from microphone to DeepSpeech using VAD")

    parser.add_argument('-v', '--vad_aggressiveness', type=int,
                        help="Set aggressiveness of VAD: an integer between 0 and 3, 0 being the least aggressive about"
                             "filtering out non-speech, 3 the most aggressive. Default: 3")
    parser.add_argument('-c', '--config',
                        help="Path to the configuration file.")
    parser.add_argument('-m', '--model',
                        help="Path to the model (protocol buffer binary file)")
    parser.add_argument('-s', '--scorer',
                        help="Path to the external scorer file.")
    parser.add_argument('-d', '--device', type=int, default=None,
                        help="Device input index (Int) as listed by pyaudio.PyAudio.get_device_info_by_index(). If not"
                        " provided, falls back to PyAudio.get_default_device().")
    parser.add_argument('-r', '--rate', type=int,
                        help="Input device sample rate. Default: {}. Your device may require 44100."
                        .format(DEFAULT_SAMPLE_RATE)
                        )
    parser.add_argument('--hot_words', type=str,
                        help='Hot-words and their boosts.')

    parser.add_argument('--auto-play', action='store_true',
                        help="Plays automatically different audio samples on a loop. If not specified, the model will"
                             "just keep listening to any input.")

    args = parser.parse_args()

    # Load config parameters
    if args.config:
        configuration = load_config_file(args.config)
    else:
        configuration = {}

    # If given explicitly, override configuration parameters
    if args.model:
        configuration['model'] = args.model
    if args.scorer:
        configuration['scorer'] = args.scorer
    if args.vad_aggressiveness:
        configuration['vad_aggressiveness'] = args.vad_aggressiveness
    if args.rate:
        configuration['sample_rate'] = args.rate
    if args.device:
        configuration['device'] = args.device
    if args.hot_words:
        configuration['hot_words'] = {}
        for pair in args.hot_words.split(','):
            word, boost = pair.split(':')
            configuration['hot_words'][word] = boost

    # Create speech recognition object
    speech_reco = SpeechSender(config=args.config)

    try:
        speech_reco.start()
        if speech_reco.is_alive():
            speech_reco.join()

    except KeyboardInterrupt:
        speech_reco.stop()
        logging.info("Stopping, bye!")

    speech_reco.send_stopped()

if __name__ == '__main__':
    main()
