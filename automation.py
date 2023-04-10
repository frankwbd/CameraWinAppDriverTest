import time
import os
import unittest
import itertools
from appium import webdriver
from selenium.common.exceptions import NoSuchElementException
from enum import Enum

###############################################################################################################

# Here is to define constant values
IP_ADDR = "http://127.0.0.1"
PORT_NUMBER = "4723"
REMOTE_TARGET = IP_ADDR + ":" + PORT_NUMBER

# the duration (in second) of video recording
VIDEO_CAPTURE_DURATION = 30

# the amount of delay (in second) for each operation
OPERATION_WAIT_DURATION = 1

# the number of iterations for veryfying both videos/photos MEP effects
NUMBER_OF_TEST_ITERATIONS = 1000

# to take video/photo or not,
# 0: not to take
# 1: to take
TAKE_VIDEOS_PHOTOS_ACTION = 0

# the number of seconds for operation torrelance
IMPLICITLY_WAIT_TIME = 3

class CameraMode(Enum):
    VIDEO_MODE = 0
    PHOTO_MODE = 1

MEP_EFFECTS = [
    # "Automatic framing - The camera will keep you in frame and in focus for photos and videos",
    # "Eye contact - Helps you appear to be looking directly at the camera",
    # "Background effects",
]

BACKGROUND_EFFECTS = [
    # "Standard blur - Apply a heavy blur to obscure background objects",
    "Standard blur",
    # "Portrait blur - Blur the background to help keep focus on you",
    "Portrait blur",
]

FLICKER_REDUCTION = [
    "Auto",
    "50 Hz",
    "60 Hz",
]

###############################################################################################################

'''
    launchCameraApp is called to lunch WindowsCamera app (UWP) from Microsoft Store

    [output] handle of WinAppDriver
'''

def launchCameraApp():
    # Set desired capabilities to launch the Camera app
    desired_caps = {
        "app": "Microsoft.WindowsCamera_8wekyb3d8bbwe!App",
        "platformName": "Windows",
    }
    # Start the Windows Application Driver
    WindowsCameraAppDriver = webdriver.Remote(
        command_executor = REMOTE_TARGET,
        desired_capabilities = desired_caps)
    WindowsCameraAppDriver.implicitly_wait(IMPLICITLY_WAIT_TIME)
    return WindowsCameraAppDriver

###############################################################################################################

###############################################################################################################

'''
    closeCameraApp is to close WindowsCamera app and destroy the hanle,
    should be paired with launchCameraApp() call

    [input] handle of WinAppDriver
'''

def closeCameraApp(WindowsCameraAppDriver):
    # Close the Camera app
    CloseCameraButton = WindowsCameraAppDriver.find_element_by_name("Close Camera")
    time.sleep(OPERATION_WAIT_DURATION)
    CloseCameraButton.click()

    # Quit the Windows Application Driver
    WindowsCameraAppDriver.quit()

###############################################################################################################

###############################################################################################################

'''
    switchCameraCheckMEPPackageExist is to check if camera effect button exist or not,
    it conduct two rounds of checking:
    (first round)
        if effect button exists, then do nothing
        otherwise, check if "SwitchCameraButton" exists,
        - if exsis, then click on the button and goes to the second round
        - print error to notify user the MEP is not installed
    (second round)
        - if camera effect button is there, do nothing
        - print error to notify user the MEP is not installed

    [input] handle of WinAppDriver
'''

def switchCameraCheckMEPPackageExist(WindowsCameraAppDriver):
    try:
        MEPEffects = WindowsCameraAppDriver.find_element_by_name("Windows Studio effects")
    except NoSuchElementException:
        try:
            changeCameraButton = WindowsCameraAppDriver.find_element_by_accessibility_id("SwitchCameraButtonId")
        except NoSuchElementException:
            print("No MEP packages installed in this device, please check!!")
            closeCameraApp(WindowsCameraAppDriver)

        print("Not able to find MEP effects, switch to another camera!")
        changeCameraButton.click()
        time.sleep(OPERATION_WAIT_DURATION)
        try:
            MEPEffects = WindowsCameraAppDriver.find_element_by_name("Windows Studio effects")
        except NoSuchElementException:
            print("No MEP packages installed in this device, please check!!")
            closeCameraApp(WindowsCameraAppDriver)

