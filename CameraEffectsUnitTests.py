import time
import os
import glob
import re
import socket
import subprocess
import unittest
import itertools
import rotatescreen
import psutil
import re
import xlsxwriter
import shutil
from appium import webdriver
from selenium.common.exceptions import NoSuchElementException
from enum import Enum
from datetime import datetime
from videoprops import get_video_properties

###############################################################################################################

# Here is to define constant values
IP_ADDR = "127.0.0.1"
PORT_NUMBER = 4723
REMOTE_TARGET = f"http://{IP_ADDR}:{PORT_NUMBER}"

CAPTURE_FILE_FOLDER_PATH = "C:\\Users\\" + os.getlogin() + "\\Pictures\\Camera Roll\\*"
CAPTURE_FILE_VIDEO_TYPES = "C:\\Users\\" + os.getlogin() + "\\Pictures\\Camera Roll\\*.mp4"
CAPTURE_FILE_PHOTO_TYPES = "C:\\Users\\" + os.getlogin() + "\\Pictures\\Camera Roll\\*.jpg"

# the amount of delay (in second) for each operation
OPERATION_WAIT_DURATION = 1

# the number of seconds for operation torrelance
IMPLICITLY_WAIT_TIME = 5

class CameraMode(Enum):
    VIDEO_MODE = 0
    PHOTO_MODE = 1

class ExcelFileIfo():
    outputExcelFp = any
    outputExcelCurWorkSheet = any
    outputExcelRowIdx = 0
    noticeFormat = any
    targetFolderPath = any

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

VIDEO_MODE_QUALITY_LIST = [
    "1080p, 16 by 9 aspect ratio, 30 fps",
    "720p, 16 by 9 aspect ratio, 30 fps",
    "360p, 16 by 9 aspect ratio, 30 fps",
    "1440p, 4 by 3 aspect ratio, 30 fps",
    "480p, 4 by 3 aspect ratio, 30 fps",
    "640p, 1 by 1 aspect ratio, 30 fps",
    "600p, 4 by 3 aspect ratio, 30 fps",
]

PHOTO_MODE_QUALITY_LIST = [
    "2.1 megapixels, 16 by 9 aspect ratio,  1920 by 1080 resolution",
    "0.9 megapixels, 16 by 9 aspect ratio,  1280 by 720 resolution",
    "0.2 megapixels, 16 by 9 aspect ratio,  640 by 360 resolution",
    "2.8 megapixels, 4 by 3 aspect ratio,  1920 by 1440 resolution",
    "0.3 megapixels, 4 by 3 aspect ratio,  640 by 480 resolution",
    "0.4 megapixels, 1 by 1 aspect ratio,  640 by 640 resolution",
]

CAMERA_EFFECTS_SCENARIO_LIST = [
    ["On","Off","Off","AF","65536"],                     #(AF)        -scenarioID:65536
    ["Off","On","Off","EC","16"],                        #(EC)        -scenarioID:16
    ["Off","Off","On","BBS","96","True","False"],        #(BBS)       -scenarioID:96
    ["Off","Off","On","BBP","16416","False","True"],     #(BBP)       -scenarioID:16416
    ["On","On","Off","AF+EC","65552"],                   #(AF+EC)     -ScenarioID:65552
    ["On","Off","On","AF+BBS","65632","True","False"],   #(AF+BBS)    -scenarioID:65632
    ["On","Off","On","AF+BBP","81952","False","True"],   #(AF+BBP)    -scenarioID:81952
    ["Off","On","On","EC+BBS","112","True","False"],     #(EC+BBS)    -scenarioID:112
    ["Off","On","On","EC+BBP","16432","False","True"],   #(EC+BBP)    -scenarioID:16432
    ["On","On","On","AF+EC+BBS","65648","True","False"], #(AF+EC+BBS) -scenarioID:65648
    ["On","On","On","AF+EC+BBP","81968","False","True"], #(AF+EC+BBP) -scenarioID:81968
]

DEVICE_ORIENTATION = [
    "landscape",
    "portrait",
    "landscape_flipped",
    "portrait_flipped",
]

POWER_SIMULATION_STATUS = [
    "DC_power",
    "AC_power",
]

# the minimal threshold for FPS index in performance measurement
MINIMUM_FPS_THRESHOLD_IN_PERFORMANCE = 29

# the minimal threshold for time to 1st frmae in performance measurement
MINIMUM_TIME_TO_FIRST_FRAME_THRESHOLD_IN_PERFORMANCE = 1.250

# the minimal threshold for avg. processing time in performance measurement
MINIMUM_AVG_PROCESSING_TIME_THRESHOLD_IN_PERFORMANCE = 33

# the max height can apply MEP effects
MAXIMUM_MEP_RESOLUTION_HEIGHT = 1440

# the min height can apply MEP effects
MINIMUM_MEP_RESOLUTION_HEIGHT = 360

DEVELOPER_MODE_REG_KEY = "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock"
DEVELOPER_MODE_REG_NAME = "AllowDevelopmentWithoutDevLicense"
DEVELOPER_MODE_REG_TYPE = "REG_DWORD"


def checkConnection(host=IP_ADDR, port=PORT_NUMBER) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    r = s.connect_ex((host, port))
    s.close()
    return r == 0

def selectAllowDevelopmentWithoutDevLicense() -> str:
    result = subprocess.run(['reg', 'query', DEVELOPER_MODE_REG_KEY, '/v', DEVELOPER_MODE_REG_NAME], check=True, encoding='utf-8', stdout=subprocess.PIPE)
    return re.sub(r'\n|\r', r'', re.sub(r' +', r' ', result.stdout)).split(' ')[-1]

def updateAllowDevelopmentWithoutDevLicense(value=0):
    subprocess.run(['powershell', 'start-process', 'cmd.exe', f'"/c reg add {DEVELOPER_MODE_REG_KEY} /v {DEVELOPER_MODE_REG_NAME} /t {DEVELOPER_MODE_REG_TYPE} /d {value} /f"', '-verb runas'], check=True, shell=True)

def execWinAppDriver():
    subprocess.run(['start', 'WinAppDriver'], shell=True, cwd='C:\Program Files (x86)/Windows Application Driver')

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


def launchSettingApp():

    # Set desired capabilities to launch the Camera app
    desired_caps = {
        "app": "windows.immersivecontrolpanel_cw5n1h2txyewy!microsoft.windows.immersivecontrolpanel",
        "platformName": "Windows",
    }
    # Start the Windows Application Driver
    WindowsSettingAppDriver = webdriver.Remote(
        command_executor = REMOTE_TARGET,
        desired_capabilities = desired_caps)
    WindowsSettingAppDriver.implicitly_wait(IMPLICITLY_WAIT_TIME)
    return WindowsSettingAppDriver

