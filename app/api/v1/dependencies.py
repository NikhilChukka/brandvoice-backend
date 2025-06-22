from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
from app.models.user import User
from app.services.user_service_new import UserService
from fastapi import status
from app.core.firebase import initialize_firebase  # Add this import

security = HTTPBearer()

async def get_firebase_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> User:
    """
    Get the current user from the Firebase token only (no Firestore).
    """
    try:
        initialize_firebase()  # Ensure Firebase Admin SDK is initialized
        print(f"***Received Firebase token: {credentials.credentials}***")
        decoded_token = auth.verify_id_token(credentials.credentials)
        firebase_uid = decoded_token["uid"]
        print(f"***Decoded Firebase UID: {firebase_uid}***")
        user_service = UserService()
        user = await user_service.get_user_by_firebase_uid(firebase_uid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in Firebase Auth"
            )
        return user
    except Exception as e:
        print(f"***Error verifying Firebase token: {e}***")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token"
        )