###############################################################################################################

###############################################################################################################

'''
    switchToVideoMode is to switch to video mode if current camera mode is not in video mode

    [input] handle of WinAppDriver
'''

def switchToVideoMode(WindowsCameraAppDriver):
    '''
        if is not in video mode, 
        we can switch into photo mode first,
        and then switch to video mode
    '''
    try:
        WindowsCameraAppDriver.find_element_by_name("Take video")
    except NoSuchElementException:
        # switch into photo mode first
        switchToPhotoMode(WindowsCameraAppDriver)

        videoModeButtom = WindowsCameraAppDriver.find_element_by_name("Switch to video mode")
        videoModeButtom.click()
        time.sleep(OPERATION_WAIT_DURATION)
        

###############################################################################################################

###############################################################################################################

'''
    switchToPhotoMode is to switch to video mode if current camera mode is not in photo mode

    [input] handle of WinAppDriver
'''

def switchToPhotoMode(WindowsCameraAppDriver):
    try:
        WindowsCameraAppDriver.find_element_by_name("Take photo")
    except NoSuchElementException:
        PhotoModeButtom = WindowsCameraAppDriver.find_element_by_name("Switch to photo mode")
        PhotoModeButtom.click()
        time.sleep(OPERATION_WAIT_DURATION)

###############################################################################################################

###############################################################################################################

'''
    closeCameraEffectToggleButtonWithTakingAction is:
    1. close CameraEffect sub Window
    2. capture action
    3. open CameraEffect sub Window

    [input] handle of WinAppDriver
    [input] VIDEO_MODE or CAMERA_MODE
'''

def closeCameraEffectToggleButtonWithTakingAction(WindowsCameraAppDriver, mode : CameraMode):

    # to close CameraEffectToggleButton
    LightDismissButton = WindowsCameraAppDriver.find_element_by_name("Close")
    LightDismissButton.click()
    time.sleep(OPERATION_WAIT_DURATION)

    # to take video clips/photos
    takeVideosPhotos(WindowsCameraAppDriver, mode)

    CameraEffectToggleButton = WindowsCameraAppDriver.find_element_by_name("Windows Studio effects")
    CameraEffectToggleButton.click()
    time.sleep(OPERATION_WAIT_DURATION)

###############################################################################################################

###############################################################################################################

'''
    takeVideosPhotos is to press taken button,
    if in VIDEO_MODE, need to wait for VIDEO_CAPTURE_DURATION and press STOP buttom to finish taking

    [input] handle of WinAppDriver
    [input] VIDEO_MODE or CAMERA_MODE
'''

def takeVideosPhotos(WindowsCameraAppDriver, mode : CameraMode):

    print("Take videos/photos")
    if not TAKE_VIDEOS_PHOTOS_ACTION:
        time.sleep(OPERATION_WAIT_DURATION)
        return

    if (mode == CameraMode.VIDEO_MODE):
        takenButtom = WindowsCameraAppDriver.find_element_by_name("Take video")
    else:
        takenButtom = WindowsCameraAppDriver.find_element_by_name("Take photo")
    takenButtom.click()

    # for video mode, we have to delay VIDEO_CAPTURE_DURATION for recording
    if (mode == CameraMode.VIDEO_MODE):
        time.sleep(VIDEO_CAPTURE_DURATION)
        stopTakingVideoButtom = WindowsCameraAppDriver.find_element_by_name("Stop taking video")
        stopTakingVideoButtom.click()

    time.sleep(OPERATION_WAIT_DURATION)

###############################################################################################################

###############################################################################################################

'''
    updateCameraEffectList is to get all MEP effects based on current MEP package or NPU socks,
    assume the "CameraEffectToggleButton" already been pressed

    [input] handle of WinAppDriver
'''

