import requests
import json
from firebase.firebase_client import FirebaseClient

FIREBASE_API_KEY = "AIzaSyDOJRXvdFJFcwVAfA5AJs_i-SDoqku9WIU"  # Found in Firebase console -> Project settings -> General -> Web API Key

def get_id_token(email, password):
    """
    Sign in with email/password via Firebase REST API to get ID token
    """
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json()
        return data["idToken"]  # This is what you pass in WebSocket
    else:
        print("Error signing in:", response.text)
        return None

if __name__ == "__main__":
    client = FirebaseClient()

    # 1️⃣ Create user (optional if already exists)
    auth = client.get_auth()
    try:
        user = auth.create_user(email="testuser@example.com", password="TestPassword123!")
        print("User created:", user.uid)
    except Exception as e:
        print("User creation failed (maybe already exists):", e)

    # 2️⃣ Get ID token via email/password
    id_token = get_id_token("testuser@example.com", "TestPassword123!")
    print("Use this ID token in WebSocket:")
    print(f"Bearer {id_token}")
