import sys
from auth import login_user, register_user, remove_user, get_leaderboard
from game_logic import start_game_logic


# Display Menu
def show_menu():
    print("\n=== FLAPPY BIRD ===")
    print("1. Login")
    print("2. Register")
    print("3. Leaderboard")
    print("4. Exit")
    print("DEBUG: 5. Remove User")
    return input("Select an option: ")

# Core game logic function
def start_game(username):
    print(f"\nWelcome, {username}!")
    print("--- GAME STARTING ---")
    print(" (control options) ")
    # Flappy Bird logic
    start_game_logic(username)
    input("\nGame Over! Press Enter to return to menu...")

PAGE_SIZE = 10


def _print_leaderboard_page(players, page, highlight_username=None):
    start = page * PAGE_SIZE
    end = min(start + PAGE_SIZE, len(players))
    total_pages = (len(players) + PAGE_SIZE - 1) // PAGE_SIZE

    print("\n" + "=" * 36)
    print(f"       LEADERBOARD  (Page {page + 1}/{total_pages})")
    print("=" * 36)
    print(f"{'Rank':<7}{'Player':<15}{'Score':<4}")
    print("-" * 36)

    for i in range(start, end):
        rank = i + 1
        username = players[i].get("username", "---")
        score = players[i].get("highScore", 0)
        row = f"{rank:<7}{username:<15}{score:<4}"
        if highlight_username and username == highlight_username:
            print(">" * 36)
            print(f"  {row}")
            print(">" * 36)
        else:
            print(f"  {row}")

    print("=" * 36)


def _search_player(players):
    username = input("Enter username to search: ").strip()
    if not username:
        print("No username entered.")
        return

    idx = next(
        (i for i, p in enumerate(players) if p.get("username") == username), None
    )

    if idx is None:
        print(f"Player '{username}' not found in leaderboard.")
        return

    context_start = max(0, idx - 2)
    context_end = min(len(players), idx + 3)
    context_players = players[context_start:context_end]

    print("\n" + "=" * 36)
    print(f"   SEARCH RESULT: {username}")
    print("=" * 36)
    print(f"{'Rank':<7}{'Player':<15}{'Score':<4}")
    print("-" * 36)

    for i, player in enumerate(context_players):
        rank = context_start + i + 1
        uname = player.get("username", "---")
        score = player.get("highScore", 0)
        row = f"{rank:<7}{uname:<15}{score:<4}"
        if uname == username:
            print("+" + "-" * 34 + "+")
            print(f"| {row:<34}|")
            print("+" + "-" * 34 + "+")
        else:
            print(f"  {row}")

    print("=" * 36)


def display_leaderboard():
    result = get_leaderboard()

    if not result["success"]:
        print("\n" + "=" * 36)
        print(f"Error: {result['message']}")
        print("=" * 36 + "\n")
        input("Press Enter to return to menu...")
        return

    players = result["players"]

    if not players:
        print("\n" + "=" * 36)
        print("No leaderboard data available yet.")
        print("=" * 36 + "\n")
        input("Press Enter to return to menu...")
        return

    page = 0
    total_pages = (len(players) + PAGE_SIZE - 1) // PAGE_SIZE

    while True:
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
            print(f"{i}. {label}")

        choice = input("Select an option: ").strip()

        if not choice.isdigit() or not (1 <= int(choice) <= len(options)):
            print("Invalid choice, try again.")
            continue

        action = options[int(choice) - 1][0]

        if action == "prev":
            page -= 1
        elif action == "next":
            page += 1
        elif action == "goto":
            target = input(f"Enter page number (1-{total_pages}): ").strip()
            if target.isdigit() and 1 <= int(target) <= total_pages:
                page = int(target) - 1
            else:
                print(f"Invalid page number, must be between 1 and {total_pages}.")
        elif action == "search":
            _search_player(players)
            while True:
                print()
                print("1. Back to leaderboard")
                print("2. Search player")
                print("3. Back to main menu")
                sub = input("Select an option: ").strip()
                if sub == "1":
                    break
                elif sub == "2":
                    _search_player(players)
                elif sub == "3":
                    return
                else:
                    print("Invalid choice, try again.")
        elif action == "back":
            return

# Input validation
def validate_credentials(username, password):
    if not username.strip():
        print("Error: Username cannot be empty.")
        return False
    if " " in username:
        print("Error: Username cannot contain spaces.")
        return False
    if not password.strip():
        print("Error: Password cannot be empty.")
        return False
    return True

# Code handlers for string responses
def handle_register_code(code, username):
    if code == 0:
        print("Registration Successful!")
    elif code == -1:
        print(f"Error: Registration Failed: Username '{username}' is already taken.")
    elif code == -2:
        print("Error: Registration Failed: Username cannot be empty.")
    elif code == -3:
        print("Error: Registration Failed: Password cannot be empty.")
    else:
        print("Error: Cannot connect to backend.")

def handle_login_code(code):
    if code == 0:
        print("Login successful!")
    elif code == -1:
        print("Error: Login Failed: Username not found.")
    elif code == -2:
        print("Error: Login Failed: Incorrect password.")
    else:
        print("Error: Cannot connect to backend.")

def handle_remove_code(code, username):
    if code == 0:
        print(f"User '{username}' removed successfully.")
    elif code == -1:
        print(f"Error: No user with username '{username}' found.")
    else:
        print("Error: Cannot connect to backend.")

def main():
    try:
        while True:
            choice = show_menu()

            if choice == "1":
                username = input("Username: ")
                password = input("Password: ")

                if not validate_credentials(username, password):
                    continue

                # Call to external module
                result = login_user(username, password)
                code = result["code"]

                handle_login_code(code)

                if code == 0:
                    start_game(username)

            elif choice == "2":
                username = input("New Username: ")
                password = input("New Password: ")

                if not validate_credentials(username, password):
                    continue

                result = register_user(username, password)
                code = result["code"]

                handle_register_code(code, username)

            elif choice == "3":
                display_leaderboard()

            elif choice == "4":
                print("Goodbye!")
                sys.exit()

            elif choice == "5":
                print("Removing user...")
                username = input("Username to remove: ")
                result = remove_user(username)
                code = result["code"]

                handle_remove_code(code, username)

            # TESTING CODE
            elif choice == "6":
                start_game("TEST USER")
            # TESTING CODE

            else:
                print("Invalid choice, try again.")
    except (KeyboardInterrupt, EOFError):
        print("\nExiting...")
        sys.exit(0)

if __name__ == "__main__":
    main()
