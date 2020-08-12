import speech_recognition as sr
import threading
import time
from constants import (NEUTRAL,
                        HAPPY,
                        SAD,
                        ANNOYED,
                        SCARED,
                        SLEEPY)
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
    
    def run(self):
        r = sr.Recognizer()
        self.game_on = True
        with sr.Microphone() as source:
            print("Say something!")
            while self.game_on:
                audio = r.listen(source, phrase_time_limit=5)
                # recognize speech using Sphinx
                try:
                    #toText = r.recognize_google(audio)  # google to do it online. It ismore accurate
                    toText = r.recognize_sphinx(audio)  # Spinx to do it offline
                    print(toText)
                    if "happy" in toText or "funny" in toText:
                        self.game.feel=HAPPY
                        print("HAPPY")
                        time.sleep(2)
                    elif "sad" in toText:
                        self.game.feel=SAD
                        print("SAD")
                        time.sleep(2)
                    elif "angry" in toText:
                        self.game.feel=ANNOYED
                        print("ANNOYED")
                        time.sleep(2)
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
            
