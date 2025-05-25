import argparse
import subprocess
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# --- Define Actions ---
def run_streamlit_app():
    """Launches the Streamlit web application."""
    print("Attempting to launch Streamlit app...")
    streamlit_command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        os.path.join("src", "app.py") # Path relative to project root
    ]
    try:
        print(f"Executing: {' '.join(streamlit_command)}")
        print(f"From directory: {PROJECT_ROOT}")
        # `cwd=PROJECT_ROOT` ensures Streamlit runs with the project root as the current working directory.
        # This helps Python resolve modules correctly, especially for the `src` package.
        process = subprocess.Popen(streamlit_command, cwd=PROJECT_ROOT)
        process.wait()
    except FileNotFoundError:
        print("Error: streamlit command not found. Is Streamlit installed and in your PATH?")
    except Exception as e:
        print(f"An error occurred while trying to run the Streamlit app: {e}")

def setup_database():
    """Runs the database setup script."""
    print("Attempting to run database setup script...")
    db_setup_script_path = os.path.join("src", "scripts", "setup_database.py")
    
    if not os.path.exists(os.path.join(PROJECT_ROOT, db_setup_script_path)):
        print(f"Error: Database setup script not found at {db_setup_script_path}")
        return

    db_setup_command = [
        sys.executable,
        db_setup_script_path
    ]
    try:
        print(f"Executing: {' '.join(db_setup_command)}")
        # Running with cwd=PROJECT_ROOT ensures the script's relative paths (like to data/) work correctly.
        process = subprocess.Popen(db_setup_command, cwd=PROJECT_ROOT)
        process.wait()
        print("Database setup script finished.")
    except FileNotFoundError:
        print(f"Error: Python interpreter or script not found. Path: {db_setup_script_path}")
    except Exception as e:
        print(f"An error occurred during database setup: {e}")

def run_cli_chat():
    """Launches the command-line interface for the chat application."""
    print("Attempting to launch CLI chat app...")
    cli_script_path = os.path.join("src", "main_cli.py")

    if not os.path.exists(os.path.join(PROJECT_ROOT, cli_script_path)):
        print(f"Error: CLI chat script not found at {cli_script_path}")
        print("You can create this file based on previous discussions for a CLI chat interface.")
        return

    cli_command = [
        sys.executable,
        cli_script_path
    ]
    try:
        print(f"Executing: {' '.join(cli_command)}")
        process = subprocess.Popen(cli_command, cwd=PROJECT_ROOT)
        process.wait()
    except FileNotFoundError:
        print(f"Error: Python interpreter or script not found. Path: {cli_script_path}")
    except Exception as e:
        print(f"An error occurred while trying to run the CLI chat app: {e}")


# --- Main Execution ---

def main():
    parser = argparse.ArgumentParser(description="text2SQL Project Management CLI.")
    parser.add_argument(
        "action",
        choices=["run_app", "setup_db", "run_cli"],
        help="The action to perform: 'run_app' to start the Streamlit UI, "
             "'setup_db' to initialize/reset the database, "
             "'run_cli' to start the command-line chat interface."
    )

    args = parser.parse_args()

    if args.action == "run_app":
        run_streamlit_app()
    elif args.action == "setup_db":
        setup_database()
    elif args.action == "run_cli":
        run_cli_chat()
    else:
        print(f"Unknown action: {args.action}")
        parser.print_help()

if __name__ == "__main__":
    main()