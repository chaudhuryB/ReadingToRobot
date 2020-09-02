import asyncio
import copy
import cozmo
import time
from cozmo.util import degrees, distance_mm, Pose
from cozmo import event

from asyncio.locks import Lock
from random import randint

from game_cubes import BlinkyCube


cozmo.world.World.light_cube_factory = BlinkyCube

class CozmoPlayerActions(object):
    """
    A singleton class defining how cozmo will act
    """
    
    __instance = None
    
    def __new__(cls):
      if not CozmoPlayerActions.__instance:
          CozmoPlayerActions.__instance = object.__new__(cls)
          CozmoPlayerActions.__instance.robot = None
          CozmoPlayerActions.__instance.face = None
      return  CozmoPlayerActions.__instance
  
    def set_robot(self, game_robot, face):
        self.robot = game_robot
        self.face = face
        
    def be_sad(self):
        sad_anim = ['anim_fistbump_fail_01',
                      'anim_keepaway_losegame_02',
                      'anim_rtpmemorymatch_no_01',
                      'anim_speedtap_playerno_01'                                 
                     ]
        selected_anim = sad_anim[randint(0,3)]
        self.robot.play_anim(selected_anim).wait_for_completed()
        
    def be_happy(self):
        happy_anims =['id_poked_giggle',
                      'anim_reacttoblock_happydetermined_01',
                      'anim_memorymatch_failhand_player_02',
                      'anim_pyramid_reacttocube_happy_low_01',
                      'anim_pyramid_reacttocube_happy_mid_01',
                      'anim_pyramid_reacttocube_happy_high_02']
        selected_anim = happy_anims[randint(0,5)]
        self.robot.play_anim(selected_anim).wait_for_completed()
        
    def be_annoyed(self):
        angry_anim = ['anim_memorymatch_failhand_01',
                             'anim_reacttoblock_frustrated_01',
                             'anim_pyramid_reacttocube_frustrated_low_01',
                             'anim_reacttoblock_frustrated_int2_01']
        
         
        selected_anim = angry_anim[randint(0,3)]
        self.robot.play_anim(selected_anim).wait_for_completed()
        
    def be_scared(self):
        pass
        
    def do_listen(self):
        # Do little look down/up nods:
        play_wait = randint(0,2)
        if play_wait==0:
            print("Looking away")
            wait_anims = ['anim_speedtap_wait_short',
                         'anim_speedtap_wait_medium',
                         'anim_speedtap_wait_medium_02',
                         'anim_speedtap_wait_medium_03',
                         'anim_speedtap_wait_long'
                         ]
            selected_anim = wait_anims[randint(0,4)]
            self.robot.set_head_angle(degrees(0)).wait_for_completed()
            self.robot.play_anim(selected_anim).wait_for_completed()
        else:
            print("Looking at face")
            if self.face:
                # start turning towards the face
                self.robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE).wait_for_completed()
                self.robot.turn_towards_face(self.face).wait_for_completed()
                
            time.sleep(0.5)
            
    def go_to_sleep(self):
        print("That was a vey soothing story. Cozmo has just dozed off")
        self.robot.play_anim(anim_gotosleep_sleeping_01).wait_for_completed()
         
    def start_free_play(self):
        print("What is Cozmo up to?")
        self.robot.start_freeplay_behaviors()
        time.sleep(90)
        self.robot.stop_freeplay_behaviors()
    
    @event.oneshot
    def handle_fist_bump(self, event):
        print( event)
        self.fist_bump_success = True
          
    def do_fist_bump(self):
        print("Fist bump?")
        wait_time = 10.0
        self.fist_bump_success = False
        
        # This event EvtRobotMovedBish was added to the cozmo.world.py in site-packages specifically for this
        # It is dispatched when the world receives the robot delocalized message because that is what "fist bumping"
        # tiny Cozmo does.
        self.robot.add_event_handler(cozmo.world.EvtRobotMovedBish, self.handle_fist_bump)
        self.robot.move_lift(5)
        time.sleep(.2)
        self.robot.play_anim_trigger(cozmo.anim.Triggers.FistBumpRequestOnce).wait_for_completed()
        
        
        while not self.fist_bump_success and wait_time > 0:
            time.sleep(0.5)
            wait_time -= 0.5
        
        if not self.fist_bump_success:
            # No fist bumo yet request again
            wait_time = 10.0
            print("Please fist bump")
            self.robot.play_anim_trigger(cozmo.anim.Triggers.FistBumpRequestRetry).wait_for_completed()
            while not self.fist_bump_success and wait_time > 0:
                time.sleep(0.5)
                wait_time -= 0.5
       
        if self.fist_bump_success:
            print("hehe fist bumped")
            self.robot.move_lift(-3)
            time.sleep(.2)
            self.robot.play_anim_trigger(cozmo.anim.Triggers.FistBumpSuccess).wait_for_completed()
        else:
            print("Cozmo is sad, no fist bump")
            self.robot.move_lift(-3)
            time.sleep(2)
            self.robot.play_anim_trigger(cozmo.anim.Triggers.FistBumpLeftHanging).wait_for_completed()
            
        
        
        
        
         
        
