import sys
from auth import login_user, register_user, remove_user


# Display Menu
def show_menu():
    print("\n=== FLAPPY BIRD ===")
    print("1. Login")
    print("2. Register")
    print("3. Exit")
    print("DEBUG: 4. Remove User")
    return input("Select an option: ")

# Core game logic function
def start_game(username):
    print(f"\nWelcome, {username}!")
    print("--- GAME STARTING ---")
    print(" (control options) ")
    # Flappy Bird logic 
    input("\nGame Over! Press Enter to return to menu...")

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
                print("Goodbye!")
                sys.exit()
            elif choice == "4":
                print("Removing user...")
                username = input("Username to remove: ")
                result = remove_user(username)


                if result["success"]:
                    print(result["message"])
                else:
                    print(f"Error: {result['message']}")
            else:
                print("Invalid choice, try again.")
    except (KeyboardInterrupt, EOFError):
        print("\nExiting...")
        sys.exit(0)

if __name__ == "__main__":
    main()