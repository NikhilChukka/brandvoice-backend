from sqlmodel import SQLModel # Import SQLModel if it's the base for your models

# If you are exclusively using SQLModel for all your table definitions,
# and SQLModel.metadata is used in your Alembic env.py, 
# then a separate Base definition might not be strictly necessary here.
# However, ensure that all your SQLModel table models are imported somewhere
# so that their metadata is registered with SQLModel.metadata before Alembic runs.

# For example, you might have an __init__.py in your models directory that imports all model files:
# from .user import User
# from .product import Product
# ... and so on for all your models
