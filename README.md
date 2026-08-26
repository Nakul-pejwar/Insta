# Insta v3.0

Advanced multi-threaded Instagram brute-force tool with Tor-based IP rotation and anti-detection features.

> **Disclaimer:** This tool is for educational and authorized security testing purposes only. Use responsibly and only on accounts you own.

---

## Features

| Feature | Description |
|---------|-------------|
| Multi-Tor Architecture | 5 independent Tor instances (ports 9051-9055) for simultaneous IP rotation |
| Multi-Threaded Engine | Configurable parallel threads with batch processing |
| Session Persistence | Save/resume with line-number precision via `--resume` |
| Rate-Limit Handling | Exponential backoff (5s → 40s) on blocked responses |
| Password Recovery | Untested passwords saved to `nottested.lst` for later re-use |
| CSRF Pre-fetch | Automatically fetches valid token before starting |
| Device Spoofing | Random Android device IDs, phone IDs, GUIDs |
| HMAC Signing | Request signing with Instagram's `ig_sig` key |
| RSA + AES-GCM Encryption | Password encryption matching Instagram's mobile API |
| Cross-Platform | Works on Windows, Linux, and macOS |

---

## Requirements

| Package | Purpose |
|---------|---------|
| Python 3.8+ | Runtime |
| `requests` | HTTP requests to Instagram API |
| `requests[socks]` | SOCKS5 proxy support for Tor |
| `cryptography` | RSA + AES-GCM password encryption |
| `tor` | Anonymous proxy circuits (optional, for `--tor` mode) |

---

## Installation

```bash
git clone https://github.com/Nakul-pejwar/Insta.git
cd Insta
pip install -r requirements.txt
```

For Tor mode (Linux only):
```bash
sudo apt install tor
```

---

## Usage

```bash
# Start new brute-force session (direct mode)
python brute.py

# Multi-Tor brute-force
python brute.py --tor

# Test mode (stops on first match)
python brute.py --test

# Use custom SOCKS5 proxy
python brute.py --proxy socks5://ip:port

# Resume a saved session
python brute.py --resume

# Skip username prompt
python brute.py --username target_user

# Custom wordlist
python brute.py --wordlist passwords.txt

# Debug logging
python brute.py --debug
```

---

## Modes

| Mode | Description |
|------|-------------|
| `--direct` (default) | Single-threaded, uses your real IP |
| `--tor` | Multi-threaded, 5 Tor instances with IP rotation |
| `--proxy` | Single-threaded, routes through your SOCKS5 proxy |
| `--test` | Single-threaded, stops on first password match |

---

## Configuration

Edit variables at the top of `config.py`:

```python
BATCH_SIZE = 20              # Passwords per batch
DELAY_BETWEEN_BATCHES = 0    # Seconds between batch cycles
TOR_START_DELAY = 5          # Seconds to wait for Tor bootstrap
BACKOFF_INITIAL = 5          # Initial backoff delay (seconds)
BACKOFF_MAX = 40             # Maximum backoff delay (seconds)
REQUEST_DELAY = 1            # Seconds between requests
```

---

## How It Works

1. Fetches Instagram's encryption public key from API response headers
2. Encrypts passwords using RSA-PKCS1v15 + AES-GCM (matching Instagram's mobile app)
3. Validates target Instagram username exists
4. Pre-fetches CSRF token from Instagram's API
5. In Tor mode: starts 5 independent Tor instances, each with its own data directory
6. Spawns parallel threads, each routed through its own Tor proxy
7. Each thread encrypts + sends login requests with HMAC-signed payloads
8. Rotates all Tor circuits after each batch cycle
9. Applies exponential backoff when rate-limited
10. Saves credentials to `found.passwords` on success
11. Saves rate-limited passwords to `nottested.lst` for later re-use

---

## Output Files

| File | Description |
|------|-------------|
| `found.passwords` | Successfully cracked credentials |
| `nottested.lst` | Passwords blocked by rate-limiting |
| `sessions/store.session.*` | Saved session state for resume |
| `debug_login.log` | Raw API responses (when `--debug` enabled) |

---

## Project Structure

```
Insta/
├── brute.py           # Main entry point (v3.0)
├── config.py          # Constants and device generation
├── crypto.py          # Password encryption (RSA + AES-GCM)
├── api.py             # Instagram API requests
├── engine.py          # Threading brute-force engine
├── tor.py             # Tor instance management
├── utils.py           # Colors, banner, file I/O
├── requirements.txt   # Python dependencies
├── pass.txt           # Default password wordlist (1,000 entries)
├── Brute.sh           # Legacy Bash version (v2.2)
├── install.sh         # Legacy dependency installer
└── README.md          # This file
```

---

## Changelog

### v3.0
- Rewritten in Python for cross-platform support (Windows + Linux)
- Native RSA + AES-GCM password encryption (no more openssl CLI)
- Proper multi-threading with `concurrent.futures`
- Thread-safe state management
- CLI with `argparse` (all flags available)
- Session save/resume with JSON format

### v2.2
- Updated Instagram API to v428.0.0.47.67
- Added RSA password encryption
- Multi-Tor architecture (5 independent instances)
- Multi-threaded engine
- Exponential backoff on rate limits

### v1.0
- Initial Bash release
- Single-threaded brute-force
- Single Tor proxy

---

## Legacy Bash Version

The original Bash version is preserved as `Brute.sh`. See `install.sh` for dependencies.

```bash
sudo bash Brute.sh --help
```

---

## Author

**Nakul_thakur_42** — Instagram: [@Nakul_thakur_42](https://instagram.com/Nakul_thakur_42)

---

## License

This project is for educational purposes only. Use responsibly and only on accounts you own.
