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

WINDOW_NAME = "League of Legends"


SELETED_CHAMP_X = 725
SELETED_CHAMP_Y = 275


SEARCH_CHAMPION_INPUT_X = 1500
SEARCH_CHAMPION_INPUT_Y = 190

CONFIRM_BUTTON_X = 1200
CONFIRM_BUTTON_Y = 1130


def screenshot_of_app_in_background(window_name):
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


def match_template(Image, template, threshold=0.9):
    res = cv2.matchTemplate(Image, template, cv2.TM_CCORR_NORMED)
    h, w = template.shape
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    cv2.waitKey()
    if max_val > threshold:
        return True, max_loc, w, h
    return False, [], 0, 0


def mouseClick(x, y):
    mouseController = mouse.Controller()
    mouseController.position = (x, y)
    mouseController.press(Button.left)
    mouseController.release(Button.left)


def typeAt(text, x, y):
    keyboard = Controller()
    mouseClick(x, y)
    keyboard.type(text)


def find_template_on_image(image, template, shouldClick=False, callback=()):
    found, loc, w, h = match_template(image, template)
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


def champion_spell_corection(champion):
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


def accept_game(acceptBtn, inLobby):
    in_lobby = False
    print("Waiting for game stage")
    while not in_lobby:
        find_template_on_image(screenshot(), acceptBtn, True)
        in_lobby = find_template_on_image(
            screenshot_of_app_in_background(WINDOW_NAME), inLobby
        )
        if in_lobby:
            break
        sleep(1)


def select_champion(champion, x, y):
    typeAt(champion, x + SEARCH_CHAMPION_INPUT_X, y + SEARCH_CHAMPION_INPUT_Y)
    sleep(0.5)
    mouseClick(x + SELETED_CHAMP_X, y + SELETED_CHAMP_Y)
    mouseClick(x + SELETED_CHAMP_X, y + SELETED_CHAMP_Y)


def focus_window(window_name):
    try:
        window_handle = FindWindow(None, window_name)
        # SetForegroundWindow weird error sometimes this function crashes program for no reason
        SetForegroundWindow(window_handle)
        sleep(0.4)
    except:
        pass


def look_for_a_game(findMatch):
    focus_window(WINDOW_NAME)
    find_template_on_image(screenshot(), findMatch, True)


def get_args():
    local_storage = get_local_storage()
    banChamp = str(local_storage.getItem("banChamp") or "")
    pickChamp = str(local_storage.getItem("pickChamp") or "")
    try:
        banChamp = sys.argv[1]
        pickChamp = sys.argv[2]
    except:
        text, did_timeout = timedInput(f"Ban Champion (previously {banChamp}): ")
        if not did_timeout and text:
            banChamp = text
        text, did_timeout = timedInput(f"Pick Champion (previously {pickChamp}): ")
        if not did_timeout and text:
            pickChamp = text
        text, did_timeout = timedInput(
            "Dodge timer in second (if 0 then press enter): "
        )
        if not did_timeout and text:
            sleep(float(text) * 60)
    local_storage.setItem("pickChamp", champion_spell_corection(pickChamp))
    local_storage.setItem("banChamp", champion_spell_corection(banChamp))
    return (champion_spell_corection(banChamp), champion_spell_corection(pickChamp))


def main():

    # Make program aware of DPI scaling
    user32 = windll.user32
    user32.SetProcessDPIAware()

    # Get args
    banChamp, pickChamp = get_args()
    print(banChamp, pickChamp)

    # Load templates
    in_lobby = cv2.imdecode(
        np.fromstring(string_encoded_lobby_template, np.uint8, sep=","), -1
    )
    find_match = cv2.imdecode(
        np.fromstring(string_encoded_find_match_template, np.uint8, sep=","), -1
    )
    accept_btn = cv2.imdecode(
        np.fromstring(string_encoded_accept_btn_template, np.uint8, sep=","), -1
    )
    lock_in = cv2.imdecode(np.fromstring(string_encoded_lock_in, np.uint8, sep=","), -1)

    # Find game
    look_for_a_game(find_match)

    # Accept game
    accept_game(accept_btn, in_lobby)

    # Selecet champion that you want to play
    if not pickChamp or not banChamp:
        return

    print("Select champion stage")
    sleep(5)
    x, y, w, h = get_lol_position()
    focus_window(WINDOW_NAME)
    select_champion(pickChamp, x, y)

    # BAN CHAMP
    print("Ban champion stage")
    sleep(11)
    x, y, w, h = get_lol_position()
    focus_window(WINDOW_NAME)
    select_champion(banChamp, x, y)
    sleep(0.5)
    mouseClick(x + CONFIRM_BUTTON_X, y + CONFIRM_BUTTON_Y)

    # PICK CHAMP
    print("Pick Champion stage")
    while not find_template_on_image(screenshot(), lock_in, True):
        sleep(3)


main()