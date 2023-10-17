import cv2
import win32gui
import win32ui
import numpy as np
import mss
import sys

from win32gui import FindWindow, GetWindowRect, SetForegroundWindow
from time import sleep
from pynput import mouse
from pynput.mouse import Button
from pynput.keyboard import Controller
from string_encoded_images import *
from fuzzywuzzy import fuzz
from ctypes import windll
from pytimedinput import timedInput
from localStoragePy import localStoragePy
from PIL import Image
from LolChampions import CHAMPIONS
from cv2 import Mat

WINDOW_NAME = "League of Legends"



def screenshot_of_app_in_background(window_name: str):
    hwnd = win32gui.FindWindow(None, window_name)
    x, y, width, height = get_lol_position()
    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()

    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
    saveDC.SelectObject(saveBitMap)
    result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)
    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)
    im = Image.frombuffer(
        "RGB", (bmpinfo["bmWidth"], bmpinfo["bmHeight"]), bmpstr, "raw", "BGRX", 0, 1
    )

    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwndDC)
    return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2GRAY)


def get_lol_position():
    window_handle = FindWindow(None, WINDOW_NAME)
    return GetWindowRect(window_handle)


def match_template(Image: Mat, template: Mat, threshold=0.9):
    res = cv2.matchTemplate(Image, template, cv2.TM_CCORR_NORMED)
    h, w = template.shape
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    cv2.waitKey()
    if max_val > threshold:
        return True, max_loc, w, h
    return False, [], 0, 0


def mouseClick(x: int, y: int):
    mouseController = mouse.Controller()
    mouseController.position = (x, y)
    mouseController.press(Button.left)
    mouseController.release(Button.left)

def delete_word_and_type_at(delete_word: str, text: str, x: str, y:str):
    it = "\b" * len(delete_word)
    it += text 
    typeAt(it, x, y)

def typeAt(text: str, x: int, y: int):
    keyboard = Controller()
    mouseClick(x, y)
    mouseClick(x, y)
    keyboard.type(text)


def find_template_on_image(image: Mat, template: Mat, shouldClick=False, callback=(), threshold = 0.9):
    found, loc, w, h = match_template(image, template, threshold)
    callback
    if found:
        if shouldClick:
            mouseClick(loc[0] + w / 2, loc[1] + h / 2)
        callback
        return True
    return False


def screenshot():
    with mss.mss() as sct:
        screenshot = np.array(sct.grab(sct.monitors[0]))
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)
        return screenshot


def champion_spell_corection(champion: str):
    champion = champion.lower()
    if not len(champion):
        return ""
    best = champion
    score = 0
    for it in CHAMPIONS:
        if len(it) < len(champion):
            continue
        ratio = fuzz.ratio(it.lower(), champion)
        if ratio > score:
            best = it.lower()
            score = ratio

    return best


def get_local_storage():
    return localStoragePy("xsuto.accept-lol.app", "json")


def accept_game(acceptBtn: Mat, inLobby: Mat, dodge_message: Mat):
    did_accept = False
    print("Waiting for game stage")
    while True:
        lol_only_screenshot = screenshot_of_app_in_background(WINDOW_NAME)
        if find_template_on_image(lol_only_screenshot, inLobby):
            break

        # If we did accept then we shouldn't press button unless we can find dodge message
        did_accept = (
            find_template_on_image(screenshot(), acceptBtn, not did_accept)
            or did_accept
        )

        if find_template_on_image(lol_only_screenshot, dodge_message):
            did_accept = False

        sleep(1)


def select_champion(champion: str,x: int, y: int):
    typeAt(champion, x, y)
    sleep(0.5)


def focus_window(window_name: str):
    try:
        window_handle = FindWindow(None, window_name)
        # SetForegroundWindow weird error sometimes this function crashes program for no reason
        SetForegroundWindow(window_handle)
        sleep(0.4)
    except:
        pass


def look_for_a_game(findMatch: Mat):
    focus_window(WINDOW_NAME)
    sleep(0.5)
    find_template_on_image(screenshot(), findMatch, True)


def float_or_0(str: str):
    try:
        return float(str)
    except:
        return 0


def sleep_with_timer(secs: int):
    i = 0
    while i < secs:
        print("\r" + f"{int(secs - i)} seconds left", end="")
        i += 1
        sleep(1)


