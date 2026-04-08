import os
import re
import time
import signal
import atexit
import threading
import subprocess

# ─── Wait for Xvfb display before importing anything X-dependent ──────────────
def _wait_for_display(display=None, timeout=120):
    dno       = (display or os.environ.get("DISPLAY", ":1")).lstrip(":")
    sock_path = f"/tmp/.X11-unix/X{dno}"
    deadline  = time.time() + timeout
    print(f"[BOT] Waiting for X display {sock_path} ...", flush=True)
    while time.time() < deadline:
        if os.path.exists(sock_path):
            print(f"[BOT] Display ready.", flush=True)
            return True
        time.sleep(1)
    print(f"[BOT] WARNING: display not found after {timeout}s — continuing anyway.", flush=True)
    return False

_wait_for_display()

import pyautogui
from PIL import Image
from googleapiclient.discovery import build

# ─── Config ───────────────────────────────────────────────────────────────────

YOUTUBE_API_KEY      = os.environ.get("YOUTUBE_API_KEY",  "YOUR_GOOGLE_CLOUD_API_KEY_HERE")
LIVE_STREAM_VIDEO_ID = os.environ.get("YOUTUBE_VIDEO_ID", "YOUR_YOUTUBE_LIVE_VIDEO_ID")
ROBLOX_GAME_ID       = os.environ.get("ROBLOX_GAME_ID",   "YOUR_ROBLOX_GAME_ID")

ROBLOX_USERNAME = "chatusesroblox5"
ROBLOX_PASSWORD = "DenisPro1408"

LOGIN_WAIT_SECONDS  = 300
LOGIN_POLL_INTERVAL = 5

JOINGAME_PREFIX          = "!joingame"
JOINGAME_COLLECT_SECONDS = 120
JOINGAME_SEARCH_WAIT     = 10
JOINGAME_RESULT_WAIT     = 5

LEAVEGAME_PREFIX          = "!leavegame"
LEAVEGAME_INIT_WAIT       = 5
LEAVEGAME_ESC_TO_L_WAIT   = 3
LEAVEGAME_L_TO_ENTER_WAIT = 3

SCREENSHOT_DIR          = "/tmp/roblox_shots"
SCREENSHOT_DELETE_DELAY = 10

STREAM_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stream.sh")

# ─── Roblox app UI coordinates (1920×1080) ───────────────────────────────────

RBX_SEARCH_BAR_X   = 490
RBX_SEARCH_BAR_Y   = 45
RBX_FIRST_RESULT_X = 230
RBX_FIRST_RESULT_Y = 300
RBX_PLAY_BUTTON_X  = 960
RBX_PLAY_BUTTON_Y  = 615
RBX_PLAY_CONFIRM_X = 960
RBX_PLAY_CONFIRM_Y = 500

# ─── Command tables ───────────────────────────────────────────────────────────

KEY_COMMANDS = {
    "w":     "w",
    "a":     "a",
    "s":     "s",
    "d":     "d",
    "space": "space",
    "esc":   "escape",
    "down":  "down",
    "up":    "up",
    "left":  "left",
    "right": "right",
}

CLICK_COMMANDS = {
    "click":        "left",
    "lclick":       "left",
    "click mouse":  "left",
    "left click":   "left",
    "left mouse":   "left",
    "rclick":       "right",
    "right click":  "right",
    "right mouse":  "right",
    "mclick":       "middle",
    "middle click": "middle",
    "middle mouse": "middle",
}

pyautogui.PAUSE    = 0.08
pyautogui.FAILSAFE = False

screen_width, screen_height = pyautogui.size()


# ─── Stream process ───────────────────────────────────────────────────────────

_stream_proc = None