def updateCameraEffectList(WindowsCameraAppDriver):
    if len(MEP_EFFECTS) == 0:
        toggleSwitchButtons = WindowsCameraAppDriver.find_elements_by_class_name("ToggleSwitch")
        for switchButton in toggleSwitchButtons:
            MEP_EFFECTS.append(switchButton.text)

###############################################################################################################

###############################################################################################################

'''
    clearAllEffects is to clear all existing MEP effects from Windows settings,
    which to keep all combination of MEP effects can be verified,
    also assume the "CameraEffectToggleButton" already been pressed

    [input] handle of WinAppDriver
'''

def clearAllEffects(WindowsCameraAppDriver):

    # to update effect list if necessary
    updateCameraEffectList(WindowsCameraAppDriver)

    # reset toggle button to OFF
    for effect in MEP_EFFECTS:
        if effect == "Background effects":
            toggleSwitchButtons = WindowsCameraAppDriver.find_elements_by_class_name("ToggleSwitch")
            mepEffectButton = toggleSwitchButtons[len(MEP_EFFECTS) - 1]
        else:
            mepEffectButton = WindowsCameraAppDriver.find_element_by_name(effect)
        
        # un-toggle if the effect already been enabled
        if mepEffectButton.is_selected():
            mepEffectButton.click()
            time.sleep(OPERATION_WAIT_DURATION)

###############################################################################################################

###############################################################################################################

'''
    testEachCameraEffect is to clear all existing MEP effects from Windows settings,
    which to keep all single of MEP effects can be verified,
    also assume the "CameraEffectToggleButton" already been pressed

    [input] handle of WinAppDriver
    [input] VIDEO_MODE or CAMERA_MODE
'''

def testEachCameraEffect(WindowsCameraAppDriver, mode : CameraMode):

    # To open CameraEffect windows
    CameraEffectToggleButton = WindowsCameraAppDriver.find_element_by_name("Windows Studio effects")
    time.sleep(OPERATION_WAIT_DURATION)
    CameraEffectToggleButton.click()

    # reset toggle button to OFF
    clearAllEffects(WindowsCameraAppDriver)

    for idx, effect in enumerate(MEP_EFFECTS):
        mepEffectButton = WindowsCameraAppDriver.find_element_by_name(effect)

        if effect == "Background effects":
            toggleSwitchButtons = WindowsCameraAppDriver.find_elements_by_class_name("ToggleSwitch")
            mepEffectButton = toggleSwitchButtons[idx]

        mepEffectButton.click()
        time.sleep(OPERATION_WAIT_DURATION)

        if effect == "Background effects":
            for i, blurEffect in enumerate(BACKGROUND_EFFECTS):
                blurEffectButton = WindowsCameraAppDriver.find_element_by_name(blurEffect)
                blurEffectButton.click()

                closeCameraEffectToggleButtonWithTakingAction(WindowsCameraAppDriver, mode)

                if (i == (len(BACKGROUND_EFFECTS) - 1)):
                    mepEffectButton.click()
                    time.sleep(OPERATION_WAIT_DURATION)
        else:
            closeCameraEffectToggleButtonWithTakingAction(WindowsCameraAppDriver, mode)
            mepEffectButton.click()
            time.sleep(OPERATION_WAIT_DURATION)

    LightDismissButton = WindowsCameraAppDriver.find_element_by_name("Close")
    LightDismissButton.click()

###############################################################################################################

###############################################################################################################

'''
    testEachCameraEffectCombinations is to clear all existing MEP effects from Windows settings,
    which to keep all combination of MEP effects can be verified,
    also assume the "CameraEffectToggleButton" already been pressed

    [input] handle of WinAppDriver
    [input] VIDEO_MODE or CAMERA_MODE
'''