def closeSettingApp(WindowsSettingAppDriver):

    # Close the Camera app
    CloseCameraButton = WindowsSettingAppDriver.find_element_by_name("Close Settings")
    CloseCameraButton.click()
    time.sleep(OPERATION_WAIT_DURATION)

    # Quit the Windows Application Driver
    WindowsSettingAppDriver.quit()

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

def switchCameraCheckMEPPackageExist(WindowsCameraAppDriver) -> bool:
    try:
        MEPEffects = WindowsCameraAppDriver.find_element_by_name("Windows Studio Effects")
    except NoSuchElementException:
        try:
            changeCameraButton = WindowsCameraAppDriver.find_element_by_accessibility_id("SwitchCameraButtonId")
        except NoSuchElementException:
            print("No MEP packages installed in this device, please check!!")
            closeCameraApp(WindowsCameraAppDriver)
            return False

        print("Not able to find MEP effects, switch to another camera!")
        changeCameraButton.click()
        time.sleep(OPERATION_WAIT_DURATION)
        try:
            MEPEffects = WindowsCameraAppDriver.find_element_by_name("Windows Studio Effects")
        except NoSuchElementException:
            print("No MEP packages installed in this device, please check!!")
            closeCameraApp(WindowsCameraAppDriver)
            return False

    return True

###############################################################################################################

###############################################################################################################

'''
    switchToVideoMode is to switch to video mode if current camera mode is not in video mode

    [input] handle of WinAppDriver
'''

def switchToVideoMode(WindowsCameraAppDriver) -> bool:
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
    return True


###############################################################################################################

###############################################################################################################

'''
    switchToPhotoMode is to switch to video mode if current camera mode is not in photo mode

    [input] handle of WinAppDriver
'''

def switchToPhotoMode(WindowsCameraAppDriver) -> bool:
    try:
        WindowsCameraAppDriver.find_element_by_name("Take photo")
    except NoSuchElementException:
        PhotoModeButtom = WindowsCameraAppDriver.find_element_by_name("Switch to photo mode")
        PhotoModeButtom.click()
        time.sleep(OPERATION_WAIT_DURATION)
    return True

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

def closeCameraEffectToggleButtonWithTakingAction(WindowsCameraAppDriver, mode : CameraMode) -> bool:

    # to close CameraEffectToggleButton
    try:
        LightDismissButton = WindowsCameraAppDriver.find_element_by_name("Close")
    except NoSuchElementException:
        print("can not find close button in MEP setting page")
        return False

    LightDismissButton.click()
    time.sleep(OPERATION_WAIT_DURATION)

    # to take video clips/photos
    if not takeVideosPhotos(WindowsCameraAppDriver, mode):
        print("take action fail")
        return False

    try:
        CameraEffectToggleButton = WindowsCameraAppDriver.find_element_by_name("Windows Studio Effects")
    except NoSuchElementException:
        print("can not find Windows Studio effects option")
        return False
    CameraEffectToggleButton.click()
    time.sleep(OPERATION_WAIT_DURATION)

    return True

###############################################################################################################

###############################################################################################################

'''
    takeVideosPhotos is to press taken button,
    if in VIDEO_MODE, need to wait for VIDEO_CAPTURE_DURATION and press STOP buttom to finish taking

    [input] handle of WinAppDriver
    [input] VIDEO_MODE or CAMERA_MODE
'''

def takeVideosPhotos(WindowsCameraAppDriver, mode : CameraMode) -> bool:

    if (mode == CameraMode.VIDEO_MODE):
        takenButtomStr = "Take video"
    else:
        takenButtomStr = "Take photo"

    time.sleep(OPERATION_WAIT_DURATION)
    try:
        takenButtom = WindowsCameraAppDriver.find_element_by_name(takenButtomStr)
    except NoSuchElementException:
        print("can not find", takenButtomStr, "button")
        return False
    time.sleep(OPERATION_WAIT_DURATION)

    takenButtom.click()
    # for video mode, we have to delay VIDEO_CAPTURE_DURATION for recording
    if (mode == CameraMode.VIDEO_MODE):
        time.sleep(WindowsCameraAppDriver.VIDEO_CAPTURE_DURATION)
        try:
            stopTakingVideoButtom = WindowsCameraAppDriver.find_element_by_name("Stop taking video")
        except NoSuchElementException:
            print("no Stop taking video button")
            return True
        stopTakingVideoButtom.click()
    time.sleep(OPERATION_WAIT_DURATION)

    return True

###############################################################################################################

###############################################################################################################

'''
    updateCameraEffectList is to get all MEP effects based on current MEP package or NPU socks,
    assume the "CameraEffectToggleButton" already been pressed

    [input] handle of WinAppDriver
'''

def updateCameraEffectList(WindowsCameraAppDriver) -> bool:
    if len(MEP_EFFECTS) == 0:
        try:
            toggleSwitchButtons = WindowsCameraAppDriver.find_elements_by_class_name("ToggleSwitch")
        except NoSuchElementException:
            print("can not find MEP effect options in Camera effect option")
            return False

        for switchButton in toggleSwitchButtons:
            MEP_EFFECTS.append(switchButton.text)
    return True

###############################################################################################################

###############################################################################################################

'''
    clearAllEffects is to clear all existing MEP effects from Windows settings,
    which to keep all combination of MEP effects can be verified,
    also assume the "CameraEffectToggleButton" already been pressed

    [input] handle of WinAppDriver
'''

def clearAllEffects(WindowsCameraAppDriver) -> bool:

    # to update effect list if necessary
    if not updateCameraEffectList(WindowsCameraAppDriver):
        print("updateCameraEffectList fail")
        return False

    # reset toggle button to OFF
    for effect in MEP_EFFECTS:
        if effect == "Background effects":
            try:
                toggleSwitchButtons = WindowsCameraAppDriver.find_elements_by_class_name("ToggleSwitch")
            except NoSuchElementException:
                print("can not find background blur radio option")
                return False
            mepEffectButton = toggleSwitchButtons[len(MEP_EFFECTS) - 1]
        else:
            try:
                mepEffectButton = WindowsCameraAppDriver.find_element_by_name(effect)
            except NoSuchElementException:
                print("can not find", effect)
                return False

        # un-toggle if the effect already been enabled
        if mepEffectButton.is_selected():
            mepEffectButton.click()
            time.sleep(OPERATION_WAIT_DURATION)

    return True

