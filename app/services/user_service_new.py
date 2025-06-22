from firebase_admin import auth
from app.models.user import User
from datetime import datetime

class UserService:
    def __init__(self):
        pass  # No Firestore session needed

    async def get_user_by_firebase_uid(self, firebase_uid: str) -> User | None:
        try:
            print(f"***Fetching user with Firebase UID: {firebase_uid}***")
            # firebase_user = auth.get_user(firebase_uid)
            # print(f"***Found Firebase user: {firebase_user.uid}***")
            now = datetime.utcnow()
            return User(
                id=firebase_uid,
                created_at=now,
                updated_at=now,
                )
                # email=firebase_user.email,
                # full_name=firebase_user.display_name or "",
                # is_active=True,
                # is_superuser=False,
                # created_at=now,
                # updated_at=now
            # )
        except auth.UserNotFoundError:
            return None

    # All Firestore-based user methods are removed