def start_stream():
    global _stream_proc
    if not os.path.isfile(STREAM_SCRIPT):
        print(f"[STREAM] stream.sh not found at {STREAM_SCRIPT} — skipping")
        return
    print(f"[STREAM] Launching stream: {STREAM_SCRIPT}")
    _stream_proc = subprocess.Popen(
        ["bash", STREAM_SCRIPT],
        env={**os.environ, "DISPLAY": ":1"},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    print(f"[STREAM] stream.sh started (PID: {_stream_proc.pid})")

    def _log_output():
        for line in iter(_stream_proc.stdout.readline, b""):
            print(f"[STREAM] {line.decode(errors='replace').rstrip()}")
    threading.Thread(target=_log_output, daemon=True).start()


def stop_stream():
    global _stream_proc
    if _stream_proc and _stream_proc.poll() is None:
        print(f"[STREAM] Stopping stream.sh (PID: {_stream_proc.pid})...")
        _stream_proc.send_signal(signal.SIGTERM)
        try:
            _stream_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _stream_proc.kill()
        print("[STREAM] stream.sh stopped.")


atexit.register(stop_stream)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def find_roblox_exe():
    wine_prefix  = os.environ.get("WINEPREFIX", os.path.expanduser("~/.wine"))
    versions_dir = os.path.join(
        wine_prefix, "drive_c", "users", "user",
        "AppData", "Local", "Roblox", "Versions"
    )
    if os.path.isdir(versions_dir):
        for entry in sorted(os.listdir(versions_dir), reverse=True):
            candidate = os.path.join(versions_dir, entry, "RobloxPlayerBeta.exe")
            if os.path.isfile(candidate):
                print(f"[BOT] Found Roblox at: {candidate}")
                return candidate
    return None


def launch_roblox(game_id):
    exe = find_roblox_exe()
    cmd = (
        ["wine", exe, "--app", "-t", "0", f"roblox://placeId={game_id}"]
        if exe else
        ["wine", "start", f"roblox://placeId={game_id}"]
    )
    print(f"[BOT] Launching Roblox — Game ID: {game_id}")
    subprocess.Popen(cmd, env={**os.environ, "DISPLAY": ":1"})


def focus_window(title="Roblox"):
    r = subprocess.run(
        ["xdotool", "search", "--name", title, "windowactivate", "--sync"],
        capture_output=True
    )
    time.sleep(0.5)
    return r.returncode == 0


def roblox_window_visible():
    r = subprocess.run(["xdotool", "search", "--name", "Roblox"], capture_output=True)
    return r.returncode == 0 and r.stdout.strip() != b""


def take_screenshot():
    subprocess.run(
        ["scrot", "/tmp/roblox_screen.png"],
        env={**os.environ, "DISPLAY": ":1"},
        capture_output=True
    )
    try:
        return Image.open("/tmp/roblox_screen.png")
    except Exception:
        return None


def take_live_screenshot():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    path = os.path.join(SCREENSHOT_DIR, f"live_{timestamp}.png")
    result = subprocess.run(
        ["scrot", path],
        env={**os.environ, "DISPLAY": ":1"},
        capture_output=True
    )
    if result.returncode == 0 and os.path.isfile(path):
        print(f"[SCREENSHOT] Captured → {path}")
        return path
    return None


def schedule_delete(path, delay=SCREENSHOT_DELETE_DELAY):
    def _delete():
        time.sleep(delay)
        try:
            os.remove(path)
            print(f"[SCREENSHOT] Deleted  → {path}")
        except FileNotFoundError:
            pass
    threading.Thread(target=_delete, daemon=True).start()


def click_at(x, y, button="left", double=False):
    pyautogui.moveTo(x, y, duration=0.2)
    time.sleep(0.1)
    if double:
        pyautogui.doubleClick(button=button)
    else:
        pyautogui.click(button=button)
    time.sleep(0.15)


def type_text(text, interval=0.07):
    pyautogui.typewrite(text, interval=interval)


def clear_field():
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.05)
    pyautogui.press("delete")
    time.sleep(0.05)