###############################################################################################################

###############################################################################################################

'''
    testEachCameraEffect is to clear all existing MEP effects from Windows settings,
    which to keep all single of MEP effects can be verified,
    also assume the "CameraEffectToggleButton" already been pressed

    [input] handle of WinAppDriver
    [input] VIDEO_MODE or CAMERA_MODE
'''

def testEachCameraEffect(WindowsCameraAppDriver, mode : CameraMode) -> bool:

    # To open CameraEffect windows
    CameraEffectToggleButton = WindowsCameraAppDriver.find_element_by_name("Windows Studio Effects")
    time.sleep(OPERATION_WAIT_DURATION)
    CameraEffectToggleButton.click()

    # reset toggle button to OFF
    if not clearAllEffects(WindowsCameraAppDriver):
        print("clearAllEffects fail")
        return False

    for idx, effect in enumerate(MEP_EFFECTS):
        try:
            mepEffectButton = WindowsCameraAppDriver.find_element_by_name(effect)
        except NoSuchElementException:
            print("can not find", effect)
            return False

        if effect == "Background effects":
            try:
                toggleSwitchButtons = WindowsCameraAppDriver.find_elements_by_class_name("ToggleSwitch")
            except NoSuchElementException:
                print("can not find", effect)
                return False
            mepEffectButton = toggleSwitchButtons[idx]

        mepEffectButton.click()
        time.sleep(OPERATION_WAIT_DURATION)

        if effect == "Background effects":
            for i, blurEffect in enumerate(BACKGROUND_EFFECTS):
                try:
                    blurEffectButton = WindowsCameraAppDriver.find_element_by_name(blurEffect)
                except NoSuchElementException:
                    print("can not find background blur radio option")
                    return False
                blurEffectButton.click()

                if not closeCameraEffectToggleButtonWithTakingAction(WindowsCameraAppDriver, mode):
                    print("closeCameraEffectToggleButtonWithTakingAction fail")
                    return False

                if (i == (len(BACKGROUND_EFFECTS) - 1)):
                    mepEffectButton.click()
                    time.sleep(OPERATION_WAIT_DURATION)
        else:
            if not closeCameraEffectToggleButtonWithTakingAction(WindowsCameraAppDriver, mode):
                print("closeCameraEffectToggleButtonWithTakingAction fail")
                return False
            mepEffectButton.click()
            time.sleep(OPERATION_WAIT_DURATION)

    try:
        LightDismissButton = WindowsCameraAppDriver.find_element_by_name("Close")
    except NoSuchElementException:
        print("can not find close button in MEP setting page")
        return False
    LightDismissButton.click()
    return True

###############################################################################################################

###############################################################################################################

'''
    testEachCameraEffectCombinations is to clear all existing MEP effects from Windows settings,
    which to keep all combination of MEP effects can be verified,
    also assume the "CameraEffectToggleButton" already been pressed

    [input] handle of WinAppDriver
    [input] VIDEO_MODE or CAMERA_MODE
'''

def testEachCameraEffectCombinations(WindowsCameraAppDriver, mode : CameraMode) -> bool:

    # To open CameraEffect windows
    CameraEffectToggleButton = WindowsCameraAppDriver.find_element_by_name("Windows Studio Effects")
    time.sleep(OPERATION_WAIT_DURATION)
    CameraEffectToggleButton.click()

    # reset toggle button to OFF
    if not clearAllEffects(WindowsCameraAppDriver):
        print("clear all existing effect fail")
        return False

    # generate all combinations for MEP effects
    ToggleButtonCombinations = []
    for r in range(len(MEP_EFFECTS)+1):
        ToggleButtonCombinations.extend(iter(itertools.combinations(MEP_EFFECTS, r)))

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
    return True

###############################################################################################################

###############################################################################################################

'''
    retrieveQualityList is to get videos/photos quality list,
    be aware that due to we collect all "ComboBoxItem" from quality settings,
    should remove flicker options from this list in video mode.

    [input] handle of WinAppDriver
    [input] VIDEO_MODE or CAMERA_MODE
    [input][output] list of available MEP effect index

    [output] list of all existing quality options
'''

def retrieveQualityList(WindowsCameraAppDriver, mode : CameraMode, qualityListsIdx) -> tuple:

    # query quality options
    qualityComboBoxItems = WindowsCameraAppDriver.find_elements_by_class_name("ComboBoxItem")
    qualityLists = []

    # there is "Flicker reduction" ComboBox in Video quality page,
    # to remove those flicker options to keep quality options only
    if (mode == CameraMode.VIDEO_MODE):
        for flicker in FLICKER_REDUCTION:
            for vq in qualityComboBoxItems:
                if (vq.text == flicker):
                    qualityComboBoxItems.remove(vq)

    for idx, item in enumerate(qualityComboBoxItems):
        qualityLists.append(item.text)
        height = 0
        if (mode == CameraMode.VIDEO_MODE):
            # 1080p, 16 by 9 aspect ratio, 30 fps
            pos = item.text.find("p")
            height = int(item.text[:pos])
        else:
            # 2.1 megapixels, 16 by 9 aspect ratio,  1920 by 1080 resolution
            pos = item.text.find(",  ")
            tmpStr = item.text[pos:]
            pos = tmpStr.find(" by ")
            height = int(tmpStr[pos+3:len(tmpStr)-11])

        if (height <= MAXIMUM_MEP_RESOLUTION_HEIGHT) and (height >= MINIMUM_MEP_RESOLUTION_HEIGHT):
            qualityListsIdx.append(idx)

    return qualityLists

###############################################################################################################

###############################################################################################################

'''
    removeFilesFromStorage is to remove all recorded files from given path
'''

def removeFilesFromStorage() -> bool:
    files = glob.glob(CAPTURE_FILE_FOLDER_PATH)
    for f in files:
        try:
            os.remove(f)
        except Exception:
            print("Error while deleting file ", f)
            return False
    return True

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
    [input] takeVideoClips to control whether taking video clips
            - 1 : to take video clips
            - 0 : not to take clips
    [input] videoCaptureDuration
            - the vidoe duraiton if to take video clip
