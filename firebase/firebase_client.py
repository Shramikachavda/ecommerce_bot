import firebase_admin
from firebase_admin import credentials, firestore, auth
from firebase_admin.exceptions import FirebaseError
from google.auth.exceptions import DefaultCredentialsError
from config.settings import settings


class FirebaseClient:
    def __init__(self):
        self.app = None
        self.db = None
        self.auth = None
        self._initialize_firebase()

    def _initialize_firebase(self):
        """Initialize Firebase with error handling"""
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(settings.FIREBASE_KEY_PATH)
                self.app = firebase_admin.initialize_app(cred)
            else:
                self.app = firebase_admin.get_app()

            # Initialize services
            self.db = firestore.client()
            self.auth = auth

        except FileNotFoundError:
            raise RuntimeError("Firebase key file not found.")
        except DefaultCredentialsError:
            raise RuntimeError("Invalid Firebase credentials.")
        except FirebaseError as e:
            raise RuntimeError(f"Firebase initialization failed: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {str(e)}")

    def get_firestore(self):
        try:
            return self.db
        except Exception as e:
            raise RuntimeError(f"Firestore error: {str(e)}")

    def get_auth(self):
        try:
            return self.auth
        except Exception as e:
            raise RuntimeError(f"Auth error: {str(e)}")
