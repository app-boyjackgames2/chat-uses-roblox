import os
import re
import time
import threading
import subprocess
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
JOINGAME_COLLECT_SECONDS = 120   # 2-minute voting window
JOINGAME_SEARCH_WAIT     = 10    # seconds after search before clicking result
JOINGAME_RESULT_WAIT     = 5     # seconds after clicking result before clicking Play

LEAVEGAME_PREFIX          = "!leavegame"
LEAVEGAME_INIT_WAIT       = 5     # seconds before pressing ESC
LEAVEGAME_ESC_TO_L_WAIT   = 3     # seconds between ESC and L
LEAVEGAME_L_TO_ENTER_WAIT = 3     # seconds between L and ENTER

SCREENSHOT_DIR          = "/tmp/roblox_shots"
SCREENSHOT_DELETE_DELAY = 10      # seconds before each loop screenshot is deleted

# ─── Roblox app UI coordinates (1920×1080) ───────────────────────────────────
# Adjust these if your screen resolution or Roblox UI version differs.

RBX_SEARCH_BAR_X     = 490   # Search input field (top nav bar)
RBX_SEARCH_BAR_Y     = 45
RBX_FIRST_RESULT_X   = 230   # First search result card
RBX_FIRST_RESULT_Y   = 300
RBX_PLAY_BUTTON_X    = 960   # "Play" green button on game detail page
RBX_PLAY_BUTTON_Y    = 615
RBX_PLAY_CONFIRM_X   = 960   # "Play" inside the Roblox launcher popup
RBX_PLAY_CONFIRM_Y   = 500

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

# Maps chat text → mouse button
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
    """
    Captures a timestamped PNG of DISPLAY:1 into SCREENSHOT_DIR.
    Returns the path of the saved file, or None on failure.
    """
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
    """
    Deletes `path` after `delay` seconds on a background thread.
    """
    def _delete():
        time.sleep(delay)
        try:
            os.remove(path)
            print(f"[SCREENSHOT] Deleted  → {path}")
        except FileNotFoundError:
            pass
    t = threading.Thread(target=_delete, daemon=True)
    t.start()


def click_at(x, y, button="left", double=False):
    pyautogui.moveTo(x, y, duration=0.2)
    time.sleep(0.1)
    if double:
        pyautogui.doubleClick(button=button)
    else:
        pyautogui.click(button=button)
    time.sleep(0.15)


def right_click_at(x, y):
    click_at(x, y, button="right")


def middle_click_at(x, y):
    click_at(x, y, button="middle")


def type_text(text, interval=0.07):
    pyautogui.typewrite(text, interval=interval)


def clear_field():
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.05)
    pyautogui.press("delete")
    time.sleep(0.05)


def find_green_button():
    """
    Scan the screenshot for a large cluster of Roblox-green pixels
    (the Play button).  Returns (cx, cy) of the green region or None.
    """
    img = take_screenshot()
    if img is None:
        return None
    w, h = img.size
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

    deadline     = time.time() + LOGIN_WAIT_SECONDS
    login_found  = False

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


# ─── Leave Game (chat command !leavegame) ─────────────────────────────────────

def leave_game():
    """
    Leaves the current Roblox game using the in-game menu sequence:
      Wait 5s → ESC → Wait 3s → L (Leave) → Wait 3s → ENTER (Confirm)
    """
    print("[LEAVEGAME] Initiating leave sequence...")
    focus_window("Roblox")

    print(f"[LEAVEGAME] Waiting {LEAVEGAME_INIT_WAIT}s before opening menu...")
    time.sleep(LEAVEGAME_INIT_WAIT)

    print("[LEAVEGAME] Pressing ESC to open menu...")
    focus_window("Roblox")
    pyautogui.press("escape")

    print(f"[LEAVEGAME] Waiting {LEAVEGAME_ESC_TO_L_WAIT}s for menu to open...")
    time.sleep(LEAVEGAME_ESC_TO_L_WAIT)

    print("[LEAVEGAME] Pressing L to select Leave Game...")
    focus_window("Roblox")
    pyautogui.press("l")

    print(f"[LEAVEGAME] Waiting {LEAVEGAME_L_TO_ENTER_WAIT}s for confirm dialog...")
    time.sleep(LEAVEGAME_L_TO_ENTER_WAIT)

    print("[LEAVEGAME] Pressing ENTER to confirm leaving...")
    focus_window("Roblox")
    pyautogui.press("return")

    print("[LEAVEGAME] Leave sequence complete. Waiting for Roblox home screen...")
    time.sleep(5)