'''

def testEffectsOnVariousQualities(mode : CameraMode, videoCaptureDuration) -> bool:

    # open AsgLogTrace to record log
    sp = subprocess.Popen('cmd.exe /c collect.cmd', stdin=subprocess.PIPE, cwd='.\\AsgTraceLog')

    # trying to open WindowsCamera app
    WindowsCameraAppDriver = launchCameraApp()
    if not WindowsCameraAppDriver:
        print("create WindowsCameraAppDriver fail")
        return False

    WindowsCameraAppDriver.VIDEO_CAPTURE_DURATION = videoCaptureDuration

    # Switch to correct mode if necessary
    if (mode == CameraMode.VIDEO_MODE):
        switchToVideoMode(WindowsCameraAppDriver)
    else:
        switchToPhotoMode(WindowsCameraAppDriver)

    # Open settings menu
    try:
        settingsButton = WindowsCameraAppDriver.find_element_by_name("Open Settings Menu")
    except NoSuchElementException:
        print("no Open Settings Menu button")
        return False
    settingsButton.click()
    time.sleep(OPERATION_WAIT_DURATION)

    # switch quality settings and click
    if (mode == CameraMode.VIDEO_MODE):
        settingStr = "Videos settings"
    else:
        settingStr = "Photos settings"

    try:
        qualitySettingsButton = WindowsCameraAppDriver.find_element_by_name(settingStr)
    except NoSuchElementException:
        print("no", settingStr, "option")
        return False
    qualitySettingsButton.click()
    time.sleep(OPERATION_WAIT_DURATION)

    # two combo box should be there: "Video quality" / "Flicker reduction" in videos settings
    # only one combo box there: "Photo quality"  in photos settings
    try:
        ComboBoxLists = WindowsCameraAppDriver.find_elements_by_class_name("ComboBox")
    except NoSuchElementException:
        print("no ComboBox option for qualities")
        return False

    # toggle quality option
    qualityButton = ComboBoxLists[0]
    qualityButton.click()
    time.sleep(OPERATION_WAIT_DURATION)

    # query quality options
    qualityListsIdx = []
    qualityLists = retrieveQualityList(WindowsCameraAppDriver, mode, qualityListsIdx)

    # test on various photo qualities
    for idx in qualityListsIdx:

        # Switch to target resolutions
        WindowsCameraAppDriver.find_element_by_name(qualityLists[idx]).click()
        time.sleep(OPERATION_WAIT_DURATION)

        # back to camera view
        try:
            backButton = WindowsCameraAppDriver.find_element_by_name("Back")
        except NoSuchElementException:
            print("no Back button in quality setting page")
            return False
        backButton.click()
        time.sleep(OPERATION_WAIT_DURATION)

        # return fail if no "Windows Studio effects" button found
        try:
            WindowsCameraAppDriver.find_element_by_name("Windows Studio Effects")
        except NoSuchElementException:
            print("no MEP effect button for resolution:", qualityLists[idx])
            return False

        # start to verify each photo effects for specific photo quality
        if (mode == CameraMode.VIDEO_MODE):
            qulityStr = "Videos Quality:"
        else:
            qulityStr = "Photos Quality:"
        print(qulityStr, qualityLists[idx])

        if not testEachCameraEffectCombinations(WindowsCameraAppDriver, mode):
            closeCameraApp(WindowsCameraAppDriver)
            print("testEachCameraEffectCombinations fail")
            return False

        # if necessary, open setting buttom again to switch another resolution
        if (idx != qualityListsIdx[-1]):
            settingsButton.click()
            time.sleep(OPERATION_WAIT_DURATION)
            qualityButton.click()
            time.sleep(OPERATION_WAIT_DURATION)

    closeCameraApp(WindowsCameraAppDriver)
    removeFilesFromStorage()

    # terminate AsgTraceLog
    sp.communicate(input=b'\n')
    sp.terminate()
    return True


###############################################################################################################

###############################################################################################################

'''
    startAsgTracing is to launch ASG tracing utility
'''

def startAsgTracing():

    waitFrameServerServiceStopped()

    # open AsgLogTrace to record log
    sp = subprocess.Popen('cmd.exe /c collect.cmd', stdin=subprocess.PIPE, cwd='.\\AsgTraceLog')
    time.sleep(OPERATION_WAIT_DURATION * 5)
    return sp


###############################################################################################################

###############################################################################################################

'''
    stopAsgTracing is to stop ASG tracing utility
'''

def stopAsgTracing(sp):

    waitFrameServerServiceStopped()

    # terminate AsgTraceLog
    sp.communicate(input=b'\n')
    sp.terminate()

    time.sleep(OPERATION_WAIT_DURATION * 5)


###############################################################################################################

###############################################################################################################

'''
    forceCameraUseSystemSettings is to switch Camera into desired mode and configure video quality for testing

    [input] VIDEO_MODE or CAMERA_MODE
    [input] videoQuality in VIDEO_MODE_QUALITY_LIST

    [output] bool value for the operation result:
             True: success
             False: fail (UI button disappear or the desired video quality is not available)
'''

def forceCameraUseSystemSettings(mode : CameraMode, videoQuality) -> bool:

    WindowsCameraAppDriver = launchCameraApp()

    # Open settings menu
    try:
        settingsButton = WindowsCameraAppDriver.find_element_by_name("Open Settings Menu")
    except NoSuchElementException:
        print("no Open Settings Menu button")
        return False
    settingsButton.click()

    expanderElements = WindowsCameraAppDriver.find_elements_by_class_name("Microsoft.UI.Xaml.Controls.Expander")
    for e in expanderElements:
        match e.text:
            case "Camera settings":
                cameraSettingsButton = e
            case "Video settings":
                videoSettingsButton = e
            case "Photo settings":
                photoSettingsButton = e

    if cameraSettingsButton:
        cameraSettingsButton.click()
        time.sleep(OPERATION_WAIT_DURATION)
    else:
        print("no Camera settings option")
        return False

    try:
        defaultSettingButton = WindowsCameraAppDriver.find_element_by_name("Default settings - These settings apply to the Camera app at the start of each session")
    except NoSuchElementException:
        print("no Default settings option")
        return False
    defaultSettingButton.click()
    time.sleep(OPERATION_WAIT_DURATION)

    try:
        useSystemSettingsButton = WindowsCameraAppDriver.find_element_by_name("Use system settings")
    except NoSuchElementException:
        print("no Use system settings option")
        return False
    useSystemSettingsButton.click()
    time.sleep(OPERATION_WAIT_DURATION)

    # switch quality settings and click
    if (mode == CameraMode.VIDEO_MODE):
        qualitySettingsButton = videoSettingsButton
    else:
        qualitySettingsButton = photoSettingsButton

    qualitySettingsButton.click()
    time.sleep(OPERATION_WAIT_DURATION)

    try:
        ComboBoxLists = WindowsCameraAppDriver.find_elements_by_class_name("ComboBox")
    except NoSuchElementException:
        print("no ComboBox option for qualities")
        return False

    for qualityButton in ComboBoxLists:
        if (qualityButton.text in VIDEO_MODE_QUALITY_LIST):
            qualityButton.click()
            time.sleep(OPERATION_WAIT_DURATION)
            break

    # query quality options
    qualityComboBoxItems = WindowsCameraAppDriver.find_elements_by_class_name("ComboBoxItem")
    bFoundTargetQuality = False

    for item in qualityComboBoxItems:
        if (item.text == videoQuality):
            item.click()
            bFoundTargetQuality = True
            break

    closeCameraApp(WindowsCameraAppDriver)
    return bFoundTargetQuality


###############################################################################################################

###############################################################################################################

'''
    toggleDesiredEffectInSettingsApp is to configure trageting scenatio in SettingApp

    [input] cameraScenario in CAMERA_EFFECTS_SCENARIO_LIST

    [output] bool value for the operation result:
             True: success
             False: fail (UI button disappear in SettingApp)
