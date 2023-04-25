import time
import os
import glob
import re
import socket
import subprocess
import unittest
import itertools
import rotatescreen
from appium import webdriver
from selenium.common.exceptions import NoSuchElementException
from enum import Enum
from datetime import datetime

###############################################################################################################

# Here is to define constant values
IP_ADDR = "127.0.0.1"
PORT_NUMBER = 4723
REMOTE_TARGET = "http://" + IP_ADDR + ":" + str(PORT_NUMBER)

CAPTURE_FILE_FOLDER_PATH = "C:\\Users\\" + os.getlogin() + "\\Pictures\\Camera Roll\\*"

# the duration (in second) of video recording
VIDEO_CAPTURE_DURATION = 30

# the amount of delay (in second) for each operation
OPERATION_WAIT_DURATION = 1

# the number of iterations for veryfying both videos/photos MEP effects
NUMBER_OF_TEST_ITERATIONS = 1000

# to take video/photo or not,
# 0: not to take
# 1: to take
TAKE_VIDEOS_PHOTOS_ACTION = 1

# the number of seconds for operation torrelance
IMPLICITLY_WAIT_TIME = 5

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
        MEPEffects = WindowsCameraAppDriver.find_element_by_name("Windows Studio effects")
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
            MEPEffects = WindowsCameraAppDriver.find_element_by_name("Windows Studio effects")
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
        CameraEffectToggleButton = WindowsCameraAppDriver.find_element_by_name("Windows Studio effects")
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

    try:
        takenButtom = WindowsCameraAppDriver.find_element_by_name(takenButtomStr)
    except NoSuchElementException:
        print("can not find", takenButtomStr, "button")
        return False
    takenButtom.click()
    time.sleep(OPERATION_WAIT_DURATION)

    # for video mode, we have to delay VIDEO_CAPTURE_DURATION for recording
    if (mode == CameraMode.VIDEO_MODE):
        time.sleep(VIDEO_CAPTURE_DURATION)
        try:
            stopTakingVideoButtom = WindowsCameraAppDriver.find_element_by_name("Stop taking video")
        except NoSuchElementException:
            print("no Stop taking video button")
            return False
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
    CameraEffectToggleButton = WindowsCameraAppDriver.find_element_by_name("Windows Studio effects")
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
    CameraEffectToggleButton = WindowsCameraAppDriver.find_element_by_name("Windows Studio effects")
    time.sleep(OPERATION_WAIT_DURATION)
    CameraEffectToggleButton.click()

    # reset toggle button to OFF
    if not clearAllEffects(WindowsCameraAppDriver):
        print("clear all existing effect fail")
        return False

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
            height = int(item.text[0:pos])
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
        except:
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
'''

def testEffectsOnVariousQualities(mode : CameraMode) -> bool:

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
            WindowsCameraAppDriver.find_element_by_name("Windows Studio effects")
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
    return True


def testVideoRecordingChecking() -> bool:

    # trying to open WindowsCamera app
    WindowsCameraAppDriver = launchCameraApp()
    if not WindowsCameraAppDriver:
        print("create WindowsCameraAppDriver fail")
        return False

    while True:
        try:
            takenButtom = WindowsCameraAppDriver.find_element_by_name("Take video")
        except NoSuchElementException:
            print("can not find taking video button")
            return False
        takenButtom.click()
        time.sleep(OPERATION_WAIT_DURATION)

        # for video mode, we have to delay VIDEO_CAPTURE_DURATION for recording
        time.sleep(VIDEO_CAPTURE_DURATION)

        try:
            stopTakingVideoButtom = WindowsCameraAppDriver.find_element_by_name("Stop taking video")
        except NoSuchElementException:
            print("no Stop taking video button")
            return False
        stopTakingVideoButtom.click()
        time.sleep(OPERATION_WAIT_DURATION)

    closeCameraApp(WindowsCameraAppDriver)
    removeFilesFromStorage()
    return True

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
class CameraEffectsTests(unittest.TestCase):

    @classmethod
    def setUpClass(self):

        if (selectAllowDevelopmentWithoutDevLicense() == '0x0'):
            updateAllowDevelopmentWithoutDevLicense(1)
            time.sleep(1)
            print(f'updateAllowDevelopmentWithoutDevLicense:{selectAllowDevelopmentWithoutDevLicense()}')

        # if (not checkConnection()):
        execWinAppDriver()

        timeStr = datetime.fromtimestamp(datetime.now().timestamp()).strftime("%Y-%m-%d, %H:%M:%S")
        print("start CameraEffectsTests [", timeStr, "]")
        removeFilesFromStorage()

    @classmethod
    def tearDownClass(self):

        timeStr = datetime.fromtimestamp(datetime.now().timestamp()).strftime("%Y-%m-%d, %H:%M:%S")
        print("finish CameraEffectsTests[", timeStr, "]")

        if ((not checkConnection()) and (selectAllowDevelopmentWithoutDevLicense() == '0x1')):
            updateAllowDevelopmentWithoutDevLicense(0)
            time.sleep(OPERATION_WAIT_DURATION)
            print(f'updateAllowDevelopmentWithoutDevLicense:{selectAllowDevelopmentWithoutDevLicense()}')

    # def test_a_functional_video_mode(self):
    #     # CameraMode.VIDEO_MODE: to verity MEP effects on videos
    #     self.assertEqual(testEffectsOnVariousQualities(CameraMode.VIDEO_MODE), True)

    def test_b_functional_photo_mode(self):
        # CameraMode.PHOTO_MODE: to verity MEP effects on photos
        self.assertEqual(testEffectsOnVariousQualities(CameraMode.PHOTO_MODE), True)

    # def test_c_orientation_combinations(self):
    #     screen = rotatescreen.get_primary_display()
    #     curOrientation = screen.current_orientation
    #     print("test landscape")
    #     screen.set_landscape()
    #     self.assertEqual(testEffectsOnVariousQualities(CameraMode.PHOTO_MODE), True)
    #     self.assertEqual(testEffectsOnVariousQualities(CameraMode.VIDEO_MODE), True)
    #     print("test portrait")
    #     screen.set_portrait()
    #     self.assertEqual(testEffectsOnVariousQualities(CameraMode.PHOTO_MODE), True)
    #     self.assertEqual(testEffectsOnVariousQualities(CameraMode.VIDEO_MODE), True)
    #     print("test landscape_flipped")
    #     screen.set_landscape_flipped()
    #     self.assertEqual(testEffectsOnVariousQualities(CameraMode.PHOTO_MODE), True)
    #     self.assertEqual(testEffectsOnVariousQualities(CameraMode.VIDEO_MODE), True)
    #     print("test portrait_flipped")
    #     screen.set_portrait_flipped()
    #     self.assertEqual(testEffectsOnVariousQualities(CameraMode.PHOTO_MODE), True)
    #     self.assertEqual(testEffectsOnVariousQualities(CameraMode.VIDEO_MODE), True)
    #     print("revert to", curOrientation)
    #     screen.rotate_to(curOrientation)

    # def test_d_power_combinations(self):
    #     print("simulate 50% DC")
    #     os.system(r".\\enableDCPowerSimulation.vbs")
    #     self.assertEqual(testEffectsOnVariousQualities(CameraMode.PHOTO_MODE), True)
    #     self.assertEqual(testEffectsOnVariousQualities(CameraMode.VIDEO_MODE), True)
    #     print("simulate 100% AC")
    #     os.system(r".\\enableACPowerSimulation.vbs")
    #     self.assertEqual(testEffectsOnVariousQualities(CameraMode.PHOTO_MODE), True)
    #     self.assertEqual(testEffectsOnVariousQualities(CameraMode.VIDEO_MODE), True)
    #     print("disable power simulation")
    #     os.system(r".\\disablePowerSimulation.vbs")

    # def test_e_stress_video_photo_mode_iterations(self):
    #     for i in range(NUMBER_OF_TEST_ITERATIONS):
    #         timeStr = datetime.fromtimestamp(datetime.now().timestamp()).strftime("%Y-%m-%d, %H:%M:%S")
    #         print("\nINTERATION [", (i + 1), " / ", NUMBER_OF_TEST_ITERATIONS,"], TIME:", timeStr)
    #         self.assertEqual(testEffectsOnVariousQualities(CameraMode.VIDEO_MODE), True)
    #         time.sleep(OPERATION_WAIT_DURATION)
    #         self.assertEqual(testEffectsOnVariousQualities(CameraMode.PHOTO_MODE), True)
    #         time.sleep(OPERATION_WAIT_DURATION)

    # def test_conti_recording(self):
    #     testVideoRecordingChecking()

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(CameraEffectsTests)
    unittest.TextTestRunner(verbosity=2).run(suite)