# ─── Join Game (chat command !joingame) ───────────────────────────────────────

def joingame_search(game_name):
    """
    Leaves the current game, then searches for `game_name` in the Roblox app,
    clicks the first result after 10 s, then clicks Play after 5 s.
    """
    print(f"[JOINGAME] Starting join sequence for: {game_name!r}")

    leave_game()

    print(f"[JOINGAME] Searching for: {game_name!r}")
    focus_window("Roblox")
    time.sleep(0.5)

    # Click search bar
    click_at(RBX_SEARCH_BAR_X, RBX_SEARCH_BAR_Y)
    time.sleep(0.3)
    clear_field()
    type_text(game_name)
    time.sleep(0.3)
    pyautogui.press("return")

    print(f"[JOINGAME] Waiting {JOINGAME_SEARCH_WAIT}s for search results...")
    time.sleep(JOINGAME_SEARCH_WAIT)

    # Click first search result
    focus_window("Roblox")
    print("[JOINGAME] Clicking first search result...")
    click_at(RBX_FIRST_RESULT_X, RBX_FIRST_RESULT_Y)

    print(f"[JOINGAME] Waiting {JOINGAME_RESULT_WAIT}s for game page to load...")
    time.sleep(JOINGAME_RESULT_WAIT)

    # Find and click Play button (try green-detection first, fall back to fixed pos)
    focus_window("Roblox")
    green_pos = find_green_button()
    if green_pos:
        print(f"[JOINGAME] Green Play button found at {green_pos}, clicking...")
        click_at(*green_pos)
    else:
        print(f"[JOINGAME] Falling back to fixed Play button position ({RBX_PLAY_BUTTON_X}, {RBX_PLAY_BUTTON_Y})...")
        click_at(RBX_PLAY_BUTTON_X, RBX_PLAY_BUTTON_Y)

    # Confirm any "Play" popup/launcher dialog that Roblox may show
    time.sleep(3)
    focus_window("Roblox")
    green_pos2 = find_green_button()
    if green_pos2:
        print(f"[JOINGAME] Second Play/confirm button at {green_pos2}, clicking...")
        click_at(*green_pos2)
    else:
        click_at(RBX_PLAY_CONFIRM_X, RBX_PLAY_CONFIRM_Y)

    print("[JOINGAME] Play clicked — game should be loading.")


# ─── YouTube chat parsing ─────────────────────────────────────────────────────

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


def parse_command(message_text):
    """
    Returns one of:
      ("key",       key_name)
      ("mouse",     x, y)
      ("click",     button)          — click at current mouse position
      ("click_pos", button, x, y)   — move then click
      ("joingame",  game_name)       — !joingame <name>
      ("leavegame",)                 — !leavegame
      None
    """
    raw  = message_text.strip()
    text = raw.lower()

    # ── !leavegame ─────────────────────────────────────────────────────────
    if text.startswith(LEAVEGAME_PREFIX):
        return ("leavegame",)

    # ── !joingame ──────────────────────────────────────────────────────────
    if text.startswith(JOINGAME_PREFIX):
        rest = raw[len(JOINGAME_PREFIX):].strip()
        if rest:
            return ("joingame", rest)
        return None

    # ── click / right-click / middle-click at X Y ─────────────────────────
    # Patterns: "click 960 540", "rclick 100 200", "right click 500 300", etc.
    for alias, button in CLICK_COMMANDS.items():
        pattern = re.compile(
            r"^" + re.escape(alias) + r"\s+(\d+)\s+(\d+)$"
        )
        m = pattern.match(text)
        if m:
            try:
                x, y = int(m.group(1)), int(m.group(2))
                return ("click_pos", button, x, y)
            except ValueError:
                pass

    # ── click / right-click / middle-click at current position ────────────
    if text in CLICK_COMMANDS:
        return ("click", CLICK_COMMANDS[text])

    # ── mouse move: "mouse X Y" ────────────────────────────────────────────
    if text.startswith("mouse "):
        parts = text.split()
        if len(parts) == 3:
            try:
                x, y = int(parts[1]), int(parts[2])
                return ("mouse", x, y)
            except ValueError:
                pass

    # ── keyboard keys ─────────────────────────────────────────────────────
    if text in KEY_COMMANDS:
        return ("key", KEY_COMMANDS[text])

    return None