'''


def toggleDesiredEffectInSettingsApp(cameraScenario) -> bool:

    WindowsSettingAppDriver = launchSettingApp()

    if not WindowsSettingAppDriver:
        print("can not launch WindowsSetting App")
        return False

    try:
        btDevicesButton = WindowsSettingAppDriver.find_element_by_name("Bluetooth & devices")
    except NoSuchElementException:
        print("no Bluetooth & devices option")
        return False
    btDevicesButton.click()
    time.sleep(OPERATION_WAIT_DURATION)

    try:
        cCameraButton = WindowsSettingAppDriver.find_element_by_name("Connected cameras, default image settings")
    except NoSuchElementException:
        print("no Bluetooth & devices option")
        return False
    cCameraButton.click()
    time.sleep(OPERATION_WAIT_DURATION)

    try:
        cameraFrontButton = WindowsSettingAppDriver.find_element_by_name("More")
    except NoSuchElementException:
        print("no Bluetooth & devices option")
        return False
    cameraFrontButton.click()
    time.sleep(OPERATION_WAIT_DURATION)

    toggleSwitchButtons = WindowsSettingAppDriver.find_elements_by_class_name("ToggleSwitch")
    for button in toggleSwitchButtons:
        match button.text:
            case "Automatic framing":
                autoFramingButton = button
            case "Eye contact":
                eyeContactButton = button
            case "Background effects":
                backgroundEffectButton = button

    radioButtons = WindowsSettingAppDriver.find_elements_by_class_name("RadioButton")
    for button in radioButtons:
        match button.text:
            case "Standard blur":
                standardBlurButton = button
            case "Portrait blur":
                portraitBlurButton = button

    # for AF
    if autoFramingButton:
        if (((cameraScenario[0] == "On") and (not autoFramingButton.is_selected())) or
            ((cameraScenario[0] == "Off") and (autoFramingButton.is_selected()))):
            autoFramingButton.click()
            time.sleep(OPERATION_WAIT_DURATION)

    # for EC
    if eyeContactButton:
        if (((cameraScenario[1] == "On") and (not eyeContactButton.is_selected())) or
            ((cameraScenario[1] == "Off") and (eyeContactButton.is_selected()))):
            eyeContactButton.click()
            time.sleep(OPERATION_WAIT_DURATION)

    # for BBS/BBP
    if backgroundEffectButton:
        if (((cameraScenario[2] == "On") and (not backgroundEffectButton.is_selected())) or
            ((cameraScenario[2] == "Off") and (backgroundEffectButton.is_selected()))):
            backgroundEffectButton.click()
            time.sleep(OPERATION_WAIT_DURATION)

        if backgroundEffectButton.is_selected():
            if cameraScenario[5] == "True":
                standardBlurButton.click()
            else:
                portraitBlurButton.click()
            time.sleep(OPERATION_WAIT_DURATION)

    closeSettingApp(WindowsSettingAppDriver)

    return True


###############################################################################################################

###############################################################################################################

'''
    writeResultsToExcelFile is to collect the performance indice into excel file for record

    [input] excelFileInfo is the targeting excel file information
    [input] quality: video quality
    [input] scenario: testing scenario
    [input] fps: Frame per second (should be less than MINIMUM_FPS_THRESHOLD_IN_PERFORMANCE)
    [input] firstFrame: time to capture 1st frame (should be less than MINIMUM_TIME_TO_FIRST_FRAME_THRESHOLD_IN_PERFORMANCE)
    [input] avgP: average processing time
    [input] minP: minimal processing time
    [input] maxP: maximal processing time
    [input] numOfFrameAbove33: number of frames exceed 33ms processing time (should be 0 in ideal case)

