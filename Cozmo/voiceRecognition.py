import speech_recognition as sr
import threading
import time
from constants import (NEUTRAL,
                        HAPPY,
                        SAD,
                        ANNOYED,
                        SCARED,
                        EXCITED)

wordlist = {
    'happy': 'teeny green stem peeping out pot'.split(' '),
    'happy': 'happy day second week'.split(' '),
    'happy': 'keep them wet and wait'.split(' '),
    'groan': 'very long week sat there'.split(' '),
    'groan': 'there was no tree seen'.split(' '),
    'groan': 'this is silly'.split(' '),
    'excited': 'Molly saw leaf'.split(' '),
    'excited': 'peeping out pot'.split(' '),
    'excited': 'yippee have tree'.split(' '),
    'sad': 'Molly was very sad'.split(' '),
    'scared': 'Molly was scared'.split(' ')}


def evaluate_text(text):
    expression = None
    bestmatch = 3
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
#class Human_Listener():
    def __init__(self,
                 robot_proxy,
                 read_game):
        threading.Thread.__init__(self)
        self.robot_proxy = robot_proxy
        self.game = read_game
        self.game_on = False
        self.not_understood_count = 0
        self.reaction_delay = 1

    def run(self):
        r = sr.Recognizer()
        self.game_on = True
        with sr.Microphone() as source:
            print("Say something!")
            while self.game_on:
                audio = r.listen(source, timeout=1, phrase_time_limit=5)
                # recognize speech using Sphinx
                try:
                    toText = r.recognize_google(audio)  # google to do it online. It ismore accurate
                    #toText = r.recognize_sphinx(audio)  # Spinx to do it offline
                    print(toText)
                    expression = evaluate_text(toText)
                    if expression == "happy":
                        self.game.feel=HAPPY
                        print("HAPPY")
                        time.sleep(self.reaction_delay)
                    elif expression == "sad":
                        self.game.feel=SAD
                        print("SAD")
                        time.sleep(self.reaction_delay)
                    elif expression == "groan":
                        self.game.feel=ANNOYED
                        print("ANNOYED")
                        time.sleep(self.reaction_delay)
                    elif expression == "excited":
                        self.game.feel=EXCITED
                        print("EXCITED")
                        time.sleep(self.reaction_delay)
                    elif expression == "scared":
                        self.game.feel=SCARED
                        print("SCARED")
                        time.sleep(self.reaction_delay)
                    else:
                        self.game.feel=NEUTRAL
                    self.not_understood_count = 0

                except sr.UnknownValueError:
                    print("Sphinx could not understand audio")
                    self.not_understood_count += 1
                    if self.not_understood_count >= 120:
                        self.game_on = False
                        self.game.feel = SLEEPY
                except sr.RequestError as e:
                    print("Sphinx error; {0}".format(e))