def get_args():
    local_storage = get_local_storage()
    autoPickAndBan = bool(local_storage.getItem("PickAndBan") or False)
    dodge_time = 0
    banChamp = str(local_storage.getItem("banChamp") or "")
    pickChamp = str(local_storage.getItem("pickChamp") or "")
    try:
        banChamp = sys.argv[1]
        pickChamp = sys.argv[2]
    except:
        text, did_timeout = timedInput(
            f"Auto pick and ban champion (Y/N) (previously {autoPickAndBan}): "
        )

        if not did_timeout and text:
            autoPickAndBan = text.lower() == "y"

        text, did_timeout = timedInput(
            "Dodge timer in minutes (if 0 then press enter): "
        )
        if not did_timeout and text:
            dodge_time = float_or_0(text) * 60

        if not autoPickAndBan:
            local_storage.setItem("banChamp", "")
            local_storage.setItem("pickChamp", "")
            return ("", "")

        text, did_timeout = timedInput(f"Ban Champion (previously {banChamp}): ")
        if text == "none":
            banChamp = ""
        elif not did_timeout and text:
            banChamp = text

        text, did_timeout = timedInput(f"Pick Champion (previously {pickChamp}): ")
        if text == "none":
            pickChamp = ""
        elif not did_timeout and text:
            pickChamp = text

    sleep_with_timer(dodge_time)
    local_storage.setItem("PickAndBan", autoPickAndBan)
    local_storage.setItem("pickChamp", champion_spell_corection(pickChamp))
    local_storage.setItem("banChamp", champion_spell_corection(banChamp))
    return (champion_spell_corection(banChamp), champion_spell_corection(pickChamp))


def load_img_from_string(str):
    return cv2.imdecode(np.fromstring(str, np.uint8, sep=","), -1)


def main():
    # Make program aware of DPI scaling
    user32 = windll.user32
    user32.SetProcessDPIAware()

    # Get args
    print("Make sure to run client in 1600x900 resolution, you can change that in settings")
    banChamp, pickChamp = get_args()
    print(banChamp, pickChamp)

    # Load templates
    find_match = cv2.imread("./find.png", 0)
    accept_btn = cv2.imread("./accept.png", 0)
    dodge_message = cv2.imread("./dodge.png", 0)
    in_lobby = cv2.imread("./lobby.png", 0)
    ban_champion_stage = cv2.imread("./ban_stage.png", 0)
    ban_btn = cv2.imread("./ban_btn.png", 0)
    search = cv2.imread("./search.png", 0)
    ban_search = cv2.imread("./ban_search.png", 0)
    lock_in = cv2.imread("./lock.png", 0)
    cv2.waitKey(0)

    # Find game
    look_for_a_game(find_match)

    # Accept game
    accept_game(accept_btn, in_lobby, dodge_message)
    x, y, w, h = get_lol_position()

    SELETED_CHAMP_X = 480
    SELETED_CHAMP_Y = 210

    # Selecet champion that you want to play
    if pickChamp:
        print("Select champion stage")
        sleep(5)
        focus_window(WINDOW_NAME)
        while True:
            found, loc, w, h = match_template(screenshot(), search)
            if found:
                print("Ready to select champ")
                select_champion(pickChamp, loc[0] + w / 2, loc[1] + h / 2)
                break
        sleep(0.5)
        x, y, w, h = get_lol_position()
        focus_window(WINDOW_NAME)
        mouseClick(x + SELETED_CHAMP_X, y + SELETED_CHAMP_Y)

    # BAN CHAMP
    if banChamp:
        print("Ban champion stage")
        while not find_template_on_image(
            screenshot_of_app_in_background(WINDOW_NAME), ban_champion_stage, threshold=0.85
        ):
            sleep(1)
        sleep(2)
        focus_window(WINDOW_NAME)
        print("Looking for ban search")
        while True:
            matched, loc, w, h = match_template(screenshot(), ban_search, threshold=0.85)
            if matched:
                print("Ready to ban chemp")
                delete_word_and_type_at(pickChamp, banChamp, loc[0] + w / 2, loc[1] + h / 2)
                break
        sleep(0.5)
        x, y, w, h = get_lol_position()
        focus_window(WINDOW_NAME)
        mouseClick(x + SELETED_CHAMP_X, y + SELETED_CHAMP_Y)
        sleep(0.5)
        find_template_on_image(screenshot(), ban_btn, True) 
        sleep(5)
    
    
    # PICK CHAMP
    if pickChamp:
        print("Pick Champion stage")
        while not find_template_on_image(screenshot(), lock_in, True):
            sleep(1)


main()
