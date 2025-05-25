import os
from langchain_community.utilities import SQLDatabase

# --- Database Path Configuration ---
# This logic should be consistent with the setup_database.py script
# to locate the database file correctly.
DB_FILE_NAME = "data_query_assistant.db"

# Assuming this script (database.py) is in src/core/
# Navigate up two levels to get to the project root
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, DB_FILE_NAME)


def get_sqlite_uri() -> str:
    """
    Constructs the SQLite URI for SQLAlchemy.
    Ensures the database file exists.
    """
    if not os.path.exists(DB_PATH):
        # Suggest running the setup script if the DB doesn't exist.
        # In a real app, you might have more robust error handling or setup triggers.
        error_message = (
            f"Database file not found at {DB_PATH}. "
            f"Please run the database setup script (e.g., python src/scripts/setup_database.py) "
            "to create and populate the database."
        )
        raise FileNotFoundError(error_message)
    return f"sqlite:///{DB_PATH}"


def get_db_instance() -> SQLDatabase:
    DB_URI = get_sqlite_uri()
    # db_path = "sqlite:///../data/data_query_assistant.db"
    db = SQLDatabase.from_uri(database_uri=DB_URI)
    return db


db_instance = get_db_instance()
