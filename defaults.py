# -*- coding: utf-8 -*-
"""Default parameters for experiments

Experiments will be set up with these parameters unless they're overridden with keyword arguments when the
Experiment object is first instantiated.

    # SCREEN DEFAULTS
    screen_size=(1024,768),
    bits_per_pixel=16,
    refresh_rate=120, #Hz


    # DISPLAY OBJECT DEFAULTS
    # These parameters define the default values for the Display classes' attributes.
    # These parameters may also be passed as keyword arguments when creating a Display class instance.

    # response_device: a class responsible for recording responses from the subject
    # Several such classes, corresponding to different input modalities, are defined in response_collectors.py
    response_device = response_collectors.Keyboard,
    # possible_resp: a list defining the allowable responses to displays; other responses will not be recognized.
    possible_resp=["any"], # Use "any" if the response doesn't matter.
    # The names of non-alphanumeric keys are documented at http://www.pygame.org/docs/ref/key.html
    min_rt = 0, # Time before a response will be accepted (e.g. to prevent accidental rapid key repeats being accepted)

    font_name='c:\\WINNT\\fonts\\courbd.ttf', # Use \\ for \ where \ alone might produce unintended side effects.
    bold = 0,
    italic = 0,
    font_size=24,
    vertical_spacing=0, # Space, in pixels, between lines of text
    margins=(43,0,43,0), # margin width, in pixels, on left, top, bottom, and right
    align=('left','center'), # 2-tuple specifying horizontal and vertical alignment of text or image.
                            # horizontal may be "left", "center", or "right"
                            # vertical may be "top", "center", or "bottom"
    wrap=True, # True = wrap text, False = text will run off the screen if it's too long
    bgcolor=(0,0,0), # Color is specified as an RGB 3-tuple.  (0,0,0) = black; (1,1,1) = white.
    color=(1,1,1),   # Text color.

    continue_text = "Press any key to continue.", # Displayed at the bottom of a ContinueDisplay after a delay.
    continue_delay = 1000, # Delay, in msec, before continue_text is shown and responses are accepted for a ContinueDisplay

    # Python package to use for sound playback.  Currently 'winsound' and 'pygame' are supported.
    # winsound has low latency with low variance (consistently 14-15 ms on psyc-rickl04
    # However winsound only works on Windows, and will cut off any files that are longer than one minute.
    # pygame doesn't have those drawbacks, but it has really bad latency (mean 89 ms, SD 29 ms).
    audio_package = "winsound",

    # TEXT DATA FILE DEFAULTS
    data_directory='data', # This directory will be created if it does not already exist.
    data_filename_prefix='s', # Prefix to be followed by subject number and session number
    NA_string='.', #String written to the text data file as a placeholder for nonexistent attributes
    session_info = [], # List of attributes to be entered by the experimenter before the beginning of the experiment
                       # (besides subject ID, which the experimenter always has to enter).
                       # If 'session' is included then that attribute will automatically be appended to the data file name.

    # EYETRACKER DATA FILE DEFAULTS
    edf_prefix='s',   # prefix for .edf data file stored on eyetracking computer, to be followed by subject and session

    eye_used = 1,   # If recording both eyes, which eye to use for gaze-contingent displays. 1=right, 0=left
    ia_fill = True,  # If spaces between words are larger than 2*gaze_error, whether to extend interest areas to fill in the gaps between words.
    min_fixation = 800,  # Minimum fixation duration (ms) on a gaze-contingent trigger before it's triggered
    gaze_error = 35,
    # gaze_error = the distance, in pixels, between the left and right of the stimuli and the edge of the enclosing interest area, in pixels.
    # To calculate appropriate buffer values, estimate
    # the subject's distance from the screen, and assume tracker error of 0.5 (liberal) to
    # 1.0 (more conservative) degrees of visual angle (you can get an idea of the error by checking the error
    # shown after validation during tracker setup).
    # error_in_pixels = tan(visual_angle_error) * subject_distance_inches * screen_width_pixels / screen_width_inches
    
    #TRACKER PARAMETERS
    #All parameters preceded with 'tracker_' will be sent to the tracker
    #at the time of tracker setup
    #These are defined in the pylink documentation.
    tracker_setFileEventFilter="LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON",
    tracker_setFileEventData="GAZE,GAZERES,AREA,VELOCITY,STATUS",
    tracker_setFileSampleFilter="LEFT,RIGHT,GAZE,AREA,GAZERES,STATUS",
    tracker_setLinkEventFilter="LEFT,RIGHT,FIXATION,FIXUPDATE",
    tracker_setLinkEventData="GAZE,STATUS",
    tracker_setLinkSampleFilter="LEFT,RIGHT,GAZE,GAZERES,AREA,STATUS",
    tracker_setRecordingParseType='GAZE',
    tracker_setPupilSizeDiameter='NO',
    tracker_setSaccadeVelocityThreshold=30,
    tracker_setAccelerationThreshold=8000,
    tracker_setMotionThreshold=0.15,
    tracker_setPursuitFixup=60,
    tracker_setUpdateInterval=0,

    heuristic_filter="on", #The 'heuristic filter' performs a real-time smoothing algorithm for the samples,
                             #which delays retrieval of samples from the link by 4 msec.
                             #DO NOT USE REFLECTION REJECTION IF THE FILTER IS OFF.

    #DRIFT CORRECTION
    drift_correction_target=(512,384), #Coordinates of the fixation point for drift correction
    setDriftCorrectSounds=["off","off","off"] #Arguments to pylink command; see pylink docs

    #CEDRUS BUTTON BOX
    buttonbox_com=3,
    buttonbox_baud=115200
"""
import response_collectors
defaultParams = dict(
    
    # SCREEN DEFAULTS
    screen_size=(1024,768),
    bits_per_pixel=16,
    refresh_rate=120, #Hz


    # DISPLAY OBJECT DEFAULTS
    # These parameters define the default values for the Display classes' attributes.
    # These parameters may also be passed as keyword arguments when creating a Display class instance.

    # response_device: a class responsible for recording responses from the subject
    # Several such classes, corresponding to different input modalities, are defined in response_collectors.py
    response_device = response_collectors.EyeLinkButtons,
    # possible_resp: a list defining the allowable responses to displays; other responses will not be recognized.
    possible_resp=["any"], # Use "any" if the response doesn't matter.
    # The names of non-alphanumeric keys are documented at http://www.pygame.org/docs/ref/key.html
    min_rt = 0, # Time before a response will be accepted (e.g. to prevent accidental rapid key repeats being accepted)
	font_name='c:\\windows\\fonts\\cour.ttf', # Use \\ for \ where \ alone might produce unintended side effects.
    bold = 0,
    italic = 0,
    font_size=24,
    vertical_spacing=70, # Space, in pixels, between lines of text
    margins=(43,0,43,0), # margin width, in pixels, on left, top, bottom, and right
    align=('left','center'), # 2-tuple specifying horizontal and vertical alignment of text or image.
                            # horizontal may be "left", "center", or "right"
                            # vertical may be "top", "center", or "bottom"
    wrap=True, # True = wrap text, False = text will run off the screen if it's too long
    bgcolor=(1,1,1), # Color is specified as an RGB 3-tuple.  (0,0,0) = black; (1,1,1) = white.
    color=(0,0,0),   # Text color.

    continue_text = u"Taste drücken zum fortfahren.", # Displayed at the bottom of a ContinueDisplay after a delay.
    continue_delay = 1000, # Delay, in msec, before continue_text is shown and responses are accepted for a ContinueDisplay

    # Python package to use for sound playback.  Currently 'winsound' and 'pygame' are supported.
    # winsound has low latency with low variance (consistently 14-15 ms on psyc-rickl04
    # However winsound only works on Windows, and will cut off any files that are longer than one minute.
    # pygame doesn't have those drawbacks, but it has really bad latency.
    audio_package = "winsound",
    audio_latency = 15, # Milliseconds between play command execution and actual onset of sound on headphones
                        # 15 for psyc-rickl04 (EyeLink I subject PC) as measured by Cedrus voicekey
                        # See "Hardware Timing Tests" folder on the lab server
    

    # TEXT DATA FILE DEFAULTS
    data_directory='data', # This directory will be created if it does not already exist.
    data_filename_prefix='s', # Prefix to be followed by subject number and session number
    NA_string='.', #String written to the text data file as a placeholder for nonexistent attributes
    session_info = [], # List of attributes to be entered by the experimenter before the beginning of the experiment
                       # (besides subject ID, which the experimenter always has to enter).
                       # If 'session' is included then that attribute will automatically be appended to the data file name.

    # EYETRACKER DATA FILE DEFAULTS
    edf_prefix='s',   # prefix for .edf data file stored on eyetracking computer, to be followed by subject and session

    eye_used = 1,   # If recording both eyes, which eye to use for gaze-contingent displays. 1=right, 0=left
    ia_fill = False,  # If spaces between words are larger than 2*gaze_error, whether to extend interest areas to fill in the gaps between words.
    min_fixation = 800,  # Minimum fixation duration (ms) on a gaze-contingent trigger before it's triggered
    buffer_size = 0,
    gcbuffer_size = 35,
	gcTargetCoords = (20,384),
    # buffer_size = the distance, in pixels, between the left and right of the stimuli and the edge of the enclosing interest area, in pixels.
    # To calculate appropriate buffer values, estimate
    # the subject's distance from the screen, and assume tracker error of 0.5 (liberal) to
    # 1.0 (more conservative) degrees of visual angle (you can get an idea of the error by checking the error
    # shown after validation during tracker setup).
    # error_in_pixels = tan(visual_angle_error) * subject_distance_inches * screen_width_pixels / screen_width_inches
    
    #TRACKER PARAMETERS
    #All parameters preceded with 'tracker_' will be sent to the tracker
    #at the time of tracker setup
    #These are defined in the pylink documentation.
    tracker_setFileEventFilter="LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON",
    tracker_setFileEventData="GAZE,GAZERES,AREA,VELOCITY,STATUS",
    tracker_setFileSampleFilter="LEFT,RIGHT,GAZE,AREA,GAZERES,STATUS",
    tracker_setLinkEventFilter="LEFT,RIGHT,FIXATION,FIXUPDATE",
    tracker_setLinkEventData="GAZE,STATUS",
    tracker_setLinkSampleFilter="LEFT,RIGHT,GAZE,GAZERES,AREA,STATUS",
    tracker_setRecordingParseType='GAZE',
    tracker_setPupilSizeDiameter='NO',
    tracker_setSaccadeVelocityThreshold=30,
    tracker_setAccelerationThreshold=8000,
    tracker_setMotionThreshold=0.15,
    tracker_setPursuitFixup=60,
    tracker_setUpdateInterval=0,

    heuristic_filter="on", #The 'heuristic filter' performs a real-time smoothing algorithm for the samples,
                             #which delays retrieval of samples from the link by 4 msec.
                             #DO NOT USE REFLECTION REJECTION IF THE FILTER IS OFF.

    #DRIFT CORRECTION
    drift_correction_target=(512,384), #Coordinates of the fixation point for drift correction
    setDriftCorrectSounds=["off","off","off"], #Arguments to pylink command; see pylink docs

    #CEDRUS BUTTON BOX
    buttonbox_com=3,
    buttonbox_baud=115200
    )
