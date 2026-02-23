import sys
from auth import login_user


# Display Menu
def show_menu():
    print("\n=== FLAPPY BIRD ===")
    print("1. Login")
    print("2. Exit")
    return input("Select an option: ")

# Core game logic function
def start_game(username):
    print(f"\nWelcome, {username}!")
    print("--- GAME STARTING ---")
    print(" (control options) ")
    # Flappy Bird logic 
    input("\nGame Over! Press Enter to return to menu...")

def main():
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
            print("Goodbye!")
            sys.exit()
        else:
            print("Invalid choice, try again.")

if __name__ == "__main__":
    main()