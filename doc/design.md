# Design

In order to provide some expressive abilities to the robots, a set of movements and configurations
was developed.
These movements are quite different from robot to robot, due to their capabilities (degrees of
freedom, sound system, or available SDK).

## Cozmo

The [Cozmo Python SDK](https://pypi.org/project/cozmo) provides access to predefined actions which
are already quite expressive.
On the other hand, it is extremely difficult to design animations for Cozmo:
the eye movements and usually fast coordinated movements of other animations are complex to set up.
For this reason, we reviewed all available animations and selected a list of movements that
represent the appropriate emotion that we want to transmit:

- Annoyed:

  - `anim_memorymatch_failhand_01`
  - `anim_reacttoblock_frustrated_01`
  - `anim_pyramid_reacttocube_frustrated_low_01`
  - `anim_reacttoblock_frustrated_int2_01`

- Excited:

  - `anim_speedtap_wingame_intensity03_01`
  - `anim_codelab_chicken_01`

- Happy:

  - `anim_poked_giggle`
  - `anim_reacttoblock_happydetermined_01`
  - `anim_memorymatch_failhand_player_02`
  - `anim_pyramid_reacttocube_happy_low_01`
  - `anim_pyramid_reacttocube_happy_mid_01`
  - `anim_pyramid_reacttocube_happy_high_02`

- Sad:

  - `anim_rtpmemorymatch_no_01`
  - `anim_speedtap_playerno_01`
  - `anim_memorymatch_failhand_02`
  - `anim_energy_cubenotfound_02`

- Scared: We couldn't find any animations that fitted this description.

- Start animation:

  - `anim_speedtap_wingame_intensity03_01`

- Final animation:
  to finalize the experiment, we use the `Fist Bump` animations from Cozmo, to allow the child to
  interact with the robot directly.

  This animation makes Cozmo ask for a fist bump, showing its intent with its eyes and lifting its
  lift.
  Once the child bumps the robot, the robot will execute an extra animation showing a high level of
  excitement.

- Background movements:
  the robot executes a few small movements during the experiment, in order to appear alive and
  engaged.
  These movements happen at random times, during the whole experiment.

  - Follow participant:
    looks for the face of the participant and follows them.
    The robot can remember the last position of the participant, so it can look straight back at
    them.
  - `anim_speedtap_wait_short`
  - `anim_speedtap_wait_medium`
  - `anim_speedtap_wait_medium_02`
  - `anim_speedtap_wait_medium_03`
  - `anim_speedtap_wait_long`

## MiRo

The MiRo robot can be controlled using ROS.
The manufacturer provides an SDK, which allows communicating with the robot and accessing different
capabilities.
This robot has complex capabilities to engage with humans, including face tracking, responses to
audio stimulus, touch sensors etc.
These provide a lot of flexibility when working with the robot, but unfortunately, Miro does not
provide a set of actions like [Cozmo](#cozmo).
In the case of this robot, we designed a set of movements that resemble the expressions we require.
In all animations, the sound is reactivated to provide a 'voice' effect.

- Annoyed:

  - [annoyed2](../readingtorobot/MiRo/animations/annoyed2.json):
    Lower the tail, reduce valence and arousal of the emotion engine and move the head down and
    sideways in disapproval.

- Excited:

  - [excited](../readingtorobot/MiRo/animations/excited2.json):
    Lift and wag the tail, maximize valence of the emotion engine, lift the head, close
    the eyes slightly.

- Happy:

  - [happy](../readingtorobot/MiRo/animations/happy1.json):
    Lift and wag the tail, lift the head, and increase valence and arousal.

- Sad:

  - [sad](../readingtorobot/MiRo/animations/sad1.json):
    Lower tail, lower valence and arousal, lower head.

- Scared: We didn't manage to express this feeling properly with this robot successfully.

- Start animation:

  - [start](../readingtorobot/MiRo/animations/start.json):
    Wag the tail and increase valence and arousal. Move head in a nod.

- Final animation:

  - [end](../readingtorobot/MiRo/animations/end.json):
    Similar to the 'excited' movement.

- Background movements:
  All background movements are provided by the MiRo SDK.
  By activating its autonomous abilities, the robot can engage without many issues.

NOTE: Other animations were developed for this robot, but were not selected for the final
experiment, since they were not as expressive.
All those animations can be found in this [archive](../readingtorobot/MiRo/animations/archived)

## NAO

Similarly to [MiRo](#miro), the NAO Robot provides a set of autonomous abilities that allow it to
easily follow a participant and interact with them.
The movements of the robot are implemented similarly to [Cozmo's](#cozmo), being possible to
execute a set of predefined animations on command.
However, these movements are designed for a standing position and are limited to sitting poses.
Since the robot is required to sit during the experiment, we had to implement new movements for
expressions and background animations.

All of NAO's movements are defined in [nao_expression.py](../readingtorobot/NAO/nao_expression.py).
These include also other movements needed for demo purposes, and to record some of the videos.

NAO performs all these movements from a sitting position.
At the start of the experiment, if NAO is in a different position (standing, in a crouching
position or other), the robot will first position itself in that sitting position.
Once the robot is in the start position, it will start with the background movements.

All the sounds used for the following emotions are sourced from the `Aldebaran` sound set, which
should be installed in the robot.

- Annoyed:
  Move the upper body and head backwards, while playing `enu_ono_exclamation_disapointed_05`.

- Excited:
  Move the head in a nod, while playing `enu_ono_laugh_excited_01`.

- Happy:
  We could not find a good way to express this feeling clearly with NAO.

- Sad:
  Lower slowly the head while playing `frf_ono_exclamation_sad_06`.

- Scared:
  Move the upper body and head backwards slightly, but abruptly.
  Plays `enu_ono_scared_02` simultaneously.

- Start animation:
  Move the head and arms up while playing `enu_word_yeah`.

- Final animation:
  Says 'Hey, thank you!', and performs a dab.

- Background movements:
  Place the arms so that either one or two of the robot's hands or forearms rest on its knees.
  The head moves towards the ground (looking at the book) or towards the participant intermittently.
  All changes of position are made randomly, in short intervals of 1s.
  This means that the robot will at least stay in one position for a second, but could stay there
  for several.
  When looking towards the participant, facial recognition and tracking is enabled.
