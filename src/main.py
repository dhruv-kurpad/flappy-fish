import os
import sys
import time
import random
import subprocess
import threading
from pathlib import Path
from auth import login_user, register_user, remove_user, get_leaderboard
from game_logic import start_game_logic
from colorama import init, Fore, Style

init(autoreset=False)

# ── BGM player ────────────────────────────────────────────────────────────────
class _BGMPlayer:
    """Loops a WAV file in a background thread. Call switch() to cross-fade tracks."""

    def __init__(self):
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._current: str | None = None

    def _loop(self, path: str, stop: threading.Event):
        while not stop.is_set():
            if sys.platform == "darwin":
                proc = subprocess.Popen(["afplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif sys.platform == "win32":
                # winsound.PlaySound blocks; use a subprocess for looping on Windows
                proc = subprocess.Popen(
                    ["powershell", "-c", f"(New-Object Media.SoundPlayer '{path}').PlayLooping(); Start-Sleep 9999"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                stop.wait()
                proc.terminate()
                return
            else:
                proc = subprocess.Popen(["aplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Wait for afplay/aplay to finish OR for stop signal
            while proc.poll() is None:
                if stop.is_set():
                    proc.terminate()
                    return
                time.sleep(0.05)

    def play(self, name: str):
        """Start playing a BGM track by name (no extension). No-op if already playing."""
        path = str(_SOUNDS / f"{name}.wav")
        if not Path(path).exists():
            return
        if self._current == name and self._thread and self._thread.is_alive():
            return
        self.stop()
        self._current = name
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._loop, args=(path, self._stop_event), daemon=True
        )
        self._thread.start()

    def stop(self):
        if self._thread and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join(timeout=1.0)
        self._current = None

    def switch(self, name: str):
        """Stop current BGM and start a new one."""
        if self._current != name:
            self.stop()
            self.play(name)


_bgm = _BGMPlayer()

# ── Color shortcuts ──────────────────────────────────────────────────────────
Y   = Fore.YELLOW
C   = Fore.CYAN
G   = Fore.GREEN
R   = Fore.RED
W   = Fore.WHITE
DIM = Style.DIM
BRT = Style.BRIGHT
RST = Style.RESET_ALL

# ── ASCII Banner ─────────────────────────────────────────────────────────────
BANNER = (
    f"\n{Y}"
    "   ███████╗██╗      █████╗ ██████╗ ██████╗ ██╗   ██╗\n"
    "   ██╔════╝██║     ██╔══██╗██╔══██╗██╔══██╗╚██╗ ██╔╝\n"
    "   █████╗  ██║     ███████║██████╔╝██████╔╝ ╚████╔╝ \n"
    "   ██╔══╝  ██║     ██╔══██║██╔═══╝ ██╔═══╝   ╚██╔╝  \n"
    "   ██║     ███████╗██║  ██║██║     ██║        ██║    \n"
    "   ╚═╝     ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝        ╚═╝   \n"
    f"{C}"
    "           ███████╗██╗███████╗██╗  ██╗\n"
    "           ██╔════╝██║██╔════╝██║  ██║\n"
    "           █████╗  ██║███████╗███████║\n"
    "           ██╔══╝  ██║╚════██║██╔══██║\n"
    "           ██║     ██║███████║██║  ██║\n"
    f"           ╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝ {RST}\n"
)

current_user = None

_ASSETS = Path(__file__).resolve().parent / "assets"
_SOUNDS = _ASSETS / "sounds"


def _play_sfx(name: str):
    """Play a WAV sound file asynchronously. Works on macOS, Windows, and Linux."""
    path = _SOUNDS / f"{name}.wav"
    if not path.exists():
        return

    if sys.platform == "darwin":
        cmd = ["afplay", str(path)]
        threading.Thread(
            target=lambda: subprocess.run(cmd, capture_output=True),
            daemon=True,
        ).start()
    elif sys.platform == "win32":
        import winsound
        threading.Thread(
            target=lambda: winsound.PlaySound(str(path), winsound.SND_FILENAME),
            daemon=True,
        ).start()
    else:  # Linux
        cmd = ["aplay", str(path)]
        threading.Thread(
            target=lambda: subprocess.run(cmd, capture_output=True),
            daemon=True,
        ).start()


def _flush_stdin():
    """Discard any keystrokes buffered during animations so they don't skip the next prompt."""
    try:
        import termios
        termios.tcflush(sys.stdin, termios.TCIFLUSH)
    except Exception:
        # Windows fallback
        try:
            import msvcrt
            while msvcrt.kbhit():
                msvcrt.getwch()
        except Exception:
            pass


def _animated_input() -> str:
    """Blinking ><> fish as the prompt cursor: yellow → blank → cyan → blank → …"""
    stop = threading.Event()

    # Four states, 0.25 s each: yellow fish, blank, cyan fish, blank
    states = [
        f"{Y}{BRT}><>{RST}",
        "   ",
        f"{C}{BRT}><>{RST}",
        "   ",
    ]

    # Print initial prompt: 2-space indent + yellow fish + 1 space
    sys.stdout.write(f"  {states[0]} ")
    sys.stdout.flush()

    def _animate():
        tick = 0
        while not stop.is_set():
            time.sleep(0.25)
            tick += 1
            fish = states[tick % len(states)]
            # Save cursor → jump to fish position (col 3) → rewrite → restore
            sys.stdout.write(f"\033[s\r\033[2C{fish}\033[u")
            sys.stdout.flush()

    t = threading.Thread(target=_animate, daemon=True)
    t.start()

    # Flush any keystrokes typed during the preceding animation so they
    # don't immediately skip this prompt before the user sees the screen.
    _flush_stdin()
    val = input("").strip()

    stop.set()
    t.join(timeout=0.4)

    return val


def _menu_input() -> str:
    """Animated-input wrapper that plays a button click sound on Enter."""
    val = _animated_input()
    _play_sfx("button_click")
    return val


# ── Intro Animation ───────────────────────────────────────────────────────────
def show_intro():
    from blessed import Terminal

    with open(_ASSETS / "fish.txt") as f:
        fish_lines = [line.rstrip('\n') for line in f]

    fish_width = max(len(line) for line in fish_lines)
    fish_height = len(fish_lines)

    term = Terminal()

    # Physics state
    fish_x    = float(-fish_width)
    fish_y    = float(term.height // 2 - fish_height // 2)
    velocity  = -2.0
    gravity   = 0.20
    speed     = 1.5
    flap_every = 12   # auto-flap every N frames

    bubbles = []      # each entry: [x, y, lifetime]
    frame   = 0

    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        while int(fish_x) < term.width:
            # ── Physics ──────────────────────────────────────────────────────
            velocity += gravity
            fish_y   += velocity
            fish_x   += speed

            if frame % flap_every == 0:
                velocity = -2.0

            # vertical clamp
            if fish_y < 0:
                fish_y   = 0.0
                velocity = 0.5
            if fish_y > term.height - fish_height - 1:
                fish_y   = float(term.height - fish_height - 1)
                velocity = -2.0

            # ── Emit bubble behind the fish ───────────────────────────────────
            if frame % 3 == 0 and int(fish_x) > 0:
                bubbles.append([
                    int(fish_x) - 2,
                    int(fish_y) + fish_height // 2 + random.randint(-1, 1),
                    15,
                ])

            bubbles = [[x, y, lt - 1] for x, y, lt in bubbles if lt > 0]

            # ── Render ────────────────────────────────────────────────────────
            W = term.width
            H = term.height - 1
            out = [term.clear]

            # skip hint at bottom
            hint = f"{DIM}Press any key to skip{RST}"
            out.append(term.move_xy(0, H) + hint)

            # bubbles — cyan, matching the "FISH" half of the banner
            for bx, by, _ in bubbles:
                if 0 <= bx < W and 0 <= by < H:
                    out.append(term.move_xy(bx, by) + term.cyan + "o" + term.normal)

            # fish — yellow bold, matching the "FLAPPY" half of the banner
            fy, fx = int(fish_y), int(fish_x)
            for i, line in enumerate(fish_lines):
                y = fy + i
                if 0 <= y < H:
                    x_start = max(0, fx)
                    offset  = max(0, -fx)
                    visible = line[offset: offset + max(0, W - x_start)]
                    if visible and x_start < W:
                        out.append(
                            term.move_xy(x_start, y) +
                            term.yellow + term.bold + visible + term.normal
                        )

            print("".join(out), end="", flush=True)

            frame += 1

            if term.inkey(timeout=0.04):
                break


PAGE_SIZE = 10

MEDALS = {
    1: f"{Y}{BRT}[1ST]{RST}",
    2: f"{W}{BRT}[2ND]{RST}",
    3: f"{Fore.RED}{BRT}[3RD]{RST}",
}

CLEAR_SCREEN = "\033[2J\033[H"


def clear_screen(show_banner=False):
    # Use ANSI clear+home so each screen render starts from a clean frame.
    print(CLEAR_SCREEN, end="", flush=True)
    if show_banner:
        print(BANNER)


def _vcenter_pad(content_lines: int = 1):
    """Print blank lines so that `content_lines` rows appear vertically centered."""
    try:
        term_h = os.get_terminal_size().lines
    except OSError:
        term_h = 24
    pad = max(0, (term_h - content_lines) // 2)
    print("\n" * pad, end="")


def _typewriter(text, delay=0.03, color=""):
    """Print text character by character. Pass a full ANSI color code via color=;
    it is written atomically before the loop so the terminal never sees a partial escape sequence."""
    if color:
        sys.stdout.write(color)
        sys.stdout.flush()
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    if color:
        sys.stdout.write(RST)
    sys.stdout.write("\n")
    sys.stdout.flush()


def _typewrite_option(prefix: str, label: str, delay: float = 0.018):
    """Print one menu option: prefix (with colour codes) instantly, label char-by-char."""
    sys.stdout.write(prefix)
    sys.stdout.flush()
    for ch in label:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")
    sys.stdout.flush()

def _input_with_sfx(prompt: str = "") -> str:
    """Plain input() that plays a button click sound when Enter is pressed."""
    val = input(prompt)
    _play_sfx("button_click")
    return val


def pause_after_message():
    _input_with_sfx(f"\n{DIM}Press Enter to continue...{RST}")



# ── Display Menu ─────────────────────────────────────────────────────────────
def _draw_menu(options, selected_idx=None, animate=False):
    """Render the full menu. When selected_idx is set, box that option."""
    clear_screen(show_banner=True)
    print(f"\n{Y}{'═' * 32}{RST}")
    print(f"  {Y}{BRT}        FLAPPY  FISH{RST}")
    print(f"{Y}{'═' * 32}{RST}")

    if current_user:
        print(f"  {G}● Logged in as: {BRT}{current_user}{RST}")
        print(f"{Y}{'─' * 32}{RST}")

    for i, (_, label) in enumerate(options):
        if i == selected_idx:
            inner  = f"  {i + 1}. {label}  "
            border = "─" * len(inner)
            print(f"  {Y}{BRT}┌{border}┐{RST}")
            print(f"  {Y}{BRT}│{inner}│{RST}")
            print(f"  {Y}{BRT}└{border}┘{RST}")
        elif animate:
            _typewrite_option(f"  {C}{i + 1}.{RST} ", label)
        else:
            print(f"  {C}{i + 1}.{RST} {label}")

    print(f"  {DIM}{len(options) + 1}. Remove User (DEBUG){RST}")
    print(f"{Y}{'═' * 32}{RST}")


def show_menu():
    if current_user:
        options = [
            ("start",       "Start Game"),
            ("leaderboard", "Leaderboard"),
            ("logout",      "Logout"),
            ("exit",        "Exit"),
        ]
    else:
        options = [
            ("login",       "Login"),
            ("register",    "Register"),
            ("leaderboard", "Leaderboard"),
            ("exit",        "Exit"),
        ]

    _draw_menu(options, animate=True)
    choice = _animated_input()

    # TESTING CODE
    if choice == str(len(options) + 2):
        return "test"
    # TESTING CODE
    if choice == str(len(options) + 1):
        return "remove"

    if choice.isdigit() and 1 <= int(choice) <= len(options):
        selected_idx = int(choice) - 1
        action = options[selected_idx][0]

        _play_sfx("button_click")
        _draw_menu(options, selected_idx=selected_idx)
        time.sleep(0.25)
        return action

    return "invalid"


# ── Game rules screen ────────────────────────────────────────────────────────
def show_rules():
    clear_screen()
    print(f"\n{C}{'═' * 42}{RST}")
    print(f"  {Y}{BRT}HOW TO PLAY{RST}")
    print(f"{C}{'═' * 42}{RST}")
    print(f"""
  {W}Objective:{RST}
    Guide your fish through the gaps between
    pipes and survive as long as possible.

  {W}Controls:{RST}
    {C}SPACE{RST}  — Flap wings (jump up)
    {C}Q{RST}      — Quit to menu

  {W}Scoring:{RST}
    +1 point for every pipe you pass through.
    Your {Y}high score{RST} is saved automatically.

  {W}Tips:{RST}
    • Tap quickly for small hops.
    • Gravity pulls you down constantly.
    • The pipes move faster over time.
""")
    print(f"{C}{'═' * 42}{RST}")
    _typewrite_option(f"  {C}1.{RST} ", "Start game")
    _typewrite_option(f"  {C}2.{RST} ", "Back to main menu")
    print(f"{C}{'═' * 42}{RST}")
    choice = _menu_input()
    if choice != "1":
        return False
    
    # Removed old countdown and replaced with screen - Brock
    
    return True


# ── Core game logic function ─────────────────────────────────────────────────
def start_game(username):
    _typewriter(f"Welcome, {username}! Get ready...", delay=0.04, color=G)
    pause_after_message()
    while True:
        if not show_rules():
            _bgm.switch("menu_bgm")
            return
        clear_screen()
        print(f"{Y}--- GAME STARTING ---{RST}")
        print(" (control options) ")
        _bgm.switch("game_bgm")
        start_game_logic(username)
        _bgm.switch("menu_bgm")

        clear_screen()
        print(f"\n{R}{'═' * 32}{RST}")
        print(f"  {R}{BRT}    GAME  OVER{RST}")
        print(f"{R}{'═' * 32}{RST}")
        _typewrite_option(f"  {C}1.{RST} ", "Play again")
        _typewrite_option(f"  {C}2.{RST} ", "Back to main menu")
        print(f"{R}{'═' * 32}{RST}")
        choice = _menu_input()
        if choice != "1":
            return False

        return True


# ── Leaderboard helpers ──────────────────────────────────────────────────────
def _print_leaderboard_page(players, page, highlight_username=None):
    start = page * PAGE_SIZE
    end = min(start + PAGE_SIZE, len(players))
    total_pages = (len(players) + PAGE_SIZE - 1) // PAGE_SIZE

    print(f"\n{C}{'═' * 38}{RST}")
    print(f"  {Y}{BRT}   LEADERBOARD{RST}  "
          f"{DIM}(Page {page + 1}/{total_pages}){RST}")
    print(f"{C}{'═' * 38}{RST}")
    print(f"  {BRT}{'Rank':<8}{'Player':<15}{'Score'}{RST}")
    print(f"{C}{'-' * 38}{RST}")

    for i in range(start, end):
        rank = i + 1
        username = players[i].get("username", "---")
        score = players[i].get("highScore", 0)

        medal = MEDALS.get(rank, "     ")
        row = f"{medal} {rank:<4} {username:<15}{score}"

        if highlight_username and username == highlight_username:
            print(f"{Y}{'>' * 38}{RST}")
            print(f"  {row}")
            print(f"{Y}{'>' * 38}{RST}")
        elif rank == 1:
            print(f"  {Y}{BRT}{row}{RST}")
        elif rank == 2:
            print(f"  {W}{BRT}{row}{RST}")
        elif rank == 3:
            print(f"  {Fore.RED}{BRT}{row}{RST}")
        else:
            print(f"  {row}")

    print(f"{C}{'═' * 38}{RST}")


def _search_player(players):
    """Ask for username and display result inline (no screen clear). Returns True if found."""
    username = _input_with_sfx(f"  {C}Enter username to search: {RST}").strip()
    if not username:
        _typewriter("  No username entered.", color=R)
        return False

    idx = next(
        (i for i, p in enumerate(players) if p.get("username") == username), None
    )

    if idx is None:
        _typewriter(f"  Player '{username}' not found in leaderboard.", color=R)
        return False

    context_start = max(0, idx - 2)
    context_end = min(len(players), idx + 3)
    context_players = players[context_start:context_end]

    print(f"\n{C}{'═' * 38}{RST}")
    print(f"  {Y}{BRT}SEARCH RESULT: {username}{RST}")
    print(f"{C}{'═' * 38}{RST}")
    print(f"  {BRT}{'Rank':<8}{'Player':<15}{'Score'}{RST}")
    print(f"{C}{'-' * 38}{RST}")

    for i, player in enumerate(context_players):
        rank = context_start + i + 1
        uname = player.get("username", "---")
        score = player.get("highScore", 0)
        row = f"{rank:<8}{uname:<15}{score}"
        if uname == username:
            print(f"{Y}  +{'─' * 34}+{RST}")
            print(f"{Y}  | {row:<34}|{RST}")
            print(f"{Y}  +{'─' * 34}+{RST}")
        else:
            print(f"    {row}")

    print(f"{C}{'═' * 38}{RST}")
    return True


def display_leaderboard():
    clear_screen()
    result = get_leaderboard()

    if not result["success"]:
        _typewriter(f"\n{'═' * 38}", color=R)
        _typewriter(f"Error: {result['message']}", color=R)
        _typewriter(f"{'═' * 38}\n", color=R)
        pause_after_message()
        return

    players = result["players"]

    if not players:
        _typewriter(f"\n{'═' * 38}", color=Y)
        _typewriter("  No leaderboard data available yet.")
        _typewriter(f"{'═' * 38}\n", color=Y)
        pause_after_message()
        return

    page = 0
    total_pages = (len(players) + PAGE_SIZE - 1) // PAGE_SIZE

    while True:
        clear_screen()
        _print_leaderboard_page(players, page)

        has_prev = page > 0
        has_next = page < total_pages - 1

        options = []
        if has_prev:
            options.append(("prev", "Previous page"))
        if has_next:
            options.append(("next", "Next page"))
        options.append(("goto", f"Go to page (1-{total_pages})"))
        options.append(("search", "Search player"))
        options.append(("back", "Back to main menu"))

        print()
        for i, (_, label) in enumerate(options, start=1):
            _typewrite_option(f"  {C}{i}.{RST} ", label)

        choice = _menu_input()

        if not choice.isdigit() or not (1 <= int(choice) <= len(options)):
            continue

        action = options[int(choice) - 1][0]

        if action == "prev":
            page -= 1
        elif action == "next":
            page += 1
        elif action == "goto":
            # Keep leaderboard visible; ask for page number inline below it
            target = _input_with_sfx(f"  Enter page number (1-{total_pages}): ").strip()
            if target.isdigit() and 1 <= int(target) <= total_pages:
                page = int(target) - 1
            # invalid input falls through; loop clears and redraws leaderboard
        elif action == "search":
            # Keep leaderboard visible; search input appears below it
            _search_player(players)
            while True:
                # Show sub-menu options below whatever is currently on screen
                print()
                _typewrite_option(f"  {C}1.{RST} ", "Back to leaderboard")
                _typewrite_option(f"  {C}2.{RST} ", "Search player")
                _typewrite_option(f"  {C}3.{RST} ", "Back to main menu")
                sub = _menu_input()
                if sub == "1":
                    break
                elif sub == "2":
                    # Re-draw leaderboard fresh, then search below it
                    clear_screen()
                    _print_leaderboard_page(players, page)
                    print()
                    _search_player(players)
                elif sub == "3":
                    return
                # invalid input: sub-menu re-prints below on next iteration
        elif action == "back":
            return


# ── Input validation ─────────────────────────────────────────────────────────
def validate_credentials(username, password):
    if not username.strip():
        _typewriter("Error: Username cannot be empty.", color=R)
        return False
    if " " in username:
        _typewriter("Error: Username cannot contain spaces.", color=R)
        return False
    if not password.strip():
        _typewriter("Error: Password cannot be empty.", color=R)
        return False
    return True


# ── Code handlers ─────────────────────────────────────────────────────────────
def handle_register_code(code, username):
    if code == 0:
        _typewriter("Registration Successful!", color=G)
    elif code == -1:
        _typewriter(f"Error: Username '{username}' is already taken.", color=R)
    elif code == -2:
        _typewriter("Error: Username cannot be empty.", color=R)
    elif code == -3:
        _typewriter("Error: Password cannot be empty.", color=R)
    else:
        _typewriter("Error: Cannot connect to backend.", color=R)


def handle_login_code(code):
    if code == 0:
        _typewriter("Login successful!", color=G)
    elif code == -1:
        _typewriter("Error: Username not found.", color=R)
    elif code == -2:
        _typewriter("Error: Incorrect password.", color=R)
    else:
        _typewriter("Error: Cannot connect to backend.", color=R)


def handle_remove_code(code, username):
    if code == 0:
        _typewriter(f"User '{username}' removed successfully.", color=G)
    elif code == -1:
        _typewriter(f"Error: No user with username '{username}' found.", color=R)
    else:
        _typewriter("Error: Cannot connect to backend.", color=R)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    global current_user
    show_intro()
    _bgm.play("menu_bgm")
    try:
        while True:
            action = show_menu()

            if action == "login":
                username = _input_with_sfx(f"  {C}Username: {RST}")
                password = _input_with_sfx(f"  {C}Password: {RST}")
                if not validate_credentials(username, password):
                    pause_after_message()
                    continue
                result = login_user(username, password)
                code = result["code"]
                handle_login_code(code)
                if code == 0:
                    current_user = username
                pause_after_message()

            elif action == "register":
                username = _input_with_sfx(f"  {C}New Username: {RST}")
                password = _input_with_sfx(f"  {C}New Password: {RST}")
                if not validate_credentials(username, password):
                    pause_after_message()
                    continue
                result = register_user(username, password)
                code = result["code"]
                handle_register_code(code, username)
                pause_after_message()

            elif action == "start":
                start_game(current_user)

            elif action == "leaderboard":
                display_leaderboard()

            elif action == "logout":
                _typewriter(f"Logged out. See you, {current_user}!", color=G)
                current_user = None
                pause_after_message()

            elif action == "exit":
                _bgm.stop()
                clear_screen()
                _typewriter("Goodbye! See you next time ~", delay=0.04, color=Y)
                time.sleep(1.5)
                sys.exit()

            elif action == "remove":
                username = _input_with_sfx(f"  {C}Username to remove: {RST}")
                result = remove_user(username)
                code = result["code"]
                handle_remove_code(code, username)
                pause_after_message()

            # TESTING CODE
            elif action == "test":
                start_game("TEST USER")
                _bgm.switch("menu_bgm")
            # TESTING CODE

            else:
                clear_screen()
                _typewriter("Invalid choice, try again.", color=R)
                pause_after_message()
    except (KeyboardInterrupt, EOFError):
        _bgm.stop()
        print(f"\n{Y}Exiting...{RST}")
        sys.exit(0)


if __name__ == "__main__":
    main()
