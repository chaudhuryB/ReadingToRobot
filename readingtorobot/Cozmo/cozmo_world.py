

import cozmo


class EvtRobotMovedBish(cozmo.event.Event):
    '''Dispatched when a new camera image is received and processed from the robot delocalised.'''
    pass


class CozmoWorld(cozmo.world.World):
    def _recv_msg_robot_delocalized(self, evt, *, msg):
        # Invalidate the pose for every object
        cozmo.world.logger.info("Robot delocalized - invalidating poses for all objects")
        for obj in self._objects.values():
            obj.pose.invalidate()
        self.dispatch_event(EvtRobotMovedBish)