def find_green_button():
    img = take_screenshot()
    if img is None:
        return None
    w, h   = img.size
    pixels = img.load()
    green_pixels = []
    for y in range(h // 3, h):
        for x in range(w // 4, 3 * w // 4):
            r, g, b = pixels[x, y]
            if g > 120 and g > r * 1.4 and g > b * 1.4:
                green_pixels.append((x, y))
    if len(green_pixels) > 200:
        xs = [p[0] for p in green_pixels]
        ys = [p[1] for p in green_pixels]
        return (sum(xs) // len(xs), sum(ys) // len(ys))
    return None


# ─── Login ────────────────────────────────────────────────────────────────────

def roblox_login():
    cx = screen_width  // 2
    cy = screen_height // 2

    USERNAME_OFFSET = -80
    PASSWORD_OFFSET =   0
    SIGNIN_OFFSET   =  80

    print("[LOGIN] Waiting up to 5 minutes for the Roblox login screen...")

    deadline    = time.time() + LOGIN_WAIT_SECONDS
    login_found = False

    while time.time() < deadline:
        if not roblox_window_visible():
            print("[LOGIN] Window not visible yet...")
            time.sleep(LOGIN_POLL_INTERVAL)
            continue

        focus_window("Roblox")
        img = take_screenshot()
        if img:
            w, h   = img.size
            crop   = img.crop((w // 4, h // 4, 3 * w // 4, 3 * h // 4))
            pixels = list(crop.getdata())
            light  = sum(1 for r, g, b in pixels if r > 200 and g > 200 and b > 200)
            if pixels and light / len(pixels) > 0.3:
                print("[LOGIN] Login screen detected.")
                login_found = True
                break

        remaining = int(deadline - time.time())
        print(f"[LOGIN] Still waiting... {remaining}s remaining")
        time.sleep(LOGIN_POLL_INTERVAL)

    if not login_found:
        print("[LOGIN] Timeout — attempting login anyway.")

    focus_window("Roblox")
    time.sleep(1.0)

    print("[LOGIN] Entering username...")
    click_at(cx, cy + USERNAME_OFFSET)
    time.sleep(0.2)
    clear_field()
    type_text(ROBLOX_USERNAME)
    time.sleep(0.3)

    print("[LOGIN] Entering password...")
    click_at(cx, cy + PASSWORD_OFFSET)
    time.sleep(0.2)
    clear_field()
    type_text(ROBLOX_PASSWORD)
    time.sleep(0.3)

    print("[LOGIN] Clicking Sign In...")
    click_at(cx, cy + SIGNIN_OFFSET)
    time.sleep(0.4)
    pyautogui.press("return")

    print("[LOGIN] Waiting 30 seconds for game to load after sign-in...")
    time.sleep(30)
    focus_window("Roblox")
    print("[LOGIN] Login sequence complete.")


# ─── Leave Game ───────────────────────────────────────────────────────────────

def leave_game():
    print("[LEAVEGAME] Initiating leave sequence...")
    focus_window("Roblox")

    print(f"[LEAVEGAME] Waiting {LEAVEGAME_INIT_WAIT}s before opening menu...")
    time.sleep(LEAVEGAME_INIT_WAIT)

    print("[LEAVEGAME] Pressing ESC...")
    focus_window("Roblox")
    pyautogui.press("escape")

    print(f"[LEAVEGAME] Waiting {LEAVEGAME_ESC_TO_L_WAIT}s for menu to open...")
    time.sleep(LEAVEGAME_ESC_TO_L_WAIT)

    print("[LEAVEGAME] Pressing L (Leave Game)...")
    focus_window("Roblox")
    pyautogui.press("l")

    print(f"[LEAVEGAME] Waiting {LEAVEGAME_L_TO_ENTER_WAIT}s for confirm dialog...")
    time.sleep(LEAVEGAME_L_TO_ENTER_WAIT)

    print("[LEAVEGAME] Pressing ENTER to confirm...")
    focus_window("Roblox")
    pyautogui.press("return")

    print("[LEAVEGAME] Left game. Waiting for home screen...")
    time.sleep(5)


# ─── Join Game ────────────────────────────────────────────────────────────────

def joingame_search(game_name):
    print(f"[JOINGAME] Starting join sequence for: {game_name!r}")

    leave_game()

    print(f"[JOINGAME] Searching for: {game_name!r}")
    focus_window("Roblox")
    time.sleep(0.5)

    click_at(RBX_SEARCH_BAR_X, RBX_SEARCH_BAR_Y)
    time.sleep(0.3)
    clear_field()
    type_text(game_name)
    time.sleep(0.3)
    pyautogui.press("return")

    print(f"[JOINGAME] Waiting {JOINGAME_SEARCH_WAIT}s for search results...")
    time.sleep(JOINGAME_SEARCH_WAIT)

    focus_window("Roblox")
    print("[JOINGAME] Clicking first search result...")
    click_at(RBX_FIRST_RESULT_X, RBX_FIRST_RESULT_Y)

    print(f"[JOINGAME] Waiting {JOINGAME_RESULT_WAIT}s for game page...")
    time.sleep(JOINGAME_RESULT_WAIT)

    focus_window("Roblox")
    green_pos = find_green_button()
    if green_pos:
        print(f"[JOINGAME] Green Play button at {green_pos}, clicking...")
        click_at(*green_pos)
    else:
        print(f"[JOINGAME] Fallback Play position ({RBX_PLAY_BUTTON_X}, {RBX_PLAY_BUTTON_Y})...")
        click_at(RBX_PLAY_BUTTON_X, RBX_PLAY_BUTTON_Y)

    time.sleep(3)
    focus_window("Roblox")
    green_pos2 = find_green_button()
    if green_pos2:
        print(f"[JOINGAME] Confirm Play at {green_pos2}, clicking...")
        click_at(*green_pos2)
    else:
        click_at(RBX_PLAY_CONFIRM_X, RBX_PLAY_CONFIRM_Y)

    print("[JOINGAME] Play clicked — game loading.")


# ─── YouTube chat ─────────────────────────────────────────────────────────────

def get_live_chat_messages(youtube, live_chat_id, page_token=None):
    params = {
        "liveChatId": live_chat_id,
        "part":       "snippet,authorDetails",
        "maxResults": 200,
    }
    if page_token:
        params["pageToken"] = page_token
    return youtube.liveChatMessages().list(**params).execute()


def get_live_chat_id(youtube, video_id):
    response = youtube.videos().list(
        part="liveStreamingDetails",
        id=video_id
    ).execute()
    items = response.get("items", [])
    if not items:
        raise ValueError(f"No video found with ID: {video_id}")
    details = items[0].get("liveStreamingDetails", {})
    chat_id  = details.get("activeLiveChatId")
    if not chat_id:
        raise ValueError("No active live chat found for this video.")
    return chat_id


# ─── Command parsing ──────────────────────────────────────────────────────────

def parse_command(message_text):
    raw  = message_text.strip()
    text = raw.lower()

    if text.startswith(LEAVEGAME_PREFIX):
        return ("leavegame",)

    if text.startswith(JOINGAME_PREFIX):
        rest = raw[len(JOINGAME_PREFIX):].strip()
        if rest:
            return ("joingame", rest)
        return None

    for alias, button in CLICK_COMMANDS.items():
        m = re.match(r"^" + re.escape(alias) + r"\s+(\d+)\s+(\d+)$", text)
        if m:
            try:
                return ("click_pos", button, int(m.group(1)), int(m.group(2)))
            except ValueError:
                pass

    if text in CLICK_COMMANDS:
        return ("click", CLICK_COMMANDS[text])

    if text.startswith("mouse "):
        parts = text.split()
        if len(parts) == 3:
            try:
                return ("mouse", int(parts[1]), int(parts[2]))
            except ValueError:
                pass

    if text in KEY_COMMANDS:
        return ("key", KEY_COMMANDS[text])

    return None


def tally_votes(messages):
    votes = {}
    cmds  = {}
    for msg in messages:
        cmd = parse_command(msg.get("snippet", {}).get("displayMessage", ""))
        if cmd:
            key = str(cmd)
            votes[key] = votes.get(key, 0) + 1
            cmds[key]  = cmd
    if not votes:
        return None
    return cmds[max(votes, key=votes.__getitem__)]


def tally_joingame(messages):
    votes = {}
    for msg in messages:
        cmd = parse_command(msg.get("snippet", {}).get("displayMessage", ""))
        if cmd and cmd[0] == "joingame":
            name = cmd[1].lower()
            votes[name] = votes.get(name, 0) + 1
    return max(votes, key=votes.__getitem__) if votes else None


# ─── Execute ──────────────────────────────────────────────────────────────────

def execute_command(cmd):
    if cmd is None:
        return
    kind = cmd[0]

    if kind == "key":
        print(f"[BOT] Key: {cmd[1]}")
        pyautogui.keyDown(cmd[1])
        time.sleep(0.3)
        pyautogui.keyUp(cmd[1])

    elif kind == "mouse":
        x = max(0, min(cmd[1], screen_width  - 1))
        y = max(0, min(cmd[2], screen_height - 1))
        print(f"[BOT] Mouse move → ({x}, {y})")
        pyautogui.moveTo(x, y, duration=0.2)

    elif kind == "click":
        print(f"[BOT] {cmd[1]} click at current position")
        pyautogui.click(button=cmd[1])

    elif kind == "click_pos":
        x = max(0, min(cmd[2], screen_width  - 1))
        y = max(0, min(cmd[3], screen_height - 1))
        print(f"[BOT] {cmd[1]} click → ({x}, {y})")
        pyautogui.moveTo(x, y, duration=0.2)
        time.sleep(0.1)
        pyautogui.click(button=cmd[1])


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("[BOT] ============================================================")
    print("[BOT]              Chat Plays Roblox — Starting                   ")
    print("[BOT] ============================================================")
    print(f"[BOT] YouTube API Key  : {'SET' if YOUTUBE_API_KEY != 'YOUR_GOOGLE_CLOUD_API_KEY_HERE' else 'NOT SET'}")
    print(f"[BOT] Video ID         : {LIVE_STREAM_VIDEO_ID}")
    print(f"[BOT] Game ID          : {ROBLOX_GAME_ID}")
    print(f"[BOT] Roblox Username  : {ROBLOX_USERNAME}")
    print(f"[BOT] Login Timeout    : {LOGIN_WAIT_SECONDS}s")
    print("[BOT] ============================================================")
    print("[BOT] Chat commands:")
    print("[BOT]   Movement  : W  A  S  D  SPACE  ESC  UP  DOWN  LEFT  RIGHT")
    print("[BOT]   Mouse     : MOUSE X Y  |  CLICK  |  RCLICK  |  MCLICK")
    print("[BOT]   Positioned: CLICK X Y  |  RCLICK X Y")
    print("[BOT]   Join game : !joingame <name>  (2-minute vote window)")
    print("[BOT]   Leave game: !leavegame  → ESC → L → ENTER")
    print("[BOT] ============================================================")

    # ── Launch stream.sh in the background ────────────────────────────────────
    start_stream()

    # ── Launch Roblox and log in ───────────────────────────────────────────────
    launch_roblox(ROBLOX_GAME_ID)
    roblox_login()

    # ── Connect to YouTube Live Chat ───────────────────────────────────────────
    print("[BOT] Connecting to YouTube Live Chat API...")
    youtube      = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    live_chat_id = get_live_chat_id(youtube, LIVE_STREAM_VIDEO_ID)
    print(f"[BOT] Live Chat ID: {live_chat_id}")

    page_token         = None
    collected_messages = []
    joingame_mode      = False
    joingame_deadline  = None

    print("[BOT] Command loop running...")

    def is_special(msg, kind):
        cmd = parse_command(msg.get("snippet", {}).get("displayMessage", ""))
        return cmd is not None and cmd[0] == kind

    while True:
        try:
            # ── Live screenshot: capture DISPLAY:1, auto-delete after 10s ─────
            live_shot = take_live_screenshot()
            if live_shot:
                schedule_delete(live_shot, delay=SCREENSHOT_DELETE_DELAY)

            response   = get_live_chat_messages(youtube, live_chat_id, page_token)
            items      = response.get("items", [])
            collected_messages.extend(items)
            page_token = response.get("nextPageToken")
            poll_ms    = response.get("pollingIntervalMillis", 10000)

            # ── !leavegame — immediate ─────────────────────────────────────────
            if any(is_special(m, "leavegame") for m in items) and not joingame_mode:
                print("[BOT] !leavegame triggered — executing leave sequence...")
                leave_game()
                collected_messages = []
                wait_until = time.time() + (poll_ms / 1000.0)
                while time.time() < wait_until:
                    time.sleep(1)
                continue

            # ── !joingame — open 2-minute voting window ────────────────────────
            if any(is_special(m, "joingame") for m in items) and not joingame_mode:
                joingame_mode     = True
                joingame_deadline = time.time() + JOINGAME_COLLECT_SECONDS
                print("[BOT] !joingame detected — 2-minute voting window open...")

            # ── Wait for next poll ─────────────────────────────────────────────
            wait_until = time.time() + (poll_ms / 1000.0)
            while time.time() < wait_until:
                time.sleep(1)

            # ── !joingame: tally and execute after 2 minutes ───────────────────
            if joingame_mode and time.time() >= joingame_deadline:
                game_name = tally_joingame(collected_messages)
                if game_name:
                    print(f"[BOT] !joingame winner: {game_name!r}")
                    joingame_search(game_name)
                else:
                    print("[BOT] !joingame — no valid game name found")
                joingame_mode      = False
                joingame_deadline  = None
                collected_messages = []
                continue

            # ── Normal command window ──────────────────────────────────────────
            if not joingame_mode and collected_messages:
                regular = [
                    m for m in collected_messages
                    if not is_special(m, "joingame") and not is_special(m, "leavegame")
                ]
                winning_cmd = tally_votes(regular)
                if winning_cmd:
                    focus_window("Roblox")
                    execute_command(winning_cmd)
                collected_messages = []

        except Exception as e:
            print(f"[BOT] Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
