"""
    Client class listening to speech server.

    [Requires Python 2.7 compatibility]
"""

import logging
import select
import socket
import threading
import subprocess

from .configuration_loader import module_file


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
        self.sp = subprocess.Popen(module_file('common/speech_service.py'))

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
                ready = select.select((self.sock,), (), (), 0.5)
                if not ready[0]:
                    continue
                raw_frame, address = self.sock.recvfrom(self.buffer_size)
            except Exception as e:
                self.logger.warning("Failed to receive frame: {}".format(e))
                continue

            self.command_callback(raw_frame.decode('utf-8'))
