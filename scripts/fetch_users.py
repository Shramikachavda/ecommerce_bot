from firebase import FirebaseClient

def fetch_all_users():
    print("🚀 Starting user fetch script...")

    try:
        # Initialize Firebase client
        print("🔑 Connecting to Firebase...")
        client = FirebaseClient()
        db = client.get_firestore()
        print("✅ Firebase connection established.")

        # Access the users collection
        print("📂 Fetching all documents from 'users' collection...")
        users_ref = db.collection("users")
        docs = users_ref.stream()

        found = False
        for doc in docs:
            found = True
            print(f"👤 User ID: {doc.id}")
            print(f"   Data: {doc.to_dict()}")
            print("-" * 50)

        if not found:
            print("⚠️ No users found in the 'users' collection.")

    except Exception as e:
        print("❌ Error while fetching users:", e)

    print("🏁 Script finished.")

if __name__ == "__main__":
    fetch_all_users()
