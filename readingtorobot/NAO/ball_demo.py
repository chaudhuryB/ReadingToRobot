#!/usr/bin/python2
import argparse
import qi
import sys
import time
import threading

from readingtorobot.NAO.nao_base import NAOBase
from readingtorobot.NAO.nao_expression import hand_hold_ball, stand_hand_fwd, point_forward, explain, wave, open_hand

class BallDemo(NAOBase):
    def run(self):
        self.running = True
        self.posture.goToPosture('Crouch', 2.0)
        self.movement.setStiffnesses("Body", 1.0)

        # Sit and hold hand
        self.do_action(*hand_hold_ball())
        self.do_action(*stand_hand_fwd())

        # Walking motion
        self.movement.setMoveArmsEnabled( True, False )
        self.movement.moveToward(1, 0, 0)
        time.sleep(3)
        self.do_action(*open_hand())
        time.sleep(1.5)
        # Drop ball
        self.movement.stopMove()
        self.posture.goToPosture('Stand', 2.0)

        t = threading.Thread(target=self.tts.say, args=["Oh!"])
        t.start()
        self.do_action(*point_forward())
        t.join()

        t = threading.Thread(target=self.tts.say, args=["We dropped the ball!"])
        t.start()
        self.do_action(*explain())
        t.join()
        time.sleep(3)

class ByeForNow(NAOBase):
    def run(self):
        self.running = True
        self.movement.wakeUp()
        self.movement.setStiffnesses("Body", 1.0)

        t = threading.Thread(target=self.tts.say, args=["Bye for now!"])
        t.start()
        self.do_action(*wave())
        t.join()

        time.sleep(3)

def play_ball_demo():

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int,  default="9559",
                        help="Needed for connecting to virtual Choregraphe Nao")
    parser.add_argument("--robotIP", type=str,  default="127.0.0.1",
                        help="IP address of the robot, use 'localhost' for virtual Nao in" \
                        "Choregraphe")

    parser.add_argument("-a", type=str,  default="ball",
                        help="Animation options: 'ball' or 'hi'")

    args = parser.parse_args()

    try:
        # Initialize qi framework.
        connection_url = "tcp://" + args.robotIP + ":" + str(args.port)
        app = qi.Application(["HumanListener", "--qi-url=" + connection_url])
    except RuntimeError:
        print ("Can't connect to Naoqi at ip \"" + args.robotIP + "\" on port " + str(args.port) +".\n"
               "Please check your script arguments. Run with -h option for help.")
        sys.exit(1)

    manager = ByeForNow(app) if args.a == 'hi' else BallDemo(app)
    # Keep robot running
    try:
        manager.run()
    except KeyboardInterrupt:
        print "\nInterrupted by user, shutting down"
        raise
    except BaseException, err:
        print err
        raise
    finally:
        manager.stop()
        sys.exit(0)

if __name__ == '__main__':
    play_ball_demo()