'''


def writeResultsToExcelFile(excelFileInfo: ExcelFileIfo, quality, scenario, fps, firstFrame, avgP, minP, maxP, numOfFrameAbove33):
    colIdx = 0

    excelFileInfo.outputExcelCurWorkSheet.write(excelFileInfo.outputExcelRowIdx, colIdx, quality)
    colIdx += 1

    excelFileInfo.outputExcelCurWorkSheet.write(excelFileInfo.outputExcelRowIdx, colIdx, scenario)
    colIdx += 1

    if fps < MINIMUM_FPS_THRESHOLD_IN_PERFORMANCE or fps == -1:
        excelFileInfo.outputExcelCurWorkSheet.write(excelFileInfo.outputExcelRowIdx, colIdx, format(fps, ".2f"), excelFileInfo.noticeFormat)
    else:
        excelFileInfo.outputExcelCurWorkSheet.write(excelFileInfo.outputExcelRowIdx, colIdx, format(fps, ".2f"))
    colIdx += 1

    if firstFrame == -1:
        excelFileInfo.outputExcelCurWorkSheet.write(excelFileInfo.outputExcelRowIdx, colIdx, "None", excelFileInfo.noticeFormat)
    elif firstFrame > MINIMUM_TIME_TO_FIRST_FRAME_THRESHOLD_IN_PERFORMANCE:
        excelFileInfo.outputExcelCurWorkSheet.write(excelFileInfo.outputExcelRowIdx, colIdx, format(firstFrame, ".3f"), excelFileInfo.noticeFormat)
    else:
        excelFileInfo.outputExcelCurWorkSheet.write(excelFileInfo.outputExcelRowIdx, colIdx, format(firstFrame, ".3f"))
    colIdx += 1

    if avgP > MINIMUM_AVG_PROCESSING_TIME_THRESHOLD_IN_PERFORMANCE or avgP == -1:
        excelFileInfo.outputExcelCurWorkSheet.write(excelFileInfo.outputExcelRowIdx, colIdx, format(avgP, ".2f"), excelFileInfo.noticeFormat)
    else:
        excelFileInfo.outputExcelCurWorkSheet.write(excelFileInfo.outputExcelRowIdx, colIdx, format(avgP, ".2f"))
    colIdx += 1

    if minP == -1:
        excelFileInfo.outputExcelCurWorkSheet.write(excelFileInfo.outputExcelRowIdx, colIdx, format(minP, ".2f"), excelFileInfo.noticeFormat)
    else:
        excelFileInfo.outputExcelCurWorkSheet.write(excelFileInfo.outputExcelRowIdx, colIdx, format(minP, ".2f"))
    colIdx += 1

    if maxP == -1:
        excelFileInfo.outputExcelCurWorkSheet.write(excelFileInfo.outputExcelRowIdx, colIdx, format(maxP, ".2f"), excelFileInfo.noticeFormat)
    else:
        excelFileInfo.outputExcelCurWorkSheet.write(excelFileInfo.outputExcelRowIdx, colIdx, format(maxP, ".2f"))
    colIdx += 1

    if numOfFrameAbove33 > 0 or numOfFrameAbove33 == -1:
        excelFileInfo.outputExcelCurWorkSheet.write(excelFileInfo.outputExcelRowIdx, colIdx, numOfFrameAbove33, excelFileInfo.noticeFormat)
    else:
        excelFileInfo.outputExcelCurWorkSheet.write(excelFileInfo.outputExcelRowIdx, colIdx, numOfFrameAbove33)
    colIdx += 1


###############################################################################################################

###############################################################################################################

'''
    getTimeToFirstFrameInfo is to calculate time to 1st frame according to timestamps of below two log:
    startLogStr with pattern "starting Microsoft.ASG.Perception provider"
    stopLogStr with pattren "First frame for PerceptionCore instance "

    [input] startLogStr
    [input] stopLogStr

    [output] the cost of time to 1st frame in second with floating format

'''


def getTimeToFirstFrameInfo(startLogStr, stopLogStr) -> float:
    # datatime: 2023/06/01 06:43:05.594
    fmt = '%Y/%m/%d %H:%M:%S.%f'
    tokens = startLogStr.split(", ")
    startStr = tokens[3]
    tokens = stopLogStr.split(", ")
    stoptStr = tokens[3]
    tstampStart = datetime.strptime(startStr, fmt)
    tstampStop = datetime.strptime(stoptStr, fmt)
    return (tstampStop - tstampStart).total_seconds()


###############################################################################################################

###############################################################################################################

'''
    outputPerformanceIndex is to create new folder to store video clip/asg trace,
    and parse the result asg file for performance index

    [input] videoQuality in VIDEO_MODE_QUALITY_LIST
    [input] cameraScenario in CAMERA_EFFECTS_SCENARIO_LIST
    [input] excelFileInfo is the infomation of writing excel file (performance record)

    [output] bool value for the operation result:
             True: success
             False: fail (asg tracing fail due to wrong scenario id)
'''


def outputPerformanceIndex(videoQuality, cameraScenario, excelFileInfo: ExcelFileIfo) -> bool:

    pos = videoQuality.find(", ")
    targetFolderPathWithQuality = f"{excelFileInfo.targetFolderPath}\{videoQuality[:pos]}"
    if not os.path.isdir(targetFolderPathWithQuality):
        os.makedirs(targetFolderPathWithQuality)
    scenarioLogPath = f"{targetFolderPathWithQuality}\{cameraScenario[3]}"
    if not os.path.isdir(scenarioLogPath):
        os.makedirs(scenarioLogPath)

    # fetch frame rate from video clip
    files = glob.glob(CAPTURE_FILE_VIDEO_TYPES)
    try:
        props = get_video_properties(files[0])
        shutil.copy2(files[0], scenarioLogPath)

        frameRateStr = props['avg_frame_rate']
        pos = frameRateStr.find("/")
        denominator = int(frameRateStr[pos+1:])
        numerator = int(frameRateStr[:pos])
        avgFPS = (numerator/denominator)
    except Exception:
        print("video clip broken")
        avgFPS = -1

    cameraScenarioId = cameraScenario[4]

    timeToInitializeFirstFrame = -1
    minProcessingTimePerFrame = -1
    avgProcessingTimePerFrame = -1
    maxProcessingTimePerFrame = -1
    numberOfFramesAbove33ms = -1

    regExpStart = "(.)+starting Microsoft.ASG.Perception provider"
    regExpEnd = "(.)+, First frame for PerceptionCore instance"
    regExp = fr"(.)+::PerceptionSessionUsageStats,(.)+PerceptionCore-(.)+{cameraScenarioId}"
    startLogStr = ""
    stopLogStr = ""
    perfStr = ""
    shutil.copy2(r".\\AsgTraceLog\\AsgTrace.txt", scenarioLogPath)
    with open(r".\\AsgTraceLog\\AsgTrace.txt", 'r') as fp:
        for line in fp:
            # search string
            if re.search(regExpStart, line):
                startLogStr = line
            elif re.search(regExpEnd, line):
                stopLogStr = line
            elif re.search(regExp, line):
                perfStr = line
                break

    if startLogStr and stopLogStr:
        timeToInitializeFirstFrame = getTimeToFirstFrameInfo(startLogStr, stopLogStr)

    pos = videoQuality.find(", ")
    if perfStr:
        tokens = perfStr.split(", ")
        minProcessingTimePerFrame = (int(tokens[12]) / 1000000)  # minProcessingTimePerFrame
        avgProcessingTimePerFrame = (int(tokens[11]) / 1000000)  # avgProcessingTimePerFrame
        maxProcessingTimePerFrame = (int(tokens[13]) / 1000000)  # maxProcessingTimePerFrame
        numberOfFramesAbove33ms = int(tokens[20])  #numberOfFramesAbove33ms
    else:
        print(videoQuality[:pos], cameraScenario[3], "test fail, ASG trace log error\n")
        return False

    excelFileInfo.outputExcelRowIdx += 1
    # print(
    #     videoQuality[:pos],
    #     cameraScenario[3],
    #     "result:\n" "FPS:",
    #     avgFPS,
    #     "timeToInitialize1stFrame:",
    #     timeToInitializeFirstFrame,
    #     ", processTimePerFrame[avg, min, max]: [",
    #     avgProcessingTimePerFrame,
    #     "ms,",
    #     minProcessingTimePerFrame,
    #     "ms,",
    #     maxProcessingTimePerFrame,
    #     "ms ]",
    #     "numberOfFramesAbove33ms:",
    #     numberOfFramesAbove33ms,
    # )
    writeResultsToExcelFile(
        excelFileInfo,
        videoQuality[:pos],
        cameraScenario[3],
        avgFPS,
        timeToInitializeFirstFrame,
        avgProcessingTimePerFrame,
        minProcessingTimePerFrame,
        maxProcessingTimePerFrame,
        numberOfFramesAbove33ms,
    )
    return True


###############################################################################################################

###############################################################################################################

'''
    cameraRecordingAction is to enalbe ASG tracing as well as taking video within CameraApp,
    also parsing asg trace result for performance analysis

    [input] VIDEO_MODE or CAMERA_MODE
    [input] videoQuality in VIDEO_MODE_QUALITY_LIST
    [input] cameraScenario in CAMERA_EFFECTS_SCENARIO_LIST
    [input] videoCaptureDuration is the recording time for video clip, can be tweak via environment variable(VIDEO_CAPTURE_DURATION)
    [input] excelFileInfo is the infomation of writing excel file (performance record)

    [output] bool value for the operation result:
             True: success
             False: fail (asg tracing fail or taking video fail)
