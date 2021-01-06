import os
import time
import threading
import numpy as np
import speech_recognition as sr

from .feeling_declaration import Feel
from .deepspeech_module import load_deepspeech_model, ContinuousSpeech
from .configuration_loader import load_config_file


wordlist = {
    'happy': "teeny green stem peeping out pot".split(' ') + "happy day second week".split(' ') +
             "keep them wet and wait".split(' '),
    'groan': "very long week sat there".split(' ') + "there was no tree seen".split(' ') + "this is silly".split(' '),
    'excited': "Molly saw leaf".split(' ') + "peeping out pot".split(' ') + "yippee have tree".split(' '),
    'sad': 'Molly was very sad'.split(' '),
    'scared': 'Molly was scared'.split(' ')
    }


def evaluate_text(text):
    expression = None
    bestmatch = 3
    global wordlist

    for em in wordlist:
        matches = 0
        for word in wordlist[em]:
            if word in text:
                matches += 1
        if matches >= bestmatch:
            expression = em
            bestmatch = matches
    return expression


class SpeechReco(threading.Thread):
    """
        Speech recognition module, using DeepSpeech or Google Cloud Speech API (through the speech_recognition module).

        Interpreter options:
        - 'ds' : DeepSpeech (default)
        - 'gc' : Google Cloud Speech API
    """
    def __init__(self,
                 robot_proxy,
                 read_game,
                 config=None,
                 interpreter=None) -> None:
        threading.Thread.__init__(self)
        self.robot_proxy = robot_proxy
        self.game = read_game
        self.game_on = False
        self.not_understood_count = 0
        self.reaction_delay = 1
        if config is None:
            config = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                  "resources/ds_config.json")

        cf = load_config_file(config)
        if interpreter is None:
            interpreter = cf.get('interpreter', 'ds')

        self.audio_proc = ContinuousSpeech.from_json(cf)
        self.ds = load_deepspeech_model(cf) if interpreter == 'ds' else sr.Recognizer()
        print('Finished audio initialization')

    def emotion_from_string(self, s: str) -> None:
        expression = evaluate_text(s)
        if expression == "happy":
            self.game.do_feel(Feel.HAPPY)
            print("HAPPY")
            self.audio_proc.clear_audio()
            time.sleep(self.reaction_delay)
        elif expression == "sad":
            self.game.do_feel(Feel.SAD)
            print("SAD")
            self.audio_proc.clear_audio()
            time.sleep(self.reaction_delay)
        elif expression == "groan":
            self.game.do_feel(Feel.ANNOYED)
            print("ANNOYED")
            self.audio_proc.clear_audio()
            time.sleep(self.reaction_delay)
        elif expression == "excited":
            self.game.do_feel(Feel.EXCITED)
            print("EXCITED")
            self.audio_proc.clear_audio()
            time.sleep(self.reaction_delay)
        elif expression == "scared":
            self.game.do_feel(Feel.SCARED)
            print("SCARED")
            self.audio_proc.clear_audio()
            time.sleep(self.reaction_delay)

    def stop(self):
        self.game_on = False
        self.join()

    def run(self):
        self.game_on = True
        print("Say something!")
        try:
            self.audio_proc.start()
            last_step_time = time.perf_counter()
            while self.game_on:
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
                    self.emotion_from_string(text)

            self.audio_proc.stop()
        except Exception as e:
            self.audio_proc.stop()
            raise e
