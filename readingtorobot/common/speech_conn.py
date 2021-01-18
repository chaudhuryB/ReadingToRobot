"""
    Client class listening to speech server.

    [Requires Python 2.7 compatibility]
"""

import logging
import select
import socket
import subprocess
import threading
import os

from .configuration_loader import module_file
from .feeling_declaration import Feel


class SpeechReceiver(threading.Thread):
    """
        This thread launches a subprocess to process audio data.

        The subprocess takes care of the speech recognition and sends the results via socket to this thread.
        The callback method required for the initialization of this class is used to process the data sent over socket,
        a string representing the expected action.

    """

    HOST = '127.0.0.1'
    PORT = 44111

    def __init__(self, callback):
        super(SpeechReceiver, self).__init__()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.logger = logging.getLogger(__name__)
        self.buffer_size = 1024
        self.running = False
        self.command_callback = callback
        self.sp = subprocess.Popen(module_file(os.path.join('common', 'speech_service.py')))

    def start(self):
        self.running = True
        super(SpeechReceiver, self).start()

    def stop(self):
        self.running = False
        self.sp.terminate()
        self.join()

    def run(self):
        while self.running:
            try:
                if self.sp.poll() is not None:
                    self.running = False
                    continue
                ready = select.select((self.sock,), (), (), 0.5)
                if not ready[0]:
                    continue
                raw_frame, address = self.sock.recvfrom(self.buffer_size)
            except Exception as e:
                self.logger.warning("Failed to receive frame: {}".format(e))
                continue

            self.command_callback(raw_frame.decode('utf-8'))
        self.logger.info('Stopped speech recognition processes.')


class DetachedSpeechReco(SpeechReceiver):
    def __init__(self, read_game):
        super(DetachedSpeechReco, self).__init__(self.process_text)
        self.game = read_game

    def process_text(self, s):
        expression = self.book.evaluate_text(s)
        self.logger.debug("\033[93mRecognized: {}\033[0m".format(s))
        try:
            if expression == "happy":
                self.game.do_feel(Feel.HAPPY)
                self.logger.debug("Feeling {}".format("Happy"))
            elif expression == "sad":
                self.game.do_feel(Feel.SAD)
                self.logger.debug("Feeling {}".format("Sad"))
            elif expression == "groan":
                self.game.do_feel(Feel.ANNOYED)
                self.logger.debug("Feeling {}".format("Groan"))
            elif expression == "excited":
                self.game.do_feel(Feel.EXCITED)
                self.logger.debug("Feeling {}".format("Excited"))
            elif expression == "scared":
                self.game.do_feel(Feel.SCARED)
                self.logger.debug("Feeling {}".format("Scared"))
        except Exception as e:
            self.logger.warning(e)
            pass
