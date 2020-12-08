import threading
import time
import numpy as np

from ..common.feeling_declaration import Feel
from ..common.deepspeech_module import load_model, load_vad
from ..common.configuration_loader import load_config_file

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


# obtain audio from the microphone
class SpeechReco(threading.Thread):
    def __init__(self,
                 robot_proxy,
                 read_game) -> None:
        threading.Thread.__init__(self)
        self.robot_proxy = robot_proxy
        self.game = read_game
        self.game_on = False
        self.not_understood_count = 0
        self.reaction_delay = 1
        cf = load_config_file("ds_config.json")
        self.ds = load_model(cf)
        self.audio_proc = load_vad(cf)

    def emotion_from_string(self, s: str) -> None:
        expression = evaluate_text(s)
        if expression == "happy":
            self.game.feel = Feel.HAPPY
            print("HAPPY")
            time.sleep(self.reaction_delay)
        elif expression == "sad":
            self.game.feel = Feel.SAD
            print("SAD")
            time.sleep(self.reaction_delay)
        elif expression == "groan":
            self.game.feel = Feel.ANNOYED
            print("ANNOYED")
            time.sleep(self.reaction_delay)
        elif expression == "excited":
            self.game.feel = Feel.EXCITED
            print("EXCITED")
            time.sleep(self.reaction_delay)
        elif expression == "scared":
            self.game.feel = Feel.SCARED
            print("SCARED")
            time.sleep(self.reaction_delay)
        else:
            self.game.feel = Feel.NEUTRAL

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

                # Start stream and timer
                stream = self.ds.createStream()

                for frame in frames:
                    stream.feedAudioContent(np.frombuffer(frame, np.int16))
                text = stream.finishStream()
                stream = self.ds.createStream()
                if text:
                    self.emotion_from_string(text)
                last_step_time = time.perf_counter()
            self.audio_proc.stop()
        except Exception as e:
            self.audio_proc.stop()
            raise e
