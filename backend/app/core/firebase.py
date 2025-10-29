import firebase_admin
from firebase_admin import credentials, firestore, storage
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cred = credentials.Certificate(os.path.join(BASE_DIR, "firebase-key.json"))

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
    "storageBucket": "deepfake-fc59d.firebasestorage.app"
    })


db = firestore.client()
bucket = storage.bucket()