'''


def  cameraRecordingAction(mode : CameraMode, videoQuality, cameraScenario, videoCaptureDuration, excelFileInfo: ExcelFileIfo) -> bool:

    sp = startAsgTracing()

    # trying to open WindowsCamera app
    WindowsCameraAppDriver = launchCameraApp()
    if not WindowsCameraAppDriver:
        print("create WindowsCameraAppDriver fail")
        return False

    # Switch to correct mode if necessary
    if (mode == CameraMode.VIDEO_MODE):
        switchToVideoMode(WindowsCameraAppDriver)
    else:
        switchToPhotoMode(WindowsCameraAppDriver)

    WindowsCameraAppDriver.VIDEO_CAPTURE_DURATION = videoCaptureDuration

    # taking video...
    retCode = takeVideosPhotos(WindowsCameraAppDriver, mode)
    if not retCode:
        print("takeVideosPhotos fail")

    switchToPhotoMode(WindowsCameraAppDriver)
    closeCameraApp(WindowsCameraAppDriver)
    stopAsgTracing(sp)

    retCode = retCode and outputPerformanceIndex(videoQuality, cameraScenario, excelFileInfo)

    removeFilesFromStorage()

    return retCode


###############################################################################################################

###############################################################################################################

'''
    testPerformanceForQualityScenario is to test the target scenario with corresponding video quality

    [input] VIDEO_MODE or CAMERA_MODE
    [input] videoQuality in VIDEO_MODE_QUALITY_LIST
    [input] cameraScenario in CAMERA_EFFECTS_SCENARIO_LIST
    [input] videoCaptureDuration is the recording time for video clip, can be tweak via environment variable(VIDEO_CAPTURE_DURATION)
    [input] excelFileInfo is the infomation of writing excel file (performance record)

    [output] bool value for the operation result:
             True: success
             False: fail (UI button disappear in SettingApp or taking video fail in CameraApp)
'''

def testPerformanceForQualityScenario(mode : CameraMode, videoQuality, cameraScenario, videoCaptureDuration, excelFileInfo: ExcelFileIfo) -> bool:

    if not toggleDesiredEffectInSettingsApp(cameraScenario):
        return False

    return cameraRecordingAction(mode, videoQuality, cameraScenario, videoCaptureDuration, excelFileInfo)


###############################################################################################################

###############################################################################################################

'''
    waitFrameServerServiceStopped is to wait until frame server status switch to stop
