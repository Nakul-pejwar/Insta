import json
import time
import uuid as _uuid
import requests
from urllib.parse import quote_plus

from config import (
    APP_ID, USER_AGENT, BLOKS_VERSIONING_ID,
    LOGIN_URL, FETCH_HEADERS_URL, generate_phone_id, generate_guid,
)
from crypto import generate_jazoest


def _make_session(proxy=None, phone_id=None, device_id=None):
    s = requests.Session()

    pid = phone_id or generate_phone_id()
    did = device_id or f"android-{_uuid.uuid4().hex[:16]}"
    guid = generate_guid()

    s.headers.update({
        "User-Agent": USER_AGENT,
        "X-IG-App-ID": APP_ID,
        "X-IG-Capabilities": "3brTv10=",
        "X-IG-Connection-Type": "WIFI",
        "X-Bloks-Version-Id": BLOKS_VERSIONING_ID,
        "X-IG-App-Locale": "en_US",
        "X-IG-Device-Locale": "en_US",
        "X-IG-Mapped-Locale": "en_US",
        "X-Pigeon-Session-Id": f"UFS-{_uuid.uuid4()}-1",
        "X-Pigeon-Rawclienttime": str(round(time.time(), 3)),
        "X-IG-Bandwidth-Speed-KBPS": "4448",
        "X-IG-Bandwidth-TotalBytes-B": "1593322",
        "X-IG-Bandwidth-TotalTime-MS": "358",
        "X-IG-App-Startup-Country": "US",
        "X-IG-WWW-Claim": "0",
        "X-Bloks-Is-Layout-RTL": "false",
        "X-Bloks-Is-Panorama-Enabled": "true",
        "X-IG-Device-ID": did,
        "X-IG-Family-Device-ID": pid,
        "X-IG-Android-ID": did,
        "X-IG-Timezone-Offset": "0",
        "X-IG-Nav-Chain": "9MV:self_profile:2,1BJ:self_profile:6",
        "IG-INTENDED-USER-ID": "0",
        "Accept-Language": "en-US",
        "Accept-Encoding": "gzip, deflate",
        "X-FB-HTTP-Engine": "Tigon/MNS/TCP",
        "X-Tigon-Is-Retry": "False",
        "X-FB-Client-IP": "True",
        "X-FB-Server-Cluster": "True",
        "Connection": "keep-alive",
        "Host": "i.instagram.com",
    })
    if proxy:
        s.proxies = {"http": proxy, "https": proxy}
    return s


def _build_body(data_dict):
    json_str = json.dumps(data_dict, separators=(",", ":"))
    return f"signed_body=SIGNATURE.{quote_plus(json_str)}"


def fetch_csrf_token(proxy=None):
    s = _make_session(proxy)
    try:
        r = s.get(FETCH_HEADERS_URL, params={
            "challenge_type": "signup",
            "guid": str(_uuid.uuid4()),
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
        r = s.get("https://i.instagram.com/api/v1/qe/sync/", timeout=15)
        key_id = r.headers.get("ig-set-password-encryption-key-id", "")
        pubkey = r.headers.get("ig-set-password-encryption-pub-key", "")
        if key_id and pubkey:
            if debug:
                print(f"\033[1;93m[DEBUG] Got key_id={key_id} from qe/sync (len={len(pubkey)})\033[0m")
            return int(key_id), pubkey
    except Exception as e:
        if debug:
            print(f"\033[1;93m[DEBUG] qe/sync failed: {e}\033[0m")

    try:
        r = s.get(FETCH_HEADERS_URL, params={
            "challenge_type": "signup",
            "guid": str(_uuid.uuid4()),
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

    if debug:
        print("\033[1;93m[DEBUG] Could not fetch encryption keys from API\033[0m")
    return None, None


def _login_post(data_dict, proxy=None, phone_id=None, device_id=None):
    s = _make_session(proxy, phone_id, device_id)
    body = _build_body(data_dict)
    r = s.post(LOGIN_URL, data=body, timeout=15,
               headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})
    return r.status_code, r.text


def login_request(username, enc_password, phone_id, adid, guid, device_id, proxy=None):
    data = {
        "jazoest": generate_jazoest(phone_id),
        "country_codes": '[{"country_code":"1","source":["default"]}]',
        "phone_id": phone_id,
        "enc_password": enc_password,
        "username": username,
        "adid": adid,
        "guid": guid,
        "device_id": device_id,
        "google_tokens": "[]",
        "login_attempt_count": "0",
    }
    try:
        return _login_post(data, proxy, phone_id, device_id)
    except requests.exceptions.Timeout:
        return 0, "timeout"
    except requests.exceptions.ConnectionError:
        return 0, "connection_error"
    except Exception as e:
        return 0, str(e)


def healthcheck(username, phone_id, adid, guid, device_id, proxy=None):
    data = {
        "jazoest": generate_jazoest(phone_id),
        "country_codes": '[{"country_code":"1","source":["default"]}]',
        "phone_id": phone_id,
        "enc_password": "#PWD_INSTAGRAM:4:0:__HEALTHCHECK__",
        "username": username,
        "adid": adid,
        "guid": guid,
        "device_id": device_id,
        "google_tokens": "[]",
        "login_attempt_count": "0",
    }
    try:
        code, body = _login_post(data, proxy, phone_id, device_id)
        return code, body[:80]
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
