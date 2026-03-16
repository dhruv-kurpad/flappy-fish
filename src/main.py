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

def display_leaderboard():
    result = get_leaderboard()

    print("\n" + "=" * 30)
    print("          LEADERBOARD")
    print("=" * 30)

    if not result["success"]:
        print(f"Error: {result['message']}")
        print("=" * 30 + "\n")
        input("Press Enter to return to menu...")
        return

    players = result["players"]

    if not players:
        print("No leaderboard data available yet.")
        print("=" * 30 + "\n")
        input("Press Enter to return to menu...")
        return

    print(f"{'Rank':<7}{'Player':<15}{'Score':<4}")
    print("-" * 30)

    for rank, player in enumerate(players, start=1):
        username = player.get("username", "---")
        score = player.get("highScore", 0)
        print(f"{rank:<7}{username:<15}{score:<4}")

    print("=" * 30 + "\n")
    input("Press Enter to return to menu...")

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