def testEachCameraEffectCombinations(WindowsCameraAppDriver, mode : CameraMode):

    # To open CameraEffect windows
    CameraEffectToggleButton = WindowsCameraAppDriver.find_element_by_name("Windows Studio effects")
    time.sleep(OPERATION_WAIT_DURATION)
    CameraEffectToggleButton.click()

    # reset toggle button to OFF
    clearAllEffects(WindowsCameraAppDriver)

    # generate all combinations for MEP effects
    ToggleButtonCombinations = []
    for r in range(len(MEP_EFFECTS)+1):
        for combination in itertools.combinations(MEP_EFFECTS, r):
            ToggleButtonCombinations.append(combination)
    
    # to test all combinations for MEP effects
    for tuple in ToggleButtonCombinations:
        # start config desired combination
        isBlurEffectEnable = False
        for t in tuple:
            if t == "Background effects":
                toggleSwitchButtons = WindowsCameraAppDriver.find_elements_by_class_name("ToggleSwitch")
                mepEffectButton = toggleSwitchButtons[len(MEP_EFFECTS) - 1]
                mepEffectButton.click()
                time.sleep(OPERATION_WAIT_DURATION)
                isBlurEffectEnable = True

                for blurEffect in BACKGROUND_EFFECTS:
                    blurEffectButton = WindowsCameraAppDriver.find_element_by_name(blurEffect)
                    blurEffectButton.click()
                    time.sleep(OPERATION_WAIT_DURATION)
                    closeCameraEffectToggleButtonWithTakingAction(WindowsCameraAppDriver, mode)
            else:
                mepEffectButton = WindowsCameraAppDriver.find_element_by_name(t)
                mepEffectButton.click()
                time.sleep(OPERATION_WAIT_DURATION)

        if not isBlurEffectEnable:
            closeCameraEffectToggleButtonWithTakingAction(WindowsCameraAppDriver, mode)
        
        # revert to original
        clearAllEffects(WindowsCameraAppDriver)
    
    LightDismissButton = WindowsCameraAppDriver.find_element_by_name("Close")
    LightDismissButton.click()

###############################################################################################################

###############################################################################################################

'''
    retrieveQualityList is to get videos/photos quality list,
    be aware that due to we collect all "ComboBoxItem" from quality settings,
    should remove flicker options from this list in video mode.

    [input] handle of WinAppDriver
    [input] VIDEO_MODE or CAMERA_MODE

    [output] list of all existing quality options
'''

def retrieveQualityList(WindowsCameraAppDriver, mode : CameraMode):

    # query quality options
    qualityLists = WindowsCameraAppDriver.find_elements_by_class_name("ComboBoxItem")

    # there is "Flicker reduction" ComboBox in Video quality page,
    # to remove those flicker options to keep quality options only
    if (mode == CameraMode.VIDEO_MODE):
        for flicker in FLICKER_REDUCTION:
            for vq in qualityLists:
                if (vq.text == flicker):
                    qualityLists.remove(vq)

    return qualityLists

###############################################################################################################

###############################################################################################################

'''
    reUpdateQualityList is to re-update the quality lists,
    has to click setting button first and go into "Photos settings" or "Videos settings" as desired

    [input] handle of WinAppDriver
    [input] instance of setting button
    [input] instance of quality button
    [input] VIDEO_MODE or CAMERA_MODE

    [output] list of all existing quality options
'''

def reUpdateQualityList(WindowsCameraAppDriver, settingsButton, qualityButton, mode : CameraMode):
    settingsButton.click()
    time.sleep(OPERATION_WAIT_DURATION)
    qualityButton.click()
    time.sleep(OPERATION_WAIT_DURATION)
    return retrieveQualityList(WindowsCameraAppDriver, mode)

###############################################################################################################

###############################################################################################################

'''
    testEffectsOnVariousQualities is to test MEP effects:
    1. launch Camera app
    2. switch to VIDEOS/PHOTOS mode depends on the input parameter
    3. open setting page to toggle desired testing quality (rosulutions)
    4. laucn testEachCameraEffectCombinations
    5. close Camera app

    [input] VIDEO_MODE or CAMERA_MODE
'''

