"""Methods used in the interpretation of detected speech to trigger robot actions."""

import logging
import time
from typing import Optional
import numpy as np
import speech_recognition as sr
from threading import Thread

from .continuous_speech import ContinuousSpeech
from .configuration_loader import load_config_file, resource_file
from .book_reactions import Book


class VoiceRecognition(Thread):
    """
    Speech recognition module, using DeepSpeech or Google Cloud Speech API (through the speech_recognition package).

    Interpreter options:
    - 'ds' : DeepSpeech (default)
    - 'gc' : Google Cloud Speech API

    :param name: Name of the thread.
    """

    def __init__(self, config: Optional[str] = None, interpreter: Optional[str] = None) -> None:
        """
        Initialize VoiceRecognition.

        :param config: configuration file path.
        :param interpreter: 'ds' for DeepSpeech or 'gc' for Google Cloud.
        """
        super().__init__()
        self.name = "SpeechRecognition"
        self._running = False
        if config is None:
            config = resource_file("ds_config.json")

        cf = load_config_file(config)
        if interpreter is None:
            interpreter = cf.get("interpreter", "ds")

        self._audio_proc = ContinuousSpeech.from_json(cf)
        if interpreter == "ds":
            from .deepspeech_module import load_deepspeech_model

            self._ds = load_deepspeech_model(cf)
        else:
            self._ds = sr.Recognizer()

        self._book = Book("the_teeny_tree_literal.txt")

        self._logger = logging.getLogger(name=__name__)

    def start(self) -> None:
        """Start thread."""
        self._running = True
        super().start()

    def stop(self) -> None:
        """Stop thread."""
        self._running = False
        if self.is_alive():
            self.join()

    def run(self) -> None:
        """Run in the thread."""
        self._logger.info("Say something!")
        try:
            self._audio_proc.start()
            last_step_time = time.perf_counter()
            while self._running:
                while time.perf_counter() - last_step_time < self._audio_proc.wait_time:
                    time.sleep(0.01)
                # Get audio track
                frames = self._audio_proc.get_audio(int(time.perf_counter() - last_step_time))
                last_step_time = time.perf_counter()

                if isinstance(self._ds, sr.Recognizer):
                    audio = self._audio_proc.frames_to_SR(frames)
                    query = self._ds.recognize_google(audio, show_all=True, language="en-AU")
                    if query:
                        if "confidence" in query["alternative"]:
                            # return alternative with highest confidence score
                            best_hypothesis = max(
                                query["alternative"], key=lambda alternative: alternative["confidence"]
                            )
                        else:
                            # when there is no confidence available, we arbitrarily choose the first hypothesis.
                            best_hypothesis = query["alternative"][0]
                        text = best_hypothesis["transcript"]
                    else:
                        text = ""
                else:
                    # Start stream
                    stream = self._ds.createStream()

                    for frame in frames:
                        stream.feedAudioContent(np.frombuffer(frame, np.int16))
                    text = stream.finishStream()

                if text:
                    self._process_text(text)

            self._audio_proc.stop()
        except Exception as e:
            self._audio_proc.stop()
            raise e

    def _process_text(self, text: str) -> None:
        """Process the given text."""
        del text
