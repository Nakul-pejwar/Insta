import sys
import os


class Color:
    GREEN = "\033[1;92m"
    RED = "\033[1;91m"
    YELLOW = "\033[1;93m"
    GRAY = "\033[1;77m"
    MAGENTA_BG = "\033[1;77m\033[45m"
    RESET = "\033[0m"

    @staticmethod
    def disable():
        for attr in ["GREEN", "RED", "YELLOW", "GRAY", "MAGENTA_BG", "RESET"]:
            setattr(Color, attr, "")


if sys.platform == "win32":
    os.system("")
    try:
        os.system("")
    except Exception:
        Color.disable()


def cprint(color, text):
    print(f"{color}{text}{Color.RESET}", end="")


def banner():
    print(f"{Color.GREEN}     _                                      {Color.RESET}")
    print(f"{Color.GREEN} _  | |                                     {Color.RESET}")
    print(f"{Color.GREEN}( \\ | | ____    ___  _| |_  _____           {Color.RESET}")
    print(f"{Color.GREEN} ) )| ||  _ \\  /___)(_   _)(____ |          {Color.RESET}")
    print(f"{Color.GRAY}(_/ | || | | ||___ |  | |_ / ___ |  _____   {Color.RESET}")
    print(f"{Color.GRAY}    |_||_| |_|(___/    \\__)\\_____| (_____)  {Color.RESET}")
    print()
    print(f"{Color.MAGENTA_BG}   Instagram Brute Forcer v 3.0 Author: Nakul_thakur_42   {Color.RESET}")
    print(f"{Color.MAGENTA_BG}   Python Multi-Threaded | Anti-Detection               {Color.RESET}")
    print()


def save_found(username, password):
    with open("found.passwords", "a") as f:
        f.write(f"Username: {username}, Password: {password}\n")


def save_nottested(password):
    with open("nottested.lst", "a") as f:
        f.write(password + "\n")


def log_debug(msg, debug_on):
    if debug_on:
        with open("debug_login.log", "a") as f:
            f.write(msg + "\n")
