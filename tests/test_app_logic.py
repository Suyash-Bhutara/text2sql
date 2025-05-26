import pytest
import uuid
import os
import sys
import subprocess
from datetime import datetime, timedelta

# Ensure the src directory is in the Python path
# This allows importing modules from src (e.g., src.core.graph)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if PROJECT_ROOT not in sys.path: # Also add project root for main.py if needed by scripts
    sys.path.insert(0, PROJECT_ROOT)


from langchain_core.messages import HumanMessage, AIMessage
# from src.core.graph import compiled_graph # MOVED: This import is deferred
# from src.core.graph_components import State # If you need to assert specific state structures

# --- Constants for Dates ---
# It's good practice to have consistent dates for testing if possible,
# or calculate them dynamically as done here.
TODAY = datetime.now()
YESTERDAY = TODAY - timedelta(days=1)
TODAY_STR = TODAY.strftime("%Y-%m-%d")
YESTERDAY_STR = YESTERDAY.strftime("%Y-%m-%d")
SEVEN_DAYS_AGO_STR = (TODAY - timedelta(days=7)).strftime("%Y-%m-%d")


# --- Pytest Fixture for Database Setup ---
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Ensures the database is set up before any tests run.
    This runs once per test session.
    """
    print("Setting up the test environment...")

    # 1. Check for .env file (and create a dummy if not present for tests)
    env_path = os.path.join(PROJECT_ROOT, ".env")
    if not os.path.exists(env_path):
        print("Warning: .env file not found. Creating a dummy .env for testing.")
        print("Please ensure GOOGLE_API_KEY is set in your environment or this dummy file if LLM calls are made.")
        with open(env_path, "w") as f:
            f.write("GOOGLE_API_KEY=YOUR_API_KEY_HERE\n") # Replace if you have a test key
            f.write("GOOGLE_MODEL=gemini-1.5-flash-preview-0514\n") # Or your preferred test model

    # 2. Ensure data directory exists
    data_dir = os.path.join(PROJECT_ROOT, "data")
    os.makedirs(data_dir, exist_ok=True)

    # 3. Run the database setup script
    # Assumes main.py and setup_database.py are in the correct locations relative to PROJECT_ROOT
    db_setup_script_path = os.path.join(SRC_DIR, "scripts", "setup_database.py")
    
    # Check if the setup script exists
    if not os.path.exists(db_setup_script_path):
        pytest.fail(f"Database setup script not found at {db_setup_script_path}. "
                    "Ensure your project structure is correct.")

    print(f"Running database setup script: {db_setup_script_path}")
    try:
        # Use subprocess to run the script, ensuring it uses the project's Python environment
        # Running from PROJECT_ROOT as cwd helps the script resolve its paths (like to data/)
        process = subprocess.run(
            [sys.executable, db_setup_script_path],
            cwd=PROJECT_ROOT, # Run from the project root
            capture_output=True,
            text=True,
            check=True # Will raise CalledProcessError if script fails
        )
        print("Database setup script output:\n", process.stdout)
        if process.stderr:
            print("Database setup script errors:\n", process.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Database setup script failed with error code {e.returncode}.")
        print("Stdout:", e.stdout)
        print("Stderr:", e.stderr)
        pytest.fail("Database setup script failed. Check errors above.")
    except FileNotFoundError:
        pytest.fail(f"Failed to find Python interpreter or script: {db_setup_script_path}")
    
    print("Test environment setup complete.")
    # No teardown needed here as setup_database.py handles fresh DB creation


# --- Helper Function to Run a Question Through the Graph ---
def run_question(question: str, chat_history: list = None, conversation_id: str = None):
    """
    Sends a question to the compiled_graph and returns the final state.
    """
    from src.core.graph import compiled_graph # MOVED: Import compiled_graph here
    
    if chat_history is None:
        chat_history = []
    if conversation_id is None:
        conversation_id = str(uuid.uuid4())

    graph_input = {
        "question": question,
        "chat_history": chat_history.copy()
    }
    config = {"configurable": {"thread_id": conversation_id}}

    final_graph_output = None
    # Using stream_mode="values" as in app.py to get the final accumulated state
    for step_output in compiled_graph.stream(graph_input, config=config, stream_mode="values"):
        final_graph_output = step_output # The last item is the final state

    if final_graph_output is None:
        pytest.fail(f"Graph did not return an output for question: {question}")

    return final_graph_output, conversation_id


# --- Test Cases ---

def test_tc001_basic_retrieval_single_table():
    """TC001: Basic Valid Query - Single Table"""
    question = "Show all userids from user_activity."
    output, _ = run_question(question)

    assert "query" in output, "Graph output should contain a 'query'."
    assert "answer" in output, "Graph output should contain an 'answer'."
    assert output["query"].strip().upper().startswith("SELECT"), "Query should start with SELECT."
    assert "USERID FROM USER_ACTIVITY" in output["query"].upper(), "Query should select userid from user_activity."
    # For the answer, check for general sense rather than exact match due to LLM variability
    assert "user ids" in output["answer"].lower() or "users" in output["answer"].lower()

def test_tc002_filter_with_where_clause():
    """TC002: Valid Query - With WHERE Clause"""
    question = "List users with loyalty_category 'Gold'."
    output, _ = run_question(question)

    assert "query" in output
    assert "USER_ACTIVITY" in output["query"].upper()
    assert "LOYALTY_CATEGORY" in output["query"].upper()
    assert "'GOLD'" in output["query"].upper() # Check for the literal 'Gold'
    assert "WHERE" in output["query"].upper()
    assert "Gold" in output["answer"] or "gold" in output["answer"].lower()

def test_tc003_aggregation_sum():
    """TC003: Valid Query - With Aggregation (SUM)"""
    # Using a more specific date to make the query more predictable
    question = f"What is the total number of games played by all users on {YESTERDAY_STR}?"
    output, _ = run_question(question)
    
    assert "query" in output
    query_upper = output["query"].upper()
    assert "SELECT SUM(GAMES_COUNT)" in query_upper
    assert "FROM USER_GAME_SUMMARY" in query_upper
    assert f"DATE = '{YESTERDAY_STR}'" in query_upper
    assert "total games" in output["answer"].lower() or "number of games" in output["answer"].lower() or "a total of" in output["answer"].lower()

def test_tc004_date_range_relative():
    """TC004: Valid Query - Date Range (Relative)"""
    question = "Show total revenue in the last 7 days."
    output, _ = run_question(question)

    assert "query" in output
    query_upper = output["query"].upper()
    assert "TOTAL_REVENUE" in query_upper
    assert "USER_ACTIVITY" in query_upper
    # The prompt uses `date('now', '-7 days')` for SQLite.
    assert "DATE" in query_upper
    # assert "NOW" in query_upper
    assert "-7 DAYS" in query_upper or "7 DAY" in query_upper # Allow for slight variations
    assert "total revenue" in output["answer"].lower()

@pytest.mark.skip(reason="LLM-based join inference can be complex to assert reliably without more specific schema knowledge in the test.")
def test_tc005_multiple_tables_implicit_join():
    """TC005: Valid Query - Multiple Tables (Implicit Join)"""
    question = f"Show the total deposit for users who played more than 10 games on {YESTERDAY_STR}."
    output, _ = run_question(question)

    assert "query" in output
    query_upper = output["query"].upper()
    assert "USER_DEPOSITS" in query_upper
    assert "USER_GAME_SUMMARY" in query_upper
    assert "TOTAL_DEPOSIT" in query_upper
    assert "GAMES_COUNT > 10" in query_upper
    assert f"DATE = '{YESTERDAY_STR}'" in query_upper # Assuming date applies to both conditions
    # Answer check
    assert "total deposit" in output["answer"].lower()

def test_tc006_clarification_needed_ambiguous():
    """TC006: Clarification Needed - Ambiguous Question"""
    question = "Tell me about user activity."
    output, _ = run_question(question)

    assert "answer" in output
    if output.get("clarification_needed") is True: # If your State explicitly has this
         assert "clarification_question" in output and output["clarification_question"]
    else: # Check if the answer asks for clarification
        answer_lower = output["answer"].lower()
        assert "clarify" in answer_lower or \
               "specific" in answer_lower or \
               "details" in answer_lower or \
               "which users" in answer_lower or \
               "what dates" in answer_lower or \
               output["answer"].endswith("?")

def test_tc007_query_non_existent_column():
    """TC007: Query for Non-Existent Column/Data"""
    question = f"What is the 'user_mood' for players on {YESTERDAY_STR}?"
    output, _ = run_question(question)

    assert "answer" in output
    # Expect an answer indicating the information is not available or an error occurred.
    answer_lower = output["answer"].lower()
    assert "could not find" in answer_lower or \
           "cannot find" in answer_lower or \
           "can't find" in answer_lower or \
           "don't have information" in answer_lower or \
           "error" in answer_lower or \
           "column 'user_mood' does not exist" in answer_lower or \
           "no such column" in output.get("result","").lower() # Check raw result if available
    
    # Also check if the query reflects the attempt or an error
    if "ERROR_GENERATING_QUERY" not in output.get("query", ""):
        assert "USER_MOOD" in output.get("query", "").upper() # If it tried to query

def test_tc009_follow_up_question_correct_context():
    """TC009: Follow-up Question - Correct Context"""
    conv_id = str(uuid.uuid4())
    chat_history = []

    # First question
    q1 = f"List Gold loyalty users with total revenue over 100 on {YESTERDAY_STR}."
    output1, conv_id = run_question(q1, chat_history=chat_history, conversation_id=conv_id)
    
    assert "answer" in output1
    # Don't assert too strictly on q1's answer, focus on q2
    chat_history.append(HumanMessage(content=q1))
    chat_history.append(AIMessage(content=output1["answer"]))

    # Second question (follow-up)
    q2 = "For these users, what was their games_count on that day?"
    output2, _ = run_question(q2, chat_history=chat_history, conversation_id=conv_id)

    assert "query" in output2
    query2_upper = output2["query"].upper()
    assert "GAMES_COUNT" in query2_upper
    assert "USER_GAME_SUMMARY" in query2_upper # Should query game summary
    # Check if it's trying to use context (e.g., filtering by user IDs from previous step,
    # or by re-applying conditions if LLM reconstructs)
    # This is hard to assert perfectly without knowing the exact SQL the LLM generates for context.
    # A simple check could be that it's still referencing the date or loyalty.
    assert f"DATE = '{YESTERDAY_STR}'" in query2_upper or "GOLD" in query2_upper
    assert "games count" in output2["answer"].lower() or "number of games" in output2["answer"].lower()

def test_tc011_empty_result_set():
    """TC011: Empty Result Set"""
    # Assuming no user has this impossibly high revenue
    question = f"Find users with total_revenue over 999999999 on {YESTERDAY_STR}."
    output, _ = run_question(question)

    assert "answer" in output
    answer_lower = output["answer"].lower()
    assert "no data was found" in answer_lower or \
           "no users matched" in answer_lower or \
           "could not find any users" in answer_lower or \
           "no results" in answer_lower
    
    # The 'result' field in the state should also reflect this
    # Langchain's SQL tool often returns "[]" or an empty list string for no results.
    assert output.get("result") == "[]" or output.get("result") is None or not output.get("result")


def test_tc017_top_k_results_limit():
    """TC017: Configuration - Top K Results (Implicit check)"""
    # This test assumes DEFAULT_TOP_K_RESULTS is e.g. 10 (as in your config.py)
    # Ask a broad question that would likely return many results if not limited.
    question = "Show me all user activity." # Very broad
    output, _ = run_question(question)

    assert "query" in output
    query_upper = output["query"].upper()
    
    # The prompt instructs the LLM to limit to top_k.
    # Check if "LIMIT" is in the generated query.
    # The default top_k is 10 from your config.py, used in prompts.py
    assert "LIMIT" in query_upper
    # We can't easily check the exact number in the LIMIT clause without parsing SQL,
    # but presence of LIMIT is a good indicator.
    # A more robust check would be to parse the SQL if a library is available.
    # For now, presence of LIMIT is the main check.

    # Check if the answer implies a limited set if many results were possible
    # e.g., "Here are some of the user activities..."
    # This part is highly LLM-dependent.
    # For a more direct test, you'd need to inspect the actual data returned if your
    # `execute_query` node returned the raw data count before formatting by `generate_answer`.

# --- More Test Ideas (to be implemented similarly) ---

# TC008: Query for Non-Existent Table
# "Show data from the 'promotions' table."
# Expected: Error message in answer, query might show attempt or error.

# TC012: SQL Execution Error (Hard to induce reliably without direct SQL injection)
# One way could be to make the LLM generate a syntactically correct but semantically problematic query
# for the given DB schema, e.g., wrong data type comparison if not handled by SQLite flexibly.
# question = "Show users where total_revenue is 'abc'." (SQLite might coerce, so this is tricky)
# Expected: Answer indicates an error during data retrieval.

# TC015: Database Setup Script (Covered by fixture, but can have an explicit test if needed)
# def test_tc015_database_file_exists():
#     db_path = os.path.join(PROJECT_ROOT, "data", "data_query_assistant.db")
#     assert os.path.exists(db_path), "Database file should exist after setup."

# TC018: Complex Query
# question = "Show user IDs and total winnings for 'Platinum' users who made >2 deposits " \
#            f"and played <5 cash games on {YESTERDAY_STR}, with revenue > $100 on that day."
# Expected: LLM attempts a complex query. Assertions on parts of the query and a coherent answer.