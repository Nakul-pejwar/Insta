import hmac as hmac_mod
import hashlib
import json
import requests

from config import (
    IG_SIG, APP_ID, USER_AGENT, BLOKS_VERSIONING_ID,
    LOGIN_URL, FETCH_HEADERS_URL,
)
from crypto import generate_jazoest


def _make_session(proxy=None):
    s = requests.Session()
    s.headers.update({
        "User-Agent": USER_AGENT,
        "X-IG-App-ID": APP_ID,
        "X-IG-Capabilities": "3brTv10=",
        "X-IG-Connection-Type": "WIFI",
        "X-Bloks-Version-Id": BLOKS_VERSIONING_ID,
        "Accept": "*/*",
    })
    if proxy:
        s.proxies = {"http": proxy, "https": proxy}
    return s


def _sign(data: str) -> str:
    return hmac_mod.new(IG_SIG.encode(), data.encode(), hashlib.sha256).hexdigest()


def fetch_csrf_token(proxy=None):
    s = _make_session(proxy)
    try:
        r = s.get(FETCH_HEADERS_URL, params={
            "challenge_type": "signup",
            "guid": "00000000-0000-0000-0000-000000000000",
        }, timeout=15)
        token = r.cookies.get("csrftoken", "")
        if not token:
            for line in r.headers.get("Set-Cookie", "").split(","):
                if "csrftoken=" in line:
                    token = line.split("csrftoken=")[1].split(";")[0].strip()
                    break
        return token
    except Exception:
        return ""


def fetch_public_key(proxy=None, debug=False):
    s = _make_session(proxy)

    try:
        r = s.get(FETCH_HEADERS_URL, params={
            "challenge_type": "signup",
            "guid": "00000000-0000-0000-0000-000000000000",
        }, timeout=15)

        key_id = r.headers.get("ig-set-password-encryption-key-id", "")
        pubkey = r.headers.get("ig-set-password-encryption-pub-key", "")

        if key_id and pubkey:
            if debug:
                print(f"\033[1;93m[DEBUG] Got key_id={key_id} from fetch_headers (len={len(pubkey)})\033[0m")
            return int(key_id), pubkey
    except Exception as e:
        if debug:
            print(f"\033[1;93m[DEBUG] fetch_headers failed: {e}\033[0m")

    try:
        jazoest = generate_jazoest("00000000-0000-0000-0000-000000000000")
        login_data = json.dumps({
            "jazoest": jazoest,
            "country_codes": '[{"country_code":"1","source":["default"]}]',
            "phone_id": "00000000-0000-0000-0000-000000000000",
            "enc_password": "#PWD_INSTAGRAM:4:0:test",
            "username": "__test__",
            "adid": "00000000-0000-0000-0000-000000000000",
            "guid": "00000000-0000-0000-0000-000000000000",
            "device_id": "android-0000000000000000",
            "google_tokens": "[]",
            "login_attempt_count": "0",
        })
        h = _sign(login_data)
        body = f"ig_sig_key_version=4&signed_body={h}.{login_data}"

        r = s.post(LOGIN_URL, data=body, timeout=15,
                   headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})

        key_id = r.headers.get("ig-set-password-encryption-key-id", "")
        pubkey = r.headers.get("ig-set-password-encryption-pub-key", "")

        if key_id and pubkey:
            if debug:
                print(f"\033[1;93m[DEBUG] Got key_id={key_id} from login endpoint (len={len(pubkey)})\033[0m")
            return int(key_id), pubkey
    except Exception as e:
        if debug:
            print(f"\033[1;93m[DEBUG] login endpoint failed: {e}\033[0m")

    if debug:
        print("\033[1;93m[DEBUG] Could not fetch encryption keys from API\033[0m")
    return None, None


def login_request(username, enc_password, phone_id, adid, guid, device_id, proxy=None):
    s = _make_session(proxy)

    jazoest = generate_jazoest(phone_id)
    login_data = json.dumps({
        "jazoest": jazoest,
        "country_codes": '[{"country_code":"1","source":["default"]}]',
        "phone_id": phone_id,
        "enc_password": enc_password,
        "username": username,
        "adid": adid,
        "guid": guid,
        "device_id": device_id,
        "google_tokens": "[]",
        "login_attempt_count": "0",
    })
    h = _sign(login_data)
    body = f"ig_sig_key_version=4&signed_body={h}.{login_data}"

    try:
        r = s.post(LOGIN_URL, data=body, timeout=15,
                   headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})
        return r.status_code, r.text
    except requests.exceptions.Timeout:
        return 0, "timeout"
    except requests.exceptions.ConnectionError:
        return 0, "connection_error"
    except Exception as e:
        return 0, str(e)


def healthcheck(username, phone_id, adid, guid, device_id, proxy=None):
    s = _make_session(proxy)

    jazoest = generate_jazoest(phone_id)
    test_data = json.dumps({
        "jazoest": jazoest,
        "country_codes": '[{"country_code":"1","source":["default"]}]',
        "phone_id": phone_id,
        "enc_password": "#PWD_INSTAGRAM:4:0:__HEALTHCHECK__",
        "username": username,
        "adid": adid,
        "guid": guid,
        "device_id": device_id,
        "google_tokens": "[]",
        "login_attempt_count": "0",
    })
    h = _sign(test_data)
    body = f"ig_sig_key_version=4&signed_body={h}.{test_data}"

    try:
        r = s.post(LOGIN_URL, data=body, timeout=15,
                   headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})
        return r.status_code, r.text[:80]
    except Exception as e:
        return 0, str(e)


def check_username(username):
    try:
        r = requests.get(
            f"https://www.instagram.com/{username}/",
            headers={"User-Agent": USER_AGENT},
            timeout=10
        )
        if "page may have been removed" in r.text.lower() or "sorry, this page" in r.text.lower():
            return False
        return True
    except Exception:
        return True