def testEffectsOnVariousQualities(mode : CameraMode):

    # trying to open WindowsCamera app
    WindowsCameraAppDriver = launchCameraApp()

    # Switch to correct mode if necessary
    if (mode == CameraMode.VIDEO_MODE):
        switchToVideoMode(WindowsCameraAppDriver)
    else:
        switchToPhotoMode(WindowsCameraAppDriver)

    # Open settings menu
    settingsButton = WindowsCameraAppDriver.find_element_by_name("Open Settings Menu")
    settingsButton.click()
    time.sleep(OPERATION_WAIT_DURATION)

    # switch quality settings and click
    if (mode == CameraMode.VIDEO_MODE):
        qualitySettingsButton = WindowsCameraAppDriver.find_element_by_name("Videos settings")
    else:
        qualitySettingsButton = WindowsCameraAppDriver.find_element_by_name("Photos settings")
    qualitySettingsButton.click()
    time.sleep(OPERATION_WAIT_DURATION)

    # two combo box should be there: "Video quality" / "Flicker reduction" in videos settings
    # only one combo box there: "Photo quality"  in photos settings
    ComboBoxLists = WindowsCameraAppDriver.find_elements_by_class_name("ComboBox")
    time.sleep(OPERATION_WAIT_DURATION)

    # toggle quality option
    qualityButton = ComboBoxLists[0]
    qualityButton.click()
    time.sleep(OPERATION_WAIT_DURATION)

    # query quality options
    qualityLists = retrieveQualityList(WindowsCameraAppDriver, mode)

    # test on various photo qualities
    for idx, vq in enumerate(qualityLists):

        if (idx >= len(qualityLists)):
            break

        # Switch to different resolutions
        qualityLists[idx].click()
        time.sleep(OPERATION_WAIT_DURATION)

        # back to camera view
        backButton = WindowsCameraAppDriver.find_element_by_name("Back")
        backButton.click()
        time.sleep(OPERATION_WAIT_DURATION)

        # some resolutions are out of MEP scope, skip these quality
        try:
            WindowsCameraAppDriver.find_element_by_name("Windows Studio effects")
        except NoSuchElementException:
            if (idx < (len(qualityLists) - 1)):
                qualityLists = reUpdateQualityList(WindowsCameraAppDriver, settingsButton, qualityButton, mode)
                continue

        # start to verify each photo effects for specific photo quality
        if (mode == CameraMode.VIDEO_MODE):
            qulityStr = "Videos Quality:"
        else:
            qulityStr = "Photos Quality:"
        print(qulityStr, qualityLists[idx].text)

        testEachCameraEffectCombinations(WindowsCameraAppDriver, mode)

        # if necessary, open setting buttom again to switch another resolution
        if (idx < (len(qualityLists) - 1)):
            qualityLists = reUpdateQualityList(WindowsCameraAppDriver, settingsButton, qualityButton, mode)

    closeCameraApp(WindowsCameraAppDriver)

###############################################################################################################

###############################################################################################################

'''
    monitorFrameServerServiceStatus is to show current status of both  frameserver/frameservermonitor service
'''

def monitorFrameServerServiceStatus():
    print("frameserver status: ")
    os.system('sc query frameserver | find /c "RUNNING"')
    print("frameservermonitor status: ")
    os.system('sc query frameservermonitor | find /c "RUNNING"')


###############################################################################################################

###############################################################################################################

'''
    This is the main function of test procedure:
    1. CameraMode.VIDEO_MODE: to verity MEP effects on videos
    2. CameraMode.PHOTO_MODE: to verity MEP effects on photos
'''
# Call the test function 100 times
for i in range(NUMBER_OF_TEST_ITERATIONS):
    print("INTERATION [", (i + 1), " / ", NUMBER_OF_TEST_ITERATIONS,"]")
    testEffectsOnVariousQualities(CameraMode.VIDEO_MODE)
    time.sleep(OPERATION_WAIT_DURATION)
    # testEffectsOnVariousQualities(CameraMode.PHOTO_MODE)
    # time.sleep(OPERATION_WAIT_DURATION)
    # monitorFrameServerServiceStatus()
    # time.sleep(OPERATION_WAIT_DURATION)
