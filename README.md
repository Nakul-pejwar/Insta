# Insta v2.0

Advanced multi-threaded Instagram brute-force tool with Tor-based IP rotation and anti-detection features.

> **Disclaimer:** This tool is for educational and authorized security testing purposes only. Use responsibly and only on accounts you own.

---

## Features

| Feature | Description |
|---------|-------------|
| Multi-Tor Architecture | 5 independent Tor instances (ports 9051-9055) for simultaneous IP rotation |
| Multi-Threaded Engine | 5 parallel threads, 20 passwords each (100 passwords per cycle) |
| Session Persistence | Save/resume with line-number precision via `--resume` |
| Rate-Limit Handling | Exponential backoff (5s → 40s) on blocked responses |
| Password Recovery | Untested passwords saved to `nottested.lst` for later re-use |
| CSRF Pre-fetch | Automatically fetches valid token before starting |
| Device Spoofing | Random Android device IDs, phone IDs, GUIDs |
| HMAC Signing | Request signing with Instagram's `ig_sig` key |

---

## Requirements

See [`install.sh`](install.sh) for dependency installation.

| Package | Purpose |
|---------|---------|
| `tor` | Anonymous proxy circuits |
| `curl` | HTTP requests to Instagram API |
| `openssl` | HMAC-SHA256 signing + random ID generation |
| `awk`, `sed`, `cat`, `tr`, `wc`, `cut`, `uniq` | Standard POSIX utilities |

### Quick Install

```bash
sudo ./install.sh
```

---

## Installation

```bash
git clone https://github.com/Nakul-pejwar/Insta.git
cd Insta
chmod +x install.sh Brute.sh
sudo ./install.sh
```

---

## Usage

```bash
# Start new brute-force session
./Brute.sh

# Resume a saved session
./Brute.sh --resume

# Show help
./Brute.sh --help
```

---

## Configuration

Edit variables at the top of `Brute.sh`:

```bash
BATCH_SIZE=20              # Passwords per thread per batch
DELAY_BETWEEN_BATCHES=0    # Seconds between batch cycles
TOR_START_DELAY=5          # Seconds to wait for Tor bootstrap
BACKOFF_INITIAL=5          # Initial backoff delay (seconds)
BACKOFF_MAX=40             # Maximum backoff delay (seconds)
```

---

## How It Works

1. Starts 5 independent Tor instances with separate data directories
2. Validates target Instagram username exists
3. Pre-fetches CSRF token from Instagram's API
4. Spawns 5 parallel threads, each routed through its own Tor proxy
5. Each thread processes 20 passwords per batch via background subshells
6. Rotates all Tor circuits after each batch cycle
7. Applies exponential backoff when rate-limited
8. Saves credentials to `found.passwords` on success
9. Saves rate-limited passwords to `nottested.lst` for later re-use

---

## Output Files

| File | Description |
|------|-------------|
| `found.passwords` | Successfully cracked credentials |
| `nottested.lst` | Passwords blocked by rate-limiting |
| `sessions/store.session.*` | Saved session state for resume |

---

## Project Structure

```
Insta/
├── Brute.sh          # Main brute-force script (v2.0)
├── install.sh        # Dependency installer
├── pass.txt          # Default password wordlist (1,000 entries)
└── README.md         # This file
```

---

## Changelog

### v2.0
- Multi-Tor architecture (5 independent instances)
- Multi-threaded engine (5 parallel threads)
- Session save/resume with line-number precision
- Exponential backoff on rate limits
- Untested password recovery (`nottested.lst`)
- CSRF token pre-fetch
- Configurable parameters
- `--help` flag

### v1.0
- Initial release
- Single-threaded brute-force
- Single Tor proxy
- Basic session save/resume

---

## Author

**Nakul_thakur_42** — Instagram: [@Nakul_thakur_42](https://instagram.com/Nakul_thakur_42)

---

## License

This project is for educational purposes only. Use responsibly and only on accounts you own.
