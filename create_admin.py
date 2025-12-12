from database import Database

def create_admin_account():
    
    db = Database()
    
    print("-----------------------------------")
    print("   LOST & FOUND ADMIN CREATOR")
    print("-----------------------------------")
    
    username = input("Enter new Admin Username: ")
    password = input("Enter new Admin Password: ")
    
    confirm = input(f"Create Admin user '{username}'? (y/n): ")
    if confirm.lower() != 'y':
        print("Cancelled.")
        return

    # Create the account with "Admin"
    if db.register_user(username, password, "Admin"):
        print("\n[SUCCESS] Admin account created successfully!")
        print("You can now login with this account in the main app.")
    else:
        print("\n[ERROR] Username already exists. Please try a different one.")

if __name__ == "__main__":
    create_admin_account()