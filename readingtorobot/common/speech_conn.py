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

    HOST = socket.gethostbyname(socket.gethostname())
    PORT = 44111

    def __init__(self, callback, launch_speech=False, hostname=None, port=None):
        super(SpeechReceiver, self).__init__()

        self.logger = logging.getLogger(__name__)
        self.buffer_size = 1024
        self.running = False
        self.command_callback = callback
        self.launch_speech = launch_speech
        if hostname is not None:
            self.HOST = hostname
        if port is not None:
            self.PORT = port

    def start(self):
        self.ser_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ser_sock.bind((self.HOST, self.PORT))

        if launch_speech:
            mf = module_file(os.path.join('common', 'speech_service.py'))
            self.sp = subprocess.Popen(mf)
        else:
            self.sp = None
        self.sock = None

        self.running = True
        super(SpeechReceiver, self).start()

    def stop(self):
        self.running = False
        if self.sp is not None and self.sp.poll() is None:
            self.sp.terminate()
        self.join()

    def run(self):
        while self.running:
            try:
                if self.sock is None:
                    self.ser_sock.listen(2)
                    self.sock, _ = self.ser_sock.accept()
                if self.sp is not None and self.sp.poll() is not None:
                    self.running = False
                    continue
                cli_sock, cli_add = self.sock.accept()
                ready = select.select((self.sock,), (), (), 0.5)
                if not ready[0]:
                    continue
                raw_frame, address = self.sock.recvfrom(self.buffer_size)
            except KeyboardInterrupt:
                self.running = False
                raise
            except Exception as e:
                self.logger.warning("Failed to receive frame: {}".format(e))
                continue

            msg = raw_frame.decode('utf-8')
            self.logger.info('Recieved message: {}'.format(msg))
            self.command_callback(msg)

        self.logger.info('Stopped speech recognition processes.')


class DetachedSpeechReco(SpeechReceiver):
    def __init__(self, read_game, *args, **kwargs):
        super(DetachedSpeechReco, self).__init__(self.process_text, *args, **kwargs)
        self.game = read_game

    def process_text(self, s):
        self.logger.debug("\033[93mRecognized: {}\033[0m".format(s))
        try:
            if s == "happy":
                self.game.do_feel(Feel.HAPPY)
                self.logger.debug("Feeling {}".format("Happy"))
            elif s == "sad":
                self.game.do_feel(Feel.SAD)
                self.logger.debug("Feeling {}".format("Sad"))
            elif s == "groan":
                self.game.do_feel(Feel.ANNOYED)
                self.logger.debug("Feeling {}".format("Groan"))
            elif s == "excited":
                self.game.do_feel(Feel.EXCITED)
                self.logger.debug("Feeling {}".format("Excited"))
            elif s == "scared":
                self.game.do_feel(Feel.SCARED)
                self.logger.debug("Feeling {}".format("Scared"))
        except Exception as e:
            self.logger.warning(e)
            pass
