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

def main():
    try:
        while True:
            choice = show_menu()

            if choice == "1":
                username = input("Username: ")
                password = input("Password: ")

                # Call to external module
                result = login_user(username, password)

                if result["success"]:
                    print(result["message"])
                    start_game(username)
                else:
                    print(f"Error: {result['message']}")

            elif choice == "2":
                username = input("New Username: ")
                password = input("New Password: ")

                result = register_user(username, password)

                if result["success"]:
                    print(result["message"])
                else:
                    print(f"Error: {result['message']}")

            elif choice == "3":
                display_leaderboard()
            elif choice == "4":
                print("Goodbye!")
                sys.exit()
            elif choice == "5":
                print("Removing user...")
                username = input("Username to remove: ")
                result = remove_user(username)


                if result["success"]:
                    print(result["message"])
                else:
                    print(f"Error: {result['message']}")

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
    