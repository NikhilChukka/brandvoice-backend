from dotenv import load_dotenv
import os
from app.core.db import engine  # Assuming your synchronous engine is here
from app.models import user, schedule, content, product  # Import your SQLModel models here
# from app.models import other_model # etc.
from sqlmodel import SQLModel

# Load .env file from the current directory (app)
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

def create_db_and_tables():
    print("Creating database tables...")
    # Make sure all SQLModel models are imported before calling create_all
    # so that their metadata is registered with SQLModel.metadata
    SQLModel.metadata.create_all(engine)
    print("Database tables created.")

if __name__ == "__main__":
    # This check ensures that if you import this file elsewhere,
    # the create_db_and_tables function isn't automatically run.
    create_db_and_tables()