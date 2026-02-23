def login_user(username, password):
    
    # USE this function to send the HTTP request to spring boot

    
    # The below code is just for testing and to give an example of how itd work
    if username == "admin" and password == "password":
        return {"success": True, "message": "Login successful!"}
    else:
        return {"success": False, "message": "Invalid login details!"}

def register_user(username, password):
    # Registration logic function
    return {"success": True, "message": "User registered successfully!"}