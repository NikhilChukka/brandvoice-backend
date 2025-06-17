import firebase_admin
from firebase_admin import credentials, firestore
from functools import lru_cache
import os
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)

_firebase_app = None
_firestore_client = None

def initialize_firebase():
    """
    Initialize Firebase Admin SDK and return the Firestore client.
    This function is cached to ensure we only initialize Firebase once.
    """
    global _firebase_app, _firestore_client
    
    if _firebase_app is None:
        try:
            settings = get_settings()
            # Initialize Firebase Admin SDK
            cred = credentials.Certificate(settings.google_application_credentials)
            _firebase_app = firebase_admin.initialize_app(cred)
            _firestore_client = firestore.client()
            logger.info("Firebase initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")
            raise RuntimeError(f"Failed to initialize Firebase: {str(e)}")
    
    return _firestore_client

def get_firestore_client():
    """
    Get the Firestore client instance.
    """
    if _firestore_client is None:
        return initialize_firebase()
    return _firestore_client 