def tally_votes(messages):
    """Return the most-voted command tuple, or None."""
    votes = {}
    cmds  = {}
    for msg in messages:
        text = msg.get("snippet", {}).get("displayMessage", "")
        cmd  = parse_command(text)
        if cmd:
            key = str(cmd)
            votes[key] = votes.get(key, 0) + 1
            cmds[key]  = cmd
    if not votes:
        return None
    winner = max(votes, key=votes.__getitem__)
    return cmds[winner]


def tally_joingame(messages):
    """
    Among all !joingame messages, return the game name with the most votes.
    """
    votes = {}
    for msg in messages:
        text = msg.get("snippet", {}).get("displayMessage", "")
        cmd  = parse_command(text)
        if cmd and cmd[0] == "joingame":
            name = cmd[1].lower()
            votes[name] = votes.get(name, 0) + 1
    if not votes:
        return None
    return max(votes, key=votes.__getitem__)


# ─── Execute ──────────────────────────────────────────────────────────────────

def execute_command(cmd):
    if cmd is None:
        return

    kind = cmd[0]

    if kind == "key":
        key = cmd[1]
        print(f"[BOT] Key press: {key}")
        pyautogui.keyDown(key)
        time.sleep(0.3)
        pyautogui.keyUp(key)

    elif kind == "mouse":
        _, x, y = cmd
        x = max(0, min(x, screen_width  - 1))
        y = max(0, min(y, screen_height - 1))
        print(f"[BOT] Mouse move → ({x}, {y})")
        pyautogui.moveTo(x, y, duration=0.2)

    elif kind == "click":
        button = cmd[1]
        print(f"[BOT] Mouse {button} click at current position")
        pyautogui.click(button=button)

    elif kind == "click_pos":
        _, button, x, y = cmd
        x = max(0, min(x, screen_width  - 1))
        y = max(0, min(y, screen_height - 1))
        print(f"[BOT] Mouse {button} click → ({x}, {y})")
        pyautogui.moveTo(x, y, duration=0.2)
        time.sleep(0.1)
        pyautogui.click(button=button)


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
    print("[BOT]   Join game : !joingame <game name>  (2-minute vote window)")
    print("[BOT]   Leave game: !leavegame  → ESC (5s) → L (3s) → ENTER")
    print("[BOT] ============================================================")

    launch_roblox(ROBLOX_GAME_ID)
    roblox_login()

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

            # ── Detect !leavegame in this window (immediate, beats joingame) ──
            leavegame_this_window = any(is_special(m, "leavegame") for m in items)
            if leavegame_this_window and not joingame_mode:
                print("[BOT] !leavegame triggered by chat — executing leave sequence...")
                leave_game()
                collected_messages = []
                # skip the rest of this window
                wait_until = time.time() + (poll_ms / 1000.0)
                while time.time() < wait_until:
                    time.sleep(1)
                continue

            # ── Detect !joingame in this window ───────────────────────────────
            joingame_this_window = any(is_special(m, "joingame") for m in items)
            if joingame_this_window and not joingame_mode:
                joingame_mode     = True
                joingame_deadline = time.time() + JOINGAME_COLLECT_SECONDS
                print("[BOT] !joingame detected — 2-minute voting window open...")

            # Wait for next poll
            wait_until = time.time() + (poll_ms / 1000.0)
            while time.time() < wait_until:
                time.sleep(1)

            # ── !joingame mode: accumulate for 2 minutes then act ─────────────
            if joingame_mode and time.time() >= joingame_deadline:
                game_name = tally_joingame(collected_messages)
                if game_name:
                    print(f"[BOT] !joingame winner: {game_name!r} — starting join sequence")
                    joingame_search(game_name)
                else:
                    print("[BOT] !joingame vote window ended — no valid game name found")
                joingame_mode      = False
                joingame_deadline  = None
                collected_messages = []
                continue

            # ── Normal command window ──────────────────────────────────────────
            if not joingame_mode and collected_messages:
                regular = [
                    msg for msg in collected_messages
                    if not is_special(msg, "joingame") and not is_special(msg, "leavegame")
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
