"""
    Methods used in the interpretation of detected speech to trigger robot actions.
"""

import logging
import time
import numpy as np
import speech_recognition as sr
from threading import Thread

from .feeling_declaration import Feel
from .deepspeech_module import load_deepspeech_model, ContinuousSpeech
from .configuration_loader import load_config_file, resource_file
from .book_reactions import Book


class SpeechReco(Thread):
    """
        Speech recognition module, using DeepSpeech or Google Cloud Speech API (through the speech_recognition module).

        Interpreter options:
        - 'ds' : DeepSpeech (default)
        - 'gc' : Google Cloud Speech API
    """
    def __init__(self,
                 read_game,
                 config=None,
                 interpreter=None) -> None:
        super().__init__()
        self.name = 'SpeechRecognition'
        self.game = read_game
        self.running = False
        self.not_understood_count = 0
        self.reaction_delay = 1
        if config is None:
            config = resource_file("ds_config.json")

        cf = load_config_file(config)
        if interpreter is None:
            interpreter = cf.get('interpreter', 'ds')

        self.audio_proc = ContinuousSpeech.from_json(cf)
        self.ds = load_deepspeech_model(cf) if interpreter == 'ds' else sr.Recognizer()

        self.book = Book("the_teeny_tree_literal.txt")

        self.logger = logging.getLogger(name=__name__)

    def start(self):
        self.running = True
        super().start()

    def stop(self):
        self.running = False
        self.join()

    def process_text(self, s: str) -> None:
        expression = self.book.evaluate_text(s)
        self.logger.debug("\033[93mRecognized: {}\033[0m".format(s))
        try:
            if expression == "happy":
                self.game.do_feel(Feel.HAPPY)
                self.logger.debug("Feeling {}".format("Happy"))
                self.audio_proc.clear_audio()
                time.sleep(self.reaction_delay)
            elif expression == "sad":
                self.game.do_feel(Feel.SAD)
                self.logger.debug("Feeling {}".format("Sad"))
                self.audio_proc.clear_audio()
                time.sleep(self.reaction_delay)
            elif expression == "groan":
                self.game.do_feel(Feel.ANNOYED)
                self.logger.debug("Feeling {}".format("Groan"))
                self.audio_proc.clear_audio()
                time.sleep(self.reaction_delay)
            elif expression == "excited":
                self.game.do_feel(Feel.EXCITED)
                self.logger.debug("Feeling {}".format("Excited"))
                self.audio_proc.clear_audio()
                time.sleep(self.reaction_delay)
            elif expression == "scared":
                self.game.do_feel(Feel.SCARED)
                self.logger.debug("Feeling {}".format("Scared"))
                self.audio_proc.clear_audio()
                time.sleep(self.reaction_delay)
        except Exception as e:
            self.logger.warning(e)
            pass

    def run(self):
        self.logger.info("Say something!")
        try:
            self.audio_proc.start()
            last_step_time = time.perf_counter()
            while self.running:
                while time.perf_counter() - last_step_time < self.audio_proc.wait_time:
                    time.sleep(0.01)
                # Get audio track
                frames = self.audio_proc.get_audio(time.perf_counter() - last_step_time)
                last_step_time = time.perf_counter()

                if isinstance(self.ds, sr.Recognizer):
                    audio = self.audio_proc.frames_to_SR(frames)
                    query = self.ds.recognize_google(audio, show_all=True)
                    if query:
                        if "confidence" in query["alternative"]:
                            # return alternative with highest confidence score
                            best_hypothesis = max(query["alternative"],
                                                  key=lambda alternative: alternative["confidence"])
                        else:
                            # when there is no confidence available, we arbitrarily choose the first hypothesis.
                            best_hypothesis = query["alternative"][0]
                        text = best_hypothesis["transcript"]
                    else:
                        text = ''
                else:
                    # Start stream
                    stream = self.ds.createStream()

                    for frame in frames:
                        stream.feedAudioContent(np.frombuffer(frame, np.int16))
                    text = stream.finishStream()

                if text:
                    self.process_text(text)

            self.audio_proc.stop()
        except Exception as e:
            self.audio_proc.stop()
            raise e