'''
def getService(name):

    service = None
    try:
        service = psutil.win_service_get(name)
        service = service.as_dict()
    except Exception as ex:
        print(ex)
    return service

def waitFrameServerServiceStopped():

    while True:
        service = getService('frameserver')
        if (service['status'] != "stopped"):
            time.sleep(OPERATION_WAIT_DURATION)
        else:
            break

###############################################################################################################

###############################################################################################################
class CameraEffectsTests(unittest.TestCase):

    # the number of iterations for veryfying both videos/photos MEP effects
    NUMBER_OF_TEST_ITERATIONS = 100

    # the duration (in second) of video recording
    VIDEO_CAPTURE_DURATION = 20

    @classmethod
    def setUpClass(cls):

        # if (selectAllowDevelopmentWithoutDevLicense() == '0x0'):
        #     updateAllowDevelopmentWithoutDevLicense(1)
        #     time.sleep(1)
        #     print(f'updateAllowDevelopmentWithoutDevLicense:{selectAllowDevelopmentWithoutDevLicense()}')

        # if (not checkConnection()):
        #     execWinAppDriver()

        timeStr = datetime.fromtimestamp(datetime.now().timestamp()).strftime("%Y-%m-%d, %H:%M:%S")
        print("start CameraEffectsTests [", timeStr, "]")

        if "VIDEO_CAPTURE_DURATION" in os.environ:
            cls.VIDEO_CAPTURE_DURATION = int(os.environ["VIDEO_CAPTURE_DURATION"])
        if "NUMBER_TEST_ITERATIONS" in os.environ:
            cls.NUMBER_OF_TEST_ITERATIONS = int(os.environ["NUMBER_TEST_ITERATIONS"])

    @classmethod
    def tearDownClass(cls):

        timeStr = datetime.fromtimestamp(datetime.now().timestamp()).strftime("%Y-%m-%d, %H:%M:%S")
        print("finish CameraEffectsTests[", timeStr, "]")

        # if ((not checkConnection()) and (selectAllowDevelopmentWithoutDevLicense() == '0x1')):
        #     updateAllowDevelopmentWithoutDevLicense(0)
        #     time.sleep(OPERATION_WAIT_DURATION)
        #     print(f'updateAllowDevelopmentWithoutDevLicense:{selectAllowDevelopmentWithoutDevLicense()}')


    def run_photo_video_test(self):
        self.assertTrue(testEffectsOnVariousQualities(CameraMode.PHOTO_MODE, 0))
        time.sleep(OPERATION_WAIT_DURATION)
        self.assertTrue(testEffectsOnVariousQualities(CameraMode.VIDEO_MODE, self.VIDEO_CAPTURE_DURATION))
        time.sleep(OPERATION_WAIT_DURATION)

    def test_functional_video_mode(self):
        # CameraMode.VIDEO_MODE: to verity MEP effects on videos
        self.assertTrue(testEffectsOnVariousQualities(CameraMode.VIDEO_MODE, self.VIDEO_CAPTURE_DURATION))

    def test_functional_photo_mode(self):
        # CameraMode.PHOTO_MODE: to verity MEP effects on photos
        self.assertTrue(testEffectsOnVariousQualities(CameraMode.PHOTO_MODE, 0))

    def test_orientation_combinations(self):
        screen = rotatescreen.get_primary_display()
        curOrientation = screen.current_orientation

        for _ in range(3):
            screen.rotate_to((screen.current_orientation + 90) % 360)
            print("test rotate degree", screen.current_orientation)
            self.run_photo_video_test()

        print("revert to", curOrientation)
        screen.rotate_to(curOrientation)

    def test_power_DC_power_simulation(self):
        print("simulate 50% DC")
        subprocess.Popen('cmd.exe /c cmd.exe /c enableDCPowerSimulation.vbs', cwd='.\\vbs').wait()
        self.run_photo_video_test()
        subprocess.Popen('cmd.exe /c cmd.exe /c disablePowerSimulation.vbs', cwd='.\\vbs').wait()

    def test_power_AC_power_simulation(self):
        print("simulate 100% AC")
        subprocess.Popen('cmd.exe /c cmd.exe /c enableACPowerSimulation.vbs', cwd='.\\vbs').wait()
        self.run_photo_video_test()
        subprocess.Popen('cmd.exe /c cmd.exe /c disablePowerSimulation.vbs', cwd='.\\vbs').wait()

    def test_stress_video_photo_mode_iterations(self):
        print("STRESS TEST for", self.NUMBER_OF_TEST_ITERATIONS, "runs")
        for i in range(self.NUMBER_OF_TEST_ITERATIONS):
            timeStr = datetime.fromtimestamp(datetime.now().timestamp()).strftime("%Y-%m-%d, %H:%M:%S")
            print("\nINTERATION [", (i + 1), " / ", self.NUMBER_OF_TEST_ITERATIONS,"], TIME:", timeStr)
            self.run_photo_video_test()

    def test_performance_video(self):

        timeStr = datetime.fromtimestamp(datetime.now().timestamp()).strftime("%Y-%m-%d (%H.%M)")

        logFolderPath = f"{os.getcwd()}\{timeStr}"
        if not os.path.isdir(logFolderPath):
            os.makedirs(logFolderPath)

        txtFileName = f".\{timeStr}\\testResult.txt"
        txtFp = open(txtFileName, 'w')

        excelFileName = f"{timeStr}.xlsx"
        excelFileInfo = ExcelFileIfo()
        excelFileInfo.outputExcelFp = xlsxwriter.Workbook(excelFileName)
        excelFileInfo.noticeFormat = excelFileInfo.outputExcelFp.add_format({'bold':True, 'font_color':'red'})

        retCode = True

        # go through all power criterias
        for power in POWER_SIMULATION_STATUS:

            if (power == "AC_power"):
                subprocess.Popen('cmd.exe /c cmd.exe /c enableACPowerSimulation.vbs', cwd='.\\vbs').wait()
            elif (power == "DC_power"):
                subprocess.Popen('cmd.exe /c cmd.exe /c enableDCPowerSimulation.vbs', cwd='.\\vbs').wait()
            time.sleep(OPERATION_WAIT_DURATION)

            # go through four different simulated orientations
            for orientation in DEVICE_ORIENTATION:
                screen = rotatescreen.get_primary_display()
                curOrientation = screen.current_orientation

                if (orientation == "portrait"):
                    targetOrientation = (screen.current_orientation + 90) % 360
                elif (orientation == "landscape_flipped"):
                    targetOrientation = (screen.current_orientation + 180) % 360
                elif (orientation == "portrait_flipped"):
                    targetOrientation = (screen.current_orientation + 270) % 360
                else:
                    targetOrientation = (screen.current_orientation) % 360

                screen.rotate_to(targetOrientation)
                time.sleep(OPERATION_WAIT_DURATION)

                # create a excel file to record all performance results
                excelFileInfo.outputExcelCurWorkSheet = excelFileInfo.outputExcelFp.add_worksheet(f"{power}_{orientation}")
                excelFileInfo.outputExcelRowIdx = 0
                workSheetTitleList = [
                    "Quality",
                    "Scenario",
                    "FPS",
                    "timeToFirstFrame",
                    "avgProcessingTimePerFrame",
                    "minProcessingTimePerFrame",
                    "maxProcessingTimePerFrame",
                    "numberOfFramesAbove33ms"
                ]
                excelFileInfo.outputExcelCurWorkSheet.write_row(
                    excelFileInfo.outputExcelRowIdx,
                    0,
                    workSheetTitleList
                )

                # prepare the output folder path, which contains recorded video clips and corresponding asgTrace files under different qualities and scenarios
                targetFolderPath = f"{logFolderPath}\{power}_{orientation}"
                if not os.path.isdir(targetFolderPath):
                    os.makedirs(targetFolderPath)
                excelFileInfo.targetFolderPath = targetFolderPath

                for videoQuality in VIDEO_MODE_QUALITY_LIST:
                    pos = videoQuality.find(", ")
                    if not forceCameraUseSystemSettings(CameraMode.VIDEO_MODE, videoQuality):
                        txtLog = f"{power}\{orientation}\{videoQuality[:pos]}: Skipped\n"
                        txtFp.write(txtLog)
                        continue

                    for cameraScenario in CAMERA_EFFECTS_SCENARIO_LIST:
                        ret = testPerformanceForQualityScenario(CameraMode.VIDEO_MODE, videoQuality, cameraScenario, self.VIDEO_CAPTURE_DURATION, excelFileInfo)
                        if not ret:
                            txtLog = f"{power}\{orientation}\{videoQuality[:pos]}\{cameraScenario[3]}: Failed\n"
                        else:
                            txtLog = f"{power}\{orientation}\{videoQuality[:pos]}\{cameraScenario[3]}: Passed\n"
                        txtFp.write(txtLog)
                        retCode = retCode or ret

                screen.rotate_to(curOrientation)
                time.sleep(OPERATION_WAIT_DURATION)

            subprocess.Popen('cmd.exe /c cmd.exe /c disablePowerSimulation.vbs', cwd='.\\vbs').wait()
            time.sleep(OPERATION_WAIT_DURATION)

        txtFp.close()
        excelFileInfo.outputExcelFp.close()
        self.assertTrue(retCode)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(CameraEffectsTests)
    unittest.TextTestRunner(verbosity=2).run(suite)

