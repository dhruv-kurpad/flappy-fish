import sys
import time
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


def wait_to_clear():
    """Wait before the next menu redraw so messages are not cleared immediately."""
    input(f"\n  {DIM}Press Enter to continue...{RST}")


# ── Display Menu ─────────────────────────────────────────────────────────────
def show_menu():
    clear_screen(show_banner=True)
    print(f"\n{Y}{'═' * 32}{RST}")
    print(f"  {Y}{BRT}        FLAPPY  FISH{RST}")
    print(f"{Y}{'═' * 32}{RST}")

    if current_user:
        print(f"  {G}● Logged in as: {BRT}{current_user}{RST}")
        print(f"{Y}{'─' * 32}{RST}")
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

    for i, (_, label) in enumerate(options, start=1):
        print(f"  {C}{i}.{RST} {label}")
    print(f"  {DIM}{len(options) + 1}. Remove User (DEBUG){RST}")
    print(f"{Y}{'═' * 32}{RST}")

    choice = input(f"  {C}› {RST}").strip()
    # TESTING CODE
    if choice == str(len(options) + 2):
        return "test"
    # TESTING CODE
    if choice.isdigit() and 1 <= int(choice) <= len(options):
        return options[int(choice) - 1][0]
    if choice == str(len(options) + 1):
        return "remove"
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
    print(f"  {C}1.{RST} Start game")
    print(f"  {C}2.{RST} Back to main menu")
    print(f"{C}{'═' * 42}{RST}")
    choice = input(f"  {C}› {RST}").strip()
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
        print(f"  {C}1.{RST} Play again")
        print(f"  {C}2.{RST} Back to main menu")
        print(f"{R}{'═' * 32}{RST}")
        choice = input(f"  {C}› {RST}").strip()
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
    username = input(f"  {C}Enter username to search: {RST}").strip()
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
        input("Press Enter to return to menu...")
        return

    players = result["players"]

    if not players:
        print(f"\n{Y}{'═' * 38}{RST}")
        print("  No leaderboard data available yet.")
        print(f"{Y}{'═' * 38}{RST}\n")
        input("Press Enter to return to menu...")
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
            print(f"  {C}{i}.{RST} {label}")

        choice = input(f"  {C}› {RST}").strip()

        if not choice.isdigit() or not (1 <= int(choice) <= len(options)):
            print(f"{R}Invalid choice, try again.{RST}")
            wait_to_clear()
            continue

        action = options[int(choice) - 1][0]

        if action == "prev":
            page -= 1
        elif action == "next":
            page += 1
        elif action == "goto":
            target = input(f"  Enter page number (1-{total_pages}): ").strip()
            if target.isdigit() and 1 <= int(target) <= total_pages:
                page = int(target) - 1
            else:
                print(f"{R}Invalid page number, must be between 1 and {total_pages}.{RST}")
                wait_to_clear()
        elif action == "search":
            _search_player(players)
            while True:
                print()
                print(f"  {C}1.{RST} Back to leaderboard")
                print(f"  {C}2.{RST} Search player")
                print(f"  {C}3.{RST} Back to main menu")
                sub = input(f"  {C}› {RST}").strip()
                if sub == "1":
                    break
                elif sub == "2":
                    clear_screen()
                    _search_player(players)
                elif sub == "3":
                    return
                else:
                    print(f"{R}Invalid choice, try again.{RST}")
                    wait_to_clear()
        elif action == "back":
            return


# ── Input validation ─────────────────────────────────────────────────────────
def validate_credentials(username, password):
    if not username.strip():
        print(f"{R}Error: Username cannot be empty.{RST}")
        wait_to_clear()
        return False
    if " " in username:
        print(f"{R}Error: Username cannot contain spaces.{RST}")
        wait_to_clear()
        return False
    if not password.strip():
        print(f"{R}Error: Password cannot be empty.{RST}")
        wait_to_clear()
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
    clear_screen(show_banner=True)
    try:
        while True:
            action = show_menu()

            if action == "login":
                username = input(f"  {C}Username: {RST}")
                password = input(f"  {C}Password: {RST}")
                if not validate_credentials(username, password):
                    continue
                result = login_user(username, password)
                code = result["code"]
                handle_login_code(code)
                if code == 0:
                    current_user = username
                wait_to_clear()

            elif action == "register":
                username = input(f"  {C}New Username: {RST}")
                password = input(f"  {C}New Password: {RST}")
                if not validate_credentials(username, password):
                    continue
                result = register_user(username, password)
                code = result["code"]
                handle_register_code(code, username)
                wait_to_clear()

            elif action == "start":
                start_game(current_user)

            elif action == "leaderboard":
                display_leaderboard()

            elif action == "logout":
                print(f"{G}Logged out. See you, {current_user}!{RST}")
                current_user = None
                wait_to_clear()

            elif action == "exit":
                _typewriter(f"{Y}Goodbye! See you next time ~{RST}", delay=0.04)
                sys.exit()

            elif action == "remove":
                print(f"{DIM}Removing user...{RST}")
                username = input(f"  {C}Username to remove: {RST}")
                result = remove_user(username)
                code = result["code"]
                handle_remove_code(code, username)
                wait_to_clear()

            # TESTING CODE
            elif action == "test":
                start_game("TEST USER")
            # TESTING CODE

            else:
                print(f"{R}Invalid choice, try again.{RST}")
                wait_to_clear()
    except (KeyboardInterrupt, EOFError):
        print(f"\n{Y}Exiting...{RST}")
        sys.exit(0)


if __name__ == "__main__":
    main()
