import sqlite3
import random
from datetime import datetime, timedelta
import uuid
import os # Added for directory creation and path joining

# --- Configuration ---
# Adjusted DB_NAME to point to the data/ subdirectory
DB_FILE_NAME = "data_query_assistant.db"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Get project root (assuming script is in src/scripts/)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, DB_FILE_NAME) # Full path to the database file

NUM_USERS = 10
NUM_DAYS_OF_DATA = 30 # Generate data for the last X days
START_DATE = datetime.now() - timedelta(days=NUM_DAYS_OF_DATA)

# --- Helper Functions ---
def get_db_connection():
    """Establishes a connection to the SQLite database."""
    # Ensure the data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"Ensuring database will be created/accessed at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

def create_tables(conn):
    """Creates the database tables if they don't already exist."""
    cursor = conn.cursor()

    # Table 1: user_activity
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_activity (
        userid TEXT NOT NULL,
        date DATE NOT NULL,
        loyalty_category TEXT,
        total_revenue REAL DEFAULT 0,
        total_withdrawls REAL DEFAULT 0,
        total_bonus REAL DEFAULT 0,
        PRIMARY KEY (userid, date)
    )
    """)
    print("Table 'user_activity' created or already exists.")

    # Table 2: user_game_summary
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_game_summary (
        userid TEXT NOT NULL,
        date DATE NOT NULL,
        games_count INTEGER DEFAULT 0,
        total_winnings REAL DEFAULT 0,
        wager REAL DEFAULT 0,
        point_game INTEGER DEFAULT 0,
        total_cashgamecount INTEGER DEFAULT 0,
        total_gamewon INTEGER DEFAULT 0,
        total_gamelost INTEGER DEFAULT 0,
        PRIMARY KEY (userid, date)
    )
    """)
    print("Table 'user_game_summary' created or already exists.")

    # Table 3: user_deposits
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_deposits (
        userid TEXT NOT NULL,
        date DATE NOT NULL,
        total_deposit REAL DEFAULT 0,
        deposit_count INTEGER DEFAULT 0,
        PRIMARY KEY (userid, date)
    )
    """)
    print("Table 'user_deposits' created or already exists.")

    conn.commit()
    print("-" * 30)

def generate_dummy_data(conn):
    """Generates and inserts dummy data into the tables."""
    cursor = conn.cursor()
    user_ids = [str(uuid.uuid4()) for _ in range(NUM_USERS)]
    loyalty_categories = ['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond']
    dates = [START_DATE + timedelta(days=i) for i in range(NUM_DAYS_OF_DATA)]

    print(f"Generating data for {NUM_USERS} users over {NUM_DAYS_OF_DATA} days...")

    for user_id in user_ids:
        current_loyalty = random.choice(loyalty_categories)
        for date_obj in dates:
            date_str = date_obj.strftime('%Y-%m-%d')

            # --- user_activity data ---
            if random.random() < 0.9: # assuming 90% chance of user activity
                total_revenue = round(random.uniform(0, 5000), 2)
                total_withdrawls = round(random.uniform(0, min(total_revenue * 0.8, 200)), 2)
                total_bonus = round(random.uniform(0, 500), 2)
                if date_obj.day == 1 and random.random() < 0.2:
                    current_loyalty = random.choice(loyalty_categories)

                cursor.execute("""
                INSERT INTO user_activity (userid, date, loyalty_category, total_revenue, total_withdrawls, total_bonus)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(userid, date) DO NOTHING;
                """, (user_id, date_str, current_loyalty, total_revenue, total_withdrawls, total_bonus))

            # --- user_game_summary data ---
            if random.random() < 0.85: # 85% chance of playing games
                games_count = random.randint(0, 50)
                if games_count > 0:
                    total_gamewon = random.randint(0, games_count)
                    total_gamelost = games_count - total_gamewon
                    total_winnings = round(random.uniform(0, games_count * 25), 2)
                    wager = round(random.uniform(games_count * 0.5, games_count * 10), 2)
                    point_game = random.randint(0, games_count // 2)
                    total_cashgamecount = games_count - point_game
                else:
                    total_gamewon, total_gamelost, total_winnings, wager, point_game, total_cashgamecount = 0,0,0,0,0,0

                cursor.execute("""
                INSERT INTO user_game_summary (userid, date, games_count, total_winnings, wager, point_game, total_cashgamecount, total_gamewon, total_gamelost)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(userid, date) DO NOTHING;
                """, (user_id, date_str, games_count, total_winnings, wager, point_game, total_cashgamecount, total_gamewon, total_gamelost))

            # --- user_deposits data ---
            if random.random() < 0.3: # 30% chance of making a deposit
                deposit_count = random.randint(1, 5)
                total_deposit = round(random.uniform(10, 300) * deposit_count, 2)
                cursor.execute("""
                INSERT INTO user_deposits (userid, date, total_deposit, deposit_count)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(userid, date) DO NOTHING;
                """, (user_id, date_str, total_deposit, deposit_count))

    conn.commit()
    print("Dummy data generation complete.")
    print("-" * 30)

def verify_data_insertion(conn):
    """Prints counts from each table to verify insertion."""
    cursor = conn.cursor()
    tables = ["user_activity", "user_game_summary", "user_deposits"]
    print("Verifying data insertion (row counts):")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"Table '{table}': {count} rows")
    print("-" * 30)


# --- Main Execution ---
if __name__ == "__main__":
    # Ensure the data directory exists before attempting to delete the DB file
    os.makedirs(DATA_DIR, exist_ok=True)

    if os.path.exists(DB_PATH):
        print(f"Deleting existing database: {DB_PATH}")
        os.remove(DB_PATH)

    conn = get_db_connection()

    create_tables(conn)
    generate_dummy_data(conn)
    verify_data_insertion(conn)

    conn.close()
    print(f"Database '{DB_PATH}' created and populated successfully.")
    print(f"You can now inspect '{DB_PATH}' using a SQLite browser.")