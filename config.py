import os
import uuid as _uuid
import random
import string

VERSION = "3.0"
AUTHOR = "Nakul_thakur_42"

IG_SIG = "46024e8f31e295869a0e861eaed42cb1dd8454b55232d85f6c6764365079374b"
APP_ID = "567067343352427"
USER_AGENT = "Instagram 428.0.0.47.67 Android (34/14; 480dpi; 1344x2992; Google/google; Pixel 8 Pro; husky; husky; en_US; 961145276)"
BLOKS_VERSIONING_ID = "7189b949425f9bf80ea8bd880cf5a3080b292d9b1c4b38a18d112f7c4b71e7a8"

BASE_URL = "https://i.instagram.com/api/v1"
LOGIN_URL = f"{BASE_URL}/accounts/login/"
FETCH_HEADERS_URL = f"{BASE_URL}/si/fetch_headers/"

TOR_PORTS = [9051, 9052, 9053, 9054, 9055]
TOR_DIRS = [f"/var/lib/tor{i+1}" for i in range(5)]

BATCH_SIZE = 20
DELAY_BETWEEN_BATCHES = 0
TOR_START_DELAY = 5
BACKOFF_INITIAL = 5
BACKOFF_MAX = 40
REQUEST_DELAY = 1


def generate_device_id():
    return "android-" + os.urandom(16).hex()


def generate_uuid():
    return _uuid.uuid4().hex


def generate_phone_id():
    a = _uuid.uuid4().hex[:8]
    b = _uuid.uuid4().hex[:4]
    return f"{a}-{b}-{b}-{b}-{_uuid.uuid4().hex[:12]}"


def generate_guid():
    a = _uuid.uuid4().hex[:8]
    b = _uuid.uuid4().hex[:4]
    return f"{a}-{b}-{b}-{b}-{_uuid.uuid4().hex[:12]}"


def generate_adid():
    return str(_uuid.uuid4())
