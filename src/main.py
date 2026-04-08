import sys
import time
import random
import subprocess
import threading
from pathlib import Path
from auth import login_user, register_user, remove_user, get_leaderboard
from game_logic import start_game_logic
from colorama import init, Fore, Style

init(autoreset=True)

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

    val = input("").strip()   # prompt already printed above

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


def _typewriter(text, delay=0.03):
    for ch in text:
        print(ch, end="", flush=True)
        time.sleep(delay)
    print()


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
    """Input with blinking ><> fish cursor and button click SFX on Enter."""
    stop = threading.Event()
    states = [
        f"{Y}{BRT}><>{RST}",
        "   ",
        f"{C}{BRT}><>{RST}",
        "   ",
    ]
    # Separate leading newlines from the prompt body, then strip caller indentation
    body = prompt.lstrip("\n")
    leading_newlines = "\n" * (len(prompt) - len(body))
    body = body.lstrip(" ")

    if leading_newlines:
        sys.stdout.write(leading_newlines)
        sys.stdout.flush()

    sys.stdout.write(f"  {states[0]} {body}")
    sys.stdout.flush()

    def _animate():
        tick = 0
        while not stop.is_set():
            time.sleep(0.25)
            tick += 1
            fish = states[tick % len(states)]
            sys.stdout.write(f"\033[s\r\033[2C{fish}\033[u")
            sys.stdout.flush()

    t = threading.Thread(target=_animate, daemon=True)
    t.start()
    val = input("").strip()
    stop.set()
    t.join(timeout=0.4)
    _play_sfx("button_click")
    return val


def pause_after_message():
    _input_with_sfx(f"\n{DIM}Press Enter to continue...{RST}")



# ── Display Menu ─────────────────────────────────────────────────────────────
def _draw_menu(options, selected_idx=None, selected_label=None, animate=False):
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

    if selected_label is not None:
        print(f"  {C}›{RST} {Y}{BRT}{selected_label}{RST}")


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
        _draw_menu(options, selected_idx=selected_idx, selected_label=action)
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
    clear_screen()
    _typewriter(f"{G}Welcome, {username}! Get ready...{RST}", delay=0.04)
    while True:
        if not show_rules():
            return
        clear_screen()
        print(f"{Y}--- GAME STARTING ---{RST}")
        print(" (control options) ")
        start_game_logic(username)

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
    username = _input_with_sfx(f"  {C}Enter username to search: {RST}").strip()
    if not username:
        print(f"{R}No username entered.{RST}")
        return

    idx = next(
        (i for i, p in enumerate(players) if p.get("username") == username), None
    )

    if idx is None:
        print(f"{R}Player '{username}' not found in leaderboard.{RST}")
        return

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


def display_leaderboard():
    clear_screen()
    result = get_leaderboard()

    if not result["success"]:
        print(f"\n{R}{'═' * 38}{RST}")
        print(f"{R}Error: {result['message']}{RST}")
        print(f"{R}{'═' * 38}{RST}\n")
        _input_with_sfx("Press Enter to return to menu...")
        return

    players = result["players"]

    if not players:
        print(f"\n{Y}{'═' * 38}{RST}")
        print("  No leaderboard data available yet.")
        print(f"{Y}{'═' * 38}{RST}\n")
        _input_with_sfx("Press Enter to return to menu...")
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
            print(f"{R}Invalid choice, try again.{RST}")
            continue

        action = options[int(choice) - 1][0]

        if action == "prev":
            page -= 1
        elif action == "next":
            page += 1
        elif action == "goto":
            target = _input_with_sfx(f"  Enter page number (1-{total_pages}): ").strip()
            if target.isdigit() and 1 <= int(target) <= total_pages:
                page = int(target) - 1
            else:
                print(f"{R}Invalid page number, must be between 1 and {total_pages}.{RST}")
        elif action == "search":
            _search_player(players)
            while True:
                print()
                _typewrite_option(f"  {C}1.{RST} ", "Back to leaderboard")
                _typewrite_option(f"  {C}2.{RST} ", "Search player")
                _typewrite_option(f"  {C}3.{RST} ", "Back to main menu")
                sub = _menu_input()
                if sub == "1":
                    break
                elif sub == "2":
                    clear_screen()
                    _search_player(players)
                elif sub == "3":
                    return
                else:
                    print(f"{R}Invalid choice, try again.{RST}")
        elif action == "back":
            return


# ── Input validation ─────────────────────────────────────────────────────────
def validate_credentials(username, password):
    if not username.strip():
        print(f"{R}Error: Username cannot be empty.{RST}")
        return False
    if " " in username:
        print(f"{R}Error: Username cannot contain spaces.{RST}")
        return False
    if not password.strip():
        print(f"{R}Error: Password cannot be empty.{RST}")
        return False
    return True


# ── Code handlers ─────────────────────────────────────────────────────────────
def handle_register_code(code, username):
    if code == 0:
        print(f"{G}Registration Successful!{RST}")
    elif code == -1:
        print(f"{R}Error: Username '{username}' is already taken.{RST}")
    elif code == -2:
        print(f"{R}Error: Username cannot be empty.{RST}")
    elif code == -3:
        print(f"{R}Error: Password cannot be empty.{RST}")
    else:
        print(f"{R}Error: Cannot connect to backend.{RST}")


def handle_login_code(code):
    if code == 0:
        print(f"{G}Login successful!{RST}")
    elif code == -1:
        print(f"{R}Error: Username not found.{RST}")
    elif code == -2:
        print(f"{R}Error: Incorrect password.{RST}")
    else:
        print(f"{R}Error: Cannot connect to backend.{RST}")


def handle_remove_code(code, username):
    if code == 0:
        print(f"{G}User '{username}' removed successfully.{RST}")
    elif code == -1:
        print(f"{R}Error: No user with username '{username}' found.{RST}")
    else:
        print(f"{R}Error: Cannot connect to backend.{RST}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    global current_user
    show_intro()
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
                print(f"{G}Logged out. See you, {current_user}!{RST}")
                current_user = None
                pause_after_message()

            elif action == "exit":
                _typewriter(f"{Y}Goodbye! See you next time ~{RST}", delay=0.04)
                sys.exit()

            elif action == "remove":
                print(f"{DIM}Removing user...{RST}")
                username = _input_with_sfx(f"  {C}Username to remove: {RST}")
                result = remove_user(username)
                code = result["code"]
                handle_remove_code(code, username)
                pause_after_message()

            # TESTING CODE
            elif action == "test":
                start_game("TEST USER")
            # TESTING CODE

            else:
                print(f"{R}Invalid choice, try again.{RST}")
                pause_after_message()
    except (KeyboardInterrupt, EOFError):
        print(f"\n{Y}Exiting...{RST}")
        sys.exit(0)


if __name__ == "__main__":
    main()
